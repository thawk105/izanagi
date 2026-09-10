dev-wave の段 2 規約に従った静的プランです。必読 3 点は読めています。書き込み・pytest・実 build は行っていません。

結論は、A の最終 publish 集合を v2 `{binary_relpath, completion.json}`、legacy `{binary, admission.json}` に固定し、B は既存の単一 registry を型付きで拡張する構成です。T-841 の receipt 束縛には踏み込みません。

## A — build 出力 copy-out

### consumer 棚卸しと allowlist

最終 cache directory の production consumer は次に閉じています。

| consumer | 現行 file:line | 読むもの |
|---|---|---|
| v2 manifest validator | `orchestrator/campaign/buildcache.py:415-482` | `completion.json` と manifest が指す binary |
| legacy sidecar validator | `orchestrator/campaign/buildcache.py:390-412` | `admission.json` |
| v2 cache hit | `orchestrator/campaign/buildcache.py:743-768` | 上記 validator の結果、binary |
| legacy cache hit | `orchestrator/campaign/buildcache.py:920-941` | sidecar、binary |
| stale cache 回収 | `orchestrator/campaign/buildcache.py:943-945,1060-1087` | binary の有無だけ。CMake tree の再利用はしない |
| 再現コマンド生成 | `orchestrator/campaign/buildcache.py:543-584,909-918` | `-B bdir` を文字列として BuildResult に記録するだけ |
| fresh build | `orchestrator/campaign/buildcache.py:780-806,945-962` | 常に別 staging を `-B` に使う |
| source/trace gate | `orchestrator/campaign/buildcache.py:816-832,969-987,1008-1057` | bdir/staging は失敗時の破棄先。CMakeCache/object は読まない |
| campaign pipeline | `orchestrator/campaign/pipeline.py:883-911,932,1042-1046,1092,1193` | binary path と full SHA |
| calibration/profile | `orchestrator/campaign/s1_verify_extime_calibration.py:358-371`, `backoff_profile.py:148-160`, `backoff_overthrottle.py:83-92` | binary |
| correctness controls | `orchestrator/campaign/s2_verify_calibration.py:300-331`, `s3_lock_coverage.py:199-204`, `s5_permutation_coverage.py:191-200` | binary |
| floor | `orchestrator/campaign/between_run_floor.py:163-177`, `pegasus_floor_scoping.py:212-233` | binary |
| S8b | `orchestrator/campaign/s8b_floor_campaign.py:1210-1252` | binary path、SHA、再現 argv |

`BuildResult.build_dir` は production では内容を再利用しておらず、定義・返却点は `orchestrator/campaign/buildcache.py:165-190,567-584,998-1005`、実際の directory 内容を検査するのはテストだけです。

したがって正確な契約は次です。

- untrusted staging から読む allowlist は binary の exact relative path 1 本だけ。
- 最終 publish 集合は v2 `{binary_relpath, completion.json}`、legacy `{binary, admission.json}`。
- `completion.json` / `admission.json` は staging からコピーせず、現行 `orchestrator/campaign/buildcache.py:833-848,979-985` の host-generated body を clean directory に新規作成する。
- CMakeCache、object、Makefile、偽の completion/admission、その他 byproduct は最終 cache に出さない。

これにより親 P2 のファイル集合は十分ですが、「metadata も untrusted staging から copy」という解釈は過剰です。

### `orchestrator/campaign/buildcache.py`

#### `:14-24,318-387` — secure copy helper

現行 path-based `_fsync_file` / JSON reader-writer の近傍に、次の内部 helper を置きます。

- `stat` を import。
- relative path は absolute、空 component、`.`、`..`、NUL、separator 混入を拒否。
- staging root を以下で開く。

```python
os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
```

- 各中間 component は、root の held dir-fd から

```python
os.stat(name, dir_fd=fd, follow_symlinks=False)
os.open(name, os.O_RDONLY | os.O_DIRECTORY |
              os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
os.fstat(child_fd)
```

と進み、pre-stat と fstat の device/inode/type が一致することを要求する。

- leaf は FIFO 等で block しないよう

```python
os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC
```

で `dir_fd` 相対 open し、`os.fstat()` + `stat.S_ISREG()` を要求する。
- allowlisted source binary の `st_nlink != 1` は拒否する。hard link が staging 外 inode への beneath-only 迂回になり得るためで、全 link が staging 内にあることを安全に証明できない。
- copy 前後で source fd の device/inode/size/mtime_ns/ctime_ns/nlink と leaf の no-follow stat を再照合する。
- clean 側の component は `os.mkdir(..., 0o700, dir_fd=...)` と no-follow open で作る。
- destination binary は

```python
os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
```

で作り、copy 後に `os.fchmod(fd, 0o700)`。source の suid/sgid/sticky・group/other mode は引き継がない。metadata は exact `0o600`。
- destination の `st_nlink == 1` も要求する。
- Python 3.10 で利用可能な `dir_fd`、`follow_symlinks=False`、`pass_fds` の範囲に限定し、`openat2` 等は使わない。

#### `:353-482` — cache hit の no-follow 化

publish 後の旧 entry が symlink bypass として残らないよう、manifest、sidecar、binary の cache-hit read も同じ dir-fd helperへ寄せます。

- `_read_completion_manifest` / `_read_legacy_admission_sidecar` は held fd から bytes を読み、read 前後の fstat 不変性を確認する。
- `_validate_v2_entry` は bdir を final-component no-follow で開き、`completion.json` と `binary_relpath` をその fd の beneath-only で読む。
- legacy は `os.path.exists(binary)` を symlink-following hit 判定に使わず、broken leaf symlink も拒否対象にする。
- `_clear_stale_build_dir` は bdir symlink・非 directory を削除対象として追わず `BuildCacheError` にする。削除後確認は `os.path.lexists` にする。

fd は BuildResult へ持ち出さないため、return 後に同一 UID の別 process が path を差し替える残余は閉じません。host-security boundary の主張対象外です。

#### `:770-862` — v2 clean publish

現行 `.staging-<pid>-<nonce>` は CMake 専用の untrusted tree のまま残し、同じ `parent` 内に `.publish-<pid>-<nonce>` を `0700` で新規作成します。同一 filesystem なので最終 rename は atomic です。

順序は次に固定します。

1. 現行 claim 取得と競合検査 `:770-780`。
2. staging build `:781-808`。
3. allowlisted binary だけを clean directory の destination fd へ copy。
4. 現行順序を維持して `_recheck_source_evidence` → `_assert_trace_diff` → perf 時の `_assert_no_trace_symbols`。
5. `_assert_no_trace_symbols` は destination fd を `/proc/self/fd/<fd>` と `pass_fds=(fd,)` で `nm -C` に渡す。
6. 同じ destination fd を `/proc/self/fd/<fd>` 経由で `full_sha256` し、その値だけを manifest に入れる。
7. 同じ fd を `os.fsync`。以後 binary inode へ書かない。
8. clean directory に host-generated `completion.json` を create-only で書き、metadata fd、binary 親 directory 群、clean root を内側から fsync。
9. staging を `_discard_build_dir` で除去。
10. `:776` の既存競合検査を残したうえで、rename 直前にも `os.path.lexists(bdir)` を再検査。
11. `os.rename(clean, bdir)`、`_fsync_dir(parent)`、最後に現行どおり claim を解放。

検査対象・SHA・fsync・publish される inode は destination fd の同一 inodeです。staging path を検査後に再 open しません。

v2 の失敗時は現行 `:858-862` と同じ診断方針を保ち、claim、残存 staging、clean publish candidate を自動回収しません。完成名 `bdir` だけは作りません。

#### `:943-997` — legacy clean publish

`root` 内に `<bdir>.publish-<pid>-<nonce>` を作り、v2 と同じ binary copy helper を使います。

- 現行 `_recheck_source_evidence` → `_assert_trace_diff` → `_assert_no_trace_symbols` の順序は不変。
- SHA/fsync は clean destination fd に対して行う。
- `admission.json` は clean directory に host-generated create-only で書く。
- staging 除去後、現行 `:988-993` の競合検査 → `os.rename(clean, bdir)` → `_fsync_dir(root)` を維持。
- legacy の現行 cleanup 方針 `:994-997` に clean directory も加え、失敗時は staging/clean の双方を除去する。

#### `:1095-1118` — nm の fd 対応

`_assert_no_trace_symbols(binary, *, binary_fd=None)` とし、fresh/cache-hit の secure pathでは held fdを使います。表示用エラーには最終予定 pathを残します。`binary_fd=None` の既存単体利用は互換維持します。

### failure policy

- allowlisted binary の欠落、path component symlink、leaf symlink、非通常ファイル、hard link、copy 中の inode/metadata 変化は fail-closed。build output 不正なら `BuildError`、cache/publish namespace 不正なら `BuildCacheError`。
- unallowlisted entry は再帰的に「検査して捨てる」のではなく、最初から開かず、copy 対象にせず、staging ごと除去する。
- unallowlisted entry を理由に一律失敗させません。通常の CMake build は CMakeCache/object/Makefile 等を必ず生成するため、それでは全正常 build を過剰拒否します。
- unallowlisted symlink/FIFO 等も final namespace へ出ず、内容を読みません。これを許すのは build sandbox の安全性を認めるためではなく、copy-out の受理対象が exact allowlist だけだからです。

## C — lexical gate の併置

### `orchestrator/campaign/coder_effect_gate.py:4-20`

module docstring にだけ最小追記します。

- 本 gate は build 前の coder hole bytes に対する有限 lexical 防壁。
- `buildcache` copy-out は build 後の output boundary。
- 両方を併置するが、どちらも host-security boundary でも certified safety の証明でもない。
- `p3_s4_red` / kickoff 型の既知 Python bypass は `materializer_admission` の bounded registry で非 admissible にするが、shell materializer・任意 binary path は閉じない。
- cache / WAL / COMMIT / freeze への gate receipt 非束縛は T-841 として残る。

`docs/dev-wave/**` には追記しません。

## B — coder-derived build の機械隔離

### DW-O13: 実在 field と quarantine の関係

実成果物に存在する coder 判定は次だけです。

- `BuildProvenance.CODER_AUTHORED = "coder-authored"`: `orchestrator/campaign/build_admission.py:43-55`
- CLI token 発行: `orchestrator/campaign/build_admission.py:253-278`
- token 消費: `orchestrator/campaign/build_admission.py:292-313`
- dirty source + token から class 導出: `orchestrator/campaign/build_admission.py:424-483`
- WAL `BUILD_START.build_admission`: `orchestrator/campaign/pipeline.py:796-807`

一方、`quarantine()` は `DiffQuarantineResult` を返す process-local seam であり、persistent receipt を発行しません。実装は `orchestrator/campaign/p3_s4_loop.py:193-270`、通過時だけ build へ進む経路は `:941-955` です。

したがって以下を混同しません。

- `build_admission.class`: 実成果物にある source provenance。
- `authority_kind="cli-opt-in"`: opt-in の事実。quarantine 通過証明ではない。
- `coder_entrypoint_site`: bounded Python inventory 用の process/source-site 名。成果物 field にしない。
- `quarantine_result.passed`: 同一 iteration 内だけの gate 結果。

B は downstream artifact から quarantine receipt を推定せず、非 admissible entry point を token 発行前に止めます。

### `orchestrator/campaign/materializer_admission.py:2-99`

既存 `MATERIALIZER_ADMISSION_REGISTRY` 1 個を型付きで拡張します。第 2 registry は作りません。

`MaterializerRegistration` に site kind を加えます。

- `DIRECT_MATERIALIZER`
- `CODER_ENTRYPOINT`

status は既存の `NON_ADMISSIBLE` / `ADMITTED_GATEWAY` に `QUARANTINE_GATED` を追加します。

coder entry point は次の exact 集合です。

- `orchestrator.campaign.p3_kickoff.main` — `NON_ADMISSIBLE`
- `orchestrator.campaign.p3_s4_red.main` — `NON_ADMISSIBLE`
- `orchestrator.campaign.p3_s4_loop.main` — `QUARANTINE_GATED`
- `orchestrator.campaign.p3_s4_loop_sort.main` — `QUARANTINE_GATED`
- `orchestrator.campaign.p3_s4_loop_trigger_gating.main` — `QUARANTINE_GATED`
- `orchestrator.campaign.p3_autonomous_workload_trial.main` — `QUARANTINE_GATED`

根拠は、kickoff が manual patch から直接 `run_campaign` へ進む `p3_kickoff.py:89-118`、red も同型の `p3_s4_red.py:142-175` である一方、正常 4 経路は以下を通るためです。

- backoff: `p3_s4_loop.py:930-955`
- sort: `p3_s4_loop_sort.py:254-265,432-496`
- trigger: `p3_s4_loop_trigger_gating.py:576-604,894-922`
- autonomous: `p3_autonomous_workload_trial.py:1835-1862,2327-2351` から trigger driver へ委譲

projection は分けますが正本 map は同じです。

- `CLOSED_PYTHON_MATERIALIZER_SITES`: direct CMake/buildcache inventory だけの互換 projection。
- `CLOSED_CODER_ENTRYPOINT_SITES`: coder authority issuer の projection。
- `NON_ADMISSIBLE_MATERIALIZERS` と `non_admissible_materializer()` の既存出力 schema は変えない。`s5_permutation_coverage.py:185-189` 等の成果物 schema drift を避ける。

`require_admitted_coder_entrypoint(site)` を加え、`QUARANTINE_GATED` だけを通し、未登録・NON_ADMISSIBLE は `BuildAdmissionError` 相当へ変換可能な明示例外にします。

### `orchestrator/campaign/build_admission.py:253-278`

既存の低位 token issuer と同じ opaque token を使う `add_registered_coder_build_authority_argument(parser, *, coder_entrypoint_site=...)` を追加します。

- flag が実際に指定された時点で `require_admitted_coder_entrypoint()` を呼ぶ。
- NON_ADMISSIBLE の red/kickoff は token を発行しない。
- 正常 entry point だけ既存 `_CoderAuthorityAction` へ進む。
- `BuildRunContext`、policy preimage、`ADMISSION_SCHEMA`、receipt body `:470-482` は変えない。

既存低位 helper は build-admission 単体 fixture 用に残しますが、production AST 閉包では使用 0 件を要求します。同一 process の caller が issuer を直接呼べる限界は `build_admission.py:4-13` のままで、認証境界とはしません。

### production entry point の置換

以下は import/call を registered helper に置換し、exact site literal を渡します。

- `orchestrator/campaign/p3_kickoff.py:35-37,89-98`
- `orchestrator/campaign/p3_s4_red.py:45-47,142-151`
- `orchestrator/campaign/p3_s4_loop.py:59-60,1091-1117`
- `orchestrator/campaign/p3_s4_loop_sort.py:73-74,392-430`
- `orchestrator/campaign/p3_s4_loop_trigger_gating.py:57-58,847-892`
- `orchestrator/campaign/p3_autonomous_workload_trial.py:87-93,2245-2289`

red/kickoff は flag parse 中に拒否されるため、cache/WAL/COMMIT を生成しません。これは「非認証成果物を後段で区別する」より狭い、生成前隔離です。

`s5_permutation_coverage._build_broken` は既に `materializer_admission.py:42-46` に登録され、成果物にも `s5_permutation_coverage.py:185-189` で diagnostic classification を載せるため変更しません。

shell materializer と任意 binary path は `materializer_admission.py:11-13` の明記だけを維持します。偽の registry entry を置くと Python closure が shell 面まで閉じたように見えるため、登録しません。

### AST 閉包

`orchestrator/tests/test_p3_build_authority_cli.py:47-120,355-393` を拡張します。

走査範囲は固定して `orchestrator/campaign/**/*.py`。

- production から低位 `add_coder_build_authority_argument` を呼ぶ site は 0 件。
- registered helper の call site 集合が `CLOSED_CODER_ENTRYPOINT_SITES` と exact equality。
- `coder_entrypoint_site` は `ast.Constant(str)` で、実際の enclosing `module.main` と一致すること。
- `build_run_context(... coder_authority=...)` の production call は、同じ module の registered entry point にのみ存在すること。
- 既存 `test_s8b_floor_campaign.py:1628-1736` の direct CMake/buildcache 閉包は維持し、typed projection によって coder entry point が混入しないようにする。

これにより新しい Python issuer、site literal の削除、未登録 entry point の追加が赤になります。動的 alias・外部 Python・同一 process 内の意図的な token 転用までは主張しません。

## 正負制御

### A: `orchestrator/tests/test_buildcache_v2.py`

既存被覆は metadata/hash/tamper/cache-hit が中心です。

- legacy sidecar fresh/hit: `:666-685`
- v2 manifest field・tamper: `:713-774,816-850`
- fresh/hit での observer gate 発火回数: `:792-813`

allowlisted-only copy、symlink、hardlink、特殊ファイル、same-fd SHA/publish は未被覆です。次を純増します。

- 正例を legacy/v2 で parameterize:
  - fake CMake staging に正常 binary、CMakeCache、object、偽 metadata、unallowlisted symlink/FIFO を置く。
  - fresh が通り、最終 file set が binary + host-generated metadata の exact 集合。
  - binary bytes/full SHA が独立 `hashlib.sha256` と一致、mode `0700`、2 回目は hit。
- 負例を legacy/v2 で parameterize:
  - allowlisted leaf が symlink、FIFO、directory、hardlink。
  - `BuildError` / `BuildCacheError`、完成 bdir 不在、build/run spy 未到達。
- TOCTOU 制御:
  - copy 後に元 staging pathを差し替える spy を入れる。
  - nm、SHA、fsync、published bytes が clean destination fd の同一 inodeを指すことを assert。
- cache-hit 負例:
  - binary の中間 directory または manifest/sidecar を symlink 化し、`_run` 未呼出しで拒否。
- gate 順序:
  - `_recheck_source_evidence` → `_assert_trace_diff` → `_assert_no_trace_symbols` → SHA → fsync → rename の観測列を exact assert。

既存 fixture hash は変更しません。

### B: `orchestrator/tests/test_p3_build_authority_cli.py`

- 正例: registered backoff/trigger entry point の flag が opaque tokenを発行し、dirty sourceが `CODER_AUTHORED` に達する。build spy が一度発火する。
- 負例: red/kickoff/unknown site の flag は token発行前に拒否され、build spy・WAL spyとも 0。
- AST closure exact equality により、registry entry削除・site literal削除・低位 issuerへの差戻しを検出する。

### B: `orchestrator/tests/test_p3_exploration_namespace.py:37-137,313-356`

現行 `:76-137` は red/kickoff も「flag があれば build spyへ届く」正例としており、T-840 と逆です。

- `_DRIVERS` を admitted 3 本と non-admissible 2 本へ分ける。
- loop/sort/trigger の既存 build-spy 正例を残す。
- red/kickoff は flag指定でも `BuildAdmissionError`、run/layout/WAL spy 0、directory未作成を負例に置換する。
- autonomous の registered site は `test_p3_build_authority_cli.py` の registry/action 正例と既存 autonomous launcher tests を使い、新たな重い integration fixture は作らない。

## 段 5 の所有分割

編集所有は次の素集合にします。

実装子 A — buildcache publish + C:

- `orchestrator/campaign/buildcache.py`
- `orchestrator/campaign/coder_effect_gate.py`
- `orchestrator/tests/test_buildcache_v2.py`

実装子 B — registry + 閉包:

- `orchestrator/campaign/materializer_admission.py`
- `orchestrator/campaign/build_admission.py`
- `orchestrator/campaign/p3_kickoff.py`
- `orchestrator/campaign/p3_s4_red.py`
- `orchestrator/campaign/p3_s4_loop.py`
- `orchestrator/campaign/p3_s4_loop_sort.py`
- `orchestrator/campaign/p3_s4_loop_trigger_gating.py`
- `orchestrator/campaign/p3_autonomous_workload_trial.py`
- `orchestrator/tests/test_p3_build_authority_cli.py`
- `orchestrator/tests/test_p3_exploration_namespace.py`

重複所有はありません。`s5_permutation_coverage.py`、`s8b_materialization.py`、`test_s8b_floor_campaign.py` は既存登録・互換 projection を保つため参照対象ですが、編集対象にしません。

## 総括

- P1 — 支持。staging から完成 namespace へ出す経路は v2 `orchestrator/campaign/buildcache.py:809-857` と legacy `:943-997` の2本だけです。cache hit は既存完成 entry の再利用で、第3 publish経路ではありません。
- P2 — 支持、ただし精密化。最終集合は親案どおりですが、untrusted staging からコピーするのは binary だけで、metadata は host-generated です。CMake `-B bdir` は再現文字列 `:543-584,909-918` にのみ残り、実 build は毎回 staging `:781-806,947-962` なので incremental rebuild の正しさ後退はありません。
- P3 — 支持、ただし単一 registry の typed projection と runtime flag gateを追加します。現行正本は `materializer_admission.py:31-83`、既存 direct-build AST閉包は `test_s8b_floor_campaign.py:1628-1736`。shell/任意 binary path は明示的に inventory外です。
- P4 — 支持（静的設計上、未実走）。A は既存 fake `_run` seam `test_buildcache_v2.py:195-223`、B は parser/build spy と AST で正負制御できます。計算ノードでの real buildを acceptance条件にする必要はありません。

scope外確認:

- `build_admission.py:470-482` の receipt schemaは変えない。
- `pipeline.py:796-807` の WAL body、cache preimage、COMMIT、freezeへの field追加はしない。
- quarantine結果を persistent receiptにしない。
- したがって T-841 は完全にscope外のままです。
- host-security boundary、issuer認証、certified safetyは主張しません。

実装前に親が読むだけで測れると有益な点:

- 既存正常cache binaryの `st_mode` / `st_nlink`。hard-link拒否で正常品を過剰拒否しない確認。
- 代表的な既存CMake treeに含まれるsymlink/特殊file種別。unallowlisted extrasをfail理由にしない判断の記録。
- 実行環境で `O_NOFOLLOW`、`O_DIRECTORY`、`os.supports_dir_fd`、`os.supports_follow_symlinks`、`/proc/self/fd` が利用可能か。
- 親による実装前baselineと実装後の関連テスト実測。こちらではpytestを走らせておらず、緑の主張はありません。