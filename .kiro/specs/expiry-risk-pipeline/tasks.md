# Implementation Plan: Expiry Risk Pipeline

## Overview

This implementation plan builds on the existing FastAPI backend foundation to complete ThePerfectShop's expiry risk management system. The plan focuses on adding missing components (actions service, KPIs service, UI) while enhancing existing services to match the design specifications.

## Tasks

- [x] 1. Update project branding and enhance existing services
  - Update project name from "ExpiryShield" to "ThePerfectShop" in main.py
  - Add missing master data tables (store_master, sku_master) to models.py
  - Enhance validation service with detailed error reporting
  - Add comprehensive error handling to upload routes
  - _Requirements: 1.1, 1.3, 1.4, 1.7_

- [x] 1.1 Write property tests for data ingestion
  - **Property 1: File validation completeness**
  - **Property 2: Column mapping consistency**
  - **Property 3: Duplicate handling preservation**
  - **Property 4: Date parsing robustness**
  - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7**

- [ ]* 2. Implement Actions Service and API routes
  - Create actions service with transfer and markdown recommendation logic
  - Add action management (approve, reject, complete) functionality
  - Create API routes for action generation and management
  - Add action models and database tables
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [ ]* 2.1 Write property tests for action generation
  - **Property 13: Transfer capacity constraints**
  - **Property 14: Transfer savings calculation**
  - **Property 15: Action prioritization ordering**
  - **Property 16: Discount percentage mapping**
  - **Property 17: Markdown savings calculation**
  - **Property 18: Action creation consistency**
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6**

- [ ]* 2.2 Write property tests for action management
  - **Property 19: Status transition validity**
  - **Property 20: Audit trail completeness**
  - **Property 21: Outcome tracking consistency**
  - **Validates: Requirements 6.2, 6.3, 6.4, 6.5, 6.6**

- [ ]* 3. Implement KPIs Service and dashboard API
  - Create KPIs service for calculating savings metrics and performance indicators
  - Add API routes for retrieving KPI data with filtering
  - Implement aggregation functions for at-risk value and savings tracking
  - Add time-based filtering and trend analysis
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [ ]* 3.1 Write property tests for KPI calculations
  - **Property 22: At-risk value aggregation**
  - **Property 23: Savings aggregation accuracy**
  - **Property 24: Time-based filtering consistency**
  - **Validates: Requirements 7.1, 7.2, 7.3**

- [ ] 4. Enhance existing services with missing functionality
  - Add data completeness detection to features service
  - Enhance risk scoring with monotonicity and bounds checking
  - Add cost fallback logic for missing unit costs
  - Improve velocity calculation with insufficient data handling
  - _Requirements: 2.3, 3.4, 3.5, 3.6_

- [ ]* 4.1 Write property tests for enhanced features and scoring
  - **Property 5: Velocity calculation accuracy**
  - **Property 6: Volatility calculation correctness**
  - **Property 7: Data completeness detection**
  - **Property 8: Feature storage round-trip**
  - **Property 9: Risk calculation mathematical correctness**
  - **Property 10: Risk score monotonicity**
  - **Property 11: Risk score bounds**
  - **Property 12: Cost fallback logic**
  - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

- [ ] 5. Checkpoint - Ensure all backend services are working
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 6. Create Streamlit UI application
  - Set up Streamlit application structure in ui/ directory
  - Create file upload interface with drag-and-drop support
  - Build Risk Inbox page with filtering capabilities
  - Implement Action Queue interface for action management
  - Create Savings Dashboard with key metrics visualization
  - Add Data Health status page
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [ ]* 6.1 Write unit tests for UI components
  - Test file upload functionality
  - Test filtering and display logic
  - Test action management workflows
  - **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**

- [ ]* 7. Implement daily pipeline automation
  - Create pipeline script for daily feature building, risk scoring, and action generation
  - Add demo data generator for testing and demonstrations
  - Set up scheduling mechanism (cron or GitHub Actions)
  - Add pipeline monitoring and error handling
  - _Requirements: 2.5, 3.7_

- [ ]* 7.1 Write integration tests for pipeline
  - Test end-to-end pipeline execution
  - Test error handling and recovery
  - Test data consistency across pipeline stages

- [ ]* 8. Add comprehensive API enhancements
  - Enhance API with proper pagination support
  - Add comprehensive request validation and error responses
  - Implement filtering for all API endpoints
  - Add API documentation with OpenAPI/Swagger
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

- [ ]* 8.1 Write property tests for API behavior
  - **Property 25: API response structure consistency**
  - **Property 26: API validation completeness**
  - **Property 27: Pagination correctness**
  - **Property 28: Filter application consistency**
  - **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 9.2, 9.3, 9.4, 9.5**

- [ *] 9. Final integration and deployment preparation
  - Create Docker configuration for easy deployment
  - Add comprehensive logging throughout the application
  - Create database migration scripts
  - Add configuration management for different environments
  - Set up Redis caching for performance optimization

- [ ]* 10. Final checkpoint - Complete system validation
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The implementation builds on existing code rather than starting from scratch