静的検査のみ実施した。pytest は実走しておらず、親提示の 9 passed / `check_docs` rc=0 / `spool_fold --dry-run` rc=0 は再現していない。

実装上の 3 root cause は閉じており、M1〜M8 に `SURVIVED` はない。ただし R4 記録と fix 後の変異期待集合の事前登録が未完なため、現時点では land 不可と判定する。

## 1. 所見対応表

| 出所・所見 | 判定 | 対応 | 根拠 |
|---|---|---|---|
| C: finding の対象 path 未検証 | real | closed | helper が cleanup path prefix 込みで検査する。[test_check_docs.py:6740](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6740) |
| C: n2 の二重欠陥、M2/M3 が殺せない | real | closed | ID 隣接負例は exact code-span path を保持し、path 負例は境界付き F26 を保持する。[test_check_docs.py:6766](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6766) [test_check_docs.py:6782](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6782) |
| C: frontmatter decoy | real | closed | scanner 入力を閉じ delimiter 後の本文へ限定し、専用負例も追加された。[check_docs.py:4076](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4076) [test_check_docs.py:6832](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6832) |
| C: link definition の quoted-title decoy | real | 裁定により実装しない | Markdown 意味解釈を要する既知限界として明示裁定され、D fragment に記録済み。[fix-spec.md:18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-address-edge-lint/fix-spec.md:18) [decision fragment:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/docs/spool/decisions/2026-08-11-dev-wave-t675-address-edge-lint-1.md:28) |
| C: 4-space indented code block | real | 裁定により実装しない | 同上。[fix-spec.md:18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-address-edge-lint/fix-spec.md:18) [decision fragment:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/docs/spool/decisions/2026-08-11-dev-wave-t675-address-edge-lint-1.md:30) |
| C: 打ち消し線 | real | 裁定により実装しない | 同上。[fix-spec.md:18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-address-edge-lint/fix-spec.md:18) [decision fragment:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/docs/spool/decisions/2026-08-11-dev-wave-t675-address-edge-lint-1.md:30) |
| C: 否定形 prose | real | 裁定により実装しない | 意味解析へ広げない裁定で、限界も記録済み。[fix-spec.md:18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-address-edge-lint/fix-spec.md:18) [decision fragment:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/docs/spool/decisions/2026-08-11-dev-wave-t675-address-edge-lint-1.md:31) |
| C: 見出し＋本文の拒否を偽陽性とする所見 | refuted | 裁定により実装しない | 同一可視行・code span へ形を固定する仕様上の拒否である。[fix-spec.md:21](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-address-edge-lint/fix-spec.md:21) [decision fragment:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/docs/spool/decisions/2026-08-11-dev-wave-t675-address-edge-lint-1.md:33) |
| C: 2 行 key/value 表の拒否を偽陽性とする所見 | refuted | 裁定により実装しない | 同上。[fix-spec.md:21](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-address-edge-lint/fix-spec.md:21) [decision fragment:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/docs/spool/decisions/2026-08-11-dev-wave-t675-address-edge-lint-1.md:34) |
| C: backtick 無し Markdown link の拒否を偽陽性とする所見 | refuted | 裁定により実装しない | 同上。[fix-spec.md:21](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-address-edge-lint/fix-spec.md:21) [decision fragment:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/docs/spool/decisions/2026-08-11-dev-wave-t675-address-edge-lint-1.md:35) |
| C: `accepts_baseline` の重複 | refuted（全 suite では重複するが、指定 9-node 変異集合では positive control） | 裁定により実装しない | 既存 baseline は指定 9 nodeid に含まれず、対象 baseline は M5/M6 を殺す。[test_check_docs.py:856](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:856) [test_check_docs.py:6880](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6880) |
| C: M5 の事前登録第一失敗が p2 | real | partial | fix 後は負例 6 本と正例 2 本がすべて赤になり、提示順の第一失敗は split-lines。旧記録は未訂正。[plan-v2.md:154](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-address-edge-lint/plan-v2.md:154) |
| C: M6 の対象束縛・第一失敗 | real | closed | path prefix assert により負例も dev-wave finding を代用できない。提示順の第一失敗は plan の n1＝split-lines と一致する。[test_check_docs.py:6740](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6740) [plan-v2.md:155](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-address-edge-lint/plan-v2.md:155) |
| D: trust root の過剰表現 | real | closed | 現 fragment は trust root を人間レビューだけとし、敵対監査を判断材料へ降格した。[decision fragment:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/docs/spool/decisions/2026-08-11-dev-wave-t675-address-edge-lint-1.md:14) |
| D: 未裏付け provenance 文 | refuted | closed | failure fragment の文自体は残るが、段 3 lens B が F173 原文と checker/予算対象を独立に照合して所見化した記録がある。[failure fragment:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/docs/spool/failures/2026-08-11-dev-wave-t675-address-edge-lint-2.md:19) [s3-lensB-out.md:33](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-address-edge-lint/s3-lensB-out.md:33) |
| D: R4 の s1/s2/c1/c2/c3・`DW-G05`・B-057 記録不足 | real | partial | R4 は worklog へ全項目を書く契約だが、現 worktree に R4 fragment はない。s2/c2 相当の内容だけ decision fragment に部分的に存在する。[plan-v2.md:136](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-address-edge-lint/plan-v2.md:136) [s6-lensD-out.md:29](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-address-edge-lint/s6-lensD-out.md:29) |

## 2. frontmatter fix の回帰判定

`_parse_frontmatter` と追加ロジックの区切り判定は完全に同じである。

- どちらも `text.splitlines()`。
- 先頭行が exact `---` の場合だけ開始。
- `lines.index("---", 1)` で最初の exact `---` を閉じ delimiter とする。
- 閉じ delimiter 不在は `ValueError` 扱い。

根拠は [_parse_frontmatter:3457](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:3457) と [除去ロジック:4077](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4077)。

閉じ `---` が無い場合、除去だけは fail-open して全文走査になる。しかし同じ入力は直後の `_parse_frontmatter` が必ず `None` を返し、`frontmatter を一意に解析できない` finding を追加する。[check_docs.py:4095](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4095)  
したがって address-edge finding を frontmatter decoy で隠せても checker 全体は必ず赤であり、この局所 fail-open は許容できる。

分割した負例は単一理由になっている。

- ID 隣接負例は `` `docs/failures.md` `` を維持し、壊すのは `F26`→`F260` だけ。[test_check_docs.py:6770](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6770)
- path 負例は境界付き `F26` を維持し、壊すのは backtick code-span 条件だけ。[test_check_docs.py:6786](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6786)

## 3. `DW-M07` 変異期待集合

以下の判定は [production predicate](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4086) と [9 node のテスト本文](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6750) の静的評価である。

`S-neg` は次の完全な 6-node 集合:

```text
orchestrator/tests/test_check_docs.py::test_cleanup_address_edge_rejects_split_lines
orchestrator/tests/test_check_docs.py::test_cleanup_address_edge_rejects_id_adjacent_decoy
orchestrator/tests/test_check_docs.py::test_cleanup_address_edge_rejects_non_code_span_path_decoy
orchestrator/tests/test_check_docs.py::test_cleanup_address_edge_rejects_raw_html_block
orchestrator/tests/test_check_docs.py::test_cleanup_address_edge_rejects_link_definition
orchestrator/tests/test_check_docs.py::test_cleanup_address_edge_rejects_frontmatter_decoy
```

`S-all-address` は次の完全な 8-node 集合:

```text
orchestrator/tests/test_check_docs.py::test_cleanup_address_edge_rejects_split_lines
orchestrator/tests/test_check_docs.py::test_cleanup_address_edge_rejects_id_adjacent_decoy
orchestrator/tests/test_check_docs.py::test_cleanup_address_edge_rejects_non_code_span_path_decoy
orchestrator/tests/test_check_docs.py::test_cleanup_address_edge_rejects_raw_html_block
orchestrator/tests/test_check_docs.py::test_cleanup_address_edge_rejects_link_definition
orchestrator/tests/test_check_docs.py::test_cleanup_address_edge_rejects_frontmatter_decoy
orchestrator/tests/test_check_docs.py::test_cleanup_address_edge_accepts_rewording
orchestrator/tests/test_check_docs.py::test_cleanup_address_edge_accepts_baseline
```

| 変異 | 静的判定 | 赤になる nodeid の完全な集合 |
|---|---|---|
| M1 | KILLED | `S-neg` |
| M2 | KILLED | `orchestrator/tests/test_check_docs.py::test_cleanup_address_edge_rejects_id_adjacent_decoy` |
| M3 | KILLED | `orchestrator/tests/test_check_docs.py::test_cleanup_address_edge_rejects_non_code_span_path_decoy`、`orchestrator/tests/test_check_docs.py::test_cleanup_address_edge_rejects_link_definition` |
| M4 | KILLED | `orchestrator/tests/test_check_docs.py::test_cleanup_address_edge_rejects_raw_html_block` |
| M5 | KILLED | `S-all-address` |
| M6 | KILLED | `S-all-address` |
| M7 | KILLED | `orchestrator/tests/test_check_docs.py::test_cleanup_address_edge_rejects_raw_html_block` |
| M8 | KILLED | `orchestrator/tests/test_check_docs.py::test_cleanup_address_edge_rejects_frontmatter_decoy` |

M3 では backtick 条件を外すと、非 code-span path 負例だけでなく `[F26]: …/docs/failures.md` も境界付き F26 と裸 path を同一行に持つため、link-definition node も赤になる。  
meta-test node はいずれの production 変異でも赤にならない。`SURVIVED` はない。

最小修正は、変異本走前に M1〜M8 の期待集合を上表へ更新し、とくに M5 の旧「第一失敗=p2」を訂正すること。段 7 では R4 に s1/s2/c1/c2/c3、`DW-G05` backlog、B-057 発火を明記すること。

## 総括

実装上の対象 path、単一理由性、frontmatter root cause は閉じ、frontmatter fix の回帰もない。  
M1〜M8 は指定 9 node の静的評価ですべて KILLED、SURVIVED はない。  
ただし変異期待集合と段 7 の R4 記録が未完であり、現状態の land は不可。  
NO-GO