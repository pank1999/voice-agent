const {
  app,
  BrowserWindow,
  shell,
  session,
  systemPreferences,
  dialog,
  ipcMain,
} = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const fs = require("fs");
const { autoUpdater } = require("electron-updater");

// Configuration
const CONFIG_DIR = path.join(require("os").homedir(), ".jarvis");
const CONFIG_FILE = path.join(CONFIG_DIR, "config.json");

const BACKEND_PORT = 8000;
const BACKEND_READY_TIMEOUT = 15000;
const isDev = process.env.NODE_ENV === "development";

let mainWindow = null;
let splashWindow = null;
let onboardingWindow = null;
let backendProcess = null;

// ── Config Management ────────────────────────────────────────────────────────

function loadConfig() {
  try {
    if (fs.existsSync(CONFIG_FILE)) {
      return JSON.parse(fs.readFileSync(CONFIG_FILE, "utf8"));
    }
  } catch (e) {
    console.error("[electron] failed to load config:", e);
  }
  return null;
}

function saveConfig(config) {
  try {
    fs.mkdirSync(CONFIG_DIR, { recursive: true });
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2));
    return true;
  } catch (e) {
    console.error("[electron] failed to save config:", e);
    return false;
  }
}

function needsOnboarding() {
  const config = loadConfig();
  return !config || !config.openaiApiKey;
}

// ── Backend ─────────────────────────────────────────────────────────────────

function getAppRoot() {
  // In packaged app, backend is in Resources/app
  // In dev, it's two levels up from frontend/electron
  return isDev
    ? path.join(__dirname, "../..")
    : path.join(process.resourcesPath, "app");
}

function getBackendPath() {
  // In dev mode, use Python directly from project
  if (isDev) {
    const devPaths = [
      path.join(__dirname, "../../venv/bin/python3"),
      path.join(__dirname, "../../venv/bin/python"),
      "/usr/local/bin/python3",
      "/usr/bin/python3",
    ];
    for (const p of devPaths) {
      try {
        if (require("fs").existsSync(p))
          return {
            cmd: p,
            args: [
              "-m",
              "uvicorn",
              "app.main:app",
              "--host",
              "127.0.0.1",
              "--port",
              String(BACKEND_PORT),
            ],
            cwd: path.join(__dirname, "../.."),
          };
      } catch {}
    }
    // Fallback: try uvicorn directly
    return {
      cmd: "uvicorn",
      args: [
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        String(BACKEND_PORT),
      ],
      cwd: path.join(__dirname, "../.."),
    };
  }

  // In production, use bundled binary
  const bundledBinary = path.join(process.resourcesPath, "jarvis-backend");
  if (require("fs").existsSync(bundledBinary)) {
    return { cmd: bundledBinary, args: [], cwd: process.resourcesPath };
  }

  // Fallback to app directory
  const appBinary = path.join(process.resourcesPath, "app", "jarvis-backend");
  if (require("fs").existsSync(appBinary)) {
    return {
      cmd: appBinary,
      args: [],
      cwd: path.join(process.resourcesPath, "app"),
    };
  }

  return null;
}

function startBackend() {
  const backend = getBackendPath();

  if (!backend) {
    dialog.showErrorBox(
      "Backend Not Found",
      "Could not find JARVIS backend. Please download the app again from GitHub releases.",
    );
    app.quit();
    return;
  }

  console.log(`[electron] starting backend: ${backend.cmd}`);
  console.log(`[electron] backend cwd: ${backend.cwd}`);
  console.log(`[electron] backend args: ${backend.args.join(" ")}`);

  // Check if binary exists and log details
  try {
    const stats = require("fs").statSync(backend.cmd);
    console.log(`[electron] backend binary size: ${stats.size} bytes`);
    console.log(`[electron] backend binary mode: ${stats.mode.toString(8)}`);
  } catch (e) {
    console.error(`[electron] cannot stat backend: ${e.message}`);
  }

  updateSplashStatus("Starting backend...");

  backendProcess = spawn(backend.cmd, backend.args, {
    cwd: backend.cwd,
    env: { ...process.env, JARVIS_DESKTOP: "1" },
    stdio: ["ignore", "pipe", "pipe"],
  });

  backendProcess.on("error", (err) => {
    console.error(`[electron] backend spawn error: ${err.message}`);
    updateSplashStatus("Failed to start backend", "error");
    dialog.showErrorBox(
      "Backend Error",
      `Failed to start backend: ${err.message}\n\nPath: ${backend.cmd}`,
    );
  });

  backendProcess.stdout.on("data", (d) =>
    process.stdout.write("[backend] " + d),
  );
  backendProcess.stderr.on("data", (d) =>
    process.stderr.write("[backend] " + d),
  );

  backendProcess.on("exit", (code, signal) => {
    console.log(`[backend] exited with code ${code}, signal ${signal}`);
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
  let checks = 0;
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(`http://127.0.0.1:${BACKEND_PORT}/`);
      if (res.ok) {
        updateSplashStatus("Systems online", "ready");
        return true;
      }
    } catch {
      checks++;
      if (checks % 4 === 0) {
        // Update every ~2 seconds
        const elapsed = Math.round((Date.now() - start) / 1000);
        updateSplashStatus(`Waiting for backend... (${elapsed}s)`);
      }
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  updateSplashStatus("Backend timeout", "error");
  return false;
}

// ── Splash Window ────────────────────────────────────────────────────────────

function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 400,
    height: 300,
    frame: false,
    alwaysOnTop: true,
    transparent: true,
    resizable: false,
    movable: true,
    center: true,
    show: false,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  const splashPath = isDev
    ? path.join(__dirname, "../public/splash.html")
    : path.join(__dirname, "../dist/splash.html");

  splashWindow.loadFile(splashPath);

  splashWindow.once("ready-to-show", () => {
    splashWindow.show();
  });

  splashWindow.on("closed", () => {
    splashWindow = null;
  });
}

function closeSplashWindow() {
  if (splashWindow && !splashWindow.isDestroyed()) {
    // Fade out effect
    splashWindow.setOpacity(0);
    setTimeout(() => splashWindow.close(), 300);
  }
}

function updateSplashStatus(message, type = "") {
  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.webContents.send("backend-status", { message, type });
  }
}

// ── Onboarding Window ────────────────────────────────────────────────────────

function createOnboardingWindow() {
  onboardingWindow = new BrowserWindow({
    width: 500,
    height: 420,
    frame: false,
    resizable: false,
    movable: true,
    center: true,
    show: false,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  const onboardingPath = isDev
    ? path.join(__dirname, "../public/onboarding.html")
    : path.join(__dirname, "../dist/onboarding.html");

  onboardingWindow.loadFile(onboardingPath);

  onboardingWindow.once("ready-to-show", () => {
    onboardingWindow.show();
  });

  onboardingWindow.on("closed", () => {
    onboardingWindow = null;
  });
}

function closeOnboardingWindow() {
  if (onboardingWindow && !onboardingWindow.isDestroyed()) {
    onboardingWindow.close();
  }
}

// ── Main Window ──────────────────────────────────────────────────────────────

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
    icon: path.join(__dirname, "../public/icon.png"),
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
    mainWindow.loadFile(path.join(__dirname, "../dist/index.html"));
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

// ── IPC Handlers ─────────────────────────────────────────────────────────────

ipcMain.on("save-config", (event, config) => {
  if (saveConfig(config)) {
    event.sender.send("config-saved");
    // Close onboarding and open main window
    setTimeout(() => {
      closeOnboardingWindow();
      createWindow();
      setTimeout(closeSplashWindow, 500);
    }, 1500);
  } else {
    event.sender.send("config-error", "Failed to save configuration");
  }
});

// ── App Lifecycle ─────────────────────────────────────────────────────────────

app.whenReady().then(async () => {
  // Check if onboarding is needed
  const firstRun = needsOnboarding();

  if (firstRun) {
    // Show onboarding instead of splash
    createOnboardingWindow();

    // Still start backend in background
    if (!isDev) {
      startBackend();
    }
    return;
  }

  // Normal startup with splash
  createSplashWindow();

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

  // Close splash after main window is ready
  setTimeout(closeSplashWindow, 800);

  // Check for updates (only in production)
  if (!isDev) {
    autoUpdater.checkForUpdatesAndNotify();
  }
});

app.on("window-all-closed", () => {
  stopBackend();
  if (process.platform !== "darwin") app.quit();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    if (needsOnboarding()) {
      createOnboardingWindow();
    } else {
      createWindow();
    }
  }
});

app.on("before-quit", () => stopBackend());

// ── Auto-updater Events ─────────────────────────────────────────────────────

autoUpdater.on("checking-for-update", () => {
  console.log("[electron] checking for updates...");
});

autoUpdater.on("update-available", (info) => {
  console.log("[electron] update available:", info.version);
  dialog.showMessageBox(mainWindow, {
    type: "info",
    title: "Update Available",
    message: `JARVIS ${info.version} is available.`,
    detail:
      "The update will be downloaded in the background and installed when you restart the app.",
    buttons: ["OK"],
  });
});

autoUpdater.on("update-downloaded", (info) => {
  console.log("[electron] update downloaded:", info.version);
  dialog
    .showMessageBox(mainWindow, {
      type: "question",
      title: "Update Ready",
      message: `JARVIS ${info.version} has been downloaded.`,
      detail: "Restart now to install the update?",
      buttons: ["Restart", "Later"],
      defaultId: 0,
    })
    .then((result) => {
      if (result.response === 0) {
        autoUpdater.quitAndInstall();
      }
    });
});

autoUpdater.on("error", (err) => {
  console.error("[electron] auto-updater error:", err);
});
