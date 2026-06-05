import { APIGatewayProxyResult } from 'aws-lambda';

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, X-Api-Key',
};

interface ResponseBody {
  message: string;
  timestamp: string;
  data?: unknown;
  error?: string;
  [key: string]: unknown;
}

export function successResponse(
  data?: unknown,
  message = 'success',
  extra?: Record<string, unknown>
): APIGatewayProxyResult {
  const body: ResponseBody = {
    message,
    timestamp: new Date().toISOString(),
  };

  if (data !== undefined) {
    body.data = data;
  }

  if (extra) {
    Object.assign(body, extra);
  }

  return {
    statusCode: 200,
    headers: CORS_HEADERS,
    body: JSON.stringify(body),
  };
}

export function errorResponse(
  error: string,
  statusCode = 500
): APIGatewayProxyResult {
  return {
    statusCode,
    headers: CORS_HEADERS,
    body: JSON.stringify({
      message: 'error',
      error,
      timestamp: new Date().toISOString(),
    }),
  };
}
