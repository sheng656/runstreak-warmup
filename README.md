# RunStreak Daily Warmup

Automated daily warmup tool for [runstreak.sheng.nz](https://runstreak.sheng.nz/) to eliminate Azure backend cold-start delays.

---

## Overview

The backend for **RunStreak** is hosted on Azure. When idle, the backend instance scales down to save resources, causing a **1-2 minute cold-start delay** on the first visit of the day.

This repository runs an automated headless browser task every morning at **08:00 AM Auckland Time (New Zealand)**. It navigates to the website, executes the demo login workflow, and waits for the dashboard and backend APIs to fully initialize. Subsequent visits by users will be fast and responsive with zero cold start.

> **Note:** This process performs read and authentication operations only; it **does not create or modify any run logs**.

---

## Workflow

When triggered by GitHub Actions on schedule:

1. **Launches an Ubuntu environment** with headless Chromium.
2. **Navigates to the homepage** (`https://runstreak.sheng.nz/`).
3. **Opens the demo login modal** by clicking `MSA Marker Demo`.
4. **Submits credentials** via `Sign In` to authenticate.
5. **Waits for dashboard rendering**, ensuring the Azure container and database are fully active and warm.

---

## Repository Structure

| File | Description |
| :--- | :--- |
| [`warmup.py`](file:///d:/Dev/runstreak-warmup/warmup.py) | Playwright automation script executing the warmup sequence |
| [`.github/workflows/daily-warmup.yml`](file:///d:/Dev/runstreak-warmup/.github/workflows/daily-warmup.yml) | Scheduled GitHub Actions workflow running daily at 08:00 AM NZ time |

---

## Setup & Deployment

1. **Push this repository** (including `warmup.py` and `.github/workflows/daily-warmup.yml`) to GitHub.
2. Go to **Settings -> Actions -> General** in your GitHub repository and ensure **"Allow all actions and reusable workflows"** is enabled.
3. In the **Actions** tab, select **Daily Warmup** and click **Run workflow** (`workflow_dispatch`) to verify the execution.
4. The workflow will run automatically every day at 08:00 AM NZ time without requiring manual intervention.

---

## Timezone & Daylight Saving Time (NZST / NZDT)

GitHub Actions cron expressions operate in **UTC**:

- **NZST (Standard / Winter Time, UTC+12)**: 08:00 AM NZ = 20:00 UTC (previous day) -> `0 20 * * *` *(Active)*
- **NZDT (Daylight Saving / Summer Time, UTC+13)**: 08:00 AM NZ = 19:00 UTC (previous day) -> `0 19 * * *`

> **Note:** New Zealand Daylight Saving Time typically begins on the last Sunday of September and ends on the first Sunday of April. When daylight saving begins, switch the cron expression in [`.github/workflows/daily-warmup.yml`](file:///d:/Dev/runstreak-warmup/.github/workflows/daily-warmup.yml) to `0 19 * * *`.

---

## Local Development & Testing

```bash
# Install dependencies
pip install playwright
playwright install chromium

# Run warmup script
python warmup.py
```

Exit codes:
- `0`: Success (page and backend reached and verified).
- `1`: Failure (exception encountered or timeout exceeded).
