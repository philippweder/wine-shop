import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Ensure that the main app's config and database modules are loaded first
# This sets up the database URL and engine correctly.
try:
    from app.config import settings
    from app.database import engine, SessionLocal, Base
    from app.models import Wine
except ImportError as e:
    print(f"Error importing app modules: {e}")
    print("Please ensure you run this script from the 'backend' directory,")
    print("and that your main application structure (app/config.py, app/database.py, app/models.py) is correct.")
    exit(1)

sample_wines_data = [
    {
        "name": "Masi Costasera Amarone Classico DOCG", "type": "Red", "varietal": "Corvina, Rondinella, Molinara",
        "price": 34.95, "vintage": 2018, "region": "Valpolicella Classico, Veneto", "country": "Italy",
        "description": "A benchmark Amarone, rich and complex with notes of ripe cherry and cocoa.",
        "image_url": "/images/red-wine.png"  # Updated
    },
    {
        "name": "Whispering Angel Rosé Côtes de Provence AOP", "type": "Rosé", "varietal": "Grenache, Cinsault, Rolle",
        "price": 21.95, "vintage": 2023, "region": "Côtes de Provence", "country": "France",
        "description": "Iconic Provence rosé, elegant, dry with notes of red berries and citrus.",
        "image_url": "/images/rose-wine.jpg"  # Updated
    },
    {
        "name": "Cloudy Bay Sauvignon Blanc", "type": "White", "varietal": "Sauvignon Blanc",
        "price": 29.90, "vintage": 2023, "region": "Marlborough", "country": "New Zealand",
        "description": "Aromatic and vibrant with notes of passionfruit, grapefruit, and a hint of herbaceousness.",
        "image_url": "/images/white-wine.png"  # Updated
    },
    {
        "name": "Champagne Moët & Chandon Brut Impérial", "type": "Sparkling", "varietal": "Pinot Noir, Chardonnay, Pinot Meunier",
        "price": 49.90, "vintage": None, "region": "Champagne", "country": "France",
        "description": "The flagship champagne of Moët & Chandon, known for its bright fruitiness and elegant maturity.",
        "image_url": "/images/champagne-wine.jpg"  # Updated
    },
    {
        "name": "Antinori Tignanello Toscana IGT", "type": "Red", "varietal": "Sangiovese, Cabernet Sauvignon, Cabernet Franc",
        "price": 120.00, "vintage": 2020, "region": "Tuscany", "country": "Italy",
        "description": "One of the original \\'Super Tuscans,\\' complex with red fruit, spice, and oak notes.",
        "image_url": "/images/red-wine.png"  # Updated
    },
    {
        "name": "Domaine Ott Château de Selle Coeur de Grain Rosé", "type": "Rosé", "varietal": "Grenache, Cinsault, Syrah, Mourvèdre",
        "price": 45.00, "vintage": 2022, "region": "Côtes de Provence", "country": "France",
        "description": "A prestigious Provence rosé, refined and aromatic with a long finish.",
        "image_url": "/images/rose-wine.jpg"  # Updated
    },
    {
        "name": "Penfolds Bin 389 Cabernet Shiraz", "type": "Red", "varietal": "Cabernet Sauvignon, Shiraz",
        "price": 70.00, "vintage": 2020, "region": "South Australia", "country": "Australia",
        "description": "Often called \\'Baby Grange,\\' a classic Australian blend known for its richness and structure.",
        "image_url": "/images/red-wine.png"  # Updated
    },
    {
        "name": "Louis Jadot Pouilly-Fuissé", "type": "White", "varietal": "Chardonnay",
        "price": 28.50, "vintage": 2021, "region": "Pouilly-Fuissé, Burgundy", "country": "France",
        "description": "A classic white Burgundy, elegant with notes of white fruits, citrus, and minerality.",
        "image_url": "/images/white-wine.png"  # Updated
    },
    {
        "name": "Vega Sicilia Valbuena 5°", "type": "Red", "varietal": "Tempranillo, Merlot",
        "price": 150.00, "vintage": 2018, "region": "Ribera del Duero", "country": "Spain",
        "description": "A younger expression from Vega Sicilia, powerful yet elegant, with complex aromas.",
        "image_url": "/images/red-wine.png"  # Updated
    },
    {
        "name": "Graham\\'s 20 Year Old Tawny Port", "type": "Dessert", "varietal": "Touriga Nacional, Touriga Franca, Tinta Roriz",
        "price": 55.00, "vintage": None, "region": "Douro Valley", "country": "Portugal",
        "description": "A rich and mellow tawny port with notes of nuts, dried fruit, and spice.",
        "image_url": "/images/red-wine.png"  # Updated (using red as placeholder for Dessert)
    }
]

async def seed_data():
    # Ensure tables are created.
    # This is usually handled by the main app's lifespan, but good to have if running script standalone.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all) # Uncommented to drop tables first
        await conn.run_sync(Base.metadata.create_all)
        print("Database tables dropped and recreated.")

    async with SessionLocal() as db:
        result = await db.execute(select(Wine).limit(1))
        if result.scalars().first():
            print("Database already contains wine data. Skipping seeding.")
            return

        print(f"Seeding {len(sample_wines_data)} wines...")
        for wine_data in sample_wines_data:
            db_wine = Wine(**wine_data)
            db.add(db_wine)
        
        try:
            await db.commit()
            print(f"Successfully seeded {len(sample_wines_data)} wines.")
        except Exception as e:
            await db.rollback()
            print(f"Error seeding data: {e}")
        finally:
            await db.close()

async def main():
    # The import of settings should have loaded the .env file.
    # Let's print part of the DB URL to confirm it's loaded (masking credentials).
    db_url_display = settings.DATABASE_URL
    if "@" in db_url_display:
        db_url_display = "postgresql+asyncpg://****:****@" + db_url_display.split('@', 1)[1]
    print(f"Attempting to connect to database: {db_url_display}")
    
    await seed_data()

if __name__ == "__main__":
    asyncio.run(main())
