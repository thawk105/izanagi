# 段 1 brief — [T-816] FN-2 trace v2 の C++ 半分 (手順 1・2)

wave: dev-wave-t756-fn2-trace-v2 / branch worktree-dev-wave-t756-fn2-trace-v2
repo root (worktree): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2

## 確定済みユーザー裁定 (前提、覆さない)

[T-816] 2026-08-11 /rulings、Q1〜Q3 全問 (a)。正本 =
`output/insights/2026-08-11_t756-commit-witness/verbatim/ruling-package.md`。
4 段手順のうち **本 wave は手順 1・2 だけ**を担う。

1. submodule `izanagi-trace` へ trace v2 の **local commit** を作り SHA を報告する。gitlink は動かさない。
2. **旧 pin 対新 pin の TRACE=0 翻訳単位同一検査**を実装・実行し結果を報告する (規律 1 の機械保証)。

射程外 (本 wave で触らない): 手順 3 = push と承認定数 `CCBENCH_FULL_SHA` / `pin.CURRENT_PIN` の更新
(人間手番)、手順 4 = gitlink 前進・v1 trace の拒否化・`test_characterization_txn_tail_loss_is_false_green`
の反転 (承認後の別 wave)。

## 裁定前提を覆す新事実 (段 4 で再裁定する)

**NF-1 (実測、機械拒否):** `hooks/guard_write.py:36-38` の `EVOLVE_BLOCK_SOURCES` は
`("include/backoff.hh", "cc/silo/transaction.cc")` だけを `external/ccbench` の編集面として許す。
裁定パッケージ §1 が挙げた `include/trace.hh` と `cc/si/transaction.cc` への書き込みは
**hook が機械拒否する**。同じ壁は D41 (decisions.md) で既に踏まれており、そこでは
(i) scratch copy + `git apply` の迂回が「hook のブロック回避」として却下され、
(ii) **transaction.cc 内で既存 `izanagi_trace::stream()` を直接呼ぶ設計へ変更して trace.hh を
一切変更せず完結させる**、という解決が採られている (P 行 = permutation violation の先例)。

- **(P1) 親の provisional 裁定 (攻撃対象):** D41 の先例に従い、v2 の C 行と txn 終端マーカーを
  `cc/silo/transaction.cc` 内で `izanagi_trace::stream()` へ直接書く。`include/trace.hh` は 1 byte も
  変更しない。→ 手順 1 は編集面内で完結し、迂回もしない。
- **(P2) 親の provisional 裁定 (攻撃対象):** `cc/si/transaction.cc` (SI) は編集面外なので **本 wave の
  射程外**とし、silo だけ v2 化する。SI と将来の mocc を v2 化する経路 (= 編集面の裁定) は
  段 7 で裁定パッケージとして返す。手順 4 の「v1 拒否」を SI へ適用すると SI trace が検証不能に
  なるため、この残余は手順 4 の前提として明示する。

## 成果物の形

- **A. submodule local commit (Codex author)**: `cc/silo/transaction.cc` のみ変更。v2 形式 =
  C 行に R/W 件数、txn 終端マーカー行。全て `#if TRACE` 内。SHA を報告し、worktree 撤去で
  消えないよう `git bundle` を repo 外の durable path へ出す。**gitlink は d706650 のまま戻す。**
- **B. TU 同一検査 (Codex author)**: `tools/` に新規 checker。旧 pin / 新 pin の対象ソースを
  TRACE=0 で preprocess して byte 同一を要求し、`#include` 行差も併せて検査する (preprocess は
  include を落とすため単独では死角)。fail-closed。pytest は合成 fixture で正例・負例を張る
  (新 commit は main に存在しないため実 commit 依存のテストは置かない)。
- **C. 実走証拠**: 旧 pin 対新 pin の実 TU 同一検査を 1 回実走し、結果を worklog へ書く。
- **D. 記録**: spool fragment (worklog / decisions)、insights (逐語・変異台帳)、裁定パッケージ (P2 残余)。

## 不変条件 (破ったら停止)

- `external/ccbench` の gitlink は `d706650cdb31e442bef45b9b4216951d4fb40969` のまま。
  `test_ccbench_full_sha_matches_real_gitlink` が実 gitlink 一致を要求するため、submodule の
  working tree は受入・land の前に d706650 へ戻す。
- 承認定数 `CCBENCH_FULL_SHA` / `pin.CURRENT_PIN` を書き換えない (追認禁止)。
- push しない。`origin/izanagi-trace` は人間手番。
- 凍結成果物 (`output/s1-freeze/`, `output/s8b-freeze/`) の bytes を変えない。
- trace 追加はすべて `#if TRACE` 内 (規律 1、D14)。`#ifdef` にしない。
- 既存テストを削除・弱体化しない (worklog 428 の自省事項)。

## DW-G05 成果物影響 (実装しなかった場合に何が変わるか)

- A/B を入れない → FN-2 (trx 尾部欠落 = C 行だけ残り R/W が消える) が塞がらず、certified 選択の
  土台に「R/W が落ちた trace でも certified」という偽陰性経路が残る。承認手番も始まらない。
- B (TU 同一検査) を入れない → 新 pin の trace-hook 変更が TRACE=0 側へ漏れても機械検出されない。
  `source_digest.assert_trace_diff_matches_head` は pin 自身が動くと baseline も動くため
  新 pin の変更そのものを検査しない (裁定パッケージ §1-4)。性能計測値の観測者効果汚染 =
  campaign の全 throughput 値の意味が変わる。

## 並列分割

段 2 (plan) 1 本 → 段 3 (敵対) 2 本 → 段 5 実装 2 本 (A = submodule v2 / B = TU checker、
所有ファイルが交わらない) → 段 6 review 2 本 + fix。

## 実測環境

親の pytest・checker は login node の repo root。受入全走は計算ノード dispatch (runbook)。
preprocess (`g++ -E`) は login node で可 (g++ 11.4.0 実在を実測済み)。
