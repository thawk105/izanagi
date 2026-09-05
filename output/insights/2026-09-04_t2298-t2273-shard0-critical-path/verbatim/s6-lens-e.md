## 所見対応表 (closed / partial / regressed)

| 所見 | 判定 | 現物判定 |
|---|---|---|
| MF-1 | **closed** | 実 read scope は競合 SH 成功・EX 失敗、write scope は競合 SH 失敗を確認しています。[現物:1496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1496) AST も共通 scope の `access_mode=access_mode`、両 wrapper の literal mode、yield の `with` 内包を固定しています。[現物:1537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1537) |
| MF-2 | **partial** | 現実装は production `seed()` から atomic helper を呼び、helper も temp write→flush→fsync→replace の正しい順序です。[現物:1188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1188) ただし追加検査には後述する直接公開と fsync 順序の生存変異があります。 |
| regressed | **なし** | fix による実装本体・wrapper・17 consumer の退行は認めません。統合差分は当該 test file だけで、consumer hunk は従前レビュー済みの M17/M18 の fixture 名変更だけです。[差分:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2298-certified-evidence-lock/artifacts/stage6-diff.patch:1) [差分:801](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2298-certified-evidence-lock/artifacts/stage6-diff.patch:801) |

差分は累積差分ですが、fix 前の lens C/D に記録された実装本体・wrapper・M17/M18 と現物が一致し、fix 部分は検査側に限定されています。他の15 consumer には hunk がありません。

新規 AST 検査は、対象なしの場合に KeyError／StopIteration／件数 assertion で赤になります。`any(...)` は対象を1件と確認した後に使われ、空集合で緑になる箇所や、例外を捕捉して緑にする箇所もありません。

## must-fix

1. **MF-2A — `seed()` の直接公開禁止が等価な path 構文を捕捉しません。**

   `is_direct_metadata_path()` は `shared / "evidence.json"` とその単純 alias だけを認識します。[現物:1644](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1644) 正しい helper call を残したまま、先に次を加える変異は検査を通過します。

   ```python
   shared.joinpath("evidence.json").write_bytes(payload)
   _write_certified_evidence_metadata(shared / "evidence.json", metadata)
   ```

   helper の件数・引数は正しく、`joinpath()` は metadata path と判定されないため `direct_publications == []` も通ります。seed 内に正当な直接 file write はないため、receiver の path 推論に依存せず `write_bytes`、`write_text`、直接 `open`／`replace` を禁止する方が確実です。

   **成果物影響:** worker 中断時に部分 JSON が ready marker として残り、後続 worker が壊れた certified evidence を採用できます。

2. **MF-2B — temp fd の fsync が write 後であることを検査していません。**

   atomic 検査が記録するのは `fsync` と `replace` だけです。[現物:1759](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1759) `os.fsync(stream.fileno())` を `stream.write(payload)` より前へ移しても、操作列は `["fsync", "replace"]`、fd・source・target・最終 bytes も同じなので緑になります。write／flush／fsync／replace の順序まで観測する必要があります。

   **成果物影響:** marker が書込み後に同期されないまま rename され、障害回復後の certified metadata の永続性を受入が保証できません。

## nit

- 変異 h は単一検査への一意帰属ではありません。実 scope 検査に加えて mode 転送 AST も独立に赤になるため、kill 表では「主検査＋冗長 kill」と明記するのが正確です。
- 既裁定済みの `os.fdopen` 例外時 fd leak と、M18 の最初の共有変異が `try` 外にある点は現存しますが、fix の退行ではなく今回の scope 外です。

## 変異 h / g2 の帰属

- **h — KILL、ただし二重帰属。**
  - 最初に赤になるのは `test_certified_evidence_fixture_scope_holds_both_modes_through_yield` です。read scope が EX となり、競合 SH の成功箇所で OSError が発生します。[現物:1515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1515)
  - 後続の `test_certified_evidence_fixture_scope_yield_is_inside_lock_ast` も、RHS が `Name("access_mode")` でなくなるため赤です。[現物:1569](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1569)
  - 各失敗の理由は単一ですが、suite 全体の killer は一意ではありません。file 順では事前登録された実 scope 検査が先です。

- **g2 — KILL、単一帰属。**
  - helper call を直接 `write_bytes` へ置換する登録変異では、`test_certified_evidence_seed_publishes_metadata_only_through_atomic_helper_ast` の `len(helper_calls) == 1` が最初に赤になります。[現物:1689](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1689)
  - 実 scope の先行検査では正常な完全 JSON が書かれるため赤にならず、未使用となった helper の atomic 検査も緑です。したがって exact g2 の帰属は production call-edge に一意です。
  - ただし helper を残して別構文の直接 write を加える MF-2A の変異は生存します。

## 総括

**changes requested。MF-1 は closed、MF-2 は partial、regression はなしです。**

現在の実装自体は契約どおりですが、MF-2 の受入検査には「helper を残した直接公開」と「write 前 fsync」という明確な緑通過反例があります。親の焦点走が緑でもこの静的な抜けは閉じないため、MF-2A／MF-2B の修正後に受入可能です。指定どおり pytest は実行していません。