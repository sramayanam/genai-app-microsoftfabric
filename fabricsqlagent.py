from langchain.agents import create_sql_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.vectorstores import FAISS
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_openai.embeddings.azure import AzureOpenAIEmbeddings
from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_community.callbacks.streamlit import (
    StreamlitCallbackHandler,
)
import streamlit as st
import altair as alt
from dotenv import load_dotenv
import pandas as pd
import json
import prompt as prompt
from utilities import create_llm
from utilities import clear_chat
from sqlalchemy import event, text
import struct
from azure.identity import DefaultAzureCredential,get_bearer_token_provider
from utilities import get_connection_string
from sqlalchemy import create_engine,text
from langchain.sql_database import SQLDatabase
import sys
load_dotenv()
azure_credentials = DefaultAzureCredential()
llm = create_llm()

engine=create_engine(get_connection_string())
SQL_COPT_SS_ACCESS_TOKEN = (1256)
TOKEN_URL = "https://database.windows.net/.default"
FABRIC_SCOPE = "https://fabric.microsoft.com/.default"
    
@event.listens_for(engine, "do_connect")
def provide_token(dialect, conn_rec, cargs, cparams):
    cargs[0] = cargs[0].replace(";Trusted_Connection=Yes", "")
    raw_token = azure_credentials.get_token(
        TOKEN_URL, scopes=[FABRIC_SCOPE]
    ).token.encode("utf-16-le")
    token_struct = struct.pack(f"<I{len(raw_token)}s", len(raw_token), raw_token)
    cparams["attrs_before"] = {SQL_COPT_SS_ACCESS_TOKEN: token_struct}


try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT @@VERSION"))
        version = result.fetchone()
        print("Connection successful!")
        print(version)
        db = SQLDatabase(engine, view_support=True, schema="dbo")
        print("Found following tables:", db.get_usable_table_names())
except Exception as e:
    print(e)
    sys.exit(1)


system_prefix = prompt.systemprompt

examples = prompt.queryexamples

example_selector = SemanticSimilarityExampleSelector.from_examples(
    examples,
    AzureOpenAIEmbeddings(model="text-embedding-3-large"),
    FAISS,
    k=5,
    input_keys=["input"],
)

few_shot_prompt = FewShotPromptTemplate(
    example_selector=example_selector,
    example_prompt=PromptTemplate.from_template(
        "User input: {input}\nSQL query: {query}"
    ),
    input_variables=["input", "mssql", "100"],
    prefix=system_prefix,
    suffix="",
)

full_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate(prompt=few_shot_prompt),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ]
)

prompt_val = full_prompt.invoke(
    {
        "input": "Compute Average Annual Income by Purpose?",
        "top_k": 1,
        "dialect": "MSSQL",
        "agent_scratchpad": [],
    }
)

toolkit = SQLDatabaseToolkit(db=db, llm=llm)

agent_executor = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type="openai-tools",
    agent_executor_kwargs={"return_intermediate_steps": True},
    #    prompt=full_prompt,
    # prompt=prompt_val,
)

# Initialize chat history in session state if not already present
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# Add a reset button
if st.button("Reset Chat"):
    clear_chat()


if prompt := st.chat_input():

    st.chat_message("user").write(prompt)

    prompt_val = full_prompt.invoke(
        {
            "input": "Compute Average Annual Income by Purpose?",
            "top_k": 1,
            "dialect": "MSSQL",
            "agent_scratchpad": [],
        }
    )

    with st.chat_message("assistant"):
        st_callback = StreamlitCallbackHandler(st.container())
        response = agent_executor.invoke(
            {"input": prompt_val}, {"callbacks": [st_callback]}
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
