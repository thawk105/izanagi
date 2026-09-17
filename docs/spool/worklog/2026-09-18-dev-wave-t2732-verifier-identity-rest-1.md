---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2732-verifier-identity-rest
seq: 1
title: [T-2732] T126 qualification の code identity へ verifier の __init__ / report / commit_receipt を含めた — D2120 項 6 の裁定 (40 → 43、D2091 と同条件) を Codex author + 変異事前登録で実装し、verifier の個別束縛を 4 → 7 file にした (コード + テスト + docs、branch worktree-dev-wave-t2732-verifier-identity-rest、変異 matrix = baseline PASSED・負例 5/5 KILLED 期待 node 完全一致・等価 1 SURVIVED・MISMATCH 0、初回走は親の規律違反で N2 後に中止し --resume で完走 = F106 再発)
---

## 本文

- 依頼は command 引数のとおり (D2120 項 6 の実装。着手直前の local main から fresh worktree、Codex author、既存 pin テストの更新と焦点走、互換層・旧成果物の再受理なし、
  本題の 3 path 追加だけ)。一次資料は `output/insights/2026-09-18/t2732-verifier-identity-rest/README.md`、逐語は同 `verbatim/`、運転 script・log・spec・attempt json は
  job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2732-verifier-identity-rest/`。先例は entry 1583 / D2091 (T-1209)。新しい設計判断なし (裁定は D2120 項 6 が採用済み) のため decisions fragment は無し。
- 起動時実測: 変更前 sha256 / blob の pin は output/ 含め 0 件、他 branch 未 land 0 件、164 worktree 走査の modified 13 件は着地済み Codex 子木のみ (稼働 process 0)。
  裁定 inbox に追加裁定なし、main は wave 中不動 (d2ebef7a4)。
- 段 3 の 2 レンズは実装 must-fix 0。**親 brief の一般化 4 件を real として訂正した**: 「verifier package 全 7 file」→ tracked 9 file 中 7 (`__main__.py` / `cli.py` は
  T126 経路から到達されない CLI 入口で集合外、裁定パッケージは立てない)、「script は path 名を列挙しない」→ submit script に 5 / 7 path の限定列挙はあるが集合の複製ではない、
  Codex 子木 dirt の観測は時点付き、「焦点走 4 file に drift gate 無し」→ 実 repo live loader 比較の経路が無いことを本 wave の checkout で実走して確認した。
- 実装 commit `eb0f38969` (Codex author、2 file +9 行、逐語どおり)。焦点走 (4 file、計算ノード): 変更前 485 passed / 17.85 秒 (4993.nqsv) → 変更後 489 passed / 18.54 秒 (4995.nqsv、
  未 commit の作業ツリー)、差 +4 = 新 test 1 + parametrized 3。full provenance 監査 11207 件新規違反なし。
- 旧 40-key 形の series-identity は現行 verify で `contract.py:536-540` の `required set mismatch` → driver rc=2 / collector invalid。bytes と当時の判定は保持され現行契約への適合を失う。
  この不受理を過去測定の無効化に使わない (規律 7)。
- 段 6 レビュー 2 本: A 所見 0、B must-fix 0 / nit 1 (焦点走外の consumer test 7 群は受入全走で覆う、insight §5 に列挙)。fix 子なし。
- **変異 matrix の初回走は N2 完了後に harness が中止した (rc=2、`runner/test bytes に固定 HEAD 外の変更を検出`)。** 親が走行中に insight の逐語 file を worktree へ置いて `git add -N` した
  自分起因の規律違反 (DW-M05、F106 の同型再発として failures へ追記)。変異対象は復元済み、index を戻し file を job dir へ退避して `--resume` で残り 3 変異を走らせた。
- 変異 matrix (spec sha256 d292686f…、4 file、dispatch、測った checkout = HEAD eb0f38969): baseline PASSED (45.8 秒)、N1〜N5 すべて KILLED で期待 node と観測 node が完全一致、等価 E1 SURVIVED、MISMATCH 0 (summary = registered 6 / completed 6 / matching 6)。
  N1〜N5 は新 test だけが赤 = 既存の集合由来 test はどれも追随して緑のまま (新規検出力)。
- 工数: codex 子 6 本 (plan 1、consult 2、author 1、review 2、全段 `gpt-6-astra`、plan/consult `medium`)。計算ノード job: 焦点走 2、変異 8 走 (collection 1 + baseline 1 + 変異 6)、
  最終受入 (結果は land の受領証)。

## 次の一手差分

### 完了

- [T-2732] verifier の `__init__.py` / `report.py` / `commit_receipt.py` を T126 code identity へ含めた (commit `eb0f38969`、40 → 43)。旧成果物は据え置き、以後の取得から新 identity。
  remaining: none
  base: 3aae193421367865d615575730fa0f4bb942fad160e6f98683cf06cec3dd3bc8
