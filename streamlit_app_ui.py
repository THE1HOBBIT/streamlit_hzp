import streamlit as st
import subprocess
import time  # 必须导入 time
from pathlib import Path
import sys

# 1. 解决 Bad message format 的核心：在脚本最开始稍微留出一点点 Session 初始化时间
time.sleep(0.1) 

LOG_FILE = "server.log"

st.set_page_config(page_title="Log Panel", layout="wide")
st.title("🚀 Server Log Panel")

# 确保日志文件存在
if not Path(LOG_FILE).exists():
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("--- System Initialized ---\n")

# --- 侧边栏控制 ---
with st.sidebar:
    st.header("Controls")
    if st.button("Clear Logs"):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("--- Logs Cleared ---\n")
        st.rerun()

# --- 主界面 ---
# 启动程序按钮
if st.button("▶️ Start Program", type="primary"):
    # 使用 a+ 模式确保文件流正确
    log_f = open(LOG_FILE, "a", encoding="utf-8")
    try:
        subprocess.Popen(
            [sys.executable, "youtube_video_analyze.py"], 
            stdout=log_f,
            stderr=log_f,
            bufsize=1  # 行缓冲，让日志更实时
        )
        st.success("Program started successfully!")
    except Exception as e:
        st.error(f"Failed to start: {e}")

st.divider()
st.subheader("📜 Real-time Logs")

log_placeholder = st.empty()

def read_last_lines(file, n=100):
    try:
        if Path(file).exists():
            with open(file, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
                return "".join(lines[-n:])
        return "Log file not found."
    except Exception as e:
        return f"Error reading logs: {e}"

# --- 刷新逻辑 ---
# 获取当前日志内容
logs = read_last_lines(LOG_FILE)
log_placeholder.code(logs, language="bash")

# 这里的逻辑是：渲染完页面后，等待 3 秒，然后触发一次重新运行
# 3秒是一个比较安全的阈值，可以避免 SessionInfo 报错
time.sleep(3) 
st.rerun()