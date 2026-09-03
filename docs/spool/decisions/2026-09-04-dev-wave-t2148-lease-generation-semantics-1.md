---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-04
wave: dev-wave-t2148-lease-generation-semantics
seq: 1
---

## {{D:lease-generation-marker-and-no-second-discriminator}}. 非保持走行の世代は予約語 1 つで表し、取得の有無を表す第二の引数は置かない

**決定:** D1527 が求めた「排他権を取得しなかった走行を表す値」を、signed-v6 受領証の
`lease_generation` の値域に予約語 `"not-acquired"` を加える形で定める。判定は完全一致だけとし、
前後空白の除去・大文字小文字の畳み込み・部分一致・Unicode 正規化を行わない。
**取得の有無を別に申告する引数 (`lease_acquired` / `expected_lease_acquired`)、その組を検査する
helper、issuer CLI の専用 option と mutually-exclusive group は採らない。**

**理由:**
- 予約語と 64 桁小文字 16 進は構文的に交わらないので、値そのものが取得あり / 取得なしを運ぶ。
  既存の `payload["lease_generation"] == expected_lease_generation` の完全一致が、その 2 状態を
  既に区別する。第二の discriminator は同じ区別を 2 度目に行う関門であり、受理される受領証の集合も
  署名 bytes も変えない。
- 敵対検査が示したとおり、状態引数を足しても取得の有無は照合されない — 状態とその期待値の両方を
  同じ caller が渡すためである。したがって棄却によって失う保証は無い。D906 が却下欄で名指しした
  「署名だけを足して恒真になる」形を、引数を増やす方向で再生産しないことを選ぶ。
- 予約語は暗黙の既定値ではない。`lease_generation` は元から必須引数・必須 CLI option であり、
  非保持走行では呼び手が予約語を明示して渡す。D1499 が却下した「既定値を入れる」形には当たらない。
- 値は取得ありも取得なしも caller の自己申告である。この module は live な排他権を読まず取得の
  有無を検査しない。D1443 に従い、production の着地ツールがこの verifier を呼ばないため
  この関門が不可避でないことも同じ docstring へ書く。世代の導出方式は選ばない (D1528)。

**却下した選択肢:**
- **必須 `lease_acquired: bool` と verifier 側の `expected_lease_acquired` を足す** — 上記のとおり
  受理集合を変えず、取得の有無も照合しない。要求外の関門を 1 つ増やすだけになる。
- **64 桁の全ゼロ値を非保持の印にする** — sha256 の値域そのものに含まれ、将来の正規の取得値と
  衝突しうる。保持した走行の受領証と構文的に区別できない。
- **JSON `null` を使う** — 欠落・不明・非保持を混同しやすく、既定値への縮退を誘発する。
- **issuer CLI に専用 option を足す** — 既存の必須 option へ予約語を明示すれば足り、
  別 spelling と conflict 検査を増やすだけになる。
