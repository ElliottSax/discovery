# HuggingFace Space Worker

Distributed compute worker running on HuggingFace Spaces (Free Tier)

## Features

- **Free Compute**: 2 vCPU cores, 16GB RAM
- **Always On**: Persistent service (stays awake with activity)
- **REST API**: FastAPI-based worker endpoint
- **Lightweight**: Optimized for free tier resources

## Setup Instructions

### 1. Create HuggingFace Account
- Go to https://huggingface.co/join
- Sign up for free account

### 2. Create New Space
1. Click "New Space" at https://huggingface.co/new-space
2. Configure:
   - **Name**: `discovery-worker-1`
   - **SDK**: Gradio
   - **Hardware**: CPU basic (free)
   - **Visibility**: Public or Private

### 3. Upload Files
Upload these files to your Space:
- `app.py` (this directory)
- `requirements.txt` (this directory)

### 4. Get Space URL
- Your worker will be at: `https://YOUR_USERNAME-discovery-worker-1.hf.space`
- Add to `.env`:
  ```bash
  HUGGINGFACE_WORKER_1=https://YOUR_USERNAME-discovery-worker-1.hf.space
  ```

### 5. Test Worker
```bash
curl https://YOUR_USERNAME-discovery-worker-1.hf.space/health
```

## Usage

### From Python
```python
import requests

worker_url = "https://YOUR_USERNAME-discovery-worker-1.hf.space"

# Health check
response = requests.get(f"{worker_url}/health")
print(response.json())

# Analyze trades
data = {
    "trades": [
        {"price": 100, "volume": 1000, "price_change": 2.5},
        {"price": 102.5, "volume": 1500, "price_change": 1.2}
    ],
    "analysis_types": ["sentiment", "volume_analysis", "price_patterns"]
}

response = requests.post(f"{worker_url}/analyze", json=data)
print(response.json())
```

## Endpoints

- `GET /` - Service info
- `GET /health` - Health check
- `POST /analyze` - Process trade analysis

## Resource Limits

**Free Tier:**
- 2 vCPU cores
- 16GB RAM
- No GPU
- Space sleeps after 48h inactivity

**Tips:**
- Keep requests lightweight
- Batch process when possible
- Use for CPU-bound tasks only
- Implement request queuing for high load

## Scaling

Create multiple spaces for more compute:
- `discovery-worker-2`
- `discovery-worker-3`
- etc.

Each space gets 2 cores, so 3 spaces = 6 cores free compute!

## Troubleshooting

### Space is sleeping
- Make a request to wake it up
- First request after sleep takes ~30 seconds
- Consider upgrading to persistent hardware ($0.60/hour)

### Out of memory
- Reduce batch sizes
- Simplify analysis algorithms
- Split work across multiple spaces

### API errors
- Check Space logs in HuggingFace UI
- Verify requirements.txt is correct
- Ensure app.py is valid Python
