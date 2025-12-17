import streamlit as st
import anthropic

st.set_page_config(page_title="AI Assistant", layout="wide")

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

st.title("AI Assistant")

tab1, tab2, tab3 = st.tabs(["📝 Summarize", "✍️ Draft", "🔍 Research"])

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