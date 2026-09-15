# 段 1 brief — [T-1338] 床値依存の残件

基底 local main `0600887d92538b3f34d894f9674d202d0a29a578`。branch
`worktree-dev-wave-t1338-floor-residual`。

## 研究前進

8b oracle の official 受理経路を開くための残作業の実体を確定し、誤った撤去で D1758〜D2013 の
床値凍結系列 (権威 floor の exact 有理数凍結・official 許可表) を壊すことを防ぐ。完了判定 =
T-1338 の残件が実装可能かを一次資料で確定し、実装可能なものは実装、不可能なものは根拠つきで
裁定へ返す。T-1338 は worklog 643 から 1501 まで P1 のまま持ち越されており、実体の確定自体が
後続 wave の空費を止める。

## 依頼引数と、実測で覆った前提 (段 4 で再裁定する)

依頼の破線節は「残った 3 件 = per-pair 床値対表の exact 検査 / `floor_budget_snapshot_sha256` /
oracle driver への `expected_perf_sha256` 供給」と書く。**この 3 件は 2026-09-14 の wave が
D1985 に従って撤去済みである** (worklog 1479)。破線節は撤去前の持ち越し文
(`docs/archive/worklog-phase3-0818-643.md:597`) の括弧内をそのまま写している。

一次資料が記録する実際の残件は 3 件で、いずれも**撤去**である
(`docs/archive/worklog-phase3-0914-1479.md:186`、insight README の U2)。

| # | 残件 | 現物 (実アンカー) |
|---|---|---|
| R1 | driver の floor/budget null refusal | `orchestrator/campaign/s8b_oracle_driver.py:524-527` (`floor-null` / `budget-null`) |
| R2 | budget の凍結数値 loader | `orchestrator/campaign/s8b_budget.py:96-118` (`load_oracle_limits`)、呼出しは同 `s8b_oracle_driver.py:1433` |
| R3 | report の解決経路 | `orchestrator/campaign/s8b_oracle_report.py:2548` (`assert_g1_floor_selection_identity`) |

## (P1) 親の provisional 裁定 — 攻撃対象

**(P1-a) R1 は既裁定が明示的に却下している。** D811 (2026-08-25、ユーザー裁定) の却下選択肢に
「床値を空のまま `floor-null` の拒否だけを個別に解く — 拒否は床値が無いことの正しい表現であり、
表現だけを変えると門が守っていた性質が失われる」がある。D1985 (2026-09-14) も「残すもの」に
「floor/budget の null 拒否と外形・budget 値・共有性の検査」を名指しする。

**(P1-b) R1〜R3 の撤去前提は D811 以降の系列に追い越されている。** 残件の出所は 2026-08-18 の
持ち越し文であり、その後 D811・D1716・D1717・D1758・D1759・D1808・D1819・D1831・D2013 が
「床値を official 経路で採り、exact な有理数で凍結し直す」方向を確定している。床値は消費を
やめる対象ではなく、正しく充填する対象になっている。R2 (`load_oracle_limits`) は freeze の
budget を現走行の資源上限へ射影するもので、過去値との比較ではない。R3 は D1984 (2026-09-14) が
現用として事実を記録している。

**(P1-c) 依頼の破線節どおりに読んでも実装対象は残らない。** 撤去済み 3 件の残骸を実測した。
`perf_sha_by_cell` は 0 件。`floor_budget_snapshot_sha256` の残存は
`orchestrator/tests/test_s8b_oracle_manifest.py:803` の**旧 key 拒否の負例 1 件だけ**で、これは
意図した受理形である。`expected_perf_sha256` は `orchestrator/campaign/pipeline.py:1565/2091`
の generic な optional gate として残り、production 供給元は 0 件だが、D1985 が
「名指していない・供給元を失うことは記録するが本 wave で直す欠陥ではない」と明示的に残した。

**(P1-d) 本 wave の provisional scope = 実装なし。** R1〜R3 の撤去はいずれも受理集合を広げ、
既裁定 (D811) と現行の床値系列に反する。依頼自身の「新しい受入条件を増やさない」とも、
撤去以外の読み (関門の再追加) は両立しない。よって成果物は **T-1338 の実体を確定する記録と
裁定パッケージ**とする。段 2・3 が実装可能な部分集合を示したら段 4 で覆す。

## 確定済みユーザー裁定 (緩めない)

D811 (floor-null 拒否を個別に解かない)、D496 決定 1 (凍結した過去値を比較の基礎にしない)、
D501 決定 7 (条件 3 は逐語凍結、再裁定が要る)、D1985 (残すものの名指し)。絶対規律 2 により
anomaly 検出 variant の即 reject は不変。

## 不変条件

- 受理集合を広げない。gate・検査・台帳・一般化を新設しない (依頼が scope 外と明示)。
- `s8b_verdict` の truth table と条件 3 に触れない。
- live な approved oracle spec 成果物は repo に存在せず (`load_approved_spec` は fixed-path
  literal 照合、official は `no-approved-spec` で fail-closed)、本 wave は凍結成果物の bytes を
  変えない。DW-O09 の pin 閉包は「変える対象なし」で閉じる。
- 3 台帳は直接編集せず `docs/spool/` の fragment にする。

## 成果物の形

`output/insights/2026-09-15/t1338-floor-residual/` に README (実体確定と根拠)、brief、段 2・3 の
逐語、段 4 裁定。worklog / decisions の fragment を `docs/spool/` へ。実装面差分は 0 を想定
(DW-S04 により実装面差分ゼロなら変異 matrix 免除、受入全走は免除しない)。

## 並列分割方針

実装なしを想定するため所有分割は不要。段 2 は read-only 1 本、段 3 は異なる 2 レンズ。
段 4 で実装ありへ覆った場合のみ、R1〜R3 を素集合の 3 単位へ分ける。
