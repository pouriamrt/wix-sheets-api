const BASE_URL = "https://wix-fastapi-nabis-545041871674.us-east1.run.app";

const FETCH_HEADERS = {
  "Content-Type": "application/json",
  "ngrok-skip-browser-warning": "true",
  "Accept": "application/json"
};


$w.onReady(function () {
  $w("#sendBtn").onClick(handleEntrySubmit);
  $w("#commentBtn").onClick(handleCommentSubmit);
});


async function handleEntrySubmit() {
  const entryData = buildEntryData();

  if (!hasAnyEntryInput(entryData)) {
    setStatus("#formStatusText", "Please fill at least one field.");
    return;
  }

  setStatus("#formStatusText", "Sending...");
  $w("#sendBtn").disable();

  try {
    await postJSON("/entry", { data: stripEmpty(entryData) });
    setStatus("#formStatusText", "Saved!");
    clearFormInputs();
  } catch (e) {
    console.error(e);
    setStatus("#formStatusText", `Error: ${e.message || e}`);
  } finally {
    $w("#sendBtn").enable();
  }
}


async function handleCommentSubmit() {
  const comment = ($w("#commentInput").value || "").trim();

  if (!comment) {
    setStatus("#commentStatusText", "Please enter a comment.");
    return;
  }

  setStatus("#commentStatusText", "Sending...");
  $w("#commentBtn").disable();

  try {
    await postJSON("/comment", { comment });
    setStatus("#commentStatusText", "Comment submitted!");
    $w("#commentInput").value = "";
  } catch (e) {
    console.error(e);
    setStatus("#commentStatusText", `Error: ${e.message || e}`);
  } finally {
    $w("#commentBtn").enable();
  }
}


function buildEntryData() {
  return {
    "Organization Name": ($w("#orgNameInput").value || "").trim(),
    "Country": $w("#countryDropdown").value || "",
    "Scope": $w("#scopeDropdown").value || "",
    "Region": ($w("#regionInput").value || "").trim(),
    "Type": joinMulti($w("#typeCheckbox").value),
    "Population Served": joinMulti($w("#populationCheckbox").value),
    "Services / Resources": joinMulti($w("#servicesCheckbox").value),
    "Website": ($w("#websiteInput").value || "").trim(),
    "Other": ($w("#otherInput").value || "").trim()
  };
}


function hasAnyEntryInput(data) {
  return Object.values(data).some(v => (v || "").trim().length > 0);
}


function joinMulti(arr) {
  if (!Array.isArray(arr) || arr.length === 0) return "";
  return arr.join(", ");
}


function stripEmpty(data) {
  const result = {};
  for (const [k, v] of Object.entries(data)) {
    if ((v || "").trim()) result[k] = v;
  }
  return result;
}


async function postJSON(path, body) {
  const res = await fetch(BASE_URL + path, {
    method: "POST",
    headers: FETCH_HEADERS,
    body: JSON.stringify(body)
  });

  const text = await res.text();
  if (!res.ok) throw new Error(`POST ${path} failed HTTP ${res.status}: ${text.slice(0, 200)}`);

  try { return JSON.parse(text); } catch { return { message: text }; }
}


function setStatus(selector, message) {
  if ($w(selector)) $w(selector).text = message;
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
