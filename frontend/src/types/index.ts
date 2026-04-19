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

export interface StoryGroup {
  id: number;
  title: string;
  synthesis: string[];
  articles: any[];
}

export interface DigestData {
  date: string;
  generated_at: string;
  headline: string;
  top_stories: StoryGroup[];
  other_news: Record<string, any[]>;
  stats: Record<string, number>;
  categories: string[];
}

export type Tab = 'digest' | 'search' | 'qa';

export interface SystemStatus {
  date: string;
  gemini_usage: number;
  model_name?: string;
}
