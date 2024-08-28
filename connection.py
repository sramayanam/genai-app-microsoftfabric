from sqlalchemy import create_engine, event, text
from azure.identity import DefaultAzureCredential
import struct
import sys
from utilities import get_connection_string
from langchain.sql_database import SQLDatabase

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
            token_struct = struct.pack(f"<I{len(raw_token)}s", len(raw_token), raw_token)
            cparams["attrs_before"] = {self.SQL_COPT_SS_ACCESS_TOKEN: token_struct}

    def connect_to_database(self):
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT @@VERSION"))
                version = result.fetchone()
                print("Connection successful!")
                print(version)
                db = SQLDatabase(self.engine, view_support=True, schema="dbo")
                print("Found following tables:", db.get_usable_table_names())
                return db
        except Exception as e:
            print(e)
            sys.exit(1)
