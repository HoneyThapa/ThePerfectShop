from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import date
import uuid
import hashlib
import json

from app.services.context_builder import build_context_for_date
from app.services.action_engine import generate_actions_for_risks
from app.services.groq_client import groq_client
from app.db.session import SessionLocal
from app.db.models import RecommendationFeedback

router = APIRouter(prefix="/ai", tags=["AI Operations Copilot"])

class InsightsRequest(BaseModel):
    inventory_data: Optional[List[Dict[str, Any]]] = []  # Accept inventory data directly
    snapshot_date: Optional[date] = None
    store_id: Optional[str] = None
    sku_id: Optional[str] = None
    top_n: int = 20

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str
    inventory_data: Optional[List[Dict[str, Any]]] = []  # Accept inventory data directly
    store_id: Optional[str] = None
    sku_id: Optional[str] = None
    snapshot_date: Optional[date] = None

class FeedbackRequest(BaseModel):
    recommendation_id: Optional[str] = "frontend_generated"
    action: Optional[str] = None  # For backward compatibility
    feedback_type: str  # "will_consider" or "reject"
    context_hash: str
    action_type: str
    action_parameters: Dict[str, Any]
    risk_score: float
    user_notes: Optional[str] = None

@router.post("/insights")
async def get_ai_insights(request: InsightsRequest):
    """Generate AI-driven insights and action recommendations"""
    try:
        print(f"🔍 Insights request received: inventory_data={len(request.inventory_data or [])}, snapshot_date={request.snapshot_date}")
        
        # Check if inventory data is provided directly
        if request.inventory_data:
            print("📊 Using provided inventory data")
            # Build context from provided data
            from app.services.context_builder import ContextBuilder
            context_builder = ContextBuilder()
            context = context_builder.build_context_from_data(
                inventory_data=request.inventory_data,
                snapshot_date=request.snapshot_date,
                store_id=request.store_id,
                sku_id=request.sku_id,
                top_n=request.top_n
            )
            context_builder.close()
        else:
            print("🗄️ Using database data")
            # Build context from database (original behavior)
            context = build_context_for_date(
                snapshot_date=request.snapshot_date,
                store_id=request.store_id,
                sku_id=request.sku_id,
                top_n=request.top_n
            )
        
        print(f"✅ Context built: {len(context['risk_items'])} risk items")
        
        # Generate deterministic actions
        try:
            print("🎯 Generating deterministic actions...")
            from app.services.action_engine import generate_actions_for_risks
            deterministic_actions = generate_actions_for_risks(
                context["risk_items"], 
                context["user_preferences"]
            )
            print(f"✅ Actions generated: {len(deterministic_actions)} actions")
        except Exception as action_error:
            print(f"❌ Action generation failed: {action_error}")
            # Provide fallback actions
            deterministic_actions = []
            for item in context["risk_items"][:5]:  # Top 5 items
                deterministic_actions.append({
                    "action_type": "markdown",
                    "priority": "high",
                    "description": f"Review {item.get('product_name', 'Unknown')} at {item.get('store_id', 'Unknown')}",
                    "confidence": 0.7,
                    "expected_impact": f"Potential savings from {item.get('at_risk_units', 0)} units",
                    "action_parameters": {
                        "store_id": item.get("store_id"),
                        "sku_id": item.get("sku_id"),
                        "batch_id": item.get("batch_id")
                    }
                })
        
        # Try to get AI insights, but provide fallback if it fails
        try:
            print("🤖 Calling Groq AI service...")
            ai_response = groq_client.get_insights(context, {
                "store_id": request.store_id,
                "sku_id": request.sku_id,
                "top_n": request.top_n
            })
            print("✅ AI response received")
        except Exception as ai_error:
            # Fallback response when AI fails
            print(f"⚠️ AI service failed, using fallback: {ai_error}")
            ai_response = {
                "executive_summary": f"Analysis completed successfully. Found {len(context['risk_items'])} items requiring attention with total at-risk value of ${context['key_metrics'].get('total_at_risk_value', 0):,.2f}.",
                "prioritized_actions": [],
                "assumptions": ["AI service temporarily unavailable - using deterministic analysis"]
            }
        
        print("📋 Building final response...")
        
        # Combine deterministic actions with AI insights
        response = {
            "executive_summary": ai_response.get("executive_summary", "Analysis completed"),
            "prioritized_actions": deterministic_actions[:10],  # Top 10 actions
            "ai_insights": ai_response.get("prioritized_actions", []),
            "key_metrics": context["key_metrics"],
            "confidence_scores": {
                "data_quality": _assess_data_quality(context),
                "recommendation_confidence": _assess_recommendation_confidence(context)
            },
            "assumptions": ai_response.get("assumptions", []),
            "context_summary": {
                "total_risk_items": len(context["risk_items"]),
                "snapshot_date": context["snapshot_date"],
                "filters_applied": context["filters"]
            }
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating insights: {str(e)}")

@router.post("/chat")
async def ai_chat(request: ChatRequest):
    """Conversational AI interface for inventory questions"""
    try:
        # Check if inventory data is provided directly
        if request.inventory_data:
            # Build context from provided data
            from app.services.context_builder import ContextBuilder
            context_builder = ContextBuilder()
            context = context_builder.build_context_from_data(
                inventory_data=request.inventory_data,
                snapshot_date=request.snapshot_date,
                store_id=request.store_id,
                sku_id=request.sku_id,
                top_n=50  # More context for chat
            )
            context_builder.close()
        else:
            # Build context from database (original behavior)
            context = build_context_for_date(
                snapshot_date=request.snapshot_date,
                store_id=request.store_id,
                sku_id=request.sku_id,
                top_n=50  # More context for chat
            )
        
        # Get conversational response
        chat_response = groq_client.chat_response(
            message=request.message,
            context_data=context,
            conversation_history=[]  # TODO: Implement conversation history storage
        )
        
        response = {
            "conversation_id": request.conversation_id or str(uuid.uuid4()),
            "response": chat_response.get("response", "I'm sorry, I couldn't process that request."),
            "structured_actions": chat_response.get("structured_actions", []),
            "evidence_used": chat_response.get("evidence_used", []),
            "data_gaps": chat_response.get("data_gaps", []),
            "context_summary": {
                "data_points_available": len(context["risk_items"]),
                "snapshot_date": context["snapshot_date"]
            }
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in chat response: {str(e)}")

@router.post("/feedback")
async def record_feedback(request: FeedbackRequest):
    """Record user feedback on recommendations for learning"""
    try:
        db = SessionLocal()
        
        try:
            feedback = RecommendationFeedback(
                recommendation_id=request.recommendation_id or "frontend_generated",
                user_id="default",  # MVP: single user
                action=request.feedback_type,  # Use feedback_type as action
                context_hash=request.context_hash,
                action_type=request.action_type,
                action_parameters=request.action_parameters,
                risk_score=request.risk_score
            )
            
            db.add(feedback)
            db.commit()
            db.refresh(feedback)
            
            return {
                "status": "success",
                "message": "Feedback recorded successfully",
                "feedback_id": feedback.id
            }
        finally:
            db.close()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording feedback: {str(e)}")

@router.get("/health")
async def ai_health_check():
    """Health check for AI services"""
    try:
        # Test Groq connection
        test_response = groq_client.chat_completion([
            {"role": "user", "content": "Say 'OK' if you can hear me"}
        ])
        
        return {
            "status": "healthy",
            "groq_api": "connected",
            "model": "llama-3.1-8b-instant",
            "test_response": test_response["choices"][0]["message"]["content"]
        }
    except Exception as e:
        return {
            "status": "degraded",
            "groq_api": "error",
            "error": str(e)
        }

def _assess_data_quality(context: Dict[str, Any]) -> float:
    """Assess quality of available data for recommendations"""
    score = 0.8  # Base score
    
    # Check if we have recent data
    risk_items = context.get("risk_items", [])
    if len(risk_items) == 0:
        score -= 0.4
    elif len(risk_items) < 5:
        score -= 0.2
    
    # Check if we have velocity features
    velocity_features = context.get("velocity_features", [])
    if len(velocity_features) == 0:
        score -= 0.3
    
    return max(0.1, min(1.0, score))

def _assess_recommendation_confidence(context: Dict[str, Any]) -> float:
    """Assess confidence in recommendations based on data completeness"""
    score = 0.7  # Base confidence
    
    # Higher confidence with more data points
    risk_items = len(context.get("risk_items", []))
    if risk_items >= 10:
        score += 0.2
    elif risk_items >= 5:
        score += 0.1
    
    # Higher confidence with user preferences
    if context.get("user_preferences", {}).get("optimize_for") != "balanced":
        score += 0.1
    
    # Higher confidence with feedback history
    feedback_patterns = context.get("feedback_patterns", {})
    if feedback_patterns.get("total_feedback", 0) > 10:
        score += 0.1
    
    return max(0.1, min(1.0, score))