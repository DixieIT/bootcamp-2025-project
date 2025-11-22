import os
import streamlit as st
import requests
from typing import Optional

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")

# Page config
st.set_page_config(
    page_title="bootcamp-2025",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar navigation
st.sidebar.title("bootcamp-2025 Dashboard")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["📝 Create Prompts", "🔄 Manage Active", "🤖 Run Predictions", "📊 View History", "⚙️ Config"],
    label_visibility="collapsed"
)

# User ID input (global)
st.sidebar.markdown("---")
user_id = st.sidebar.text_input("User ID", value="demo_user", help="Your user identifier")

st.sidebar.markdown("---")
st.sidebar.caption("FastAPI Backend: " + API_BASE_URL)

# Helper functions
def api_get(endpoint: str, params: Optional[dict] = None, headers: Optional[dict] = None) -> Optional[dict]:
    """Make GET request to API"""
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return None

def api_post(endpoint: str, json_data: dict, headers: Optional[dict] = None, params: Optional[dict] = None) -> Optional[dict]:
    """Make POST request to API"""
    try:
        response = requests.post(f"{API_BASE_URL}{endpoint}", json=json_data, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return None

def api_patch(endpoint: str, json_data: dict, headers: Optional[dict] = None) -> Optional[dict]:
    """Make PATCH request to API"""
    try:
        response = requests.patch(f"{API_BASE_URL}{endpoint}", json=json_data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return None

def api_delete(endpoint: str, headers: Optional[dict] = None) -> Optional[dict]:
    """Make DELETE request to API"""
    try:
        response = requests.delete(f"{API_BASE_URL}{endpoint}", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return None

# ==================== PAGES ====================

if page == "📝 Create Prompts":
    st.title("📝 Create New Prompt")
    st.markdown("Create and manage prompt templates for document processing.")

    col1, col2 = st.columns([2, 1])

    with col1:
        purpose = st.text_input("Purpose", placeholder="e.g., summarize, extract_entities, translate", help="What is this prompt for?")
        name = st.text_input("Prompt Name", placeholder="e.g., Basic Summarizer", help="A descriptive name")

        st.markdown("**Template**")
        st.caption("Use `{document}` for legacy or `{{ document }}` for Jinja2 templates")
        template = st.text_area(
            "Template",
            placeholder="Example:\nPlease summarize the following document:\n\n{document}",
            height=200,
            label_visibility="collapsed"
        )

        if st.button("Create Prompt", type="primary"):
            if not purpose or not name or not template:
                st.error("All fields are required!")
            else:
                data = {
                    "purpose": purpose,
                    "name": name,
                    "template": template
                }
                result = api_post("/v1/prompts/", data, headers={"X-User-Id": user_id})
                if result:
                    st.success(f"✅ Prompt created! ID: {result.get('id')}")
                    st.json(result)

    with col2:
        st.markdown("### 💡 Template Examples")
        st.code("""# Legacy syntax
Summarize: {document}

# Jinja2 syntax
Summarize: {{ document }}

# With filters
{{ document | upper }}

# Advanced
{% if document|length > 1000 %}
Long doc: {{ document[:500] }}...
{% else %}
{{ document }}
{% endif %}""", language="jinja2")

    # Show existing prompts
    st.markdown("---")
    st.subheader("Existing Prompts")

    prompts_data = api_get("/v1/prompts/", params={}, headers={"X-User-Id": user_id})
    if prompts_data and isinstance(prompts_data, list):
        if prompts_data:
            for prompt in prompts_data:
                with st.expander(f"{prompt.get('name')} ({prompt.get('purpose')})"):
                    st.write(f"**ID:** `{prompt.get('id')}`")
                    st.write(f"**Active:** {'✅ Yes' if prompt.get('active') else '❌ No'}")
                    st.write(f"**Version:** {prompt.get('version')}")
                    st.code(prompt.get('template'), language="text")
                    if st.button("🗑️ Delete", key=f"delete_{prompt.get('id')}"):
                        result = api_delete(f"/v1/prompts/{prompt.get('id')}", headers={"X-User-Id": user_id})
                        if result:
                            st.success("Deleted!")
                            st.rerun()
        else:
            st.info("No prompts created yet.")

elif page == "🔄 Manage Active":
    st.title("🔄 Manage Active Prompts")
    st.markdown("Activate prompts for different purposes.")

    # Get all prompts
    prompts_data = api_get("/v1/prompts/", headers={"X-User-Id": user_id})

    if prompts_data and isinstance(prompts_data, list):
        if not prompts_data:
            st.warning("No prompts available. Create some prompts first!")
        else:
            # Group by purpose
            purposes = {}
            for prompt in prompts_data:
                purpose = prompt.get('purpose')
                if purpose not in purposes:
                    purposes[purpose] = []
                purposes[purpose].append(prompt)

            st.subheader(f"Active Prompts for: `{user_id}`")

            for purpose, prompt_list in purposes.items():
                st.markdown(f"### Purpose: `{purpose}`")

                # Find active one
                active_prompt = next((p for p in prompt_list if p.get('active')), None)

                if active_prompt:
                    st.success(f"✅ Active: **{active_prompt.get('name')}** (v{active_prompt.get('version')})")
                else:
                    st.info("No active prompt for this purpose")

                # Show all prompts for this purpose
                for prompt in prompt_list:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**{prompt.get('name')}**")
                    with col2:
                        st.write(f"v{prompt.get('version')}")
                    with col3:
                        if not prompt.get('active'):
                            if st.button(f"Activate", key=f"activate_{prompt.get('id')}"):
                                result = api_post(
                                    f"/v1/prompts/{prompt.get('id')}/activate",
                                    {},
                                    headers={"X-User-Id": user_id},
                                    params={"purpose": purpose}
                                )
                                if result:
                                    st.success("✅ Activated!")
                                    st.rerun()
                        else:
                            st.write("✅ Active")

                st.markdown("---")

elif page == "🤖 Run Predictions":
    st.title("🤖 Run Predictions")
    st.markdown("Process documents using active prompts.")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Get available prompts for user
        prompts_data = api_get("/v1/prompts/", headers={"X-User-Id": user_id})
        prompt_options = {}  # display_name -> purpose
        if prompts_data and isinstance(prompts_data, list):
            for prompt in prompts_data:
                if prompt.get('active'):
                    display = f"@{prompt.get('name')} ({prompt.get('purpose')})"
                    prompt_options[display] = prompt.get('purpose')

        selected_display = st.selectbox("Template", list(prompt_options.keys()), help="Which prompt to use")
        purpose = prompt_options.get(selected_display) if selected_display else None
        provider = st.selectbox("Provider", ["mock", "google", "openai"], help="LLM provider")

        document_text = st.text_area(
            "Document Text",
            placeholder="Enter the document you want to process...",
            height=300
        )

        if st.button("🚀 Process Document", type="primary"):
            if not purpose or not document_text:
                st.error("Purpose and document text are required!")
            else:
                with st.spinner("Processing..."):
                    data = {
                        "purpose": purpose,
                        "document_text": document_text,
                        "provider": provider
                    }
                    result = api_post("/v1/predict/", data, headers={"X-User-Id": user_id})

                    if result:
                        st.success("✅ Processing complete!")
                        st.markdown("### Result")
                        st.text_area("Output", value=result.get('output_text'), height=200)

                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Latency", f"{result.get('latency_ms')}ms")
                        with col_b:
                            st.metric("Prompt ID", result.get('prompt_id')[:8] + "...")
                        with col_c:
                            st.metric("Version", result.get('prompt_version'))

    with col2:
        st.markdown("### 📊 Recent Predictions")
        predictions = api_get("/v1/predictions", params={"user_id": user_id, "limit": 5})
        if predictions and predictions.get('predictions'):
            for pred in predictions['predictions']:
                with st.expander(f"{pred.get('purpose')} - {pred.get('timestamp')[:16]}"):
                    st.write(f"**Provider:** {pred.get('provider')}")
                    st.write(f"**Latency:** {pred.get('latency_ms')}ms")
                    st.caption(f"Response: {pred.get('response')[:100]}...")

elif page == "📊 View History":
    st.title("📊 View History")

    tab1, tab2 = st.tabs(["Predictions", "Logs"])

    with tab1:
        st.subheader("Prediction History")

        col1, col2, col3 = st.columns(3)
        with col1:
            limit = st.number_input("Limit", min_value=1, max_value=100, value=10)
        with col2:
            filter_user = st.text_input("Filter by User ID", value="")
        with col3:
            filter_purpose = st.text_input("Filter by Purpose", value="")

        params = {"limit": limit}
        if filter_user:
            params["user_id"] = filter_user
        if filter_purpose:
            params["purpose"] = filter_purpose

        predictions = api_get("/v1/predictions", params=params)

        if predictions and predictions.get('predictions'):
            st.info(f"Found {predictions.get('count')} predictions")
            for pred in predictions['predictions']:
                with st.expander(f"[{pred.get('timestamp')}] {pred.get('purpose')} by {pred.get('user_id')}"):
                    st.write(f"**Provider:** {pred.get('provider')}")
                    st.write(f"**Latency:** {pred.get('latency_ms')}ms")
                    st.write(f"**Prompt ID:** {pred.get('prompt_id')}")
                    st.markdown("**Prompt:**")
                    st.code(pred.get('prompt'), language="text")
                    st.markdown("**Response:**")
                    st.code(pred.get('response'), language="text")
        else:
            st.info("No predictions found")

    with tab2:
        st.subheader("Application Logs")

        col1, col2 = st.columns(2)
        with col1:
            log_limit = st.number_input("Log Limit", min_value=1, max_value=500, value=50)
        with col2:
            log_level = st.selectbox("Level", ["All", "INFO", "WARNING", "ERROR"])

        params = {"limit": log_limit}
        if log_level != "All":
            params["level"] = log_level

        logs = api_get("/history", params=params)

        if logs and logs.get('history'):
            for log in logs['history']:
                level = log.get('level')
                if level == "ERROR":
                    st.error(f"[{log.get('timestamp')}] {log.get('message')}")
                elif level == "WARNING":
                    st.warning(f"[{log.get('timestamp')}] {log.get('message')}")
                else:
                    st.info(f"[{log.get('timestamp')}] {log.get('message')}")
        else:
            st.info("No logs found")

elif page == "⚙️ Config":
    st.title("⚙️ Configuration")
    st.markdown("View system configuration.")

    config = api_get("/config")

    if config:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Settings")
            st.metric("File Snapshot", "✅ Enabled" if config.get('FILE_SNAPSHOT') else "❌ Disabled")
            st.metric("Log Level", config.get('LOG_LEVEL'))

        with col2:
            st.subheader("API Keys")
            st.text(f"Google: {config.get('GOOGLE_API_KEY') or 'Not set'}")
            st.text(f"OpenAI: {config.get('OPENAI_API_KEY') or 'Not set'}")

        st.subheader("File Paths")
        st.code(f"""Database: {config.get('database_path')}
Logs: {config.get('log_file_path')}
Snapshot: {config.get('snapshot_path')}""", language="text")

        st.markdown("---")
        st.subheader("Full Configuration")
        st.json(config)

    # Health check
    st.markdown("---")
    st.subheader("Health Check")
    health = api_get("/health")
    if health and health.get('status') == 'ok':
        st.success("✅ API is healthy!")
    else:
        st.error("❌ API is not responding")
