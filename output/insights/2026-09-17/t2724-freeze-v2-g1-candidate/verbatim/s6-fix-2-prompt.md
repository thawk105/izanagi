単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-impl

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。これは射影 file 限定の停止規則であり、自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-freeze-v2-g1-candidate/s5-author-prompt.md` — 段 5 実装子契約 (権限・所有・禁止・検査・報告形式)。**全文を継承する**
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-freeze-v2-g1-candidate/s6-fix-prompt.md` — 1 巡目 fix の裁定 (F-1〜F-4、適用済み)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-impl/orchestrator/campaign/s8b_holdout_freeze.py` — 編集対象。`_validate_floor_inputs` (1375〜1685) 全体を読む

repo root は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-impl`。所有 path は段 5 と同じ 3 file。**既存テストの期待値を変更しない。** docs 編集・commit をしない。

## 親の実測 (焦点走、計算ノード、fix 1 巡目適用前の bytes だが該当箇所は同じ)

`orchestrator/tests/test_s8b_holdout_freeze.py` 単独走: **21 failed / 141 passed / 2 skipped**。21 件すべて同じ traceback:

```
    return (
        result_rel, result_raw, result, protocol_raw, protocol,
>       floor, path_info, record.path,
    )
E   AttributeError: 'dict' object has no attribute 'path'
orchestrator/campaign/s8b_holdout_freeze.py:1681: AttributeError
```

原因: `_validate_floor_inputs` の後段に既存の `for record in journal_sessions:` (journal の session record を回す loop、HF:1600 付近) があり、変数 `record` が dict で上書きされる。段 5 で先頭に足した `record = _floor_campaign.resolve_current_floor_protocol(root=root)` と名前が衝突している。失敗 node の例: `test_v2_candidate_rejects_earlier_official_symlink[result]`、`test_v2_candidate_threads_receipt_derived_degraded_mode_to_floor_stats`、`test_floor_selection_threads_earlier_run_identity_and_manifest_to_derivation`、`test_v2_candidate_reads_selected_certificate_from_bound_run_dirfd` など (journal に session record を持つ fixture を通る test)。

## fix (F-5)

- 解決直後に `protocol_rel = record.path` (または record 自体を `protocol_record` に改名) を取り、以後 `record.path` / `record.commit_oid` を参照する箇所をその名前に置換する。既存 loop の `record` 名は変えない (既存 code の差分を最小にする)。
- 末尾 return の `record.path` を `protocol_rel` に置換する。
- 同じ file 内で段 5 以降に足した `record` 参照が他に無いか grep で確かめる。

## 検査

- 段 5 契約と同じ焦点走を試みる (`PYTHONPATH=. python3 -m pytest -q orchestrator/tests/test_s8b_holdout_freeze.py -p no:cacheprovider`)。dispatch 障害なら「実装済み・未実走」と書く (親が実走する)。
- AST parse、`git diff --check`、`FLOOR_PROTOCOL_REL` 代入 1 件・`_run_git*` 各 1 件・必須 3 呼出し。
- `grep -n "record\." orchestrator/campaign/s8b_holdout_freeze.py` の結果を報告に載せ、段 5 以降の参照がすべて新名へ移ったことを示す。

## 出力形式

**出力は file に書かず、最終メッセージの本文に全文を書け。** 見出しはすべて `##`、最後の節は必ず `## 総括`。

節の順:

## 所見ごとの対応表 (closed / partial / regressed)
## 変更点 (file:line)
## 実走した検査と結果
## 総括
