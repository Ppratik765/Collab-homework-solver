import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import nbformat as nbf
import pypdf
import docx
import json
import io
import time

# --- HELPER FUNCTIONS ---

def extract_text_from_file(uploaded_file):
    """
    Extracts text from PDF or DOCX based on file type.
    """
    text = ""
    try:
        if uploaded_file.type == "application/pdf":
            pdf_reader = pypdf.PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs:
                text += para.text + "\n"
                
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None
        
    return text

def generate_notebook_content(text_content, api_key, provider):
    """
    Sends text to the selected AI provider (Gemini or OpenAI)
    and requests a structured JSON response.
    """
    
    # Common System Prompt for both AIs
    system_prompt = """
    You are an automated homework solver. 
    
    **Instructions:**
    1. Analyze the text and identify if the questions are divided into parts or sections (e.g., "Part A", "Section 1").
    2. If no specific sections exist, group everything under a single section named "Questions".
    3. Extract the distinct questions for each section.
    4. Write working Python code to solve each question.
    5. Return the output strictly as a JSON list of Section objects.

    **JSON Schema:**
    [
        {
            "section_title": "Part A: Multiple Choice",
            "questions": [
                {
                    "question": "Text of Q1...",
                    "code": "print('Answer to Q1')"
                }
            ]
        }
    ]
    """

    try:
        if provider == "Google Gemini":
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            full_prompt = f"{system_prompt}\n\n**Input Text:**\n{text_content}"
            
            response = model.generate_content(
                full_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            return json.loads(response.text)

        elif provider == "OpenAI (ChatGPT)":
            client = OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini", # Using 4o-mini for speed and cost efficiency
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here is the homework text:\n{text_content}"}
                ],
                response_format={ "type": "json_object" }
            )
            return json.loads(response.choices[0].message.content)

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
        # Handle cases where AI might wrap the list in a root key (common with OpenAI)
        if isinstance(structured_data, dict):
            # Try to find the list inside values
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

# --- STREAMLIT UI ---

st.set_page_config(page_title="Colab Homework Solver", layout="centered")

st.title("📄 Auto-Colab Solver")
st.write("Upload a PDF or Word file, and I'll generate a solved Jupyter Notebook (.ipynb) for you.")

# --- SIDEBAR CONFIGURATION ---
st.sidebar.header("Configuration")

# 1. Provider Selection
provider = st.sidebar.radio(
    "Select AI Model:",
    ("Google Gemini", "OpenAI (ChatGPT)")
)

# 2. Dynamic Tooltip Instructions
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

# 3. API Key Input with Tooltip
api_key = st.sidebar.text_input(
    f"Enter {provider} API Key", 
    type="password",
    help=tooltip_text  # This creates the hoverable "i" / "?" icon
)

if not api_key:
    st.sidebar.warning(f"Please enter your {provider} API Key to proceed.")

# --- MAIN APP INPUTS ---
col1, col2 = st.columns(2)
with col1:
    name = st.text_input("Student Name", placeholder="John Doe")
with col2:
    roll_no = st.text_input("Roll Number", placeholder="12345")

uploaded_file = st.file_uploader("Upload Homework", type=["pdf", "docx"])

if st.button("Generate Notebook"):
    if not api_key:
        st.error(f"Please enter your {provider} API Key in the sidebar.")
    elif not uploaded_file:
        st.warning("Please upload a file.")
    elif not name or not roll_no:
        st.warning("Please fill in Name and Roll Number.")
    else:
        progress_text = "Starting operation..."
        my_bar = st.progress(0, text=progress_text)

        # Step 1: Parsing
        my_bar.progress(25, text="Reading file content...")
        raw_text = extract_text_from_file(uploaded_file)
        
        if not raw_text or len(raw_text) < 10:
            my_bar.empty()
            st.error("Could not extract text. The file might be empty or an image scan.")
        else:
            # Step 2: AI Generation
            my_bar.progress(50, text=f"Sending questions to {provider}...")
            
            # Pass provider info to the function
            structured_data = generate_notebook_content(raw_text, api_key, provider)
            
            if structured_data:
                # Step 3: Building Notebook
                my_bar.progress(90, text="Formatting .ipynb file...")
                notebook_obj = create_ipynb(name, roll_no, structured_data)
                
                output_stream = io.StringIO()
                nbf.write(notebook_obj, output_stream)
                notebook_data = output_stream.getvalue().encode('utf-8')

                # Step 4: Complete
                my_bar.progress(100, text="Complete!")
                time.sleep(0.5)
                my_bar.empty()

                st.success(f"Notebook generated successfully using {provider}!")
                
                st.download_button(
                    label="📥 Download .ipynb File",
                    data=notebook_data,
                    file_name=f"{roll_no}_{name}_Assignment.ipynb",
                    mime="application/x-ipynb+json"
                )
