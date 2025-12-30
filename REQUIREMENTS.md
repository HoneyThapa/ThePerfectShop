# The Perfect Shop - AI Operations Copilot Requirements

## Project Overview

The Perfect Shop is an AI-powered inventory management system that provides intelligent insights, risk analysis, and action recommendations for retail operations. The system combines traditional inventory management with advanced AI capabilities to optimize operations and reduce waste.

## System Architecture

### Backend (FastAPI + SQLite)
- **Framework**: FastAPI with Python 3.8+
- **Database**: SQLite for development, PostgreSQL-ready for production
- **AI Integration**: Groq LLM API for intelligent analysis
- **API Design**: RESTful endpoints with JSON responses

### Frontend (Streamlit)
- **Framework**: Streamlit for rapid web application development
- **UI Design**: Glass-morphism design with dark themes
- **Navigation**: Tab-based navigation with sidebar controls
- **Responsive**: Adaptive layout for different screen sizes

## Core Requirements

### 1. AI Operations Copilot System

#### 1.1 AI Insights Engine
- **Endpoint**: `POST /ai/insights`
- **Functionality**: 
  - Analyze inventory data for risk patterns
  - Generate executive summaries
  - Provide confidence scores and data quality metrics
  - Support filtering by store, SKU, and date range

#### 1.2 Conversational AI Assistant
- **Endpoint**: `POST /ai/chat`
- **Functionality**:
  - Natural language interaction with inventory data
  - Context-aware responses with data citations
  - Support for follow-up questions
  - Error handling for unavailable data

#### 1.3 Action Recommendation System
- **Component**: Deterministic action engine
- **Functionality**:
  - Generate specific action recommendations
  - Prioritize actions by impact and confidence
  - Support for markdown, transfer, reorder, and FEFO actions
  - Expected impact calculations

### 2. User Management & Preferences

#### 2.1 User Preferences System
- **Endpoints**: `GET/POST /preferences/`
- **Settings**:
  - Optimization strategy (balanced, stability, profit, waste minimization)
  - Service level priority (low, medium, high)
  - Multi-location transfer aggressiveness
  - Persistent storage and retrieval

#### 2.2 Authentication System
- **Frontend**: Login modal with session management
- **Credentials**: Admin authentication (admin/admin123)
- **Features**: Session persistence, logout functionality
- **Profile**: User dashboard with activity tracking

### 3. Data Management

#### 3.1 CSV Upload & Processing
- **Format**: Standard inventory CSV with required columns
- **Validation**: Data type checking and format validation
- **Preview**: Display sample data before confirmation
- **Confirmation**: Explicit user confirmation required

#### 3.2 Database Schema
- **Tables**: 
  - `inventory_batches`: Core inventory data
  - `sales_data`: Historical sales information
  - `batch_features`: Computed risk features
  - `batch_risk_scores`: Risk assessment results
  - `user_preferences`: User configuration
  - `news_events`: External events affecting demand
  - `recommendation_feedback`: User feedback on AI suggestions

### 4. Frontend Requirements

#### 4.1 Navigation System
- **Home Tab**: Welcome page with system overview
- **Dashboard Tab**: Metrics and what-if simulations
- **AI Insights Tab**: AI analysis and recommendations
- **Risk Analysis Tab**: Traditional risk tables and exports
- **AI Chatbot Tab**: Conversational interface
- **Profile Tab**: User account management

#### 4.2 User Experience
- **Upload Flow**: Sidebar upload → preview → confirmation → navigation unlock
- **Navigation Control**: Buttons disabled until data confirmed
- **Visual Feedback**: Loading states, success/error messages
- **Responsive Design**: Works on desktop and tablet devices

#### 4.3 Visual Design
- **Theme**: Glass-morphism with dark overlays
- **Background**: Dynamic darkening after CSV upload
- **Typography**: Anton SC font for titles, clean sans-serif for content
- **Colors**: Blue accent colors for AI elements, white text on dark backgrounds
- **Animations**: Smooth transitions with cubic-bezier easing

### 5. AI Integration Requirements

#### 5.1 Groq API Integration
- **Model**: llama-3.1-8b-instant (working model)
- **API Key**: Configured via environment variable
- **Error Handling**: Graceful fallback for API failures
- **Rate Limiting**: Respect API limits with retry logic

#### 5.2 Context Building
- **Data Sources**: Inventory, sales, features, risk scores
- **Filtering**: By store, SKU, date range, risk level
- **Aggregation**: Summary statistics and key metrics
- **Citations**: Reference to source data fields

### 6. Performance Requirements

#### 6.1 Response Times
- **API Endpoints**: < 5 seconds for AI insights
- **Database Queries**: < 1 second for data retrieval
- **File Upload**: < 10 seconds for CSV processing
- **Page Navigation**: < 500ms for tab switching

#### 6.2 Scalability
- **Database**: Support for 10,000+ inventory items
- **Concurrent Users**: Handle 10+ simultaneous users
- **File Size**: Support CSV files up to 10MB
- **Memory Usage**: Efficient data processing and caching

### 7. Security Requirements

#### 7.1 Data Protection
- **Input Validation**: Sanitize all user inputs
- **SQL Injection**: Use parameterized queries
- **File Upload**: Validate file types and sizes
- **Session Management**: Secure session handling

#### 7.2 API Security
- **CORS**: Proper cross-origin resource sharing
- **Rate Limiting**: Prevent API abuse
- **Error Messages**: No sensitive information in errors
- **Logging**: Audit trail for important actions

### 8. Deployment Requirements

#### 8.1 Development Environment
- **Python**: 3.8+ with pip package management
- **Dependencies**: Listed in requirements.txt
- **Database**: SQLite for local development
- **Environment Variables**: .env file for configuration

#### 8.2 Production Readiness
- **Database**: PostgreSQL migration support
- **Logging**: Structured logging with levels
- **Monitoring**: Health check endpoints
- **Configuration**: Environment-based settings

## Technical Specifications

### API Endpoints

#### AI Operations
- `POST /ai/insights` - Generate AI insights and recommendations
- `POST /ai/chat` - Conversational AI interface
- `POST /ai/feedback` - Record user feedback on recommendations

#### User Management
- `GET /preferences/` - Retrieve user preferences
- `POST /preferences/` - Update user preferences

#### Data Management
- `GET /news/` - Retrieve news events
- `POST /news/` - Create news events

### Data Models

#### Inventory Batch
```python
{
    "store_id": str,
    "sku_id": str,
    "batch_id": str,
    "product_name": str,
    "category": str,
    "on_hand_qty": int,
    "expiry_date": date,
    "cost_per_unit": float,
    "selling_price": float
}
```

#### AI Insights Response
```python
{
    "executive_summary": str,
    "prioritized_actions": List[Action],
    "key_metrics": Dict[str, Any],
    "confidence_scores": Dict[str, float],
    "assumptions": List[str]
}
```

### Frontend Components

#### Navigation Tabs
- Home: System introduction and instructions
- Dashboard: Metrics, KPIs, and simulations
- AI Insights: AI analysis and action recommendations
- Risk Analysis: Traditional risk management tables
- AI Chatbot: Conversational interface
- Profile: User account and preferences

#### UI States
- Initial: Home tab, navigation disabled
- Upload: CSV preview, confirmation required
- Confirmed: All navigation enabled, background darkened
- Logged In: Profile tab accessible, user info displayed

## Quality Assurance

### Testing Requirements
- **Unit Tests**: Core business logic functions
- **Integration Tests**: API endpoint functionality
- **UI Tests**: Frontend component behavior
- **End-to-End Tests**: Complete user workflows

### Performance Testing
- **Load Testing**: Multiple concurrent users
- **Stress Testing**: Large CSV file processing
- **Memory Testing**: Long-running sessions
- **API Testing**: Response time validation

### Browser Compatibility
- **Chrome**: Latest version (primary)
- **Firefox**: Latest version
- **Safari**: Latest version
- **Edge**: Latest version

## Documentation Requirements

### User Documentation
- **User Guide**: Step-by-step usage instructions
- **FAQ**: Common questions and troubleshooting
- **Video Tutorials**: Key feature demonstrations
- **API Documentation**: Endpoint specifications

### Developer Documentation
- **Setup Guide**: Development environment setup
- **Architecture Overview**: System design and components
- **API Reference**: Detailed endpoint documentation
- **Database Schema**: Table structures and relationships

## Compliance & Standards

### Code Quality
- **PEP 8**: Python code style compliance
- **Type Hints**: Function and variable annotations
- **Documentation**: Docstrings for all functions
- **Error Handling**: Comprehensive exception management

### Data Privacy
- **No PII Storage**: No personally identifiable information
- **Data Retention**: Clear data lifecycle policies
- **Access Control**: Role-based access to sensitive data
- **Audit Logging**: Track data access and modifications

## Success Criteria

### Functional Success
- ✅ All AI features working with Groq integration
- ✅ Complete navigation system with proper state management
- ✅ CSV upload and confirmation workflow
- ✅ User authentication and profile management
- ✅ Responsive UI with glass-morphism design

### Performance Success
- ✅ Sub-5 second AI insight generation
- ✅ Smooth navigation and transitions
- ✅ Reliable file upload and processing
- ✅ Stable concurrent user support

### User Experience Success
- ✅ Intuitive navigation flow
- ✅ Clear visual feedback and error messages
- ✅ Professional and modern UI design
- ✅ Accessible on multiple devices and browsers