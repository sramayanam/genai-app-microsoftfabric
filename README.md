# LLM Agent on Microsoft Fabric

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

# Use your own tables. Sample data will not be provided with the repository. Couple of sample screen shots this app generates. 

## Prompt Input

### Create a bar chart showing average credit score by Years of experience

### Output Visualization
![visualization](https://github.com/user-attachments/assets/25bd849d-6c42-4e0b-9eff-ca24a176d48a)

