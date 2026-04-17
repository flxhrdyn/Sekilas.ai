export interface NewsArticle {
  id?: string;
  title: string;
  summary: string;
  keyPoints: string[];
  source: string;
  category: string;
  publishedAt: string;
  url: string;
  relevanceScore?: number;
}

export interface DigestData {
  date: string;
  generated_at: string;
  headline: string;
  category_digests: Record<string, any[]>;
  stats: Record<string, number>;
  categories: string[];
}

export type Tab = 'digest' | 'search' | 'qa';

export interface SystemStatus {
  date: string;
  gemini_usage: number;
  model_name?: string;
}
