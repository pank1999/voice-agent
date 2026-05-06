const {
  app,
  BrowserWindow,
  shell,
  session,
  systemPreferences,
} = require("electron");
const path = require("path");
const { spawn } = require("child_process");

const BACKEND_PORT = 8000;
const BACKEND_READY_TIMEOUT = 15000;
const isDev = process.env.NODE_ENV === "development";

let mainWindow = null;
let backendProcess = null;

// ── Backend ─────────────────────────────────────────────────────────────────

function startBackend() {
  const projectRoot = path.join(__dirname, "..");

  const cmd = process.platform === "win32" ? "uvicorn" : "uvicorn";
  backendProcess = spawn(
    cmd,
    ["app.main:app", "--host", "127.0.0.1", "--port", String(BACKEND_PORT)],
    {
      cwd: projectRoot,
      env: { ...process.env },
      stdio: ["ignore", "pipe", "pipe"],
    },
  );

  backendProcess.stdout.on("data", (d) =>
    process.stdout.write("[backend] " + d),
  );
  backendProcess.stderr.on("data", (d) =>
    process.stderr.write("[backend] " + d),
  );

  backendProcess.on("exit", (code) => {
    console.log(`[backend] exited with code ${code}`);
    backendProcess = null;
  });
}

function stopBackend() {
  if (backendProcess) {
    backendProcess.kill("SIGTERM");
    backendProcess = null;
  }
}

async function waitForBackend(timeoutMs = BACKEND_READY_TIMEOUT) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(`http://127.0.0.1:${BACKEND_PORT}/`);
      if (res.ok) return true;
    } catch {}
    await new Promise((r) => setTimeout(r, 500));
  }
  return false;
}

// ── Window ───────────────────────────────────────────────────────────────────

function createWindow() {
  // Grant microphone permission automatically — required for Web Speech API
  session.defaultSession.setPermissionRequestHandler(
    (_webContents, permission, callback) => {
      const allowed = ["media", "microphone", "audioCapture"];
      callback(allowed.includes(permission));
    },
  );

  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    titleBarStyle: "hiddenInset",
    backgroundColor: "#020917",
    icon: path.join(__dirname, "../frontend/public/vite.svg"),
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (isDev) {
    mainWindow.loadURL("http://localhost:5173");
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, "../frontend/dist/index.html"));
  }

  // Open external links in the system browser, not inside Electron
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

// ── App lifecycle ─────────────────────────────────────────────────────────────

async function waitForVite(timeoutMs = 30000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch("http://localhost:5173/");
      if (res.ok) return true;
    } catch {}
    await new Promise((r) => setTimeout(r, 500));
  }
  return false;
}

app.whenReady().then(async () => {
  if (isDev) {
    console.log(
      "[electron] dev mode — skipping backend spawn (use bash run.sh separately)",
    );
    console.log("[electron] waiting for Vite dev server on :5173…");
    const viteReady = await waitForVite();
    if (!viteReady) console.warn("[electron] Vite not ready — loading anyway");
  } else {
    startBackend();
    console.log("[electron] waiting for backend…");
    const ready = await waitForBackend();
    if (!ready)
      console.warn(
        "[electron] backend did not respond in time — loading anyway",
      );
  }
  // Request macOS microphone access — triggers the system permission dialog
  if (process.platform === "darwin") {
    const micStatus = systemPreferences.getMediaAccessStatus("microphone");
    console.log("[electron] microphone status:", micStatus);
    if (micStatus !== "granted") {
      const granted = await systemPreferences.askForMediaAccess("microphone");
      console.log("[electron] microphone permission granted:", granted);
    }
  }

  createWindow();
});

app.on("window-all-closed", () => {
  stopBackend();
  if (process.platform !== "darwin") app.quit();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

app.on("before-quit", () => stopBackend());
