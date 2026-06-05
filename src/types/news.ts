export interface NewsItem {
  id: number;
  title: string;
  summary: string;
  source: string;
  published_at: string;
  url: string | null;
  currencies: string[];
  votes: {
    positive?: number;
    negative?: number;
    important?: number;
    comments?: number;
  };
  domain: string | null;
}

export interface CryptoCompareNewsItem {
  id: string;
  title: string;
  body: string;
  source: string;
  published_on: number;
  url: string;
  categories: string;
  upvotes: string;
  downvotes: string;
  source_info: {
    name: string;
  };
}

export interface CryptoCompareResponse {
  Data: CryptoCompareNewsItem[];
}
