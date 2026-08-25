---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1664-occupancy-blind-spot
seq: 1
title: [T-1664] 占有検査の unreadable-cwd fail-open は観測では閉じられないと実測で確定し、前提の潜在欠陥だけを閉じた (コード + テスト、branch worktree-dev-wave-t1664-occupancy-blind-spot)
---

## 本文

- **ユーザー裁定 (c)「cwd が読めない生存 process を立てて占有と判定させ、同じ process が対象外なら
  撤去可を維持する」は実装不能と判明した。** 対象の中に居る non-dumpable process と外に居るものは、
  読める `/proc` field (`cmdline` / `comm` / `status` / `stat`) を完全に同一にできる。
  読めないのは `cwd` / `exe` / `root` だけである。中と外を区別する述語は存在しない。
  `DW-S04` に従い親は不採用にせず、新事実を添えてユーザー再裁定へ戻す。詳細は {{D:occupancy-blind-spot-undecidable}}。
- **fail-open 自体は現物で再現した。** `prctl(PR_SET_DUMPABLE,0)` + `chdir(対象)` の生存 process を
  立てると checker は `rc=0 status=unoccupied scanned=2224` を返し、
  `dev_wave_cleanup._assert_unoccupied()` も例外を投げず受理した (= `rm -rf` へ進む)。
- **観測ベースの discharge 案は 3 つとも親の実測で反証した。** (i) comm allowlist は F490 が既に反証。
  (ii) argv と祖先 argv による除外は、cwd が worktree 内の実 worker 125 本のうち **78 本**を
  「占有しえない」側へ落とす。落ちるのは `claude bg-spare` (wave manager 本体)、launcher の bash、
  python3、待ち手の sleep/tail/timeout である。(iii) 起動時刻による除外は 107 本のうち **16 本**を
  落とし、その正体も wave manager 本体であった (本 wave 自身の manager を含む)。
  どちらも「自分が座っている worktree を消してよい」と判定する。
- **fail-closed 化の運用コストも実測した。** 現存 77 本の worktree のうち **59 本が rc=0 (撤去可)**、
  17 本が occupied、1 本が indeterminate。blind spot は 6 サンプルすべてで **3 で不変**
  ((sd-pam) / sshd / ssh-agent) なので、fail-closed にすると 59 本が即座に撤去不能化し
  DW-O28 の自己撤去は 100% 失敗する。D706 が記録した「満たせない gate は停止装置であり迂回を招く」
  型そのものであり、手動 `rm -rf` は occupancy だけでなく branch ancestry・clean tree・fold state の
  全 gate を同時に飛ばすため正味で危険が増える。
- **台帳本文の設計指定を親が段 1 で取り落としていた。** T-1664 の本文は
  「再挑戦は lease 前提の設計から始める」と明記していたが、親は brief で lease を scope 外に置いた。
  段 3 の敵対 2 レンズが独立に lease / privileged observer / cgroup v2 へ収束して初めて露見した。
- **代わりに、同じ file 対に実在した別の潜在欠陥を閉じた。** `_report_payload` は blind spot が空だと
  `same_uid_cwd_unreachable` を payload から落とすが、consumer はその key を必須にしている。
  占有ゼロ・issue ゼロ・blind spot ゼロという最も綺麗な走査が
  「occupancy payload lacks required fields」で拒否され、blind spot が空の環境では撤去が
  一切成立しない。変異走行でこの欠陥が実在したことも裏づけられた —
  key を落とす変異で既存の end-to-end 撤去 node 7 件が赤になった。詳細は {{F:occupancy-payload-conditional-key}}。
- **実装子が足した consumer テスト 1 本は修正の control になっていなかった。** 親が段 5 受領時に
  helper のハードコードから疑い、変異走行で確定した (checker を壊す変異のどちらでも赤にならない)。
  段 6 の fix で、実 checker の payload を consumer まで通す統合 node へ置き換えた。
- **恒真な保証を 1 件消した。** checker の docstring と `--help` は「worker でありうる process が
  一つでもあれば削除してはならない」と約束していたが、実装は blind list を status に使っていない。
  status 判定は据え置き、説明を実装へ合わせて狭めた。
- **子の工数**: codex 子 6 本 (plan 1・consult 2・author 1・review 2・fix 1 のうち consult sol は
  F492 型の launcher 不具合で `not_accepted`)。親が rollout と events を検算し、
  `codex_exit_code=0` / `termination_verified=True` / `validator_rc=0` / output hash 一致 /
  events 全行妥当を確認して attempt 出力を回収し、`check_codex_output.py` rc=0 で採用した。
  F492 の暫定運用どおりである。
- **子はテストを実走できなかった** (Pegasus の dispatch infra `rc=16`、`qstat -Q` の
  `EACCTAUTH Unknown user-id`)。author も fix も正直に「実装済み・未実走」と申告した。
  実走はすべて親が行った。

## 次の一手差分

### 更新

- [T-1664] **P1・ユーザー裁定待ち**: 占有検査の unreadable-cwd fail-open は、
  観測だけでは閉じられないことが実測で確定した (対象内外の non-dumpable process は
  可読 field を同一にできる)。observation ベースの discharge 3 案はすべて反証済み。
  fail-closed 単独は 59/77 を即座に撤去不能化する。
  {{D:occupancy-blind-spot-undecidable}} の 3 択をユーザーへ返す —
  (1) T-1664A (lease / cgroup を shadow 実装) と T-1664B (全層同時切替) へ分割、
  (2) 可用性を捨てて fail-closed 単独、(3) 穴を開けたまま説明を狭める。
  本 wave では (3) の説明是正と、前提となる payload 欠落欠陥の修正までを済ませた。
  base: 6b6531ab87d1b1f95aa64f890a93b1d198c81ac0a2893a7536f347c0990558b1

### 新規

- {{T:occupancy-hidepid-completeness}} **P2・新規**: `hidepid=ptraceable` の procfs では
  non-dumpable な同 uid PID が列挙自体から消えうる。checker は proc root の列挙だけで PID を固定
  するため、対象内の生存 process を見ずに rc0 へ進む経路が残る。procfs の mount option、
  PID namespace、observer の capability を検査し、完全性を証明できないなら走査全体を
  rc2 にするかを決める。段 3 の正しさ境界レンズが real として挙げた。
- {{T:occupancy-zombie-sibling-thread}} **P2・新規**: main thread が `pthread_exit()` した後も
  別 thread が実行中で cwd を保持する thread group を、現行の zombie 分類が非占有として扱う疑いがある。
  `/proc/PID/cwd` が利用不能になるため cmdline も走査されない。
  main thread 終了後に sibling thread が待機する real control を作って確かめる。
  段 3 の正しさ境界レンズが suspected として挙げた。
