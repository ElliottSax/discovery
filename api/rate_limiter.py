"""
Rate limiting for API endpoints
"""

import time
from collections import defaultdict, deque
from typing import Dict, Optional
from fastapi import Request
import asyncio

class RateLimiter:
    """
    Simple in-memory rate limiter
    In production, use Redis for distributed rate limiting
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        requests_per_day: int = 10000
    ):
        """
        Initialize rate limiter
        
        Args:
            requests_per_minute: Max requests per minute
            requests_per_hour: Max requests per hour
            requests_per_day: Max requests per day
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests_per_day = requests_per_day
        
        # Store request timestamps per IP
        self.requests: Dict[str, deque] = defaultdict(deque)
        
        # Cleanup task
        self.cleanup_task = None
        
    def get_client_ip(self, request: Request) -> str:
        """
        Get client IP from request
        
        Args:
            request: FastAPI request object
            
        Returns:
            Client IP address
        """
        # Check for proxy headers
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
            
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
            
        # Default to client host
        return request.client.host if request.client else "unknown"
        
    async def check_rate_limit(self, request: Request) -> bool:
        """
        Check if request is within rate limits
        
        Args:
            request: FastAPI request object
            
        Returns:
            True if within limits, False otherwise
        """
        client_ip = self.get_client_ip(request)
        current_time = time.time()
        
        # Get request history for this IP
        request_times = self.requests[client_ip]
        
        # Remove old requests (older than 24 hours)
        cutoff_time = current_time - 86400  # 24 hours
        while request_times and request_times[0] < cutoff_time:
            request_times.popleft()
            
        # Add current request
        request_times.append(current_time)
        
        # Check rate limits
        
        # Per minute
        minute_ago = current_time - 60
        minute_requests = sum(1 for t in request_times if t > minute_ago)
        if minute_requests > self.requests_per_minute:
            return False
            
        # Per hour
        hour_ago = current_time - 3600
        hour_requests = sum(1 for t in request_times if t > hour_ago)
        if hour_requests > self.requests_per_hour:
            return False
            
        # Per day
        day_ago = current_time - 86400
        day_requests = len(request_times)  # All requests are within 24 hours
        if day_requests > self.requests_per_day:
            return False
            
        return True
        
    def get_rate_limit_info(self, request: Request) -> Dict:
        """
        Get rate limit information for client
        
        Args:
            request: FastAPI request object
            
        Returns:
            Rate limit status
        """
        client_ip = self.get_client_ip(request)
        current_time = time.time()
        request_times = self.requests[client_ip]
        
        # Calculate requests in different time windows
        minute_ago = current_time - 60
        hour_ago = current_time - 3600
        
        minute_requests = sum(1 for t in request_times if t > minute_ago)
        hour_requests = sum(1 for t in request_times if t > hour_ago)
        day_requests = len(request_times)
        
        return {
            "ip": client_ip,
            "requests": {
                "per_minute": {
                    "used": minute_requests,
                    "limit": self.requests_per_minute,
                    "remaining": max(0, self.requests_per_minute - minute_requests)
                },
                "per_hour": {
                    "used": hour_requests,
                    "limit": self.requests_per_hour,
                    "remaining": max(0, self.requests_per_hour - hour_requests)
                },
                "per_day": {
                    "used": day_requests,
                    "limit": self.requests_per_day,
                    "remaining": max(0, self.requests_per_day - day_requests)
                }
            },
            "reset_times": {
                "minute": 60 - (current_time % 60),
                "hour": 3600 - (current_time % 3600),
                "day": 86400 - (current_time % 86400)
            }
        }
        
    async def cleanup_old_requests(self):
        """
        Periodically clean up old request records
        """
        while True:
            await asyncio.sleep(3600)  # Run every hour
            
            current_time = time.time()
            cutoff_time = current_time - 86400  # 24 hours
            
            # Clean up old requests
            for ip in list(self.requests.keys()):
                request_times = self.requests[ip]
                
                # Remove old requests
                while request_times and request_times[0] < cutoff_time:
                    request_times.popleft()
                    
                # Remove IP if no recent requests
                if not request_times:
                    del self.requests[ip]
                    
    def start_cleanup(self):
        """Start the cleanup task"""
        if not self.cleanup_task:
            self.cleanup_task = asyncio.create_task(self.cleanup_old_requests())