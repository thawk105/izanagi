指定された必読ファイルはすべて読了した。以下は静的検査結果であり、pytest は実行していない。既知の manifest 一意性矛盾は所見から除外した。

### 1. [must-fix] 同一 poll 内の usage 巻き戻しで token 上限を迂回できる

- 攻撃入力・状態: 1 回の tail で、`cli_reported=1000` の `token_count`、続けて `input=1000, cached=999, output=1, total=1001`（`cli_reported=2`）を読ませ、stdout 最終 usage を後者に合わせる。`max_cli_reported_tokens=100` でも、最後の累積値だけが残るため `limit_trigger=null`、`outcome=accepted` になる。`total_tokens` は 1000→1001 なので ledger の唯一の単調性検査も通る。
- 壊れる不変条件: 一度でも観測 proxy が上限を超えた attempt は accepted にしない。
- 成果物影響: receipt と台帳の `cli_reported` が 2 となり、実際には 1000 を観測した job が accepted 集合へ入る。
- 該当: [codex_worker_launch.py:661](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:661)、[codex_worker_launch.py:978](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:978)、[codex_worker_launch.py:858](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:858)、[codex_worker_ledger.py:500](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_ledger.py:500)

### 2. [must-fix] `token_count.info=null` が model call を不可視化する

- 攻撃入力・状態: 任意個の `token_count` with `info=null` と、最後に 1 件だけ有効な `token_count` を置く。null は invalid にも model call にも数えられず、有効な 1 件だけで `metering_status=complete` になる。`max_model_calls=1` でも accepted 可能。
- 壊れる不変条件: 観測した `token_count` は計数するか、metering 不完全として拒否する。receipt の `"observed_token_count_events"` という意味とも矛盾する。
- 成果物影響: receipt/台帳の `model_calls` が過少となり、上限超過 job が accepted 集合へ入る。
- 該当: [codex_worker_launch.py:657](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:657)、[codex_worker_launch.py:726](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:726)、[codex_worker_launch.py:1190](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1190)、[codex_worker_ledger.py:474](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_ledger.py:474)、[test_codex_worker_ledger.py:454](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/orchestrator/tests/test_codex_worker_ledger.py:454)

### 3. [must-fix] `check-receipt` だけで limit-stop receipt を accepted に昇格できる

- 攻撃入力・状態: TERM handler が正常 output と terminal usage を残した limit-stop receipt に対し、receipt 内だけを次のように変更する: 上限を actual より大きくする、`limit_trigger=null`、`attempt.accepted=true`、`outcome=accepted`、`stop_reason=completed`、`launcher_rc=0`、receipt の `output_path` を既存 attempt output に、`output_sha256` をその hash にする。CLI は期待上限・期待 output path・期待 prompt hashを受け取らないため、hash、validator、metering、manifest membership の再計算を全部通して rc=0 になる。
- 壊れる不変条件: checker は receipt の自己申告から独立して受理判断と policy identity を再構成する。
- 成果物影響: 元は `not_accepted` だった attempt が、改変 receipt では正式な accepted 集合へ入る。
- 該当: [codex_worker_launch.py:1523](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1523)、[codex_worker_launch.py:1565](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1565)、[codex_worker_launch.py:1626](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1626)、[codex_worker_launch.py:1822](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1822)、[codex_worker_launch.py:1886](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1886)

### 4. [must-fix] receipt 後の rollout 追記が checker を通り、ledger 値を改変する

- 攻撃入力・状態: accepted receipt 作成後、sealed byte offset より後へ新しい `token_count`、`agent_message`、`task_complete` を追記する。checker は prefix hash だけを見るので rc=0。一方 ledger は EOF まで読み、追記を正規証拠として扱う。
- 壊れる不変条件: receipt と台帳は同じ rollout snapshot を参照する。
- 成果物影響: receipt を一切変えずに、台帳の `model_calls`、token 値、さらに `outcome` を後から変更できる。
- 該当: [codex_worker_launch.py:1792](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1792)、[codex_worker_ledger.py:389](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_ledger.py:389)、[codex_worker_ledger.py:474](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_ledger.py:474)、[test_codex_worker_launch.py:797](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/orchestrator/tests/test_codex_worker_launch.py:797)

### 5. [must-fix] `/proc` 読取不能を residual=0 と解釈し、偽の終了確認を作る

- 攻撃入力・状態: leader が同一 process group に長寿命子を残して正常終了し、`/proc` 全体または子の `stat` 読取を失敗させる。scan 失敗・個別読取失敗はいずれも「未知」でなく 0 件へ落ち、normal reap は `termination_verified=true` を返す。
- 壊れる不変条件: 終了を肯定できない状態は fail-closed にする。
- 成果物影響: 生存子がいるのに receipt は `process_group_residual=0`、`termination_verified=true`、`outcome=accepted` となる。
- 該当: [codex_worker_launch.py:763](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:763)、[codex_worker_launch.py:819](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:819)、[codex_worker_launch.py:858](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:858)、[worker.py:146](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/dev_waves/worker.py:146)

### 6. [must-fix] manifest 1 entry に一致する rollout が複数あっても非 strict では rc=0

- 攻撃入力・状態: 異なる directory に、同じ filename UUID と同じ exact `session_meta.session_id` を持つ rollout を 2 本置く。manifest はその session を 1 entry だけ持つ。両方が三者一致し、set ベースの欠損検査も通る。`duplicate_session_id` は issue になるだけで、`--strict` なしでは rc=0。
- 壊れる不変条件: manifest の 1 session entry は一意な 1 rollout record に対応する。R10 の完全性を strict に戻さない。
- 成果物影響: 台帳の sessions、model calls、token totals が二重計上され、1 attempt が複数 record として受理される。
- 該当: [codex_worker_ledger.py:977](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_ledger.py:977)、[codex_worker_ledger.py:1033](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_ledger.py:1033)、[codex_worker_ledger.py:1105](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_ledger.py:1105)

### 7. [must-fix] wall-clock hard cap が preflight/postflight を計測しない

- 攻撃入力・状態: `codex --version` を timeout 未満の 4 秒待たせ、実 `exec` を 0.1 秒未満で正常終了させ、`max_wall_clock_s=0.2` とする。clock は version/hash/preflight 完了後に始まり、receipt 作成後の publish/self-check も actuals に入らない。
- 壊れる不変条件: CLI が称する wall-clock hard cap は worker job 全体を覆う。
- 成果物影響: end-to-end では上限を数秒超過した job が、receipt の `actuals.wall_clock_s<=limit` と `outcome=accepted` を持つ。
- 該当: [codex_worker_launch.py:1225](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1225)、[codex_worker_launch.py:1305](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1305)、[codex_worker_launch.py:1168](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1168)、[codex_worker_launch.py:1381](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1381)

### 8. [must-fix] 完全 receipt の上書き拒否が TOCTOU

- 攻撃入力・状態: 異なる 2 job が同じ receipt path、別 artifact/output path を使って並行起動する。両方が preflight 時点で receipt 不在を確認でき、最後は双方とも無条件 `os.replace` する。先行 job が self-check を終えた後に後行 job が置換すれば、両方 rc=0 でも最終 receipt は 1 件だけになる。
- 壊れる不変条件: 既存の完全 receipt は並行時も create-only で、決して上書きされない。
- 成果物影響: manifest/ledger に 2 job が残る一方、先行 accepted job の receipt 参照が消失する。
- 該当: [codex_worker_launch.py:354](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:354)、[codex_worker_launch.py:1298](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1298)、[codex_worker_launch.py:1385](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1385)

### 9. [must-fix] manifest の repo/base header は形式検査だけで実体へ束縛されない

- 攻撃入力・状態: `--cwd` と無関係な既存 directory を `--repo-root` にし、任意の lowercase hex40 を `--base-commit` に渡す。初回 manifest はそのまま作られる。また receipt 後にこの 2 field だけを別の有効値へ変更しても、checker は wave_id しか比較しない。
- 壊れる不変条件: create-only header は実行した repository/base snapshot の identity である。
- 成果物影響: accepted session と台帳を別 repository・別 commit の証拠として参照できる。
- 該当: [codex_worker_launch.py:1248](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1248)、[codex_worker_launch.py:1345](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1345)、[codex_worker_launch.py:1756](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1756)、[codex_worker_ledger.py:265](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_ledger.py:265)

### 10. [scope外候補] manifest への foreign entry 追記を既存 receipt は検出しない

- 攻撃入力・状態: receipt 完成後、同じ wave_id の manifest に別 job/session entry と対応 rollout を追加する。membership は subset 検査なので既存 receipt は rc=0、ledger は追加 session も選択する。
- 壊れる不変条件: receipt が参照した manifest の受理集合が後から拡大しない。
- 成果物影響: 台帳の session/job 集合と totals に foreign entry が追加される。
- 該当: [codex_worker_launch.py:1089](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1089)、[codex_worker_launch.py:1812](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1812)、[codex_worker_ledger.py:959](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_ledger.py:959)

plan v2 が manifest seal ceremony を明示的に scope 外としているため must-fix にはしない。ただし現在の receipt は manifest snapshot の証明ではない。

### 11. [nit] `limit_trigger && accepted` の独立検査分岐は到達不能

- 攻撃入力・状態: 任意の `accepted=false` attempt。`elif` に入った時点で `attempt["accepted"]` は偽なので条件は恒偽。
- 壊れる不変条件: 独立の truth-table 防壁を装う分岐が実際に発火すること。
- 成果物影響: 直前の accepted semantic binding が同条件を守るため、現状の受理集合への単独影響はない。
- 該当: [codex_worker_launch.py:1496](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1496)、[codex_worker_launch.py:1508](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1508)

`cached_input_tokens > input_tokens` は launcher の [codex_worker_launch.py:539](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:539) と ledger の [codex_worker_ledger.py:212](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_ledger.py:212) の双方で拒否されており、この点の実装差は見つからなかった。

## 総括

**NO-GO**

最重要 3 件:

1. receipt 自己申告を書き換えるだけで limit-stop attempt を accepted に昇格できる。
2. 同一 poll 内の累積 usage 巻き戻しにより token 上限を実際に超えたまま accepted へ到達できる。
3. `/proc` 読取失敗が residual=0／`termination_verified=true` となり、生存 process group を伴う accepted receipt を作れる。