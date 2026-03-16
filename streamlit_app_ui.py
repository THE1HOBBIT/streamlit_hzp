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
from streamlit_autorefresh import st_autorefresh

LOG_FILE = "server.log"

st.title("Server Log Panel")

# 启动程序
if st.button("Start Program"):
    with open(LOG_FILE, "a") as f:
        subprocess.Popen(
            [sys.executable, "youtube_video_analyze.py"],
            stdout=f,
            stderr=f
        )
    st.success("Program started")

# 每1秒刷新一次
st_autorefresh(interval=1000, key="logrefresh")

def read_last_lines(file, n=200):
    with open(file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return "".join(lines[-n:])

if Path(LOG_FILE).exists():
    logs = read_last_lines(LOG_FILE)
    st.code(logs, language="bash")
else:
    st.write("No logs yet...")