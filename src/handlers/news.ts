import { APIGatewayProxyHandler } from 'aws-lambda';
import { errorResponse, successResponse } from '../common/response';
import { fetchNews } from '../services/cryptocompare';

export const handler: APIGatewayProxyHandler = async () => {
  try {
    const news = await fetchNews();

    return successResponse({ results: news }, 'News fetched successfully', {
      count: news.length,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return errorResponse(message);
  }
};
