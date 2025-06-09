import asyncio
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Ensure that the main app's config and database modules are loaded first
# This sets up the database URL and engine correctly.
try:
    from app.config import settings
    from app.database import engine, SessionLocal, Base
    from app.models import Wine
    from app.schemas import WineCreate # For potential validation if needed
except ImportError as e:
    print(f"Error importing app modules: {e}")
    print("Please ensure you run this script from the 'backend' directory,")
    print("and that your main application structure (app/config.py, app/database.py, app/models.py) is correct.")
    exit(1)

# Path to the scraped JSON data
SCRAPED_WINES_PATH = "../lab/martel_wines.json" # Adjusted path relative to backend directory

async def load_scraped_wines():
    try:
        with open(SCRAPED_WINES_PATH, 'r', encoding='utf-8') as f:
            wines_data = json.load(f)
        print(f"Successfully loaded {len(wines_data)} wines from {SCRAPED_WINES_PATH}")
        return wines_data
    except FileNotFoundError:
        print(f"Error: {SCRAPED_WINES_PATH} not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {SCRAPED_WINES_PATH}.")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while loading scraped wines: {e}")
        return []

async def seed_data_from_json():
    # Ensure tables are created.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all) # Optional: Drop tables first if you want a clean seed
        await conn.run_sync(Base.metadata.create_all)
        print("Database tables dropped and recreated.") # Updated print message

    scraped_wines = await load_scraped_wines()
    if not scraped_wines:
        print("No wines to seed from JSON. Exiting.")
        return

    async with SessionLocal() as db:
        # Optional: Check if data already exists to prevent duplicates
        # This simple check assumes if any wine exists, we don't re-seed.
        # You might want a more sophisticated check based on wine names or product_urls.
        result = await db.execute(select(Wine).limit(1))
        if result.scalars().first():
            print("Database already contains wine data. To re-seed, clear the 'wines' table first or modify this script.")
            # If you want to clear and re-seed, you can add:
            # await db.execute(Wine.__table__.delete())
            # await db.commit()
            # print("Cleared existing wine data.")
            # return # Or continue to seed new data

        print(f"Seeding {len(scraped_wines)} wines from JSON...")
        wines_to_add = []
        for wine_data in scraped_wines:
            # Map JSON fields to model fields
            # The 'brandName' from JSON is mapped to 'producer' in the model
            # Ensure all required fields in Wine model are present or have defaults
            wine_entry = {
                "name": wine_data.get("name"),
                "type": wine_data.get("type"),
                "varietal": wine_data.get("varietal"),
                "vintage": int(wine_data["vintage"]) if wine_data.get("vintage") and wine_data.get("vintage").isdigit() else None,
                "region": wine_data.get("region"),
                "country": wine_data.get("country"),
                "price": float(wine_data["price"]) if wine_data.get("price") is not None else None,
                "description": wine_data.get("description"),
                "image_url": wine_data.get("image_url"),
                "producer": wine_data.get("brandName"), # Mapping brandName to producer
                "sub_region": wine_data.get("sub_region"),
                "food_pairing": wine_data.get("food_pairing"),
                "drinking_window": wine_data.get("drinking_window"),
                "body_type": wine_data.get("body_type"),
                "product_url": wine_data.get("product_url"),
                "size": wine_data.get("size"),
                "source": wine_data.get("source", "martel.ch") # Default source if not in JSON
            }

            # Basic validation: ensure essential fields like name and price are present
            if not wine_entry["name"] or wine_entry["price"] is None:
                print(f"Skipping wine due to missing name or price: {wine_data.get('name')}")
                continue
            
            # You could use Pydantic model for validation here if desired:
            # try:
            #     validated_data = WineCreate(**wine_entry)
            #     db_wine = Wine(**validated_data.model_dump())
            # except Exception as ve:
            #     print(f"Validation error for wine {wine_entry.get('name')}: {ve}")
            #     continue
            db_wine = Wine(**wine_entry)
            wines_to_add.append(db_wine)
        
        if wines_to_add:
            db.add_all(wines_to_add)
            try:
                await db.commit()
                print(f"Successfully seeded {len(wines_to_add)} wines from JSON.")
            except Exception as e:
                await db.rollback()
                print(f"Error seeding data from JSON: {e}")
        else:
            print("No valid wines found in JSON to seed.")
        
        await db.close()

async def main():
    db_url_display = settings.DATABASE_URL
    if "@" in db_url_display:
        db_url_display = "postgresql+asyncpg://****:****@" + db_url_display.split('@', 1)[1]
    print(f"Attempting to connect to database: {db_url_display}")
    
    await seed_data_from_json()

if __name__ == "__main__":
    # This script should be run from the 'backend' directory.
    # Example: cd backend && python seed_db.py
    asyncio.run(main())
