---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: dev-wave-t1431-floor-resubmit
seq: 1
title: '[T-1431] 床値pilotを再投入し[T-1437]解消を確認したが新blocker (masstree staging未配線) でfail-closed停止、実測未達 (docsのみ、branch worktree-dev-wave-t1431-floor-resubmit)'
---

## 本文

- D581 (decisions.md:23453) に従い、前回insight
  (`output/insights/2026-08-20_t1431-floor-pilot-measurement/README.md`) の投入パラメータを
  そのまま再利用して床値pilotを再投入した ([T-1431]、entry 743 起票)。
- **重複稼働チェック (投入前実施、live ownerなしと確認)**: git worktree一覧・ListAgents
  (11 peer sessions)・admission claims/consumed (直近ファイルは8/16)・floor submissions dir
  (直近投入なし)・qstat (floor関連job不在、`izdw-*`系ジョブは別wave
  `T-1428-worktree-submodule-tool`の汎用計算dispatchと確認) のいずれにも同一
  T-1431・floor pilot・admission keyを扱うlive ownerを確認できなかった。受入lease
  (`land-lease`)は別waveの受入待ち行列で混雑していたが、floor pilotのadmission ticket system
  とは別系統であり投入をブロックしなかった。queue状態は`qstat -Qf gen_S`でActive/Enable、
  停止していないことを確認した。
- **[T-1437] (D615)は意図通り機能した。** 今回の投入ではmocc source_digest由来の停止は
  一切発生せず、driverはprotocol解決を通過しfloor-driverが実際に起動、複数セルのbuild段階
  まで進んだ (前回entry743はprotocol解決直後で停止していた)。
- 投入 (request 928510.nqsv、nonce fe5670379a689c3fc94d694241377830、queue gen_S、10h割当)
  から142秒でdriverがrc=1を返しfail-closed停止した。12セル中preflight 12/12通過、build開始
  4/12、oracle段階到達1/12 (`rr20::sort_best`)でfail、実測値を得たセルは0/12。
- **新blocker: `rr20::sort_best`セルのSWO oracle依存 (masstree) の取得が計算ノードで失敗した
  (`SortSwoOracleUnavailable: sort-swo-oracle-infrastructure-unavailable`)。** 計算ノードは
  直結外部networkが使えず (`docs/pegasus-runbook.md:749-762`)、CMake FetchContentでmasstreeを
  直接取得できない。代替解決経路`IZANAGI_SORT_SWO_MASSTREE_ROOT`
  (`orchestrator/campaign/sort_swo_oracle.py:1130-1131`、D399設計)が`tools/pegasus/floor_campaign.sh`
  に未配線 (grep実測0件)。**これは新規欠陥ではなく、2026-08-14の[T-971] (entry549、D399、
  branch worktree-dev-wave-t971-swo-oracle-floor) が実測・特定した上で明示的にscope外と裁定
  した既知gapの再現である。** T-971当時「本waveは『床値が取れるようになった』と主張しない」と
  明記されており、floor_campaign.sh側の配線は今日まで未着手のまま。mocc blockerと独立した別
  問題であり、T-1437はこちらを修正する設計ではない。
- 設計択一は既存裁定 (D581・D399) で決着済みで正しさ防壁・受理集合に触れないため、段2/3の
  codex起草・敵対相談は省略した (前回entry743と同型の軽量版判断)。Codex子は0本。
- **admissionチケット消費ゼロを確認した** (claims/consumed両ディレクトリとも投入時刻以降の
  新規fileなし、build_cellsのticket消費段に未到達)。retry_slots_per_cell=2を12セルぶんフル
  保持したまま次回再投入できる。
- 証拠一式 (submission receipt・job staging・checkpoint・run directory・claim marker・
  s8b-build-cache、計159 file) はrepo外bundle
  (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1431-floor-resubmit/evidence-bundle/`) へ
  MANIFEST.sha256付きで退避し、repo内untracked pathは削除した (holdout clean-scan汚染回避、
  前回entry743と同運用)。詳細・file:line裏取りは
  `output/insights/2026-08-21_t1431-floor-pilot-resubmit/README.md`参照。
- 本pilot試行はofficial floor・certified artifact・H1/H2の科学的結論としては扱わない
  (command指示どおり)。
- **エージェント工数**: 0 (Codex子を起動していない、段2/3/5/6を全て省略した軽量版)。

## 次の一手差分

### 更新

- [T-1431] **P1・{{T:floor-masstree-staging}}完了後に再開可能 (2026-08-21)**: D581に従い
  床値pilotを再投入し[T-1437]解消を確認したが (mocc blockerには再遭遇せず)、
  `rr20::sort_best`セルのSWO oracle依存 (masstree FetchContent) が計算ノードで未配線のため
  新たにfail-closed停止した (12セル中実測値0件、admissionチケット消費ゼロ)。この gap は
  2026-08-14の[T-971] (D399) が既にscope外と裁定した既知問題の再現であり、
  {{T:floor-masstree-staging}}での配線完了後、本insightの投入パラメータをそのまま再利用して
  再々投入できる。
  base: 8bf4f25f4b5837a40afa8335ebeb1460c96db9d92257d0c8bab57c82f7548604

### 新規

- {{T:floor-masstree-staging}} **P1・新規**: D399の設計
  (`IZANAGI_SORT_SWO_MASSTREE_ROOT` env var transport) に従い、`tools/pegasus/floor_campaign.sh`
  へmasstree source rootのログインノードpinned staging→計算ノード受け渡し配線を追加する。
  `tools/pegasus/silo_ladder_rung1.sh`の先例を参照。配線完了後、[T-1431]の床値pilot再投入を
  再開できる。詳細は`output/insights/2026-08-21_t1431-floor-pilot-resubmit/README.md`の
  「推奨する次の一手」参照。
