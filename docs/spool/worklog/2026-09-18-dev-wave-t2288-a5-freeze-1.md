---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2288-a5-freeze
seq: 1
title: [T-2288] B-4 床値 spec 3 本の A-5 を D2120 項 4 の委任で確定して凍結した — 凍結 commit の 3 spec が実 checkout で `--validate-only` を 3 本とも通り、期待 spec 列は同じ commit の決定記録に置いた (docs + spec JSON、branch worktree-dev-wave-t2288-a5-freeze、変異 matrix = 実装面差分ゼロにつき免除)
---

## 本文

- ユーザー依頼は「[T-2288] (D2120 項 4、D1641 決定 1〜3 / D1638 の委任) B-4 床値 spec の A-5 を AI が確定して凍結 commit へ進める —
  1 spec あたり 2 窓の `not_before` / `not_after`、各窓の `campaign_id`、`seed_hex`、`artifact_relpath` ×2、`summary_relpath`、3 spec と
  集約出力の対応。着手直前の local main から fresh worktree を作る。順序と落ち方は binder precheck の insight「凍結 wave への注意点」に
  従い、捨て branch の 3 commit は置き方の実例として読む (land しない)。spec の path・命名は本 wave の決定として insight に明記。今回は
  凍結まで (床値実測・集約・採用裁定は後続)。規律 2 を緩めない。本題の凍結だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は
  scope 外」。
- **A-5 を確定し、3 spec (`floor-pair-spec/v3`、rr95 / rr50 / rr5) を 1 commit で凍結した。** 凍結 commit `0b4fbd7a67652d37bb41cd18386e1234268eafdc`
  (親 = `provenance.source_commit` = 起点 local main `d2ebef7a407dc6be61622ed596cf08b8b518f606`)。値と理由は {{D:b4-floor-a5-freeze}}
  (同じ commit に置いた fragment)、実走の記録と後続への申し送りは `output/insights/2026-09-18/t2288-a5-freeze/README.md`。
  置き場は `output/env/pegasus/floor-pair/t2288-f1/`、窓は w1 [2026-09-19T00:00:00Z, 2026-09-27T00:00:00Z) と
  w2 [2026-09-29T00:00:00Z, 2026-10-07T00:00:00Z) (UTC 半開、3 spec 共通、開始許容帯の差 48 h)、campaign_id は `t2288-f1-<wl>-c1` / `-c2`、
  seed は公開式 SHA-256 (`spec_relpath` と `source_commit` から)、出力 (窓 JSONL ×2・summary JSON) は spec と同じ directory に
  D1641 決定 3 の 5 成分を名前に含めて置く。集約は 3 組 (relpath, sha256) を期待 spec 列として D に記録し、summary から導出しない。
- **凍結 checkout で `--validate-only --expected-sha256` を 3 本実走し、3 本とも rc=0・stderr 空**で `floor-pair-plan/v2` (各 248 session・
  496 測定・窓ごと 124、§11.2 の名目と一致) を返した。`place` は rc=0 (`7cdf0dc3…` 701,760 bytes、policy 現行一致)。負対照 1 本
  (期待 sha 1 桁違い) は rc=1 `frozen spec sha256 不一致`。実装面 (driver・issuer・test) は 0 byte 変更。
- 段 2 plan は親 brief を 8 点訂正し全件採用: 窓判定は session 開始時刻で「任意 session 間 > 24 h」は過大 (48 h の隙間は余裕であって
  終了→開始の分離の保証ではない、人手確認は D1974 のまま)、HMAC は標本順・side 順・session 内測定順の 3 箇所を決める (「side 順序だけ」
  「有利な選択は無い」は誤り)、実行設定は較正由来でなく本 wave の運用選択、1 窓 ≈ 1.6 h は上限でない、spec 名にも campaign 成分、
  D2088 の「spec の非保証欄」は schema v3 に無いので D と insight に置く (記録先の訂正)、三軸走査器は仮置き語を見ない (別 grep)、
  plan bytes 不変は条件付き。段 3 レンズ A (正しさ境界) must-fix 4 / 情報 5、レンズ B (実装照合) must-fix 3 / 情報 5 / nit 1、
  must-fix は全件採用 (48 h と timeout 和を session 上限にしない、w1・w2・finalize の同一 HEAD 条件を申し送る、生成器と記録の同期、
  D2088 の訂正を明示)。nit 1 件 (生成器の create-only が atomic でない) は不採用 (repo 外の親の補助)。両レンズとも「授権は D2120 項 4 で
  十分、ユーザーへ返す事項なし」で一致。裁定の全文は insight `verbatim/s4-ruling.md`。
- 裁定 inbox: 段 4 直前まで local main は `d2ebef7a4` のまま (wave 開始後の更新なし)。
- 段 1 で判明した新事実 (後続への申し送り): (1) main の Pegasus 実行体登録簿に floor-pair 系 job body は無く、`run_window` の実測には
  job body を着地させる別 wave が先に要る (F660)。(2) finalize は両窓の header の `loaded_head` / `runtime_head` に finalize 時の HEAD との
  exact 一致を要求するので、各 spec の w1・w2・finalize は同じ実行 HEAD で走らせ、測定途中に成果物 commit で HEAD を進めない。
- 段 6 の敵対レビュー 2 本 (記録 3 点に対して): レビュー A (逐語整合) = must-fix 1 / nit 3 / 情報 3、レビュー B (実物照合) = must-fix 0
  (spec 3 hash・凍結 blob・親 OID・較正と receipt の sha256・seed・生成器出力 bytes・集約予測名・実装面差分 0 を独立実測で全件一致)。
  must-fix (検査結果の記録が予定形のまま) と nit 3 件 (directory の階層表現、既決値と運用選択の区分、非保証に module bytes) は親が
  本 fragment・D fragment・insight で是正した。所見の全文は insight `verbatim/s6-review-{a,b}.md`。
- 受入・検査 (本記録 commit 前、insight・fragment 2 本・D fragment の是正を含む作業ツリーで実走): `check_docs` rc=0、
  `spool_fold --dry-run --show-diff` rc=0 (仮採番 D2135・entry 1636、[T-2288] の更新は base `f5251c0e…` で適用)、三軸語走査
  `s8b_holdout_freeze search` rc=0 (27,705 file、holdout rr80 / rr20 とも conjunction hit 0、正対照 190 hit、所要約 20 分)、
  仮置き語 grep は spec 3 本 0 件。受入全走は本記録 commit を含む最終 tip に対して land 前に 1 回だけ投入し、child-green でなければ
  land しない (受領証は job dir)。
- 段 8 の自己改善: 候補 0 件 (踏んだ guard 拒否は複合 command・heredoc・python 本文中の語の既知型、docs の新規収容も F の再発追記も無い)。
- エージェント工数: codex 子 5 本を起動し 5 本とも受理 (段 2 plan 1 / 段 3 consult 2 / 段 6 review 2、いずれも read-only、`gpt-6-astra`、
  plan・consult は `reasoning=medium`、review は docs 権威由来)。実装子・fix 子は実装面が無いため立てていない。親の実走は `place` 1 本、
  `--validate-only` 正例 3 本、負対照 1 本、すべて login node。計算ノード job は受入全走の分だけ。

## 次の一手差分

### 更新

- [T-2288] **P1・A-5 を確定し 3 spec を凍結した。残るのは実測とその前提の job body**: 凍結 commit `0b4fbd7a6` の
  `output/env/pegasus/floor-pair/t2288-f1/` に spec 3 本 (rr95 / rr50 / rr5)、値と期待 spec 列は同 commit の D (`b4-floor-a5-freeze`)、
  実走記録は insight `2026-09-18/t2288-a5-freeze`。窓は w1 2026-09-19〜09-27・w2 2026-09-29〜10-07 (UTC 半開、各 62 標本)。
  **次は (a) `run_window` / `finalize` を計算ノードで起動する Pegasus job body を着地させる wave (main の登録簿に floor-pair 系は無い、
  F660 により実測とは別 wave)、(b) 実測 wave — 実行 HEAD を 1 つ決め、`place` を測定 checkout で行い、w1 (09-19T00Z 以降に session 開始)
  → w2 (09-29T00Z 以降) → finalize を同じ HEAD で走らせ、証拠確認 (24 h 分離・n = 62・欠測率) の後に集約発行と採用裁定 (D1641 決定 2)、
  §5 floor 欄の記入へ進む。** 窓を使えずに終わったら延長・差替えをせず新しい凍結を別 commit で行う。
  base: f5251c0ef26f3330d617e4b5d4dbfe5b4347be5c1f2a047e04aaf2265fa88bbb
