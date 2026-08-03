# 段 4 裁定

## 総裁定

**本 wave では生死確認 (transport smoke) までを実施し、恒久実装は行わない。**
設計択一と blocker はユーザー裁定パッケージで返す。

根拠は 3 つ。

1. 段 3 の独立 2 レンズが**両方とも恒久実装を NO-GO** と判定した。レンズは互いを見ていない。
2. blocker に**ユーザー裁定そのもの**が含まれる (D105/D117 の supersede 要否)。
   `DW-S04` は「未裁定または大きい変更を既成事実にせず、裁定パッケージとしてユーザーへ返す」と定める。
3. ユーザーの依頼自体が「恒久実装の**前に**生死確認を取る」であり、この着地はその指示に忠実である。

段 5・6 を飛ばす `4→7→8→9` は採らない。生死確認の driver は実行可能な script = 実装面なので、
`role=author` の codex 実装子が書き、親が走らせる。production コードの差分は作らないため
**変異 matrix は対象外**とする (先例: (118) の [T-139])。

## 所見の real / refuted と採否

### 採用 (生死確認の設計へ反映する)

| # | 所見 | 裁定 | 反映 |
|---|---|---|---|
| A1 | 提案 G01 の walltime 20 分は hard bound (5 走 × timeout 300 s) 未満 | **real** | 全走化に伴い walltime を実測ベースで再計算し、余裕を明示的に積む |
| A3 | kill window が閉じておらず、dirty tree からは resume 不能 | **real** (既存設計、F32 のとおり) | **使い捨て worktree で走らせる**。wave worktree と main を汚さない |
| A6/B12 | targeted `-n 0` の 3 node 走は「全走で verdict 不変」の証明にならない | **real** | **全走 (`tools/run_tests.py -rf -p no:cacheprovider`) で走らせる**。targeted へ縮めない |
| A7 | collection は dispatch だけ `-n 0` を足し、local 経路は既定 48 になる (`mutation_harness.py:928-942`) | **real・重大** | これは**まさに生死確認が暴くべき差**である。隠さず全走で観測する |
| A10 | 2.7 h の導出標本に選択バイアス | **real** | 全 41 record から再集計済み。下記「訂正した実測値」 |
| B14 | §C の変異候補は old 逐語 count=0 の設計メモであり事前登録ではない | **real** | 恒久実装をしないので事前登録は行わない。台帳に「対象外」と射程を明記する |

### 採用するが本 wave では実装しない (裁定パッケージへ)

| # | 所見 | 裁定 |
|---|---|---|
| A2 | 親 dispatcher の overall-timeout → `_best_effort_qdel` が**走行中**のジョブを qdel する (`dispatch_compute.py:1182, 1381`)。queue 待ちが running walltime を食う | **real・既存欠陥**。今日の dispatch 経路にも存在。束ねでは発火確率が跳ね上がる |
| A5/B | Lustre の cross-node flock は未確認。silent fail-open なら二重注入で verdict が非決定になる | **real・blocker**。実測が要る |
| B1/B2 | 第 3 task の追加には D105 supersede + D117 の 4 契約が要る | **real・ユーザー裁定事項** |
| B3 | `_job_run` の child は `os.environ.copy()` を継承するため、requested env の allowlist は実効契約にならない | **real** |
| B5 | `mutation_harness.py` を `_SANCTIONED_PATHS` へ足してはならない (login 直 local run を許してしまう) | **real**。親も提案していない |
| B8 | transport 証拠が gitignore 下にしか残らない | **real** |
| B4/A6 | mutation task の test command が canonical 全走に固定されていない | **real** |

### refuted / 縮小

| # | 所見 | 裁定 |
|---|---|---|
| 親 brief の「lock 保証が実質ゼロ」 | **過大**。正しくは「同一 node・同一 tempdir・同一 resolved repo path でのみ有効」。bnode 間で消えるという運用上の結論は正しい |
| 親 brief の「task 追加は採用済みパターンに乗る」 | **誤り**。D117 決定 (4) 本文で親が裏取り済み。訂正する |
| 親 brief の「baseline も同じ overhead を払う」 | **誤り**。実測は 22.7 s |
| A4 の「shared lock の移行窓」/ A9 の「lock 配置」/ B6-B11 | いずれも **real だが恒久実装に付随する**。実装しないので本 wave の scope 外 |

## 訂正した実測値 (全 41 record、選択バイアスなし)

`output/insights/2026-08-02_t243-parallel-docs-spool/mutation-ledger.json` の
`artifact.stdout` 全文から再集計した。

| 量 | 値 |
|---|---|
| 変異 1 件の総所要 | median 467.045 s |
| うち内側 pytest | median 238.380 s (min 227.610 / max 279.870) |
| **差 = scheduler overhead** | **median 228.424 s** (min 23.482 / max 238.360) |
| baseline の overhead | 22.686 s (即時開始した 1 例。「毎回 230 s」ではない) |
| collection | 226.653 s。`--collect-only` は `in Xs` 行を出さないので内訳を分離できない |
| **43 走の総 overhead** | **9161.6 s = 2.545 h** |

## 生死確認 (transport smoke) の確定仕様

**名前を「生死確認 (transport smoke)」とする。** これは移設全体の安全性の証明ではなく、
「transport を変えて verdict が変わらないか」の最安の生死判定である (レンズ A6/B12 の指摘を受けた明示)。

- **場所**: 使い捨て worktree を anchor commit へ新設し、そこで走らせる。
  wave worktree と main は変異させない (A3)。
- **spec**: `tools/spool_fold.py` の 3 guard (`:608` filename 不一致、`:729` symbol 重複、
  `:744` malformed placeholder 残留)。段 5 で old 逐語 count=1 と期待 node の collect 実在を機械確認する。
- **test command**: **canonical 全走** `tools/run_tests.py -rf -p no:cacheprovider`。縮めない (A6/B12)。
- **leg 1 (現行)**: `--runner-mode dispatch` を、外側上限のない background から起動。
- **leg 2 (束ね)**: 使い捨て qsub script (100 行以内) から `--runner-mode local` で 1 ジョブ。
  walltime は 5 走 × 実測 240 s に停止・復元余裕を積んで決める (A1)。
- **合否条件 (事前確定、事後解釈しない)**:
  - 一致を要求する射影 = 各 mutation の `{id, status, failed_nodes, matches_expectation}` の順序付き完全一致、
    かつ `repo_head` / `spec_sha256` / record 数 / baseline `PASSED` の一致。
  - 一致しない場合は **NO-GO** とし、差分の原因 (特に collection の並列度差 A7) を台帳へ記録する。
  - 比較対象から外す = `runner_mode`、per-record receipt path、`duration_s` (経路差そのもの)。
- **不一致でも成果**: A7 の collection 並列度差が実際に verdict を変えるなら、それは恒久実装の
  設計を変える一次証拠であり、この wave の主要な成果物になる。

## DW-G05 成果物影響

- 生死確認を**実施しない**場合: 恒久実装の設計択一を、実測なしでユーザーへ返すことになる。
  「束ねても verdict が変わらない」は誰も確かめていない仮説のままで、裁定の材料が欠ける。
- 恒久実装を**この wave で強行した**場合: cross-node flock が silent fail-open なら二重注入で
  変異台帳の `status` / `failed_nodes` / 復元後 bytes が非決定になり、
  D105/D117 を未裁定で supersede すれば計算ノード受理 task 集合が 2 → 3 へ黙って広がる。

## 分割

- **段 5 実装子 (codex `role=author`, workspace-write) 1 本**: 生死確認の driver 一式を job dir へ書く
  (spec JSON、anchor 検証、両 leg の起動 script、verdict 比較 script)。repo は編集しない。
- **親**: 使い捨て worktree の作成、両 leg の実走、比較、記録、commit。
- **段 6**: 焦点レビュー 1 本 (「この smoke は本当に transport 同値を示したか」)。
  production 差分ゼロのため敵対レビュー 2 本は課さない (`DW-C00` の docs-only 相当)。
