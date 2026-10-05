import { API } from "./api.js";

function showAlert(message, type = "success") {
  const alertContainer = document.querySelector("#error-container");
  alertContainer.innerHTML = "";

  const div = document.createElement("div");
  div.className = `alert alert-${type} mt-2`;
  div.role = "alert";
  div.textContent = message;
  alertContainer.appendChild(div);
}

document.addEventListener("DOMContentLoaded", () => {
  const wait = document.querySelector(".wait");
  const importBtn = document.getElementById("import-button");
  const scheduleBtn = document.getElementById("schedule-button");
  const exportBtn = document.getElementById("export-button");
  const exportInput = document.getElementById("export-file-input");

  importBtn.addEventListener("click", async () => {
    importBtn.disabled = true;
    wait.style.visibility = "visible";

    const result = await API.importNow();
    showAlert(result.message, result.success ? "success" : "danger");

    importBtn.disabled = false;
    wait.style.visibility = "hidden";


    fetchImportStatus();
  });

  scheduleBtn.addEventListener("click", async () => {
    const hour = document.getElementById("hour-input").value;
    const minute = document.getElementById("minute-input").value || "0";

    const result = await API.scheduleImport(hour, minute);
    showAlert(result.message, result.success ? "success" : "danger");
  });

  exportBtn.addEventListener("click", async () => {
    if (!exportInput.files.length) {
      showAlert("Choose the Whoop export zip or CSV files first", "danger");
      return;
    }

    exportBtn.disabled = true;
    const result = await API.importExport(exportInput.files);
    showAlert(result.message, result.success ? "success" : "danger");
    exportBtn.disabled = false;
  });

  fetchImportStatus();
  startPolling();
});


async function fetchImportStatus() {
  const result = await API.getImportStatus();

  if (!result.success) {
    console.error(result.message);
    return;
  }

  const { backlog, last_status } = result.data;

  const backlogBadge = document.getElementById("backlog-badge");
  const statusBadge = document.getElementById("status-badge");

  backlogBadge.textContent = backlog ?? 0;
  statusBadge.textContent = last_status ?? "N/A";

  if (backlog > 0) {
    backlogBadge.classList.remove("badge-primary");
    backlogBadge.classList.add("badge-warning");
  } else {
    backlogBadge.classList.remove("badge-warning");
    backlogBadge.classList.add("badge-primary");
  }
}

let statusInterval;

function startPolling() {
  let running = false;

  statusInterval = setInterval(async () => {
    if (running) return;
    running = true;
    await fetchImportStatus();
    running = false;
  }, 5000);
}

