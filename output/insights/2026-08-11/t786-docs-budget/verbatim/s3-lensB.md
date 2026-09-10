## 総括

新設検査の「配置」は新規ですが、「実際に canonical waiter を使った」ことは証明しません。可視 literal を置いたまま、実運用では `wait.sh`、`--pid`、任意の child command を使う入力が通ります。

最も現実的な 3 か月後の無意味化経路は、command/reference に `` `tools/dev_wave_wait.py acceptance` `` を「使用しない参照名」として残し、manager の実 argv だけを `wait.sh` または `--pid` 経由へ変更することです。`check_docs` は緑、`test_dev_wave_wait.py` は script 単体なので緑、receipt は未検査のまま、F32 型の長時間ハングが再発します。

### 1. literal の存在だけで恒真になる — REAL

- file: [plan2.md:326](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/plan2.md:326>), [plan2.md:337](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/plan2.md:337>)
- 何が壊れるか: 「canonical invocation を consumer が使う」という義務が、単なる文字列配置義務へ縮退する。
- 再現シナリオ:

```text
6. 受入は `tools/run_tests.py` を直接起動する。
   `tools/dev_wave_wait.py acceptance` は参照名として残すだけで、実行しない。
```

同様に、`DW-C00` に「`tools/dev_wave_wait.py` は参考名で実運用は `wait.sh`」、`DW-O01` に「`tools/dev_wave_wait.py producer` と `--pid-file` は説明用で、実際は `wait.sh --pid`」と書く。可視 literal は各 exact 1 件なので通る。

- 判定: **real**
- 修正案: literal 検査を「必要な command-shaped block の構文」と「実行 receipt」の両方へ分ける。receipt が導入できないなら、canonical waiter に吸収した prose を削除せず、scope 外として裁定へ戻す。

### 2. runtime argv と receipt が完全に scope 外 — REAL

- file: [plan2.md:432](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/plan2.md:432>), [tools/dev_wave_wait.py:866](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/tools/dev_wave_wait.py:866>)
- 何が壊れるか: 検査対象が command/reference の prose に閉じ、実際の起動を一切束縛しない。
- 層別結果:

| 層 | 現状 | 欠落 |
|---|---|---|
| command 段6/9 | visible literal の exact count | 実 argv、child command、release/message |
| `DW-C00` / `DW-O01` | visible literal の exact count | literal と実コマンドの対応 |
| dispatch edge | section ID と条件/段の配線 | waiter invocation の配線 |
| runbook §7.3 | 検査対象外 | canonical argv の drift |
| runtime argv | 検査なし | `--pid-file`、`--owned-path`、`run_tests.py` の実使用 |
| receipt | 検査なし | stage/wave/source SHA と invocation の結束 |

`run_acceptance()` は任意の child command を受け取り、`acceptance-command argv=...` を stderr に出すだけです。永続 receipt として検証されません。repo 内の Python production caller 検索でも、tool 本体とテスト以外の consumer は見つかりませんでした。

- 再現シナリオ: 文書には canonical literal を置き、実行時には `dev_wave_wait.py acceptance ... -- true` または旧 `wait.sh` を呼ぶ。
- 判定: **real**
- 修正案: runtime launcher を実装して invocation receipt を発行し、stage・wave・argv・script digest を検証する。これを今回の scope 外にするなら、(P1) の「解決済み」とせず裁定パッケージにする。

### 3. canonical script 自体の PID 保証と C00 の本数義務が未閉包 — REAL

- file: [tools/dev_wave_wait.py:353](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/tools/dev_wave_wait.py:353>), [tools/dev_wave_wait.py:375](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/tools/dev_wave_wait.py:375>)
- 何が壊れるか: plan は exact PID/starttime を代替実装として扱うが、`/proc` 読取失敗時に pid-only へ縮退する。
- 再現シナリオ:

  1. `_initial_start_time()` が `/proc/<pid>/stat` の `OSError` を受け、`None` を返す。
  2. `_pid_state()` は `kill(pid, 0)` だけで alive と判定する。
  3. 元 producer 終了後に PID が再利用され、再利用先の終了を元 producer の死と誤認する。
  4. stale `.done` と artifact が残っていれば成功する。

既存テストもこの fallback を通して成功を期待しています（`test_producer_file_visibility_grace_is_bounded`）。

さらに、canonical path を使っても manager が同じ条件の waiter を 2 本起動したり、通知ごとに再生成したりすることを防げません。これは `DW-C00` の「1 条件 1 本」「再生成禁止」の未検査部分です。

- 判定: **real**
- 修正案: starttime を読めない場合は fail-closed にするか、fallback を明示的な非安全モードとして受入不可にする。条件単位の invocation ID / singleton receipt も必要です。

### 4. invocation の引数結束と段9終端義務を見ていない — REAL

- file: [plan2.md:328](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/plan2.md:328>), [plan2.md:333](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/plan2.md:333>), [plan2.md:87](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/plan2.md:87>)
- 何が壊れるか:

  - `DW-O01` の `tools/dev_wave_wait.py producer` と `--pid-file` は別々に置ける。
  - producer の必須 `--done-file` / `--artifact-file`、acceptance の `--owned-path`、child の `tools/run_tests.py` は要求されない。
  - 段9では acceptance literal だけ残して、`release` や land 成功後の `message` を削除しても新設検査は通る。

- 再現シナリオ:

```text
`tools/dev_wave_wait.py producer` は canonical の説明例。
`--pid-file` は別の launcher option の説明。
実際の producer は wait.sh --pid を使う。
```

段9から `release` / `message` を削除し、acceptance literalだけ残す。dispatch と H2 は変えない。

- 判定: **real**
- 修正案: 文字列を独立 count せず、必要な argv 集合を同一の fenced command block として解析する。段9は waiter invocation に加えて `release`、land-success 条件、message の順序を別 pin にする。

### 5. 「既存検査との重複なし」は過大主張 — REAL（限定的）

- file: [plan2.md:359](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/plan2.md:359>), [tools/check_docs.py:507](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/tools/check_docs.py:507>), [orchestrator/tests/test_check_docs.py:5758](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/orchestrator/tests/test_check_docs.py:5758>)
- 既存で見られている性質:

  - H2 の存在・一意性・section inventory
  - C00 の条件24 target
  - O01 の stage/condition dispatch edge
  - O01 の model authority / route
  - visible markdown、fence、HTML comment の遮蔽
  - `dev_wave_wait.py` 自体の PID、zombie、`.done`、artifact、pattern 不在
  - `wave_land_window.py` の FIFO、heartbeat、TTL

- 判定: **「waiter path の consumer binding は新規」は real。ただし、構造・canonical script 性質まで純増とする主張は refuted。**
- 修正案: 新設検査の純増分を「docs の consumer literal と target path の binding」だけに限定して記述する。

### 6. pin 閉包に差分がある — REAL

確認できた pin 面は次のとおりです。

- `tools/check_docs.py`: `REQUIRED_REFERENCE_SECTIONS`、stage/condition contracts、O01 model/route、visible H2、layer budget。
- `test_check_docs.py`: synthetic dispatch literal、`_write_command_guard_docs()`、`_TEST_DEV_WAVE_LAYERS`、slice/byte oracle、`_COMMAND_GUARD_CASES` / needle / expected count、condition24、exact-section pins。
- `test_dev_wave_launch_authority.py`: O01 model authority と S06-A/C の独立 cross-check。
- `test_dev_wave_wait.py`: canonical script path、`--pid-file` CLI、PID/starttime/zombie/pattern の behavior。
- `.agents/skills/dev-wave/SKILL.md`: O01 worker route と段9 adapter。
- `docs/pegasus-runbook.md` §7.3: acceptance と producer の実 argv。

plan の差集合は以下です。

- synthetic command (`test_check_docs.py:598`) に現状 `## 9 段状態機械` の段6/9本文がなく、新しい positive/negative fixture の独立 pin が未列挙。
- `_COMMAND_GUARD_NEEDLES`、expected counts、registration meta-test は plan の本文では触れているが、pin 閉包表にはない。同期漏れ時に mutation が新設検査ではなく fixture-registration failure で赤くなる。
- runbook §7.3 の canonical argv は新 checker の対象外。runbook を `wait.sh` に変えても green のまま。
- `.agents/skills/dev-wave/SKILL.md` は waiter literal を持たない。plan の「編集不要」は妥当な scope 宣言だが、skill/adapter 層を consumer と数えるなら未被覆。
- `test_dev_wave_wait.py` は script 単体の oracle であり、docs → runtime consumer の pin ではない。

- 判定: **real**
- 修正案: machine pin、behavior pin、runbook reference、runtime consumer を別表で明示し、runbook/skill/runtime を scope 外にするなら裁定として明記する。synthetic fixture は production 定数からの共謀生成にせず、literal を手書きで固定する。

### 7. byte 再計算は最終値なら正しいが、段階投入では一時的に赤い — REFUTED / sequencing risk REAL

- file: [tools/check_docs.py:3662](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/tools/check_docs.py:3662>), [plan2.md:379](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/plan2.md:379>), [plan2.md:419](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/plan2.md:419>)
- preamble と H2 slice 境界を含めて再計算した結果:

| 状態 | L1 | L1.5 | `DW-O09` | L2 最大 |
|---|---:|---:|---:|---:|
| 現在 | 10,625 | 9,554 | 935 | 861 (`DW-O19`) |
| T-773 だけ | 10,596 | **9,597** | 935 | 861 |
| 全変更、S04除外 | 10,608 | 9,545 | 836 | 861 |
| 全変更 | 10,578 | 9,545 | 836 | 861 |

したがって plan の最終値、preamble の帰属、L1/L1.5 差集合、O09 の最大節移動に数え違いはありません。一方、優先2の T-773 だけを先に land/check すると L1.5 が 31 bytes 超過します。

- 判定: **最終算術は refuted。一括 land 前提でないなら sequencing risk は real。**
- 修正案: 縮約と追加を同一 atomic change にするか、T-773 結線より先に L1.5 の余白を作る。中間状態を green と報告しない。

### 8. P3 は実測と snapshot が不整合 — REAL

- file: [brief.md:31](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/brief.md:31>), [brief.md:68](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/brief.md:68>), [docs/worklog.md:3344](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/docs/worklog.md:3344>)
- 何が壊れるか:

  - brief/plan は滞留8件で計算している。
  - 現在の worklog には同じ T-786 を「同梱9件」とし、T-788 の `DW-O02` 追加を明記した記録がある。
  - T-788 は L1.5 を 228 bytes 超過させる候補なので、plan の最終 L1.5=9,545 は現行 backlog 全体の結論ではない。

F32 は段2で20時間23分、段6で7時間36分停止した実害があり、T-773を上位に置く根拠はあります。一方、T-769/T-775(ii) は「4例目の MISMATCH 予防」という予測で、brief には頻度・停止時間・重大度の実測がありません。さらに T-757/T-738(c) を「0 bytesで解消」とする plan の結論は、PID fallback と F156 の実例により未成立です。

- 判定: **real**
- 修正案: brief の対象 snapshot を固定し、T-788 を明示的に除外するか、9件 package として再計算する。T-757/T-738(c) は runtime binding の証拠が出るまで「吸収済み」としない。

### 9. 変異 matrix は個別帰属は概ね clean だが、恒真性を証明しない — REAL

- file: [plan2.md:343](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/plan2.md:343>), [plan2.md:357](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/plan2.md:357>)
- planned mutation のうち、stage6 relocation、stage9 deletion、C00 fence hiding、O01 `--pid` replacement、target symlink は、既存の section/dispatch/budget 検査だけでは通常赤にならず、新 checker に帰属できる。ここは **他理由で赤になる懸念は refuted** です。
- ただし全変異が「literalを消す・移す」型なので、literal count checker が vacuous でも全て殺せます。negated/dead-text の decoy mutation がありません。
- 再現シナリオ: 所見1の「実行しない canonical literal」を正例 fixture として検査すると、現在の契約では green になる。
- 判定: **恒真性に対する matrix の証明不足は real。個別 mutation の汚染は refuted。**
- 修正案: literal を保持したまま実体を custom waiter に差し替える decoy、canonical path と無関係な child argv、`--pid-file` を別文へ分離する mutation を追加し、期待 finding を新 checker の finding prefix に限定する。

## 破れなかった面

- 親が提示した最終 byte 値は、`check_docs.py` の preamble 帰属と raw H2 slice で再計算して一致した。
- waiter path の docs consumer literal 自体は、現行 `check_docs.py` に存在しないため、狭い意味では純増検出です。
- plan の5つの単純な配置変異は、静的依存上は新設検査以外の理由で赤くなる形ではありません。

テスト実測・pytest は実行していません。