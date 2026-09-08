## 1. D1653 の記録 commit blob 照合が抜けている

- **判定: real**
- **影響:** inner identity を保ったまま authority の 24 個の blob SHA を再 canonical 化した lock が report 入口へ入り、レポートが誤った測定時 source authority を参照できる。

`decode_historical_campaign_lock()` は exact-24 grammar、hex 形式、canonical JSON までは検査するが、`contract_loader_commit:path` の実 blob SHA との照合はしない。根拠は `campaign_lock.py:382-424,568-612`。一方 D1653 は全 path の記録 commit blob 照合を必須としている (`verbatim-D1653.md:20-27`)。

段 2 プランの受理条件 `s2-plan.md:21-29` と `_assert_report_lock_binding()` の変更案 `s2-plan.md:87` にこの照合がない。現物の authority commit は三者で異なる。

- write-heavy `campaign.lock:1`: `0a07481b...`
- balanced `campaign.lock:1`: `c7ed5658...`
- read-heavy `campaign.lock:1`: `2a338449...`

最小修正: report 専用 lock 検査で、decoder が返す ordered 24 path を記録 commit から `_git(..., "show", commit:path)` で読み、全 SHA を照合する。1 path の digest を再 canonical 化しても拒否する負例を足す。

## 2. `load_calibration` は lock 由来 spec だけでは歴史値へ切り替わらない

- **判定: real**
- **影響:** live calibration の選択が変わると report が停止するか、歴史 campaign と異なる calibration path、SHA、records をレポートへ記録する。

`PreregistrationSpec` は calibration の path、artifact SHA、records を保持しない (`b10_backoff_shape_sweep.py:413-458`)。しかし現物 lock は `search_config.calibration` にそれらを記録している (`campaign.lock:1`, 3 系列とも同じ `calibration-753f...json`)。

段 2 の「`load_calibration(..., prereg.spec)` を lock 由来 spec に替える」だけでは、`load_calibration()` が live registry を読む事実は変わらない (`b10_backoff_shape_sweep.py:1619-1666`, `s2-plan.md:45,64`)。その結果は `_write_reports()` の provenance と Markdown の records 値へ流れる (`b10_backoff_shape_sweep.py:3667,3705`)。`validate_runtime_physical_residual()` もその live calibration の clocks 値を使う (`b10_backoff_shape_sweep.py:1502-1548,3950-3951`)。

最小修正: 3 lock の `search_config.calibration` を exact 共通比較して `CalibrationSelection` を復元し、report では `load_calibration()` を呼ばない。residual 検査と writer にその locked calibration を渡す。

## 3. live patch と `patchharness.applied` の扱いが閉じていない

- **判定: real**
- **影響:** historical spec の patch SHA を既存 call に流せば既知の SHA 不一致で report は発行不能のままになり、current patch と自己比較するなら歴史 report が無関係な live C++ tree の変化で再び停止する。

現在の report は次を通過して初めて collector に達する。

| 検査 | 現行箇所 | 段 2 の扱い |
|---|---:|---|
| phase exact enum | `3928` | 維持 |
| binary path policy | `3934` | 記載なし、維持される |
| `load_preregistration` | `3936`, 本体 `1551-1616` | report では除去 |
| submission receipt と prereg commit | `3937-3940`, `625-703` | 歴史 commit へ変更 |
| patch read と `validate_patch_bytes` | `3941-3943`, `845-860` | expected SHA の源が未定 |
| site、contract、official root | `3945-3949` | 記載なし、維持される |
| `load_calibration` | `3950` | 不十分。所見 2 |
| physical residual | `3951` | locked spec 化 |
| single tenant、CCBench pin、toolchain | `3952-3956` | 記載なし、維持される |
| `checkout` と `patchharness.applied` | `3958-3959` | current evidence として維持するとだけ記載 |
| `validate_applied_tree` | `3960-3965`, 本体 `888-970` | expected patch/formula の源が未定 |
| collector、lock、records、135 cells | `3974-3983`, `3518-3608` | locked identity/spec 化 |
| `report_root` | `3984-3987` | common locked spec SHA 化 |
| `_write_reports` | `3988-3997` | identity 分離を予定 |

現物歴史値は patch `36cd974c...`、formula `5b3d8dee...` だが、live 値は別である (`s1-brief.md:14-16`)。段 2 は current applied-tree 検査を維持するとする一方 (`s2-plan.md:69`)、`run_formal` の変更表にはその入力と writer の `applied_evidence` をどう構成するかがない (`s2-plan.md:97`)。

最小修正: report 分岐を patch checkout より前へ出し、report では `validate_patch_bytes`、`applied`、`validate_applied_tree` を実行しない。current report analyzer の evidence は HEAD、clean tree、`ANALYSIS_REL` blob/hash だけに限定する。

## 4. `_write_reports` に current era の identity が残る

- **判定: real**
- **影響:**判定値が locked v4 spec 由来でも、発行レポートは measurement space を v3、formula を current 値として表示し、測定 identity の参照が矛盾する。

現行 writer は module literal の `SPACE_VERSION` と current formula を出す。

- `SPACE_VERSION = "b10-backoff-shape/v3"`: `b10_backoff_shape_sweep.py:87-93`
- provenance の `space_version`: `3642`
- top-level formula と SHA: `3668-3669`
- current formula SHA `1205b1ff...` の pin: `test_b10_backoff_shape_sweep.py:3290-3297`

対して現物 3 lock は `search_config.space_version == "b10-backoff-shape/v2"`、formula SHA `5b3d8dee...` である (`campaign.lock:1`)。段 2 は `_write_reports` の型変更を述べるが (`s2-plan.md:96`)、これらの field mapping を名指ししていない。

最小修正: v3 provenance の measurement identity に lock の `space_version`、formula、patch、3 binding を置く。current 情報は `report_analyzer` の source commit と module SHA だけに分離し、Markdown も同じ区別にする。

## 5. 同じ file の編集は live campaign identity を必ず回転させる

- **判定: real**
- **影響:** merge 前の live campaign は同じ identity では resume できず、新しい campaign ID または exact binding rejection へ移る。

`ANALYSIS_REL` は編集対象自身 (`b10_backoff_shape_sweep.py:92`)。`load_preregistration()` はその current bytes を SHA 化し (`1598-1615`)、`PreregistrationBinding.core()` は `analysis_code_sha256` を binding digest に含める (`394-406`)。さらに `config_for()` が binding を search config に入れ (`1691-1710`)、`ident.campaign_id()` がそこから campaign ID を作る (`4043`)。

同じ layout に到達した場合も、`assert_resumable_binding()` は lock と BUILD_START の exact binding を検査する (`1787-1820`)。`bind_build_start_wal()` は新 SHA を WAL に記録する (`1823-1854`)。歴史 identity をこれらへ渡す漏れはないが、file hash の変化だけで live identity は変わる。

これは親 brief が認識している自己 hash (`s1-brief.md:57-58`) の未記載の帰結であり、段 2 の「非reportは従来どおり」 (`s2-plan.md:97-98`) だけでは live 無影響とはいえない。

最小修正: コード上の緩和はしない。親が live identity rotation を明示的に受け入れ、merge 前に既存 live B-10 campaign を drain するか、resume 放棄を裁定する。

## 6. `run_formal(report)` の wiring を空のまま残せるテスト計画

- **判定: real**
- **影響:** 新 helper の単体テストが全て通っても `run_formal()` の `load_preregistration()` が残り、report は `prereg-blob` で停止したままになりうる。

提案テスト `test_report_lock_v4_spec_is_reconstructed_without_live_parser` は復元入口の直接テストとして書かれている (`s2-plan.md:133-134`)。ところが変異表では、これが report の `load_preregistration()` 再呼び出しまで検出すると主張している (`s2-plan.md:157-158`)。直接 helper を呼ぶだけでは現行 `run_formal:3936` の残存を検出できない。

既存の report AST テストも `_write_reports` が report branch 内に 1 回あることしか固定しない (`test_b10_backoff_shape_sweep.py:1459-1476`)。

最小修正: `run_formal(phase="report")` を呼ぶ orchestration test を追加する。`load_preregistration`、`load_calibration`、patch/applied 経路を fail stub にし、3 lock の収集から `_write_reports` まで到達したことを assert する。

## 7. 合成 lock fixture は現物 3 本の互換性を証明しない

- **判定: real**
- **影響:** 合成 exact-24 lock のテストが緑でも、現物の authority map、outer bytes、系列固有 identity の一つを実装が拒否し、report が発行不能のまま残りうる。

段 2 は raw lock を複製せず、relevant fields から canonical lock を再構成する (`s2-plan.md:112-121`)。これは次だけを保証する。

- 現行 codec が、テストが作った exact-24 key set を decode できる。
- テストが転記した workload、binding、spec に対する B-10 検査が動く。

保証しないものは次である。

- 現物 outer bytes の直接 decode。
- 各 24 path の現物 blob digest と commit の組。
- activation/environment authority field。
- 現物 lock 3 本の raw SHA。
- 対応する block records、receipts、WAL との結合。

現物 raw SHA は write-heavy `0a32c22b...`, balanced `087e46df...`, read-heavy `5abdfe11...`。いずれも `campaign.lock:1` の単一 canonical JSON である。

最小修正: 3 本の exact raw bytes と SHA を hermetic fixture として固定し、decoder と report identity 入口へ直接通す。写しはその snapshot の byte 互換性だけを保証し、外部 evidence tree の不変性や関連 record/receipt までは保証しないとテスト名またはコメントへ明記する。

## 8. 通常 decoder への歴史 grammar 漏れは refuted

- **判定: refuted**
- **影響:** 段 2 の記載どおり実装すれば、通常 start/resume/certified admission の受理集合は広がらない。

通常 decoder は exact-63 のまま (`campaign_lock.py:508-548`)。歴史 decoder は別返却型 (`200-241,568-612`)。段 2 は通常 codec を変更せず (`s2-plan.md:72`)、B-10 report 入口でさらに v2 exact-24 に絞り、v1/current grammar を負例にする (`s2-plan.md:23-24,127-128`)。

また live resume は `_decode_lock_search_config()` が通常 decoder を使い (`b10_backoff_shape_sweep.py:1776-1784`)、report return 後だけ `assert_resumable_binding()` へ進む (`3970-3998,4047`)。`bind_build_start_wal()` も live verify 系だけである (`4049-4065`)。

最小修正: この分離をそのまま保つ。ただし所見 1 の commit blob 照合は report 専用入口へ追加する。

## 9. 死んだ既存検査は refuted、二重権威は一部残る

- **判定: refuted**
- **影響:** `load_preregistration`、patch 検査、resume/WAL 検査は非report phase で生き続けるため、関数自体は死なない。

`load_preregistration()` は live build/verify/perf/trial に必要で、`validate_patch_bytes()` は live/probe にも使われる (`b10_backoff_shape_sweep.py:1551-1616,3810-3847,4000-4243`)。既存 v1 report-lock 正例を exact-24 正例と v1 負例へ置換する判断も正しい (`test_b10_backoff_shape_sweep.py:2463-2483`, `s2-plan.md:147`)。

ただし新しい `_load_report_analysis_identity()` が clean tree、HEAD、analysis blob の検査を独自実装すると、`load_preregistration():1568-1577,1598-1606` と二重実装になる。現時点で成果物を変える反例まではないため real とは数えない。

最小修正: current analysis identity の既存部分だけを小さい共通 private helper に抜き、live loader と report loader の双方から呼ぶ。lock binding の module literal と artifact 値の二重照合は D1771 の有限 allowlist なので統合しない。

## 10. 親 brief と CLI 波及

- **判定: refuted。ただし運用確認が必要**
- **影響:** 現物 3 lock の `preregistration_binding.prereg_commit` は全て `77b33e37...` なので、P1-3 の値自体は現物と一致する。

`main()` は全 phase 共通の required `--prereg-commit` を `run_formal()` へ渡す (`b10_backoff_shape_sweep.py:4253-4265`)。既存テストが pin する job script も `IZANAGI_B10_PREREG_COMMIT` をそのまま driver へ渡す (`test_b10_backoff_shape_sweep.py:3521-3534`)。submit dry-run も phase ごとに同じ option を受ける (`3723-3739`)。したがって CLI syntax や job argv の変更は不要だが、report と live phase で要求値が異なるという運用契約は増える。

P1 ごとの判定は以下。

- P1-1: 「measurement prereg identity/spec」に限定すれば正しい。calibration まで lock 由来とするよう補強が必要。
- P1-2: 別 decoder、別返却型、exact-24 postconditionを保つ限り正しい。D1653 blob 照合が不足。
- P1-3: 現物値と一致し、別 flag も不要。ただし report submission receipt も同じ歴史値で作る必要がある (`load_submission_identity():672-673`)。

指定された射影外の runbook と job/submit script 本文は、単独段 dispatch の制約に従い読んでいない。そのため runbook が現在値を固定しているかは未確認である。

最小修正: report のみ `77b33e37...`、非report は live commit、という phase 別契約を既存 caller/runbook で確認し、report receipt の正例を追加する。

## 11. 段 5 の所有分割

- **判定: refuted**
- **影響:** 実装子が 1 本なら所有集合は自明に素であり、driver と既存 test file を同じ子が原子的に変更してよい。

ただし `s2-plan.md:76` は対象を driver 1 file と書き、`s2-plan.md:110,164-166` は test file も同じ実装子が更新するとしており、表現が食い違う。

最小修正: 段 5 の ownership を `{b10_backoff_shape_sweep.py, test_b10_backoff_shape_sweep.py}` と明記する。所見 7 に従って fixture file を追加するなら、それらも同じ実装子の所有集合へ入れる。

## 総括

1. **real 所見は 7 件。** 最も重いのは、D1653 が必須とする記録 commit blob の全 path 照合がなく、再 canonical 化した偽 authority lock を report が受理できる点。
2. **現状の段 2 プランは採用不可。** 特に locked calibration、patch/applied 分岐、writer の measurement/current identity 分離、`run_formal(report)` の到達テストを補ってから author へ渡すべきである。
3. 親が段 4 で裁定すべき論点は、(a) D1653 の 24 blob 実照合を report 入口へ必須追加すること、(b) report から current patch/applied-tree gate を外して analyzer source identity のみにすること、(c) 同 file 編集による live campaign identity rotation を受け入れて merge 前に drain すること、(d) raw lock 3 本を hermetic fixture として所有すること、の 4 点。

pytest は実走していない。以上は指定資料だけによる静的検査である。