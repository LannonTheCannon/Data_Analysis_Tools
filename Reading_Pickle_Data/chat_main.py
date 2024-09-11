import pandas as pd
import streamlit as st
import openai
from io import StringIO
from data import load_data
import time


def prepare_dataset_summary(df):
    buffer = StringIO()
    df.info(buf=buffer)
    info_string = buffer.getvalue()

    summary = f"""
    Dataset Summary:

    Number of rows: {len(df)}
    Number of columns: {len(df.columns)}

    Column descriptions:
    {info_string}

    Basic statistics:
    {df.describe().to_string()}

    Sample data (first 5 rows):
    {df.head().to_string()}
    """
    return summary


def update_assistant_with_dataset(client, assistant_id, dataset_summary):
    try:
        client.beta.assistants.update(
            assistant_id=assistant_id,
            instructions=f"You are an AI assistant specializing in credit card fraud detection. "
                         f"Use the following dataset information to provide insights and answer questions:\n\n"
                         f"{dataset_summary}"
        )
        st.success("Assistant updated with dataset information.")
    except Exception as e:
        st.error(f"Error updating assistant: {str(e)}")


def get_assistant_response(client, assistant_id, thread_id, user_input):
    try:
        # Add the user's message to the thread
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_input
        )

        # Create a run
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )

        # Wait for the run to complete
        while True:
            run_status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
            if run_status.status == 'completed':
                break
            time.sleep(1)

        # Retrieve the assistant's messages
        messages = client.beta.threads.messages.list(thread_id=thread_id)

        # Return the latest assistant message
        return messages.data[0].content[0].text.value
    except Exception as e:
        st.error(f"Error getting assistant response: {str(e)}")
        return "I'm sorry, but an error occurred while processing your request."


def display_ai_chat(df, client, assistant_id, thread_id):
    st.header("Chat with AI about the Dataset")

    if 'messages' not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What would you like to know about the credit card fraud data?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = get_assistant_response(client, assistant_id, thread_id, prompt)
            message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})


def display_dashboard(df):
    st.header("Credit Card Fraud Dashboard")
    st.write("This is a placeholder for the dashboard. You can add visualizations here.")
    st.dataframe(df.head())


def display_data_explorer(df):
    st.header("Data Explorer")
    st.write("This is a placeholder for the data explorer. You can add more detailed data analysis here.")
    st.write(df.describe())


def sidebar():
    with st.sidebar:
        st.title("🤖 AI Credit Card Fraud Analysis")
        st.markdown("---")
        st.markdown("## Navigation")
        page = st.radio("Go to", ["Dashboard", "Data Explorer", "AI Chat"])
        st.markdown("---")
        st.markdown("## About")
        st.info(
            "This dashboard uses AI to analyze credit card fraud data. You can explore the data, chat with an AI assistant, and get insights on the dataset.")
    return page


def main():
    st.set_page_config(page_title="AI Credit Card Fraud Analysis Dashboard", layout="wide")

    client = openai.OpenAI(api_key=st.secrets['OPENAI_API_KEY'])
    ASSISTANT_ID = 'asst_Gprcn49z0jmzvKpKaWeU7ZAw'
    THREAD_ID = "thread_0du078hnyl1z7AbIM7JyebsX"

    try:
        df = load_data("/data")
        if df.empty:
            st.error("The loaded dataset is empty. Please check your data source.")
            return
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return

    dataset_summary = prepare_dataset_summary(df)
    update_assistant_with_dataset(client, ASSISTANT_ID, dataset_summary)

    page = sidebar()

    if page == "Dashboard":
        display_dashboard(df)
    elif page == "Data Explorer":
        display_data_explorer(df)
    elif page == "AI Chat":
        display_ai_chat(df, client, ASSISTANT_ID, THREAD_ID)


if __name__ == "__main__":
    main()