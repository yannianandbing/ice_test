#!/usr/bin/env python3
import subprocess
import sys
import importlib.util

REQUIRED_PACKAGES = ["streamlit", "openai"]
MAIN_SCRIPT = "main.py"   # 请改成您的主程序文件名

def install(pkg):
    print(f"📦 安装 {pkg} ...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

if __name__ == "__main__":
    for pkg in REQUIRED_PACKAGES:
        if importlib.util.find_spec(pkg) is None:
            install(pkg)
        else:
            print(f"✅ {pkg} 已安装")

    print(f"🚀 启动 {MAIN_SCRIPT} ...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", MAIN_SCRIPT])