---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-02
wave: dev-wave-t2067-oracle-manifest-selection
seq: 3
---

## 新規

### {{F:submodule-init-first-call-io-failure}}. submodule 初期化 tool の 1 回目が必ず落ち 2 回目で通る [手順漏れ]

- 事象: 新規 worktree に対する `python3 tools/dev_wave_submodule_init.py --worktree <ABS>` の
  **1 回目の呼出しが `ERROR: runtime-io-failure:
  detail={'label': 'submodule', 'kind': 'update-no-fetch'}` で rc=1** になり、
  同じ command を続けて実行すると rc=0 で成功する。本 wave では実装子用 worktree 1 回、
  fix 子用 worktree 2 回の計 3 回とも同じ挙動だった。worktree 作成時にも
  `warning: unable to access '<path>/.gitattributes': システムコール割り込み` が出ていた。
- 根本原因: 未特定。detail が `label` と `kind` しか出さないため、tool の出力からは
  失敗した git command も errno も読めない。worktree 作成時の EINTR と同時に観測されており、
  共有ファイルシステム上の一過性 I/O 中断が疑わしいが、本 wave では原因を切り分けていない。
- 恒久対応: 未実施。**rc=1 を「初期化不能」と読んで停止しないこと**が当面の運用側の対応で、
  `DW-C01` の submodule 行が指す tool をそのまま 1 度だけ再実行して rc=0 を確かめる。
  検出器は `tools/check_wave_startup.py` の
  `NG: submodule is not initialized` で、未初期化のまま子を起動する経路は既に fail-closed
  で塞がっている (本 wave の fix 子初回投入はこれで止まった)。
  tool 側で再試行するか detail を厚くするかは、原因を切り分けてから裁定する。
- 再発検知: 同 tool が rc=1 を返したとき、detail が
  `{'label': 'submodule', 'kind': 'update-no-fetch'}` だけであることを確かめ、
  再実行で rc=0 になるなら本エントリの型である。2 回目も落ちるなら別の事象として扱い、
  `git submodule update --init --recursive --no-fetch` を直接実行して生の git エラーを読む。
  なお runner script 内で生の git を使うと `transport 'file' not allowed` で必ず失敗する。
  これは本エントリの型ではなく、`DW-C01` が既に tool の使用を求めている。
