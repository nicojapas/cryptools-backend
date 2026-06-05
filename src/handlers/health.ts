import { APIGatewayProxyHandler } from 'aws-lambda';
import { successResponse } from '../common/response';

export const handler: APIGatewayProxyHandler = async () => {
  return successResponse(
    { status: 'healthy' },
    'Service is running'
  );
};
