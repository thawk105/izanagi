---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t987-oracle-spec-design
seq: 3
---

## 再発

### F57

- **再発: 2026-08-16 ([T-987] wave の受入全走)** — `test_codex_worker_launch.py` の 12 node と
  `test_dev_wave_wait.py::test_public_main_real_signal_releases_lease` の計 **13 件**が同時に落ち、
  待ち手の非帰属 checker は全件を `attributable` と分類した (`stage=acceptance-red-check` rc=70)。
  本 wave の差分は `docs/spool/` と `output/insights/` の **docs 10 file のみ**で、Python・test
  file・`docs/dev-wave/` のいずれにも触れておらず、launcher 実装へ到達しえない。
  同 2 file の単独再走 (計算ノードへ dispatch、request `912484`) は **400 passed / 1 failed /
  6.45 秒**で、**帰属された 13 件は 1 件も再現しなかった**。`DW-O18` により帰属しない。
  **新しい情報は 3 点。**
  (i) **同時失敗数が 1 件から 13 件へ跳ねた初の観測である。** 台帳の既存再発はいずれも 1 件だった。
  (ii) **2026-08-08 の再発が「成立していない」と明記した条件が、今回は成立していた** —
  当該走行の隣で別 wave (`dev-wave-t523-holdout-admission`) の codex `fix` 子が
  `sandbox=workspace-write` / `--max-wall-clock-s 7200` / `--max-model-calls 500` で稼働しており、
  親自身は子を 1 本も起動していない。**「受入の隣で子 process が走る」条件と失敗数の跳ねが
  同時に観測されたのはこれが初めてで、台帳の資源競合の見立てを支持する。**
  ただし本 wave は原因を確定していない — 観測は 1 例であり、他 wave の子は本 wave の制御外にある。
  (iii) 単独再走で落ちた 1 件は帰属 13 件のいずれでもない
  `test_dev_wave_wait.py::test_signal_after_core_success_uses_restored_real_handler` であり、
  「失敗 node が移動する」という既存の見立てと整合する。
  恒久対応は F57 既載の失敗 artifact 保存による原因分離のままで、本 wave では変えていない。
  **本 wave で新たに分かったのは、非帰属 checker の `attributable` 分類が、
  隣で走る他 wave の子による資源競合を差分への帰属と取り違えうるということである。**
