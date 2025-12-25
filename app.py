import streamlit as st
import anthropic
from document_processor import DocumentProcessor, Document

st.set_page_config(page_title="Steve Wan's AI Legal Assistant", layout="wide")

# Initialize document processor lazily
@st.cache_resource
def get_document_processor():
    """Initialize document processor (cached to avoid reloading)"""
    return DocumentProcessor()

# Get document processor
doc_processor = get_document_processor()

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
    st.header("📝 Document Summary with Grounding")
    st.info("Generate grounded summaries from your uploaded documents. Every point is cited with source references.")
    
    # Show if documents are available
    stats = doc_processor.get_vector_stats()
    if stats['total_chunks'] == 0:
        st.warning("⚠️ No documents uploaded. Please upload documents first to generate summaries.")
    else:
        st.success(f"✅ {stats['total_documents']} documents indexed with {stats['total_chunks']} chunks")
    
    # Summary mode selection
    summary_mode = st.selectbox(
        "Select Summary Mode",
        ["Executive Summary", "Issue Spotting", "Chronology"],
        help="Choose the type of summary you want to generate"
    )
    
    # Topic/focus input
    summary_topic = st.text_area(
        "Topic or focus (optional):",
        placeholder="e.g., contract terms, merger analysis, case facts",
        help="Leave blank to summarize all documents, or specify a topic to focus on"
    )
    
    col1, col2 = st.columns([3, 1])
    with col1:
        num_sources = st.slider("Number of sources to retrieve", min_value=5, max_value=20, value=10)
    
    if st.button("Generate Summary", key="sum_btn", type="primary"):
        if stats['total_chunks'] == 0:
            st.error("Please upload documents before generating summaries.")
        else:
            with st.spinner("Retrieving relevant information..."):
                try:
                    # Determine search query
                    if summary_topic.strip():
                        search_query = summary_topic
                    else:
                        search_query = "main points key information important details"
                    
                    # Retrieve relevant chunks
                    results = doc_processor.search_documents(search_query, top_k=num_sources)
                    
                    if not results:
                        st.warning("No relevant information found in your documents.")
                    else:
                        # Build context with citations
                        context_parts = []
                        sources = []
                        
                        for idx, result in enumerate(results, 1):
                            page_info = f" (Page {result['page']})" if result['page'] else ""
                            context_parts.append(f"[{idx}] From '{result['doc_title']}'{page_info}:\n{result['chunk_text']}")
                            
                            sources.append({
                                'citation': idx,
                                'document': result['doc_title'],
                                'page': result['page'],
                                'snippet': result['chunk_text'][:200] + "...",
                                'full_text': result['chunk_text'],
                                'similarity': result['similarity']
                            })
                        
                        context = "\n\n".join(context_parts)
                        
                        # Create mode-specific prompt
                        if summary_mode == "Executive Summary":
                            prompt = f"""You are creating an executive summary based strictly on the provided sources.

GROUNDING RULES:
1. Provide EXACTLY 5 key points in bullet format
2. EVERY bullet point MUST include at least one citation [1], [2], etc.
3. Only include information explicitly stated in the sources
4. If a point cannot be supported by the sources, write "Not supported by provided documents" instead

Sources:
{context}

Topic focus: {summary_topic if summary_topic.strip() else 'General summary of all documents'}

Generate an executive summary with exactly 5 bullet points. Each bullet must cite sources [1][2] etc."""

                        elif summary_mode == "Issue Spotting":
                            prompt = f"""You are identifying issues, ambiguities, and missing facts based strictly on the provided sources.

GROUNDING RULES:
1. Identify issues, ambiguities, and missing information
2. EVERY issue MUST include at least one citation [1], [2], etc. to show where the issue appears
3. Only identify issues that are evident from the sources
4. If you cannot identify issues from the sources, write "Not supported by provided documents"
5. Format as bullet points under categories: Issues, Ambiguities, Missing Facts

Sources:
{context}

Topic focus: {summary_topic if summary_topic.strip() else 'General analysis of all documents'}

Identify and categorize issues with citations for each point."""

                        else:  # Chronology
                            prompt = f"""You are creating a chronological timeline based strictly on the provided sources.

GROUNDING RULES:
1. Create a timeline of events in chronological order
2. EVERY event MUST include at least one citation [1], [2], etc.
3. Only include events explicitly mentioned in the sources with dates or temporal references
4. If no chronological information exists, write "Not supported by provided documents"
5. Format as a table with columns: Date/Time | Event | Source Citation

Sources:
{context}

Topic focus: {summary_topic if summary_topic.strip() else 'General chronology from all documents'}

Create a chronological timeline table. Each row must cite sources."""

                        with st.spinner(f"Generating {summary_mode}..."):
                            message = client.messages.create(
                                model=model,
                                max_tokens=3000,
                                messages=[{
                                    "role": "user",
                                    "content": prompt
                                }]
                            )
                            
                            summary = message.content[0].text
                            
                            # Display summary
                            st.success(f"📋 {summary_mode}:")
                            st.markdown(summary)
                            
                            # Analyze which sources were cited
                            cited_sources = []
                            uncited_sources = []
                            
                            for source in sources:
                                citation_pattern = f"[{source['citation']}]"
                                if citation_pattern in summary:
                                    cited_sources.append(source)
                                else:
                                    uncited_sources.append(source)
                            
                            # Display sources
                            st.divider()
                            st.subheader("📚 Supporting Sources")
                            
                            # Display cited sources
                            if cited_sources:
                                st.markdown("**✅ Cited Sources:**")
                                for source in cited_sources:
                                    with st.expander(f"[{source['citation']}] {source['document']}" + (f" - Page {source['page']}" if source['page'] else "") + f" (Relevance: {source['similarity']:.2%})"):
                                        st.markdown("**Preview:**")
                                        st.write(source['snippet'])
                                        st.markdown("**Full Text:**")
                                        st.text_area("", source['full_text'], height=200, key=f"sum_source_{source['citation']}", label_visibility="collapsed")
                            
                            # Display uncited sources
                            if uncited_sources:
                                st.markdown("**ℹ️ Additional Retrieved Sources** (not cited):")
                                st.caption("These sources were retrieved but not used in the summary.")
                                
                                for source in uncited_sources:
                                    with st.expander(f"[{source['citation']}] {source['document']}" + (f" - Page {source['page']}" if source['page'] else "") + f" (Relevance: {source['similarity']:.2%})"):
                                        st.markdown("**Preview:**")
                                        st.write(source['snippet'])
                                        st.markdown("**Full Text:**")
                                        st.text_area("", source['full_text'], height=200, key=f"sum_uncited_{source['citation']}", label_visibility="collapsed")
                        
                except Exception as e:
                    st.error(f"Summary error: {str(e)}")

with tab2:
    st.header("✍️ Draft Documents with Grounding")
    st.info("Generate legal documents grounded in your uploaded documents. All facts are cited, assumptions are flagged, and open questions are identified.")
    
    # Show if documents are available
    stats = doc_processor.get_vector_stats()
    if stats['total_chunks'] == 0:
        st.warning("⚠️ No documents uploaded. Please upload documents first to generate drafts.")
    else:
        st.success(f"✅ {stats['total_documents']} documents indexed with {stats['total_chunks']} chunks")
    
    # Template selection
    template = st.selectbox(
        "Select Document Template",
        ["Client Update Email", "Internal Case Memo", "Demand Letter Skeleton"],
        help="Choose the type of document you want to draft"
    )
    
    # Context/instructions
    col1, col2 = st.columns([2, 1])
    with col1:
        draft_instructions = st.text_area(
            "Drafting Instructions:",
            placeholder="e.g., Focus on timeline of events, highlight key contractual obligations, emphasize damages",
            height=100,
            help="Provide specific instructions for what to include in the draft"
        )
    
    with col2:
        recipient = st.text_input("Recipient (if applicable):", placeholder="e.g., John Smith, Client")
        num_sources = st.slider("Number of sources to retrieve", min_value=5, max_value=20, value=12)
    
    if st.button("Generate Draft", key="draft_btn", type="primary"):
        if stats['total_chunks'] == 0:
            st.error("Please upload documents before generating drafts.")
        else:
            with st.spinner("Retrieving relevant information..."):
                try:
                    # Retrieve relevant chunks
                    search_query = draft_instructions if draft_instructions.strip() else "key facts important information"
                    results = doc_processor.search_documents(search_query, top_k=num_sources)
                    
                    if not results:
                        st.warning("No relevant information found in your documents.")
                    else:
                        # Build context with citations
                        context_parts = []
                        sources = []
                        
                        for idx, result in enumerate(results, 1):
                            page_info = f" (Page {result['page']})" if result['page'] else ""
                            context_parts.append(f"[{idx}] From '{result['doc_title']}'{page_info}:\n{result['chunk_text']}")
                            
                            sources.append({
                                'citation': idx,
                                'document': result['doc_title'],
                                'page': result['page'],
                                'snippet': result['chunk_text'][:200] + "...",
                                'full_text': result['chunk_text'],
                                'similarity': result['similarity']
                            })
                        
                        context = "\n\n".join(context_parts)
                        
                        # Template-specific prompts
                        if template == "Client Update Email":
                            template_guidance = f"""Draft a professional client update email to {recipient if recipient else '[Client Name]'}.

FORMAT:
Subject: [Appropriate subject line]

Dear {recipient if recipient else '[Client Name]'},

[Opening paragraph with context]

[Body paragraphs with updates - cite all facts with [1][2] etc.]

[Closing with next steps]

Best regards,
[Your name]"""

                        elif template == "Internal Case Memo":
                            template_guidance = """Draft an internal case memorandum.

FORMAT:
TO: [Team/Supervisor]
FROM: [Your name]
RE: [Case name/matter]
DATE: [Date]

SUMMARY:
[Brief overview with key facts - cite sources [1][2]]

FACTS:
[Detailed factual background - every fact must cite sources]

ANALYSIS:
[Legal analysis based on facts - cite supporting sources]

RECOMMENDATION:
[Recommended course of action]"""

                        else:  # Demand Letter Skeleton
                            template_guidance = f"""Draft a demand letter skeleton to {recipient if recipient else '[Recipient]'}.

FORMAT:
[Date]

{recipient if recipient else '[Recipient Name]'}
[Address]

Re: [Matter description]

Dear {recipient if recipient else '[Recipient]'}:

[Opening - establish relationship/context]

[Statement of facts - cite all facts with [1][2]]

[Statement of claims/demands - cite supporting sources]

[Demand for relief/action]

[Consequences if demand not met]

Sincerely,
[Your name]"""

                        # Create comprehensive prompt
                        prompt = f"""You are drafting a legal document based strictly on provided sources.

CRITICAL GROUNDING RULES:
1. Every factual statement MUST cite sources using [1], [2], etc.
2. If you make an assumption or inference, explicitly label it as "ASSUMPTION: [statement]"
3. Do NOT invent facts - only use information from the sources
4. Identify gaps in information as open questions

TEMPLATE GUIDANCE:
{template_guidance}

DRAFTING INSTRUCTIONS:
{draft_instructions if draft_instructions.strip() else 'Create a comprehensive document based on available information'}

SOURCES:
{context}

Generate the document in four sections:

**SECTION 1: DRAFT**
[The actual document following the template format. Cite all facts with [1][2] etc. Label assumptions clearly.]

**SECTION 2: FACTS USED (WITH CITATIONS)**
List all factual statements used in the draft with their citations:
- [Fact 1] [1][2]
- [Fact 2] [3]
etc.

**SECTION 3: OPEN QUESTIONS / MISSING INFORMATION**
Identify information gaps that would strengthen the document:
- [Question/gap 1]
- [Question/gap 2]
etc.

**SECTION 4: RISKS / ASSUMPTIONS**
List any assumptions made and potential risks:
- ASSUMPTION: [Any assumptions made]
- RISK: [Potential weaknesses or risks]
etc.

Generate all four sections."""

                        with st.spinner(f"Generating {template}..."):
                            message = client.messages.create(
                                model=model,
                                max_tokens=4096,
                                messages=[{
                                    "role": "user",
                                    "content": prompt
                                }]
                            )
                            
                            output = message.content[0].text
                            
                            # Display the output
                            st.success(f"📄 {template} Generated:")
                            st.markdown(output)
                            
                            # Analyze which sources were cited
                            cited_sources = []
                            uncited_sources = []
                            
                            for source in sources:
                                citation_pattern = f"[{source['citation']}]"
                                if citation_pattern in output:
                                    cited_sources.append(source)
                                else:
                                    uncited_sources.append(source)
                            
                            # Display sources
                            st.divider()
                            st.subheader("📚 Source Documents")
                            
                            # Display cited sources
                            if cited_sources:
                                st.markdown("**✅ Cited Sources:**")
                                for source in cited_sources:
                                    with st.expander(f"[{source['citation']}] {source['document']}" + (f" - Page {source['page']}" if source['page'] else "") + f" (Relevance: {source['similarity']:.2%})"):
                                        st.markdown("**Preview:**")
                                        st.write(source['snippet'])
                                        st.markdown("**Full Text:**")
                                        st.text_area("", source['full_text'], height=200, key=f"draft_source_{source['citation']}", label_visibility="collapsed")
                            
                            # Display uncited sources
                            if uncited_sources:
                                st.markdown("**ℹ️ Additional Retrieved Sources** (not cited):")
                                st.caption("These sources were retrieved but not used in the draft.")
                                
                                for source in uncited_sources:
                                    with st.expander(f"[{source['citation']}] {source['document']}" + (f" - Page {source['page']}" if source['page'] else "") + f" (Relevance: {source['similarity']:.2%})"):
                                        st.markdown("**Preview:**")
                                        st.write(source['snippet'])
                                        st.markdown("**Full Text:**")
                                        st.text_area("", source['full_text'], height=200, key=f"draft_uncited_{source['citation']}", label_visibility="collapsed")
                        
                except Exception as e:
                    st.error(f"Drafting error: {str(e)}")

with tab3:
    st.header("🔍 Research with RAG")
    st.info("Research using Retrieval-Augmented Generation. Answers are strictly grounded in your uploaded documents with citations.")
    
    # Show if documents are available
    stats = doc_processor.get_vector_stats()
    if stats['total_chunks'] == 0:
        st.warning("⚠️ No documents uploaded. Please upload documents first to use RAG research.")
    else:
        st.success(f"✅ {stats['total_documents']} documents indexed with {stats['total_chunks']} chunks")
    
    research_topic = st.text_input("Enter your research question:", placeholder="e.g., What are the key obligations in the contract?")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        num_chunks = st.slider("Number of sources to retrieve", min_value=3, max_value=15, value=8)
    
    if st.button("Research", key="research_btn", type="primary"):
        if research_topic:
            if stats['total_chunks'] == 0:
                st.error("Please upload documents before using RAG research.")
            else:
                with st.spinner("Retrieving relevant information..."):
                    try:
                        # Retrieve relevant chunks
                        results = doc_processor.search_documents(research_topic, top_k=num_chunks)
                        
                        if not results:
                            st.warning("No relevant information found in your documents.")
                        else:
                            # Build context with citations
                            context_parts = []
                            sources = []
                            
                            for idx, result in enumerate(results, 1):
                                page_info = f" (Page {result['page']})" if result['page'] else ""
                                context_parts.append(f"[{idx}] From '{result['doc_title']}'{page_info}:\n{result['chunk_text']}")
                                
                                sources.append({
                                    'citation': idx,
                                    'document': result['doc_title'],
                                    'page': result['page'],
                                    'snippet': result['chunk_text'][:200] + "...",
                                    'full_text': result['chunk_text'],
                                    'similarity': result['similarity']
                                })
                            
                            context = "\n\n".join(context_parts)
                            
                            # Create strict grounding prompt
                            prompt = f"""You are a research assistant that provides answers strictly based on the provided sources. You must follow these rules:

1. ONLY use information from the provided sources below
2. Every statement must be cited with [1], [2], etc. matching the source numbers
3. If the sources don't contain information to answer the question, say "The provided documents do not contain information about [topic]"
4. Do not add any information not present in the sources
5. Include multiple citations [1][2] when multiple sources support a point

Sources:
{context}

Question: {research_topic}

Provide a comprehensive answer with citations after every claim."""

                            with st.spinner("Generating research answer..."):
                                message = client.messages.create(
                                    model=model,
                                    max_tokens=3000,
                                    messages=[{
                                        "role": "user",
                                        "content": prompt
                                    }]
                                )
                                
                                answer = message.content[0].text
                                
                                # Display answer
                                st.success("📝 Research Answer:")
                                st.markdown(answer)
                                
                                # Analyze which sources were cited
                                cited_sources = []
                                uncited_sources = []
                                
                                for source in sources:
                                    citation_pattern = f"[{source['citation']}]"
                                    if citation_pattern in answer:
                                        cited_sources.append(source)
                                    else:
                                        uncited_sources.append(source)
                                
                                # Display sources
                                st.divider()
                                st.subheader("📚 Sources")
                                
                                # Display cited sources first
                                if cited_sources:
                                    st.markdown("**✅ Cited Sources** (used in answer above):")
                                    for source in cited_sources:
                                        with st.expander(f"[{source['citation']}] {source['document']}" + (f" - Page {source['page']}" if source['page'] else "") + f" (Relevance: {source['similarity']:.2%})"):
                                            st.markdown("**Preview:**")
                                            st.write(source['snippet'])
                                            st.markdown("**Full Text:**")
                                            st.text_area("", source['full_text'], height=200, key=f"source_{source['citation']}", label_visibility="collapsed")
                                
                                # Display uncited sources with explanation
                                if uncited_sources:
                                    st.markdown("**ℹ️ Additional Retrieved Sources** (not directly cited):")
                                    st.caption("These sources were retrieved but not cited in the answer. They may contain redundant information already covered by cited sources, or less relevant details.")
                                    
                                    for source in uncited_sources:
                                        with st.expander(f"[{source['citation']}] {source['document']}" + (f" - Page {source['page']}" if source['page'] else "") + f" (Relevance: {source['similarity']:.2%})"):
                                            st.markdown("**Preview:**")
                                            st.write(source['snippet'])
                                            st.markdown("**Full Text:**")
                                            st.text_area("", source['full_text'], height=200, key=f"source_uncited_{source['citation']}", label_visibility="collapsed")
                                
                    except Exception as e:
                        st.error(f"Research error: {str(e)}")
        else:
            st.warning("Please enter a research question")

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