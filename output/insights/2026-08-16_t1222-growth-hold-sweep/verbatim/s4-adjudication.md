# 段 4 裁定 — [T-1222] 成長比例テストの母集合の棚卸し

親裁定。2026-08-16 20:20 JST。base = 64808422 (local main 取り込み済み)。
入力: 親 brief、段 2 プラン (s2-plan.md)、段 3 レンズ A (s3-lensA.md)、レンズ B (s3-lensB.md)、
および親の実測 (probe_growth_axes / probe_s8c_fixture / probe_prereg_validate / probe_growth_rates)。

## 0. 判定式を先に固定する (両レンズの争点はここに帰着する)

D335 の対象は「repository の成長に比例して実行コストが増える構造」である。
本 wave は次を判定式とする。**秒数の閾値では判定しない。入力集合の性質で判定する。**

node t が実 ROOT を読み、その入力集合 F(t) について

- **比例 (D335 対象)**: F(t) が repository の通常運転で単調に増える集合である。すなわち
  (a) tip 側の commit 履歴、(b) tracked file 総数または repo 全走査、
  (c) docs / archive の総量、(d) output artifact corpus。
- **非比例**: F(t) が
  (e) 固定 path・固定 byte 上限・**固定された歴史 commit の集合**、または
  (f) 設計上限のある固定用途 directory であって、実測で成長していないもの。

(f) の「成長していない」は主観ではなく実測で決める。親は同一手続き
(`git ls-tree -r -l` を各時点の commit へ適用) で 30 日ぶんを数えた。

| 部分木 | 30 日前 | 14 日前 | 7 日前 | 現在 |
|---|---|---|---|---|
| repo 全体 | 845 file | 4,448 | 10,585 | **12,685** |
| docs | 56 file / 1,968 KiB | 121 | 304 | **510 / 14,097 KiB** |
| output | 544 file | 3,833 | 9,709 | **11,451** |
| orchestrator/tests | 67 file | 187 | 219 | **308** |
| `.claude/agents` | 13 file / 82 KiB | 13 | 13 | **13 / 81 KiB** |
| `.codex/role-adapters` | 13 file / 167 KiB | 13 | 13 | **13 / 167 KiB** |
| `orchestrator/codex_roles` | 8 file | 8 | 8 | **8** |
| `tools/task_runs` | 0 (未作成) | 7 | 7 | **7** |

repo が 30 日で 15 倍、docs が 7 倍になる間、copytree 系 fixture が写す 4 部分木は
**1 file も増えていない**。レンズ B が提案した式 (`unbounded-input(F_t)`) にも、この 4 集合は
入らない。したがって「file が増えればコピー量が増えるので構造上比例」という論法は、
**発火しない一般化**であり、D335 の適用根拠にならない。

## 1. 所見の real / refuted

| # | 出所 | 所見 | 裁定 |
|---|---|---|---|
| 1 | レンズ A 所見 1 | A10 の guard binding は `test_dev_waves_integration.py:2050-2058` の fresh subprocess self-import を壊し、保留対象外の `test_socket_roundtrip_works_beyond_108_byte_repository_path` (`:2165`) を既定で赤にする | **real・採用** |
| 2 | レンズ A 所見 1 | 同 file の `plain_runner` は AST 契約上 `manual` であり、段 2 の `pytest-delegating` は不一致 | **real・採用** |
| 3 | レンズ A 所見 2 / 8 | A06/A09/A10 の「代替経路」は正常系しか実行せず、tamper・drift・duplicate key・bijection の拒否経路を発火させない。71 key = 112 item の検出力が既定ゼロになる | **real・採用** |
| 4 | レンズ A 所見 4 / レンズ B BLOCKER 1 | 段 2 の全件走査は `test_s8c_preregistration_invariant.py:257-279` (`check_docs.main()` を同一プロセスで呼ぶ) と `load_role_specs(ROOT)` 経由 7 件を落としている | **real・採用** (親も独立に :274 を検出済み) |
| 5 | レンズ B BLOCKER 2 | `test_check_ai_provenance.py` の実 repo node は全祖先 `rev-list` を走るので commits 比例 | **refuted** (下記 2 節) |
| 6 | レンズ A 所見 5 / レンズ B | 親 P1 の copytree refuted は誤り | **refuted** (0 節の実測。ただし親の理由は「実測秒数が小さい」から「入力集合が 30 日間不変」へ差し替える) |
| 7 | レンズ A 所見 5 | silo 2 本目 (`test_silo_ladder_rung1_evidence.py:1216`) は `runtime_modules_binding(ROOT)` 経由で glob/rglob 閉包へ到達し比例 | **部分 real** — 到達は事実。ただし対象は実測 9 file (`orchestrator/verifier` 8 + `env_contract_activations` 1) の固定用途集合であり (f) に当たる。**登録しない** |
| 8 | レンズ A 所見 6 | 親の「数十 ms」は fixture 反復・parametrize 展開を含まず、実際は合計約 2.8 秒 | **real・採用**。親の費用評価を訂正する。ただし 2.8 秒でも 112 item の正しさ検査とは交換しない |
| 9 | レンズ A 所見 7 / レンズ B | s8c の共有 fixture は consumer 3 件すべてに帰属し、全保留は防壁ゼロ・部分保留は純損失 | **real・採用** (親 P2 の結論は維持、範囲を 1 → 3 node へ訂正) |
| 10 | レンズ A 所見 3 / レンズ B | A05 の代替経路 (land / wave checker) は正常系では同値だが、noop fold・noncompleted wave では走らない | **real・採用**。登録は維持し、発火時点の差を collateral note に書く |
| 11 | レンズ B | inventory 文言は `registered-layers-only` に限定する | **real・採用**。レンズ B の定型文を採る |
| 12 | レンズ B | I3 は acceptance 内の全体走査禁止に限定し、固定費の台帳整合検査までは禁じない | **real・採用**。I3 を狭める |
| 13 | レンズ B | floor の direct call は既に `REAL_REPO_SERIAL_NODES` 登録済みで新規 hold ではない | **real・採用** (棚卸しに `already_default_serial` として記す) |

### 所見 5 を refuted とする根拠

`_commit_range` は `--range` が与えられたとき `rev-list --reverse <range>` をそのまま使う
(`tools/check_ai_provenance.py:1316-1324`)。実 repo を見る 2 node は範囲を**固定の歴史 commit**で渡す。

- `test_empty_registry_restores_all_thirty_real_findings` (`:2546`) は 30 個の固定 sha を列挙する。
- `test_ledgered_3f2c43d7580b_is_known_and_rc0` (`:2646`) は `3f2c43d7…^!` を渡す。

`_build_ancestry` (`:1365-1392`) は与えられた commit の祖先を走るが、
**固定の歴史 commit の祖先集合は将来 commit が増えても変わらない。**
親実測: `--range 3f2c43d7…^!` = 3.78 秒。この値は今後の開発では増えない。
判定式 (e) に該当し、D335 の対象外である。

## 2. 登録する集合 (R)

**A05 の 3 node だけを登録する。** 追加後の総数は 56 → **59**。

| node_id | 比例軸 | 実測 | 根拠 |
|---|---|---|---|
| `test_check_docs.py::test_real_repo_clean` | `docs_bytes` | 5.33 秒 | 実 `tools/check_docs.py` を引数なしで subprocess 起動 (`:9433-9441`) |
| `test_check_docs.py::test_dev_wave_model_pins_accept_current_docs_contract` | `docs_bytes` | 5.33 秒 | 同上 (`:7282-7289`) |
| `test_check_docs.py::test_normative_exact_section_pins_accept_real_repo` | `docs_bytes` | 5.33 秒 | 同上 (`:7462-7471`) |

- 比例源: docs は 30 日で 56 file / 1.9 MiB → 510 file / 13.8 MiB (7 倍)。判定式 (c)。
- D451: 同じ checker を land (`tools/dev_wave_land.py:2211-2237`) と
  wave checker (`tools/dev_waves/checker.py:351-361,643-688`) が既定で実行する。
  正常系の検出は保たれる。**発火時点が受入から land へ後退する**ことは collateral note に書く。
- guard binding: `test_check_docs.py` に standalone 自己読込 consumer は無い
  (loader 全件検索 70 hit / 48 file のうち該当ゼロ、live docs/tools に直接起動も無い)。
  `plain_runner="manual"` (main guard は `SystemExit(_run())`、`_run` は手書き runner)。
- **付随損失 (必ず note に書く)**:
  1. `test_real_repo_clean` の `_admission_findings(res) == []` (Pegasus admission drift ゼロの assert)。
  2. 新設 pin が実 repo を過剰拒否しないことの正例 2 本 (model pin / normative section pin)。
  3. **file 全体の素の `python3` 実行が拒否されるようになる。** 同 file の docstring
     (`:4`) が「pytest でも 素の `python3 …` でも走る」と書いており、
     この記述が偽になる。実装子に docstring を訂正させ、解除 token
     (`IZANAGI_RUN_GROWTH_HELD_TESTS=explicit-user-command`) を付ければ素の実行も可能である旨を書かせる。

## 3. 登録しない集合と理由 (すべて棚卸しへ記録する)

| 分類 | 件数 | 理由 |
|---|---|---|
| `d451_last_runner` | 段 2 の 148 件 + s8c 3 件 + s8c `:257` の 1 件 | 同じ拒否条件を発火させる独立した既定走行が無い |
| `not_proportional_bounded_input` | A06 21 / A09 10 / A10 40 / silo 2 本目 1 | 入力集合が 30 日間不変の固定用途集合 (判定式 (f)) |
| `not_proportional_fixed_history` | provenance 2 件 | 固定歴史 commit の祖先集合 (判定式 (e)) |
| `guard_binding_blocked` | `test_s8b_floor_campaign.py` 2 件 | 同 file を `spec_from_file_location` で再読込する正規 consumer がある |
| `already_default_skipped` | T-080 stub-free 6 function (11 node) | `IZANAGI_T080_E2E=1` 必須で既定 skip |
| `already_default_serial` | floor の direct call | `REAL_REPO_SERIAL_NODES` に登録済み |
| `refuted` | `test_s8b_ratified_verify.py` 全 node / silo 1 本目 | 実 ROOT からは固定 1〜2 file のみ |

**A10 は上の「非比例」に加えて、guard binding が既定受入を赤にする**ため二重に不可である
(所見 1)。仮に将来比例が成立しても、subprocess helper を別 module へ分離してからでなければ扱えない。

## 4. 母集合の完全性について

**閉じたとは書かない。** 段 2 の 230 件は最低 8 件を落としており、親とレンズがさらに
2 件 (s8c `:257`、provenance) を足した。primitive 列挙型の走査は
「production の重い関数を in-process で呼ぶ」形を構造的に落とす。記録の定型文は次とする。

> 対象は `orchestrator/tests` の top-level test node と、本文に列挙した探索 primitive・
> 既存 2 台帳に限定した候補分析である。数値はこの対象内の候補数を示す。
> hold inventory の `completeness` は `registered-layers-only` であり、未知の hold 層は自動発見しない。

## 5. 不変条件 (実装子への拘束)

- I1. 既存 56 row を変更しない。追加のみ。
- I2. guard binding は `test_check_docs.py` だけに入れる。他 file へ入れない。
- I3 (狭めた形). acceptance 内に repository 全体を走査する新規検査を作らない。
  固定費の台帳整合検査・差分限定の外部 preflight は禁止しない。
- I4. pin は 3 件 + 独立 mirror を**同一 patch**で更新する。値は最終 tree から一度だけ算出する。
- I5. `REAL_REPO_SERIAL_NODES` の golden、`dispatch_compute.py` の env allowlist、
  suite identity は触らない (row 追加だけでは波及しない)。

## 6. 変異事前登録 (DW-M01)

いずれも既定で走り、failure として記録され、`xdist_group` に属さない node を期待赤に選ぶ。

| ID | 変異 | 期待赤 node | 単一理由性 |
|---|---|---|---|
| M1 | 追加した 3 row のうち 1 行を `_HOLD_ROWS` から削除 | `test_growth_test_holds_contract.py::test_inventory_count_and_key_digest_are_independently_pinned` | count pin が先に落ちる。前段に同じ入力を拒否する層は無い (`_validate_hold_rows` は行数を検査しない) |
| M2 | `test_check_docs.py` の `enforce_held_functions(...)` 呼出し行を削除 | `test_growth_test_holds_contract.py::test_every_held_module_has_exact_top_level_guard_binding` | binding 検査は AST 直読みで、collection では発火しない |
| M3 | 同呼出しの `plain_runner="manual"` を `"pytest-delegating"` へ | 同上 | AST runner 判定との不一致メッセージ (`does not match AST runner`) で単一 |
| M4 | 追加 row の 1 件の `hold_axis` を `docs_bytes` → `commits` へ | `test_growth_test_holds_contract.py::test_inventory_count_and_key_digest_are_independently_pinned` | row contract digest が変わる。axis 語彙としては valid なので `_validate_hold_rows` は通り、赤理由は digest 1 つ |

正例 (受理集合を縮める wave の過剰拒否検出、DW-M01): 変異なしの焦点走で
`test_check_docs.py` の**保留 3 件だけが skip**され、残りが従来どおり pass すること。
件数を worklog へ実測で記録する。

## 7. 段 5 の分割

実装単位は 1 つ (registry + guard binding + pin/mirror は同一 patch を要求されるため分割不能)。
Codex `role=author` 1 本。docs は親が段 7 で書く。
