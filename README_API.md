# Chatbot FastAPI Backend

A FastAPI-based chatbot backend powered by Google Gemini, ready to deploy on Vercel.

## Local Development

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run locally
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### API Documentation
Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### POST /chat
Send a message to the chatbot

**Request:**
```json
{
  "message": "Hello, how are you?",
  "thread_id": "user123",
  "language": "English"
}
```

**Response:**
```json
{
  "response": "I'm doing well, thank you for asking! How can I help you today?",
  "thread_id": "user123"
}
```

### GET /
API information and available endpoints

### GET /health
Health check endpoint

### DELETE /chat/{thread_id}
Clear chat history for a specific thread

## Deploy to Vercel

### Prerequisites
1. Install Vercel CLI: `npm install -g vercel`
2. Make sure your `credentials.json` is in the project root

### Deployment Steps

1. **Login to Vercel**
```bash
vercel login
```

2. **Deploy**
```bash
vercel --prod
```

3. **Set Environment Variables** (if needed)
```bash
vercel env add GOOGLE_APPLICATION_CREDENTIALS
```

### Important Notes for Vercel Deployment

⚠️ **Credentials File**: 
- For production, it's better to use environment variables instead of the credentials.json file
- You can set the entire JSON content as an environment variable in Vercel dashboard
- Update the code to read from environment variable:

```python
import json
credentials = json.loads(os.environ.get("GOOGLE_CREDENTIALS_JSON"))
# Use credentials with your Google API
```

⚠️ **Memory Limitation**:
- MemorySaver keeps data in memory, which resets on Vercel's serverless functions
- For persistent storage, consider using a database or external storage solution

⚠️ **Cold Starts**:
- First request might be slower due to serverless cold starts
- Consider using Vercel's Edge Functions for faster response times

## Example Usage

### Using curl
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is FastAPI?",
    "thread_id": "user123"
  }'
```

### Using Python requests
```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={
        "message": "Hello!",
        "thread_id": "user123"
    }
)
print(response.json())
```

### Using JavaScript fetch
```javascript
fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: 'Hello!',
    thread_id: 'user123'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

## LangSmith Integration

To enable LangSmith tracing, uncomment and fill in these environment variables in `main.py`:

```python
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-langsmith-api-key-here"
os.environ["LANGCHAIN_PROJECT"] = "your-project-name-here"
```

Or set them in Vercel's environment variables dashboard.
