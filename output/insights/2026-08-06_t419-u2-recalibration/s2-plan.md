判定は、単位1・2は実装可能、単位3・4を満たした状態での certify 再投入は現状の編集禁止条件では NO-GO です。特に、現 HEAD には既に self-pass gate があり、単位1の純増は「benchmark 前への移動」と「構造化診断」です。

## 前提実測の補正

- 背景2の前半は正しいです。`_acquisition_reasons` は clock を見ません（[cli.py:400–440](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:400)）。

- ただし「そのため現 HEAD でも accepted publish できる」は誤りです。現 HEAD は canonical 述語を呼ぶ `_effective_clock_self_comparison_passes()`（[cli.py:380–397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:380)）を benchmark 後の [cli.py:612–613](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:612) で適用しています。登録済み反例はこの gate 導入前の job です。

- 登録済み artifact の反例は確認できました。method は旧 `proc-cpuinfo`、sample index 40 が `3080.935`、他は `2101.0`、tolerance は 2% です（[artifact:1440–1493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1440)）。

- D176 fuse は確認できました。2 世代目は [env_contract.py:316–326](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/env_contract.py:316) で無条件拒否されます。

### (P1)〜(P4) の評価

| provisional | 判定 |
|---|---|
| P1 | 一部誤り。gate は既に存在する。実装すべき純増は早期化・診断と生死 driver。登録等を外す部分は正しい。 |
| P2 | 条件分岐が不成立。certify の CCBench configure は未検証の FetchContent transport に依存しているため、projection を次サイクルへ送って certify だけ再実行することはできない。 |
| P3 | 正しい。loader self-pass は現行 g1 を拒否するため入れない。 |
| P4 | 正しい。ただし `#PBS -b 1` は単独性の証明ではないので、process visibility・競合観測が必要。 |

## 単位1 — 取得経路の canonical self-pass gate

### 発火点の比較と選択

| 発火点 | 受理集合・副作用 |
|---|---|
| `_acquisition_reasons` | schema preflight 後、benchmark 前。同じ `profile` に canonical 述語を適用でき、現 HEAD の最終 publish 集合を変えずに約2時間の実行を省ける。 |
| `_assemble_v2` | rejected preflight と accepted/rejected artifact の双方を組み立てる serializer。無条件 gate は rejected artifact まで狭め、status 条件付きなら依然 benchmark 後になる。 |
| `window_probe` | process isolation の反復境界であり profile を所有しない。複数回発火し、clock policy と isolation を誤結合する。 |

選択は `_acquisition_reasons` の一箇所です。既存の後段 [cli.py:612–613](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:612) は削除し、二重 gate にしません。

### 編集箇所と関数

1. [execution_guard.py:183–219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:183)

   - 帯計算を一度だけ行う private evaluator を抽出する。

   ```python
   def _effective_clock_band_evaluation(
       expected: object, observed: object
   ) -> Optional[dict[str, object]]
   ```

   - 診断 projection を追加する。

   ```python
   def effective_clock_comparison_diagnostics(
       expected: object, observed: object
   ) -> dict[str, object]
   ```

   - `effective_clock_comparison_passes()` と既存 `_effective_clock_band_math_passes()` は同じ evaluator に委譲する。新しい受理判断は必ず既存 public canonical 述語を呼び、diagnostics の値を admission に使わない。

   - 診断には `median_mhz`、`lower_mhz`、`upper_mhz`、`out_of_band_count` と、各違反の `sample_index`、`sample_mhz`、`direction`、`deviation_from_median_mhz`、`outside_by_mhz` を含める。

2. [cli.py:380–440](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:380)

   ```python
   def _acquisition_reasons(
       receipt: dict, *, budget: dict, binary_sha256: str, profile: dict
   ) -> tuple[list[str], list[dict[str, object]]]
   ```

   - `_effective_clock_self_comparison_passes(profile)`、したがって canonical `effective_clock_comparison_passes()` を呼ぶ。
   - false なら reason `effective-clock-self-comparison-failed` と structured diagnostic を返す。
   - schema preflight は [cli.py:556–565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:556) が先行するため、ここでの false は正常な profile に対する帯外として診断できる。診断生成自体が失敗しても拒否は維持する。

3. [cli.py:465–473](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:465)

   ```python
   def _write_rejection(
       staging: str,
       reasons: list[str],
       budget: dict,
       *,
       diagnostics: Sequence[Mapping[str, object]] = (),
   ) -> None
   ```

   - `rejection.json` に `diagnostics.effective_clock_self_comparison` を追加する。
   - `quality.reasons` は schema 上文字列列なので、詳細をそこへ文字列化しない。

4. [cli.py:525–571](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:525)、[cli.py:660–681](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:660)

   - diagnostics accumulator を保持し、acquisition failure 時に create-only `rejection.json` へ渡す。
   - benchmark、`window-probes.json`、`calibration.json`、publish は開始しない。

### 恒真でない署名

- 正例: `P([2101.0] * 48, tolerance=2.0) == True`。median `2101.0`、帯 `[2058.98, 2143.02]`、帯外0件。

- 負例: `P([2101.0] * 40 + [3080.935] + [2101.0] * 7, tolerance=2.0) == False`。index 40、上限超過 `937.915 MHz`。

### テスト署名

- `test_effective_clock_diagnostics_are_equivalent_to_canonical_predicate()`
- `test_effective_clock_diagnostics_report_every_outlier_position_and_excess()`
- `test_cli_effective_clock_self_failure_is_acquisition_rejected_before_benchmark(tmp_path, monkeypatch, outlier_index)`
- 既存 `test_cli_published_artifact_passes_runtime_effective_clock_self_comparison`
- 既存 `test_registry_effective_clock_self_failures_are_exact_known_exception`

負例 fixture は clock 以外を valid にし、`calibrate_fn` が未呼出しであることを固定します。`_static_profile_bytes()` は clock を除外するため、別の mismatch による偽赤を避けられます。

受理集合への影響: 現 HEAD 比で最終 accepted publish 集合は不変。拒否時点と診断だけを変更し、既存 artifact の loader/registry/consumer 集合は不変です。

依存順序: execution_guard evaluator → CLI acquisition gate → integration test。

## 単位2 — 計算ノード上の α 生死 driver

### 既存経路の選択

本番取得は [env_attestation.py:669–716](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/env_attestation.py:669) の `ea.probe()` です。方式 identity は [env_attestation.py:36–43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/env_attestation.py:36) に固定されています。

薄い producer と create-only writer は [run_probe.py:23–89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/run_probe.py:23)、PBS の job 専用 create-only 配置・Python 3.10 選定・done marker は [t419_probe_causality.pbs:41–70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/probes/t419_probe_causality.pbs:41) と [同:95–139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/probes/t419_probe_causality.pbs:95) を再利用します。445 read の因果 driver 本体は用途が違うため呼びません。

### 編集箇所と関数

1. [tools/pegasus/run_probe.py:30–106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/run_probe.py:30)

   ```python
   def run_alpha_liveness(
       *,
       output: Path,
       importer: Callable[[str], object] = importlib.import_module,
       hostname_fn: Callable[[], str] = socket.gethostname,
       loadavg_fn: Callable[[], tuple[float, float, float]] = os.getloadavg,
       affinity_fn: Callable[[], set[int]] = lambda: os.sched_getaffinity(0),
       isolation_probe: Callable[..., Mapping[str, object]] = composite_competing_probe,
   ) -> tuple[int, dict[str, Any]]
   ```

   - `ea.probe()` を直接1回呼び、別実装の clock sampler は作らない。
   - Unit 1 の canonical predicate と diagnostics を使う。
   - policy の `expected_physical_cores=48`（[policy.json:12–17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/policy.json:12)）と affinity/sample count、`bnodeNNN`、α method exact を検査する。
   - `composite_competing_probe()`（[runner.py:221–297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/runner.py:221)）を probe 前後に実行する。これは canary が `pgrep` に見えることと、他の `ycsb_.*\.exe` がないことを同時に確認する。
   - load1 と `/proc/loadavg` の runnable/total snapshot を前後で記録する。単なる `-b 1` を「専有証明」とは扱わない。
   - CLI に `--alpha-liveness` を追加し、既存 default `run()` の v2 shape は変更しない。

2. 新規 `tools/pegasus/probes/t419_alpha_liveness.pbs`

   - `#PBS -A SFC`, `-q gen_S`, `-b 1`, 10分。
   - 出力先は `output/env/pegasus/t419-alpha-liveness/${PBS_JOBID//:/_}/`。
   - job directory、`liveness.json`、stdout/stderr、rc、done-marker はすべて create-only。
   - compute hostname と Python 3.10 を probe 起動前に fail-closed 検査する。
   - production 追加量は `run_probe.py` 約55行＋PBS約40行、合計100行以内を上限にする。

### 出力契約

```text
schema_version = pegasus-effective-clock-liveness/v1
purpose = pre-certify-liveness
non_certifying = true
calibration_eligible = false
hostname / pbs_jobid / affinity_cpu_count
load1.before / load1.after / runnable_tasks.before / runnable_tasks.after
isolation.before / isolation.after
effective_clock.method / tolerance_pct / median_mhz / lower_mhz / upper_mhz
effective_clock.out_of_band_count / violations
pass
```

`calibration/v2`、`acquisition_receipt`、`quality`、`sweep`、binary hash を持たず、calibration directory に置かず、publish API も呼ばないため較正として利用できません。canonical predicate false、method/48 CPU/compute marker/isolation のいずれかが不成立なら nonzero です。`out_of_band_count` は診断であり、別の admission 判定にはしません。

### テスト署名

- `test_run_alpha_liveness_accepts_in_band_profile_and_marks_non_certifying`
- `test_run_alpha_liveness_rejects_outlier_via_canonical_predicate`
- `test_run_alpha_liveness_rejects_non_alpha_method_or_non_48_cpu_shape`
- `test_run_alpha_liveness_requires_pre_and_post_isolation_canaries`
- `test_run_alpha_liveness_output_collision_preserves_existing_bytes`
- `test_t419_alpha_liveness_pbs_is_create_only_single_node_compute_only`
- 回帰: `test_run_probe_fixture_to_stdout_shape_and_file`

受理集合への影響: calibration/consumer の受理集合は変更しない。certify を投入してよいかという運用前段だけを fail-closed にします。

依存順序: Unit 1 の canonical diagnostics API → liveness mode/PBS → compute-node liveness 実測。certify は帯外0件の job receipt 後です。

## 単位3 — [T-444] proof chain 束縛

### 現在束縛されているもの

- qsub、allocation、toolchain、CCBench head/clean/build argv/binary hash、job script hash、walltime、known-values は `AcquisitionReceipt` に型付けされています（[schema_v2.py:445–469](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/schema_v2.py:445)、[同:611–627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/schema_v2.py:611)）。

- 現 artifact にも全フィールドがあります（[artifact:2–70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:2)）。

- CLI は receipt を artifact へ deep-copy し（[cli.py:443–462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:443)）、artifact bytes と binary hashを publish に束縛します。

### 束縛されていないもの

- submit receipt の `source_commit` は job 冒頭で照合されますが（[submit_certify.sh:204–229](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/submit_certify.sh:204)、[certify_calibration.sh:172–206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:172)）、embedded acquisition receipt には落ちません。

- gflags/glog head は build argv 中の文字列に現れるだけで、schema/CLI による意味的 cross-check はありません。

- masstree/mimalloc/googletest の実 source HEAD、source path、cache identity、hydrate receipt、実 transport、`fetch_third_party.py` bytes、Git hardening の成否はありません。

したがって「acquisition receipt 新設」は既に済んでいますが、T-444 の対象には明確な純増があります。`docs/archive/worklog-phase3-0804-172.md:288–291` の未束縛4項目は現在も未解消です。

### 現 scope での判定

現状では実装しません。schema や writer だけ増やしても、実際の source acquisition と CMake argv を作る [submit_certify.sh:166–229](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/submit_certify.sh:166) と [certify_calibration.sh:486–637](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:486) が編集禁止なので、保証が production 経路へ到達しません。

段4で編集面が拡張された場合の最小完全形は次です。

1. login 側で `fetch_third_party.py hydrate` と `verify-deps` の create-only receipt を submission nonce 配下へ保存し、helper bytes・receipt bytes・cache/source root を hash 束縛する。

2. compute 側でその hash を再照合し、既存 `third_party_source_contract()` と `_third_party_configure_flags()`（[silo_ladder_rung1.py:907–965](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/silo_ladder_rung1.py:907)、[同:1022–1032](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/silo_ladder_rung1.py:1022)）で `/scr` の build 用コピーを再検証する。

3. configure argv に3本の `FETCHCONTENT_SOURCE_DIR_*` と `FETCHCONTENT_FULLY_DISCONNECTED=ON` を入れる。

4. `schema_v2.py:445–469,561,611–627` に optional `SourceAcquisitionReceipt` を追加し、legacy key 集合と legacy＋proof の二形だけを exact に受理する。loader は両方を読む。

5. 新 producer では proof を必須にし、helper hash、hydrate/verify receipt `{path,sha256}`、source commit、transport、hardening、三 source の name/pin/head/path と configure argv を cross-check する。

6. [make_acquisition_receipt.py:30–48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/make_acquisition_receipt.py:30) で新 receipt を exact validation する。

これは新 producer の受理集合を狭めるので、D96（[decisions.md:4269–4296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/docs/decisions.md:4269)）に従い、新 D と境界テストを同一変更へ入れます。既存 artifact の読み取り集合は維持します。

依存順序: Unit 4 の transport 判定 → 段4裁定 → login receipt → compute projection → schema/writer/producer gate → certify。

## 単位4 — 過去 certify build の機序

### 静的に確定できたこと

- CCBench は `ThirdParty.cmake` を無条件 include します（[CMakeLists.txt:32–43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/external/ccbench/CMakeLists.txt:32)）。

- FetchContent の向き先は GitHub の masstree、mimalloc、googletest です（[ThirdParty.cmake:35–55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/external/ccbench/cmake/ThirdParty.cmake:35)、[同:106–136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/external/ccbench/cmake/ThirdParty.cmake:106)）。

- 事前取得されているのは gflags/glog だけです。policy の永続 source を pinned-clean 検査して `/scr` で build します（[policy.json:14–17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/policy.json:14)、[certify_calibration.sh:357–484](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:357)）。

- CCBench は create-only の fresh `/scr/$JOBID`、fresh worktree、fresh build dir を使います（[certify_calibration.sh:24–31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:24)、[同:486–507](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:486)）。argv に `FETCHCONTENT_SOURCE_DIR_*` はありません。

- 過去 job は bnode011 上で実行され（[qstat-f.stdout:50–61](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/output/env/pegasus/calibration/job-staging/0:867876.nqsv/qstat-f.stdout:50>)）、configure は fresh `/scr/.../ccbench-build` へ成功し（[configure.stdout:37–41](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/output/env/pegasus/calibration/job-staging/0:867876.nqsv/configure.stdout:37>)）、build は `_deps/mimalloc-build` と masstree を使っています（[build.stdout:1–22](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/output/env/pegasus/calibration/job-staging/0:867876.nqsv/build.stdout:1>)）。

したがって「login node で build/downloadした」は否定でき、job-local warm `_deps` も否定できます。成功には計算ノード側で何らかの Git transport が働いた必要があります。

ただし 867876 の env・Git global config・proxy は receipt に残っていません。runbook の後日の実測は lowercase HTTP(S) proxy の存在を示します（`docs/pegasus-runbook.md:556–608`）が、それを過去 job へ遡及して断定できません。最有力は compute-node proxy ですが、proxy、Git URL rewrite、未記録の共有 source のどれだったかは、まさにT-444の証拠欠落により確定不能です。

本 wave で必要な変更は「あり」です。certify 再実行前に verified source projection と fully-disconnected gate が必要です。しかし現在の編集禁止条件では実装不能なので、単位4自体は調査のみ、certify は投入しません。campaign 側 argv の変更は依頼どおり scope 外です。

## 単位間依存と並列化

```text
execution_guard evaluator
 ├─ Unit 1: early acquisition gate
 └─ Unit 2: alpha liveness driver

Unit 4 investigation ──> 段4裁定 ──> Unit 3 / certify projection
```

- evaluator の interface 固定後、Unit 1 の CLI 結線と Unit 2 は並列化可能です。
- Unit 3 は Unit 4 と段4裁定に依存し、現状は開始不可です。
- 運用順は tests → liveness compute job → 帯外0件確認 → T443/T444 完了確認 → certify です。

## 変異事前登録候補

### 単位1

| 変異 | 赤になるべき node |
|---|---|
| acquisition self gate を削除 | `test_cli_effective_clock_self_failure_is_acquisition_rejected_before_benchmark` |
| `all` を `any`/median-only に退化 | `test_effective_clock_diagnostics_report_every_outlier_position_and_excess` |
| index 0/末尾を走査しない | 同上の全 index parameterization |
| tolerance を100%または profile 任せにする | `test_self_gate_rejects_all_nonpolicy_equality_edges` |
| gate を benchmark 後へ戻す | integration test の `calibrate_fn` 未呼出し assert |
| canonical predicateを呼ばず診断値で判定 | predicate spy を持つ integration test |
| diagnostics の index/excessを落とす | structured rejection exact-shape test |
| loader に self-pass を追加 | `test_registry_effective_clock_self_failures_are_exact_known_exception` |
| 恒 false にする | positive publish test |

負例は他の acquisition・schema・quality 条件を満たすため、基本的に単一理由性があります。canonical math 自体の破壊は execution_guard と CLI の両方が赤くなるため、期待 node 集合を事前に二つへ固定します。

### 単位2

| 変異 | 赤になるべき node |
|---|---|
| `ea.probe()` を fixture/static readerへ置換 | probe spy を持つ positive test |
| canonical predicate を恒 true | outlier negative test |
| report の帯外件数を admission にして predicate を無視 | predicate spy test |
| `non_certifying`/`calibration_eligible` を反転 | exact output-shape test |
| create-only を `"w"` に変更 | collision-preservation test |
| pre/post isolation の片方を削除 | isolation call-count test |
| compute hostname/48 CPU gate を削除 | shape negative test |
| α method exact を見ない | non-alpha method negative test |

outlier fixture は host・CPU数・method・isolationを valid にし、clock だけを失敗させます。これで別 gate による偽 kill を避けます。

### 単位3（段4で許可された場合）

| 変異 | 赤になるべき node |
|---|---|
| helper/receipt hash を比較しない | `test_source_acquisition_receipt_rejects_tampered_hash` |
| source 1本の pin/path を交換 | `test_new_certification_rejects_projection_proof_mismatch` |
| CMake flag 1本を削除 | `test_certify_projects_exact_three_verified_sources` |
| disconnected flag を削除 | 同上 |
| hardening=falseを受理 | schema bad-field test |
| 新 producer が legacy proof 無しを受理 | `test_cli_new_certification_requires_source_proof_before_benchmark` |
| legacy artifact readerまで拒否 | registry既知例外 test |

missing key は schema preflight が先に拒否し、semantic gate の変異を mask します。semantic mutation では exact shape を維持したまま hash/path 値だけを変える必要があります。

### 単位4

調査のみなので現 scope の code mutation はありません。projection が許可された場合は「source flag 1本削除」「GitHub URL fallback 復活」「fresh `_deps` download を許可」を単位3の static argv test で killします。

## 実装しない項目

- `env_contract.py`、世代登録、pin、`EXPECTED_GENERATION_HASHES`、`contract_sha256`、frozen manifest。
- `KNOWN_SELF_INCONSISTENT_CALIBRATIONS` の空化。
- `load_verified_calibration()`、registry、consumer の self-pass。
- `_assemble_v2` や `window_probe` への clock gate。
- campaign 群の CMake argv。
- 禁止された submit/certify script の変更。段4で明示的に編集面が変わらない限り Unit 3 と certify 再投入を行わない。

## 実走すべき node id

計算ノードで少なくとも以下を実行します。

- `orchestrator/tests/test_execution_guard.py::{new diagnostic tests}`
- `orchestrator/tests/test_calibrator_certify.py::{new early-gate tests}`
- `orchestrator/tests/test_calibrator_certify.py::test_cli_published_artifact_passes_runtime_effective_clock_self_comparison`
- `orchestrator/tests/test_env_contract.py::test_registry_effective_clock_self_failures_are_exact_known_exception`
- `orchestrator/tests/test_env_attestation.py::test_load_verified_calibration_accepts_result_to_dict_derived_v2`
- `orchestrator/tests/test_effective_clock_policy.py`
- `orchestrator/tests/test_pegasus_tools.py::{new liveness tests}`
- Unit 3 許可時のみ `test_schema_v2.py`、`test_pegasus_thirdparty_fetch.py`、receipt/projection tests。
- 関連テスト後に repository 規律どおり `check_codex_agents.py`、`check_docs.py`、commit 後 provenance audit。

今回は read-only 静的調査のみで、pytest は一件も実行しておらず、緑は主張しません。worktree は clean でした。

## 総括

- 骨子は、既存 canonical gate を benchmark 前へ移し、同じ evaluator から構造化診断を出すこと。
- α 生死 driver は本番 `ea.probe()` を1回だけ呼ぶ non-certifying/create-only jobにする。
- 現 HEAD 比で Unit 1 は publish 受理集合を変えず、既存 reader は一切狭めない。
- 最大の risk は、certify の FetchContent transport が未束縛で再現不能なこと。
- T-444 には純増があるが、禁止された submit/certify 境界なしでは実効的に結線できない。
- 段4の択一は、(A) 両 script の限定編集を許可してT443/T444完了後にcertify、または (B) 編集禁止を維持してUnit 1/2までで停止しcertifyを延期、の二択。