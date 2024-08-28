from sqlalchemy import create_engine, event, text
from azure.identity import DefaultAzureCredential
import struct
import sys
from utilities import get_connection_string
from langchain.sql_database import SQLDatabase

"""
- **sqlalchemy**: SQL toolkit and Object-Relational Mapping (ORM) library.
  - **create_engine**: Creates a new SQLAlchemy engine instance.
  - **event**: Provides event listening capabilities.
  - **text**: Allows execution of raw SQL queries.

- **azure.identity**: Provides Azure Active Directory token authentication.
  - **DefaultAzureCredential**: Simplifies authentication by providing a default credential.

- **struct**: Provides functions to work with C-style data structures.
- **sys**: Provides access to system-specific parameters and functions.

- **langchain.sql_database**: Provides SQL database functionalities.
  - **SQLDatabase**: Represents a SQL database.
  - **SQL_COPT_SS_ACCESS_TOKEN**: Constant for SQL Server access token.
  - **TOKEN_URL**: URL for obtaining the Azure token.
  - **FABRIC_SCOPE**: Scope for the Azure token.
  - **setup_event_listener**: Sets up the event listener for the engine.

- **setup_event_listener**: Sets up an event listener for the engine's [`do_connect`](command:_github.copilot.openSymbolFromReferences?%5B%22do_connect%22%2C%5B%7B%22uri%22%3A%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22%2FUsers%2Fsreeram%2FDocuments%2FGitHub%2Fsqlagentonfabric%2Fconnection.py%22%2C%22external%22%3A%22file%3A%2F%2F%2FUsers%2Fsreeram%2FDocuments%2FGitHub%2Fsqlagentonfabric%2Fconnection.py%22%2C%22path%22%3A%22%2FUsers%2Fsreeram%2FDocuments%2FGitHub%2Fsqlagentonfabric%2Fconnection.py%22%2C%22scheme%22%3A%22file%22%7D%2C%22pos%22%3A%7B%22line%22%3A17%2C%22character%22%3A41%7D%7D%5D%5D "Go to definition") event.
  - **provide_token**: Event listener function that provides the Azure token for authentication.
    - **cargs**: Connection arguments, modified to remove [`Trusted_Connection`](command:_github.copilot.openSymbolFromReferences?%5B%22Trusted_Connection%22%2C%5B%7B%22uri%22%3A%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22%2FUsers%2Fsreeram%2FDocuments%2FGitHub%2Fsqlagentonfabric%2Fconnection.py%22%2C%22external%22%3A%22file%3A%2F%2F%2FUsers%2Fsreeram%2FDocuments%2FGitHub%2Fsqlagentonfabric%2Fconnection.py%22%2C%22path%22%3A%22%2FUsers%2Fsreeram%2FDocuments%2FGitHub%2Fsqlagentonfabric%2Fconnection.py%22%2C%22scheme%22%3A%22file%22%7D%2C%22pos%22%3A%7B%22line%22%3A19%2C%22character%22%3A42%7D%7D%5D%5D "Go to definition").
    - **raw_token**: Azure token encoded in UTF-16-LE.
    - **token_struct**: Packed token structure.
    - **cparams**: Connection parameters, updated with the token structure.

- **connect_to_database**: Connects to the database and retrieves version information.

"""

class DatabaseManager:
    def __init__(self):
        self.azure_credentials = DefaultAzureCredential()
        self.engine = create_engine(get_connection_string())
        self.SQL_COPT_SS_ACCESS_TOKEN = 1256
        self.TOKEN_URL = "https://database.windows.net/.default"
        self.FABRIC_SCOPE = "https://fabric.microsoft.com/.default"
        self.setup_event_listener()

    def setup_event_listener(self):
        @event.listens_for(self.engine, "do_connect")
        def provide_token(dialect, conn_rec, cargs, cparams):
            cargs[0] = cargs[0].replace(";Trusted_Connection=Yes", "")
            raw_token = self.azure_credentials.get_token(
                self.TOKEN_URL, scopes=[self.FABRIC_SCOPE]
            ).token.encode("utf-16-le")
            token_struct = struct.pack(
                f"<I{len(raw_token)}s", len(raw_token), raw_token
            )
            cparams["attrs_before"] = {self.SQL_COPT_SS_ACCESS_TOKEN: token_struct}

    def connect_to_database(self):
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT @@VERSION"))
                version = result.fetchone()
                print("Connection successful!")
                print(version)
                db = SQLDatabase(self.engine, view_support=True, schema="dbo")
                #print("Found following tables:", db.get_usable_table_names())
                return db
        except Exception as e:
            print(e)
            sys.exit(1)
