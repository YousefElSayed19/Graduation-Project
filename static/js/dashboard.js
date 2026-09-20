const startBtn = document.getElementById("start_scan_btn");
const targetInput = document.getElementById("target_url");
const terminalBody = document.getElementById("terminal_body");
const emptyState = document.getElementById("empty_state");
const statusPill = document.getElementById("status_pill");
const findingsList = document.getElementById("findings_list");
const noFindings = document.getElementById("no_findings");

let currentScanUid = null;
let sinceIndex = 0;
let pollTimer = null;

function setStatus(status) {
  statusPill.className = "status-pill " + status;
  statusPill.innerHTML = `<span class="dot"></span> ${status}`;
}

function appendLog(logEntry) {
  if (emptyState) emptyState.remove();

  const line = document.createElement("div");
  line.className = "log-line level-" + logEntry.level;

  const time = new Date(logEntry.ts * 1000).toLocaleTimeString("en-US");
  line.innerHTML = `${logEntry.message} <span class="ts">${time}</span>`;

  terminalBody.appendChild(line);
  terminalBody.scrollTop = terminalBody.scrollHeight;
}

async function pollLogs() {
  if (!currentScanUid) return;

  const res = await fetch(`/api/scan/${currentScanUid}/logs?since=${sinceIndex}`);
  const data = await res.json();

  data.logs.forEach(appendLog);
  sinceIndex = data.next_index;
  setStatus(data.status);

  if (data.status === "done" || data.status === "failed") {
    clearInterval(pollTimer);
    loadResults();
    startBtn.disabled = false;
    startBtn.textContent = "Start scan";
  }
}

async function loadResults() {
  const res = await fetch(`/api/scan/${currentScanUid}/results`);
  const data = await res.json();

  findingsList.innerHTML = "";

  if (!data.findings || data.findings.length === 0) {
    noFindings.style.display = "block";
    return;
  }

  noFindings.style.display = "none";

  data.findings.forEach((f) => {
    const li = document.createElement("li");
    li.className = "finding-card";
    li.innerHTML = `
      <div class="finding-top">
        <span class="finding-type">${f.type}</span>
        <span class="severity ${f.severity}">${f.severity}</span>
      </div>
      <p class="finding-desc">${f.description}</p>
      <p class="finding-desc" style="margin-top:4px; opacity:0.7;">${f.location}</p>
    `;
    findingsList.appendChild(li);
  });
}

startBtn.addEventListener("click", async () => {
  const targetUrl = targetInput.value.trim();
  if (!targetUrl) {
    alert("Enter a target URL first");
    return;
  }

  startBtn.disabled = true;
  startBtn.textContent = "Scanning...";
  terminalBody.innerHTML = "";
  findingsList.innerHTML = "";
  noFindings.style.display = "block";
  sinceIndex = 0;

  const res = await fetch("/api/scan/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target_url: targetUrl }),
  });

  const data = await res.json();

  if (data.error) {
    alert(data.error);
    startBtn.disabled = false;
    startBtn.textContent = "Start scan";
    return;
  }

  currentScanUid = data.scan_uid;
  setStatus("running");
  pollTimer = setInterval(pollLogs, 1200);
});
