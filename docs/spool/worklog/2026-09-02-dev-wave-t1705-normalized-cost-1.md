---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t1705-normalized-cost
seq: 1
title: [T-1705] 正規化 cost の生成物へ arm 間比較可能性を自己宣言させた (コード + テスト、branch worktree-dev-wave-t1705-normalized-cost、変異 11/11 検出・生存 0)
---

## 本文

- **依頼の前提は実測で覆った。** command 引数は「cost の値は生成されておらず、version の
  provenance が装置へ束縛されているだけ」と述べたが、部分正規化 cost の計算器は
  2026-08-25 に [T-1434] で既に着地していた。事前登録 §10 と
  `tools/codex_reasoning_ab.py` の `_normalized_cost_metadata` / `_normalized_cost_for_attempt` /
  `_aggregate_normalized_costs` の実コードが一致して裏付ける。したがって本 wave の純増は、
  依頼後半の「生成した値がどの arm 間で比較可能かを、生成物自身に書かせること」だけである。
  段 4 でこの前提を再裁定し、scope をその 1 点へ確定した。
- **既存 cost fixture は arm を 1 種類しか持っていなかった。** `_bound_price_schedule` の 2 slot は
  どちらも `arm="max"` で、arm 間比較を一度も覆っていない。これは段 3 の独立検証が指摘し、
  親がコードで裏取りした。arm 間比較可能性を扱う wave の土台としては空だったことになる。
- 段 3 の独立検証 2 本で 9 所見、段 6 のレビュー 2 本で 3 所見。**refuted はゼロ、
  すべて real と裁定した。** 特に重いのは 2 点。(1) 件数が揃っても観測できた試行の identity が
  arm 間で入れ替わっていれば paired 比較にならないため、`accounted_total_key` に
  status 別の `(block_id, attempt)` 集合が要る。(2) `basis_key` が比較 universe を識別しないと
  別成果物の行が同じ比較集合を参照し、実験間差を arm 間差として読む。
- scope 外と裁定した real 所見が 1 件ある。**cache write の未計上量が arm 間で系統的に違うかは
  判断できない。** 正規 receipt に数量 field が無いためで、扱うには receipt schema の
  新しい登録世代が要る (事前登録 §10 が未着手と明記)。本 wave の計算層 scope を越える。
- **変異は probe と本走の 2 段になった。** 1 回目 (spec sha256 `8e3e3a4d...bbe5`) は
  registered 11 / completed 11 / **SURVIVED 0** / TIMEOUT 0 / PARSE_ERROR 0 で、
  KILLED 5・MISMATCH 6。MISMATCH は実装の検出力不足ではなく親の期待 node 予測が不足しており、
  実測はいずれも期待の上位集合または近接集合だった。`DW-M08` に従い 1 回目を probe と明記し、
  実測 node で spec v2 (`e765e710...f196`) へ再登録した。**本走は 11/11 KILLED、
  MISMATCH 0 / SURVIVED 0 / TIMEOUT 0 / PARSE_ERROR 0 で rc=0。**
- **本走は計算ノードの queue 枯渇で 3 回 rc=16 になった。** `artifact_error` は
  `receipt scheduler_logs.stdout.path がない` で、実装の赤ではない。gen_S は待ち 49〜64 /
  実行 51〜53 / 保留 96〜100 の混雑が続き、既定 15 分の queue 待ちでは足りなかった。
  login node の `--runner-mode local` は harness が禁止するため迂回できない。
  `IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=2200` を設定した 4 回目の `--resume` で
  全件が通った。**この env override は待ち時間だけを変え、判定・受理集合には触れない。**
- **M01 (gate 化) は過剰決定である。** 15 node が落ちる。受理集合を守る層が既に複数あり、
  単独変異としての帰属は弱い。`DW-M03` に従い冗長 gate と明記し、単独変異の証拠から外す。
  M06 も既存の float 走査 test が同時に落とす。
- 実装子と fix 子はいずれも計算ノードへテストを投げられず (`rc=16` / `qstat` の socket 拒否)、
  正しく「実装済み・未実走」と申告した。**実走はすべて親が行った。**

## 次の一手差分

### 完了

- [T-1705] 正規化 cost の arm 間比較可能性を生成物へ自己宣言させ、変異 11/11 KILLED と
  焦点走 610 passed / 27 skipped で確かめた。
  remaining: none
  base: 45335a9c941bd0e2a7c0d51a770f3ec69d872f9950d09dc549af3e7fa2fb1231
