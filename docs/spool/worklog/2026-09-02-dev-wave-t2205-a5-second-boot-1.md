---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2205-a5-second-boot
seq: 1
title: A-5 (D1100) 別 boot 再取得の測定 job を作り、実測が着地待ちであることを確定した — 機体選定の根拠は「到達不能」ではなく 2026-08-05 のユーザー裁定だった (コード + テスト + insight、branch worktree-dev-wave-t2205-a5-second-boot、変異 6/6 KILLED + M2 は check_docs で単一理由を実測)
---

## 本文

- **依頼は論文採用 2 値 (write-heavy 静的 10µs で +38.3288%、balanced 静的 5µs で +11.2682%) の
  別 boot 再取得だった。測定 job は作ったが、実測値は 1 つも取れていない。** 理由は F660 で、
  迂回はしていない。詳細と次の一手は
  `output/insights/2026-09-02_t2205-a5-second-boot-measurement-job/README.md`。
- **段 1 brief の根拠が 2 箇所とも誤っていた。** 敵対相談が両方を覆した。
  - 「元の機体 (linux-baremetal) に到達できないから Pegasus で回す」と書いたが、
    到達不能は証明されていない。正しい根拠は **2026-08-05 のユーザー裁定 (P3 U-7)** —
    linux-baremetal (cygnus、D59 の研究室共有 Dell R760) は**使えるが使わない**、
    cygnus 依存の研究はしない、evidence は Pegasus で新規に測る。
  - 「2 job を別ノードへ投げれば異なる 2 boot の内部対照が取れる」と書いたが、A-2 の正式走が
    既に `bnode141` / `bnode064` の異なる 2 boot で走っている
    (`output/insights/2026-08-24_paper-story-a2-certification/raw-manifest.json`)。
    fan-out の形は新しい対照ではない。node と boot の記録は provenance に留めた。
- **敵対相談は「cygnus の到達可否と再起動権限を確認し、可能なら同じ機体の新 boot で取り直せ」と
  勧告したが、不採用にした。** 上のユーザー裁定に正面から反するためである。
  **ただしこの択一はユーザーの手番に戻す価値がある** — D1100 を厳密な意味 (同一機体の別起動) で
  満たすには cygnus を使うしかなく、その可否は 2026-08-05 裁定の射程の問題である。
  裁定パッケージとして残す。
- **段 6 のレビューが、契約テストが行の見た目しか見ておらず事前登録した変異 4 件が意味上は
  生き残っていることを見つけた。** とくに呼び出し直前の `BASELINE_FLAGS["BACK_OFF"] = 1` は
  全テストを通したうえで分母を stock 適応へすり替える。AST による意味検査へ作り直した。
- **M2 (runbook 投影表の行削除) は pytest 層では生存した。** 実効 gate は `tools/check_docs.py` で、
  `test_check_docs.py` は合成 fixture 上で動くため実 repo の行削除を見ない。
  `DW-O19` の一時変異で直接測り、単一理由の赤 (`Pegasus admission drift`) を実測して復元した。
- **子の工数と事故。** 段 2 plan 1 本、段 3 相談 2 本、段 5 実装 1 本、段 6 レビュー 2 本、fix 1 本。
  段 6 のレビューは 2 度落ちた — 1 度目は `--lane` を渡したため (consult 専用) rc=2、
  2 度目は `tools/pegasus/admission_registry.json` の未 commit 差分が codex hook 配線の
  HEAD blob 照合を破ったため rc=2。**登録簿は段 6 の子を起動する前に commit しておく必要がある。**

## 次の一手差分

### 新規

- {{T:a5-second-boot-measure}} **P1・新規**: A-5 (D1100) の実測を走らせる。
  本 wave が着地した後、`bash tools/pegasus/submit_a5_second_boot_backoff_sweep.sh
  --output-parent <repo 外の既存 directory>` を 1 回。job は開始時に `PBS_O_WORKDIR` の HEAD が
  投入時の SHA と一致することを検査するので、**2 job が終わるまでその branch へ commit しない**。
  完了後に `git worktree list` で scratch worktree の残骸が無いことを確かめる。
  受理してよい主張と書いてはいけない主張は insight に固定済み。

- {{T:a5-cygnus-ruling}} **P2・ユーザー裁定待ち**: D1100 を厳密な意味 (同一機体の別起動) で
  満たすには cygnus を使うしかない。2026-08-05 のユーザー裁定は cygnus 依存の研究をしないと
  定めており、Pegasus で回すと「別の起動」と「別の環境」が交絡して起動単独の効果を分離できない。
  (a) Pegasus の結果を A-5 の充足として受け入れる、(b) この 1 回だけ cygnus を例外として使う、
  (c) A-5 を未充足のまま残す、のいずれかをユーザーに諮る。
