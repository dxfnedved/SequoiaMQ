# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# 获取当前目录
current_dir = os.getcwd()

# 获取当前目录下的所有Python文件
strategy_files = [(f"strategy/{f}", f"strategy/") for f in os.listdir("strategy") if f.endswith('.py')]
news_sources_files = [(f"news_sources/{f}", f"news_sources/") for f in os.listdir("news_sources") if f.endswith('.py')]

# 合并所有数据文件
datas = [
    ('.env', '.'),
    ('settings.py', '.'),
    ('README.md', '.'),
    ('main.py', '.'),
    ('utils.py', '.'),
    ('data_fetcher.py', '.'),
    ('logger_manager.py', '.'),
    ('work_flow.py', '.'),
    ('llm_interface.py', '.')
] + strategy_files + news_sources_files

a = Analysis(
    ['launcher.py'],
    pathex=[current_dir],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'pandas',
        'numpy',
        'akshare',
        'requests',
        'bs4',
        'colorama',
        'tqdm',
        'openai',
        'httpx',
        'python-dotenv',
        'strategy',
        'news_sources',
        'json',
        'datetime',
        'logging',
        'traceback',
        'time',
        'random'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='SequoiaMQ',
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
    icon='icon.ico' if os.path.exists('icon.ico') else None
) 