# Serverless Workshop - Module 3
This is implementation of the backend REST API using Python and AWS SAM. 

## Initial Setup
If you haven't finished Module 2 please follow [instructions](./_start_state/README.md) to run initial setup and deploy resources necessary for this module.

## Deploy the completed module

1. Find the Cognito User Pool Id from Module 2. 
   1. Navigate to CloudFormation
   2. Select the `serverless-workshop` stack
   3. Navigate to the **Outputs** tab
   4. Find the `UserPool` key and copy the value.
2. Open a terminal window to the `module3/sam-python` directory
3. Run `sam build`. When completed...
4. Run `sam deploy --guided`. Accept all default values **except** when prompted for `Parameter UserPool`. Enter the Cognito User Pool Id value from above. 


## Run the integration tests

1. Set two environment variables:

```
export ENV_STACK_NAME=serverless-workshop
export MOD3_STACK_NAME=serverless-workshop-module3
```

2. Install the python testing module
   1. Run the following command in your command line: `pip install -U pytest`
   2. Check that you installed a working version: `$ pytest --version`

3. Run the tests

```
cd module3
python -m pytest tests/integration -v
```
