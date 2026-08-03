実装単位 A を完了しました。docs・既存テスト・所有外ファイルは変更せず、commit / git add も行っていません。

## 編集内容

- [tools/dev_waves/effort_levels.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u1/tools/dev_waves/effort_levels.py:1)
  - 5 値を順序付き tuple として `CLAUDE_EFFORTS` / `CODEX_REASONING_EFFORTS` に定義。
  - `none` は含めていません。
  - repo policy と CLI capability attest の違い、Claude 語彙の根拠、F56 の model 依存性、supervisor digest 閉包に置く理由を日本語 docstring に記載。
  - 標準ライブラリを含め import のない leaf module です。

- [orchestrator/codex_roles/launcher.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u1/orchestrator/codex_roles/launcher.py:85)
  - 既存 4 値を `SAFE_ADAPTER_CODEX_REASONING_EFFORTS` として命名。
  - `_safe_adapter()` の membership 判定だけを定数参照へ変更。
  - 診断文言は未変更です。

- [orchestrator/codex_roles/spec.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u1/orchestrator/codex_roles/spec.py:70)
  - 既存 2 値を `ROLE_MANIFEST_CODEX_REASONING_EFFORTS` として命名。
  - manifest の membership 判定だけを定数参照へ変更。
  - opus 固定条件および診断文言は未変更です。

- [orchestrator/tests/test_effort_levels.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u1/orchestrator/tests/test_effort_levels.py:1)
  - launcher / spec の集合が repo policy の部分集合であることを検査。
  - 両正本 tuple を 5 値・順序込みのリテラルで固定。
  - AST で `orchestrator` import の逆流を検査。
  - `globals()` から `test_*` を集める plain runner を追加。

## 受理・拒否挙動

変更前後で同一です。

- launcher の命名済み集合は `low / medium / high / xhigh` を許可し、`max / none` その他を拒否します。
- spec は `medium / high` のみ許可し、`low / xhigh / max / none` その他を拒否します。
- 通常の `_safe_adapter()` 経路では先に spec が解析されるため、role manifest 全体としての実効受理集合は引き続き `medium / high` です。
- `source.model == "opus"` の `gpt-5.6-sol/high` 固定条件は [spec.py:613](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u1/orchestrator/codex_roles/spec.py:613) のままです。
- 新しい 5 値 tuple は policy 定義であり、単位 A 単独では既存 runtime の受理集合を変更しません。

## 所有外への波及可能性

静的に次を確認しました。

- launcher の外部 caller:
  - [tools/run_codex_role.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u1/tools/run_codex_role.py:87) から `run_role`
  - 同ファイル 89 行から containment probe、93 行から `attest_role`
  - これらは `_safe_adapter()` を経由しますが、集合と診断が同一なので挙動への波及はありません。

- spec の consumer:
  - [tools/check_codex_agents.py:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u1/tools/check_codex_agents.py:44) と同 298 行が `load_role_specs()` を使用。
  - 現行 manifest の全 13 reasoning 値は `medium` または `high` であり、受理結果は変わりません。

- `test_codex_agents.py`:
  - [共有 fixture](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u1/orchestrator/tests/test_codex_agents.py:36) は `codex_roles` 全体をコピーします。
  - [adapter policy 検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u1/orchestrator/tests/test_codex_agents.py:130) および [model/effort 負例](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u1/orchestrator/tests/test_codex_agents.py:406) は同じ spec 判定を通るため、期待値への影響はありません。

- `test_codex_role_runtime.py`:
  - [直接 `_safe_adapter()` を呼ぶ consumer test](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u1/orchestrator/tests/test_codex_role_runtime.py:468) を確認しました。
  - 使用する `critic` は既存の `high` のままで、adapter bytes や診断を変更していないため期待値への影響はありません。

## Supervisor digest

[daemon.py:179](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u1/tools/dev_waves/daemon.py:179) は直下の `.py` / `.json` を読み込むため、新ファイル追加で `_supervisor_digest()` の値は意図どおり変わります。

静的検索では、この digest のリテラル値を固定したテストは見つかりませんでした。digest は manifest への記録 ([daemon.py:736](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u1/tools/dev_waves/daemon.py:736)) と run 内の before/after 比較 ([daemon.py:1114](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u1/tools/dev_waves/daemon.py:1114)、同 1211 行) に使われています。schema 側も [64 桁 hex の形だけを検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/t189-u1/tools/dev_waves/schema.py:748)しており、既存リテラル pin を壊す要因はありません。

## 静的確認

- `git diff --check`: 問題なし。
- 4 ファイルを `compile()` で構文確認済み。
- `git status --short` で変更対象が指定された 4 ファイルだけであることを確認。
- pytest および plain runner を含むテスト実測は一切行っていません。

## 総括

編集ファイル: 指定された 4 ファイルのみ。
波及: 既存 caller・fixture・consumer test の受理結果や診断への変更なし。
未解決点: 親による計算ノードでのテスト実測、および後続の単位 B / C への正本配線。