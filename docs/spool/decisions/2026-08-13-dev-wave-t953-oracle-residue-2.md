---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-13
wave: dev-wave-t953-oracle-residue
seq: 2
---

## {{D:oracle-contract-binds-implementation-and-scan-scope}}. oracle の contract ID は実装 bytes と走査範囲を束縛する

**決定:** SWO oracle の contract ID は、手動 version 定数と corpus データ hash だけでなく、
公理判定に関わる 4 関数の `inspect.getsource()` 本文と、走査範囲を決める意味論定数
(要素数・order 集合・corpus 集合) を digest 入力に含める。component hash は 1 本の
authoritative digest へ畳み、短縮タグは診断専用とする。

**理由:**
- 変更前は checker のコードを書き換えても identity が動かず、`corpus` 集合を半減させて
  検査範囲を縮めても contract ID が同じままだった。identity が実際の検査能力を表していない。
- 束縛は**列挙**であって閉包ではない。判定ロジックを列挙外の helper へ移せば identity は動かない。
  この残余は docstring に明記し、「閉じている」と読める命名を避ける。
- 消費側が contract ID を格納する欄には長さ上限があり、超過すると黙って空文字化される。
  component ごとに hash を並べる形では上限に収まらないため、1 本へ畳む形を採った。

**却下した選択肢:**
- AST allowlist で候補実装を構文的に制限する案 — 受理集合を狭めすぎ、上流で不採用が確定済み。
- component hash を receipt に並べて診断能力を担保する案 — receipt にその field が無く、
  「receipt に残るから診断能力は落ちない」という前提が成り立たなかった。

## {{D:oracle-finding-validator-rejects-producerless-kinds}}. 消費側の schema は producer が実在する形だけを受理する

**決定:** critic の oracle finding validator は、kind ごとの exact key 集合、kind ごとに閉じた
reason_code 集合、producer 正準形の corpus_id、observations 要素の schema で受理集合を定める。
**trusted producer が 1 つも存在しない kind と、必ず環境故障側へ倒れる reason_code は受理しない。**

**理由:**
- 「将来の互換のために受理しておく」枝は、発火しない恒真枝であると同時に、外部由来文字列を
  materials へ運ぶ経路になる (規律 6)。gate の入力は実成果物の field に実在してから設計する。
- 長さ検査だけでは不十分だった。任意文字列が正準形の検査を経ずに描画されていた。
- 消費側が producer の意味論定数を直書きすると、producer の世代更新で正当な finding が黙って
  anomaly 化する。producer が公開する定数を import し、両者の不一致が赤になる経路を作る。

**却下した選択肢:**
- 未知 kind を通して描画側で弾く案 — 判定不能を合格にしない規律に反する。
- 検証後に observations を射影から落とす案 — 現在描画していないだけで、落とすと将来の
  描画時に証拠が無い。保持したうえで schema で縛る。

## {{D:postflight-is-correlation-not-independent-diagnosis}}. 事後 control は相関であって独立診断ではない

**決定:** 候補 compile の失敗後に trusted control を再度 compile する事後検査は、
「候補 compile の後に control も落ちた」という**相関**として扱う。候補成果物は事後検査の前に
除去し、事後検査は専用の別一時 directory で走らせるが、filesystem quota・cgroup・host 状態は
共有のままであり、候補から独立した環境判定であるとは主張しない。
**除去に失敗しても事後検査は飛ばさない** — 事後検査が通れば本来の REJECT を返し、
除去失敗と事後検査失敗が併発したときだけ専用 detail code で証拠を残す。

**理由:**
- 除去失敗だけで事後検査を飛ばして UNAVAILABLE へ倒すと、環境が健全でも確定済みの
  candidate compile finding が hard REJECT にならず、有効な拒否を取りこぼす。
- 候補は compile に失敗した時点で**一度も実行されていない**ため、除去失敗を候補が作る経路は無い。
  したがって「候補が自分の REJECT を UNAVAILABLE へ変える」攻撃面の緩和にはあたらない。
- 保証範囲を広く書くと、後続の設計がそれを前提にする。docstring は狭く正直に書く。

**却下した選択肢:**
- 事後検査を候補から完全に隔離する案 (別 cgroup / 別 quota) — 本 gate の指示範囲を超え、
  相関以上を主張するための機構を新設することになる。
