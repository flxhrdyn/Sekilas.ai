import { DigestData, NewsArticle, SystemStatus } from '../types';

export const apiService = {
  async getDigest(): Promise<DigestData> {
    const res = await fetch('/api/digest');
    if (!res.ok) throw new Error('Failed to fetch digest');
    return res.json();
  },

  async searchArticles(query: string, topK: number = 8): Promise<NewsArticle[]> {
    const res = await fetch('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, top_k: topK })
    });
    if (!res.ok) throw new Error('Search failed');
    const data = await res.json();
    return (data.results || []).map((r: any) => ({
      title: r.title,
      summary: r.summary,
      keyPoints: r.key_points || [],
      source: r.source,
      category: r.category,
      publishedAt: r.published_at,
      url: r.url,
      relevanceScore: r.score
    }));
  },

  async askQA(question: string) {
    const res = await fetch('/api/qa', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    });
    const data = await res.json();
    return {
      answer: data.answer,
      sources: data.sources,
      retrieved: (data.retrieved || []).map((r: any) => ({
        title: r.title,
        summary: r.summary,
        keyPoints: r.key_points || [],
        source: r.source,
        category: r.category,
        publishedAt: r.published_at,
        url: r.url
      }))
    };
  },

  async getSystemStatus(): Promise<SystemStatus> {
    const res = await fetch('/api/digest/system/status');
    if (!res.ok) throw new Error('Failed to fetch system status');
    return res.json();
  },

  async updateSystemUsage(count: number): Promise<void> {
    const res = await fetch('/api/digest/system/usage', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ count })
    });
    if (!res.ok) throw new Error('Failed to update system usage');
  }
};
