from datetime import date, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy import text, desc
from app.db.session import SessionLocal, engine
from app.db.models import BatchRisk, FeatureStoreSKU, InventoryBatch, SalesDaily, UserPreferences, RecommendationFeedback, NewsEvents
import pandas as pd

class ContextBuilder:
    def __init__(self):
        self.db = SessionLocal()
    
    def build_context(
        self, 
        snapshot_date: date = None,
        store_id: Optional[str] = None,
        sku_id: Optional[str] = None,
        top_n: int = 20
    ) -> Dict[str, Any]:
        """Build comprehensive context for AI analysis"""
        if not snapshot_date:
            snapshot_date = date.today()
        
        context = {
            "snapshot_date": snapshot_date.isoformat(),
            "filters": {
                "store_id": store_id,
                "sku_id": sku_id,
                "top_n": top_n
            }
        }
        
        # Get top risk items
        context["risk_items"] = self._get_risk_items(snapshot_date, store_id, sku_id, top_n)
        
        # Get key metrics
        context["key_metrics"] = self._get_key_metrics(snapshot_date, store_id, sku_id)
        
        # Get sales velocity features
        context["velocity_features"] = self._get_velocity_features(snapshot_date, store_id, sku_id)
        
        # Get user preferences
        context["user_preferences"] = self._get_user_preferences()
        
        # Get recent feedback patterns
        context["feedback_patterns"] = self._get_feedback_patterns()
        
        # Get relevant news events
        context["news_events"] = self._get_news_events(snapshot_date)
        
        return context
    
    def _get_risk_items(self, snapshot_date: date, store_id: Optional[str], sku_id: Optional[str], top_n: int) -> List[Dict]:
        """Get top risk items with details"""
        query = self.db.query(BatchRisk).filter(BatchRisk.snapshot_date == snapshot_date)
        
        if store_id:
            query = query.filter(BatchRisk.store_id == store_id)
        if sku_id:
            query = query.filter(BatchRisk.sku_id == sku_id)
        
        risks = query.order_by(desc(BatchRisk.risk_score)).limit(top_n).all()
        
        return [
            {
                "store_id": r.store_id,
                "sku_id": r.sku_id,
                "batch_id": r.batch_id,
                "days_to_expiry": r.days_to_expiry,
                "at_risk_units": r.at_risk_units,
                "at_risk_value": float(r.at_risk_value),
                "risk_score": float(r.risk_score),
                "expected_sales_to_expiry": float(r.expected_sales_to_expiry)
            }
            for r in risks
        ]
    
    def _get_key_metrics(self, snapshot_date: date, store_id: Optional[str], sku_id: Optional[str]) -> Dict[str, Any]:
        """Calculate key aggregate metrics"""
        query = self.db.query(BatchRisk).filter(BatchRisk.snapshot_date == snapshot_date)
        
        if store_id:
            query = query.filter(BatchRisk.store_id == store_id)
        if sku_id:
            query = query.filter(BatchRisk.sku_id == sku_id)
        
        risks = query.all()
        
        if not risks:
            return {
                "total_at_risk_value": 0,
                "total_at_risk_units": 0,
                "high_risk_batches": 0,
                "medium_risk_batches": 0,
                "avg_days_to_expiry": 0,
                "total_batches": 0
            }
        
        total_value = sum(float(r.at_risk_value) for r in risks)
        total_units = sum(r.at_risk_units for r in risks)
        high_risk = sum(1 for r in risks if r.risk_score >= 70)
        medium_risk = sum(1 for r in risks if 40 <= r.risk_score < 70)
        avg_days = sum(r.days_to_expiry for r in risks) / len(risks)
        
        return {
            "total_at_risk_value": round(total_value, 2),
            "total_at_risk_units": total_units,
            "high_risk_batches": high_risk,
            "medium_risk_batches": medium_risk,
            "avg_days_to_expiry": round(avg_days, 1),
            "total_batches": len(risks)
        }
    
    def _get_velocity_features(self, snapshot_date: date, store_id: Optional[str], sku_id: Optional[str]) -> List[Dict]:
        """Get sales velocity features for context"""
        query = self.db.query(FeatureStoreSKU).filter(FeatureStoreSKU.date == snapshot_date)
        
        if store_id:
            query = query.filter(FeatureStoreSKU.store_id == store_id)
        if sku_id:
            query = query.filter(FeatureStoreSKU.sku_id == sku_id)
        
        features = query.limit(50).all()  # Limit for context size
        
        return [
            {
                "store_id": f.store_id,
                "sku_id": f.sku_id,
                "v7": float(f.v7 or 0),
                "v14": float(f.v14 or 0),
                "v30": float(f.v30 or 0),
                "volatility": float(f.volatility or 0)
            }
            for f in features
        ]
    
    def _get_user_preferences(self) -> Dict[str, Any]:
        """Get user preferences for personalization"""
        prefs = self.db.query(UserPreferences).filter(UserPreferences.user_id == "default").first()
        
        if not prefs:
            return {
                "optimize_for": "balanced",
                "service_level_priority": "medium",
                "multi_location_aggressiveness": "medium"
            }
        
        return {
            "optimize_for": prefs.optimize_for,
            "service_level_priority": prefs.service_level_priority,
            "multi_location_aggressiveness": prefs.multi_location_aggressiveness
        }
    
    def _get_feedback_patterns(self) -> Dict[str, Any]:
        """Get recent feedback patterns for learning"""
        # Get feedback from last 30 days
        cutoff_date = date.today() - timedelta(days=30)
        
        feedback = self.db.query(RecommendationFeedback).filter(
            RecommendationFeedback.timestamp >= cutoff_date
        ).all()
        
        if not feedback:
            return {"total_feedback": 0, "patterns": {}}
        
        patterns = {}
        for f in feedback:
            action_type = f.action_type
            if action_type not in patterns:
                patterns[action_type] = {"accepted": 0, "rejected": 0, "dismissed": 0}
            patterns[action_type][f.action] += 1
        
        return {
            "total_feedback": len(feedback),
            "patterns": patterns
        }
    
    def _get_news_events(self, snapshot_date: date) -> List[Dict]:
        """Get relevant news events that might affect scoring"""
        # Get events from last 7 days
        start_date = snapshot_date - timedelta(days=7)
        
        events = self.db.query(NewsEvents).filter(
            NewsEvents.event_date >= start_date,
            NewsEvents.event_date <= snapshot_date
        ).all()
        
        return [
            {
                "event_date": e.event_date.isoformat(),
                "event_type": e.event_type,
                "description": e.description,
                "score_modifier": float(e.score_modifier)
            }
            for e in events
        ]
    
    def build_context_from_data(
        self,
        inventory_data: List[Dict[str, Any]],
        snapshot_date: date = None,
        store_id: Optional[str] = None,
        sku_id: Optional[str] = None,
        top_n: int = 20
    ) -> Dict[str, Any]:
        """Build context from provided inventory data instead of database"""
        if not snapshot_date:
            snapshot_date = date.today()
        
        # Convert inventory data to DataFrame for easier processing
        df = pd.DataFrame(inventory_data)
        
        # Apply filters if provided
        if store_id:
            df = df[df.get('store_id') == store_id]
        if sku_id:
            df = df[df.get('sku_id') == sku_id]
        
        # Calculate basic risk metrics from the data
        risk_items = []
        total_value = 0
        total_units = 0
        
        for _, row in df.iterrows():
            # Calculate days to expiry
            try:
                expiry_date = pd.to_datetime(row.get('expiry_date', '2024-12-31')).date()
                days_to_expiry = (expiry_date - snapshot_date).days
            except:
                days_to_expiry = 30  # Default if parsing fails
            
            # Calculate risk score (simple heuristic)
            qty = float(row.get('on_hand_qty', 0))
            cost = float(row.get('cost_per_unit', 0))
            value = qty * cost
            
            # Risk factors
            expiry_risk = max(0, (30 - days_to_expiry) / 30)  # Higher risk as expiry approaches
            quantity_risk = min(qty / 100, 1.0)  # Higher risk for larger quantities
            risk_score = (expiry_risk * 0.7 + quantity_risk * 0.3) * 100
            
            total_value += value
            total_units += qty
            
            if risk_score > 20:  # Only include items with significant risk
                risk_items.append({
                    "store_id": row.get('store_id', 'UNKNOWN'),
                    "sku_id": row.get('sku_id', 'UNKNOWN'),
                    "batch_id": row.get('batch_id', 'UNKNOWN'),
                    "product_name": row.get('product_name', 'Unknown Product'),
                    "category": row.get('category', 'Unknown'),
                    "on_hand_qty": qty,
                    "at_risk_units": qty,  # Add expected field name
                    "at_risk_value": value,  # Add expected field name
                    "expiry_date": row.get('expiry_date', '2024-12-31'),
                    "cost_per_unit": cost,
                    "selling_price": float(row.get('selling_price', cost * 1.5)),
                    "days_to_expiry": days_to_expiry,
                    "risk_score": risk_score,
                    "total_value": value
                })
        
        # Sort by risk score and limit
        risk_items = sorted(risk_items, key=lambda x: x['risk_score'], reverse=True)[:top_n]
        
        context = {
            "snapshot_date": snapshot_date.isoformat(),
            "filters": {
                "store_id": store_id,
                "sku_id": sku_id,
                "top_n": top_n
            },
            "risk_items": risk_items,
            "key_metrics": {
                "total_at_risk_value": sum(item['total_value'] for item in risk_items),
                "total_at_risk_units": sum(item['on_hand_qty'] for item in risk_items),
                "high_risk_batches": len([item for item in risk_items if item['risk_score'] > 70]),
                "medium_risk_batches": len([item for item in risk_items if 30 < item['risk_score'] <= 70]),
                "low_risk_batches": len([item for item in risk_items if item['risk_score'] <= 30]),
                "avg_days_to_expiry": sum(item['days_to_expiry'] for item in risk_items) / len(risk_items) if risk_items else 0,
                "total_inventory_value": total_value,
                "total_inventory_units": total_units
            },
            "velocity_features": [],  # Could be enhanced with historical data
            "user_preferences": self._get_default_preferences(),
            "news_events": self._get_recent_news_events(snapshot_date)
        }
        
        return context
    
    def _get_default_preferences(self) -> Dict[str, Any]:
        """Get default user preferences when no database is available"""
        return {
            "optimize_for": "cost",
            "service_level_priority": "medium",
            "multi_location_aggressiveness": "medium",
            "markdown_threshold": 0.7,
            "transfer_threshold": 0.5,
            "disposal_threshold": 0.9
        }
    
    def _get_recent_news_events(self, snapshot_date: date) -> List[Dict[str, Any]]:
        """Get recent news events (simplified version for data-only mode)"""
        try:
            # Try to get from database if available
            start_date = snapshot_date - timedelta(days=7)
            
            events = self.db.query(NewsEvents).filter(
                NewsEvents.event_date >= start_date,
                NewsEvents.event_date <= snapshot_date
            ).all()
            
            return [
                {
                    "event_date": e.event_date.isoformat(),
                    "event_type": e.event_type,
                    "description": e.description,
                    "score_modifier": float(e.score_modifier)
                }
                for e in events
            ]
        except:
            # Return default events if database is not available
            return [
                {
                    "event_date": snapshot_date.isoformat(),
                    "event_type": "market_condition",
                    "description": "Normal market conditions",
                    "score_modifier": 1.0
                }
            ]

    def close(self):
        """Close database session"""
        self.db.close()

# Convenience function
def build_context_for_date(snapshot_date: date = None, **filters) -> Dict[str, Any]:
    """Build context and automatically close session"""
    builder = ContextBuilder()
    try:
        return builder.build_context(snapshot_date, **filters)
    finally:
        builder.close()