const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electron", {
  isElectron: true,
  getSessionId: () => ipcRenderer.invoke("get-session-id"),
});
