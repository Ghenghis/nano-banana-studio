"""
Nano Banana Studio Pro - 2Captcha Integration for Suno
========================================================
Automatic CAPTCHA solving for Suno API when hCaptcha is triggered.

Install:
    pip install 2captcha-python

Usage:
    solver = CaptchaSolver()
    token = await solver.solve_hcaptcha(site_key, page_url)
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger("captcha-solver")

# Check if 2captcha is installed
try:
    from twocaptcha import TwoCaptcha
    TWOCAPTCHA_AVAILABLE = True
except ImportError:
    TWOCAPTCHA_AVAILABLE = False
    logger.warning("2captcha-python not installed. Run: pip install 2captcha-python")


@dataclass
class CaptchaResult:
    """Result from CAPTCHA solving"""
    success: bool
    token: Optional[str] = None
    cost: float = 0.0
    solve_time: float = 0.0
    error: Optional[str] = None


class CaptchaSolver:
    """
    2Captcha integration for automatic CAPTCHA solving.
    
    Supports:
    - hCaptcha (used by Suno)
    - reCAPTCHA v2/v3
    - Image CAPTCHA
    - Turnstile
    
    Setup:
        1. Create account at https://2captcha.com
        2. Add funds (starts at $3)
        3. Get API key from dashboard
        4. Set TWOCAPTCHA_API_KEY environment variable
    
    Pricing (as of 2024):
        - hCaptcha: $2.99 per 1000
        - reCAPTCHA v2: $2.99 per 1000
        - reCAPTCHA v3: $2.99 per 1000
    
    Example:
        solver = CaptchaSolver()
        result = await solver.solve_hcaptcha(
            site_key="your-site-key",
            page_url="https://suno.com"
        )
        if result.success:
            print(f"Token: {result.token}")
    """
    
    # Suno's known hCaptcha site key (may change)
    SUNO_HCAPTCHA_SITEKEY = "a9b5fb07-92ff-493f-86fe-352a2803b3df"
    SUNO_URL = "https://suno.com"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize CAPTCHA solver.
        
        Args:
            api_key: 2Captcha API key (or uses TWOCAPTCHA_API_KEY env var)
        """
        if not TWOCAPTCHA_AVAILABLE:
            raise ImportError(
                "2captcha-python not installed. Run: pip install 2captcha-python"
            )
        
        self.api_key = api_key or os.getenv("TWOCAPTCHA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "2Captcha API key required. Set TWOCAPTCHA_API_KEY env var or pass api_key."
            )
        
        self.solver = TwoCaptcha(self.api_key)
        
        # Statistics
        self.total_solved = 0
        self.total_cost = 0.0
        self.total_time = 0.0
        
        logger.info("CaptchaSolver initialized")
    
    async def solve_hcaptcha(
        self,
        site_key: Optional[str] = None,
        page_url: Optional[str] = None,
        invisible: bool = False
    ) -> CaptchaResult:
        """
        Solve hCaptcha challenge.
        
        Args:
            site_key: hCaptcha site key (defaults to Suno's key)
            page_url: Page URL where CAPTCHA appears
            invisible: Whether it's invisible hCaptcha
            
        Returns:
            CaptchaResult with token if successful
        """
        site_key = site_key or self.SUNO_HCAPTCHA_SITEKEY
        page_url = page_url or self.SUNO_URL
        
        logger.info(f"Solving hCaptcha for {page_url}...")
        start_time = datetime.now()
        
        try:
            # Run in thread pool since 2captcha is sync
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.solver.hcaptcha(
                    sitekey=site_key,
                    url=page_url,
                    invisible=invisible
                )
            )
            
            solve_time = (datetime.now() - start_time).total_seconds()
            
            # Update stats
            self.total_solved += 1
            self.total_time += solve_time
            # Approximate cost
            cost = 0.003  # $2.99 per 1000
            self.total_cost += cost
            
            logger.info(f"hCaptcha solved in {solve_time:.1f}s")
            
            return CaptchaResult(
                success=True,
                token=result.get("code") if isinstance(result, dict) else result,
                cost=cost,
                solve_time=solve_time
            )
            
        except Exception as e:
            solve_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"hCaptcha solve failed: {e}")
            
            return CaptchaResult(
                success=False,
                error=str(e),
                solve_time=solve_time
            )
    
    async def solve_recaptcha_v2(
        self,
        site_key: str,
        page_url: str,
        invisible: bool = False
    ) -> CaptchaResult:
        """
        Solve reCAPTCHA v2.
        
        Args:
            site_key: Google reCAPTCHA site key
            page_url: Page URL
            invisible: Whether invisible reCAPTCHA
            
        Returns:
            CaptchaResult with token
        """
        logger.info(f"Solving reCAPTCHA v2 for {page_url}...")
        start_time = datetime.now()
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.solver.recaptcha(
                    sitekey=site_key,
                    url=page_url,
                    invisible=invisible
                )
            )
            
            solve_time = (datetime.now() - start_time).total_seconds()
            self.total_solved += 1
            cost = 0.003
            self.total_cost += cost
            
            return CaptchaResult(
                success=True,
                token=result.get("code") if isinstance(result, dict) else result,
                cost=cost,
                solve_time=solve_time
            )
            
        except Exception as e:
            return CaptchaResult(
                success=False,
                error=str(e),
                solve_time=(datetime.now() - start_time).total_seconds()
            )
    
    async def solve_recaptcha_v3(
        self,
        site_key: str,
        page_url: str,
        action: str = "verify",
        min_score: float = 0.3
    ) -> CaptchaResult:
        """
        Solve reCAPTCHA v3.
        
        Args:
            site_key: Google site key
            page_url: Page URL
            action: Action name
            min_score: Minimum score (0.1-0.9)
            
        Returns:
            CaptchaResult with token
        """
        logger.info(f"Solving reCAPTCHA v3 for {page_url}...")
        start_time = datetime.now()
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.solver.recaptcha(
                    sitekey=site_key,
                    url=page_url,
                    version="v3",
                    action=action,
                    score=min_score
                )
            )
            
            solve_time = (datetime.now() - start_time).total_seconds()
            self.total_solved += 1
            cost = 0.003
            self.total_cost += cost
            
            return CaptchaResult(
                success=True,
                token=result.get("code") if isinstance(result, dict) else result,
                cost=cost,
                solve_time=solve_time
            )
            
        except Exception as e:
            return CaptchaResult(
                success=False,
                error=str(e),
                solve_time=(datetime.now() - start_time).total_seconds()
            )
    
    async def solve_turnstile(
        self,
        site_key: str,
        page_url: str
    ) -> CaptchaResult:
        """
        Solve Cloudflare Turnstile.
        
        Args:
            site_key: Turnstile site key
            page_url: Page URL
            
        Returns:
            CaptchaResult with token
        """
        logger.info(f"Solving Turnstile for {page_url}...")
        start_time = datetime.now()
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.solver.turnstile(
                    sitekey=site_key,
                    url=page_url
                )
            )
            
            solve_time = (datetime.now() - start_time).total_seconds()
            self.total_solved += 1
            cost = 0.003
            self.total_cost += cost
            
            return CaptchaResult(
                success=True,
                token=result.get("code") if isinstance(result, dict) else result,
                cost=cost,
                solve_time=solve_time
            )
            
        except Exception as e:
            return CaptchaResult(
                success=False,
                error=str(e),
                solve_time=(datetime.now() - start_time).total_seconds()
            )
    
    async def solve_image(
        self,
        image_path: str = None,
        image_base64: str = None
    ) -> CaptchaResult:
        """
        Solve image CAPTCHA.
        
        Args:
            image_path: Path to CAPTCHA image
            image_base64: Base64 encoded image
            
        Returns:
            CaptchaResult with text
        """
        logger.info("Solving image CAPTCHA...")
        start_time = datetime.now()
        
        try:
            loop = asyncio.get_event_loop()
            
            if image_path:
                result = await loop.run_in_executor(
                    None,
                    lambda: self.solver.normal(image_path)
                )
            elif image_base64:
                result = await loop.run_in_executor(
                    None,
                    lambda: self.solver.normal(image_base64)
                )
            else:
                raise ValueError("Either image_path or image_base64 required")
            
            solve_time = (datetime.now() - start_time).total_seconds()
            self.total_solved += 1
            cost = 0.001  # Image CAPTCHAs are cheaper
            self.total_cost += cost
            
            return CaptchaResult(
                success=True,
                token=result.get("code") if isinstance(result, dict) else result,
                cost=cost,
                solve_time=solve_time
            )
            
        except Exception as e:
            return CaptchaResult(
                success=False,
                error=str(e),
                solve_time=(datetime.now() - start_time).total_seconds()
            )
    
    async def get_balance(self) -> float:
        """
        Get 2Captcha account balance.
        
        Returns:
            Account balance in USD
        """
        try:
            loop = asyncio.get_event_loop()
            balance = await loop.run_in_executor(
                None,
                self.solver.balance
            )
            return float(balance)
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return 0.0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get solver statistics.
        
        Returns:
            Dict with stats
        """
        return {
            "total_solved": self.total_solved,
            "total_cost": round(self.total_cost, 4),
            "total_time": round(self.total_time, 1),
            "avg_solve_time": round(self.total_time / max(1, self.total_solved), 1)
        }


# =============================================================================
# SUNO-SPECIFIC CAPTCHA HANDLER
# =============================================================================

class SunoCaptchaHandler:
    """
    Handles CAPTCHA challenges specifically for Suno API.
    
    Integrates with the Suno service to automatically solve
    CAPTCHAs when they occur during generation.
    
    Example:
        handler = SunoCaptchaHandler()
        
        # When CAPTCHA is detected
        if "captcha" in error.lower():
            token = await handler.solve()
            # Retry request with token
    """
    
    def __init__(self):
        """Initialize handler"""
        self.solver = None
        self._init_solver()
    
    def _init_solver(self):
        """Initialize solver if API key available"""
        api_key = os.getenv("TWOCAPTCHA_API_KEY")
        
        if api_key and TWOCAPTCHA_AVAILABLE:
            try:
                self.solver = CaptchaSolver(api_key)
                logger.info("CAPTCHA solver ready")
            except Exception as e:
                logger.warning(f"CAPTCHA solver init failed: {e}")
                self.solver = None
        else:
            logger.info("CAPTCHA solving not configured (set TWOCAPTCHA_API_KEY)")
    
    @property
    def available(self) -> bool:
        """Check if CAPTCHA solving is available"""
        return self.solver is not None
    
    async def solve(self) -> Optional[str]:
        """
        Solve Suno's hCaptcha.
        
        Returns:
            CAPTCHA token or None if failed/unavailable
        """
        if not self.available:
            logger.warning("CAPTCHA solving not available")
            return None
        
        result = await self.solver.solve_hcaptcha()
        
        if result.success:
            logger.info(f"CAPTCHA solved in {result.solve_time:.1f}s (${result.cost:.4f})")
            return result.token
        else:
            logger.error(f"CAPTCHA solve failed: {result.error}")
            return None
    
    async def check_balance(self) -> float:
        """Check 2Captcha balance"""
        if not self.available:
            return 0.0
        return await self.solver.get_balance()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get solving statistics"""
        if not self.available:
            return {"available": False}
        
        stats = self.solver.get_stats()
        stats["available"] = True
        return stats


# =============================================================================
# SINGLETON
# =============================================================================

_captcha_handler: Optional[SunoCaptchaHandler] = None

def get_captcha_handler() -> SunoCaptchaHandler:
    """Get or create CAPTCHA handler"""
    global _captcha_handler
    if _captcha_handler is None:
        _captcha_handler = SunoCaptchaHandler()
    return _captcha_handler


# =============================================================================
# CLI TEST
# =============================================================================

async def _test():
    """Test CAPTCHA solver"""
    handler = get_captcha_handler()
    
    print(f"CAPTCHA solving available: {handler.available}")
    
    if handler.available:
        balance = await handler.check_balance()
        print(f"2Captcha balance: ${balance:.2f}")
        
        # Uncomment to test actual solving (costs money!)
        # token = await handler.solve()
        # print(f"Token: {token[:50]}..." if token else "Failed")
        
        stats = handler.get_stats()
        print(f"Stats: {stats}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_test())
