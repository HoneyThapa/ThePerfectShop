#!/usr/bin/env python3
"""
Trigger data processing pipeline to generate features, risk analysis, and actions
"""

from datetime import date, timedelta
from app.services.features import build_features
from app.services.scoring import ScoringService
from app.services.actions import ActionsService
from app.db.session import SessionLocal
import sys

def process_data_pipeline(snapshot_date=None):
    """Run the complete data processing pipeline"""
    
    if not snapshot_date:
        snapshot_date = date.today()
    
    print(f"🚀 Starting Data Processing Pipeline for {snapshot_date}")
    print("=" * 60)
    
    try:
        # Step 1: Build Features
        print("1️⃣ Building Features...")
        feature_result = build_features(snapshot_date)
        
        if feature_result["status"] == "success":
            print(f"✅ Features built: {feature_result['features_created']} store-SKU combinations")
            if feature_result.get("errors", 0) > 0:
                print(f"⚠️  {feature_result['errors']} errors occurred")
        else:
            print(f"❌ Feature building failed: {feature_result}")
            return False
        
        # Step 2: Generate Risk Scores
        print("\n2️⃣ Generating Risk Scores...")
        db = SessionLocal()
        try:
            scoring_service = ScoringService(db)
            risk_result = scoring_service.calculate_batch_risk(snapshot_date)
            
            if isinstance(risk_result, list):
                print(f"✅ Risk scores generated: {len(risk_result)} at-risk batches")
            else:
                print(f"✅ Risk scoring completed")
        except Exception as e:
            print(f"❌ Risk scoring failed: {e}")
            return False
        finally:
            db.close()
        
        # Step 3: Generate Actions
        print("\n3️⃣ Generating Action Recommendations...")
        db = SessionLocal()
        try:
            actions_service = ActionsService(db)
            actions_result = actions_service.generate_actions(snapshot_date)
            
            if isinstance(actions_result, list):
                print(f"✅ Actions generated: {len(actions_result)} recommendations")
            else:
                print(f"✅ Action generation completed")
        except Exception as e:
            print(f"❌ Action generation failed: {e}")
            return False
        finally:
            db.close()
        
        print("\n🎉 Data Processing Pipeline Completed Successfully!")
        print("=" * 60)
        print("✅ Features: Built")
        print("✅ Risk Analysis: Generated")
        print("✅ Actions: Generated")
        print("\n🔗 Your UI should now show data!")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        return False

def quick_test():
    """Quick test to see what data we have"""
    print("🔍 Quick Data Check")
    print("=" * 30)
    
    from app.db.session import SessionLocal
    from app.db.models import StoreMaster, SKUMaster, SalesDaily, InventoryBatch
    
    db = SessionLocal()
    try:
        stores = db.query(StoreMaster).count()
        skus = db.query(SKUMaster).count()
        sales = db.query(SalesDaily).count()
        inventory = db.query(InventoryBatch).count()
        
        print(f"🏪 Stores: {stores}")
        print(f"🛒 Products: {skus}")
        print(f"📈 Sales Records: {sales:,}")
        print(f"📦 Inventory Batches: {inventory}")
        
        if all([stores > 0, skus > 0, sales > 0, inventory > 0]):
            print("\n✅ Raw data looks good - ready for processing!")
            return True
        else:
            print("\n❌ Missing raw data - check database setup")
            return False
    finally:
        db.close()

if __name__ == "__main__":
    # Quick test first
    if not quick_test():
        print("❌ Raw data issues found. Run: python setup_local_db.py")
        sys.exit(1)
    
    # Get snapshot date from command line or use today
    if len(sys.argv) > 1:
        try:
            snapshot_date = date.fromisoformat(sys.argv[1])
        except ValueError:
            print("❌ Invalid date format. Use YYYY-MM-DD")
            sys.exit(1)
    else:
        snapshot_date = date.today()
    
    # Run the pipeline
    success = process_data_pipeline(snapshot_date)
    sys.exit(0 if success else 1)