# dev-wave supervisor — 運用契約 (v1、機械層のみ)

bounded dev-wave supervisor の運用正本。設計の全文は
`output/insights/2026-07-21_dev-waves-supervisor-design.md`、採用裁定は worklog
2026-07-21 (7) の [T-069]、実装 wave の記録は [T-076] の worklog エントリ、設計追補は
decisions の D74 を参照。

## 現在の段階 — real 実行は未開放

**本実装は段階導入ステップ 2 (fake child の機械層) である。** worker は spawn 前に child
実行体へ供試 handshake (`--dev-waves-fake-handshake <nonce>` へ `dev-waves-fake/v1 <nonce>`
を echo) を要求し、失敗は create-only record として永続化され最終 reason
`fake-handshake-failed` で停止する。real Claude Code はこの handshake に応答しないため、
**通常の運用操作で real child が起動されることはない** (ただし後述の非目標 1 のとおり、
これは意図的な wrapper に対する防壁ではない)。real 開放には後続 wave (段階 3〜7) と
「real 開放前に必要なユーザー裁定」の確定が必要である。

## 実行鎖と責務

```text
python3 tools/dev_waves.py serve   (foreground、通常 terminal からのみ)
  ← python3 tools/dev_waves.py client submit/status/cancel  (Unix socket、固定 schema)
  → wave ごと: exact main SHA から worktree 作成 → worker → fake child → 独立検証
```

- daemon は唯一の制御主体。worker は 1 child の所有だけを担う単一 thread の小 process。
  child は preexec で setpgid + SIGSTOP 自停止し、identity (pid + /proc start identity) の
  create-only 永続化後に SIGCONT で発進する。PDEATHSIG(SIGKILL) と signal disposition の
  初期化を preexec で行う
- child の receipt は「主張」であり、独立照合に全件合格した completed wave だけが
  `wave-accepted` になる。completed の受理には envelope の
  `subtype==success && is_error==false && permission_denials==[]`、
  `main_after == landed_main_sha == landed_commits 末尾 == wave branch tip`、
  selected task ID 非空、worklog 前進、task-run completed、check 群 green が必要。
  **検査不合格の wave は receipt の outcome にかかわらず terminal `failed`** で、
  outcome→terminal の写像 (`no-actionable-task`→`completed`、`user-ruling-required` /
  `blocked`→`blocked`、`failed`→`failed`) は全検査合格時にのみ適用する。非 completed
  outcome は main 不変を要求し、次 child は起動しない
- supervised worktree は `output/dev-wave-supervisor/runtime/<run-id>/worktrees/wNNN`
  (gitignored) に作る。`.claude/worktrees/` は使わない (fresh clone で main の clean gate を
  壊さないため、D74)
- **push・rebase・merge・force・自動 retry・自動 worktree 削除・`submodule deinit` は
  supervisor の API に存在しない** (git runner の allowlist 表を構造テストで固定)。
  local main への ff-only land は child (/dev-wave 段 9) の責務で、supervisor は結果を
  独立確認するだけである
- check script 群 (`tools/check_*.py`・`tools/task_runs`・`tools/run_tests.py`・
  `tools/task_run_check.py`・テスト木) は wave 開始時 (before SHA) の git object から
  digest を取り、wave が変更していたら `trust-root-changed` で停止する。check の実行は
  監査対象 SHA の隔離 checkout で行う

## 上限は全部明示 — 既定値なし

`serve` は profile の絶対上限 (max-waves / per-wave・total timeout / per-wave・total
budget / 出力 byte / run byte)・required hook・model allowlist を**全部必須引数**とする。
`client submit` の上限は明示指定が必須で、欠落・矛盾・profile cap 超過は **run を作らずに**
拒否し、容量上限付きの root 監査 log (`invalid-requests.jsonl`) にのみ記録する。
budget は spawn 前に「残額予約」され、child へ渡る上限は min(per-wave, total 残)、受理される
累積 cost も total を超えない (**supervisor が拘束するのは渡す上限と受理額まで** — child が
上限を無視した実支出は非目標 7 のとおり拘束外)。total deadline は durable run 作成時点から
CLOCK_BOOTTIME で計時し、各 side-effect helper の入口で残時間を検査する。秒未満の残は
期限切れとして扱う (fail-closed 方向)。

## private runtime

`output/dev-wave-supervisor/runtime/` (gitignored、0700/0600) に run ごとの
control WAL (`events.jsonl`、単一 writer・append-only + fsync)、raw child stdout/stderr、
create-only の worker/child 開始・終了記録、sanitized receipt・checks を分離保存する。
WAL append/fsync 失敗後は新しい side effect を始めない (fail-closed)。fsync 失敗を観測した
run は poison され、status にも poisoned が優先表示され、同一 daemon instance への次の
submit も拒否され、人間の明示操作なしに resume できない。run bootstrap は staging → rename で、WAL 先頭 record の fsync 成功までは run は
存在しない。cancel (API・SIGINT/SIGTERM・shutdown のすべての経路)・worker spawn は
intent (prepare) → fsync → 実行 → observe の順で WAL に束縛され、identity 照合に失敗した
signal は `signalled` と記録せず ambiguous 扱いにする。`status.json` / `summary.md` は WAL から再生成できる cache であり、
存在だけで完了を判断しない。

## 状態機械と reason code

状態は `created → preflight → ready → wave-prepared → child-running → child-exited →
verifying → wave-accepted → (ready | completed)`、停止は `stopping → blocked | failed |
interrupted`。`stopping → completed` は `no-actionable-task` に限る (D74)。terminal からの
自動遷移はない。daemon 再起動時は非 terminal run (staging・poison 含む) が 1 件でもあれば
新規 submit を拒否する (recovery gate)。`resume RUN_ID` は「accepted 済み wave の Git + receipt 一致 (HEAD・branch・main と
submodule の cleanliness・repo identity の再照合を含む) → 同 wave 確定 (child 再実行なし)」
までを reconcile し、それ以外の実行有無不明 gap は `ambiguous-recovery` で停止する。reason code は閉集合
(`tools/dev_waves/schema.py` の `ReasonCode` が正本)。

## v1 が主張しないこと (明示非目標)

1. **同一 UID からの防御。** child・操作者は daemon と同じ UID で動くため、runtime の
   WAL・manifest・socket に物理アクセスできるし、handshake だけ応答して他を real `claude`
   へ委譲する wrapper を作ることもできる。fake handshake・0700/0600・append-only は
   **事故に対する契約であり、同一 UID の意図的迂回への防壁ではない** (設計 §7.3 と同水準)。
   採用済みの機械対策は lock inode 再照合と control 面 path の child manifest 非掲載のみ
2. **敵対的 nested-launch の遮断。** `CLAUDECODE=1` の拒否は事故防止 guard であり、
   env を剥がす wrapper による迂回は防げない
3. **commit の意味的監査。** receipt に正直に列挙された「想定外だが隠されていない commit」を
   機械では拒否しない。隠れ commit (receipt と `rev-list` の不一致) は拒否する
4. **Git 観測の完全な TOCTOU 遮断。** snapshot は安定化再試行つきだが、最終検査と
   `wave-accepted` 記録の間に外部プロセスが main を動かす窓は残り、この窓での改変の
   検出は保証しない
5. **孤児 grandchild の完全回収。** 二重 setsid で process group から脱出した孫は
   group kill の対象外 (leader exit 後の残存 PG 検査で検出は試みる)
6. **NFS 上の crash durability。** fsync rc=0 は NFS のクラッシュ耐久を証明しない。
   lease は hostname + boot id で単一 host に束縛する (`foreign-lease`)
7. **child の実支出・runtime 外書込みの拘束。** supervisor が拘束するのは child へ渡す
   上限値・受理する累積 cost・runtime 配下の artifact 合算量まで。child が上限を無視した
   実支出や、runtime 外 (HOME・/tmp 等) への書込み総量は OS 側の quota でしか拘束できない
8. **「金額を保証した」という記録。** enforceable でない認証形では max-waves・deadline・
   process timeout が代替上限であり、金額保証とは記録しない
9. **real CLI との exact argv・実 envelope の適合。** 親の実測は flag の存在確認まで。
   exact な文法適合は real 無課金 canary (段階 4) まで未証明として扱う。
   pilot 中は [T-069] 裁定により `--no-session-persistence` を argv に**入れない**
   (禁止 token として構造検査)

## real 開放前に必要なユーザー裁定 (裁定パッケージ、worklog 参照)

1. per-wave / total の timeout・cost 具体値と、client 宣言値への絶対上限値
2. real child の settings/hook 必須政策 (現行 `.claude/settings.json` に push deny は無い)
3. [T-069]「実装前に明示指定」の読みの確認
4. 上記「v1 が主張しないこと」の受諾確認

## CLI (実 parser から転記)

```text
python3 tools/dev_waves.py doctor [--repo-root PATH] [--claude-executable PATH] [--probe-cli] [--probe-timeout-s N] [--probe-fs]
python3 tools/dev_waves.py serve --repo-root PATH --profile default \
  --fake-child-executable PATH --fake-child-sha256 HEX --model NAME --allowed-model NAME \
  --effort NAME --check-timeout-s N --termination-grace-s N --required-hook SPEC \
  --max-waves N --max-per-wave-timeout-s N --max-total-timeout-s N \
  --max-per-wave-budget-usd D --max-total-budget-usd D --max-wave-output-bytes N --max-run-bytes N
python3 tools/dev_waves.py client submit --max-waves N --profile default \
  --per-wave-timeout-s N --total-timeout-s N --per-wave-budget-usd D --total-budget-usd D \
  --max-wave-output-bytes N --max-run-bytes N [--request-id UUID]
python3 tools/dev_waves.py client status RUN_ID [--compact|--json]
python3 tools/dev_waves.py client cancel RUN_ID [--request-id UUID]
python3 tools/dev_waves.py validate RUN_ID
python3 tools/dev_waves.py resume RUN_ID
python3 tools/dev_waves.py export RUN_ID --output PATH
```

`doctor` は model を呼ばない (`--probe-cli` も `--version`/`--help` のみで `-p` を付けない)。
`export` は session ID・URL・credential・raw prompt/output を除いた sanitized summary のみを
新規ファイルへ書く。

## テスト

`orchestrator/tests/test_dev_waves_*.py` (**11 ファイル・203 node**、いずれも二重 runner
対応)。fake child + temp Git repo で failure injection (budget 予約・deadline 到達後の
side-effect 不開始・artifact 合算超過・trust-root runner 改変・daemon の実 SIGKILL→restart・
WAL fault・PID reuse・SIGHUP-ignore 負例を含む) を実走する。real claude・network・課金は
使わない。deadline の秒未満切捨ては期限切れ側 (fail-closed) に倒してある。
