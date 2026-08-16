---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t1157-fetchcontent-reuse
seq: 2
---

## 新規

### {{F:false-positive-from-unrelated-field-in-verdict}}. 判定式に、狙った事象と無関係に動く field を入れて偽陽性を作った [テスト代表性]

- 事象: 2026-08-16 の [T-1157] wave で、共有 FetchContent base の再利用を測る probe が
  `REFETCHED` (再 fetch) の判定式に ExternalProject の `patch` step stamp を含めていた。
  第 2 走 (`Request 912886.nqsv`) の実測では、production の 3 transition のうち 2 つで
  この stamp が「変化」した。単独性検査が先に `INCONCLUSIVE` で止めていなければ、
  **probe は `REFETCHED` を返し、床値本走へ根拠のない NO-GO を出していた。**
- 根本原因: stamp の中身を見ずに「stamp が変われば再取得」と対応づけた。実測すると
  変化していたのは `st_mtime_ns` だけで、`st_ino` も sha256 も (空 file のまま) 同一だった。
  `PATCH_COMMAND` を持たない no-op step の stamp は populate のたびに touch されるだけで、
  source の再取得とも置換とも関係がない。**「その field は、狙った事象が起きていなくても
  動くか」を確かめていなかった。**
- 恒久対応: 判定 field を `exists` / `st_ino` / `sha256` に限定し、`st_mtime_ns` は
  診断系列 (`diagnostic_signature`) へ移した。ただし `FETCH_HEAD` の `st_mtime_ns` は判定に残す
  — up-to-date な `git fetch` は内容も refs も変えずに `FETCH_HEAD` を書き直すため、
  そこだけは mtime が唯一の信号である (同 wave の直接 fetch 正例で実測)。
  **緩めていないことの担保は、変更後も置換・fetch の positive control 2 本が発火すること**を
  判定順序に残した点にある (逐語 =
  `output/insights/2026-08-16_t1157-fetchcontent-reuse/README.md` §4)。
- 再発検知: 判定式へ field を入れるときは、その field が「狙った事象を起こさない操作」で
  動かないことを確かめる。動くなら診断へ回す。偽陰性 (恒真ゲート) だけでなく
  **偽陽性が実作業を止める側の害**も同じ台帳で数える。

## 再発

### F28

- **再発: 2026-08-16** — [T-1157] wave で、対象が変異ではなく **probe の positive control** で
  同型が出た。「再 fetch を検出できる」ことを示すはずの正例が、pin された完全 SHA の object が
  ローカルに在るため CMake update script の `fetch_required NO` 分岐に食われ、
  **fetch せず checkout するだけ**で発火していた。probe はその HEAD 変化で
  `refetch_detection_proven=true` を立てられたので、**検出力ゼロのまま
  「再 fetch しない」を主張できる**状態だった。F28 の恒久対応 (i)「その位置より手前に
  同じ入力を落とす検査が無いこと」を、変異だけでなく positive control にも適用する必要がある。
  段 6 の焦点再レビューが実走前に検出し、実 `git fetch` を起こす正例へ差し替えて閉じた。
