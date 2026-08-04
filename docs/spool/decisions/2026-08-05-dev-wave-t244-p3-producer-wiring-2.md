---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-05
wave: dev-wave-t244-p3-producer-wiring
seq: 2
---

## {{D:p3-producer-wiring-blocked}}. P3 producer 結線は実装を止める — prototype が production で起動できないことを実測し、予算束縛・commit-reveal・発火 gate の 3 つが同時に成立しないと確定した

**背景:** D159 決定 (4) と U-G の裁定は「P3 の充足は producer 結線と P7 まで含めて数える」と定め、
prototype 単体を P3 充足と記録しないことを確定した。本 wave はその producer 結線の再起票である。
段 1 前提実測・段 2 プラン (read-only codex)・段 3 敵対レンズ 2 本の 4 情報源が独立に
「現在の前提では実装できない」へ収束した。

**決定 (1): 本 wave は実装しない。** 実装差分が無いため変異 matrix と実装後の受入全走は対象外である。
残す成果物は設計メモ・敵対レビュー 2 本・段 1 実測・本裁定と裁定パッケージに限る。
拒否専用 adapter や fixture 限定 leaf を「producer 結線」として land しない — これは D147 が
却下した「未結線のまま leaf だけ land して実装済みと記録する」の再演になる。

**決定 (2): prototype は production では起動できないと記録する (実測)。** runtime store の genesis は
private test seam の `create=True` 1 点だけで、公開 API 3 本はいずれも `create=False` で入り、
create が偽なら `O_CREAT` を付けない。production 経路で公開 API を呼ぶと
`cannot open authority lock` で停止する (親が実行して確認、runtime dir は作られない)。
したがって「結線」は leaf への production bootstrap 追加を必然的に含み、
**誰が・いつ・どの authority 世代で genesis するかという未裁定の設計判断を伴う。**

**決定 (3): 結線を阻む 3 条件を名指しで固定する。** (a) **予算束縛** — ledger が iteration/query を
数えるのは batch commit 時だけで、候補生成後に commit する順序では commit 前に停止して
新しい run root で再実行すれば無課金で候補を引き直せる。予算束縛は P3 の目的そのものであり、
成立しない結線は名乗りだけになる。(b) **commit-reveal** — authoritative な admission は
workload 実行後であり seal がそれに先行する。さらに preview の可否が auditor の skip と実呼出しを
分岐させ、実呼出しは raw file を即時 fsync する。seal 前に最低 1 bit が漏れる。
(c) **発火 gate** — authority registry が空で bootstrap も無いため実装できるのは拒否側だけであり、
DW-G04 はこの場合を設計メモに限定する。「空 authority を正しく拒否した」は fail-closed の証拠で
あって、候補を受理し予算を消費し seal するという条件節の発火証拠ではない。

**決定 (4): observed cell の再導出不能を未解決として固定する。** cell key の 4 digest のうち
axis semantics と verifier policy は preimage 規則が repo に存在しない。manifest 13 field で
機械導出できるのは workload のみ、5 field は live campaign に source が無い。preimage を定めることは
origin 識別を恒久的に固定する行為であり、D121 P10 (origin authority のユーザー裁定) の射程に入る。
本 D は preimage を定めない。

**決定 (5): 結線先の候補はどちらも現状では不適格だと記録する。** 8c 自律 trial の
production driver が回せる workload は pilot の ycsb-a/b/c だけで、正式系列の holdout
(H1/H2) が要求する workload を回せない。E 段 loop は proposal file が auditor verdict と
diff digest を必須にするため、複数候補を評価前に用意できない。
親が段 1 で立てた「E 段なら評価前に batch を作れる」という代案は、この理由で**撤回した**。

**理由:** 3 条件のいずれも、caller 側の小さな opt-in では閉じない。(a) は候補生成前に予算を
確定する reservation event = FSM の受理集合変更を要し、(b) は artifact topology の非干渉化を要し、
(c) は authority の実体化 = ユーザー裁定を要する。scope 内で閉じられるものが 1 つも無い以上、
部分実装は「結線した」という記録だけを増やして実効をゼロのまま残す。

**却下した選択肢:**
- (a) 拒否側だけの opt-in adapter を land する — 現 runtime は未作成のため、unknown origin より
  先に lock 不在で止まる。producer admission の発火証拠にならず、DW-G04 にも反する。
- (b) 受理集合を黙って緩めて複数候補を通す — completeness の attempt/retry 固定と
  journal-report 全単射を壊す。D96 手続 (新しい設計判断の記録 + 境界テストの同一変更単位更新) を
  踏まずに受理集合を変えることになる。
- (c) 生死実験を飛ばして generic producer API・journal・error taxonomy を先に固める —
  DW-G01 に反し、生きた 1 例が無いまま抽象を固めることになる。
- (d) authority entry を実在 campaign から composeして登録する — D159 が禁じた捏造登録であり、
  予算値は P10 の未裁定事項である。

**研究状態への影響:** なし。実装差分ゼロ・authority 空・runtime 未作成のため、certified 選択・
材料レポート・試行台帳・proof chain の現在値と受理集合はいずれも不変である。
`MAX_APPROVED_GENERATIONS = 1` と cap-lift FAIL も不変で、**P3 は依然 FAIL** である。
