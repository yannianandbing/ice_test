import streamlit as st
import os
from openai import OpenAI
from datetime import datetime
import json
from typing import List, Dict

# 设置页面的配置项
st.set_page_config(
    page_title = "AI智能伴侣",
    page_icon = "random",
    # 布局
    layout = "wide",
    # 控制的是侧边栏的状态
    initial_sidebar_state = "expanded",
    menu_items = {}
)

MODEL_NAME="deepseek-v4-pro"

# 新增常量（记忆管理相关）
MAX_MESSAGES_BEFORE_SUMMARY = 140 # 消息数超过70触发摘要
KEEP_RECENT = 20 # 摘要后保留最近10条原始消息
SUMMARY_CACHE_SIZE = 5 # 缓存5个摘要后合并长期记忆
LONG_TERM_FIELD_MAX = 300 # 每个长期记忆字段最大字数
LONG_TERM_TOTAL_MAX = 1000 # 长期记忆总字数上限
CHAT_HISTORY_DIR = "chat_history" # 文件夹A
AI_CONTEXT_DIR = "ai_context" # 文件夹B

# 生成会话标识函数
def generate_session_name() -> str:
     return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# 保存会话信息函数
def save_session() -> None:
    if not st.session_state.current_session:
        return
    session_id = st.session_state.current_session

    # 保存完整对话记录（文件A）
    history_data = {
        "session_id": session_id,
        "user_nick_name":st.session_state.user_nick_name,
        "user_nature":st.session_state.user_nature,
        "ai_nick_name": st.session_state.ai_nick_name,
        "ai_nature": st.session_state.ai_nature,
        "messages": st.session_state.full_history,
    }
    os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)
    try:
        with open(os.path.join(CHAT_HISTORY_DIR, f"{session_id}.json"), "w", encoding="utf-8") as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"保存会话失败：{e}")

    # 保存AI上下文（文件B）
    context_data = {
        "session_id": session_id,
        "user_nick_name": st.session_state.user_nick_name,  # 新增
        "user_nature": st.session_state.user_nature,  # 新增
        "ai_nick_name": st.session_state.ai_nick_name,  # 新增
        "ai_nature": st.session_state.ai_nature,  # 新增
        "messages": st.session_state.messages,
        "summary_cache": st.session_state.summary_cache,
        "long_term_memory": st.session_state.long_term_memory,
    }
    os.makedirs(AI_CONTEXT_DIR, exist_ok=True)
    try:
        with open(os.path.join(AI_CONTEXT_DIR, f"{session_id}.json"), "w", encoding="utf-8") as f:
            json.dump(context_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"保存会话失败：{e}")

# 加载所有的会话列表信息
def load_sessions() -> List[str]:
    session_list = []
    if os.path.exists(CHAT_HISTORY_DIR):
        for filename in os.listdir(CHAT_HISTORY_DIR):
            if filename.endswith(".json"):
                session_list.append(filename[:-5])
    session_list.sort(reverse=True) # 排序，降序排序
    return session_list

# 加载指定的会话信息
def load_session(session_name: str) -> None:
    # 读取完整历史（文件A）
    history_path = os.path.join(CHAT_HISTORY_DIR, f"{session_name}.json")
    if os.path.exists(history_path):
        with open(history_path, "r", encoding="utf-8") as f:
            history_data = json.load(f)
            st.session_state.full_history = history_data.get("messages", [])
            st.session_state.user_nick_name = history_data.get("user_nick_name", "")
            st.session_state.user_nature = history_data.get("user_nature", "")
            st.session_state.ai_nick_name = history_data.get("ai_nick_name", "C")
            st.session_state.ai_nature = history_data.get("ai_nature", "正常人")
    else:
        # 兼容旧文件或默认
        st.session_state.full_history = []

    # 读取AI上下文（文件B）
    context_path = os.path.join(AI_CONTEXT_DIR, f"{session_name}.json")
    if os.path.exists(context_path):
        with open(context_path, "r", encoding="utf-8") as f:
            context_data = json.load(f)
            st.session_state.messages = context_data.get("messages", [])
            st.session_state.summary_cache = context_data.get("summary_cache", [])
            st.session_state.long_term_memory = context_data.get(
                "long_term_memory",
                {"user": "", "partner": "", "relationship": "", "timeline" : []})
            # 新增：如果文件B有角色信息，则优先使用（但当前逻辑下文件A也会覆盖，不影响）
            st.session_state.user_nick_name = context_data.get("user_nick_name",
                                                               st.session_state.get("user_nick_name", ""))
            st.session_state.user_nature = context_data.get("user_nature", st.session_state.get("user_nature", ""))
            st.session_state.ai_nick_name = context_data.get("ai_nick_name", st.session_state.get("ai_nick_name", "C"))
            st.session_state.ai_nature = context_data.get("ai_nature", st.session_state.get("ai_nature", "正常人"))
    else:
        # 初始默认
        st.session_state.messages = []
        st.session_state.summary_cache = []
        st.session_state.long_term_memory = {"user": "", "partner": "", "relationship": "", "timeline" : []}
    st.session_state.current_session = session_name

# 删除会话信息函数
def delete_session(session_name: str) -> None:
    # 删除历史文件A
    history_file = os.path.join(CHAT_HISTORY_DIR, f"{session_name}.json")
    if os.path.exists(history_file):
        os.remove(history_file)
    # 删除上下文文件B
    context_file = os.path.join(AI_CONTEXT_DIR, f"{session_name}.json")
    if os.path.exists(context_file):
        os.remove(context_file)

    # 如果删除的是当前会话，则需要更新消息列表
    if session_name == st.session_state.current_session:
        st.session_state.messages = []
        st.session_state.full_history = []
        st.session_state.current_session = generate_session_name()
        st.session_state.user_nick_name = ""
        st.session_state.user_nature = ""
        st.session_state.ai_nick_name = "C"
        st.session_state.ai_nature = "正常人"
        # 新增：重置记忆状态
        st.session_state.summary_cache = []
        st.session_state.long_term_memory = {"user": "", "partner": "", "relationship": "", "timeline": []}
        st.session_state.undo_pending = []
        st.session_state.undo_click_count = 0
        st.session_state.five_undo_click_count = 0

# 初始化
def init_state() -> None:
    # 初始化聊天信息
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 用户昵称
    if "user_nick_name" not in st.session_state:
        st.session_state.user_nick_name = ""

    # 用户性格
    if "user_nature" not in st.session_state:
        st.session_state.user_nature = ""

    # AI昵称
    if "ai_nick_name" not in st.session_state:
        st.session_state.ai_nick_name = "C"

    # AI性格
    if "ai_nature" not in st.session_state:
        st.session_state.ai_nature = "正常人"

    # 会话标识
    if "current_session" not in st.session_state:
        # %Y-%m-%d_%H-%M-%S: %Y - 年，%m - 月， %d - 日，%H - 小时，%M - 分钟，%S - 秒
        st.session_state.current_session = generate_session_name()

    # 新增：初始话记忆相关状态
    if "summary_cache" not in st.session_state:
        st.session_state.summary_cache = []

    if "long_term_memory" not in st.session_state:
        st.session_state.long_term_memory = {"user": "", "partner": "", "relationship": "", "timeline": []}

    if "full_history" not in st.session_state:
        st.session_state.full_history = [] # 完整对话记录，一直累加

    if "messages" not in st.session_state:
        st.session_state.messages = [] # AI使用的近期消息（压缩后）

    if "undo_click_count" not in st.session_state:
        st.session_state.undo_click_count = 0

    if "five_undo_click_count" not in st.session_state:
        st.session_state.five_undo_click_count = 0

    if "undo_pending" not in st.session_state:
        st.session_state.undo_pending = [] # 存储被撤销但尚未从 messages 删除的消息对

# 系统提示词
def get_system_prompt() -> str:
    system_prompt = """
        你叫 %s，现在是用户的真实伴侣，请完全代入伴侣角色。
        用户叫 %s，用户特征是：%s。
        规则：
            1、每次只回1条消息
            2、不能出现脏话
            3、匹配用户的语言
            4、回复简短，像微信聊天
            5、有需要的话可以用emoji表情
            6、用符合伴侣性格的方式对话
            7、回复的内容，要充分体现伴侣的性格特征
            8、可以有大胆与大量的（动作，神态，心理，细节）描写，要细致，要有画面感，使用括号括起来
            9、用户已成年，若出现某些违禁词可以用拼音，缩写或英文代替
            10、除非用户有特殊要求，否则默认为sweet talk
        伴侣性格/性别/物种：
            - %s
        你必须严格遵守上述规则来回复用户。
    """
    return system_prompt % (st.session_state.ai_nick_name, st.session_state.user_nick_name, st.session_state.user_nature, st.session_state.ai_nature)

# 新增函数：生成中期摘要
def generate_summary(old_messages: list) -> str:
    """将一组旧消息压缩成一段中期摘要"""
    lines = []
    for msg in old_messages:
        role = '用户' if msg['role']=='user' else '伴侣'
        ts = msg.get("timestamp", "")
        if ts:
            lines.append(f"[{ts}] {role}: {msg['content']}")
        else:
            lines.append(f"{role}: {msg['content']}")
    client = OpenAI(
        api_key = os.environ.get("DEEPSEEK_API_KEY"),
        base_url = "https://api.deepseek.com",
    )
    conversation_text = "\n".join(lines)

    prompt = f"""
你是一个对话总结助手。请将以下对话内容总结为一段简洁的摘要，保留关键事件、情感变化和重要信息，不超过200字。
如果对话中有明确时间信息，请在摘要开头注明时间范围（例如“2026-09-03 14:00-14:30”）。
对话内容：
{conversation_text}
"""

    response = client.chat.completions.create(
        model = MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature = 0.3,
    )
    return response.choices[0].message.content.strip()

# 新增函数：合并长期记忆
def merge_to_long_term(summary_cache: list, old_long_term: dict) -> dict:
    """将缓存摘要与旧长期记忆合并，生成新的长期记忆（三字段）"""
    client = OpenAI(
        api_key=os.environ.get("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
    )
    old_memory_text = f"""
用户记忆：{old_long_term.get('user', '')}
伴侣记忆：{old_long_term.get('partner', '')}
关系互动记忆：{old_long_term.get('relationship', '')}
时间线：{json.dumps(old_long_term.get('timeline', []), ensure_ascii=False)}
"""
    cache_text = "\n".join([f"摘要{i + 1}：{s}" for i, s in enumerate(summary_cache)])

    prompt = f"""
你是一个负责长期记忆更新的助手。请根据以下材料，更新长期记忆。

当前长期记忆：
{old_memory_text if old_memory_text.strip() else "（空）"}

新的对话摘要（按时间顺序）：
{cache_text}

请提取并合并所有关键信息，输出更新后的长期记忆。要求：
- 用户记忆：记录用户的基本信息、喜好、习惯、重要日期、情感表达等。
- 伴侣记忆：记录伴侣角色的状态变化，如情感、思维转变、标记点、共同经历等。
- 关系互动记忆：记录关系阶段、重要事件、共同目标、内部梗等。
- 时间线：按时间顺序记录重要事件，每个事件包含 time（时间范围字符串）和 summary（事件简述）。如果旧时间线已有事件，请合并更新。
- 保持简洁，每个字段（user/partner/relationship）不超过{LONG_TERM_FIELD_MAX}字，时间线最多保留20条。
- 输出格式为严格的JSON对象，包含字段："user"、"partner"、"relationship"、"timeline"。不要输出任何额外文字。
"""
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    content = response.choices[0].message.content.strip()
    # 清理可能的Markdown 代码块标记
    if content.startswith("```"):
        content = content.strip("`")
    if content.startswith("json"):
        content = content[4:]
    content = content.strip()

    try:
        memory = json.loads(content)
        for key in ["user", "partner", "relationship"]:
            if key not in memory:
                memory[key] = old_long_term.get(key, "")
        if "timeline" not in memory:
            memory["timeline"] = old_long_term.get("timeline", [])
        elif not isinstance(memory["timeline"], list):
            # 如果模型返回了字符串，尝试转为列表或使用旧值
            memory["timeline"] = old_long_term.get("timeline", [])
        return memory
    except:
        st.warning("长期记忆解析失败，保留旧记忆")
        return old_long_term

# 新增函数：强制限制记忆长度
def enforce_memory_limits(memory: dict) -> dict:
    """检查记忆长度，若超限则进行压缩"""
    total_chars = sum(len(str(memory.get(k, ""))) for k in ["user", "partner", "relationship", "timeline"])
    if total_chars <= LONG_TERM_TOTAL_MAX and all(
            len(str(memory.get(k, ""))) <= LONG_TERM_FIELD_MAX for k in ["user", "partner", "relationship"]) and len(memory.get("timeline", [])) <= 20:
        return memory

    # 需要压缩
    client = OpenAI(
        api_key=os.environ.get("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
    )
    mem_text = f"""
用户记忆：{memory.get('user', '')}
伴侣记忆：{memory.get('partner', '')}
关系互动记忆：{memory.get('relationship', '')}
时间线：{json.dumps(memory.get('timeline', []), ensure_ascii=False)}
"""
    prompt = f"""
以下长期记忆长度过长，请在不丢失最关键信息的前提下进行压缩。
要求：
- 用户记忆、伴侣记忆、关系互动记忆每个字段不超过200字。
- 时间线最多保留10条，保留最重要的时间点。
- 输出格式为严格的JSON对象，包含字段："user"、"partner"、"relationship"、"timeline"。不要输出任何额外文字。

当前长期记忆：
{mem_text}
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    content = response.choices[0].message.content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    try:
        compressed = json.loads(content)
        for key in ["user", "partner", "relationship"]:
            if key not in compressed:
                compressed[key] = memory.get(key, "")
        if "timeline" not in compressed or not isinstance(compressed["timeline"], list):
            compressed["timeline"] = memory.get("timeline", [])
        return compressed
    except:
        st.warning("记忆压缩解析失败，保留原记忆")
        return memory

# 处理用户输入
def handle_user_input(prompt: str) -> None:
    # 清理待删除的消息（从AI上下文中真正删除）
    if st.session_state.undo_pending:
        # 由于 message 可经过了压缩，简单做法：直接删除所有出现在 undo_pending 中的消息对象
        # 但更可靠的方式是记录消息在 message 中的索引，但为简化，我们在这里遍历删除
        for user_msg, ai_msg in st.session_state.undo_pending:
            # 删除 ai_msg（如果存在且还在 message 中）
            if ai_msg and ai_msg in st.session_state.messages:
                st.session_state.messages.remove(ai_msg)
            # 删除 user_msg (如果还在 message 中）
            if user_msg in st.session_state.messages:
                st.session_state.messages.remove(user_msg)
        st.session_state.undo_pending = []
        save_session() # 保存更新后的AI上下文

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    user_msg = {"role": "user", "content": prompt, "timestamp": current_time}
    st.session_state.full_history.append(user_msg)
    st.session_state.messages.append(user_msg)
    st.chat_message("user").text(prompt)
    st.session_state.undo_click_count = 0
    st.session_state.five_undo_click_count = 0

    # 新增：记忆压缩逻辑（放在调用主模型之前）
    if len(st.session_state.messages) > MAX_MESSAGES_BEFORE_SUMMARY:
        old_messages = st.session_state.messages[:-KEEP_RECENT]
        recent_messages = st.session_state.messages[-KEEP_RECENT:]

        if old_messages:
            try:
                new_summary = generate_summary(old_messages)
                st.session_state.summary_cache.append(new_summary)
            except Exception as e:
                st.warning(f"生成摘要失败：{e}")

        # 检查缓存是否已满
        if len(st.session_state.summary_cache) >= SUMMARY_CACHE_SIZE:
            try:
                new_long_term = merge_to_long_term(
                    st.session_state.summary_cache,
                    st.session_state.long_term_memory
                )
                new_long_term = enforce_memory_limits(new_long_term)
                st.session_state.long_term_memory = new_long_term
                st.session_state.summary_cache = []
            except Exception as e:
                st.warning(f"合并长期记忆失败：{e}")

        # 只保留最近消息
        st.session_state.messages = recent_messages

    # 构建 API 消息（修改：注入长期记忆和缓存摘要）
    system_content = get_system_prompt()

    mem = st.session_state.long_term_memory
    if any(mem.values()):
        mem_text = ""
        if mem.get("user"):
            mem_text += f"\n[用户记忆]\n{mem['user']}"
        if mem.get("partner"):
            mem_text += f"\n[伴侣记忆]\n{mem['partner']}"
        if mem.get("relationship"):
            mem_text += f"\n[关系互动记忆]\n{mem['relationship']}"
        if mem.get("timeline"):
            timeline_text = "\n".join(
                [f"- {item.get('time', '未知时间')}:{item.get('summary', '')}" for item in mem["timeline"]]
            )
            mem_text += f"\n[时间线]\n{timeline_text}"
        system_content += f"\n\n[长期记忆]\n{mem_text}"

    if st.session_state.summary_cache:
        cache_text = "\n".join([f"- {s}" for s in st.session_state.summary_cache])
        system_content += f"\n\n[近期对话摘要]\n{cache_text}"

    api_messages = [
        {"role": "system", "content": system_content},
        *st.session_state.messages,
    ]

    try:
        client = OpenAI(
            api_key=os.environ.get("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
        )
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=api_messages,
            stream=True,
        )
        # 输出大模型返回的结果(流式输出的解析方式）
        with st.chat_message("assistant"):
            response_message = st.empty()  # 创建一个空的组件，用于提示大模型返回的结果
            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    response_message.markdown(full_response)

        # 保存大模型返回的结果
        assistant_msg = {"role": "assistant",
                         "content": full_response,
                         "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                         }
        st.session_state.messages.append(assistant_msg)
        st.session_state.full_history.append(assistant_msg)
        save_session()

    except Exception as e:
        st.error(f"AI调用失败：{e}")
        st.session_state.messages.pop()

def generate_hidden_message(scenario: str = "undo_five") -> tuple[str, str]:
    """让 AI 生成彩蛋标题和正文，根据 scenario 生成不同语气，返回 (title, body)"""
    client = OpenAI(
        api_key=os.environ.get("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
    )

    if scenario == "all_deleted":
        prompt = (
            "你的伴侣刚刚把所有对话消息都撤回了，现在聊天记录已经清空。"
            "请根据你的角色身份与记忆进行发挥，用挽留的语气回应这件事，告诉对方你很伤心。"
            "要求：\n"
            "1. 标题：不超过10个字，带点惊讶或无奈。\n"
            "2. 正文：2~3句话，表达你的感受，不要超过60字。\n"
            "输出格式严格为JSON，包含两个字段：'title' 和 'body'。"
        )
    elif scenario == "no_more_messages":
        prompt = (
            "你的伴侣试图继续撤回消息，但你已经没有可删除的近期记忆了（AI上下文已空）。"
            "请根据你的角色身份与记忆进行发挥，用挽留的语气回应这件事，告诉对方不能再撤了。"
            "要求：\n"
            "1. 标题：不超过10个字，可以带emoji。\n"
            "2. 正文：2~3句话，表达你的态度，不要超过60字。\n"
            "输出格式严格为JSON，包含两个字段：'title' 和 'body'。"
        )
    else:  # undo_five
        prompt = (
            f"你刚刚注意到，你的伴侣（用户）刚刚在撤回了{st.session_state.five_undo_click_count}轮消息之后再一次连续撤回了5次（1轮）对话消息。"
            "请根据你的角色身份与记忆进行发挥，用挽留的语气回应这件事。"
            "根据被撤销轮数，情绪可逐层增加，但请保持在适当范围内。"
            "要求：\n"
            "1. 标题：不超过10个字，带有你的性格特点，可以用emoji。\n"
            "2. 正文：2~3句话，表达你的感受或调侃，不要超过60字。\n"
            "输出格式严格为JSON，包含两个字段：'title' 和 'body'。"
        )
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": get_system_prompt()},
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,  # 稍微提高随机性，让回复更生动
        )
        content = response.choices[0].message.content.strip()
        # 简单解析 JSON
        if content.startswith("```"):
            content = content.strip("`")
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content)
        title = data.get("title", "你撤回了好多消息呢")
        body = data.get("body", "是不是打错字啦？")
        return title, body
    except Exception as e:
        st.warning(f"彩蛋生成失败，使用默认文本: {e}")
        return "你撤回了好多消息呢", "是不是打错字啦？"

# 小彩蛋
@st.dialog("来自伴侣的悄悄话")  # 固定标题，内部显示动态标题
def show_hidden_window(scenario: str = "undo_five"):
    title, body = generate_hidden_message(scenario)
    st.markdown(f"### {title}")   # 动态标题
    st.write(body)
    if scenario == "all_deleted":
        st.write("所有对话都被你撤回了，这里空空的……")
    elif scenario == "no_more_messages":
        st.write("没办法再往前撤了，我已经没有更早的记忆了。")
    st.write("温馨提示：在您进行下次对话或关闭窗口前，您的伴侣将不会失去被撤销的记忆")
    if st.button("知道了"):
        st.rerun()

# 撤销操作
def delete_user_message():
    if not st.session_state.full_history:
        return

    # 处理完整历史
    last_msg = st.session_state.full_history[-1]
    # 如果最后一条是AI回复，则同时移除它和它前面的用户消息
    if last_msg["role"] == "assistant" and len(st.session_state.full_history) >= 2:
        user_msg = st.session_state.full_history[-2]
        ai_msg = st.session_state.full_history[-1]
        st.session_state.full_history.pop() # 移除AI回复
        st.session_state.full_history.pop() # 移除用户消息
        st.session_state.undo_pending.append((user_msg, ai_msg))
    else:
        # 如果最后一条是用户消息（例如AI回复失败），只移除它
        st.session_state.undo_pending.append((last_msg, None))
        st.session_state.full_history.pop()

    # 保存更新后的会话
    save_session()

def main():
    init_state()

    st.title("AI智能伴侣")
    if os.path.exists("resources/ice.jpg"):
        st.logo("resources/ice.jpg")

    with st.sidebar:
        # 会话信息
        st.subheader("AI控制面板")

        # 新建会话
        if st.button("新建会话", use_container_width=True, icon="🚀"):
            if st.session_state.messages:
                save_session()
            st.session_state.messages = []
            st.session_state.full_history = []
            st.session_state.undo_pending = []
            st.session_state.user_nick_name = ""
            st.session_state.user_nature = ""
            st.session_state.undo_click_count = 0
            st.session_state.five_undo_click_count = 0
            st.session_state.current_session = generate_session_name()
            st.session_state.ai_nick_name = "C"
            st.session_state.ai_nature = "正常人"
            # 新增：重置记忆状态
            st.session_state.summary_cache = []
            st.session_state.long_term_memory = {"user": "", "partner": "", "relationship": "", "timeline": []}
            st.rerun()  # 重新运行当前页面

        # 会话历史
        session_list = load_sessions()
        for session in session_list:
            col1, col2 = st.columns([4, 1])
            with col1:
                # 加载会话信息
                # 三元运算符：如果条件为真，则返回第一个表达式的值；否则，返回第二个表达式的值 --> 语法：值1 if 条件 else 值2
                if st.button(session, use_container_width=True, icon="📁", key=f"load_{session}",
                             type="primary" if session == st.session_state.current_session else "secondary"):
                    load_session(session)
                    st.rerun()
            with col2:
                # 删除会话信息
                if st.button("", use_container_width=True, icon="🗑️", key=f"delete_{session}"):
                    delete_session(session)
                    st.rerun()

            # st.button(session, use_container_width=True, icon="📁")
            # st.button("", use_container_width=True, icon="🗑️")

        # 分割线
        st.divider()

        st.subheader("您的信息（请不要随意更改哦~）")
        # 昵称输入框
        user_nick_name = st.text_input(
            "昵称",
            placeholder="请输入昵称（可不填）",
            value=st.session_state.user_nick_name,
            key = f"user_nick_{st.session_state.current_session}"
        )
        if user_nick_name != st.session_state.user_nick_name:
            st.session_state.user_nick_name = user_nick_name
            save_session()

        # 性格输入框
        user_nature = st.text_area(
            "性格/性别/物种",
            placeholder="请输入文字（可不填）",
            value=st.session_state.user_nature,
            key=f"user_nature_{st.session_state.current_session}"
        )
        if user_nature != st.session_state.user_nature:
            st.session_state.user_nature = user_nature
            save_session()

        st.subheader("伴侣信息(请不要随意更改哦~）")
        # 昵称输入框
        ai_nick_name = st.text_input(
            "昵称",
            placeholder="请输入昵称",
            value=st.session_state.ai_nick_name,
            key=f"ai_nick_{st.session_state.current_session}"
        )
        if ai_nick_name != st.session_state.ai_nick_name:
            st.session_state.ai_nick_name = ai_nick_name
            save_session()

        # 性格输入框
        ai_nature = st.text_area(
            "性格/性别/物种",
            placeholder="请输入文字",
            value=st.session_state.ai_nature,
            key=f"ai_nature_{st.session_state.current_session}"
        )
        if ai_nature != st.session_state.ai_nature:
            st.session_state.ai_nature = ai_nature
            save_session()

        # 分割线
        st.divider()

        st.text("字没打完就发出去了怎么办？")
        if st.button("撤回按钮", use_container_width=True, icon="↩️"):
            # 边界1：完整历史和AI上下文都为空
            if not st.session_state.full_history:
                show_hidden_window("all_deleted")
            elif not st.session_state.messages or len(st.session_state.undo_pending) >= len(st.session_state.messages) // 2:
                show_hidden_window("no_more_messages")
            else:
                delete_user_message()
                st.session_state.undo_click_count += 1
                if st.session_state.undo_click_count >= 5:
                    show_hidden_window("undo_five")
                    st.session_state.undo_click_count = 0
                    st.session_state.five_undo_click_count += 1
        st.text("不要一次撤回太多哦~")

    # 展示聊天信息
    st.caption(f"会话名称：{st.session_state.current_session}")
    for message in st.session_state.full_history:  # {"role": "user", "content": prompt}
        if message["role"] == "user":
            st.chat_message(message["role"]).text(message["content"])
        else:
            st.chat_message("assistant").markdown(message["content"])
        # if message["role"] == "user":
        #     st.chat_message("user").write(message["content"])
        # else:
        #     st.chat_message("assistant").write(message["content"])

    if prompt := st.chat_input("请输入您要问的问题"):
        handle_user_input(prompt)

if __name__ == '__main__':
    main()