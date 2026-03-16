# ================= Streamlit UI 界面 =================
import streamlit as st
import subprocess
from pathlib import Path
import sys
from streamlit_autorefresh import st_autorefresh
from collections import deque

LOG_FILE = "server.log"

st.title("Youtube视频内容 AI分析工具")

# 启动程序
if st.button("开始运行"):

    # 1️⃣ 先清空旧日志
    open(LOG_FILE, "w").close()

    # 2️⃣ 再以追加模式写入新日志
    with open(LOG_FILE, "a") as f:
        subprocess.Popen(
            [sys.executable, "-u", "youtube_video_analyze.py"],  # -u 实时输出日志
            stdout=f,
            stderr=f
        )

    st.success("Program started")

# 每1秒刷新一次
st_autorefresh(interval=1000, key="logrefresh")

def read_last_lines(file, n=200):
    with open(file, "r", encoding="utf-8") as f:
        return "".join(deque(f, n))

if Path(LOG_FILE).exists():
    logs = read_last_lines(LOG_FILE)
    st.code(logs, language="bash")
else:
    st.write("No logs yet...")