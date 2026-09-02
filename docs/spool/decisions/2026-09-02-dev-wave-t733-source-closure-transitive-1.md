---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-02
wave: dev-wave-t733-source-closure-transitive
seq: 1
---

## {{D:closure-first-layer-includes-package-init}}. enforcement source closure の第 1 層は package 初期化まで含める

**決定:** enforcement source closure を推移閉包へ広げる段階実装では、第 1 層を
「現行 member が直接 import する module」だけでなく、**Python が対象 module より先に実行する
package 初期化 file** まで含めた集合とする。今回は exact 24 path から exact 62 path へ広げた
(既存 24 + 明示 import 先 36 + package 初期化 2)。

**理由:**
- 明示 import の集合だけを第 1 層と呼ぶと、`orchestrator/critic/__init__.py` と
  `orchestrator/qualification/__init__.py` が閉包の外に残る。どちらも再輸出を行う実コードであり、
  差し替えれば import 時の副作用・受理・参照先を変えられる。それでも epoch は動かない。
- 既存 24 path に `orchestrator/verifier/__init__.py` が入っている先例と整合する。
  package 初期化を除く扱いは、この先例と矛盾する。
- 段 3 の 2 レンズが**独立に同じ 2 file** を挙げた。親の測定は明示 import しか見ておらず、
  実行時に必ず走る経路を落としていた。

**却下した選択肢:**
- **明示 import の 36 path だけで第 1 層とする** — 上記 2 file が閉包の外に残り、
  「直接委譲の 1 段目まで収載した」という診断文字列が偽になる。
- **D1075 が名指しした 6 種だけに絞る** — `pipeline.py` が直接委譲する
  `runner` / `stability` / `holdout_observation`、`axis_trigger_gating` / `reflux_ir` /
  `trigger_gate_binding` が残り、裁定の理由部分 (正しさ防壁自身が束縛されていない穴) を塞げない。
- **first-party import の推移閉包 131 module を一度に収載する** — 実装は同じ literal 追加だが、
  受入の検査項目が大幅に増え、閉包 member の編集のたびに epoch が動く代償が大きい。
  D1075 は段階実装を明示的に許している。

## {{D:closure-scope-string-states-what-it-is-not}}. 閉包の診断文字列は「閉包ではないもの」を明記する

**決定:** `campaign_verifier_epoch` の `identity_scope` と `excluded_scope` は、収載した path 数
だけでなく、**推移閉包ではないこと**、未収載 module 数、非 import 委譲 (data/schema、生成物、
subprocess、外部 command/Git、toolchain、binary、動的 import) が対象外であること、
そして完全性を主張しないことを本文に書く。docstring はこの 2 定数を正本として参照するだけとし、
保証内容を言い直さない。

**理由:**
- D1075 は「保証の文言は閉包が閉じるまで広げない」と命じている。path 数だけを更新した文字列は、
  読み手に「委譲先を網羅した」と読ませる。
- docstring 側で保証内容を再掲すると 2 つ目の正本ができ、片方だけが更新されて drift する。
  実際、本 wave の初回実装は定数を正しく更新した一方で docstring 3 箇所が旧説明のまま残り、
  段 6 の敵対レビューがこれを検出した。
- 非 import の委譲経路は列挙しても網羅を証明できない。個別列挙を文字列へ焼くと、
  列挙漏れがそのまま偽の保証になる。例示にとどめ、一般形で除外する。

**却下した選択肢:**
- **path 数だけ更新する** — 実態より強い保証を主張する。
- **非 import 委譲を全件列挙して除外する** — 網羅を証明できず、漏れが偽の保証になる。
- **docstring にも保証内容を書く** — 正本が 2 つになり drift する。

## {{D:closure-order-pinned-by-known-answer}}. 閉包の順序は固定 known-answer で束縛する

**決定:** enforcement source closure の順序を検査するテストには、production tuple と
独立 literal の等値検査に加えて、**固定文字列として書いた known-answer** を置く。
具体的には合成 fixture に対する E1 の値と、tuple 順に連結した path 列の SHA-256 を pin する。

**理由:**
- 期待 E1 を test 側の literal から再導出するだけだと、production tuple と test literal を
  同時に並べ替える変異に検査が追随してしまい、同じ記録 map から異なる E1 を発行しても緑になる。
  epoch の preimage は tuple 順に path と digest を連結するため、順序は値に効く。
- 固定文字列はどちらの literal からも導出されないので、両方を同時に書き換えても落ちる。
- 変異走行で実測した。この pin を含む構成では、新規 path 2 本を入れ替える変異が
  131 件のテストで検出された。

**却下した選択肢:**
- **等値検査だけを置く** — 両側同時変異で無力化される。
- **working tree の hash を pin する** — 揮発値であり、無関係な編集で落ちる。
