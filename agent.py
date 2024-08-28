from langchain_community.agent_toolkits import SQLDatabaseToolkit

class Agent:
    def __init__(self, db, llm):
        self.db = db
        self.llm = llm
        self.toolkit = SQLDatabaseToolkit(db=db, llm=llm)
