## 経路の実アンカー

親 brief の表は大筋で正しいです。ただし、後述する二点を明示的に補正します。

| driver | production 入口から関門まで | source / stock root | request と admission |
|---|---|---|---|
| `backoff_sweep` | [`main()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/orchestrator/campaign/backoff_sweep.py:435) から `run_workload()` を呼ぶのが CLI 入口。`run_workload()` は line 326-358 で single-tenant、site、calibration、genome、toolchain、build policy を確定し、line 359 で `buildcache._ccbench_dir()` を取得する。line 363 で stock checkout、line 364 で共有 source tree に patch、line 365 で source root を canonicalize、line 366-377 で FetchContent を準備し、line 378-392 で `_require_backoff_condition_gate()` を呼ぶ。 | source は patch 済み `external/ccbench` の resolve 済みパス。stock は `patchharness.checkout()` の一時 worktree。configure 引数は line 389-391 の `-DFETCHCONTENT_BASE_DIR=<canonical_base>`。 | helper は line 117 で `BACKOFF_FIXED == -1` を認識し、line 118-126 で `stock_comparison=True`、`default_value=None` の request を作る。line 127-155 が両腕、line 156-169 が `raw-measurement` admission と拒否例外。 |
| `backoff_repro` | [`main()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/orchestrator/campaign/backoff_repro.py:225) → `run_workload()` line 148-166 → `_conditioned_backoff_patch()` line 63-84。line 66 で `buildcache._ccbench_dir()`、line 70 で stock checkout、line 71 で共有 source tree に patch、line 72-83 で共通 helper を呼ぶ。 | source は patch 済みだが resolve していない `buildcache._ccbench_dir()` の文字列。stock は一時 worktree。configure 引数なし。use class は `raw-measurement`。 | `_genomes_reversed()` line 87-94 は必ず `BACKOFF_FIXED=-1` 点を末尾へ入れる。共通 helper のため request は `stock_comparison=True`、`default_value=None`。 |
| `s1_direct_comparison` | [`run_role()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/orchestrator/campaign/s1_direct_comparison.py:988) line 1147-1151 から `prepare_cell()` を呼ぶ。`prepare_cell()` line 785-815 が cell/flags を検証し、line 818-828 で source と必要時の stock worktree を作る。line 829-915 の configuration 固有 patch、quarantine、oracle 前処理を終え、line 916-921 で `_condition_records_for_genome()` に入る。関門本体は line 266-308。 | source は `patchharness.checkout()` が作る使い捨て `sub`。stock も別の使い捨て checkout。configure 引数なし。実 role では develop が `raw`、それ以外が `certified-selection`（line 1005、1147-1151）。 | request は line 194-210。`BACKOFF_FIXED=-1` では `stock_comparison=True` だが、sweep/repro と違って `default_value=-1` も保持する。meaning 宣言は line 229-246、両腕と admission は line 275-307。 |

共通 helper の正確な実体は [`backoff_sweep.py:88-169`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/orchestrator/campaign/backoff_sweep.py:88) です。

親 brief への補正は次の二点です。

- s1 の stock checkout 条件は「flags 全体が既定値と一致」ではありません。line 821-828 の条件は、対象となる condition macro のうち少なくとも一つが `BACKOFF_FIXED=-1`、または `_CONDITION_DEFAULTS` と一致することです。
- repro の row は root の記述自体は正しいものの、重要な前提が省略されています。`CCBENCH_COMMIT="dff0f1e"`（line 46-48）であり、`patchharness.checkout()` は stock worktree を作るだけで共有 source tree の HEAD を動かしません。共有 `external/ccbench` 自身が事前に `dff0f1e` でなければ、line 71 の `applied()` が関門前に拒否します。

関門側の実アンカーは以下です。

- [`capture_define_inputs()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/orchestrator/campaign/condition_meaning_gate.py:792) line 792-831
- 実 CMake argv の構築と実行: line 1614-1685
- requested/control の二つの configure: line 1794-1892、特に line 1839-1848
- stock inert supply 判定: line 2488-2655
- `BACKOFF_FIXED=-1` の stock adaptive branch meaning: line 2697-2811、3272-3424
- family admission: line 4012-4074
- record/admission の canonical JSON: line 640-691

## 起動設計と production 経路である根拠

(P1) と (P2) を採ります。ただし、親の (P3)「別ノードへ同時投入」は採りません。三つの独立 PBS job を `afterany` で直列化し、前 job が赤でも後続を必ず走らせます。

### `backoff_sweep`

`run_workload()` を省略せず、次の production 呼び出しを行います。

```python
backoff_sweep.run_workload(
    "write-heavy",
    dict(backoff_sweep.WORKLOADS[0][1]),
    screening_enabled=True,
    screening_fixed_us=2,
    confirm_each_candidate=False,
)
```

これは line 326-392 の全前処理を通ります。すなわち single-tenant、site/runtime、calibration、2 genome 選択、campaign config、compiler/toolchain manifest、build admission、共有 source root、stock root、patch、canonicalization、Masstree FetchContent 準備、関門の順です。省く production 前処理はありません。関門通過後も最小 screening を完走させるため、関門直後で sentinel を投げるような短絡は入れません。

### `backoff_repro`

最初の production workload である `write-heavy` の入力を使います。

```python
backoff_repro._assert_single_tenant()
point = backoff_repro.ORIG["write-heavy"]
genomes = backoff_repro._genomes_reversed(point["best_us"])
_, cxx = backoff_repro.buildcache.compilers_for_current_site()

with backoff_repro._conditioned_backoff_patch(genomes, cxx=cxx):
    pass
```

これにより production 関数自身が次を実行します。

1. `buildcache._ccbench_dir()` による source root 束縛。
2. historical pin からの stock checkout。
3. production patch path の適用。
4. production driver ID、genome 値列、compiler、`raw-measurement` を使った共通 helper 呼び出し。
5. 成否にかかわらない patch revert と clean 検査。

`run_workload()` の line 152-164 にある config、build context、environment binding、capability resolver、`PerfConfig` は後段の `run_campaign()` 専用で、`_conditioned_backoff_patch()` の引数や source/stock root を変えません。関門入力へ流れる `genomes` と `cxx`、および安全前提の single-tenant 検査は省きません。

### `s1_direct_comparison`

`floor` role の verified freeze から、schedule 上で最初に現れる `variant.flags["BACKOFF_FIXED"] == -1` の cell を選びます。

```python
document = s1.load_verified_freeze()
s1._operating_point(document)
s1._workload_flags(document)
schedule = s1.schedule_for_role(document, "floor")
item = next(
    row for row in schedule
    if row.cell["variant"]["flags"].get("BACKOFF_FIXED") == -1
)
s1._assert_single_tenant()
_, cxx = s1.buildcache.compilers_for_current_site()

with s1.prepare_cell(
    item.cell,
    document["ccbench_pin"],
    cxx=cxx,
    condition_use_class="certified-selection",
):
    pass
```

これは手製の cell ではなく、署名・schema を検証済みの production freeze 入力です。`prepare_cell()` 内では、flags 正規化、source checkout、stock checkout、configuration 固有の patch/quarantine/oracle をすべて実行してから関門へ入ります。したがって関門へ渡される source tree を模擬しません。

`run_role()` の environment authorization、campaign layout、WAL/session ledger、budget ledger、perf preflight は `prepare_cell()` の `cell`、pin、`cxx`、`condition_use_class` に流れません。これらを省くことで既存 campaign と ledger を保護します。先行 schedule cell も各回が別の使い捨て worktreeであり、対象 cell の関門入力を変更しないため省略できます。

`--dry-run` は line 1019-1023 で `prepare_cell()` より前に返るため不採用です。

### root 隔離

各 PBS job は、`PBS_O_WORKDIR` の exact HEAD から `/scr/$PBS_JOBID/...` に node-local repo clone を作り、さらに `external/ccbench` をローカル共有 cloneします。

- sweep clone の `external/ccbench` は `backoff_sweep.CCBENCH_COMMIT`。
- repro clone は `dff0f1e`。
- s1 cloneは freeze pin の objectを含む clean repository。

probe はこの clone 内の production module を importします。`buildcache._ccbench_dir()` や `ROOT/external/ccbench` は一切 monkeypatch しません。したがって絶対パスは node-local になりますが、root を決める production 束縛そのものと source bytes、pin、patch 順序は同一です。

## probe 設計 (file:line 粒度)

追加する一組は次です。

- `tools/pegasus/probes/t2228_driver_gate_liveness_probe.py`
- `tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs`

予定行は実装時のレビューアンカーとして固定します。

### `t2228_driver_gate_liveness_probe.py`

- line 1-32: shebang、schema `izanagi-t2228-driver-gate-liveness/v1`、repo root の import path、driver choices、期待 driver ID。
- line 33-61: create-only JSON writer。既存 [`run_probe.py:22-26`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/run_probe.py:22) と同じ `open("x")` とし、既存結果を上書きしない。
- line 62-118: `_GateObserver`。`sys.setprofile()` の `return` event を使い、次の production 関数の実 return object だけを観測する。
  - `make_define_request`
  - `evaluate_define_supply_effectuation`
  - `evaluate_define_runtime_meaning`
  - `require_condition_gate_family`
  
  function binding、引数、戻り値は変更しない。対象 `__code__` と exact dataclass 型を照合し、driver ID が対象 driver と一致する record だけを保持する。mock、stub、synthetic record は使わない。
- line 119-157: canonical serializer。各 arm recordについて次を出す。
  - `macro`
  - `arm`
  - `terminal_status`
  - `reason_code`
  - `request_digest`
  - `record_id`
  - `canonical_json`
  - `document = json.loads(record.canonical_json())`
  
  Admission も `canonical_json` と decode 済み document を保持する。request については `requested_value`、`default_value`、`stock_comparison` も記録し、実際に `BACKOFF_FIXED=-1` の stock request が発行されたことを確認する。
- line 158-196: 共通 result builder。初期値は必ず `ok=False`。以下をすべて満たした場合だけ `ok=True`、`rc=0` とする。
  1. production 呼び出しが例外なく戻った。
  2. `BACKOFF_FIXED=-1`、`stock_comparison is True` の実 request がある。
  3. その request digest に supply と meaning の各一 record がある。
  4. 両方の `terminal_status` が `green`。
  5. 両 record ID を参照する admission が存在して `admitted is True`。
- line 197-222: 例外の直列化。`type`、`message`、`getattr(exc, "reason_code", None)`、cause/context chain を加工せず保存する。共通 helper が投げる `RuntimeError` や s1 の `DriverError` には reason code 属性がないため、その場合は `null` とする。reason code を message から推測しない。赤 arm の reason code は canonical record 側にそのまま残る。
- line 223-246: sweep runner。前節の `run_workload()` を一回だけ呼び、返った `CampaignSummary.campaign_id` も記録する。
- line 247-268: repro runner。`write-heavy` の production genome 列と production compiler を使い、context を一回だけ enterする。
- line 269-307: s1 runner。verified freeze、`floor` schedule、最初の inert cell、`certified-selection` を使う。対象 cell ID、configuration、freeze pin を JSON に記録する。
- line 308-347: CLI `--driver`、`--output`、`--scratch-output-root`。importsを含む全 driver 実行を `try/except/finally` に入れ、例外時も JSON を書く。例外があるのに `ok=True` となる分岐は設けない。retry、引数緩和、別 rootへの fallbackは設けない。
- line 348-365: stdoutにも一行 JSON を出し、payload 内の `rc` と同じ値で終了する。write失敗は専用非ゼロ rc とし、driver成功へ変換しない。

想定 record 数は以下です。

- sweep: `BACKOFF_FIXED=(-1, 2)` なので 4 arm records、1 admission。
- repro: `write-heavy` は `(10, 5, -1)` なので 6 arm records、1 admission。
- s1: 選ばれた production cell 内の全 condition macroについて `2 × macro数`。`BACKOFF_FIXED` の2 recordsを必須とするが、他 macroのrecordsも省かない。

### `t2228_driver_gate_liveness_probe.pbs`

既存 [`t2187_adaptive_const_probe.pbs`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:1) の作法を踏襲します。

- line 1-8: `gen_S`、1 node、`elapstim_req=02:00:00`、driver別 job name。
- line 9-43: `set -Eeuo pipefail`、`umask 077`、`PBS_JOBID` / `PBS_O_WORKDIR` 検証、`bnode` compute-only 検査。
- line 44-68: `IZANAGI_T2228_DRIVER` を三択で検証。attempt ID と output directory を安全な文字集合、canonical absolute path、専用 namespaceで検証する。
- line 69-94: exact outer HEAD と tracked-clean 検査。probe/PBS/policy が regular fileかつ非 symlink であることを確認する。
- line 95-117: create-only `/scr/${PBS_JOBID//:/_}-t2228-driver-gate` を `TMPDIR` にし、EXIT trap でその exact directoryだけを除去する。
- line 118-143: `PYTHONPATH` 等を unsetし、Python 3.10 以上を `-I -S -B` で選ぶ。
- line 144-205: T-2187 PBS line 246-341 と同じ pinned gflags/glog prologueを node-localに構築し、`CMAKE_PREFIX_PATH` と既存 third-party cacheを設定する。
- line 206-247: exact HEAD の node-local repo cloneと、元 `external/ccbench` からの network-free `git clone --shared --no-checkout`。driverごとの必要 pinを checkoutし、HEAD、tracked/untracked clean、必要 commit objectを確認する。
- line 248-267: node-local cloneへ `cd` し、campaign/output rootを `$TMPDIR` 配下へ束縛する。永続させる唯一の書き込み先は専用 evidence directoryのdriver JSON。
- line 268-284: probeを一回だけ起動し、その rcをPBS job rcとして返す。`exec`してよい。JSON payloadにも同じ rcが入る。

三 job は次の順で投入します。

1. `s1_direct_comparison`
2. `backoff_repro`
3. `backoff_sweep`

後続 dependency は `afterany` とします。したがって前 job が rc 非ゼロでも後続は走ります。三本の同時投入はしません。

書き込み先と保護方法は以下です。

| 書き込み候補 | 対処 |
|---|---|
| sweep/repro の patch 対象 | driver別 node-local `external/ccbench` のみ。共有 wave treeには適用しない。 |
| `patchharness.checkout()` の Git worktree metadata | node-local ccbench cloneの `.git` 内のみ。 |
| gate の requested/stock CMake build、dependency file、meaning source/binary | `TMPDIR` 配下。context終了またはPBS trapで削除。 |
| sweep の FetchContent base | `TemporaryDirectory` かつ node-local。 |
| sweep の screening campaign、WAL、build cache | node-local repo/output root配下。job終了時に削除。 |
| s1 session ledger / budget ledger | `run_role()` を呼ばないので作らない。 |
| s1 build cache | `prepare_cell()` だけで `pipeline.evaluate()` を呼ばない。 |
| 凍結成果物 | 読み取りだけ。 |
| 最終 evidence | 専用 attempt directoryへdriver別 JSONをcreate-onlyで保存。 |

## backoff_sweep の最小起動

production CLIとしての具体 argv は次です。

```bash
python3 -B -u orchestrator/campaign/backoff_sweep.py \
  write-heavy \
  --screening \
  --screening-fixed-us 2
```

`2` は `SWEEP_US` の既存点です（[`backoff_sweep.py:60`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/orchestrator/campaign/backoff_sweep.py:60)）。line 329-339 により、実走 genome は次の2点だけになります。

1. baseline: `BACK_OFF=0, BACKOFF_FIXED=-1`
2. candidate: `BACK_OFF=1, BACKOFF_FIXED=2`

したがって inert request と非 inert 対照 requestの両方を通しつつ、全8点 sweepを避けられます。

campaign identityが既存 sweepと別になる根拠は `config_for()` line 205-225 です。

- 通常 sweep の `search_config` は line 208-210。
- `screening_fixed_us is not None` の場合だけ line 213-214 で `"screening_fixed_us": 2` が追加される。
- line 211-212 のコメントも、このキーを positive-control等の最小 screening campaign専用とし、省略時だけ既存 campaign-idを不変にすると明記している。

加えて実測 plan では campaign出力先自体を node-local scratchへ隔離するため、仮に identity計算に想定外があっても既存 campaignのWALやlockには到達しません。JSONには返却された実 campaign IDを保存します。

## 事前予測

これは静的予測であり、実測値ではありません。

| driver | 予測 | 根拠 |
|---|---|---|
| `backoff_sweep` | 関門は緑 | production経路が line 370-377 で Masstree FetchContentを事前準備し、line 389-391 でそのcanonical baseを関門の両 CMake configureへ渡す。inert supplyは `stock-inert-preprocess-identical` または `stock-inert-preprocess-root-location-only`、meaningは `declared-meaning-observed`、admissionは `admitted=true` と予測する。 |
| `backoff_repro` | 赤の可能性が最も高い | historical pinを正しく準備した後でも、configure argsとFetchContent準備がない。supply腕のrequested/control configureが一時build rootごとに依存取得を試み、`configure-failed` または `configure-timeout` になると予測する。meaning腕はCMakeを使わないため、inert requestについては緑になる可能性が高い。familyはsupply赤により拒否。 |
| `s1_direct_comparison` | 赤の可能性が最も高い | reproと同じくFetchContent baseを渡さない。さらにcell固有materializationが期待したCMake supplyを持たない場合は、取得成功後に `macro-not-supplied` や `stock-inert-mismatch` が出る可能性もある。inert meaning自体は緑、familyはsupply赤で拒否と予測する。 |

重要な実装上の訂正として、`capture_define_inputs()` 自体は configure を実行しません。line 792-831 で行うのは以下だけです。

- configure args の型と重複検査。
- source/stock root のresolveとdirectory identity取得。
- `configure_args` のtuple化と保存。

実 configure は supply evaluatorが `_configured_define_compile_commands()` に入り、line 1839-1848 で requested/controlの二回を実行するときです。argvは line 1653-1661 で構築されます。

- sweepでは両 argv に `-DFETCHCONTENT_BASE_DIR=<prepared base>` が入る。
- repro/s1では `captured.configure_args` が空なので入らない。
- その結果、requested build rootとstock/default build rootがそれぞれ独自のFetchContent状態を持ち、事前配置された共通Masstree sourceを参照できない。networkが必要になれば、禁止、遅延、120秒 timeoutの影響を直接受ける。
- `_run_process()` line 1544-1572 は非ゼロrcだけでなく、成功rcでもstderrがあれば `configure-failed` にする。FetchContent/CMake warningも赤要因になる。

一方、`BACKOFF_FIXED=-1` のmeaningは line 3371-3376 から `_assert_backoff_fixed_branch_meaning()` に入り、patch済み `include/backoff.hh` の条件枝を単独preprocessします。FetchContentやCMake configureには依存しません。

## 落とし穴と対処

- **historical pinの不一致:** reproは `dff0f1e` を要求します。現在の共有submoduleが `511c953` のままなら、`applied()` の `assert_pinned_clean()` が関門前に停止します。node-local cloneを明示的に `dff0f1e` へ置き、HEADとclean状態を確認してから起動します。自動 fallbackはしません。

- **隔離 outer worktreeでもsource treeは自動隔離されない:** sweep/reproの `patchharness.checkout()` はstock用worktreeだけを作ります。続く `applied(..., ccbench_dir)` は固定の `external/ccbench` を直接変更します。[`patchharness.py:247-263`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/orchestrator/campaign/patchharness.py:247) の通り、applyとrevertの対象は `ccbench_dir` 自身です。outer repoがGit worktreeであることだけでは安全になりません。

- **別ノード間のlockは共有されない:** `_lock_path()` line 113-117 はlockを `$TMPDIR` に置きます。PBSで`TMPDIR=/scr/...`なら別ノードのlock fileは別物です。同じ共有 source treeを二 jobがpatchしても相互排他になりません。このため親の(P3)は不採用です。

- **同一treeでsweepとreproはpinも両立しない:** sweepはcurrent pin、reproは`dff0f1e`を `applied()` 前提にします。共有treeを順にcheckoutする方式は、checkout自体が`applied()`のlock外であり、並行waveと競合します。driver別node-local cloneで回避します。

- **submodule未初期化またはobject不足:** original `external/ccbench` がGit repositoryであり、current pin、`dff0f1e`、freeze pinのobjectを持つことを投入前にread-onlyで確認します。不足時はnetwork fetchせずpreflight赤で止めます。

- **untracked残骸:** `patchharness.assert_pinned_clean()` は通常untrackedを無視します。probeのnode-local sourceは開始時に `--untracked-files=all` も空であることを確認し、終了時はclone全体を廃棄します。

- **network:** repro/s1に `FETCHCONTENT_BASE_DIR` を追加したり、失敗後だけcacheを注入したりしません。それはproduction入力を変え、赤を緑にするためです。network起因の `configure-failed` / `configure-timeout` も測定結果です。

- **temporary storage:** CMake build tree、Git worktree、decoder、FetchContent、campaign outputはすべてjob固有 `/scr` 配下に置きます。十分なinode/容量を事前確認し、既存pathがあれば再利用せず停止します。

- **walltime:** 関門の各 subprocess timeoutは120秒です。sweepにはさらにMasstree準備の900秒上限が二箇所あり、その後に最小screeningがあります。PBSは2時間を確保し、短い外部timeoutで強制終了してJSONを失う設計にはしません。

- **single tenant:** 三 jobは同時実行せず、各 driverでproductionのsingle-tenant検査を実行します。失敗時はそのdriverを赤にし、再投入や検査の無効化はしません。後続jobは`afterany`で走ります。

- **sweep calibration:** `resolve_site_runtime()` と `_assert_matches_calibration()` をstubしません。必要な既存calibrationが読めなければ関門前失敗として記録し、別 calibrationへのfallbackは行いません。

- **例外前にrecordが存在しない場合:** pin不一致、root capture失敗、入力contract違反など、arm record発行前の例外ではrecords/admissionを捏造しません。JSONは空配列または`null`とexact exceptionを持ち、rc非ゼロになります。

- **post-gate失敗:** sweep screeningやs1の関門後 `source_digest.resolve()` が失敗した場合、取得済みrecord/admissionは保存しますが、例外があるためdriver全体の `ok` はfalse、rcは非ゼロにします。関門が緑だった事実とproduction呼び出し全体の失敗を別フィールドで読めるようにします。

## 総括

採る設計は、sweepだけを最小2点の `run_workload()` で実走し、reproは `_conditioned_backoff_patch()`、s1はverified freezeの最初のinert cellを `prepare_cell()` へ渡すものです。record採取はpass-through wrapperではなく `sys.setprofile()` による非介入観測とし、production evaluatorが発行したexact objectだけをcanonical JSON化します。

事前予測は「sweep緑、repro赤、s1赤」です。後二者の主因予測は、空の `configure_args` によりrequested/controlの実CMake configureが共通の準備済みFetchContent baseを使えないことです。実測が異なれば、予測を修正せず、実recordとadmissionをそのまま結果とします。

この段では射影資料の静的読解だけを行いました。ファイル編集、commit、push、テスト、計算ノード実測は行っていません。