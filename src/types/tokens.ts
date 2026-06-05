// Frontend response types for /tokens endpoint

export interface BiggestCoin {
  image: string;
  name: string;
  symbol: string;
  marketCapRank: number;
  marketCap: string;
  marketCapChange24H: string;
  marketCapChangePercentage24H: string;
  currentPrice: string;
  priceChange24H: string;
  circulatingSupply: string;
  stable?: boolean;
  wrapped?: boolean;
  sentiment?: 'bullish' | 'bearish' | 'neutral';
}

export interface GainerLoser {
  image: string;
  name: string;
  symbol: string;
  price: string | number;
  priceChangePercentage24H: number | null;
  price_change_percentage_24h?: number;
  id: string | null;
}

export interface TrendingCoin {
  id: string | null;
  name: string;
  symbol: string;
  score: number;
  large: string;
}

export interface BannerCoin {
  image: string;
  name: string;
  symbol: string;
  price: string | number;
  priceChangePercentage24H: number | null;
  id: string | null;
}

export type Sentiment = 'bullish' | 'bearish' | 'neutral';

export interface TokensResponse {
  biggestCoins: BiggestCoin[];
  topGainers: GainerLoser[];
  worstLosers: GainerLoser[];
  trendingCoins: TrendingCoin[];
  banner: BannerCoin[];
  sentiment: Sentiment;
}export const COINGECKO_HEADERS = {
  accept: 'application/json',
  'x-cg-demo-api-key': process.env.COINGECKO_API_KEY || '',
};

