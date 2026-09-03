---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-03
wave: dev-wave-t2141-rejection-durability
seq: 2
---

## {{D:rejection-ledger-scope}}. raw-record producer の棄却台帳は完全性を主張せず、守っていない範囲を成果物へ書く

**決定:** publication root 直下の固定名 leaf `raw-record-rejections.jsonl` に、
publication の検証に成功した後の producer rejection だけを canonical JSONL で追記する。
台帳に **hash chain を置かない。** 代わりに次を成果物へ明記する。

- 台帳の削除と末尾の完全切断は検出しない。
- absent な planned leaf の現在の理由は決定できない (未試行・deferred・記録前の棄却・記録失敗を
  区別できない)。
- publication の検証そのものが失敗した棄却は記録できない。
- 件数と率は「観測できた可読な台帳前置部分の event」という母集団から出た値である。

**理由:**

- chain head を外部の権威へ pin しない chain は、末尾の完全切断と file 削除を検出できない。
  守れない範囲を守れるかのように見せる恒真な保証になる。
- D1533 は成果物の不変性を「同じ path が残っている間の再作成防止」までとし、防いでいない範囲を
  成果物へ明記せよと定めている。改竄が正式な受理まで届く実経路が示されていない段階では、
  bytes 級 provenance は見送り側に入る。chain はまさにその見送り側である。
- D1529 は欠測を含む母集団から出た数値主張に、文書単位でなく主張と母集団の単位で但し書きを
  付けよと定めている。棄却件数と棄却率がこれに当たる。
- 非保証を単純に落とすと偽の完全性になる。棄却の後に deferred が起きた候補では、
  「absent かつ matching rejection あり」でも現在の absent 理由は棄却とは限らない。
  そこで非保証を 2 つに割り、記録された棄却の復元可能性だけを主張し、現在理由の不可知は残した。

**却下した選択肢:**

- **event に hash chain を置く** — head を pin しないため完全性を主張できず、
  D1533 の見送り側に当たる。
- **chain head を別権威へ pin する仕組みを新設する** — 成果物とは別の権威へ attempt を予約する
  機構が要る。実経路が示されていない。
- **既存の記録経路へ相乗りする** — issuer の固定 artifact は receipt が bytes を pin するため
  後追記で publication が失効する。admission record は事前 admission の read-only verifier で
  writer を持たない。analysis ledger の violation 事象は理由語彙が 5 値に閉じ producer の
  issue code を保持できず、file へ書かない。campaign WAL は publication root から常に導出できず、
  request 検証前の棄却では campaign root 自体が未確定。成功 attempt leaf への union は
  planned path conflict と leaf の IO error という最も重要な棄却理由ほど記録できない。
- **deferred も台帳へ書く** — deferred は再試行で解消する一時状態であり、記録しても現在の
  absent 理由を決定できない。器を増やさず、非保証を狭める側で閉じた。
- **非保証を全部落とす** — 記録前の棄却・記録失敗・未試行・deferred を区別できないままでは偽になる。

## {{D:rejection-ledger-failure-isolation}}. 棄却台帳の読み書きの失敗を、成功公開と assembly の可否へ漏らさない

**決定:** 棄却台帳の追記に失敗したら、元の rejection へ IO エラーの issue を 1 件足して
**rejection のまま返す。** 成功公開へ倒れる枝を作らない。台帳の読み取りに失敗したら、
その状態を独立した値として運び、**raw analysis assembly の成否へ昇格させない。**
`fsync` に失敗したときは同じ lock を保持したまま追記開始 offset へ切り戻し、
「数えられた event は fsync が成功している」を真に保つ。

**理由:**

- 記録は観測であって判定ではない。観測の失敗が判定を変えると、記録を増やすほど受理集合が
  動くことになる。絶対規律 2 が禁じる方向である。
- 台帳の検証失敗を assembly の失敗へ昇格させると、正常な成功 leaf が揃っていても材料レポートが
  利用不能になる。記録の失敗が後続の成果物の利用可否へ漏れる。
- `fsync` 前に可視化された event を耐久 event と同じ顔で数えると、crash で消えうる分を
  完全性の主張へ混ぜることになる。切り戻せば、数えた event はすべて耐久済みになる。

**却下した選択肢:**

- **追記失敗を無視して元の rejection をそのまま返す** — 記録の欠落が呼び手に見えない。
- **台帳が invalid なら assembly も拒否する** — 記録の失敗が成果物の利用可否へ漏れる。
- **`fsync` 失敗の event を残したまま IO エラーだけ返す** — 後続の loader が通常 event として
  数え、件数・率・未解決・非保証が耐久 event と同じ値になる。
