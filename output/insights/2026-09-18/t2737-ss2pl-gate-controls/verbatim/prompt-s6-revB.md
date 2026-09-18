単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2737-ss2pl-gate-controls

## レンズ B — 整合と実効性: 材料は裁定に足りるか、probe と receipt は運用の穴を残していないか

## 必読事項の射影 (読めなければ即停止)

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/s4-ruling.md` — 段 4 裁定
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/verbatim-d2120-item12.md` — ユーザー裁定の逐語 (材料が答えるべき問い)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/codex-artifacts/dev-wave-t2737-ss2pl-gate-controls/s3-b.md` — 段 3 レンズ B (自分の前身。B1〜B8 が裁定で採用済み)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/codex-artifacts/dev-wave-t2737-ss2pl-gate-controls/s5-author.md` と `s6-fix1.md`
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/probe/README-probe.md`
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/probe/t2737_gate_probe.py`
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/receipts/probe-result-2.json` — 計算ノード job 2 の受領証 (fix2 版、主資料) と `probe-result-1.json` (job 1、warm-up 内部例外。plain build 後の 16 cell は有効)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/compute-2.log` と `compute-1.log` — dispatch の stdout (request ID、node、rc)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2737-ss2pl-gate-controls/tools/pegasus/run_ss2pl_lock_study.py` — runner (40-110、1061-1095、1334-1500、1657-1700、1928-2050、2054-2090)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2737-ss2pl-gate-controls/orchestrator/campaign/buildcache.py` — 2034-2110 (`prepare_masstree_fetchcontent`)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2737-ss2pl-gate-controls/docs/decisions.md` — `grep -n "^## D2131\."` でその節だけ ((iii) の既存実装形)

repo root は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2737-ss2pl-gate-controls`。**大きい file を全文 `cat` しない**。

## 攻撃点

1. **裁定充足**: D2120 項 12 の問い「代表的な inert / 非 inert arm で gate 不変のまま必要な比較 (stock 側 target / owner TU の成立を含む) が成立するか」に対し、receipt の 45 cell は (a) 非 inert 4 軸それぞれの drift がどの patch 変更で閉じたかを 1 対 1 で読めるか (current/O/phase1 の D/E/A/D と revs/O/phase1 の対)、(b) inert (S) がどの層 (patch / 登録簿 target / companion) で何まで進み、何で止まったかを一意に読めるか (current/O/S → current/T-/S → revs/O/S → revs/T+/S → revs/T-/S の鎖)、(c) (iii) の対 (pristine → warm) が同じ staging 複製・同じ木で取れているか (`attempt`、`staging_before/after`、`warm_up.before/after`)、(d) KIND の T+/T- 対 (companion の有無だけ) が phase1 で取れているか、(e) 欠落・冗長。
2. **runner 契約**: receipt の `static_contracts` (abort 所有権 2 版、study header 宣言) と `builds.S` の `_wfg_absence_evidence` の結果。試作を runner がそのまま食えるか / 食えない箇所 (abort 所有権 vs S 一致の衝突) が材料として一意に読めるか。`collect_inert_witness` 未実走の注記 (B3)。
3. **運用の穴**: `tempfile_gettempdir` / 空き容量 / `tools` の realpath・version / `pbs_jobid` 候補と `compute-1.log` の request ID の対応 / `staging_original_after == staging_original` / 予算未実施 cell の有無 / `internal_exception` の有無 / configure-failed cell の `diagnostic_configure` の stderr 全文に CMake 未使用変数警告が出ているか / 各 cell の秒数と合計 (walltime 内か)。
4. **probe と production の差 (F29)**: probe が runner の `_require_condition_gates` と同じ 3 呼び出し・同じ `configure_args` を使っているか (差があれば列挙)。`configure_args()` の中身と R:1988-2003 の照合。
5. **insight の表**: 親が書く予定の 1 表 (案・比較 / 成立した比較 / 成立しない比較 / 必要な変更層 / 隙間 / 証拠 cell) と裁定パッケージ案の骨子が、採否を先取りせず、層別に読めるか。特に「shadow-T は機構診断であり D2120 の YCSB 比較は未成立」を先頭に置くこと、「`__LINE__` (ERR) の残差は `#line` でしか消えない」ことの書き方。
6. **scope**: repo の実装面差分が 0 であること (job dir の成果物だけ) を前提に、親が段 7 で commit するのは insight (docs) + spool fragment だけか。probe の逐語 (`.py` → `.md`) と patch の逐語 (`.patch` → `.md`、provenance checker の `.patch` 拡張子扱いに注意) を insight に残す形の妥当性。

## 出力形式

所見ごとに: 番号、分類 (裁定充足 / runner 契約 / 運用 / F29 / 表 / scope)、real / refuted と根拠 (file:line または receipt の key path)、放置時に採否材料がどう変わるか 1 行、是正案。`## 総括` (必須) 10 行以内: real 件数、最重要、fix / 再投入の要否、材料として書けること・書けないこと。

## 禁止

file を作成・編集しない。git の状態を変えない。pytest を走らせない。走らせていない結果を緑と書かない。予算が尽きそうなら途中結論を出力形式どおり書いて終わる。
