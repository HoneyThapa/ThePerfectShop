from fastapi import FastAPI
from app.api.routes_upload import router as upload_router
from app.api.routes_risk import router as risk_router
from app.api.routes_ai import router as ai_router
from app.api.routes_preferences import router as preferences_router
from app.api.routes_news import router as news_router

app = FastAPI(title="ExpiryShield MVP with Operations Copilot")

app.include_router(upload_router)
app.include_router(risk_router)
app.include_router(ai_router)
app.include_router(preferences_router)
app.include_router(news_router)
