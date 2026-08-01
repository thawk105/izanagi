結論は、P1 を採用して Python の終了状態を明示検査し、job/submit の凍結対象を同じ 8 key に揃え、submit の和の検査は残します。P4 は不十分です。既存 test は「宣言値の凍結 test」ではありますが script の受理境界を実行していないため、新設する subprocess test も D96 の境界テストとして扱う必要があります。

## 1. job 側の修正

対象は [t126_qualification.sh:453](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/t126_qualification.sh:453) から 468 行です。

### 採る形

`print` の移動だけには留めず、process substitution を command substitution に置き換えます。

```bash
if ! RESERVATION_OUTPUT=$(
  "$PY" -I -S -B - "$RESERVATION_POLICY" <<'PY'
# parse and validate
# validation succeeds only:
for key in output_keys:
    print(p[key])
PY
); then
  exit 2
fi
readarray -t RESERVATION_VALUES <<<"$RESERVATION_OUTPUT"
unset RESERVATION_OUTPUT
[[ ${#RESERVATION_VALUES[@]} -eq 3 ]] || exit 2
```

Python 内は次の順にします。

1. JSON を読む。
2. 下記 8 key を個別に既定値と比較する。
3. 一つでも違えば `qualification envelope mismatch` で終了する。
4. 検査成功後だけ、既存と同じ順序で `walltime_s`、`wmax_s`、`prologue_cap_s` の 3 値を出力する。

凍結する 8 key は次です。

| key | 値 |
|---|---:|
| `t126_qualification_walltime` | `"10:00:00"` |
| `t126_qualification_walltime_s` | `36000` |
| `t126_qualification_member_cap_s` | `900` |
| `t126_qualification_round_gap_s` | `1800` |
| `t126_qualification_prologue_cap_s` | `900` |
| `t126_qualification_attestation_cap_s` | `600` |
| `t126_qualification_finalize_reserve_s` | `600` |
| `t126_qualification_wmax_s` | `29100` |

既存の出力配列は 3 要素のままにし、[t126_qualification.sh:466](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/t126_qualification.sh:466) 以降の代入や downstream は変えません。全 key を出力する必要はなく、検査範囲と downstream へ渡す値を分離します。

### Bash の実行意味論

- [t126_qualification.sh:6](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/t126_qualification.sh:6) の `set -Eeuo pipefail` でも、`readarray < <(producer)` の外側の終了状態は `readarray` 自身のものです。process substitution の producer 終了状態は `readarray` に合成されません。
- `pipefail` は pipeline にだけ作用し、`< <(...)` には作用しません。
- 現機の Bash 5.1.16 で、producer が 3 行出して rc=7 でも `readarray` は rc=0、配列長 3、producer の rc は別途 `wait` した場合だけ 7でした。producer が無出力 rc=7 でも `readarray` は rc=0、配列長 0 でした。
- 現行 [458-462 行](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/t126_qualification.sh:458) は 3 行を出した後に失敗するため、[465 行](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/t126_qualification.sh:465) の長さ検査が常に通ります。
- `print` を後ろへ移すだけなら既知の mismatch は拒否できますが、「3 行を出した後に interpreter/wrapper が失敗する」場合は再び通ります。したがって P1 の明示 status 検査が必要です。
- `if ! OUTPUT=$(...)` では assignment の status が command substitution の statusになり、`if` が明示的に処理します。`errexit` や `ERR` trap の偶然の挙動に依存せず、拒否 rc を `2` に正規化できます。
- command substitution は stdout を EOF まで回収し、producer の終了を待つため、出力後の失敗も観測します。固定 3 行なのでメモリ上限や SIGPIPE の問題はありません。現在も `readarray` は EOF まで読むため、今回の原因は SIGPIPE ではなく status の切断です。
- pipeline にして `python | readarray` とすると通常 `readarray` が subshell に入り、配列が親 shell に残らないため採りません。
- 明示的な一時ファイルも採りません。[86 行](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/t126_qualification.sh:86) 以降は `noclobber` であり、作成・上書き・EXIT trap 時の回収を増やす利点がありません。command substitution と小さい here-string は永続する名前付き一時ファイルを導入しません。
- command substitution 内の shell 変数変更は親へ戻りませんが、Python は shell 状態を変更しません。代入先 `RESERVATION_OUTPUT` と `readarray` は親 shell で実行されるため、必要な変数 scope は保たれます。

確認した 9 個の `readarray` は、submit 側 162、189、243、349 行、job 側 416、453、470、577、605 行です。他の 8 ブロックは変更しません。

## 2. 3 key か 8 key か

8 key にし、job と submit の「個別値の凍結範囲」を揃えます。

submit が拒否する committed policy を job が受理する非対称性を残すと、submit の旧版・欠陥・別経路を通った receipt に対する job 側の防壁が片側になります。job が downstream へ渡すのは 3 値のままでよいものの、source-stage policy の受理判定は submit と同じ 8 値にすべきです。

ただし、これは policy JSON の全 key ではありません。[t126_reservation_policy_v1.json:6](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/qualification/t126_reservation_policy_v1.json:6) の `t126_qualification_member_term_grace_s` は九つ目の設定です。submit の required tuple [199-205 行](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/submit_t126_qualification.sh:199) にも含まれず、両 script から参照されていません。今回「8 key 全部」と呼ぶ場合は、あくまで submit が現在列挙している 8 key と明記します。term grace や schema、未知 key、JSON 数値型の追加 hardening はこの wave に混ぜません。

## 3. submit 側の修正

対象は [submit_t126_qualification.sh:187](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/submit_t126_qualification.sh:187) から 232 行です。

- [216-220 行](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/submit_t126_qualification.sh:216) の既存条件へ、次の三条件を `or` で純増します。

  - `prologue_cap_s != 900`
  - `attestation_cap_s != 600`
  - `finalize_reserve_s != 600`

- 次の既存拒否はすべて残します。

  - member cap = 900
  - round gap = 1800
  - `calculated == 29100`
  - `wmax == calculated`
  - walltime seconds = 36000
  - `calculated < walltime`
  - 3 出力の配列長
  - [231-232 行](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/submit_t126_qualification.sh:231) の project/queue/nodes/walltime/wmax 固定

- [187-188 行](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/submit_t126_qualification.sh:187) の「same rejection conditions as before; only the file moved」は変更後に誤りになるので、個別 cap と Wmax closure の両方を固定する旨へ更新します。
- submit 側の process substitution 構造は変えません。ここは検査完了後にだけ出力する現行順序であり、今回の単発事故を他ブロックの族改修へ広げません。

P3 の結論どおり和の等式は残します。ただし、8 値をすべて固定した後の `calculated == 29100` は数学的には独立ではありません。残す理由は「既存拒否を外さない」「Wmax の構成式を実行可能な invariant として残す」「将来一つの個別 guard が弱まった場合の backstop」であり、「現時点でも論理的に独立」は言い過ぎです。

## 4. D96 と境界テスト

[D96:4269-4292](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/docs/decisions.md:4269) に従い、親が新 D と境界テストを同じ integration commit に入れます。

### P4 の判定

`test_reservation_policy_and_job_headers_freeze_wmax_and_walltime` は最も近い宣言値の freeze test なので更新対象としては正しいです。しかし、現在は canonical policy を読むだけで、job/submit に変異入力を渡していません。script の guard を全削除しても通るため、script の受理集合を固定する境界テストとしては単独では不十分です。

したがって次の両方を D96 の境界更新とします。

1. [test_t126_pegasus_tools.py:1209](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_pegasus_tools.py:1209) を更新し、上記 8 key の個別値を assert する。既存の Wmax 計算、walltime、PBS header、budget assertion は残す。
2. 下記の subprocess test で、commit と identity が整合した変異 policy を実際に両 script へ渡し、受理・拒否境界を固定する。

`test_protocol_freezes_observational_envelope_and_wmax` は `t126_control_v1.json` の別受理集合、`test_reservation_policy_wiring_is_pinned_to_the_contract_constant` は path wiring、2774-2785 行の identity test は「live bytes と記録 commit の不一致」の検査です。いずれも今回の script 受理境界の代替にはなりません。

### 親が書く新 D

現在の末尾なら [docs/decisions.md:5185](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/docs/decisions.md:5185) 以降に D112 を追加します。採番は commit 直前に再確認します。記録内容は次です。

- 受理集合を「submit が列挙する 8 key の個別値」へ縮小すること。
- job は producer status を明示検査し、出力行数を status の代用にしないこと。
- submit は三つの cap の個別比較と既存 Wmax closure を併用すること。
- `member_term_grace_s`、schema、未知 key、他の `readarray` は今回の射程外であること。
- 却下案: print の移動だけ、job の 3 key 維持、既存和の削除、9 key/全 parser への一般化。
- 境界 test と正例 test の名前。
- 既存の正しい policy は引き続き受理し、縮小対象は drift policy と producer failure だけであること。

実装子は scripts と test だけを編集し、commit しません。親が新 D、[docs/worklog.md:1396](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/docs/worklog.md:1396) 以降の完了記録、insights/変異台帳を書き、実装 patch と一つの commit にします。

`contract.py` は変更不要です。policy は既に [REQUIRED_CODE_IDENTITY_PATHS:38-65](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/qualification/contract.py:38)、両 script は [REQUIRED_SCRIPT_IDENTITY_PATHS:66-70](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/qualification/contract.py:66) に入っています。将来の submission は commit blob から新しい identity を導出します。

## 5. 新設テスト

### fixture の作り方

[test_t126_pegasus_tools.py:790-819](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_pegasus_tools.py:790) の `_attempt` に、既定値では現行挙動を変えない optional 引数を加えます。

- `reservation_policy_overrides`: policy copy を initial fixture commit 前に変える。
- `job_scratch_root`: fixture 内の job script の `SCR_ROOT` 1 箇所だけを `tmp_path` 配下へ置換する。置換数が 1 であることを assert してから commit する。

これにより、source archive、receipt、`code_identity`、`script_identity` が同じ変異 commit を指し、identity mismatch が先に拒否して新 guard を隠すことがありません。本番 script に test-only scratch override は追加しません。

[ `_run_bound_job_terminal`:3693-3718](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_pegasus_tools.py:3693) を使い、`IZANAGI_T126_TEST_EXIT_AFTER_BINDING=""` として予約検査まで進めます。検査通過の観測には、最初の dependency `git rev-parse HEAD` で marker を作って終了する regular wrapper を PATH 先頭へ置きます。重い build には進みません。

Python は bare `python3` に任せません。regular executable の wrapper を fake bin に作り、`sys.executable` を `exec` します。symlink は [submission.py:73-81](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/qualification/submission.py:73) が拒否するため使いません。`_run_bound_job_terminal` の launcher 自体が `sys.executable` を使っていても、job は [t126_qualification.sh:15-25](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/t126_qualification.sh:15) で `python3` を再解決するので、この wrapper が必要です。これは test fixture の hermeticity であり、T-248 の production dispatch 修正ではありません。

submit test は [ `_submit_fixture`:2809-2872](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_pegasus_tools.py:2809) で repo を複製し、fixture policy を変更後に `git add/commit` して clean にしてから、[ `_run_submit`:2924-2939](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_pegasus_tools.py:2924) と既存 scheduler stubs を使います。

### テスト一覧と kill する変異

| テスト | 検査内容 | 赤になる変異 |
|---|---|---|
| `test_job_reservation_policy_accepts_exact_point_and_rejects_each_frozen_value` | exact policy の正例は downstream marker に到達し、8 key を一つずつ変えた committed fixture は rc=2・mismatch 診断・marker 不在 | 対象 key の比較を一つ削除すると、その parameter が marker へ到達して赤。逆に mismatch を恒真化すると exact 正例が赤 |
| `test_job_reservation_reader_rejects_python_failure_after_complete_output` | wrapper が target Python の正常な 3 行出力後に rc=73 を返す。job は rc=2 で止まり、failure-injection marker は有り、downstream marker は無し | 明示 capture/status guard を process substitution + 配列長だけへ戻すと 3 行が通って downstream marker が作られ、赤 |
| `test_submit_rejects_compensating_cap_drift_before_scheduler_calls` | fixture policy を prologue=1500、attestation=0、finalize=600 とし、和を29100に保ったまま commit。rc=2、mismatch 診断、scheduler call 0 件を要求 | 新しい三つの個別比較をまとめて除き sum-only へ戻すと submit/qsub まで進み、赤 |

同時更新する既存境界 test には、同じ compensated drift を一時変異すると新しい個別 assert が赤になることを割り当てます。最終の policy JSON は変更しません。

submit の過剰拒否は既存 `test_fake_qsub_qstat_exact_visibility_and_durable_receipt` が exact policy の正例です。job 側は既存 subprocess test が [433-435 行](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/t126_qualification.sh:433) で予約検査前に止まるため、新しい正例 parameter が必要です。

既存 identity test との重複はありません。新テストの変異 policy は fixture commit 前に入れて identity を再導出する一方、既存 2774-2785 行は記録済み commit と live mapping の不一致を拒否する test です。

## 6. 壊しうる既存テスト

直接更新が必要なのは次だけです。

- `test_reservation_policy_and_job_headers_freeze_wmax_and_walltime` — [1209-1225 行](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_pegasus_tools.py:1209)。8 key の個別 assert を追加する。

回帰監視対象は次です。

- `test_shell_scripts_pass_bash_syntax` — [1328-1340 行](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_pegasus_tools.py:1328)。heredoc と `if ! ...=$(...)` の閉じ方を検出する。
- `_run_submit` の全 caller — 2943-3425 行。特に `test_fake_qsub_qstat_exact_visibility_and_durable_receipt`、duplicate/dry-run、M8a/M8b/M8c、crash recovery、retry、short-write。すべて exact policy を通る正例なので、過剰拒否や valid-path 破損を検出する。
- `_run_bound_job_terminal` の既存 caller — 3537、3660、3834、3896、3966、4012 行。現状はいずれも予約検査前に終了するため意味上は不変ですが、`_attempt` の optional 引数が既定動作を変えると壊れます。
- `test_m11b_exact_spooled_script_uses_embedded_isolated_publisher` — [5113-5177 行](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_pegasus_tools.py:5113)。script 全 bytes を commit し直して動的 hash を照合します。

script 本文を文字列 assert する既存 test も監査対象です。

- `test_reservation_policy_wiring_is_pinned_to_the_contract_constant` — 1275-1325 行
- `test_submitter_has_exact_opt_in_and_imports_persistent_publisher` — 1773-1783 行
- `test_job_script_has_no_persistent_import_and_has_isolated_publisher` — 1786-1792 行
- `test_binding_v2_consumer_wiring_diagnostic_is_present` — 3664-3680 行
- embedded publisher 抽出 helper — 704-710、3721-3728 行
- mutation anchor/meta-test — 501-519、608-610、5180-5240 行

今回変更する文字列はこれらの assert/anchor には含まれないため、更新は不要です。script SHA は `_attempt`、3905-3909 行、5130-5176 行で committed bytes から動的に計算されており、literal hash 更新も不要です。

## 7. 親 brief への異議・見落とし

1. P4 は不完全です。1209 行の test は宣言値を読むだけで、script guard の削除を検出しません。新設 subprocess test を実際の受理境界テストとして新 D に記載する必要があります。
2. P2 の「8 key 全部」は policy JSON 全体ではありません。D107 は 9 key と記録しており、未対象の `member_term_grace_s` を新 D で明示的に scope 外にしないと記述が虚偽になります。
3. P3 の結論は採用しますが、「和は独立な検出力」は個別値を全固定した後には数学的に誤りです。既存拒否保存と関係 invariant の維持が正しい理由です。
4. mismatch policy の test だけでは P1 と「print を後ろへ移すだけ」を区別できません。正常な 3 行出力後に rc を失敗させる test が必要です。
5. 受理集合縮小時の正例が brief にありません。`DW-M01` に従い、job が exact policy で検査を越える正例を同じ parameterized test に入れます。
6. `_run_bound_job_terminal` は outer launcher に `sys.executable` を使っても、job 本体が `python3` を再探索します。また予約検査へ進むと `/scr` を使います。regular Python wrapper と fixture 内 scratch 置換が必要です。

現在地は `pegasus02` なので pytest は実行していません。実施したのは読取りと Bash の status 小実験だけです。親が計算ノードで焦点 node、test file 全体、変異、全受入を順に実測します。

## 総括

### (a) 採る方針

1. job は command substitution と `if !` で Python rc を明示検査する。
2. job/submit の凍結範囲を submit 定義の 8 key に揃える。
3. submit は三つの cap 比較を追加し、既存の和・関係式を全て残す。
4. 既存 freeze test と新しい subprocess 境界 test を新 D と同一 commit にする。
5. policy JSON、共有 policy、他の `readarray` は変更しない。

### (b) 編集する file:line

- 実装子: [t126_qualification.sh:453-468](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/t126_qualification.sh:453)
- 実装子: [submit_t126_qualification.sh:187-232](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/submit_t126_qualification.sh:187)
- 実装子: [test_t126_pegasus_tools.py:790-819](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_pegasus_tools.py:790)、1209-1225、2875-2939、3693 以降
- 親: [docs/decisions.md:5185](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/docs/decisions.md:5185) 以降の新 D
- 親: [docs/worklog.md:1396](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/docs/worklog.md:1396) 以降と T-247 insights/変異台帳

### (c) 新設テスト名

- `test_job_reservation_policy_accepts_exact_point_and_rejects_each_frozen_value`
- `test_job_reservation_reader_rejects_python_failure_after_complete_output`
- `test_submit_rejects_compensating_cap_drift_before_scheduler_calls`

### (d) 親 brief への異議

P4 は単独では境界テストにならない、P2 の「全部」は九つ目の term grace を除く限定表現が必要、P3 の「独立な検出力」は不正確、P1 を最小修正と区別する late-failure test・job 正例・Python/scratch fixture が欠落しています。