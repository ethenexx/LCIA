"""
main.py - 自助式法律咨询智能体
提供基本的法律信息和指导、帮助用户理解法律文件、提供案件研究和策略建议
"""
import streamlit as st
import pandas as pd
import io
import base64
from datetime import datetime

from utils import legal_agent, get_legal_domains, get_sample_questions, get_api_credentials

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

# 尝试导入文档处理库，如果不可用则提供替代方案
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    import docx
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False

# 页面配置
st.set_page_config(
    page_title="法律咨询智能体",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 应用样式
st.markdown("""
<style>
    .main-header {color:#1E3A8A; font-size:2.5rem; font-weight:bold; margin-bottom:0.8rem;}
    .sub-header {color:#1E3A8A; font-size:1.8rem; font-weight:bold; margin-top:2rem;}
    .info-box {background-color:#F0F7FF; padding:1rem; border-radius:0.5rem; margin:1rem 0;}
    .important {color:#CC0000; font-weight:bold;}
    .highlight {background-color:#FFFFCC; padding:0.2rem; border-radius:0.3rem;}
</style>
""", unsafe_allow_html=True)

def display_document_content(doc_file, file_type):
    """显示上传文档的内容"""
    try:
        if file_type == "pdf":
            if not PDF_SUPPORT:
                st.warning("未安装PyPDF2库，无法处理PDF文件。请运行 `pip install PyPDF2` 安装。")
                return None
            pdf_reader = PyPDF2.PdfReader(doc_file)
            text = ""
            for page in range(len(pdf_reader.pages)):
                text += pdf_reader.pages[page].extract_text()
            return text
        elif file_type == "docx":
            if not DOCX_SUPPORT:
                st.warning("未安装python-docx库，无法处理Word文件。请运行 `pip install python-docx` 安装。")
                return None
            doc = docx.Document(doc_file)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        elif file_type == "txt":
            return doc_file.getvalue().decode("utf-8")
        return None
    except Exception as e:
        st.error(f"文件解析错误: {str(e)}")
        return None

def get_download_link(text, filename, label="下载分析报告"):
    """生成下载链接"""
    b64 = base64.b64encode(text.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">📄 {label}</a>'
    return href

def init_session_state():
    """初始化会话状态"""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "doc_content" not in st.session_state:
        st.session_state.doc_content = None
    if "consultation_results" not in st.session_state:
        st.session_state.consultation_results = []
    if "legal_domain" not in st.session_state:
        st.session_state.legal_domain = "一般法律咨询"

# 初始化会话状态
init_session_state()

# 侧边栏
with st.sidebar:
    st.markdown("## ⚖️ 法律咨询智能体")
    st.markdown("### 法律领域")

    legal_domains = get_legal_domains()
    selected_domain = st.selectbox(
        "选择法律领域:",
        legal_domains,
        index=legal_domains.index(st.session_state.legal_domain)
    )

    if selected_domain != st.session_state.legal_domain:
        st.session_state.legal_domain = selected_domain

    st.markdown("### 示例问题")
    sample_questions = get_sample_questions(selected_domain)
    for q in sample_questions:
        if st.button(f"📝 {q}", key=f"sample_{q}"):
            st.session_state.sample_question = q
            st.rerun()

    st.markdown("---")
    if st.button("清除历史记录"):
        st.session_state.chat_history = []
        st.session_state.consultation_results = []
        st.rerun()

    st.markdown("---")
    st.markdown("### 免责声明")
    st.info(
        "本智能体提供的信息仅供参考，不构成法律建议。"
        "对于重要法律事务，请咨询专业律师。"
    )

# 主页面
st.markdown('<p class="main-header">⚖️ 法律咨询智能体</p>', unsafe_allow_html=True)

# 选项卡
tab1, tab2, tab3 = st.tabs(["基本法律信息", "法律文件解读", "案件研究与策略"])

with tab1:
    st.markdown('<p class="sub-header">基本法律信息</p>', unsafe_allow_html=True)
    st.markdown("请输入您的法律问题，获取相关法律信息和指导。")

    query = st.text_area(
        "您的法律问题:",
        value=st.session_state.get("sample_question", ""),
        height=120,
        placeholder="例如：我需要了解劳动合同终止的法律规定..."
    )

    if st.button("获取法律信息", key="basic_info_button"):
        if not query:
            st.warning("请输入您的咨询问题")
        else:
            with st.spinner("AI正在分析您的问题，请稍等..."):
                result = legal_agent(query, "基本法律信息", st.session_state.legal_domain)

                # 保存结果
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.chat_history.append({
                    "type": "基本法律信息",
                    "query": query,
                    "result": result,
                    "timestamp": timestamp
                })

                # 显示结果
                st.markdown("### 法律建议")
                st.markdown(result.get("answer", ""))

                if "references" in result and result["references"]:
                    with st.expander("法律参考", expanded=True):
                        for ref in result["references"]:
                            st.markdown(f"- {ref}")

                # 生成下载报告
                report = f"""法律咨询报告
日期: {timestamp}
咨询类型: 基本法律信息
法律领域: {st.session_state.legal_domain}
问题: {query}

法律建议:
{result.get('answer', '')}

法律参考:
{chr(10).join(['- ' + ref for ref in result.get('references', [])])}
"""
                st.markdown(get_download_link(report, "法律咨询报告.txt"), unsafe_allow_html=True)

with tab2:
    st.markdown('<p class="sub-header">法律文件解读</p>', unsafe_allow_html=True)
    st.markdown("上传法律文件，获取专业解读和分析。")

    supported_types = []
    if DOCX_SUPPORT:
        supported_types.append("docx")
    if PDF_SUPPORT:
        supported_types.append("pdf")
    supported_types.append("txt")

    if not (DOCX_SUPPORT and PDF_SUPPORT):
        st.warning("未安装全部文档处理库。某些文件类型可能无法处理。请运行以下命令安装所需依赖：\n`pip install python-docx PyPDF2`")

    doc_file = st.file_uploader("上传需要解读的法律文件", type=supported_types)

    if doc_file:
        file_type = doc_file.name.split(".")[-1].lower()
        doc_content = display_document_content(doc_file, file_type)

        if doc_content:
            st.session_state.doc_content = doc_content
            with st.expander("文件内容预览"):
                st.text(doc_content[:1000] + ("..." if len(doc_content) > 1000 else ""))
        else:
            st.error("无法读取文件内容，请检查文件格式")

    doc_query = st.text_area(
        "请输入关于文件的具体问题:",
        height=120,
        placeholder="例如：请解释该合同的主要条款..."
    )

    if st.button("解读文件", key="doc_button"):
        if not st.session_state.doc_content:
            st.warning("请先上传法律文件")
        elif not doc_query:
            st.warning("请输入您对文件的具体问题")
        else:
            with st.spinner("AI正在分析文件内容，请稍等..."):
                full_query = f"请解读以下法律文件内容:\n{st.session_state.doc_content}\n\n用户问题: {doc_query}"
                result = legal_agent(full_query, "法律文件解读", st.session_state.legal_domain)

                # 保存结果
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.chat_history.append({
                    "type": "法律文件解读",
                    "query": doc_query,
                    "document": doc_file.name if doc_file else "",
                    "result": result,
                    "timestamp": timestamp
                })

                # 显示结果
                st.markdown("### 文件解读")
                st.markdown(result.get("answer", ""))

                if "references" in result and result["references"]:
                    with st.expander("法律参考", expanded=True):
                        for ref in result["references"]:
                            st.markdown(f"- {ref}")

                # 生成下载报告
                report = f"""法律文件解读报告
日期: {timestamp}
文件名: {doc_file.name if doc_file else "未知文件"}
问题: {doc_query}

解读结果:
{result.get('answer', '')}

法律参考:
{chr(10).join(['- ' + ref for ref in result.get('references', [])])}
"""
                st.markdown(get_download_link(report, "法律文件解读报告.txt"), unsafe_allow_html=True)

with tab3:
    st.markdown('<p class="sub-header">案件研究与策略</p>', unsafe_allow_html=True)
    st.markdown("描述您的案件情况，获取研究分析和策略建议。")

    case_details = st.text_area(
        "案件基本情况:",
        height=150,
        placeholder="描述案件的关键事实、时间线和需要解决的问题..."
    )

    case_query = st.text_area(
        "您希望获得什么样的建议:",
        height=100,
        placeholder="例如：我希望了解可能的法律风险和应对策略..."
    )

    if st.button("获取案例分析", key="case_button"):
        if not case_details:
            st.warning("请描述案件的基本情况")
        elif not case_query:
            st.warning("请说明您希望获得的建议")
        else:
            with st.spinner("AI正在分析案件，请稍等..."):
                full_query = f"案件研究请求:\n{case_details}\n\n用户问题: {case_query}"
                result = legal_agent(full_query, "案件研究与策略", st.session_state.legal_domain)

                # 保存结果
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.chat_history.append({
                    "type": "案件研究与策略",
                    "case_details": case_details,
                    "query": case_query,
                    "result": result,
                    "timestamp": timestamp
                })

                # 显示结果
                st.markdown("### 案件分析")
                st.markdown(result.get("answer", ""))

                if "steps" in result and result["steps"]:
                    st.markdown("### 建议步骤")
                    for i, step in enumerate(result["steps"], 1):
                        st.markdown(f"{i}. {step}")

                if "references" in result and result["references"]:
                    with st.expander("法律参考", expanded=True):
                        for ref in result["references"]:
                            st.markdown(f"- {ref}")

                # 生成下载报告
                report = f"""案件研究报告
日期: {timestamp}
法律领域: {st.session_state.legal_domain}
案件情况: {case_details}
咨询问题: {case_query}

案件分析:
{result.get('answer', '')}

建议步骤:
{chr(10).join([str(i+1) + '. ' + step for i, step in enumerate(result.get('steps', []))])}

法律参考:
{chr(10).join(['- ' + ref for ref in result.get('references', [])])}
"""
                st.markdown(get_download_link(report, "案件研究报告.txt"), unsafe_allow_html=True)

# 历史记录部分
if st.session_state.chat_history:
    st.markdown('<p class="sub-header">咨询历史记录</p>', unsafe_allow_html=True)

    for i, item in enumerate(reversed(st.session_state.chat_history[-5:])):
        with st.expander(f"{item['timestamp']} - {item['type']}", expanded=i==0):
            st.markdown(f"**问题**: {item['query']}")
            if item['type'] == "法律文件解读" and 'document' in item:
                st.markdown(f"**文件**: {item['document']}")
            if item['type'] == "案件研究与策略" and 'case_details' in item:
                st.markdown(f"**案件情况**: {item['case_details']}")

            st.markdown("**回答**:")
            st.markdown(item['result'].get('answer', ''))

            if "steps" in item['result'] and item['result']["steps"]:
                st.markdown("**建议步骤**:")
                for i, step in enumerate(item['result']["steps"], 1):
                    st.markdown(f"{i}. {step}")

            if "references" in item['result'] and item['result']["references"]:
                st.markdown("**法律参考**:")
                for ref in item['result']["references"]:
                    st.markdown(f"- {ref}")