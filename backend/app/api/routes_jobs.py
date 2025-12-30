"""
Job management API routes for ExpiryShield backend.

Provides endpoints for triggering and monitoring scheduled jobs.

Requirements 7.1, 7.5:
- Support scheduled execution of feature building, risk scoring, and action generation
- Provide job status and progress information via API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from app.jobs.scheduler import scheduler, JobResult
from app.auth import get_current_user

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobTriggerRequest(BaseModel):
    """Request model for triggering a job."""
    parameters: Optional[Dict[str, Any]] = None


class JobStatusResponse(BaseModel):
    """Response model for job status."""
    name: str
    type: str
    enabled: bool
    is_running: bool
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    latest_execution: Optional[Dict[str, Any]] = None


class JobExecutionResponse(BaseModel):
    """Response model for job execution result."""
    success: bool
    message: str
    data: Dict[str, Any]
    error: Optional[str] = None


class JobHistoryResponse(BaseModel):
    """Response model for job execution history."""
    id: int
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    result_summary: Optional[Dict[str, Any]] = None


@router.get("/", response_model=List[JobStatusResponse])
async def list_jobs(current_user: dict = Depends(get_current_user)):
    """
    List all registered jobs and their current status.
    
    Requirements 7.5:
    - Provide job status and progress information via API endpoints
    """
    try:
        jobs_status = scheduler.get_all_jobs_status()
        return [JobStatusResponse(**job) for job in jobs_status]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve job status: {str(e)}")


@router.get("/{job_name}", response_model=JobStatusResponse)
async def get_job_status(job_name: str, current_user: dict = Depends(get_current_user)):
    """
    Get detailed status of a specific job.
    
    Requirements 7.5:
    - Provide job status and progress information via API endpoints
    """
    try:
        job_status = scheduler.get_job_status(job_name)
        if not job_status:
            raise HTTPException(status_code=404, detail=f"Job '{job_name}' not found")
        
        return JobStatusResponse(**job_status)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve job status: {str(e)}")


@router.post("/{job_name}/trigger", response_model=JobExecutionResponse)
async def trigger_job(
    job_name: str,
    request: JobTriggerRequest = JobTriggerRequest(),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger execution of a specific job.
    
    Requirements 7.1:
    - Support scheduled execution of feature building, risk scoring, and action generation
    """
    try:
        # Start job execution in background
        result = await scheduler.run_job(job_name, request.parameters)
        
        return JobExecutionResponse(
            success=result.success,
            message=result.message,
            data=result.data,
            error=result.error
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger job: {str(e)}")


@router.get("/{job_name}/history", response_model=List[JobHistoryResponse])
async def get_job_history(
    job_name: str,
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """
    Get execution history for a specific job.
    
    Requirements 7.5:
    - Provide job status and progress information via API endpoints
    """
    try:
        history = scheduler.get_job_history(job_name, limit)
        return [JobHistoryResponse(**exec) for exec in history]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve job history: {str(e)}")


@router.post("/feature-build/trigger", response_model=JobExecutionResponse)
async def trigger_feature_build(
    lookback_days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger feature building job with custom parameters.
    
    Requirements 7.1:
    - Support scheduled execution of feature building, risk scoring, and action generation
    """
    try:
        result = await scheduler.run_job(
            "nightly_feature_build",
            {"lookback_days": lookback_days}
        )
        
        return JobExecutionResponse(
            success=result.success,
            message=result.message,
            data=result.data,
            error=result.error
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger feature build: {str(e)}")


@router.post("/risk-scoring/trigger", response_model=JobExecutionResponse)
async def trigger_risk_scoring(current_user: dict = Depends(get_current_user)):
    """
    Trigger risk scoring job.
    
    Requirements 7.1:
    - Support scheduled execution of feature building, risk scoring, and action generation
    """
    try:
        result = await scheduler.run_job("nightly_risk_scoring")
        
        return JobExecutionResponse(
            success=result.success,
            message=result.message,
            data=result.data,
            error=result.error
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger risk scoring: {str(e)}")


@router.post("/action-generation/trigger", response_model=JobExecutionResponse)
async def trigger_action_generation(
    min_risk_score: float = 50.0,
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger action generation job with custom parameters.
    
    Requirements 7.1:
    - Support scheduled execution of feature building, risk scoring, and action generation
    """
    try:
        result = await scheduler.run_job(
            "nightly_action_generation",
            {"min_risk_score": min_risk_score}
        )
        
        return JobExecutionResponse(
            success=result.success,
            message=result.message,
            data=result.data,
            error=result.error
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger action generation: {str(e)}")


@router.get("/{job_name}/statistics", response_model=Dict[str, Any])
async def get_job_statistics(
    job_name: str,
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """
    Get comprehensive statistics for a specific job.
    
    Requirements 7.2:
    - Create comprehensive job logging and status reporting
    """
    try:
        statistics = scheduler.get_job_statistics(job_name, days)
        return statistics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve job statistics: {str(e)}")


@router.get("/system/health", response_model=Dict[str, Any])
async def get_system_health(current_user: dict = Depends(get_current_user)):
    """
    Get overall system health metrics for job processing.
    
    Requirements 7.2:
    - Create comprehensive job logging and status reporting
    """
    try:
        health_metrics = scheduler.get_system_health()
        return health_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve system health: {str(e)}")


@router.post("/nightly-processing/trigger", response_model=JobExecutionResponse)
async def trigger_nightly_processing(
    full_refresh: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger complete nightly processing pipeline.
    
    Requirements 7.1:
    - Support scheduled execution of feature building, risk scoring, and action generation
    """
    try:
        result = await scheduler.run_job(
            "nightly_full_processing",
            {"full_refresh": full_refresh}
        )
        
        return JobExecutionResponse(
            success=result.success,
            message=result.message,
            data=result.data,
            error=result.error
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger nightly processing: {str(e)}")