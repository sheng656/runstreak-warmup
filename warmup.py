#!/usr/bin/env python3
"""
RunStreak Daily Warmup Script
=============================
Purpose: Automatically open and log into runstreak.sheng.nz once a day
         to eliminate Azure backend cold start latency (~1-2 minutes)
         for subsequent real users.

Flow:
  1. Open https://runstreak.sheng.nz/ and wait up to 3 minutes for initial cold start.
  2. Wait for interactive elements (demo button, sign in button, or dashboard) to render.
  3. If not already authenticated, trigger demo login and submit credentials.
  4. Wait for dashboard to finish loading and confirm the backend is warmed up.

Note: This script performs read/login operations only and does not create or modify run records.
"""

import sys
import time
from playwright.sync_api import sync_playwright

BASE_URL = "https://runstreak.sheng.nz/"

# Timeouts in seconds (allowing ample time for Azure cold starts)
COLD_START_TIMEOUT = 180
LOGIN_TIMEOUT = 120


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def warmup() -> bool:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            )
        )
        page = context.new_page()
        # Set default timeout to 180s to accommodate cold start delays across all actions
        page.set_default_timeout(COLD_START_TIMEOUT * 1000)

        try:
            log("Step 1: Navigating to home page (waiting for initial cold start)...")
            page.goto(BASE_URL, wait_until="load", timeout=COLD_START_TIMEOUT * 1000)

            log("   Waiting for interactive UI to render after backend cold boot...")
            # Wait for either login interactive buttons or dashboard elements to appear (up to 180s)
            interactive_target = page.locator(
                "button:has-text('MSA Marker Demo'), button:has-text('Sign In'), :text('Test Runner')"
            ).first
            interactive_target.wait_for(timeout=COLD_START_TIMEOUT * 1000)
            log(f"   UI rendered. Current URL: {page.url}")

            # If already authenticated and dashboard is present, warmup is complete
            if page.locator(":text('Test Runner')").count() > 0 or ("/login" not in page.url and page.locator("button:has-text('MSA Marker Demo')").count() == 0):
                log("   [SUCCESS] Already on dashboard. Azure backend is warm.")
                browser.close()
                return True

            # Step 2: Trigger demo login modal
            log("Step 2: Clicking 'MSA Marker Demo' button...")
            page.click("button:has-text('MSA Marker Demo')", timeout=COLD_START_TIMEOUT * 1000)
            page.wait_for_timeout(1000)

            # Ensure credentials are populated, fallback if not
            email_input = page.locator("#login-email")
            if email_input.count() > 0 and not email_input.input_value():
                log("   Notice: Auto-fill empty, manually providing demo credentials...")
                page.fill("#login-email", "testuser")
                page.fill("#login-password", "Test1234!")

            # Step 3: Click "Sign In" in the modal
            log("Step 3: Clicking 'Sign In' inside the login modal...")
            modal_signin = page.locator(".fixed.inset-0 button:has-text('Sign In')").last
            modal_signin.click(timeout=COLD_START_TIMEOUT * 1000)

            log("   Waiting for dashboard transition (accommodating backend auth delay)...")
            page.wait_for_url(lambda u: "/login" not in u, timeout=LOGIN_TIMEOUT * 1000)
            log(f"   Post-login URL: {page.url}")

            # Step 4: Verify dashboard key element rendered
            log("Step 4: Verifying dashboard content rendered...")
            dashboard_element = page.locator(":text('Test Runner')").first
            dashboard_element.wait_for(timeout=COLD_START_TIMEOUT * 1000)
            log("   [SUCCESS] Dashboard loaded successfully. Azure backend is warm.")
            browser.close()
            return True

        except Exception as e:
            log(f"   [ERROR] Warmup failed: {e}")
            try:
                browser.close()
            except Exception:
                pass
            return False


if __name__ == "__main__":
    success = warmup()
    sys.exit(0 if success else 1)
