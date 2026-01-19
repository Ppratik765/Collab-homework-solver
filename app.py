import streamlit as st
import streamlit.components.v1 as components
import json
import io
import time
import nbformat as nbf
# NOTE: Heavy imports (openai, genai, pypdf, etc.) are removed from here 
# and moved inside the functions below to make the app load instantly.

# --- 1. VISUAL BRANDING & ANIMATED BACKGROUND (CSS) ---
st.set_page_config(page_title="Automated Intelligence", layout="centered", page_icon="programmer.png")

st.markdown("""
<style>
    /* 1. Hide Footer */
    footer {visibility: hidden;}
    
    /* 2. HEADER TRANSPARENCY */
    header[data-testid="stHeader"] {
        background: transparent !important;
        z-index: 1000 !important;
    }

    /* 3. ENTRANCE ANIMATION */
    @keyframes floatUp {
        0% { opacity: 0; transform: translateY(30px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    .block-container, section[data-testid="stSidebar"] {
        animation: floatUp 0.8s cubic-bezier(0.2, 0.8, 0.2, 1);
    }

    /* 4. MAIN CONTENT STYLING */
    .block-container {
        padding-top: 6rem !important;
        z-index: 10;
        background: rgba(0, 0, 0, 0.6); 
        border-radius: 15px;
        padding-bottom: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(1px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-top: 2rem;
        margin-left: auto;
        margin-right: auto;
    }
    
    /* 5. SIDEBAR STYLING */
    section[data-testid="stSidebar"] {
        z-index: 99999 !important;
        background-color: rgba(15, 15, 20, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* 6. Background Color */
    .stApp {
        background: linear-gradient(to bottom, #0b1021 0%, #1b2735 100%);
    }
    
    /* 7. Lively Snowfall Animation */
    .stApp::before {
        content: ""; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background-image: 
            radial-gradient(4px 4px at 100px 50px, #fff, transparent), 
            radial-gradient(6px 6px at 200px 150px, #fff, transparent), 
            radial-gradient(3px 3px at 300px 250px, #fff, transparent);
        background-size: 550px 550px;
        animation: snowfall 10s linear infinite;
        pointer-events: none; opacity: 0.3; 
    }
    @keyframes snowfall {
        0% { background-position: 0 0; }
        100% { background-position: 0 550px; }
    }

    /* 8. Typography */
    h1, h2, h3 { color: #ffffff !important; text-shadow: 0 0 10px #00d2ff; }
    p, label, .stMarkdown { color: #e0e0e0 !important; }

    }

    /* Ensure Sidebar Arrow is visible */
    [data-testid="stSidebarCollapsedControl"] {
        display: block !important;
        visibility: visible !important;
        color: white !important;
    }
    
    [data-testid="stSidebarCollapsedControl"] svg {
        fill: white !important;
        stroke: white !important;
    }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---

def clean_ui():
    js_code = """
    <script>
    function cleanUI() {
        // 1. FORK/DEPLOY BUTTON (Text Search)
        const allElements = window.parent.document.querySelectorAll('button, a');
        allElements.forEach(el => {
            if (el.innerText && (el.innerText.toUpperCase() === 'FORK' || el.innerText.toUpperCase() === 'DEPLOY')) {
                el.style.display = 'none';
            }
        });


        // 3. 3-DOTS MENU (Hidden by removing Header Action Elements)
        const menu = window.parent.document.querySelector('[data-testid="stHeaderActionElements"]');
        if (menu) {
            menu.style.display = 'none';
        }
        
        // Backup selector for the menu (older Streamlit versions)
        const oldMenu = window.parent.document.querySelector('#MainMenu');
        if (oldMenu) {
            oldMenu.style.display = 'none';
        }
    }

    // Run every 500ms to ensure they stay hidden if Streamlit re-renders
    setInterval(cleanUI, 500);
    </script>
    """
    components.html(js_code, height=0)

# --- CALL THE FUNCTION AT THE TOP OF YOUR APP ---
clean_ui()

def extract_text_from_file(uploaded_file):
    """
    Extracts text from PDF or DOCX.
    Uses Lazy Loading for pypdf and docx.
    """
    # LAZY IMPORT: Load these only when this function runs
    import pypdf
    import docx
    
    text = ""
    try:
        if uploaded_file.type == "application/pdf":
            pdf_reader = pypdf.PdfReader(uploaded_file)
            if pdf_reader.is_encrypted:
                st.error("🔒 **Error:** This PDF is password protected. Please remove the password and upload again.")
                return None
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs:
                text += para.text + "\n"
                
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None
    # Validation check
    if not text.strip():
        st.error("⚠️ **Empty File:** We couldn't find any readable text in this file. It might be an image-only PDF (scanned). Try converting it to text first.")
        return None
        
    return text

def generate_notebook_content(text_content, api_key, provider, custom_instructions=""):
    """
    Sends text to AI.
    Uses Lazy Loading for genai and openai.
    """
    # LAZY IMPORT: Load these only when this function runs
    import google.generativeai as genai
    from openai import OpenAI

    # --- UPDATED SYSTEM PROMPT ---
    system_prompt = f"""
    You are an automated homework solver. 
    
    **Instructions:**
    1. Analyze the text and identify if the questions are divided into parts or sections.
    2. If no specific sections exist, group everything under a single section named "Questions".
    3. Extract the distinct questions for each section.
    4. **CRITICAL - FORMATTING:** You MUST preserve the original formatting of the question text.
       - If the question contains a **Table**, represent it using **Markdown Table syntax**.
       - If the question contains **Bullet Points** or **Numbered Lists**, keep them as Markdown lists.
       - If the question contains **Mathematical Equations**, keep them in LaTeX format (e.g., $x^2$).
    5. Write working Python code to solve each question.
    6. Return the output strictly as a JSON list of Section objects.
    
    **USER CUSTOM INSTRUCTIONS:**
    {custom_instructions}

    **JSON Schema:**
    [
        {{
            "section_title": "Part A: Multiple Choice",
            "questions": [
                {{
                    "question": "Calculate the values for the following table:\\n\\n| Mass | Velocity |\\n|---|---|\\n| 10kg | 20m/s |",
                    "code": "# Python code to solve..."
                }}
            ]
        }}
    ]
    """

    try:
        if provider == "Google Gemini":
            # 1. Validation: Fail fast if key is obviously wrong
            if not api_key or len(api_key.strip()) < 10:
                 st.error("🚨 **Invalid API Key:** The key looks too short. Please check it.")
                 return None
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            full_prompt = f"{system_prompt}\n\n**Input Text:**\n{text_content}"
            try:
                response = model.generate_content(
                    full_prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                return json.loads(response.text)
            except Exception as e:
                # Gemini specific error handling
                if "401" in str(e) or "API_KEY_INVALID" in str(e):
                    st.error("🚨 **Invalid API Key:** The Gemini API key you entered is incorrect. Please check your Google AI Studio dashboard.")
                    return None
                else:
                    raise e # Re-raise other errors to be caught by the outer except

        elif provider == "OpenAI (ChatGPT)":
            client = OpenAI(api_key=api_key)
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini", 
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Here is the homework text:\n{text_content}"}
                    ],
                    response_format={ "type": "json_object" }
                )
                return json.loads(response.choices[0].message.content)
            except AuthenticationError:
                st.error("🚨**Invalid API Key:** The OpenAI API key is incorrect. Please check your settings at platform.openai.com.")
                return None
            except RateLimitError:
                st.error("⏳**Rate Limit Hit:** You have sent too many requests too quickly. Please wait a moment or check your OpenAI quota.")
                return None
            except Exception as e:
                st.error(f"❌**OpenAI Error:** {str(e)}")
                return None
    except json.JSONDecodeError:
        st.error("**AI Error:** The AI generated a response, but it wasn't valid JSON. Please try again (sometimes just clicking Generate again fixes this).")
        return None
    except Exception as e:
        st.error(f"Error communicating with {provider}: {e}")
        return None

def create_ipynb(student_name, roll_no, structured_data):
    nb = nbf.v4.new_notebook()

    # Header
    header_md = f"# Homework Assignment\n\n**Name:** {student_name}\n\n**Roll No:** {roll_no}\n\n---"
    nb.cells.append(nbf.v4.new_markdown_cell(header_md))

    # Sections & Questions
    if structured_data:
        # Handle dict wrapping
        if isinstance(structured_data, dict):
            for key, value in structured_data.items():
                if isinstance(value, list):
                    structured_data = value
                    break

        if isinstance(structured_data, list):
            for section in structured_data:
                sec_title = section.get('section_title', 'Section')
                nb.cells.append(nbf.v4.new_markdown_cell(f"## {sec_title}"))

                for item in section.get('questions', []):
                    q_text = f"### Question\n\n{item.get('question', 'No question text found.')}"
                    nb.cells.append(nbf.v4.new_markdown_cell(q_text))

                    code_text = item.get('code', '# No code generated')
                    nb.cells.append(nbf.v4.new_code_cell(code_text))
    return nb

# --- MOCK DATA FOR DEMO MODE ---
MOCK_TEXT = "Question 1: Calculate the force of gravity on a 10kg object on Earth. Question 2: Create a list of the first 5 prime numbers."
MOCK_JSON = [
    {
        "section_title": "Python Colab demo",
        "questions": [
            {"question": """Create a line plot for the following data:
- X-axis: Numbers from 1 to 10
- Y-axis: Squares of the numbers (e.g., y=x2y = x^2y=x2)
Customize the plot by adding:
- A title
- Labels for the X and Y axes
- A grid.""",
                "code": """import matplotlib.pyplot as plt
import numpy as np
x = np.arange(1, 11)
y = x ** 2

plt.figure()
plt.plot(x, y)
plt.title("Squares of Numbers")
plt.xlabel("Number")
plt.ylabel("Square")
plt.grid(True)
plt.show()"""
            },
            {"question": "Write a program that takes a list of temperatures in Celsius and converts them to Fahrenheit using map().",
                "code": """Input=[0, 20, 37, 100]
Fahrenheit = lambda c: (c * 9/5) + 32
output = list(map(Fahrenheit, Input))
print(output)"""}
        ]
    }
]

# --- UI START ---
st.title("Automated Intelligence")
st.write("Upload a PDF or Word file, and I'll generate a solved Jupyter Notebook (.ipynb) for you.")

# --- SIDEBAR CONFIGURATION ---
st.sidebar.header("Configuration")

# 1. Provider Selection
provider = st.sidebar.radio(
    "Select AI Model:",
    ("Google Gemini", "OpenAI (ChatGPT)")
)

# Tooltips
if provider == "Google Gemini":
    tooltip_text = """
    **How to get a Google Gemini API Key:**
    1. Go to [Google AI Studio](https://aistudio.google.com/).
    2. Sign in with your Google account.
    3. Click on "Get API key" (top left).
    4. Click "Create API key in new project".
    5. Copy the key and paste it here.
    """
else:
    tooltip_text = """
    **How to get an OpenAI API Key:**
    1. Go to [platform.openai.com](https://platform.openai.com/api-keys).
    2. Sign in or create an account.
    3. Click "+ Create new secret key".
    4. Name your key and click "Create secret key".
    5. Copy the key (you won't see it again!) and paste it here.
    """

# 2. API Key Input
api_key = st.sidebar.text_input(
    f"Enter {provider} API Key", 
    type="password",
    help=tooltip_text
)
if not api_key:
    st.sidebar.warning(f"Please enter your {provider} API Key to proceed.")

# 🔒 SECURITY MESSAGE

# Main reassurance message
st.sidebar.success("🔒 **Security Note:** Your API Key is processed securely in memory and is **never** stored.")

# Technical details in an expandable dropdown
with st.sidebar.expander("Why is this secure?"):
    st.markdown("""
    * **Encrypted Transit:** Your key is sent via HTTPS, making it invisible to hackers.
    * **RAM-Only:** The key lives in temporary memory for this session only.
    * **No Databases:** We do not have a database. Nothing is saved to disk.
    * **Session Isolation:** Your inputs are sandboxed and cannot be seen by other users.
    """)

# 3. Advanced Options
with st.sidebar.expander("Advanced Options"):
    custom_instructions = st.text_area(
        "Additional AI Instructions:",
        placeholder="E.g., 'Use only standard Python libraries'..."
    )

# --- MAIN INPUTS ---
col1, col2 = st.columns(2)
with col1:
    name = st.text_input("Student Name", placeholder="John Doe")
with col2:
    roll_no = st.text_input("Roll Number", placeholder="12345")

uploaded_file = st.file_uploader("Upload Homework", type=["pdf", "docx"])

# --- ACTION BUTTONS ---
btn_col1, btn_col2 = st.columns([1, 1])

with btn_col1:
    generate_btn = st.button("Generate Notebook", use_container_width=True)
with btn_col2:
    demo_btn = st.button("Try Demo Mode", use_container_width=True)

# Initialize variables
structured_data = None
notebook_data = None
final_name = name if name else "Student"
final_roll = roll_no if roll_no else "0000"

# --- LOGIC FLOW ---

if demo_btn:
    with st.status("Running Demo Mode...", expanded=True) as status:
        st.write("📂 Loading mock homework file...")
        time.sleep(1) 
        st.write("🧠 Simulating AI thinking...")
        time.sleep(1)
        
        # Load Mock Data
        structured_data = MOCK_JSON
        
        st.write("📝 Formatting .ipynb file...")
        notebook_obj = create_ipynb("Demo User", "12345", structured_data)
        
        output_stream = io.StringIO()
        nbf.write(notebook_obj, output_stream)
        notebook_data = output_stream.getvalue().encode('utf-8')
        
        status.update(label="Demo Complete!", state="complete", expanded=False)
        
    st.success("✅ Demo Generated Successfully!")
    final_name = "Demo_User"
    final_roll = "12345"

elif generate_btn:
    if not api_key:
        st.error(f"Please enter your {provider} API Key in the sidebar.")
    elif not uploaded_file:
        st.warning("Please upload a file.")
    elif not name or not roll_no:
        st.warning("Please fill in Name and Roll Number.")
    else:
        with st.status("Processing your request...", expanded=True) as status:
            # Step 1: Parsing
            try:
                st.write("🔍 Reading file content...")
                raw_text = extract_text_from_file(uploaded_file)
                
                if not raw_text or len(raw_text) < 10:
                    status.update(label="Failed", state="error")
                    st.error("Could not extract text.")
                else:
                    # Step 2: AI Generation
                    st.write(f"🧠Sending questions to {provider}(this usually takes time)...")
                    structured_data = generate_notebook_content(raw_text, api_key, provider, custom_instructions)
                    
                    if structured_data:
                        # Step 3: Building Notebook
                        st.write("📝 Formatting .ipynb file...")
                        notebook_obj = create_ipynb(name, roll_no, structured_data)
                        
                        output_stream = io.StringIO()
                        nbf.write(notebook_obj, output_stream)
                        notebook_data = output_stream.getvalue().encode('utf-8')

                        status.update(label="Process Complete!", state="complete", expanded=False)
                        st.success("✅ Notebook generated successfully!")
                    else:
                        status.update(label="Generation Failed", state="error", expanded=True)

            except Exception as e:
                # Catch-all for any other crash to ensure spinner stops
                status.update(label="System Error", state="error", expanded=True)
                st.error(f"Critical Error: {str(e)}")

# --- POST-GENERATION UI ---

if structured_data and notebook_data:
    with st.expander("Preview (Check results before downloading)"):
        st.markdown("### Generated Questions & Solutions")
        
        data_to_show = structured_data
        if isinstance(structured_data, dict):
            for k, v in structured_data.items():
                if isinstance(v, list):
                    data_to_show = v
                    break
        
        if isinstance(data_to_show, list):
            for section in data_to_show:
                st.markdown(f"#### {section.get('section_title', 'Section')}")
                for q in section.get('questions', []):
                    st.markdown(f"**Q:** {q.get('question')}")
                    st.code(q.get('code'), language='python')
                    st.markdown("---")

    st.warning("⚠️ **Note:** This code is AI-generated, It is usually correct for college-level homeworks, but it's always a good practice to review the code before submitting.")

    col1, col2 = st.columns([1, 1])
    with col1:
        st.download_button(
            label="Download .ipynb File",
            data=notebook_data,
            file_name=f"{final_roll}{final_name} Assignment.ipynb",
            mime="application/x-ipynb+json",
            use_container_width=True
        )
