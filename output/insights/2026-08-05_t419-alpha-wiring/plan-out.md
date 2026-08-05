# 段 2 プラン案 — [T-419/T-528] 方式 α の本番結線

必須資料 2 件は読了した。以下は read-only の静的計画であり、コード編集・pytest・実機 probe は実施していない。したがってテストの緑は主張しない。

## 編集範囲

実装面は原則として次の 2 ファイルに閉じる。

- [env_attestation.py:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:27)
- [test_env_attestation.py:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/tests/test_env_attestation.py:36)

`schema_v2.py`、`execution_guard.py`、受理述語、凍結較正、`env_contract.py` は変更しない。

## 1. `env_attestation.py` の分割

### 定数と方式 identity

[env_attestation.py:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:27) の既存 probe 定数群の直後に置く。

- `EFFECTIVE_CLOCK_ALPHA_K = 5`
- `EFFECTIVE_CLOCK_ALPHA_RULE_ID = "sysfs-affinity-intersection-evenly-spaced-v1"`
- `EFFECTIVE_CLOCK_METHOD = f"proc-cpuinfo-rotating-min/k{EFFECTIVE_CLOCK_ALPHA_K}/{EFFECTIVE_CLOCK_ALPHA_RULE_ID}"`

具体的な出力値は次とする。

```text
proc-cpuinfo-rotating-min/k5/sysfs-affinity-intersection-evenly-spaced-v1
```

`PROBE_METHOD="strict-sysfs-procfs"` と `PROBE_VERSION="1"` は外側の receipt 方式なので据え置く。今回変更する identity は比較対象でもある `effective_clock.method` である。

K と規則 ID から method を組み立て、独立な文字列 literal にしない。選択関数も `EFFECTIVE_CLOCK_ALPHA_RULE_ID` の既知値だけを受理し、未知の規則 ID は `AttestationError` にする。さらに既知入力に対する選択結果をテストで固定する。これにより、

- K の変更 → method が自動変化
- 規則 ID の変更 → method が自動変化
- 実装だけ変えて ID を据え置く → 既知ベクトルテストが失敗

という三層で identity drift を検出する。

### 注入 seam

[ProbeRoots:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:54) は filesystem root 専用のまま維持する。behavior を混ぜない。

[HardwareProbe:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:50) 付近に、次の OS 境界を持つ `CpuinfoSamplingRuntime` Protocol と Linux 実装を置く。

- `get_affinity() -> set[int]`
- `set_affinity(cpus: set[int]) -> None`
- `current_processor(proc_root: Path) -> int`
- `read_cpuinfo(path: Path) -> tuple[dict[str, object], dict[int, float]]`

`probe()` は次のように keyword-only 引数を追加する。

```text
probe(roots=DEFAULT_PROBE_ROOTS, *, cpuinfo_runtime=DEFAULT_CPUINFO_RUNTIME)
```

これは既存の no-argument caller と `probe_hardware = probe` を壊さない。テストは fake runtime を引数で渡し、`ea.os.sched_*` の monkeypatch を廃止する。集約済み結果を返す高位 sampler の注入にはしない。高位注入では α の巡回・K 回読み・復元自体をテストが迂回できるためである。

### 単読み parser は維持する

[_parse_cpuinfo():211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:211) の返却型と責務は変えない。

- 1 snapshot 内の全 logical CPU の identity 一致
- processor ID の重複拒否
- CPU ID → MHz の構築

を引き続き担当する。戻り値を dataclass に変えないため、非認証 probe の parser crosscheck [t419_probe_causality.py:3633](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/tools/pegasus/probes/t419_probe_causality.py:3633) も壊さない。

その直後に本番用の小さい helper を追加する。

1. `_select_evenly_spaced_cpu_ids(cpus, count, rule_id)`

   `select_evenly_spaced()` [t419_probe_causality.py:239](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/tools/pegasus/probes/t419_probe_causality.py:239) のロジックだけを移す。sorted unique CPU 列に対し、両端を含む  
   `round(i * (n - 1) / (K - 1))` を用いる。実験 module は import しない。

2. `_current_processor(proc_root)`

   `/proc/self/stat` の末尾 `)` より後を解析し、processor field を返す。実験 probe の `_self_processor()` [t419_probe_causality.py:1768](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/tools/pegasus/probes/t419_probe_causality.py:1768) から必要な parsing だけを移す。

3. `_reduce_cpuinfo_reads(reads, expected_cpu_ids)`

   正確に K 個の `(identity, mhz_by_cpu)` を受ける純関数とする。各 read について、

   - `set(mhz_by_cpu) == expected_cpu_ids`
   - identity dict が第 1 read と完全一致
   - CPU 集合が非空

   を検査する。identity は raw name を含む全 5 field を比較し、normalized name だけの一致では受理しない。全条件成立後だけ、CPU ID ごとの `min()` を返す。

4. `_collect_rotating_cpuinfo(path, proc_root, expected_cpu_ids, runtime)`

   affinity の取得、K target の決定、pin、K 回読み、復元を所有する唯一の helper とする。戻り値は identity、CPU ごとの最小値、元 affinity の要素数に限定し、生 K ベクトルは schema へ出さない。

### `probe()` の置換

現行 [probe():404–455](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:404) を次の順に組み替える。

1. `_cpu_directories()` から sysfs CPU 集合を確定。
2. `_collect_rotating_cpuinfo()` を呼ぶ。
3. 返却 CPU 集合が sysfs 集合と一致することを呼出側でも再確認。
4. topology、governor、TSC、visibility を現状どおり取得。
5. `samples_mhz` は CPU ID 昇順の論理 CPU ごとの最小値。
6. [method literal:449](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:449) を `EFFECTIVE_CLOCK_METHOD` に置換。
7. `cores.affinity_visible` は巡回前に保存した元 affinity の要素数を使う。

[_recorded_verdict():709](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:709)、[execution_guard.py:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/execution_guard.py:183)、許容値 2.0 は編集しない。判定は引き続き全 observed position が帯内かであり、β・γの性質は入れない。

## 2. 退化時の fail-closed

Python の `assert` は最適化で消えるため、正しさ条件には使わない。すべて明示的な `if ...: raise AttestationError(...)` と制御構造で固定する。

| 退化 | 拒否点 | 例外 |
|---|---|---|
| `len(sysfs_cpu_ids ∩ original_affinity) < 5` | target 選択前。pin も cpuinfo read も行わない | `AttestationError` |
| `sched_getaffinity` 不在・拒否・空集合 | 元 affinity 取得時 | `AttributeError` / `OSError` を cause にした `AttestationError` |
| `sched_setaffinity({target})` 拒否 | 各 read の直前 | `OSError` / `AttributeError` を cause にした `AttestationError` |
| singleton affinity が反映されない | set 後の affinity 再取得で `{target}` と exact 不一致 | `AttestationError` |
| 実走行 CPU が target と異なる | cpuinfo read の直前と直後の両方 | read index と target を含む `AttestationError` |
| cpuinfo の一部が不可読・parse 不正 | K loop 内。skip/continue しない | read index を付けた `AttestationError` |
| read 間で CPU 集合が増減 | 各 read と sysfs CPU 集合の比較 | `AttestationError` |
| read 間で identity が変化 | `_reduce_cpuinfo_reads()` | `AttestationError` |
| K 未達 | reducer の `len(reads) != 5` | `AttestationError` |
| affinity 復元失敗・復元後不一致 | `finally` 内 | `AttestationError`。取得側の例外は chained context に残す |

単読み fallback を防ぐ構造は次のとおり。

- 戻り値を生成できるのは `_reduce_cpuinfo_reads()` の K exact gate 通過後だけ。
- `except AttestationError: _parse_cpuinfo(path)` のような回復分岐を置かない。
- read 失敗を `continue` しない。
- K target はすべて distinct でなければ拒否。
- `samples_mhz` を作る入口をこの helper の戻り値 1 本にする。

## 3. affinity の復元

`original_affinity = runtime.get_affinity()` を mutation 前に immutable copy として保存する。最初の singleton set から K 回取得の終了までを一つの `try/finally` で囲む。

`finally` では必ず次を行う。

1. `set_affinity(original_affinity)`
2. `get_affinity()` を再取得
3. exact に元集合へ戻っていることを検査

取得成功後も、任意 read の例外後も、pin 不一致後も同じ `finally` を通す。復元に失敗した場合は profile を返さず拒否する。「復元を試みた」だけを成功扱いにはしない。

## 4. fixture と正規 seam

既存 [_probe_tree():36–64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/tests/test_env_attestation.py:36) は CPU 2 個なので、そのままでは K=5 の成功 fixture にならない。

次のように変更する。

- `_probe_tree(tmp_path, *, cpu_ids=range(5))` として CPU 集合を引数化。
- 既存成功・governor・visibility テストは既定の 5 CPU を使用し、cores、NUMA、samples の期待値も exact に 5 CPU へ更新。
- CPU 2 個は削除せず、`cpu_ids=range(2)` を K 未満の拒否専用 fixture として利用。
- [_patch_runtime_probe():67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/tests/test_env_attestation.py:67) の `ea.os.sched_getaffinity` monkeypatch を fake `CpuinfoSamplingRuntime` へ置換。
- TSC の既存 monkeypatch は α の OS pin seam と独立なので維持してよい。

期待値を「旧 method または新 method」のように緩めず、新 method を exact assert する。

## 5. 純増する検出力

追加先は [test_env_attestation.py:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/tests/test_env_attestation.py:80) 付近の probe テスト群とする。

| test 関数名 | assert する性質 |
|---|---|
| `test_alpha_method_identity_and_target_selection_are_versioned` | K=5、method の完全一致、候補 `range(9)` から target が `[0,2,4,6,8]`。K/rule drift を検出 |
| `test_probe_alpha_rotating_min_accepts_migrating_reader_outlier` | K 回すべてを読み、各 read の reader だけが帯外でも最小値は全 CPU 帯内。method/sample verdict が pass。成功後 affinity が元へ復元 |
| `test_probe_alpha_rotating_min_keeps_persistent_outlier_rejected` | reader と無関係な CPU 1 個を全 K read で帯外にし、最小値にも残ることと `effective_clock.samples_mhz` の fail を確認 |
| `test_probe_alpha_rejects_fewer_than_k_affinity_without_read` | 2 CPU fixture で `AttestationError`、read/set call が 0 |
| `test_probe_alpha_rejects_setaffinity_error_without_fallback` | singleton set の `OSError` が `AttestationError` になり、cpuinfo を 1 回も fallback read しない |
| `test_probe_alpha_rejects_wrong_reader_cpu_before_and_after_read` | pre/post のどちらの processor 不一致も拒否し、元 affinity を復元 |
| `test_probe_alpha_rejects_partial_k_read_and_restores_affinity` | 3 read 目を失敗させ、4・5 read を行わず拒否。元 affinity 復元 |
| `test_probe_alpha_rejects_cpu_set_drift_between_reads` | 2 read 目で CPU を 1 個欠落・追加すると拒否 |
| `test_probe_alpha_rejects_identity_drift_between_reads` | 2 read 目の vendor/model/raw name のいずれかを変えると拒否 |
| `test_probe_alpha_restore_failure_is_fatal` | K read が成功しても restore が失敗すれば profile を返さない |

### reader CPU が帯外になる fixture

9 CPU の scripted runtime を使う。

- 元 affinity: `{0,1,2,3,4,5,6,7,8}`
- 選択 target: `[0,2,4,6,8]`
- 各 read の vector:

```text
mhz[cpu] = 3000.0  if cpu == current_pin_target
           2101.0  otherwise
```

各単読みは必ず 1 要素が 2% 帯外なので、旧単読み・固定 reader・K=1 では通らない。一方、CPU ごとの K 回最小値は全要素 2101.0 になる。テストでは、

- 各 raw vector 単独なら拒否されること
- K=5 の集約結果だけが通ること
- set target の順序と read 数
- method の exact 値
- 最終 affinity

を同時に固定する。

真の逸脱側は、選択 target ではない CPU 1 を全 K read で 3000.0 にする。これにより「reader 汚染だけを吸収し、持続的な帯外は残す」を単一理由で確認できる。

### 事前登録すべき変異

既存 330 test には依存せず、少なくとも次を新テストで kill する。

- method だけ旧 `"proc-cpuinfo"` に戻す
- K を 1 または 4 にする
- pin target を固定する
- target 選択を先頭 K 個へ変える
- `min` を first / last / max に変える
- setaffinity 失敗時に単読みする
- reader CPU 検査を削る
- read 失敗を skip する
- CPU 集合または identity 比較を削る
- `finally` の復元を削る
- 持続的帯外を除外・1 個許容する

## 6. caller と遅延・拒否の波及

親実測の 1 read 約 20 ms を前提にすると、1 probe の cpuinfo 部分は約 100 ms、純増は約 80 ms。ただし今回は静的評価のみであり、この時間を再実測したとは主張しない。

### 直接 caller

| 入口 | 経路と影響 |
|---|---|
| [t126_driver.py:442](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/qualification/t126_driver.py:442) | 最大 8 pre-round + post-series、aggregate cap は 600 秒。約 0.72 秒の純増見込みで cap 破壊の静的兆候はない。ただし同 driver は現在 `verified.calibration` を profile として渡す既知の意図的 fail-closed 状態で、[test_t126_qualification_driver.py:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/tests/test_t126_qualification_driver.py:54) が拒否を固定している。本 wave で修正しない |
| [execution_guard.py:319–357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/execution_guard.py:319) | `AttestationError` は `strict attestation probe failed` の `ExecutionGuardError` へ変換。method 不一致は comparisons failed として receipt 発行前に拒否 |
| [s8b_floor_campaign.py:2767–2785](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/s8b_floor_campaign.py:2767) | 起動時 1 回。`ExecutionGuardError` を `FloorCampaignError` へ変換し、campaign 本体前に停止 |
| [calibrator/cli.py:344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/calibrator/cli.py:344) | static-pre、dynamic-pre、static-post の 3 probe、計 15 cpuinfo read。α の取得失敗は `attempt-fatal: AttestationError`、rc=1、publish なし。旧登録較正との比較はこの入口ではしない |
| [run_probe.py:37–72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/tools/pegasus/run_probe.py:37) | α 失敗は `stage="probe"`、`type="AttestationError"`、rc=3 の structured failure。単体では登録済み較正と比較しない |

### transitive caller

- [campaign/loop.py:86–97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/loop.py:86): 最初の書込み前に `ExecutionGuardError`。
- [s8b_oracle_driver.py:790](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/s8b_oracle_driver.py:790): 起動時は `OracleDriverError("execution attestation 失敗")`。
- [s8b_oracle_driver.py:934](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/s8b_oracle_driver.py:934): schedule 行ごとの再検査は `OracleDriverError("途中 execution guard 失敗")`。行数×約 80 ms の増加はあるが、bench/reservation の秒単位 budget を静的には破らない。
- [silo_ladder_rung1.py:1945](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/silo_ladder_rung1.py:1945): `run_probe.py` の timeout は 120 秒。method は [1984–1987](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/silo_ladder_rung1.py:1984) で独立 exact 比較され、`InfraFailure("attestation")` になる。
- `certify_calibration.sh` の static/pre/post probe は各 120 秒 timeout で、100 ms 級への増加だけを理由に timeout の変更は不要。
- `smoke_probe.sh` は structured rc をそのまま overall rc に反映する。

新たに拒否される環境は、usable affinity 5 未満、affinity syscall 不可、pin 不発、CPU hotplug/identity drift、部分読取り失敗を持つ環境である。これは意図した α の fail-closed であり、単読みへの救済は設けない。

## 7. 登録済み較正との確定的不一致

現登録 artifact は [calibration JSON:1440–1493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1440) で、

```text
effective_clock.method = "proc-cpuinfo"
```

を持つ。

新 live probe は新 method を返す。method は [_common_comparison_values():679](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:679) に含まれ、[_recorded_verdict():749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:749) の exact equality に落ちる。したがって samples の成否に関係なく `effective_clock.method` が必ず fail する。

経路は次のとおり。

```text
probe()
  → compare_profiles()
  → effective_clock.method = fail
  → execution_guard.attest_and_build_receipt()
  → ExecutionGuardError
  → FloorCampaignError / OracleDriverError / loop の起動拒否
```

silo ladder は共有 comparator とは別に method を exact 比較して同様に拒否する。`run_probe.py` と calibrator の取得自体は比較をしないため、新 method を記録して成功し得るが、再取得・publish・登録・pin 更新の実行は本 wave の scope 外である。

## 8. 親 brief (P1)–(P5) への評価

| 項目 | 評価 |
|---|---|
| P1 K=5 固定 | 賛成。CLI 引数や環境変数にせず production 定数 1 個に固定する |
| P2 schema key 不変、method のみ | **条件付き賛成。** 本 wave の編集結果として key 不変を採る。ただし「method だけで K 回取得を証明できる」とは扱わない |
| P3 sysfs CPU ∩ affinity から等間隔 K 点 | 賛成。元 affinity を 1 回 snapshot し、その集合から決定する |
| P4 `/proc/self/stat` で pin 実効性検査 | 賛成。各 read の直前・直後の両方を検査する |
| P5 sampler seam | 賛成。ただし集約結果を差し替える seam ではなく、OS/read 境界の keyword-only runtime seam とする |

### P2 と「K 回保持 schema」の利害

生 K ベクトルを保持する利点は、各 read と `min()` の再計算、CPU 集合 drift、外れ値の診断を後から監査できる点である。ただし raw MHz ベクトルだけでは reader が本当に target CPU 上にいたことを証明できず、pin target と pre/post processor まで schema に入れなければならない。これは実験 probe の診断 schema を本番へ持ち込む方向になる。

さらに schema 追加は次へ波及する。

- [EffectiveClockProfile:219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/calibrator/schema_v2.py:219) と observed 型 [243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/calibrator/schema_v2.py:243)
- `_CLOCK_KEYS` の exact 集合 [schema_v2.py:552](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/calibrator/schema_v2.py:552)
- calibration parser [schema_v2.py:598](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/calibrator/schema_v2.py:598)
- expected/observed exact parser [env_attestation.py:501–535](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:501)
- probe-output v1/v2 exact parser [env_attestation.py:581](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:581)
- profile hash と observed projection [env_attestation.py:616–648](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:616)
- artifact 全体の digest・登録 filename [calibrator/cli.py:633–655](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/calibrator/cli.py:633)
- 現較正 bytes の sha pin [env_contract.py:265–271](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_contract.py:265)

`_CLOCK_KEYS` に必須 key を足すと、現登録 artifact は method 比較へ到達する前に schema 不正で読めなくなる。optional key にすると exact schema を弱める。正しく行うなら probe-output と calibration の versioned schema、hash projection、凍結 bytes、contract pin を同時に扱う必要があり、本 wave の制約に反する。

したがって本 wave では、

- K 個の snapshot は取得中だけメモリに保持
- outward schema は CPU ごとの最小値と method のみ
- raw K 証拠を保持しないことを明示的な証拠上の損失として受容
- method を名乗るだけの退化は新規テストと変異で検出

を推奨する。

これは裁定パッケージの「schema (K 回保持)」を実装したという意味ではない。将来 raw 証拠が必須と裁定された場合は、別の versioned-schema wave として扱うべきである。

## 実装順

1. `env_attestation.py` に定数、runtime seam、選択・processor・reducer・collector helper を追加。
2. `probe()` を collector 1 本へ結線し、旧単読みと別途の `sched_getaffinity` を除去。
3. 5 CPU 化した既存 fixture の期待値を exact に更新。
4. reader-outlier 正例、persistent-outlier 負例、全 fail-closed・復元テストを純増。
5. 親が計算ノードで新規テスト、既存 clock/freeze 系、全 caller 関連テストを実測し、変異 matrix を確認する。現時点では未実走。

## 総括

推奨案: schema を変えず、K=5・決定的 affinity 巡回・位置ごとの最小値を専用 helper に閉じ、方式 identity と正規 runtime seam を追加する。

最大の危険: raw K 証拠を残さないため、method が実手続きの証明ではない。単読み・pin 不発・復元欠落を直接撃つ純増テストと変異が必須である。

親 brief への反対点: P2 の編集結果には賛成するが、「方式 identity を method だけに載せれば証拠も十分」という読みには反対する。裁定パッケージの schema 保持要求は未充足として明記すべきである。