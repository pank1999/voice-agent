# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path

block_cipher = None

# Get project root (where backend.spec is located)
project_root = os.path.dirname(os.path.abspath(SPECPATH))

a = Analysis(
    ['app/main.py'],
    pathex=[project_root],
    binaries=[],
    datas=[
        ('app', 'app'),
    ],
    hiddenimports=[
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'fastapi',
        'fastapi.middleware.cors',
        'pydantic',
        'pydantic.deprecated.decorator',
        'pydantic.v1',
        'pydantic.v1.typing',
        'pydantic.v1.validators',
        'email_validator',
        'openai',
        'starlette',
        'starlette.middleware',
        'starlette.middleware.cors',
        'starlette.middleware.errors',
        'anyio',
        'anyio._backends',
        'anyio._backends._asyncio',
        'sqlite3',
        'google.auth',
        'google.auth.transport',
        'google.auth.transport.requests',
        'google_auth_oauthlib',
        'google_auth_oauthlib.flow',
        'googleapiclient',
        'googleapiclient.discovery',
        'googleapiclient.errors',
        'googleapiclient.http',
        'httplib2',
        'requests',
        'urllib3',
        'certifi',
        'charset_normalizer',
        'idna',
        'sniffio',
        'typing_extensions',
        'annotated_types',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'Pillow',
        'tkinter',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
        'wxPython',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='jarvis-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # macOS app bundle
    bundle_identifier='dev.pankajpandey.jarvis-backend',
)

# For macOS, create an app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='jarvis-backend.app',
        icon=None,
        bundle_identifier='dev.pankajpandey.jarvis-backend',
    )
