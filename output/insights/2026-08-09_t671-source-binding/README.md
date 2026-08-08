# [T-671] 汎用 certified producer の source binding + t530 件 6 — 設計択一を裁定へ返した (2026-08-09)

wave = `dev-wave-t671-source-binding` / branch = `worktree-dev-wave-t671-source-binding` /
起点 main = `ee2da0bf`。親の裁定要約は worklog の該当エントリ。

## 射程 (これを越える引用を禁じる)

本 wave は **実装差分ゼロの設計 wave** である。land したのは裁定パッケージと逐語だけで、
**source binding も campaign identity の変更も 1 行も実装していない。**

- したがって「[T-671] が解決した」「t530 件 6 が閉じた」と書いてはならない。決まったのは
  **択一の整理と、その前提事実の実測**だけである。
- **本番コードの編集はユーザー指示により禁止されていた。** テストも追加していない。
- R1〜R8 のどれを実装するにも、**発火計測が先に要る** (`DW-G04`)。現在の production artifact では
  提案されたどの gate も正に発火させられない — 既存 30 campaign は contract hash も
  `build_admission` も持たない。
- **raw reader / freeze / offline report の迂回は t530 件 2、S8b private lock は t530 件 3** の所有。
  本パッケージを全部実装しても「proof chain が全経路で完結した」とは名乗れない。
- `docs/dev-wave/**` へ規範文を足す実装は **[T-664] の予算捻出が前提** (aggregate 残り 1 byte)。

## 成果物

- `package.md` — 裁定パッケージ (R1〜R8 + 実測 19 件 + 却下案 6 件)。**ユーザーが読む正本。**
- `verbatim/s1-brief.md` — 段 1 brief (provisional 裁定 P1〜P5。**P1 と P2 は後に親が撤回した**)
- `verbatim/s1-explore-a.md` — 段 1 実測 A (source binding 非対称、file:line)
- `verbatim/s1-explore-b.md` — 段 1 実測 B (campaign id 分裂の機序、場合分け)
- `verbatim/s2-plan.md` — 段 2 codex プラン (sol / max / read-only、rc=0)
- `verbatim/s3-lensA.md` — 段 3 レンズ A (sol / max、NO-GO / must-fix 11・nit 1)
- `verbatim/s3-lensB.md` — 段 3 レンズ B (luna / max、NO-GO / must-fix 7・nit 3)
- `verbatim/s4-adjudication.md` — 段 4 親裁定 (real/refuted、P1〜P5 の最終処置)

## 証拠の状態 (これを隠して引用してはならない)

- **実測はすべて本 wave で取った** (repo 実読、`tools/check_docs.py` 実走、byte 集計、
  既存テストの逐語確認)。package.md は実測 (A/B 節) と反実仮想・一般化 (C 節) を分離してある。
- **未観測**: g2 は未活性化 (activation serial 1 のみ)。「dirty loader で certified 成果物が
  生成される」は将来経路であって観測事実ではない。ただし **同じ穴は現在の g1 でも成立している** —
  g2 活性化は発覚の契機であって発生条件ではない。
- **親が自分の誤りを 2 件訂正した**: (i) 段 1 brief P1 の `DW-G03` 解釈 (「独立 2 実装があるから
  族一般化してよい」は誤読。`DW-G03` は同型欠陥の 2 件再現を要求する)、(ii) 実測 B の
  「未完了 campaign」条件 (terminal な campaign でも再実行で新 root ができる)。
- **親の provisional 裁定 P2 は段 2 が反証し、親が撤回した** (`ever_active` 解決による旧世代 resume は
  履歴検証と新規計測許可の混同)。
