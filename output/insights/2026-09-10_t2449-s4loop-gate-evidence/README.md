# [T-2449] 段 4 loop の condition gate supply arm は現行 main で既に通る — 止めていたのは gflags ではなく masstree の offline 供給だった

dev-wave `dev-wave-t2449-s4loop-gate-evidence` (branch `worktree-dev-wave-t2449-s4loop-gate-evidence`、
base = local main `7f17e1c63b5db01b424c87cf5778635dd653dab2`、2026-09-09 22:30 JST〜) の一次資料。

## 依頼と、実測が返した答え

依頼は「job `983020.nqsv` (2026-09-08) で `condition_meaning_gate` の supply arm
(`preprocess-failed`) が止めた件を計算ノードで**再現**し、gate の preprocess argv と stderr を
evidence root へ写し、system gflags 不在と gflags/glog の include 経路の関係を確かめる」だった。

**答え: 現行 main では再現しない。** そして止めていたのは **gflags ではなく masstree の offline 供給**だった。

## 何を根拠にそう言えるか

### 根拠 1 — 現行 main と同一 bytes のコードが、計算ノードで gate を越えている

姉妹 wave `dev-wave-t2182-k2-eval-run` の attempt-0001 が同じ job body を計算ノードへ投入している。

| 項目 | 値 |
|---|---|
| job | `988516.nqsv` |
| Created / Started / Ended | 2026-09-09 22:51:21 / 22:59:16 / 23:00:07 (JST)、Elapse 55S |
| `driver_rc` | 0 |
| `job.stderr` | CMake の `Manually-specified variables were not used by the project: CMAKE_C_COMPILER` が 2 回のみ。**`condition gate rejected P3 S4 loop` の traceback は無い** |
| `job.stdout` の到達点 | `[campaign] evaluate silo\|BACKOFF_FIXED=20,BACK_OFF=1,...` → `[eval 8a84a7b00103] built trace=cf94503330a15b40 perf=3f1db7e3a3cd5f39` → `[eval 8a84a7b00103] abort: trace-parse-error` → `[campaign] done: 0 committed / 1 aborted / 0 skipped (of 1)` |
| fixture 値 | 20 (job `983020.nqsv` と同じ) |

`_require_condition_gate` は `run_campaign` より前に例外を上げる (`p3_s4_loop.py` の
`_run_one_iteration_resolved` 内、gate 呼出しが `run_campaign` 呼出しより前) ので、
`[campaign] evaluate` 行への到達そのものが gate 通過の証拠である。

**この走行が使ったコードは本 wave の base と同一 bytes である。** submit-tree の
`orchestrator/campaign/p3_s4_loop.py` = sha256
`9207514ba04ab51b662a8b48ff063e1b8198867cc2100705d66227a744db14e4`、
`orchestrator/campaign/condition_meaning_gate.py` = sha256
`b4f6cabc3538f39b3949610514447b909d747a19b994cbc222e76d43978f8511` で、
local main `7f17e1c63` の現物と一致する。したがって「別の版で通った」ではなく「**この版で通った**」である。

**この evidence は他 session (T-2182 wave) の成果物である。** 本 wave は伝聞でなく現物を読んで確認し、
その wave の job dir が撤去されても検証できるよう `evidence/t2182-attempt-0001/` へ写した。
**可逆最小正規化 (DW-S07):** `job.stdout` は逐語コピーが `git diff --check` の行末空白に抵触するため、
行末の空白 / tab を除去した (可視文字不変)。原文 sha256
`457b3be59facad01956107b9e5c6f9d161fa014c974decd29e88d3aecbe9e02a` (12408 bytes)、正規化後
`3b4396b715496549eb48c354aaa25bdaf28f5e6371677f7dcc6322822f641160` (12404 bytes)。
`diff -w -B` で原文と一致する (実測 rc=0、2026-09-10)。`compute-result.json` (sha256
`023e593645c13ca568a4bb19a6cd84b5f3034a29cc4eb3c58cbc4f56bcde4f89`) と `job.stderr` (sha256
`e03f8a67ab25dea9444ee1eafdaa3f4684c67da39d2830f7992c1857cde25e35`) は無変更のコピーである。
原本は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2182-k2-eval-run/evidence/attempt-0001/`。

### 根拠 2 — 983020 の時点で gate へ offline 引数が渡っていなかった

`_configure_compile_commands` は `captured.configure_args` を gate 自身の cmake configure argv へ
そのまま入れる。983020 の commit `a173f0ab5` では gate 呼出しが無条件に
`_require_condition_gate(sub, genome)` で、`configure_args` は既定の `()` だった。offline 引数
(`-DCMAKE_PREFIX_PATH` / `-DFETCHCONTENT_BASE_DIR` / `-DFETCHCONTENT_SOURCE_DIR_*`) は後段の
`campaign_options` にしか渡っていない。

gate へ渡す seam は commit `9a32ef5ca` (2026-09-09 02:36 JST、[T-2182]) で入った。
`git merge-base --is-ancestor 9a32ef5ca a173f0ab5` は rc=1 で、983020 の木には無い。

### 根拠 3 — owner TU の include 連鎖 (CCBench PIN `511c9538`、静的)

gate が preprocess する owner TU は `cc/silo/transaction.cc` (`_DEFINE_SPECS["BACKOFF_FIXED"]` の
`_SILO_OWNER`)。その include 連鎖は `cc/silo/include/common.hh` で二股になる。

- `gflags/gflags.h` と `glog/logging.h` を直接 include。これらは `find_package` が
  `CMAKE_PREFIX_PATH` から解決する。
- `../../../include/masstree_wrapper.hh` を include。これがさらに `<config.h>` `<compiler.hh>`
  `<kvthread.hh>` `<masstree.hh>` `<masstree_insert.hh>` ほかを include する。これらは FetchContent の
  source dir から来る。**`config.h` は masstree 事前構築が生成する成果物であり、source を置くだけでは
  存在しない。**

## 帰属

983020 で preprocess が落ちた直接の原因は、**gate 専用の configure に FetchContent の offline 指定が
渡っていなかったこと**である。env の `CMAKE_PREFIX_PATH` は D1773 (d) により export 済みだったので
gflags/glog は `find_package` で解決できた。渡っていなかったのは `-DFETCHCONTENT_BASE_DIR` と
`-DFETCHCONTENT_SOURCE_DIR_*` であり、計算ノードには外部ネットワークが無いため gate 専用 build root に
masstree source も生成済み `config.h` も無く、owner TU の `-E` が `masstree_wrapper.hh` 経由の
header を解決できなかった。

**依頼が疑っていた「計算ノードに system gflags が無いこと」は、この失敗の直接原因ではない。**
gflags/glog が owner TU の include 連鎖に入っているのは事実だが (根拠 3)、その供給は job body の
prologue と export 済み `CMAKE_PREFIX_PATH` で既に足りていた。

**この帰属はコードと成果物からの帰属であって、捕まえた stderr ではない。** 983020 の preprocess
stderr は isolate worktree (`/scr`) と共に job 終了時に消えており、復元できない。旧 commit を
再走させても測るのは既に置き換わった producer なので、別命題になる (絶対規律 7)。
**この「本文が残らない」性質こそ本 wave が実装で塞いだものである。**

なお `/usr/include/gflags` が不在で `pkg-config --exists gflags` が rc=1 であることは
ログインノードでも実測した (2026-09-09)。ただしこの 2 点だけでは「compiler から gflags が
不可視」までは言えない (別 prefix・`PKG_CONFIG_PATH`・module・sysroot・CMake config package を
揃えて検査していない)。段 3 レンズ A の指摘に従い、主張はこの 2 点に限定する。

## 実装 (証拠採取の配線)

| 項目 | 値 |
|---|---|
| 統合 commit | `88f57e008` (Codex author gpt-5.6-sol xhigh / 親 integrator) |
| merge commit | `c11bd8a60` (main `3258c2409` を取り込み、docs のみで編集面と非競合) |
| 変更 file | `orchestrator/campaign/condition_meaning_gate.py`、`orchestrator/campaign/p3_s4_loop.py`、`orchestrator/tests/test_condition_meaning_gate.py`、`orchestrator/tests/test_p3_s4_loop.py` |
| 不変 | gate の受理集合・reason code 語彙・admission 判定・rc・green 経路の bytes、`tools/pegasus/` 一式、`policy.json`、`admission_registry.json` |
| 段構成 | 段 2・3 の子と段 6 レビュー 2 本を立てた (正しさ防壁に触るため軽量版にしない、DW-C00) |

- `_run_process` が送出する失敗 detail へ、実行しようとした argv を載せる。500 byte を超える argv は
  切り詰め、切り詰め時は切り詰め前 argv 全体の sha256 を印に含める。整形関数は決して例外を送出せず、
  整形できないときは固定の代替文字列を返す。
- `_require_condition_gate` は拒否時にだけ supply / meaning の arm record と admission の
  canonical JSON を `IZANAGI_S4_EVIDENCE_ROOT` 配下へ保存する。file 名は arm 名と内容 digest から作り、
  同じ directory 内の一時名へ書いて `fsync` してから `os.replace` で公開し、親 directory も `fsync` する。
  保存のどの失敗も元の gate 拒否を置き換えない。環境変数が未設定・空なら保存を省略する。

設計判断は decisions の `condition-gate-rejection-evidence` (番号は fold が付ける)。

## 段 3 / 段 6 の所見と裁定

段 3 (2 レンズ、`verbatim/s3-lensA.md`、`verbatim/s3-lensB.md`) と段 6 (2 レビュー、
`verbatim/s6-reviewA.md`、`verbatim/s6-reviewB.md`) の所見は `verbatim/s4-adjudication.md` に裁定表がある。

**可逆最小正規化 (DW-S07):** `verbatim/s6-reviewA.md` は逐語コピーが `git diff --check` の行末空白に
抵触する 2 行を持つため、行末の空白 / tab を除去した (可視文字不変)。原文 sha256
`5c4e841f8d035f76f9761366a3ed11d18cdc4125f2aa0cb293edec6260511c73` (8006 bytes)、正規化後
`0cc2c04dfe1664a009b68eb581bde1b8d6cec966b6cfb5b3ecc0474d227a8231` (8002 bytes)。復元は当該 2 行の
末尾へ半角空白 2 個を戻す。`diff -w -B` で原文と一致する (実測 rc=0、2026-09-10)。他の逐語 8 本は無変更である。

- **段 2 の最大の誤り (両レンズが独立に指摘)**: 過去実走の凍結 evidence を「現行 producer の red record
  bytes を縛る consumer」と読み、依頼が明示していた argv 採取を自ら scope から落としていた。
  親が `git grep` で生きた consumer 0 件を実測して反証し、採用へ戻した。失敗台帳の
  `frozen-record-read-as-live-contract` (番号は fold が付ける)。
- **段 6 の最大の所見 (両レビューが独立に収束)**: 証拠 file の最終 digest 名を内容完成前に
  `open("xb")` で公開しており、途中 kill・容量不足・close 失敗で壊れた file が最終名で固定化され、
  同じ record の再試行が `FileExistsError` で修復不能になる。一時名 + `os.replace` + 親 dir fsync へ直した。
- **refuted**: `except Exception` を `except BaseException` へ変える案。
  `KeyboardInterrupt` / `SystemExit` / `GeneratorExit` の伝播は正しい挙動で、「拒否すべき variant を
  受理する」方向の破れではない (何も受理されない)。`SystemExit` を `RuntimeError` へ変換する方が誤り。
  `MemoryError` は `Exception` なので既存の境界で捕捉済み。
- **real・不採用 (scope 外、記録)**: job body が canonical 化した `evidence_root` を元の環境変数名へ
  再 export していない (相対 path で shell と driver が別 dir を指しうる)。
  `p3_s4_loop.py` の編集が B-4 projection closure の live hash を動かすこと (起動時に admission record を
  渡したときだけ発火し、repo に committed な record は無いので、closure member を編集する全 wave に
  共通する帰結である)。

## 変異 matrix

`tools/mutation_harness.py` (`--runner-mode dispatch --detached`、runner =
`tools/run_tests.py --force-dispatch orchestrator/tests/test_p3_s4_loop.py
orchestrator/tests/test_condition_meaning_gate.py -q -rf`)、統合 commit `88f57e008` の wave worktree で
実走した。probe (全件 SURVIVED 登録で観測 node を集める) → 期待 node を埋めた本走、の 2 段。
spec と台帳の要約は `mutation/`
(`mutation-spec-final.json` sha256 `2bef18c17463ab8376b67de9bb6bbaaf8a4cf562cf39cd836c2e2a1b31cc62ee`)。

| 結果 | 値 |
|---|---|
| baseline | PASSED (rc=0、247.3 秒) |
| probe | 9 変異、全件 SURVIVED 登録に対し MISMATCH 9 (= 全件が検出された)。観測 node を採取 |
| 本走 | 9 変異、**KILLED 9 / SURVIVED 0**、MISMATCH 0、matching 9/9 (期待 node 完全一致)、rc=0 |

**DW-M08 に従い、この 9 件は「受理集合を変えず構造化シグナルだけを pin する変異」= diagnostic
sensitivity pin として記録する。** 本 wave の変更は gate の受理集合を 1 bit も変えないので、
kill は「拒否すべき入力を受理しなくなった」ことではなく「失敗本文が失われる実装を検査が捕らえる」
ことを示す。

検出の帰属は 8 個の test node に分かれる。

| 変異 | 検出 node 数 | 帰属 |
|---|---|---|
| m01 rc 分岐が argv を落とす | 2 | 実 process 失敗の正例 + 切り詰め検査 |
| m02 stderr 分岐が argv を落とす | 1 | 実 process 失敗の正例 |
| m03 整形関数が再送出する | 1 | 整形失敗が元の拒否を保つ検査 |
| m04 切り詰めが全文 sha256 を落とす | 2 | 切り詰め検査 + 全文束縛検査 |
| m05 まったく保存しない | 4 | 保存の正例・負例 4 本 |
| m06 supply arm だけ保存する | 4 | 同上 |
| m07 最終名へ直接書く | 2 | 途中失敗で最終名も一時 file も残さない検査ほか |
| m08 親 directory の fsync を落とす | 1 | 保存の正例 |
| m09 detail 不在分岐が None を出す | 1 | 保存の正例 |

## 焦点走と受入

- 焦点走 1 回目は **rc=16 `queue-wait-timeout`、`child_started=false`** = テストが 1 行も走っていない
  infra 失敗だった (差分に帰属しない)。D612 の opt-in 上書き
  (`IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=3600` / `IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE=600`) を
  投入 script に入れて張り直した。
- 焦点走 2 回目 (fix 後、統合 commit 前): **rc=0、534 passed / 0 failed**
  (`test_p3_s4_loop.py` + `test_condition_meaning_gate.py` + `test_plain_runner_coverage.py`)。
- 受入全走はこの記録 commit を含む最終 tip に対して land の前に 1 回走らせる (DW-O18/O26/O27)。
  結果は記録 commit の後に確定するため本 README には書かない。受入 receipt と land 出力は job dir
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2449-s4loop-gate-evidence/` に残り、要約は wave 終端の
  報告と worklog エントリ (fold 後) に書く。

**受入台帳 (`orchestrator/tests/acceptance_duration_ledger.json`) は更新していない。** 新 test は既存
2 file へ足したので新規 test file は無く、台帳は `conftest.py` が読む scheduling hint で、未登録 nodeid は
unknown 扱いになる fail-soft 設計である。登録には JUnit 実走をもう 1 巡 dispatch する必要があり、
得られるのが scheduling の精度だけなので本 wave では見送った。

## 本 wave が計算ノードへ投入しなかった理由

根拠 1 が、本 wave の base と同一 bytes のコードで gate 通過を計算ノード上で既に示している。
本 wave の変更は gate が **拒否したときだけ** 発火する診断であり、green 走行では 1 行も通らない。
同じ答えを得るためだけに混雑した queue へ 1 本足すのは「レコード数・実験スケールを無造作に大きく
しない」(絶対規律 4) に反し、`DW-G01` の「最安の生死確認」は姉妹 wave が既に済ませている。
投入したのは焦点走・変異走・受入全走の dispatch だけである。

## ユーザー裁定パッケージ

1. **`_run_process` の「rc=0 でも stderr が非空なら失敗」規則は configure に対して脆い。**
   CMake が新しい警告を 1 行出すだけで gate が `configure-failed` になる。実際 983020 と 988516 の
   双方の `job.stderr` に `Manually-specified variables were not used by the project:
   CMAKE_C_COMPILER` が出ている (別段のものだが、gate の configure が同種の警告を出せば拒否になる)。
   規律 2 を緩めずにこの脆さを扱う方向 — configure に限った警告 allowlist / 別 reason code /
   現状維持 — の裁定が要る。
2. **次の関門は `trace-parse-error` である。** 段 4 loop は gate を越えたが、evaluate で
   `abort: trace-parse-error` になり `0 committed / 1 aborted` で終わる。計算ノードでの試行台帳は
   依然 0 行のままである。別タスクとして起票すべきである。
3. **同じ「record を作って捨てる」形は兄弟 driver にもある** (`p3_kickoff.py`、`p3_s4_loop_sort.py`、
   `backoff_sweep.py` ほか)。`DW-G03` (族一般化には独立 2 例) により本 wave では一般化しなかった。
   独立 2 例が出たら制度化を裁定する。
4. **job body が canonical 化した `evidence_root` を元の環境変数名へ再 export していない**
   (`tools/pegasus/p3_s4_loop_pegasus.sh`)。相対 path が渡ると shell と driver が別 directory を
   指しうる。job body の変更は D1773/D1801 の契約テストに触れるため裁定が要る。

## 段 8 (自己改善) の結果

候補は 3 件出た。

1. **失敗台帳の恒久対応を `DW-O09` へ収容する** — 「hit した pin が生きた契約か過去実走の
   provenance 記録かを分ける」の 1 行。**入らなかった。** 同節は 992 bytes / 上限 1000 bytes で、
   必要な約 110 bytes の headroom が無い。予算のために他の安全義務を削るのは
   `docs/skill-self-improvement.md` が明示的に禁じているので削らなかった。D782 の梯子でいう
   「収容できなかった実測 1 例」として記録する。恒久対応の正本は失敗台帳側に残る。
2. **焦点走 script に D612 の opt-in 上書きを最初から入れる** — 本 wave でも書き忘れて焦点走を
   1 巡失った。同型は既に記憶側に記録があり、docs 側 (`DW-O18` 997 bytes / `DW-O26`) も予算満杯で
   収容できないことが過去 wave で実測済みである。本 wave は新しい情報を足さないので、
   候補の再掲に留める。
3. **`tools/pegasus/README.md` §7 の `THIRDPARTY_SOURCE_ROOT` 実例が腐っている** — 過去 wave の
   submit-tree 配下を指しており、その checkout は既に無い。dev-wave の入口・reference ではなく
   製品側 docs なので本契約の routing 対象外とし、次の一手 (`pegasus-readme-s7-stale-thirdparty-path`)
   として起票した。

段構成・実装子権限・正しさ防壁・裁定境界・予算の変更は実装していない。

## 次 wave の出発点

- `trace-parse-error` の帰属と修正 (裁定パッケージ 2)。段 4 loop の compute 実走を 1 件でも
  committed にするには、次はここを開ける必要がある。
- 裁定パッケージ 1・3・4 はユーザー裁定待ち。
