---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: t1428-worktree-submodule-tool
seq: 2
---

## 新規

### {{F:submodule-nonlocal-url-false-reject}}. update_submodules_no_fetch が local override を無視し正当な local 操作を拒否する [テスト代表性]

- 事象: [T-1428] 実装後の実環境検証で、`tools/dev_waves/git_state.py::update_submodules_no_fetch()`
  を本 repo の実際の worktree に対して実行すると `nonlocal-url` で拒否された。単体で直接
  呼んでも同じ失敗になることを確認済み (実装差分のバグではない)。
- 根本原因: pre-flight 検査 (`GIT_COMMANDS["submodule-config"]` = `git config --file
  .gitmodules ...`) が追跡ファイルの宣言 URL だけを見ており、本 repo の実際の環境設定
  (`external/ccbench` は `.gitmodules` 宣言が remote URL だが、`.git/config` に
  local override `submodule.external/ccbench.url = <common-dir>/modules/external/ccbench`
  が既に設定されている) を考慮していなかった。この関数の既存テスト・daemon.py の運用実績は
  全て宣言と解決済み URL が一致する (両方 local な) synthetic fixture でしか検証されておらず、
  「宣言と解決済みが乖離する」構成が代表されていなかった。
- 恒久対応: {{D:submodule-url-resolved-fallback}} により、pre-flight 検査を解決済み URL も
  考慮する対称判定へ拡張した (`tools/dev_waves/git_state.py::update_submodules_no_fetch`)。
  変異matrix M2 (KILLED) で単一理由の検出力を確認済み。
- 再発検知: `orchestrator/tests/test_dev_waves_git_state.py` に、宣言 local + 解決済み
  non-local override を拒否する回帰テストと、宣言 non-local + 解決済み local override を
  許可する回帰テストの両方を追加した。

### {{F:worktree-registry-spoofed-gitdir}}. 新設 worktree 身元検証が偽装 gitdir で回避できた [テスト代表性]

- 事象: [T-1428] で新設した `resolve_registered_worktree()` (stale な registry entry が
  無関係な repository に再利用されるケースを拒否する検証) の初版実装を、段6 の敵対レビュー
  2本が独立に、main worktree 自身の `.git` を指す偽装 `gitdir:` file を stale path に
  置くことで common-dir 検査を通過できると指摘した (2件が独立に同一脆弱性を発見)。
- 根本原因: common-dir の一致だけを見ており、候補の実際の gitdir が
  `<common_dir>/worktrees/` 配下にあるかどうかを検証していなかった。テストケースも
  「無関係な独立 repository」という単純な偽装しか検証しておらず、「本 repo 内の別の場所を
  指す偽装」という、より巧妙な変種が代表されていなかった。
- 恒久対応: `resolve_registered_worktree()` に `common_dir/worktrees/` 配下の実在パスである
  ことを追加検証した (`tools/dev_waves/git_state.py`)。変異matrix M1 (KILLED) で
  単一理由の検出力を確認済み。境界は {{D:registered-worktree-chroot-boundary}} に明記。
- 再発検知: `orchestrator/tests/test_dev_waves_git_state.py` に、main の gitdir を指す偽装を
  拒否する回帰テストを追加した。
- **残る限界 (恒久対応は未実施、次 wave 送り)**: 統合後の焦点再レビューが、「main ではなく
  別の実在・登録済み worktree の gitdir を指す偽装」は依然通過しうると指摘した。
  DW-O16 の fix 3巡上限に達したため、本 wave では対応しなかった。実害度の評価は
  {{D:registered-worktree-chroot-boundary}} を参照。

## supersede 追記

- F320 **supersede: 2026-08-20** — 恒久対応(「未実施、[T-1139]未裁定」)は[T-1428]が`tools/dev_wave_submodule_init.py`の新設と`docs/dev-wave/core.md` DW-C01のpointer置換で実施した。詳細は{{D:worktree-submodule-init-tool}}。
