import sys
from pathlib import Path
from backend.agents.scraper import NewsScraper

def test_extraction(url: str):
    print(f"\n[TESTING] URL: {url}")
    print("-" * 50)
    
    # Initialize scraper
    scraper = NewsScraper(
        sources_file=Path("backend/config/sources.yaml"),
        processed_urls_file=Path("data/processed_urls.txt")
    )
    
    try:
        content = scraper._fetch_article_content_standalone(url)
    except Exception as e:
        print(f"[!] ERROR: {e}")
        content = None
    
    if content:
        print(f"BERHASIL EKSTRAKSI ({len(content)} karakter)")
        print("\n=== AWAL KONTEN ===")
        # Print first 500 chars
        print(content[:500] + "...")
        print("\n=== AKHIR KONTEN ===")
        # Print last 500 chars to see if noise remains
        print("..." + content[-500:])
        
        # Check for noise keywords
        noise_keywords = ["Baca juga", "Simak juga", "Klik di sini", "Pilihan Editor"]
        found_noise = [k for k in noise_keywords if k.lower() in content.lower()]
        
        if found_noise:
            print(f"\n[!] WARNING: Ditemukan sisa noise: {found_noise}")
        else:
            print("\n[OK] Tidak ditemukan kata kunci noise umum.")
    else:
        print("[!] GAGAL EKSTRAKSI")

if __name__ == "__main__":
    # Testing with a real URL (using one from the user's screenshot context if possible, 
    # but here I'll use a standard one for verification)
    test_urls = [
        "https://www.cnbcindonesia.com/news/20260425093111-4-729779/negosiasi-via-pakistan-menlu-iran-tolak-4-mata-dengan-utusan-trump",
        "https://news.detik.com/internasional/d-7298124/iran-pakistan-perundingan-damai-as" # Example URL
    ]
    
    for url in test_urls:
        test_extraction(url)
