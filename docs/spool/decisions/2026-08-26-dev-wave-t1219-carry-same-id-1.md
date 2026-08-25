---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-26
wave: dev-wave-t1219-carry-same-id
seq: 1
---

## {{D:carry-mismatch-ledger-key}}. 既知違反台帳の key は行の digest 対にし、座標を使わない

**決定:** D837 が認めた歴史的 carry ID 不一致の既知違反台帳は、
外側 key を carry を書いている entry の H2 raw 行の sha256、
内側 key を carry 論理行 (list marker を含む raw slice) の sha256 とする。
file path・行番号・entry 番号を同一性の key に使わない。
`KNOWN_PLACEHOLDER_DEBTS` と同型である。

**理由:**
- worklog の entry は定期的に archive へ移り、file 名も行番号も変わる。
  座標を key にすると通常のローテーションで台帳が腐る。H2 と項目の bytes は移動しても不変である。
- entry 番号と task ID と参照先番号の三つ組だけでは、同じ座標に別内容を置く差し替えを
  既知違反として認証してしまう。これは F58 (同じ ID で内容がすり替わる) と同型の穴である。
- list marker を含まない論理項目の digest では、`- ` を `1. ` へ書き換えるだけで
  同じ digest になり、別の行が既知として通る。

**却下した選択肢:**
- (source entry 番号, task ID, 参照先 entry 番号) の三つ組 — 座標の再利用と内容差し替えを許す。
- file path と行番号を含める — 最初のローテーションで腐る。

## {{D:carry-population-completeness}}. 母集合の完全性は件数の下限でなく構造の一致で担保する

**決定:** carry 検査の母集合が縮退していないことは、
(1) carry 風 candidate 数と厳密 parse 成功数の一致、
(2) 全域 entry universe と次の一手索引の key 集合の一致、
の 2 つで担保する。実測値に固定した下限は**粗い補助**として併置するが、
完全性の保証とはみなさない。

**理由:**
- 実測値に固定した下限は、単調増加する量に対して時間とともに腐る。
  母数が C 件増えた後なら C 件失われても下限を上回るため、部分消失を黙認する。
- (1) は parser の退行を即座に赤にする。carry を名乗る項目が厳密文法に読めなければ、
  件数が変わらなくても赤になる。コーパスが増えても腐らない。
- (2) は索引構築の取りこぼしを赤にする。これも導出値どうしの一致なので腐らない。
- 下限は「母集合が丸ごと消える」型だけを捉える。(1) は candidate も parsed も 0 なら
  一致してしまうため、下限と対で持つ必要がある。

**却下した選択肢:**
- 下限だけを母数 gate にする — 上記のとおり最初の追加から検出力が落ちる。
- 実測値を exact pin にする — 正常な carry 追加のたびに checker 本体の更新が要る。
- 凍結 entry ごとに期待件数を固定し fold と原子的に ratchet する — 実効性は高いが
  `tools/spool_fold.py` 側の変更が要り、本 wave の編集面 2 file を超える。裁定へ返す。
