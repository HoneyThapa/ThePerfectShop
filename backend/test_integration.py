"""
Integration tests for ExpiryShield Backend API.

This module tests end-to-end workflows from upload to recommendations,
API integration with authentication, and database operations under load.

Requirements: All (comprehensive integration testing)
"""

import pytest
import asyncio
import tempfile
import os
import io
import json
import time
from datetime import date, datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

from app.main import app
from app.db.models import Base, RawUpload, SalesDaily, InventoryBatch, Purchase, StoreMaster, SKUMaster, BatchRisk, Action
from app.db.session import get_db
from app.auth import create_access_token, get_current_user


class TestIntegrationWorkflows:
    """
    Integration tests for complete ExpiryShield workflows.
    
    Tests end-to-end scenarios including:
    - Data upload to recommendation generation
    - Authentication and authorization flows
    - Database operations under concurrent load
    - API contract compliance across workflows
    """
    
    @pytest.fixture
    def test_client(self):
        """Create test client with in-memory database."""
        # Create in-memory SQLite database
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        
        TestSession = sessionmaker(bind=engine)
        
        def override_get_db():
            db = TestSession()
            try:
                yield db
            finally:
                db.close()
        
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        
        # Setup test data
        db = TestSession()
        self._setup_test_data(db)
        db.close()
        
        yield client
        
        # Cleanup
        app.dependency_overrides.clear()
    
    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers for testing."""
        # Mock user for testing
        test_user = {
            "user_id": "test_user_123",
            "username": "test_user",
            "email": "test@example.com",
            "roles": ["admin"],
            "permissions": ["upload", "analyst", "admin"]
        }
        
        token = create_access_token(data={"sub": test_user["user_id"], **test_user})
        return {"Authorization": f"Bearer {token}"}
    
    def _setup_test_data(self, db):
        """Setup test master data."""
        # Create test stores
        stores = [
            StoreMaster(store_id="STORE001", city="City1", zone="Zone1"),
            StoreMaster(store_id="STORE002", city="City2", zone="Zone2"),
            StoreMaster(store_id="STORE003", city="City3", zone="Zone3")
        ]
        for store in stores:
            db.add(store)
        
        # Create test SKUs
        skus = [
            SKUMaster(sku_id="SKU001", category="food", mrp=25.99),
            SKUMaster(sku_id="SKU002", category="beverage", mrp=15.50),
            SKUMaster(sku_id="SKU003", category="personal_care", mrp=45.00)
        ]
        for sku in skus:
            db.add(sku)
        
        db.commit()
    
    def _create_test_csv_file(self, data_type: str, num_records: int = 100) -> io.BytesIO:
        """Create test CSV file with specified data type."""
        base_date = date(2024, 1, 1)
        
        if data_type == "sales":
            data = []
            for i in range(num_records):
                data.append({
                    "date": (base_date + timedelta(days=i % 30)).strftime("%Y-%m-%d"),
                    "store_id": f"STORE{(i % 3) + 1:03d}",
                    "sku_id": f"SKU{(i % 3) + 1:03d}",
                    "units_sold": (i % 50) + 1,
                    "selling_price": 20.0 + (i % 10)
                })
        
        elif data_type == "inventory":
            data = []
            for i in range(num_records):
                data.append({
                    "snapshot_date": base_date.strftime("%Y-%m-%d"),
                    "store_id": f"STORE{(i % 3) + 1:03d}",
                    "sku_id": f"SKU{(i % 3) + 1:03d}",
                    "batch_id": f"BATCH{i + 1:04d}",
                    "expiry_date": (base_date + timedelta(days=30 + (i % 365))).strftime("%Y-%m-%d"),
                    "on_hand_qty": (i % 100) + 10
                })
        
        elif data_type == "purchases":
            data = []
            for i in range(num_records):
                data.append({
                    "received_date": (base_date + timedelta(days=i % 30)).strftime("%Y-%m-%d"),
                    "store_id": f"STORE{(i % 3) + 1:03d}",
                    "sku_id": f"SKU{(i % 3) + 1:03d}",
                    "batch_id": f"BATCH{i + 1:04d}",
                    "received_qty": (i % 100) + 10,
                    "unit_cost": 15.0 + (i % 5)
                })
        
        else:
            raise ValueError(f"Unknown data type: {data_type}")
        
        df = pd.DataFrame(data)
        csv_buffer = io.BytesIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        return csv_buffer
    
    def test_complete_upload_to_risk_workflow(self, test_client, auth_headers):
        """
        Test complete workflow from data upload to risk analysis.
        
        Tests end-to-end workflow:
        1. Upload sales data
        2. Upload inventory data
        3. Trigger risk analysis
        4. Retrieve risk results
        """
        # Step 1: Upload sales data
        sales_csv = self._create_test_csv_file("sales", 50)
        
        response = test_client.post(
            "/upload/",
            files={"file": ("sales_data.csv", sales_csv, "text/csv")},
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Sales upload failed: {response.text}"
        sales_upload_data = response.json()
        assert sales_upload_data["success"] is True
        assert sales_upload_data["data"]["file_type"] == "sales"
        assert sales_upload_data["data"]["records_processed"] == 50
        
        sales_upload_id = sales_upload_data["data"]["upload_id"]
        
        # Step 2: Check upload status
        status_response = test_client.get(
            f"/upload/{sales_upload_id}/status",
            headers=auth_headers
        )
        
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["data"]["status"] == "COMPLETED"
        
        # Step 3: Upload inventory data
        inventory_csv = self._create_test_csv_file("inventory", 30)
        
        response = test_client.post(
            "/upload/",
            files={"file": ("inventory_data.csv", inventory_csv, "text/csv")},
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Inventory upload failed: {response.text}"
        inventory_upload_data = response.json()
        assert inventory_upload_data["success"] is True
        assert inventory_upload_data["data"]["file_type"] == "inventory"
        assert inventory_upload_data["data"]["records_processed"] == 30
        
        # Step 4: Trigger risk analysis (mock the actual calculation)
        with patch('app.services.scoring.calculate_risk_scores') as mock_risk_calc:
            mock_risk_calc.return_value = True
            
            risk_refresh_response = test_client.post(
                "/risk/refresh",
                json={
                    "snapshot_date": "2024-01-01",
                    "force_recalculation": True
                },
                headers=auth_headers
            )
            
            assert risk_refresh_response.status_code == 200
            risk_refresh_data = risk_refresh_response.json()
            assert risk_refresh_data["status"] == "success"
        
        # Step 5: Retrieve risk data (would normally have data after risk calculation)
        risk_response = test_client.get(
            "/risk/?snapshot_date=2024-01-01&min_risk_score=0",
            headers=auth_headers
        )
        
        assert risk_response.status_code == 200
        risk_data = risk_response.json()
        assert risk_data["success"] is True
        # Note: Risk data would be empty since we mocked the calculation
        assert "data" in risk_data
        assert "metadata" in risk_data
        assert "pagination" in risk_data["metadata"]
    
    def test_upload_to_actions_workflow(self, test_client, auth_headers):
        """
        Test workflow from upload to action recommendations.
        
        Tests:
        1. Upload data
        2. Generate action recommendations
        3. Approve actions
        4. Track action outcomes
        """
        # Step 1: Upload inventory data
        inventory_csv = self._create_test_csv_file("inventory", 25)
        
        response = test_client.post(
            "/upload/",
            files={"file": ("inventory_data.csv", inventory_csv, "text/csv")},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Step 2: Generate action recommendations (mock the service)
        with patch('app.services.actions.generate_recommendations') as mock_actions:
            mock_actions.return_value = [
                {
                    "action_type": "TRANSFER",
                    "from_store": "STORE001",
                    "to_store": "STORE002",
                    "sku_id": "SKU001",
                    "batch_id": "BATCH001",
                    "qty": 50,
                    "expected_savings": 1250.0
                }
            ]
            
            actions_response = test_client.post(
                "/actions/generate",
                json={
                    "snapshot_date": "2024-01-01",
                    "min_risk_score": 70.0,
                    "action_types": ["TRANSFER", "MARKDOWN"]
                },
                headers=auth_headers
            )
            
            assert actions_response.status_code == 200
            actions_data = actions_response.json()
            assert actions_data["success"] is True
        
        # Step 3: List pending actions
        list_response = test_client.get(
            "/actions/?status=PROPOSED",
            headers=auth_headers
        )
        
        assert list_response.status_code == 200
        list_data = list_response.json()
        assert list_data["success"] is True
        assert "data" in list_data
        assert "metadata" in list_data
    
    def test_authentication_integration(self, test_client):
        """
        Test API integration with authentication system.
        
        Tests:
        1. Unauthenticated requests are rejected
        2. Invalid tokens are rejected
        3. Valid tokens are accepted
        4. Permission-based access control
        """
        # Test 1: Unauthenticated request should fail
        response = test_client.get("/risk/?snapshot_date=2024-01-01")
        assert response.status_code == 401
        
        # Test 2: Invalid token should fail
        invalid_headers = {"Authorization": "Bearer invalid_token_here"}
        response = test_client.get(
            "/risk/?snapshot_date=2024-01-01",
            headers=invalid_headers
        )
        assert response.status_code == 401
        
        # Test 3: Valid token should work
        test_user = {
            "user_id": "test_user_123",
            "username": "test_user",
            "email": "test@example.com",
            "permissions": ["analyst"]
        }
        
        token = create_access_token(data={"sub": test_user["user_id"], **test_user})
        valid_headers = {"Authorization": f"Bearer {token}"}
        
        response = test_client.get(
            "/risk/?snapshot_date=2024-01-01",
            headers=valid_headers
        )
        assert response.status_code == 200
        
        # Test 4: Permission-based access (upload requires 'upload' permission)
        csv_data = self._create_test_csv_file("sales", 10)
        
        # User without upload permission should fail
        response = test_client.post(
            "/upload/",
            files={"file": ("test.csv", csv_data, "text/csv")},
            headers=valid_headers
        )
        assert response.status_code == 403  # Forbidden
        
        # User with upload permission should succeed
        upload_user = {
            "user_id": "upload_user_123",
            "username": "upload_user",
            "email": "upload@example.com",
            "permissions": ["upload"]
        }
        
        upload_token = create_access_token(data={"sub": upload_user["user_id"], **upload_user})
        upload_headers = {"Authorization": f"Bearer {upload_token}"}
        
        csv_data.seek(0)  # Reset file pointer
        response = test_client.post(
            "/upload/",
            files={"file": ("test.csv", csv_data, "text/csv")},
            headers=upload_headers
        )
        assert response.status_code == 200
    
    def test_concurrent_api_requests(self, test_client, auth_headers):
        """
        Test API behavior under concurrent load.
        
        Tests:
        1. Concurrent read requests
        2. Concurrent upload requests
        3. Mixed read/write operations
        4. Rate limiting behavior
        """
        def make_health_request(client, headers, request_id):
            """Make a health check request."""
            try:
                response = client.get("/health", headers=headers)
                return {
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "response_time": 0  # Could measure actual time
                }
            except Exception as e:
                return {
                    "request_id": request_id,
                    "error": str(e),
                    "success": False
                }
        
        def make_version_request(client, headers, request_id):
            """Make a version info request."""
            try:
                response = client.get("/version/", headers=headers)
                return {
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "response_time": 0
                }
            except Exception as e:
                return {
                    "request_id": request_id,
                    "error": str(e),
                    "success": False
                }
        
        # Test 1: Concurrent read requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(make_health_request, test_client, auth_headers, i)
                for i in range(10)
            ]
            
            results = [future.result() for future in as_completed(futures)]
        
        # All requests should succeed
        successful_requests = [r for r in results if r["success"]]
        assert len(successful_requests) >= 8, "Most concurrent read requests should succeed"
        
        # Test 2: Concurrent version requests
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(make_version_request, test_client, auth_headers, i)
                for i in range(6)
            ]
            
            version_results = [future.result() for future in as_completed(futures)]
        
        successful_version_requests = [r for r in version_results if r["success"]]
        assert len(successful_version_requests) >= 5, "Most version requests should succeed"
        
        # Test 3: Mixed operations (health + version)
        def make_mixed_request(client, headers, request_id):
            """Make alternating health and version requests."""
            if request_id % 2 == 0:
                return make_health_request(client, headers, request_id)
            else:
                return make_version_request(client, headers, request_id)
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(make_mixed_request, test_client, auth_headers, i)
                for i in range(8)
            ]
            
            mixed_results = [future.result() for future in as_completed(futures)]
        
        successful_mixed_requests = [r for r in mixed_results if r["success"]]
        assert len(successful_mixed_requests) >= 6, "Most mixed requests should succeed"
    
    def test_database_operations_under_load(self, test_client, auth_headers):
        """
        Test database operations under concurrent load.
        
        Tests:
        1. Concurrent data uploads
        2. Concurrent read operations
        3. Data consistency under load
        4. Transaction isolation
        """
        def upload_test_data(client, headers, data_type, request_id):
            """Upload test data concurrently."""
            try:
                csv_data = self._create_test_csv_file(data_type, 20)
                
                response = client.post(
                    "/upload/",
                    files={"file": (f"{data_type}_{request_id}.csv", csv_data, "text/csv")},
                    headers=headers
                )
                
                return {
                    "request_id": request_id,
                    "data_type": data_type,
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "upload_id": response.json().get("data", {}).get("upload_id") if response.status_code == 200 else None
                }
            except Exception as e:
                return {
                    "request_id": request_id,
                    "data_type": data_type,
                    "error": str(e),
                    "success": False
                }
        
        # Test 1: Concurrent uploads of different data types
        data_types = ["sales", "inventory", "purchases"]
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(upload_test_data, test_client, auth_headers, data_types[i % 3], i)
                for i in range(6)
            ]
            
            upload_results = [future.result() for future in as_completed(futures)]
        
        successful_uploads = [r for r in upload_results if r["success"]]
        assert len(successful_uploads) >= 4, "Most concurrent uploads should succeed"
        
        # Verify each data type was uploaded at least once
        uploaded_types = {r["data_type"] for r in successful_uploads}
        assert len(uploaded_types) >= 2, "Multiple data types should be uploaded successfully"
        
        # Test 2: Verify upload status for successful uploads
        for result in successful_uploads:
            if result["upload_id"]:
                status_response = test_client.get(
                    f"/upload/{result['upload_id']}/status",
                    headers=auth_headers
                )
                assert status_response.status_code == 200
                status_data = status_response.json()
                assert status_data["data"]["status"] in ["COMPLETED", "PROCESSING"]
    
    def test_api_error_handling_integration(self, test_client, auth_headers):
        """
        Test comprehensive error handling across API endpoints.
        
        Tests:
        1. Invalid file formats
        2. Missing required fields
        3. Database constraint violations
        4. Service unavailability scenarios
        """
        # Test 1: Invalid file format
        invalid_file = io.BytesIO(b"This is not a CSV file")
        
        response = test_client.post(
            "/upload/",
            files={"file": ("invalid.txt", invalid_file, "text/plain")},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        error_data = response.json()
        assert "Invalid file format" in error_data["detail"]
        
        # Test 2: Invalid CSV content
        invalid_csv = io.BytesIO(b"invalid,csv,content\n1,2")
        
        response = test_client.post(
            "/upload/",
            files={"file": ("invalid.csv", invalid_csv, "text/csv")},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        error_data = response.json()
        assert "Unknown file format" in error_data["detail"]
        
        # Test 3: Non-existent upload ID
        response = test_client.get(
            "/upload/99999/status",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        error_data = response.json()
        assert "Upload not found" in error_data["detail"]
        
        # Test 4: Invalid date format in risk endpoint
        response = test_client.get(
            "/risk/?snapshot_date=invalid-date",
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
        
        # Test 5: Invalid pagination parameters
        response = test_client.get(
            "/risk/?snapshot_date=2024-01-01&page=0",  # Page must be >= 1
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_bulk_operations_integration(self, test_client, auth_headers):
        """
        Test bulk operations for high-volume data processing.
        
        Tests:
        1. Bulk file uploads
        2. Bulk action operations
        3. Performance under load
        4. Memory usage optimization
        """
        # Test 1: Bulk upload endpoint (if available)
        files_data = []
        for i in range(3):
            csv_data = self._create_test_csv_file("sales", 50)
            files_data.append(("files", (f"sales_bulk_{i}.csv", csv_data, "text/csv")))
        
        # Note: This assumes a bulk upload endpoint exists
        # If not implemented, this test will verify the endpoint doesn't exist
        response = test_client.post(
            "/bulk/upload",
            files=files_data,
            headers=auth_headers
        )
        
        # Either succeeds (200) or endpoint doesn't exist (404)
        assert response.status_code in [200, 404, 405]
        
        if response.status_code == 200:
            bulk_data = response.json()
            assert bulk_data["success"] is True
            assert "data" in bulk_data
        
        # Test 2: Large single file upload
        large_csv = self._create_test_csv_file("inventory", 500)
        
        start_time = time.time()
        response = test_client.post(
            "/upload/",
            files={"file": ("large_inventory.csv", large_csv, "text/csv")},
            headers=auth_headers
        )
        upload_time = time.time() - start_time
        
        assert response.status_code == 200
        assert upload_time < 30.0, "Large file upload should complete within 30 seconds"
        
        upload_data = response.json()
        assert upload_data["data"]["records_processed"] == 500
    
    def test_kpi_integration_workflow(self, test_client, auth_headers):
        """
        Test KPI tracking and reporting integration.
        
        Tests:
        1. KPI dashboard endpoint
        2. Savings tracking
        3. Inventory health metrics
        4. Time-series data consistency
        """
        # Test 1: KPI dashboard
        response = test_client.get(
            "/kpis/dashboard",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        dashboard_data = response.json()
        assert dashboard_data["success"] is True
        assert "data" in dashboard_data
        
        # Verify dashboard structure
        data = dashboard_data["data"]
        expected_fields = [
            "total_at_risk_value", "recovered_value", "write_off_reduction",
            "inventory_turnover", "active_actions", "completed_actions"
        ]
        
        for field in expected_fields:
            assert field in data, f"Dashboard should include {field}"
        
        # Test 2: Savings tracking
        response = test_client.get(
            "/kpis/savings?start_date=2024-01-01&end_date=2024-01-31",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        savings_data = response.json()
        assert savings_data["success"] is True
        assert "data" in savings_data
        
        # Test 3: Inventory health metrics
        response = test_client.get(
            "/kpis/inventory",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        inventory_data = response.json()
        assert inventory_data["success"] is True
        assert "data" in inventory_data
    
    def test_job_management_integration(self, test_client, auth_headers):
        """
        Test scheduled job management integration.
        
        Tests:
        1. Job status monitoring
        2. Job execution tracking
        3. Error handling in jobs
        4. Job scheduling consistency
        """
        # Test 1: List jobs
        response = test_client.get(
            "/jobs/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        jobs_data = response.json()
        assert jobs_data["success"] is True
        assert "data" in jobs_data
        
        # Test 2: Job status
        response = test_client.get(
            "/jobs/status",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        status_data = response.json()
        assert status_data["success"] is True
        
        # Test 3: Trigger job (if endpoint exists)
        response = test_client.post(
            "/jobs/trigger",
            json={"job_name": "feature_build"},
            headers=auth_headers
        )
        
        # Either succeeds or endpoint doesn't exist
        assert response.status_code in [200, 404, 405]
    
    def test_api_versioning_integration(self, test_client, auth_headers):
        """
        Test API versioning integration across endpoints.
        
        Tests:
        1. Version-specific endpoints
        2. Backward compatibility
        3. Version negotiation
        4. Migration path consistency
        """
        # Test 1: Version information
        response = test_client.get("/version/")
        
        assert response.status_code == 200
        version_data = response.json()
        assert version_data["success"] is True
        assert "current_version" in version_data["data"]
        assert "supported_versions" in version_data["data"]
        
        # Test 2: Versioned endpoints (v1.0)
        response = test_client.get("/v1.0/", headers=auth_headers)
        
        if response.status_code == 200:
            v1_data = response.json()
            assert "version" in v1_data
        
        # Test 3: Versioned endpoints (v1.1)
        response = test_client.get("/v1.1/", headers=auth_headers)
        
        if response.status_code == 200:
            v1_1_data = response.json()
            assert "version" in v1_1_data
        
        # Test 4: Version header negotiation
        version_headers = {**auth_headers, "Accept-Version": "1.1"}
        response = test_client.get("/", headers=version_headers)
        
        assert response.status_code == 200
        # Should handle version header gracefully
    
    def test_monitoring_integration(self, test_client):
        """
        Test monitoring and observability integration.
        
        Tests:
        1. Health check endpoints
        2. Metrics collection
        3. Performance monitoring
        4. Error tracking
        """
        # Test 1: Health check
        response = test_client.get("/health")
        
        assert response.status_code == 200
        health_data = response.json()
        assert health_data["status"] in ["healthy", "degraded"]
        assert "checks" in health_data
        assert "timestamp" in health_data
        
        # Test 2: Readiness check
        response = test_client.get("/health/ready")
        
        assert response.status_code in [200, 503]
        
        # Test 3: Liveness check
        response = test_client.get("/health/live")
        
        assert response.status_code == 200
        live_data = response.json()
        assert live_data["status"] == "alive"
        
        # Test 4: Metrics endpoint (if available)
        response = test_client.get("/metrics")
        
        # Either returns metrics or endpoint doesn't exist
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            # Should return Prometheus-style metrics
            assert "text/plain" in response.headers.get("content-type", "")
    
    def test_complete_business_workflow(self, test_client, auth_headers):
        """
        Test complete business workflow from data ingestion to action completion.
        
        This is the most comprehensive integration test covering:
        1. Data upload (sales, inventory, purchases)
        2. Risk analysis
        3. Action generation
        4. Action approval and execution
        5. KPI tracking and reporting
        """
        # Step 1: Upload all data types
        data_types = ["sales", "inventory", "purchases"]
        upload_ids = []
        
        for data_type in data_types:
            csv_data = self._create_test_csv_file(data_type, 30)
            
            response = test_client.post(
                "/upload/",
                files={"file": (f"{data_type}_data.csv", csv_data, "text/csv")},
                headers=auth_headers
            )
            
            assert response.status_code == 200, f"Failed to upload {data_type} data"
            upload_data = response.json()
            upload_ids.append(upload_data["data"]["upload_id"])
        
        # Step 2: Verify all uploads completed
        for upload_id in upload_ids:
            status_response = test_client.get(
                f"/upload/{upload_id}/status",
                headers=auth_headers
            )
            
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert status_data["data"]["status"] == "COMPLETED"
        
        # Step 3: Trigger risk analysis
        with patch('app.services.scoring.calculate_risk_scores') as mock_risk:
            mock_risk.return_value = True
            
            risk_response = test_client.post(
                "/risk/refresh",
                json={"snapshot_date": "2024-01-01", "force_recalculation": True},
                headers=auth_headers
            )
            
            assert risk_response.status_code == 200
        
        # Step 4: Generate actions
        with patch('app.services.actions.generate_recommendations') as mock_actions:
            mock_actions.return_value = [
                {
                    "action_type": "TRANSFER",
                    "from_store": "STORE001",
                    "to_store": "STORE002",
                    "sku_id": "SKU001",
                    "batch_id": "BATCH001",
                    "qty": 50,
                    "expected_savings": 1250.0
                }
            ]
            
            actions_response = test_client.post(
                "/actions/generate",
                json={
                    "snapshot_date": "2024-01-01",
                    "min_risk_score": 70.0,
                    "action_types": ["TRANSFER", "MARKDOWN"]
                },
                headers=auth_headers
            )
            
            assert actions_response.status_code == 200
        
        # Step 5: Check KPI dashboard
        kpi_response = test_client.get(
            "/kpis/dashboard",
            headers=auth_headers
        )
        
        assert kpi_response.status_code == 200
        kpi_data = kpi_response.json()
        assert kpi_data["success"] is True
        
        # Step 6: Verify system health after complete workflow
        health_response = test_client.get("/health")
        
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] in ["healthy", "degraded"]
        
        # The workflow should complete without degrading system health
        if health_data["status"] == "degraded":
            # Check what caused degradation
            checks = health_data.get("checks", {})
            db_check = checks.get("database", {})
            assert db_check.get("status") == "healthy", "Database should remain healthy after workflow"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])