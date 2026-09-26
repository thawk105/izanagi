## 変更 file と要点

C++ 形の [coder role](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-role/.claude/agents/coder-v4-autonomous-policy.md) と IR 形の [coder role](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-role/.claude/agents/coder-v4-autonomous-policy-ir.md) を新設し、[auditor](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-role/.claude/agents/auditor.md) を改訂しました。登録簿、checker、テストも16 role に追随しています。commit はしていません。

**未完了です。** 実効 sandbox が `.codex/` への書込みを拒否したため、adapter 3 件と `.codex/agents/README.md` は反映できませんでした。`spec.render_adapter` で生成した JSON は [/tmp/t2865-unit-role-adapters](/tmp/t2865-unit-role-adapters)、README 案は [/tmp/t2865-unit-role-README.md](/tmp/t2865-unit-role-README.md) に置いています。

## role 本文の要旨 (2 role と auditor 改訂、逐語案から変えた箇所の一覧)

両 coder は fresh・tools なし・構造化出力のみで、入力例を interface §3 の必須5 key、出力を `proposal` のみにしました。C++ 形は `policy_spec` を受理契約の正本とし、IR 形は具体値のない tagged object 文法を記載しています。`justification` は台帳に残し、critic と次の coder には渡さない契約です。

auditor には型22〜26を追加しました。逐語案から、型25は候補ごとの sanitizer receipt を要求せず構文検査・単独 TU compile の受領を確認する形へ、型26は hook 計数を要求せず lock 方策を既定で「verify 中の発火証拠なし」と扱う形へ修正しました。チェックリスト15も同じ受領条件に変更し、型17〜21の免除を sort IR と機械生成 IR 候補に限定しました。

## 登録簿の追随 (更新した pin ごとに理由 1 行)

- `EXPECTED_ROLE_COUNT`：新 role 2 件により14→16。
- `SOURCE_FILE_SHA256`：新 role 本文2件と auditor 本文改訂を固定。
- `DESCRIPTION_SHA256`：新 role の frontmatter description 2件を固定。
- `ROLE_MANIFEST_SHA256`：新 role entry 2件と auditor の出力型上限変更を固定。
- `SCHEMA_SHA256`：新 role の入出力 schema と auditor の型上限26を固定。
- `ROLE_IO_CONTRACTS`：新 role 2件の direct 入力5 key・出力 `proposal` を固定。

[policy.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-role/orchestrator/codex_roles/policy.py) に role 別禁止 key を追加し、[manifest.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-role/orchestrator/codex_roles/manifest.json)、[checker](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-role/tools/check_codex_agents.py)、[テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-role/orchestrator/tests/test_codex_agents.py) を更新しました。

## test と検査の実走 (コマンド・passed / failed 件数)

- `python3 tools/check_codex_agents.py`：0 passed / 1 failed。新 adapter 2 件の未配置で停止。
- `python3 tools/run_tests.py -q -p no:cacheprovider orchestrator/tests/test_codex_agents.py`：0 件実走。dispatch infrastructure failure、rc=16。
- 指定の `python3 -m pytest -q -p no:cacheprovider orchestrator/tests/test_codex_agents.py`：0 件実走。PreToolUse hook がログインノードでの直接 pytest を拒否。
- role 入出力例の schema 整合検査：2 role passed / 0 failed。
- `python3 tools/check_docs.py`：違反0件。`git diff --check`：違反0件。

## 所有外への波及

新 role を利用する親担当の policy driver は、登録名と5 key 入力契約を参照する必要があります。[agent architecture](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-role/docs/agent-architecture.md) の coder role 説明は旧系列を記述しており、親の docs 担当による確認対象です。所有外のファイルは編集していません。

## 総括

role と登録簿の実装は進めましたが、`.codex/` の書込み拒否とテスト実走不能により、単位 D は**実装済み・未実走、adapter 反映未了**です。adapter・README の反映後に checker と対象 pytest の再実走が必要です。