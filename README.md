# LLM Agent on Microsoft Fabric

This code generates a visual or table based on the user input
The backend database is Microsoft Fabric SQL warehouse
SQL Agent connects to Fabric based on the following contents from .env file
Create an env file following the sample template below
```
sqlservername={Microst Fabric Warehouse GUID}.datawarehouse.fabric.microsoft.com
sqlserverdatabase={Name of the Microsoft Fabric Warehouse}
gpt4deploymentname={LLM Deployment name}
azureopenaiapiversion={Deployment Version}
azureopenaiendpoint={Azure Open AI EndPoint}
azureopenaiapikey={Azure Open AI Key}
armsubscriptionid={Your Subscription ID}
azuretenantid={Your Azure Tenant ID}
azureclientid={Your SP Client ID}
azureclientsecret={Your SP Secret}
```

# Initialize and Run the Application

## Use Docker

```
docker build -t genaiapp .

docker run -d -p 8501:8501 -e SQL_SERVER_NAME=${sqlservername} \
    -e SQL_SERVER_DATABASE=${sqlserverdatabase} \
    -e GPT4_DEPLOYMENT_NAME=${gpt4deploymentname} \
    -e AZURE_OPENAI_API_VERSION=${azureopenaiapiversion} \
    -e AZURE_OPENAI_ENDPOINT=${azureopenaiendpoint} \
    -e AZURE_OPENAI_API_KEY=${azureopenaiapikey} \
    -e ARM_SUBSCRIPTION_ID=${armsubscriptionid} \
    -e AZURE_TENANT_ID=${azuretenantid} \
    -e AZURE_CLIENT_ID=${azureclientid} \
    -e AZURE_CLIENT_SECRET=${azureclientsecret} \
    -t genaiapp:latest
```

## Run locally

```
streamlit run app.py
```

# Use your own tables. This fictitious sample data will not be provided with the repository. Couple of sample screen shots this app generates. **** These visualizations are generated with Made UP Data ****

## Prompt Sample Input 1:

### Create a bar chart to render the average annual income by loan type

### Output Visualition
![visualization (1)](https://github.com/user-attachments/assets/31995175-536a-40ae-a6e2-ac14a8aad788)

## Prompt Sample Input 2:

### Create a bar chart showing average credit score by Years of experience

### Output Visualization
![visualization](https://github.com/user-attachments/assets/25bd849d-6c42-4e0b-9eff-ca24a176d48a)

