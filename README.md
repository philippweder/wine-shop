# Sentio Wine Shop

This project is an online wine shop named "Sentio".

## Development

### Prerequisites

- Python 3.10+
- Node.js 20+ (for frontend)
- PostgreSQL (or other compatible database)

### Backend Setup

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\\Scripts\\activate`
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the `backend` directory and populate it with your database URL and other necessary credentials. Example:
    ```env
    DATABASE_URL="postgresql+asyncpg://user:password@host:port/dbname"
    # Add other keys like SHOPIFY_API_KEY, STRIPE_SECRET_KEY etc.
    ```

5.  **Seed the database (optional, if you have a seed script and want initial data):**
    Make sure your database server is running.
    ```bash
    python seed_db.py
    ```
    *Note: The `seed_db.py` script is currently configured to drop and recreate tables. This will delete existing data.*

6.  **Run the FastAPI backend server:**
    ```bash
    uvicorn app.main:app --reload
    ```
    The backend will typically be available at `http://127.0.0.1:8000`.

### Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```

2.  **Install Node.js dependencies:**
    ```bash
    npm install
    ```
    *(If you prefer yarn, use `yarn install`)*

3.  **Set up environment variables (if any):**
    If your frontend requires environment variables (e.g., for API keys that are safe to expose client-side, or the backend URL), create a `.env.local` file in the `frontend` directory.
    Example:
    ```env
    NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:8000"
    ```

4.  **Run the Next.js frontend development server:**
    ```bash
    npm run dev
    ```
    *(If you prefer yarn, use `yarn dev`)*

    The frontend will typically be available at `http://localhost:3000`.

---

*This README was last updated on June 9, 2025.*