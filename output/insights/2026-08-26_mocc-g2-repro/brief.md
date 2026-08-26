# 段 1 brief — dev-wave-mocc-g2-repro-20260826

- base main: `b0c1a8bd` / branch `worktree-dev-wave-mocc-g2-repro-20260826`
- 対象: [T-1892] (P1)、[T-1894] (P2)。**[T-1893] は裁定待ちなので触らない。**

## scope

1. **[T-1892] MoCC TRACE=1 の反復による G2 再現率の測定。** 反復数・分母・判定規則を実走前に
   凍結して commit し、その commit を outer identity として本走する。得た結果は
   `official_certification=false` のままで headline・certified 選択・floor・oracle・fitness の
   根拠にしない。**成果物影響:** 実装しなければ §8 C-1 の「MoCC の性質か trace hook の
   取り違えか未確定」が未確定のまま残り、mocc 由来の証拠を将来 certified 側へ入れる判断ができない。
   実装しても certified 選択・floor・oracle・fitness の値は 1 つも動かない (使わないため)。
2. **[T-1894] provenance 残件 3 件。** (i) TRACE=1 receipt から計数 field
   (`workload.completed_txns` / `workload.elapsed_s`) を除去し、性能値を算術で導出できなくする。
   (ii) live 判定器の TOCTOU — job は判定前に outer HEAD と clean を 1 度検査するだけなので、
   判定後の再検査を足して両方を receipt へ束縛する。(iii) pair checker の `checker.sha256` が
   自己申告なので、outer commit の git blob を外部 trust anchor にする。
   **成果物影響:** (i) は TRACE=1 receipt の bytes と pilot receipt schema version を変え、
   規律 1 の観測者効果分離を「宣言」から「導出不能」へ上げる。(ii)(iii) は pair checker の
   受理集合を狭める (現行 accepted な receipt が新 checker で拒否されうる)。
   放置すると mocc 由来 receipt の provenance 主張が恒真に近いまま残る。

## 確定済みユーザー裁定・不変条件

- 規律 2 は緩めない。anomaly が出たら理由を構造化して返すだけで、verifier の受理集合は変えない。
- 規律 1: TRACE=1 は正しさ専用、TRACE=0 は性能専用。両者を混ぜない。
- `prohibited_uses` が宣言であって強制ではない点を記録する ([T-1893] の consumer gate は作らない)。
- push・remote 操作なし。`docs/pegasus-runbook.md` と `tools/pegasus/admission_registry.json` は
  稼働中 b10 系 2 wave と編集面が当たるので触らない。

## 実測した前提 (段 1 前)

- 依頼文の「同一 source 4 本中 1 本」は正しいが、**4 本は 2 つの異なる outer commit にまたがる**
  (`97906410` の 3 本 + probe `949555` の outer `e29084e0` の 1 本、ccbench は同じ `058d0c4e`)。
- TRACE=1 の 1 本は queue 待ち込みで約 85 秒 (`949961`: submit 1787735041 → 完了 1787735142)。
  予算残 13,428 / 16,000 点。前 wave は 6 本並行投入が全部通った。
- 生死確認 (DW-G01) として `950267.nqsv` を投入済み。**これは凍結前の probe なので本走に入れない。**
- G2 の 2 トランザクションは**別スレッド** (txid 515615 = thid 40 / commit `(53,2868)`、
  txid 515616 = thid 21 / commit `(53,2869)`)。**同一スレッドの連続 trx の取り違えという仮説は消えた。**
- pair receipt を bytes で pin する台帳・test・trust root は 0 件 (DW-O09)。参照は
  `docs/paper-story/README.md` の本文のみ。FROZEN_MANIFEST に mocc 項目は無い。
- 同型の再現率スタディの既存被覆は 0 件 (worklog / archive を「再現率」で全文検索)。純増である。

## 親の provisional 裁定 (攻撃対象)

- **(P1) 反復数 N = 30、3 batch × 10 本、batch は前 batch の完了後に投入する。** 分母は
  verifier が verdict を出した本数 (certified + non-serializable)。verdict 前に落ちた本
  (build / hydrate / walltime / scheduler) は分母から外し、失敗段階つきで全件報告する。
  推定は Clopper-Pearson 95%。**結果を見てから本数を足さない・値で捨てない。**
- **(P2) [T-1894] を同 wave で実装し、修正後の job script で本走を取る。** 1 つの source identity で
  30 本を揃えるため。probe で生死を先に確かめてから本走に入る。
- **(P2) 対照アーム (silo TRACE=1 を同 workload で同数) は本 wave の scope 外。** 別 submitter が
  要るため。ただし段 2 が安い経路を見つけたら再裁定する。
- **(P2) 第 3 の分岐を明示する** — 「MoCC の性質」「trace hook の記録ミス」に加え、
  **verifier の `(epoch,tid)` 全順序仮定が MoCC の TID 生成規則で成り立たない**可能性がある。
  本 wave では**読んで記述するだけ**とし、verifier は一切変えない (規律 2)。

## 成果物の形

`output/insights/2026-08-26_mocc-g2-repro/` に事前登録 (凍結 commit)、結果 md、
per-run の構造化台帳 JSON。spool fragment (worklog / decisions / failures)。

## 並列分割

段 2 は 1 本 (事前登録 + [T-1894] 実装計画)。段 3 は 2 レンズ (統計設計 / 受理集合と規律 1・2)。
段 5 は所有を (A) job script + receipt schema、(B) pair checker の trust anchor に分ける。

## 変更面 (実アンカー)

| path | 現在の状態 | 触る理由 |
|---|---|---|
| `tools/pegasus/mocc_trace_pilot.sh` | 1514 行、`completed_txns` は 1391 行、`elapsed_s` は 1393 行 | [T-1894](i)(ii) |
| `orchestrator/campaign/mocc_trace_pair.py` | 791 行、`PAIR_SCHEMA` は 18 行、`checker` block は 715 行 | [T-1894](iii) |
| `orchestrator/tests/test_mocc_trace_job_contract.py` | 既存 | 上記の検査 |
| `orchestrator/tests/test_mocc_trace_pair.py` | 既存 | 上記の検査 |
| `output/insights/2026-08-26_mocc-g2-repro/` | 新規 | 事前登録・結果・台帳 |
