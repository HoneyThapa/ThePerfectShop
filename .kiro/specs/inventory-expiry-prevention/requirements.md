# Requirements Document

## Introduction

ExpiryShield is an inventory expiry prevention system that helps businesses reduce waste and dead stock by predicting which batches won't sell in time and automatically recommending transfers, markdowns, and liquidation actions before it's too late.

## Glossary

- **Backend_API**: The FastAPI-based server that handles data ingestion, processing, and action recommendations
- **Batch**: A specific lot of inventory with a unique identifier and expiry date
- **Risk_Score**: A 0-100 probability score indicating likelihood of batch expiry before sale
- **Action_Engine**: The decision system that recommends transfers, markdowns, or liquidation
- **Store**: A retail location or warehouse where inventory is held
- **SKU**: Stock Keeping Unit - a unique product identifier
- **Velocity**: The rate at which a SKU sells (units per day/week)
- **At_Risk_Units**: Quantity of inventory predicted to expire before sale

## Requirements

### Requirement 1: Data Ingestion and Validation

**User Story:** As a store manager, I want to upload messy CSV/Excel files with sales and inventory data, so that the system can process my existing data exports without requiring system integrations.

#### Acceptance Criteria

1. WHEN a user uploads a CSV or Excel file, THE Backend_API SHALL validate the file format and structure
2. WHEN column names don't match expected schema, THE Backend_API SHALL provide intelligent column mapping suggestions
3. WHEN data contains errors or missing values, THE Backend_API SHALL generate a detailed validation report
4. WHEN duplicate records are detected, THE Backend_API SHALL handle them according to configurable rules
5. WHEN file upload is successful, THE Backend_API SHALL store raw data and return upload confirmation with data health metrics

### Requirement 2: Inventory Risk Assessment

**User Story:** As a supply chain manager, I want to identify which inventory batches are at risk of expiring, so that I can take preventive action before losses occur.

#### Acceptance Criteria

1. WHEN inventory data is processed, THE Backend_API SHALL calculate days to expiry for each batch
2. WHEN sales velocity is computed, THE Backend_API SHALL generate rolling averages for 7, 14, and 30-day periods
3. WHEN risk scoring runs, THE Backend_API SHALL predict expected sales before expiry for each batch
4. WHEN at-risk units are identified, THE Backend_API SHALL calculate the monetary value at risk
5. WHEN risk assessment completes, THE Backend_API SHALL generate risk scores from 0-100 for all batches

### Requirement 3: Action Recommendation Engine

**User Story:** As a store manager, I want automated recommendations for handling at-risk inventory, so that I can take specific actions to prevent losses.

#### Acceptance Criteria

1. WHEN a batch is at risk, THE Action_Engine SHALL evaluate transfer opportunities to faster-selling stores
2. WHEN transfer is viable, THE Action_Engine SHALL calculate expected savings minus transfer costs
3. WHEN transfer is not viable, THE Action_Engine SHALL recommend appropriate markdown percentages
4. WHEN markdown is recommended, THE Action_Engine SHALL estimate clearance probability and recovery value
5. WHEN liquidation is the best option, THE Action_Engine SHALL calculate expected recovery value

### Requirement 4: Action Management and Tracking

**User Story:** As a supply chain manager, I want to approve, track, and measure the outcomes of recommended actions, so that I can validate the system's effectiveness.

#### Acceptance Criteria

1. WHEN actions are generated, THE Backend_API SHALL create proposed actions with status tracking
2. WHEN a user approves an action, THE Backend_API SHALL update the action status and log approval details
3. WHEN an action is completed, THE Backend_API SHALL record actual outcomes and measured savings
4. WHEN outcomes are recorded, THE Backend_API SHALL calculate variance between predicted and actual results
5. WHEN action history is requested, THE Backend_API SHALL provide complete audit trail with timestamps

### Requirement 5: Performance Metrics and KPI Calculation

**User Story:** As a business owner, I want to see quantified savings and performance metrics, so that I can measure the ROI of the expiry prevention system.

#### Acceptance Criteria

1. WHEN KPI calculation runs, THE Backend_API SHALL compute total at-risk inventory value
2. WHEN savings are measured, THE Backend_API SHALL track prevented expiry losses by category and store
3. WHEN cash flow impact is calculated, THE Backend_API SHALL measure working capital freed from dead inventory
4. WHEN performance reports are generated, THE Backend_API SHALL show inventory turnover improvements
5. WHEN dashboard data is requested, THE Backend_API SHALL provide real-time metrics with historical trends

### Requirement 6: API Endpoints and Data Access

**User Story:** As a frontend developer, I want well-defined API endpoints with consistent response formats, so that I can build a reliable user interface.

#### Acceptance Criteria

1. WHEN data upload is requested, THE Backend_API SHALL provide POST /upload endpoint with file validation
2. WHEN risk data is requested, THE Backend_API SHALL provide GET /risk endpoint with filtering capabilities
3. WHEN actions are requested, THE Backend_API SHALL provide GET /actions endpoint with status-based filtering
4. WHEN KPIs are requested, THE Backend_API SHALL provide GET /kpis endpoint with date range parameters
5. WHEN action updates are submitted, THE Backend_API SHALL provide POST endpoints for status changes

### Requirement 7: Data Storage and Schema Management

**User Story:** As a system administrator, I want reliable data storage with proper schema management, so that the system can handle growing data volumes and maintain data integrity.

#### Acceptance Criteria

1. WHEN raw data is uploaded, THE Backend_API SHALL store it separately from processed data
2. WHEN data processing occurs, THE Backend_API SHALL maintain referential integrity across all tables
3. WHEN schema changes are needed, THE Backend_API SHALL support database migrations
4. WHEN data queries are executed, THE Backend_API SHALL optimize for performance with proper indexing
5. WHEN data backup is required, THE Backend_API SHALL support export of all critical business data

### Requirement 8: Scheduled Processing and Automation

**User Story:** As a system operator, I want automated daily processing of inventory data, so that risk assessments and recommendations stay current without manual intervention.

#### Acceptance Criteria

1. WHEN scheduled processing runs, THE Backend_API SHALL execute feature calculation for all active stores
2. WHEN risk scoring is scheduled, THE Backend_API SHALL update all batch risk scores nightly
3. WHEN action generation is automated, THE Backend_API SHALL create new recommendations based on current data
4. WHEN KPI updates are scheduled, THE Backend_API SHALL refresh all performance metrics
5. WHEN processing fails, THE Backend_API SHALL log errors and send notifications to administrators