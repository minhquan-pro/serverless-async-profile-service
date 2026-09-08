# Serverless Workshop - Module 2 ending state
This is ending state of the Module 2.

### Cleanup resources created by previous modules
To delete the resources that you may have created in the previous modules, use AWS SAM (answer "y" to the confirmation prompts):

```bash
sam delete --stack-name serverless-workshop 
```

### Deploy the previous module results

To build and deploy your application, navigate to _start_state folder, and run the following in your shell:

```bash
sam build 
sam deploy --stack-name serverless-workshop --resolve-s3 --capabilities CAPABILITY_IAM
```

The first command will build the source of your application. The second command will package and deploy your application to AWS, with a series of prompts.

