---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-17
wave: dev-wave-cross-protocol-scope-release
seq: 2
---

## 新規

### {{F:substring-absence-check-hits-embedded-repo-path}}. 部分文字列の不在検査が、script に埋め込まれた repo path の一部に当たって決定的な偽赤になる [テスト代表性]

- 事象: 受入全走 1 走目で `orchestrator/tests/test_pegasus_dispatch_compute.py` の
  `test_compute_marker_is_cross_namespace_evidence_without_release_handshake` が赤になった。同 test は
  compute job script に「release handshake が無い」ことを `assert "release" not in script.lower()` で見るが、
  script には `dispatcher=<repo_root>/…` として **worktree の絶対 path が埋め込まれる**。本 wave の worktree /
  branch 名が `…-cross-protocol-scope-release` だったため、path の末尾 `scope-release` に当たって
  決定的に赤になった (docs-only の wave で実装面 0 byte)。同じ受入の他 16 件は負荷起因の
  `TimeoutExpired` / real-repo lock の非帰属赤で、この 1 件だけが自分起因だった。
- 根本原因: 語 1 つの不在で構文の不在を代理させている。「release」は一般語で、path・comment・
  branch 名にも現れる。検査対象 (script 本文) に環境依存の文字列 (repo path) が混ざる以上、語の不在検査は
  検査対象と無関係な入力で反転する。F908 (部分文字列の存在検査の恒真) の裏返しで、こちらは偽赤の側。
- 恒久対応: 受入を通すための即時対応は worktree / branch を `…-cross-protocol-scope-lift` に切り直した
  (submodule を含む worktree は `git worktree move` できないため新規 worktree を同一 commit から作成)。
  test 側の是正 (語の不在ではなく handshake 構文 — 例: `release` を含む marker 操作行 — の不在を、path を
  除いた本文に対して検査する) は実装面なので本 wave では行わず、次の一手に起票した
  (Codex `role=author` 必須)。暫定の防壁は memory
  (`~/.claude/projects/-work-1-SFC-tanab-izanagi/memory/wave-slug-must-not-contain-release.md`):
  wave の slug / branch / worktree 名に `release` を含めない。
- 再発検知: 受入全走で同 test が赤になり、assert 本文の `'release' is contained here:` が path 断片を指す。

## 再発

### F810

- **再発: 2026-09-17** — 本 wave の 1 つ目の worktree (`…-scope-release`) で
  `tools/dev_wave_submodule_init.py` の 1 走目が `runtime-io-failure: detail={'label': 'submodule',
  'kind': 'update-no-fetch'}` を出し、submodule 自体は初期化済み (status 行頭の `-` が消えていた)、
  2 走目で `OK` rc=0。同 wave で後から作った 2 つ目の worktree (`…-scope-lift`、同一 commit) では
  1 走目で rc=0 だった。回数は固定ではないという既知の観測と整合する。
