revA には `F-xx` 見出しはなく、実在する `A-01〜A-03 / N-01 / R-01〜R-04` を全件掲載した。`F1〜F6` は fix1 側の対応番号である。`closed` は現行コードと親提示の fix3 後実測に基づく。本レビュー自身は pytest・変異を実走していない。

| 所見・実測赤 | 状態 | 現在の判定 |
|---|---|---|
| A-01（fix F1）ambient contract 再解決 | **partial** | trigger の `default_cfg()` は未束縛化されたが、15か所の直接 ambient bind と autonomous の固定 lookup が残存。歴史 report への影響も残る。 |
| A-02（fix F2）衝突 H の削除・上書き | **closed** | [ident.py:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/ident.py:61) は同一 H の再束縛だけを許可し、不一致を拒否。trigger wrapper の key 削除も消えている。 |
| A-03（fix F4）recovery 追記順 gate 欠落 | **closed** | [test_campaign.py:1028](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_campaign.py:1028) が recovery ABORT と repair receipt の双方を bytes 不変で固定。 |
| N-01 guided fixture の lane 指定漏れ | **closed** | production と2 fixture caller が `require_environment_contract=False` を明示。 |
| R-01 validator 恒真性疑義 | **closed** | 原 refutation を再確認。lock の H が発火条件で、形式・一致・ever-active・env_tag を独立検査している。 |
| R-02 事前登録8変異の expected nodeid | **partial** | 各 expected nodeid は静的には赤になるが、#1・#6・#7 は「それだけが赤」にならない。 |
| R-03 repair/recovery の production 順序 | **closed** | [wal.py:559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/wal.py:559)、[wal.py:1311](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/wal.py:1311) とも同一 `LOCK_EX` 区間で書込み前に検証。 |
| R-04 matching resume / qualification / legacy | **closed** | matching H は evaluate/build とも0回、Hなし legacy/guided は明示 lane で読める。qualification sink は依然 H 非対象。 |
| B-01 S1 raw reader の新 identity 迂回 | **partial（実質未解消）** | [s1_direct_comparison.py:239](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/s1_direct_comparison.py:239) と共有 `layout_for()` が残り、[s1_report.py:339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/s1_report.py:339) の探索先を変える。 |
| B-02 trigger の競合 H 上書き | **closed** | A-02 と同じ。注入 layout も最終 campaign ID と照合する。 |
| B-03 autonomous producer/offline consumer | **regressed** | offline consumer は lock H 解決へ直ったが、producer は linux H で先に ID を作り、正当な Pegasus contract への再束縛を fail-closed で拒否する。 |
| B-04 guided caller・偽正例 | **closed** | caller 2件と public resume 相当の repair/terminal read が補完された。 |
| B-05 歴史 ID exact pin 弱体化 | **closed** | T343/T428 の no-H preimage を再構成して完全 ID を比較する形へ戻っている。 |
| B-06 固定 vector と ambient authorization の混在 | **closed** | generation-1 vector と writer 伝播検査を分離し、writer 側は実際に認可された H と比較する。 |
| RED-01 `test_guided.py::test_cmd_evaluate_repairs_committed_tail_before_four_new_frames` | **closed** | fixture が unbound lane を明示。親提示の fix3 後 rc=0 と整合。 |
| RED-02 `test_guided.py::test_cmd_start_atomic_loser_is_structured_and_touches_no_meta_or_wal` | **closed** | 同上。 |
| RED-03 `test_p3_s4_loop_trigger_gating.py::test_fresh_default_seams_flow_distinct_contract_to_measurement_sink` | **closed** | `default_cfg()` 未束縛化、site seam で一度束縛。 |
| RED-04 `test_p3_s4_loop_trigger_gating.py::test_fresh_default_seams_flow_distinct_contract_to_reject_sink` | **closed** | 同上。 |
| RED-05 `test_p3_s4_loop_trigger_gating.py::test_contract_sentinel_flows_to_run_campaign` | **closed** | 明示 contract が `run_campaign` まで伝播する形へ修正。 |
| RED-06 `test_p3_s4_loop_trigger_gating.py::test_empty_numactl_contract_flows_as_empty_list` | **closed** | ambient lookup による seam 迂回は trigger public 経路では解消。 |
| RED-07 `test_p3_exploration_namespace.py::test_coder_driver_flag_reaches_build_spy_with_exact_run_context[trigger_gating]` | **closed** | exact `BuildRunContext` 到達前の ambient lookup が除去された。 |

## 恒真性と変異8件

現 validator は非恒真である。[wal.py:947](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/wal.py:947) は lock に H がある場合だけ発火し、COMMIT field の欠落・形式・H 不一致・未知 H・env_tag 不一致を別々に拒否する。期待 nodeid を parser、admission、attempt topology などの先行層が覆う例はない。

| # | 期待 nodeid | 期待どおり赤か | 「それだけが赤」か |
|---|---|---|---|
| 1 | `test_campaign.py::test_bind_environment_contract_rejects_conflicting_prebound_hash` | はい | **いいえ**。[test_p3_s4_loop_trigger_gating.py:647](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:647) も同じ衝突条件を検査する。 |
| 2 | `test_campaign.py::test_pipeline_no_bench_wal_commit_binds_authorized_contract` | はい | 静的にははい。raw COMMIT H の直接比較で、先行拒否なし。 |
| 3 | `test_campaign.py::test_pipeline_bench_wal_commit_binds_authorized_contract` | はい | 静的にははい。同上。 |
| 4 | `test_campaign.py::test_commit_contract_validator_rejects_missing_field_without_defaulting` | はい | 静的にははい。custom `Payload.get` により defaulting 変異だけを通す。 |
| 5 | `test_campaign.py::test_commit_contract_requirement_is_derived_from_lock_not_record_presence` | はい | 静的にははい。custom `__contains__` により record-derived 変異だけを通す。 |
| 6 | `test_campaign.py::test_commit_contract_rejection_precedes_tail_repair_mutation` | はい | **いいえ**。[test_campaign.py:1028](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_campaign.py:1028) の統合順序 test も repair 後検証を検出する。 |
| 7 | `test_campaign.py::test_commit_contract_validator_rejects_unknown_ever_active_hash` | はい | **いいえ**。resolver の素朴な削除は構文エラーまたは `resolved` 未束縛となり、env mismatch・matching resume 等も赤くする。expected nodeid も意図した理由では落ちない。 |
| 8 | `test_campaign.py::test_commit_contract_validator_rejects_contract_env_tag_mismatch` | はい | 静的にははい。valid H のため env 比較まで直接到達する。 |

#7 は「resolver 行を削除」ではなく、「`EnvContractError` を受理へ倒す」変異として再登録すべきである。#1・#6 は singleton を要求するなら、追加で赤になる nodeid を期待集合へ含める必要がある。

## fix2 / fix3 の exact 型検査

production 緩和の疑義は **refuted**。

- [ident.py:56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/ident.py:56)、[p3_autonomous_workload_trial.py:581](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/p3_autonomous_workload_trial.py:581)、[同:1652](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/p3_autonomous_workload_trial.py:1652)、[wal.py:993](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/wal.py:993) の exact 型検査は維持されている。
- fix2/fix3 はテスト側の module identity を揃えただけで、production は変更していない。
- `A._campaign_for()` 等へ渡る contract/context は `A.env_contract` / `A.build_run_context` 由来に統一済み。別 namespace の `_T530_LAYER3_CONTRACT` は同じ別 namespace の `ident.bind_environment_contract` とだけ組み合わされ、A 側 exact 境界を跨がない。
- したがって fix3 の「同型を揃えた」範囲に静的な取り残しは見つからなかった。

## merge 18 commit の影響

`ec530e9b..HEAD` の `orchestrator/` 変更は `test_check_docs.py` だけで、campaign production・T530 テストへの main 側変更はない。

`tools/check_docs.py` の強化対象は dev-wave の model 権威、段6 reasoning、不可視行・Unicode 行区切りであり、campaign test の nodeid・命名・fixture 形を走査していない。`DW-S05-C` の「新設・改名時は対応 meta-test を走らせる」という運用文も今回新設された制約ではない。sol/luna 混成化は将来の段3 dispatch にだけ効き、本 wave の実装意味とは衝突しない。静的には merge 起因の回帰なし。ただし `check_docs` 自体は本レビューでは実走していない。

## 残存・新規所見

### C-01 — autonomous の正当な Pegasus compute が拒否される

- file:line: [p3_autonomous_workload_trial.py:620](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/p3_autonomous_workload_trial.py:620)、[同:1657](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/p3_autonomous_workload_trial.py:1657)、[p3_s4_loop_trigger_gating.py:734](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/p3_s4_loop_trigger_gating.py:734)
- 判定: **real**
- 成果物影響: T-276 opt-in 済みの正当な compute build が linux H の ID/layout を先に作り、Pegasus H 束縛時の `ValueError` で WAL 作成前に拒否される。
- 修正案: site と contract を workload 開始時に一度だけ解決し、contract を `_prepare_campaign_identity()` の必須引数にする。同じ解決値を sealed な内部 drive 経路へ渡し、実際の Pegasus H/ID/layout を検査する正例を追加する。

### C-02 — ambient fallback と raw reader scope 逸脱が残存

- file:line: [s1_direct_comparison.py:239](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/s1_direct_comparison.py:239)、[s1_report.py:339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/s1_report.py:339)、[backoff_sweep.py:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/backoff_sweep.py:83)、[backoff_sweep_report.py:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/backoff_sweep_report.py:35)
- 判定: **real**
- 独立検索: `backoff_repro:99`、`p3_kickoff:100`、`p3_s4_loop:752/865/998/1085`、`p3_s4_loop_sort:197/230/322/430`、`p3_s4_red:147`、`s6_sort_sweep:190`、`s8a_trigger_sweep:288` を含む直接 ambient bind が計15か所残る。
- 成果物影響: S1 report が旧 policy-bound root でなく新H rootを読み、backoff report は prefix discoveryだけのためにも current registry を要求して歴史成果物を欠落扱いし得る。
- 修正案: config/layout helper を未束縛の純関数へ戻し、writer は guard が返した contract を一度だけ渡す。歴史 reader は slug/search-tag 導出に H を要求しない。

### C-03 — 変異事前登録の singleton 条件が成立しない

- file:line: [ident.py:63](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/ident.py:63)、[wal.py:965](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/wal.py:965)、[test_campaign.py:1006](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_campaign.py:1006)
- 判定: **real**
- 成果物影響: #1/#6/#7 の matrix receipt が「期待 nodeidだけが意味どおり殺した」という帰属を持てず、誤った理由の全体赤を検出力として受理し得る。
- 修正案: #1/#6 の期待赤集合を更新し、#7 を未知Hの例外受理変異へ再定義してから matrix を走らせる。

## 総括

**NO-GO**

- must-fix: autonomous の正当な Pegasus compute を同一 contract で ID・layout・drive まで束縛する。
- must-fix: 残る ambient lookup を writer の明示 contract 伝播へ置換し、S1/backoff の歴史 reader を現在契約から切り離す。
- must-fix: 変異 #1/#6 の期待集合と #7 の変異演算を修正する。
- validator の非恒真性、fix2/fix3 の production exact 型検査、merge 18 commit の非衝突は確認できた。
- 本レビューでは pytest・受入全走・変異 matrix・`check_docs` は実走していない。