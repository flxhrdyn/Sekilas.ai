import threading
import sys
import os

# Tambahkan project root ke sys.path
sys.path.append(os.getcwd())

from backend.config.monitor import SystemMonitor
import time

def worker(num_increments):
    for _ in range(num_increments):
        SystemMonitor.increment_gemini_usage()

def test_race_condition():
    print("[TEST] Memulai pengujian race condition (simultan)...")
    SystemMonitor.update_usage(0)
    
    num_threads = 10
    increments_per_thread = 20
    threads = []
    
    start_time = time.time()
    for _ in range(num_threads):
        t = threading.Thread(target=worker, args=(increments_per_thread,))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
    
    end_time = time.time()
    final_stats = SystemMonitor.get_stats()
    final_usage = final_stats.get("gemini_usage", 0)
    expected = num_threads * increments_per_thread
    
    print(f"[RESULT] Selesai dalam {end_time - start_time:.2f} detik.")
    print(f"[RESULT] Usage Akhir: {final_usage}")
    print(f"[RESULT] Expected: {expected}")
    
    if final_usage == expected:
        print("[SUCCESS] Pengujian Berhasil! Portalocker menangani race condition dengan sempurna.")
    else:
        print(f"[FAIL] Pengujian Gagal! Ada {expected - final_usage} data yang hilang.")

if __name__ == "__main__":
    test_race_condition()
