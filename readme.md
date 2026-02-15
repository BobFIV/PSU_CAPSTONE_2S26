This is the readme for the 2026 Smart Luggage Logistics Capstone Project

## Channel Sounding Updates

### Overview
Started with the Channel Sounding Initiator with REEQ and Channel Sounding with RSSP Demos. Modified them to improve the distance estimation logic and simplify output handling.

### Changes Made
- Switched to Mode 3 (RTT + PBR) for improved measurement reliability.
- Implemented a best-estimate selector for distance:
  - Prefer RTT when valid.
  - Fallback to phase slope, then IFFT if RTT is unavailable.
  - If RTT and phase slope disagree significantly, select the smaller value (likely closer to the direct path).
  - If multiple antenna paths are enabled, choose the smallest valid estimate across paths.
- Output now prints a single distance value per update (in meters).