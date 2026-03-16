# ================= Streamlit UI 界面 ================= 
import streamlit as st 
import subprocess 
from pathlib import Path 
import sys 
from streamlit_autorefresh import st_autorefresh 
from collections import deque 

LOG_FILE = "server.log" 

st.title("YouTube 视频内容 AI 分析工具") 

# 启动程序 
if st.button("开始运行"): 
    # 核心修复：使用 "w" 模式打开文件，这会清除之前的所有内容
    with open(LOG_FILE, "w", encoding="utf-8") as f: 
        f.write(f"--- 程序启动于 {sys.executable} ---\n") # 可选：写入启动标记
        
    # 以追加模式 "a" 打开供进程写入，或者直接重新打开
    log_f = open(LOG_FILE, "a", encoding="utf-8")
    
    subprocess.Popen( 
        [sys.executable, "youtube_video_analyze.py"], 
        stdout=log_f, 
        stderr=log_f,
        bufsize=1 # 设置缓冲，让日志实时写入文件
    ) 
    st.success("程序已重新启动，旧日志已清理。") 

# 每1秒刷新一次 
st_autorefresh(interval=1000, key="logrefresh") 
    
def read_last_lines(file, n=200): 
    try:
        with open(file, "r", encoding="utf-8") as f: 
            return "".join(deque(f, n))
    except Exception as e:
        return f"读取日志出错: {e}"
         
if Path(LOG_FILE).exists(): 
    st.subheader("实时运行日志")
    logs = read_last_lines(LOG_FILE) 
    # 使用 height 参数固定日志框高度，防止页面因日志增长而闪烁
    st.code(logs, language="bash") 
else: 
    st.info("暂无日志，请点击上方按钮开始运行。")