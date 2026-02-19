## Channel Sounding

- **Added a sliding window over distance estimates**
  - Stores the last `DE_SLIDING_WINDOW_SIZE` results per antenna path (AP).
  - Computes a per-estimator smoothed value (IFFT / phase_slope / RTT) using a **trimmed mean** over the window.

- **Changed the estimator preference to be IFFT/phase-slope based**
  - Fusion prioritizes **IFFT + phase_slope** when both are valid and agree within a threshold.
  - RTT is treated as a weak helper and is only blended in when it **agrees tightly** with the IFFT/phase-slope fused value.

- **Multi-antenna path handling**
  - If multiple antenna paths are available, computes a fused distance per AP and selects the AP with the **smallest estimator spread** (best internal agreement).

- **Robust outlier rejection on the final measurement stream**
  - Maintains a history window (`MAD_WIN`) of recent outputs and applies a **median/MAD gate**.
  - Measurements that deviate too far from the recent median are rejected and replaced with the median-based value.

- **Added two-stage temporal smoothing on the final output**
  - Stage 1: **Alpha–beta filter** (constant-velocity tracker) to smooth jitter while still tracking movement.
  - Stage 2: **EMA smoothing** after the alpha–beta filter to further reduce small oscillations.
  - Uses **adaptive gains**: when a frame looks unreliable (outlier gate triggers or AP spread is large), the filter updates more conservatively.

- **Output behavior**
 - Prints one value per output in meters
