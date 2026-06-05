import { Config } from '../common/config';
import {
  BiggestCoin,
  GainerLoser,
  TrendingCoin,
  BannerCoin,
  Sentiment,
  TokensResponse,
} from '../types/tokens';

interface CoinGeckoMarketCoin {
  id: string;
  symbol: string;
  name: string;
  image: string;
  current_price: number;
  market_cap: number;
  market_cap_rank: number;
  price_change_24h: number;
  price_change_percentage_24h: number;
  market_cap_change_24h: number;
  market_cap_change_percentage_24h: number;
  circulating_supply: number;
  sparkline_in_7d?: { price: number[] };
}

interface CoinGeckoTrendingResponse {
  coins: Array<{
    item: {
      id: string;
      name: string;
      symbol: string;
      score: number;
      large: string;
    };
  }>;
}

const COINGECKO_HEADERS = {
  accept: 'application/json',
  'x-cg-demo-api-key': process.env.COINGECKO_API_KEY || '',
};

async function fetchTopCoins(limit: number = 250): Promise<CoinGeckoMarketCoin[]> {
  const params = new URLSearchParams({
    vs_currency: 'usd',
    order: 'market_cap_desc',
    per_page: String(limit),
    page: '1',
    sparkline: 'false',
  });

  const response = await fetch(`${Config.coingecko.topCoins}?${params}`, {
    headers: COINGECKO_HEADERS,
    signal: AbortSignal.timeout(Config.requestTimeout),
  });

  if (!response.ok) {
    throw new Error(`CoinGecko API error: ${response.status}`);
  }

  return response.json();
}

async function fetchTrending(): Promise<CoinGeckoTrendingResponse> {
  const response = await fetch(Config.coingecko.trending, {
    headers: COINGECKO_HEADERS,
    signal: AbortSignal.timeout(Config.requestTimeout),
  });

  if (!response.ok) {
    throw new Error(`CoinGecko trending API error: ${response.status}`);
  }

  return response.json();
}

function mapToBiggestCoin(coin: CoinGeckoMarketCoin, rank: number): BiggestCoin {
  const isStable = Math.abs(coin.price_change_percentage_24h || 0) < 1;
  const isWrapped =
    coin.name.toLowerCase().includes('wrapped') ||
    coin.symbol.toLowerCase().startsWith('w');

  return {
    image: coin.image,
    name: coin.name,
    symbol: coin.symbol.toUpperCase(),
    marketCapRank: rank,
    marketCap: String(coin.market_cap),
    marketCapChange24H: String(coin.market_cap_change_24h || 0),
    marketCapChangePercentage24H: String(coin.market_cap_change_percentage_24h || 0),
    currentPrice: String(coin.current_price),
    priceChange24H: String(coin.price_change_24h || 0),
    circulatingSupply: String(coin.circulating_supply || 0),
    stable: isStable,
    wrapped: isWrapped,
  };
}

function mapToGainerLoser(coin: CoinGeckoMarketCoin): GainerLoser {
  return {
    id: coin.id,
    image: coin.image,
    name: coin.name,
    symbol: coin.symbol.toUpperCase(),
    price: coin.current_price,
    priceChangePercentage24H: coin.price_change_percentage_24h,
    price_change_percentage_24h: coin.price_change_percentage_24h,
  };
}

function mapToBannerCoin(coin: CoinGeckoMarketCoin): BannerCoin {
  return {
    id: coin.id,
    image: coin.image,
    name: coin.name,
    symbol: coin.symbol.toUpperCase(),
    price: coin.current_price,
    priceChangePercentage24H: coin.price_change_percentage_24h,
  };
}

function calculateSentiment(coins: CoinGeckoMarketCoin[]): Sentiment {
  const bitcoin = coins.find(
    (c) => c.symbol.toLowerCase() === 'btc' || c.name.toLowerCase() === 'bitcoin'
  );

  if (!bitcoin) return 'neutral';

  const change = bitcoin.price_change_percentage_24h || 0;
  if (change > 1) return 'bullish';
  if (change < -1) return 'bearish';
  return 'neutral';
}

export async function fetchTokens(
  perPage: number = 50,
  gainerLimit: number = 20,
  bannerLimit: number = 20
): Promise<TokensResponse> {
  // Fetch all data in parallel
  const [allCoins, trendingData] = await Promise.all([
    fetchTopCoins(250), // Need 250 to calculate gainers/losers
    fetchTrending(),
  ]);

  // Biggest coins (top by market cap)
  const biggestCoins = allCoins
    .slice(0, perPage)
    .map((coin, i) => mapToBiggestCoin(coin, i + 1));

  // Sort for gainers/losers
  const sortedByChange = [...allCoins].sort(
    (a, b) => (b.price_change_percentage_24h || 0) - (a.price_change_percentage_24h || 0)
  );

  const topGainers = sortedByChange.slice(0, gainerLimit).map(mapToGainerLoser);
  const worstLosers = sortedByChange.slice(-gainerLimit).reverse().map(mapToGainerLoser);

  // Trending coins
  const trendingCoins: TrendingCoin[] = trendingData.coins.map((c) => ({
    id: c.item.id,
    name: c.item.name,
    symbol: c.item.symbol.toUpperCase(),
    score: c.item.score,
    large: c.item.large,
  }));

  // Banner (top coins)
  const banner = allCoins.slice(0, bannerLimit).map(mapToBannerCoin);

  // Sentiment
  const sentiment = calculateSentiment(allCoins);

  return {
    biggestCoins,
    topGainers,
    worstLosers,
    trendingCoins,
    banner,
    sentiment,
  };
}
