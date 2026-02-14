export const API = {
  async importNow() {
    try {
      const response = await fetch("/import", { method: "POST" });
      if (!response.ok) throw new Error(`Failed to import (status: ${response.status})`);
      return { success: true, message: "Import tasks queued" };
    } catch (err) {
      return { success: false, message: err.message };
    }
  },

  async scheduleImport(hour, minute) {
    try {
      const response = await fetch("/schedule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ hour, minute }),
      });
      if (!response.ok) throw new Error(`Failed to schedule (status: ${response.status})`);
      const data = await response.json();
      return { success: true, message: data.message };
    } catch (err) {
      return { success: false, message: err.message };
    }
  },

  async getImportStatus() {
    try {
      const response = await fetch("/import/status");
      if (!response.ok) throw new Error(`Failed to get status (status: ${response.status})`);
      const data = await response.json();
      return { success: true, data };
    } catch (err) {
      return { success: false, message: err.message };
    }
  }
};
