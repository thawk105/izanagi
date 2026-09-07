---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: t2338-a2-reject-conditions
seq: 1
title: [T-2338] A-2 reject の測定条件を追記訂正し、支持する命題を BACK_OFF の有効/無効へ改めた — 併せて機構が指数でなく適応 backoff であることが pin の現物から出た (docs + insight、branch worktree-t2338-a2-reject-conditions、実装面の差分 0)
---

## 本文

- ユーザー裁定 D1645 の実行。追記先は `output/insights/2026-08-28_t2022-a2-certification-run/README.md`
  (末尾追記、既存 45 行は不変) と `output/insights/2026-08-24_paper-story-a2-certification/README.md` (新設)。
  改訂稿は `docs/paper-story/results/2026-09-07-a2-certification-reject.md`。2026-09-04 の稿は append-only の
  凍結物として bytes 不変で残し、`docs/paper-story/README.md` の results 表と
  `docs/paper-story/figures/README.md` の proof chain 参照を新稿へ向けた。
- **裁定の前提を一次資料で裏取りした。** durable authority の WAL 2 本の `build_start` 4 record は
  すべて `src_token=stock` / `tracked_clean=true` / tracked diff は空 bytes の SHA-256 / `tracked_paths=[]`。
  読んだ WAL と raw cell 6 件の SHA-256 は `raw-manifest.json` の `files` map と一致した。
- **裁定の文言に対する新事実が 1 件出た。** D1645 は機構を「内蔵指数 backoff」と書くが、pin `511c9538` の
  CCBench の `include/backoff.hh` はスループット勾配で待機量を固定幅 100 だけ増減し 0〜1000 に収める
  **適応制御**であり、指数的ではない。`cmake/Options.cmake` の option 説明文だけが `exponential backoff on abort` と
  呼んでおり、裁定の文言はそこに由来すると見られる。**D1645 の決定内容 (支持する命題を `BACK_OFF` の
  有効/無効へ書き換えること) はそのまま実行し、機構名だけを実装に合わせた。** 裁定文の追記訂正が要るかは
  ユーザーの判断に返す。
- 段 6 review A が「`BACKOFF_FIXED` は CMake に届いていない」という親の記述を real 所見として覆した。
  `-DCCBENCH_BACKOFF_FIXED=10` は cmake の argv に確かに渡っており、届かなかったのではなく、pin の CCBench に
  対応する option 定義が無いため compile definition にならなかった、が正しい。4 文書すべてを直した。
- 段 6 の must-fix は review A が 4 件 (機構名・4 cell の証拠閉包・`src_token` 単独の意味・living README の
  消し込み)、review B2 が 3 件 (表の転記元を provenance にする・living README が統制稿を一次資料と呼ぶ・
  限定の出所が claim-evidence)。nit は 7 件。**すべて採用し、コード fix は 0 件。**
- **受入全走が全 wave で 1 件赤になる環境欠陥を見つけて直した。** この機体の `/tmp` に 2026-09-05 12:55 作成の
  空ディレクトリ `.git` が残っており、`layout.py` の repository 外検査が pytest の `tmp_path` をすべて
  「repository 内」と判定していた。`test_official_run_observes_and_passes_current_toolchain_manifest` が
  決定的に赤になる。`rmdir` で除去して同 test が緑になることを実測した。本 wave の差分とは無関係である。
- 段 6 review B の 1 回目は codex が正常終了したのに launcher が rollout event 2 件の `event_invalid` で
  受理しなかった。同じ prompt の再投入は job-id が同一になり「既存 receipt は上書きできない」で rc=2。
  `--job-id` を変え、修正後の木に対して走らせ直して受理させた。
- 実装面の差分は 0 なので変異 matrix は免除 (`DW-S04`)。Codex 実装子は起動していない。

## 次の一手差分

### 完了

- [T-2338] D1645 の追記訂正を 3 文書へ実施し、論文素材の参照を新稿へ向けた。
  remaining: none
  base: 3a6bf37212eb9967ad83d5992ee19755fa54d07671bfcce1c8331877f95910c6
