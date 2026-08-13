必読対象はすべて読取可能だった。実装方針は成立する。ただし、親案には二つ補強が必要である。

- marker は一組だけであることも受理条件に加える。
- `FileNotFoundError` 以外の読取失敗は marker の観測可否にかかわらず reject する。

また、現行 `s8a_trigger_coverage` の template 初期値 `izanagi_gate_pass = true;` は emitter の閉じた 32 述語に属さないため、新 validator 到達後は意図どおり reject される。これを救う例外は追加しない。

## 1. 共有 validator の署名と配置

署名は次で固定する。

`_require_materialized_trigger_axis_predicate(evidence: SourceEvidence) -> None`

- 引数: exact `SourceEvidence`
- 返り値: `None`
- reject: `BuildAdmissionError`
- エラー文は単一定数、例えば `trigger axis predicate が materialized source と不一致`
- source/parser 由来例外は `raise BuildAdmissionError(...) from None` に正規化する
- admission receipt や mask は返さない。検証結果を receipt に追加しないためである

配置:

- [build_admission.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/build_admission.py:24) の標準 import に `os`、`re` を追加。
- [build_admission.py:32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/build_admission.py:32) 付近に以下を追加。
  - `axis_trigger_gating` の `MARKER_ID`、`SOURCE_REL`、`PREDICATE_HOLE_INDENT`
  - `diff_quarantine.parse_template_file`
  - `reflux_ir.TriggerGateIR`、`emit_predicate`
- validator と補助定数・raw physical-line 分割 helper は `_source_map` の直後、現行 [build_admission.py:123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/build_admission.py:123) の後へ置く。
- `range(32)` から期待 hole bytes を module import 時に tuple 化し、評価ごとに emitter を32回呼ばない。

実 import グラフは次のとおりで、循環はない。

- 現行: `build_admission → source_digest → model`、`build_admission → pin`
- 追加: `build_admission → diff_quarantine`。同 module は標準ライブラリしか import しない（[diff_quarantine.py:32-38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/diff_quarantine.py:32)）。
- 追加: `build_admission → reflux_ir → axis_trigger_gating → pin`（[reflux_ir.py:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/reflux_ir.py:8)、[axis_trigger_gating.py:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/axis_trigger_gating.py:20)）。
- `pipeline → build_admission` は既存だが、`build_admission` から `pipeline` は import しない。
- `trigger_gate_binding` は import しない。同 module の canonical 判定は `.strip()` を使うため（[trigger_gate_binding.py:111-133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/trigger_gate_binding.py:111)）、今回必要な exact source bytes 判定には使えない。

## 2. 呼出し点と検査順序

`derive_build_admission`:

- 現行 [build_admission.py:518](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/build_admission.py:518) の `source_body = _source_map(source)` の直後に呼ぶ。
- generator/review の曖昧性判定 [519-520](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/build_admission.py:519) と stock/review/generator/coder class 分岐 [524-551](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/build_admission.py:524) より前に置く。

`require_build_admission`:

- exact `BuildAdmission` 判定 [642-643](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/build_admission.py:642) の直後に `_source_map(expected_source)` で exact source を先に確定し、validator を呼ぶ。
- その後、現行 [644-650](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/build_admission.py:644) の sealed body と class を検証する。

class 判定前に置くことで成立する性質は、「stock/human/generator/coder のどの class 値も semantic gate の発火条件にならず、class 選択で迂回できない」ことである。malformed trigger source と曖昧 capability が同時にある場合は、source semantic error が先に返るが、どちらも fail-closed で receipt は発行されない。

`validate_build_admission_receipt` には入れない。

- 同関数は `expected_source=None` を許す永続 receipt 検証である（[build_admission.py:656-667](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/build_admission.py:656)）。
- WAL replay は source を渡さず呼ぶ（[wal.py:1115-1125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/wal.py:1115)）。
- S8a の保存 artifact 検証も source を渡さない（[s8a_trigger_sweep.py:181-185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/s8a_trigger_sweep.py:181)）。
- build materializer は receipt mapping ではなく sealed admission を `require_build_admission` で再検査する（[buildcache.py:1273-1277](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/buildcache.py:1273)、[buildcache.py:1538-1542](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/buildcache.py:1538)）。

したがって replay に live file I/O を混ぜても発行時の意味を証明できず、過去 checkout の消失だけで replay を壊す。`_ADMISSION_KEYS` [428-432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/build_admission.py:428) と body [553-565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/build_admission.py:553) は変更しない。

## 3. 受理述語

受理条件は次の連言とする。

1. `source_root/SOURCE_REL` が読める。
2. trigger marker directive が存在する場合、parser と同じ BEGIN/END 正規表現で BEGIN 1 件・END 1 件だけである。
3. `parse_template_file(path, MARKER_ID)` が `TemplateMarker` を返す。
4. `marker.hole_first..marker.hole_last` がちょうど1物理行である。
5. その1行の payload bytes が、いずれかの `mask ∈ {0,…,31}` について  
   `PREDICATE_HOLE_INDENT.encode("utf-8") + emit_predicate(TriggerGateIR(mask)).encode("utf-8")`  
   と完全一致する。

`PREDICATE_HOLE_INDENT` は ASCII space 2 bytes（[axis_trigger_gating.py:23-27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/axis_trigger_gating.py:23)）。mask の閉区間は IR 自身も 0〜31 に制限する（[reflux_ir.py:69-72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/reflux_ir.py:69)）。emitter は必ず単一行を返す（[reflux_ir.py:131-141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/reflux_ir.py:131)）。

物理行分割は既存 binding 検査 [pipeline.py:83-100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/pipeline.py:83) と同じにする。`\r\n?|\n` を delimiter として認識し、CR delimiter の `\r` は payload に残す。

| 入力 | 結果 |
|---|---|
| LF + exact 2-space indent + emitter bytes | accept |
| CRLF の hole 行 | payload 末尾に `\r` が残るため reject |
| tab indent | expected 2 spaces と不一致で reject |
| 余分な先頭・末尾空白 | byte 不一致で reject |
| 空 hole | `len(hole_lines) == 0` で reject |
| 複数行 hole | `len(hole_lines) != 1` で reject |
| `izanagi_gate_pass = true;` | どの emitter 出力でもないため reject |
| BEGIN/END marker の重複 | unique pair 条件で reject |
| canonical hole と異なる binding mask | generic validator は accept、その後の既存 mask-specific 検査が reject |

marker 件数は raw `MARKER_ID` の単純出現回数で数えない。実 patch は marker directive 以外の説明コメントにも同 ID を含む（[template patch:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/patches/silo-backoff-trigger-gating-variant.patch:43)）。BEGIN/END directive だけを parser 互換の行単位 regex で数える。

`parse_template_file` は最初の END で走査を打ち切るため（[diff_quarantine.py:573-607](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/diff_quarantine.py:573)）、unique pair の前置検査がないと後続の重複 block を見逃す。

## 4. no-op と reject

| 状態 | 判定 | 根拠 |
|---|---|---|
| `SourceEvidence.source_root` field が欠落・相対 path | reject | exact `SourceEvidence` 自体が成立しない（[source_digest.py:123-127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/source_digest.py:123)） |
| filesystem 上で source root が存在しない | no-op | target open の `FileNotFoundError`。合成 evidence と過去 path を維持する |
| root はあるが `SOURCE_REL` が無い | no-op | trigger axis 未 materialize と扱う |
| source は読めるが BEGIN/END trigger marker が双方 0 件 | no-op | stock・非 trigger 木 |
| BEGIN または END が一方だけ、あるいは重複 | reject | axis marker を観測済みだが構造が一意でない |
| marker あり、`parse_template_file` が `None` | reject | parser の documented fail-closed 契約（[diff_quarantine.py:541-561](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/diff_quarantine.py:541)） |
| marker あり、UTF-8 decode 不能 | reject | hole bytes の位置と構造を確定不能 |
| `PermissionError`、`EIO`、`ENOTDIR` 等 | reject | `FileNotFoundError` だけを明示 no-op にし、アクセス失敗による marker 隠蔽を許さない |

実 production の `resolve_evidence` は `EVOLVE_BLOCK_SOURCES` 全体を読む（[source_digest.py:640-650](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/source_digest.py:640)）。対象 file が無ければ `_read` が既に fail-closed になる（[source_digest.py:580-594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/source_digest.py:580)）。したがって missing-file no-op が成功 build を新規に許すわけではない。

既存合成試験への静的影響も確認済み。

- `test_build_admission.py` の `_source` は `/evidence/ccbench` 等の合成 root（[test_build_admission.py:50-69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/tests/test_build_admission.py:50）。target 不在なので no-op。
- `test_campaign.py` の標準 evidence は `/tmp/izanagi-test-ccbench`（[test_campaign.py:125-142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/tests/test_campaign.py:125)）。専用 marker fixture 以外は target 不在。
- 既存 canonical materialization 正例 [test_campaign.py:5582-5625](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/tests/test_campaign.py:5582) は新 validator も通る。
- crossed-mask 試験 [test_campaign.py:5629-5665](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/tests/test_campaign.py:5629) は generic validator を通った後、既存 binding 検査で従来どおり落ちる。
- `s8b_floor`、buildcache、WAL/report 等の合成 evidence も `/fixture/...` または temp layout root に対象 file を置かない形である。pytest はこの sandbox では未実走であり、緑とは報告しない。

## 5. binding を省略する5経路の到達証明

| 経路 | gateway 到達 |
|---|---|
| S8a trigger coverage | `_build` が evidence を作り [s8a_trigger_coverage.py:153-158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/s8a_trigger_coverage.py:153) で `derive_build_admission` と `require_build_admission` の双方を通る |
| S-1 direct comparison | `run_role` の production default は `pipeline.evaluate`（[s1_direct_comparison.py:674-681](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/s1_direct_comparison.py:674)）。呼出し [869-873](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/s1_direct_comparison.py:869) は binding を渡さず、pipeline の [derive/require:768-778](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/pipeline.py:768) に到達する |
| S8b oracle/floor campaign | evidence/review 後に [s8b_floor_campaign.py:1207-1209](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/s8b_floor_campaign.py:1207) で derive。続く `build_v2` でも require される |
| between-run floor | [between_run_floor.py:166-171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/between_run_floor.py:166) の inline derive を通り、`buildcache.build` の require にも到達する |
| S-1 extime calibration | patch/quarantine 後 [s1_verify_extime_calibration.py:349-364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/s1_verify_extime_calibration.py:349) で derive、その後 `buildcache.build` の require に到達する |

到達しない経路はない。したがって ruling (b) の範囲で5 call site を編集する必要はない。

ただし S8a coverage は template patch をそのまま適用して build し（[s8a_trigger_coverage.py:257-268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/s8a_trigger_coverage.py:257)）、hole は現行 `izanagi_gate_pass = true;`（[template patch:101-103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/patches/silo-backoff-trigger-gating-variant.patch:101)）である。emitter は必ず `kUnset` 比較から始まるため、これは32候補の外であり reject される。段4では「この characterization driver の再実行を閉じる」帰結を明示確認する。`true` の特例受理や call-site 迂回は規律2違反なので提案しない。

## 6. テスト計画

追加先は [test_build_admission.py:95-99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/tests/test_build_admission.py:95) の helper 群付近と、現行 admission 試験末尾 [test_build_admission.py:239-249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/tests/test_build_admission.py:239) の後とする。

追加 nodeid:

- `test_trigger_axis_semantic_admission_accepts_exact_emitter_bytes_without_binding[mask-0]`
- `test_trigger_axis_semantic_admission_accepts_exact_emitter_bytes_without_binding[mask-31]`
- `test_trigger_axis_semantic_admission_rejects_noncanonical_hole_bytes[crlf]`
- `...[tab-indent]`
- `...[extra-leading-space]`
- `...[trailing-space]`
- `...[empty-hole]`
- `...[two-hole-lines]`
- `...[template-default-true]`
- `...[non-emitter-spelling]`
- `test_trigger_axis_semantic_admission_rejects_duplicate_marker_blocks`
- `test_trigger_axis_semantic_admission_rejects_unparseable_marker[missing-else]`
- `...[invalid-utf8]`
- `test_trigger_axis_semantic_admission_rejects_unreadable_source`
- `test_trigger_axis_semantic_admission_is_noop_without_axis[missing-root]`
- `...[missing-source-file]`
- `...[marker-absent]`
- `test_runtime_admission_rechecks_trigger_axis_while_receipt_replay_does_not`
- `test_trigger_axis_semantic_validator_precedes_class_selection`
- `test_bindingless_trigger_build_paths_reach_semantic_admission_gateway`

`runtime_admission...` は canonical source で derive した後に hole を非正準へ変え、次を同時に固定する。

- `require_build_admission` は再読して reject。
- `validate_build_admission_receipt` は live source に依存せず同じ receipt を受理。
- receipt key 集合は既存 [test_build_admission.py:207-223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/tests/test_build_admission.py:207) と完全一致のまま。

5経路の不変条件試験は文字列検索ではなく `ast` を使う。

- `build_admission.derive_build_admission` と `require_build_admission` の双方に validator call があること。
- `s8a_trigger_coverage._build`、`s8b_floor_campaign.build_cells`、`between_run_floor.main`、`s1_verify_extime_calibration._build_target` の direct gateway call を exact function node 内で確認。
- `s1_direct_comparison.run_role` は `evaluate_fn` の default が `pipeline.evaluate` であり、その callable を実際に呼ぶことを確認。
- `pipeline.evaluate` が derive と require の双方を呼ぶことを確認。
- inventory は上記5件の exact set とし、経路追加・削除・alias 化はレビューなしに通さない。

これにより validator call 削除、mask 範囲の上下端欠落、`.strip()` 導入、1行制約削除、CR除去、marker uniqueness 削除、I/O error の no-op 化をそれぞれ別の試験が検出する。

## 7. 性能

現行 stock file は約23.5 KiB、741行である。marker 無しでは raw file を1回読むだけで parser を呼ばない。marker ありでは raw bytes 読取と `parse_template_file` の text 読取の計2回、いずれも O(file size) である。

cache は導入しない。

- `SourceEvidence` 自身が checkout の可変性と ABA 窓を明記している（[source_digest.py:101-105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/source_digest.py:101)）。
- derive 後、pipeline require、trace/perf 各 build の require で再読することは、source 変更後に古い合格を使い回さないための意図的な再検査である。
- `source_root`、mtime、`SourceEvidence`、digest を key にした memoization はこの再検査を弱める。
- 32 emitter bytes だけは import 時に一度生成し、ファイル検査ごとの生成コストを避ける。

数十 KiB の再読は source digest の preprocess と C++ build に比べて十分小さく、正しさ境界を狭める cache は正当化できない。

## 8. 親 brief P1〜P5 の評価

| 項目 | 判定 | 根拠 |
|---|---|---|
| P1 | 同意 | `derive_build_admission` は genome を受け取らず（[build_admission.py:507-513](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/build_admission.py:507)）、`SourceEvidence` は `genome_sha256` しか持たない（[source_digest.py:108-116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/source_digest.py:108)）。gateway が観測できる axis 実在入力は source root と marker である |
| P2 | 同意 | derive は発行時、require は materializer 再検査時、receipt validator は archival replay という責務分離が既存 call graph と一致する。receipt replay に file I/O を入れない |
| P3 | 一部反対 | 1物理行・exact bytes・mask 0〜31 は正しい。ただし `parse_template_file` が最初の block 後で停止するため、full acceptance predicate としては marker pair uniqueness が不足する。また現行 S8a の literal `true` が reject される帰結を明記する必要がある |
| P4 | 反対 | missing root/file と marker 無しの no-op には同意する。しかし「marker を判定できた場合だけ read failure を reject」は権限・I/O failure による fail-open を作る。`FileNotFoundError` 以外の `OSError` は無条件 reject とする |
| P5 | 同意 | `build_admission.py` と `test_build_admission.py` だけで閉じる。pipeline の既存 mask-specific 検査 [pipeline.py:74-105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/pipeline.py:74)、5 call site、T-921 所有 file は編集しない |

## 総括

単一 validator を `build_admission.py` に置き、derive と require の class 判定前から必ず呼ぶ。受理集合は「一意な marker pair、1物理行、LF、2-space indent、mask 0〜31 の emitter bytes 完全一致」に閉じ、receipt は一 byte も変えない。

5経路はすべて既存 gateway に到達する。現行 S8a coverage の literal `true` も例外なく reject される。missing root/file と marker 無しだけを no-op とし、それ以外の読取不能・parse 不能・重複 marker・非正準 hole は `BuildAdmissionError` で fail-closed にする。