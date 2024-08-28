from IPython.display import Markdown, display
from langchain_openai import AzureChatOpenAI
import os
import streamlit as st



from dotenv import load_dotenv
load_dotenv()

def printmd(string):
    display(Markdown(string))

def create_llm():
    return AzureChatOpenAI(
        deployment_name="gpt-4o",
        temperature=0.2,
        max_tokens=2000,
        api_version="2023-12-01-preview",
    )

def get_connection_string():
    sql_server = os.environ["SQL_SERVER_NAME"]
    sql_database = os.environ["SQL_SERVER_DATABASE"]
    return (
        "mssql+pyodbc://"
        + sql_server
        + "/"
        + sql_database
        + "?driver=ODBC+Driver+18+for+SQL+Server"
    )


def clear_chat():
    st.session_state["chat_history"] = []
