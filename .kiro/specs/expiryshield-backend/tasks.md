# Implementation Plan: ExpiryShield Backend

## Overview

This implementation plan breaks down the ExpiryShield backend development into discrete, manageable tasks that build incrementally. Each task focuses on implementing specific API endpoints, business services, and database operations while maintaining clean interfaces with the frontend and ML teams.

## Tasks

### ✅ Already Implemented
- **Core Infrastructure**: FastAPI app, database models, session management
- **File Upload System**: POST /upload endpoint with CSV/Excel support
- **Data Validation**: Column mapping and basic validation
- **Data Ingestion**: Services for loading sales, inventory, and purchase data
- **Feature Calculation**: Rolling velocity calculations (7/14/30 day averages)
- **Risk Scoring**: Basic risk calculation with business rules
- **Risk API**: GET /risk endpoint for retrieving risk data

### 🔧 Remaining Tasks

- [x] 1. Enhance and integrate existing components
  - [x] 1.1 Wire upload routes into main FastAPI app
    - Add upload router to main.py
    - Test file upload functionality end-to-end
    - _Requirements: 1.1, 1.4_

  - [x] 1.2 Wire risk routes into main FastAPI app
    - Add risk router to main.py
    - Test risk retrieval functionality
    - _Requirements: 2.5_

  - [x] 1.3 Add missing database tables and relationships
    - Create store_master and sku_master tables
    - Add actions and action_outcomes tables
    - Set up proper foreign key relationships
    - _Requirements: 5.1_

  - [x] 1.4 Write property test for existing data pipeline

    - **Property 1: Upload Validation Completeness**
    - **Property 2: Risk Scoring Consistency**
    - **Validates: Requirements 1.1-1.5, 2.1-2.5**

- [x] 2. Checkpoint - Ensure existing functionality works
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Implement action recommendation engine
  - [x] 3.1 Create transfer recommendation logic
    - Identify faster-moving stores for transfers
    - Calculate transfer feasibility and costs
    - Estimate expected savings from transfers
    - _Requirements: 3.1_

  - [x] 3.2 Build markdown optimization service
    - Calculate optimal discount percentages
    - Estimate clearance rates and uplift factors
    - Handle markdown constraints and business rules
    - _Requirements: 3.2_

  - [x] 3.3 Implement liquidation recommendation logic
    - Identify batches suitable for liquidation
    - Estimate recovery values and liquidation costs
    - Generate liquidation recommendations as fallback
    - _Requirements: 3.3_

  - [x] 3.4 Create action ranking and API endpoints
    - Rank all recommendations by expected savings
    - Implement POST /actions/generate endpoint
    - Add GET /actions for listing recommendations
    - Create approval and completion endpoints
    - _Requirements: 3.4, 3.5_

  - [x] 3.5 Write property test for action recommendations

    - **Property 3: Action Recommendation Completeness**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

- [x] 4. Implement KPI tracking and reporting system
  - [x] 4.1 Create KPI calculation service
    - Calculate total at-risk inventory values
    - Measure recovered value from completed actions
    - Track write-off reduction and inventory turnover metrics
    - Generate time-series data for trend analysis
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [x] 4.2 Build audit trail and outcome tracking
    - Implement action outcome recording
    - Create comprehensive audit trails
    - Track financial impact measurements
    - _Requirements: 4.5_

  - [x] 4.3 Create KPI API endpoints
    - Implement GET /kpis/dashboard for main metrics
    - Add GET /kpis/savings for savings tracking
    - Create GET /kpis/inventory for inventory health
    - _Requirements: 4.4_

  - [x]* 4.4 Write property test for KPI calculations
    - **Property 4: Metrics Calculation Accuracy**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

- [x] 5. Checkpoint - Ensure core business logic is complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Add missing infrastructure components
  - [x] 6.1 Create Pydantic schemas for API validation
    - Define request/response models for all endpoints
    - Add proper validation and serialization
    - _Requirements: 8.2_

  - [x] 6.2 Set up database migrations with Alembic
    - Initialize Alembic configuration
    - Create migration scripts for existing tables
    - Add migration for new action tables
    - _Requirements: 5.3_

  - [x] 6.3 Add comprehensive error handling
    - Implement global exception handlers
    - Add proper HTTP status codes and error messages
    - Create error logging and monitoring
    - _Requirements: 5.2, 8.5_

  - [x] 6.4 Write property test for data integrity

    - **Property 5: Data Integrity Preservation**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

- [x] 7. Implement security and authentication
  - [x] 7.1 Add authentication middleware
    - Implement JWT token validation
    - Add authentication requirements to protected endpoints
    - Handle authentication errors with proper responses
    - _Requirements: 6.1, 6.2_

  - [x] 7.2 Implement rate limiting and input validation
    - Add rate limiting middleware to prevent abuse
    - Implement comprehensive input validation
    - Add SQL injection and XSS protection
    - _Requirements: 6.3, 6.5_

  - [x] 7.3 Add security logging and data protection
    - Implement secure logging with sensitive data masking
    - Add request/response logging for audit trails
    - Ensure no sensitive data leaks in logs
    - _Requirements: 6.4_

  - [x] 7.4 Write property test for security enforcement

    - **Property 6: Security Enforcement**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**

- [ ] 8. Implement scheduled processing and job management
  - [x] 8.1 Create scheduled job framework
    - Implement job scheduling system for nightly processing
    - Add feature building, risk scoring, and action generation jobs
    - Create job status tracking and monitoring
    - _Requirements: 7.1, 7.5_

  - [x] 8.2 Add job error handling and recovery
    - Implement robust error handling for scheduled jobs
    - Add job retry logic with exponential backoff
    - Create comprehensive job logging and status reporting
    - _Requirements: 7.2_

  - [x] 8.3 Optimize incremental processing
    - Implement incremental data processing where possible
    - Add change detection to avoid full recomputation
    - Optimize job performance for large datasets
    - _Requirements: 7.3, 7.4_

  - [x] 8.4 Write property test for processing reliability

    - **Property 7: Processing Reliability**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**

- [x] 9. Implement API documentation and consistency
  - [x] 9.1 Add OpenAPI documentation
    - Generate comprehensive Swagger/OpenAPI specs
    - Document all endpoints with examples
    - Add request/response schema documentation
    - _Requirements: 8.1_

  - [x] 9.2 Ensure API response consistency
    - Standardize JSON response formats across all endpoints
    - Implement consistent error response structures
    - Add proper HTTP status codes for all operations
    - _Requirements: 8.2, 8.5_

  - [x] 9.3 Add bulk operations support
    - Implement bulk data upload capabilities
    - Add batch processing for large datasets
    - Optimize API performance for high-volume operations
    - _Requirements: 8.3_

  - [x] 9.4 Implement API versioning
    - Add API version management system
    - Ensure backward compatibility for existing endpoints
    - Create migration guides for API changes
    - _Requirements: 8.4_

  - [x] 9.5 Write property test for API contract compliance

    - **Property 8: API Contract Compliance**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**

- [x] 10. Final integration and deployment preparation
  - [x] 10.1 Create deployment configuration
    - Set up Docker containerization
    - Configure environment variables and secrets management
    - Add health check endpoints for monitoring
    - _Requirements: 8.1_

  - [x] 10.2 Add monitoring and observability
    - Implement application metrics collection
    - Add performance monitoring and alerting
    - Create operational dashboards for system health
    - _Requirements: 7.5_

  - [x] 10.3 Write integration tests

    - Test end-to-end workflows from upload to recommendations
    - Test API integration with authentication
    - Test database operations under load
    - _Requirements: All_

- [x] 11. Final checkpoint - Complete system validation
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation and team coordination
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Focus on building APIs that your frontend teammate can integrate with
- Ensure clean interfaces for ML model integration with your data science teammate