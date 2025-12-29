# Requirements Document

## Introduction

ThePerfectShop is an inventory expiry risk management system that helps retailers minimize losses from expired products. The system ingests messy Excel/CSV exports, analyzes expiry risk across store-SKU-batch combinations, and generates actionable recommendations (transfers and markdowns) with savings estimates. The MVP focuses on three core capabilities: data ingestion, risk analysis, and action generation.

## Glossary

- **ThePerfectShop**: The complete inventory expiry risk management system
- **Risk_Engine**: Component that calculates expiry risk scores for inventory batches
- **Action_Generator**: Component that creates transfer and markdown recommendations
- **Data_Pipeline**: Component that processes raw uploads into clean, analyzable data
- **Batch**: A specific lot of inventory with a unique expiry date
- **SKU**: Stock Keeping Unit - a unique product identifier
- **Velocity**: Sales rate (units per day) for a store-SKU combination
- **At_Risk_Units**: Inventory units unlikely to sell before expiry
- **Transfer_Action**: Recommendation to move inventory between stores
- **Markdown_Action**: Recommendation to discount products to accelerate sales

## Requirements

### Requirement 1: Data Ingestion and Validation

**User Story:** As a retail operations manager, I want to upload messy Excel/CSV files containing sales, inventory, and purchase data, so that the system can analyze expiry risk across my stores.

#### Acceptance Criteria

1. WHEN a user uploads a CSV or Excel file, THE Data_Pipeline SHALL validate the file format and structure
2. WHEN column names don't match expected schema, THE Data_Pipeline SHALL attempt intelligent mapping (e.g., "SKU Code" → "sku_id")
3. WHEN data validation fails, THE Data_Pipeline SHALL return a detailed error report with specific issues and line numbers
4. WHEN data is successfully validated, THE Data_Pipeline SHALL store raw data and generate a data health report
5. THE Data_Pipeline SHALL handle duplicate rows by identifying and flagging them without failing the upload
6. WHEN date fields are encountered, THE Data_Pipeline SHALL parse multiple date formats safely
7. THE Data_Pipeline SHALL detect and report missing critical fields (expiry dates, negative stock levels)

### Requirement 2: Sales Velocity Calculation

**User Story:** As a data analyst, I want the system to calculate rolling sales velocities for each store-SKU combination, so that I can understand product movement patterns.

#### Acceptance Criteria

1. THE Risk_Engine SHALL compute 7-day, 14-day, and 30-day rolling sales velocities for each store-SKU combination
2. THE Risk_Engine SHALL calculate sales volatility using standard deviation over the last 30 days
3. WHEN insufficient sales history exists, THE Risk_Engine SHALL flag the store-SKU as having incomplete data
4. THE Risk_Engine SHALL store computed features in a structured features table for downstream analysis
5. THE Risk_Engine SHALL update velocity calculations daily based on new sales data

### Requirement 3: Expiry Risk Scoring

**User Story:** As a store manager, I want to see which inventory batches are at risk of expiring, so that I can take preventive action.

#### Acceptance Criteria

1. THE Risk_Engine SHALL calculate days to expiry for each inventory batch
2. THE Risk_Engine SHALL estimate expected sales to expiry using 14-day velocity multiplied by days remaining
3. THE Risk_Engine SHALL compute at-risk units as the excess of on-hand quantity over expected sales
4. THE Risk_Engine SHALL calculate at-risk value using unit cost or average cost when unit cost is unavailable
5. THE Risk_Engine SHALL assign risk scores from 0-100 based on at-risk units and days to expiry
6. WHEN a batch has higher at-risk units and shorter days to expiry, THE Risk_Engine SHALL assign a higher risk score
7. THE Risk_Engine SHALL generate daily risk snapshots for all active inventory batches

### Requirement 4: Transfer Action Generation

**User Story:** As an inventory coordinator, I want the system to recommend transferring at-risk inventory to stores with higher demand, so that I can prevent waste through redistribution.

#### Acceptance Criteria

1. WHEN a batch is identified as at-risk in Store A, THE Action_Generator SHALL identify potential destination stores with higher velocity
2. THE Action_Generator SHALL calculate the destination store's absorption capacity based on velocity and days to expiry
3. THE Action_Generator SHALL recommend transfer quantities that don't exceed the destination's absorption capacity
4. THE Action_Generator SHALL estimate transfer savings as (transfer_qty × unit_cost) minus estimated transfer costs
5. THE Action_Generator SHALL prioritize transfers with the highest savings potential
6. THE Action_Generator SHALL create transfer actions with status "PROPOSED" for management approval

### Requirement 5: Markdown Action Generation

**User Story:** As a pricing manager, I want the system to recommend strategic markdowns for at-risk inventory, so that I can accelerate sales before expiry.

#### Acceptance Criteria

1. WHEN transfer is not viable for at-risk inventory, THE Action_Generator SHALL recommend markdown actions
2. THE Action_Generator SHALL suggest discount percentages based on risk severity: low risk (5%), medium risk (10%), high risk (15-25%)
3. THE Action_Generator SHALL estimate expected sales uplift from markdowns using configurable multipliers
4. THE Action_Generator SHALL calculate expected savings as (recovered_value - discount_cost)
5. THE Action_Generator SHALL create markdown actions with status "PROPOSED" for management approval
6. THE Action_Generator SHALL prioritize markdowns by expected savings and urgency

### Requirement 6: Action Management and Tracking

**User Story:** As a retail operations manager, I want to approve, track, and measure the outcomes of recommended actions, so that I can validate the system's effectiveness.

#### Acceptance Criteria

1. THE ThePerfectShop SHALL provide an interface to view all proposed actions ranked by expected savings
2. WHEN a manager approves an action, THE ThePerfectShop SHALL update the action status to "APPROVED"
3. WHEN an action is completed, THE ThePerfectShop SHALL allow marking it as "DONE" with optional outcome notes
4. THE ThePerfectShop SHALL track actual recovered value and cleared units for completed actions
5. THE ThePerfectShop SHALL allow rejecting actions with status "REJECTED" and reason codes
6. THE ThePerfectShop SHALL maintain a complete audit trail of all action state changes

### Requirement 7: KPI Dashboard and Savings Tracking

**User Story:** As a retail executive, I want to see the financial impact of the expiry risk management system, so that I can measure ROI and make informed decisions.

#### Acceptance Criteria

1. THE ThePerfectShop SHALL calculate total at-risk value across all stores and SKUs daily
2. THE ThePerfectShop SHALL compute expected savings from all proposed actions
3. THE ThePerfectShop SHALL track actual savings from completed actions over configurable time periods
4. THE ThePerfectShop SHALL display key metrics: total at-risk value, proposed savings, realized savings, and action completion rates
5. THE ThePerfectShop SHALL provide filtering by store, category, and date range for detailed analysis
6. THE ThePerfectShop SHALL generate summary reports showing trends in risk reduction and savings over time

### Requirement 8: API and Data Access

**User Story:** As a system integrator, I want programmatic access to risk data and actions, so that I can integrate ExpiryShield with existing retail systems.

#### Acceptance Criteria

1. THE ThePerfectShop SHALL provide REST API endpoints for uploading data files
2. THE ThePerfectShop SHALL provide API endpoints to retrieve risk lists filtered by store, date, and risk threshold
3. THE ThePerfectShop SHALL provide API endpoints to fetch proposed actions and update action statuses
4. THE ThePerfectShop SHALL provide API endpoints to retrieve KPI data and savings metrics
5. THE ThePerfectShop SHALL return structured JSON responses with appropriate HTTP status codes
6. THE ThePerfectShop SHALL validate API requests and return clear error messages for invalid inputs
7. THE ThePerfectShop SHALL support pagination for large result sets

### Requirement 9: User Interface

**User Story:** As a store operations team member, I want an intuitive web interface to interact with the expiry risk system, so that I can efficiently manage inventory without technical expertise.

#### Acceptance Criteria

1. THE ThePerfectShop SHALL provide a web interface for uploading data files with drag-and-drop support
2. THE ThePerfectShop SHALL display a Risk Inbox showing at-risk batches with filtering by store, category, and days to expiry
3. THE ThePerfectShop SHALL provide an Action Queue interface for reviewing, approving, and tracking recommended actions
4. THE ThePerfectShop SHALL display a Savings Dashboard with key metrics and trend visualizations
5. THE ThePerfectShop SHALL show data health status including upload history and validation results
6. THE ThePerfectShop SHALL provide responsive design that works on desktop and tablet devices