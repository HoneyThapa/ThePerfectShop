# ThePerfectShop — AI Operations Copilot

**ThePerfectShop** is an **expiry risk intelligence system** with **AI Operations Copilot** for retail inventory.  
This repository contains the complete system that:

1. Ingests messy Excel/CSV exports (sales, inventory-by-batch, purchases)
2. Builds store–SKU sales behavior features
3. Computes a **daily batch-level expiry risk list**
4. **🤖 NEW: AI Operations Copilot** - Provides AI-driven insights, action recommendations, grounded chatbot, and learning mechanisms

---

## 🚀 What's New: AI Operations Copilot

✨ **AI-Driven Insights**: Executive summaries and prioritized action recommendations  
🤖 **Grounded Chatbot**: Ask questions about your inventory with evidence-based responses  
📊 **Smart Actions**: Deterministic action engine with AI re-ranking and explanations  
🧠 **Learning Mechanism**: User feedback loop and preference-based personalization  
📈 **What-If Simulations**: Simple scenario modeling with clear assumptions  
⚙️ **User Preferences**: Customize optimization for stability vs profit vs waste minimization  

---

## 📌 What this system does

✔ Handles messy retail Excel / CSV files  
✔ Normalizes column names and validates data  
✔ Stores clean data in PostgreSQL  
✔ Computes rolling sales velocities (v7, v14, v30)  
✔ Calculates batch-level expiry risk (deterministic, explainable)  
✔ **🤖 AI Operations Copilot with Groq LLM integration**  
✔ **Smart action recommendations with user feedback learning**  
✔ **Conversational AI interface for inventory questions**  
✔ **User preference-based personalization**  

---

## 🧱 Architecture

```
Excel / CSV
    ↓
Ingestion + Validation
    ↓
PostgreSQL (Sales, Inventory, Features)
    ↓
Risk Scoring Engine
    ↓
🤖 AI Operations Copilot
    ├── Context Builder (pulls relevant data)
    ├── Action Engine (deterministic recommendations)  
    ├── Groq LLM (insights + explanations)
    ├── Learning Loop (feedback + preferences)
    └── Streamlit UI (chat + insights panels)
```

---

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Groq API key (provided in instructions)

### 1. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and set:
# GROQ_API_KEY=your_groq_api_key_here

# Create database tables (including new AI tables)
python create_copilot_tables.py

# Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup

```bash
cd frontend

# Install Streamlit (if not already installed)
pip install streamlit requests

# Start the frontend
streamlit run streamlit_app.py
```

### 3. Test AI Features

```bash
cd backend

# Test all AI endpoints
python test_ai_endpoints.py
```

---

## 🤖 AI Operations Copilot Features

### 1. AI Insights Panel
- **Executive Summary**: High-level overview of key risks and opportunities
- **Prioritized Actions**: Top 5-10 recommended actions with confidence scores
- **Key Metrics**: At-risk value, high-risk batches, average days to expiry
- **Evidence Citations**: All recommendations cite specific data fields

### 2. Conversational AI Assistant
- **Grounded Responses**: Only uses provided inventory data, never fabricates
- **Evidence-Based**: Cites specific fields and data points in responses
- **Structured Actions**: Provides actionable recommendations in conversation
- **Data Gap Identification**: Explicitly states when information is missing

### 3. Smart Action Engine
- **Deterministic Core**: Rule-based action generation for auditability
- **AI Enhancement**: LLM provides explanations and re-ranking
- **Action Types**: Markdown, transfer, reorder pause, bundle, FEFO attention
- **Confidence Scoring**: Each action includes confidence and expected impact

### 4. Learning Mechanisms
- **User Preferences**: Optimize for stability vs profit vs waste minimization
- **Feedback Loop**: Accept/reject buttons on recommendations for continuous learning
- **News Events**: Manual event entry (demand spikes, supplier delays) affects scoring
- **Contextual Adaptation**: Actions adapt based on user feedback patterns

### 5. Safety & Grounding
- **No Hallucination**: AI never invents SKUs, quantities, or database values
- **Structured Responses**: All AI outputs follow strict JSON schemas
- **Fallback Modes**: Graceful degradation when AI service unavailable
- **Audit Trail**: All recommendations traceable to underlying data

---

## 🔧 API Endpoints

### Core Endpoints (Existing)
- `POST /upload` - Upload CSV/Excel files
- `GET /risk` - Get risk list for snapshot date

### 🤖 AI Operations Copilot Endpoints (New)
- `POST /ai/insights` - Get AI-driven insights and recommendations
- `POST /ai/chat` - Conversational AI interface
- `POST /ai/feedback` - Record user feedback for learning
- `GET /ai/health` - AI service health check

### User Management
- `GET /preferences/` - Get user preferences
- `POST /preferences/` - Update user preferences
- `GET /preferences/options` - Get available preference options

### News Events
- `GET /news/` - Get news events (with filtering)
- `POST /news/` - Create news event
- `DELETE /news/{id}` - Delete news event

---

## 🎯 Demo Workflow

1. **Upload Data**: Use the sample CSV or your own inventory data
2. **View Risk List**: See traditional risk scoring with batch-level details
3. **Get AI Insights**: Click "🤖 Get AI Insights" for AI analysis
4. **Review Actions**: See prioritized recommendations with explanations
5. **Provide Feedback**: Use ✅/❌ buttons to train the system
6. **Chat with AI**: Ask questions like "Why is SKU-123 high risk?"
7. **Adjust Preferences**: Set optimization goals (profit vs waste vs stability)
8. **View Dashboard**: See AI-enhanced metrics and what-if scenarios

---

## 🔑 Environment Variables

```bash
# Required
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ThePerfectShop

# Optional
GROQ_MODEL=llama-3.1-70b-versatile
GROQ_TEMPERATURE=0.1
GROQ_MAX_TOKENS=2048
```

---

## 🧪 Testing

The system includes comprehensive testing:

```bash
# Test AI endpoints
python backend/test_ai_endpoints.py

# Test individual components
python -c "from app.services.groq_client import groq_client; print('Groq client working!')"
```

---

## 🎨 UI Features

### Enhanced Streamlit Interface
- **AI Insights Panel**: Integrated into risk/action pages
- **Chat Interface**: Floating chat button with conversation history
- **Preference Settings**: Sidebar configuration for AI behavior
- **Feedback Buttons**: Accept/reject actions directly in UI
- **What-If Simulations**: Simple scenario modeling with assumptions
- **Confidence Indicators**: Visual confidence scores for all recommendations

### Visual Enhancements
- **Glass-morphism Design**: Modern, translucent UI elements
- **Color-coded Actions**: Priority-based color coding (red/yellow/green)
- **Animated Transitions**: Smooth page transitions and loading states
- **Responsive Layout**: Works on desktop and tablet devices

---

## 🚧 Future Enhancements

- **Multi-user Support**: User authentication and personalized preferences
- **Advanced ML**: Replace simple feedback learning with proper ML models
- **Real-time Updates**: WebSocket integration for live updates
- **Mobile App**: React Native or Flutter mobile interface
- **Advanced Analytics**: Time-series forecasting and trend analysis
- **Integration APIs**: Connect with existing ERP/POS systems

---

## 📄 License

MIT License - Feel free to use and modify for your retail operations!
Clean Tables (Postgres)
↓
Feature Builder (Store–SKU velocity)
↓
Baseline Risk Scoring
↓
Risk Inbox API
