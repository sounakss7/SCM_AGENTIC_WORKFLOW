# SCM Agentic Workflow - Complete Setup Guide

## Project Structure

```
SCM_AGENTIC_WORKFLOW/
├── frontend/                 # React + Vite + TypeScript
│   ├── src/
│   │   ├── App.tsx          # Main application component
│   │   ├── main.tsx         # Entry point
│   │   ├── App.css          # Application styles
│   │   └── index.css        # Global styles
│   ├── package.json         # Frontend dependencies
│   ├── vite.config.ts       # Vite configuration
│   └── tsconfig.json        # TypeScript config
├── backend/                  # FastAPI + LangGraph + LLM
│   ├── main.py             # Main FastAPI application
│   ├── requirements.txt     # Python dependencies
│   └── .env.example        # Environment variables template
├── vercel.json             # Vercel deployment config
├── .vercelignore           # Files to exclude from build
├── .nvmrc                  # Node version specification
└── README.md               # This file
```

## Technology Stack

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Fast build tool
- **CSS** - Modern styling

### Backend
- **FastAPI** - Web framework
- **LangGraph** - Agent orchestration
- **LangChain** - LLM integration
- **Gemini AI** - LLM model
- **Uvicorn** - ASGI server

## Local Development

### Prerequisites
- Node.js 20+ (use `.nvmrc`)
- Python 3.10+
- pip (Python package manager)

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file with your GEMINI_API_KEY
echo "GEMINI_API_KEY=your_key_here" > .env

python main.py
```

Backend runs on `http://localhost:8000`

## API Documentation

### POST /api/place_order
Place an order and execute the workflow.

**Request:**
```json
{
  "order_id": "ORD-12345",
  "simulate_disruption": false
}
```

**Response:**
```json
{
  "order_id": "ORD-12345",
  "state": {
    "status": "Order Fulfilled",
    "current_phase": "Compliance",
    "detected_disruptions": [],
    "audit_trail": [
      {"agent": "UI", "action": "Order received"},
      {"agent": "Intelligence", "action": "Analysis: System operating normally"},
      {"agent": "Orchestration", "action": "Standard route selected"},
      {"agent": "Compliance", "action": "Order validated"}
    ]
  }
}
```

### GET /health
Health check endpoint.

## Environment Variables

### Frontend (`frontend/.env.local`)
```env
VITE_API_URL=http://localhost:8000
```

### Backend (`backend/.env`)
```env
GEMINI_API_KEY=your_gemini_api_key
PORT=8000
```

## Vercel Deployment

### Configuration Files
1. **vercel.json** - Build and deployment settings
   - Specifies Node.js version 20.x
   - Builds frontend with `npm ci && npm run build`
   - Outputs to `frontend/dist`

2. **.vercelignore** - Excludes unnecessary files
3. **.nvmrc** - Node version specification

### Deployment Steps

1. **Push to GitHub**
```bash
git add .
git commit -m "Deploy complete SCM agentic workflow"
git push origin main
```

2. **Deploy on Vercel**
   - Go to [vercel.com/dashboard](https://vercel.com/dashboard)
   - Connect your GitHub repository
   - Import the project
   - Vercel automatically detects the configuration from `vercel.json`
   - Add environment variables if needed
   - Deploy

3. **Or Manual Redeploy**
   - In Vercel Dashboard, find your project
   - Click Deployments tab
   - Click the three dots (•••) menu
   - Select "Redeploy" (ensure cache is off)

## Workflow Architecture

### Multi-Agent Flow
1. **UI Agent** - Initializes order placement
2. **Intelligence Agent** - AI analysis using Gemini LLM
3. **Orchestration Agent** - Workflow routing and execution
4. **Compliance Agent** - Regulatory validation

### LLM Integration
- Uses Gemini 2.5 Flash model
- Analyzes disruptions and provides mitigation strategies
- Gracefully falls back if API is unavailable

## Troubleshooting

### Frontend Build Issues
- Clear `node_modules` and `package-lock.json`
- Run `npm install` again
- Check Node version: `node --version` (should be 20.x)

### Backend Issues
- Ensure Python 3.10+: `python --version`
- Verify virtual environment is activated
- Check all dependencies: `pip list`
- Verify GEMINI_API_KEY is set

### Vercel Deployment Issues
- Check build logs in Vercel dashboard
- Ensure `vercel.json` is committed
- Verify `frontend/package.json` has correct scripts
- Check `.vercelignore` doesn't exclude important files

## Production Considerations

1. **API Rate Limiting** - Add rate limiting for production
2. **Authentication** - Implement user authentication
3. **Database** - Add persistent data storage
4. **Monitoring** - Set up error tracking and logging
5. **Testing** - Add unit and integration tests
6. **Documentation** - Keep API docs up to date

## Security

- Never commit `.env` files
- Use environment variables for secrets
- Validate all API inputs
- Implement CORS properly for production
- Use HTTPS for all API calls in production
