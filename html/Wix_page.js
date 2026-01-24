let ALL_ROWS = [];
let HEADERS = [];

const RELOAD_INTERVAL_MS = 5 * 60 * 1000; // 5 minutes
const SHEET_URL = "https://334431b039ac.ngrok-free.app/sheet";
const RANGE_TO_APPEND = "Sheet1!A:J"; // change if your tab is not Sheet1


$w.onReady(async function () {
  await refreshDataAndUI();

  // Auto-reload every 5 minutes
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
      // Optional: sync back to Wix elements if needed
    }
  });

  // SEND button -> append a row to Google Sheet through FastAPI
  $w("#sendBtn").onClick(async () => {
    try {
      if (!hasRequiredInputs()) {
        if ($w("#formStatusText")) {
          $w("#formStatusText").text = "Please fill all required fields.";
        }
        return;
      }

      if ($w("#formStatusText")) $w("#formStatusText").text = "Sending...";
      $w("#sendBtn").disable();

      // Build an object keyed by the sheet headers
      const rowObj = buildRowObjectFromForm();

      // Convert to row array in the exact current HEADERS order
      const rowValues = HEADERS.map(h => normalizeCell(rowObj[h]));

      // POST to backend (note: backend expects "value")
      await appendRowToBackend(rowValues);

      if ($w("#formStatusText")) $w("#formStatusText").text = "Saved!";
      clearFormInputs();

      // Refresh UI to show new row
      await refreshDataAndUI();
    } catch (e) {
      console.error(e);
      if ($w("#formStatusText")) $w("#formStatusText").text = `Error: ${e.message || e}`;
    } finally {
      $w("#sendBtn").enable();
    }
  });

});

async function refreshDataAndUI() {
  await loadSheet();

  // Always send latest headers + rows (schema + data)
  $w("#html1").postMessage({
    type: "INIT_DATA",
    rows: ALL_ROWS,
    headers: HEADERS
  });

  // Dynamic or fixed card map (kept as-is)
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

function buildRowObjectFromForm() {
  // Map UI -> sheet columns (match your actual sheet headers)
  return {
    "Organization Name": ($w("#orgNameInput").value || "").trim(),
    "Country": $w("#countryDropdown").value || "",
    "Scope": $w("#scopeDropdown").value || "",
    "Region": ($w("#regionInput").value || "").trim(),
    "Type": joinMulti($w("#typeCheckbox").value),
    "Population Served": joinMulti($w("#populationCheckbox").value),
    "Services / Resources": joinMulti($w("#servicesCheckbox").value),
    "Website": ($w("#websiteInput").value || "").trim(),
    "Other": ($w("#otherInput").value || "").trim(),
    "Entry verified": "False"
  };
}

function joinMulti(arr) {
  if (!arr || !Array.isArray(arr) || arr.length === 0) return "";
  return arr.join(", ");
}

function normalizeCell(v) {
  return (v === undefined || v === null) ? "" : v;
}

async function appendRowToBackend(rowValues) {
  const body = {
    range: RANGE_TO_APPEND,
    value: [rowValues] // IMPORTANT: backend expects "value", and it's 2D
  };

  const res = await fetch(SHEET_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "ngrok-skip-browser-warning": "true",
      "Accept": "application/json"
    },
    body: JSON.stringify(body)
  });

  const text = await res.text();
  if (!res.ok) throw new Error(`POST /sheet failed HTTP ${res.status}: ${text.slice(0, 200)}`);

  // If your backend returns JSON, parse it (safe)
  try { return JSON.parse(text); } catch { return { message: text }; }
}

function clearFormInputs() {
  $w("#orgNameInput").value = "";
  $w("#regionInput").value = "";
  $w("#websiteInput").value = "";
  $w("#otherInput").value = "";

  // For dropdowns you can also set a default value instead of clearing
  $w("#countryDropdown").value = "";
  $w("#scopeDropdown").value = "";

  $w("#typeCheckbox").value = [];
  $w("#populationCheckbox").value = [];
  $w("#servicesCheckbox").value = [];
}

function hasRequiredInputs() {
  return (
    ($w("#orgNameInput").value || "").trim().length > 0 &&
    ($w("#countryDropdown").value || "").trim().length > 0 &&
    ($w("#scopeDropdown").value || "").trim().length > 0 &&
    ($w("#regionInput").value || "").trim().length > 0 &&
    (($w("#typeCheckbox").value || []).length > 0) &&
    (($w("#populationCheckbox").value || []).length > 0) &&
    (($w("#servicesCheckbox").value || []).length > 0)
  );
}
