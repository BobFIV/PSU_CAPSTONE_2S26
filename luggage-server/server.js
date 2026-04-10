const express = require("express");
const app = express();

app.use(express.json());
app.use(express.static("public"));

/* ---------------- DATA ---------------- */
function enableNotifications(){

  if(!("Notification" in window)){
    notifMsg.innerText="Notifications not supported";
    return;
  }

  Notification.requestPermission()
    .then(permission=>{
      if(permission==="granted"){
        notifMsg.innerText="Notifications enabled!";
      } else {
        notifMsg.innerText="Permission denied";
      }
    });
}


// Modify HERE for oneM2M (I think)
let proximity = {
  distance_cm: 0,
  confidence: 0,
  state: "unknown"
};

let alerts = {
  separation_alert: false,
  timestamp: null
};

let wheelchairStatus = {
  battery_level: 90,
  server_state: "running",
  link_state: "connected",
  last_update_time: new Date()
};

/* -------------- API ------------------ */

app.post("/api/proximity", (req, res) => {
  const { distance_cm, confidence } = req.body;

  proximity.distance_cm = distance_cm;
  proximity.confidence = confidence;
  wheelchairStatus.last_update_time = new Date();

  // NEW THRESHOLDS
  if (distance_cm > 300) {
    proximity.state = "separation";
    alerts.separation_alert = true;
  } 
  else if (distance_cm > 150) {
    proximity.state = "caution";
    alerts.separation_alert = false;
  } 
  else {
    proximity.state = "normal";
    alerts.separation_alert = false;
  }

  res.json({ success: true });
});

app.get("/api/proximity", (req, res) => res.json(proximity));
app.get("/api/alerts", (req, res) => res.json(alerts));
app.get("/api/status", (req, res) => res.json(wheelchairStatus));

/* -------------- START ---------------- */

app.listen(3000, () =>
  console.log("Server running at http://localhost:3000")
);
