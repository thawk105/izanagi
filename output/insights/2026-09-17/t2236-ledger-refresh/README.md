# [T-2236] 受入所要時間台帳を実測 JUnit から再生成した — refresh mode の追加と、偏りの真因 (group 連結成分の床) の実測

authority: none / default_effect: no-state-change (プロセス監査・逐語凍結。可変状態の正本は worklog 末尾と現行 phase doc)

- wave branch: `worktree-dev-wave-t2236-ledger-refresh`
- 基準 commit: `b4631a92ef…` (local main、wave 開始時に ff で揃えた)
- 実装 commit: `363e79b10466266c69270f2e785b3f967e4f0e63` (Codex `role=author`、3 file: 生成器 +65/−1、test +290、台帳 +16051/−14818)
- 受入: session `895f300ad85be224d08c276069903643` (tested main `8ccf47a3e` / tip `31c92c151`、**24530 passed / 67 skipped、child-green**)
- 起票: worklog archive 1214 の T-2236 項 (2026-09-02)
- 設計判断: 本 wave の decisions fragment (slug `acceptance-ledger-refresh-mode`、D 番号は land の fold が付ける)
- job dir (prompt・log・patch・親 script の原本): `/home/SFC/tanab/.claude/jobs/897c9a22/tmp/wave-t2236/`。親の集計 script は
  repo へ入れない (実装面の path 規約) — sha256: `analyze_shards_v2.py` `69ecdb86…`、`analyze_files.py` `2802594c…`、
  `setdiff.py` `e091e7b0…`、`frozen_snapshot.py` `740fcdbe…`、`verify_after.py` `57f32819…`、`make_mutation_spec.py` `f43fa936…`

## 何をしたか

受入 shard の割付器 (`tools/acceptance_shards.py::allocate`) は `orchestrator/tests/acceptance_duration_ledger.json` の所要値を
重みに使う。台帳は 2026-09-16 以降 `--add-only` (既存値を byte 保持して未登録 node だけ足す) でしか更新されておらず、既存 node の
値が陳腐化していた。段 1 で入力走 `d3ebafc0…` (06:31、rulings-all-20260917 = main 相当、0 fail / 0 error) を現行台帳で解析すると、
**台帳予測の shard 負荷は 5701 / 5700 / 5700 秒で均等なのに、実測の直列和は 8852 / 4433 / 4519 秒**。shard-0 の差 3151 秒の
内訳は既知 node の陳腐化 2932 秒 + 未登録 219 秒で、主因は凍結 8 suite の外 (`test_s8b_oracle_driver.py` +2126 秒、
`test_s8b_floor_campaign.py` +1289 秒)。既存 2 mode (全再生成 = T-1574 の exact pin を壊す、D1152 却下 / `--add-only` = 既存値を
直せない) では主因に届かないので、既存生成器 `tools/update_acceptance_duration_ledger.py` へ **`--refresh`** を足した:
凍結 8 prefix (`_ADD_ONLY_FROZEN_SUITE_PREFIXES`) の既存 entry は値ごと保持 (再量子化しない、JUnit に無くても残す)、それ以外は
入力 JUnit から全再生成 (値の置換・旧名の削除・新名の追加)、凍結 prefix の JUnit testcase は採用しない、描画は全再生成と同じ
canonical 形。`--add-only` と排他。既存 mode・閾値 0.90・凍結 prefix・除外集合・consumer は不変。

同 mode で台帳を `d3ebafc0…` の 3 shard JUnit から再生成した (author が producer を回し、親は検算だけ):
`preserved_frozen=426 / replaced=22593 / added=1360 / removed=126 / excluded_frozen_suite=615`、entry 23145 → **24379**、
現行 collection 24568 に対する被覆 23001 → **24361 (93.62% → 99.16%)**。凍結 426 entry 行は byte 一致、T-1574 の 8 suite identity・
12 値・removed 5 件の不在は不変、非凍結 23953 entry は JUnit の量子化値と完全一致、重複 0、値の合成なし、canonical 再描画一致
(`verbatim/parent-verify-after.txt`、18 項目)。

## before / after (受入 wall は 1 走の観測値。D357 により改善・退行・300 秒達成は主張しない)

| | session (投入元) | shard-0 wall | shard-1 wall | shard-2 wall | 実測直列和 (0 / 1 / 2) | 台帳予測 (0 / 1 / 2) | 未登録 node (0 / 1 / 2) |
|---|---|---|---|---|---|---|---|
| before | `6571431e` (t2067) | 344.3 | 236.3 | 201.5 | 8858 / 4388 / 4299 | 5687 / 5686 / 5686 | 435 / 349 / 741 |
| before | `fdcea8be` (t1449) | 348.6 | 245.2 | 205.4 | 8985 / 3972 / 4796 | 5676 / 5675 / 5675 | 536 / 410 / 546 |
| before | `35fa0ca1` (t2723) | 348.3 | 241.7 | 210.7 | 8480 / 4447 / 4612 | 5701 / 5700 / 5700 | 459 / 314 / 794 |
| before (入力走) | `d3ebafc0` (rulings-all = main 相当) | 351.0 | 238.5 | 202.7 | 8852 / 4433 / 4519 | 5701 / 5700 / 5700 | 459 / 314 / 794 |
| **after** | `895f300a` (本 wave、tip `31c92c151`) | **337.9** | **249.2** | **204.1** | 8569 / 4839 / 4799 | **7502 / 5328 / 5328** | 120 / 31 / 85 |

- wall は各 shard の JUnit `testsuite.time`。before は投入元も collection 件数も異なる 4 走で、同一 tip 3 走の中央値ではない。
  after との差 (shard-0 351 → 338、shard-1 238 → 249) は D357 の 10% 未満で「変化なし」の域。
- 台帳予測 = 各 shard で実際に走った node の refresh 後台帳値の和 (未登録は consumer と同じ 1.0 秒)。before 4 走の台帳予測は
  変更前台帳の値。consumer の `nodeid@group` fallback は 5 走とも hit 0 (`verbatim/parent-measurements-v2-*.md`)。
- 48 worker、計算ノード (Pegasus gen_S)、`python3 tools/run_tests.py` を `dev_wave_wait.py acceptance` 経由で投入。
  before の 4 走は 2026-09-17 03:35〜06:31 の他 wave の受入。

**結論 (観測): 台帳の再生成だけでは偏りは縮まらなかった。** 陳腐化した台帳は割付器の予測を「均等」に見せていただけで、
真の重みを与えると割付器 (LPT) は shard-0 に **7502 秒** (他 2 shard は 5328 秒ずつ) を置いた。均等なら 6053 秒である。

## 偏りの真因 — 4 つの xdist group が 25 file / 3908 node / 7502 秒を 1 連結成分にしている

`allocate` は file と xdist group の連結成分を分割せず、宣言済み衝突 group (`test_real_repo_serialization.py` の
`_REAL_REPO_GROUP_CONFLICT_EDGES_GOLDEN`: `campaign-repository-scan` / `real-repo` / `s8c-predicate-snapshot` /
`s8c-preregistration-candidate` の 6 辺) を同一 shard へ寄せる (cf1a5c920)。`real-repo` は `conftest.py` が
`REAL_REPO_RESOURCE_NODES` の node へ動的に付ける。**その node を 1 つでも含む file は file ごと成分に入る**ので、after 走の
shard-0 は 25 file / 3908 node だけで台帳予測 7502 秒・実測 8569 秒になった (`verbatim/parent-after-shard-composition.md`)。
上位は `test_s8b_oracle_driver.py` 2804 秒 (147 node)、`test_s8b_floor_campaign.py` 2368 秒 (528 node)、
`test_t1259_qsub_env_delivery_probe.py` 550 秒、`test_codex_reasoning_ab.py` 483 秒、`test_s8c_preregistration_predicates.py` 331 秒。
この成分 (7502 秒) が均等負荷 (6053 秒) を超えるので、LPT はどう並べても shard-0 を軽くできない。これが shard-0 の床であり、
台帳が正確になったことで初めて数値として露出した (段 3 レンズ B の所見 9「最大連結成分は未実測」の答え)。

床を下げる手は本 wave の scope 外 (scheduler / test 隔離基盤) なので実装せず、次の一手に数値付きで起票する: 成分単位を file から
node へ変える (real-repo node だけを成分に置き、同 file の他 node を別 shard へ出せるか)、または大 file の real-repo node を
別 file へ分離する。どちらも受理集合を変えない設計が要る (D358 は real-repo の直列化自体を維持する)。

## 段 3・段 6 の所見 (逐語は `verbatim/`)

- 段 3 レンズ A (正しさ境界): refresh の集合式・prefix 境界・値の出所に欠陥なし。凍結 426 行は json 往復で一致、pin 一致。
  must-fix 3 = land 競合時の契約 (段 4 で明文化)、変異 M9 の fixture (凍結新規 node を coverage 一覧に含める)、brief の被覆分子と
  原因断定の訂正。
- 段 3 レンズ B (実効性): 「陳腐化が原因だから均す」は根拠を超える (real、採用 → 記録は観測値のみ)。親 script が consumer の
  `nodeid@group` fallback を再現していない (real → 再集計で影響 0 を実測)。差 3151 秒の分類 (既知 2932 + 未登録 219)。凍結残差は
  合計 −334 秒でも shard 間で最大 563 秒残りうる。最大連結成分と refresh 後の予測負荷は未実測 → after 走で実測した (上節)。
- 段 6 レビュー A / B: **must-fix 0 / GO**。nit: parametrize id (`[orchestrator/tests/test_critic.py::]`) の ASCII 短名化 (変異 harness が
  完全一致で中継できたので不採用)、refresh の `excluded_frozen_suite` が add-only の同名 count と意味が違う (記録のみ)、
  `@real-repo` entry を死蔵と断定しない (記録に反映)、親検算の「値の出所」行を before snapshot 照合へ強化 (採用)。

## 親の実走

- 焦点走 (計算ノード 2784.nqsv): `test_update_acceptance_duration_ledger.py` + `test_acceptance_schedule_order.py` (被覆 gate) +
  `test_paper_story_a1_headline.py` + `test_run_tests_shards.py` + `test_t1998_stock_inline_pair.py` = **400 passed / 65 秒**。
- 受入全走 (attempt 2、attempt 1 は post-claim の main 前進で `stage=postcheck rc=70`、走行なし): 24530 passed / 67 skipped。
- author の自走 harness: 53 passed (再生成前後)。

## 変異 matrix

固定 commit `363e79b10` の使い捨て worktree (`tools/mutation_worktree.py --scratch-root /work/1/SFC/tanab/dev-wave-jobs/t2236-mutation/scratch`)
で `tools/mutation_harness.py --runner-mode dispatch --detached`、runner は `python3 tools/run_tests.py --force-dispatch
orchestrator/tests/test_update_acceptance_duration_ledger.py -q -rf`。spec と台帳は本 dir の `mutation-spec-probe.json` (sha256
`ded8b1b7…`) / `mutation-ledger-probe.json`、`mutation-spec-final.json` (sha256 `d48fc7f3…`) / `mutation-ledger-final.json`。

- probe 走 (全件 SURVIVED 登録): baseline PASSED、M0 SURVIVED、M1〜M9 は全部 MISMATCH (= 赤 node を観測)。観測 node を本走 spec の
  `expected_nodes` へそのまま写した。段 4 の静的予測と完全一致。
- 本走: **baseline PASSED、負例 9 件 (M1〜M9) すべて KILLED で期待 node と観測 node が完全一致 (matching 10/10)、等価変異 M0
  (docstring) は SURVIVED、MISMATCH 0、TIMEOUT 0、anchor は全件 1 箇所**。wrapper の共有木事後検査は 2 走とも並行 session の
  churn で rc=125 だが、固定 commit の隔離 worktree で取れた測定は有効 (`recorded=10`)。

| ID | 変異 (single-site、`tools/update_acceptance_duration_ledger.py`) | KILLED node 数 | killer |
|---|---|---|---|
| M0 | `_refresh_result` の docstring を同義に (等価) | — (SURVIVED) | — |
| M1 | 非凍結採用の prefix 除外条件を外す (凍結 JUnit testcase を採用) | 11 | `excludes_all_frozen_junit_nodes`、`preserves_frozen…[8 prefix]`、`check_and_coverage…`、`drops_failed…` |
| M2 | 凍結 map の JUnit 共通 key を JUnit 値で上書き | 8 | `preserves_frozen_entry_bytes_and_values[8 prefix]` (専属) |
| M3 | 結果の初期値を既存全 map に (非凍結の旧名が残る) | 3 | `replaces_nonfrozen…[9.9]/[0.5]`、`drops_failed…` |
| M4 | 共通する非凍結 key に旧台帳値を採用 | 9 | `replaces_nonfrozen…[9.9]`、`preserves_frozen…[8 prefix]` (兄弟 file 0.7→0.25) |
| M5 | 凍結値に `_quantize_seconds` を再適用 (5.89→5.9) | 11 | `preserves_frozen…[8]`、`renders_canonical`、`canonicalizes_noncanonical…`、`drops_failed…` |
| M6 | 描画の `sort_keys=True` → `False` | 1 | `renders_canonical_bytes` (専属) |
| M7 | `--refresh` / `--add-only` の排他 group を独立 option に | 1 | `and_add_only_are_mutually_exclusive` (専属) |
| M8 | refresh 分岐で既存台帳不在・不正を空 map 扱い | 9 | `requires_existing_ledger`、`rejects_invalid_existing_ledger…[8 kind]` |
| M9 | coverage へ渡す集合を refresh 後でなく JUnit 全集合に | 1 | `check_and_coverage_use_refreshed_nodeids` (専属) |

`test_t1574_changed_suite_ledger_node_delta_is_exact` は checked-in 台帳を読むので生成器だけの変異では赤にならない (段 2 plan・
レビュー A の指摘どおり)。実台帳への帰属は親の検算 (`verify_after.py` 18 項目) が担う。

## 残存限界・scope 外 (記録のみ)

- 凍結 8 suite は stale 18・未登録 207 のまま (D1152 の帰結。T-1903 = 所要値の述語化が未実施の限界)。
- `--coverage-against` は `pytest --collect-only -q` 出力の `IZANAGI_GROWTH_HOLD_V1 {…"node_id":"…::…"}` marker 行 (50 行、`::` を
  含む) を nodeid と誤読して rc=2 になる。本 wave は marker 行を除いた一覧 (24568 行) を渡した。次の一手に起票。
- 1 走入力は割付の頑健性を保証しない (同一 node の time が走間で 2 倍動く例: `test_t316_sandbox_probe` 8〜9 秒 対 18〜19 秒)。
- land 時に main 側台帳が進んでいたら main 現物を base に同じ JUnit で再走し、落ちた node (main が add-only で足したもの) は名前と
  件数を本 README へ追記する。本 wave の land 時点: (land 後に amend)。
- `…test_real_patchharness_checkout_and_resolver_use_explicit_binding@real-repo` (0.19) は consumer の第 2 lookup 用の凍結 entry。
  before 4 走 + after 1 走で fallback の利用は観測されなかったが、将来も利用されないとは未確認 (レビュー B)。
- 受入 wall の均等化 (目安 267 秒) は台帳では届かない。床は上節の成分 (7502 秒) で、次の一手の手番。

## 逐語の行末空白の可逆正規化 (DW-S07)

`verbatim/` の `.md` は `git diff --check` に触れる行末空白 (Codex 出力の Markdown 二重空白改行) を除いてある。可視文字は不変。原文
bytes は `verbatim/originals.json` (sha256 `b032b20a6e9176997067ea1cc33897177283219c5316b36cd3dbc540ed4f8eab`) に UTF-8 text として
収め、各 text をそのまま書き出せば原文 bytes に戻る。

| file | 原文 bytes | 原文 sha256 | 行末空白を除いた行数 | 正規化後 bytes |
|---|---|---|---|---|
| `parent-measurements-v1-before.md` | 11378 | `2783ffbbc41d095c…` | 51 | 11327 |
| `s2-plan.md` | 19911 | `aef14620327ffd75…` | 17 | 19877 |
| `s3-lensA.md` | 11324 | `cc8dadb40ee75ed0…` | 18 | 11288 |
| `s6-reviewA.md` | 13027 | `248115fdf6ae0cbb…` | 16 | 12995 |
| `s6-reviewB.md` | 12663 | `d17ec67a22b07849…` | 19 | 12624 |
