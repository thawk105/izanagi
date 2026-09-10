## 総括

専用 module `orchestrator/campaign/floor_pair_driver.py` と専用テスト 1 本を新設し、既存 `between_run_floor.py` は変更しない設計を採る。
凍結 spec は repo 内の tracked JSON を path と期待 SHA-256 で読み、全項目を exact-key 検証する。測定は既成の `measure_point` と probe 分類器だけを再利用する。
対照対の両側は単一の candidate artifact を共有する表現にし、別々の `measure_point` 呼出しで独立セッションにする。欠測が 1 件でもあれば上限も床候補も生成しない。
実走単位は時間窓ごとの create-only JSONL、全窓完了後に別の create-only summary を生成する。
最も割れる点は P2 の統計関数である。現状に適切な既存上限関数がないため、`sample_max/v1` を spec が明記した場合だけ組込み `max` へ束縛する閉じた registry を推奨する。
静的調査のみで、repository 変更と pytest 実走は行っていない。

## 実装プラン

1. **新規 module と公開 API**

   `orchestrator/campaign/floor_pair_driver.py:1-760` を新設する。予定する公開面は次に限定する。

   ```python
   @dataclass(frozen=True)
   class FrozenPerfConfig:
       records: int
       threads: int
       workload: tuple[tuple[str, str], ...]
       extime: int
       reps: int

   @dataclass(frozen=True)
   class FloorPairSpec: ...
   @dataclass(frozen=True)
   class PlannedSession: ...
   @dataclass(frozen=True)
   class MeasurementPlan: ...
   @dataclass(frozen=True)
   class MeasurementRequest: ...
   @dataclass(frozen=True)
   class MeasurementResult: ...
   @dataclass(frozen=True)
   class GainDifference: ...
   @dataclass(frozen=True)
   class WindowRunResult: ...
   @dataclass(frozen=True)
   class FinalFloorResult: ...

   def load_frozen_spec(
       path: Path, expected_sha256: str, *, repo_root: Path
   ) -> FloorPairSpec: ...

   def make_measurement_plan(spec: FloorPairSpec) -> MeasurementPlan: ...

   def compute_gain_difference(
       candidate_1_tps: float,
       candidate_2_tps: float,
       reference_tps: float,
   ) -> GainDifference: ...

   def apply_upper_statistic(
       function_id: str, values: Sequence[float]
   ) -> float: ...

   def run_window(
       spec: FloorPairSpec,
       plan: MeasurementPlan,
       window_id: str,
       *,
       measure_fn: Callable[[MeasurementRequest], MeasurementResult],
       probe_fn: Callable[[Sequence[str], float], tuple[int, str, str]],
       now_fn: Callable[[], datetime],
   ) -> WindowRunResult: ...

   def finalize_floor(
       spec: FloorPairSpec,
       plan: MeasurementPlan,
       *,
       now_fn: Callable[[], datetime],
   ) -> FinalFloorResult: ...

   def main(argv: Sequence[str]) -> int: ...
   ```

   例外は `floor_pair_driver.py:35-55` に `FloorPairSpecError(ValueError)`、`FloorPairBindingError(RuntimeError)`、`FloorPairRunError(RuntimeError)` を置く。出力衝突だけは標準の `FileExistsError` をそのまま外へ出す。

2. **凍結 spec の形と schema**

   `floor_pair_driver.py:137-330` に strict loader を置く。top-level は次の exact key 集合とし、全 field を必須にする。

   - `schema`
   - `provenance`
   - `environment`
   - `artifacts`
   - `cells`
   - `pairs`
   - `windows`
   - `randomization`
   - `statistics`
   - `failure_policy`
   - `outputs`

   主な nested schema は次のとおりとする。

   - `provenance`: calibration artifact、execution contract、build receipt の各 repo-relative path と SHA-256、source commit identity。
   - `environment`: `site`、`env_tag`、`clocks_per_us`、`numactl_argv`、`use_perf`、`timeout_s`、`extra_env`、`probe_argv`、`probe_timeout_s`、`settle_first`。
   - `artifacts[*]`: `artifact_id`、binary path/SHA-256、build receipt path/SHA-256、`trace`。
   - `cells[*]`: `cell_id`、`protocol`、完全な `perf_config`、candidate/reference artifact の参照。
   - `perf_config`: `records`、`threads`、`workload`、`extime`、`reps` の全 5 field。positive exact int と、exact workload map を要求する。
   - `windows[*]`: `window_id`、`campaign_id`、UTC の半開区間、`sample_count`、`pair_ids`、`artifact_relpath`。
   - `randomization`: versioned algorithm ID と 64 桁 lowercase hex seed。
   - `statistics`: session reducer、stratum upper、全 stratum の閉集合、最終 combiner。
   - `failure_policy`: `all_planned_samples_required/v1`、`retry_count=0`、`require_all_reps=true`。
   - `outputs`: format ID と final summary の repo-relative path。

   JSON duplicate key、`NaN`、`Infinity`、未知 key、欠落、`bool` を整数として使うこと、空 ID、非正値、重複 ID、範囲外時刻、重なる時間窓はすべて `FloorPairSpecError` にする。I/O、hash、tracked blob、参照 artifact の不一致は `FloorPairBindingError` にする。

   `pipeline.PerfConfig` は `extime=3`、`reps=5` を既定に持つ (`orchestrator/campaign/pipeline.py:167-174`) ため、その constructor へ渡す際も 5 field を必ず明示する。新規 dataclass は全 field を default なしにし、検証コードでは `.get()`、`setdefault()`、`or fallback` を使わない。テストでは全 dataclass field の `default/default_factory` が `MISSING` であることと、各必須 field の削除が必ず失敗することを固定する。これが「凍結項目の既定値ゼロ」の機械保証になる。

3. **spec と checkout の束縛**

   `floor_pair_driver.py:165-215` で次の順に照合する。

   1. path を `repo_root` 配下へ resolve し、path component の symlink、checkout 外、非 regular file を拒否。
   2. bytes を 1 回だけ読む。
   3. 期待 SHA-256 の形式を検査し、同じ bytes の SHA-256 と比較する。
   4. JSON decode より前に、`git show HEAD:<repo-relative-path>` の bytes と一致することを確認する。未追跡、HEAD と異なる作業木 bytes は拒否。
   5. hash と tracked blob が一致した後だけ strict JSON parse を行う。

   したがって hash 不一致と JSON 不正が同時にある場合は、hash 不一致が先に `FloorPairBindingError` になる。artifact header には repo-relative spec path、期待値、実測 SHA-256、実行時 HEAD を記録する。

   calibration、contract、build receipt も `floor_pair_driver.py:216-260` で同じ path/hash 規則を適用する。binary は window 開始前と各 session の直前に `buildcache.assert_binary_sha256` で再照合する。既存 helper の full 64 桁照合契約は `orchestrator/campaign/buildcache.py:581-611` にある。

   P1 には賛成し、「repo 内」という宣言だけでなく HEAD の tracked blob と byte 一致するところまで強める。

4. **対照対と共通参照点**

   `floor_pair_driver.py:270-330` で各 pair を次の形にする。

   ```json
   {
     "pair_id": "pair-...",
     "cell_id": "cell-...",
     "reference_artifact_id": "reference-...",
     "sides": [
       {"side_id": "candidate_1", "candidate_artifact_id": "candidate-X"},
       {"side_id": "candidate_2", "candidate_artifact_id": "candidate-X"}
     ]
   }
   ```

   両側を別 binary path として表現せず、同一の `candidate_artifact_id` を 2 つの論理 side が共有する。loader は side ID が exact 2 件であること、candidate artifact ID が同値であることを要求する。これにより「hash が偶然一致した別候補」への差替え面も持たない。

   candidate/reference artifact はともに `trace is False` を必須とし、実測直前の binary hash を session record に残す。candidate の両 side は同一 artifact、同一 cell、同一 `FrozenPerfConfig` を使うが、別々の `measure_point` 呼出しと別 session ID を持つ。

   各 D 標本は candidate 2 session と reference 1 sessionの 3 session で構成する。reference session の 1 つの `reference_tps` を両 gain の共通分母に使い、別 reference や前回値への fallback は置かない。

5. **決定的な測定計画**

   `floor_pair_driver.py:332-395` の `make_measurement_plan` は乱数 global state を使わない。spec の 256-bit seed を鍵とし、次を HMAC-SHA256 の辞書順 rank で決める。

   - window 内の `(pair_id, sample_index)` の実行順。
   - 各標本内の `candidate_1`、`candidate_2`、`reference` の順。
   - 各 session の固定 ID と schedule index。

   HMAC message には schema ID、spec SHA-256、window ID、pair ID、sample index、role を NUL 区切りで入れる。algorithm ID は spec に `hmac-sha256-rank/v1` と明記されていなければ拒否する。seed、全 session plan、plan の canonical SHA-256 を validation-only の stdout と各 window header の両方へ記録する。

   window は UTC の `[not_before, not_after)`、互いに非重複、campaign ID が全て異なることを要求する。CLI は 1 process につき 1 window だけ実行し、開始時と各 session 前に時刻域を確認する。待機はせず、域外なら測定しない。

   `measure_point` 1 呼出しを 1 session とし、内部 reps は独立 campaign 数へ数えない。artifact では `window_count`、`pair_sample_count`、`session_count`、`reps_per_session` を別 field にする。同じ window の連続 session を別時間窓として集計する経路は作らない。

6. **事前 probe、測定、事後 probe、追記**

   `floor_pair_driver.py:452-560` に task 専用の薄い wrapper を置く。`s8b_floor_campaign.strict_probe` 自体は import しない。同 module は `orchestrator/campaign/s8b_floor_campaign.py:89-101` で多数の campaign 固有依存を引くためである。

   代わりに、既に軽量側にある `CompetingBenchProbeError` と `classify_competing_probe` (`orchestrator/calibrator/runner.py:297-379`) を直接 import する。probe command と timeout は spec 由来で、default を置かない。

   `floor_pair_driver.py:520-610` の `_run_planned_session` は固定順を次のようにする。

   1. binary SHA-256 再照合。
   2. pre-probe。
   3. pre が clear の場合だけ `measure_fn`。
   4. measure の成否にかかわらず finally 相当で post-probe。
   5. probes、raw reps、例外分類、時刻、binary hash を 1 session record として JSONL へ appendし、flush/fsync。

   pre が competing/indeterminate の場合も post-probe を取り、measurement は `not_run` と記録する。post が competing/indeterminate なら取得済み throughput も不適格にする。これは `s8b_floor_campaign.py:6077-6103` の形を専用 module 内で小さく再現し、分類ロジックだけ共有する案である。

   P3 には賛成する。CV を返す `between_run_floor.measure_point_floor` (`between_run_floor.py:202-252`) は使わず、`measure_point` (`runner.py:1057-1077`) を直接 adapter する。`p2_2._assert_single_tenant` (`p2_2.py:300-310`) は post-probe と raw 出力を持たないため使わない。

7. **落ちた標本の表現と除外防止**

   `floor_pair_driver.py:542-650` の JSONL は、測定前に全計画を持つ header を fsync する。その後、全 session ID に次の fixed status のいずれかを必ず 1 件残す。

   - `complete`
   - `pre_probe_competing`
   - `pre_probe_indeterminate`
   - `measure_failed`
   - `measure_incomplete`
   - `post_probe_competing`
   - `post_probe_indeterminate`
   - `binary_binding_failed`
   - `outside_window`
   - `not_run_after_fail_closed`

   retry、置換 session、追加 sample は作らない。最初の不適格 session 後に停止する場合も、残りの計画 ID を `not_run_after_fail_closed` として追記する。

   `finalize_floor` は header の全計画 ID と記録 ID の exact equality、各 session の reps 件数、各 pair sample の 3 role 完備を要求する。1 件でも非 complete または非有限値なら、全体を `not_generated_missing_samples` とし、成功分だけから upper を計算しない。したがって失敗した高い D だけを捨てて値を小さくする経路が構造上存在しない。

8. **D、上限統計、値域外**

   `floor_pair_driver.py:397-450` に純関数を置く。`compute_gain_difference` は bool を除く有限正 throughput だけを受け、次を返す。

   ```text
   gain_1 = candidate_1_tps / reference_tps - 1
   gain_2 = candidate_2_tps / reference_tps - 1
   D = abs(gain_1 - gain_2)
   ```

   window artifact には各 session の raw `throughputs` を残し、session median、gain、D は derived record とする。finalizer は保存された median や D を信用せず、raw reps から再計算して一致検査する。既存 `ScalePoint.throughput` が reps の中央値であることは `orchestrator/calibrator/model.py:78-87`、rep raw の収集面は `runner.py:1104-1117` にある。

   `apply_upper_statistic` は closed registry とし、spec が exact ID を名指ししない限り呼べない。推奨する初期 registry は次の 2 件だけである。

   - `sample_max/v1` → 各閉じた stratum の `max(D)`。
   - `max_over_closed_strata/v1` → spec の `closed_strata` 全件の最大。

   function ID の既定値、分位、信頼水準、標本数の推測は置かない。`closed_strata` は予定された全 `(window_id, pair_id)` 集合と exact equality を要求し、測った一部だけを最大対象にできないようにする。

   最終 upper が有限かつ `0 <= upper < 1` のときだけ `candidate_floor` を出す。`upper >= 1` は丸めず、その実値を残して `status="not_generated_upper_out_of_domain"`、`candidate_floor=null` とする。JSON writer は `allow_nan=False` とし、表示用丸め値を authoritative field に持たせない。

9. **create-only 出力**

   `floor_pair_driver.py:562-690` に writer を置く。各 window の `artifact_relpath` と final summary path は spec が完全に与え、loader が次を検証する。

   - 全 path が repo root 配下。
   - 全 window と summary で byte 単位に相異なる。
   - parent directory が既存 regular directoryで symlink でない。
   - path basename を driver が補完しない。

   `run_window` は測定前の最初の副作用として対象 JSONL を `os.open` の `O_CREAT|O_EXCL|O_APPEND|O_WRONLY|O_NOFOLLOW` で開く。既存なら `FileExistsError` で終了し、`measure_fn` は呼ばれない。途中失敗や crash でも file を削除せず、可能なら terminal record を追記する。再実行は同 path の存在で停止する。

   実装には `unlink`、`replace`、`rename`、一時 file の publish を置かない。`finalize_floor` も window artifact を読み取るだけで、summary を別 path へ exclusive-create する。summary には各 window artifact の SHA-256 と、raw から再計算した全導出を含める。

   既存 `_write_out` の create-only 判定 (`between_run_floor.py:255-271`) は参考にするが、同関数は campaign/window identity を filename に持たないため流用しない。

10. **測定 seam と非測定 mode**

    `floor_pair_driver.py:490-520` の `_measure_with_runner` は、`MeasurementRequest` から `measure_point` の全 relevant 引数を明示的に渡す。`runner.py:1057-1070` にある `extime`、`reps`、`numactl`、`settle_first`、`timeout_s`、`require_all_reps`、`require_complete_metrics`、`use_perf` の既定には依存しない。rep observations、return codes、timestamps の sink も常に渡す。

    `run_window` では `measure_fn` を必須 keyword にし、default を置かない。CLI の `--execute-window` 分岐だけが `_measure_with_runner` を明示注入する。build は行わず、凍結 spec が束縛した事前作成済み trace-disabled binary だけを測る adapter とする。

    CLI は次の 3 mode を mutually exclusive かつ 1 つ必須とする。

    - `--validate-only`: loader と plan 生成だけ。stdout へ canonical plan を出し、出力予約、probe、measure はしない。
    - `--execute-window WINDOW_ID`: 指定した 1 時間窓だけを実行。
    - `--finalize`: 全 window artifact を再検証し、summary を create-only 生成。

    P4 に賛成する。実走認可を装う追加 gate は作らず、execute mode の起動自体を人間の認可後の手番として残す。

11. **新規テスト**

    `orchestrator/tests/test_floor_pair_driver.py:1-520` を新設する。具体的な命題は後掲のテスト計画に対応させる。すべて tmp repo、fake probe、fake measure、fake clock を使い、`measure_point`、bench、build、計算ノード投入を起動しない。

    特に `measure_fn` spy の呼出し回数と request 内容を検査し、validation-only、既存 output、pre-probe failure、hash mismatch の各経路でゼロ回であることを固定する。

12. **段 5 の所有 path**

    段 5 は 1 実装子を妥当とする。所有集合は次の 2 path のみ。

    - `orchestrator/campaign/floor_pair_driver.py`
    - `orchestrator/tests/test_floor_pair_driver.py`

    loader、plan、JSONL schema、fake fixture が同時に変わるため、module とテストを素集合の別実装子へ分けると public schema の往復が増える。一方、既存 file は一切所有しないので他 wave との衝突面はない。

    worklog fragment は段 7 の親所有として、`docs/spool/worklog/2026-09-02-worktree-dev-wave-t2166-floor-pair-driver-1.md` を別単位にする。

## 変更 file 一覧

- 新規、段 5 単一所有: `orchestrator/campaign/floor_pair_driver.py`
- 新規、段 5 単一所有: `orchestrator/tests/test_floor_pair_driver.py`
- 新規、段 7 親所有: `docs/spool/worklog/2026-09-02-worktree-dev-wave-t2166-floor-pair-driver-1.md`
- 変更なし: `orchestrator/campaign/between_run_floor.py`
- 変更なし: preregistration 本文、材料レポート consumer、§5 値セル、既存テスト

## テスト計画

- `test_floor_pair_driver.py:25-105`: 最小 valid spec fixture。全 field が明示され、公開 dataclass に default がない。
- `:107-175`: 各必須 field の欠落、未知 field、型違い、bool-as-int、値域外、duplicate JSON key、非有限 JSON を `FloorPairSpecError` にする。
- `:177-225`: expected SHA の形式不正・不一致、checkout 外、symlink、未追跡、HEAD と異なる bytes、参照 artifact hash 不一致を `FloorPairBindingError` にする。hash 検査が JSON parse より先であることも固定する。
- `:227-270`: candidate side が同じ artifact ID の場合だけ受理し、異なる ID、`trace=true`、reference 差替えを拒否する。各実測前に binary hash が再検査される。
- `:272-320`: HMAC plan の golden order、同 seed の同一 plan、seed/spec/window 変更時の plan 変更、全 session ID の一意性、seed と plan SHA の記録を固定する。
- `:322-380`: fake probe と fake measure で pre→measure→post→append 順を検査する。measure 例外でも post-probe と session record が残る。
- `:382-420`: competing、indeterminate、欠測、非有限 throughput、reps 不足のいずれでも残り計画が記録され、retry/補充がなく、upper/candidate floor が null になる。
- `:422-455`: gain と D の公式、共通 reference の使用、raw reps からの median 再計算、`sample_max/v1` と closed-strata max を固定する。
- `:457-475`: upper が `1` 未満なら候補値、ちょうど `1` または超過なら未生成となり、値を切り詰めない。
- `:477-500`: 既存 window/summary path では `FileExistsError`、fake measure は未呼出し。失敗 artifact は削除・改名されず再利用不能。
- `:502-520`: `--validate-only` は output、probe、measure を一切触らず canonical plan だけを返す。finalizer は保存済み derived D でなく raw から再計算する。

親の受入では新規テストに加え、既存回帰、`tools/check_codex_agents.py`、`tools/check_docs.py`、commit 後の provenance 検査が必要になる。本段ではいずれも実走しておらず、緑とは判定していない。

## 却下した設計

- `between_run_floor.measure_point_floor` の流用: 固定 8 session と固定 workload (`between_run_floor.py:76-84`) から単一構成の CV を返す別量であり、D を測れない。
- `s8b_floor_campaign.strict_probe` の直接 import: probe の分類器は有用だが、巨大な S8b campaign 依存を同時に引く。共有 classifier だけを直接使う。
- `p2_2` の `RECORDS`、`THREADS`、`EXTIME`、`REPS` (`p2_2.py:47-57`) の流用: D1060 と「spec だけを根拠にする」条件に反する。
- candidate side ごとに別 path/hash を持たせる案: hash 比較後に片側だけ差し替わる面が増える。単一 artifact を 2 論理 side が共有する方が狭い。
- 成功標本だけで upper を計算する案: 値を小さくする方向の欠測除外が可能になる。1 件の欠測で全体未生成とする。
- spec から arbitrary import path の統計関数を動的 load する案: 純関数性と実装 identity を保証できず、汎用実行基盤になる。
- `random.Random.shuffle` の利用: Python 実装世代への依存を避け、HMAC rank の byte-level plan にする。
- 一時 file、rename、失敗時 unlink による publish: create-only の証拠を後から消せる。最初から最終 path を exclusive-create して追記する。
- driver 内で build する案: build 条件と候補生成まで広げると D1453 の専用 adapter を超える。hash-bound の既成 trace-disabled binary を入力とする。
- 材料レポート接続、preregistration 値セル更新、汎用 floor framework: それぞれ D1437、D1383、D1453 の scope 外。

## 未解決

- 凍結する上限統計の exact function ID は提供資料ではまだユーザー裁定されていない。推奨は、§11.2 が例示する分布自由の標本最大に対応する `sample_max/v1` と、閉じた全 stratum の `max_over_closed_strata/v1` である。
- 親がこの 2 ID を採らない場合、実装子が別の統計式を推測して追加してはならない。先に function ID、引数 schema、実装 identity を人間が凍結し、その exact 1 関数だけを registry に追加する必要がある。