---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-11
wave: dev-wave-t793-pubcore-impl
seq: 1
---

## 新規

### {{F:tools-to-orchestrator-gate-import}}. `tools/` の検査から `orchestrator` package の gate を素の名前で import し、fail-closed が恒久的な赤になった [手順漏れ] [恒真ゲート]

- 事象: `tools/spool_fold.py` へ新設 gate を結線し `from orchestrator.publication.approval_guard import ...`
  と書いた。段 5・段 6 のレビュー 2 本と変異 4 件をすべて通過したが、記録段で
  `python3 tools/check_docs.py` が rc=1 になり
  `spool approval-guard-unavailable: approval guard を import できない: No module named 'orchestrator'`
  を出し続けた。**land できない状態だった。**
- 根本原因: script として起動された `tools/check_docs.py` / `tools/spool_fold.py` の `sys.path[0]` は
  **`tools/` であって repo root ではない**。子は repo root を cwd にして手で確認したため気づかず、
  gate 自体は fail-closed で正しく設計されていたので、**「検査できない」が「常に赤」へ化けた**。
  gate の正しさではなく到達性の欠陥であり、gate の負例テストでは決して落ちない。
- 恒久対応: `tools/spool_fold.py` は自分が既に知る source repo root を import 中だけ `sys.path` へ
  挿入し `finally` で完全復元する。回帰は
  `orchestrator/tests/test_t793_approval_guard.py::test_spool_guard_resolves_from_source_root_without_repo_on_sys_path`
  が repo root を `sys.path` と module cache から外した状態で gate の解決と発火を検査する。
- 再発検知: 同型は「`tools/` 配下の検査が `orchestrator` / 他 top-level package を新たに import する」
  ときに起きる。**gate を結線した wave は fix 後に `python3 tools/check_docs.py` を実際に走らせ、
  rc を直接見る** (要約行や子の自己申告で代替しない)。同型は本 repo に既存で、
  `tools/check_docs.py` が `dev_waves` を import する一方
  `orchestrator/tests/test_spool_fold.py:2943` の `_copy_real_canonical_family` が
  `tools/dev_waves/` を複製しないため、焦点走で 4 node が落ちる。

### {{F:test-assumes-empty-spool}}. 正例テストが実 repo の `docs/spool/` が空であることを前提にし、記録を持つ wave が必ず落ちた [テスト代表性] [手順漏れ]

- 事象: marker gate の正例 `test_p2_draft_markers_outside_approved_blobs_do_not_stop_fold` が
  実 repo root に対し `plan_fold(ROOT).status == "noop"` と書いていた。本 wave が自分の
  worklog / decisions fragment を `docs/spool/` へ置いた瞬間に `planned` となり落ちた。
- 根本原因: 検査したい性質は「草案が未確定 marker を持っていても gate が fold を止めない」で
  あって、fold が no-op であることではない。**可変な repo 状態を正例の前提に焼き込んだ。**
  記録段まで spool が空だったため、実装段・レビュー段では発火しなかった。
- 恒久対応: 正例を「実 draft bytes に exact marker が存在すること」と
  「その bytes を `require_resolved_approval_markers()` が受理すること」の検査へ置き換えた
  (`orchestrator/tests/test_t793_approval_guard.py` の P2)。fold の状態には依存しない。
- 再発検知: 同型は「実 repo root を渡す正例が、その時点の可変ディレクトリの中身に依存する assert を
  持つ」ときに起きる。`docs/spool/`・`output/registry/`・`docs/handoff/` のように wave が書き込む
  path を実 root で参照する正例は、**記録 fragment を置いた後に必ず 1 度走らせる。**
