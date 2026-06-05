import { Config } from '../common/config';
import { CryptoCompareNewsItem, CryptoCompareResponse, NewsItem } from '../types/news';

function mapNewsItem(item: CryptoCompareNewsItem): NewsItem {
  const domain = new URL(item.url).hostname;
  return {
    id: parseInt(item.id, 10),
    title: item.title,
    summary: item.body.substring(0, 300),
    source: item.source_info.name,
    published_at: new Date(item.published_on * 1000).toISOString(),
    url: item.url,
    currencies: item.categories.split('|').filter(Boolean),
    votes: {
      positive: parseInt(item.upvotes, 10) || 0,
      negative: parseInt(item.downvotes, 10) || 0,
    },
    domain,
  };
}

export async function fetchNews(): Promise<NewsItem[]> {
  const apiKey = process.env.CRYPTOCOMPARE_API_KEY;
  if (!apiKey) {
    throw new Error('CRYPTOCOMPARE_API_KEY is not configured');
  }

  const response = await fetch(`${Config.cryptocompare.news}?lang=EN`, {
    headers: {
      authorization: `Apikey ${apiKey}`,
    },
    signal: AbortSignal.timeout(Config.requestTimeout),
  });

  if (!response.ok) {
    throw new Error(`CryptoCompare API error: ${response.status}`);
  }

  const data = (await response.json()) as CryptoCompareResponse;
  return data.Data.map(mapNewsItem);
}
