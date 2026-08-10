fix-1〜fix-5 を指定 2 ファイルだけに実装しました。commit / `git add` は行っていません。

### 受理集合

fix 前の preimage [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4076) は command 全文を走査していたため、本文の正当 edge に加えて frontmatter-only decoy も受理していました。別行、`F260`、非 code-span path、raw HTML block、link definition は拒否していました。

fix 後は [tools/check_docs.py:4076](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4076) で frontmatter を除いた本文だけを走査します。frontmatter-only decoy が新たに拒否され、その他の受理・拒否集合は変えていません。既知限界にも触れていません。

### 修正内容

- finding helper に cleanup command の path prefix を固定しました。[test_check_docs.py:6740](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6740)
- 二重欠陥だった負例を ID 隣接と非 code-span path の独立 2 ケースへ分割しました。[test_check_docs.py:6766](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6766)
- `description` の値だけに偽 edge を置く frontmatter 負例を追加しました。[test_check_docs.py:6832](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6832)
- meta-test の登録名を更新しました。[test_check_docs.py:2876](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:2876)
- 既存期待値、実 repo の hash 定数、合成 command は変更していません。cleanup command の SHA-256 は引き続き `a92d960c4da65a199b39a50c43d64f5ab66fccbb19205f25c5d87db47a4722e3` です。

### 検査結果

- `git diff --check`: rc=0
- `python3 tools/check_docs.py`: rc=0、違反なし
- `python3 tools/check_codex_agents.py`: rc=0
- 親 docs 変更に起因する finding: 無い
- 確認済みの赤: 無い

焦点 pytest は以下の 9 nodeidを `tools/run_tests.py` で投入しましたが、pytest 開始前に rc=16 となりました。原因は `qstat -Q` の `EACCTAUTH Unknown user-id` と、user slice 約 12.5 GiB 使用中による local headroom 不足です。したがって全 nodeid は「実装済み・未実走」であり、緑とは申告しません。

- `test_dev_wave_new_gate_case_registration_is_complete`
- `test_cleanup_address_edge_rejects_split_lines`
- `test_cleanup_address_edge_rejects_id_adjacent_decoy`
- `test_cleanup_address_edge_rejects_non_code_span_path_decoy`
- `test_cleanup_address_edge_rejects_raw_html_block`
- `test_cleanup_address_edge_rejects_link_definition`
- `test_cleanup_address_edge_rejects_frontmatter_decoy`
- `test_cleanup_address_edge_accepts_rewording`
- `test_cleanup_address_edge_accepts_baseline`

このため、揮発源である合成 cleanup command を各負例で実際に変更した後も理由・件数が安定することはテストとして実装済みですが、実走確認は未完です。

### 所有外への波及可能性

- direct caller: `_check_command_docs_guard()` を呼ぶ `tools/check_docs.py` の main 検査経路
- 外部 consumer: `tools/dev_wave_land.py`、`tools/task_run_check.py`、`tools/dev_waves/checker.py` / `daemon.py`
- 共有 production: `COMMAND_INTERFACES`、`_visible_dispatch_inventory_text`、`_parse_frontmatter`
- 共有 test fixture: `_build_min_repo`、`_read`、`_write`、`_run_check`、`_assert_violation`、`_violation_count`
- consumer test: 既存 cleanup digest/frontmatter/command-interface テスト群。既存合成 command は本文 edge を保持するため、静的には追加 finding の巻き添えはありません。

### 新 lint 本体の逐語

```python
        if rel == ".claude/commands/cleanup-branches.md":
            command_body = text
            command_lines = text.splitlines()
            if command_lines and command_lines[0] == "---":
                try:
                    frontmatter_end = command_lines.index("---", 1)
                except ValueError:
                    pass
                else:
                    command_body = "\n".join(command_lines[frontmatter_end + 1:])
            if not any(
                re.search(r"(?<![0-9A-Za-z])F26(?![0-9A-Za-z])", line)
                and "`docs/failures.md`" in line
                for line in _visible_dispatch_inventory_text(command_body).splitlines()
            ):
                findings.append(
                    f"{rel}: F26 と `docs/failures.md` が同一可視行に共起しない — "
                    "他文書にしか無い義務への到達 edge を失っている"
                )
```

## 総括

- fix-1〜fix-5 は指定 2 ファイルだけに実装済みです。
- docs、cleanup command、hash 定数、既存期待値は変更していません。
- 静的検査は緑、親 docs 由来の finding と確認済み回帰はありません。
- 焦点 9 nodeid は環境起因 rc=16 のため未実走で、残件はその再走だけです。