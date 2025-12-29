from fastapi import FastAPI
from app.api.routes_upload import router as upload_router
from app.api.routes_risk import router as risk_router
from app.api.routes_actions import router as actions_router
from app.api.routes_kpis import router as kpis_router

app = FastAPI(title="ExpiryShield MVP")

app.include_router(upload_router)
app.include_router(risk_router)
app.include_router(actions_router)
app.include_router(kpis_router)
