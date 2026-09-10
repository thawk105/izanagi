## 総括

- 採用案は第 3 案「rep 証跡を保存し、完全な rep だけを既存 `throughputs` へ射影する二層設計」とする。
- protocol の除外理由 4 件と seal 済み `floor_protocol.json` 774 bytes は一切変更しない。
- 新区分は protocol 外の `rep_integrity_failure` とし、rc・counter 完備性だけから導出する。
- 異常 rep の tps は `rep_observations` に残すが、session median の入力には入れない。
- precedence は competing → launch → rep integrity → partial → performance → valid とする。
- no-perf pilot は counter を `not_required` とし、rc==0 は引き続き必須とする。T-967 には触れない。
- 証跡を復元できない旧 v2 journal は、schema v3 化により明示的に resume 拒否する。
- 本段では静的検査のみ実施し、pytest は実走していない。

### 1. 除外区分の択一

| 案 | 内容 | 判断 |
|---|---|---|
| B1 | `SessionRecord.excluded_reason` に 5 番目を追加 | 不採用。凍結 protocol の 4 理由と同名 field の意味が食い違う。単一源を分断するか seal を壊す。 |
| B2 | rep 完備性違反数を追加し、違反 rep の tps を `throughputs` から落として既存 partial 判定へ送る | 方向は正しいが、そのままでは落とした tps と理由の対応が失われ、「都合の悪い rep を捨てた」ことを verifier が反証できない。 |
| 第 3 案 C | 全 rep の rc・counter 状態・raw tps を `rep_observations` に保存し、そこから `rep_integrity_failures` と統計入力 `throughputs` を独立再導出する | 採用。B2 の凍結安全性を保ちつつ、悪い tps も証跡に残し、producer と verifier の双方で射影を照合できる。 |

凍結依存鎖は次のとおりである。

- [s8b_floor_stats.py:47-60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_floor_stats.py:47) の `ALLOWED_EXCLUDED_REASONS` が固定順 4 件を持つ。
- [s8b_approved.py:37-58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_approved.py:37) がそれを `APPROVED_REASONS` として再輸出する。
- [s8b_floor_campaign.py:540-564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_floor_campaign.py:540) の builder が `allowed_excluded_reasons` へ焼き込み、同時に validator を通す。
- [floor_protocol.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/output/s8b-freeze/floor_protocol.json:1) はその 4 件を持つ 774 bytes の seal 済み成果物である。hash pin は [test_frozen_artifacts.py:41-49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/tests/test_frozen_artifacts.py:41)、key-set pin は同ファイル 93-123 にある。
- 独立した受理側では [s8b_floor_contract.py:44-55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_floor_contract.py:44) の `_APPROVED_REASONS` が 4 件を固定し、[同:201-225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_floor_contract.py:201) が順序を含む完全一致を要求する。

したがって、seal を拒否させずに新区分を置けるのは protocol の `excluded_reason` 表ではなく、protocol 検証後に生成される session journal/result 層である。`ALLOWED_EXCLUDED_REASONS`、`s8b_approved.APPROVED_REASONS`、`_floor_contract._APPROVED_REASONS`、builder 560 行目は変更しない。新しい定数 `REP_INTEGRITY_EXCLUSION_CLASS = "rep_integrity_failure"` は stats の session artifact 契約として別名で置き、protocol 理由表には接続しない。

### 2. rep 完備性の機械契約

対象箇所は [runner.py:351-397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/calibrator/runner.py:351) の `run_once` と [同:402-488](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/calibrator/runner.py:402) の `measure_point`。

各 logical rep に次の exact-key record を 1 件残す。

- `rep_index`: `0..reps-1` の一意な exact int
- `returncode`: subprocess が完了した場合の exact int、取得不能なら null
- `counter_status`: `complete | incomplete | not_required | unknown`
- `missing_perf_events`: `PERF_EVENTS` の固定順 subset
- `throughput`: parse できた raw tps、取得不能なら null

rc は既存 `rep_returncodes` seam を再利用する。`measure_point` に opt-in の `rep_observations` sink を追加し、その指定時だけ [runner.py:453-461](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/calibrator/runner.py:453) から `run_once(rep_returncodes=...)` を渡す。未指定時は現行どおり kwarg 自体を渡さず、既存 monkeypatch signature を維持する。

counter 完備対象は [runner.py:37-38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/calibrator/runner.py:37) の全 4 event とする。

- `LLC-load-misses` → `llc_load_misses`
- `LLC-loads` → `llc_loads`
- `instructions` → `instructions`
- `cycles` → `cycles`

[perfparse.py:23-30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/calibrator/perfparse.py:23) が対応を定め、修飾子は同 39-44 行で除去する。`<not counted>`、`<not supported>`、空、不正数値は同 35-56 行で `None` になり、parser は非 `None` の値だけを属性へ設定する（59-90 行）。したがって、4 属性がすべて非 `None` のときだけ `complete` とする。値 0 は「取得済み」なので complete であり、`llc_miss_rate` の分母判定とは混同しない。

`rep_integrity_failures` は次のどちらかを満たさない logical rep 数とする。

1. `type(returncode) is int and returncode == 0`
2. perf 使用時は `counter_status == "complete"`、no-perf 時は `counter_status == "not_required"`

throughput、median、CV、値の大小はこの数に一切使わない。観測行欠落、重複 index、null rc、`unknown`、不正型は fail-closed で当該 rep を違反とする。

no-perf は既存の [s8b_floor_campaign.py:228-237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_floor_campaign.py:228) と [同:3411-3429](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_floor_campaign.py:3411) が決めた `use_perf` をその場で使う。`use_perf=False` では全 rep を `not_required` とし、counter 欠落を違反にしないが rc は検査する。protocol、oracle、manifest へ perf 条件を新たに伝播させないため、T-967 には踏み込まない。

### 3. producer と precedence

[s8b_floor_campaign.py:1058-1076](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_floor_campaign.py:1058) の射影を次の形へ置き換える。

- `ScalePoint.throughputs` を無条件コピーしない。
- `rep_observations` から `rep_integrity_failures` を導出する。
- rc/counter が完備した rep の raw tps だけを、rep 順の `throughputs` に射影する。
- observation 内の非 null tps 列と元の `ScalePoint.throughputs` が一致しなければ、証跡と計測点の不整合として `CampaignAbort` にする。
- 違反 rep の tps は observation には残す。残った良い rep だけで median を取ることはなく、少なくとも 1 rep 違反なら `len(throughputs) < reps` となり、既存 [assess_session:141-152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_floor_stats.py:141) が session 全体を partial とする。

[s8b_floor_campaign.py:2424-2438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_floor_campaign.py:2424) の変更後 precedence は上から次の順とする。

1. pre/post probe の競合 → `competing_process`
2. measure 全体例外、全 rep 実行不能、現行の矛盾状態 → `launch_failure`
3. `rep_integrity_failures > 0` → effective class `rep_integrity_failure`
4. 完備性以外の tps 本数不足、非有限、非正値 → `nonfinite_or_partial_output`
5. 完全値の CV 超過 → `performance_anomaly`
6. その他 → valid

3 の session でも protocol field `excluded_reason` は、射影後の生値から必然となる既存 `nonfinite_or_partial_output` を持たせる。result/report 用の `exclusion_class` だけを `rep_integrity_failure` とする。これにより `_Runner._check_reason` の protocol 4 理由検査（[同:2223-2241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_floor_campaign.py:2223)）を緩めない。

### 4. 記録面と resume

[s8b_floor_stats.py:158-175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_floor_stats.py:158) の `SessionRecord` に次を追加する。

- `rep_observations: tuple`
- `rep_integrity_failures: Optional[int]`

通常の measure 完了では count を exact int にする。pre-probe skip や証跡を持たない launch error は null を許すが、competing/launch より下の precedence で null が現れた場合は fail-closed 違反とする。

[s8b_floor_stats.py:403-425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_floor_stats.py:403) の `_REQUIRED_SESSION` に両 field を追加し、新 schema では必須にする。[s8b_floor_campaign.py:2454-2487](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_floor_campaign.py:2454) の journal `event=session` と、[同:2653-2667](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_floor_campaign.py:2653) の result 再構成へ同じ値を通す。

[同:2698-2717](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_floor_campaign.py:2698) の `excluded` と `attempts` には `rep_integrity_failures` と派生 `exclusion_class` を追加し、[同:2842-2869](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_floor_campaign.py:2842) の Markdown 集計は `exclusion_class` を優先表示する。top-level field は増やさない。

過去 journal は互換受理しない。理由は、v2 session から rc/counter 証跡を復元できず、0 件として補うと正しさゲートを緩めるためである。

- [s8b_floor_contract.py:30-32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_floor_contract.py:30) の `RESULT_SCHEMA` と `JOURNAL_SCHEMA` を v3 にする。`PROTOCOL_SCHEMA`、`FORMULA_ID`、`MANIFEST_SCHEMA` は据え置く。
- [s8b_floor_campaign.py:3577-3604](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_floor_campaign.py:3577) が旧 v2 campaign-start を副作用前に明示拒否する。偶発的な KeyError にはしない。
- v3 resume では同 3706-3747 行の start/session 対応検査に observation の exact schema と派生 count 検査を追加する。
- `M-finalize-pending` の旧 v2 も publish しない。T-968 前の median を後から公開する抜け道になるためである。

inner schema の exact consumer も更新が必要である。[s8b_ratified_freeze.py:199-220](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_ratified_freeze.py:199) の result projection key、同 223-248 行の journal session key、同 2181-2194 行の exact 検査を合わせる。[s8b_holdout_freeze.py:1315-1318](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_holdout_freeze.py:1315) の schema エラー文も v3 に合わせる。これは oracle 変更ではなく、floor result の既存 consumer 取り残し防止である。

### 5. verifier

[s8b_floor_stats.py:501-545](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_floor_stats.py:501) の session 検査へ、producer と独立した再導出を追加する。

- observation の exact key、件数、index 全単射、rc exact type、counter status、missing event の固定順 subset を検査する。
- `derived_integrity_failures` を再計算し、申告 count と完全一致させる。
- observation から integrity-qualified tps 列を再構成し、`SessionRecord.throughputs` と完全一致させる。
- count > 0 なら、competing/launch が優先する場合を除き、effective class は必ず `rep_integrity_failure`、legacy `excluded_reason` は必ず partial、`valid` は false、`session_median` は nullでなければならない。
- count == 0 なのに `rep_integrity_failure` を申告、または observation が全件良好なのに正当な tps を integrity 理由で落としている場合は拒否する。
- malformed、unknown、count null が通常 session に現れた場合はエラーを返し、artifact publish を止める。

要求された双方向は次の検査になる。

- (a) rc 非 0、counter incomplete、unknown の証跡があるのに count 0、全 tps 採用、`valid=True`、median 非 nullのいずれかを主張する → 赤。
- (b) 全 rep が rc 0 かつ counter complete/not-required なのに count > 0 または `exclusion_class=rep_integrity_failure` を主張する → 赤。

さらに [同:582-667](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_floor_stats.py:582) の cells/floors 再計算に加え、`excluded`・`attempts` の `exclusion_class` も session から再構成して照合する。新区分を表示面だけで捏造する余地を残さない。

### 6. テスト計画

fixture は [test_s8b_floor_campaign.py:399-460](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/tests/test_s8b_floor_campaign.py:399) の `_FakeScalePoint` / `_make_measure_fn` に、明示的な rc・counter status・raw tps を渡せる seam を足す。正常既定は全 rc 0・全 counter complete とし、partial fixture は「5 observation、1 tps null、integrity failure 0」として既存 partial と新区分を混同しない。

追加 nodeid は次を予定する。

- `orchestrator/tests/test_s8b_floor_campaign.py::test_rep_integrity_nonzero_rc_tps_never_reaches_median_positive_control`
- `orchestrator/tests/test_s8b_floor_campaign.py::test_rep_integrity_missing_each_perf_event_excludes_session`
- `orchestrator/tests/test_s8b_floor_campaign.py::test_rep_integrity_precedence_below_competing_and_launch_above_partial_and_performance`
- `orchestrator/tests/test_s8b_floor_campaign.py::test_no_perf_rep_integrity_requires_zero_rc_and_marks_counters_not_required`
- `orchestrator/tests/test_s8b_floor_campaign.py::test_rep_integrity_evidence_round_trips_journal_result_and_report`
- `orchestrator/tests/test_s8b_floor_campaign.py::test_resume_rejects_v2_journal_without_rep_integrity_evidence`
- `orchestrator/tests/test_s8b_floor_campaign.py::test_resume_v3_preserves_rep_integrity_evidence`
- `orchestrator/tests/test_s8b_floor_stats.py::test_verify_rejects_integrity_violation_with_valid_claim`
- `orchestrator/tests/test_s8b_floor_stats.py::test_verify_rejects_false_rep_integrity_exclusion`
- `orchestrator/tests/test_s8b_floor_stats.py::test_verify_rejects_rep_integrity_count_and_projection_mismatch`
- `orchestrator/tests/test_s8b_floor_stats.py::test_verify_rejects_malformed_rep_observation_indices_and_types`
- `orchestrator/tests/test_s8b_floor_stats.py::test_verify_accepts_counter_not_required_but_not_nonzero_rc`

positive control は raw tps を `[100, 100, 101, 103, 103]` とし、まず既存 `assess_session` 単体なら低 CV・5/5 本で median 101 を作れることを確認する。その中央 rep に rc 非 0、または 1 event 欠落を与え、raw tps は observation に残る一方、qualified `throughputs` は 4 本、session median は null、cell medians に 101 が入らないことを確認する。既存 partial、非有限、CV gate のどれにも初めから落ちない入力なので恒真ではない。

既存期待値は次の扱いとする。

- [test_s8b_floor_stats.py:120-124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/tests/test_s8b_floor_stats.py:120) の 4 理由・固定順は変更しない。
- [test_s8b_floor_campaign.py:1867-1878](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/tests/test_s8b_floor_campaign.py:1867) の欠落・余分・並べ替え拒否も変更しない。
- partial、competing、performance の既存 `excluded_reason` 期待値は維持する。
- `_sess` と `_honest_artifact`（[test_s8b_floor_stats.py:87-97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/tests/test_s8b_floor_stats.py:87)、同 360-406 行）は正常 observation/count を追加する。
- ratified fixture の exact journal/result key、schema v3 期待を更新する。凍結 `floor_protocol.json` の期待値は更新しない。

runner seam 自体には、隣接して次も必要である。

- `orchestrator/tests/test_calibrator.py::test_measure_point_rep_observations_reuse_returncode_seam_and_cover_all_perf_events`
- `orchestrator/tests/test_calibrator.py::test_measure_point_rep_observations_marks_no_perf_not_required`

既存 `test_measure_point_survives_partial_rep_failure` と `test_measure_point_all_reps_fail_raises` は、opt-in なしの monkeypatch signature 回帰としてそのまま残す。

### 7. 変異事前登録

| 検査 | 最小変異 | 落ちるべき nodeid |
|---|---|---|
| rc 収集 | `run_once` へ既存 `rep_returncodes` seam を渡さない | `test_measure_point_rep_observations_reuse_returncode_seam_and_cover_all_perf_events` |
| 4 event 完備 | `cycles` など 1 event を判定対象から外す、または `all` を `any` にする | `test_rep_integrity_missing_each_perf_event_excludes_session[...]` |
| no-perf 分岐 | `not_required` を incomplete と扱う | `test_no_perf_rep_integrity_requires_zero_rc_and_marks_counters_not_required` |
| producer 射影 | 新コードを wave 前の [s8b_floor_campaign.py:1074](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t968-floor-rep-integrity/orchestrator/campaign/s8b_floor_campaign.py:1074) の「全 throughputs コピー」へ戻す | positive control |
| session 全体無効 | 違反 rep だけ除き、残り 4 本で median を許す | positive control |
| precedence | partial を rep integrity より先にする | `test_rep_integrity_precedence_below_competing_and_launch_above_partial_and_performance` |
| competing/launch 優先 | rep integrity を最上位へ移す | 同上 |
| verifier (a) | evidence/count/qualified tps 突合ブロックを削除し、wave 前の throughput/reason 検査だけに戻す | `test_verify_rejects_integrity_violation_with_valid_claim` |
| verifier (b) | 申告 `rep_integrity_failures` を再導出せず信用する | `test_verify_rejects_false_rep_integrity_exclusion` |
| observation 完全集合 | `zip` だけで比較し、短い列・重複 index を許す | `test_verify_rejects_malformed_rep_observation_indices_and_types` |
| result projection | `exclusion_class` を legacy `excluded_reason` だけから作る | round-trip/report テスト |
| resume | v2 欠落 field を count 0 で補う | `test_resume_rejects_v2_journal_without_rep_integrity_evidence` |
| monkeypatch seam | opt-in でない全呼び出しにも新 kwarg を送る | 既存 `test_measure_point_survives_partial_rep_failure` |
| 凍結境界 | `ALLOWED_EXCLUDED_REASONS` 自体へ 5 番目を足す | 既存 `test_allowed_reasons_closed_table_order` と `test_validate_protocol_pins_reasons_exact_order` |

### 8. リスクと波及

- silo ladder、calibrator sweep、oracle pipelineなど非 floor 呼び出しは、新しい observation seam の既定を無効にし、`run_once` の 3-tuple と `ScalePoint` を変更しなければ無影響である。`require_complete_metrics` の既存例外契約も変更しない。
- floor の既定 closure だけが observation を opt-in する。pilot の注入 `measure_fn` が証跡を返さない場合は unknown として無効化するため、テスト fixture と明示的な開発用 caller は更新が必要である。
- `s8b_ratified_freeze` は journal/result の exact-key consumer なので、更新漏れがあると新しい official result を全拒否する。これは必須の隣接変更であり、s8b oracle や silo ladder へ広げる変更ではない。
- v2 resume 非互換は意図的である。証跡の無い過去 session を valid に補う安全な変換は存在しない。運用上は新 run が必要になる。
- protocol 4 理由、`FORMULA_ID=s8b-floor-stats/v2`、manifest schema、凍結 artifact bytes は不変とする。統計式は変えず、統計へ渡す rep 資格付けとその検証だけを強化する。
- 分類条件には rc と counter 状態以外を入れない。raw throughput は証跡保存と既存 partial/performance 判定にだけ使い、rep integrity の採否には使わない。

調査は base commit `01487bb4`、clean worktree に対する read-only 静的確認のみである。Web 検索、ファイル編集、pytest、build は実施しておらず、検査を「緑」とは報告しない。