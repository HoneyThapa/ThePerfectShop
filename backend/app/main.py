from fastapi import FastAPI
from app.api.routes_upload import router as upload_router
from app.api.routes_risk import router as risk_router
from app.api.routes_features import router as features_router

app = FastAPI(title="ThePerfectShop")

app.include_router(upload_router)
app.include_router(risk_router)
app.include_router(features_router)
