## Security

All APIs require an API Key.

Add this header to every request:

X-API-Key: <your_api_key>

Set your API key in the `.env` file:

API_KEY=your_secret_key


## How to Run

# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables
cp .env.example .env
# Update values inside .env

# 3. Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload