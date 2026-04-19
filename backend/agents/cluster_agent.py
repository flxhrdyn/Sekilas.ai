from __future__ import annotations

import numpy as np
from sklearn.cluster import DBSCAN
from backend.agents.embedder import NewsEmbedder
from backend.agents.models import RawHeadline


class NewsClusterAgent:
    """
    Agent responsible for grouping similar headlines into Topic Clusters
    using local semantic embeddings and DBSCAN algorithm.
    """

    def __init__(
        self, 
        embedder: NewsEmbedder, 
        similarity_threshold: float = 0.82, 
        min_samples: int = 1
    ) -> None:
        self.embedder = embedder
        # DBSCAN 'eps' for cosine metric is 1 - similarity
        self.eps = 1.0 - similarity_threshold
        self.min_samples = min_samples

    def cluster_headlines(self, headlines: list[RawHeadline]) -> list[list[RawHeadline]]:
        """
        Groups headlines into semantic clusters.
        Returns a list of clusters, where each cluster is a list of RawHeadlines.
        Sorted by cluster size (descending).
        """
        if not headlines:
            return []

        print(f"[PROCESS] Clustering {len(headlines)} judul berita secara semantik...")
        
        texts = [h.title for h in headlines]
        embeddings = self.embedder.embed_documents(texts)
        X = np.array(embeddings)

        # DBSCAN find clusters of points that are close to each other
        clustering = DBSCAN(
            eps=self.eps, 
            min_samples=self.min_samples, 
            metric="cosine"
        ).fit(X)
        
        labels = clustering.labels_
        
        clusters: dict[int, list[RawHeadline]] = {}
        for idx, label in enumerate(labels):
            # label -1 is noise in DBSCAN, but for us, it's just a cluster of 1
            if label == -1:
                # Assign unique ID to noise to treat them as individual clusters
                label = 100000 + idx
            
            # Simpan cluster_id ke dalam metadata objek headline
            headline = headlines[idx]
            headline.cluster_id = int(label)
            clusters.setdefault(label, []).append(headline)

        # Sort clusters by size (largest first = Trending Topics)
        sorted_clusters = sorted(clusters.values(), key=len, reverse=True)
        
        n_clusters = len([c for c in sorted_clusters if len(c) > 1])
        print(f"[OK] Ditemukan {len(sorted_clusters)} grup berita ({n_clusters} topik tren).")
        
        return sorted_clusters

    def select_best_representatives(self, clusters: list[list[RawHeadline]], limit: int = 25) -> list[RawHeadline]:
        """
        Pick the 'best' article from each cluster (Round-Robin) until limit is reached.
        Prioritizes larger clusters (Trends) first.
        """
        selected: list[RawHeadline] = []
        
        # Sort each cluster internal by date/whatever if needed, but headlines are already fresh
        # Round-robin selection
        cluster_list = [list(c) for c in clusters]
        
        while len(selected) < limit and cluster_list:
            to_remove = []
            for i, cluster in enumerate(cluster_list):
                if cluster:
                    selected.append(cluster.pop(0))
                    if len(selected) >= limit:
                        break
                else:
                    to_remove.append(i)
            
            for index in sorted(to_remove, reverse=True):
                cluster_list.pop(index)
                
        return selected
