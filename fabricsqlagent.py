import streamlit as st
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent, load_tools
from langchain_openai import AzureChatOpenAI
from langchain_community.callbacks.streamlit import (
    StreamlitCallbackHandler,
)
from dotenv import load_dotenv
from langchain.agents import create_sql_agent
from langchain.agents.agent_types import AgentType
from langchain.sql_database import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.vectorstores import FAISS
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_openai.embeddings.azure import AzureOpenAIEmbeddings
import os
import altair as alt
import pandas as pd
import os
from dotenv import load_dotenv
from langchain.agents import create_sql_agent
from langchain.sql_database import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_openai import AzureChatOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from sqlalchemy import create_engine, inspect, text, event
from sqlalchemy.engine import URL
import struct
import sys
from IPython.display import Markdown, HTML, display

from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
    SystemMessagePromptTemplate,
)
import json

load_dotenv()


def printmd(string):
    display(Markdown(string))


sql_server = os.environ["SQL_SERVER_NAME"]
sql_database = os.environ["SQL_SERVER_DATABASE"]

SQL_COPT_SS_ACCESS_TOKEN = (
    1256  # Connection option for access tokens, as defined in msodbcsql.h
)
TOKEN_URL = (
    "https://database.windows.net/.default"  # The token URL for any Azure SQL database
)
FABRIC_SCOPE = "https://fabric.microsoft.com/.default"
connection_string = (
    "mssql+pyodbc://"
    + sql_server
    + "/"
    + sql_database
    + "?driver=ODBC+Driver+18+for+SQL+Server"
)
engine = create_engine(connection_string)
azure_credentials = DefaultAzureCredential()


@event.listens_for(engine, "do_connect")
def provide_token(dialect, conn_rec, cargs, cparams):
    # remove the "Trusted_Connection" parameter that SQLAlchemy adds
    cargs[0] = cargs[0].replace(";Trusted_Connection=Yes", "")

    # create token credential
    raw_token = azure_credentials.get_token(
        TOKEN_URL, scopes=[FABRIC_SCOPE]
    ).token.encode("utf-16-le")
#    print("Token acquired", raw_token)
    token_struct = struct.pack(f"<I{len(raw_token)}s", len(raw_token), raw_token)

    # apply it to keyword arguments
    cparams["attrs_before"] = {SQL_COPT_SS_ACCESS_TOKEN: token_struct}


with engine.connect() as conn:
    try:
        # Use the text() construct for safer SQL execution
        result = conn.execute(text("SELECT @@VERSION"))
        version = result.fetchone()
        print("Connection successful!")
        print(version)
    except Exception as e:
        print(e)
        sys.exit(1)


try:
    db = SQLDatabase(engine, view_support=True, schema="dbo")
except Exception as e:
    print(f"An error occurred while connecting to the database: {e}")
    db = None  # Optionally, set db to None or handle the error as needed
    sys.exit(1)  # Exit the application with a non-zero status code indicating an error
print("Found following tables:", db.get_usable_table_names())

printmd(f"#### Connected to Database!")

llm = AzureChatOpenAI(
    deployment_name="gpt-4o",
    temperature=0.2,
    max_tokens=2000,
    api_version="2023-12-01-preview",
)
system_prefix = """

You are an agent designed to interact with a mssql database.
Always Format the response in Output as Json
Given an input question, create a syntactically correct sql query to run, then look at the results of the query and return the answer.
Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most 500 results.
You can order the results by a relevant column to return the most interesting examples in the database.
Never query for all the columns from a specific table, only ask for the relevant columns given the question.
You have access to tools for interacting with the database.
Only use the given tools. Only use the information returned by the tools to construct your final answer.
You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

If the question does not seem related to the database, just return "I don't know" as the answer.

Here are some examples of user inputs and their corresponding SQL queries:

Use the "loansfinal" view. Donot perform joins between table and a view to answer the query. All the information will be present in the view

Facts you need to know:
    - There is NO 'llm_chain' attribute - never reference it as a database column
    - If you cannot interpret the column name don't use it in the query

Rules:
    - Always Format the Output as Json, Retain the Column Names as they are in the Database
    - LIMIT the number of outputs of agent to 500 rows
"""


examples = [
    {
        "input": "Compute Average Credit Score by home ownership type",
        "query": "SELECT HomeOwnshp, AVG(CAST(CrdtScore AS INT)) AS AvgCreditScore FROM loansfinal GROUP BY HomeOwnshp",
    },
    {
        "input": "Produce a table listing Average credit score, Average Annual Income of applicants by their employment experience.",
        "query": "SELECT YearsJob, AVG(CAST(AnnlIncome AS FLOAT)) AS AvgAnnualIncome FROM loansfinal GROUP BY YearsJob",
    },
]

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
    prompt=full_prompt,
)


def clear_chat():
    st.session_state["chat_history"] = []


# Initialize chat history in session state if not already present
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# Add a reset button
if st.button("Reset Chat"):
    clear_chat()


if prompt := st.chat_input():
    st.chat_message("user").write(prompt)
    with st.chat_message("assistant"):
        st_callback = StreamlitCallbackHandler(st.container())
        response = agent_executor.invoke(
            {"input": prompt}, {"callbacks": [st_callback]}
        )
        
        response_text = response.get("output", "")
        print("Response Text ##########",response_text)
        json_start = response_text.find('```json\n') + len('```json\n')
        json_end = response_text.find('\n```', json_start)
        json_data = response_text[json_start:json_end]        
        parsed_data = json.loads(json_data)
        print("Data Parsed ##########",parsed_data)
        
        
        keys = list(parsed_data[0].keys())
        print("Keys ##########",keys)
        values = [list(item.values()) for item in parsed_data]
        print("Values ##########",values)
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
