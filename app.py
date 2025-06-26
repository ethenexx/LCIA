"""
app.py - 法律咨询智能体启动文件
"""
import streamlit as st
from utils import get_api_credentials

# 检查API密钥是否已设置
api_key, _ = get_api_credentials()
if not api_key:
    st.error("错误：未找到API密钥！请在Streamlit Secrets中设置API_KEY。")
    st.info("""
    ### 如何设置API密钥：
    
    在Streamlit Cloud部署：
    1. 进入应用设置 > Secrets
    2. 添加：`API_KEY = "你的API密钥"`
    
    本地运行：
    1. 创建`.streamlit/secrets.toml`文件
    2. 添加：`API_KEY = "你的API密钥"`
    """)
    st.stop()

# 导入主应用
import main