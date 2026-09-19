# 段 4 裁定 — dev-wave-test-inventory-prune (2026-09-19 22:50 JST、親)

## 所見の裁定

相談 A (正しさ境界)・B (過剰・削除不足) はいずれも plan の「A/B1/C 削除 0、B2 重複 1 row、D 全件保持」を支持した。

| # | 出所 | 所見 | 裁定 | 処置 |
|---|---|---|---|---|
| 1 | A-1, B-3 | 唯一の削除 row で検出力が失われる疑い | refuted | 同関数・同型・同入力、id 未使用、fixture は tmp repo を毎回作る。変異 pre/post で裏取り (下記) |
| 2 | A-2, B-2 | scanner の AST 同一・`==` 比較は削除根拠にならない | real / 対処済み | B1 7 組・B2 26 row を保持。inventory の件数を「削除可能数」として使わない |
| 3 | A-3 | (A)(C) に誤検出があるが誤削除案は無い | real / 対処済み | A/C 削除 0 を維持。plan の全件確認を「独立監査済み」とは書かない |
| 4 | A-4, B-7 | (D) 291 は確定一覧ではない (代表確認 41 file、個別未確認 246) | real / must-fix (報告完成) | insight README で「確認済み (D) / (D) でない / 未確認候補」を分け、確認済みだけ pin 先付きで裁定パッケージにする |
| 5 | A-5, B-3 | 対象 node の登録簿・pin 見落とし | refuted | duration 台帳 (3 entry) 以外に名指し無し。台帳は編集しない (consumer は余剰 entry を許す) |
| 6 | A-6 | M1/M2 anchor 不成立・drift mask | refuted (静的) | anchor 一意 (grep -c 1)。drift 由来の赤は probe で分離し、E1 の赤を検出力の証拠に混ぜない (DW-M03/D334) |
| 7 | A-7 | 規律 2 の test を fixture/helper 経由で弱める | refuted | 変更は decorator の row と id だけ |
| 8 | B-1 | **scanner 外の重複 5 件** (`test_p3_s4_loop.py`): `:3238 test_value_literal_consistency_accepts_match` ⊂ `:3248` の `[middle-int]`/`[middle-float]`、`:3271` の row `nonintegral`/`bool`/`zero`/`above-upper` ⊂ `:1911` の同値 row | **real / 採用** | 親が本文で同値性を確認 (同 module `L`、同 implementation 文字列、残存側の assertion が包含)。削除集合に追加し、module `orchestrator/campaign/p3_s4_loop.py` の spec を 1 本足す。scanner の限界 (通常関数 vs parametrize 包含、別 decorator 間の実効入力) を inventory の限界節へ書く |
| 9 | B-5 | 「module × 3 走 = 3 job」は過少見積 | real | 1 harness 起動 = collection 1 + baseline 1 + 変異 3 = 5 dispatch job。2 module × (probe + post) = 20 job 前後。pre の正式 KILLED 走は probe の記録 (失敗 node 完全集合) で代替し、post だけを KILLED 登録で走らせる (DW-M08 の probe→erratum→再登録を post 側で満たす)。所要は実測で記録 |
| 10 | B-裁定パッケージ | module ごと 1 spec の例外化 | 現行維持 | 2 module とも spec 1 本ずつ |
| 11 | A-brief-1, B-brief | 母数の混在 (391 file / 363 file、台帳 24,379 / collection 25,381、台帳欠落 949) と wall 短縮の未証明 | real / must-fix (報告) | 成果物では「台帳換算 worker 秒」と「collection node 数」を分け、wall 短縮を主張しない。391 は `orchestrator/tests/*.py` (helper 込み)、363 は `test_*.py` |
| 12 | A-brief-4, B-4 | 有限変異は検出力保存の一般証明ではない | real | 主張を「静的同値性 + 登録変異に対する検出集合保存 (S_post = S_pre − Del、非空)」に限定 |
| 13 | B-brief | DW-G05 の 1 行の表現 | real | 「放置しても certified 選択・レポート・台帳値は変わらず、重複 6 node の台帳換算 worker 秒が残る。誤削除は earliest-eligible 選択違反 / value-literal 帰属の回帰防壁を欠落させ得るため、残存 case の同値性と登録変異の pre/post 検出集合で確認する」に改める |

## 削除集合 v2 (author 所有 = 2 file、素集合)

| 単位 | file | 変更 | 削除 node | 台帳秒 |
|---|---|---|---|---:|
| U1 | `orchestrator/tests/test_s8b_holdout_freeze.py` | `:2381` parametrize の 3 行目 `True` と id `drop-candidate-selection` を除去 | `test_v2_candidate_rejects_later_run_using_derived_earlier_eligibility[drop-candidate-selection]` | 33.000 |
| U2 | `orchestrator/tests/test_p3_s4_loop.py` | `:3238-3246` 関数 `test_value_literal_consistency_accepts_match` を削除 (直前の区切り comment 行は残す)。`:3271` parametrize の row `nonintegral`/`bool`/`zero`/`above-upper` と対応 id を除去 (残る row: nan/inf/negative/decimal/floatable-object) | `test_value_literal_consistency_accepts_match`、`test_coder_proposal_rejects_values_outside_exact_integral_domain[nonintegral|bool|zero|above-upper]` | 台帳から親が集計 |

不変条件: 関数本文・docstring・他 decorator・helper・fixture・import・期待値は不変。conftest・golden・台帳・production は非接触。file 内 test 0 になる file 無し。

## 変異事前登録 (B-057、実装前)

runner は module ごとに当該 test file 1 本 (`tools/run_tests.py --force-dispatch <file> -q -rf`)。両走で同一 file 集合。source は独立 clone の固定 commit worktree (submodule 初期化済み) へ `tools/mutation_harness.py --repo` を直接当てる (DW-M05 正本経路、`--runner-mode dispatch --detached`)。

Spec H (`orchestrator/campaign/s8b_holdout_freeze.py`):
- M1 `min(eligible, …)` → `max(eligible, …)` (1981 行、負例)。予測: `[min-to-max]`・`[drop-candidate-selection]` (削除予定)・`[use-reported-eligible]` が赤。
- M2 `if required_run_id != selected_run_id:` → `if False and …` (1983 行、負例)。予測: 同上。
- E1 encoding comment に `  # mutation-control` 追加 (対照)。予測: 赤 0。

Spec L (`orchestrator/campaign/p3_s4_loop.py`):
- M1 `if not assigned or assigned_value != coder_value:` → `… == coder_value:` (assert_value_literal_consistent、負例)。予測: `test_value_literal_consistency_accepts_match` (削除予定)、`…accepts_declared_integral_boundaries[*]` ほか一致系の正例が赤。
- M2 `    if decision.accepted:` → `    if decision.accepted or True:` (_assert_coder_value_domain、負例)。予測: `…rejects_values_outside_exact_integral_domain[*]` (削除予定 4 row を含む 9 row)、`test_backoff_value_adapter_preserves_main_exception_and_structured_rule[*]` ほか値域拒否の負例が赤。
- E1 encoding comment 対照。予測: 赤 0。

手順: (1) 変更前 commit で probe (全件 SURVIVED 期待) → 失敗 node 完全集合 S_pre を記録 (erratum 扱い)。(2) 削除 commit で S_post = S_pre − Del を KILLED 期待で登録し本走。合格条件: 各負例で S_post と完全一致かつ非空、E1 は前後とも赤 0 (drift 由来の赤があれば冗長 gate として明記し証拠から外す)。非 ASCII id は両 file とも 0 件 (collect.txt で確認済み)。

## scope 外・裁定パッケージ

- (D) 確認済み分は insight README で件数・file・pin 先を列挙 (削除しない)。
- ユーザー裁定 (module ごと 1 spec、D exact pin 不変) は維持。
