---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t748-pilot-path
seq: 5
title: W-2 を実投入して床値経路の欠陥 4 件を潰し、5 つ目で計算ノードに perf が無いことを確定した — 測定は環境手番待ちで停止 (コード + docs、branch worktree-dev-wave-t748-pilot-path)
---

## 本文

- **裁定 (c) の実装を land した後、W-2 を実際に投入した。4 回投げて障壁が 4 件出て、
  いずれも実投入でしか出なかった。** 静的レビュー 4 本 (段 3 の 2 本 + 段 6 の 2 本) は
  1 件も見つけていない。
- **障壁 1 — submission receipt が canonical JSON でなく admission が必ず落ちる。**
  job は 6 秒で `{"gate":"admission","reason":"floor receipt strict read failed"}` に落ちた。
  `submit_floor.sh` は indent=2 で整形して書く一方、計算ノード側の
  `certified_writer_admission` は `load_json_strict` で canonical bytes を要求する
  (実測: raw 4542 bytes / canonical 4331 bytes)。**floor の投入経路は一度も admission を
  通れたことがなかった。** 書き手を canonical へ寄せた。`load_json_strict` は緩めていない。
- **障壁 2 — scheduler 出力が repo の中に落ち、次の投入を自分で詰ませる。**
  `qsub -o/-e` を渡していなかったため `floor_campaign.sh.e905894` が worktree 直下に出た。
  これは `output/` 外の untracked なので、submit の clean 検査が**次回を必ず拒否する**。
  nonce ごとの submission directory 内へ向けた。runbook §8 が警告していた罠そのものである。
- **障壁 3 — attestation が「測定器の名前」の exact 一致で第 1 世代を構造的に排除していた。**
  `effective_clock.method` が期待 `proc-cpuinfo` / 実測
  `proc-cpuinfo-rotating-min/k5/...` で不一致。**クロックの実測値は第 1・第 2 世代とも
  2101.0 MHz で一致しており機械は同じ**で、probe が第 1 世代の取得後に改良されたため
  現行 probe は旧 method 文字列を二度と出せない状態だった。
  **ユーザー裁定** (2026-08-12、「ソースコードがこれの時に測定しましたみたいな厳格な一致リストや
  保証まではいらない」「参考情報でいい」) に従い、method を判定から外し receipt には残した。
  設計判断は {{D:attestation-tool-name-is-provenance}}。**物理量の許容幅比較・governor・
  CPU model・TSC・cache/NUMA/core 数は一切変えていない。**
- **障壁 4 — [T-783] の site 解決化に取り残しが 1 箇所あった。**
  `build_cells` は site 解決済み cxx を渡すのに、`prepare_cell` → `source_digest.resolve` は
  既定値 `g++-13` のままで、Pegasus に無い compiler を要求して fails-closed で止まっていた。
  `cxx` を必須キーワード引数にして暗黙 fallback を封じ、共有 materializer を使う
  floor / oracle / S-1 の 3 経路へ通した。**既定値は変えていない** —
  どの compiler で照会したかは identity に効くためである。
- **障壁 5 (未解決・環境手番) — 計算ノードに perf が無い。**
  実 campaign 2 ノード (bnode049 / bnode130) と probe 6 ノード
  (bnode013/021/023/027/031/032) の **8/8 で `perf stat` が rc=2** である。
  計算ノードの kernel は `5.15.0-173-generic` だが `/usr/lib/linux-tools/` には
  `5.15.0-100` と `5.15.0-135` しか無い。login ノードは kernel `5.15.0-186` で
  tools は 101/136/173 — **自ノード用がやはり無い。**
  第 1 世代 calibration は 2026-07 に bnode011 (同じ kernel 5.15.0-173) で perf 込みで
  取得できているので、**その後の更新で欠けた**。詳細は {{F:pegasus-compute-perf-missing}}。
- **「rc=0 / status completed」は成功ではなかった。** 障壁 5 の 2 回はいずれも driver が
  rc=0 を返し `status: "completed"` だったが、**120 回の測定試行が全て `launch_failure`
  (1 回 0.17 秒) で床値は全 null**、`floors` の理由は「stock セル無効/不在」だった。
  rc だけを見ていれば「W-2 完了」と誤報告していた。
- **待ち方の恒久対応を入れた (ユーザー是正)。** 初回投入時、親は `qstat` の `PRR` だけを見て
  「10 時間かかる」と報告し、F49 (ii) の 3 点目 (計算ノード側 marker の実在) を
  「後で確認する」と先送りした。**その 6 秒後に job は死んでいた。**
  ユーザーの是正を受け、`floor_liveness` を追加して有界時間で 4 分類
  (queue 待ち / 実行中かつ marker 実在 / 終了済み / 判定不能) を返すようにした。
  **`request_disappeared_is_success` は常に false** で、終了時は `failure.json`・
  driver stderr・`job-result.json`・scheduler stderr から理由を回収する。
  障壁 3〜5 はいずれもこの機構が数分で理由つきに落として見せた。
- **AI 工数**: 本 phase は codex 子 4 本 (author 3 / fix 1)。焦点走は計算ノードで
  64 passed → 202 passed → 461 passed / 15 skipped、いずれも rc=0。
- **ユーザー手番**: 計算ノードへの linux-tools 導入 (下記「新規」)。push は行わない。

## 次の一手差分

### 更新

- [T-748] **P1・投入経路は開通済み。測定は環境手番待ちで停止 (B 系)**:
  裁定 (c) の固定 pilot 化に加え、実投入で見つかった経路欠陥 4 件を潰した。
  **admission・attestation・toolchain 束縛・実体化はすべて通過し、campaign は 12 セルを
  実行するところまで到達している。** 残る停止点は測定そのもので、
  計算ノードに perf が無いため 120 試行が全て launch_failure になる。
  **perf を外す回避は取らない** — production command が測定契約に焼き込まれており、
  第 1 世代 calibration も perf 込みで取得されている。
  perf が入り次第、`submit_floor.sh` の投入 1 回で再開できる。
  base: 140f693f8b026451794981500d5c86ba4d7e9f592a02c4c99ab486e79b17b5df

### 新規

- {{T:pegasus-compute-perf-restore}} **P1・ユーザー手番 (B 系)**:
  計算ノードに現行 kernel (`5.15.0-173-generic`) 用の linux-tools を入れてもらう。
  実測は 8/8 ノードで不在、`perf stat` rc=2。**これが無い限り床値・calibration・oracle の
  いずれも測れない。** login ノードも自 kernel (`5.15.0-186-generic`) 用が無い。
  代替として第 1 世代 calibration が取得できた 2026-07 時点との差分 (kernel 更新に
  linux-tools が追随していない) を管理者へ伝える形が要る。
- {{T:floor-preflight-perf-check}} **P2・ユーザー裁定待ち (B 系)**:
  perf の可用性を**測定を始める前に**確かめる preflight を置くか。
  現状 attestation は CPU・cache・クロックを照合するが「測定器が動くか」を見ないため、
  12 セル分の build を終えてから 120 回続けて失敗する。
  build 費用を捨てる前に止められる。
