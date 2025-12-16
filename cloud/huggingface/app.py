"""
HuggingFace Space Worker - Free Compute Node
Provides distributed computing capabilities for the discovery platform
"""
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import List, Dict, Any
import asyncio

app = FastAPI(
    title="Discovery Worker - HuggingFace",
    description="Distributed worker node running on HuggingFace Spaces",
    version="1.0.0"
)

# Enable CORS for communication with main server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalysisRequest(BaseModel):
    """Request for trade analysis"""
    trades: List[Dict[str, Any]]
    analysis_types: List[str]
    options: Dict[str, Any] = {}


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    worker_type: str
    compute_platform: str
    available_analyses: List[str]


class PredictionRequest(BaseModel):
    """Request for stock predictions"""
    tickers: List[str]
    trades: List[Dict[str, Any]]
    date: str = None
    confidence_threshold: float = 0.0


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Discovery Worker",
        "platform": "HuggingFace Spaces",
        "status": "running",
        "endpoints": ["/health", "/analyze", "/predict", "/docs"]
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        worker_type="general",
        compute_platform="huggingface_spaces",
        available_analyses=[
            "sentiment",
            "volume_analysis",
            "price_patterns",
            "basic_stats",
            "stock_predictions"
        ]
    )


@app.post("/analyze")
async def analyze(request: AnalysisRequest):
    """
    Process trade analysis requests

    This endpoint receives trade data and performs requested analyses
    """
    try:
        results = {}

        # Basic sentiment analysis (lightweight for free tier)
        if "sentiment" in request.analysis_types:
            results["sentiment"] = await analyze_sentiment(request.trades)

        # Volume analysis
        if "volume_analysis" in request.analysis_types:
            results["volume"] = await analyze_volume(request.trades)

        # Price patterns
        if "price_patterns" in request.analysis_types:
            results["patterns"] = await analyze_patterns(request.trades)

        return {
            "status": "success",
            "worker_id": "huggingface-worker-1",
            "results": results,
            "trades_processed": len(request.trades)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict")
async def predict(request: PredictionRequest):
    """
    Generate stock predictions

    Distributed prediction endpoint for parallel processing
    """
    try:
        from datetime import datetime

        # Use baseline predictor (lightweight for free tier)
        # For production, load trained ML models
        try:
            # Try to import predictor
            from ml_models.stock_predictor import BaselinePredictor
            predictor = BaselinePredictor()
        except:
            # Fallback to simple prediction
            return {
                "status": "error",
                "message": "Predictor not available on this worker",
                "worker_id": "huggingface-worker"
            }

        predictions = []
        current_date = datetime.fromisoformat(request.date) if request.date else datetime.now()

        for ticker in request.tickers:
            try:
                prediction = predictor.predict(
                    ticker=ticker,
                    trades=request.trades,
                    current_date=current_date,
                    price_history=None  # Not available on worker
                )

                # Filter by confidence
                if prediction['confidence'] >= request.confidence_threshold:
                    predictions.append(prediction)

            except Exception as e:
                # Skip failed predictions
                pass

        return {
            "status": "success",
            "worker_id": "huggingface-worker",
            "predictions": predictions,
            "tickers_processed": len(request.tickers),
            "predictions_generated": len(predictions)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def analyze_sentiment(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Lightweight sentiment analysis"""
    # Simplified analysis for free tier compute
    positive = sum(1 for t in trades if t.get('price_change', 0) > 0)
    negative = sum(1 for t in trades if t.get('price_change', 0) < 0)
    neutral = len(trades) - positive - negative

    return {
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
        "overall_sentiment": "positive" if positive > negative else "negative"
    }


async def analyze_volume(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Volume analysis"""
    volumes = [t.get('volume', 0) for t in trades]
    avg_volume = sum(volumes) / len(volumes) if volumes else 0

    return {
        "average_volume": avg_volume,
        "total_volume": sum(volumes),
        "max_volume": max(volumes) if volumes else 0,
        "min_volume": min(volumes) if volumes else 0
    }


async def analyze_patterns(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Basic price pattern detection"""
    prices = [t.get('price', 0) for t in trades]

    if len(prices) < 3:
        return {"pattern": "insufficient_data"}

    # Simple trend detection
    increasing = sum(1 for i in range(1, len(prices)) if prices[i] > prices[i-1])
    decreasing = sum(1 for i in range(1, len(prices)) if prices[i] < prices[i-1])

    if increasing > decreasing * 1.5:
        pattern = "uptrend"
    elif decreasing > increasing * 1.5:
        pattern = "downtrend"
    else:
        pattern = "sideways"

    return {
        "pattern": pattern,
        "strength": abs(increasing - decreasing) / len(prices),
        "price_range": max(prices) - min(prices) if prices else 0
    }


if __name__ == "__main__":
    # HuggingFace Spaces runs on port 7860 by default
    port = int(os.getenv("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
