---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-t2423-floor-protocol-identity
seq: 1
---

## {{D:b4-floor-protocol-from-receipt-genome}}. 権威 floor の identity 要素 protocol は build receipt の canonical genome から導出し、凍結 spec へ宣言させない

**決定 (dev-wave 段 4 裁定、依頼の択一の外):** 権威 floor 成果物名の 5 要素 (D1641) のうち `protocol` は、
凍結 spec の各 artifact が指す build receipt (portable record、`s8b-binary-admission/v2`) の
`binding.genome_canonical` (`Genome.canonical()` の `protocol|flags` 形) から共有 helper
`protocol_from_floor_genome()` で取り出す。全 artifact で 1 値のときだけ identity に採り、canonical でない・
読めない・sha 不一致・混在・一部失敗はいずれも `missing=("protocol",)` として発行を拒否する (fail-closed 維持)。
凍結 spec の schema・driver・receipt schema・D1641 の 5 要素は変えない。

**理由:**
- 本 wave の起票文と依頼は「protocol は spec に無く、build receipt からも導出できない」を前提に
  (a) spec へ足す / (b) D1641 を 4 要素へ訂正 の択一を置いたが、前提が偽だった。receipt の
  `genome_canonical` は `genome_sha256`・`variant_id`・`binding_sha256`・materialization binding で
  binary に束縛されており、protocol を取り出す共有 helper も既に在った。issuer が失敗していたのは
  record の top-level に `protocol` key を探していたからである。
- (a) は測定された binary の事実から protocol を切り離し、人手宣言値で成果物名を発行できるようにする
  (規律 2 の向きに反し、D1374 の却下欄「検査していないことを検査したと読ませる」型)。加えて spec schema・
  spec sha・HMAC 順序 golden の不要な変更面を生む。
- (b) は D1641 の逐語を減らし、`between_run_floor` が silo / mocc を名前で分ける既存経路と矛盾し、
  別 protocol の 2 件目を create-only で発行不能にする。
- receipt 経路は変更面が issuer 1 file とその test だけで、D1696 (spec 側 validator を拡張しない) と
  D1373 (protocol は source / binary の事実へ束縛) の両方に整合する。

**却下した選択肢:**
- (a) 凍結 spec に top-level `protocol` を足し schema を v4 へ進める — 上記のとおり binary 束縛を失う。
- (b) D1641 を 4 要素へ訂正 — 情報を落とし別 protocol の床値と同名衝突する。
- protocol の許可リスト / CCBench source 束縛 gate を issuer に足す — D1696 の再訪条件 (人手の見落とし 1 件) が
  未成立。裁定パッケージ候補として残す。
- `Genome` の flag 名に `|` を含む値 (例 `mocc|A|B=1`) を issuer だけで拒否する — それは `Genome.canonical()` の
  正準形そのものであり、共有 helper と解釈が割れる。文法を締めるなら model 側で行う (裁定パッケージ候補)。
