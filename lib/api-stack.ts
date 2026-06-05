import * as cdk from 'aws-cdk-lib';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as nodejs from 'aws-cdk-lib/aws-lambda-nodejs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';
import * as path from 'path';

const BUCKET_NAME = 'cryptools-cache';

export class ApiStack extends cdk.Stack {
  public readonly api: apigateway.RestApi;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // API Gateway
    this.api = new apigateway.RestApi(this, 'CryptoolsApi', {
      restApiName: 'Cryptools API',
      defaultCorsPreflightOptions: {
        allowOrigins: ['*'],
        allowMethods: ['GET', 'POST', 'OPTIONS'],
        allowHeaders: ['Content-Type', 'Authorization'],
      },
    });

    // S3 bucket for caching
    const bucket = s3.Bucket.fromBucketName(this, 'CacheBucket', BUCKET_NAME);

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

    // Health endpoint
    this.addEndpoint('health', 'GET', lambdaRole, 5);
  }

  private addEndpoint(
    name: string,
    method: string,
    role: iam.Role,
    timeout: number = 10,
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
    resource.addMethod(method, new apigateway.LambdaIntegration(fn));

    return fn;
  }
}
