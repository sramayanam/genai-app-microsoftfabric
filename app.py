from langchain_community.callbacks.streamlit import (
    StreamlitCallbackHandler,
)
import streamlit as st
import altair as alt
from dotenv import load_dotenv
import pandas as pd
import json
from utilities import clear_chat
from connection import DatabaseManager
from prompt import Prompt
from fabricsqlagent import SQLAgent
from utilities import create_llm

load_dotenv()

# Initialize agents and database connection. 
# Initialize llm deployment

db_manager = DatabaseManager()
db = db_manager.connect_to_database()
llm = create_llm()
agent = SQLAgent(db=db, llm=llm)
agent_executor = agent.get_agent_executor()

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

if st.button("Reset Chat"):
    clear_chat()
    

#   StreamlitCallbackHandler: Handles Streamlit-specific callbacks.
#   streamlit: A library for creating web apps.
#   altair: A declarative statistical visualization library.
#   Handle User Input:
#       prompt: User input from the chat.
#       full_prompt: Full prompt generated from the user input.


if prompt := st.chat_input():

    st.chat_message("user").write(prompt)

    full_prompt = Prompt(prompt).get_full_prompt()

    with st.chat_message("assistant"):
        st_callback = StreamlitCallbackHandler(st.container())
        response = agent_executor.invoke(
            {"input": full_prompt}, {"callbacks": [st_callback]}
        )

        response_text = response.get("output", "")
        print("Response Text ##########", response_text)
        json_start = response_text.find("```json\n") + len("```json\n")
        json_end = response_text.find("\n```", json_start)
        json_data = response_text[json_start:json_end]
        parsed_data = json.loads(json_data)
        print("Data Parsed ##########", parsed_data)

        keys = list(parsed_data[0].keys())
        print("Keys ##########", keys)
        values = [list(item.values()) for item in parsed_data]
        print("Values ##########", values)
        data = pd.DataFrame(values, columns=keys)

        st.write(data)

        bar_chart = (
            alt.Chart(data)
            .mark_bar()
            .encode(x=keys[0], y=keys[1], color=keys[0])
            .properties(title="Plot of {} Against {}".format(keys[0], keys[1]))
        )
        if "bar chart" in prompt.lower():
            st.altair_chart(bar_chart, use_container_width=True)


for role, message in st.session_state["chat_history"]:
    st.chat_message(role).write(message)
