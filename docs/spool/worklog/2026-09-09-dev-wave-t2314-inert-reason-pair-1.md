---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-09
wave: dev-wave-t2314-inert-reason-pair
seq: 1
title: [T-2314] inert 比較の受理条件を組 2 つのどちらか 1 つへ (コード + docs、branch worktree-dev-wave-t2314-inert-reason-pair)
---

## 本文

- D1625 (ユーザー裁定) を実装した。sandbox backend probe の条件関門は、inert 比較の緑を
  gate の表が定める (理由コード, comparison) の組 2 つのどちらか 1 つで受理する。
  **受理集合を変える変更である。** 実装 commit `bf09c81df`。一次資料は
  `output/insights/2026-09-09_t2314-inert-reason-pair/`。受領証の記録形は
  {{D:t316-receipt-records-fired-inert-pair}}。
- **段 3 敵対相談が段 2 プランの実装欠陥を 1 件止めた。** プランは
  `supply.evidence["comparison"]` を添字参照していたが、gate は production 発行の**赤** supply を
  正当な record として返し、その evidence に `comparison` key は無い。添字だと `verdict_s6` が
  `KeyError` で脱出し、fail-closed の inconclusive が process 失敗に変わる。`.get` へ直した。
- 相談はさらに、負例が恒真になる 2 経路を止めた。第 3 の組の fixture は `stock_comparison=False`
  でないと evaluator の前段で落ちる。交叉の負例は gate 層を中和するだけでは足りず、交叉 family から
  作り直した受領証を渡さないと受領証一致検査の手前で拒否され、probe の述語に到達しない。
- **親 brief の誤りを 4 点、相談が正した。** (1) 成果物影響は「先行条件を通過した観測では固定」が
  正しい。(2) 到達可能性の根拠は t316 自身の実測ではなく、A-5 の `backoff_sweep` が**同じ
  evaluator** で root-location-only の緑になった記録である。値が production で到達可能なことは
  示すが、t316 driver がその環境に置かれることは示さない — **限界として残す**。(3) 編集面は
  受入台帳を含めて 3 file。(4) literal SHA の pin は 0 件だが `HEAD:<path>` を key にした実行時
  pin は存在するので「pin は無い」とは書けない (commit 後に自動で新 blob へ束縛される)。
- 受入所要台帳について、相談は「`nodeid_count` が合わないと受入が赤」と述べたが**これは誤り**。
  実際の関門は 90% 被覆の 1 件だけで、gate 側の root-location-only test は今も台帳に無い。
  親は段 4 で重大度を下げて採用したが、段 7 で D1152 (定期更新の担い手は land 側) を引き当てて
  **不採用へ倒し、これが誤りだった**。そのとき書いた「追加後の被覆 20042/20047 = 99.98%」は
  分母を取り違えた計算で、被覆の分母は台帳 entry 数ではなく collection の node 数である。
  受入全走が `test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` を
  **89.991874% (19935/22152)** で赤にした。5 件を除くと 90.0122% なので**赤は本 wave に帰属する**。
  正本 producer (`--add-only` + 本走の JUnit) で是正した (commit d44bc8a01、20042 → 22118、
  既存値・bytes 不変、0.0 placeholder 0 件、更新後 99.363489%)。
  **D1152 が言う land 側の実装は land tool に存在せず、閾値を割った wave が直すほかない。**
  F67 の 3 件目 (near-miss) として追記した経緯は、この受入赤で「near-miss」ではなくなった
  — 実際に受入 1 巡と Codex 子 1 本を余分に費やした。
- 段 8 の自己改善候補は 2 件。(1) 上記の担い手検索 → F67 追記。義務の `DW-S04` への追加は
  L1 予算の空きが 0 bytes と既に実測されているため裁定へ返す。(2) 変異 spec の必須 field
  (`expected_status` / `hang_risk`) が `DW-M01` / `DW-M08` に書かれておらず初回 `--plan-only` が
  rc=2 になった件 — harness が欠落 field を名指しで返すため予算を使う価値がないと判断し**不採用**。
- 段 6 レンズ D は「root-location-only family を 3 回生成するので 1〜3 秒の重複」を nit としたが、
  **実測では追加所要が観測されなかった** (単独走 122 passed / 4.50s → 127 passed / 4.44s)。
  fix は当てていない。
- 変異 matrix は 4 変異すべて KILLED、期待 node 完全一致、MISMATCH 0 / SURVIVED 0、erratum なし。
  直積判定への緩和 (m02) は gate が交叉を先に弾くため、gate 層を中和した test だけが殺せる。
- 工数: codex 子 6 本 (plan 1 / consult 2 / author 1 / review 2、いずれも gpt-5.6-sol、
  plan・consult は reasoning=xhigh、author・review は docs 権威の effort)。fix 巡回 0 (must-fix ゼロ)。

## 次の一手差分

### 完了

- [T-2314] D1625 を実装した。probe は inert 比較の緑を gate の表が定める組 2 つのどちらか 1 つで
  受理し、発火した組を受領証へ記録する。正例 2・負例 3 と事前登録変異 4 件 (全 KILLED) を伴う。
  remaining: none
  base: 4b21e0eefd8122f3a4c460533089fa477739a8a58d2eed56ae8260b480b88254

### 新規

- {{T:t316-bound-path-index-drift}} **P1・新規**: `t316_sandbox_backend_probe.py` の
  `_execution_binding` が runtime PBS spool の bytes を `_BOUND_RELATIVE_PATHS[1]` と比較するが、
  index 1 は `.py` であって `.pbs` ではない (`.pbs` は index 2)。この行は commit `5e12db6ce` で
  index 1 が `.pbs` だった時点に書かれ、commit `0218acc61` が
  `orchestrator/campaign/condition_meaning_gate.py` を tuple の先頭へ足したときに 1 つずれた。
  次に計算ノードで probe を走らせると `runtime PBS bytes differ` で落ちる見込み。
  成果物影響 = [T-2314] が塞いでいた関門を開けても、この 1 点で t316 の再実測は始められない。
  段 6 敵対レビューが指摘し、親が git 履歴で裏取りした。
- {{T:t316-root-location-reachability}} **P2・新規**: t316 driver 自身が
  `stock-inert-preprocess-root-location-only` の緑に到達する環境を、本 commit を束縛した
  計算ノード probe で実測する。現在の根拠は A-5 の別 driver が同じ evaluator で到達した記録で、
  t316 実経路の実測ではない。成果物影響 = 実測しない限り「新しい理由コードで関門を通せる」は
  構成可能性の主張に留まる。{{T:t316-bound-path-index-drift}} の後に行う。
