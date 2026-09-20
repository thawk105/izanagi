## 方針と現物確認

scope (1) 同 job pair → (2) 較正動作点 CLI → (3) exact correctness の順に実装する。production の主変更は `tools/pegasus/p3_s4_loop_pegasus.sh` と `orchestrator/campaign/p3_s4_loop.py`。**`pipeline.py` と `loop.py` は既存の接続を使い、変更不要**と判断する。

以下の略記を使う。行番号は今回読んだ現物に基づく。

| 略記 | ファイル |
|---|---|
| L | `orchestrator/campaign/p3_s4_loop.py` |
| J | `tools/pegasus/p3_s4_loop_pegasus.sh` |
| C | `orchestrator/campaign/loop.py` |
| P | `orchestrator/campaign/pipeline.py` |
| I | `orchestrator/campaign/ident.py` |
| S | `orchestrator/campaign/source_digest.py` |
| TJ | `orchestrator/tests/test_p3_s4_loop_job_contract.py` |
| TL | `orchestrator/tests/test_p3_s4_loop.py` |
| TV | `orchestrator/tests/test_pipeline_verify_result_retention.py` |

親のアンカーにはずれがある。現物では `perf = default_perf()` は **L:3044**、候補の `run_campaign` は **L:2012–2021**、`campaign_id` は **I:232–235**。本計画では現物側を採る。

必読の射影資料はすべて読めた。pytest・build・計測・ファイル書込みは実行していない。

## P1〜P6 の判定

| 裁定 | 判定 | 根拠・条件 |
|---|---|---|
| P1 同 campaign | **支持** | I:196–223 の preimage に genome は入らない。ただし K2 manifest、環境、build policy、動作点、verify mode の束縛を候補と一致させる必要がある。L:1611–1618、2988、3037。 |
| P2 applied template の stock | **条件付き** | `BACKOFF_FIXED=-1` の adaptive reference は b10:799–803 に存在する。ただし STOCK はフラグ名から決まらず、current/baseline digest の一致で決まる。S:2307–2335。今回の tree/compiler での実測成立は未確認。 |
| P3 較正 CLI 二口 | **条件付き支持** | 定数・workload を `p2_2` から取り、max_ope を明示すれば成立する。二口の片指定時の扱いを閉じ、identity に workload と extime/reps も束縛する。P:193–223。 |
| P4 verify opt-in と記録 | **支持** | C:153–161、782–792 が既に接続済み。完全な動作点を search_config に記録すれば追加 receipt は不要。 |
| P5 候補後に stock | **条件付き支持** | J:9 は `set -Eeuo pipefail`。現在の末尾へ単純追記すると候補 rc≠0 で stock に到達しない。候補 rc の捕捉と最終 rc 集約が必要。 |
| P6 通常段構成 | **支持、理由修正** | 正しさ・identity・既定互換の二レンズは妥当。ただし「pipeline production を変更するから」は不要になる。段数は親の進行管理であり、本 plan 段では追加の子を起動しない。 |

## (1) driver の stock 評価口

**CLI は `--stock-control` を新設し、候補経路と独立させる。** L:2797–2854 に追加し、L:2855–2864 の既存 `supplied` 集合で明示指定を判定する。`--value` の既定値 20.0 は変更しない。

L:2878 付近、receipt 読込み・manifest 解決・layout 作成より前に次を検査する。

| 組合せ | `ap.error()` の本文 |
|---|---|
| stock + run-iteration | `--stock-control cannot be combined with --run-iteration` |
| stock + 明示 value | `--stock-control cannot be combined with --value` |
| stock + emit-planner-context | `--stock-control cannot be combined with --emit-planner-context` |
| stock + no-build | `--stock-control cannot be combined with --no-build` |
| stock + coder-role | `--stock-control cannot be combined with --coder-role` |
| stock + B4 opt-in | `--stock-control cannot be combined with --b4-reflux-ablation` |

agent ingestion は L:2865–2879 の既存排他で拒否する。agent inputs/prompts、diagnosis、B4 receipt の既存検査も残す。stock に knowledge manifest とその宣言値を渡すことは許す。

**新設 `_run_stock_control_resolved(...)` を使う。** `_run_one_iteration_resolved` に stock 分岐を混ぜない。新関数は cfg、perf、sub、layout、contract、resolved_site、build context、cache/prebuild 引数を受け、planner/coder/state は受け取らない。

L:3050–3055 の worktree context 準備後、L:3058 の proposal 分岐より前に stock 分岐を置く。既存の site admission、build authority、single tenant、pin、knowledge identity の準備を通したうえで新関数を呼ぶ。

新関数内の順序は次に固定する。

| stock の処理 | 候補経路の対応箇所 |
|---|---|
| exact `BuildRunContext` と grammar version の確認 | L:1909–1911 |
| `Genome("silo", {**_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": -1})` | 候補の genome は L:1929–1930 |
| `layout.ensure()` | L:1931 |
| `ident.ensure_resumable_attempts(cfg, layout, admission_policy=build_context.policy)` | L:1933–1935 |
| `with applied(os.path.join(_repo_root(), TEMPLATE_PATCH), PIN, sub):` | L:1969 |
| `_require_condition_gate`、prebuild 時は同じ offline configure 引数 | L:1980–1992 |
| 同じ環境・依存関係 options を組み `run_campaign(cfg, [genome], perf, ...)` | L:1996–2021 |
| context を抜けた後、summary と WAL から結果を報告 | L:2022–2037 |

**stock では attribution、hole 挿入、quarantine、`project_whiteboard`、`drive_iteration` を呼ばない。** L:3137 以降の fixture 用 LoopState 作成にも到達させない。`ensure_resumable_attempts` は identity 照合と interrupted attempt の回復であり（I:511–535）、LoopState 更新ではない。

stock WAL の評価レコードは C:782–792 → P:1910、2130、2571–2575 の既存 writer が発行する。driver/job body に WAL の手書きは足さない。

## (1) terminal skip、digest、STOCK の意味

C:589–610 は terminal から retryable abort を除き、C:695–704 は確定した variant ID を使って skip する。したがって stock が既に COMMIT または非 retryable ABORT なら再評価されるとは限らない。fresh layout なら既存 terminal がなく、この理由の skip は起きない。

**既存 `_resolve_duplicate` をそのまま stock から呼ぶ案は反証する。** L:1846、1858 が whiteboard を更新するため I4 に反する。

代案は L:1794–1864 の terminal 復元を次の二層にする。

- 新設 `_resolve_terminal_result(layout, summary, log=...)`：`summary.skipped_variants`、`_duplicate_snapshot`、`require_persisted_certified_commit`、attempt ID 整合を使って結果を返す。state/planner を受けない。
- 既存 `_resolve_duplicate(...)`：上の結果に従って従来どおり whiteboard を更新する wrapper。候補側の戻り値、分類、ログを維持する。
- stock は前者のみ呼ぶ。`identity_skipped` で確定 ID がない場合、成功や stock ID を捏造しない。

再解決禁止の理由は L:1802–1809 のとおり。`applied` の復元後に source digest を取り直すと、評価時とは異なる ID を参照し得る。

stock CLI は新規 certified または admission 済み既存 certified の復元なら rc=0、aborted・証拠拒否・identity 不明なら rc=1 とする案を推奨する。ただし復元時は **`outcome=duplicate` と明示し、新規の同 job session を取得したとは報告しない**。fresh layout は運用条件として残す。

stock を候補の後に追加すると候補起動時の digest は古くなるため、stock CLI の終了処理で L:3164–3176 と同じ admitted view・projection を使い、`s4_loop_digest.txt` を更新する。checkpoint/whiteboard は更新しない。新しい台帳は作らない。

P2 の根拠と限界は以下である。

- b10 の adaptive stock は `b10_backoff_shape_sweep.py:799–803`。
- 同ファイル:1027–1036 は applied tree で current/baseline digest の一致と STOCK token を実際に検査している。
- 本経路の `resolve_evidence` は S:2431–2447 で allowlist、include、conditional macro を検査し、digest を比較する。
- **STOCK の条件は S:2316–2317 の digest 一致。** `BACKOFF_FIXED=-1` だけでは保証されない。
- 非一致なら grammar version 束縛済み source token となり、P:137–143 の variant ID に `|src=...` が入る。L:1093–1105 の critic projection も `stock` ではなく `candidate-NNNN`／その source label として扱う。

stock と表示するため token を上書きしてはならない。静的読解や digest 入力の stub test は、実 compiler での inert 成立証明にはならない。

## (1) 同 campaign の identity

I:212–223 の preimage は次の五要素である。

`spec_content / ccbench_commit / search_tag / search_config / trial`

`genomes` は C:347 の別引数であり、追加した stock genome を search_config に入れなければ campaign identity は変わらない。`--stock-control` 自体も search_config に入れない。

候補と stock は以下を共有する。

- L:1552–1583 の default cfg と admission policy。
- L:2988 の site/environment 束縛。
- **L:1611–1618 の knowledge level・manifest SHA 束縛。**
- 後述する較正動作点と verify mode。

特に K2 の stock 起動から manifest を省くと、同 campaign にならない。job body は stock に同じ manifest・classification・de novo 宣言を渡す一方、`--coder-role` と proposal path は渡さない。knowledge receipt の既存処理を再利用し、stock を coder proposal として記録しない。

critic identity projection は L:1065–1136 に stock label と stock/source/attempt/admission の対応を既に持つ。別 campaign に分ける必要はない。

## (1) job body の変更

J:17–24 の `required_env` は変更しない。新 env はすべて任意であり、未設定時の既存 argv を保つ。

J:97 の後、repository path 解決より前に以下の任意設定処理を置く。

| env | 既定・転送 |
|---|---|
| `IZANAGI_S4_STOCK_CONTROL` | 未設定または `0` は無効、`1` で候補後の stock 起動。その他・設定済み空値は rc=2 |
| `IZANAGI_S4_CALIBRATED_PERF` | 未設定または `0` は無効、`1` → `--calibrated-perf` |
| `IZANAGI_S4_PERF_WORKLOAD` | 設定時に `--perf-workload VALUE` |
| `IZANAGI_S4_VERIFY_PERFORMANCE` | 未設定または `0` は無効、`1` → `--verify-performance` |

二口の較正設定は対で要求する。workload の choices は driver の argparse を正本とし、shell に workload 表を再定義しない。verify は較正設定を要求する。誤った組合せは事前構築前に拒否する。

`measurement_argv=()` を作り、proposal・fixture・stock の三起動へ同じ配列を渡す。既存 pin を残すため、proposal/fixture の配列展開は **J:584／591 の prebuild 引数より前**に挿入する。これで TJ:418–425 の連続した既存 fragment は残せる。

stock 用 `stock_identity_argv` は J:77–93 と同じ manifest・任意宣言値から作る。`k2_argv` は引き続き proposal 専用とする。

末尾 J:580–593 の実装方針：

1. `candidate_rc=0` を初期化する。
2. 既存 proposal/fixture の各 Python コマンド末尾に `|| candidate_rc=$?` を付ける。
3. stock 無効なら `exit "$candidate_rc"`。driver 起動は従来どおり一回。
4. stock 有効なら、同じ `$PY`、build authority、isolate、prebuild receipt、measurement 引数、stock identity 引数で `--stock-control` を一回呼ぶ。`|| stock_rc=$?` で捕捉する。
5. pair 有効時だけ候補/stock の rc を stdout に出す。
6. 候補 rc≠0 ならその rc、それ以外は stock rc で終了する。

J:9 の strict shell を外さない。候補 Python の失敗を捕捉するだけで、prologue・prebuild の失敗後まで stock を強行するものではない。timeout・job kill による allocation 終了後の stock 実行も保証しない。

J:138–157 の EXIT trap と `compute-result.json` schema は変更しない。`driver_rc` は引き続き job 全体の rc を表す。新規の rc receipt は不要。

## (1) job 契約 pin と親担当 docs 差分

TJ:154–427 の required fragment と TJ:611–780 の mutation matrix に追加する。既存 `proposal`（TJ:654–660）、`fixture`（TJ:682–687）、`k2-request-set-detection`、`k2-proposal-required` は削らない。

新しい各 `id` と mutation 対は次を基本とする。

| id | pin → mutation |
|---|---|
| `stock-default-off` | `${IZANAGI_S4_STOCK_CONTROL-0}` → `${IZANAGI_S4_STOCK_CONTROL-1}` |
| `stock-mode` | stock 呼出し末尾の `--stock-control` → `--value -1` |
| `stock-prebuild` | stock 呼出しの receipt＋stock identity 連続 fragment → receipt 削除 |
| `stock-knowledge-manifest` | `stock_identity_argv` の manifest 転送 → 転送削除 |
| `proposal-status-capture` | proposal 末尾 `|| candidate_rc=$?` → 捕捉削除 |
| `fixture-status-capture` | fixture 末尾 `|| candidate_rc=$?` → 捕捉削除 |
| `stock-status-capture` | stock 末尾 `|| stock_rc=$?` → 捕捉削除 |
| `pair-status-priority` | 候補非零優先の最終分岐 → stock rc だけ返す |
| `measurement-argv-binding` | 三起動の measurement 配列転送 → stock 側だけ削除 |

既存 mutation runner は TJ:785–790 で fragment の一意性と「一つの static failure」を要求する。重複する短い `--fetchcontent-prebuild-receipt` だけを fragment にせず、stock 固有の隣接行まで含める。既存 fragment と重なる新 pin を作って複数 failure にしない。

TJ:550–558 の stage-order 検査へ stock 起動の位置を足し、proposal/fixture 分岐より後と検査する。TJ:1382–1390 の「`k2_argv` は proposal 専用」は維持できる。

親が `tools/pegasus/README.md:359–371`、397–406 に追記する差分案：

- 上記四 env の表、未設定時の一回起動、設定値域・組合せ。
- stock は候補後、同 allocation・pin・toolchain・prebuild receipt を使う。
- stock は proposal を読まず LoopState を進めないが、同 campaign にするため manifest identity を共有する。
- candidate rc≠0 でも stock step を試み、job rc は候補非零を優先する。
- terminal stock は復元され得る。同 job の新規 pair を得るには fresh layout が必要。
- K2 の候補後 stock は、本 wave では B-5 の「初回 planner 前の系列開始 stock」まで実装したことを意味しない。

## (2) 較正動作点 CLI と identity

L:2803 付近に以下を追加する。

- `--calibrated-perf`：`store_true`。
- `--perf-workload {write-heavy,balanced,read-heavy}`：既定 `None`。
- 片指定は `ap.error("--calibrated-perf and --perf-workload must be supplied together")`。

L:1631–1636 の `default_perf()` は一切変更しない。直後に `calibrated_perf(workload_name)` を新設する。

```python
PerfConfig(
    records=p2_2.RECORDS,
    threads=p2_2.THREADS,
    workload={
        **dict(p2_2.WORKLOADS)[workload_name],
        "ycsb_max_ope": S2_FLAGS["ycsb_max_ope"],
    },
    extime=p2_2.EXTIME,
    reps=p2_2.REPS,
)
```

`p2_2.py:54–57` の値は 1M／48／3／5、同:74–77 の workload は rr5／50／95、skew `"0.9"`、rmw `"0"`。値の再定義はしない。

max_ope の `"10"` は **P:159–162 の `S2_FLAGS`** を出所とする。P:1697–1702 の qualification shape にも同値があるが、この qualification policy を流用するわけではない。CCBench の既定値に依存する設計にもせず、四 key を明示する。

確定する workload は次の exact dict：

```text
ycsb_rratio      = "5" | "50" | "95"
ycsb_zipf_skew   = "0.9"
ycsb_rmw         = "0"
ycsb_max_ope     = "10"
```

これで P:208–214 の四 key exact を満たす。workload 名を perf.workload に混ぜない。

**cfg の差替えは L:2988 の直前に置く。** `default_cfg()` の後、emit 分岐・knowledge receipt・campaign ID 計算より前に perf を決め、較正 opt-in 時だけ以下を `replace` で焼く。

```python
search_config={
    **cfg.search_config,
    "records": perf.records,
    "threads": perf.threads,
    "workload": dict(perf.workload),
    "extime": perf.extime,
    "reps": perf.reps,
}
```

workload 名を別 key に入れる必要はない。実効四 key が識別子となる。extime/reps も記録し、後述の correctness 引数・回数を復元可能にする。

L:3044 の無条件代入は削除し、ここで確定した perf を使う。指定なしの場合は `default_perf()` を使い、search_config には**一つも key を追加しない**。stock flag も identity に焼かない。

既定 identity の確認は、同じ環境・policy・manifest 条件で変更前の canonical preimage の bytes を test fixture として固定し、変更後の `ident.canonical_preimage(cfg).encode("utf-8")` と exact 比較する。変更後の `default_cfg()` 同士を比べるだけの自己参照テストにはしない。既存 fixture/proposal の captured argv と cfg/perf も従来値のまま検査する。

## (3) exact correctness と記録

`--verify-performance` を追加する。較正 opt-in がなければ次で拒否する案を推奨する。

`--verify-performance requires --calibrated-perf and --perf-workload`

理由は既定 `default_perf()` が max_ope を持たず、extime=1 であり（L:1634–1636）、そのまま P:193–223 に渡せないためである。既定 perf を暗黙に補正して identity を曖昧にする案は採らない。

較正 cfg の構築と同じ位置で、opt-in 時だけ次を追加する。

```python
search_config[SEARCH_CONFIG_VERIFY_KEY] = VERIFY_LEGACY_PLUS_PERFORMANCE
```

接続は既に成立している。

1. C:515 → C:153–161 が verify mode を読む。
2. P:193–223 が perf から exact correctness を作る。
3. C:782–792 が `evaluate(extra_correctness=...)` に渡す。
4. P:1719–1722 が **legacy を先頭に残して** performance pass を追加する。
5. P:2180–2188 は各 repetition の失敗で即 return。
6. P:2434–2440 は全 pass 通過後だけ certified にする。
7. P:2551–2575 は `verify_configs` を含む COMMIT を既存 writer から出す。

Pegasus では L:2014 の `list(contract.numactl)` と L:2016 の `authorize(contract.env_tag)` が同じ契約に由来する。P:1723–1737 は list を tuple にして exact 比較し、空 prefix の Pegasus も許す。新 stock 関数でもこの渡し方を維持し、固定 `NUMA` を使わない。

**correctness は legacy 1 回＋performance 5 回になる。** P:222 が `perf.reps` を引き継ぎ、P:2185 がその回数実行する。trace extime は較正 perf により各回 3 秒。これを一回へ減らす変更は本計画に含めない。

記録先は **campaign.lock の identity preimage** とする。

- verify mode、records、threads、四 key workload、extime、reps を上記 search_config に束縛する。
- I:583–602 がその preimage を campaign.lock に格納する。
- P:215–223 から correctness の flags と reps を決定論的に復元できる。
- WAL は workload tag、attempt、COMMIT の verify_configs を既存形式で残す。

P:945–961 は remote verify payload の `workload == {"tag": tag}` を exact 検査する。そこへ flags は追加しない。これは「実行予定の引数を identity で束縛する」記録であり、OS に渡した argv を独立に観測した receipt と同義ではない。今回の結線・記録要求には前者で足り、create-only receipt と pipeline schema の拡張は不要と判断する。

## テスト計画

ここでは計画のみ。author 段でも real build を行うテストは追加しない。既存の build/source/admission fixture を使い、production の driver・loop・pipeline を通す層を分ける。

**TL：stock と CLI。** 挿入先は condition-gate tests（TL:90 付近）、CLI tests（TL:6506、7144 付近）、duplicate tests（TL:7970–8244）、prebuild tests（TL:8375–8985）。

| 新 test 名 | production 呼出しと assert |
|---|---|
| `test_stock_control_reaches_campaign_under_applied_template` | 新 stock 関数を実呼出し。applied 内で gate→run_campaign の順、stock genome、同 cfg/perf、契約/prebuild 引数を捕捉。 |
| `test_stock_control_does_not_touch_loop_state` | `main --stock-control` を呼ぶ。既存 checkpoint bytes 不変、不在時は未作成。load/save/project/drive/quarantine/proposal loader は呼ぶと失敗する spy。 |
| `test_stock_control_cli_rejects_conflicting_modes` | main の上記排他を parametrize。rc=2、error 本文、layout/receipt 読込み以前の拒否。 |
| `test_fixture_value_minus_one_remains_rejected` | `main --value -1` を既存 CLI fixture で実呼出し。従来の値域拒否、run_campaign 未到達。TL:1898–1918 も維持。 |
| `test_stock_terminal_restore_has_no_whiteboard_projection` | 新 terminal helper と stock 経路を呼び、certified/abort/証拠拒否/ID 不明を検査。再 source resolve は禁止。 |
| `test_stock_terminal_skip_and_fresh_layout` | 実 `C.run_campaign` を使う。TL:8921–8985 型の terminal fixture では evaluate 0 回、fresh layout では一回。 |
| `test_stock_and_candidate_share_manifest_campaign_identity` | 両 main 経路で cfg を捕捉。同 manifest・契約なら canonical preimage と layout が同じ、genome は異なる。 |
| `test_stock_digest_refresh_includes_both_variants` | admitted test view と実 projection/digest を使い、stock 追加後の digest と checkpoint 不変を確認。 |

**TL：較正・verify。**

| 新 test 名 | production 呼出しと assert |
|---|---|
| `test_calibrated_perf_uses_p2_constants_and_exact_workload` | `calibrated_perf` を三 workload で呼ぶ。p2 定数、四 key、rratio、max_ope を検査。 |
| `test_calibrated_cli_binds_effective_perf_before_layout` | main の emit/proposal/fixture/stock で cfg/perf を捕捉。records/threads/workload/extime/reps が一致し、emit と評価の identity が一致。 |
| `test_default_cli_preserves_preimage_bytes` | 変更前の明示 fixture と canonical preimage bytes を比較。新 key の不在も確認。 |
| `test_perf_cli_rejects_partial_and_invalid_options` | 二口の片指定、未知 workload、verify 単独を main で拒否。 |
| `test_verify_opt_in_reaches_real_loop_evaluate_options` | 実 `C.run_campaign` を呼び evaluate の境界を捕捉。extra に PERFORMANCE_TAG と exact flags/reps、既定は None。TL:8742–8789 を型として使う。 |
| `test_stock_token_and_projection_follow_digest_equality` | 実 `S._resolved_src_token`、`P.variant_id`、critic projection を使用。一致なら STOCK、非一致なら別 ID・candidate label。実 compiler inert の証明とは区別。 |

**TV：正しさの回帰。** TV:35–44 の local evaluation fixture を拡張し、production `pipeline.evaluate` に実 `performance_correctness_workload(perf)` を渡す。build/trace 実行は既存の模擬境界、verifier は小さい fixture trace を使う。

- `test_performance_verify_keeps_legacy_and_all_repetitions`：legacy 1 回→performance 5 回、exact flags、COMMIT の `verify_configs == ["legacy", "performance"]`。
- `test_performance_anomaly_aborts_before_bench_and_commit`：legacy pass 後、performance の最初の赤 trace で即 abort。後続 rep・bench・COMMIT はなし。typed VerifyResult の保持は TV:56–78 と同じく検査する。
- `test_performance_verify_requires_exact_contract_numactl`：Pegasus の空 prefix は通る。異なる非空 prefix は build/verify 前に拒否。

**TJ：実 shell。** TJ:1153–1324 の helper は現在最後の argv を上書き保存するため、一回起動の証明にならない。stub driver を argv 履歴の append 記録へ変え、任意の候補/stock rc を返せるようにする。実 job body を通し、scheduler/build/driver の外部処理だけ模擬する。

- `test_default_job_invokes_driver_once`：env 不在の fixture/proposal/K2 各経路で履歴長=1、従来 argv exact。
- `test_pair_job_runs_candidate_then_stock`：履歴長=2、順序、同 receipt/measurement/manifest、stock に value/proposal/coder-role がない。
- `test_pair_job_runs_stock_after_candidate_failure`：rc 対 `(7,0)/(0,9)/(7,9)` で二回実行と最終 rc `7/9/7`、compute-result の rc。
- `test_pair_job_forwards_calibrated_and_verify_options`：両起動に同じ引数。
- `test_invalid_pair_environment_refuses_before_prebuild`：不正 bool、空値、較正片指定を拒否。

既存期待値の変更は、TJ helper の履歴化に伴う TJ:1327–1380 の参照方法と、新 stage-order の期待だけを基本とする。既存 argv の内容は変えない。terminal helper 抽出により TL:8057 の「resolver を持たない」構造検査は wrapper と抽出先の両方を見るよう更新する。既存 duplicate の戻り値・whiteboard 期待は変更しない。

## 段4用の変異候補

1. stock genome の `BACKOFF_FIXED=-1` を `1` に変える → genome 捕捉 test。
2. stock の `BACK_OFF=1` を `0` に変える → adaptive stock exact test。
3. stock から `project_whiteboard`／checkpoint 保存を呼ぶ → LoopState 不変 test。
4. stock+run-iteration の排他を外す → CLI 負例。
5. fixture の値域を拡張して `--value -1` を通す → 従来拒否 test。
6. stock 起動から knowledge manifest を落とす → 同 campaign identity test。
7. terminal 復元時に source token を再解決する → resolver 禁止／skip ID test。
8. 較正 perf の records/threads を search_config に反映しない → effective perf 束縛 test。
9. 指定なしでも workload/verify key を追加する → preimage bytes test。
10. performance opt-in で legacy を除去する、または赤でも継続する → pass 順序／anomaly 即停止 test。
11. stock env の既定を on にする → driver 一回起動 test。
12. 候補 rc 捕捉を外す、または最後を stock rc だけで上書きする → 候補失敗後の二回起動／rc 集約 test。

## 不確定点 Q1〜Q4

根拠はそれぞれ C:589–704、P:222・2185、L:1634–1636、S:2316–2322。

- **Q1：terminal stock は既存どおり復元し、同 job 新規測定の成立は fresh layout 運用で担保する方針でよいか？** 推奨はこれ。強制再測定は duplicate 意味論を変更するため別 scope。
- **Q2：exact correctness は既存 helper に従い、legacy 1 回＋performance 5 回で実装してよいか？** 推奨はこれ。一回へ減らすなら、helper の接続だけでは済まない設計変更として扱う。
- **Q3：較正二口は同時指定必須、verify-performance は較正設定必須としてよいか？** 推奨はこれ。較正 flag 単独時に balanced を補う案もあるが、暗黙の workload 選択を増やす。
- **Q4：P2 の実 inert 成立は、今回は静的根拠と模擬境界 test まで、実 compiler の STOCK 確認は land 後の認可済み pair wave で行う区切りでよいか？** 推奨はこれ。非 STOCK を STOCK に読み替えず、成立しなければ同 wave の結果を対照成立と認定しない。

## 総括

変更予定と概算は以下。author はコード・テストだけを編集し、commit しない。

| ファイル | 概算 |
|---|---:|
| `orchestrator/campaign/p3_s4_loop.py` | 追加・変更 180〜260 行。stock 口、terminal 復元の分離、perf/verify CLI・identity |
| `tools/pegasus/p3_s4_loop_pegasus.sh` | 追加・変更 70〜110 行。任意 env、stock 起動、rc 集約 |
| `orchestrator/tests/test_p3_s4_loop.py` | 追加・変更 280〜420 行 |
| `orchestrator/tests/test_p3_s4_loop_job_contract.py` | 追加・変更 180〜280 行 |
| `orchestrator/tests/test_pipeline_verify_result_retention.py` | 追加 80〜140 行 |
| `tools/pegasus/README.md` | 親担当で約25〜40行 |
| `pipeline.py`、`loop.py`、`ident.py`、`source_digest.py`、`p2_2.py` | **変更なし** |

P 判定は **P1 支持、P2 条件付き、P3 条件付き支持、P4 支持、P5 条件付き支持、P6 支持（pipeline 変更を理由から外す）**。

親の確認事項は **Q1 terminal 復元と fresh layout、Q2 correctness 5 reps、Q3 CLI の組合せ、Q4 実 inert 確認の段階分離**。既定経路の bytes 不変、stock の LoopState 非更新、legacy を残す correctness 拒否を受入の中心とする。