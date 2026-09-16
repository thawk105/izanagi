---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2683-attestation-mismatch-diag
seq: 2
---

## {{D:t126-attestation-mismatch-sidecar}}. T126 attestation の不一致は fork した子が失敗時だけ診断 sidecar を 1 つ残し、受理判定・rc・台帳の形は変えない

**決定 (D2104 項 14・15 の実装形):**

1. `_attest` は不一致 (空比較を含む) で `AttestationMismatchError` (`QualificationDriverError` の
   subclass、message は従来の全文) を上げ、比較行の全行・expected / observed profile の sha256・
   projection schema を属性に持つ。比較の述語 (非空かつ全行 pass) と probe 例外の包み方は変えない。
2. fork した子の処理を module-level `_run_attestation_child` に置く。不一致時だけ accepted path の
   隣に `{stage}-{n}.mismatch.json` (schema `t126-qualification-attestation-mismatch/v1`、`status`
   `rejected`、stage / round_index、両 sha256、projection schema、比較行を無加工の全行、`failed_fields`)
   を既存の `create_json` (create-only) で 1 つ書き、rc=31 を返す。一致時は従来と同じ payload を
   同じ path へ書き、sidecar は書かない。診断の書込み失敗・create-only 衝突・probe 例外では
   sidecar を書かず rc=31 のまま (D474: 診断の障害が制御結果を汚染しない)。
3. 親は非ゼロ終了時、sidecar が実在すれば `AttestationError` の message に attempt 相対 path と
   failed field 名を足す。読取り不能は `failed_fields=unavailable`、例外は外へ出さず、表示以外に
   使わない。`run_series` の reject evidence の key 集合 (stage / type / message)、`verify()`、成功
   series の evidence manifest は非接触。
4. `execution_guard.attest_and_build_receipt` は変えない。同関数は 2026-07-19 から非 pass 行を JSON で
   例外 message に載せており、production 呼び手 4 本は `str(exc)` を伝播する。floor campaign は失敗時に
   出力 root を作らないことを test で固定しており、file の sidecar は開始前・副作用ゼロの契約と衝突する。

**理由:**
- 規律 3 は「なぜ壊れたか」の構造化を要求する。値は `compare_profiles` が既に返しており、driver が
  捨てていただけである。D2056 (較正 CLI は失敗時だけ attempt staging へ診断 sidecar を 1 つ残す) と
  同じ形にし、成功時の receipt を増やさない (D2104 項 15)。
- sidecar は診断であって checker authority ではない (D474)。受理判定は従来どおり子の rc と親の
  例外だけで決まり、sidecar の有無・内容は受理集合を動かさない。
- 子側処理を module-level に抽出したのは、fork を経由せずに実物 (parser・比較・hash・create-only
  writer・strict loader) を通す test を書くためである。production の closure が helper を呼ぶことは
  AST の配線 pin (子分岐・非ゼロ分岐の所属と keyword) と実 fork の test で固定する。

**射程 (この決定が保証しないこと):**
- `create_json` は fsync する。fsync の stall は子の `attestation_cap_s` timeout に入り、mismatch の
  文言は timeout の文言に置き換わる。子が SIGKILL されると create-only の staging file が残り、
  collector の「abandoned staging bytes」拒否で failure receipt が発行できない。**これは accepted payload
  の `create_json` に元からある窓と同じ型**で、mismatch 経路の露出が accepted 経路と同数になるだけである。
  外側 wrapper の timeout (rc=124) も保証外。D474 の「fsync しない」は launcher の監視ループ向けの
  規定であり、ここでは既存 writer との一貫性 (同じ capability・同じ create-only 契約) を優先した。
- 比較行と 2 つの sha256 だけでは、凍結 attestation profile 全体や照合時の policy 値を含む自己完結の
  再計算 (D2056 決定 5 相当) はできない。主張は「比較時の全行と判定値の保存」に限る。
- `run()` 全体を通す E2E test は attempt bootstrap 全体を要するため作っていない。配線の保証は AST pin と
  実 fork の helper test まで。
- 開始前・副作用ゼロで拒否する execution_guard 経路の比較行は例外 message (stdout / stderr) にしか残らない。

**却下した選択肢:**
- **execution_guard の例外に構造化属性を足す** — 読む consumer が無く、恒真な追加になる。
- **非 fsync の診断 writer を新設する** — 新しい機構であり局所修正を超える。実害の観測がない。
- **`run_series` の reject evidence に key を足す** — 台帳の形が変わる。message に path を含めれば足りる。
- **sidecar に非 pass 行だけを載せる** — 通った前提が残らず、規律 3 の「全体像」に欠ける。
- **空比較では sidecar を書かない** — probe 例外の「sidecar なし」と区別できなくなる。
