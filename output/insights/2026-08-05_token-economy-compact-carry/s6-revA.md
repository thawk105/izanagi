## 総括

must-fix は **1件**。最重要 1: M08 は到達可能入力上の等価変異で、事前登録どおり kill できない。  
最重要 2: ordinal 排他判定は正規表現の構造上到達不能で、保証を実際には発火させない（nit）。  
最重要 3: 旧書式の未来参照拒否は実装上有効だが、compact 専用テストしかない（nit）。  
判定は **NO-GO**。M08 の変異契約または実装上の冗長な終端 anchor を是正し、親の実測で kill を確認する必要がある。

### MF-1 — M08 は multiline テストで kill できない

- file: [tools/spool_fold.py:1151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1151)、[test_spool_fold.py:718](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:718)
- 具体入力: `- [T-001] (1)\n  詳細\n`
- regex 自体が `^ ... \n$` で終わるため、`fullmatch` を `match` にしても `詳細` の手前で `$` が成立せず、どちらも不一致になる。さらに `_split_top_items` は末尾の空行を正規化するため、空行だけを suffix にした差も到達不能である。[spool_fold.py:312](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:312)
- したがって意図された `test_multiline_compact_prefix_item_uses_full_substantive_digest` は M08 下でも緑のまま。現実装の受理集合を保つ修正例は、`fullmatch` を残して冗長な終端 `$` を除くこと。
- **成果物影響:** このままでは変異 matrix／wave レポートの M08 を KILLED と記録できず、台帳の検出力証明が偽になる。

### NIT-1 — `legacy_ordinal` / `compact_ordinal` 排他例外は到達不能

- file: [tools/spool_fold.py:1166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1166)
- legacy 入力では必ず `(str, None)`、compact 入力では必ず `(None, str)` になる。両 branch の capture は各 alternative 内で必須なので、両方あり／両方なしでは regex 自体が一致せず、1168 行目へ到達しない。
- 具体入力 `- [T-001] 変わらず ((1) 参照) (2)\n` も `carry is None` となり、例外 branch ではなく実体 digest fallback へ進む。
- **成果物影響:** 現在の受理集合・台帳値への影響はないため **nit**。ただし「発火する防壁」ではない。

### NIT-2 — 旧書式の未来参照に独立した回帰テストがない

- file: [test_spool_fold.py:656](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:656)、[tools/spool_fold.py:1180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1180)
- 現コードは両形式から `referenced` を選んだ後の共通 `referenced >= ordinal` で拒否するため、新旧双方に効いている。
- ただしテスト入力は compact のみ。例えば current `(2)` の `- [T-001] 変わらず ((3) 参照)` と archive `(3)` の実体を置き、比較を compact branch 内だけへ移す変異は既存テストをすり抜ける。
- **成果物影響:** 現実装は正しいため直接影響はなく **nit**。旧書式専用の未来参照 fixture を足すと防壁を固定できる。

## fail-open と受理集合

producer は [spool_fold.py:1353](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1353) で parser と byte-exact に一致する形を生成する。正規 compact が認識漏れして stub digest へ落ちる経路は見つからなかった。認識後の missing entry、missing task、自己・未来参照は例外を捕捉せず伝播する。

変更前に実体 item だったものから carry へ再分類される集合は、正規化後の `item.block` が次へ完全一致するものだけである。

```regex
^- \[T-(?:0(?:0[1-9]|[1-9][0-9])|[1-9][0-9]{2,})\] \([1-9][0-9]*\)\n$
```

すなわち canonical T-ID、正整数・先頭ゼロなし ordinal、本文なしの単一行である。これ以外の旧実体 item は再分類されない。現行 worklog と全 archive にこの exact 形は **0件**だった。

裁定 §5 の禁止形はいずれも carry として拒否され、従来どおり実体 item になる。

- `(0)`、`(01)`、`()`：`[1-9][0-9]*` に不一致。
- `(1) 実体本文`：`)` の直後に要求される `\n$` に不一致。
- `(1)\n  詳細`：item 全体が終端 anchor に不一致。

## M01〜M08 の静的 kill 帰属

| 変異 | 静的に kill する nodeid |
|---|---|
| M01 | `orchestrator/tests/test_spool_fold.py::test_n08_all_carries_preserve_order_and_count`、`::test_real_worklog_105_to_106_next_action_is_byte_exact_golden` |
| M02 | M01 と同じ byte-exact 2 node |
| M03 | `::test_compact_and_legacy_carry_chain_resolves_substantive_base`、`::test_parallel_new_then_existing_update_uses_substantive_base_digest` |
| M04 | `::test_global_carry_resolves_global_entry_not_legacy_collision`、`::test_global_carry_cannot_fall_back_to_legacy_only_target`、`::test_n37_real_repo_canonical_family_requires_archive_active_history` |
| M05 | `::test_compact_carry_uses_explicit_prior_across_ordinal_gap` |
| M06 | `::test_two_worklog_fragments_use_immediate_prior_ordinals` |
| M07 | `::test_compact_carry_missing_entry_rejects_before_stub_digest`、`::test_compact_carry_missing_task_rejects_before_stub_digest` |
| M08 | **なし。等価変異として生存** |

M05 fixture は要求どおり current 末尾 `(5)`、archive max `(9)`、new `(10)`、出力 `(5)` になっている。[test_spool_fold.py:766](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:766)

## 既存テスト・D70・docs

- 既存期待値の反転、緩和、skip、xfail、削除はない。real-worklog golden は最終的に引き続き byte-exact 比較であり、変換件数も `215` に固定されている。[test_spool_fold.py:2008](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:2008)
- 後方互換 3 本は残存し、先頭 2 本の入力は旧書式のまま。3 本目も旧書式の実 corpus をコピーしている。
- 揮発 hash・working-tree 値を期待値へ焼き込んだ新設テストはない。rotation の実 apply と ordinal-gap の実 fold も再現形になっている。
- `git diff -- tools/check_docs.py` は空で、本体は無改変。
- ID 単独 source は `$` 分岐で抽出され、後続 entry と見送り台帳の双方から落ちれば finding になる。[check_docs.py:521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/check_docs.py:521)、[check_docs.py:1497](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/check_docs.py:1497)
- 新テストも `- [T-001]` source を sink から削り、具体的 D70 finding を要求している。[test_check_docs.py:4726](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_check_docs.py:4726)
- docs 4 面は新旧書式・substantive digest・書式非依存 consumer に追随済み。`rulings.md` は 4,988 bytes の net-neutral。

pytest、`check_docs.py`、変異 harness は実行しておらず、緑は主張しない。静的検査と `git diff --check` のみ実施した。