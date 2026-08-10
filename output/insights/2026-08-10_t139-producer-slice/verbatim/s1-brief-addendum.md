# 段 1 brief 追補 — 追加で実測した新事実 N3 / N4

親 brief `s1-brief.md` §4 の N1 / N2 に続く。段 2 のプラン起草中に親が独立に実測した。
段 3 のレンズはこれも攻撃対象に含める。段 4 で N1〜N4 を一括して裁定する。

## N3. R2 (a) の「第 2 の erratum」が起草されていない — core §7 の義務が未達のまま段階 2 が発効した

**裁定。** §47 (2026-08-08) は R2 = (a)「core §7 の当該文へ**第 2 の erratum** を当て、
義務を『事前固定 stress check』へ置換する」を承認している。

**実測。** その erratum blob は存在しない。`output/insights/` 配下の t139 系 erratum は
`2026-08-08_t139-addendum-a/erratum-core-s15.md` の 1 枚だけである。
承認済み追補 A の `a12` 自身が、この差を逐語で認めている:

> core は「weak null の型 I 誤りは事前 simulation で**較正する**」と書く。
> 本 field はその較正を**与えない** — cluster 間変動の観測が 1 点も無いためである。
> したがって本 field が core §7 の義務を満たしたと扱ってはならない。(…)
> **本 wave はこの差を解消していない。**

**なぜ問題か。** §51 は追補 A を承認して段階 2 を発効させたが、
承認された追補 A は「core §7 の義務は未達である」と明示している。
すなわち **core §7 の「較正する」という義務は、現時点で誰も満たしていない。**
「較正した」と扱えば、実際には保証していない性質を保証したことになる (絶対規律 3)。

**本 wave への影響。**

- approval manifest (R1) が列挙する**承認済み erratum の exact set は 1 要素** (`t139-core-s15-exactkey-v1`) になる。
  resolver の exact set 契約自体は 1 要素でも成立するので、実装は止まらない。
- ただし **pilot 投入可否の判定材料としては blocker 級**である。
  core §7 の義務が未達のまま pilot を投入すると、pilot から導く `J` と `q` の型 I 誤り制御が
  「較正済み」と称せない状態で本走へ入る。
- **本 wave では起草しない** — 第 2 erratum は統計設計 (cluster level 型 I 誤りの扱い) の文書であり、
  producer 実装の scope 外である。裁定パッケージへ返す。

## N4. `a13` の原子予約台帳が未実体化 — 実体化は本 wave の責務と追補 A が明記している

**裁定。** §47 は R3 = (a)「`a13` 移管 + **原子予約台帳**」を承認している。

**実測。** 台帳の実体は存在しない。`family_root` / `alpha 台帳` を key にした検索で、
`docs/` `orchestrator/` `tools/` に実装・データとも **0 件**である
(hit するのは archive worklog の裁定文 2 行だけ)。

追補 A `a13` は次を要求し、実体化を本 wave の責務と明記する。

> **予約は producer が選べない canonical な台帳で原子的に行う。** 受領証は
> 台帳の path・予約 entry の digest・予約 commit を必須記録し、validator は台帳を読み直して
> `(family_root, ordinal)` の**重複が無いこと**を確認する。(…)
> その台帳の実体化は producer 実装 wave の責務であり、本書はコードを追加しない。

`family_root` は `F = 88d68f9127b31df5aafc3d59607896626a1652e8`、本 study は `k = 1` を占める。
台帳が無い状態で複数 study が同じ根に `k = 1` を主張すると、
独立な 3 つの真の帰無で全体誤り率は `1 − (1 − 0.025)³ ≈ 0.0731 > 0.05` になる。

**本 wave への影響。** 台帳が無いと受領証の `a13` 予約証拠 (`ledger_path`, `family_root`,
`ordinal`, `reservation_entry_sha256`, `reservation_commit`) を書けず、
**schema-valid な受領証が end-to-end で 1 本出る正例 (§44 Q4 (a) の 5 番目) が成立しない。**
したがって **alpha 台帳の実体化は本 wave の scope に入る** (親の provisional 裁定 (P6))。

- **(P6)** alpha 台帳を本 wave の単位 A へ加える。create-only の原子予約、
  `(family_root, ordinal)` の一意性、失敗・中断した試行も番号を解放しない、
  producer が path を選べない (定数で持ち毎回読む) を満たす。
  予約 commit は canonical 台帳の commit であるため、N1 と同じ「land 後に確定する」循環を持つ。

## N1 の更新 — 循環は解ける (peer 通知を契機に親が local main を独立に読み直した)

**実測。** local main が `2169a06c` へ進み、**worklog エントリ 346** が §51 の裁定
(Q1〜Q5 全問 (a)、追補 A 一式を一括承認・段階 2 発効) を canonical 台帳へ記録した。
一次控えは rulings-inbox §51、記録は fold commit `2169a06c` である。

**ただし approval manifest そのものは依然として存在しない。**
エントリ 346 は散文の裁定記録であり、R1 (a) が要求する
「承認対象の追補 A と全 erratum の `(path, commit, sha256)`、適用順序、合成後 core の
`composed_sha256` を逐語で持つ manifest」ではない。

**循環の解き方 (親の provisional 裁定 (P7))。**
`approval_fold_commit` は **manifest 自身の commit ではなく、manifest が記載する値**である
(erratum §5「resolver はこの manifest から `approval_fold_commit` と blob identity を取得する」)。
したがって

- `approval_fold_commit` = **`2169a06c`** (§51 の承認を canonical 台帳へ fold した commit) と置く。
  これは既に実在し `measurement_head` の祖先にできる。
- 本 wave が起草する manifest は、その承認を**機械可読へ写した pin** であり、
  自分自身の commit を trust root にしない。

これで N1 の循環は解ける。**land 前でも実 repo の正例を構成できる** —
manifest blob が measurement checkout に存在し、`approval_fold_commit = 2169a06c` が
その祖先であればよい。(P3) の hermetic fixture は維持しつつ、実 repo 正例も
段 6 で 1 本測れる見込みが立った。

## N5. 承認済み 2 文書が直接矛盾する — 受領証 schema を確定できない (段 2 が発見、親が検算した)

**事実。**

- `record-items.md` §2 (d) は、`reason_code == "post_performance_failure"` に対し
  「marker の実在**または**性能 run の raw 痕跡の実在」を要求する。
- `addendum-a-reissue.md` `a04` の表は、「`a03` が不成立 (**preflight の観測窓**・待機末尾の観測窓を問わない)」を
  **性能測定の開始後の失敗へ写す**と定める。

preflight の最初の `a03` 観測で不成立になった attempt は、**marker も性能 run の raw 痕跡も持たない**。
`a04` はそれを `post_performance_failure` へ写すことを要求し、`record-items` はその row を拒否する。
両文書とも §51 で承認済みである。

**なぜ問題か。** R6 (a) は「受領証 schema は本 wave が発行し **digest 固定**」と定める。
矛盾を残したまま digest を固定すると、**正当な失敗 attempt を記録できない schema** が凍結される。
`pre_performance_infra_failure` へ写す回避は `a04` 違反、marker を先に作る回避は追補 A の順序違反であり、
どちらも親が採ってよい範囲ではない (受理集合が動く)。

**親の provisional 裁定 (P8)。** `post_performance_failure` の**第三の分岐**として
「`a03` failure evidence + 対応する `attempts[].environment_observations[]` の実在」を認める。
これは `record-items` の literal 条件の**追加**なので、schema digest を固定する前にユーザー裁定が要る。
段 4 で裁定パッケージへ回す。

## 影響のまとめ (段 4 で裁定する)

| # | 事実 | 本 wave の扱い (provisional) |
|---|---|---|
| N1 | approval manifest が未実体化、`approval_fold_commit` が循環 | 本 wave が manifest を起草し land で発効。実 repo 正例は land 後の判定材料 |
| N2 | 追補 A を名乗る blob が 2 つあり同一 `core_ref` を記す | manifest が blob digest で pin。旧版 `2026-08-08_t139-addendum-a/addendum-a.md` は非承認と明記 |
| N3 | R2 (a) の第 2 erratum が未起草。core §7 の義務が未達 | **本 wave では起草しない。**裁定パッケージへ返す。pilot 投入の blocker として報告 |
| N4 | `a13` の原子予約台帳が未実体化 | **本 wave の scope に加える** (P6)。無いと e2e 正例が成立しない |
| N5 | 承認済み 2 文書が直接矛盾 (`a04` の preflight 写像 vs `record-items` の `post_performance_failure` 条件) | **schema digest 固定の前に裁定が要る** (P8)。R6 が本 wave の責務なので blocker |
