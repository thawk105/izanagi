---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-02
wave: dev-wave-t2191-verifier-parallel
seq: 3
---

## 新規

### {{F:submodule-init-reports-failure-after-succeeding}}. `dev_wave_submodule_init.py` は成功した初期化に対しても `update-no-fetch` を返す [手順漏れ]

- 事象: 新規 worktree 3 本 (実装子・fix1・fix2) で
  `python3 tools/dev_wave_submodule_init.py --worktree <path>` が毎回
  `ERROR: runtime-io-failure: detail={'label': 'submodule', 'kind': 'update-no-fetch'}`
  を返した。しかし `external/ccbench/` は実際には展開されており
  (`.git` と `CMakeLists.txt` を含む 13 entry)、`tools/check_wave_startup.py --mode midflight`
  を再走すると緑になった。親は 1 本目で「初期化に失敗した」と読み違えて別手段を探した。
- 根本原因: 同 tool の最後の `submodule-update` は再帰的に走り、`external/ccbench` 配下の
  入れ子 submodule が local objects だけでは解決できずに非 0 で戻る。top-level の展開は
  その前に完了しているが、tool は最後の返り値だけを見て全体を失敗として報告する。
  開始 gate が要求するのは top-level だけなので、gate と tool の判定基準がずれている。
- 恒久対応: `docs/dev-wave/operations.md` の `DW-O20` が既に
  「新規 worktree は未初期化 submodule で非 0。`DW-C01` に従い初期化して再検査」と定めており、
  **再検査すれば緑になる**という現行手順で閉じる。tool の返り値を初期化の成否と読み替えない。
- 再発検知: `tools/check_wave_startup.py` の submodule 検査 (top-level の
  `CMakeLists.txt` が非 symlink の regular file、`.git` が存在) が権威であり、
  tool の rc ではなくこちらの結果で判定する。
