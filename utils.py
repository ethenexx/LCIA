"""
utils.py - 法律咨询智能体使用的工具函数
"""
import json
import os
from typing import List, Dict, Any

import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# 法律领域列表
LEGAL_DOMAINS = [
    "一般法律咨询",
    "劳动法",
    "合同法",
    "婚姻家庭法",
    "刑事法",
    "民事诉讼",
    "商业法",
    "知识产权",
    "房地产法",
    "行政法",
    "交通事故",
    "消费者权益",
    "医疗纠纷"
]

# 示例问题映射
SAMPLE_QUESTIONS = {
    "一般法律咨询": [
        "如何查询某项法律法规的最新版本？",
        "我需要法律援助，应该如何申请？",
        "什么情况下需要公证？",
    ],
    "劳动法": [
        "单位无故拖欠工资怎么办？",
        "试用期被辞退是否有赔偿？",
        "加班费如何计算？",
    ],
    "合同法": [
        "口头协议是否具有法律效力？",
        "合同中的违约金上限是多少？",
        "对方不履行合同义务怎么办？",
    ],
    "婚姻家庭法": [
        "离婚时财产如何分割？",
        "如何申请子女抚养权？",
        "家庭暴力应如何寻求法律保护？",
    ],
    "刑事法": [
        "什么是正当防卫？",
        "取保候审的条件是什么？",
        "轻伤和重伤的法律界定标准是什么？",
    ],
    "民事诉讼": [
        "民事诉讼的基本流程是什么？",
        "如何申请法院强制执行？",
        "民事诉讼的诉讼时效是多久？",
    ],
    "商业法": [
        "注册公司的基本法律要求是什么？",
        "股东权益如何得到法律保障？",
        "公司破产清算的流程是什么？",
    ],
    "知识产权": [
        "如何为自己的创意申请专利？",
        "商标侵权的判定标准是什么？",
        "软件著作权保护期限是多久？",
    ],
    "房地产法": [
        "二手房交易中需要注意哪些法律问题？",
        "房屋租赁合同必须包含哪些条款？",
        "业主维权的法律途径有哪些？",
    ],
    "行政法": [
        "如何申请政府信息公开？",
        "行政复议的申请条件和流程是什么？",
        "行政处罚决定不服如何救济？",
    ],
    "交通事故": [
        "交通事故责任如何认定？",
        "交通事故赔偿项目包括哪些？",
        "交通事故调解不成功怎么办？",
    ],
    "消费者权益": [
        "网购商品存在质量问题如何维权？",
        "餐饮食品安全问题的赔偿标准是什么？",
        "如何投诉商家虚假宣传？",
    ],
    "医疗纠纷": [
        "医疗事故与医疗过错的区别是什么？",
        "医疗损害赔偿的构成要件有哪些？",
        "如何收集医疗纠纷证据？",
    ]
}

# 提示模板
PROMPT_TEMPLATE = """你是一位专业的法律顾问，请根据用户的问题提供准确、客观的法律信息和建议。

请注意，你的回答应当：
1. 基于中国现行法律法规，避免给出可能误导用户的个人见解
2. 明确指出法律的局限性和不确定性
3. 提醒用户在重要法律事务上咨询专业律师
4. 提供清晰、结构化的回答

当前咨询类型: {consult_type}
法律领域: {legal_domain}

请按照以下JSON格式回应:

对于基本法律信息:
{{"answer": "详细的法律解释和信息", "references": ["相关法律条款1", "相关法律条款2"]}}

对于法律文件解读:
{{"answer": "对文件的解释和分析", "references": ["相关法律依据1", "相关法律依据2"]}}

对于案件研究与策略:
{{"answer": "对案件的分析", "steps": ["建议步骤1", "建议步骤2"], "references": ["相关法律案例1", "相关法律案例2"]}}

用户问题: {query}
"""

def get_legal_domains() -> List[str]:
    """获取法律领域列表"""
    return LEGAL_DOMAINS

def get_sample_questions(domain: str) -> List[str]:
    """获取指定领域的示例问题"""
    return SAMPLE_QUESTIONS.get(domain, SAMPLE_QUESTIONS["一般法律咨询"])

def get_api_credentials():
    """获取API凭据，使用st.secrets直接索引方式"""
    try:
        # 使用方括号直接访问secrets
        api_key = st.secrets['API_KEY']
        api_base = 'https://twapi.openai-hk.com/v1'

        return api_key, api_base
    except Exception as e:
        # 如果st.secrets访问失败，尝试环境变量
        try:
            import os
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv("OPENAI_API_KEY")
            api_base = os.getenv("OPENAI_API_BASE", "https://twapi.openai-hk.com/v1")

            if api_key:
                return api_key, api_base
        except:
            pass

        st.error(f"获取API凭据时出错: {e}")
        return None, "https://api.openai.com/v1"

def legal_agent(query: str, consult_type: str, legal_domain: str = "一般法律咨询") -> Dict[str, Any]:
    """法律咨询智能体函数"""

    try:
        # 获取API凭据
        api_key, api_base = get_api_credentials()

        if not api_key:
            return {
                "answer": "错误：未找到API密钥。请在Streamlit Secrets中设置API_KEY。",
                "references": ["请在Streamlit设置中添加API_KEY"]
            }

        # 使用固定模型，不再尝试多个模型
        try:
            model = ChatOpenAI(
                api_key=api_key,
                base_url=api_base,
                model="gpt-3.5-turbo",
                temperature=0.2,
                max_tokens=4096
            )

            prompt = PromptTemplate(
                input_variables=["query", "consult_type", "legal_domain"],
                template=PROMPT_TEMPLATE
            )

            chain = LLMChain(llm=model, prompt=prompt)
            response = chain.run(query=query, consult_type=consult_type, legal_domain=legal_domain)

            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # 处理非JSON格式的响应
                return {
                    "answer": response,
                    "references": ["无法识别格式化参考"]
                }
        except Exception as e:
            return {
                "answer": f"抱歉，无法连接到AI服务：{str(e)}",
                "references": ["请检查您的API密钥和网络连接"]
            }

    except Exception as err:
        print(f"Error: {err}")
        return {
            "answer": f"抱歉，处理您的请求时遇到了问题：{str(err)}。请稍后再试。",
            "references": ["系统错误"]
        }