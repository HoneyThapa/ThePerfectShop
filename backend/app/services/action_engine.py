from typing import List, Dict, Any, Optional
from datetime import date
from app.db.models import BatchRisk, UserPreferences, RecommendationFeedback
from app.db.session import SessionLocal

class ActionEngine:
    def __init__(self):
        self.db = SessionLocal()
    
    def generate_actions(self, risk_items: List[Dict], user_preferences: Dict = None) -> List[Dict[str, Any]]:
        """Generate deterministic actions based on risk items and preferences"""
        actions = []
        
        for item in risk_items:
            item_actions = self._generate_item_actions(item, user_preferences)
            actions.extend(item_actions)
        
        # Apply preference-based ranking
        actions = self._rank_actions(actions, user_preferences)
        
        return actions
    
    def _generate_item_actions(self, item: Dict, user_preferences: Dict = None) -> List[Dict[str, Any]]:
        """Generate actions for a single risk item"""
        actions = []
        risk_score = item["risk_score"]
        days_to_expiry = item["days_to_expiry"]
        at_risk_units = item["at_risk_units"]
        at_risk_value = item["at_risk_value"]
        
        # High urgency items (< 3 days)
        if days_to_expiry <= 3:
            if risk_score >= 80:
                actions.append({
                    "action_type": "markdown",
                    "priority": "high",
                    "description": f"Apply 30-50% markdown to {item['sku_id']} at {item['store_id']}",
                    "parameters": {
                        "store_id": item["store_id"],
                        "sku_id": item["sku_id"],
                        "batch_id": item["batch_id"],
                        "suggested_markdown": 0.4,
                        "units_affected": at_risk_units
                    },
                    "expected_impact": f"Clear {at_risk_units} units, recover ~${at_risk_value * 0.6:.2f}",
                    "confidence": 0.9,
                    "why_numbers": {
                        "risk_score": risk_score,
                        "days_to_expiry": days_to_expiry,
                        "at_risk_value": at_risk_value
                    }
                })
            
            actions.append({
                "action_type": "fefo_attention",
                "priority": "high",
                "description": f"FEFO priority flag for {item['sku_id']} batch {item['batch_id']}",
                "parameters": {
                    "store_id": item["store_id"],
                    "sku_id": item["sku_id"],
                    "batch_id": item["batch_id"]
                },
                "expected_impact": "Ensure oldest stock sells first",
                "confidence": 0.95,
                "why_numbers": {
                    "days_to_expiry": days_to_expiry
                }
            })
        
        # Medium urgency (3-7 days)
        elif 3 < days_to_expiry <= 7:
            if risk_score >= 60:
                actions.append({
                    "action_type": "transfer",
                    "priority": "medium",
                    "description": f"Consider transferring {at_risk_units} units of {item['sku_id']} to higher-velocity store",
                    "parameters": {
                        "from_store": item["store_id"],
                        "sku_id": item["sku_id"],
                        "batch_id": item["batch_id"],
                        "units": at_risk_units
                    },
                    "expected_impact": f"Reduce waste risk by moving to faster-selling location",
                    "confidence": 0.7,
                    "why_numbers": {
                        "risk_score": risk_score,
                        "at_risk_units": at_risk_units
                    }
                })
            
            if risk_score >= 70:
                actions.append({
                    "action_type": "markdown",
                    "priority": "medium",
                    "description": f"Apply 15-25% markdown to {item['sku_id']} at {item['store_id']}",
                    "parameters": {
                        "store_id": item["store_id"],
                        "sku_id": item["sku_id"],
                        "batch_id": item["batch_id"],
                        "suggested_markdown": 0.2,
                        "units_affected": at_risk_units
                    },
                    "expected_impact": f"Accelerate sales, recover ~${at_risk_value * 0.8:.2f}",
                    "confidence": 0.8,
                    "why_numbers": {
                        "risk_score": risk_score,
                        "days_to_expiry": days_to_expiry
                    }
                })
        
        # Longer term (7+ days)
        else:
            if risk_score >= 50:
                actions.append({
                    "action_type": "bundle",
                    "priority": "low",
                    "description": f"Create bundle promotion with {item['sku_id']}",
                    "parameters": {
                        "store_id": item["store_id"],
                        "sku_id": item["sku_id"],
                        "batch_id": item["batch_id"],
                        "bundle_discount": 0.1
                    },
                    "expected_impact": "Increase velocity through cross-selling",
                    "confidence": 0.6,
                    "why_numbers": {
                        "risk_score": risk_score
                    }
                })
            
            if at_risk_value > 500:  # High value items
                actions.append({
                    "action_type": "reorder_pause",
                    "priority": "medium",
                    "description": f"Pause reorders for {item['sku_id']} at {item['store_id']} until inventory normalizes",
                    "parameters": {
                        "store_id": item["store_id"],
                        "sku_id": item["sku_id"],
                        "pause_duration_days": 14
                    },
                    "expected_impact": "Prevent additional overstock",
                    "confidence": 0.8,
                    "why_numbers": {
                        "at_risk_value": at_risk_value,
                        "at_risk_units": at_risk_units
                    }
                })
        
        return actions
    
    def _rank_actions(self, actions: List[Dict], user_preferences: Dict = None) -> List[Dict[str, Any]]:
        """Rank actions based on user preferences and feedback history"""
        if not user_preferences:
            user_preferences = {"optimize_for": "balanced"}
        
        # Get feedback patterns to adjust ranking
        feedback_patterns = self._get_feedback_patterns()
        
        for action in actions:
            base_score = self._calculate_base_score(action)
            preference_modifier = self._apply_preference_modifier(action, user_preferences)
            feedback_modifier = self._apply_feedback_modifier(action, feedback_patterns)
            
            action["ranking_score"] = base_score + preference_modifier + feedback_modifier
        
        # Sort by ranking score (higher is better)
        actions.sort(key=lambda x: x["ranking_score"], reverse=True)
        
        return actions
    
    def _calculate_base_score(self, action: Dict) -> float:
        """Calculate base ranking score for action"""
        priority_scores = {"high": 10, "medium": 5, "low": 2}
        confidence_weight = action["confidence"] * 5
        
        return priority_scores.get(action["priority"], 0) + confidence_weight
    
    def _apply_preference_modifier(self, action: Dict, preferences: Dict) -> float:
        """Apply user preference modifiers to action ranking"""
        modifier = 0.0
        optimize_for = preferences.get("optimize_for", "balanced")
        
        if optimize_for == "waste_min":
            if action["action_type"] in ["markdown", "fefo_attention"]:
                modifier += 2.0
        elif optimize_for == "profit":
            if action["action_type"] in ["transfer", "bundle"]:
                modifier += 2.0
            elif action["action_type"] == "markdown":
                modifier -= 1.0
        elif optimize_for == "stability":
            if action["action_type"] == "reorder_pause":
                modifier += 1.5
        
        return modifier
    
    def _apply_feedback_modifier(self, action: Dict, feedback_patterns: Dict) -> float:
        """Apply feedback-based learning modifier"""
        action_type = action["action_type"]
        
        if action_type not in feedback_patterns:
            return 0.0
        
        pattern = feedback_patterns[action_type]
        total_feedback = sum(pattern.values())
        
        if total_feedback < 3:  # Not enough data
            return 0.0
        
        acceptance_rate = pattern.get("accepted", 0) / total_feedback
        rejection_rate = pattern.get("rejected", 0) / total_feedback
        
        # Boost frequently accepted actions, penalize frequently rejected ones
        return (acceptance_rate - rejection_rate) * 2.0
    
    def _get_feedback_patterns(self) -> Dict[str, Dict[str, int]]:
        """Get feedback patterns for learning"""
        feedback = self.db.query(RecommendationFeedback).all()
        
        patterns = {}
        for f in feedback:
            action_type = f.action_type
            if action_type not in patterns:
                patterns[action_type] = {"accepted": 0, "rejected": 0, "dismissed": 0}
            patterns[action_type][f.action] += 1
        
        return patterns
    
    def close(self):
        """Close database session"""
        self.db.close()

# Convenience function
def generate_actions_for_risks(risk_items: List[Dict], user_preferences: Dict = None) -> List[Dict[str, Any]]:
    """Generate actions and automatically close session"""
    engine = ActionEngine()
    try:
        return engine.generate_actions(risk_items, user_preferences)
    finally:
        engine.close()