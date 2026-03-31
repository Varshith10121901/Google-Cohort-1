import os
from dotenv import load_dotenv

# Load .env file explicitly so DB credentials populate into os.environ
load_dotenv()

from app.main import app
import uvicorn

if __name__ == "__main__":
    print("""
    ========================================================
     AURA LITE BACKEND CONSOLIDATED STARTUP
    ========================================================
    Loading FastAPI app from app.main...
    Starting tracks 1, 2, and 3 on port 8080
    ========================================================
    """)
    uvicorn.run("backend:app", host="0.0.0.0", port=8080, reload=True)
