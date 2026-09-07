# Module 4 – Asynchronous Invocation

**Workshop:** AWS Serverless Patterns
**Link:** https://catalog.workshops.aws/serverless-patterns/en-US/module4
**Estimated duration:** 1–2 hours

## Overview

This module builds on the previous ones by implementing the **CQRS** (Command Query Responsibility Segregation) pattern, which separates data-change commands (mutations) from the underlying data store and query models.

### Scenario

Teams have different requirements for processing delivery address changes. Some of these processes may be long-running or not time-sensitive, so the user submitting the change doesn't need to wait for them to complete. When an address changes, the rider service needs to update the delivery area map to determine whether riders can service the new address — important, but not something the requester needs to wait on.

Asynchronous processing gives the user immediate feedback that their request was accepted, while downstream services process the data on their own timeline.

You will build a **User Profile service** composed of two key services:

- **Address Service**
- **Favorite Service**

## What You'll Learn

Implementing the **CQRS** and **Event-Driven Architecture (EDA)** design patterns:

- Deploy an **Amazon EventBridge** event bus and an **Amazon SQS** queue to decouple API Gateway from the back-end services that process requests.
- Use **API Gateway mapping templates** to integrate API Gateway methods directly with AWS services.
- Write integration tests to verify the API.
- Increase observability of backend processes with metrics.

## Tasks (SAM + Python track)

Build asynchronous microservices for user profiles using AWS SAM templates with Python:

1. Create an API Gateway (using the OpenAPI specification) and DynamoDB tables for the Address and Favorite services.
2. Create an EventBridge bus to route address events to consumers.
3. Integrate Lambda functions with the address bus.
4. Create an Amazon SQS queue to accept favorites requests.
5. Add Lambda event source mappings to the favorites queue.

## AWS Services Used

| Service | Purpose |
|---|---|
| Amazon EventBridge | Loosely coupled, event-driven architecture for routing address events |
| Amazon SQS | Fully managed message queue for the favorites requests |
| API Gateway mapping templates | Transform/integrate API Gateway requests directly with AWS services |
| OpenAPI | Language-agnostic spec used to define the REST API |
| AWS SAM | Shorthand IaC framework to define functions, APIs, databases, and event source mappings; deployed via the SAM CLI |
| Amazon Cognito | Identity store for user sign-up/sign-in and access control |
| Amazon DynamoDB | Fully managed NoSQL key/value store for Address and Favorite data |
| Amazon API Gateway | Front door for the REST API |
| AWS Lambda | Serverless compute for processing events and queue messages |

## Prerequisites

A development environment with all required dependencies (cloud-based IDE or local setup). If not already configured, complete the **Getting Started** section of the workshop first.

## Notes

- This module maps closely to **Domain 2 (Design)** of the AWS Certified Developer – Associate (DVA-C02) exam, particularly around decoupling architectures with EventBridge and SQS.
- Previous: Module 3 · Next: Module 5