from datetime import date
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import (
    BatchRisk,
    FeatureStoreSKU,
    StoreMaster,
    SKUMaster,
    Action,
    Purchase
)


@dataclass
class TransferRecommendation:
    from_store: str
    to_store: str
    sku_id: str
    batch_id: str
    qty: int
    transfer_cost: float
    expected_savings: float
    feasibility_score: float


@dataclass
class MarkdownRecommendation:
    store_id: str
    sku_id: str
    batch_id: str
    qty: int
    discount_pct: float
    expected_clearance_rate: float
    expected_savings: float


@dataclass
class LiquidationRecommendation:
    store_id: str
    sku_id: str
    batch_id: str
    qty: int
    recovery_rate: float
    liquidation_cost: float
    expected_savings: float


class ActionEngine:
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        
    def generate_transfer_recommendations(
        self, 
        snapshot_date: date,
        min_risk_score: float = 70.0,
        max_transfer_distance: int = 500  # km
    ) -> List[TransferRecommendation]:
        """
        Identify faster-moving stores for transfers and calculate transfer feasibility.
        
        Requirements 3.1:
        - Identify faster-moving stores for transfers
        - Calculate transfer feasibility and costs
        - Estimate expected savings from transfers
        """
        recommendations = []
        
        # Get high-risk batches that need action
        high_risk_batches = (
            self.db.query(BatchRisk)
            .filter(
                BatchRisk.snapshot_date == snapshot_date,
                BatchRisk.risk_score >= min_risk_score,
                BatchRisk.at_risk_units > 0
            )
            .all()
        )
        
        # Get velocity data for all store-SKU combinations
        velocity_data = {}
        for feature in self.db.query(FeatureStoreSKU).filter_by(date=snapshot_date):
            velocity_data[(feature.store_id, feature.sku_id)] = {
                'v7': float(feature.v7 or 0),
                'v14': float(feature.v14 or 0),
                'v30': float(feature.v30 or 0)
            }
        
        # Get store locations for distance calculations
        stores = {store.store_id: store for store in self.db.query(StoreMaster).all()}
        
        # Get unit costs for savings calculations
        unit_costs = {}
        for purchase in self.db.query(Purchase).all():
            unit_costs[(purchase.store_id, purchase.sku_id)] = float(purchase.unit_cost)
        
        for batch in high_risk_batches:
            source_velocity = velocity_data.get((batch.store_id, batch.sku_id), {}).get('v14', 0)
            
            # Find potential destination stores with higher velocity for this SKU
            potential_destinations = []
            
            for (store_id, sku_id), velocity_info in velocity_data.items():
                if (sku_id == batch.sku_id and 
                    store_id != batch.store_id and
                    velocity_info['v14'] > source_velocity * 1.2):  # At least 20% faster
                    
                    # Calculate transfer feasibility
                    transfer_cost = self._calculate_transfer_cost(
                        batch.store_id, store_id, batch.at_risk_units
                    )
                    
                    # Estimate how much faster the destination can move inventory
                    velocity_improvement = velocity_info['v14'] - source_velocity
                    days_saved = batch.at_risk_units / max(velocity_improvement, 0.1)
                    
                    # Calculate expected savings (avoided write-off minus transfer cost)
                    unit_cost = unit_costs.get((batch.store_id, batch.sku_id), 10.0)
                    avoided_writeoff = batch.at_risk_units * unit_cost
                    expected_savings = avoided_writeoff - transfer_cost
                    
                    # Calculate feasibility score based on multiple factors
                    feasibility_score = self._calculate_transfer_feasibility(
                        batch.store_id, store_id, velocity_improvement, 
                        transfer_cost, avoided_writeoff
                    )
                    
                    if expected_savings > 0 and feasibility_score > 0.3:
                        potential_destinations.append({
                            'store_id': store_id,
                            'velocity_improvement': velocity_improvement,
                            'transfer_cost': transfer_cost,
                            'expected_savings': expected_savings,
                            'feasibility_score': feasibility_score
                        })
            
            # Sort by expected savings and feasibility
            potential_destinations.sort(
                key=lambda x: (x['expected_savings'], x['feasibility_score']), 
                reverse=True
            )
            
            # Create recommendations for top destinations
            for dest in potential_destinations[:3]:  # Top 3 destinations
                recommendations.append(TransferRecommendation(
                    from_store=batch.store_id,
                    to_store=dest['store_id'],
                    sku_id=batch.sku_id,
                    batch_id=batch.batch_id,
                    qty=batch.at_risk_units,
                    transfer_cost=dest['transfer_cost'],
                    expected_savings=dest['expected_savings'],
                    feasibility_score=dest['feasibility_score']
                ))
        
        return recommendations
    
    def _calculate_transfer_cost(self, from_store: str, to_store: str, qty: int) -> float:
        """Calculate transfer cost based on distance and quantity."""
        # Simplified cost calculation - in reality would use actual distances
        # Base cost per unit + distance factor
        base_cost_per_unit = 2.0
        
        # Simple distance estimation based on store IDs (placeholder)
        # In real implementation, would use actual geographic coordinates
        distance_factor = 1.0
        if from_store[:2] != to_store[:2]:  # Different regions
            distance_factor = 1.5
        
        return qty * base_cost_per_unit * distance_factor
    
    def _calculate_transfer_feasibility(
        self, 
        from_store: str, 
        to_store: str, 
        velocity_improvement: float,
        transfer_cost: float,
        avoided_writeoff: float
    ) -> float:
        """Calculate feasibility score for transfer (0-1 scale)."""
        # Factors affecting feasibility:
        # 1. Velocity improvement ratio
        # 2. Cost-benefit ratio
        # 3. Store capacity (simplified)
        
        velocity_score = min(velocity_improvement / 10.0, 1.0)  # Normalize to 0-1
        cost_benefit_score = min(avoided_writeoff / max(transfer_cost, 1.0) / 10.0, 1.0)
        capacity_score = 0.8  # Simplified - assume most stores have capacity
        
        return (velocity_score * 0.4 + cost_benefit_score * 0.4 + capacity_score * 0.2)
    
    def generate_markdown_recommendations(
        self,
        snapshot_date: date,
        min_risk_score: float = 50.0,
        max_discount: float = 0.7  # Maximum 70% discount
    ) -> List[MarkdownRecommendation]:
        """
        Calculate optimal discount percentages and estimate clearance rates.
        
        Requirements 3.2:
        - Calculate optimal discount percentages
        - Estimate clearance rates and uplift factors
        - Handle markdown constraints and business rules
        """
        recommendations = []
        
        # Get at-risk batches suitable for markdown
        at_risk_batches = (
            self.db.query(BatchRisk)
            .filter(
                BatchRisk.snapshot_date == snapshot_date,
                BatchRisk.risk_score >= min_risk_score,
                BatchRisk.at_risk_units > 0
            )
            .all()
        )
        
        # Get velocity data for demand elasticity calculations
        velocity_data = {}
        for feature in self.db.query(FeatureStoreSKU).filter_by(date=snapshot_date):
            velocity_data[(feature.store_id, feature.sku_id)] = {
                'v7': float(feature.v7 or 0),
                'v14': float(feature.v14 or 0),
                'v30': float(feature.v30 or 0),
                'volatility': float(feature.volatility or 1.0)
            }
        
        # Get SKU pricing information
        sku_pricing = {}
        for sku in self.db.query(SKUMaster).all():
            sku_pricing[sku.sku_id] = float(sku.mrp or 0)
        
        # Get unit costs
        unit_costs = {}
        for purchase in self.db.query(Purchase).all():
            unit_costs[(purchase.store_id, purchase.sku_id)] = float(purchase.unit_cost)
        
        for batch in at_risk_batches:
            velocity_info = velocity_data.get((batch.store_id, batch.sku_id), {})
            current_velocity = velocity_info.get('v14', 0)
            volatility = velocity_info.get('volatility', 1.0)
            
            mrp = sku_pricing.get(batch.sku_id, 0)
            unit_cost = unit_costs.get((batch.store_id, batch.sku_id), mrp * 0.6)
            
            if mrp <= 0:
                continue
            
            # Calculate optimal discount based on multiple factors
            optimal_discount = self._calculate_optimal_discount(
                batch.days_to_expiry,
                batch.at_risk_units,
                current_velocity,
                volatility,
                batch.risk_score,
                max_discount
            )
            
            # Estimate clearance rate based on discount and demand elasticity
            clearance_rate = self._estimate_clearance_rate(
                optimal_discount,
                current_velocity,
                volatility,
                batch.days_to_expiry
            )
            
            # Calculate expected savings
            discounted_price = mrp * (1 - optimal_discount)
            margin_per_unit = discounted_price - unit_cost
            
            # Units expected to clear at this discount
            units_to_clear = min(batch.at_risk_units, 
                               int(batch.at_risk_units * clearance_rate))
            
            # Revenue from cleared units minus cost of remaining writeoffs
            revenue_from_cleared = units_to_clear * margin_per_unit
            writeoff_cost = (batch.at_risk_units - units_to_clear) * unit_cost
            expected_savings = revenue_from_cleared - writeoff_cost
            
            # Only recommend if savings are positive and discount is reasonable
            if expected_savings > 0 and optimal_discount <= max_discount:
                recommendations.append(MarkdownRecommendation(
                    store_id=batch.store_id,
                    sku_id=batch.sku_id,
                    batch_id=batch.batch_id,
                    qty=batch.at_risk_units,
                    discount_pct=optimal_discount * 100,  # Convert to percentage
                    expected_clearance_rate=clearance_rate,
                    expected_savings=expected_savings
                ))
        
        return recommendations
    
    def _calculate_optimal_discount(
        self,
        days_to_expiry: int,
        at_risk_units: int,
        current_velocity: float,
        volatility: float,
        risk_score: float,
        max_discount: float
    ) -> float:
        """Calculate optimal discount percentage based on urgency and demand factors."""
        # Base discount increases with urgency
        urgency_factor = max(0, (30 - days_to_expiry) / 30.0)  # 0-1 scale
        base_discount = urgency_factor * 0.4  # Up to 40% for urgency
        
        # Risk-based discount adjustment
        risk_factor = risk_score / 100.0
        risk_discount = risk_factor * 0.3  # Up to 30% for high risk
        
        # Velocity-based adjustment (slower moving needs higher discount)
        velocity_factor = max(0, (5 - current_velocity) / 5.0)  # Inverse relationship
        velocity_discount = velocity_factor * 0.2  # Up to 20% for slow movers
        
        # Combine factors
        total_discount = base_discount + risk_discount + velocity_discount
        
        # Apply constraints
        return min(total_discount, max_discount)
    
    def _estimate_clearance_rate(
        self,
        discount_pct: float,
        current_velocity: float,
        volatility: float,
        days_to_expiry: int
    ) -> float:
        """Estimate what percentage of inventory will clear at given discount."""
        # Price elasticity of demand (simplified model)
        # Higher discount = higher demand uplift
        demand_uplift = 1 + (discount_pct * 2.5)  # 2.5x multiplier for elasticity
        
        # Adjust for volatility (more volatile = less predictable clearance)
        volatility_adjustment = max(0.5, 1 - (volatility / 10.0))
        
        # Time constraint factor
        time_factor = min(1.0, days_to_expiry / 14.0)  # Assume 14 days needed for full effect
        
        # Calculate expected clearance rate
        clearance_rate = min(1.0, demand_uplift * volatility_adjustment * time_factor)
        
        return clearance_rate
    
    def generate_liquidation_recommendations(
        self,
        snapshot_date: date,
        min_risk_score: float = 80.0,
        min_days_to_expiry: int = 7
    ) -> List[LiquidationRecommendation]:
        """
        Identify batches suitable for liquidation and estimate recovery values.
        
        Requirements 3.3:
        - Identify batches suitable for liquidation
        - Estimate recovery values and liquidation costs
        - Generate liquidation recommendations as fallback
        """
        recommendations = []
        
        # Get very high-risk batches that are close to expiry
        liquidation_candidates = (
            self.db.query(BatchRisk)
            .filter(
                BatchRisk.snapshot_date == snapshot_date,
                BatchRisk.risk_score >= min_risk_score,
                BatchRisk.days_to_expiry <= min_days_to_expiry,
                BatchRisk.at_risk_units > 0
            )
            .all()
        )
        
        # Get unit costs for recovery calculations
        unit_costs = {}
        for purchase in self.db.query(Purchase).all():
            unit_costs[(purchase.store_id, purchase.sku_id)] = float(purchase.unit_cost)
        
        # Get SKU categories for category-specific recovery rates
        sku_categories = {}
        for sku in self.db.query(SKUMaster).all():
            sku_categories[sku.sku_id] = sku.category or 'general'
        
        for batch in liquidation_candidates:
            unit_cost = unit_costs.get((batch.store_id, batch.sku_id), 10.0)
            category = sku_categories.get(batch.sku_id, 'general')
            
            # Calculate recovery rate based on category and condition
            recovery_rate = self._calculate_recovery_rate(
                category,
                batch.days_to_expiry,
                batch.risk_score
            )
            
            # Calculate liquidation costs (handling, transportation, processing)
            liquidation_cost = self._calculate_liquidation_cost(
                batch.at_risk_units,
                unit_cost,
                category
            )
            
            # Calculate expected recovery value
            gross_recovery = batch.at_risk_units * unit_cost * recovery_rate
            net_recovery = gross_recovery - liquidation_cost
            
            # Compare with total writeoff cost
            total_writeoff_cost = batch.at_risk_units * unit_cost
            expected_savings = net_recovery  # Savings compared to total writeoff
            
            # Only recommend if liquidation provides some recovery
            if expected_savings > 0 and recovery_rate > 0.1:  # At least 10% recovery
                recommendations.append(LiquidationRecommendation(
                    store_id=batch.store_id,
                    sku_id=batch.sku_id,
                    batch_id=batch.batch_id,
                    qty=batch.at_risk_units,
                    recovery_rate=recovery_rate,
                    liquidation_cost=liquidation_cost,
                    expected_savings=expected_savings
                ))
        
        return recommendations
    
    def _calculate_recovery_rate(
        self,
        category: str,
        days_to_expiry: int,
        risk_score: float
    ) -> float:
        """Calculate expected recovery rate for liquidation based on category and condition."""
        # Base recovery rates by category
        category_rates = {
            'food': 0.15,      # Food items have lower recovery due to expiry concerns
            'beverage': 0.20,   # Beverages slightly better
            'personal_care': 0.35,  # Personal care items hold value better
            'household': 0.40,  # Household items good for liquidation
            'electronics': 0.25,  # Electronics depreciate but have some value
            'general': 0.25     # Default rate
        }
        
        base_rate = category_rates.get(category.lower(), 0.25)
        
        # Adjust for time to expiry (closer to expiry = lower recovery)
        time_factor = max(0.5, days_to_expiry / 30.0)  # Scale based on 30-day window
        
        # Adjust for risk score (higher risk = lower recovery)
        risk_factor = max(0.5, (100 - risk_score) / 100.0)
        
        return base_rate * time_factor * risk_factor
    
    def _calculate_liquidation_cost(
        self,
        qty: int,
        unit_cost: float,
        category: str
    ) -> float:
        """Calculate costs associated with liquidation process."""
        # Base processing cost per unit
        base_cost_per_unit = 1.0
        
        # Category-specific cost adjustments
        category_multipliers = {
            'food': 1.5,        # Higher handling costs for food
            'beverage': 1.3,    # Moderate handling costs
            'electronics': 1.2, # Some testing/refurbishment costs
            'general': 1.0      # Standard costs
        }
        
        multiplier = category_multipliers.get(category.lower(), 1.0)
        
        # Fixed costs (minimum processing fee) + variable costs
        fixed_cost = 50.0  # Minimum processing fee
        variable_cost = qty * base_cost_per_unit * multiplier
        
        return fixed_cost + variable_cost
    
    def generate_all_recommendations(
        self,
        snapshot_date: date
    ) -> List[Dict]:
        """
        Generate all types of recommendations and rank by expected savings.
        
        Requirements 3.4, 3.5:
        - Rank all recommendations by expected savings
        - Generate comprehensive action recommendations
        """
        all_recommendations = []
        
        # Generate transfer recommendations
        transfer_recs = self.generate_transfer_recommendations(snapshot_date)
        for rec in transfer_recs:
            all_recommendations.append({
                'action_type': 'TRANSFER',
                'from_store': rec.from_store,
                'to_store': rec.to_store,
                'sku_id': rec.sku_id,
                'batch_id': rec.batch_id,
                'qty': rec.qty,
                'discount_pct': None,
                'expected_savings': rec.expected_savings,
                'feasibility_score': rec.feasibility_score,
                'details': {
                    'transfer_cost': rec.transfer_cost
                }
            })
        
        # Generate markdown recommendations
        markdown_recs = self.generate_markdown_recommendations(snapshot_date)
        for rec in markdown_recs:
            all_recommendations.append({
                'action_type': 'MARKDOWN',
                'from_store': rec.store_id,
                'to_store': None,
                'sku_id': rec.sku_id,
                'batch_id': rec.batch_id,
                'qty': rec.qty,
                'discount_pct': rec.discount_pct,
                'expected_savings': rec.expected_savings,
                'feasibility_score': rec.expected_clearance_rate,
                'details': {
                    'clearance_rate': rec.expected_clearance_rate
                }
            })
        
        # Generate liquidation recommendations
        liquidation_recs = self.generate_liquidation_recommendations(snapshot_date)
        for rec in liquidation_recs:
            all_recommendations.append({
                'action_type': 'LIQUIDATE',
                'from_store': rec.store_id,
                'to_store': None,
                'sku_id': rec.sku_id,
                'batch_id': rec.batch_id,
                'qty': rec.qty,
                'discount_pct': None,
                'expected_savings': rec.expected_savings,
                'feasibility_score': rec.recovery_rate,
                'details': {
                    'recovery_rate': rec.recovery_rate,
                    'liquidation_cost': rec.liquidation_cost
                }
            })
        
        # Sort by expected savings (descending) and feasibility score
        all_recommendations.sort(
            key=lambda x: (x['expected_savings'], x['feasibility_score']), 
            reverse=True
        )
        
        return all_recommendations
    
    def save_recommendations_to_db(
        self,
        recommendations: List[Dict],
        status: str = 'PROPOSED'
    ) -> List[int]:
        """Save recommendations to the actions table and return action IDs."""
        action_ids = []
        
        for rec in recommendations:
            action = Action(
                action_type=rec['action_type'],
                from_store=rec['from_store'],
                to_store=rec.get('to_store'),
                sku_id=rec['sku_id'],
                batch_id=rec['batch_id'],
                qty=rec['qty'],
                discount_pct=rec.get('discount_pct'),
                expected_savings=rec['expected_savings'],
                status=status
            )
            
            self.db.add(action)
            self.db.flush()  # Get the ID
            action_ids.append(action.action_id)
        
        self.db.commit()
        return action_ids