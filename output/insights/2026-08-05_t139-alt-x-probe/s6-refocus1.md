## F1〜F7 対応表

| 所見 | 判定 | 根拠 |
|---|---|---|
| F1 compile argv | `closed` | ycsb object を output suffix まで exact-one にし、`result.cc` / `util.cc` も exact-one: `tools/pegasus/probes/t139_positive_control_probe.sh:50,59,60,61,75,78,89`。既存実 DB でも一致数は各1件: `output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/attempts/1/build-stock/compile_commands.json:4,9,529,544,559,574`。新 build は未実走。 |
| F2 2窓 liveness | `partial` | YCSB は barrier 後、初回・retry の各試行で `begin()` を必ず通り、`started` により再設定されない: `external/ccbench/common/runner.hh:189,192,193`、`external/ccbench/include/ycsb.hh:108,111,113,155,164`、`tools/pegasus/probes/t139_positive_control.patch:80,82,85`。しかし起点は `thread_local` であり、段4の worker 間共有時刻ではない: `s4-adjudication.md:78,80`、patch`:75,76,83,93,99`。 |
| F3 `git status` fail-open | `closed` | main と全 dependency/third-party/CCBench で rc を先に捕捉し、非0を拒否する: `tools/pegasus/probes/t139_positive_control_probe.pbs:74,78,165,167`。 |
| F4 commit 束縛 | `regressed` | commit blob bundle と実行中 PBS hash は実装済み: PBS`:29,100,108,120,128,295`。ただし commit は qsub 時でなくジョブ開始時に選ばれ、canonical preregistration の basename を必ず拒否する: PBS`:8,29,95,98`。 |
| F5 pin 閉包 | `partial` | pin/clean/replace/index/shallow/alternates と実 clone の状態は整合: PBS`:152,156,165,168,171,177`、`tools/pegasus/policy.json:36,40`。一方、third-party/CCBench snapshot は検査後の mutable working tree を `tar` しており、消費 bytes と pin の TOCTOU が残る: PBS`:165,185,189,242,244,265,270`。 |
| F6 閉表 state | `partial` | 通常経路の phase・terminal state と true/false/correctness/liveness は実装済み: PBS`:40,45,48,57`、driver`:319,321,468,559,563`。ただし必須 env・`RUN_COMMIT` 検査は EXIT trap 設置前で、この失敗には state が出ない: PBS`:8,29,33,40,64`。 |
| F7 副次診断 | `closed` | TPS を先に primary へ確定し、診断欠落は `NA` と理由に落ちるだけ: driver`:498,504,506,533,542,548,558`。 |

## 事前登録 P-A〜P-G 照合

| 項目 | 判定 | 根拠 |
|---|---|---|
| P-A | `partial` | modeX・arm・rep は一致するが、段4が要求する hash/pin/tree/root の凍結値が文書にない: `s4-adjudication.md:116,120,121`、`preregistration.md:24,26,31,32`。 |
| P-B | 一致 | `preregistration.md:54,57,58,59,60,61`。 |
| P-C | 不一致 | 文書も実装も「各 worker の初回試行起点」へ変更しており、段4の共有時刻と矛盾する。また段4の nm 補助 gate が受理条件から欠落: `s4-adjudication.md:80,135`、`preregistration.md:75,78,79,81,85`。 |
| P-D | 一致 | `preregistration.md:89,91,92`。 |
| P-E | 一致 | `preregistration.md:94,96,97,98,100,101,102`。 |
| P-F | 一致 | `preregistration.md:104,106,109,110`。 |
| P-G | 内容は一致・状態は未充足 | 実走前 commit は明記されているが、現在は未追跡: `preregistration.md:1,9,11`。 |

## 新規所見

[blocker] [F2 の境界は依然として走行全体の固定 `[0,1500ms)` / `[1500,3000ms)` ではない。各 thread が別々の `now()` を保存する] [根拠: `s4-adjudication.md:78,80`、`tools/pegasus/probes/t139_positive_control.patch:75,76,80,83,88,93,99`、`external/ccbench/common/runner.hh:294,296,298,299`、`external/ccbench/include/ycsb.hh:111,113,161`] [成果物影響: 遅延 worker の in-flight commit が全体の3秒終了後でも window 2 を埋められ、逆に正常 worker が遅れて起動すると window 2 を得られず、576/576 の受理集合が偽陽性・偽陰性の双方へ変わる] [最小の直し方: runner の `storeRelease(start,true)` 直前に `ADD_ANALYSIS` 専用の共有 `steady_clock` 起点を一度だけ設定し、全 worker の報告をその時刻へ結び直す。事前登録79行も共有時刻へ戻す]

[blocker] [F4/P-A/P-C は qsub 時点の study identity に束縛されていない。`RUN_COMMIT` はジョブ開始時の HEAD であり、事前登録にも期待 commit/hash/root/pin がなく、nm gate も欠落する] [根拠: `s4-adjudication.md:120,121,135,156,158`、PBS`:8,29,100,120,128`、driver`:347,357,360,363`、`preregistration.md:24,67,75,81,85`] [成果物影響: queue 待ち中に HEAD が A→B へ進み PBS blob が不変なら、Aとして投入した submission ID がBのpatch/driver/policyを実行できる。さらに事前登録上は受理可能な run を実装の nm gate が拒否し、study identity と受理集合が一致しない] [最小の直し方: qsub 時に期待 commit を必須 env で渡し、ジョブで一致を検査してその commit だけを展開する。投入前 receipt に3 blob hash、policy、CCBench、dependency/third-party root・pin・treeを固定し、事前登録へ nm 条件も追記する]

[blocker] [親が置いた canonical preregistration は basename gate により恒真拒否される] [根拠: `tools/pegasus/probes/t139_positive_control_probe.pbs:95,96,98`、`output/insights/2026-08-05_t139-alt-x-probe/preregistration.md:1,6`] [成果物影響: 指定 env を canonical path にすると exit 3 となり、bundle/hash/dependency/build/verdictへ一度も到達しない] [最小の直し方: basename を `preregistration.md` に直すか、より強く canonical relative path 全体との exact 比較にする。literal 本文検査自体は現文書で通る]

[blocker] [F5 の tracked snapshot は Git object ではなく status 検査後の working-tree bytes を読むため、pin TOCTOU が残る] [根拠: PBS`:165,167,179,185,189,190,242,244,250,265,270,273`] [成果物影響: status 後から tar 読取りまでに tracked file が変更されると、witness は pinned tree/clean=1 のまま別 bytes を build し、binary・TPS・verdictを変更できる] [最小の直し方: `$pin` の tree/object DB から job-local snapshot を生成する。CCBench は export-ignore を避けるため、一時 index + `read-tree "$pin"` / `checkout-index`、または `ls-tree` + `cat-file` を使う]

[blocker] [F6 の EXIT trap より前に terminal state 未発行の失敗経路が残る] [根拠: `tools/pegasus/probes/t139_positive_control_probe.pbs:8,11,13,29,31,33,40,64`、`s4-adjudication.md:141,144,147,148`] [成果物影響: 新 env の設定漏れや HEAD 取得 timeout が state artifact を残さず、submission の報告漏れ・infra replacement の誤判定を許す] [最小の直し方: PBS_JOBID/PBS_O_WORKDIR から OUT を確定した直後に trap を設置し、commit 未確定時は `run_commit=unavailable` を持つ pre-performance state を発行する]

[blocker] [内部 timeout の直列総和は 3817 秒で、3600秒 walltimeにも3300秒 absolute deadlineにも収まらない] [根拠: `s4-adjudication.md:107,108`、PBS`:4,16,29,66,74,81,102,137,156,179,187,208,213,214,228,244,248,249,256,270,271,279,283,284,285,290,291,295`、driver`:367,369,370,371,403,405,448,493`] [成果物影響: `pre=1417` 秒、driver=`2400` 秒、合計 `3817` 秒。前段が許容 cap 近くで正常完了すると driver に最大1883秒しか残らず、個別 cap 内の正常実装でも verdict 前に infra failure になる] [最小の直し方: Git検査・snapshotをsource単位の一つの timeoutへ集約し、driverを含む直列 cap 総和を3300秒以下へ再配分する。absolute deadlineによる後段切詰めだけで済ませない]

## Refuted

- F2 の「初回前に `begin()` を通らない」「retryで起点が再設定される」は refuted。問題は共有性です。
- F4 の「NQSV spool のため PBS hash が常に不一致」は refuted。同じ scheduler の既存実測で実行 path は `.../user_script`、sha256 はrepo scriptと一致しています: `tools/pegasus/t141_region_profile.sh:468,473,490`、`output/env/pegasus/profile/t141-directive-calibration/0_873859.nqsv/attestation.txt:12,13`。
- F5 の追加検査が現在の6 sourceを誤拒否する疑いは refuted。全HEADがpolicy/gitlinkと一致し、status空、replace/index特殊bit/shallow/alternatesなしでした。例: `tools/pegasus/policy.json:36,40`、各 `.git/HEAD:1`。
- F1 の実 object path 不一致と、F7 の副次診断 gate は refuted。
- F6 の trap 設置後における二重発行競合は refuted。科学的 false は state=`verdict_false` を出して rc=0、trapは既存stateを保持します。ただし qstat上の成功は pass を意味しません。

## 総括

- (a) 投入: **NO-GO**
- (b) blocker: **6件**
- (c) regressed: **1件（F4）**
- (d) refuted: `begin()` 未呼出し／retry再設定、NQSV spool恒真拒否、現行6 Git sourceの正常clone誤拒否、F1 object path不一致、F7 secondary gate、post-trap state二重発行
- (e) 親が投入前に手で確認すべきこと:
  - 上記6件を直し、焦点再レビューを再実施する。
  - 3 probe file と canonical preregistration を同一 commit に含め、期待 commit/hash receipt を qsub 前に固定する。
  - dependency 6本の clean/pin状態を投入直前に再確認する。
  - timeout総和を再計算して `≤3300` 秒にする。
  - 実走後は `state/terminal-state.tsv` と `verdict.tsv` を必ず突き合わせる。PBS rc=0だけで pass と読まない。
  - 全 submission ID・replacement理由を結果閲覧前から台帳化する。

実施したのは静的検査のみです。`bash -n` と `git diff --check` は rc=0。build・pytest・self-check・qsubは実行しておらず、緑とは判定していません。