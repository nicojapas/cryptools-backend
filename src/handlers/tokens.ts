import { APIGatewayProxyHandler } from 'aws-lambda';
import { getFromCache, saveToCache } from '../common/cache';
import { Config } from '../common/config';
import { errorResponse, successResponse } from '../common/response';
import { fetchTokens } from '../services/coingecko';
import { TokensResponse } from '../types/tokens';

const CACHE_KEY = 'tokens';

export const handler: APIGatewayProxyHandler = async (event) => {
  try {
    const query = event.queryStringParameters || {};
    const perPage = Math.min(parseInt(query.per_page || '50', 10), Config.maxPageSize);

    // Try cache first
    const cacheKey = `${CACHE_KEY}_p${perPage}`;
    let tokens = await getFromCache<TokensResponse>(cacheKey, Config.cache.tokens);

    if (!tokens) {
      tokens = await fetchTokens(perPage);
      await saveToCache(cacheKey, tokens);
    }

    return successResponse(tokens, 'Tokens fetched successfully', {
      count: tokens.biggestCoins.length,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return errorResponse(message);
  }
};
