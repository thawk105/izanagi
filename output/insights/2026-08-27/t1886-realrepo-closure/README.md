# 2026-08-27 [T-1886] / [T-1936] real-repo 排他閉包の穴埋めと、床の再測定

wave branch `worktree-dev-wave-t1886-realrepo-closure-split`、実装 anchor commit
`cf1a5c9202f1ac2732545e7f0e43e1a0e27365ab`。

## 一次資料の地図

- `verbatim/brief.md` — 親 brief (段 1)。中心的前提は段 2 で反証された
- `verbatim/brief-erratum.md` — 親が自分で見つけた brief の訂正 2 件
- `verbatim/s2-plan.md` — 段 2 プラン (codex, plan, read-only)
- `verbatim/s3-lens-a.md` / `verbatim/s3-lens-b.md` — 段 3 敵対相談 2 レンズ
- `verbatim/s4-adjudication.md` — 段 4 裁定と plan v2 (親)
- `verbatim/s5-author.md` — 段 5 実装子の完了報告
- `verbatim/s6-review-a.md` / `verbatim/s6-review-b.md` — 段 6 敵対レビュー 2 本
- `verbatim/s6-fix.md` / `verbatim/s6-fix2.md` — 段 6 fix 子 2 本の報告
- `mutation-probe-spec.json` / `mutation-probe-out.json` — 変異 probe (全件 SURVIVED 期待)
- `mutation-final-spec.json` / `mutation-final-out.json` — 変異 matrix 本走

## 親が実測した数値 (すべてこの wave 内で取得)

### 受入 wall の床は「real-repo 排他鎖」ではない

- `orchestrator/tests/acceptance_duration_ledger.json` と `REAL_REPO_ACCESS_BY_NODE` を
  突き合わせた marker 付き node の所要合計は 90 family / 93 instance / **266.32 秒**。
  内訳は共有ロックのみの instance が 266.13 秒、排他 writer が 0.19 秒。
- **同じ 90 node を実際に走らせると pytest wall は 74.91 秒である**
  (`tools/run_tests.py` 経由、Pegasus 自動 dispatch request `951549.nqsv`、rc=0、
  52 passed / 41 skipped、総所要 110.3 秒は queue 込み)。
  合計の 3.6 分の 1 で終わる。**この集合は直列鎖を作っていない。**
- 直列でない理由は `orchestrator/tests/conftest.py` の collection hook が、
  process memo 4 本を除く全 real-repo node から `@real-repo` suffix を除去するためである。
  xdist 3.8.0 の `LoadGroupScheduling._split_scope` は suffix の無い nodeid を
  full nodeid scope として扱うので、残りは 1 node = 1 work unit になる。
  既存テストの docstring も
  `Historical name: only the four process-memo nodes remain one work unit` と書いている。
- この形は D1008 (2026-08-26) が既に決定・実装しており、D1103 (2026-08-27) が K=3 を実測している。

### 排他 writer の 0.00 秒は regime 固有である

`(parent=read, ccbench=write)` の 3 本は
`cmake` / `gcc-13` / `g++-13` / `nm` を要求する `skipif` 付きの slow real-build canary である。
**この login node には `gcc-13` / `g++-13` が無い**ため skip される (親が `shutil.which` で実測)。
固定 toolchain のある計算ノードでは走り、`ccbench` へ排他を取って実 build cache へ書く。
「排他 writer は無視できる」は login node regime 限定の言明であり、転移させてはならない。

### 長寿命 fixture group の所要 (統合しない根拠)

- `s8c-preregistration-candidate` = 83.5 秒 (named 5 consumer)
- `s8c-predicate-snapshot` = 52.0 秒 (3 consumer)
- `campaign-repository-scan` (本 wave 新設) = 0.004 秒

現在この 2 group は別 worker で並行に走る (critical path 83.5 秒)。段 2 plan が提案した
「全部を canonical `real-repo` へ統合する」案を採ると **1 worker 上の 135.6 秒の直列鎖**になる。
5 分の絶対上限に対して余裕を半分近く食い、D1035 が選んだ方向とも逆なので却下した。

## 閉じた閉包の穴 (7 点)

依頼が名指ししたのは 3 点だったが、段 2 が 1 点、段 3 レンズ A が 2 点、段 6 レビュー B が 1 点を
追加で見つけた。

1. T810 の live-authority 3 node が無 lock で親 Git common-dir の linked-worktree registry を読む。
   **前 wave で実際に rc=1 の偽赤を起こした経路である。** `REAL_REPO_CLASSIFIED_NODES` (92 件) に
   1 つも入っていなかった。
2. 実親 repo の object database へ候補 commit を書く session fixture 2 系統が登録外。
3. 実作業木を走査する session fixture が登録外。
4. 実 HEAD を読む module fixture `current_commit_snapshot` が登録外 (段 2 が追加発見)。
5. suite 全体を subprocess collect する 3 node が登録外 (段 3 で 2 本、段 6 レビュー B が 3 本目を発見)。
   3 本目は `test_g6_all_real_repo_items_stay_one_unit_and_keep_relative_order` で台帳 14.0 秒。
6. controller の prewarm 2 系統が node protocol の外で実 repo resolver を動かす (段 3 レンズ A)。
7. lock key が worktree root 由来で、同じ Git common-dir を共有する sibling worktree を排他しない。

## 段 6 が見つけた実装の破れ 2 件

- **同一 process の SH → EX 自己 deadlock** (レビュー A)。module scope の共有 fixture を保持したまま
  同 module の function scope 排他 fixture へ入ると、別 fd を開くため 245 秒 timeout で自滅する。
  資源ごとに 1 process 1 fd とし、参照 count と mode の優越 (read < write) で
  同じ fd を昇格・降格する形へ作り替えた。
- **common-dir resolver が lock の外で実 repo を読んでいた** (レビュー B)。
  `git rev-parse --git-common-dir` の実行区間が無保護だったので、
  旧 key を先に取得してから解決する順序へ変えた。

## 変異 matrix

anchor `cf1a5c9202f1ac2732545e7f0e43e1a0e27365ab`、`--runner-mode dispatch`。

- probe (全件 SURVIVED 期待、観測 node 収集): baseline rc=0、9 変異すべて rc=1。
  観測 node は延べ 16 件。
- 本走: **baseline PASSED、KILLED 9 / 9、SURVIVED 0、MISMATCH 0、TIMEOUT 0。**

閉包の穴を復活させる 2 変異 (`t810-live-reader-unregistered` /
`nested-collection-node-unregistered`) は独立に 3 本の検査が殺した。
lock の昇格機構は `legacy-key-not-acquired` と `predicate-candidate-lock-removed` の
両方で発火しており、恒真ではない。

## codex 子の工数

plan 1 / consult 2 / author 1 / review 2 / fix 2 の計 8 本。いずれも `gpt-5.6-sol`、
`reasoning=xhigh`、rc=0、`check_codex_output.py` rc=0。
**実装子・fix 子はいずれも sandbox から計算ノードへ dispatch できず (`qstat -Q preflight rc=1`)、
pytest を 1 件も走らせられなかった。** 実測はすべて親が行った。
