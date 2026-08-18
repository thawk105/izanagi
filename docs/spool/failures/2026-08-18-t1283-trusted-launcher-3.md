---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-18
wave: t1283-trusted-launcher
seq: 3
---

## supersede 追記

- F385 **supersede: 2026-08-18** — 恒久対応を {{D:acceptance-launcher-authority}} へ更新した。受領証の内容を候補外の `tools/acceptance_launcher.py` が生成し、land が実行 bytes 3 本の内容 SHA-256 を Git tree から独立に再計算して `child-green` にも照合する。**それでも閉じていない** — 起動権は tip 側待ち手にあり、bounded / dispatch の内側の子は束縛外で、land verifier 自身も候補コードである。残余は {{T:acceptance-launcher-outer-entrypoint}} / {{T:acceptance-inner-child-binding}} / {{T:land-verifier-attribution}} で追う。
