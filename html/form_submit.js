let HEADERS = [];

const SHEET_URL = "https://wix-fastapi-nabis-545041871674.us-east1.run.app/sheet";
const RANGE_TO_APPEND = "Sheet1!A:J";


$w.onReady(async function () {
  // Load headers so we know the column order for submissions
  await loadHeaders();

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

      const rowObj = buildRowObjectFromForm();
      const rowValues = HEADERS.map(h => normalizeCell(rowObj[h]));

      await appendRowToBackend(rowValues);

      if ($w("#formStatusText")) $w("#formStatusText").text = "Saved!";
      clearFormInputs();
    } catch (e) {
      console.error(e);
      if ($w("#formStatusText")) $w("#formStatusText").text = `Error: ${e.message || e}`;
    } finally {
      $w("#sendBtn").enable();
    }
  });
});

async function loadHeaders() {
  const res = await fetch(SHEET_URL + "?header_row=1", {
    method: "GET",
    headers: {
      "ngrok-skip-browser-warning": "true",
      "Accept": "application/json"
    }
  });

  const text = await res.text();
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${text.slice(0, 120)}`);

  const payload = JSON.parse(text);
  HEADERS = (payload.headers || []).filter(h => (h || "").trim().length > 0);
}

function buildRowObjectFromForm() {
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
    value: [rowValues]
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

  try { return JSON.parse(text); } catch { return { message: text }; }
}

function clearFormInputs() {
  $w("#orgNameInput").value = "";
  $w("#regionInput").value = "";
  $w("#websiteInput").value = "";
  $w("#otherInput").value = "";

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
