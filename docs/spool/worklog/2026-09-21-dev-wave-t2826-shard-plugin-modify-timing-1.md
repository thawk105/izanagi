---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-t2826-shard-plugin-modify-timing
seq: 1
title: [T-2826] 受入 pre の modify 複合区間の関数別計時は Codex の利用上限で段 5 の probe 実装が止まり未計測 — 計測設計 v2 と読み方 R1〜R8 を結果を見る前に凍結し docs-only で閉じた (docs + insight、branch worktree-dev-wave-t2826-shard-plugin-modify-timing)
---

## 本文

- 依頼 (ユーザー起動引数、2026-09-21 14:03 JST): 受入 `pre` の worker 側 45 秒 (T-2817 §5 (b)) を関数別に計時する診断。短縮の実装は含めない (D1936 項 35)、probe は job dir・Codex author、本題の計測だけ。起点 local main `d99c556df` (fresh worktree、開始 gate rc 0 = 14:08:04 JST)。insight は `output/insights/2026-09-21/t2826-shard-plugin-modify-timing/README.md`。
- 段構成 (本記録の時点までに実行した順): 段 1 brief → 段 3 read-only 相談 1 本 → 段 4 裁定 → 段 5 author 子 1 本 (途中終了) → 段 4 追補 (実装しない) → 段 7 (本記録と事実照合)。段 2 は省いた。
- 段 3 相談 (codex gpt-6-astra / medium、2 レンズを 1 本): 所見 9 件 (高 4・中 5)、全件 real・採用、refuted 0、判定「修正後 GO」。最重要 = 短縮量の主比較を計器の揃った `S3-f − S3-cf` に替える (S3-u は観測者効果の対照だけ)、閉包は排他的な葉だけで `median(|残差|)` を見る、memo の公開時刻は prewarm の正常復帰で取り ε は実測残差にする。反実仮想セル (probe 内で resolve を memo 化) は「条件付きで scope 内」を採った。
- 段 4 裁定で計算ノード 1 job・11 セルの計測設計 v2 と読み方 R1〜R8 を、job を 1 本も投げる前に確定した (insight `verbatim/s4-ruling.md` §3 / §4)。変異 matrix は repo の実装面差分ゼロで免除。
- **段 5 の Codex author 子が利用上限で終了した** (14:24:40 起動 → 14:33 終了、観測できた model 呼出し 9 回・514 秒、`codex_exit_code=1`、`f45_missing_output`、出力 0 byte。停止本文は `try again at Sep 26th, 2026 7:35 PM`)。D582 に従いユーザーへ端末通知を送り (携帯 push は未送信)、自動再投入はしていない。入口の凍結境界と `docs/ai-provenance.md` (Codex 実行不能なら代行せず停止) により親は probe を代行せず、従量経路へも切り替えていない。段 4 追補で「実装しない」に再裁定し docs-only で閉じた。
- 段 7 の事実照合は Codex が使えないため Claude の read-only 子 1 本 (opus) で行った: 所見 13 (must-fix 2 = 再開手順の文言、should 2、nit 9)、全件 real・反映、数値・hash・逐語・件数の不一致 0 (insight `verbatim/s7-review-out.md`)。
- **計測は未実施** (計算ノード job 0 本)。T-2825 の比較測定と区間は重なっていない。書きかけの probe 3 file (1,292 行、未検査) は起動器の終端 commit `31894443e` (branch `author-t2826-probe`、land しない) にあり、wave 専用 dir `partial-author/` へ退避した。
- 工数: codex 子 = consult 1 (完了) + author 1 (利用上限で途中終了)、Claude 子 = 事実照合 1。計算ノード job 0。login で wave 木の pyc を温めた (`27033 tests collected`、insight §2)。

## 次の一手差分

### 更新

- [T-2826] **P1・Codex 復帰待ち**: 受入 `pre` の worker 側 45 秒 (shard plugin を載せた段の modify 複合区間、process 群の sys +2027 秒、Lustre `intent_lock` 11.7 倍) の内訳を関数別に計時する (probe は job dir、Codex author)。2026-09-21 の wave は段 5 で Codex の利用上限に当たり未計測 (解除表示 2026-09-26 19:35、またはユーザーのアカウント切替後)。**再開は fresh wave で段 4 から** (入口の「裁定後に別 context が段 4 から再開する型」) — 段 3 相談を流用し、段 4 で `output/insights/2026-09-21/t2826-shard-plugin-modify-timing/` の `verbatim/s4-ruling.md` §3 (計測設計 v2: 11 セル、主比較 = 同計器の S3-f − S3-cf) / §4 (読み方 R1〜R8、`pre` ≈ max(W_w, M) の予測を含む) を変えずに採り直して段 5 へ進む。段 5 は `verbatim/s5-author-prompt.md` を雛形に wave 固有の値 (子 worktree の path と branch、仕様 file の置き場、既定の出力先、tip が進んでいれば行番号) を差し替え、新しい `--job-id` で投入する。標本の時点 (計測 tip・as-of) は再開 wave の開始 gate で改めて固定する。書きかけ probe (wave 専用 dir `partial-author/`、未検査) は参考資料としてだけ渡す。縮約方式の設計・実受入の隣接対は計測の後の別項。
  base: 09c7157ced2be67aad9ed32a3a4972d1f7d0d1521455f454330edf40d964dc0b
