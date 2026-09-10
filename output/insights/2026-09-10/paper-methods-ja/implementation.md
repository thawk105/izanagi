# 日本語方法節の実装対応メモ

対象本文は [方法節草稿](methods.md)。照合対象は local main の `98a3d7c9e` を起点とする
2026-09-10 のコードと指定文書である。本資料のための新規 CC 合成・性能測定は行っていない。
以下の「実装済み」は記載した関数・経路の存在と挙動を指し、その機能を使った正式実験の完走を含まない。
本資料は新しい論文シリーズ、実験登録、判定器ではない。

## 正本の優先関係と執筆裁定

- `docs/decisions.md` D1598: 方法の核を CC、対象実装の action vocabulary の拡張、毎反復の
  正しさゲートに置く。説明の忠実性、proof chain、試行 provenance は補助に留める。
- 同 D1936: 採用済みの変更と実装完了を分ける。項1の pin 更新と再投入、項3の A-1 再開、
  項6の較正条件の修正等は、裁定本文だけでは実施済みにならない。本稿は各変更の追跡台帳を作らない。
  項8・9により B-4 は記述統計限定、部分実装を完成と呼ばず、正式選択への接続条件を維持する。
  項16の B5 保留は、調べた対象世界に候補が存在しないことの証明ではない。
- `docs/paper-story/README.md`「最新スナップショット以後に確定したこと（stale 注記）」:
  A-2 の古いラベルは内蔵の「適応 backoff」であり指数 backoff ではない。
  制限解除を確認していない新しい散文の存在だけで A-2 の旧図・結論を復活させない。
  B-10 の記述的観測を因果同定や完了へ昇格させず、別論文の T-2265 成果を本体へ数えない。
  方法節にはこれらの性能値や図を転載しない。
- `docs/phase3.md`「kickoff の最小スコープ」「現行 Phase 3 must と発火条件」「後続段」:
  有効な編集契約と段ごとの実装・実走の射程を引く。冒頭の古い日付の要約だけで現在の全状態を決めない。
- `docs/phase3-main-experiment.md`: 旧登録と日付付き改訂の区別を保つ。旧 headline の
  4 比較対照を、D52 による休眠・差し替え後も一律の現行実走と書かない。

## 主要記述とコードの対応

コードの参照はリポジトリ相対パスと関数名で示す。本文番号は methods.md の節番号である。

| 本文 | 記述 | 実装アンカー | 区分と上限 |
|---|---|---|---|
| §1–2 | planner/coder/critic の分担、セッションによる反復駆動 | `orchestrator/campaign/p3_s4_loop.py` モジュール説明、`PlannerProposal`、`CoderProposal`、`planner_context_payload`、`drive_iteration` | 実装済み。関数は提案を受け取り、LLM 自体は起動しない。プロジェクト全体の無人化ではない |
| §1–2 | 導入済みの hole に限定したコード生成 | 同 `render_hole`、`quarantine`、`_run_one_iteration_resolved`、`orchestrator/campaign/backoff_hole_grammar.py` | 実装済み。backoff は値と一致する単一数値リテラルの一文。コード出力形式と非列挙空間の探索は同義でない |
| §2 | 骨格・stock 枝の保存、ホスト作用と軸文法の検査 | 同 `quarantine` → `DiffQuarantine.validate`、`coder_effect_gate.scan_host_effects`、軸文法 | 実装済み。字句検査は有限の規則。任意の外部作用・意味逸脱を完全に封じるとは書かない |
| §2 | 提案値と実コードの帰属を一致させる | 同 `assert_value_literal_consistent`、`_check_attribution_before_quarantine`、genome の構築 | 実装済み。値の対応を確認する範囲であり、一般的な意味等価証明ではない |
| §2 | patch の適用・評価・復元とソースの識別 | 同 `_run_one_iteration_resolved` → `patchharness.applied` → `loop.run_campaign`、`orchestrator/campaign/pipeline.py` `_prepare_evaluation_core` | 実装済み。実ソースの証拠とビルド識別に基づく。過去の測定を現在の差分だけで無効化しない |
| §2 | 拒否と重複提案を成功から区別 | `p3_s4_loop.py` `record_diff_reject`、`_resolve_duplicate`、`_run_one_iteration_resolved` | 実装済み。重複は保存済み証拠の再利用。毎回再測定したとは書かない。`dry-pass` は検疫のみ |
| §3 | 空履歴・異常終了・証拠欠落・検証赤は採用しない | `pipeline.py` `_execute_verification_repetition` → `verify_trace_dir_with_capability`、`_prepare_evaluation_core`、`orchestrator/verifier/__init__.py`、`report.py` `_anomaly_to_dict` | 実装済み。検証赤は循環・依存辺を含む構造化 `verify` 診断付きで abort。指定された履歴と検証意味論の範囲に限る |
| §3 | 全検証構成・全反復の合格を要求 | 同 `CorrectnessWorkload`、`s2_correctness_workload`、`performance_correctness_workload`、`_prepare_evaluation_core` 内の pass/repetition 走査 | 実装済み。`legacy+s2` と `legacy+performance` は別の opt-in。全 caller で性能相当検証が既定とは書かない |
| §3 | 構造化反例と生存性・検疫拒否を critic へ提示 | `p3_s4_loop.py` `make_critic_digest` → `load_rejections`、`load_liveness_rejections`、`render_rejections` | 実装済み。`reflux=False` は赤い診断節を要約から除くだけで検証は継続。因果的な改善効果は未証明 |
| §3 | 状態保存と停止判定 | 同 `save_loop_state`、`load_loop_state`、`project_whiteboard`、`check_stop`、`drive_iteration` | 実装済み。予算・小変更の連続・逆方向推奨で止める。統計的最適性の判定ではない |
| §4 | trace 有効/無効の別ビルド・別実行 | `pipeline.py` `_prepare_evaluation_core` 内の `_build_one(trace=True/False)`、`_execute_verification_repetition`、`_run_bench` | 実装済み。buildcache/source_digest に観測者効果の検査を委譲。`TRACE` の実行時分岐化は許可しない |
| §4 | 測定の排他・反復・不安定性を記録 | 同 `_run_bench` → `bench_lock`、`competing_bench_pids`、`measure_point`、`remeasure_until_stable` | 実装済み。`unstable` は残り得る。全 measured COMMIT が安定・有意な勝者とは限らない |
| §5 | bench-first は opt-in、明白な劣位だけを未認証棄却 | 同 `ScreeningConfig`、`_prepare_evaluation_core` の `active_screening` 分岐 | 実装済み。下記の閾値と例外条件を持つ。段4 LLM loop の通常評価順を変更するものではない |
| §5 | verify 後だけ COMMIT、測定値と認証を分離 | 同 `evaluate`、`_commit_prepared` | 実装済み。`do_bench=False` の COMMIT は `fitness_tps=None`。COMMIT の存在だけで性能選択可能とは言えない |
| §5 | 保存済み証拠を用途に応じて受理 | `orchestrator/campaign/artifact_admission.py` `require_admitted_campaign`、`require_persisted_certified_commit`、`CampaignReadPurpose` | 実装済み。`HISTORICAL_RAW` と `CERTIFIED_ACCEPTANCE` は異なる view。履歴読み取りは認証への昇格ではない |
| §6 | descriptor から固定候補を一つ指名 | `orchestrator/campaign/s8b_selector_input.py` `build_selector_payload`、`load_catalog`、`s8b_selector_output.py` `parse_selector_output` | 実装済み。固定6候補の一つと理由を受理する部品。任意コード生成でも最終比較判定でもない |
| §6 | 正式評価が要求する証拠を照合 | `orchestrator/campaign/s8b_oracle_report.py` `_assess_window`、`_assess_campaign`、`build_observations` | 実装済みの評価部品。trial の検証・測定記録と登録を照合する。全正式実験の完走証拠にはしない |
| §6 | 証拠があれば新規候補、なければ stock/tie を正直に返す | `docs/phase3.md` 冒頭「各 run の正直な出力契約」 | 系全体の契約。`p3_s4_loop.py` 単体による汎用最終選択の実装とは書かない。前提欠落は有効な tie でない |
| §6 | 材料レポートと説明を区別 | `orchestrator/campaign/layer3_report.py` モジュール説明、`build_report`、`render` | 記録の射影は実装済み。通常出力は `certifying_input=false`。`mechanism_hypotheses` は空の予約区画で、機序仮説の自動生成は未実装 |

## screening の具体的な読み分け

`ScreeningConfig` の基準 throughput を T₀、between-run floor を f とすると、bench-first の
遅さによる棄却条件は T < T₀(1 − kf) であり、k は 1.5 以上である。これだけでは棄却せず、
`unstable` でないこと、abort 率が得られていること、基準 abort 率に係数を掛けた値を超えないことも
要求する。古い基準点なら screening を無効にして verify-first に戻る。
この閾値は「候補が優れている」ことを認定する閾値ではない。

| 記録・経路 | 読めること | 読めないこと |
|---|---|---|
| 性能だけの探索・診断 | その条件で得た raw な観測 | 検証済み fitness、正式選択、headline |
| bench-first の検証前 `BENCH_DONE` | 性能標本が取得された | 検証通過 |
| `screen-slower-than-floor` で abort | 保守的スクリーニングで棄却された | 正しさ違反が検出された、certified な劣位が確定した |
| 全 verify 後の測定付き COMMIT | 指定検証を通し性能を記録した | すべての consumer で正式適格、安定性・優越性が確定した |
| 探索 namespace の certified outcome | 当該探索で検証を通った | official namespace の正式認証成果物になった |
| `HISTORICAL_RAW` による履歴読み取り | 記録当時の事実を用途限定で読む | 現行の certified 判定へ再ラベルする |

## 実走・契約・未了の境界

本稿の静的照合は、新しい測定を実施したという記録ではない。`docs/phase3.md`「後続段」2・4 は
過去の赤の診断提示と人間監督の実反復を報告するが、その実績を現在の pin による新試行の完了や
一般的な性能優越へ移さない。8c の限定的な駆動実装も、段4の責任分担を遡って無人化しない。

`docs/phase3-main-experiment.md` の検証相、非 LLM 対照、系列単位の標本設計、floor、
多重比較は評価契約として読む。D52 の S、縮小後の S' と workload 特化の前向き評価を混ぜず、
旧 headline が不成立となったことを、方法節で成功へ言い換えない。

D1936 項8・9の B-4 は、適格な赤 precursor が揃い、記述統計の追補と consumer が整合し、
登録どおり実走したという証拠までが本稿では未確認である。writer は create-only、report の4分類は
未実効、launcher は単一 arm までという裁定上の限界を残す。正式選択への接続も未完として扱う。
「拒否診断を返す実装がある」から「そのフィードバックによる改善効果を実証した」へ飛躍しない。

## 本文照合の確認点

親が生成→検疫→検証→測定→記録の呼出しを追い、以下を確認した。
数値リテラル一つの backoff を任意コード合成と読ませないこと、診断還流 off を検証 off と
取り違えないこと、raw 観測・探索 certified・正式適格を分けること、COMMIT と最終勝者を
同一視しないことを本文へ反映した。本文と表の「実装済み」は静的確認であり、本 wave の
受入テストとは別の根拠である。
