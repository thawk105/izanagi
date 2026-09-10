## 採る案とその理由

**案 A を採る。** 失効した quota 観測だけを無効化し、旧・新 registration commit の証拠を同一 bundle 内で artifact 単位に束縛する。

理由は次のとおり。

- `observed_at_utc + reset_seconds` を過ぎた観測だけを「次の request の可否を決める材料として古い」と扱える。新しい応答を得た後は、現行の `remaining - 30 >= credits_per_request` をそのまま適用できる。
- 正規化 request は catalog から再構築して旧 checkpoint の完全 request と一致させるため、契約 §8 の非意味的修繕に収まる。epoch・query ID・完走述語は変えない。
- 案 B は新 root なら persisted quota が無いため発行できるが、[runner.py:695](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/orchestrator/axis1_search/runner.py:695) の quota 状態が bundle 単位だからにすぎない。旧 Q1 checkpoint は [run_axis1_search.py:122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/tools/run_axis1_search.py:122) と [validator.py:1110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/orchestrator/axis1_search/validator.py:1110) の絶対 root 束縛により新 root へ移せず、[runner.py:1243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/orchestrator/axis1_search/runner.py:1243) 以降も元 root の ledger・page を必要とする。
- bundle validator は [validator.py:968](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/orchestrator/axis1_search/validator.py:968) で root を一つしか受けず、[validator.py:933](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/orchestrator/axis1_search/validator.py:933) から catalog 全体の identity map を bundle ごとに導出する。二つの bundle を一つの `exact_identity_map` として検査する合成面はない。
- 実 bundle の静的確認では checkpoint 169 本・page 593 本があり、checkpoint–ledger と page–ledger の `registration_commit` 不一致はいずれも 0 件だった。この既存の artifact 単位束縛を、新旧 commit 併存時にも維持できる。

## 変更する file と行

- [orchestrator/axis1_search/runner.py:230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/orchestrator/axis1_search/runner.py:230)

  現在は `QuotaObservation.permits_next()` が残量と予約だけを判定し、時刻を見ない。`permits_next()` 自体は変更せず、近傍に「観測期限を過ぎたか」だけを返す helper を置く。

  `observed_at_utc` が timezone-aware ISO 時刻、`reset_seconds` が非負整数で、`now >= observed_at + reset_seconds` の場合だけ expired とする。欠落、parse 不能、naive datetime、負値は expired とせず fail-closed にする。

- [orchestrator/axis1_search/runner.py:651](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/orchestrator/axis1_search/runner.py:651)

  `_load_persisted_quota()` に現在時刻を渡し、expired な観測だけ `None` として返す。runtime file はこの段階で削除・書換えせず、次の実応答を [runner.py:1765](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/orchestrator/axis1_search/runner.py:1765) で観測した時点で既存処理により更新する。

- [orchestrator/axis1_search/runner.py:1625](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/orchestrator/axis1_search/runner.py:1625) と [runner.py:1685](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/orchestrator/axis1_search/runner.py:1685)

  初回 gate と retry 前の再読の両方で、同じ時計による失効判定を通す。片側だけ直すと retry loop が古い runtime を再ロードして再施錠するため、二箇所とも必要。

  expired の場合に許すのは登録済み request 1 本の発行だけである。その応答から得た新観測に対して [runner.py:2103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/orchestrator/axis1_search/runner.py:2103) の既存予約 gate が直ちに再適用される。

- [orchestrator/axis1_search/runner.py:2269](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/orchestrator/axis1_search/runner.py:2269) と [runner.py:2381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/orchestrator/axis1_search/runner.py:2381)

  resume API に「今回 preflight を通した registration commit」を明示的に渡す。旧 checkpoint は request・cursor・prefix の出所として読み、[runner.py:2299](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/orchestrator/axis1_search/runner.py:2299) の catalog 再構築との完全一致を維持する。一致後の `_run_leaf_impl()` には新 commit を渡し、新規 page、ledger、後継 checkpoint、manifest は新 commit を記録する。旧 checkpoint は変更しない。

- [tools/run_axis1_search.py:114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/tools/run_axis1_search.py:114)

  現在の line 118 の即時 commit 不一致拒否を、限定的な registration 移行へ置き換える。catalog path、bundle root、run ID の拒否は維持する。新 commit の `verify_registration()` が成功し、旧 checkpoint の選択 request が現 catalog から再構築した request と完全一致した場合だけ旧→新 commit を許す。

  [run_axis1_search.py:170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/tools/run_axis1_search.py:170) では新 CLI commit を resume API へ渡す。不一致を無条件に許す実装にはしない。

- [orchestrator/axis1_search/validator.py:1085](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/orchestrator/axis1_search/validator.py:1085)

  現在の line 1105 は全 checkpoint と最新 manifest の commit が同一であることを要求する。これを次の artifact 単位の束縛へ置き換える。

  - checkpoint の epoch、catalog SHA/path、bundle root、query、index は従来どおり一致必須。
  - checkpoint の `registration_commit` は、その `completed_ledger` の `registration_commit` と一致必須。
  - checkpoint 内の三つの完全 request は現 catalog から同じ page/position で再構築した request と完全一致必須。
  - page evidence の `identity.registration_commit` は、その page が参照する ledger の `registration_commit` と一致必須。
  - manifest の `registration_commit` は、その bundle を最後に finalize した現行 runner commit とする。

  これにより、旧 checkpoint を「旧 bytes の生成元」として保持しながら、新規 artifact を新 commit に束縛できる。単に line 1105 を削除するだけの弱体化にはしない。

- [tools/check_axis1_search.py:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/tools/check_axis1_search.py:97)

  line 103 に同じ commit 一致 consumer が残っているため、launcher と同じ限定 predicateを使う。ここを残すと、実行はできても正式な checkpoint preflight が旧 checkpoint を拒否する。

- [orchestrator/schemas/axis1_search_checkpoint.schema.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/orchestrator/schemas/axis1_search_checkpoint.schema.json:1)

  **変更しない。** v2 は既に artifact ごとの40桁 `registration_commit` と `previous_checkpoint` の digest 束縛を表現できる。新しい epoch、resume action、移行専用 schema field は増やさない。

## 登録 commit の張り替え手順

1. quota 失効、resume commit 引継ぎ、validator、二つの CLI consumer、テストを一つの実装 commit `C_reg2` に含める。契約文書・catalog・epoch・query ID は変更しない。
2. 関連テストを `tools/run_tests.py` 経由で実行し、`check_codex_agents.py`、`check_docs.py`、commit 後の `check_ai_provenance.py` を通す。pytest 直接起動はしない。
3. 実行用 worktree は絶対 path を変えず、`d0ba65c01…` から `C_reg2` へ detached HEAD を張り替える。これで旧 checkpoint の `bundle_root` 束縛を維持する。
4. `C_reg2`、既存 catalog、登録済み16 path で registration preflight を実行し、`HEAD == C_reg2`、登録 path clean、catalog blob 一致を確認する。
5. 再開には pristine bundle 内の発行済み `checkpoints/000084.json` を使う。実測用で bundle から戻された `probe-checkpoint-000170.json` は移行元にしない。
6. CLI には `--registration-commit C_reg2` と旧 `000084.json` を同時に与える。旧 checkpoint の bytes、ID、commit、cursor、ledger digest は変更しない。runner は request 同一性を確認してから新 commit で続行する。
7. quota が再び予約へ達した場合は、create-only の新 checkpoint が `registration_commit=C_reg2` と旧 checkpoint の `previous_checkpoint` digest を持つ。Q1 が terminal になった場合は旧 checkpoint は歴史的 artifact として残るが、active resume point には選ばれない。
8. 新 runner が finalize した manifest は `C_reg2` を現行 commit として持つ。main 側 checker で bundle 全体を再検査し、旧・新 artifact の commit–ledger 束縛と `exact_identity_map=true` を確認する。
9. 以後は同じ bundle root、同じ epoch、既存の登録順で77 leafを進め、各窓の停止時に新 checkpoint を残す。旧 page、ledger、raw、checkpoint は書き換えない。既存設計上 mutable な runtime と exact-set manifest/digest のみ更新される。

## 新設・改訂するテスト

- 正例 — `test_expired_quota_resumes_historical_checkpoint_under_new_registration_commit`

  旧 commit の checkpoint と `remaining=10`、有効な観測時刻・reset を bundle に置き、時計を期限後へ進める。新 commit を指定して resume し、登録 request が1回発行されること、新応答で quota が置換されること、新 artifact と manifest が新 commit を持つこと、旧 checkpoint bytes が不変であること、mixed-commit bundle を validator が受理することを確認する。

- 負例1 — 既存 `test_quota_reserve_persists_across_leaf_sessions` を改訂

  reset header と期限内の二つ目の時計を明示する。`remaining=35`、reserve 30、cost 10 なので `35 - 30 < 10`。二つ目の leaf は従来どおり `paused_quota`、`request_count=0`、transport call 0 とする。既存期待値は変えない。

- 負例2 — `test_registration_rebind_rejects_changed_checkpoint_request_before_http`

  旧 checkpoint の filter、position、sort、page size、projection のいずれか一つを現 catalog と異ならせ、新 commit での rebind を試す。`PreflightError`、transport call 0、bundle bytes 不変を要求する。同じ fixture を bundle validator にも渡し、`checkpoint_request_mismatch` を要求する。

## 受理集合の変化

| 入力 | 変更前 | 変更後 |
|---|---|---|
| 期限を過ぎた低残量観測 | 永久に `paused_quota`、0 request | 古い観測を可否判定から外し、登録 request 1 本で再観測 |
| 期限内で `remaining - 30 < cost` | `paused_quota`、0 request | 同じく拒否。変更なし |
| reset または観測時刻が欠落・不正 | 実質的に持続 quota として扱う | expired と推定せず fail-closed。低残量なら拒否 |
| 旧 checkpoint + 同じ commit | 受理 | 受理。変更なし |
| 旧 checkpoint + 新 commit + request 完全一致 | line 118 で拒否 | 新 commit の registration preflight 後に受理 |
| 旧 checkpoint + 新 commit + request drift | 拒否 | HTTP 前に拒否 |
| manifest が新 commit、旧 checkpoint が旧 commit | line 1105 で bundle 拒否 | checkpoint–ledger、page–ledger、catalog request が一致するときだけ受理 |
| root を変えた旧 checkpoint | 拒否 | 引き続き拒否 |
| 完走述語、条件1〜6、epoch、query ID の変更 | 対象外 | 引き続き対象外・拒否 |

## 積み残しと危険

- OpenAlex 条件1は T-2091 の裁定待ちである。取得が進んでも `axis_complete=false`、`未完走` のままでよい。
- `observed_at + reset_seconds` は API が返した観測値に基づく期限であり、「窓長を測定した」という主張にはしない。時計が期限前へ戻った場合も expired とせず停止側へ倒す。
- baseline bundle には旧 commit の checkpoint が169本ある。`000084` だけを例外扱いすると他168本で validator が落ちるため、artifact 単位の一貫性として扱う必要がある。
- manifest の commit 一致を単純削除すると provenance gate を弱める。checkpoint–ledger、page–ledger、catalog 再構築 request の三束縛は必須である。
- 既存の凍結記録が pin する旧 manifest digest と、追記後の現行 manifest digest は別時点の事実として新しい実行記録に併記する。旧記録や旧 artifact を遡及更新しない。
- 本 wave は1窓分の取得と次の checkpoint までで受理可能であり、78 leaf の完走を要求しない。
- pytest は今回実走していない。上記は静的検査に基づく author 向け計画である。

## 総括

案 A とし、quota 予約式には触れず、期限を過ぎた観測だけを一度の再観測対象にする。登録 commit の移行は旧 checkpoint を書き換えず、新 commit の preflight、catalog からの request 完全再構築、artifact–ledger の commit 束縛で成立させる。これなら同一 bundle・同一 epoch・同一 query ID のまま Q1 cursor と残り77 leafを継続できる。