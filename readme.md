# Official Github Repository for the Smart Luggage Logistics and Connectivity for Wheelchair Travelers Project

This GitHub Repository contains all of the code used for the Smart Luggage Logistics and Connectivity for Wheelchair Travelers Project. 

The repository has three main sections of code:

1. Code for the front end webtool
2. Code used on the raspberry pi with oneM2M
3. Code used for channel sounding. 

Each heading below will provide the necessary information about each section. 

## Front End Website

The front end website provides a real time interface to monitor the status of one's luggage in relation to the wheelchair. There are two distinct views, the user view and the developer view (the developer view has more detailed information than simply if the luggage is detached or not).

**Features**

- **Real time updates**
- **Color coded status indicator**
      - Green for normal
      - Yellow for caution
      - Red for separation
- **Adjustable thresholds for each status level**
      - The user can input at what distance away the luggage should be in order to receive an alert.

**Running the front end**

index.html contains the full front-end implementation, including the UI layout, styling, and JavaScript logic.

- Start the backend server by running node server.js
- Navigate to http://localhost:3000 in a browser to see the web tool


## oneM2M 

## Channel Sounding

Channel sounding Initiator and Reflector code started from the samples Bluetooth LE Channel Sounding Initiator with RREQ and Bluetooth LE Channel Sounding Reflector with RRSP. Below are the changes made from those samples specifically for this project

- **Added a sliding window over distance estimates**
    - Stores the last `DE_SLIDING_WINDOW_SIZE` results per antenna path (AP).
    - Computes a per-estimator smoothed value (IFFT / phase_slope / RTT) using a trimmed mean over the window.

- **Changed Estimator preference to be IFFT/phase-slope based**
    - Fusion prioritizes IFFT + phase_slope when both are valid and agree within a threshold.
    - RTT is treated as a weak helper and is only blended in when it agrees tightly with the IFFT/phase-slope fused value.

- **Multi-antenna path handling**
    - If multiple antenna paths are available, computes a fused distance per AP and selects the AP with the smallest estimator spread (best internal agreement).

- **Robust outlier rejection on the final measurement stream**
    - Maintains a history window (`MAD_WIN`) of recent outputs and applies a median/MAD gate.
    - Measurements that deviate too far from the recent median are rejected and replaced with the median-based value.

- **Added Two-stage temporal smoothing on the final output**
    - Stage 1: Alpha–beta filter (constant-velocity tracker) to smooth jitter while still tracking movement.
    - Stage 2: EMA smoothing after the alpha–beta filter to further reduce small oscillations.
    - Uses adaptive gains: when a frame looks unreliable (outlier gate triggers or AP spread is large), the filter updates more conservatively.

- **Output Behavior**
    - Prints distance value per output in meters
    - Prints unique tag ID once every twenty distance messages

- **Build**
    - To build the code, first you must have a Nordic Semiconductor nrf54l15 device
    - You must also install the nRF connect vs-code extension. 
    - You must build code for both the Initiator and Reflector, then flash that build to each device respectively. 
        - A common issue with building is the filepath becomes too long. Make sure to build the code in the root director of your computer (directly on the C drive if in windows).
        - If you need more help with building, view nordic semiconductor's trainings for more information. 
