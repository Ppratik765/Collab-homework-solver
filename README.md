# Automated Intelligence

Automated Intelligence is a specialised Streamlit application designed to streamline the process of solving homework assignments and technical assessments. By leveraging state-of-the-art Large Language Models (Google Gemini and OpenAI GPT), this tool ingests homework files (PDF or DOCX), analyses the content, generates code-based solutions, and compiles everything into a professionally formatted Jupyter Notebook (.ipynb) ready for Google Colab or local execution.

## Table of Contents

1.  [Overview](#overview)
2.  [Key Features](#key-features)
3.  [Technical Architecture](#technical-architecture)
4.  [Installation & Local Setup](#installation--local-setup)
5.  [Configuration](#configuration)
6.  [Usage Guide](#usage-guide)
7.  [Deployment](#deployment)
8.  [Project Structure](#project-structure)
9.  [Author](#author)

## Overview

This application bridges the gap between raw assignment files and executable code solutions. It parses text from uploaded documents, constructs a structured prompt for the AI to ensure correct formatting (preserving Markdown tables, LaTeX equations, and lists), and creates a download-ready Jupyter Notebook. It features a highly customised, dark-themed user interface with glassmorphism effects and optimised performance via lazy loading.

## Key Features

* **Multi-Format Input:** detailed support for parsing text from PDF documents and Word (DOCX) files.
* **Dual AI Engine Support:**
    * **Google Gemini:** Uses the `gemini-2.5-flash` model for high-speed, cost-effective generation.
    * **OpenAI:** Uses `gpt-4o-mini` for robust reasoning and code generation.
* **Intelligent Formatting Preservation:** The AI system prompt is engineered to detect and preserve Markdown tables, bullet points, and LaTeX mathematical notations in the final notebook.
* **Automated Notebook Generation:** Dynamically builds `.ipynb` files using the `nbformat` library, organising content into Markdown cells (for questions) and Code cells (for solutions).
* **Optimised Performance:** Implements lazy loading for heavy libraries (`pypdf`, `docx`, `google.generativeai`, `openai`) to ensure instant application startup and a snappy user interface.
* **Custom User Interface:**
    * Immersive dark mode with a cinematic, animated background.
    * Transparent header and sidebar elements.
    * Custom CSS styling for input fields, removing default browser outlines and enforcing a clean, monochrome aesthetic.
* **Demo Mode:** Includes a built-in simulation mode to demonstrate functionality without requiring API keys.

## Technical Architecture

### 1. The Frontend (Streamlit & CSS)
The application uses Streamlit for the interface but overrides the default styling using injected CSS. Key design elements include:
* **Z-Index Layering:** Ensures the sidebar and main content float correctly above the animated background.
* **CSS Animations:** Implements entrance animations for the main container and sidebar.
* **Input Styling:** Custom styling for text inputs to ensure visibility against dark backgrounds, specifically targeting the Streamlit widget DOM structure.

### 2. The Logic Layer
* **File Parsing:** Uses `pypdf` for reading PDFs page-by-page and `python-docx` for iterating through Word document paragraphs.
* **Prompt Engineering:** The application sends a strict system prompt to the LLM, enforcing a JSON schema return format. This ensures that the AI separates the "Question" text from the "Solution" code reliably.
* **Lazy Imports:** Heavy dependencies are imported strictly inside the execution functions (`generate_notebook_content`, `extract_text_from_file`) rather than at the top level.

## Installation & Local Setup

Prerequisites: Python 3.8 or higher.

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/Ppratik765/Collab-homework-solver.git](https://github.com/Ppratik765/Collab-homework-solver.git)
    ```

2.  **Create a Virtual Environment (Optional but Recommended)**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    Create a `requirements.txt` file with the contents listed below, then run the install command.
    ```bash
    pip install -r requirements.txt
    ```

    **requirements.txt content:**
    ```text
    streamlit
    google-generativeai
    openai
    nbformat
    pypdf
    python-docx
    watchdog
    ```

4.  **Run the Application**
    ```bash
    streamlit run app.py
    ```

## Configuration

To use the generation features, you must provide valid API keys. The application does not store these keys; they are used only for the current session.

* **Google Gemini API Key:**
    1.  Visit Google AI Studio.
    2.  Create a new project and generate an API key.
* **OpenAI API Key:**
    1.  Visit the OpenAI Platform.
    2.  Generate a new secret key.

## Usage Guide

1.  **Launch the App:** Open the local URL provided by Streamlit (usually http://localhost:8501).
2.  **Configure API:** Open the sidebar (left arrow), select your preferred AI provider, and paste your API key.
3.  **Enter Details:** Input the "Student Name" and "Roll Number". These are added as metadata headers in the generated notebook.
4.  **Upload File:** Drag and drop your PDF or DOCX homework file into the uploader.
5.  **Generate:** Click the "Generate Notebook" button.
6.  **Review & Download:**
    * Expand the "Live Preview" section to verify the questions and code solutions.
    * Click "Download .ipynb File" to save the notebook.
    * Open the file in Jupyter Lab, VS Code, or Google Colab.
  
## Author
Created and Maintained by Ppratik765.
