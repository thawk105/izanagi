# 段 1 brief — [T-2519] [T-2505] t316 実経路の inert 要求到達性を計算ノードで実測する

- wave: `dev-wave-t2519-t2505-t316-inert`
- branch: `worktree-dev-wave-t2519-t2505-t316-inert`
- worktree (子が読む repo root): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert`
- 起点 main / HEAD: `3b80b5a96589e30bd22410c9e2d7b4cb77d9e13a`
- 日付: 2026-09-14

## 研究前進 (土台)

D1856 が adaptive const probe (`tools/pegasus/probes/t2187_adaptive_const_probe.py`) の build 地点を
条件関門へ配線することを繰延べており、その解除条件 2「inert 要求が supply effectuation の緑へ到達する
ことの計算ノード実測」は誰も測っていない。本 wave はその前段として、**既に条件関門が配線済みの
唯一の計算ノード driver である t316 probe** で inert 要求が緑へ到達するかを実測する。
最小差分 = 本 commit を束縛した t316 probe job を計算ノードへ 1 回投入する (実装面ゼロ見込み)。

完了判定 = receipt の `condition_gates` に supply entry が 1 件現れ、その `reason_code` と
`comparison` が実測値として記録されること。緑でも赤でも実測は成立する。

## scope

1. 本 commit を束縛した t316 probe job を計算ノードへ投入し、S6 の条件関門が `BACKOFF_FIXED=-1`
   (inert 値) の supply effectuation でどの理由コードへ到達するかを実測する。
2. 結果 (緑/赤・reason code・comparison・到達 stage) を insight と 3 台帳 fragment に記録する。
3. 実測が T-2519 と T-2505 のどちらを満たし、どちらを満たさないかを証拠に基づいて判定する。

**scope 外** (依頼が明示): 13 macro への runtime meaning witness 新設、t2187 probe の条件関門配線、
D1856 の繰延べ解除、仮想リスク向けの gate・検査・台帳・一般化の追加。

## 確定済みユーザー裁定 (逐語は同 dir の別 file)

- **D1936 項17** (2026-09-10、対象 T-2213 / T-2519): D1856 の繰延べを維持し、まず既存機構で inert
  要求が stock 同等の緑へ到達するかを計算ノードで実測する。13 種類の witness 新設も、未確認のまま
  supply だけ先に配線する案も採らない。T-2518 の先行実測は維持する。
- **D1856** (2026-09-09): 繰延べ解除条件 2 件 (1: 13 macro の runtime meaning witness の実在、
  2: patch stack を当てた木の inert 要求が supply effectuation の緑に到達する計算ノード実測)。
- **D1625** (decisions.md:49855): t316 probe の inert 緑は新旧 2 契約
  (`stock-inert-preprocess-identical` + `stock-inert-identity`、
  `stock-inert-preprocess-root-location-only` + `stock-inert-root-location-only`) の
  どちらか 1 つに exact 一致することだけを許す。それ以外の緩和はしない。
- **D1849**: 発火した組を receipt の supply entry へ `comparison` scalar field として記録する。

## 親の provisional 裁定 (攻撃対象)

- **(P1-1)** T-2519 の「既存機構」は t316 probe の `BACKOFF_FIXED` inert 要求を指し、T-2505 と同じ
  probe 1 回で両方満たせる。T-2518 (t2187 の A+B+C patch 木) は D1936 が別項として維持しており
  重複しない。
- **(P1-2)** 今の main の probe は無改変で S6 の条件関門まで到達し、実測が得られる (実装面ゼロ)。

## 不変条件

- **絶対規律 2 を緩めない。** 関門を通すためだけの修正で偽の緑を作らない。赤なら赤を事実として記録する。
- probe の受理集合 (D1625 の 2 契約 exact 一致) を緩めない。`condition_meaning_gate.py` と
  probe の bytes を変えない。
- **job 走行中は worktree の HEAD と BOUND_PATHS 5 件を変えない。** probe の `_execution_binding` が
  投入時 commit を束縛し、BOUND_PATHS の dirty を拒否する。走行中に書いてよいのは `output/` 配下だけ。
- 実測環境 = Pegasus 計算ノード (`gen_S`、1 node、walltime 01:30:00)。login node では CCBench の
  依存 (gflags / glog) が無く CMake configure が止まる (T-2213 wave の実測、
  `output/insights/2026-09-09/t2213-probe-condition-gate/README.md`)。投入元は本 worktree。

## 成果物の形

- `output/env/pegasus/t316-sandbox-backend/<PBS_JOBID>/receipt.json` + `COMPLETED`
  (計算ノードが worktree 内へ書く)
- `output/insights/2026-09-14_t2519-t2505-t316-inert/` の insight README (到達判定・reason code・
  comparison・限界・この実測が保証しないこと) と verbatim 一式
- `docs/spool/` の worklog fragment、必要なら decisions fragment

## 変更面 (実アンカー)

実装面の変更を予定しない。予定する編集は上記 docs / insight だけである。

## 並列分割方針

軽量版を基本とするが、(P1-1) の解釈が割れうるので段 2 (plan) と段 3 (敵対相談 2 レンズ) は省かない。
段 5 は実装面が必要と判明した場合だけ起こす。job は brief 確定直後に投入済み
(`996644.nqsv`、2026-09-14)。queue 待ちの間に段 2 / 3 を回す。

## 成果物影響 (DW-G05)

実測しない限り「新しい理由コードで t316 の関門を通せる」は構成可能性の主張に留まり、D1856 の
繰延べは解除の証拠を 1 つ欠いたままになる。結果として adaptive const probe の build 地点 2 件は
条件関門の外に残り続け、その driver が出す成果物は supply effectuation の機械証拠を持たない。
