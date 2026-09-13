# [T-575] silo 昇格を実行する consumer の同定 (dev-wave 2026-09-14)

`authority: none` / `default_effect: no-state-change` — 本書は凍結スナップショットであり、
可変状態の正本 (worklog 末尾・現行 phase doc) ではない。判定の正本は decisions の該当 D。

基準 commit: `75bea8e5f` (branch `worktree-dev-wave-t575-silo-promotion-consumer`)。

## 何を確かめたか

2026-08-06 の T-529 (契約世代の活性化権限) が、活性化 receipt を入れるべき入口を
「floor / oracle / P3 / 適格性 / selector / silo 昇格」の 6 つと列挙し、silo 昇格の実装先として
`orchestrator/campaign/silo_ladder_rung1.py` を名指しした。同 wave の段 3 で 2 つのレンズが独立に
「そのファイルは ability probe であって昇格入口ではない」と指摘し、裁定は
「真の promotion consumer が同定されるまで『silo 昇格入口は未実装』とする。ability probe を結線して
『昇格入口を守った』と報告してはならない」となった。本 wave はその「真の consumer」を探した。

## 結論

**適格性への昇格を行う consumer は、確認した静的参照閉包に存在しない。**
証拠を検査・発行する consumer と、Python 以前に書く shell/PBS writer は実在する。両者は別物である。

無限定の不存在保証はしない。確認したのは、既存 ledger・artifact schema・識別子・公開 helper・CLI・
登録表から到達する閉包である。任意の別名や汎用プログラムによる読取りまでは証明していない。

## 決め手になった実測 (親が独立に検算した 4 点)

| # | 実測 | 意味 |
|---|---|---|
| 1 | `orchestrator/campaign/silo_ladder_rung1.py:4960-4964` が `classification` を `ability_probe` / `research_goal_eligible=False` / `recovery_measurement_eligibility=False` のリテラルで固定 | producer に適格な成果物を出す枝が無い (**これが決め手**) |
| 2 | `orchestrator/campaign/silo_ladder_rung1.py:1273-1278` の validator が同値を要求 | 再読側も非適格値しか受理しない |
| 3 | ladder driver は `orchestrator/campaign/silo_ladder_rung1.py:2236-2237` で `use_class="raw-measurement"` を渡す (`_PROMOTION_USE_CLASSES` = `certified-selection` / `floor` / `oracle` / `paper`、`condition_meaning_gate.py:3478-3480`) | **用途の宣言であって機械的な昇格禁止ではない**。同 gate の受理判定 (`:4098-4103`) は raw と promotion で分岐しない |
| 4 | `orchestrator/campaign/silo_ladder_rung1_contract.py:517-518` が entry 数 1 を要求 | ledger は exact-one。新 rung を足すだけでは契約検査が違反を記録する |

## 既裁定との関係

- **D162 決定 (7)** は「昇格権威として読む consumer は 0 件」と述べているが、対象は
  `patches/ledger.json` の 3 適格性 field である。T-529 の 6 入口列挙では「適格性」と「silo 昇格」が
  別項目であり、同一命題ではない。本 wave は **ledger を経由しない経路**まで広げて確認した。
- **D196 / D215** は活性化権限の実装を保留している。本 wave は活性化権限を実装していない。
  D196 の保留理由をそのまま現在の blocker として再掲してはならない (historical resolver の配線充足は
  D215 が別途記録している)。

## 訂正したもの

1 件・2 箇所。`patches/README.md` の「新 rung は登録必須」に、現行契約が entry 数を 1 に固定している
という限定を足した。登録は必要条件であって、現行 ledger に新 rung を入れる入口が在るという意味ではない。

「silo 昇格入口」という語そのものの現行 (非凍結) 側の出現は 0 件だった。`docs/archive/**` と
`output/insights/**` には出現するが、そこでの用法は「未実装と名乗る」という裁定そのものなので
誤りではなく、凍結記録でもあるため訂正しない。

## 段 3 レンズが親を訂正した点

- 段 2 plan が `output/**` を丸ごと探索から落としたのは根拠不足だった。両レンズが output 配下の
  現用 README を読み直し、昇格誤記は 0 件と確認した。
- 段 2 plan の参照鎖表は Python 関数に偏っており、`tools/pegasus/silo_ladder_rung1.sh` と
  `tools/pegasus/submit_silo_ladder_rung1.sh` の実在 writer を挙げていなかった。
  昇格の反例にはならないが、入口被覆率の根拠としては不足していた。
- 「訂正対象 0 件」は過小だった (上記 1 件・2 箇所)。
- 親が段 2 の prompt で候補を列挙した際、`ability_probe` を「false から true へ変える」対象に
  混ぜたのは誤り。同 field は既に `true` である (`patches/ledger.json:13`)。

## 段 6 レビューが親を訂正した点 (must-fix 4 件)

いずれも親が書いた記録の側の誤りで、判定そのものは反転していない。

1. **「昇格用途の call site は oracle の 1 本だけ」は事実に反した。** 反例が現物にある
   (`orchestrator/campaign/p3_s4_loop.py:441` の `certified-selection`、
   `orchestrator/campaign/paper_story_a2_certification.py:784` の `paper` 他)。
   原因は親の検索出力が `head` で切れ、テスト除外の指定も効いていなかったこと。
   併せて「用途の宣言 = 機械的な昇格禁止」と読める書き方も直した
   (受理判定は raw と promotion で分岐しない)。
2. **見出しと完了文が、限定した判定を無限定の入口除外へ広げていた。** 対象を
   「適格性への昇格」に固定し、silo の書込み入口は調査対象に残すと明記した。
3. **探索範囲の説明が、記録された検索 argv と食い違っていた。** 実際の argv は
   `docs/archive/**` を除外し、一方のレンズは `output/insights/**` も除外している。
   「0 件」にも時点を付けた (本 wave の記録自体が以後この語を現行側へ持ち込むため)。
4. **活性化権限の発火条件について、測っていない現在値を断定していた。** 削除し、
   「本判定では測っていない」と書き換えた。

行番号の 1 行ずれ (nit 1 件) も同時に直した。

## 逐語

- `verbatim/s1-brief.md` — 段 1 親 brief
- `verbatim/s2-plan.md` — 段 2 plan (codex, read-only)
- `verbatim/s3-lensA.md` — 段 3 レンズ A (否定命題の閉包を破る)
- `verbatim/s3-lensB.md` — 段 3 レンズ B (訂正対象と成果物の設計を破る)
- `verbatim/s4-ruling.md` — 段 4 裁定
- `verbatim/s6-review.md` — 段 6 敵対レビュー (must-fix 4 / nit 1)
