import pandas as pd
import os
import json
import yt_dlp
import requests
from time import sleep
from youtube_transcript_api import YouTubeTranscriptApi
import streamlit as st

# ================= 1. 固定配置区域 =================
# 飞书多维表格配置
APP_ID = "cli_a9e76e399af95bcb"
APP_SECRET = "ec9K56aHA6kEffTaf8U7nfbTMeCHTA0e"
APP_TOKEN = "RxrsbIcu5aAIhnskn9nczm0YnEp" 
TABLE_ID = "tbl0GRAEEob78518" 

# 抓取Qwen api的配置
CONFIG_APP_TOKEN = "JthwbPgugajSURs6P7XclKXBnWg" 
CONFIG_TABLE_ID = "tblczG2gCoDWlXYe"

BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions" 
MODEL_NAME = "qwen3.5-plus"

# ================= 2. 核心逻辑函数 (保持原逻辑不变) =================

def get_feishu_api():
    # 注意：访问飞书时禁用代理
    session = requests.Session()
    session.trust_env = False 
    auth_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    res = session.post(auth_url, json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=20)
    token = res.json().get("tenant_access_token")
    
    if not token: return None

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"}
    config_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{CONFIG_APP_TOKEN}/tables/{CONFIG_TABLE_ID}/records"
    params = {"filter": 'CurrentValue.[KeyID].contains("003")', "page_size": 1}
    
    resp = session.get(config_url, headers=headers, params=params, timeout=20).json()
    items = resp.get("data", {}).get("items", [])
    if not items: return None
    
    return {"target_Qwen_api": items[0].get("fields", {}).get("Key")}

def get_feishu_youtube_links():
    session = requests.Session()
    session.trust_env = False
    token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    token_res = session.post(token_url, json={"app_id": APP_ID, "app_secret": APP_SECRET})
    token = token_res.json().get("tenant_access_token")

    read_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records"
    headers = {"Authorization": f"Bearer {token}"}
    resp = session.get(read_url, headers=headers, params={"page_size": 500}, timeout=15)
    records = resp.json().get("data", {}).get("items", [])

    video_tasks = []
    for record in records:
        fields = record.get("fields", {})
        # 如果已经分析过了则跳过
        if fields.get("Video Topic") and fields.get("Content Overview"):
            continue
        
        raw_link = fields.get("Link")
        # 兼容飞书链接字段的不同格式
        video_url = ""
        if isinstance(raw_link, dict): video_url = raw_link.get("link", "")
        elif isinstance(raw_link, list): video_url = "".join([i.get("text", "") for i in raw_link])
        else: video_url = str(raw_link) if raw_link else ""

        if video_url.startswith("http"):
            video_tasks.append({"record_id": record.get("record_id"), "url": video_url.strip()})
    return video_tasks


def get_video_all_data(video_url):
    # 1. 使用 yt-dlp 获取标题和简介
    ydl_opts = {'quiet': True, 'skip_download': True}
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            video_id = info.get('id')
            title = info.get('title')
            description = info.get('description')

        # 2. 使用 YouTubeTranscriptApi 获取字幕
        # 优先尝试中文，如果没有则尝试英文
        try:
            transcript_list = YouTubeTranscriptApi().fetch(video_id, languages=['zh-Hans', 'zh-Hant', 'en','ja','ko','fr','de','el','it'])
            # 将每一句字幕合并成一段完整的文本
            full_transcript = " ".join([item.text for item in transcript_list])
        except Exception as e:
            full_transcript = f"未找到可用字幕或获取失败: {str(e)}"
        sleep(10)
        return {
            "video_id":video_id,
            "title": title,
            "description": description,
            "transcript": full_transcript
        }

    except Exception as e:
        return {"error": f"处理过程中出错: {str(e)}"}


def analyze_youtube_video(video_url,api_result):

    print(f"正在处理: {video_url}")

    # 1. 尝试抓取视频字幕以及视频标题简介
    data = get_video_all_data(video_url)
    print(f"【id】: {data['video_id']}\n")
    print(f"【标题】: {data['title']}\n")
    print(f"【简介】: {data['description']}\n")
    print(f"【字幕预览】: {data['transcript'][:3000]}...")

    # 3. AI 分析
    try:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_result.get('target_Qwen_api')}"}
        prompt = f"""
#Role:社媒运营专家
#Task:分析YouTube视频字幕或元数据并输出JSON
#Definitions:
1.topic(视频主题):核心讨论内容,依据画面/标题/字幕/口播选中心信息,多点选主1个,强次级括号补充,例:产品开箱(吐槽);
2.classification(视频分类):内容呈现形式或表达类型,基于结构/叙事判断,不与主题混淆,主1次1,例:口播讲解/Vlog记录;
3.overview(内容概况):1-3句客观描述展示/强调内容,不评价/推测/营销
#Data:
标题: {data['title']}
简介: {data['description']}
字幕: {data['transcript']}
#Format:只返回JSON,禁解释:{{"topic":"","classification":"","overview":""}}
""".strip()
        payload = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }

        # 调用 AI API (通常中介 API 不需要代理，如果需要也可加上 proxies=proxies)
        response = requests.post(BASE_URL, json=payload, headers=headers, timeout=600)
        if response.status_code == 200:
            return json.loads(response.json()['choices'][0]['message']['content'])
    except Exception as e:
        print(f"分析失败: {str(e)}")
    return None

def update_feishu_analysis_results(record_id, analysis_data):
    """
    将分析结果回写到飞书多维表格对应列
    """
    # 1. 同样先禁用环境代理干扰
    os.environ['HTTP_PROXY'] = ""
    os.environ['HTTPS_PROXY'] = ""
    
    session = requests.Session()
    session.trust_env = False

    try:
        # 2. 获取临时访问令牌
        token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        token_payload = {"app_id": APP_ID, "app_secret": APP_SECRET}
        token_res = session.post(token_url, json=token_payload, timeout=600)
        token = token_res.json().get("tenant_access_token")

        # 3. 准备回写地址和数据
        # 对应你截图中的列名：Video Topic, Content Overview, Video Classification
        update_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records/{record_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 构造回写内容
        payload = {
            "fields": {
                "Video Topic": analysis_data.get("topic", ""),
                "Content Overview": analysis_data.get("overview", ""),
                "Video Classification": analysis_data.get("classification", "")
            }
        }

        # 4. 执行更新 (使用 PUT 或 PATCH)
        resp = session.put(update_url, json=payload, headers=headers, timeout=100)
        if resp.status_code == 200:
            print(f"成功更新记录 {record_id} 的分析结果")
        else:
            print(f"回写失败，状态码: {resp.status_code}, 详情: {resp.text}")

    except Exception as e:
        print(f"回写飞书过程出错: {str(e)}")


# 主函数
if __name__ == "__main__":
    try:
        api_result = get_feishu_api()
        link_result = get_feishu_youtube_links()

        for link in link_result:
            qwen_json_result = analyze_youtube_video(link.get('url'),api_result)
            update_feishu_analysis_results(link.get('record_id'),qwen_json_result)
    except Exception as e:
        print(f"任务失败: {str(e)}")
# ================= Streamlit UI 界面 =================
from datetime import datetime
# --- 配置页面 ---
st.set_page_config(page_title="YouTube视频内容AI分析助手", layout="wide")

st.title("🎬 YouTube 视频内容分析自动化")

# --- 核心日志逻辑 ---
# 使用 session_state 存储历史日志，防止页面重载时丢失
if "log_history" not in st.session_state:
    st.session_state.log_history = []

def write_log(message, level="INFO"):
    """实时向页面和后台存储添加日志"""
    now = datetime.datetime.now().strftime("%H:%M:%S")
    emoji = "🔹" if level == "INFO" else "✅" if level == "SUCCESS" else "❌"
    log_entry = f"[{now}] {emoji} {message}"
    
    # 将新日志插入到列表最前面（这样最新日志就在最上面）
    st.session_state.log_history.insert(0, log_entry)
    
    # 限制日志长度，防止内存占用过高
    if len(st.session_state.log_history) > 100:
        st.session_state.log_history.pop()

# --- UI 布局 ---
col_ctrl, col_progress = st.columns([1, 3])
with col_ctrl:
    run_btn = st.button("🚀 开始自动化任务", type="primary", use_container_width=True)

# 进度条和状态文字
progress_bar = st.progress(0)
status_indicator = st.empty()

st.subheader("任务实时运行日志")
# 这是解决白屏的关键：创建一个固定高度的占位符区域
log_placeholder = st.empty()

# 初始化显示（如果已有历史日志）
with log_placeholder.container():
    st.code("\n".join(st.session_state.log_history), language="bash")

# --- 点击运行后的逻辑 ---
if run_btn:
    try:
        write_log("正在初始化飞书配置...", "INFO")
        # 实时更新一次界面
        log_placeholder.code("\n".join(st.session_state.log_history), language="bash")
        
        api_info = get_feishu_api()
        tasks = get_feishu_youtube_links()

        if not tasks:
            write_log("未发现待处理任务", "INFO")
            log_placeholder.code("\n".join(st.session_state.log_history), language="bash")
            st.info("暂无待处理视频")
        else:
            total = len(tasks)
            for i, task in enumerate(tasks):
                # 1. 更新 UI 状态
                progress = (i + 1) / total
                progress_bar.progress(progress)
                status_indicator.markdown(f"**当前进度:** {i+1} / {total}")

                # 2. 抓取与日志更新
                write_log(f"正在抓取视频数据: {task['url']}")
                # 强制刷新日志框
                log_placeholder.code("\n".join(st.session_state.log_history), language="bash")
                
                # --- 这里执行你的 get_video_all_data ---
                # data = get_video_all_data(task['url']) 
                
                write_log(f"正在调用 Qwen AI 进行分析...")
                log_placeholder.code("\n".join(st.session_state.log_history), language="bash")
                
                # --- 这里执行你的 analyze_youtube_video ---
                result = analyze_youtube_video(task['url'], api_info)
                
                if result:
                    update_feishu_analysis_results(task['record_id'], result)
                    write_log(f"数据回填完成: {result.get('topic')[:20]}...", "SUCCESS")
                else:
                    write_log(f"分析失败，请检查视频链接或 API", "ERROR")
                
                # 再次强制刷新日志框
                log_placeholder.code("\n".join(st.session_state.log_history), language="bash")
                sleep(0.5)

            st.balloons()
            write_log("🏁 所有任务已处理完成！", "SUCCESS")
            log_placeholder.code("\n".join(st.session_state.log_history), language="bash")

    except Exception as e:
        write_log(f"程序崩溃: {str(e)}", "ERROR")
        log_placeholder.code("\n".join(st.session_state.log_history), language="bash")
