import streamlit as st
import os
import sys
import PyPDF2
from google import genai
from google.genai import types
from dotenv import load_dotenv
import time

# --- PAGE CONFIG & GLOBAL AVATAR REMOVAL ---
st.set_page_config(page_title="PavementEye Brain", layout="wide")

# Global CSS to remove ALL avatars
st.markdown("""
<style>
    /* Hide ALL chat message avatars */
    [data-testid="stChatMessage"] [data-testid="stImage"] {
        display: none !important;
    }
    
    /* Alternative selectors for chat avatars */
    [data-testid="stChatMessageAvatar"] {
        display: none !important;
    }
    
    /* Hide the avatar column entirely */
    .stChatMessage > div:first-child {
        display: none !important;
    }
    
    /* Target specific user and assistant avatars */
    [data-testid="chatAvatarIcon-user"],
    [data-testid="chatAvatarIcon-assistant"],
    [data-testid="stChatMessageAvatarUser"], 
    [data-testid="stChatMessageAvatarAssistant"] {
        display: none !important;
    }
    
    /* Adjust message spacing since avatars are gone */
    .stChatMessage {
        padding-left: 0 !important;
        padding-right: 0 !important;
    }
    
    .stChatMessage > div:last-child {
        margin-left: 0 !important;
        margin-right: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("PavementEye: Live AI Analyst 🧠")

# --- CUSTOM LOADER COMPONENT ---
def show_custom_loader(message="Loading..."):
    """Display custom animated loader"""
    loader_html = f"""
    <style>
    .custom-loader-container {{
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding: 20px;
        min-height: 100px;
    }}
    .loader {{
        display: flex;
        justify-content: center;
        align-items: center;
        --color: hsl(0, 0%, 87%);
        --animation: 2s ease-in-out infinite;
    }}
    .loader .circle {{
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        width: 20px;
        height: 20px;
        border: solid 2px var(--color);
        border-radius: 50%;
        margin: 0 10px;
        background-color: transparent;
        animation: circle-keys var(--animation);
    }}
    .loader .circle .dot {{
        position: absolute;
        transform: translate(-50%, -50%);
        width: 16px;
        height: 16px;
        border-radius: 50%;
        background-color: var(--color);
        animation: dot-keys var(--animation);
    }}
    .loader .circle .outline {{
        position: absolute;
        transform: translate(-50%, -50%);
        width: 20px;
        height: 20px;
        border-radius: 50%;
        animation: outline-keys var(--animation);
    }}
    .circle:nth-child(2) {{
        animation-delay: 0.3s;
    }}
    .circle:nth-child(3) {{
        animation-delay: 0.6s;
    }}
    .circle:nth-child(4) {{
        animation-delay: 0.9s;
    }}
    .circle:nth-child(5) {{
        animation-delay: 1.2s;
    }}
    .circle:nth-child(2) .dot {{
        animation-delay: 0.3s;
    }}
    .circle:nth-child(3) .dot {{
        animation-delay: 0.6s;
    }}
    .circle:nth-child(4) .dot {{
        animation-delay: 0.9s;
    }}
    .circle:nth-child(5) .dot {{
        animation-delay: 1.2s;
    }}
    .circle:nth-child(1) .outline {{
        animation-delay: 0.9s;
    }}
    .circle:nth-child(2) .outline {{
        animation-delay: 1.2s;
    }}
    .circle:nth-child(3) .outline {{
        animation-delay: 1.5s;
    }}
    .circle:nth-child(4) .outline {{
        animation-delay: 1.8s;
    }}
    .circle:nth-child(5) .outline {{
        animation-delay: 2.1s;
    }}
    @keyframes circle-keys {{
        0% {{
            transform: scale(1);
            opacity: 1;
        }}
        50% {{
            transform: scale(1.5);
            opacity: 0.5;
        }}
        100% {{
            transform: scale(1);
            opacity: 1;
        }}
    }}
    @keyframes dot-keys {{
        0% {{
            transform: scale(1);
        }}
        50% {{
            transform: scale(0);
        }}
        100% {{
            transform: scale(1);
        }}
    }}
    @keyframes outline-keys {{
        0% {{
            transform: scale(0);
            outline: solid 20px var(--color);
            outline-offset: 0;
            opacity: 1;
        }}
        100% {{
            transform: scale(1);
            outline: solid 0 transparent;
            outline-offset: 20px;
            opacity: 0;
        }}
    }}
    .loader-message {{
        margin-top: 20px;
        color: #666;
        font-size: 14px;
        text-align: center;
    }}
    </style>
    <div class="custom-loader-container">
        <div class="loader">
            <div class="circle">
                <div class="dot"></div>
                <div class="outline"></div>
            </div>
            <div class="circle">
                <div class="dot"></div>
                <div class="outline"></div>
            </div>
            <div class="circle">
                <div class="dot"></div>
                <div class="outline"></div>
            </div>
            <div class="circle">
                <div class="dot"></div>
                <div class="outline"></div>
            </div>
        </div>
        <div class="loader-message">{message}</div>
    </div>
    """
    return st.markdown(loader_html, unsafe_allow_html=True)

# --- 1. ROBUST PATH SETUP ---
current_script_dir = os.path.dirname(os.path.abspath(__file__))

def find_project_root(start_dir):
    current = start_dir
    for _ in range(3):
        if os.path.exists(os.path.join(current, "media")) or os.path.exists(os.path.join(current, "docker-compose.yml")):
            return current
        parent = os.path.dirname(current)
        if parent == current: 
            break
        current = parent
    return start_dir 

project_root = find_project_root(current_script_dir)

# Define paths
readme_path = os.path.join(project_root, "README.md")
pdf_path = os.path.join(project_root, "media", "Technical_report_PavementEye.pdf")
env_path = os.path.join(current_script_dir, ".env") 

# Setup Python Path for DB
if project_root not in sys.path:
    sys.path.append(project_root)
sys.path.append(os.path.join(project_root, "streamlit"))

# --- 2. LOAD SECRETS ---
load_dotenv(dotenv_path=env_path)
api_key = os.getenv("GEMINI_API_KEY")
db_host = os.getenv("CASSANDRA_HOST", "localhost")

if not api_key:
    st.error("❌ API Key not found. Please create a .env file.")
    st.stop()

# --- 3. DATABASE CONNECTION ---
def get_db_summary():
    """Connects to Cassandra and gets live stats."""
    try:
        try:
            from db import Cassandra
        except ImportError:
            sys.path.append(os.path.join(project_root, 'streamlit'))
            from db import Cassandra

        db = Cassandra(CASSANDRA_HOST=db_host)
        db.exec("SELECT * FROM detections LIMIT 1000") 
        
        if db.data is None or db.data.empty:
            return "\n[Database connected but no data found in 'detections' table.]\n"

        db.join_roads()
        processed_df = db.calc_pci()
        
        total_roads = len(processed_df['road_index'].unique())
        avg_pci = processed_df['pci'].mean()
        conditions = processed_df['condition'].value_counts().to_dict()
        worst_roads = processed_df[processed_df['pci'] < 40][['road_index', 'pci', 'condition']].head(3).to_dict('records')

        summary = f"""
        --- LIVE DATABASE CONTEXT ---
        - Total Roads Scanned: {total_roads}
        - Network Average PCI: {round(avg_pci, 2)}
        - Condition Breakdown: {conditions}
        - Critical Roads: {worst_roads}
        -----------------------------
        """
        return summary

    except Exception as e:
        print(f"DB Error: {e}")
        return "\n[Database context unavailable]\n"

# --- 4. DOCUMENT LOADER WITH ENHANCED INSTRUCTIONS ---
@st.cache_resource
def load_knowledge_base():
    """Reads FULL PDF and Readme to build the AI's brain."""
    context = """
    SYSTEM INSTRUCTION:
    You are the Senior AI Engineer and Expert Analyst for PavementEye.
    
    CORE CAPABILITIES:
    1. Deep Technical Understanding: Answer questions using the documentation below as your foundation.
    2. Intelligent Reasoning: For complex questions not directly covered in the docs, use logical inference based on:
       - The project's technical architecture
       - Saudi Vision 2030 alignment principles
       - Infrastructure optimization best practices
       - Road maintenance industry standards
       - Cost-benefit analysis frameworks
    3. Team Recognition: Pay close attention to the "Team Actual Work and Roles" table. ALWAYS use full names when discussing team members.
    4. Contextual Analysis: Synthesize information across multiple sections to provide comprehensive insights.
    
    REASONING GUIDELINES:
    - If a question requires knowledge beyond the docs, clearly state "Based on the project architecture and industry standards..."
    - For strategic questions, consider Vision 2030 goals, budget optimization, and scalability
    - For technical questions, infer from the documented tech stack and design patterns
    - For policy questions, align with Saudi infrastructure modernization initiatives
    - Always provide actionable insights, not just facts
    
    RESPONSE QUALITY:
    - Be thorough and analytical for complex questions
    - Provide concrete examples when possible
    - Consider multiple perspectives (technical, financial, operational)
    - Use data from the live database when relevant
    """
    
    # 1. Load PDF
    if os.path.exists(pdf_path):
        try:
            reader = PyPDF2.PdfReader(pdf_path)
            pdf_text = ""
            total_pages = len(reader.pages)
            print(f"Loading {total_pages} pages from PDF...") 
            
            for page in reader.pages:
                pdf_text += page.extract_text() + "\n"
                
            context += f"\n\n--- TECHNICAL REPORT ({total_pages} pages) ---\n{pdf_text}\n"
        except Exception as e:
            print(f"PDF Error: {e}")
            st.error(f"Error reading PDF: {e}")
    else:
        print(f"PDF Not Found at: {pdf_path}")

    # 2. Load README
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            context += f"\n\n--- README CONTENT ---\n{f.read()}\n"

    # 3. Load Database
    context += get_db_summary()
    
    return context

# Load everything with custom loader
if 'knowledge_base_loaded' not in st.session_state:
    loader_placeholder = st.empty()
    with loader_placeholder.container():
        show_custom_loader("Loading Project Knowledge Base...")
    
    knowledge_base = load_knowledge_base()
    st.session_state.knowledge_base_loaded = True
    st.session_state.knowledge_base = knowledge_base
    loader_placeholder.empty()
else:
    knowledge_base = st.session_state.knowledge_base

# --- 5. CHAT INTERFACE (PROPERLY FIXED) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "generating" not in st.session_state:
    st.session_state.generating = False

# Display existing messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Show loader if generating
if st.session_state.generating:
    with st.chat_message("assistant"):
        show_custom_loader("Thinking...")

if prompt := st.chat_input("Ask about the team or data...", disabled=st.session_state.generating):
    # Add user message and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.generating = True
    st.rerun()

# Generate response if flag is set
if st.session_state.generating and len(st.session_state.messages) > 0:
    last_message = st.session_state.messages[-1]
    
    # Only generate if last message is from user and hasn't been answered
    if last_message["role"] == "user":
        # Build conversation history
        conversation_history = ""
        for msg in st.session_state.messages[-6:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            conversation_history += f"\n{role}: {msg['content']}\n"
        
        full_prompt = f"""{knowledge_base}
        
        --- RECENT CONVERSATION ---
        {conversation_history}
        
        --- CURRENT QUESTION ---
        {last_message['content']}
        
        Please provide a comprehensive, well-reasoned answer. Use the documentation when available, and apply logical inference for complex scenarios not explicitly covered.
        """
        
        client = genai.Client(api_key=api_key)
        
        with st.chat_message("assistant"):
            try:
                generate_content_config = types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(include_thoughts=True),
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    temperature=0.7,
                    max_output_tokens=2048
                )
                
                def stream_response():
                    stream = client.models.generate_content_stream(
                        model="gemini-2.0-flash-thinking-exp-1219",
                        contents=full_prompt,
                        config=generate_content_config,
                    )
                    for chunk in stream:
                        if chunk.text:
                            yield chunk.text

                response = st.write_stream(stream_response())
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                try:
                    fallback_config = types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                        temperature=0.7,
                        max_output_tokens=2048
                    )
                    response_fallback = client.models.generate_content(
                        model="gemini-2.0-flash", 
                        contents=full_prompt,
                        config=fallback_config
                    )
                    
                    response_text = response_fallback.text
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                    
                except Exception as e2:
                    error_msg = f"Error: {str(e2)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        st.session_state.generating = False
        st.rerun()