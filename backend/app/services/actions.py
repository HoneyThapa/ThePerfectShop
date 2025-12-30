from datetime import date
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import SessionLocal
from app.db.models import (
    BatchRisk,
    FeatureStoreSKU,
    StoreMaster,
    SKUMaster,
    Action,
    Purchase,
    DataChangeTracking
)

logger = logging.getLogger(__name__)


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
        max_transfer_distance: int = 500,  # km
        incremental: bool = True,
        changed_batches: Optional[Set[tuple]] = None
    ) -> List[TransferRecommendation]:
        """
        Identify faster-moving stores for transfers and calculate transfer feasibility.
        
        Requirements 3.1:
        - Identify faster-moving stores for transfers
        - Calculate transfer feasibility and costs
        - Estimate expected savings from transfers
        
        Requirements 7.3, 7.4:
        - Implement incremental data processing where possible
        - Optimize job performance for large datasets
        """
        recommendations = []
        
        # Get high-risk batches that need action
        if incremental and changed_batches is not None:
            # Process only changed high-risk batches
            high_risk_batches = self._get_changed_high_risk_batches(
                snapshot_date, min_risk_score, changed_batches
            )
        else:
            # Process all high-risk batches
            high_risk_batches = (
                self.db.query(BatchRisk)
                .filter(
                    BatchRisk.snapshot_date == snapshot_date,
                    BatchRisk.risk_score >= min_risk_score,
                    BatchRisk.at_risk_units > 0
                )
                .all()
            )
        
        if not high_risk_batches:
            logger.info("No high-risk batches found for transfer recommendations")
            return recommendations
        
        # Load reference data into memory for efficient processing
        velocity_data = self._load_velocity_data(snapshot_date)
        stores = {store.store_id: store for store in self.db.query(StoreMaster).all()}
        unit_costs = self._load_unit_costs()
        
        # Process batches in chunks for large datasets
        batch_size = 100
        for i in range(0, len(high_risk_batches), batch_size):
            batch_chunk = high_risk_batches[i:i + batch_size]
            chunk_recommendations = self._process_transfer_batch(
                batch_chunk, velocity_data, stores, unit_costs
            )
            recommendations.extend(chunk_recommendations)
        
        logger.info(f"Generated {len(recommendations)} transfer recommendations")
        return recommendations
    
    def _get_changed_high_risk_batches(
        self, 
        snapshot_date: date, 
        min_risk_score: float, 
        changed_batches: Set[tuple]
    ) -> List[BatchRisk]:
        """Get high-risk batches that have changed."""
        if not changed_batches:
            return []
        
        # Convert set to list for SQL processing
        batch_list = list(changed_batches)
        
        # Process in chunks to avoid SQL parameter limits
        chunk_size = 500
        all_batches = []
        
        for i in range(0, len(batch_list), chunk_size):
            chunk = batch_list[i:i + chunk_size]
            
            # Build conditions for this chunk
            batch_conditions = []
            for store_id, sku_id, batch_id in chunk:
                batch_conditions.append(
                    (BatchRisk.store_id == store_id) &
                    (BatchRisk.sku_id == sku_id) &
                    (BatchRisk.batch_id == batch_id)
                )
            
            if not batch_conditions:
                continue
                
            # Combine conditions with OR
            combined_condition = batch_conditions[0]
            for condition in batch_conditions[1:]:
                combined_condition = combined_condition | condition
            
            chunk_batches = (
                self.db.query(BatchRisk)
                .filter(
                    BatchRisk.snapshot_date == snapshot_date,
                    BatchRisk.risk_score >= min_risk_score,
                    BatchRisk.at_risk_units > 0,
                    combined_condition
                )
                .all()
            )
            
            all_batches.extend(chunk_batches)
        
        return all_batches
    
    def _load_velocity_data(self, snapshot_date: date) -> Dict[Tuple[str, str], Dict[str, float]]:
        """Load velocity data into memory for efficient lookup."""
        velocity_data = {}
        for feature in self.db.query(FeatureStoreSKU).filter_by(date=snapshot_date):
            velocity_data[(feature.store_id, feature.sku_id)] = {
                'v7': float(feature.v7 or 0),
                'v14': float(feature.v14 or 0),
                'v30': float(feature.v30 or 0)
            }
        return velocity_data
    
    def _load_unit_costs(self) -> Dict[Tuple[str, str], float]:
        """Load unit costs into memory for efficient lookup."""
        unit_costs = {}
        for purchase in self.db.query(Purchase).all():
            unit_costs[(purchase.store_id, purchase.sku_id)] = float(purchase.unit_cost)
        return unit_costs
    
    def _process_transfer_batch(
        self,
        batch_chunk: List[BatchRisk],
        velocity_data: Dict[Tuple[str, str], Dict[str, float]],
        stores: Dict[str, StoreMaster],
        unit_costs: Dict[Tuple[str, str], float]
    ) -> List[TransferRecommendation]:
        """Process a batch of high-risk batches for transfer recommendations."""
        recommendations = []
        
        for batch in batch_chunk:
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
        max_discount: float = 0.7,  # Maximum 70% discount
        incremental: bool = True,
        changed_batches: Optional[Set[tuple]] = None
    ) -> List[MarkdownRecommendation]:
        """
        Calculate optimal discount percentages and estimate clearance rates.
        
        Requirements 3.2:
        - Calculate optimal discount percentages
        - Estimate clearance rates and uplift factors
        - Handle markdown constraints and business rules
        
        Requirements 7.3, 7.4:
        - Implement incremental data processing where possible
        - Optimize job performance for large datasets
        """
        recommendations = []
        
        # Get at-risk batches suitable for markdown
        if incremental and changed_batches is not None:
            at_risk_batches = self._get_changed_at_risk_batches(
                snapshot_date, min_risk_score, changed_batches
            )
        else:
            at_risk_batches = (
                self.db.query(BatchRisk)
                .filter(
                    BatchRisk.snapshot_date == snapshot_date,
                    BatchRisk.risk_score >= min_risk_score,
                    BatchRisk.at_risk_units > 0
                )
                .all()
            )
        
        if not at_risk_batches:
            logger.info("No at-risk batches found for markdown recommendations")
            return recommendations
        
        # Load reference data
        velocity_data = self._load_velocity_data_with_volatility(snapshot_date)
        sku_pricing = self._load_sku_pricing()
        unit_costs = self._load_unit_costs()
        
        # Process in batches for large datasets
        batch_size = 200
        for i in range(0, len(at_risk_batches), batch_size):
            batch_chunk = at_risk_batches[i:i + batch_size]
            chunk_recommendations = self._process_markdown_batch(
                batch_chunk, velocity_data, sku_pricing, unit_costs, max_discount
            )
            recommendations.extend(chunk_recommendations)
        
        logger.info(f"Generated {len(recommendations)} markdown recommendations")
        return recommendations
    
    def _get_changed_at_risk_batches(
        self, 
        snapshot_date: date, 
        min_risk_score: float, 
        changed_batches: Set[tuple]
    ) -> List[BatchRisk]:
        """Get at-risk batches that have changed."""
        return self._get_changed_high_risk_batches(snapshot_date, min_risk_score, changed_batches)
    
    def _load_velocity_data_with_volatility(self, snapshot_date: date) -> Dict[Tuple[str, str], Dict[str, float]]:
        """Load velocity data with volatility for markdown calculations."""
        velocity_data = {}
        for feature in self.db.query(FeatureStoreSKU).filter_by(date=snapshot_date):
            velocity_data[(feature.store_id, feature.sku_id)] = {
                'v7': float(feature.v7 or 0),
                'v14': float(feature.v14 or 0),
                'v30': float(feature.v30 or 0),
                'volatility': float(feature.volatility or 1.0)
            }
        return velocity_data
    
    def _load_sku_pricing(self) -> Dict[str, float]:
        """Load SKU pricing information."""
        sku_pricing = {}
        for sku in self.db.query(SKUMaster).all():
            sku_pricing[sku.sku_id] = float(sku.mrp or 0)
        return sku_pricing
    
    def _process_markdown_batch(
        self,
        batch_chunk: List[BatchRisk],
        velocity_data: Dict[Tuple[str, str], Dict[str, float]],
        sku_pricing: Dict[str, float],
        unit_costs: Dict[Tuple[str, str], float],
        max_discount: float
    ) -> List[MarkdownRecommendation]:
        """Process a batch of at-risk batches for markdown recommendations."""
        recommendations = []
        
        for batch in batch_chunk:
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
        risk_factor = float(risk_score) / 100.0
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
        min_days_to_expiry: int = 7,
        incremental: bool = True,
        changed_batches: Optional[Set[tuple]] = None
    ) -> List[LiquidationRecommendation]:
        """
        Identify batches suitable for liquidation and estimate recovery values.
        
        Requirements 3.3:
        - Identify batches suitable for liquidation
        - Estimate recovery values and liquidation costs
        - Generate liquidation recommendations as fallback
        
        Requirements 7.3, 7.4:
        - Implement incremental data processing where possible
        - Optimize job performance for large datasets
        """
        recommendations = []
        
        # Get very high-risk batches that are close to expiry
        if incremental and changed_batches is not None:
            liquidation_candidates = self._get_changed_liquidation_candidates(
                snapshot_date, min_risk_score, min_days_to_expiry, changed_batches
            )
        else:
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
        
        if not liquidation_candidates:
            logger.info("No liquidation candidates found")
            return recommendations
        
        # Load reference data
        unit_costs = self._load_unit_costs()
        sku_categories = self._load_sku_categories()
        
        # Process in batches
        batch_size = 100
        for i in range(0, len(liquidation_candidates), batch_size):
            batch_chunk = liquidation_candidates[i:i + batch_size]
            chunk_recommendations = self._process_liquidation_batch(
                batch_chunk, unit_costs, sku_categories
            )
            recommendations.extend(chunk_recommendations)
        
        logger.info(f"Generated {len(recommendations)} liquidation recommendations")
        return recommendations
    
    def _get_changed_liquidation_candidates(
        self, 
        snapshot_date: date, 
        min_risk_score: float, 
        min_days_to_expiry: int,
        changed_batches: Set[tuple]
    ) -> List[BatchRisk]:
        """Get liquidation candidates that have changed."""
        if not changed_batches:
            return []
        
        # Similar to other methods but with additional filters
        batch_list = list(changed_batches)
        chunk_size = 500
        all_candidates = []
        
        for i in range(0, len(batch_list), chunk_size):
            chunk = batch_list[i:i + chunk_size]
            
            batch_conditions = []
            for store_id, sku_id, batch_id in chunk:
                batch_conditions.append(
                    (BatchRisk.store_id == store_id) &
                    (BatchRisk.sku_id == sku_id) &
                    (BatchRisk.batch_id == batch_id)
                )
            
            if not batch_conditions:
                continue
                
            combined_condition = batch_conditions[0]
            for condition in batch_conditions[1:]:
                combined_condition = combined_condition | condition
            
            chunk_candidates = (
                self.db.query(BatchRisk)
                .filter(
                    BatchRisk.snapshot_date == snapshot_date,
                    BatchRisk.risk_score >= min_risk_score,
                    BatchRisk.days_to_expiry <= min_days_to_expiry,
                    BatchRisk.at_risk_units > 0,
                    combined_condition
                )
                .all()
            )
            
            all_candidates.extend(chunk_candidates)
        
        return all_candidates
    
    def _load_sku_categories(self) -> Dict[str, str]:
        """Load SKU categories for liquidation calculations."""
        sku_categories = {}
        for sku in self.db.query(SKUMaster).all():
            sku_categories[sku.sku_id] = sku.category or 'general'
        return sku_categories
    
    def _process_liquidation_batch(
        self,
        batch_chunk: List[BatchRisk],
        unit_costs: Dict[Tuple[str, str], float],
        sku_categories: Dict[str, str]
    ) -> List[LiquidationRecommendation]:
        """Process a batch of liquidation candidates."""
        recommendations = []
        
        for batch in batch_chunk:
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
        risk_factor = max(0.5, (100 - float(risk_score)) / 100.0)
        
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
        snapshot_date: date,
        incremental: bool = True,
        changed_batches: Optional[Set[tuple]] = None
    ) -> List[Dict]:
        """
        Generate all types of recommendations and rank by expected savings.
        
        Requirements 3.4, 3.5:
        - Rank all recommendations by expected savings
        - Generate comprehensive action recommendations
        
        Requirements 7.3, 7.4:
        - Implement incremental data processing where possible
        - Optimize job performance for large datasets
        """
        all_recommendations = []
        
        # Generate transfer recommendations
        transfer_recs = self.generate_transfer_recommendations(
            snapshot_date, incremental=incremental, changed_batches=changed_batches
        )
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
        markdown_recs = self.generate_markdown_recommendations(
            snapshot_date, incremental=incremental, changed_batches=changed_batches
        )
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
        liquidation_recs = self.generate_liquidation_recommendations(
            snapshot_date, incremental=incremental, changed_batches=changed_batches
        )
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
        
        logger.info(f"Generated {len(all_recommendations)} total recommendations ({len(transfer_recs)} transfers, {len(markdown_recs)} markdowns, {len(liquidation_recs)} liquidations)")
        
        return all_recommendations
    
    def save_recommendations_to_db(
        self,
        recommendations: List[Dict],
        status: str = 'PROPOSED'
    ) -> List[int]:
        """Save recommendations to the actions table and return action IDs."""
        action_ids = []
        
        # Process in batches for large datasets
        batch_size = 100
        for i in range(0, len(recommendations), batch_size):
            batch = recommendations[i:i + batch_size]
            
            for rec in batch:
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
            
            # Flush batch to get IDs
            self.db.flush()
            
            # Collect action IDs from this batch
            for action in self.db.new:
                if isinstance(action, Action):
                    action_ids.append(action.action_id)
        
        self.db.commit()
        logger.info(f"Saved {len(recommendations)} recommendations to database")
        return action_ids


def detect_risk_score_changes(snapshot_date: date) -> Set[tuple]:
    """
    Detect which batches have changed risk scores since last action generation.
    
    Requirements 7.3, 7.4:
    - Add change detection to avoid full recomputation
    """
    db = SessionLocal()
    
    try:
        # Get the last action generation date
        last_action_generation = (
            db.query(DataChangeTracking)
            .filter(
                DataChangeTracking.processing_type == "action_generation",
                DataChangeTracking.snapshot_date <= snapshot_date
            )
            .order_by(DataChangeTracking.snapshot_date.desc())
            .first()
        )
        
        if not last_action_generation:
            # No previous generation, return all high-risk batches
            logger.info("No previous action generation found, processing all high-risk batches")
            all_batches = (
                db.query(
                    BatchRisk.store_id,
                    BatchRisk.sku_id,
                    BatchRisk.batch_id
                )
                .filter(
                    BatchRisk.snapshot_date == snapshot_date,
                    BatchRisk.risk_score >= 50.0  # Minimum risk threshold
                )
                .distinct()
                .all()
            )
            return set((store_id, sku_id, batch_id) for store_id, sku_id, batch_id in all_batches)
        
        # Find batches with changed risk scores
        current_risks = {}
        for risk in db.query(BatchRisk).filter_by(snapshot_date=snapshot_date):
            key = (risk.store_id, risk.sku_id, risk.batch_id)
            current_risks[key] = float(risk.risk_score or 0)
        
        # Get previous risk scores if available
        previous_risks = {}
        if last_action_generation.snapshot_date:
            for risk in db.query(BatchRisk).filter_by(snapshot_date=last_action_generation.snapshot_date):
                key = (risk.store_id, risk.sku_id, risk.batch_id)
                previous_risks[key] = float(risk.risk_score or 0)
        
        # Find changed batches (new batches or significant risk score changes)
        changed_batches = set()
        risk_threshold = 5.0  # Minimum change in risk score to trigger reprocessing
        
        for key, current_risk in current_risks.items():
            previous_risk = previous_risks.get(key)
            
            # Include if new batch or significant risk change
            if (previous_risk is None or 
                abs(current_risk - previous_risk) >= risk_threshold or
                current_risk >= 50.0):  # Always include high-risk batches
                changed_batches.add(key)
        
        logger.info(f"Detected {len(changed_batches)} batches with risk score changes since {last_action_generation.snapshot_date}")
        
        return changed_batches
        
    except Exception as e:
        logger.error(f"Error detecting risk score changes: {str(e)}")
        # On error, return empty set to trigger full processing
        return set()
    finally:
        db.close()


def optimize_action_generation_performance(snapshot_date: date) -> dict:
    """
    Optimize action generation performance for large datasets.
    
    Requirements 7.3, 7.4:
    - Optimize job performance for large datasets
    """
    db = SessionLocal()
    
    try:
        # Get statistics about the data volume
        total_high_risk_batches = (
            db.query(func.count(BatchRisk.batch_id))
            .filter(
                BatchRisk.snapshot_date == snapshot_date,
                BatchRisk.risk_score >= 50.0
            )
            .scalar()
        ) or 0
        
        total_stores = (
            db.query(func.count(func.distinct(BatchRisk.store_id)))
            .filter(BatchRisk.snapshot_date == snapshot_date)
            .scalar()
        ) or 0
        
        total_skus = (
            db.query(func.count(func.distinct(BatchRisk.sku_id)))
            .filter(BatchRisk.snapshot_date == snapshot_date)
            .scalar()
        ) or 0
        
        # Determine optimal processing strategy
        if total_high_risk_batches > 10000:
            strategy = "chunked_incremental"
            chunk_size = 100
        elif total_high_risk_batches > 5000:
            strategy = "batch_incremental"
            chunk_size = 200
        else:
            strategy = "full_processing"
            chunk_size = None
        
        logger.info(f"Action generation optimization: {strategy} for {total_high_risk_batches} high-risk batches across {total_stores} stores and {total_skus} SKUs")
        
        return {
            "strategy": strategy,
            "chunk_size": chunk_size,
            "total_high_risk_batches": total_high_risk_batches,
            "total_stores": total_stores,
            "total_skus": total_skus
        }
        
    except Exception as e:
        logger.error(f"Error optimizing action generation: {str(e)}")
        return {
            "strategy": "full_processing",
            "chunk_size": None,
            "total_high_risk_batches": 0,
            "total_stores": 0,
            "total_skus": 0
        }
    finally:
        db.close()