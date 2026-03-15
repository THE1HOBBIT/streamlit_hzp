
# ================= Streamlit UI 界面 =================
import streamlit as st 
import subprocess 
import time 
from pathlib import Path 
import pandas as pd 
import os 
import json 
import yt_dlp 
import requests 
from youtube_transcript_api import YouTubeTranscriptApi 
import sys 
import io 

LOG_FILE = "server.log" 
st.title("Server Log Panel") 
# 启动程序按钮 
if st.button("Start Program"):
    # 使用 sys.executable 确保环境一致
    # 使用 with 自动管理文件关闭
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
    while True: 
        if Path(LOG_FILE).exists(): 
            logs = read_last_lines(LOG_FILE) 
            log_placeholder.code(logs, language="bash") 
            
    time.sleep(1)