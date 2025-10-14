# AI Implementation Prompt: Portfolio Optimization Platform

## Context

You are tasked with building a production-ready portfolio optimization web application that calculates the Kelly Criterion for ETF portfolios. This document provides complete instructions for implementing the system from start to finish.

**Current State:**
- Existing SolidJS frontend with client-side Kelly Criterion calculator
- SST v3 infrastructure deploys a static site to AWS
- No backend, no database, no real data - everything is mock/manual entry
- Located at: `/Users/seanflanagan/dev/investing-portfolio`

**Target State:**
- Full-stack serverless application on AWS
- Real-time ETF data from Polygon.io API
- Historical data storage for correlation analysis
- Production-ready API with admin controls
- Enhanced client with asset search, volatility charts, and black swan modeling

**Reference Documents:**
- `project-prd.md` - Complete technical specifications
- `highlevel-prd.md` - User-friendly overview
- `CLAUDE.md` - Project-specific guidelines

---

## Implementation Strategy

### Guiding Principles

1. **Build Incrementally**: Implement in phases, test each phase thoroughly
2. **Backend First**: Infrastructure and API before client updates
3. **Type Safety**: Use TypeScript everywhere with strict types
4. **Testing**: Write tests for all Lambda functions
5. **Monitoring**: Add logging and metrics from day one
6. **Documentation**: Document all APIs and architecture decisions

### Technology Choices (Pre-determined)

- **IaC**: SST v3 (Ion) with Pulumi backend
- **Runtime**: Node.js 20.x for Lambda
- **Database**: DynamoDB + Amazon Timestream + S3
- **API**: API Gateway HTTP API
- **Logging**: AWS Lambda Powertools (TypeScript)
- **Testing**: Jest + ts-jest
- **Client**: Keep existing SolidJS setup

---

## Phase-by-Phase Implementation

## PHASE 1: Infrastructure Foundation

### Goal
Set up all AWS resources: DynamoDB, Timestream, S3, API Gateway, Lambda scaffolding.

### Steps

#### 1.1 Update SST Configuration

**File:** `sst.config.ts`

Add new infrastructure imports and configuration:

```typescript
/// <reference path="./.sst/platform/config.d.ts" />

export default $config({
  app(input) {
    return {
      name: "portfolio-optimizer",
      removal: input?.stage === "production" ? "retain" : "remove",
      protect: ["production"].includes(input?.stage),
      home: "aws",
    };
  },
  async run() {
    // Import infrastructure modules
    const { storage } = await import("./infra/storage");
    const { database } = await import("./infra/database");
    const { api } = await import("./infra/api");
    const { monitoring } = await import("./infra/monitoring");

    // Create resources
    const { assetsBucket } = storage;
    const { assetsTable, historicalPricesDB } = database;
    const { httpApi } = api;
    const { logGroups } = monitoring;

    // Existing static site
    const site = new sst.aws.StaticSite("PortfolioOptimizer", {
      build: { command: "pnpm run build", output: "dist" },
      environment: {
        VITE_API_URL: httpApi.url
      }
    });

    return {
      api: httpApi.url,
      site: site.url
    };
  },
});
```

#### 1.2 Create Storage Infrastructure

**File:** `infra/storage.ts`

```typescript
import { Bucket } from "sst/aws";

// S3 bucket for data backups and exports
export const assetsBucket = new Bucket("AssetsBucket", {
  public: false,
  versioning: true,
  lifecycle: {
    rules: [
      {
        id: "transition-backups-to-glacier",
        enabled: true,
        prefix: "backups/",
        transitions: [
          {
            days: 30,
            storageClass: "GLACIER"
          }
        ]
      },
      {
        id: "delete-exports",
        enabled: true,
        prefix: "exports/",
        expiration: { days: 90 }
      },
      {
        id: "delete-polygon-raw",
        enabled: true,
        prefix: "polygon-raw/",
        expiration: { days: 7 }
      }
    ]
  }
});

export const storage = { assetsBucket };
```

#### 1.3 Create Database Infrastructure

**File:** `infra/database.ts`

```typescript
import * as aws from "@pulumi/aws";

// DynamoDB table for asset metadata
export const assetsTable = new aws.dynamodb.Table("AssetsTable", {
  name: `portfolio-optimizer-assets-${$app.stage}`,
  billingMode: "PAY_PER_REQUEST",
  hashKey: "PK",
  rangeKey: "SK",
  attributes: [
    { name: "PK", type: "S" },
    { name: "SK", type: "S" },
    { name: "category", type: "S" },
    { name: "assetClass", type: "S" },
    { name: "symbol", type: "S" },
    { name: "sharpeRatio", type: "N" }
  ],
  globalSecondaryIndexes: [
    {
      name: "CategoryIndex",
      hashKey: "category",
      rangeKey: "symbol",
      projectionType: "ALL"
    },
    {
      name: "AssetClassIndex",
      hashKey: "assetClass",
      rangeKey: "sharpeRatio",
      projectionType: "ALL"
    }
  ],
  streamEnabled: true,
  streamViewType: "NEW_AND_OLD_IMAGES",
  pointInTimeRecovery: {
    enabled: $app.stage === "production"
  },
  tags: {
    Environment: $app.stage,
    Application: "portfolio-optimizer"
  }
});

// Timestream database for historical prices
export const timestreamDB = new aws.timestreamwrite.Database("HistoricalPricesDB", {
  databaseName: `portfolio-optimizer-${$app.stage}`,
  tags: {
    Environment: $app.stage,
    Application: "portfolio-optimizer"
  }
});

export const historicalPricesTable = new aws.timestreamwrite.Table("HistoricalPricesTable", {
  databaseName: timestreamDB.databaseName,
  tableName: "HistoricalPrices",
  retentionProperties: {
    memoryStoreRetentionPeriodInHours: 168, // 7 days
    magneticStoreRetentionPeriodInDays: 7300 // 20 years
  },
  magneticStoreWriteProperties: {
    enableMagneticStoreWrites: true
  },
  tags: {
    Environment: $app.stage,
    Application: "portfolio-optimizer"
  }
});

export const database = {
  assetsTable,
  historicalPricesDB: timestreamDB,
  historicalPricesTable
};
```

#### 1.4 Create API Infrastructure

**File:** `infra/api.ts`

```typescript
import { Function } from "sst/aws";
import * as aws from "@pulumi/aws";
import { assetsTable, historicalPricesDB } from "./database";
import { assetsBucket } from "./storage";

// Lambda function defaults
const functionDefaults = {
  runtime: "nodejs20.x" as const,
  timeout: "30 seconds" as const,
  memory: "512 MB" as const,
  environment: {
    ASSETS_TABLE_NAME: assetsTable.name,
    TIMESTREAM_DB_NAME: historicalPricesDB.databaseName,
    TIMESTREAM_TABLE_NAME: "HistoricalPrices",
    ASSETS_BUCKET_NAME: assetsBucket.name,
    STAGE: $app.stage
  },
  link: [assetsTable, historicalPricesDB, assetsBucket]
};

// Public Lambda functions
export const getAssetsFunction = new Function("GetAssets", {
  ...functionDefaults,
  handler: "functions/getAssets/index.handler",
  description: "Get list of all assets"
});

export const getAssetFunction = new Function("GetAsset", {
  ...functionDefaults,
  handler: "functions/getAsset/index.handler",
  description: "Get single asset details"
});

export const getVolatilityFunction = new Function("GetVolatility", {
  ...functionDefaults,
  handler: "functions/getVolatility/index.handler",
  description: "Get volatility history for an asset"
});

export const calculateCorrelationFunction = new Function("CalculateCorrelation", {
  ...functionDefaults,
  handler: "functions/calculateCorrelation/index.handler",
  memory: "1024 MB",
  timeout: "60 seconds",
  description: "Calculate correlation matrix"
});

export const calculateKellyFunction = new Function("CalculateKelly", {
  ...functionDefaults,
  handler: "functions/calculateKelly/index.handler",
  memory: "1024 MB",
  description: "Calculate Kelly Criterion allocations"
});

// Admin Lambda functions
export const adminAuthorizerFunction = new Function("AdminAuthorizer", {
  ...functionDefaults,
  handler: "functions/adminAuthorizer/index.handler",
  timeout: "10 seconds",
  description: "Authorize admin API requests"
});

export const adminUpdateAssetsFunction = new Function("AdminUpdateAssets", {
  ...functionDefaults,
  handler: "functions/admin/updateAssets.handler",
  description: "Admin: Update asset metadata"
});

export const adminTriggerIngestFunction = new Function("AdminTriggerIngest", {
  ...functionDefaults,
  handler: "functions/admin/triggerIngest.handler",
  description: "Admin: Manually trigger data ingestion"
});

export const adminUploadDataFunction = new Function("AdminUploadData", {
  ...functionDefaults,
  handler: "functions/admin/uploadData.handler",
  description: "Admin: Bulk data upload"
});

// API Gateway
export const httpApi = new aws.apigatewayv2.Api("HttpApi", {
  name: `portfolio-optimizer-api-${$app.stage}`,
  protocolType: "HTTP",
  corsConfiguration: {
    allowOrigins: ["*"], // Restrict in production
    allowMethods: ["GET", "POST", "OPTIONS"],
    allowHeaders: ["Content-Type", "Authorization", "X-Api-Key"],
    maxAge: 3600
  },
  tags: {
    Environment: $app.stage,
    Application: "portfolio-optimizer"
  }
});

// API Gateway Stage
export const apiStage = new aws.apigatewayv2.Stage("ApiStage", {
  apiId: httpApi.id,
  name: $app.stage,
  autoDeploy: true,
  accessLogSettings: {
    destinationArn: apiLogGroup.arn,
    format: JSON.stringify({
      requestId: "$context.requestId",
      ip: "$context.identity.sourceIp",
      requestTime: "$context.requestTime",
      httpMethod: "$context.httpMethod",
      routeKey: "$context.routeKey",
      status: "$context.status",
      protocol: "$context.protocol",
      responseLength: "$context.responseLength"
    })
  },
  defaultRouteSettings: {
    throttlingBurstLimit: 200,
    throttlingRateLimit: 100
  }
});

// Define integrations and routes...
// (Routes defined in next section)

export const api = { httpApi, apiStage };
```

#### 1.5 Test Infrastructure Deployment

```bash
# Deploy to dev environment
pnpm sst deploy --stage dev

# Verify resources created
aws dynamodb describe-table --table-name portfolio-optimizer-assets-dev
aws timestream-write describe-database --database-name portfolio-optimizer-dev
aws s3 ls | grep portfolio-optimizer
```

**Expected Output:**
- DynamoDB table created with GSIs
- Timestream database and table created
- S3 bucket created with lifecycle policies
- No errors in deployment

**Acceptance Criteria:**
- [ ] All AWS resources deploy successfully
- [ ] SST deploy completes without errors
- [ ] Can query DynamoDB table (empty results OK)
- [ ] Can access S3 bucket
- [ ] Cost is $0 (no usage yet)

---

## PHASE 2: Data Ingestion Pipeline

### Goal
Implement the daily data ingestion process that fetches data from Polygon.io API and stores it in DynamoDB and Timestream.

### Steps

#### 2.1 Create Ingestion Infrastructure

**File:** `infra/ingestion.ts`

```typescript
import * as aws from "@pulumi/aws";
import { Function } from "sst/aws";
import { assetsTable, historicalPricesDB } from "./database";
import { assetsBucket } from "./storage";

// SQS Queue for rate-limited ingestion
export const ingestionQueue = new aws.sqs.Queue("IngestionQueue", {
  name: `portfolio-optimizer-ingestion-${$app.stage}.fifo`,
  fifoQueue: true,
  contentBasedDeduplication: true,
  visibilityTimeoutSeconds: 300, // 5 minutes
  messageRetentionSeconds: 86400, // 24 hours
  tags: {
    Environment: $app.stage,
    Application: "portfolio-optimizer"
  }
});

// Dead Letter Queue
export const ingestionDLQ = new aws.sqs.Queue("IngestionDLQ", {
  name: `portfolio-optimizer-ingestion-dlq-${$app.stage}`,
  messageRetentionSeconds: 1209600, // 14 days
  tags: {
    Environment: $app.stage,
    Application: "portfolio-optimizer"
  }
});

// Redrive policy
const redrivePolicy = aws.sqs.Queue.getRedrivePolicy({
  deadLetterTargetArn: ingestionDLQ.arn,
  maxReceiveCount: 3
});

ingestionQueue.redrivePolicy.apply(policy =>
  pulumi.output(JSON.stringify(redrivePolicy))
);

// Schedule Ingestion Lambda
export const scheduleIngestionFunction = new Function("ScheduleIngestion", {
  handler: "functions/scheduleIngestion/index.handler",
  runtime: "nodejs20.x",
  timeout: "5 minutes",
  memory: "256 MB",
  environment: {
    ASSETS_TABLE_NAME: assetsTable.name,
    INGESTION_QUEUE_URL: ingestionQueue.url,
    STAGE: $app.stage
  },
  link: [assetsTable, ingestionQueue],
  permissions: [
    {
      actions: ["sqs:SendMessage"],
      resources: [ingestionQueue.arn]
    }
  ]
});

// Process Ingestion Lambda
export const processIngestionFunction = new Function("ProcessIngestion", {
  handler: "functions/processIngestion/index.handler",
  runtime: "nodejs20.x",
  timeout: "5 minutes",
  memory: "512 MB",
  environment: {
    ASSETS_TABLE_NAME: assetsTable.name,
    TIMESTREAM_DB_NAME: historicalPricesDB.databaseName,
    TIMESTREAM_TABLE_NAME: "HistoricalPrices",
    ASSETS_BUCKET_NAME: assetsBucket.name,
    POLYGON_API_KEY_SECRET: "/portfolio-optimizer/polygon-api-key",
    STAGE: $app.stage
  },
  link: [assetsTable, historicalPricesDB, assetsBucket, ingestionQueue],
  permissions: [
    {
      actions: ["timestream:WriteRecords"],
      resources: ["*"]
    },
    {
      actions: ["secretsmanager:GetSecretValue"],
      resources: ["*"]
    }
  ]
});

// SQS Event Source Mapping
export const ingestionEventSource = new aws.lambda.EventSourceMapping("IngestionEventSource", {
  eventSourceArn: ingestionQueue.arn,
  functionName: processIngestionFunction.name,
  batchSize: 1,
  maximumConcurrency: 1, // Process one at a time for rate limiting
  functionResponseTypes: ["ReportBatchItemFailures"]
});

// EventBridge Rule for daily scheduling
export const dailyIngestionRule = new aws.cloudwatch.EventRule("DailyIngestion", {
  name: `portfolio-optimizer-daily-ingestion-${$app.stage}`,
  description: "Trigger daily data ingestion at 6 PM ET",
  scheduleExpression: "cron(0 23 * * ? *)", // 11 PM UTC = 6 PM ET
  isEnabled: true,
  tags: {
    Environment: $app.stage,
    Application: "portfolio-optimizer"
  }
});

export const dailyIngestionTarget = new aws.cloudwatch.EventTarget("DailyIngestionTarget", {
  rule: dailyIngestionRule.name,
  arn: scheduleIngestionFunction.arn
});

// Permission for EventBridge to invoke Lambda
export const dailyIngestionPermission = new aws.lambda.Permission("DailyIngestionPermission", {
  action: "lambda:InvokeFunction",
  function: scheduleIngestionFunction.name,
  principal: "events.amazonaws.com",
  sourceArn: dailyIngestionRule.arn
});

export const ingestion = {
  ingestionQueue,
  ingestionDLQ,
  scheduleIngestionFunction,
  processIngestionFunction,
  dailyIngestionRule
};
```

#### 2.2 Store Polygon.io API Key

```bash
# Store API key in Secrets Manager
aws secretsmanager create-secret \
  --name /portfolio-optimizer/polygon-api-key \
  --secret-string "YOUR_POLYGON_API_KEY" \
  --region us-east-1
```

#### 2.3 Implement Schedule Ingestion Lambda

**File:** `functions/scheduleIngestion/index.ts`

```typescript
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, ScanCommand } from "@aws-sdk/lib-dynamodb";
import { SQSClient, SendMessageCommand } from "@aws-sdk/client-sqs";
import { Logger } from "@aws-lambda-powertools/logger";

const dynamodb = DynamoDBDocumentClient.from(new DynamoDBClient({}));
const sqs = new SQSClient({});
const logger = new Logger({ serviceName: "scheduleIngestion" });

const ASSETS_TABLE = process.env.ASSETS_TABLE_NAME!;
const QUEUE_URL = process.env.INGESTION_QUEUE_URL!;

export async function handler(event: any) {
  logger.info("Starting daily ingestion scheduling");

  try {
    // Get all active assets from DynamoDB
    const { Items: assets } = await dynamodb.send(new ScanCommand({
      TableName: ASSETS_TABLE,
      FilterExpression: "SK = :metadata AND isActive = :active",
      ExpressionAttributeValues: {
        ":metadata": "METADATA",
        ":active": true
      }
    }));

    logger.info(`Found ${assets?.length || 0} active assets`);

    // Send one message per asset to SQS
    const promises = (assets || []).map(asset =>
      sqs.send(new SendMessageCommand({
        QueueUrl: QUEUE_URL,
        MessageBody: JSON.stringify({
          symbol: asset.symbol,
          date: new Date().toISOString().split('T')[0]
        }),
        MessageGroupId: asset.symbol,
        MessageDeduplicationId: `${asset.symbol}-${Date.now()}`
      }))
    );

    await Promise.all(promises);

    logger.info(`Queued ${promises.length} assets for ingestion`);

    return {
      statusCode: 200,
      body: JSON.stringify({
        assetsQueued: promises.length,
        timestamp: new Date().toISOString()
      })
    };
  } catch (error) {
    logger.error("Failed to schedule ingestion", { error });
    throw error;
  }
}
```

#### 2.4 Implement Process Ingestion Lambda

**File:** `functions/processIngestion/index.ts`

```typescript
import { SQSEvent } from "aws-lambda";
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, UpdateCommand } from "@aws-sdk/lib-dynamodb";
import { TimestreamWriteClient, WriteRecordsCommand } from "@aws-sdk/client-timestream-write";
import { SecretsManagerClient, GetSecretValueCommand } from "@aws-sdk/client-secrets-manager";
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";
import { Logger } from "@aws-lambda-powertools/logger";
import { fetchPolygonData, calculateVolatility } from "./polygon";

const dynamodb = DynamoDBDocumentClient.from(new DynamoDBClient({}));
const timestream = new TimestreamWriteClient({});
const secretsManager = new SecretsManagerClient({});
const s3 = new S3Client({});
const logger = new Logger({ serviceName: "processIngestion" });

const ASSETS_TABLE = process.env.ASSETS_TABLE_NAME!;
const TIMESTREAM_DB = process.env.TIMESTREAM_DB_NAME!;
const TIMESTREAM_TABLE = process.env.TIMESTREAM_TABLE_NAME!;
const ASSETS_BUCKET = process.env.ASSETS_BUCKET_NAME!;
const POLYGON_API_KEY_SECRET = process.env.POLYGON_API_KEY_SECRET!;

// Rate limiter state (persists across invocations in same container)
let lastCallTime = 0;
const CALLS_PER_MINUTE = 5;
const INTERVAL_MS = 60000 / CALLS_PER_MINUTE; // 12 seconds

async function rateLimitedFetch(url: string, apiKey: string) {
  const now = Date.now();
  const timeSinceLastCall = now - lastCallTime;

  if (timeSinceLastCall < INTERVAL_MS) {
    const waitTime = INTERVAL_MS - timeSinceLastCall;
    logger.debug(`Rate limiting: waiting ${waitTime}ms`);
    await new Promise(resolve => setTimeout(resolve, waitTime));
  }

  lastCallTime = Date.now();
  return fetchPolygonData(url, apiKey);
}

async function getPolygonApiKey(): Promise<string> {
  const { SecretString } = await secretsManager.send(
    new GetSecretValueCommand({ SecretId: POLYGON_API_KEY_SECRET })
  );
  return SecretString!;
}

export async function handler(event: SQSEvent) {
  const apiKey = await getPolygonApiKey();

  for (const record of event.Records) {
    const { symbol, date } = JSON.parse(record.body);
    logger.info(`Processing ingestion for ${symbol} on ${date}`);

    try {
      // Fetch data from Polygon.io (rate-limited)
      const endDate = new Date(date);
      const startDate = new Date(endDate);
      startDate.setDate(startDate.getDate() - 365); // 1 year of data

      const url = `https://api.polygon.io/v2/aggs/ticker/${symbol}/range/1/day/${startDate.toISOString().split('T')[0]}/${date}?adjusted=true&sort=asc&limit=50000`;

      const data = await rateLimitedFetch(url, apiKey);

      // Store raw data in S3
      await s3.send(new PutObjectCommand({
        Bucket: ASSETS_BUCKET,
        Key: `polygon-raw/${symbol}/${date}.json`,
        Body: JSON.stringify(data),
        ContentType: "application/json"
      }));

      // Process and store in Timestream
      const timestreamRecords = data.results.map((bar: any) => ({
        Dimensions: [
          { Name: "symbol", Value: symbol }
        ],
        MeasureName: "price_data",
        MeasureValueType: "MULTI",
        MeasureValues: [
          { Name: "open", Value: String(bar.o), Type: "DOUBLE" },
          { Name: "high", Value: String(bar.h), Type: "DOUBLE" },
          { Name: "low", Value: String(bar.l), Type: "DOUBLE" },
          { Name: "close", Value: String(bar.c), Type: "DOUBLE" },
          { Name: "volume", Value: String(bar.v), Type: "BIGINT" }
        ],
        Time: String(bar.t),
        TimeUnit: "MILLISECONDS"
      }));

      await timestream.send(new WriteRecordsCommand({
        DatabaseName: TIMESTREAM_DB,
        TableName: TIMESTREAM_TABLE,
        Records: timestreamRecords
      }));

      // Calculate volatilities
      const returns = data.results.map((bar: any, i: number) => {
        if (i === 0) return 0;
        return Math.log(bar.c / data.results[i-1].c);
      });

      const vol7Day = calculateVolatility(returns.slice(-7));
      const vol30Day = calculateVolatility(returns.slice(-30));
      const vol90Day = calculateVolatility(returns.slice(-90));
      const vol1Year = calculateVolatility(returns);

      // Update DynamoDB
      await dynamodb.send(new UpdateCommand({
        TableName: ASSETS_TABLE,
        Key: { PK: `ASSET#${symbol}`, SK: "METADATA" },
        UpdateExpression: "SET volatility7Day = :v7, volatility30Day = :v30, volatility90Day = :v90, volatility1Year = :v1y, lastUpdated = :updated",
        ExpressionAttributeValues: {
          ":v7": vol7Day,
          ":v30": vol30Day,
          ":v90": vol90Day,
          ":v1y": vol1Year,
          ":updated": new Date().toISOString()
        }
      }));

      logger.info(`Successfully processed ${symbol}`, {
        bars: data.results.length,
        vol30Day
      });
    } catch (error) {
      logger.error(`Failed to process ${symbol}`, { error });
      throw error; // Will retry and eventually go to DLQ
    }
  }

  return {
    batchItemFailures: [] // All succeeded
  };
}
```

**File:** `functions/processIngestion/polygon.ts`

```typescript
export async function fetchPolygonData(url: string, apiKey: string) {
  const response = await fetch(`${url}&apiKey=${apiKey}`);

  if (!response.ok) {
    throw new Error(`Polygon API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

export function calculateVolatility(returns: number[]): number {
  if (returns.length < 2) return 0;

  const mean = returns.reduce((sum, r) => sum + r, 0) / returns.length;
  const variance = returns.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / (returns.length - 1);
  const stdDev = Math.sqrt(variance);

  // Annualize (252 trading days)
  return stdDev * Math.sqrt(252);
}
```

#### 2.5 Test Data Ingestion

```bash
# Deploy updated infrastructure
pnpm sst deploy --stage dev

# Manually trigger ingestion for testing
aws lambda invoke \
  --function-name portfolio-optimizer-dev-ScheduleIngestion \
  --payload '{}' \
  response.json

# Check SQS queue
aws sqs get-queue-attributes \
  --queue-url <QUEUE_URL> \
  --attribute-names ApproximateNumberOfMessages

# Monitor Lambda logs
aws logs tail /aws/lambda/portfolio-optimizer-dev-ProcessIngestion --follow
```

**Acceptance Criteria:**
- [ ] EventBridge rule created
- [ ] SQS queue receives messages
- [ ] ProcessIngestion respects rate limit (12 seconds between calls)
- [ ] Data written to Timestream
- [ ] Volatility updated in DynamoDB
- [ ] Failed messages go to DLQ after 3 attempts
- [ ] No 429 (rate limit) errors from Polygon.io

---

## PHASE 3: API Implementation

### Goal
Implement all public API endpoints for the client application.

### Steps

#### 3.1 Create Shared Utilities

**File:** `functions/shared/types.ts`

```typescript
// Define all TypeScript interfaces from project-prd.md
export interface Asset {
  symbol: string;
  name: string;
  category: string;
  assetClass: string;
  currentImpliedVol30Day: number;
  volatility30Day: number;
  expectedReturn: number;
  sharpeRatio: number;
  lastUpdated: string;
}

export interface AssetDetail extends Asset {
  volatility7Day: number;
  volatility90Day: number;
  volatility1Year: number;
  volatilityLongTerm: number;
  tailRiskFactor: number;
  maxDrawdown1Year: number;
  maxDrawdown5Year: number;
  correlationBreakdownRisk: number;
  dataQuality: "HIGH" | "MEDIUM" | "LOW";
  createdAt: string;
  updatedAt: string;
}

// ... (continue with all types from PRD)
```

**File:** `functions/shared/errors.ts`

```typescript
export class APIError extends Error {
  constructor(
    public code: string,
    message: string,
    public details?: Record<string, any>
  ) {
    super(message);
    this.name = "APIError";
  }
}

export function errorResponse(error: any, requestId: string) {
  if (error instanceof APIError) {
    return {
      statusCode: 400,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        error: {
          code: error.code,
          message: error.message,
          details: error.details
        },
        requestId
      })
    };
  }

  // Unknown error
  console.error("Unexpected error:", error);
  return {
    statusCode: 500,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      error: {
        code: "INTERNAL_ERROR",
        message: "An unexpected error occurred"
      },
      requestId
    })
  };
}
```

**File:** `functions/shared/validation.ts`

```typescript
import { APIError } from "./errors";

export function validateSymbol(symbol: string): string {
  if (!symbol || typeof symbol !== "string") {
    throw new APIError("INVALID_REQUEST", "Symbol is required");
  }

  const cleaned = symbol.trim().toUpperCase();

  if (cleaned.length > 10) {
    throw new APIError("INVALID_REQUEST", "Symbol must be 10 characters or less");
  }

  return cleaned;
}

export function validateLimit(limit?: string): number {
  if (!limit) return 100;

  const parsed = parseInt(limit, 10);

  if (isNaN(parsed) || parsed < 1 || parsed > 500) {
    throw new APIError("INVALID_REQUEST", "Limit must be between 1 and 500");
  }

  return parsed;
}

// ... (continue with other validators)
```

#### 3.2 Implement GET /assets

**File:** `functions/getAssets/index.ts`

```typescript
import { APIGatewayProxyEvent, APIGatewayProxyResult } from "aws-lambda";
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, QueryCommand, ScanCommand } from "@aws-sdk/lib-dynamodb";
import { Logger } from "@aws-lambda-powertools/logger";
import { Metrics, MetricUnits } from "@aws-lambda-powertools/metrics";
import { validateLimit } from "../shared/validation";
import { errorResponse } from "../shared/errors";
import { Asset } from "../shared/types";

const dynamodb = DynamoDBDocumentClient.from(new DynamoDBClient({}));
const logger = new Logger({ serviceName: "getAssets" });
const metrics = new Metrics({ namespace: "PortfolioOptimizer" });

const ASSETS_TABLE = process.env.ASSETS_TABLE_NAME!;

export async function handler(event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> {
  const requestId = event.requestContext.requestId;
  logger.info("Processing getAssets request", { requestId });

  metrics.addMetric("ApiRequest", MetricUnits.Count, 1);

  try {
    const { category, assetClass, limit: limitParam, cursor } = event.queryStringParameters || {};
    const limit = validateLimit(limitParam);

    let result;

    if (category) {
      // Query using CategoryIndex GSI
      result = await dynamodb.send(new QueryCommand({
        TableName: ASSETS_TABLE,
        IndexName: "CategoryIndex",
        KeyConditionExpression: "category = :category",
        ExpressionAttributeValues: {
          ":category": category
        },
        Limit: limit,
        ExclusiveStartKey: cursor ? JSON.parse(Buffer.from(cursor, "base64").toString()) : undefined
      }));
    } else if (assetClass) {
      // Query using AssetClassIndex GSI
      result = await dynamodb.send(new QueryCommand({
        TableName: ASSETS_TABLE,
        IndexName: "AssetClassIndex",
        KeyConditionExpression: "assetClass = :assetClass",
        ExpressionAttributeValues: {
          ":assetClass": assetClass
        },
        Limit: limit,
        ScanIndexForward: false, // Sort by sharpeRatio descending
        ExclusiveStartKey: cursor ? JSON.parse(Buffer.from(cursor, "base64").toString()) : undefined
      }));
    } else {
      // Full scan
      result = await dynamodb.send(new ScanCommand({
        TableName: ASSETS_TABLE,
        FilterExpression: "SK = :metadata",
        ExpressionAttributeValues: {
          ":metadata": "METADATA"
        },
        Limit: limit,
        ExclusiveStartKey: cursor ? JSON.parse(Buffer.from(cursor, "base64").toString()) : undefined
      }));
    }

    const assets: Asset[] = (result.Items || []).map(item => ({
      symbol: item.symbol,
      name: item.name,
      category: item.category,
      assetClass: item.assetClass,
      currentImpliedVol30Day: item.currentImpliedVol30Day,
      volatility30Day: item.volatility30Day,
      expectedReturn: item.expectedReturn,
      sharpeRatio: item.sharpeRatio,
      lastUpdated: item.lastUpdated
    }));

    const response = {
      assets,
      nextCursor: result.LastEvaluatedKey
        ? Buffer.from(JSON.stringify(result.LastEvaluatedKey)).toString("base64")
        : undefined,
      total: assets.length
    };

    metrics.addMetric("ApiSuccess", MetricUnits.Count, 1);

    return {
      statusCode: 200,
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "public, max-age=300" // Cache for 5 minutes
      },
      body: JSON.stringify(response)
    };
  } catch (error) {
    metrics.addMetric("ApiError", MetricUnits.Count, 1);
    logger.error("Failed to get assets", { error });
    return errorResponse(error, requestId);
  }
}
```

#### 3.3 Implement Remaining Endpoints

Create similar Lambda functions for:
- `functions/getAsset/index.ts` - GET /assets/{symbol}
- `functions/getVolatility/index.ts` - GET /volatility/{symbol}
- `functions/calculateCorrelation/index.ts` - POST /calculate/correlation
- `functions/calculateKelly/index.ts` - POST /calculate/kelly

Follow the same pattern as getAssets with:
- Type-safe interfaces
- Input validation
- Error handling
- Logging & metrics
- Appropriate caching headers

#### 3.4 Configure API Gateway Routes

**Update:** `infra/api.ts`

```typescript
// Add after Lambda function definitions

// API Routes
export const getAssetsIntegration = new aws.apigatewayv2.Integration("GetAssetsIntegration", {
  apiId: httpApi.id,
  integrationType: "AWS_PROXY",
  integrationUri: getAssetsFunction.arn,
  payloadFormatVersion: "2.0"
});

export const getAssetsRoute = new aws.apigatewayv2.Route("GetAssetsRoute", {
  apiId: httpApi.id,
  routeKey: "GET /assets",
  target: pulumi.interpolate`integrations/${getAssetsIntegration.id}`
});

export const getAssetsPermission = new aws.lambda.Permission("GetAssetsPermission", {
  action: "lambda:InvokeFunction",
  function: getAssetsFunction.name,
  principal: "apigateway.amazonaws.com",
  sourceArn: pulumi.interpolate`${httpApi.executionArn}/*/*`
});

// Repeat for all other routes...
```

#### 3.5 Test API Endpoints

```bash
# Deploy API
pnpm sst deploy --stage dev

# Get API URL
export API_URL=$(aws cloudformation describe-stacks \
  --stack-name portfolio-optimizer-dev \
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
  --output text)

# Test GET /assets
curl "$API_URL/assets?limit=5"

# Test GET /assets/{symbol}
curl "$API_URL/assets/SPY"

# Test POST /calculate/kelly
curl -X POST "$API_URL/calculate/kelly" \
  -H "Content-Type: application/json" \
  -d '{
    "assets": [{"symbol": "SPY"}, {"symbol": "TLT"}],
    "riskFreeRate": 0.03,
    "riskAversion": 5
  }'
```

**Acceptance Criteria:**
- [ ] All endpoints return 200 for valid requests
- [ ] Validation errors return 400 with clear messages
- [ ] Response times < 2 seconds (P95)
- [ ] Responses match TypeScript interfaces
- [ ] CORS headers allow client origin

---

## PHASE 4: Admin Endpoints & Authentication

### Goal
Secure admin endpoints with API key authentication.

### Steps

#### 4.1 Generate and Store Admin API Key

```bash
# Generate secure API key
ADMIN_API_KEY=$(openssl rand -hex 32)

# Store in Secrets Manager
aws secretsmanager create-secret \
  --name /portfolio-optimizer/admin-api-key \
  --secret-string "$ADMIN_API_KEY" \
  --region us-east-1

# Save to secure location for later use
echo "$ADMIN_API_KEY" > .admin-api-key
chmod 600 .admin-api-key

# Add .admin-api-key to .gitignore
echo ".admin-api-key" >> .gitignore
```

#### 4.2 Implement Lambda Authorizer

**File:** `functions/adminAuthorizer/index.ts`

```typescript
import { APIGatewayAuthorizerResult, APIGatewayTokenAuthorizerEvent } from "aws-lambda";
import { SecretsManagerClient, GetSecretValueCommand } from "@aws-sdk/client-secrets-manager";

const secretsManager = new SecretsManagerClient({});

let cachedApiKey: string | null = null;

async function getApiKey(): Promise<string> {
  if (cachedApiKey) return cachedApiKey;

  const { SecretString } = await secretsManager.send(
    new GetSecretValueCommand({
      SecretId: "/portfolio-optimizer/admin-api-key"
    })
  );

  cachedApiKey = SecretString!;
  return cachedApiKey;
}

export async function handler(
  event: APIGatewayTokenAuthorizerEvent
): Promise<APIGatewayAuthorizerResult> {
  const token = event.authorizationToken;
  const apiKey = await getApiKey();

  // Check for Bearer token or x-api-key header format
  const providedKey = token.startsWith("Bearer ")
    ? token.substring(7)
    : token;

  const isValid = providedKey === apiKey;

  return {
    principalId: "admin",
    policyDocument: {
      Version: "2012-10-17",
      Statement: [{
        Action: "execute-api:Invoke",
        Effect: isValid ? "Allow" : "Deny",
        Resource: event.methodArn
      }]
    }
  };
}
```

#### 4.3 Implement Admin Endpoints

**File:** `functions/admin/updateAssets.ts`

```typescript
import { APIGatewayProxyEvent, APIGatewayProxyResult } from "aws-lambda";
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, UpdateCommand } from "@aws-sdk/lib-dynamodb";
import { Logger } from "@aws-lambda-powertools/logger";
import { errorResponse } from "../shared/errors";

const dynamodb = DynamoDBDocumentClient.from(new DynamoDBClient({}));
const logger = new Logger({ serviceName: "adminUpdateAssets" });

const ASSETS_TABLE = process.env.ASSETS_TABLE_NAME!;

export async function handler(event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> {
  const requestId = event.requestContext.requestId;
  logger.info("Admin update assets request", { requestId });

  try {
    const body = JSON.parse(event.body || "{}");
    const { symbol, ...updates } = body;

    if (!symbol) {
      throw new Error("Symbol is required");
    }

    // Build update expression dynamically
    const updateExpressions: string[] = [];
    const expressionAttributeNames: Record<string, string> = {};
    const expressionAttributeValues: Record<string, any> = {};

    Object.entries(updates).forEach(([key, value], index) => {
      updateExpressions.push(`#field${index} = :value${index}`);
      expressionAttributeNames[`#field${index}`] = key;
      expressionAttributeValues[`:value${index}`] = value;
    });

    // Add updatedAt timestamp
    updateExpressions.push("#updatedAt = :updatedAt");
    expressionAttributeNames["#updatedAt"] = "updatedAt";
    expressionAttributeValues[":updatedAt"] = new Date().toISOString();

    await dynamodb.send(new UpdateCommand({
      TableName: ASSETS_TABLE,
      Key: { PK: `ASSET#${symbol}`, SK: "METADATA" },
      UpdateExpression: `SET ${updateExpressions.join(", ")}`,
      ExpressionAttributeNames: expressionAttributeNames,
      ExpressionAttributeValues: expressionAttributeValues
    }));

    logger.info(`Updated asset ${symbol}`, { updates });

    return {
      statusCode: 200,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        success: true,
        symbol,
        updated: Object.keys(updates)
      })
    };
  } catch (error) {
    logger.error("Failed to update asset", { error });
    return errorResponse(error, requestId);
  }
}
```

#### 4.4 Configure Admin Routes with Authorizer

**Update:** `infra/api.ts`

```typescript
// Create authorizer
export const adminAuthorizer = new aws.apigatewayv2.Authorizer("AdminAuthorizer", {
  apiId: httpApi.id,
  authorizerType: "REQUEST",
  authorizerUri: adminAuthorizerFunction.invokeArn,
  identitySources: ["$request.header.x-api-key"],
  name: "admin-authorizer",
  authorizerPayloadFormatVersion: "1.0",
  authorizerResultTtlInSeconds: 300
});

// Admin routes with authorizer
export const adminUpdateAssetsRoute = new aws.apigatewayv2.Route("AdminUpdateAssetsRoute", {
  apiId: httpApi.id,
  routeKey: "POST /admin/assets",
  target: pulumi.interpolate`integrations/${adminUpdateAssetsIntegration.id}`,
  authorizationType: "CUSTOM",
  authorizerId: adminAuthorizer.id
});
```

#### 4.5 Test Admin Endpoints

```bash
# Load admin API key
ADMIN_API_KEY=$(cat .admin-api-key)

# Test without API key (should fail)
curl -X POST "$API_URL/admin/assets" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "SPY", "isActive": true}'

# Expected: 401 Unauthorized

# Test with API key (should succeed)
curl -X POST "$API_URL/admin/assets" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $ADMIN_API_KEY" \
  -d '{"symbol": "SPY", "tailRiskFactor": 2.5}'

# Expected: 200 with success response
```

**Acceptance Criteria:**
- [ ] Admin endpoints reject requests without API key
- [ ] Valid API key grants access
- [ ] Update operations modify DynamoDB records
- [ ] All admin operations logged with requester info

---

## PHASE 5: Client Application Updates

### Goal
Update the SolidJS client to use the new API and add enhanced features.

### Steps

#### 5.1 Create API Client Service

**File:** `src/services/api.ts`

```typescript
import type {
  Asset,
  AssetDetail,
  GetAssetsQuery,
  VolatilityHistory,
  CorrelationRequest,
  CorrelationResponse,
  KellyRequest,
  KellyResponse
} from "./types";

class APIError extends Error {
  constructor(public code: string, message: string, public details?: any) {
    super(message);
    this.name = "APIError";
  }
}

class PortfolioAPI {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private async fetch<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new APIError(error.error.code, error.error.message, error.error.details);
    }

    return response.json();
  }

  async getAssets(params?: GetAssetsQuery): Promise<{ assets: Asset[]; nextCursor?: string; total: number }> {
    const query = new URLSearchParams(params as any).toString();
    return this.fetch(`/assets${query ? `?${query}` : ""}`);
  }

  async getAsset(symbol: string): Promise<AssetDetail> {
    return this.fetch(`/assets/${symbol}`);
  }

  async getVolatility(symbol: string, startDate?: string, endDate?: string): Promise<VolatilityHistory> {
    const params = new URLSearchParams();
    if (startDate) params.set("startDate", startDate);
    if (endDate) params.set("endDate", endDate);
    return this.fetch(`/volatility/${symbol}${params.toString() ? `?${params}` : ""}`);
  }

  async calculateCorrelation(request: CorrelationRequest): Promise<CorrelationResponse> {
    return this.fetch("/calculate/correlation", {
      method: "POST",
      body: JSON.stringify(request)
    });
  }

  async calculateKelly(request: KellyRequest): Promise<KellyResponse> {
    return this.fetch("/calculate/kelly", {
      method: "POST",
      body: JSON.stringify(request)
    });
  }
}

// Export singleton instance
export const api = new PortfolioAPI(
  import.meta.env.VITE_API_URL || "https://api.kellyportfolios.com"
);
```

**File:** `src/services/types.ts`

Copy all TypeScript interfaces from `functions/shared/types.ts` to ensure type consistency.

#### 5.2 Create Asset Search Component

**File:** `src/components/AssetSearch.tsx`

```typescript
import { createSignal, createEffect, For, Show } from "solid-js";
import { api } from "~/services/api";
import type { Asset } from "~/services/types";
import { Icon } from "./Icon";

interface AssetSearchProps {
  onSelect: (asset: Asset) => void;
  excludeSymbols?: string[];
}

export function AssetSearch(props: AssetSearchProps) {
  const [query, setQuery] = createSignal("");
  const [results, setResults] = createSignal<Asset[]>([]);
  const [isLoading, setIsLoading] = createSignal(false);
  const [showResults, setShowResults] = createSignal(false);

  let debounceTimer: number | undefined;

  createEffect(() => {
    const q = query();

    if (q.length < 2) {
      setResults([]);
      setShowResults(false);
      return;
    }

    clearTimeout(debounceTimer);

    debounceTimer = window.setTimeout(async () => {
      setIsLoading(true);
      try {
        const { assets } = await api.getAssets({ limit: 20 });
        const filtered = assets.filter(
          a =>
            (a.symbol.toLowerCase().includes(q.toLowerCase()) ||
              a.name.toLowerCase().includes(q.toLowerCase())) &&
            !props.excludeSymbols?.includes(a.symbol)
        );
        setResults(filtered);
        setShowResults(true);
      } catch (error) {
        console.error("Search failed:", error);
      } finally {
        setIsLoading(false);
      }
    }, 300);
  });

  const handleSelect = (asset: Asset) => {
    props.onSelect(asset);
    setQuery("");
    setResults([]);
    setShowResults(false);
  };

  return (
    <div class="relative">
      <div class="relative">
        <input
          type="text"
          value={query()}
          onInput={(e) => setQuery(e.target.value)}
          placeholder="Search by symbol or name..."
          class="input-field text-lg pr-12"
          data-testid="asset-search"
        />
        <div class="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400">
          <Show when={isLoading()} fallback={<Icon name="search" size={5} />}>
            <Icon name="spinner" size={5} class="animate-spin" />
          </Show>
        </div>
      </div>

      <Show when={showResults() && results().length > 0}>
        <div class="absolute z-10 w-full mt-2 bg-white rounded-xl shadow-lg border border-slate-200 max-h-96 overflow-y-auto">
          <For each={results()}>
            {(asset) => (
              <button
                type="button"
                onClick={() => handleSelect(asset)}
                class="w-full px-4 py-3 text-left hover:bg-slate-50 transition-colors border-b border-slate-100 last:border-b-0"
                data-testid="search-result"
              >
                <div class="flex items-center justify-between">
                  <div>
                    <div class="font-semibold text-slate-900">{asset.symbol}</div>
                    <div class="text-sm text-slate-600">{asset.name}</div>
                  </div>
                  <div class="text-right">
                    <div class="text-sm text-slate-600">Vol: {(asset.volatility30Day * 100).toFixed(1)}%</div>
                    <div class="text-sm text-emerald-600">Return: {(asset.expectedReturn * 100).toFixed(1)}%</div>
                  </div>
                </div>
              </button>
            )}
          </For>
        </div>
      </Show>
    </div>
  );
}
```

#### 5.3 Create Volatility Chart Component

**File:** `src/components/VolatilityChart.tsx`

Use Chart.js or similar library to display historical volatility.

```typescript
import { createSignal, createEffect, onMount } from "solid-js";
import { api } from "~/services/api";
import type { VolatilityHistory } from "~/services/types";

interface VolatilityChartProps {
  symbol: string;
  days?: 7 | 30 | 90 | 365;
}

export function VolatilityChart(props: VolatilityChartProps) {
  const [data, setData] = createSignal<VolatilityHistory | null>(null);
  const [isLoading, setIsLoading] = createSignal(true);
  let canvas: HTMLCanvasElement | undefined;

  createEffect(async () => {
    setIsLoading(true);
    try {
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - (props.days || 30));

      const volatility = await api.getVolatility(
        props.symbol,
        startDate.toISOString()
      );

      setData(volatility);
    } catch (error) {
      console.error("Failed to load volatility data:", error);
    } finally {
      setIsLoading(false);
    }
  });

  onMount(() => {
    // Initialize Chart.js chart
    // Implementation depends on charting library choice
  });

  return (
    <div class="card p-6">
      <h3 class="text-lg font-semibold mb-4">Volatility History</h3>
      <canvas ref={canvas} />
    </div>
  );
}
```

#### 5.4 Update Calculator Page

**File:** `src/routes/calculator.tsx`

Update the calculator to use AssetSearch and the API:

```typescript
// Replace manual asset entry with AssetSearch
<AssetSearch
  onSelect={handleAssetSelected}
  excludeSymbols={selectedAssets().map(a => a.symbol)}
/>

// Use API for Kelly calculation
async function optimizePortfolio() {
  setIsOptimizing(true);
  try {
    const result = await api.calculateKelly({
      assets: selectedAssets().map(a => ({ symbol: a.symbol })),
      riskFreeRate: settings.riskFreeRate,
      riskAversion: settings.riskAversion,
      includeBlackSwan: blackSwanSettings.enabled,
      blackSwanMultiplier: blackSwanSettings.multiplier
    });

    setOptimizationResult(result);
  } catch (error) {
    console.error("Optimization failed:", error);
  } finally {
    setIsOptimizing(false);
  }
}
```

#### 5.5 Add Environment Configuration

**File:** `.env.development`
```
VITE_API_URL=https://dev-api.kellyportfolios.com
```

**File:** `.env.production`
```
VITE_API_URL=https://api.kellyportfolios.com
```

#### 5.6 Test Client Updates

```bash
# Run dev server
pnpm dev

# Open http://localhost:5173/calculator

# Test workflow:
# 1. Search for "SPY"
# 2. Select SPY from results
# 3. Search for "TLT"
# 4. Select TLT
# 5. Click "Optimize"
# 6. Verify results display
```

**Acceptance Criteria:**
- [ ] Asset search returns results in <500ms
- [ ] Selected assets display correctly
- [ ] Optimize button calls API
- [ ] Results display with allocations
- [ ] Loading states work correctly
- [ ] Error messages display for failed requests

---

## PHASE 6: Initial Data Seeding

### Goal
Populate the database with 100 ETFs and their historical data.

### Steps

#### 6.1 Create Seed Script

**File:** `scripts/seed-assets.ts`

```typescript
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, PutCommand } from "@aws-sdk/lib-dynamodb";

const dynamodb = DynamoDBDocumentClient.from(new DynamoDBClient({}));
const TABLE_NAME = "portfolio-optimizer-dev-assets";

const assets = [
  // Large Cap Equity
  { symbol: "SPY", name: "SPDR S&P 500 ETF Trust", category: "Large Cap", assetClass: "Equity" },
  { symbol: "VOO", name: "Vanguard S&P 500 ETF", category: "Large Cap", assetClass: "Equity" },
  { symbol: "IVV", name: "iShares Core S&P 500 ETF", category: "Large Cap", assetClass: "Equity" },
  { symbol: "QQQ", name: "Invesco QQQ Trust", category: "Technology", assetClass: "Equity" },
  { symbol: "QQQM", name: "Invesco NASDAQ 100 ETF", category: "Technology", assetClass: "Equity" },
  { symbol: "VTI", name: "Vanguard Total Stock Market ETF", category: "Total Market", assetClass: "Equity" },
  { symbol: "DIA", name: "SPDR Dow Jones Industrial Average ETF", category: "Large Cap", assetClass: "Equity" },
  { symbol: "IWM", name: "iShares Russell 2000 ETF", category: "Small Cap", assetClass: "Equity" },

  // Bonds
  { symbol: "AGG", name: "iShares Core U.S. Aggregate Bond ETF", category: "Bonds", assetClass: "Fixed Income" },
  { symbol: "BND", name: "Vanguard Total Bond Market ETF", category: "Bonds", assetClass: "Fixed Income" },
  { symbol: "TLT", name: "iShares 20+ Year Treasury Bond ETF", category: "Bonds", assetClass: "Fixed Income" },
  { symbol: "IEF", name: "iShares 7-10 Year Treasury Bond ETF", category: "Bonds", assetClass: "Fixed Income" },
  { symbol: "SHY", name: "iShares 1-3 Year Treasury Bond ETF", category: "Bonds", assetClass: "Fixed Income" },

  // Commodities
  { symbol: "GLD", name: "SPDR Gold Shares", category: "Commodities", assetClass: "Commodity" },
  { symbol: "IAU", name: "iShares Gold Trust", category: "Commodities", assetClass: "Commodity" },
  { symbol: "SLV", name: "iShares Silver Trust", category: "Commodities", assetClass: "Commodity" },

  // International
  { symbol: "VEA", name: "Vanguard FTSE Developed Markets ETF", category: "International", assetClass: "Equity" },
  { symbol: "IEFA", name: "iShares Core MSCI EAFE ETF", category: "International", assetClass: "Equity" },
  { symbol: "VWO", name: "Vanguard FTSE Emerging Markets ETF", category: "Emerging Markets", assetClass: "Equity" },
  { symbol: "IEMG", name: "iShares Core MSCI Emerging Markets ETF", category: "Emerging Markets", assetClass: "Equity" },

  // ... (add remaining 80 ETFs from PRD)
];

async function seedAsset(asset: typeof assets[0]) {
  const now = new Date().toISOString();

  await dynamodb.send(new PutCommand({
    TableName: TABLE_NAME,
    Item: {
      PK: `ASSET#${asset.symbol}`,
      SK: "METADATA",
      symbol: asset.symbol,
      name: asset.name,
      category: asset.category,
      assetClass: asset.assetClass,
      currentImpliedVol30Day: 0,
      volatility7Day: 0,
      volatility30Day: 0,
      volatility90Day: 0,
      volatility1Year: 0,
      volatilityLongTerm: 0,
      expectedReturn: 0,
      sharpeRatio: 0,
      tailRiskFactor: 2.0,
      maxDrawdown1Year: 0,
      maxDrawdown5Year: 0,
      correlationBreakdownRisk: 0.1,
      isActive: true,
      dataQuality: "LOW",
      createdAt: now,
      updatedAt: now,
      lastUpdated: now
    }
  }));

  console.log(`Seeded ${asset.symbol}`);
}

async function main() {
  console.log(`Seeding ${assets.length} assets...`);

  for (const asset of assets) {
    await seedAsset(asset);
  }

  console.log("Seeding complete!");
}

main().catch(console.error);
```

#### 6.2 Run Seed Script

```bash
# Make script executable
chmod +x scripts/seed-assets.ts

# Run with tsx
pnpm tsx scripts/seed-assets.ts

# Verify seeding
aws dynamodb scan \
  --table-name portfolio-optimizer-dev-assets \
  --select COUNT
```

#### 6.3 Trigger Initial Data Ingestion

```bash
# Manually trigger ingestion for all assets
aws lambda invoke \
  --function-name portfolio-optimizer-dev-ScheduleIngestion \
  --payload '{}' \
  response.json

# Monitor progress
watch -n 10 'aws sqs get-queue-attributes \
  --queue-url <QUEUE_URL> \
  --attribute-names ApproximateNumberOfMessages'
```

**Note:** Full backfill will take ~20 days due to rate limits. For faster initial testing:
1. Reduce to 10-20 most popular ETFs
2. Or upgrade Polygon.io to paid tier temporarily

**Acceptance Criteria:**
- [ ] 100 assets in DynamoDB
- [ ] All assets have `isActive: true`
- [ ] Initial ingestion queued
- [ ] At least 5 assets have historical data

---

## PHASE 7: Testing & Optimization

### Goal
Comprehensive testing and performance optimization.

### Steps

#### 7.1 Write Unit Tests

**File:** `functions/getAssets/handler.test.ts`

```typescript
import { handler } from "./index";
import { mockClient } from "aws-sdk-client-mock";
import { DynamoDBDocumentClient, ScanCommand } from "@aws-sdk/lib-dynamodb";

const ddbMock = mockClient(DynamoDBDocumentClient);

describe("getAssets", () => {
  beforeEach(() => {
    ddbMock.reset();
  });

  it("should return assets", async () => {
    ddbMock.on(ScanCommand).resolves({
      Items: [
        {
          PK: "ASSET#SPY",
          SK: "METADATA",
          symbol: "SPY",
          name: "SPDR S&P 500 ETF Trust",
          category: "Large Cap",
          assetClass: "Equity",
          volatility30Day: 0.16,
          expectedReturn: 0.10,
          sharpeRatio: 0.85
        }
      ]
    });

    const event = {
      requestContext: { requestId: "test-123" },
      queryStringParameters: { limit: "10" }
    } as any;

    const response = await handler(event);

    expect(response.statusCode).toBe(200);
    const body = JSON.parse(response.body);
    expect(body.assets).toHaveLength(1);
    expect(body.assets[0].symbol).toBe("SPY");
  });

  it("should validate limit parameter", async () => {
    const event = {
      requestContext: { requestId: "test-123" },
      queryStringParameters: { limit: "1000" } // Exceeds max
    } as any;

    const response = await handler(event);

    expect(response.statusCode).toBe(400);
    const body = JSON.parse(response.body);
    expect(body.error.code).toBe("INVALID_REQUEST");
  });
});
```

Run tests:
```bash
pnpm test:unit
```

#### 7.2 Write Integration Tests

**File:** `tests/integration/api.test.ts`

```typescript
import { describe, it, expect } from "@jest/globals";

const API_URL = process.env.API_URL || "http://localhost:3000";

describe("Assets API Integration", () => {
  it("should fetch assets", async () => {
    const response = await fetch(`${API_URL}/assets?limit=10`);
    expect(response.status).toBe(200);

    const data = await response.json();
    expect(Array.isArray(data.assets)).toBe(true);
    expect(data.total).toBeGreaterThan(0);
  });

  it("should fetch single asset", async () => {
    const response = await fetch(`${API_URL}/assets/SPY`);
    expect(response.status).toBe(200);

    const data = await response.json();
    expect(data.symbol).toBe("SPY");
    expect(data.volatility30Day).toBeGreaterThan(0);
  });

  it("should calculate Kelly allocations", async () => {
    const response = await fetch(`${API_URL}/calculate/kelly`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        assets: [{ symbol: "SPY" }, { symbol: "TLT" }],
        riskFreeRate: 0.03,
        riskAversion: 5
      })
    });

    expect(response.status).toBe(200);

    const data = await response.json();
    expect(data.allocations).toHaveLength(2);
    expect(data.portfolioMetrics.expectedReturn).toBeGreaterThan(0);
  });
});
```

Run integration tests:
```bash
export API_URL=$(aws cloudformation describe-stacks \
  --stack-name portfolio-optimizer-dev \
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
  --output text)

pnpm test:integration
```

#### 7.3 Load Testing with Artillery

**File:** `artillery-config.yml`

```yaml
config:
  target: "{{ $processEnvironment.API_URL }}"
  phases:
    - duration: 60
      arrivalRate: 5
      name: "Warm up"
    - duration: 300
      arrivalRate: 20
      name: "Sustained load"
    - duration: 60
      arrivalRate: 50
      name: "Peak load"

scenarios:
  - name: "Browse assets"
    weight: 50
    flow:
      - get:
          url: "/assets?limit=20"
      - think: 2

  - name: "View asset details"
    weight: 30
    flow:
      - get:
          url: "/assets/{{ $randomString() | pick(['SPY','QQQ','TLT','AGG','GLD']) }}"
      - think: 3

  - name: "Calculate Kelly"
    weight: 20
    flow:
      - post:
          url: "/calculate/kelly"
          json:
            assets:
              - symbol: "SPY"
              - symbol: "TLT"
            riskFreeRate: 0.03
            riskAversion: 5
      - think: 5
```

Run load test:
```bash
export API_URL=https://dev-api.kellyportfolios.com
artillery run artillery-config.yml --output report.json
artillery report report.json
```

#### 7.4 Performance Optimization

**Optimization Checklist:**
- [ ] Add DynamoDB on-demand pricing or provision appropriately
- [ ] Enable API Gateway caching for GET /assets (5-minute TTL)
- [ ] Add provisioned concurrency for frequently-called Lambdas
- [ ] Optimize Lambda bundle sizes (use esbuild)
- [ ] Add CloudFront in front of API Gateway
- [ ] Implement response compression

#### 7.5 Cost Optimization

**Monitor costs:**
```bash
# Check current month costs
aws ce get-cost-and-usage \
  --time-period Start=$(date -u +%Y-%m-01),End=$(date -u +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE
```

**Expected costs (dev):**
- Lambda: $0-5/month (free tier)
- DynamoDB: $0-10/month
- Timestream: $5-10/month
- API Gateway: $0-5/month
- Total: ~$20/month

**Acceptance Criteria:**
- [ ] 80%+ code coverage
- [ ] All integration tests pass
- [ ] Load test shows P95 latency < 2 seconds
- [ ] No errors under 50 RPS sustained load
- [ ] Monthly dev cost < $50

---

## PHASE 8: Production Deployment

### Goal
Deploy to production with monitoring, alarms, and documentation.

### Steps

#### 8.1 Production Infrastructure

```bash
# Deploy to production
pnpm sst deploy --stage production

# Verify deployment
export PROD_API_URL=$(aws cloudformation describe-stacks \
  --stack-name portfolio-optimizer-production \
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
  --output text)

curl "$PROD_API_URL/assets?limit=5"
```

#### 8.2 Custom Domain Setup

**Add to** `infra/api.ts`:

```typescript
// Custom domain for API
export const apiDomain = new aws.apigatewayv2.DomainName("ApiDomain", {
  domainName: "api.kellyportfolios.com",
  domainNameConfiguration: {
    certificateArn: acmCertificate.arn,
    endpointType: "REGIONAL",
    securityPolicy: "TLS_1_2"
  }
});

export const apiMapping = new aws.apigatewayv2.ApiMapping("ApiMapping", {
  apiId: httpApi.id,
  domainName: apiDomain.id,
  stage: apiStage.name
});

// Route 53 record
export const apiRecord = new aws.route53.Record("ApiRecord", {
  zoneId: hostedZoneId,
  name: "api.kellyportfolios.com",
  type: "A",
  aliases: [{
    name: apiDomain.domainNameConfiguration.targetDomainName,
    zoneId: apiDomain.domainNameConfiguration.hostedZoneId,
    evaluateTargetHealth: false
  }]
});
```

#### 8.3 Configure CloudWatch Alarms

**File:** `infra/monitoring.ts`

```typescript
import * as aws from "@pulumi/aws";

// High error rate alarm
export const highErrorRateAlarm = new aws.cloudwatch.MetricAlarm("HighErrorRateAlarm", {
  name: `portfolio-optimizer-${$app.stage}-high-error-rate`,
  comparisonOperator: "GreaterThanThreshold",
  evaluationPeriods: 2,
  metricName: "5XXError",
  namespace: "AWS/ApiGateway",
  period: 300,
  statistic: "Sum",
  threshold: 10,
  alarmDescription: "Alert when API has high error rate",
  alarmActions: [snsTopicArn],
  dimensions: {
    ApiName: httpApi.name
  }
});

// DLQ message alarm
export const dlqMessageAlarm = new aws.cloudwatch.MetricAlarm("DLQMessageAlarm", {
  name: `portfolio-optimizer-${$app.stage}-dlq-messages`,
  comparisonOperator: "GreaterThanThreshold",
  evaluationPeriods: 1,
  metricName: "ApproximateNumberOfMessagesVisible",
  namespace: "AWS/SQS",
  period: 300,
  statistic: "Average",
  threshold: 5,
  alarmDescription: "Alert when DLQ has messages",
  alarmActions: [snsTopicArn],
  dimensions: {
    QueueName: ingestionDLQ.name
  }
});

// High API latency alarm
export const highLatencyAlarm = new aws.cloudwatch.MetricAlarm("HighLatencyAlarm", {
  name: `portfolio-optimizer-${$app.stage}-high-latency`,
  comparisonOperator: "GreaterThanThreshold",
  evaluationPeriods: 2,
  extendedStatistic: "p95",
  metricName: "Latency",
  namespace: "AWS/ApiGateway",
  period: 300,
  threshold: 2000, // 2 seconds
  alarmDescription: "Alert when P95 latency exceeds 2 seconds",
  alarmActions: [snsTopicArn],
  dimensions: {
    ApiName: httpApi.name
  }
});

export const monitoring = {
  highErrorRateAlarm,
  dlqMessageAlarm,
  highLatencyAlarm
};
```

#### 8.4 Create CloudWatch Dashboard

**File:** `scripts/create-dashboard.ts`

```typescript
import { CloudWatchClient, PutDashboardCommand } from "@aws-sdk/client-cloudwatch";

const cloudwatch = new CloudWatchClient({});

const dashboardBody = {
  widgets: [
    {
      type: "metric",
      properties: {
        metrics: [
          ["AWS/ApiGateway", "Count", { stat: "Sum", label: "Total Requests" }],
          [".", "4XXError", { stat: "Sum", label: "Client Errors" }],
          [".", "5XXError", { stat: "Sum", label: "Server Errors" }]
        ],
        period: 300,
        stat: "Sum",
        region: "us-east-1",
        title: "API Requests",
        yAxis: { left: { min: 0 } }
      }
    },
    {
      type: "metric",
      properties: {
        metrics: [
          ["AWS/ApiGateway", "Latency", { stat: "p50" }],
          ["...", { stat: "p95" }],
          ["...", { stat: "p99" }]
        ],
        period: 300,
        region: "us-east-1",
        title: "API Latency (ms)",
        yAxis: { left: { min: 0 } }
      }
    },
    // Add more widgets for Lambda, DynamoDB, Timestream
  ]
};

async function createDashboard() {
  await cloudwatch.send(new PutDashboardCommand({
    DashboardName: "PortfolioOptimizerProduction",
    DashboardBody: JSON.stringify(dashboardBody)
  }));

  console.log("Dashboard created!");
}

createDashboard();
```

#### 8.5 Final Verification

**Production Checklist:**
- [ ] API accessible at api.kellyportfolios.com
- [ ] Client deployed to kellyportfolios.com
- [ ] SSL certificates valid
- [ ] All endpoints respond correctly
- [ ] CloudWatch alarms configured
- [ ] SNS notifications working
- [ ] Dashboard created
- [ ] Documentation complete
- [ ] Cost alerts configured
- [ ] Backup strategy in place

---

## Success Criteria

### Phase 1: Infrastructure
- ✅ DynamoDB, Timestream, S3 deployed
- ✅ API Gateway created
- ✅ Lambda functions scaffolded

### Phase 2: Data Ingestion
- ✅ Daily cron job triggers
- ✅ Rate limiting works (5 calls/min)
- ✅ Data stored in databases
- ✅ Failed jobs go to DLQ

### Phase 3: API
- ✅ All endpoints functional
- ✅ Response times < 2s (P95)
- ✅ Error handling works
- ✅ Type safety throughout

### Phase 4: Admin
- ✅ API key authentication works
- ✅ Admin endpoints secured
- ✅ Bulk updates functional

### Phase 5: Client
- ✅ Asset search works
- ✅ API integration complete
- ✅ Enhanced UI features
- ✅ Loading/error states

### Phase 6: Data
- ✅ 100 ETFs seeded
- ✅ Historical data backfilled
- ✅ Data quality HIGH

### Phase 7: Testing
- ✅ 80%+ code coverage
- ✅ Integration tests pass
- ✅ Load tests pass
- ✅ Cost < $50/month (dev)

### Phase 8: Production
- ✅ Production deployed
- ✅ Custom domains configured
- ✅ Alarms set up
- ✅ Monitoring in place

---

## Common Issues & Solutions

### Issue: Polygon.io 429 Rate Limit Errors

**Solution:**
```typescript
// Increase wait time between calls
const INTERVAL_MS = 15000; // 15 seconds instead of 12

// Or upgrade to paid tier
// Basic: $200/month for 500 calls/min
```

### Issue: Lambda Cold Starts

**Solution:**
```typescript
// Add provisioned concurrency for critical functions
new aws.lambda.ProvisionedConcurrencyConfig("GetAssetsProvisioned", {
  functionName: getAssetsFunction.name,
  qualifier: getAssetsFunction.version,
  provisionedConcurrentExecutions: 2
});
```

### Issue: Timestream Query Costs Too High

**Solution:**
```typescript
// Cache frequent queries in DynamoDB
// Add query result caching layer
// Limit time ranges in queries
```

### Issue: DynamoDB Throttling

**Solution:**
```bash
# Switch to on-demand pricing
aws dynamodb update-table \
  --table-name portfolio-optimizer-production-assets \
  --billing-mode PAY_PER_REQUEST

# Or increase provisioned capacity
```

---

## Next Steps After Completion

Once all 8 phases are complete:

1. **Gather User Feedback**: Share with beta users, collect feedback
2. **Iterate on Features**: Add most-requested features
3. **Expand Asset Coverage**: Add individual stocks, crypto, etc.
4. **Implement User Accounts**: Allow saving portfolios
5. **Add Premium Features**: Build monetization tier
6. **Mobile App**: Consider React Native or similar
7. **API for Developers**: Public API access

---

## Resources

- **Project PRD**: `project-prd.md`
- **High-Level PRD**: `highlevel-prd.md`
- **SST Documentation**: https://sst.dev/docs
- **Polygon.io API**: https://polygon.io/docs
- **AWS Lambda Powertools**: https://docs.powertools.aws.dev/lambda/typescript/latest/

---

## Final Notes

This is a comprehensive implementation plan designed to be followed linearly. Each phase builds on the previous one. Test thoroughly at each phase before proceeding.

The architecture is production-ready, scalable, and cost-effective. With proper implementation, the system should handle 10,000+ users with minimal operational overhead.

Good luck with the implementation! 🚀
