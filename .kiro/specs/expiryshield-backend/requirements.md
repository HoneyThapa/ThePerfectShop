# Requirements Document

## Introduction

The ExpiryShield backend is a FastAPI-based REST service that provides the core business logic and data operations for the inventory expiry prevention system. It handles data ingestion from CSV/Excel uploads, performs risk analysis, generates action recommendations, and tracks performance metrics. The backend interfaces with a PostgreSQL database and provides APIs for the frontend team while consuming ML predictions from the data science team.

## Glossary

- **Backend_API**: The FastAPI-based REST service that handles all business logic and data operations
- **Batch**: A specific lot of inventory with a unique identifier and expiry date
- **Risk_Score**: A 0-100 numerical value indicating probability that a batch will expire before selling
- **Action_Engine**: The system component that generates transfer, markdown, and liquidation recommendations
- **Data_Ingestion**: The process of accepting and validating CSV/Excel uploads from client systems
- **Store**: A physical or virtual location where inventory is held and sold
- **SKU**: Stock Keeping Unit - a unique identifier for a product variant

## Requirements

### Requirement 1: Data Upload and Validation

**User Story:** As a store manager, I want to upload sales and inventory data from my POS system, so that the system can analyze expiry risks.

#### Acceptance Criteria

1. WHEN a user uploads a CSV or Excel file, THE Backend_API SHALL validate the file format and required columns
2. WHEN required columns are missing or incorrectly named, THE Backend_API SHALL return a detailed validation report with mapping suggestions
3. WHEN data contains invalid dates or negative quantities, THE Backend_API SHALL flag these issues and continue processing valid records
4. WHEN upload is successful, THE Backend_API SHALL store raw data and return an upload confirmation with data health metrics
5. THE Backend_API SHALL support column mapping for common variations like "SKU Code" vs "sku_id"

### Requirement 2: Risk Analysis and Scoring

**User Story:** As a supply chain manager, I want to see which inventory batches are at risk of expiring, so that I can take preventive action.

#### Acceptance Criteria

1. WHEN inventory data is processed, THE Backend_API SHALL calculate days to expiry for each batch
2. WHEN sales velocity is computed, THE Backend_API SHALL use rolling 7, 14, and 30-day averages per store-SKU combination
3. WHEN risk scoring runs, THE Backend_API SHALL predict expected sales before expiry and identify at-risk quantities
4. THE Backend_API SHALL assign risk scores from 0-100 based on at-risk units and days to expiry
5. WHEN risk analysis completes, THE Backend_API SHALL store results and make them available via API endpoints

### Requirement 3: Action Recommendations

**User Story:** As a store manager, I want specific recommendations on what to do with at-risk inventory, so that I can minimize losses.

#### Acceptance Criteria

1. WHEN high-risk batches are identified, THE Action_Engine SHALL generate transfer recommendations to faster-moving stores
2. WHEN transfers are not viable, THE Action_Engine SHALL calculate optimal markdown percentages and expected clearance rates
3. WHEN neither transfer nor markdown is effective, THE Action_Engine SHALL recommend liquidation with recovery estimates
4. THE Backend_API SHALL rank all recommendations by expected savings and feasibility
5. WHEN actions are approved and executed, THE Backend_API SHALL track outcomes and measure actual savings

### Requirement 4: Performance Tracking and KPIs

**User Story:** As a business owner, I want to see how much money the system has saved, so that I can measure ROI.

#### Acceptance Criteria

1. THE Backend_API SHALL calculate total at-risk inventory value across all stores and categories
2. WHEN actions are completed, THE Backend_API SHALL measure recovered value and prevented losses
3. THE Backend_API SHALL track key metrics including write-off reduction, inventory turnover improvement, and cash freed
4. WHEN KPI reports are requested, THE Backend_API SHALL provide time-series data for trend analysis
5. THE Backend_API SHALL maintain audit trails for all actions and their financial outcomes

### Requirement 5: Database Operations and Data Management

**User Story:** As a system administrator, I want reliable data storage and retrieval, so that the system performs consistently.

#### Acceptance Criteria

1. THE Backend_API SHALL store raw uploaded data separately from processed clean data
2. WHEN database operations fail, THE Backend_API SHALL handle errors gracefully and provide meaningful error messages
3. THE Backend_API SHALL support database migrations for schema updates
4. WHEN concurrent requests occur, THE Backend_API SHALL handle them safely without data corruption
5. THE Backend_API SHALL implement proper indexing for fast queries on large datasets

### Requirement 6: API Security and Authentication

**User Story:** As a security administrator, I want to ensure only authorized users can access sensitive inventory data, so that business information remains protected.

#### Acceptance Criteria

1. THE Backend_API SHALL require authentication for all non-health-check endpoints
2. WHEN invalid credentials are provided, THE Backend_API SHALL return appropriate HTTP status codes and error messages
3. THE Backend_API SHALL implement rate limiting to prevent abuse
4. WHEN sensitive data is logged, THE Backend_API SHALL mask or exclude confidential information
5. THE Backend_API SHALL validate all input parameters to prevent injection attacks

### Requirement 7: Scheduled Processing and Automation

**User Story:** As a system operator, I want the system to automatically process data and generate recommendations, so that users always have up-to-date insights.

#### Acceptance Criteria

1. THE Backend_API SHALL support scheduled execution of feature building, risk scoring, and action generation
2. WHEN scheduled jobs fail, THE Backend_API SHALL log errors and provide status information
3. THE Backend_API SHALL process incremental data updates without full recomputation when possible
4. WHEN processing completes, THE Backend_API SHALL update all dependent calculations and notify relevant systems
5. THE Backend_API SHALL provide job status and progress information via API endpoints

### Requirement 8: Integration and Data Exchange

**User Story:** As a technical integrator, I want well-documented APIs that can integrate with existing systems, so that ExpiryShield fits into current workflows.

#### Acceptance Criteria

1. THE Backend_API SHALL provide OpenAPI/Swagger documentation for all endpoints
2. WHEN external systems request data, THE Backend_API SHALL return responses in consistent JSON format
3. THE Backend_API SHALL support bulk operations for efficient data exchange
4. WHEN API versions change, THE Backend_API SHALL maintain backward compatibility or provide clear migration paths
5. THE Backend_API SHALL include proper HTTP status codes and error handling for all operations