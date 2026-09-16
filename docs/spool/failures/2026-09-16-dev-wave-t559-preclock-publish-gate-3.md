---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t559-preclock-publish-gate
seq: 3
---

## 新規

### {{F:submodule-init-false-ok-before-worktree-add-completes}}. `git worktree add` の完了前に当てた submodule 初期化が、何もせずに rc=0 と「OK」を返した [恒真ゲート] [手順漏れ]

- 事象: (2026-09-16、段 5 の実装子 worktree 作成時) `git worktree add` が前景の時間上限を超えて
  背景へ移った。checkout の途中で `python3 tools/dev_wave_submodule_init.py --worktree <ABSOLUTE>`
  を当てたところ、rc=0 と `OK: submodules initialized in <path>` を返した。直後の
  `tools/check_wave_startup.py --mode midflight` は
  `NG: submodule is not initialized (external/ccbench/CMakeLists.txt must be a non-symlink
  regular file and external/ccbench/.git must exist without being a symlink)` を返し、
  `external/ccbench/` は**空ディレクトリ**だった。`DW-O08` が許す 1 度の再実行も同じ偽の OK を返し、
  midflight は NG のままだった。`git worktree add` の終了 (rc=0) を確認してから 3 度目を当てて
  初めて実体化し、midflight が rc=0 になった。
- 根本原因: 初期化 tool は `.gitmodules` の登録に対して初期化を試み、その結果を「成功」とするが、
  **親 worktree の checkout が完了していること**を前提条件として検査しない。checkout 途中では
  submodule の gitlink がまだ index から作業ツリーへ展開されておらず、初期化すべき対象が
  0 件に見える。0 件の初期化は「全部終わった」と区別が付かないため、rc=0 と OK が返る。
  事象の側の引き金は、`git worktree add` が前景 timeout で背景へ移されたのに、その終了を
  待たずに次の git 系操作を当てたことである。
- 恒久対応: 未実施。回避策は、`git worktree add` の終了 (background task の exit code) を確認してから
  初期化を当てること。検出は `tools/check_wave_startup.py --mode midflight` が担っており、
  この wave では実際に段 5 投入前に止めた。初期化 tool 側で「対象 0 件」と「全件初期化済み」を
  区別する改修は本 wave の scope 外とした。
- 再発検知: 初期化 tool が rc=0 を返した直後に midflight / 開始 gate が
  `submodule is not initialized` で NG になったらこの型である。
  `ls <worktree>/external/ccbench/` が空なら確定する。初期化 tool の rc と OK 文言を
  初期化済みの証拠に数えないこと。
