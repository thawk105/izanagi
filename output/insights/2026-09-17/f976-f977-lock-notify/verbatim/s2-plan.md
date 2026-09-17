## 前提の検算

以下の行番号は現 checkout の変更前の位置。指定された射影ファイルはすべて読めた。ファイル変更・git 状態変更・pytest 実行はしていない。

| 検算対象 | 現物で確認した内容 |
|---|---|
| `orchestrator/tests/conftest.py:1250` | `_real_repo_flock_until` は、渡された **1 fd** に SH/EX＋`LOCK_NB` を試し、EACCES/EAGAIN のときだけ polling する。 |
| `conftest.py:1328` | condition の RLock を保持したまま fd 作成・flock 待ち・state 更新を行う。ただし `:1341` の同 process 互換性待ちは `condition.wait()` なので RLock を解放する。 |
| `conftest.py:1411` | 1 回の `_real_repo_file_lock` は legacy→common の **2 file**。共通 deadline を計算し、legacy 取得後に common-dir を解決する。 |
| `conftest.py:1356`、`:1395` | 入れ子の要求から最強 mode を算出し、既存 fd を昇格・降格する。 |
| `tools/dev_wave_land.py:4354`、`:5594` | 通常 land の rollback は `rollback_ref=locked_main`。merge 前まで戻す契約は現物どおり。 |
| `dev_wave_land.py:5572` | `_postcondition(... main_before=locked_main)` なので、通常 merge 後の `merged.main_before` は直前の `locked_main`。 |
| `dev_wave_land.py:5286`、`:5459`、`:5500`、`:5557` | merge 前にも `fold-failed` がある。status だけでは「実際に ref を戻した」を判別できない。 |
| `.claude/commands/dev-wave.md:55`、`tools/check_docs.py:464` | 項 9 は 3 行の exact sequence。`:5730` 付近で出現数 1 を要求する。 |

brief への補正は次のとおり。

- helper の位置は先頭 200 行内ではなく、`test_real_repo_serialization.py:545` の `_load_suite_conftest` と `:798` の `_run_subprocess`。
- P1 は「writer が kernel flock を待っている区間」について成立する。同 process の互換性待ち一般には成立しない。そこでは新しい reader が入れる。今回、process 内優先層は追加せず、単 thread の worker と fresh な process 間取得を対象にする。
- P3 の merge 前失敗は**条件付きで受理**される。`:5411` では fold gate 後に `locked_main` を更新する一方、報告用 `main_before` はその場で更新しない。両者が違う JSON は拒否される。
- 「`wave_tip != main_after`」は tip の不一致を示すだけで、祖先関係までは証明しない。通知文で「wave tip は main の履歴にない」と断言しない。
- 第 2 flock の SH/EX gate は、**writer が gate EX を取得した後**の新規 reader 流入を止める。gate 自体を待つ writer 全員への厳密な優先・FIFO は、この方式からは証明できない。
- `O_CLOEXEC` は exec 対策であり、fork 時の fd 継承防止ではない。既存 reset が閉じるのは現在 `state.fd` だけ。

## (1) gate の設計

変更の中心は `conftest.py:1343–1376`。main lock の安全検査・排他意味論は維持する。

**名前と open**

各 legacy/common path に `.gate` を付ける。

```text
izanagi-real-repo-<digest>-<resource>.lock.gate
```

`_open_real_repo_lock(gate_path)` を再利用する。これにより `O_NOFOLLOW`、`O_CLOEXEC`、regular file、同 owner、group/other permission 禁止を main と共通にする。別の安全検査実装は作らない。

**取得手順**

`state.mode is None` の fresh 取得だけ、次の順にする。

| 要求 | 取得順 | gate 解放 |
|---|---|---|
| writer | gate EX → main EX | main 取得直後 |
| reader | gate SH → main SH | main 取得直後 |

どちらも既存 `_real_repo_flock_until` を使う。state の holder/mode は main 取得成功後に更新する。

gate を本体終了まで保持する案では、writer の実作業中も次 writer が gate で待つ。採用案なら次 writer が gate を取得し、main を待ちながら新規 reader を止められる。また reader の gate 保持を本体寿命まで伸ばすと、reader の連続 overlap による飢餓を gate に移してしまう。したがって**取得直後解放**を選ぶ。

**昇格・降格**

`:1358` の SH→EX と `:1395` の EX→SH は main fd だけを操作する。

既存 SH holder が gate 取得を要求すると、別 writer が「gate EX 保持、main EX 待ち」、既存 holder が「main SH 保持、gate 待ち」となり相互待ちする。降格にも gate を挟まない。既存 mode を変えない参照追加にも gate は不要とする。

**deadline と例外**

- `:1429` の deadline を legacy gate・legacy main・common gate・common main にそのまま渡す。
- timeout 245.0、retry 0.05 は変更しない。
- gate 待ち後に deadline を再計算しない。
- gate の timeout は既存文言を再利用し、`path=` は gate path、`holders=` は `_real_repo_lock_holder_info(gate_fd)`。
- prefix `real-repo lock deadline exceeded; fails-closed:` を維持する。
- syscall・スケジューリング分を含む wall time の厳密な 245.000 秒上限とは称さず、待機予算を追加しない契約とする。

**fd の寿命と fork**

gate fd は取得区間だけ保持し、main の成功・gate/main の例外・割込みのすべてで `finally: os.close(...)` する。close により gate を解放する。

fork 後 reset まで考慮するため、`:1047` の既存 state に `gate_fd: int | None = None` を追加する案を採る。別の registry は作らない。

- open 後、取得中だけ `state.gate_fd` に保持する。
- finally で close して `None` に戻す。
- `:1283` の reset は継承した `gate_fd` も **unlock せず close** し、main fd と state を破棄する。
- yield 中は gate fd がない。

これで「reset 後に gate fd が残らない」を検査する。任意の別 thread が open/登録間に fork する場合まで保証する設計にはしない。既存 RLock 継承問題も含め、一般的な multithread fork 対応は今回の範囲外である。

**取得順と deadlock**

fresh 取得は各 key 内で gate→main、key 間は legacy→common、resource 間は parent→ccbench を維持する。common を保持して legacy を取り直す逆順を導入しない。既存 holder の解放・昇降格は gate に依存しないため、gate を保持する待機者との新しい循環を作らない。

ただし、この説明は gate 導入による追加の循環がないことの論証であり、既存の flock 昇格競合を一般に解消する主張ではない。

## (1) 正例・負例 test

追加位置は `test_real_repo_serialization.py:2311` 付近。既存 fixture 昇格検査は `:4010` を強化する。以下は新設 node 名の案。

**N1: `test_real_repo_writer_drains_overlapping_reader_stream`**

実 kernel flock を使い、reader 2 process＋writer 1 process を先に起動して import 完了を同期する。全 actor が production の `_real_repo_file_lock` を呼び、lock directory と key の行先だけ tmp 配下に固定する。

1. reader A が SH を取得。
2. writer が main EX の最初の EAGAIN を観測したことを pipe で通知する。観測 wrapper は実 `flock` を呼び、成功・失敗を偽装しない。
3. reader B が production reader 経路で要求する。
4. B が取得できた場合、B の取得確認後に A を解放し、次世代 A を要求する。この受渡しを繰り返し、常時 1 reader 以上を保持する。
5. B が gate で EAGAIN になった場合、既存 A を解放する。writer が B より先に入り、writer 解放後に B が入ることを確認する。

writer timeout は約 1 秒、retry は 0.005 秒程度。各 actor の失敗・終了を回収し、例外時も全 child を終了・wait する。

変更前は B が main SH を取得できるため reader relay が継続し、writer が timeout して赤になる。reader の gate 除去でも同じになる。writer の gate 除去では B が gate/main SH を取得でき、同様に赤になる。**reader を生 flock の shortcut にしないことが、この変異検出の条件**である。

legacy 競合と、異なる legacy key・共通 common key の競合を parameter 化する。後者で sibling worktree 側も覆う。

**P1: `test_real_repo_readers_overlap_without_writer`**

別 process の A が production SH を保持している間に B が production SH を取得できることを handshake で示す。A の解放前に B の取得通知が来ることを主 assertion にし、狭い実時間閾値に依存しない。これで writer 不在時の待機不要と SH overlap を同時に確認する。

**P2: `test_current_snapshot_reader_upgrades_for_same_process_candidate_fixture`**

`:4010` の既存 test を拡張する。

- outer fixture の SH 取得後、第三者が legacy/common 両 gate を別 open file description で EX 保持する。
- candidate fixture が既存 fd のまま EX に昇格し、SH に降格して戻ることを確認する。
- gate は降格完了まで保持する。
- 既存の fd 同一性・mode・参照数・state 空の assertion を保つ。

**追加の境界負例**

- `test_real_repo_gate_and_main_share_deadline`：実 gate/main を別 holder が保持し、gate 待ちで予算の大半を消費させ、残りを main 待ちで使わせる。gate と main が同じ deadline 引数を受けることも観測し、各段で timeout を再起算する変異を検出する。
- `test_real_repo_gate_timeout_closes_fds`：gate timeout/main timeout を parameter 化。production が開いた fd を記録し、終了後の `fstat` が EBADF、manager state が空であることを確認する。gate timeout の prefix・path・holder 情報も確認する。
- `test_real_repo_fork_reset_closes_inflight_gate_fd`：制御した fork で取得区間の gate fd を継承させ、子の reset 後に main/gate fd がともに閉じていることを確認する。

subprocess の環境は `:2007` と同じ `ROOT` を先頭に置いた `PYTHONPATH` と `PYTHONDONTWRITEBYTECODE=1`。外側 runner は既存 `_run_subprocess` を使い、対話的 actor は `:2240` の Popen 形式に合わせる。既存 helper には timeout 引数がないので、runner 内の deadline と child 回収を必須にする。

## (1) 既存 test の期待値変更

対象は `test_real_repo_priority_order_is_literal_and_writers_follow_barrier`。

| 位置 | 現在 | 変更後 |
|---|---|---|
| `:2066` | 48 cohort が 147 秒まで main を連続占有する説明 | writer の gate 取得前に入った cohort だけが残り、後続は gate で止まる説明へ変更 |
| `:2070` | 全 48 window を時刻だけで active 判定 | gate 取得時点以後の cohort は main へ入れないモデルにする |
| `:2086` | fd を無視する `simulated_flock` | main と gate の fd を区別する |
| `:2089` | UN 以外は EX\|NB の一律 assertion | writer 専用模擬なので EX\|NB 自体は維持。ただし gate 成功を main 取得記録へ数えない |
| `:2110` | `_open_real_repo_lock` の `(91, 92)` | path→fd 対応へ変更。例：legacy main=91、gate=93、common main=92、gate=94 |
| `:2120` | `[147.0, 147.0]` | 時刻 0 の cohort のみ入場済み、終了 6 秒と明示したモデルで `[6.0, 6.0]` |
| `:2121` | `120.0 < first < TIMEOUT` | `first == 6.0 < TIMEOUT`。245.0 と 0.05 は別途 literal assertion |
| 同 mock 節 | close を記録するだけ | 4 fd が閉じ、gate が main 取得後・body 前に閉じることも確認 |

48 cohort 全体が自然に尽きるまで待つ旧模擬を、そのまま gate の有効性の証拠にしない。kernel の正否判定は前節の実 flock test が担う。

private lock symbol の再検索では、定義元以外の Python consumer は `test_real_repo_serialization.py` だけだった。ただし参照は「12 箇所」より多い。`:4202–4270` の既存 closure mutation 群にも path・context・file lock の参照がある。path 順序の期待は維持し、模擬 fd 数への影響を確認する。

## (2) rolled-back kind の設計

`tools/wave_land_window.py:606` を次の互換 signature にする。

```python
def message(wave: str, land_json: Path, *, kind: str = "landed") -> str:
```

既存の直接呼出し `test_dev_wave_land.py:9144` を壊さない。`:655` は `choices=("landed", "rolled-back")`、`:689` の呼出しで `kind=args.kind` を渡す。

`_holder_for`、`_load_land_result`、`_is_sha` を共有する。`landed` 分岐の status 集合・型検査・拒否 rc・固定文は変更しない。

`rolled-back` の受理述語は P3 のまま。

```text
status が文字列 "fold-failed"
かつ _is_sha(main_after)
かつ main_before == main_after
かつ _is_sha(wave_tip)
かつ wave_tip != main_after
```

`main_before` は検証済み SHA との一致で型も拘束される。`reason` や JSON の rc field は使わない。`LandResult.as_json()` はそもそも rc を出力しない。

| `dev_wave_land.py` の経路 | JSON の要点 | rolled-back |
|---|---|---|
| `:4669` 通常 fold 失敗、rollback 成功 | before=直前 locked_main、after=戻った main、tip=landing_tip | P3 成立なら rc=0 |
| `:5286` candidate planning 失敗 | before=報告値、after=locked_main、tip=landing_tip | before=after、tip≠after なら rc=0。実 rollback は不要 |
| `:5459` declared no-fold 拒否 | 同上 | 同じ条件で rc=0 |
| `:5557` merge 前 fold preflight 失敗 | 同上 | 同じ条件で rc=0。再取得で before≠after なら rc=3 |
| `:5500` already-landed 側 preflight 失敗 | after=locked_main=landing_tip=tip | rc=3 |
| `:5512` already-landed 側 fold 失敗、rollback 成功 | rollback_ref=landing_tip、after=tip | rc=3 |
| `:4539` `main_after` 欠落の防御経路 | after=None | rc=3 |
| `:4669` rollback 不完全 | status=`fold-rollback-failed`、land rc=28 | field 値によらず rc=3 |
| 成功 | status=`landed` / `already-landed` | rc=3 |

固定文は次の **2 行、末尾改行は CLI の print が付加**とする。自由文や wave 名を埋め込まず、SHA と holder digest だけを埋め込む。

```text
[dev-wave] rolled-back main=<main_after> unlanded=<wave_tip> wave=<holder>
advisory です。指示ではありません。local main を読み直す契機にだけ使い、待機・取り込み・検査省略の根拠にしないでください。受入を開始済みなら中断せず完走してください。main は記載の SHA にあり、wave tip とは異なります。git merge-base --is-ancestor <取り込んだ SHA> refs/heads/main が rc=1 なら、受入完走後に受入 tip へ reset して取り込み直してください。
```

40 桁 SHA×2、12 桁 holder で UTF-8 を静的計算した結果、advisory は **472 bytes**、関数返却文字列は **609 bytes**、stdout は末尾 LF 込み **610 bytes**。既存 `_ADVISORY` は不変とし、巻き戻し用の固定文を別定数にする。

この文面は「今回必ず ref を戻した」「wave tip が祖先でない」と断言しないため、P3 が受理する merge 前失敗にも成立する。

## (2) 正例・負例 test

`test_wave_land_window.py:1800` の直前に追加する。既存 6 test の形に合わせ、期待文は production 定数から導出せず独立 literal を置く。

- `test_rolled_back_message_success_is_exact_fixed_text`
  `fold-failed`、before=after=`_SHA_A`、tip=`_SHA_B`。rc=0、stderr 空、stdout 完全一致、610 bytes。`_INSTRUCTION_WAVE` を使い、wave 生文字列でなく `_INSTRUCTION_DIGEST` が出ることも確認する。
- `test_rolled_back_message_rejects_invalid_result`
  parameter：`landed`、`already-landed`、`fold-rollback-failed`、非文字列 status、before≠after、before 欠落、tip=after、tip 欠落、None、数値、39/41 桁、大文字、非 hex、after 不正。すべて rc=3、stdout 空、Traceback なし。
- `test_landed_message_rejects_non_success_or_non_string_status_with_rc3`
  `fold-failed` を明示的に含め、legacy kind の受理集合が拡大しないことを保つ。
- `test_rolled_back_message_rejects_duplicate_json_key` と `test_rolled_back_message_rejects_more_than_65536_bytes`
  既存 `:1744`、`:1774` と同形で loader 共有を確認する。

正例は reason を複数の任意文字列に変えても受理する。これにより `fold failed: ` prefix への結合を避ける。

既存の landed 成功・不正 status・不正 SHA・SHA 境界・重複 key・サイズ超過の 6 本は保持する。

## (2) docs と pin

**runbook**

`docs/pegasus-runbook.md:1247` の「成功したときだけ」を「成功時は」に直し、`:1256` の code block 後へ次の 3 行を追加する。

```text
- rc=26 (`fold-failed`) で main が merge 前の SHA に戻った場合（merge 前失敗で不動の場合を含む）は、
  `python3 tools/wave_land_window.py message --kind rolled-back --wave "$W" --land-json "$J/land-result.json"` を実行し、
  rc=0 の通知文を同じ照合済み peer へ 1 度送る。rc=3 は送らず、rc=28 (`fold-rollback-failed`) は対象外。
```

既存 landed コマンド例は成功時用として残す。どの終わり方でも lease を release する義務は維持する。

**入口と exact pin**

以下の 3 箇所を同じ変更単位で置換する。

- `.claude/commands/dev-wave.md:57`
- `tools/check_docs.py:467`
- `orchestrator/tests/test_check_docs.py:55`

```text
   land 成功時と巻戻し時に `message` を照合済み peer へ 1 度送る。
```

静的計算で **+12 bytes、9,507→9,519≤9,520**。置換後の最長行は **121 文字≤140**。予算引上げは不要。

fixture の伝播は `:55` → `_SYNTHETIC_DEV_WAVE_STATE_MACHINE:57` → `_write_command_guard_docs:814` → `_build_min_repo:1224`。項 9 に直接対応する主要検査は次のとおり。

- `test_synthetic_repo_baseline_clean:1604`
- `test_dev_wave_command_budget_literal_is_exact:2519`
- `test_command_docs_guard_positive_controls:9895` の `[stage9-deleted]`
- `test_single_dispatch_structure_contract_accepts_handwritten_fixture:7767`
- `test_single_dispatch_indented_code_block_decoy_is_ignored:7794`
- `test_single_dispatch_tab_indented_code_block_decoy_is_ignored:7811`

加えて `test_dev_wave_waiter_consumer_pins_accept_current_docs_contract:7754` は合成 fixture ではなく実文書を検査する。`_build_min_repo` は多数の他 test に共用されているため、影響確認は `test_check_docs.py` 全体を対象にする。

検索で、現行 literal の実装上の pin は上記 3 箇所だった。同文は archive worklog と過去の `output/insights` にも残るが、履歴資料であり更新しない。

**tests README**

`orchestrator/tests/README.md:257` の最初の段落末へ次の 2 文を追加する。

> 各 key の fresh 取得は同名の `.gate` flock を経由し、writer が gate EX を保持して main を待つ間は新規 reader を gate SH で待たせる。gate は main 取得直後に閉じ、既存 fd の昇格・降格は gate を通さず、取得 deadline は全段で共有する。

`docs/dev-wave/operations.md` の DW-O23 は変更しない。

## 変異 matrix の事前登録候補

計 **10 件（M0＋9 件）**。以下の「KILLED」は期待であり、未実測。

| ID | 対象・変異 | 期待する検出 node |
|---|---|---|
| M0 | `conftest.py:1320` の説明 comment のみ変更 | 等価。SURVIVED を期待し、機能差分なしを確認 |
| M1 | `conftest.py:1358` 付近：reader の gate を省略 | `test_real_repo_writer_drains_overlapping_reader_stream` |
| M2 | 同所：writer の gate を省略 | 同上 |
| M3 | 同所と `:1395`：既存 fd の昇格・降格にも gate を要求 | 強化した `test_current_snapshot_reader_upgrades_for_same_process_candidate_fixture` |
| M4 | 同所：main 待ちで deadline を再起算 | `test_real_repo_gate_and_main_share_deadline` |
| M5 | 同所：例外時の gate close を省略 | `test_real_repo_gate_timeout_closes_fds[main-timeout]` |
| M6 | `wave_land_window.py:606` 付近：before=after 検査を削除 | `test_rolled_back_message_rejects_invalid_result[main-mismatch]` |
| M7 | 同所：tip≠after 検査を削除 | 同 node の `[tip-equals-main]` |
| M8 | 同所：status に `fold-rollback-failed` を許可 | 同 node の `[rollback-incomplete]` |
| M9 | `wave_land_window.py:38` 付近：巻き戻し専用固定文を 1 文字変更 | `test_rolled_back_message_success_is_exact_fixed_text` |

M3 は昇格側で早期に殺されるため、降格の独立保証は通常 test 内で第三者 gate を保持し続ける assertion に持たせる。必要なら実施時に M3 を昇格／降格へ分割し、matrix の件数を調整する。

`landed` の allowlist 拡大は既存 status 負例が検出する。今回は 10 件上限のため独立変異には選ばない。非等価なのに検出 node のない変異を「等価」と分類しない。

## 焦点テスト集合と影響範囲

検索で確認した 2 段の consumer は次のとおり。

| 変更元 | 第 1 段 | 第 2 段 |
|---|---|---|
| conftest の private lock | `_real_repo_file_lock`、`_real_repo_locks`、fixture/protocol | `test_real_repo_serialization.py`、実 repo 資源を使う test 群 |
| `wave_land_window.py` | `dev_wave_land.py:44` の import、`dev_wave_wait.py:2871` の CLI 呼出し | `test_dev_wave_land.py`、`test_dev_wave_wait.py` |
| 同上 | `test_wave_land_window.py` の直接 import | message の正負例 |
| 同上 | `test_resume_gate_acceptance_boundary.py:285` の tool 配置 | resume/acceptance 境界検査 |
| 項 9 literal | `check_docs.py:5730` の sequence 検査 | `test_check_docs.py` の実文書・合成 repo 検査 |

「4 test file が import」は厳密には違う。resume 境界 test は tool の配置側 consumer、wait 本体は CLI consumer である。また `tools/check_docs.py` 自体にも `wave_land_window` の参照がある。

焦点走の file 集合：

```text
orchestrator/tests/test_real_repo_serialization.py
orchestrator/tests/test_wave_land_window.py
orchestrator/tests/test_check_docs.py
orchestrator/tests/test_dev_wave_wait.py
orchestrator/tests/test_dev_wave_land.py
orchestrator/tests/test_resume_gate_acceptance_boundary.py
```

実装後は最初に新設・変更 node を確認し、その後に上記集合を既存 `tools/run_tests.py` 経由の計算ノード dispatch で走らせる。受入は既存 `tools/dev_wave_wait.py acceptance` 経路を使う。

新規ロック検査の待機は合計数秒を目標とする。child import は競合計測区間前に済ませ、48 process は作らない。ただし現在の file 全体の所要時間は未測定であり、受入 5 分内を静的検査だけで保証しない。deadline 延長・worker 制限は対処に含めない。

## リスクと未確定点

- **優先保証の境界**：採用案は gate EX holder に対する新規 reader の追越しを防ぐ。一方、NB polling の gate 自体には FIFO や writer 待機登録がなく、「writer が待ち始めた瞬間から必ず reader を止める」という厳密な契約は満たすと断言できない。これは実装前に親へ明示すべき仕様差である。
- **旧 session**：旧コードは gate を通らない。main の排他互換性は維持するが、旧 reader に対する飢餓防止は保証できない。
- **同 process の既存 state**：参照追加と入れ子要求は fresh ではなく、gate を通らない。P1 を任意の multithread reader stream へ一般化しない。
- **gate file の残置**：main lock と同様に `/tmp` に残す。稼働中の unlink は同名別 inode を作って協調を壊すため、自動削除は追加しない。
- **跨ホスト**：D1594/D1618 の shard affinity と同一 host/filesystem 前提は不変。`acceptance_shards.py` は変更しない。
- **holder 診断**：gate 待ちでは gate inode の READ/WRITE holder を最大 16 件表示する。main の holder や NB polling 中の待機者を表示するものではない。観測競合等では既存の unavailable 表示になり得る。
- **fork**：state に一時 gate fd を持たせれば reset 後の残留は閉じられる。任意の multithread fork の全面保証は今回の局所修正に含めない。
- **通知の意味**：`rolled-back` は P3 の結果状態を通知する。実際の rollback 発生履歴を証明しない。already-landed の fold 失敗は tip=after なので拒否される。
- **並列所有**：(1) は conftest・serialization test・tests README、(2) は message tool・message test・runbook・入口・checker・checker fixture。編集面は重ならず、段 5 で Codex author 2 本へ分けられる。この段では子を起動していない。

## 総括

通知側は P3、既存 landed 互換、610-byte 固定 stdout、文書 9,519-byte 予算まで具体化できた。rollback 契約と `dev_wave_land.py` は変更しない。

ロック側は fresh 取得だけの短寿命 gate、共通 deadline、実 flock の reader relay 負例、既存昇降格の維持を採る。ただし **gate 取得前の厳密な writer 優先は未保証**であり、P1 と fork の保証範囲にも補正が必要である。これらを隠して「writer 飢餓を全面解消」と判定せず、実装後の正負例と変異実測で局所修正の効果を確認する。
