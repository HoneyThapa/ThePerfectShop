"""
Job scheduler for ExpiryShield backend.
Handles scheduled processing of features, risk scoring, and action generation.

Requirements 7.1, 7.5:
- Support scheduled execution of feature building, risk scoring, and action generation
- Provide job status and progress information via API endpoints
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
import time
import random

from app.db.session import SessionLocal, engine
from app.db.models import JobExecution
from app.services.features import build_features
from app.services.scoring import compute_batch_risk
from app.services.actions import ActionEngine

# Set up logging
logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job execution status enumeration."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class JobType(Enum):
    """Types of scheduled jobs."""
    FEATURE_BUILD = "FEATURE_BUILD"
    RISK_SCORING = "RISK_SCORING"
    ACTION_GENERATION = "ACTION_GENERATION"
    NIGHTLY_PROCESSING = "NIGHTLY_PROCESSING"


@dataclass
class JobResult:
    """Result of job execution."""
    success: bool
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    retry_count: int = 0
    execution_time_seconds: Optional[float] = None


@dataclass
class RetryConfig:
    """Configuration for job retry behavior."""
    max_retries: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 300.0  # 5 minutes
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class ScheduledJob:
    """Definition of a scheduled job."""
    name: str
    job_type: JobType
    function: Callable
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    retry_config: RetryConfig = field(default_factory=RetryConfig)


class JobScheduler:
    """
    Main job scheduler for ExpiryShield backend.
    
    Handles scheduling and execution of nightly processing jobs including:
    - Feature building (velocity calculations)
    - Risk scoring (batch risk assessment)
    - Action generation (recommendations)
    """
    
    def __init__(self):
        self.jobs: Dict[str, ScheduledJob] = {}
        self.running_jobs: Dict[str, asyncio.Task] = {}
        self._setup_default_jobs()
        self._ensure_job_table_exists()
    
    def _ensure_job_table_exists(self):
        """Create job execution tracking table if it doesn't exist."""
        try:
            from app.db.models import Base
            Base.metadata.create_all(bind=engine)
            logger.info("Job execution tracking table initialized")
        except Exception as e:
            logger.error(f"Failed to create job tracking table: {e}")
    
    def _setup_default_jobs(self):
        """Set up default scheduled jobs for the system."""
        # Feature building job
        self.register_job(
            name="nightly_feature_build",
            job_type=JobType.FEATURE_BUILD,
            function=self._run_feature_build,
            parameters={"lookback_days": 30}
        )
        
        # Risk scoring job
        self.register_job(
            name="nightly_risk_scoring",
            job_type=JobType.RISK_SCORING,
            function=self._run_risk_scoring,
            parameters={}
        )
        
        # Action generation job
        self.register_job(
            name="nightly_action_generation",
            job_type=JobType.ACTION_GENERATION,
            function=self._run_action_generation,
            parameters={"min_risk_score": 50.0}
        )
        
        # Combined nightly processing job
        self.register_job(
            name="nightly_full_processing",
            job_type=JobType.NIGHTLY_PROCESSING,
            function=self._run_nightly_processing,
            parameters={"full_refresh": True}
        )
    
    def register_job(
        self,
        name: str,
        job_type: JobType,
        function: Callable,
        parameters: Dict[str, Any] = None,
        enabled: bool = True,
        retry_config: RetryConfig = None
    ):
        """Register a new scheduled job with retry configuration."""
        self.jobs[name] = ScheduledJob(
            name=name,
            job_type=job_type,
            function=function,
            parameters=parameters or {},
            enabled=enabled,
            retry_config=retry_config or RetryConfig()
        )
        logger.info(f"Registered job: {name} ({job_type.value}) with retry config: max_retries={self.jobs[name].retry_config.max_retries}")
    
    def get_job_status(self, job_name: str) -> Optional[Dict[str, Any]]:
        """Get current status of a specific job."""
        if job_name not in self.jobs:
            return None
        
        job = self.jobs[job_name]
        is_running = job_name in self.running_jobs
        
        # Get latest execution from database
        db = SessionLocal()
        try:
            latest_execution = (
                db.query(JobExecution)
                .filter(JobExecution.job_name == job_name)
                .order_by(JobExecution.created_at.desc())
                .first()
            )
            
            return {
                "name": job.name,
                "type": job.job_type.value,
                "enabled": job.enabled,
                "is_running": is_running,
                "last_run": job.last_run.isoformat() if job.last_run else None,
                "next_run": job.next_run.isoformat() if job.next_run else None,
                "latest_execution": {
                    "status": latest_execution.status if latest_execution else None,
                    "started_at": latest_execution.started_at.isoformat() if latest_execution and latest_execution.started_at else None,
                    "completed_at": latest_execution.completed_at.isoformat() if latest_execution and latest_execution.completed_at else None,
                    "error_message": latest_execution.error_message if latest_execution else None,
                    "result_summary": latest_execution.result_summary if latest_execution else None
                } if latest_execution else None
            }
        finally:
            db.close()
    
    def get_all_jobs_status(self) -> List[Dict[str, Any]]:
        """Get status of all registered jobs."""
        return [self.get_job_status(name) for name in self.jobs.keys()]
    
    async def run_job(self, job_name: str, parameters: Dict[str, Any] = None) -> JobResult:
        """
        Execute a specific job by name.
        
        Requirements 7.1:
        - Support scheduled execution of feature building, risk scoring, and action generation
        """
        if job_name not in self.jobs:
            return JobResult(
                success=False,
                message=f"Job '{job_name}' not found",
                error="Job not registered"
            )
        
        job = self.jobs[job_name]
        if not job.enabled:
            return JobResult(
                success=False,
                message=f"Job '{job_name}' is disabled",
                error="Job disabled"
            )
        
        if job_name in self.running_jobs:
            return JobResult(
                success=False,
                message=f"Job '{job_name}' is already running",
                error="Job already running"
            )
        
        # Create job execution record
        db = SessionLocal()
        execution = JobExecution(
            job_name=job_name,
            job_type=job.job_type.value,
            status=JobStatus.PENDING.value,
            parameters=parameters or job.parameters
        )
        db.add(execution)
        db.commit()
        execution_id = execution.id
        db.close()
        
        # Start job execution
        task = asyncio.create_task(self._execute_job(job, execution_id, parameters))
        self.running_jobs[job_name] = task
        
        try:
            result = await task
            job.last_run = datetime.now()
            return result
        finally:
            if job_name in self.running_jobs:
                del self.running_jobs[job_name]
    
    async def _execute_job(
        self,
        job: ScheduledJob,
        execution_id: int,
        parameters: Dict[str, Any] = None
    ) -> JobResult:
        """
        Execute a job with retry logic and comprehensive error handling.
        
        Requirements 7.2:
        - Implement robust error handling for scheduled jobs
        - Add job retry logic with exponential backoff
        - Create comprehensive job logging and status reporting
        """
        db = SessionLocal()
        retry_count = 0
        start_time = time.time()
        
        try:
            # Update status to running
            execution = db.query(JobExecution).filter(JobExecution.id == execution_id).first()
            execution.status = JobStatus.RUNNING.value
            execution.started_at = datetime.now()
            db.commit()
            
            logger.info(f"Starting job execution: {job.name}")
            
            # Execute the job function with retry logic
            job_parameters = {**(job.parameters or {}), **(parameters or {})}
            
            while retry_count <= job.retry_config.max_retries:
                try:
                    # Execute the job function
                    result = await job.function(**job_parameters)
                    
                    # Add execution metadata
                    execution_time = time.time() - start_time
                    result.retry_count = retry_count
                    result.execution_time_seconds = execution_time
                    
                    # Update status to completed
                    execution.status = JobStatus.COMPLETED.value
                    execution.completed_at = datetime.now()
                    execution.result_summary = {
                        **result.data,
                        "retry_count": retry_count,
                        "execution_time_seconds": execution_time
                    }
                    db.commit()
                    
                    logger.info(f"Job completed successfully: {job.name} (attempt {retry_count + 1}/{job.retry_config.max_retries + 1})")
                    return result
                    
                except Exception as e:
                    retry_count += 1
                    error_message = str(e)
                    
                    logger.warning(f"Job attempt {retry_count}/{job.retry_config.max_retries + 1} failed for {job.name}: {error_message}")
                    
                    # If we've exhausted retries, fail the job
                    if retry_count > job.retry_config.max_retries:
                        execution_time = time.time() - start_time
                        
                        # Update status to failed
                        execution.status = JobStatus.FAILED.value
                        execution.completed_at = datetime.now()
                        execution.error_message = f"Failed after {retry_count} attempts. Last error: {error_message}"
                        execution.result_summary = {
                            "retry_count": retry_count - 1,
                            "execution_time_seconds": execution_time,
                            "final_error": error_message
                        }
                        db.commit()
                        
                        logger.error(f"Job failed permanently: {job.name} after {retry_count} attempts")
                        return JobResult(
                            success=False,
                            message=f"Job '{job.name}' failed after {retry_count} attempts",
                            error=error_message,
                            retry_count=retry_count - 1,
                            execution_time_seconds=execution_time
                        )
                    
                    # Calculate delay for next retry with exponential backoff
                    delay = self._calculate_retry_delay(retry_count, job.retry_config)
                    
                    logger.info(f"Retrying job {job.name} in {delay:.2f} seconds (attempt {retry_count + 1}/{job.retry_config.max_retries + 1})")
                    
                    # Update execution record with retry information
                    execution.error_message = f"Attempt {retry_count} failed: {error_message}. Retrying in {delay:.2f}s"
                    execution.result_summary = {
                        "retry_count": retry_count,
                        "last_error": error_message,
                        "next_retry_in_seconds": delay
                    }
                    db.commit()
                    
                    # Wait before retrying
                    await asyncio.sleep(delay)
            
        except Exception as e:
            # Unexpected error in retry logic itself
            execution_time = time.time() - start_time
            
            execution = db.query(JobExecution).filter(JobExecution.id == execution_id).first()
            execution.status = JobStatus.FAILED.value
            execution.completed_at = datetime.now()
            execution.error_message = f"Unexpected error in job execution framework: {str(e)}"
            execution.result_summary = {
                "retry_count": retry_count,
                "execution_time_seconds": execution_time,
                "framework_error": str(e)
            }
            db.commit()
            
            logger.error(f"Unexpected error in job execution framework for {job.name}: {str(e)}")
            return JobResult(
                success=False,
                message=f"Job '{job.name}' failed due to framework error",
                error=str(e),
                retry_count=retry_count,
                execution_time_seconds=execution_time
            )
        finally:
            db.close()
    
    def _calculate_retry_delay(self, retry_count: int, config: RetryConfig) -> float:
        """
        Calculate delay for retry with exponential backoff and jitter.
        
        Requirements 7.2:
        - Add job retry logic with exponential backoff
        """
        # Calculate exponential backoff delay
        delay = config.base_delay_seconds * (config.exponential_base ** (retry_count - 1))
        
        # Apply maximum delay limit
        delay = min(delay, config.max_delay_seconds)
        
        # Add jitter to prevent thundering herd
        if config.jitter:
            jitter_amount = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_amount, jitter_amount)
        
        return max(delay, 0.1)  # Minimum 0.1 second delay
    
    async def _run_feature_build(self, lookback_days: int = 30, incremental: bool = True, **kwargs) -> JobResult:
        """
        Execute feature building job with incremental processing support.
        
        Requirements 7.3, 7.4:
        - Implement incremental data processing where possible
        - Add change detection to avoid full recomputation
        - Optimize job performance for large datasets
        
        Builds rolling velocity features for all store-SKU combinations.
        """
        try:
            from app.services.features import (
                build_features, 
                detect_sales_data_changes, 
                optimize_feature_calculation_performance
            )
            
            snapshot_date = date.today()
            
            logger.info(f"Building features for snapshot date: {snapshot_date} (incremental={incremental})")
            
            # Optimize processing strategy based on data volume
            optimization_info = optimize_feature_calculation_performance(snapshot_date)
            
            # Check if incremental processing is possible and beneficial
            changed_store_skus = None
            if incremental:
                changed_store_skus = detect_sales_data_changes(snapshot_date, lookback_days)
                
                if not changed_store_skus:
                    logger.info("No sales data changes detected, skipping feature building")
                    return JobResult(
                        success=True,
                        message=f"Feature building skipped - no changes detected for {snapshot_date}",
                        data={
                            "snapshot_date": snapshot_date.isoformat(),
                            "features_built": 0,
                            "lookback_days": lookback_days,
                            "incremental": True,
                            "skipped_reason": "no_changes_detected",
                            "optimization_strategy": optimization_info["strategy"]
                        }
                    )
                
                logger.info(f"Detected {len(changed_store_skus)} store-SKU combinations with changes")
            
            # Run feature building with incremental processing
            build_features(snapshot_date, incremental=incremental, changed_store_skus=changed_store_skus)
            
            # Get count of features built
            db = SessionLocal()
            try:
                from app.db.models import FeatureStoreSKU
                feature_count = (
                    db.query(FeatureStoreSKU)
                    .filter(FeatureStoreSKU.date == snapshot_date)
                    .count()
                )
                
                # Update change tracking with current processing
                if incremental:
                    await self._update_change_tracking(snapshot_date, "features", feature_count)
                
            finally:
                db.close()
            
            return JobResult(
                success=True,
                message=f"Feature building completed for {snapshot_date}",
                data={
                    "snapshot_date": snapshot_date.isoformat(),
                    "features_built": feature_count,
                    "lookback_days": lookback_days,
                    "incremental": incremental,
                    "changed_store_skus": len(changed_store_skus) if changed_store_skus else 0,
                    "optimization_strategy": optimization_info["strategy"]
                }
            )
            
        except Exception as e:
            logger.error(f"Feature building failed: {str(e)}")
            raise
    
    async def _run_risk_scoring(self, incremental: bool = True, **kwargs) -> JobResult:
        """
        Execute risk scoring job with incremental processing support.
        
        Requirements 7.3, 7.4:
        - Implement incremental data processing where possible
        - Add change detection to avoid full recomputation
        - Optimize job performance for large datasets
        
        Computes risk scores for all inventory batches.
        """
        try:
            from app.services.scoring import (
                compute_batch_risk, 
                detect_inventory_changes, 
                optimize_risk_calculation_performance
            )
            
            snapshot_date = date.today()
            
            logger.info(f"Computing risk scores for snapshot date: {snapshot_date} (incremental={incremental})")
            
            # Optimize processing strategy based on data volume
            optimization_info = optimize_risk_calculation_performance(snapshot_date)
            
            # Check if incremental processing is possible
            changed_batches = None
            if incremental:
                changed_batches = detect_inventory_changes(snapshot_date)
                
                if not changed_batches:
                    logger.info("No relevant data changes detected, skipping risk scoring")
                    return JobResult(
                        success=True,
                        message=f"Risk scoring skipped - no changes detected for {snapshot_date}",
                        data={
                            "snapshot_date": snapshot_date.isoformat(),
                            "batches_scored": 0,
                            "high_risk_batches": 0,
                            "incremental": True,
                            "skipped_reason": "no_changes_detected",
                            "optimization_strategy": optimization_info["strategy"]
                        }
                    )
                
                logger.info(f"Detected {len(changed_batches)} changed inventory batches")
            
            # Run risk scoring with incremental processing
            compute_batch_risk(snapshot_date, incremental=incremental, changed_batches=changed_batches)
            
            # Get count of risk scores computed
            db = SessionLocal()
            try:
                from app.db.models import BatchRisk
                risk_count = (
                    db.query(BatchRisk)
                    .filter(BatchRisk.snapshot_date == snapshot_date)
                    .count()
                )
                
                high_risk_count = (
                    db.query(BatchRisk)
                    .filter(
                        BatchRisk.snapshot_date == snapshot_date,
                        BatchRisk.risk_score >= 70
                    )
                    .count()
                )
                
                # Update change tracking
                if incremental:
                    await self._update_change_tracking(snapshot_date, "risk_scoring", risk_count)
                
            finally:
                db.close()
            
            return JobResult(
                success=True,
                message=f"Risk scoring completed for {snapshot_date}",
                data={
                    "snapshot_date": snapshot_date.isoformat(),
                    "batches_scored": risk_count,
                    "high_risk_batches": high_risk_count,
                    "incremental": incremental,
                    "changed_batches": len(changed_batches) if changed_batches else 0,
                    "optimization_strategy": optimization_info["strategy"]
                }
            )
            
        except Exception as e:
            logger.error(f"Risk scoring failed: {str(e)}")
            raise
    
    async def _run_action_generation(self, min_risk_score: float = 50.0, incremental: bool = True, **kwargs) -> JobResult:
        """
        Execute action generation job with incremental processing support.
        
        Requirements 7.3, 7.4:
        - Implement incremental data processing where possible
        - Add change detection to avoid full recomputation
        - Optimize job performance for large datasets
        
        Generates transfer, markdown, and liquidation recommendations.
        """
        try:
            from app.services.actions import (
                ActionEngine, 
                detect_risk_score_changes, 
                optimize_action_generation_performance
            )
            
            snapshot_date = date.today()
            
            logger.info(f"Generating actions for snapshot date: {snapshot_date} (incremental={incremental})")
            
            # Optimize processing strategy based on data volume
            optimization_info = optimize_action_generation_performance(snapshot_date)
            
            # Check if incremental processing is possible
            changed_batches = None
            if incremental:
                changed_batches = detect_risk_score_changes(snapshot_date)
                
                if not changed_batches:
                    logger.info("No risk score changes detected, skipping action generation")
                    return JobResult(
                        success=True,
                        message=f"Action generation skipped - no changes detected for {snapshot_date}",
                        data={
                            "snapshot_date": snapshot_date.isoformat(),
                            "total_recommendations": 0,
                            "transfer_recommendations": 0,
                            "markdown_recommendations": 0,
                            "liquidation_recommendations": 0,
                            "total_expected_savings": 0.0,
                            "action_ids": [],
                            "incremental": True,
                            "skipped_reason": "no_changes_detected",
                            "optimization_strategy": optimization_info["strategy"]
                        }
                    )
                
                logger.info(f"Detected {len(changed_batches)} batches with risk score changes")
            
            # Initialize action engine
            action_engine = ActionEngine()
            
            # Generate all recommendations with incremental processing
            recommendations = action_engine.generate_all_recommendations(
                snapshot_date, 
                incremental=incremental, 
                changed_batches=changed_batches
            )
            
            # Save recommendations to database
            action_ids = action_engine.save_recommendations_to_db(recommendations)
            
            # Categorize recommendations
            transfer_count = sum(1 for r in recommendations if r['action_type'] == 'TRANSFER')
            markdown_count = sum(1 for r in recommendations if r['action_type'] == 'MARKDOWN')
            liquidation_count = sum(1 for r in recommendations if r['action_type'] == 'LIQUIDATE')
            
            total_expected_savings = sum(r['expected_savings'] for r in recommendations)
            
            # Update change tracking
            if incremental:
                await self._update_change_tracking(snapshot_date, "action_generation", len(recommendations))
            
            return JobResult(
                success=True,
                message=f"Action generation completed for {snapshot_date}",
                data={
                    "snapshot_date": snapshot_date.isoformat(),
                    "total_recommendations": len(recommendations),
                    "transfer_recommendations": transfer_count,
                    "markdown_recommendations": markdown_count,
                    "liquidation_recommendations": liquidation_count,
                    "total_expected_savings": float(total_expected_savings),
                    "action_ids": action_ids,
                    "incremental": incremental,
                    "changed_batches": len(changed_batches) if changed_batches else 0,
                    "optimization_strategy": optimization_info["strategy"]
                }
            )
            
        except Exception as e:
            logger.error(f"Action generation failed: {str(e)}")
            raise
    
    async def _run_nightly_processing(self, full_refresh: bool = True, **kwargs) -> JobResult:
        """
        Execute complete nightly processing pipeline.
        
        Runs feature building, risk scoring, and action generation in sequence.
        """
        try:
            snapshot_date = date.today()
            results = {}
            
            logger.info(f"Starting nightly processing for {snapshot_date}")
            
            # Step 1: Feature building
            logger.info("Step 1: Building features")
            feature_result = await self._run_feature_build()
            results["feature_build"] = feature_result.data
            
            if not feature_result.success:
                raise Exception(f"Feature building failed: {feature_result.error}")
            
            # Step 2: Risk scoring
            logger.info("Step 2: Computing risk scores")
            risk_result = await self._run_risk_scoring()
            results["risk_scoring"] = risk_result.data
            
            if not risk_result.success:
                raise Exception(f"Risk scoring failed: {risk_result.error}")
            
            # Step 3: Action generation
            logger.info("Step 3: Generating actions")
            action_result = await self._run_action_generation()
            results["action_generation"] = action_result.data
            
            if not action_result.success:
                raise Exception(f"Action generation failed: {action_result.error}")
            
            logger.info("Nightly processing completed successfully")
            
            return JobResult(
                success=True,
                message=f"Nightly processing completed for {snapshot_date}",
                data={
                    "snapshot_date": snapshot_date.isoformat(),
                    "processing_steps": results,
                    "total_features": results["feature_build"]["features_built"],
                    "total_risk_scores": results["risk_scoring"]["batches_scored"],
                    "total_recommendations": results["action_generation"]["total_recommendations"],
                    "expected_savings": results["action_generation"]["total_expected_savings"]
                }
            )
            
        except Exception as e:
            logger.error(f"Nightly processing failed: {str(e)}")
            raise
    
    def get_job_history(self, job_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get execution history for a specific job."""
        db = SessionLocal()
        try:
            executions = (
                db.query(JobExecution)
                .filter(JobExecution.job_name == job_name)
                .order_by(JobExecution.created_at.desc())
                .limit(limit)
                .all()
            )
            
            return [
                {
                    "id": exec.id,
                    "status": exec.status,
                    "started_at": exec.started_at.isoformat() if exec.started_at else None,
                    "completed_at": exec.completed_at.isoformat() if exec.completed_at else None,
                    "duration_seconds": (
                        (exec.completed_at - exec.started_at).total_seconds()
                        if exec.started_at and exec.completed_at else None
                    ),
                    "error_message": exec.error_message,
                    "parameters": exec.parameters,
                    "result_summary": exec.result_summary
                }
                for exec in executions
            ]
        finally:
            db.close()
    
    def get_job_statistics(self, job_name: str, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a job over the specified period.
        
        Requirements 7.2:
        - Create comprehensive job logging and status reporting
        """
        db = SessionLocal()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            executions = (
                db.query(JobExecution)
                .filter(
                    JobExecution.job_name == job_name,
                    JobExecution.created_at >= cutoff_date
                )
                .all()
            )
            
            if not executions:
                return {
                    "job_name": job_name,
                    "period_days": days,
                    "total_executions": 0,
                    "success_rate": 0.0,
                    "average_duration_seconds": 0.0,
                    "total_retries": 0,
                    "last_execution": None
                }
            
            total_executions = len(executions)
            successful_executions = sum(1 for e in executions if e.status == JobStatus.COMPLETED.value)
            success_rate = successful_executions / total_executions if total_executions > 0 else 0.0
            
            # Calculate average duration for completed jobs
            completed_executions = [
                e for e in executions 
                if e.status == JobStatus.COMPLETED.value and e.started_at and e.completed_at
            ]
            
            average_duration = 0.0
            if completed_executions:
                total_duration = sum(
                    (e.completed_at - e.started_at).total_seconds() 
                    for e in completed_executions
                )
                average_duration = total_duration / len(completed_executions)
            
            # Count total retries
            total_retries = sum(
                e.result_summary.get("retry_count", 0) 
                for e in executions 
                if e.result_summary and isinstance(e.result_summary, dict)
            )
            
            # Get latest execution info
            latest_execution = max(executions, key=lambda e: e.created_at)
            
            return {
                "job_name": job_name,
                "period_days": days,
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "failed_executions": total_executions - successful_executions,
                "success_rate": round(success_rate * 100, 2),  # Percentage
                "average_duration_seconds": round(average_duration, 2),
                "total_retries": total_retries,
                "last_execution": {
                    "status": latest_execution.status,
                    "started_at": latest_execution.started_at.isoformat() if latest_execution.started_at else None,
                    "completed_at": latest_execution.completed_at.isoformat() if latest_execution.completed_at else None,
                    "error_message": latest_execution.error_message
                }
            }
        finally:
            db.close()
    
    async def _detect_data_changes(self, snapshot_date: date, processing_type: str) -> Dict[str, Any]:
        """
        Detect if relevant data has changed since last processing.
        
        Requirements 7.3, 7.4:
        - Add change detection to avoid full recomputation
        - Optimize job performance for large datasets
        """
        db = SessionLocal()
        try:
            from app.db.models import DataChangeTracking, SalesDaily, InventoryBatch, FeatureStoreSKU, BatchRisk
            import hashlib
            
            # Get last processing record
            last_processing = (
                db.query(DataChangeTracking)
                .filter(
                    DataChangeTracking.processing_type == processing_type,
                    DataChangeTracking.snapshot_date <= snapshot_date
                )
                .order_by(DataChangeTracking.snapshot_date.desc())
                .first()
            )
            
            # If no previous processing, assume changes exist
            if not last_processing:
                return {
                    "has_changes": True,
                    "change_summary": "No previous processing record found",
                    "last_change_date": None,
                    "data_hash": None
                }
            
            # Calculate current data hash based on processing type
            current_hash = None
            change_summary = []
            
            if processing_type == "features":
                # Check for changes in sales data that would affect features
                sales_query = (
                    db.query(SalesDaily)
                    .filter(
                        SalesDaily.date >= snapshot_date - timedelta(days=30),
                        SalesDaily.date <= snapshot_date
                    )
                )
                
                # Create hash of relevant sales data
                sales_data = []
                for sale in sales_query.all():
                    sales_data.append(f"{sale.date}|{sale.store_id}|{sale.sku_id}|{sale.units_sold}")
                
                if sales_data:
                    current_hash = hashlib.md5("|".join(sorted(sales_data)).encode()).hexdigest()
                
                # Check if sales data changed
                if current_hash != last_processing.data_hash:
                    change_summary.append(f"Sales data changed (hash: {current_hash[:8]}...)")
                
            elif processing_type == "risk_scoring":
                # Check for changes in inventory and features that would affect risk scoring
                inventory_query = (
                    db.query(InventoryBatch)
                    .filter(InventoryBatch.snapshot_date == snapshot_date)
                )
                
                features_query = (
                    db.query(FeatureStoreSKU)
                    .filter(FeatureStoreSKU.date == snapshot_date)
                )
                
                # Create combined hash
                data_elements = []
                
                for inv in inventory_query.all():
                    data_elements.append(f"inv|{inv.store_id}|{inv.sku_id}|{inv.batch_id}|{inv.on_hand_qty}|{inv.expiry_date}")
                
                for feat in features_query.all():
                    data_elements.append(f"feat|{feat.store_id}|{feat.sku_id}|{feat.v14}|{feat.volatility}")
                
                if data_elements:
                    current_hash = hashlib.md5("|".join(sorted(data_elements)).encode()).hexdigest()
                
                if current_hash != last_processing.data_hash:
                    change_summary.append(f"Inventory or features data changed (hash: {current_hash[:8]}...)")
                
            elif processing_type == "action_generation":
                # Check for changes in risk scores that would affect action generation
                risk_query = (
                    db.query(BatchRisk)
                    .filter(BatchRisk.snapshot_date == snapshot_date)
                )
                
                risk_data = []
                for risk in risk_query.all():
                    risk_data.append(f"{risk.store_id}|{risk.sku_id}|{risk.batch_id}|{risk.risk_score}|{risk.at_risk_units}")
                
                if risk_data:
                    current_hash = hashlib.md5("|".join(sorted(risk_data)).encode()).hexdigest()
                
                if current_hash != last_processing.data_hash:
                    change_summary.append(f"Risk scores changed (hash: {current_hash[:8]}...)")
            
            # Determine if changes exist
            has_changes = (
                current_hash != last_processing.data_hash or
                (datetime.now() - last_processing.last_processed_at).days >= 1  # Force refresh after 1 day
            )
            
            if not has_changes:
                change_summary.append("No significant changes detected")
            
            return {
                "has_changes": has_changes,
                "change_summary": "; ".join(change_summary),
                "last_change_date": last_processing.last_processed_at.isoformat(),
                "data_hash": current_hash,
                "previous_hash": last_processing.data_hash
            }
            
        except Exception as e:
            logger.warning(f"Error detecting data changes for {processing_type}: {str(e)}")
            # On error, assume changes exist to be safe
            return {
                "has_changes": True,
                "change_summary": f"Error detecting changes: {str(e)}",
                "last_change_date": None,
                "data_hash": None
            }
        finally:
            db.close()
    
    async def _update_change_tracking(
        self, 
        snapshot_date: date, 
        processing_type: str, 
        records_processed: int,
        data_hash: str = None
    ):
        """
        Update change tracking record after successful processing.
        
        Requirements 7.3, 7.4:
        - Add change detection to avoid full recomputation
        """
        db = SessionLocal()
        try:
            from app.db.models import DataChangeTracking
            
            # Create or update tracking record
            tracking_record = (
                db.query(DataChangeTracking)
                .filter(
                    DataChangeTracking.processing_type == processing_type,
                    DataChangeTracking.snapshot_date == snapshot_date
                )
                .first()
            )
            
            if tracking_record:
                tracking_record.last_processed_at = datetime.now()
                tracking_record.records_processed = records_processed
                tracking_record.data_hash = data_hash
                tracking_record.change_summary = {"records_processed": records_processed}
                tracking_record.updated_at = datetime.now()
            else:
                tracking_record = DataChangeTracking(
                    table_name=f"{processing_type}_data",
                    processing_type=processing_type,
                    snapshot_date=snapshot_date,
                    last_processed_at=datetime.now(),
                    records_processed=records_processed,
                    data_hash=data_hash,
                    change_summary={"records_processed": records_processed}
                )
                db.add(tracking_record)
            
            db.commit()
            logger.info(f"Updated change tracking for {processing_type} on {snapshot_date}: {records_processed} records")
            
        except Exception as e:
            logger.error(f"Error updating change tracking for {processing_type}: {str(e)}")
            db.rollback()
        finally:
            db.close()
    
    async def _optimize_batch_processing(
        self, 
        processing_function: Callable,
        data_items: List[Any],
        batch_size: int = 1000,
        **kwargs
    ) -> Any:
        """
        Optimize processing of large datasets using batching.
        
        Requirements 7.3, 7.4:
        - Optimize job performance for large datasets
        """
        if len(data_items) <= batch_size:
            # Process all at once if dataset is small
            return await processing_function(data_items, **kwargs)
        
        # Process in batches for large datasets
        results = []
        total_batches = (len(data_items) + batch_size - 1) // batch_size
        
        logger.info(f"Processing {len(data_items)} items in {total_batches} batches of {batch_size}")
        
        for i in range(0, len(data_items), batch_size):
            batch = data_items[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            logger.debug(f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)")
            
            try:
                batch_result = await processing_function(batch, **kwargs)
                results.append(batch_result)
                
                # Small delay between batches to prevent overwhelming the database
                if batch_num < total_batches:
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Error processing batch {batch_num}: {str(e)}")
                raise
        
        return results
        """
        Get overall system health metrics for job processing.
        
        Requirements 7.2:
        - Create comprehensive job logging and status reporting
        """
        db = SessionLocal()
        try:
            # Get recent executions (last 24 hours)
            cutoff_date = datetime.now() - timedelta(hours=24)
            
            recent_executions = (
                db.query(JobExecution)
                .filter(JobExecution.created_at >= cutoff_date)
                .all()
            )
            
            # Calculate system-wide metrics
            total_jobs = len(recent_executions)
            successful_jobs = sum(1 for e in recent_executions if e.status == JobStatus.COMPLETED.value)
            failed_jobs = sum(1 for e in recent_executions if e.status == JobStatus.FAILED.value)
            running_jobs = len(self.running_jobs)
            
            # Get job type breakdown
            job_type_stats = {}
            for execution in recent_executions:
                job_type = execution.job_type
                if job_type not in job_type_stats:
                    job_type_stats[job_type] = {"total": 0, "successful": 0, "failed": 0}
                
                job_type_stats[job_type]["total"] += 1
                if execution.status == JobStatus.COMPLETED.value:
                    job_type_stats[job_type]["successful"] += 1
                elif execution.status == JobStatus.FAILED.value:
                    job_type_stats[job_type]["failed"] += 1
            
            # Calculate success rates by job type
            for job_type, stats in job_type_stats.items():
                if stats["total"] > 0:
                    stats["success_rate"] = round((stats["successful"] / stats["total"]) * 100, 2)
                else:
                    stats["success_rate"] = 0.0
            
            return {
                "timestamp": datetime.now().isoformat(),
                "period_hours": 24,
                "overall_stats": {
                    "total_executions": total_jobs,
                    "successful_executions": successful_jobs,
                    "failed_executions": failed_jobs,
                    "currently_running": running_jobs,
                    "overall_success_rate": round((successful_jobs / total_jobs * 100) if total_jobs > 0 else 0, 2)
                },
                "job_type_breakdown": job_type_stats,
                "registered_jobs": len(self.jobs),
                "enabled_jobs": sum(1 for job in self.jobs.values() if job.enabled)
            }
        finally:
            db.close()


# Global scheduler instance
scheduler = JobScheduler()