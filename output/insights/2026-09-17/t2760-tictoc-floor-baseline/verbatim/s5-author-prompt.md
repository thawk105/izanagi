単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2760-tictoc-floor-baseline

必読事項の射影 (読めなければ即停止):
- /home/SFC/tanab/.claude/jobs/1adff7e0/tmp/wave/parent-brief.md — 親 brief (scope・根拠・不変条件) と段 4 裁定 (変異事前登録 M0〜M7)。**この文書が最優先**。
- /home/SFC/tanab/.claude/jobs/1adff7e0/tmp/wave/D2114-excerpt.md — D2114 (項 4 が本 T の起票元)。
- /home/SFC/tanab/.claude/jobs/1adff7e0/tmp/wave/D2083-excerpt.md — D2083 (項 4〜6: 現行 pin での関門の挙動と再開の必要条件)。
- /home/SFC/tanab/.claude/jobs/1adff7e0/tmp/wave/D1373.md — D1373 (関門は許可リストでなく source 事実へ束縛。緩めない)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2760-tictoc-floor-baseline/orchestrator/campaign/between_run_floor.py — 変更対象。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2760-tictoc-floor-baseline/orchestrator/tests/test_between_run_floor.py — 変更対象 (test)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2760-tictoc-floor-baseline/orchestrator/campaign/genome.py — `TICTOC_SPACE` / `space_for` / `_tictoc_no_wait_not_both` (読むだけ)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2760-tictoc-floor-baseline/external/ccbench/cmake/Options.cmake — cache 既定の正本 (読むだけ、submodule は編集不可)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2760-tictoc-floor-baseline/external/ccbench/cc/tictoc/CMakeLists.txt — tictoc の OPTIONS 供給 (読むだけ)。

## 依頼

[T-2760] を実装せよ。**編集してよい file は次の 2 つだけ** (所有 path):

- `orchestrator/campaign/between_run_floor.py`
- `orchestrator/tests/test_between_run_floor.py`

docs・他 file・submodule (`external/ccbench/`) は編集しない。commit しない。git の状態変更 (add / stash / checkout / reset) をしない。

### 現行の受理・拒否挙動 (scope 前の事実)

- `BASELINES` (L60-73) は `silo` / `mocc` の 2 鍵。`_parse_cli_args` (L259-289) は `--protocol` の値が `BASELINES` に無ければ `ValueError("unknown protocol: ...")`、`main()` はそれを rc=2 + usage にする。現状 `--protocol tictoc` はここで拒否される。
- `main()` (L292-) は引数解析後、`_protocol_source_has_trace_hook_evidence_only(protocol)` が偽なら `ValueError("protocol ... の現行 CCBench source に trace hook の証拠がない")` を上げ、`_assert_single_tenant`・build・measure・`_write_out` のいずれも呼ばない (D1373 の関門)。現行 pin 511c9538 では silo=True、mocc=False、**tictoc=False** (`cc/tictoc/` に `izanagi_trace` は 0 件)。
- `_write_out` (L196-) の stem は silo が `between_run_noise_t48_…`、それ以外が `between_run_noise_<protocol>_t48_…`。
- **変えないもの:** silo / mocc の entry bytes、`_protocol_source_has_trace_hook_evidence_only` の bytes、`_write_out` の stem 規則、`_parse_cli_args` の規則、既存 test の期待値。新しい gate・validator・schema・env・argv を足さない。tictoc の floor 生成は現行 pin では引き続き関門で build 前に拒否される (受理集合不変)。

### 実装 (parent-brief.md の scope 表に従う)

1. `BASELINES` の `mocc` entry の直後に次を追加する (flag の並びは canonical 順 = アルファベット順に揃える):

   ```python
       # tictoc: 準備登録 (D2114 項 4、T-2760)。値は現行 pin の external/ccbench/cmake/Options.cmake
       # の cache 既定 (BACK_OFF, NO_WAIT_LOCKING_IN_VALIDATION, NO_WAIT_OF_TICTOC, PREEMPTIVE_ABORTS,
       # TIMESTAMP_HISTORY) で、mocc と同じく CMake 既定を stock とする。TICTOC_SPACE の点 (no-wait は
       # (1,0)、D1418) で、accepted な tictoc 認定較正 record (rr50 / rr95、D2083) の genome と同一。
       # 現行 pin には trace hook が無く、下の D1373 関門が build 前に拒否する (実測の開通は別件)。
       "tictoc": Genome("tictoc", {
           "BACK_OFF": 1,
           "NO_WAIT_LOCKING_IN_VALIDATION": 1,
           "NO_WAIT_OF_TICTOC": 0,
           "PREEMPTIVE_ABORTS": 1,
           "TIMESTAMP_HISTORY": 1,
       }),
   ```

   L59 の header comment・silo / mocc entry・`BASELINE = BASELINES["silo"]` は 1 byte も変えない。module docstring も変えない。

2. 他の実装変更は不要。`_parse_cli_args` は `BASELINES` を参照しているので tictoc は自動的に受理される。

### test (`orchestrator/tests/test_between_run_floor.py`)

この file は **pytest 無しの素の runner** (`_run()`、末尾) でも走る形式である: test 関数は引数を取らない、`pytest.mark.parametrize` / fixture (`tmp_path`、`monkeypatch`) を使わない、module 属性の差し替えは既存 test と同じく `originals` dict に退避して `finally` で復元する、一時 dir は `tempfile.TemporaryDirectory()`。新規 test 名は `test_t2760_` で始める。

- 既存 `test_trace_hook_admission_is_bound_to_source_facts` (L251-253) に `assert not between_run_floor._protocol_source_has_trace_hook_evidence_only("tictoc")` を 1 行追加する (既存 2 assert は変えない)。
- (1) `test_t2760_baselines_are_points_of_their_registered_genome_space`: `from orchestrator.campaign.genome import space_for` を使い、`between_run_floor.BASELINES` の全 entry について `space_for(protocol).enumerate()` に含まれる (`in`) こと、かつ entry の `protocol` 属性が鍵と一致することを assert。鍵集合が `{"silo", "mocc", "tictoc"}` であることも assert。
- (2) `test_t2760_tictoc_baseline_matches_ccbench_cmake_cache_defaults_at_pin`: `between_run_floor.CCBENCH_ROOT / "cmake" / "Options.cmake"` を読み、`BASELINES["tictoc"].flags` の各 axis について `re.search(rf"^\s*set\(CCBENCH_{axis}\s+(\d+)\s+CACHE\b", text, re.MULTILINE)` で既定値を取り、`int(...) == flags[axis]` を assert する (5 axis すべて hit することも assert)。silo は歴史的 stock (BACK_OFF=0) なので対象にしない。これは根拠 (CMake 既定) を現行 checkout の source 事実へ束縛する test であり、gate ではない。
- (3) `test_t2760_parse_cli_args_accepts_tictoc_and_rejects_unregistered_protocol`: `_parse_cli_args(["prog", "--protocol", "tictoc"]) == (None, "tictoc")`、`_parse_cli_args(["prog", "read-heavy", "--protocol=tictoc"]) == ("read-heavy", "tictoc")`、`_parse_cli_args(["prog", "--protocol", "cicada"])` が `ValueError` で message に `unknown protocol` と `'cicada'` を含む (cicada は genome 空間にはあるが baseline が無い = 負例)。
- (4) `test_t2760_protocol_output_stem_names_tictoc_without_colliding`: 既存 `test_protocol_output_stem_preserves_silo_and_names_mocc` (L166) と同形で、同一 tmp dir に silo・mocc・tictoc の 3 つを `_write_out` し、tictoc の json 名が `between_run_noise_tictoc_t48_skew0p9_rr95_rmw0.json`、3 つの名前が相異なる (create-only の衝突が起きない) こと、tictoc の md に `BASELINES["tictoc"].canonical()` の文字列が含まれることを assert。`res["genome"]` には `BASELINES["tictoc"].canonical()` を渡す。
- (5) `test_t2760_tictoc_floor_rejected_before_build_or_measure_without_trace_hook`: 既存 `test_mocc_floor_rejected_before_build_or_measure_without_trace_hook` (L440-483) と同形。`CCBENCH_ROOT` は差し替えず**現行 pin の実 source** に対して `main(["prog", "read-heavy", "--protocol", "tictoc"])` を呼び、`ValueError` の message に `trace hook` と `'tictoc'` を含むこと、`calls == []` (tenant / build / measure / write のいずれも呼ばれない) を assert。
- (6) `test_t2760_hook_bearing_source_routes_tictoc_baseline_through_main`: 既存 `test_hook_bearing_source_routes_mocc_baseline_through_main` (L486-552) と同形で `cc/tictoc/` の fixture source (hook 入り) を作り、`main([... "--protocol", "tictoc"]) == 0`、`calls == {"build": [BASELINES["tictoc"]], "measure": [BASELINES["tictoc"]], "write": ["tictoc"]}` を assert。

既存 test の assertion を弱めない・削らない。fixture に現行 hash を差し込んで緑にしない。期待値に揮発 payload を焼き込まない。

### 検査と報告

- 実走: cwd は worktree root。`python3 -m pytest orchestrator/tests/test_between_run_floor.py -q -p no:cacheprovider` と `python3 orchestrator/tests/test_between_run_floor.py` (素の runner) の両方を走らせ、緑には実走 nodeid・件数を併記する。sandbox 由来で走らない/赤になる node は「実装済み・未実走」または「sandbox 由来の疑い」と分類し、`closed` と申告しない。
- 制約 meta-test を自ら洗い出す: `orchestrator/tests/` で `test_between_run_floor` / `BASELINES` / `between_run_floor` を grep し、test 名・件数・source 文字列を pin する test があれば走らせて報告する。
- 完了報告に、所有外 caller (`BASELINES` / `BASELINE` / `_parse_cli_args` の他 file 参照)、consumer test (`test_screening_driver.py`、`test_layer3_report.py`、`test_s8b_floor_campaign.py`、`test_pegasus_floor_scoping.py`、`test_floor_pair_driver.py`) への波及可能性を静的に列挙する。
- 完了報告に、変異事前登録 M0〜M7 (parent-brief.md の段 4 裁定) の各位置を実装後の行番号と置換前文字列 (old) で対応づける (anchor 表)。各 M の期待 killer test 名 (実装後の nodeid) も書く。

予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式

Markdown。先頭に `## 総括` (10 行以内: 変更 hunk 数、新規 test 数、実走結果 (passed/failed/未実走)、scope 逸脱の有無)。続けて `## 変更一覧` (file:line)、`## 実走`、`## 変異 anchor 表`、`## 波及可能性`、`## 未実走・懸念`。
