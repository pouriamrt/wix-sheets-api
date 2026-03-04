let ALL_ROWS = [];
let HEADERS = [];

const RELOAD_INTERVAL_MS = 2 * 60 * 1000; // 2 minutes
const SHEET_URL = "https://wix-fastapi-nabis-545041871674.us-east1.run.app/sheet";


$w.onReady(async function () {
  await refreshDataAndUI();

  // Auto-reload every 2 minutes
  setInterval(async () => {
    try {
      await refreshDataAndUI();
      console.log("Auto-reloaded sheet data");
    } catch (e) {
      console.error("Auto-reload failed:", e);
    }
  }, RELOAD_INTERVAL_MS);

  // Listen for messages from HTML UI (only once)
  $w("#html1").onMessage((event) => {
    const msg = event.data;
    if (!msg || typeof msg !== "object") return;

    if (msg.type === "FILTERS_CHANGED") {
      console.log("Filters from HTML:", msg.filters);
    }
  });
});

async function refreshDataAndUI() {
  await loadSheet();

  $w("#html1").postMessage({
    type: "INIT_DATA",
    rows: ALL_ROWS,
    headers: HEADERS
  });

  const cardMap = {
    title: ["Organization Name"],
    address: ["Region", "Country"],
    services: ["Services / Resources"],
    cost: ["Scope"],
    funding: ["Type", "Population Served"],
    logo: [],
    url: ["Website"]
  };

  $w("#html1").postMessage({
    type: "SET_CARD_MAP",
    map: cardMap
  });
}

async function loadSheet() {
  const API_URL = SHEET_URL + "?header_row=1";

  const res = await fetch(API_URL, {
    method: "GET",
    headers: {
      "ngrok-skip-browser-warning": "true",
      "Accept": "application/json"
    }
  });

  const contentType = res.headers.get("content-type") || "";
  const text = await res.text();

  if (!res.ok) throw new Error(`HTTP ${res.status}: ${text.slice(0, 120)}`);
  if (!contentType.includes("application/json")) throw new Error("Not JSON returned from server.");

  const payload = JSON.parse(text);

  ALL_ROWS = (payload.rows || []).map((r, i) => ({ _id: String(i), ...r }));
  HEADERS = (payload.headers || []).filter(h => (h || "").trim().length > 0);
}
