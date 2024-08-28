from langchain.agents import create_sql_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from agent import Agent
class SQLAgent(Agent):
    def __init__(self, db, llm):
        super().__init__(db, llm)
        self.agent_executor = create_sql_agent(
            llm=llm,
            toolkit=self.toolkit,
            verbose=True,
            agent_type="openai-tools",
            agent_executor_kwargs={"return_intermediate_steps": True},
        )

    def get_agent_executor(self):
        return self.agent_executor

