import streamlit as st
import requests

st.set_page_config(page_title="AI Assistant", layout="wide")

API_URL = "http://localhost:8000"

st.title("AI Assistant")

tab1, tab2, tab3 = st.tabs(["📝 Summarize", "✍️ Draft", "🔍 Research"])

with tab1:
    st.header("Summarize Text")
    text_to_summarize = st.text_area("Enter text to summarize:", height=200)
    
    if st.button("Summarize", key="sum_btn"):
        if text_to_summarize:
            with st.spinner("Summarizing..."):
                try:
                    response = requests.post(
                        f"{API_URL}/summarize",
                        json={"text": text_to_summarize}
                    )
                    if response.status_code == 200:
                        st.success("Summary:")
                        st.write(response.json()["result"])
                    else:
                        st.error(f"Error: {response.json()['detail']}")
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")
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
                    response = requests.post(
                        f"{API_URL}/draft",
                        json={"text": draft_context, "prompt": draft_prompt}
                    )
                    if response.status_code == 200:
                        st.success("Draft:")
                        st.write(response.json()["result"])
                    else:
                        st.error(f"Error: {response.json()['detail']}")
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")
        else:
            st.warning("Please enter a prompt")

with tab3:
    st.header("Research Topic")
    research_topic = st.text_input("Enter topic to research:")
    
    if st.button("Research", key="research_btn"):
        if research_topic:
            with st.spinner("Researching..."):
                try:
                    response = requests.post(
                        f"{API_URL}/research",
                        json={"text": research_topic}
                    )
                    if response.status_code == 200:
                        st.success("Research Results:")
                        st.write(response.json()["result"])
                    else:
                        st.error(f"Error: {response.json()['detail']}")
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")
        else:
            st.warning("Please enter a research topic")