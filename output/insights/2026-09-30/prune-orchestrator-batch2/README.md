# 不要コードの整理 第 2 束 — 使われていない提出 gate と一回限りの分析 (2026-09-30)

- authority: none
- default_effect: no-state-change (削除 0。コード・test・台帳・docs の地図は変えていない)
- 依頼: `verbatim/request-md_4.txt` (並行 wave 共通指示 speedup-2026-09-29 の md_4、共通指示は `verbatim/request-common.txt`。ユーザー依頼「不要なテスト、ツール、ファイルは削除して記録しておき、後でgit参照しやすいように」)
- 基準: 判定は local main `4f412c67bcd7ff9cca1e78ce9bd1dd7a15d46037` の tracked tree。判定の基準は D1989 (参照 4 分類) と D2179 (一回限り・結果凍結済み・現行機構の実装でない の 3 連言、専用 test の専用性)
- 経過: 段 1 brief (`verbatim/s1-brief.md`) → 段 2 Codex (`verbatim/s2-plan-prompt.md` / `verbatim/s2-plan-codex.md`、read-only・静的、「残しすぎ」「消しすぎ」の両方向を 1 本に課した) → 段 4 裁定 (`verbatim/s4-ruling.md`、削除 0 = 実装しない)。段 3・5・6 の実装/fix は無し。記録の独立 read-only レビュー 1 本 (`verbatim/s6-review-codex.md`、NO-GO: 削除 0 は支持、根拠の分類に must-fix 2 件 = nonmonotonicity の D1989 分類と sweep_report の D12 根拠、nit 2 件。数値はすべて現物と一致。4 件とも real と裁定し、commit 前に本書と fragment を直した)

## 1. 結論

- 依頼 md の候補は **9 群・19 file** (`orchestrator/submission_gate/` の 11 file と、`orchestrator/campaign/` の 8 module)。親の段 1 brief は「12 module」と書いたが、段 2 の指摘どおり 9 群が正しい。
- **9 群とも残す (削除 0)**。8 群は「使われていない」のではなく、有効な決定・凍結事前登録・現行 runbook の手順・live test の照合先・共有 test のいずれかに拘束されていた (D1989 の現役の拘束的 consumer)。残る 1 群 (`backoff_nonmonotonicity_analysis.py`) は D1989 上は歴史的言及しか持たないが、後続の probe が library として再利用した事実で D2179 条件 1 (一回限り) が成立しないので残す (§2)。未確認のまま残した条件は 1 つも無い。
- 依頼が挙げた速度面の見込み (submission_gate 系 test の約 790 秒) は台帳の値としては正しい — `acceptance_duration_ledger.json` で `test_t338_submission_gate_unit1..5` と `test_t139_submission_path` は **222 node・788.8 worker 秒** (台帳全体 26,614 node・16,048.0 worker 秒の 4.9 %、うち `test_t139_submission_path` 25 node が 500.2 秒、`unit5` 58 node が 252.7 秒)。ただし削除条件を満たさないので、この時間は縮まない。worker 秒は受入 wall の短縮量ではない (D2172 項 6)。
- 同じ 8 module のうち 4 本 (counterfactual 2 本・nonmonotonicity・sweep_report) は、2026-09-20 の T-2800 削除 wave が同じ D2179 で「残す」と判定済みだった (`output/insights/2026-09-20/t2800-dead-code-delete/README.md` §3)。その後に拘束が外れた事実は見つからなかった。md の候補一覧 (調査役の機械集計) はこの判定を反映していなかった。

## 2. 候補別の判定

| 候補 | 判定 | 拘束 (D1989 分類) | D2179 で崩れた項 |
|---|---|---|---|
| `orchestrator/submission_gate/` (11 file、6,223 行) + `test_t338_submission_gate_unit1..5`・`test_t139_submission_path` (計 4,139 行) + `orchestrator/tests/fixtures/t338_submission_gate/` (48 file) | 残す | 現役の拘束的 consumer = 有効な決定。D574 (T-139 の受理述語) を D597 が「T-338 単位 3・5 が実装すべき正確な要件」とし、D749 (ユーザー裁定 2026-08-24) が「private receipt gate の実装と検証は完了…残る実装 wave は pilot 禁止を維持したまま進められる」と、この gate を前提に次の実装を置く。[T-139] は worklog 持ち越しに active のまま (D2257 項 7)。`docs/phase3.md` の T-338「active から除外」は持ち越しの走査対象から外す意味で、D2257「取り下げの意味と射程」のとおり D を取り消さない。fixture 側は別に、`orchestrator/preregistration/t139-approval-manifest-v1.json:20`・`t139-vector-approval-v1.json:21` が `fixtures/t338_submission_gate/conformance/index-v2.json` を (path, commit `6d431a60a`, sha256) で束縛する (D574 決定 (1) の対象) | 現行機構の実装でない、が不成立 |
| `orchestrator/campaign/backoff_counterfactual_analysis.py` | 残す | 凍結事前登録 `docs/backoff-counterfactual-preregistration.md:343-347` が「解析器は…(v1) と…(v2) を、それぞれ独立した定数として pin しなければならない」と解析器に契約を課す | 現行機構の実装でない、が不成立 |
| `backoff_counterfactual_cohort2_analysis.py` | 残す | 上に加え、live な `orchestrator/tests/test_t2187_adaptive_const_probe.py:1977` (`test_probe_seed_table_matches_cohort2_preregistered_seeds`) が probe の certification seed 表を本 module の `PREREGISTERED_SEEDS` と照合する | 現行機構の実装でない、が不成立 |
| `backoff_nonmonotonicity_analysis.py` | 残す | **現役の拘束的 consumer は無い** (専用 test 以外の参照は歴史的言及だけ)。ただし T-2583 (`output/insights/2026-09-15/t2583-backoff-high-band-sign/README.md` の「解析器 (無改変)」行、関数 6 本を再利用) と T-2635 (`output/insights/2026-09-16/t2635-high-band-control-feasibility/README.md:202`) の probe が library として再利用した記録がある | 一回限り (D2179 条件 1「以後に別の作業が同 module を library・driver として再利用していない」) が不成立。再利用の事実は後から消えない |
| `backoff_policy_performance_analysis.py` | 残す | 凍結事前登録 `docs/backoff-policy-performance-preregistration.md:330`「解析は `orchestrator/campaign/backoff_policy_performance_analysis.py` の公開関数 1 本で行い」。live な `test_t2187_adaptive_const_probe.py:23` も import する | 現行機構の実装でない、が不成立 |
| `backoff_sweep_report.py` | 残す | 共有 test `orchestrator/tests/test_backoff_consumers.py:21` が live の `backoff_repro`・`wal`・`artifact_admission` と並べて本 module を import し、`:108` 以降で certified view の読み分けを検査する (module だけ消すとこの test の収集が壊れる)。`docs/phase2.md:184` は本 module を `replay.discover_campaign_dir` へ統一した読み手 3 本の 1 つと記録する。(段 1 は `docs/orchestrator-design.md` §材料レポートを根拠に挙げたが、同節は `orchestrator/reports/` の一般規約で本 module を名指ししないので根拠から外した) | 一回限り (T-2187 が 2026-09-02 に改修、T-2800 §3) と、専用 test の専用性 (対になる専用 test が無く、検査は共有 test にある) が不成立 |
| `s8b_floor_evacuation.py` | 残す | 現行 runbook `docs/phase3-8b-restart-runbook.md:279` が `python3 -m orchestrator.campaign.s8b_floor_evacuation evacuate --env-tag <env>` を手順として指定。非専用の `test_s8b_holdout_freeze.py:3324` も import。`test_ccbench_spawn_sites.py:297` に spawn 表 1 行 | 一回限り・現行機構でない、が不成立 |
| `s8b_oracle_exploration.py` | 残す | D528 決定 (2) (`declared_use_class` の確定) が `artifact_role` の現用の所在として本 module を名指し。`test_s8b_oracle_artifacts.py:341` が CLI を実行 | 現行機構の実装でない、が不成立。test は official loader も検査する共有 test (`:120` `test_official_loaders_reject_exploration_schema_for_all_roles` 他) で専用でない |
| `s8b_verdict.py` | 残す | 8b 最終判定層の実装。D555 が `judge_combined` の条件改訂を指定、`test_official_perf_closure.py:187,439` の閉包固定表と `test_s8b_oracle_manifest_contract.py:25-35` に列挙、`docs/freeze-permanent-design.md:366` が凍結対象に挙げる | 現行機構の実装でない、が不成立 |

- 共通指示 §2 は「8b / 8c の module の切り離し」を採らないとしており、s8b 3 本はいずれも 8b 系列の現行部品である (8b 系列を退役させるユーザー裁定は無い。D2212 項 5 は論文の必須経路の外と置いただけ)。
- nodeid・file 名を固定する台帳 (`orchestrator/tests/README.md` の allowlist、`test_plain_runner_coverage`、`REAL_REPO_SERIAL_NODES`、growth / flaky の hold)、`test_ccbench_spawn_sites.py` の spawn 表、`docs/README.md` の地図、`docs/archive/README.md` の墓標は、test も docs も 1 本も削除しないので**変更なし**。所要台帳も編集していない。

## 3. 消したら失われていた検査性質 (受理集合への影響)

削除 0 なので受理集合は変わらない。依頼 §「消した test が検査していた性質が、残る test のどこにも無くなるか」への回答として、仮に消した場合に失われる検査を段 2 の関数単位の列挙から記す (親は §2 の根拠行と下の 3 関数を本文で確認、他は段 2 の静的判定に依拠)。
削除単位は「module と専用 test の対を消す」を仮定する。専用 test が無く検査が共有 test にある sweep_report と、test が共有の s8b_oracle_exploration は、
(a) module だけ消すと共有 test の import が壊れて収集が赤になり、(b) 共有 test ごと消すと表の検査に加えて同じ file の live code の検査も失われる。どちらも削除として成立しない。

| 候補 | 消すと残る test のどこにも無くなる検査 |
|---|---|
| submission_gate 群 | Git 履歴・束縛 (`unit1`)、安全な IO と受領証 schema (`unit2`)、受領証の意味検証 (`unit3`)、全履歴の一意性と attempt authority (`unit4`)、conformance vector index と公開 call site (`unit5`)、固定 authority での投入経路 (`test_t139_submission_path`) |
| counterfactual 2 本 | v2 事前登録 sha と解析入力の束縛、推定と等価性境界、cohort2 の LCG・終端処理。cohort2 の seed 照合 (`test_t2187…:1977`) は残る test 側の import が壊れる |
| nonmonotonicity | 保存値からの方向性再計算、J0〜J4 の判定 |
| policy_performance | 登録済み仮説の三値判定、入力 identity、事前登録 bytes の pin |
| sweep_report | (b) の場合: 共有 `test_backoff_consumers.py` の certified view の読み分け・noise 境界・IPC 欠測表示 |
| s8b_floor_evacuation | 退避失敗時の byte 保持、namespace 全体の復元、clean scan との関係 |
| s8b_oracle_exploration | (b) の場合: 探索出力を official 出力から分離する CLI 検査と、同じ file の official loader の検査 |
| s8b_verdict | 条件 1・2、oracle の診断限定、freeze identity、測定 claim gate |

## 4. 変異と受入

- 実装面の差分ゼロのため変異 matrix は免除 (DW-S04)。kill 型の変異は 0 件。
- 変更は本 insight と worklog fragment だけなので、受入は本書を commit した後に D2316 の縮小受入で行う。本書は受入前に凍結するので、受入の結果は本書に書かない (受領証と land の記録に残る)。

## 5. hash (sha256・blob id) による pin 閉包

候補 19 file の現行 sha256 と git blob id (各 40・12 桁の前方一致を含む) を 1 回の `git grep -F` で tracked 全体から検索した
(`verbatim/candidate-hash-hits.txt`、前半が 19 file の値)。hit は 9 行で、すべて歴史記録だった。

| file | hit の所在 | 分類 |
|---|---|---|
| `backoff_counterfactual_analysis.py` (sha256) | `output/insights/2026-09-08_t2265-itt-seq0/verbatim/` のレビュー逐語 2 行 | 歴史的言及 |
| `backoff_nonmonotonicity_analysis.py` (sha256) | T-2583 README 2 行・逐語 1 行、T-2635 README 1 行・実行 json 1 行 | 歴史的言及 (再利用した解析器を「無改変」と束縛した記録。§2 の「一回限り不成立」の根拠でもある) |
| `s8b_verdict.py` (blob) | `output/insights/2026-09-16/t2638-codex-worktree-retirement/data/reach2.tsv`・`reach_all.tsv` 各 1 行 | 歴史的言及 (当時の到達性台帳) |

hash で現行の実在を要求する pin (manifest・test・trust root) は見つからなかった。§2 の拘束はすべて path・module 名・決定の名指しによるもので、hash 閉包はそれを変えない。

## 6. 確かめたこと・確かめていないこと

- 確かめた (親の実測): 9 群の名前参照の tracked 全文検索 (output・archive を除く)、候補 19 file の sha256 / blob id の tracked 全文検索 (§5)、D1989・D2179・D2172 項 5・6・D2257・D574 決定 (1)・D597・D749・D555 と `artifact_role` を名指す D の逐語、T-139 の持ち越しと最新本文 (archive `worklog-phase3-0824-891.md`、D749)、T-2800 §3 の 4 本の判定、事前登録 2 本の該当行、`test_t2187_adaptive_const_probe.py:1977`・`test_s8b_oracle_artifacts.py:120`・`test_backoff_consumers.py:21` の import・`docs/phase2.md:184`・`docs/orchestrator-design.md` §材料レポート (本 module を名指ししないこと)・T-2583 README の再利用行、所要台帳の集計値。
- 段 2 Codex の静的判定に依拠 (親は再走査していない): §3 の関数単位の検査性質の列挙 (上の 3 関数以外)、`test_backoff_consumers.py` が sweep_report の唯一の検査面であること。
- hash 検索の対象は候補の module 19 file だけで、関連 test と `fixtures/t338_submission_gate/` の 48 file は含めていない (全群を残すので判定には影響しない。将来これらを消す wave は含めて検索し直す)。
- test の実走はしていない (コード・test を変えていないため)。

## 7. 付随して見つけたこと (scope 外、記録のみ)

- md の候補一覧は「tests 以外から import 0」を削除の目安にしていたが、D2179 の理由欄が既に述べるとおり、prod import 0 は事前登録の契約・live test の照合先・library 再利用・現行 runbook の `python3 -m` 呼出しを見落とす。本束の 9 群はすべてこの型だった。
