import { APIGatewayProxyHandler } from 'aws-lambda';
import { getFromCache, saveToCache } from '../common/cache';
import { Config } from '../common/config';
import { errorResponse, successResponse } from '../common/response';
import { fetchNews } from '../services/cryptocompare';
import { NewsItem } from '../types/news';

const CACHE_KEY = 'news';

export const handler: APIGatewayProxyHandler = async () => {
  try {
    // Try cache first
    let news = await getFromCache<NewsItem[]>(CACHE_KEY, Config.cache.news);

    if (!news) {
      // Cache miss - fetch fresh data
      news = await fetchNews();
      await saveToCache(CACHE_KEY, news);
    }

    return successResponse({ results: news }, 'News fetched successfully', {
      count: news.length,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return errorResponse(message);
  }
};
