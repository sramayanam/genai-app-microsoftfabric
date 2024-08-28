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

class Prompt:
    def __init__(self, input):
        
        self.input = input
        
        self.systemprompt = """
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

        self.queryexamples = [
            {
                "input": "Compute Average Credit Score by home ownership type",
                "query": "SELECT HomeOwnshp, AVG(CAST(CrdtScore AS INT)) AS AvgCreditScore FROM loansfinal GROUP BY HomeOwnshp",
            },
            {
                "input": "Produce a table listing Average credit score, Average Annual Income of applicants by their employment experience.",
                "query": "SELECT YearsJob, AVG(CAST(AnnlIncome AS FLOAT)) AS AvgAnnualIncome FROM loansfinal GROUP BY YearsJob",
            },
        ]

        self.system_prefix = self.systemprompt
        self.examples = self.queryexamples
        '''
        example_selector: An instance of SemanticSimilarityExampleSelector that selects examples based on semantic similarity.
        '''
        self.example_selector = SemanticSimilarityExampleSelector.from_examples(
            self.examples,
            AzureOpenAIEmbeddings(model="text-embedding-3-large"),
            FAISS,
            k=5,
            input_keys=["input"],
        )

        '''
        few_shot_prompt: A FewShotPromptTemplate instance that generates a prompt for few-shot learning.
        '''
        self.few_shot_prompt = FewShotPromptTemplate(
            example_selector=self.example_selector,
            example_prompt=PromptTemplate.from_template(
                "User input: {input}\nSQL query: {query}"
            ),
            input_variables=["input", "mssql", "100"],
            prefix=self.system_prefix,
            suffix="",
        )
    
        '''
        An instance of ChatPromptTemplate that constructs the full prompt from a series of messages.
        '''
        self.full_prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate(prompt=self.few_shot_prompt),
                ("human", "{input}"),
                MessagesPlaceholder("agent_scratchpad"),
            ]
        )

    def get_full_prompt(self):
        finalprompt = self.full_prompt.invoke(
            {
                "input": self.input,
                "top_k": 1,
                "dialect": "MSSQL",
                "agent_scratchpad": [],
            }
        )
        return finalprompt
