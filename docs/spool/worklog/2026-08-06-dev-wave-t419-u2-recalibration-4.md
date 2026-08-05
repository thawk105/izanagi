---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-06
wave: dev-wave-t419-u2-recalibration
seq: 4
title: [T-419] certify job を投入し、方式 α が計算ノードで帯内になることを実測した — 取得自体は pin 済み依存 source の消失で不能 (成果物 + docs、job 892177.nqsv、branch worktree-dev-wave-t419-u2-recalibration)
---

## 本文

- **certify job を 1 本投入し、11 秒で fail-closed した** (request `892177.nqsv`、bnode004、
  専有 1 ノード 48 CPU)。停止段は `gflags` で、理由は `gflags source path missing`。
  policy が pin する `/home/SFC/tanab/github/gflags` と `.../glog` が**環境から消えている**。
  親が実測で確認した (`/home/SFC/tanab/github/` 自体が存在しない)。
- **落ちる前に静的 attestation profile を取得しており、これが方式 α の計算ノード実測になった。**
  `method` は D181 の宣言値と一致し、**48 sample すべてが 2101.0 MHz、tolerance 2% の帯外 0 件**、
  governor は `performance`。一次資料 =
  `output/env/pegasus/calibration/job-staging/0:892177.nqsv/attestation-static.json`。
- **この実測の射程を限定する。** 言えるのは *この job・この host (bnode004)・この boot・
  この cpuset・この時刻の profile が全位置帯内だった* ことだけである。
  「α は計算ノードで常に帯内になる」という普遍命題ではない (D181 が別プロトコルの 9/9 を
  本番手続きの妥当性根拠に使わないと明記した限定と同じ理由)。
  ただし対照は明確で、**単読み時代の登録済み較正は bnode011 で CPU 40 が 3080.935 MHz、
  login node での α は 96 CPU 中 1 件が帯外**だった。同じ機序に対して専有ノードでは帯外が消えている。
- **U-2 の blocker が 1 つ増えた。** これまで判明していた [T-529] 活性化権限 (登録の前提) と
  [T-443]/[T-444] の source proof に加えて、**certify がそもそも起動できない**。
  pin 済み依存 source の所在は policy 側の設定であり、home を作業物で汚さない運用方針とも
  関わるため、親は独断で再作成せず裁定へ返す。
- 本 wave が入れた early gate はこの走行では発火していない (gflags 段が手前で落ちたため)。
  early gate の効果は変異 matrix と単体走行で裏取りしてある。
- certify の成果物 (submit receipt、job-staging 一式) は本 commit で取り込んだ。

## 次の一手差分

### 新規

- {{T:certify-pinned-dependency-sources-missing}} **P1・新規・ユーザー裁定待ち**:
  certification job が pin する gflags / glog の永続 source tree
  (`tools/pegasus/policy.json` の `gflags_source_path` / `glog_source_path` = `/home/SFC/tanab/github/` 配下) が
  存在せず、job は `gflags source path missing` で 11 秒で停止する。**新較正の取得は
  活性化権限や source proof 以前にこの一点で不能**である。
  `tools/pegasus/fetch_third_party.py` は FetchContent 3 source を cache へ取りに行く道具で、
  この 2 つの依存 source を再作成する経路は持たない (`verify-deps` は検証のみ)。
  択一は (a) pin 済み HEAD で同じ path へ再作成する、(b) source の所在を policy ごと
  home の外へ移す、(c) 依存 source も cache 経由の hydrate 対象へ広げる。
  (b)(c) は `tools/pegasus/` の変更を伴うため裁定が要る
