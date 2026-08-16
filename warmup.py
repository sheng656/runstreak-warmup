#!/usr/bin/env python3
"""
RunStreak 每日预热脚本
======================
目的：每天自动打开一次 runstreak.sheng.nz 并完成登录流程，
      让 Azure 后端保持"热身"状态，避免后续真人访问时遇到冷启动延迟。

流程：
  1. 打开 https://runstreak.sheng.nz/
  2. 点击首页 "MSA Marker Demo" 按钮（触发登录框，并自动填入 test 账号）
  3. 在弹出的登录框内点击 "Sign In" 完成登录
  4. 等待 dashboard 加载完成（后端被预热）

注意：本脚本不写入任何跑步记录（Log Run），仅做登录访问以预热后端。
"""

import sys
import time
from playwright.sync_api import sync_playwright

BASE_URL = "https://runstreak.sheng.nz/"

# 登录后最多等待 dashboard 就绪的秒数（含 Azure 冷启动缓冲）
LOGIN_TIMEOUT = 120
PAGE_READY_TIMEOUT = 180


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
        page.set_default_timeout(PAGE_READY_TIMEOUT * 1000)

        try:
            log("1) 打开首页 ...")
            page.goto(BASE_URL, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            log(f"   当前 URL: {page.url}")

            # 如果已经登录（直接进了 dashboard），则无需再登录
            if "/login" not in page.url:
                log("   已在 dashboard，无需登录，后端已热身。")
                browser.close()
                return True

            # 2) 点击 "MSA Marker Demo" 触发登录框（自动填充 test 账号）
            log("2) 点击 'MSA Marker Demo' ...")
            page.click('button:has-text("MSA Marker Demo")')
            page.wait_for_timeout(1500)

            # 校验自动填充是否生效
            filled = page.evaluate(
                """() => {
                    const e = document.querySelector('#login-email')
                             || document.querySelector('input[name=email],input[name=username],input[type=email],input[type=text]');
                    const pw = document.querySelector('#login-password')
                             || document.querySelector('input[type=password]');
                    return { email: e ? e.value : null, pw: pw ? pw.value : null };
                }"""
            )
            log(f"   登录框自动填充: email={filled.get('email')!r} pw={'***' if filled.get('pw') else None}")

            # 3) 在登录框(modal)内点击 "Sign In"
            log("3) 在登录框内点击 'Sign In' ...")
            modal_signin = page.locator('.fixed.inset-0 button:has-text("Sign In")').last
            modal_signin.click()
            log("   等待 dashboard 加载（含 Azure 冷启动缓冲）...")
            page.wait_for_timeout(LOGIN_TIMEOUT * 1000)

            final_url = page.url
            log(f"   登录后 URL: {final_url}")

            if "/login" in final_url:
                log("   ⚠ 仍处于登录页，登录可能未成功。")
                browser.close()
                return False

            # 4) 确认 dashboard 关键内容已渲染
            log("4) 校验 dashboard 已加载 ...")
            page.wait_for_selector('text=Test Runner', timeout=PAGE_READY_TIMEOUT * 1000)
            log("   ✅ dashboard 加载完成，后端已热身。")
            browser.close()
            return True

        except Exception as e:
            log(f"   ❌ 发生异常: {e}")
            try:
                browser.close()
            except Exception:
                pass
            return False


if __name__ == "__main__":
    ok = warmup()
    sys.exit(0 if ok else 1)
