const state = {
  sessionId: "",
  scamDetected: false,
  takeoverAccepted: false,
  engagementComplete: false,
  finalResult: null,
};

const el = {
  sessionId: document.getElementById("sessionId"),
  newSessionBtn: document.getElementById("newSessionBtn"),
  timeline: document.getElementById("chatTimeline"),
  scammerInput: document.getElementById("scammerInput"),
  userInput: document.getElementById("userInput"),
  sendScammerBtn: document.getElementById("sendScammerBtn"),
  sendUserBtn: document.getElementById("sendUserBtn"),
  modeLabel: document.getElementById("modeLabel"),
  scamLabel: document.getElementById("scamLabel"),
  engagementLabel: document.getElementById("engagementLabel"),
  composerSection: document.getElementById("composerSection"),
  finalCenterPanel: document.getElementById("finalCenterPanel"),
  finalCenterContent: document.getElementById("finalCenterContent"),
  cybercrimeEmailInput: document.getElementById("cybercrimeEmailInput"),
  downloadReportBtn: document.getElementById("downloadReportBtn"),
  shareWhatsappBtn: document.getElementById("shareWhatsappBtn"),
  emailCybercrimeBtn: document.getElementById("emailCybercrimeBtn"),
  takeoverModal: document.getElementById("takeoverModal"),
  confirmTakeoverBtn: document.getElementById("confirmTakeoverBtn"),
  dismissTakeoverBtn: document.getElementById("dismissTakeoverBtn"),
};

function initSession() {
  state.sessionId = el.sessionId.value.trim() || `session-${Date.now()}`;
  el.sessionId.value = state.sessionId;
  state.scamDetected = false;
  state.takeoverAccepted = false;
  state.engagementComplete = false;
  state.finalResult = null;
  el.timeline.innerHTML = "";
  renderStatus();
  renderIntel();
  applyUiByState();
}

function renderStatus() {
  el.scamLabel.textContent = state.scamDetected ? "Yes" : "No";
  el.modeLabel.textContent = !state.scamDetected
    ? "Manual"
    : state.takeoverAccepted
      ? "Agent Takeover"
      : "Awaiting Takeover Approval";
  el.engagementLabel.textContent = state.engagementComplete ? "Completed" : "In Progress";
}

function appendMessage(sender, text, timestamp = "") {
  const bubble = document.createElement("div");
  bubble.className = `msg ${sender}`;
  bubble.innerHTML = `<div>${text}</div><small>${sender.toUpperCase()} ${timestamp ? "• " + new Date(timestamp).toLocaleTimeString() : ""}</small>`;
  el.timeline.appendChild(bubble);
  el.timeline.scrollTop = el.timeline.scrollHeight;
}

function appendWaitingBubble() {
  const bubble = document.createElement("div");
  bubble.className = "msg user waiting";
  bubble.innerHTML = `
    <div class="typing-dot"></div>
    <div class="typing-dot"></div>
    <div class="typing-dot"></div>
  `;
  el.timeline.appendChild(bubble);
}

function renderTimeline(history) {
  el.timeline.innerHTML = "";
  history.forEach((msg) => appendMessage(msg.sender, msg.text, msg.timestamp));

  const lastSender = history.length ? history[history.length - 1].sender : "";
  const showWaiting = !state.engagementComplete && lastSender === "scammer" && !state.takeoverAccepted;
  if (showWaiting) {
    appendWaitingBubble();
  }

  el.timeline.scrollTop = el.timeline.scrollHeight;
}

function listItems(items) {
  if (!items || !items.length) return "<span class=\"tag\">None</span>";
  return `<ul class="value-list">${items.map((item) => `<li>${item}</li>`).join("")}</ul>`;
}

function buildFinalReportMarkup(finalResult) {
  const intel = (finalResult && finalResult.extractedIntelligence) || {};
  return `
    <div class="final-grid">
      <div class="kv"><strong>Session ID</strong>${finalResult.sessionId || state.sessionId}</div>
      <div class="kv"><strong>Total Messages Exchanged</strong>${finalResult.totalMessagesExchanged || 0}</div>
      <div class="kv"><strong>Scam Detection</strong><span class="tag ${finalResult.scamDetected ? "good" : ""}">${finalResult.scamDetected ? "Confirmed" : "Not Confirmed"}</span></div>
      <div class="kv"><strong>Agent Notes</strong>${finalResult.agentNotes || "N/A"}</div>
      <div class="kv"><strong>Bank Accounts</strong>${listItems(intel.bankAccounts)}</div>
      <div class="kv"><strong>UPI IDs</strong>${listItems(intel.upiIds)}</div>
      <div class="kv"><strong>Phishing Links</strong>${listItems(intel.phishingLinks)}</div>
      <div class="kv"><strong>Phone Numbers</strong>${listItems(intel.phoneNumbers)}</div>
      <div class="kv"><strong>Email Addresses</strong>${listItems(intel.emailAddresses)}</div>
      <div class="kv"><strong>IFSC Codes</strong>${listItems(intel.ifscCodes)}</div>
      <div class="kv"><strong>PAN Numbers</strong>${listItems(intel.panNumbers)}</div>
      <div class="kv"><strong>Suspicious Keywords</strong>${listItems(intel.suspiciousKeywords)}</div>
    </div>
  `;
}
function buildReportText(finalResult) {
  if (!finalResult) return "No engagement report available.";
  const intel = finalResult.extractedIntelligence || {};
  const list = (items) => (items && items.length ? items.join(", ") : "None");

  return [
    "CyberCop Engagement Report",
    "==========================",
    `Session ID: ${finalResult.sessionId || state.sessionId}`,
    `Total Messages Exchanged: ${finalResult.totalMessagesExchanged || 0}`,
    `Scam Detection: ${finalResult.scamDetected ? "Confirmed" : "Not Confirmed"}`,
    `Agent Notes: ${finalResult.agentNotes || "N/A"}`,
    "",
    "Extracted Intelligence",
    "----------------------",
    `Bank Accounts: ${list(intel.bankAccounts)}`,
    `UPI IDs: ${list(intel.upiIds)}`,
    `Phishing Links: ${list(intel.phishingLinks)}`,
    `Phone Numbers: ${list(intel.phoneNumbers)}`,
    `Email Addresses: ${list(intel.emailAddresses)}`,
    `IFSC Codes: ${list(intel.ifscCodes)}`,
    `PAN Numbers: ${list(intel.panNumbers)}`,
    `Suspicious Keywords: ${list(intel.suspiciousKeywords)}`,
  ].join("\n");
}

function getCybercrimeEmailId() {
  return (el.cybercrimeEmailInput.value || "").trim();
}

function downloadReport() {
  if (!state.finalResult) {
    alert("Report will be available once engagement is completed.");
    return;
  }

  const content = buildReportText(state.finalResult);
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${state.sessionId || "engagement"}-report.txt`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function shareToWhatsApp() {
  if (!state.finalResult) {
    alert("Report will be available once engagement is completed.");
    return;
  }

  const report = buildReportText(state.finalResult);
  const message = encodeURIComponent(report.slice(0, 1800));
  window.open(`https://wa.me/?text=${message}`, "_blank");
}

function emailCybercrime() {
  if (!state.finalResult) {
    alert("Report will be available once engagement is completed.");
    return;
  }

  const email = getCybercrimeEmailId();
  if (!email) {
    alert("Please enter a cybercrime email ID.");
    return;
  }

  const subject = `CyberCop Engagement Report - ${state.sessionId || "Session"}`;
  const fullReport = buildReportText(state.finalResult);
  const compactBody = fullReport.length > 1500
    ? `${fullReport.slice(0, 1500)}\n\n[Report truncated. Use Download Report for full content.]`
    : fullReport;

  // Gmail web compose URL (Option 3)
  const gmailUrl =
    `https://mail.google.com/mail/?view=cm&fs=1` +
    `&to=${encodeURIComponent(email)}` +
    `&su=${encodeURIComponent(subject)}` +
    `&body=${encodeURIComponent(compactBody)}`;

  // Open Gmail compose in new tab
  window.open(gmailUrl, "_blank");
}



function renderIntel() {
  if (!state.finalResult) {
    el.finalCenterContent.innerHTML = "";
    return;
  }
  el.finalCenterContent.innerHTML = buildFinalReportMarkup(state.finalResult);
}

function applyUiByState() {
  const agentActive = state.scamDetected && state.takeoverAccepted;
  const engagementDone = state.engagementComplete;

  el.userInput.disabled = agentActive || engagementDone;
  el.sendUserBtn.disabled = agentActive || engagementDone;

  el.composerSection.classList.toggle("hidden", engagementDone);
  el.finalCenterPanel.classList.toggle("hidden", !engagementDone);
  el.timeline.classList.toggle("hidden", engagementDone);
}

function showTakeoverModal(show) {
  el.takeoverModal.classList.toggle("hidden", !show);
}

async function postJSON(url, payload) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Request failed");
  }
  return res.json();
}

async function sendScammerMessage() {
  if (!state.sessionId) initSession();
  const text = el.scammerInput.value.trim();
  if (!text) return;

  const optimisticTimestamp = new Date().toISOString();
  appendMessage("scammer", text, optimisticTimestamp);
  appendWaitingBubble();
  el.timeline.scrollTop = el.timeline.scrollHeight;
  el.scammerInput.value = "";

  const payload = {
    sessionId: state.sessionId,
    message: { sender: "scammer", text, timestamp: Date.now() },
    conversationHistory: [],
    metadata: { channel: "Chat", language: "English", locale: "IN" },
  };

  const data = await postJSON("/ui/scammer-message", payload);


  state.scamDetected = !!data.scamDetected;
  state.engagementComplete = !!data.engagementComplete;
  state.finalResult = data.finalResult || state.finalResult;

  renderTimeline(data.history || []);
  if (data.confirmationRequired) {
    showTakeoverModal(true);
  }
  if (state.engagementComplete && state.finalResult) {
    renderIntel();
  }
  renderStatus();
  applyUiByState();
}

async function sendUserMessage() {
  if (!state.sessionId) initSession();
  const text = el.userInput.value.trim();
  if (!text) return;

  const data = await postJSON("/ui/user-message", {
    sessionId: state.sessionId,
    text,
  });

  el.userInput.value = "";
  state.scamDetected = !!data.scamDetected;
  state.engagementComplete = !!data.engagementComplete;
  state.finalResult = data.finalResult || state.finalResult;

  renderTimeline(data.history || []);
  renderStatus();
  applyUiByState();
}

async function confirmTakeover() {
  showTakeoverModal(false);
  const data = await postJSON("/ui/takeover", { sessionId: state.sessionId });
  state.scamDetected = true;
  state.takeoverAccepted = true;
  state.engagementComplete = !!data.engagementComplete;
  state.finalResult = data.finalResult || state.finalResult;
  renderTimeline(data.history || []);
  if (state.engagementComplete && state.finalResult) {
    renderIntel();
  }
  renderStatus();
  applyUiByState();
  //showTakeoverModal(false);
}

el.newSessionBtn.addEventListener("click", initSession);
el.sendScammerBtn.addEventListener("click", () => sendScammerMessage().catch((e) => alert(e.message)));
el.sendUserBtn.addEventListener("click", () => sendUserMessage().catch((e) => alert(e.message)));
el.confirmTakeoverBtn.addEventListener("click", () => confirmTakeover().catch((e) => alert(e.message)));
el.dismissTakeoverBtn.addEventListener("click", () => showTakeoverModal(false));
el.downloadReportBtn.addEventListener("click", downloadReport);
el.shareWhatsappBtn.addEventListener("click", shareToWhatsApp);
el.emailCybercrimeBtn.addEventListener("click", emailCybercrime);
initSession();
