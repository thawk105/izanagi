## registration preflight

[preflight.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-unit-b/orchestrator/axis_b5_search/preflight.py) を実装しました。

- HEAD、clean 状態、commit tree と worktree の exact file set・mode・bytes を照合
- catalog の固定 SHA-256 と `render_catalog_json()` の byte 一致を検査
- 各 path の blob、mode、byte 数、SHA-256 を seal に保存
- `leaf-executor-provisional` と checkpoint / resume などの除外層を明記
- seal 自身の hash は未収録
- registration 失敗前には live transport を生成しないことを test 済み

commit 禁止のため、現在の実 repository に対する registration preflight の rc=0 は未実走です。

## live preflight と anchor registry

[anchor_registry.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-unit-b/orchestrator/axis_b5_search/anchor_registry.json) に 16 anchor、OpenAlex 16・arXiv 1・DBLP 13 の exact 30 member を転記しました。

- `G2-08` の主キーは DOI `10.1137/17M1154679`
- arXiv lookup key は別 field の `1710.11258`
- 3 種類の登録済み lookup URL だけを生成
- OpenAlex 404 は content type より先に `非収録` と判定
- media type parameter は無視
- 未知の正常応答形は `unclassified`
- W-ID drift は登録値と観測値を並べて保存し、追加 gate に不使用
- exact 30 のうち 1 件でも非成功なら `未完走`、開始不可
- timeout、User-Agent、間隔を逐語保存
- durable JSON を atomic write し、schema 検証後に保存

外部 request は実行していません。

## leaf runner

[runner.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-unit-b/orchestrator/axis_b5_search/runner.py) を実装しました。

- page size、位置 parameter、pagination kind、retry delay、host/path を固定
- 3 catalog collection を横断して leaf を exact 1 件解決
- offset は固定 step、OpenAlex 初回 cursor は literal `*`
- continuation cursor のみ percent encoding
- page 0 URL と catalog の byte 一致を検査
- 保存済み応答へ条件 1〜6 を適用
- OpenAlex AST は兄弟順のみ無視し、多重度・深さ・join・型・重複 key を保持
- 条件 2 は位置だけ、条件 3 は container の実要素数だけを使用
- 正常な部分最終 page を受理
- 重複 occurrence と DBLP cutoff 判定を消さずに保存
- 総件数 drift は page 0 から最大 1 回だけ再評価可能
- response header の同名重複、body digest、byte 数、最終 URL を保存
- control は request 完走値だけを返し、発火 field を持たない
- 軸全体の完走・RW3・成熟度 API は未作成

production `run_leaf` は registration preflight を再実行し、schema-valid な durable live record と同一 seal・exact 30 member を照合します。

## schema

draft-07 の次の 3 本を追加しました。

- [page evidence](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-unit-b/orchestrator/schemas/axis_b5_search_page_evidence.schema.json)
- [live preflight](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-unit-b/orchestrator/schemas/axis_b5_search_live_preflight.schema.json)
- [registration seal](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-unit-b/orchestrator/schemas/axis_b5_search_registration_seal.schema.json)

3 schema とも `Draft7Validator.check_schema` を通過しました。

## 実走した test

指定の自走 harness で実行しました。

- `orchestrator/tests/test_axis_b5_search_executor.py` 全 34 node: **34 passed**
- `orchestrator/tests/test_axis_b5_search_parsers.py` 全 20 node: **20 passed**
- `orchestrator/tests/test_plain_runner_coverage.py` 全 3 node: **3 passed**

追加で確認済みです。

- 所有 Python file の AST parse 成功
- 所有 JSON file の parse 成功
- `git diff --check` 成功
- catalog SHA-256 は登録値 `7eb8385e...4c346f` と一致
- 所有成果物に U+0300〜U+036F なし
- 変更は指定された所有 path だけ

## 未登録の運用値の扱い

既定値で補った箇所はありません。

本走発行は `UnregisteredRunPolicyError` で停止し、次の 6 項目を機械可読に返します。

- `expected_content_types`
- `timeout_s`
- `user_agent`
- `request_interval_s`
- `retryable_failures`
- `redirect_policy`

## 波及可能性

- 所有外の production caller は、registration commit と durable live preflight record の path を渡す必要があります。
- live preflight caller は timeout、User-Agent、request 間隔を必ず明示する必要があります。
- fixture root の追加・削除・byte 変更は registration seal の exact-set 検査へ波及します。
- runner・schema・registry の変更は seal 更新を必要とします。
- checkpoint / resume を後続 wave で追加すると runner bytes が変わるため、暫定 seal の再取得が必要です。
- acceptance duration ledger、共有 fixture、catalog、docs、既存 consumer test は編集していません。

## 未実走・未実装

- live preflight と本走の外部通信は、禁止に従い未実走です。
- commit 禁止のため、実 commit に対する registration preflight 成功確認は親作業です。
- checkpoint / resume、軸集約器、control 発火、補助 anchor stream 実行は scope 外です。
- `ruff` は環境に存在せず未実走です。
- commit、add、push は行っていません。

## 総括

単位 B の registration preflight、live preflight、16-anchor registry、保存済み応答用 leaf runner、draft-07 schema 3 本、統合 test を実装しました。全 57 test node が自走 harness で通過し、外部 request と未登録運用値の補完は 0 件です。