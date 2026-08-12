---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-t921-perf-preflight
seq: 2
title: W-2 を実投入し、床値の停止点が perf でなく sort_best セルの SWO oracle だと実測した (計測、branch worktree-dev-wave-t921-perf-preflight)
---

## 本文

- **W-2 を 2 回投入し、2 回とも同一箇所で決定的に停止した。** job `908158.nqsv` (98 秒) と
  `908164.nqsv` (90 秒)、いずれも `pilot` 固定経路、source commit `2988e5dc`。
  失敗は `stage=floor_driver` / `rc=1` で、逐語は
  `orchestrator.campaign.sort_swo_oracle.SortSwoOracleUnavailable:
  sort-swo-oracle-infrastructure-unavailable` (`s1_direct_comparison.py:598`,
  `configuration = sort_best`)。**T-748 の「途中死は救出せず新規 job で再実行」に従って
  2 本目を出し、transient でないことを確かめた。**
- **停止点は測定ではなく 12 セルの実体化 (`build_cells`) である。** perf preflight は
  その手前にあり、abort せずに通過した。**perf を前提から外したことで、床値経路の
  次の閂が初めて表に出た**形である。過去 2 回の W-2 試行 (`873200` / `873225`) は
  official 拒否の rc=2 で実体化まで到達していないため、**build_cells に到達したのは
  今回が最初**である。
- **perf の判定結果は回収できなかった。** receipt は `manifest.json` にしか書かれず、
  manifest は `build_cells` の後に書かれるため、build 失敗時に失われる。
  run directory の journal に残ったのは `reservation-preflight` の 1 行だけだった。
  **段 3 の敵対レビュー (luna 所見 5) が予告した通りの実測**であり、
  親は当時これを scope 外と裁定していた。{{T:perf-receipt-persist-before-build}} で起票する。
- **成果物は repo へ commit せず repo 外 bundle へ退避した。**
  `/work/1/SFC/tanab/dev-wave-jobs/w2-floor-bundle-20260813/`。構成は
  run directory 2 file / job staging 84 file / submission receipt 38 file /
  **binary store 0 file** (build が sort_best セルで停止したため生成されていない)。
  bundle manifest は同 dir の `bundle-manifest.json`、
  sha256 = `a1f82235322b7cb4c76f187cd4dcac313195f80d1abd110e89fd07ac424b6acb`。
- **床値の実測値は 1 つも得られていない。** `floors` は生成されておらず、
  wave で追加した「driver rc=0 の後に床値の有限性を要求する」検査は今回発火していない
  (driver 自体が rc=1 で落ちたため)。
- **原因の仮説 (未確定、次の一手の入力)。** oracle は `resolve_oracle_environment` で
  masstree の source root を解決するが、候補は環境変数
  `IZANAGI_SORT_SWO_MASSTREE_ROOT`、`<ccbench>/build/_deps/masstree-src`、
  および ccbench の祖先から導く `<name>-thirdparty-cache/masstree` の 3 系統である。
  **`tools/pegasus/floor_campaign.sh` はこの環境変数を設定しない** (grep で 0 件)。
  永続 cache `/work/1/SFC/tanab/izanagi-thirdparty-cache/masstree` は実在するので、
  実体化先の path から祖先探索が届かなければ解決に失敗しうる。
  **これは仮説であり、job 側は infrastructure 詳細を artifact に残さないため未確定である。**

## 次の一手差分

### 更新

- [T-748] **P1・W-2 は投入済み・実測値は未回収。次の閂は SWO oracle (B 系)**:
  perf は閂ではなくなり、job は `build_cells` まで到達するようになった。
  **残る停止点は `sort_best` セルの SWO oracle 実行基盤**である
  (`sort-swo-oracle-infrastructure-unavailable`、2 job で決定的に再現)。
  床値の実測値は 0 件。証拠 bundle は
  `/work/1/SFC/tanab/dev-wave-jobs/w2-floor-bundle-20260813/`
  (manifest sha256 `a1f82235322b7cb4c76f187cd4dcac313195f80d1abd110e89fd07ac424b6acb`)。
  次は oracle 実行基盤の不可用理由を確定させること (masstree root の解決が第一候補)。
  base: cb72a2cd52c253d19ce3b4f332e29385e21f8f6e2e2ded4a595c9d2c6706f700

### 新規

- {{T:sort-swo-oracle-unavailable-on-floor}} **P1・新規 (B 系)**:
  床値経路で `sort_best` セルの SWO oracle が `infrastructure-unavailable` になる理由を確定し、
  解消する。job は詳細を artifact に残さないため、まず**不可用の詳細を記録させる**必要がある。
  第一候補は masstree source root の解決失敗
  (`floor_campaign.sh` が `IZANAGI_SORT_SWO_MASSTREE_ROOT` を設定しない)。
  **これが解けるまで W-2 の床値は 1 件も得られない。**
- {{T:perf-receipt-persist-before-build}} **P2・新規 (B 系)**:
  perf preflight の receipt を `build_cells` より前に journal または job staging へ
  create-only で残す。現状は `manifest.json` にしか書かれず、build 失敗時に判定が失われる
  (2026-08-13 の W-2 2 job で実測)。失敗した job から「perf が使えたのか」を後から言えない。
