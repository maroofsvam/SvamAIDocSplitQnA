import streamlit as st
import io
from typing import Optional
import google.generativeai as genai
import os
import tempfile
from dotenv import load_dotenv 
 
# Get API key from environment variable
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
def setup_gemini() -> bool:
    """Setup Gemini API with the API key from environment"""
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Test the connection
        model = genai.GenerativeModel('gemini-2.5-flash')
        test_response = model.generate_content("Hello")
        return True
    except Exception as e:
        st.error(f"Error setting up API: {str(e)}")
        return False
 
def upload_file_to_gemini(uploaded_file) -> Optional[object]:
    """Upload file directly to Gemini using the File API"""
    try:
        # Create a temporary file to save the uploaded content
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
       
        # Upload file to Gemini
        gemini_file = genai.upload_file(tmp_file_path, display_name=uploaded_file.name)
       
        # Clean up temporary file
        os.unlink(tmp_file_path)
       
        return gemini_file
       
    except Exception as e:
        st.error(f"Error uploading file to Gemini: {str(e)}")
        return None
 
def answer_question_with_gemini(query: str, gemini_file) -> str:
    """Use Gemini to answer questions about the uploaded document"""
    if not gemini_file:
        return "No document uploaded yet."
   
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
       
        # Create the prompt with both the file and the question
        prompt = f"Please answer this question about the uploaded document: {query}"
       
        response = model.generate_content([prompt, gemini_file])
       
        return response.text
       
    except Exception as e:
        return f"Error generating response: {str(e)}"
 
def get_file_info(gemini_file) -> dict:
    """Get information about the uploaded file"""
    try:
        file_info = genai.get_file(gemini_file.name)
        return {
            'name': file_info.display_name or gemini_file.name,
            'size': f"Unknown size",  # Size info not easily accessible in this API
            'mime_type': file_info.mime_type if hasattr(file_info, 'mime_type') else "Unknown type",
            'state': file_info.state.name if hasattr(file_info, 'state') else "Active"
        }
    except Exception as e:
        return {
            'name': gemini_file.display_name if hasattr(gemini_file, 'display_name') else 'Uploaded file',
            'size': 'Unknown size',
            'mime_type': 'Unknown type',
            'state': 'Active'
        }
 
def simple_search_fallback(query: str) -> str:
    """Fallback message when Gemini is not available"""
    return "SVAM AI is currently unavailable. Please try again later or check your internet connection."
 
def main():
    st.set_page_config(
        page_title="Document Q&A with SVAM AI",
        page_icon="🚀",
        layout="wide"
    )
   
    st.title("🚀 Document Q&A with SVAM AI")
    st.markdown("Upload documents directly to SVAM AI and ask intelligent questions with native document processing!")
   
    # Initialize session state
    if 'gemini_file' not in st.session_state:
        st.session_state.gemini_file = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'gemini_configured' not in st.session_state:
        st.session_state.gemini_configured = False
    if 'file_info' not in st.session_state:
        st.session_state.file_info = None
   
    # Initialize Gemini on first run
    if not st.session_state.gemini_configured:
        with st.spinner("🔧 Initializing SVAM AI..."):
            if setup_gemini():
                st.session_state.gemini_configured = True
   
    # Sidebar for file upload and status
    with st.sidebar:
        # Show SVAM AI status
        if st.session_state.gemini_configured:
            st.success("🤖 SVAM AI Ready!")
        else:
            st.error("❌ SVAM AI Unavailable")
            st.info("Please check your API key and internet connection.")
       
        st.markdown("---")
       
        st.header("📁 Upload Document")
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['pdf', 'docx', 'txt', 'md', 'csv', 'xlsx', 'png', 'jpg', 'jpeg'],
            help="Upload documents that SVAM AI can process natively"
        )
       
        if uploaded_file is not None and st.session_state.gemini_configured:
            # Check if this is a new file
            file_key = f"{uploaded_file.name}_{uploaded_file.size}"
            if not st.session_state.gemini_file or getattr(st.session_state, 'current_file_key', None) != file_key:
                with st.spinner("📤 Uploading to SVAM AI..."):
                    gemini_file = upload_file_to_gemini(uploaded_file)
                    if gemini_file:
                        st.session_state.gemini_file = gemini_file
                        st.session_state.current_file_key = file_key
                        st.session_state.chat_history = []  # Clear chat history for new file
                       
                        # Get file info
                        st.session_state.file_info = get_file_info(gemini_file)
                       
                        st.success(f"✅ Successfully uploaded: {uploaded_file.name}")
       
        # Display file info
        if st.session_state.file_info:
            st.markdown("---")
            st.subheader("📊 File Information")
            info = st.session_state.file_info
            st.info(f"**Name:** {info['name']}\n**Type:** {info['mime_type']}\n**Status:** {info['state']}")
       
        # Supported formats info
        st.markdown("---")
        st.subheader("🎯 Supported Formats")
        st.markdown("""
        **Native SVAM AI Support:**
        - 📄 PDF (up to 3,600 pages)
        - 📝 DOCX, TXT, MD
        - 📊 CSV, XLSX
        - 🖼️ Images (PNG, JPG, etc.)
        - 🎥 Videos, 🎵 Audio files
        """)
   
    # Main chat interface
    if st.session_state.gemini_file and st.session_state.gemini_configured:
        st.header("💬 Ask Questions About Your Document")
       
        # Display chat history
        if st.session_state.chat_history:
            st.subheader("📜 Chat History")
            for i, (question, answer) in enumerate(st.session_state.chat_history):
                with st.expander(f"Q{i+1}: {question}", expanded=False):
                    st.markdown(f"**Answer:** {answer}")
       
        # Chat input
        st.subheader("❓ Ask a New Question")
        question = st.text_input(
            "Your question:",
            placeholder="e.g., What are the main points discussed in this document?",
            key="question_input"
        )
       
        col1, col2, col3 = st.columns([1, 1, 3])
       
        with col1:
            ask_button = st.button("Ask", type="primary")
       
        with col2:
            if st.button("Clear History"):
                st.session_state.chat_history = []
                st.rerun()
       
        if ask_button and question:
            with st.spinner("🤔 SVAM AI is analyzing..."):
                answer = answer_question_with_gemini(question, st.session_state.gemini_file)
               
                # Add to chat history
                st.session_state.chat_history.append((question, answer))
               
                # Show current answer
                st.success("**Answer:**")
                st.markdown(answer)
   
    elif not st.session_state.gemini_configured:
        st.error("🚫 SVAM AI is currently unavailable. Please check your API key configuration.")
        st.markdown("""
        **Troubleshooting:**
        - Ensure your API key is valid and active
        - Check if you have sufficient quota
        - Verify your internet connection
        - Try refreshing the page
        """)
       
    else:
        st.info("👆 Please upload a document using the sidebar to get started!")
       
        # Show features and example section
        st.header("🚀 Key Features:")
       
        col1, col2 = st.columns(2)
       
        with col1:
            st.markdown("""
            ### 🎯 **Native Document Processing**
            - Direct file upload to SVAM AI
            - No text extraction needed
            - Preserves document structure and formatting
            - Supports images, charts, and tables within documents
           
            ### 📄 **Advanced PDF Support**
            - Up to 3,600 pages supported
            - Vision-based understanding
            - Analyzes charts, diagrams, and tables
            - Maintains layout context
            """)
       
        with col2:
            st.markdown("""
            ### 🤖 **Intelligent Q&A**
            - Context-aware responses
            - Multi-modal understanding (text + visuals)
            - Comprehensive document analysis
            - Follow-up question support
           
            ### ⚡ **Simple & Fast**
            - No setup required
            - Instant processing
            - Clean, modern interface
            - Real-time responses
            """)
       
        st.markdown("---")
        st.header("💡 Example Questions You Can Ask:")
       
        examples = [
            "What is the main topic of this document?",
            "Can you provide a summary of the key findings?",
            "What are the conclusions and recommendations?",
            "Are there any charts or graphs? What do they show?",
            "Who are the main people or organizations mentioned?",
            "What are the important dates or deadlines?",
            "Can you extract any numerical data or statistics?",
            "What are the action items or next steps mentioned?"
        ]
       
        for i, example in enumerate(examples, 1):
            st.markdown(f"**{i}.** {example}")
   
    # Footer
    st.markdown("---")
    st.markdown("""
    **🎉 Powered by SVAM AI** - The best price-performance model with thinking capabilities!
   
    **💡 Pro Tips:**
    - Be specific in your questions for better answers
    - Ask about visual elements like charts and diagrams
    - Try follow-up questions to dive deeper into topics
    - Upload high-quality documents for best results
    """)
 
if __name__ == "__main__":

    main()
