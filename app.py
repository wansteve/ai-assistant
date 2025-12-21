import streamlit as st
import anthropic
from document_processor import DocumentProcessor, Document

st.set_page_config(page_title="Steve Wan's AI Legal Assistant", layout="wide")

# Initialize document processor
doc_processor = DocumentProcessor()

# Get API key from Streamlit secrets (for cloud deployment)
# or from local config for local testing
try:
    api_key = st.secrets["api_key"]
    model = st.secrets.get("model", "claude-sonnet-4-20250514")
except:
    # Fallback to config.yaml for local development
    import yaml
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
            api_key = config["api_key"]
            model = config.get("model", "claude-sonnet-4-20250514")
    except:
        st.error("Please configure your API key in Streamlit secrets or config.yaml")
        st.stop()

client = anthropic.Anthropic(api_key=api_key)

st.title("⚖️ Steve Wan's AI Legal Assistant")

# Sidebar for document upload and management
with st.sidebar:
    st.header("📄 Document Management")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Document",
        type=['pdf', 'docx', 'txt'],
        help="Upload PDF, DOCX, or TXT files for processing"
    )
    
    if uploaded_file is not None:
        if st.button("Process Document"):
            with st.spinner("Processing document..."):
                try:
                    doc = doc_processor.process_file(uploaded_file)
                    st.success(f"✅ Document processed: {doc.title}")
                    st.json({
                        "Document ID": doc.doc_id,
                        "Title": doc.title,
                        "Type": doc.file_type,
                        "Pages": doc.page_count if doc.page_count else "N/A",
                        "Text Length": f"{len(doc.text)} characters"
                    })
                except Exception as e:
                    st.error(f"Error processing document: {str(e)}")
    
    # List uploaded documents
    st.divider()
    st.subheader("Uploaded Documents")
    documents = doc_processor.list_documents()
    
    if documents:
        for doc in documents:
            with st.expander(f"📄 {doc.title}"):
                st.write(f"**Type:** {doc.file_type}")
                st.write(f"**ID:** {doc.doc_id}")
                if doc.page_count:
                    st.write(f"**Pages:** {doc.page_count}")
                st.write(f"**Uploaded:** {doc.upload_date[:10]}")
                st.write(f"**Characters:** {len(doc.text):,}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"📊 Use", key=f"use_{doc.doc_id}"):
                        st.session_state['selected_doc'] = doc
                        st.rerun()
                
                with col2:
                    if st.button(f"🗑️ Delete", key=f"del_{doc.doc_id}", type="secondary"):
                        if doc_processor.delete_document(doc.doc_id):
                            # Clear selection if this was the selected doc
                            if st.session_state.get('selected_doc') and st.session_state['selected_doc'].doc_id == doc.doc_id:
                                st.session_state['selected_doc'] = None
                            st.success(f"Deleted: {doc.title}")
                            st.rerun()
                        else:
                            st.error("Failed to delete document")
    else:
        st.info("No documents uploaded yet")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Summarize", "✍️ Draft", "🔍 Research", "📄 Document Analysis", "🔎 Semantic Search"])

with tab1:
    st.header("Summarize Text")
    text_to_summarize = st.text_area("Enter text to summarize:", height=200)
    
    if st.button("Summarize", key="sum_btn"):
        if text_to_summarize:
            with st.spinner("Summarizing..."):
                try:
                    message = client.messages.create(
                        model=model,
                        max_tokens=1024,
                        messages=[{
                            "role": "user",
                            "content": f"Summarize the following text concisely:\n\n{text_to_summarize}"
                        }]
                    )
                    st.success("Summary:")
                    st.write(message.content[0].text)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter text to summarize")

with tab2:
    st.header("Draft Content")
    draft_prompt = st.text_input("What would you like to draft?")
    draft_context = st.text_area("Additional context (optional):", height=150)
    
    if st.button("Generate Draft", key="draft_btn"):
        if draft_prompt:
            with st.spinner("Generating draft..."):
                try:
                    message = client.messages.create(
                        model=model,
                        max_tokens=2048,
                        messages=[{
                            "role": "user",
                            "content": f"Write a draft based on this prompt: {draft_prompt}\n\nContext: {draft_context}"
                        }]
                    )
                    st.success("Draft:")
                    st.write(message.content[0].text)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter a prompt")

with tab3:
    st.header("Research Topic")
    research_topic = st.text_input("Enter topic to research:")
    
    if st.button("Research", key="research_btn"):
        if research_topic:
            with st.spinner("Researching..."):
                try:
                    message = client.messages.create(
                        model=model,
                        max_tokens=2048,
                        messages=[{
                            "role": "user",
                            "content": f"Research and provide detailed information about: {research_topic}"
                        }]
                    )
                    st.success("Research Results:")
                    st.write(message.content[0].text)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter a research topic")

with tab4:
    st.header("Document Analysis")
    
    # Check if a document is selected
    selected_doc = st.session_state.get('selected_doc', None)
    
    if selected_doc:
        st.info(f"📄 Analyzing: **{selected_doc.title}** ({selected_doc.file_type})")
        
        analysis_type = st.selectbox(
            "Select Analysis Type",
            ["Summarize Document", "Extract Key Points", "Legal Review", "Custom Query"]
        )
        
        custom_query = ""
        if analysis_type == "Custom Query":
            custom_query = st.text_area("Enter your question about the document:")
        
        if st.button("Analyze Document", key="analyze_btn"):
            with st.spinner("Analyzing document..."):
                try:
                    # Prepare prompt based on analysis type
                    if analysis_type == "Summarize Document":
                        prompt = f"Provide a comprehensive summary of this legal document:\n\n{selected_doc.text}"
                    elif analysis_type == "Extract Key Points":
                        prompt = f"Extract and list the key points, clauses, and important terms from this document:\n\n{selected_doc.text}"
                    elif analysis_type == "Legal Review":
                        prompt = f"Perform a legal review of this document. Identify potential issues, risks, and areas that may need attention:\n\n{selected_doc.text}"
                    else:
                        prompt = f"Document: {selected_doc.text}\n\nQuestion: {custom_query}"
                    
                    message = client.messages.create(
                        model=model,
                        max_tokens=4096,
                        messages=[{
                            "role": "user",
                            "content": prompt
                        }]
                    )
                    st.success("Analysis Complete:")
                    st.write(message.content[0].text)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        # Show document preview
        with st.expander("📄 View Document Text"):
            st.text_area("Document Content", selected_doc.text, height=400)
    else:
        st.warning("⬅️ Please upload and select a document from the sidebar to analyze.")

with tab5:
    st.header("🔎 Semantic Search")
    st.info("Search across all uploaded documents using natural language queries. The system will find the most relevant passages.")
    
    # Show vector store stats
    stats = doc_processor.get_vector_stats()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Documents Indexed", stats['total_documents'])
    with col2:
        st.metric("Text Chunks", stats['total_chunks'])
    with col3:
        st.metric("Embedding Dimension", stats['embedding_dim'])
    
    st.divider()
    
    # Search interface
    search_query = st.text_input("Enter your search query:", placeholder="e.g., What are the payment terms?")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        top_k = st.slider("Number of results", min_value=1, max_value=10, value=5)
    
    if st.button("Search", key="search_btn", type="primary"):
        if search_query:
            if stats['total_chunks'] == 0:
                st.warning("No documents have been uploaded yet. Please upload documents first.")
            else:
                with st.spinner("Searching..."):
                    try:
                        results = doc_processor.search_documents(search_query, top_k=top_k)
                        
                        if results:
                            st.success(f"Found {len(results)} relevant results:")
                            
                            for i, result in enumerate(results, 1):
                                with st.expander(f"Result {i}: {result['doc_title']} (Score: {result['similarity']:.3f})"):
                                    st.markdown(f"**Document:** {result['doc_title']}")
                                    if result['page']:
                                        st.markdown(f"**Page:** {result['page']}")
                                    st.markdown(f"**Similarity Score:** {result['similarity']:.3f}")
                                    st.divider()
                                    st.markdown("**Content:**")
                                    st.write(result['chunk_text'])
                                    
                                    # Option to use this result with Claude
                                    if st.button(f"Analyze with AI", key=f"analyze_result_{i}"):
                                        with st.spinner("Analyzing..."):
                                            message = client.messages.create(
                                                model=model,
                                                max_tokens=2048,
                                                messages=[{
                                                    "role": "user",
                                                    "content": f"Based on this document excerpt from '{result['doc_title']}':\n\n{result['chunk_text']}\n\nAnswer this question: {search_query}"
                                                }]
                                            )
                                            st.success("AI Analysis:")
                                            st.write(message.content[0].text)
                        else:
                            st.warning("No relevant results found. Try a different query.")
                    except Exception as e:
                        st.error(f"Search error: {str(e)}")
        else:
            st.warning("Please enter a search query")