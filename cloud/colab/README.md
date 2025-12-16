# Google Colab GPU Worker

Free GPU compute for intensive analysis tasks

## Quick Start

1. **Open in Colab**
   - Upload `discovery_worker.ipynb` to Google Drive
   - Open with Google Colab
   - Or directly: [Open in Colab](https://colab.research.google.com)

2. **Enable GPU**
   - Runtime > Change runtime type
   - Hardware accelerator: GPU
   - GPU type: T4 (free tier)

3. **Get ngrok Token**
   - Sign up at https://dashboard.ngrok.com/signup
   - Copy your auth token

4. **Run All Cells**
   - Runtime > Run all
   - Paste ngrok token when prompted
   - Copy the public URL

5. **Add to .env**
   ```bash
   COLAB_GPU_WORKER=https://xxxx.ngrok.io
   ```

## What You Get (Free)

| Resource | Amount |
|----------|--------|
| GPU | NVIDIA T4 (16GB VRAM) |
| CPU | 2 cores |
| RAM | 12-13 GB |
| Disk | 78 GB |
| Runtime | 12 hours max |
| Cost | $0 |

## Limitations

- **12 hour limit**: Disconnects after 12 hours
- **Idle timeout**: ~90 minutes of inactivity
- **Daily resets**: Need to restart each day
- **No persistence**: Data/state not saved between sessions

## Best Use Cases

✅ **Good for:**
- ML model inference
- GPU-accelerated calculations
- Batch processing large datasets
- Testing GPU algorithms
- One-off heavy computations

❌ **Not good for:**
- 24/7 services
- Persistent workers
- Real-time streaming
- Database hosting

## Tips

1. **Keep Active**: Keep browser tab open to prevent idle disconnect
2. **Checkpointing**: Save results frequently to Google Drive
3. **Batch Jobs**: Queue up work to maximize 12-hour window
4. **GPU Usage**: Only use for GPU-specific tasks
5. **Fallback**: Configure other workers for when Colab disconnects

## Upgrading

**Colab Pro ($10/month):**
- 24 hour runtime
- Faster GPUs (P100, V100)
- More RAM (32 GB)
- Background execution

**Colab Pro+ ($50/month):**
- Priority GPU access
- Longer runtimes
- Even more resources

## Alternative: Kaggle Kernels

Similar free GPU option:
- **GPU**: NVIDIA P100 or T4
- **RAM**: 13 GB
- **Runtime**: 9 hours/week GPU quota
- **Signup**: https://kaggle.com

Kaggle advantages:
- No ngrok needed (built-in web access)
- Easier dataset management
- Weekly GPU quota system

## Integration Example

```python
import os
import requests

# Get worker URL
colab_worker = os.getenv('COLAB_GPU_WORKER')

# Check if available
response = requests.get(f"{colab_worker}/health", timeout=5)
if response.ok:
    # Use Colab worker for GPU tasks
    result = requests.post(
        f"{colab_worker}/analyze",
        json={
            "trades": trades,
            "analysis_types": ["ml_predictions", "clustering"]
        }
    )
else:
    # Fallback to CPU workers
    print("Colab worker offline, using alternative")
```
