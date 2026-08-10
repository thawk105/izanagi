# [T-673] 残余 (3) — 本番側 guard D の検出力とコストを本番編集禁止下で測る wave

wave branch: `worktree-dev-wave-t673-d-guard-measurement`
計測 base: `44e35c8b` / probe tree (**land 対象外・repo 外の clone 内にのみ存在**):
C0 `101e8f2b` (driver のみ) / C1 `85afbbe8` (+D₁) / C2 `a7f5be04` (+D₂) / cost `61a60099`

## 何をして、何をしなかったか

**していない。** 本番コードと既存テストを 1 byte も変えていない。D も driver も land していない。
**probe commit を izanagi の object DB に作っていない** — D の実体は repo 外の `--shared` clone の中だけに
存在する。この wave が land するのは **docs fragment と本 insights だけ**である。

**した。** ユーザー裁定 §56「(3) D 計測可・本番編集禁止恒久」に従い、走査完全性 guard D の
**検出力・コスト・偽陽性・残穴**を実測し、裁定パッケージ (`RULING-PACKAGE.md`) を作った。

## この wave が確定させた事実

- **D は既存テストの検出力を 1 マスも増やさない。** 直接 slice 14 種に対する frontier は
  D の有無で完全に同一 (G は N≤3、P は本 arm の 2 node では全域 SURVIVED)。
  fixture の env 数を超える N では `[:N]` が恒等になるため、guard は発火しようがない。
- **切り詰めが実際に起きる入力では、D は 43 セルで誤受理を拒否へ変えた** (env 65 個の合成 chain、
  公開 API と loader の 2 層)。両層変異 (guard を `if False` へ) で赤が C0 と同じ集合へ戻ることを
  確認したので、この 43 セルは driver でなく **D の作用**である。
- **D は測定可能に遅い。** `validate_activation_records()` 1 call あたり中央値
  +949 ns (M=2) / +1101 ns (M=8) / +1564 ns (M=64)。相対 1.18 % / 0.75 % / 0.21 %。
  事前登録した順位判定 3 条件が 3 つの M すべてで成立した (先行 wave は単発観測で順位を付けられなかった)。
- **D は意味保存リファクタで偽陽性を出さない (0/5、C0 対照も 0/5)。**
  先行 wave の C1 (AST 構造検査) が 3/3 で誤検出したのと決定的に異なる。
- **D₂ (診断上書き型) は既存の pin 済み診断を壊す。** 全ファイル走で no-op 系 3 node と
  発行 tool 1 node を追加で赤にした。**D₁ (診断保存型) は壊さない。**
- **D は走査の完全性を保証しない。** 見ているのは loop の反復回数であり、counter 直後に
  `continue` を入れると件数は一致したまま述語を 1 度も評価せず素通しする。
- **D 自身は無保護である。** guard の削除・骨抜き 4 件は、既存 77 node + probe 17 node の
  どれも赤にしない (4/4 SURVIVED)。
- **未変異のとき D は何も変えない。** C0 / C1 / C2 の 3 tree で 94 node すべて緑。
- **発行 tool 層は測れない。** 実 catalog が env 2 個に固定されており、N≥2 の切り詰めが恒等になる
  ため、今日の入力では露出しない (`UNMEASURED`、[T-737] へ)。
- **変異は distinct 32 種を 10 arm へ適用し、最終 ledger entry 93 件、事前登録との不一致 0。**

## 構成

- `RULING-PACKAGE.md` — 裁定パッケージ (本体)
- `ledgers-round2/` — 最終台帳のうち再走した 5 arm (f0 / f1 / f2 / v1 / ra)
- `ledgers-round1/` — 第 1 巡。うち `v0` `ga` `bl` `fp0` `fp1` は最終台帳、残りは erratum の証拠
- `specs/` — 変異 spec 10 本 (最終)
- `cost-result.json` — overhead 測定の生データ (block 単位まで保存)
- `verbatim/` — D₁/D₂ の本番差分、probe driver、コスト測定器、親測定の逐語
- `SHA256SUMS.txt` — 全ファイルの SHA-256

## 事前登録の erratum (2 件、いずれも親の導出誤り)

1. F arm で先行 wave の focal 4 node 用の期待値を使いながら runner にファイル全体を渡した。
2. D₁ の G guard が発火すると P loop 自体が走らないという先取り効果を見落とした。

どちらも規則をコードから導き直して再走し、最終台帳は全件一致した。第 1 巡の台帳は消していない。
