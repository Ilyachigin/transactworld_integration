📦 Install Dependencies
>pip install -r requirements.txt

🗄 Initialize the Database
>sqlite3 merchant_data.db < utils/init.sql

🚀 Run the Application
>uvicorn main:app --reload

---
🗂 Project Structure
```
.
├── main.py                 # Entry point
├── config.py               # Configuration
├── gateway/                # Core proxy logic and routing
├── client/                 # Outbound request logic
├── schemas/                # Pydantic data models
├── utils/                  # Utility modules: DB, logger, etc.
├── requirements.txt        # Dependencies
├── Dockerfile              # (optional)
├── README.md               # This file
└── merchant_data.db        # SQLite DB (generated after init)
