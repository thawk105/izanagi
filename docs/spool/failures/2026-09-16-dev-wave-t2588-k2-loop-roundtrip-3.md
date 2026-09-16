---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2588-k2-loop-roundtrip
seq: 3
---

## 新規

### {{F:submodule-init-green-without-effect}}. submodule 初期化 tool が rc=0 と OK を返したのに木が空だった [恒真ゲート] [手順漏れ]

- 事象: [T-2588] の wave 開始時、`tools/dev_wave_submodule_init.py --worktree <abs>` が
  rc=0 と `OK: submodules initialized in <path>` を返したが、`external/ccbench/` は空のままだった
  (`ls` が 0 件、`git -C external/ccbench rev-parse HEAD` が superproject の HEAD を返す =
  そこに `.git` が無い)。`DW-O08` は失敗が赤で出る前提で「なお赤なら止める」と書いており、
  **緑を効果の着地と読むと未初期化のまま次段へ進む。** 同じ引数の 1 度の再実行で解消した。
- 根本原因: 親が `git worktree add` の完了を待たずに初期化を投げた疑いが強い。tool 投入時点で
  worktree は登録済み・上位 file も出ていたが、`git worktree add` の process はまだ返っていなかった
  (background job の完了通知が初期化の後に届いた)。**未完了の木に対しては初期化が
  「やることが無い」と判断して正直に OK を返しうる。** 親の永続 memory には既に
  「add の完了前に別の git を当てない」があったが、登録済みの見た目を完了と読んだ。
- 恒久対応: `docs/dev-wave/operations.md` の `DW-O08` へ
  「rc=0 と OK 表示でも submodule 木が空でありうるので、rc でなく木の中身で効果を実測する」を
  1 文追加した ([T-2588] の段 8)。
- 再発検知: 初期化の直後に対象 submodule directory の実体を数え、0 件なら緑と扱わない。
  本 wave では submit-tree 側の初期化でも同じ実測を入れ、13 件を確認してから次へ進んだ。
