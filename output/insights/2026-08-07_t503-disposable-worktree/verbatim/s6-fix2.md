## 総括
変更行: `str(signum)` を `str(int(signum))` に修正。  
SIGINT (`2`) と SIGTERM (`15`) を厳密に区別するため、検出力は維持。  
戻り値 assert は保持し、構文検査も成功。