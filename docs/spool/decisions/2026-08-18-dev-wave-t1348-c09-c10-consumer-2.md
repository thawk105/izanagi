---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-18
wave: dev-wave-t1348-c09-c10-consumer
seq: 2
---

## {{D:cross-binding-receipt-leaves}}. cross-binding 受領証は leaf を保存し aggregate を再計算する

**決定:** 正式 acceptance 受領証を v3 へ上げ、trial ごとの cross-binding 受領証 digest (leaf) を
受領証本体へ保存する。top-level の `cross_binding_receipt_sha256` は検証時に leaf から
再計算して照合する。再計算しない v3 検証は採用しない。v1 / v2 の受領証は
schema 別の exact key 集合で従来どおり parse できる状態を保つ。

**理由:**
- aggregate を 1 値だけ保存する形では、任意の正しい形式の SHA-256 へ差し替えても
  受領証検証が通る。「参照された byte 列を束縛した」という受領証の主張を独立に検証できない。
- leaf を持てば、受領証だけを見て aggregate を再導出でき、
  改竄は受領証の内部整合性の破れとして現れる。
- 段 3 と段 6 の敵対子が独立に同じ blocker を出した。片方だけの所見ではない。

**却下した選択肢:**
- v2 の exact key 集合を黙って拡張する — 凍結済みの v1 / v2 受領証が
  unknown key または missing key で拒否され、既存の受理参照が失われる。
- aggregate を受領証の外へ出す — 既存 parser と受領証検証の信頼境界の外になり、
  受領証だけでは束縛を確かめられない。
- leaf を持たず aggregate だけ必須にする — schema の外観だけが増え、検証力が増えない。

## {{D:no-build-conditional-reason}}. 層3 chain の欠落は条件付き non-certifying reason で表す

**決定:** 正式 registry 権威は、build report に対して層3 chain を実走し、
`do_build=False` の report には `no-build`、層3 レポートを持たない build cell を含む report には
`layer3-chain-absent` を non-certifying reason として積む。どちらも受領証の
mandatory reason 集合には入れず、report の実値から導く条件付き reason とする。
build report の chain 検証そのものは reason ではなく fail-closed の例外で止める。

**理由:**
- acceptance は構造的に `certifying: False` であり、「certify を止める」を新たな停止として
  表現する余地が無い。内容由来の reason code を積むのが実装可能な唯一の意味である。
- reason code だけでは恒真になりうる。build report に対する chain の**実走**を
  fail-closed の本体に置くことで、reason は補助的な記録に留まる。
- mandatory 集合へ入れると build mode の非 certify 受領証まで一律に拒否され、
  入れないと欠落を parser が検出できない。条件付き reason はこの二者択一を避ける。

**却下した選択肢:**
- no-build report の受理そのものを拒否する — 既存の acceptance 経路が総崩れになり、
  本条件が要求していない受理集合の縮小を持ち込む。
- `no-build` を mandatory non-certifying reason に加える — build mode の受領証まで巻き込む。
