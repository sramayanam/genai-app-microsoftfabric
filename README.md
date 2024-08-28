# sqlagentonfabric

This code generates a visual or table based on the user input
The backend database is Microsoft Fabric SQL warehouse
SQL Agent connects to Fabric based on the following contents from .env file
Create an env file following the sample template below
```
SQL_SERVER_NAME={Microst Fabric Warehouse GUID}.datawarehouse.fabric.microsoft.com
SQL_SERVER_DATABASE={Name of the Microsoft Fabric Warehouse}
GPT4_DEPLOYMENT_NAME={LLM Deployment name}
AZURE_OPENAI_API_VERSION={Deployment Version}
AZURE_OPENAI_ENDPOINT={Azure Open AI EndPoint}
AZURE_OPENAI_API_KEY={Azure Open AI Key}
ARM_SUBSCRIPTION_ID={Your Subscription ID}
AZURE_TENANT_ID={Your Azure Tenant ID}
AZURE_CLIENT_ID={Your SP Client ID}
AZURE_CLIENT_SECRET={Your SP Secret}
```

# Initialize and Run the Application

```
streamlit run app.py
```