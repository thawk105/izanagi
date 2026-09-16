---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2668-tmpdir-outside-repo
seq: 1
title: [T-2668] repo 直下に一時 dir を作る test の残り 2 箇所を repo 外 / ignore 済み path へ移した (テスト、branch worktree-dev-wave-t2668-tmpdir-outside-repo、変異 matrix = baseline PASSED・3/3 KILLED・等価変異 1 件 SURVIVED (登録どおり)・MISMATCH 0・期待 node 完全一致)
---

## 本文

- **依頼の scope**: F998 の生成箇所を repo 外 (または `output/` 配下の ignore 済み path) へ移すだけ。
  被害者 test の hold 登録は禁止、gate・検査・台帳・一般化の追加は scope 外 (ユーザー指示)。軽量版で進め、
  段 2・3 と段 6 のレビュー子は省いた (設計択一は親の provisional 裁定 1 件で根拠つき、正しさ防壁の本体と
  受理集合に触れない)。実装は Codex author 1 本 (gpt-6-astra / medium、model call 5、135 秒、receipt accepted)。
- **主目的は着手前に済んでいた (stale carry)**: 起票 (1526) が名指す `test_t316_sandbox_probe.py:1736` は
  同日 10:28 の commit 9d9df64f1 (F999 の wave、Codex author) が `main checkout の親/.izanagi-t316-live` へ
  移設し main に着地済み。持ち越し (1558) は 9d9df64f1 より古い写しだった。
- **残る同型箇所は 2 件で、どちらも同じ commit で閉じた**: 指定の `git grep -n "dir=_REPO" -- orchestrator/tests`
  は 1 件 (`test_hooks.py` の hardlink test)。性質検索 (`dir=ROOT`) で純増 1 件 (`test_s1_9pair_figure_provenance.py`
  の test_p9)。後者は production `plot_s1_9pair._repo_path` が REPO_ROOT 外を拒否するため repo 外へ出せず、
  `.gitignore` 済みの `output/runs/` 配下へ移した (親の provisional 裁定 P1、依頼文の「または `output/`
  配下の ignore 済み path」に該当、前例 `test_codex_worker_launch.py`)。`test_calibration_freeze_authority_contract.py`
  の `dir=str(ROOT)` は plain runner (`__main__`) 専用で pytest 受入では発火しないので対象外。
- **hardlink test の同 device 前提を両 venue で実測した**: login (pegasus02) と計算ノード (bnode009) の両方で
  `/tmp` と authority (`/work/1/SFC/tanab/dev-wave-authority`) は別 device (分岐が発火する) であり、移設先
  `/work/1/SFC/tanab/.izanagi-t2146-hardlink` から authority への `os.link` は成功する (実 authority file の
  inode 検査は synthetic fallback へ落ちない)。probe script は job dir に保全して repo へ入れず、出力だけを
  insight の `verbatim/` に残した。
- **Codex sandbox では移設先へ書けない**: author 子の焦点走で hardlink test は `mkdir` の `EROFS` で落ちた
  (sandbox の書込範囲外)。t316 の fixture (9d9df64f1) と同じ露出であり、fallback は足さず (scope 外)
  親が sandbox 外で実走した (計算ノード request 1837.nqsv、2 passed)。
- **変異 matrix** (tip cc6e1fc54、dispatch、request 1924〜1936.nqsv): 事前登録 = M1 (導出 root を repo へ)・M2 (mkdtemp の
  `dir=` を repo へ)・M3 (s1 の `dir=` を repo root へ) + 等価変異 1 件。baseline PASSED、3/3 KILLED、等価変異は登録どおり
  SURVIVED、MISMATCH 0、期待 node 完全一致。erratum 1 件: M1 の赤 message は予告した `artifact-root-inside-repo` でなく
  `artifact-root-in-control-container` (wave worktree が `.claude/worktrees/` 下にあるため。層は同じ `_validate_shared_root`
  1 つで単一理由性は保たれる)。台帳・spec・逐語は insight `output/insights/2026-09-16/t2668-tmpdir-outside-repo/`。
- **受入全走**は本記録 commit を含む tip に対して land 前に 1 回だけ投入し、child-green でなければ land しない。
  本エントリの作成時点では未実施である。
- 失敗台帳: F998 の恒久対応末尾 (別 wave が直す) を本 wave で実施済みとして supersede 追記した。

## 次の一手差分

### 完了

- [T-2668] `test_t316_sandbox_probe.py` は 9d9df64f1 で移設済み。残る同型 2 箇所 (`test_hooks.py` の
  hardlink test = `main checkout の親/.izanagi-t2146-hardlink`、`test_s1_9pair_figure_provenance.py` の
  test_p9 = `output/runs/` 配下) を cc6e1fc54 で移設した。`git grep -n "dir=_REPO\|dir=ROOT\|dir=str(ROOT)" -- orchestrator/tests`
  の残り hit は repo 外 (`dir=_REPO.parent`) と plain runner 専用 (`dir=str(ROOT)`) の 2 件だけで、pytest 受入で
  repo 直下に作る箇所は 0 件。被害者 test の hold 登録はしていない。
  remaining: none
  base: e97e20b65a333e2b064fafc4db89e652b1599d5f6a48a4d04f64912dcec5a102
