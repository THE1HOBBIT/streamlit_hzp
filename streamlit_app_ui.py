import streamlit as st
import subprocess
import time
from pathlib import Path

LOG_FILE = "server.log"

st.title("Server Log Panel")

# 启动程序按钮
if st.button("Start Program"):
    subprocess.Popen(
        ["python", "youtube_video_analyze.py"],  # 你的底层逻辑程序
        stdout=open(LOG_FILE, "a"),
        stderr=open(LOG_FILE, "a")
    )
    st.success("Program started")

log_placeholder = st.empty()

def read_last_lines(file, n=200):
    with open(file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return "".join(lines[-n:])

# 实时刷新日志
while True:
    if Path(LOG_FILE).exists():
        logs = read_last_lines(LOG_FILE)
        log_placeholder.code(logs, language="bash")

    time.sleep(1)