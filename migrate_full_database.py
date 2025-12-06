"""
Migration script: Upload all 90 food items to Upstash Vector
Includes 75 original items + 15 new enhanced items
"""

import json
from upstash_client import UpstashClient

def migrate_all_foods_to_upstash():
    """Migrate all foods from JSON to Upstash"""
    
    print("📊 Starting complete food database migration to Upstash...\n")
    
    # Step 1: Load all food data
    print("1️⃣ Loading food data from foods.json...")
    try:
        with open('foods.json', 'r', encoding='utf-8') as f:
            food_data = json.load(f)
        print(f"✅ Loaded {len(food_data)} food items")
    except Exception as e:
        print(f"❌ Failed to load foods.json: {e}")
        return False
    
    # Step 2: Connect to Upstash
    print("\n2️⃣ Connecting to Upstash Vector...")
    try:
        upstash = UpstashClient()
    except Exception as e:
        print(f"❌ Failed to connect to Upstash: {e}")
        return False
    
    # Step 3: Prepare vectors
    print("\n3️⃣ Preparing vectors for upload...")
    vectors_to_upsert = []
    
    for item in food_data:
        # Create enriched text
        enriched_text = item["text"]
        if "region" in item:
            enriched_text += f" Region: {item['region']}."
        if "type" in item:
            enriched_text += f" Type: {item['type']}."
        if "dietary" in item:
            enriched_text += f" Dietary: {', '.join(item['dietary'])}."
        if "nutrition" in item:
            enriched_text += f" Nutrition: {item['nutrition']}."
        
        # Create metadata
        metadata = {
            "original_text": item["text"],
            "region": item.get("region", "Unknown"),
            "type": item.get("type", "Unknown"),
            "dietary": ",".join(item.get("dietary", [])),
            "nutrition": item.get("nutrition", "N/A")
        }
        
        vectors_to_upsert.append((item["id"], enriched_text, metadata))
    
    print(f"✅ Prepared {len(vectors_to_upsert)} vectors with enriched metadata")
    
    # Step 4: Upload to Upstash
    print("\n4️⃣ Uploading to Upstash Vector...")
    try:
        upstash.batch_upsert(vectors_to_upsert, batch_size=500)
        print("✅ All vectors uploaded successfully!")
    except Exception as e:
        print(f"❌ Failed to upload vectors: {e}")
        return False
    
    # Step 5: Verify
    print("\n5️⃣ Verifying upload...")
    try:
        info = upstash.get_info()
        print(f"✅ Upstash now contains {info.vector_count} vectors")
        print(f"   Dimension: {info.dimension}")
        print(f"   Database size: {info.vector_count / 1000:.1f}k vectors")
    except Exception as e:
        print(f"⚠️  Could not verify: {e}")
    
    return True

if __name__ == "__main__":
    print("🚀 RAG FOOD DATABASE COMPLETE MIGRATION\n")
    success = migrate_all_foods_to_upstash()
    
    if success:
        print("\n" + "="*50)
        print("🎉 MIGRATION SUCCESSFUL!")
        print("="*50)
        print("\n✅ All 90 food items are now in Upstash Vector")
        print("✅ Ready for RAG queries")
        print("✅ Run: python rag_run.py")
        print("\n📊 Database includes:")
        print("  • 75 original diverse food items")
        print("  • 15 new enhanced items with:")
        print("    - 5 cultural/regional cuisines (Vietnamese, Korean, etc.)")
        print("    - 5 healthy nutritional dishes (Quinoa, Salmon, Acai, etc.)")
        print("    - 5 popular international dishes (Paella, Ceviche, etc.)")
        print("\n🔍 Query examples to test:")
        print("  1. 'What is pho?'")
        print("  2. 'Which foods are high in protein?'")
        print("  3. 'Tell me about Korean fermented foods'")
        print("  4. 'What vegan options are available?'")
        print("  5. 'Which foods can be grilled?'")
    else:
        print("\n❌ Migration failed. Check errors above.")
