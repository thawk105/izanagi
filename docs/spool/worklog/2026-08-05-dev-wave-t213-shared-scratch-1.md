---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-t213-shared-scratch
seq: 1
title: [T-213] 隔離 clone の共有 FS 移設は単独では発火しないと実測し、実装しないと裁定した — 前提 2 件を裁定へ返す (docs のみ、branch worktree-dev-wave-t213-shared-scratch)
---

## 本文

- **wave 引数の前提が stale だった。** 依頼は「前身 branch `rescue-t213` (保持裁定 (212)) を
  監査して取り込む」だったが、(212) は (216) が supersede 済み。親が git で再照合しても (216) を
  支持する — `rescue-t213` (tip `77db32c`、4 ahead / 793 behind) の `tools/run_tests.py` には
  `dir="/tmp"` が現存し (116) の是正を含まず、中身の計算ノード投入器は main の
  `tools/pegasus/dispatch_compute.py` に既存。**本 wave は rescue-t213 から 1 byte も取り込んでいない。**
  branch 削除は引き続きユーザー手番
- **段 4 で「実装しない」と裁定した (`4→7→8→9`)。** 実装差分が無いため、**変異 matrix と
  受入全走は本 wave の射程外**である。承認済み裁定 (116) 択 (a) を親が不採用にしたのではなく、
  裁定時点で未見だった新事実付きでユーザー再裁定待ちへ戻す
- **新事実 1 (Blocker、親が直接実行で確認)**: 実 repo の `.gitmodules` は HTTPS URL であり、
  supervisor が wave worktree 作成直後に呼ぶ `update_submodules_no_fetch()` は
  `RUNTIME_IO_FAILURE {'label': 'submodule', 'kind': 'nonlocal-url'}` を送出する。
  **隔離 clone は 1 度も作られない**
- **新事実 2 (Blocker、親が直接実行で確認)**: 既定 fixed check の `orchestrator` は acceptance shape で、
  submodule preflight が site 判定より前に走る。隔離 clone は `--no-local` で modules cache を
  持たないため `preflight_submodule_rc=14` となり dispatch 分岐へ到達しない。
  **(116) の「同じ clone で走る orchestrator check も同時に解消する」は移設だけでは達成できない**
- **新事実 3 (実測)**: 共有 FS 移設は clone 所要を `/tmp` 6.60 s → `/work` 17.95 s へ増やす。
  clone 1 回の timeout は 30 s 上限で active 段は 2 回行うため、移設は clone timeout 由来の
  新種 `CHECK_FAILED` を作りうる
- **動機自体は成立する (実測)**: job `0:890520.nqsv` (gen_S, bnode008) で、login node の `/tmp`
  marker は計算ノードから不可視 (`marker_visible=no`)、`/work` は双方向可視。誤っていたのは
  問題意識ではなく「移設だけで解決する」という射程評価である
- **`tools/run_tests.py:717` の `dir="/tmp"` は変更不要で確定。** 敵対レビュー 2 本が独立に
  経路解析で支持した — login dispatch は sidecar 環境を除去し、計算ノード子は task-run ID を
  持たないため `_private_sidecar()` を呼ばない。producer と consumer は常に同一ノードである。
  (216) がこの行を「未実装の証拠」として引いたのは誤読だった
- **親 brief 自身の欠陥も real 判定した**: 不変条件に置いた「受理集合不変」は本 wave の目的
  (rc=16 で fail していた入力を実検査後の pass に変える) と矛盾する恒真な保証だった。
  再設計時は許容遷移を明示的に書く。親の置き場案 (既存 `worktrees/` namespace) も
  `discover_runs()` との衝突で撤回した
- 逐語・実測値・敵対レビュー所見表は `output/insights/2026-08-05_t213-shared-scratch-blockers.md`。
  一次成果物は repo 外 `/work/1/SFC/tanab/dev-wave-jobs/t213-shared-scratch/`
- **ユーザー裁定待ち 6 件** (詳細は insight §6-7 と job dir の `s4-adjudication.md`):
  (1) T-213 の再定義 — 前提を先に解くか pilot に組み替えるか、(2) supervisor の submodule
  bootstrap 権威、(3) 隔離 clone への submodule 供給、(4) dispatch 依存の trust closure と
  site 権威の一本化、(5) compute 実行の attestation、(6) 共有 FS 残骸の回収と custom runtime の
  discovery 衝突

## 次の一手差分

### 更新

- [T-213] **P2・ユーザー再裁定待ち ((116) 択 (a) の射程が実測で否定された)**: 隔離 clone を
  共有 FS へ移す動機は実測で成立するが (login `/tmp` は計算ノードから不可視、job `0:890520.nqsv`)、
  **移設だけでは目的を達成しない**ことが 2 件の直接実行で確定した — (i) 実 repo は HTTPS
  submodule URL のため supervisor が `nonlocal-url` で停止し隔離 clone に到達しない、
  (ii) 隔離 clone は `--no-local` で modules cache を持たず `orchestrator` check が
  submodule preflight で rc=14 となり dispatch へ到達しない。`tools/run_tests.py:717` の
  `dir="/tmp"` は変更不要で確定 (producer と consumer は常に同一ノード)。
  裁定待ちは 6 件 (T-213 の再定義、submodule bootstrap 権威、隔離 clone への submodule 供給、
  dispatch 依存の trust closure、compute attestation、共有 FS 残骸の回収)。
  逐語は `output/insights/2026-08-05_t213-shared-scratch-blockers.md`
  base: 45f4914a48864235eac0a75c8578e389db026b3c3eb8205e2d3033844d5f60fe
