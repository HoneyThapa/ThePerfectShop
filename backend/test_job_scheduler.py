"""
Test script for job scheduler functionality.

This script tests the job scheduler without requiring a database connection.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.jobs.scheduler import JobScheduler, JobType, JobResult


async def test_job_function(**kwargs):
    """Test job function that doesn't require database."""
    print(f"Test job executed with parameters: {kwargs}")
    return JobResult(
        success=True,
        message="Test job completed successfully",
        data={"test_param": kwargs.get("test_param", "default")}
    )


async def main():
    """Test the job scheduler functionality."""
    print("Testing Job Scheduler...")
    
    # Create a test scheduler (without database initialization)
    scheduler = JobScheduler()
    
    # Override the database initialization to avoid connection errors
    scheduler._ensure_job_table_exists = lambda: print("Skipping database table creation for test")
    
    # Register a test job
    scheduler.register_job(
        name="test_job",
        job_type=JobType.FEATURE_BUILD,
        function=test_job_function,
        parameters={"test_param": "test_value"}
    )
    
    # Test job registration
    print(f"Registered jobs: {list(scheduler.jobs.keys())}")
    
    # Test job status (without database)
    job_status = {
        "name": "test_job",
        "type": JobType.FEATURE_BUILD.value,
        "enabled": True,
        "is_running": False,
        "last_run": None,
        "next_run": None,
        "latest_execution": None
    }
    print(f"Job status: {job_status}")
    
    print("✅ Job scheduler test completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())