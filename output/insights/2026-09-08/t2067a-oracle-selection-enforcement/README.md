# [T-2067] (a) oracle report / verdict / judge へ床値選択規則の再強制を入れる

- 日付: 2026-09-08
- branch: `worktree-dev-wave-t2067a-oracle-selection`
- 実装 commit: `95e8d6a8d`
- ユーザー裁定: D1526

## 何をしたか

公式 CLI の 3 経路 (`s8b_oracle_report.py` / `s8b_oracle_judge.py` / `s8b_verdict.py`) の
`main()` で、`load_ratified_freeze` の直後・historical reverify の前に
`assert_g1_floor_selection_identity(ratified, root)` を呼ぶようにした。

## 穴の実体 (現物で確認)

強制の本体は `s8b_ratified_freeze.py` の `_launch_validate` の中の
`if result_type is LaunchValidatedFreeze:` の枝にしかない。3 経路が使う
`reverify_published_freeze` は `result_type=ReverifiedFreeze` で同じ関数を呼ぶため、
この枝に入らない。D1503 が「historical reverify は選択 identity を実行しない」と述べた事実が
そのままコードで確認できた。実走経路 (`s8b_oracle_driver.py` の 2 か所) は `launch_validate` を
通るので強制済みであり、同 file の gate core 内の load は private で独立の入口ではない。

## 凍結 pin の閉包 (DW-O09)

4 軸すべてを引いた。詳細は `verbatim/addendum-pins.md`。

- **払った pin は 1 か所だけ** — `orchestrator/tests/test_s8b_oracle_manifest.py` の
  `PIN_GATE_SPEC_RAW` に report / judge の source sha256 が literal で焼かれており、
  `PIN_GATE_SPEC_SHA256` はその blob の sha である。実 file から再計算した値へ再 pin した。
  - report: `f7ef6259f8fe...` → `30fe2b1bcad1...`
  - judge: `0e6276ddcb6c...` → `f3e2fbec0d9d...`
  - 外側: `58190f7b402e...` → `63cd82787ebe...`
- **production 側で有効な凍結 pin は 0 件。** `APPROVED_SPEC_SHA256` は `None`、
  `output/s8b-oracle-spec/` も `output/s8b-oracle-manifest-candidates/` も存在せず、
  発行済みの公式 manifest も無い。**成果物の再発行は発生しない。**
- `s8b_verdict.py` は `_GENERATOR_SOURCES` に含まれず、source hash の literal も repo に無い。
- 構造 pin (呼び手集合・呼出し回数・guard 式・行番号) は掛かっているが、
  今回の追加行では発火しない。実測でも `test_s8b_oracle_manifest_contract.py` と
  `test_official_perf_closure.py` は緑だった。

## 段 4 で裁定した争点

`verbatim/ruling-stage4.md` が正本。

- **採用 (must-fix) 3 件**
  - MF-1: 負例の earlier result を走査中立 (`b"{}"`) にする。選択済み result の bytes を
    複製すると全 repo 走査の `closure-hit-mismatch` が強制を消しても同じ入力を弾き、
    「1 行消すと受理される入力」にならない。既存先例 (`test_s8b_oracle_manifest.py` の
    real-g1 テスト) は reverify を呼ばない経路なので、**そのまま写すと壊れる。**
  - MF-2: verdict の既存 2 テストは純 no-op でなく D1504 の**記録 stub** にする。
    D1504 は「loader と選択 assert の両方を stub する」を名指しで却下している。
  - MF-3: R / J の変異の期待 node に pin test 2 件を必ず含める (F226 と同型)。
- **却下 2 件**
  - real-repo 登録簿への新規登録は不要。ヘルパを持つ suite 自身も既存先例も未登録で、
    登録簿は独立 golden と exact 一致で緑である。**実測でも `test_real_repo_serialization.py`
    は緑だった** (静的読解だけで却下していた判断が裏付けられた)。
  - `verify_manifest` → library core の迂回口は残件 (c) の射程。下記「残す非対称」を参照。

## 実測

- 焦点走 (report / judge / verdict / manifest / real-repo-serialization / manifest-contract):
  **556 passed, 1 skipped**。
- consumer test (driver / official-perf-closure / binding-driftguards / materialization /
  oracle-artifacts / s8c-preregistration-predicates): **438 passed, 8 skipped**。
- `python3 tools/check_ai_provenance.py`: rc=0、新規違反なし。
- **変異 matrix: baseline PASSED・KILLED 11・SURVIVED 0・MISMATCH 0・期待 node 完全一致 11/11。**
  期待 node は probe 走の実 collection から取った (推測で書いていない)。

### 変異が示したこと

- `R1/J1/V1-REMOVED` (強制の 1 行を `pass` へ) が各経路の負例テストを赤にした。
  **MF-1 が要求した単一帰属が実測で成立した。** 実装子 3 本は dispatch の infra 失敗 (rc=16) で
  この確認を果たせず、親が probe 走で測った。
- `V1-REMOVED` は D1504 の記録 stub にした既存 2 テスト (計 5 node) も赤にした。
  **純 no-op に倒していれば、この 5 node は gate 削除を検出できなかった。** MF-2 の効き目の実測。
- `P1-STALE-PIN` (report hash を旧値へ戻す) はちょうど pin 2 node だけを赤にした。再 pin は効いている。
- `PC1-OVER-REJECT` (強制を無条件 raise にする過剰拒否の正例) は 16 node を赤にした。
  受理集合を縮小する wave の正例として登録済み。

## 受理集合の変化

- **新たに拒否される**: active freeze が g1 で、load と historical reverify は通るが
  床値選択 identity を満たさない公式入力。3 経路とも `floor-selection-rule-mismatch` /
  `floor-selection-eligibility-underivable` / `floor-selection-unverifiable` で rc=2 になる。
- **変わらない**: 選択済み result が最古の eligible official run である正常な g1。
  report の legacy manifest 経路 (official exact-type 分岐へ入らない)。
- **非 g1 について**: 本強制は `generation_number != 1` では何も観測せず返る。
  非 g1 が 3 経路で受理されないのは**従前どおり後段 reverify の
  `certificate-generation-scope` の責務**であり、本 wave はそこを変えていない。
  段 1 brief の「非 g1 の受理は変えない」という書き方は誤解を招くので、この記述へ訂正した。

## 残す非対称 (残件 (c) の材料)

段 3 の 2 レンズが**独立に**同じ指摘をした。`verify_manifest` は選択未強制の freeze から
封印 token を発行でき、`build_observations` → `judge_oracle` → `verify_oracle_verdict` →
`judge_combined` を library として呼べば、3 CLI の gate を一度も通らずに同種の official artifact へ
到達できる。**「全層の非対称を閉じた」とは主張しない。**

本 wave で実装しなかった理由は、D1526 が名指ししたのが 3 経路であること、公開迂回口の一般化は
残件 (c) の主題で「(a) の着地後に続く」と台帳で決まっていること、repo 内の production caller は
現に 3 CLI に閉じており `test_s8b_oracle_manifest_contract.py` の `VERIFY_EXPECTED_CONSUMERS` が
4 file の完全一致で pin しているため新しい consumer は inventory を赤にすること、の 3 点である。

段 3 のレンズ B はもう 1 件、`p3_autonomous_workload_trial.py` の dormant な load-only 経路
(選択未強制の ratified freeze を C06 budget へ渡す) を挙げた。schedule authority が無条件に
送出するため今日は ledger / report へ到達不能であり、残件 (b) の裁定候補に留める。

## 次 wave の出発点

残件 (b) 母集合の数え直し、(c) 公開迂回口、(d) 導出被覆の穴。いずれも (a) の着地後と決まっていた。
(c) には上記「残す非対称」の到達経路 4 段が具体的な材料として使える。
D1241 / D1313 の advisory / non-certifying 上限は本 wave でも解除していない。
