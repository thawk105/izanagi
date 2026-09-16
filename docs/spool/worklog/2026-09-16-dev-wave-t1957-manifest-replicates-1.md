---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t1957-manifest-replicates
seq: 1
title: [T-1957] 8c trial manifest schema へ cell ごとの反復数 n を足した (コード + テスト、branch worktree-dev-wave-t1957-manifest-replicates、変異 matrix = baseline PASSED・15/15 KILLED・等価変異 1 件 SURVIVED (登録どおり)・MISMATCH 0・期待 node 完全一致)
---

## 本文

- ユーザー依頼は「manifest schema へ 8b が要求する『cell ごとの反復数』を持たせる。既存の記録済み
  manifest から反復数を復元できるかを段 1 で実測し、復元できない範囲は推定で埋めず『不明』として
  区別すること。着手直前の local main から fresh worktree を作る。実装面は Codex author (D95)。
  規律 2 を緩めない。本題の schema 追加だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は
  scope 外」。
- **対象の同定に段 1 の半分を使った。** 依頼は「manifest」としか言わず、repo 内には
  `8b-oracle-manifest/v1` (schedule 行に `replicate_index` を既に持つ)・`knowledge-manifest-receipt/v1`・
  `p3-b4-analysis-manifest/v1` など複数系統がある。依頼文が挙げた key 集合を逐語検索して
  `trial_registry.py` の `_TRIAL_KEYS` に当てたのが決め手だった。
- **「復元できるか」の答えは「母集合が空」である。** 記録済みの 8c trial manifest / registration は
  repo 全域で 0 件で、2 つの独立な方法で確かめた。移行対象も、復元できない範囲も無い。
  一次資料は `output/insights/2026-09-16/t1957-manifest-replicates/README.md`。
- **依頼の前提は仕様の逐語で裏が取れた。** 8b 設計 §10.2 に「manifest は cell ごとに `n` を持ち」と
  ある。設計判断は {{D:trial-manifest-replicate-count-uniform}} と
  {{D:schema-fixing-precedes-section5-entry}}。
- **段 3 レンズ A が親の provisional 裁定の根拠 1 つを反証し、親が採用した。** 親は「受理集合は
  狭まる向きだから D959 の順序規定に触れない」と書いたが、生 JSON 集合としては入れ替わる。
  正しい根拠は「既存の受理条件を 1 つも撤去・緩和せず、追加 field への制約だけを増やす」である。
  **結論 (実施してよい) は変わらず、根拠だけが変わった。**
- **段 3 レンズ A が (P1-b) を覆した。** 親と段 2 plan は「同一 holdout の 3 arm で一致、H1 と H2 は
  異なってよい」としていたが、8b §10.1 の「cell 間の反復集合不一致は判定不能」と衝突する。
  全 cell 同一へ倒した。
- **段 3 レンズ B が独立 fixture 3 箇所の取り残しを見つけ、親 brief の「単一 test file」を覆した。**
  親が実測で裏を取り scope を広げた。
- **段 6 レビュー B の must-fix はコードの欠陥ではなく変異登録の誤りだった。** M8 の期待失敗箇所を
  「registration load の exact-key」と書いたが、実際は正例 test が先に `KeyError` になる。
  本走前に台帳側で訂正し、コードは触らせなかった。
- **段 5 実装子と段 6 fix 子はどちらもテストを走らせられなかった** (dispatch の `qstat -Q` 事前確認が
  rc=1 で、harness が rc=16)。両者とも `closed` と申告せず「実装済み・未実走」と正しく報告した。
  実走はすべて親が行った。
- **ログインノードと計算ノードで焦点走の所要が 88 倍違った。** `test_trial_registry.py` は
  login node (load 48) で 1320 秒、計算ノードで 15.3 秒。以後この規模の焦点走は dispatch する。
- **変異走を 3 回投入した。** 1 回目は親が並行させた provenance 監査の dispatch が `pending-qsub` の
  orphan hold を作っている窓に当たって rc=2、2 回目は 1 回目が残した orphan-stop sidecar で rc=2、
  3 回目で走った。**`DW-M05` の「変異中は親の worktree へ書きうる起動を止める」を親が破った**のが
  1 回目の原因である。
- **親が `.done` を attempt 間で使い回し、稼働中の走行を「rc=2 で終了」と 1 度誤読した。**
  `DW-O01` は「既存 `.done` を消去・再利用せず再投入を止める」と定めており、launcher を
  phase だけで媒介変数化したのが誤りだった。file の mtime を突き合わせて気づいた。
- 工数: codex 子 7 本 (plan 167 秒 / 6 call、consult sol 166 秒 / 5 call・luna 362 秒 / 13 call、
  author 321 秒 / 13 call、review 97 秒 / 4 call・204 秒 / 9 call、fix 77 秒 / 6 call)。
  計算ノード job は焦点走 3 本、provenance 監査 1 本、変異 17 本。

## 次の一手差分

### 完了

- [T-1957] `p3-8c-trial-manifest/v3` と `p3-8c-trial-registration/v3` の trial へ必須 key `n` を
  足した。整数・2 以上・全 6 cell 同一を検証し、serialization と canonical identity にも入れた。
  記録済み manifest は 0 件なので移行は不要だった。
  remaining: none
  base: 9fe27daae5a35056c06ea2112e21ad11d416d7efe8ce54ae5b1a69fe1e479790

### 新規

- {{T:genesis-slot-replicate-binding}} **P2・新規**: genesis slot 集合と登録 `n` の exact 一致を
  結線する。`trial_registry.py` の受入検査は genesis の `attempt_index == 0` slot 集合を
  `replicate_index` を `0` に固定した期待集合と比べており、反復 0 の slot だけを割り当てた
  genesis しか通さない。8b が要求する全 (holdout, 構成, 反復, attempt) slot の事前割当を
  満たせない。受理集合を広げる変更なので、D959 の下では事前登録の発効が先である。
