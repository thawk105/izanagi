現 plan は **NO-GO**。指定6ファイルを全行確認し、静的レビューのみ実施した。テスト実走・編集はしておらず、親記録の 2/2 pass と fault injection 2例を再検証済み green とは扱わない。

## real

### R1 — preexisting `.s` / ownership 観測不能を `False` にすると T-138 型の偽 SKIP が戻る

- severity: **high**
- 根拠: plan は preexisting entry と pre-bind `OSError` を `False` にする [result.md:19](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/jobs/s2-plan/result.md:19)、[result.md:78](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/jobs/s2-plan/result.md:78)。唯一の consumer は `False` をそのまま SKIP にする [test_dev_waves_integration.py:1189](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1189)、[test_dev_waves_integration.py:1191](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1191)。
- 静的再現 sequence:
  1. `Supervisor` 構築または別の退行が runtime に `.s` を残す、あるいは ownership 用 nofollow stat が `EIO`。
  2. planned helper が capability 不足として `False`。
  3. long-path node は本番 bind を一度も試さず `SKIPPED / rc=0`。
- 成果物影響: product bytes は不変だが、壊れた test-only commit を受理でき、long-path acceptance proof が欠落する。
- 最小 fix: ownership precheck は socket 作成前に行い、`FileNotFoundError` のみ absent。entry 実在は保存したまま `FileExistsError`、その他の ownership 観測エラーも送出する。`False` は実際の capability 列の socket/bind/chmod/stat/listen 拒否だけに限定する。preexisting test も `False` ではなく例外を期待する。

### R2 — test-level recovery が defect observation を消す順序穴

- severity: **high**
- 根拠: partial-bind test は `.s` 不存在を期待する一方、同じ pathname を test-level `finally` で回収するとだけ書かれている [result.md:67](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/jobs/s2-plan/result.md:67)、[result.md:76](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/jobs/s2-plan/result.md:76)。
- 静的再現 sequence:
  1. 旧 helper が partial-bind 後に `False` と残留 `.s` を返す。
  2. test の `finally` が先に `.s` を削除。
  3. その後の `assert not path.exists()`、bool、既に閉じている FD assertion がすべて通る。
- 成果物影響: 旧 helper または M-T146-A が偽 green/SURVIVED になり、mutation 帰属も崩れる。
- 最小 fix: helper return/例外の直後、recovery 前に bool、nofollow の `.s` 状態、raw FD、dirfd の `EBADF` を観測・assert する。recovery は assertion を包む外側 `finally` で、patch 復元後または保存済み real syscall を用いる。

### R3 — M-T146-A の anchor が曖昧で、既存 T-138 gate による kill と区別できない

- severity: **high**
- 根拠: M-A は「例外後再確認、または `owns_path=True` を削除」と二義的 [result.md:124](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/jobs/s2-plan/result.md:124)。正常 bind 側の assignment を消せば、既存 permissive positive control の残留検査 [test_dev_waves_integration.py:1175](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1175) が先に kill する。旧台帳にも既存 test に殺される変異を「純増」から再照準した先例がある [mutation-ledger.json:12](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-27_t137-t138-socket-guard-mutation-ledger.json:12)。
- 静的再現 sequence: 正常成功側 assignment を除去 → existing positive node が `.s` 残留で失敗 → new partial node の検出力を示さないまま M-A を KILLED と記録。
- 成果物影響: mutation ledger が純増検出力を過大認証する。
- 最小 fix:
  - M-A は「bind が投げた後、実在を確認した exception branch だけで ownership を `False` に戻す」一意 anchor にする。
  - existing T-138、long-path、新 partial node を別々に走らせ、前二者 PASS・新 node FAIL・SKIP なしを要求する。
  - M-B も「推奨」でなく必須にし、FNF parameter は PASS、Permission/EIO parameter だけ FAIL、existing gate は PASS と固定する。
  - rc、FAILED node、SKIPPED node/reasonをすべて記録する。

### R4 — 「新規3 test が旧 helper を赤」の一般化と純増検出力が過大

- severity: **medium**
- 静的 matrix:
  - partial-bind residual: 旧 helper は赤。
  - cleanup FNF: 旧 helper は例外送出なので赤。
  - preexisting regular/broken symlink: faithful な `EADDRINUSE` 模擬なら旧 helperも `False`・保存で緑。
  - cleanup Permission/EIO と socket/dirfd close: 旧 helperも既に期待どおり送出・closeする。
- 根拠: plan はこれらをまとめて純増検出力と表現する [result.md:148](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/jobs/s2-plan/result.md:148) が、現 helper の `created` と cleanup 順は [test_dev_waves_integration.py:1114](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1114)、[test_dev_waves_integration.py:1125](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1125)。
- 成果物影響: product 影響はないが、test count・直列 group・検出力説明を不必要に膨らませる。
- 最小縮退案:
  1. `fault_policy` 1関数を stable ID 付き parameterize: `partial-bind/FNF/EPERM/EIO`。
  2. `preexisting_entry` 1関数を `regular/broken-symlink` で parameterizeし、R1どおり例外＋保存を期待。

  2関数で同じ policy/mutation 面を保てる。Permission/EIO は「旧赤」ではなく M-B regression guard と正直に分類する。

### R5 — 「実 raw AF_UNIX FD」と「sandbox capability 非依存・skip不可」は両立しない

- severity: **medium**
- 根拠: plan は実 socket FD を要求 [result.md:69](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/jobs/s2-plan/result.md:69) しつつ、fault test は sandbox capability 非依存とする [result.md:97](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/jobs/s2-plan/result.md:97)。
- 静的再現 sequence: AF_UNIX socket factory を禁じる sandbox → fixture 用 raw socket の作成段階で ERROR。skip すれば明示契約違反、skip しなければ合法な capability 不足環境を過剰拒否する。
- 成果物影響: fault test が long-path node より厳しい環境要件を新設し、受理集合を過剰縮小する。
- 最小 fix: `os.pipe()` 等の実 FD-backed probe wrapperで close を直接 `fstat(fd) == EBADF` 観測し、`.s` は実 filesystem entry として作る。AF_UNIX 実挙動は既存 long-path nodeに限定する。

### R6 — runner は skip node/reason を保存せず、plan の skip 拒否手順が未配線

- severity: **high**
- 根拠: plan は node ID と理由の記録を要求する [result.md:110](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/jobs/s2-plan/result.md:110) が、runner の永続記録は counts と collection digest だけ [run_tests.py:652](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/tools/run_tests.py:652)。既定 pytest argv に `-rs/-rf` もない [run_tests.py:275](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/tools/run_tests.py:275)。前台帳では SKIP + rc=0 が実際に SURVIVED だった [mutation-ledger.json:32](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-27_t137-t138-socket-guard-mutation-ledger.json:32)。
- 静的再現 sequence: new node に skip が入る → full runner は rc=0 →環境依存の既存 skip 数に埋没 → node/reasonなしで受理。
- 成果物影響: acceptance record が検出対象未実行の commit を受理し得る。
- 最小 fix: targeted matrix は `-rf -rs` を付け、新 fault parameter の skip を一件でも拒否する。long-path のみ exact reason を許可する。mutation ledgerにも failed/skipped nodeを別フィールドで保存する。

## refuted

- **consumer 到達漏れ / isolation meta-test変更必須:** refuted。integration の plain runner は同一ファイルを `pytest.main()` へ渡す [test_dev_waves_integration.py:1778](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1778)。repository runner も既定 target を pytest/xdist `loadgroup` へ渡す [run_tests.py:285](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/tools/run_tests.py:285)、[run_tests.py:777](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/tools/run_tests.py:777)。meta-test は `socket.socket` 語彙を helper 呼出しへ推移させ [test_dev_waves_isolation_contract.py:35](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_isolation_contract.py:35)、marker集合と完全一致させる [test_dev_waves_isolation_contract.py:102](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_isolation_contract.py:102)。各新規関数に `dev-waves-runtime` を1個だけ付ければ meta-test no-change は妥当。
- **mock 自己申告しか観測できない:** refuted。ただし R2/R5 の修正が条件。helper return、nofollow pathname、実 FD/dirfd の `EBADF` は直接観測でき、mock は例外の注入だけに限定できる。
- **production 効果の主張:** brief 自体は product bytes 不変と test acceptance のみを区別している [s1-brief.md:13](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/s1-brief.md:13)。helper の実 caller も同じ test file 内の二箇所だけ [test_dev_waves_integration.py:1156](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1156)、[test_dev_waves_integration.py:1182](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1182)。したがって production 全層保証とは記録してはいけないが、no-touch 方針自体は静的に整合する。

## scope外裁定候補

- **hostile concurrent writer に対する原子的 ownership:** severity **backlog**。test-private directory 契約外で、stat→bind→stat→unlink の name replacement を局所 helper だけでは閉じられない。production ownership protocol の別 wave に送る。
- **path-sensitive isolation meta-test:** severity **low**。preexisting branchは実行時 socket を作らなくても、現 meta-test は helper到達だけで直列化する。今回の2関数縮退で追加 group数を抑え、meta-test自体の精密化は別件とする。
- **phase3 product milestone更新:** scope外。現行の T-146 正本は worklog の P2 nit [worklog.md:1114](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/docs/worklog.md:1114) で、phase3 に対応チェック項目はない。完了記録は「test helper/test acceptance hardening」とし、product artifact の進展を phase docへ新設しない。
- 完了記録では、product の certified 選択・レポート・試行台帳の値/参照は不変、一方で test collection count/digest、mutation ledger、受入結果だけが変わる、と明記する。

## 総括

**NO-GO — 現 plan のまま段4で採用不可。**

段4 must-fix は次の5点。

1. preexisting `.s` と ownership 観測不能を `False/SKIP` にせず、保存して例外送出する。
2. defect observation を test recovery より先に固定し、実 FD-backed・AF_UNIX非依存の fixture にする。
3. M-T146-A/B を一意 anchor・単独帰属で必須登録し、existing gate/new node/skip を分離記録する。
4. 新規 test は2関数の parameter matrixへ縮退し、旧赤ケースと regression guard を区別する。
5. plain runner・targeted pytest・xdist meta・full runner の到達を確認し、`-rf -rs` で新規 SKIPを明示拒否する。

これらを反映した plan v2 なら段4 GO 候補。
