# 段 4 裁定 (親、2026-09-17 21:52 JST 頃、consult 完了 21:50 と author 投入 21:54 の間) — [T-2670]

## §1 consult A (裁定・契約整合) の所見

| # | 判定 | 採否 | 処置 |
|---|---|---|---|
| A1 | refuted | — | plan の移設位置 (commit-rev-parse 直後・commit-message-postcheck 前) を採用。P2 を修正して確定 |
| A2 | refuted | 限定を採用 | docs で「preclaim 受領証は条件付きで再利用 (bindings 一致時)、不一致なら全走。どちらでも取り込み分は被覆」と書く。D2045 を根拠に加える |
| A3 | refuted | scope 外維持 | `--range` 化は authoritative でない (epoch 適用差・append-only 検査なし・merge 自身を含まない)。`--head` 新設は「別設計で今回扱わない」と分けて書く |
| B1 | refuted | P1 確定 | 契約 comment (code)・負例 test・F365 追補を必須成果物にする。「cleanup 関数の変更不要」を「後始末契約の更新不要」と読み替えない |
| B2 | real (docs) | 採用 | 監査赤後の manager の次手 3 行を insight と F365 追補へ書く (下の §4)。親の追加所見: P1 の終端状態 (merge commit が残る) は現行でも同じ — 現行は監査が素通りし受入全走の後に land の監査で止まる。P1 は新しい状態を作らず、検出を受入投入前へ早める |
| B3 | real (docs) | 採用 | D518 は誤引用。前進 merge の契約は D689 / D731 / D732。「2 親だから land 適格」の一般化を削る |
| B4 | refuted | 表現採用 | lease 解放は所有権条件つき (HELD_SELF は解放しない、解放失敗は cleanup failure) |
| C1 | real | 済 | verbatim を D2044 範囲内で切り直し済み。plan の差し替え要求は撤回 |
| C2 | real (docs) | 採用 | 選択集合 = `{policy} ∪ rev-list(policy..HEAD)` と書く |
| C3 | 表現 | 採用 | brief の「実測した現状」は静的読解。動的実測は段 5/6 の焦点走・変異走で行い、結果を worklog に書く |

裁定パッケージ候補: 現時点で無し。保持した merge の違反が既存の是正契約 (前進訂正 commit / 既知違反登録のユーザー裁定) で解消できない事例が出た場合だけ返す。

## §2 consult B (実効性) の所見

| # | 判定 | 採否 | 処置 |
|---|---|---|---|
| B01 / B02 | refuted | — | plan の更新表は網羅。変異 matrix の runner = `orchestrator/tests/test_dev_wave_wait.py` を中心に、consumer の `test_dev_wave_wait_compute.py`・`test_run_tests_shards.py` を含める |
| B03 | refuted | 採用 | 実 git 負例を主証拠にする。開始時 HEAD が main-only commit の非祖先・終了時 HEAD が 2 親・違反 SHA が終了時 HEAD の祖先、を明示 assert |
| B04 | real | 採用 | 変異走で M1〜M3 の kill reason を「実 git 負例の主張 (runner 計数 / stage) の赤」で確認する。順序 pin の赤は補助証拠として分けて記録 |
| B05 | real | 採用 | 偽 checker の trace に「呼び出し種別・観測 HEAD・判定 rc・lease file の有無」を記録し、commit 後監査時に lease 存在・終了時に不在を対で assert。runner は `_write_exact_runner` 型で repo 外の計数 file に追記 |
| B06 | real | 採用 | 初回は probe 走で観測 node を集めてから本走。M4 を追加 (KILLED 期待)。M5 (stage 名変更) は diagnostic pin として登録し KILL に数えない |
| B07 | real | 採用 | 新規 CLI subprocess に `timeout=120` を付ける。親が正常系と各変異の所要を測る |
| B08 / B09 | real (docs) | 採用 | 「両監査間で HEAD と checker の意味が変わらない通常経路では同一集合。未 commit の main-only commit は加わらない」と限定。brief の行範囲は 3831–3900、cleanup 定義は 3286 / 3330 と訂正。既存 path-aware checker は history を常に緑にするので**新規 fixture** を書く |
| B10 | real | 済 | C1 と同じ |
| B11 | refuted | 採用 | plan は gate を足していない。fake 派生 test は**作らない** (既存 routing test と実 git 負例で足り、test 時間の純増を避ける) |

## §3 plan v2 (確定)

1. `tools/dev_wave_wait.py` `_run_acceptance_attempt`: `merge-history-provenance` の `_run_capture(...)` を
   `committed_sha = _head_sha(effects, repo, "commit-rev-parse")` の**直後**、`commit-message-postcheck` の**前**へ移す。
   argv・stage 名・`diagnostic_reason="full-history-provenance"`・`capture_failure_output=True` は保存。
   `active_lifecycle.merge_pending = False` は `git commit` 直後のまま (監査成功後へ遅らせない)。
   移設先に契約 comment (周囲の日本語 comment と同じ密度で 3〜5 行): HEAD = merge commit なので取り込んだ main の commit と
   merge 自身が選択集合に入る / ここで赤なら merge commit は残る (MERGE_HEAD は無く abort 対象は無い)、所有 lease は解放、
   受入 command は投入しない / claim 前監査は不変。
2. `_AcceptanceLifecycle` / `_cleanup_lifecycle` / `_cleanup_after_claim` / `_abort_pending_merge` の実処理は変更しない。
   `merge_pending` の意味 (未完了 merge の abort 権限であって commit 後の巻き戻し権限ではない) を dataclass の comment に 1 行足す。
3. `orchestrator/tests/test_dev_wave_wait.py`: plan の更新表どおり。`_provenance` helper を分離 (3 箇所)、`_STAGES` と
   `merge_stages` / `history_provenance_stages` / abort 集合 (6812・6912) の更新、abort 期待の反転 2 本
   (`test_nonzero_stage_blocks_submission_and_releases[merge-history-provenance]`、
   `test_merge_history_provenance_failure_blocks_submission_releases_and_returns_reason`)、
   `test_merge_history_provenance_unexpected_rc_fails_closed` に commit 済み・abort 不在を追加、
   `test_malformed_ai_agent_message_fails_provenance_before_commit` から merge 側 history 期待を除く、他は正例維持。
4. 新規負例 (実 git) `test_real_git_main_only_history_violation_blocks_acceptance_after_commit`:
   `_real_waiter_repo` + 新規偽 checker (temp repo の `tools/check_ai_provenance.py`。`--message-file` あり → 0。引数なし →
   repo 外の SHA file を読み `git merge-base --is-ancestor <sha> HEAD`: rc=0 → 理由を stderr に出し 1、rc=1 → 0、他 → 非 0。
   trace file に種別・観測 HEAD・rc・lease file 有無を 1 行追記) + `_write_exact_runner` 型の計数 runner (repo 外 file に追記)。
   subprocess で `acceptance` CLI を起動 (`timeout=120`)。主張: rc=70・stage=`merge-history-provenance`・source_rc=1・
   理由本文 / runner 計数 0 / lease 不在 (終了時) かつ trace の commit 後監査行で lease 存在 / HEAD ≠ 開始時 tip・2 親 (開始時 tip と
   main tip) / 違反 SHA が終了時 HEAD の祖先で開始時 tip の非祖先 / MERGE_HEAD 不在・tracked clean / receipt・log 不在。
   fake 派生版は作らない。
5. `tools/check_ai_provenance.py`・`tools/dev_wave_land.py`・`tools/dev_wave_cleanup.py`・`tools/known_violations/` は不変。
   新しい gate・検査・台帳を足さない。

## §4 監査赤後の manager の次手 (B2、docs へ)

1. 理由本文・違反 SHA・保持した merge commit SHA を記録し、所有 lease の解放結果を確認して同じ投入を止める。
2. main 由来 / merge 自身 / 実行不能 (infra) を切り分け、既存契約に従って是正を wave の履歴へ反映する
   (main の前進訂正 commit を親が `git merge` で取り込む、既知違反登録が要るならユーザー裁定へ返す)。
3. wave HEAD の authoritative 監査 (`python3 tools/check_ai_provenance.py`) が緑になってから受入を再投入し、新しい受領証で land する。

## §5 変異事前登録 (DW-M01、B-057)

対象 file: `tools/dev_wave_wait.py` (変異 anchor は移設後の block)。runner: `orchestrator/tests/test_dev_wave_wait.py`、
`orchestrator/tests/test_dev_wave_wait_compute.py`、`orchestrator/tests/test_run_tests_shards.py`。初回は probe 走で観測 node を集める。

| ID | 変異 | 期待 | 専属 killer (意味的証拠) | 補助 (順序 pin) |
|---|---|---|---|---|
| M0 | 移設 block の comment だけ変更 | SURVIVED (対照) | — | — |
| M1 | 監査呼び出しを `git commit` 前 (現行位置) へ戻す | KILLED | 実 git 負例 (監査緑 → command 投入 → runner 計数 1 → 赤) | `test_merge_sequence_and_postcheck_are_exact`、`test_nonzero_stage_blocks_submission_and_releases[*]`、`test_postclaim_merge_without_implementation_conflict_accepts_self_report` 等 |
| M2 | 監査呼び出しを削除 | KILLED | 実 git 負例 | 上記 + 既存 history 赤 2 本 |
| M3 | 監査赤を握り潰す (`_run_capture` の非 0 を無視) | KILLED | 実 git 負例 | `test_merge_history_provenance_failure_blocks_...`、`..._unexpected_rc_fails_closed`、stage param |
| M4 | `merge_pending = False` を監査成功後へ遅らせる | KILLED | 実 git 負例 (監査赤 → cleanup が `merge --abort` を試み MERGE_HEAD 不在で失敗 → rc/abort 不在の主張が赤) | 既存 history 赤 2 本 (abort 不在) |
| M5 | 移設した監査の stage 名だけ変更 | diagnostic pin (KILL に数えない) | stage 名を主張する test | — |

各変異は実装後に「同じ入力を拒否する層が前後・内側に無く赤理由が一つに絞れる」ことを確認し、絞れなければ登録せず再照準 (F28/F820)。
