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

  importBtn.addEventListener("click", async () => {
    importBtn.disabled = true;
    wait.style.visibility = "visible";

    const result = await API.importNow();
    showAlert(result.message, result.success ? "success" : "danger");

    importBtn.disabled = false;
    wait.style.visibility = "hidden";
  });

  scheduleBtn.addEventListener("click", async () => {
    const hour = document.getElementById("hour-input").value;
    const minute = document.getElementById("minute-input").value;

    const result = await API.scheduleImport(hour, minute);
    showAlert(result.message, result.success ? "success" : "danger");
  });
});
