# 段 4 裁定 (R5 closure wave) + 変異事前登録

段 3 の敵対相談 2 本 (レンズ A = 正しさ境界、レンズ B = 実効性・変異帰属) はともに **NO-GO**。
親は下記のとおり real/refuted と採否を裁定し、plan v2 を確定する。

## 1. 前 wave の must-fix 根拠に対する裁定 — 大半が refuted

### [裁定 1] C1-a の成果物影響は **refuted**。所見自体は real だが severity を下げる

- 根拠 (B-1/B-2): resume は `job_id_normalized` を submit-receipt から採る (`test_dispatch.py:6576`)。
  matched candidate から実際に採るのは `execution_hosts` (`:6587-6592`) と `identification_source`
  ラベル (`:6601-6603`) だけで、monitor へ渡る job id は candidate 由来ではない (`:6808`)。
- さらに wrong-group な matched WAL は製品が書けない (唯一の書き手 `:4852-4887` は
  `parse_qstat_candidates(..., expected_group=policy.account)` を通った candidate しか載せない)。
  WAL は hash chain (`:454-477`) なので行単位改竄も到達不能。仮に journal 全体を再構成しても
  `_validate_scheduler_lookup_chain:3864-3906` が raw qstat 受領書を再 parse して publish 時に拒否する。
- **裁定**: 前 wave と親 brief が書いた「wrong-group 既知 job が受理集合へ入り monitor/qdel の
  対象になり得る」は C1-a については **成立しない**。`DW-G05` により、成果物影響を書けない所見は
  must-fix にしない。**同一 WAL 行を 2 箇所が異なる強度で読む非対称**だけが real なので、
  fail-fast と対称性の回復として **低コストで採用**するが、受理集合の closure は主張しない。

### [裁定 2] monitor 経路の C2 は恒真に近い。非恒真な consumer は `:4404` だけ — **採用**

- 根拠 (B-4): `:5255` に到達するには毎 poll で `parse_qstat(..., expected_group=policy.account)`
  (`:5056-5061`) を通過済みである必要があり、accounting footer は `Request ID` も正規化比較済み
  (`:3238-3244`)。既存 test `test_pegasus_test_dispatch.py:1069-1090` が「wrong-group を見たら
  qdel → `CANCELED` / rc 125」を既に固定している。
- 非恒真なのは `validate_final_receipt_object:4404` (published/pending final の再検証) だけで、
  ここは monitor の qstat gate を経ずに accounting を読む。
- **裁定**: `validate_nqsv_accounting` の `expected_group` 化は **採用**。ただし
  **`:4404` を実際に被覆する test を同時に足すことを必須条件とする** (M3 の再照準、B-5)。
  `:5255` 側は「冗長な整合 assert」と明記し、closure の主張には数えない。

### [裁定 3] 実在する系列は B-3 — **本 wave の主変更に採用**

- 根拠 (B-3): `_validate_submit_object:2601-2623` は job id の内部整合
  (`normalize_job_id(raw) == normalized`) しか見ず、hash 束縛済みの `qsub.stdout` /
  `qsub-result.json` と一切照合しない。resume は `:6575-6576` でその値をそのまま採用し、
  `:6619` の qsub.stdout 再 parse は `qsub_raw is None` のときしか走らない。
- 到達系列: submit-receipt.json に任意の NQSV id が入ると、resume は `:6717` (cancel-intent) /
  `:6769` (unknown completion) で **qstat を一切経ずに他人・他 group の job へ qdel を出す**。
  final-receipt の `job_id_normalized` に他人の id が入り封印される。
- **裁定**: 前 wave が事前登録した成果物影響 (wrong-group job の monitor/qdel) を実際に達成する
  唯一の変更はこれである。**scope 内の主変更として採用**する。scope 外へ送らない理由は、
  これが R5 の「同一識別子の consumer 閉包」そのものであり、代替すると事前登録した成果物影響が
  未達のまま「closed」と記録されるため。

### [裁定 4] 変更 D (per-job qstat gate) は **不採用**

- 根拠 (A-1): 非可視 (`parse_qstat:3001-3007` の rc≠0 / timeout / output_limited / signal) でも
  qdel 2 分岐で raise するため、cancel-intent resume の常態 (job 消失 = qstat rc≠0) で final を
  封印できない。gate は状態を持たないので再 resume でも同じく raise し、当該 dispatch は
  **永久に封印不能**。`_completed_dispatch:1155-1157` が False を返し続けるので
  `_prune_retention:1188-1193` の victim にもならず、`max_retained_dispatches=8` に達した時点で
  **新規 dispatch まで起動不能**になる。
- 根拠 (A-2/B-8): 疑似コードが挿入位置に存在しない `cancel_intents_present` を参照する = NameError。
- 根拠 (A-3/B-9): 「非可視は通す」に直せば、実運用の wrong-group が落ちる主経路
  (他 group への `qstat -f` は権限で rc≠0 → not-visible → monitor visibility timeout → qdel) は
  **閉じない**。gate が閉じるのは「可視かつ Group Name 読取可」の部分集合だけ。
- **裁定**: 正しさを買わずに liveness を売るため **不採用**。裁定 3 (B-3) が新 scheduler 呼出・
  新 WAL event・既存 test script 更新なしで到達可能な risk を閉じる。gate の設計は裁定パッケージへ。

### [裁定 5] 変更 C-1 / C-2 は **不採用**

- 根拠 (A-10): C-1 (2 sha filter) は `_validate_scheduler_lookup_chain:3799-3814` が全
  `scheduler-lookup-*` event の 2 sha 一致を既に要求するため受理集合を変えない。
- 根拠 (B-6/M8/M9): C-1/C-2 を殺す変異が登録できない (fixture の matched は常に 1 行)。
- **裁定**: 純増検出力ゼロにつき **落とす**。C-3 の `candidate_normalized != normalized` も
  選択 filter により恒偽 (B-7) なので落とす。

### [裁定 6] 変更 G (P2 不採用) は **維持**、ただし根拠を訂正

- 根拠 (A-9): plan の「policy を持たない呼出元が 4 つ」は事実誤認。`:6108-6122` と `:6181-6195` は
  `cancel_job(..., policy=policy, ...)` を同スコープで呼んでおり policy を持つ。真に持たないのは
  `_completed_dispatch:1149` の 1 箇所だけ。
- **裁定**: 結論 (`validate_final_receipt_object` にシグネチャを足さず、同関数が既に持つ
  snapshot 束縛済み `bound_policy` を使う) は **維持**。根拠は「1 caller + 2 seam 実装 +
  3 死引数」へ訂正して記録する。
- A-8 (retention 破壊) は認識する。ただし「不正な final は `_completed_dispatch` で False になり
  prune victim から外れる」のは**既存の設計性質**であり、本変更は理由を 1 つ足すだけ。
  かつ裁定 2 により wrong-group accounting の実在系列はほぼ無い。**nit として記録**する。

## 2. 親自身の実測主張に対する裁定 — L1/L2 を撤回

### [裁定 7] L1 (PYTHONPATH) の「過剰拒否」判定を **撤回**

- 根拠 (A-16): `_PLUGIN_ENV` 非空拒否が守るのは子へ渡す env ではなく、**その検査を実行している
  login 側 interpreter 自身が import 汚染下でないこと**である。`tools/run_tests.py` /
  `test_dispatch.py` / `orchestrator/*` は検査時点で既に汚染 `sys.path` 下で import 済みであり、
  除去は遡及しない。緩めれば「closure を計算する dispatcher 自身が別実装だった」を検出できなくなる。
- 「既定 shell では正規手段が存在しない」も、親自身の L2 実測が反証している (L1 の壁は越えている)。
- **裁定**: 安全側の**正しい拒否**。運用は `env -u PYTHONPATH` を正規手順として runbook へ書く
  (裁定パッケージ)。dispatcher は変更しない。

### [裁定 8] L2 (nested submodule) の「過剰拒否」判定も **撤回**

- 根拠 (A-17): `:1617-1650` は `-` 拒否の上で各 repo の `ls-files --cached` を全走査し、
  snapshot に入る総 bytes / 件数を数える。未初期化のまま通すと closure が実ツリーと食い違い、
  `max_total_bytes` / `max_files` 予算も manifest closure も破綻する。緩和は frozen bytes 軸の
  受理集合**拡大**であり、brief の不変条件に正面から違反する。
- **裁定**: 正しい拒否。直すべきは契約側 (`DW-O08` を `--init --recursive` にするか、
  dispatcher 利用時の前提として runbook へ書くか) であり dispatcher ではない。裁定パッケージへ。

### [裁定 9] L3 の未帰属 3 赤を特定した (両レンズの blocking 前提条件を解消)

`test_pegasus_test_dispatch.py` は base `72e3800` に存在しない新規 file (`A`) であり、実測 B の
比較対象に入っていなかった。baseline2 の失敗本文から特定した内訳:

| test | 失敗理由 (逐語) |
|---|---|
| `test_post_terminal_combined_spool_growth_cannot_return_child_result` | `DispatchError: test dispatch aggregate bounds are inconsistent` |
| `test_signal_during_qsub_recovers_exact_id_and_qdels_once` | `ControllerSignal: controller received signal 15` |
| `test_sigterm_after_submit_qdels_once` | `ControllerSignal: controller received signal 15` |

前者は wave 自身の新 test が `max_spool_bytes: 32` を override し、wave 自身の `load_policy` の
aggregate bounds 検査が拒否する自己不整合。後 2 者は `ControllerSignal` が
`submit_and_monitor` で期待どおり変換されず素通しする。**いずれも U2 実装の自己不整合であり
R5 とは独立**。

### [裁定 10] 15 赤は本 wave の scope 外。ただし受入の主張範囲を限定する

- 内訳と根本原因: s8b 10 件 = `buildcache.py:29-32` が module import 時に
  `<repo>/tools/pegasus_policy.py` を trusted policy source として読むのに、T-080 E2E fixture の
  `required` 集合 (`test_s8b_oracle_driver.py:585-600`) に同 path が無い **consumer 取り残し**
  (A-15 が「commit しても `required` は変わらないので未 commit 状態は原因でない」と静的に確定)。
  `test_run_tests_task_run.py` 1 件 = `tools/run_tests.py:849` の `AttributeError`。
  `test_pegasus_tools.py` 1 件 = `certify_calibration.sh` に無い `PERF_CANDIDATES` 断片の期待。
  `test_pegasus_test_dispatch.py` 3 件 = 裁定 9。
- **裁定**: いずれも U2/U3 の inherited defect であり R5 closure の scope 外。**修理しない**。
  T-193 (二重正本) の裁定材料として裁定パッケージへ返す。
- 受入は**対象 file 単位の before/after 比較**で行い、suite 全体の緑は主張しない (B-14)。

### [裁定 11] L4 の受入表現を限定する

製品 dispatcher (L1/L2 により login から起動不能) を通していないため、受入で主張できるのは
「計算ノード上の pytest 集計値」までである。dispatcher の submit→lookup→monitor→accounting→
final publish の end-to-end、hash chain、retention、**本 wave が触る `Group Name` 束縛そのもの**は
主張しない (B-15)。台帳へは「製品 dispatcher 未経由・受入 script 非 commit」を併記する。

## 3. plan v2 (確定)

実装単位は **U5 の 1 つ**。編集面は `tools/pegasus/test_dispatch.py` と
`orchestrator/tests/test_pegasus_test_dispatch.py` の 2 file のみ。

- **E1 (裁定 3、主変更)**: resume が使う submit-receipt の `qsub_request_id_raw` /
  `job_id_normalized` を、hash 束縛済みの `qsub.stdout` (= `qsub-result.json` の受領書) の
  parse 結果と exact 比較して fail-closed にする。qstat を呼ばず、新 WAL event も足さない。
  `qsub.stdout` が clean return でない (parse 不能) 場合は現行の SUBMIT_UNKNOWN 経路を変えない。
- **E2 (裁定 2)**: `validate_nqsv_accounting` に keyword-only 必須 `expected_group` を足し、
  `:3217` を捕獲群化して `Request ID` 照合の直後で exact 比較する。呼出は `:5255` (`policy.account`)
  と `:4404` (`bound_policy.account`) の 2 箇所。`validate_final_receipt_object` のシグネチャは
  変えない (裁定 6)。
- **E3 (裁定 1)**: `lookup_scheduler_job:4733-4751` の candidate 検査述語をヘルパへ切り出し、
  resume の matched WAL 選択 (`:6587-6592`) から同じヘルパを呼ぶ。**逐語 move のみ**とし、
  2 sha filter・uniqueness raise・raw 比較は足さない (裁定 5)。
- **テスト**: 下表の変異を殺す red と、過剰拒否を検出する positive control。
  red は `submit_and_monitor` を経由してはならない (B-12: `:6177-6220` の `except BaseException` が
  sentinel を rc 125 に化かし偽の緑を作る)。

## 4. 変異事前登録 (`DW-M01`)

各変異は「その位置より前に同じ入力を拒否する検査が無いこと」を確認済み。
本 wave は受理集合を縮小するため、承認外の過剰拒否を検出する正例も登録する。

| ID | 単一変異 | 期待する赤 (単一理由) | 過剰拒否を検出する正例 |
|---|---|---|---|
| R1 | E1 の id 照合を削除 | receipt の id が qsub.stdout と食い違う resume が qdel/monitor へ進む | 正規 receipt の resume は現行どおり受理 |
| R2 | E1 の照合対象を `job_id_normalized` だけにする (raw を見ない) | `0:` 接頭辞違いの raw が素通り | 同一 raw の正規 resume は受理 |
| R3 | E2 の group 照合を削除 / `!=` を `==` に反転 | wrong-group accounting footer が受理される | same-group footer は `CHILD_RESULT` で受理 |
| R4 | E2 の `:4404` 束縛を `bound_policy.queue` に差替 | 実 FS resume の final 再検証が same-group を拒否 | same-group final は再検証を通る |
| R5 | E2 の `:5255` 束縛を `policy.queue` に差替 | monitor が same-group を `ACCOUNTING_INCOMPLETE` にする | same-group monitor は rc 0 |
| R6 | E3 のヘルパ内 `group_name != policy.account` を削除 | wrong-group candidate が resume で素通り | same-group candidate は受理し monitor 1 回 |

- **R4 は必須**: `:4404` は現行 test で無被覆であり (B-5)、これを殺す test を足さない限り
  E2 の実効位置は無検証のまま出荷される。最短被覆は「実 `PathMonitorFilesystem` で monitor を
  完走させて `final-receipt.json` を作り、同じ dir に `resume_dispatch` を呼ぶ」。
- **R5 は冗長 gate の診断 pin** として記録し、closure の証拠には数えない (裁定 2、`DW-M08`)。
- 登録しない変異: 変更 C-1 / C-2 / C-3 後半 / 変更 D は裁定 4・5 により実装しないため。

## 5. 裁定パッケージ (ユーザーへ返す)

1. **T-193 の二重正本**: main (`aa67805`) の `site_policy.py` + `dispatch_compute.py` と、本 branch の
   `pegasus_policy.py` + `test_dispatch.py` + `submit_tests.py` + `run_tests_job.sh` は同趣旨。
   **本 branch は現在 15 赤**であり、うち 10 件は自 wave が入れた consumer 取り残し。
   main 側は T-192 で計算ノード 4012 passed の受入実績がある。どちらを正本にするか。
2. **R10/R11 (裁定 7/8)**: dispatcher の 2 つの拒否は正しい。運用手順 (`env -u PYTHONPATH`、
   `git submodule update --init --recursive`) を runbook / `DW-O08` のどちらへ書くか。
3. **変更 D の gate 設計** (裁定 4): 「非可視でも封印を奪わない」形の group gate を後続 wave で
   設計するか、monitor の visibility timeout → 未検証 qdel を既知欠落として receipt に残すか。
4. **15 赤の修理** (裁定 10): 本 branch を正本にするなら U2/U3 の自己不整合 5 件と
   fixture closure 1 件を閉じる wave が要る。
