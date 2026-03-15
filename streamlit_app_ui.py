# ================= Streamlit UI 界面 =================
import streamlit as st 
import subprocess 
import time 
from pathlib import Path 
import pandas as pd 
import os 
import streamlit as st
import subprocess
import sys
import time
from pathlib import Path

LOG_FILE = "server.log"

st.title("Server Log Panel")

# 启动程序按钮
if st.button("Start Program"):
    with open(LOG_FILE, "a") as f:
        subprocess.Popen(
            [sys.executable, "youtube_video_analyze.py"],
            stdout=f,
            stderr=f
        )
    st.success("Program started")

log_placeholder = st.empty()

def read_last_lines(file, n=200):
    with open(file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return "".join(lines[-n:])

# 实时刷新日志
refresh_interval = 1  # 秒
while True:
    if Path(LOG_FILE).exists():
        logs = read_last_lines(LOG_FILE)
        log_placeholder.code(logs, language="bash")
    time.sleep(refresh_interval)
    st.experimental_rerun()  # 强制 Streamlit 重新运行脚本