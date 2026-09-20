---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-verifier-capacity
seq: 1
title: verifier の容量 — 10 s trace の未完走 2 型 (edge worker の copy-on-write による OOM kill / SIGTERM 無視環境での pool 停滞) を計算ノードで同定し、producer / versions の packed 配列化 + 配列だけを読む edge worker で balanced 10 s 478 s・write-heavy 10 s 297 s を node peak 32 / 15 GiB で完走、判定は旧版と bytes まで同一 (コード + docs、branch worktree-dev-wave-verifier-capacity)
---

## 本文

- **起点はユーザー依頼 (台帳 ID 未起票)。** D2160 項 4 の未完走 2 型 (balanced 10 s の SIGKILL、write-heavy 10 s の 3600 s timeout) の原因同定と、B-8 の長時間実行を可能にする範囲の省メモリ化・分割。規律 2 (検査の意味・正例負例の同一性) と規律 1 (性能計測 build 不変) を不変条件にした。
- **段 1 (profile、計算ノード 9 job + 対照 3):** 原因は fork した edge worker 16 本の copy-on-write (worker 1 本の Private_Dirty 6〜7 GiB、node 113〜119 GiB で OOM kill)。balanced は親が殺され、write-heavy は worker が殺されて pool が壊れ、残 worker が SIGTERM 無視環境で停滞 → {{F:broken-pool-hangs-when-sigterm-ignored}}。`gc.freeze()` 単独は効かず、worker 数 8 / 4 では完走するが複製量は増える。一次資料 `output/insights/2026-09-20/verifier-capacity/README.md` §2。
- **段 2 / 3 (plan 1、consult 2、gpt-6-astra / medium):** 段 3 の must-fix は 6 件 (JSON 一致は非 wire integrity の代用にならない、source replay の完全性、Private_Dirty だけで CoW を同定しない、観測 schema の固定、最小案から積む、**read-heavy 10 s は未保全・未実走 → 完了条件を bal10 / wh10 + 完走済み trace の同一性へ修正**)。全件 real として裁定 (`s4-ruling.md` §2)。brief の誤り 5 点 (単価は全体比、主 process CPU は worker 合算、「永久に得られない」は過大、など) も記録。
- **段 4 裁定:** {{D:verifier-packed-producer-array-workers}}。(i)+(ii) を 1 変更、freeze 不採用、既定 worker 16 不変、witness 同一性は A 案、CSR / 配列 Tarjan / 前判定は実装しない、pool 破綻の終端修正、段 5 は直列 2 単位。
- **段 5 (Codex author 2 本、各 9〜10 分):** 単位 1 `11f0f1972`、単位 2 `f29ef5ec1`。fixture 22 件の旧版 `result_to_dict` sha256 一覧 (親が base で採取) と一致、焦点走 (計算ノード) 302 passed。
- **段 6 (review 2 本、GO・must-fix 0、fix 巡なし):** 留保は「rh6 と 12 verdict 比較の完了」で、compare で補った。compare (旧 `947fd160a` → 新、同 node 同 trace、`result_to_dict` + `VerifyResult` 全 field): balanced 10 s 478 s / node peak 32.4 GiB (旧 8 worker 725 s / 78.7 GiB、旧 16 worker は OOM kill)、write-heavy 10 s 297 s / 15.2 GiB (旧 8 worker 493 s / 72.4 GiB、旧 16 worker は timeout)、balanced 6 s 275 s / 19.5 GiB (旧 364 s / 80.2 GiB)、read-heavy 6 s 896 s / 81.2 GiB (旧 933 s / 85.7 GiB、隣接構造は不変なので親 RSS はほぼ同じ。producer 段は 57 → 106 s に伸びる)、いずれも同一。12 verdict (fixed-5 / fixed-10 × 3 s / 6 s) の同一性は insight §4 の表。変異 matrix は insight §5。
- **裁定パッケージ (ユーザーへ、insight §7):** read-heavy 10 s の入力取得と B-8 の対象・種・長さ、校正規則 ≤ 600 s の扱い (改修版では 10 s 2 件が 600 s 内)、既存 campaign lock の drift。
- 段 1 の親の失敗 2 件 (実害なし、記録のみ): probe の `--trace-src` 仕様で manifest の置き場を誤り 6 job が即失敗 (hardlink dir で回避)、selftest の flake で 1 job が本走に進まず (gate を relaxed に)。
- 工数: codex 子 9 本 (author 4 = probe 2 + 実装 2、plan 1、consult 2、review 2)。計算ノード job: profile 9 + 対照 3 + 失敗 attempt 6、焦点走 2、compare 14、変異 probe / 本走。

## 次の一手差分

### 完了

- [T-2350] 直列性検査の鍵の大域 id を writer を持つ鍵に限る形を {{D:verifier-packed-producer-array-workers}} 項 2 で実装した (file ごとの token→key_id 配列、親は read を走査しない)。
  remaining: none
  base: 0e6bc9dd55feb21d414a2cc9f0ead2ff52622b0a2d70f47f1b437423f9e504aa

### 更新

- [T-2351] **P3・設計メモあり**: 直列性検査の SCC / 隣接の直列部を縮める。read-heavy 10 s 級 (1.2B edge 見込み) では `set`/tuple 隣接が 100 GiB 超になるため、source 範囲で bucket 化した set 再生 + CSR (dst 順は set 反復順を保存、root は初出順) と `U ≤ 2N` の txid 直接 index Tarjan (登録 pass なし) が候補 (`output/insights/2026-09-20/verifier-capacity/README.md` §7)。前判定「全辺が前向きなら非巡回」は rw 辺が逆向きになりうるため候補から外す。
  base: ad88780b2ca73153c723f838ac5d26c7de1de0684ad7d9def03fc71e97b7b5a5

### 新規

- {{T:read-heavy-10s-input-and-b8-scope}} **P2・ユーザー裁定待ち**: read-heavy 10 s の trace 取得 (bench を伴う) と B-8 の対象・種・長さ、校正規則 ≤ 600 s の扱い、既存 campaign lock の drift (旧成果物保存 + 新 closure で再走) を裁定する (`output/insights/2026-09-20/verifier-capacity/README.md` §7)。
