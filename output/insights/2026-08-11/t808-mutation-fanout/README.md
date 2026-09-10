# [T-808] 変異本走の N-job fan-out — 逐語と変異台帳

wave branch `worktree-dev-wave-t808-mutation-fanout`、実装 anchor `3c01faa5`。
裁定と実測の全文は repo 外の wave dir
(`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t808-mutation-fanout/`) に置いた。

## 変異 matrix — 2 走 6 ベクトル

`registered == recorded` は両走で成立し、baseline はどちらも `PASSED`。

| ID | 撃った gate | 期待 | 実測 | 判定 |
|---|---|---|---|---|
| M01 | `TIMEOUT` record の専用拒否 (裁定 R1) | KILLED | **KILLED** | 一致 |
| M02 | shard 内 collection 自己整合 (`collected_nodes` 対 stdout 再導出) | KILLED | **SURVIVED** | **erratum** |
| M03 | manifest 期待 path との照合 (裁定 R2) | KILLED | **KILLED** | 一致 |
| M04 | `nonterminal_history` の `TIMEOUT` 拒否 | SURVIVED | **SURVIVED** | 一致 (被覆の穴) |
| M05 | **shard 間** `collected_nodes` 一致 (M02 の再照準先) | KILLED | **KILLED** | 一致 |
| M06 | collection への expected node 包含検査 | SURVIVED | **SURVIVED** | 一致 (被覆の穴) |

**M02 の erratum (`DW-M02` に従い初回結果を消さない)。**
M02 は「shard 間の一致検査を撃った」つもりだったが、実際に撃ったのは
**各 shard 内の自己整合検査**であった。テストは `collected_nodes` と stdout を整合させたまま
負例を作るため、この層を壊しても誰も落ちない。**実効 gate は別の層にあり**、
そこへ再照準した M05 は期待どおり KILLED した。**M02 の対象層は被覆されていない。**

## 実証されたこと

- 段 4 裁定 **R1** (queue 待ちが `TIMEOUT` に化ける経路を fan-out 側で塞ぐ) の gate は
  **単一理由で実効**である (M01)。
- 段 4 裁定 **R2** (path は pairwise DIFFER でなく manifest の期待値と照合する) の gate も
  **実効**である (M03)。
- 設計時に「無料で強い」と見込んだ **shard 間 `collected_nodes` 一致検査は実効**である (M05)。

## 実証されなかったこと (被覆の穴 3 件)

いずれも **production の欠陥ではなく、テストが触れていない**という事実である。

1. shard 内 collection 自己整合 (M02 の対象層)
2. `nonterminal_history` の `TIMEOUT` 拒否 (M04)
3. collection への expected node 包含検査 (M06)

**この 3 件は「gate が無い」ではなく「gate はあるが赤くなる負例が無い」である。**
埋めるかどうかは別タスクの判断とし、本 README を根拠に起票する。

## 生死確認 (`--plan-only`) の射程

別 scratch root の 2 shard 同時 `--plan-only` は両方 rc=0、同一 scratch root では 2 本目が
rc=125 `container が既に存在するため所有を拒否` で fail-closed になった。N=4 の同時
`--plan-only` も 4 本とも rc=0 (39 秒、残渣なし)。

**`--plan-only` は pytest / qsub / receipt / evidence relocation / teardown を通らない。**
したがってこれは **scratch と lock の分離機構の確認**であって、
**fan-out 本走が N で成立することの実証ではない。**exact-N の本走実測は別タスクとする。
