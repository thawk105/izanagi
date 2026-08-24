---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1600-fold-gate
seq: 2
---

## 再発

### F24

- **再発: 2026-08-25** — 同一 wave 内で `tools/dev_wave_wait.py producer` と背景 until ループの
  偽完了が **40 回以上**起き、過去の再発記録 (2026-08-24 の 3 回) を桁違いに超えた。
  内訳は段 6 レビュー A の待ち手、焦点走 5 本、変異 probe の待ち手 3 回、変異穴 fix 子の待ち手
  2 回、変異本走の待ち手 30 回以上、時間予算 fix 子の待ち手 17 回。
  張り直すたびに十数秒で偽完了する状態が続き、待ちが実質的に機能しなかった。いずれも rc=0・出力ゼロ・`.done` 不在で戻り、実際には
  producer が `ps` / `pgrep -af` で生存して走行を続けていた。恒久対応 (`.done` 出現と producer 死の
  両方で判定し、待ち手の rc も通知も信じない) がそのまま効き、実害はゼロだった。
  **本 wave の追加事実は、生産者側を親の背景 job に結び付けるか否かで被害が変わる点である。**
  焦点走 2 回目は `run_tests.py` を親の背景 job として直接起動していたため、親側 job の消失で
  出力を丸ごと失い、計算ノード側の submission dir から回収する羽目になった (compute job 自体は
  生き残っていた)。以後の焦点走・変異走を `nohup setsid` + `.done` file の detach 方式へ
  切り替えたところ、待ち手が何度落ちても走行も成果物も失われなくなった。
  **教訓の形: 走行を親の背景 job に結び付けず、必ず detach + `.done` にする。**
