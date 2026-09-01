---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-01
wave: dev-wave-t2115-cross-protocol-impl
seq: 3
---

## 新規

### {{F:stray-git-dir-in-shared-tmp}}. 共有 `/tmp` に置き去られた空の `.git` が、全 wave の受入を無関係な赤にする [環境] [非帰属赤]

- 事象: 焦点走で `test_screening_driver.py` の 8 件が
  `ValueError: official output_root は repository 外でなければならない` で赤になった。
  実装差分とは無関係で、この計算機で走る全 wave の同種テストを同時に赤にしていた。
- 根本原因: `/tmp/.git` という**空ディレクトリ**が 10 時間前から置き去られており、
  `orchestrator/campaign/layout.py` の祖先走査が pytest の一時ディレクトリ
  (`/tmp/pytest-of-<user>/...`) を repository 内と判定した。判定は `.git` の実在だけを見るため、
  中身が空でも成立する。repo 内のコードは `/tmp/.git` を作らず (全文検索 0 件)、
  cwd をそこに置く process も無かった。
- 恒久対応: 撤去は `rmdir` で行う (空でなければ失敗する形。他者の作業中 repository を
  `rm -rf` で壊さない)。撤去後に同じ焦点走が全緑へ戻ることを実測して非帰属を確定する。
  判定手順の正本は `docs/dev-wave/operations.md` の `DW-O18` (非帰属赤の着地) であり、
  本件は「assertion 本文と差分実体で判定する」を適用した実例である。
- 再発検知: 同型の赤は `output_root` 系 assertion が複数 test file で同時に出る形で現れる。
  自分の差分が触れていない file が同じ署名で落ちたら、まず
  `ls -d /tmp/.git` と `git rev-parse --show-toplevel` を疑う。

## 再発

### F242

- **再発: 2026-09-01** — 段 5 実装子と段 6 fix 子がいずれも sandbox の制約で pytest を
  1 件も実走できず (`rc=16 / child_started=false`、dispatch は `EACCTAUTH`)、
  静的レビュー 3 本 (段 3 の 2 レンズ + 段 6 レビュー 2 本のうち該当箇所) を通過した
  create-only test の欠陥が親の初回実測で出た。既存 file を書き込み先とは別の
  directory へ置いていたため、その test は機構を一度も通らずに赤になっていた。
  実装側は正しく、直すのは fixture の path だった。
