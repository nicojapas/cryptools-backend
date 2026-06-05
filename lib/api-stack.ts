import * as cdk from 'aws-cdk-lib';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as nodejs from 'aws-cdk-lib/aws-lambda-nodejs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';
import * as path from 'path';

const ALLOWED_ORIGINS = [
  'http://localhost:5173',
  'https://nicojapas.github.io',
];

export class ApiStack extends cdk.Stack {
  public readonly api: apigateway.RestApi;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // API Gateway with restricted CORS
    this.api = new apigateway.RestApi(this, 'CryptoolsApi', {
      restApiName: 'Cryptools API',
      defaultCorsPreflightOptions: {
        allowOrigins: ALLOWED_ORIGINS,
        allowMethods: ['GET', 'OPTIONS'],
        allowHeaders: ['Content-Type', 'X-Api-Key'],
      },
      apiKeySourceType: apigateway.ApiKeySourceType.HEADER,
    });

    // API Key
    const apiKey = new apigateway.ApiKey(this, 'CryptoolsApiKey', {
      apiKeyName: 'cryptools-api-key',
      description: 'API key for Cryptools frontend',
    });

    // Usage Plan
    const usagePlan = new apigateway.UsagePlan(this, 'CryptoolsUsagePlan', {
      name: 'CryptoolsUsagePlan',
      throttle: {
        rateLimit: 100,
        burstLimit: 200,
      },
      quota: {
        limit: 10000,
        period: apigateway.Period.DAY,
      },
    });

    usagePlan.addApiKey(apiKey);
    usagePlan.addApiStage({ stage: this.api.deploymentStage });

    // S3 bucket for caching (CDK auto-generates unique name)
    const bucket = new s3.Bucket(this, 'CacheBucket', {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    // Lambda execution role
    const lambdaRole = new iam.Role(this, 'LambdaRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });

    lambdaRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ['s3:GetObject', 's3:PutObject', 's3:HeadObject'],
        resources: [`${bucket.bucketArn}/*`],
      })
    );

    // Health endpoint (no API key required)
    this.addEndpoint('health', 'GET', lambdaRole, 5, false);

    // News endpoint (API key required)
    this.addEndpoint('news', 'GET', lambdaRole, 10, true, {
      CRYPTOCOMPARE_API_KEY: process.env.CRYPTOCOMPARE_API_KEY || '',
      S3_BUCKET: bucket.bucketName,
    });

    // Tokens endpoint (API key required)
    this.addEndpoint('tokens', 'GET', lambdaRole, 15, true, {
      COINGECKO_API_KEY: process.env.COINGECKO_API_KEY || '',
      S3_BUCKET: bucket.bucketName,
    });

    // Output the API key ID (retrieve actual key from AWS Console or CLI)
    new cdk.CfnOutput(this, 'ApiKeyId', {
      value: apiKey.keyId,
      description: 'API Key ID - use AWS CLI to get the actual key value',
    });
  }

  private addEndpoint(
    name: string,
    method: string,
    role: iam.Role,
    timeout: number = 10,
    requireApiKey: boolean = true,
    environment?: Record<string, string>
  ): nodejs.NodejsFunction {
    const fn = new nodejs.NodejsFunction(this, `${name}Lambda`, {
      entry: path.join(__dirname, `../src/handlers/${name}.ts`),
      handler: 'handler',
      runtime: lambda.Runtime.NODEJS_22_X,
      role,
      timeout: cdk.Duration.seconds(timeout),
      environment,
      bundling: {
        minify: true,
        sourceMap: true,
      },
    });

    const resource = this.api.root.addResource(name);
    resource.addMethod(method, new apigateway.LambdaIntegration(fn), {
      apiKeyRequired: requireApiKey,
    });

    return fn;
  }
}
