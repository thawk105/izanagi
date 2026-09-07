単独段 dispatch: stage=consult; lane=B; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/s1-brief.md

## レンズ B: 整合と実効性 — 切った wave は成果物として成立するか

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/refs/parent-verification.md` — **親が段 3 の前に自分で走らせた検算 (V1〜V3)。plan の [実測] と食い違う箇所はこちらが正本**
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/refs/s2-plan.md` — 検査対象の段 2 プラン
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/s1-brief.md` — **親 brief。これ自身も検査対象である**
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/refs/c1a-s4-adjudication.md` — 契約 v2 の正本 (3 節)、境界 (5 節)、裁定パッケージ (6 節)
5. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/refs/c1a-README.md` — 継承元 C1a の成果と閉じていない窓
6. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/refs/decisions-verbatim.md` — 確定裁定の逐語 (D1113 / D1114 / D1341 / D1522 / D1533)

作業 repository は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a`、HEAD は `9c1951179` である。コードはすべてこの worktree の中を読む。

## 共通の制約

- 読取専用である。実装しない。書込可能な tmp が無いので pytest 緑を要求せず、静的検査と python の直接評価だけで論じる。テストの実測は親が行う。子の非実走を緑と数えない。
- **plan を守らせるのではなく攻撃する。** 親 brief の (P1)〜(P5) と、親検算 V1〜V3 の一般化も攻撃対象である。
- 主張には **[実測] / [推測]** を付ける。行番号・件数・key 集合・値域は必ず [実測] にする。plan の行番号を転記せず自分で現物に当たる。
- 所見は次の形式で書く。`| ID | 所見 | real / refuted の自己判定 | 根拠 (file:line または実行結果) | 成果物影響 (この所見を無視すると何が壊れるか) | 提案する処置 |`
- **成果物影響を書けない所見を real にしない。**
- 出力へ結合文字 U+0300〜U+036F を使わない。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力の最後に `## 総括` 節を置き、real 所見の件数、最も重い 3 件、plan を採用してよいか (yes / 条件付き / no) を 12 行以内で書け。

## このレンズの依頼

plan は規模超過を理由に C1b を「leaf + launcher」の 2 子に切り、core / profile / adapter を C1c へ送ると提案している。この分割と、plan が挙げた先行裁定 4 件が **wave の成果物として成立するか**を検査せよ。

次を必ず含めること。

1. **切った wave の成果物影響 (DW-G05)。** plan の分割では v2 terminal が開かないまま終わる。このとき C1b が残すのは「呼び手 0 件の leaf module と、その leaf を呼ぶが早期 gate で止まる launcher」である。**この成果物が実際に効く層はどこか**を列挙し、(a) 検証されない dead code を積むだけではないか (b) C1c が来る前に別 session が main へ何かを land させたとき壊れないか (c) 規律 5 (段階導入・盛らない) に照らして正当かを判定せよ。**より小さい成立する分割 (例: leaf だけ、あるいは leaf + profile の E2 だけ) が存在しないか**を具体的に検討せよ。
2. **規模見積りの検算。** plan は production +1,228〜1,717 / test +1,775〜2,465 と見積もり、C1a 実績の 3.7〜5.1 倍とした。この見積りの根拠を現物に当てて検証せよ。特に adapter +430〜620 / adapter test +700〜950 が本当に必要かを、**契約 3 節が要求する最小**まで削れないかで検査せよ。plan が「必要」と書いた項目のうち、契約が要求していない自発的拡張 (claim v4 の新設、`_AttemptState` への mode 追加、8 call surface 全部への capability 伝播) がどれかを分離せよ。
3. **先行裁定 4 件の必要性と、親の代替案。** plan は「4 件を裁定するまで author を開始できない」と書いた。1 件ずつ、**本当に人間 (またはこの wave の親) の裁定が要るのか、それとも現物から一意に決まるのか**を判定せよ。決まるなら決まる値を書け。特に:
   - 第 24 field: 契約表の 23 に足りない 1 つは何であるべきか。契約 3 節の cross-field 不変条件・E1・crash 権威の記述から**必要とされているのに表に無い field** を探せ (候補を挙げて根拠を示す。単なる計数誤りだという結論も可)。
   - issuer の 3 引数不足: plan の 2 案 (4 引数化 / hidden binding API) 以外に、**contract を変えずに済む第 3 の案**が無いかを探せ。
4. **変異候補 18 件の帰属。** 各候補について (a) その変異が他の gate (型検査、既存 test、schema exact key 検査) に先に殺されないか (b) 期待 node が変異と 1 対 1 に対応するか (c) plan の分割で C1b に残らない file への変異が混ざっていないか を検査せよ。**帰属不成立の候補を名指し**し、置き換え候補を提案せよ。DW-M01 の事前登録に耐える形かを判定せよ。
5. **親 brief の (P3) と (P5) を攻撃せよ。** (P3)「production 到達性 0 だから値域を実測できない」は、**到達性を作らない言い訳として使われていないか**。plan が「採用しない述語」として挙げた 7 件のうち、実は現物から静的に決まるので採用できるものが無いかを検査せよ。(P5) について、plan は `FROZEN_MANIFEST` 追加 0 件としつつ official perf closure への登録が要ると書いた。**leaf が `use_perf_from_receipt()` を呼ばない設計にすれば回避できるか**、回避すべきかを判定せよ。
6. **scope 外の層を実装したふりにしていないか。** C2 (campaign 配線、producer capture、RESULT_SCHEMA v5) と D2 (consumer 3 面) の境界が、plan の設計で本当に固定されているか (symbol・引数・戻り型が一意に決まるか) を検査せよ。決まっていない箇所は**裁定パッケージ候補**として返せ。
