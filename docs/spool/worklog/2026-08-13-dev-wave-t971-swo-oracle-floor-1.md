---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-t971-swo-oracle-floor
seq: 1
title: 床値 sort_best の SWO oracle 不可用を実測で確定し、原因と診断の両方を塞いだ — 敵対 4 本が親の裁定を 5 度倒した (コード + docs、branch worktree-dev-wave-t971-swo-oracle-floor)
---

## 本文

- **親の第一候補仮説は当たっていたが理由が 1 段深かった。** 起票時の仮説は
  「`floor_campaign.sh` が `IZANAGI_SORT_SWO_MASSTREE_ROOT` を設定しない」。段 1 で
  production の `patchharness.checkout` + `resolve_oracle_environment` を job と同じ
  `TMPDIR` 形で実走させたところ、真の構造は
  **「使い捨て checkout 上では env var が唯一残った解決経路である」**だった。
  床値 driver は評価ごとに ccbench を `$TMPDIR/izanagi_wt_*/wt` へ checkout し
  (job では `TMPDIR=/scr/$PBS_JOBID`)、その path で resolver を呼ぶ。
  `build/_deps` は作りたてなので不在、祖先の `<name>-thirdparty-cache/masstree` は
  祖先が `/scr` なので届かない。共有 checkout 上では祖先 fallback が当たるため
  **login では再現しない**。compiler leg は健全だった (`/usr/bin/g++`)。
- **診断が消える場所も実測で確定した。** 床値 driver は `run_role` を使わず
  `prepare_cell` を直接呼ぶため `run_role` 側の WAL 記録を通らない。`build_cells` に
  捕捉は無く、`main()` は `FloorCampaignError` しか捕まえない。
  `SortSwoOracleUnavailable` の message は理由コード 1 語だけで phase も detail_code も
  乗らない。**姉妹経路 `p3_s4_loop_sort.py` は raise 前に記録しており、直す形の先例は
  repo 内に既にあった** (族一般化ではなく局所修復)。
- **敵対 4 本 (相談 2 + レビュー 2) が親の裁定を 5 度倒した。所見 13 件のうち refuted は 1 件だけ。**
  - (P1) 記録先を journal とする案を棄却。`classify_journal_resume_state` の strict L /
    M-prestart を壊す。ただし **plan の論拠は観測された pilot 構成では効かない** —
    その構成の journal は `reservation-preflight` 1 行で既に L でない。親は結論を維持し
    根拠を「driver stdout は `certificate` / `reservation_check` の有無に依らず必ず存在し、
    write capability にも resume 状態機械にも依存しない」へ差し替えた。
  - (P2) 「gflags/glog と同じ floor policy へ足す」は二重に誤り。gflags/glog は**凍結共有**
    `tools/pegasus/policy.json` にあり D115 で 1 byte も変えられない。かつ
    **masstree の pin は既にそこにある** (`silo_ladder_rung1.third_party_sources`、
    `pin` = 親が実測した cache の HEAD と一致)。足すと正本が 2 つになる。
    D152 決定 (3) に従い cache root は明示 env / 引数で受ける形にした。
  - (P3) 「HEAD 相当を pin すれば足りる」は偽。masstree の `config.h` は
    **`.gitignore:8` で除外された生成物**で Git 非管理。HEAD を固定しても中身は自由に変わる。
  - 段 1 brief の「ゲートは緩まず**厳しくなる方向**」は**運用上は偽**。正しくは
    「固定された compiler / dependency に対する PASS/REJECT predicate は不変」かつ
    「評価可能 domain と観測 PASS 数は増える」。レンズ A は凍結 `sort_best` comparator が
    storage 昇順 + 同一 storage 内 key 降順の辞書式 strict order であることから
    **PASS を静的に予測**した (probe の期待値として使える)。
  - 段 6 で**レビュー 2 本が独立に同じ穴を発見**: 新設した phase marker が
    `_phase_marker_root` の `None` 返しで**条件付き機能に退化**しており、staging 未設定なら
    marker ゼロのまま oracle と build が走る。かつ marker は最初の関連 subprocess より
    **後**に書かれていた。DW-G04 の「謳っているだけで発火しない」型。
  - レンズ B はさらに、**この wave が新設した dependency preflight 自身が汎用
    `FloorCampaignError` で倒れる**ことを指摘した。計算ノードで最も起きやすい失敗
    (共有 cache 不可視・`config.h` 欠落) がまさにそこを通るため、
    **塞ぐはずだった穴を新しい経路で作り直していた**。
  - refuted 1 件: 「snapshot patch が現物と一致しない」は `DW-S06-B` が fix 投入**前**の
    退避を要求しているため契約どおりの挙動。
- **scope 外と裁定した real 所見 3 件 (裁定パッケージへ)。**
  - 床値 build の FetchContent staging。`buildcache.py` に
    `FETCHCONTENT` / `masstree` / `mimalloc` / `googletest` の参照は **0 件** (grep 実測)。
    渡しているのは `silo_ladder_rung1.py:1046` と probe 群だけ。
    `docs/pegasus-runbook.md:744-756` は計算ノードの直結 network 不可と
    「proxy で FetchContent が通ると一般化するな」を明記する。
    → **本 wave は「床値が取れるようになった」と主張しない。**
  - oracle compile closure の byte 封印と receipt の耐久化。レンズ A の BLOCKER。
    `OracleReceipt` の full path はこの wave より前から存在し、
    `orchestrator/critic/digest.py` の `_ORACLE_RECEIPT_KEYS` が **frozenset 完全一致**を
    要求するため key を減らすと validator が全 receipt を捨てる。schema 変更は別 wave。
  - S5 / `p3_s4_loop_sort.py` の同型経路。floor 限定の解決では直らない。
    **floor が通ったことを理由に S5 も修復済みとは報告しない。**
- **frozen artifact の `p3_s4_loop_sort.py` source pin は歴史記録であり live pin ではない**
  (親の実測: 現行 hash `f6c37a9d...` ≠ pin `9b64f34b...`、consumer は旧 bytes を literal で
  要求する)。編集は pin 的に安全だが**再 pin は禁止**。
- **子は 3 回とも pytest を走らせられなかった** (`tools/run_tests.py` が
  `qstat -Q preflight rc=1` で rc=16)。緑はすべて親が実測した。
  子の報告は一貫して「静的検査のみ、実走 0 件、緑とは報告しない」で、正しく fail-closed していた。
- **段 6 投入で親が argv を誤り、レビュー 2 本が起動直後に rc=2 で落ちた** (`--lane` は
  `--stage consult` 専用)。別名で再投入し、既存 `.done` は消していない。
- 設計判断は {{D:floor-oracle-dependency-transport}}、失敗型は {{F:new-preflight-reintroduces-opaque-failure}} を参照。

## 次の一手差分

### 更新

- [T-971] **P1・部分完了**: 床値 sort_best の SWO oracle 不可用の原因を実測で確定し、
  診断・resolver・依存束縛・compiler 明示注入を実装した。**ただし床値は 1 件も取れていない** —
  FetchContent staging が別 blocker として残り、計算ノードでの end-to-end 確認も未実施。
  残件は (a) 計算ノードでの実測 (resolver 解決と CMake configure の可否を同時に測る短い PBS probe)、
  (b) {{T:floor-build-fetchcontent-staging}} の解決。
  base: 7edbbe42e445b4fe5529baa24f68a7e560f7c1b6685de02c05916b0c870c8e3c

### 新規

- {{T:floor-build-fetchcontent-staging}} **P1・新規 (B 系)**:
  床値 build 経路に FetchContent の source 差し替えを通す。`buildcache.py` には
  `FETCHCONTENT_SOURCE_DIR_*` の配線が 0 件で、計算ノードは直結 network 不可
  (`docs/pegasus-runbook.md:744-756`)。`silo_ladder_rung1.py:1046` に先例がある。
  **これが解けない限り、oracle を直しても床値は 0 件のままである。**
  shared build path のため全 campaign へ波及する点に注意。
- {{T:oracle-compile-closure-sealing}} **P2・新規 (B 系)**:
  oracle の compile closure を byte で封印し、oracle receipt を floor proof chain へ耐久化する。
  現状は env が transport 兼 authority になりうる。`config.h` は Git 非管理なので
  HEAD pin だけでは閉じない。`expected config.h hash` の置き場所は D115 (identity 非束縛の
  key だけ floor policy へ) と D152 (cache root は policy から導出しない) の双方に
  抵触しうる**未解決の設計択一**であり、裁定が要る。
- {{T:s5-sort-oracle-ambient-resolution}} **P2・新規 (B 系)**:
  `p3_s4_loop_sort.py` の oracle 依存解決も使い捨て checkout 上で失敗する。
  floor 限定の解決では直らず、S5 の sort_best gate・WAL・campaign report は
  `infrastructure-unavailable` に汚染されたまま。全 consumer へ trusted dependency root と
  compiler を明示注入する共通 seam を作るか、S5 を明示的に別扱いにするかの裁定が要る。
