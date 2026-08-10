---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-11
wave: dev-wave-t675-address-edge-lint
seq: 1
---

## {{D:address-edge-structural-lint}}. 住所 (address edge) の構造 lint は非協調 drift の検出であって防壁ではない

**決定:** whole-file SHA-256 pin と構造 lint の責務を分ける。command 本文から他文書にしか無い
義務への**到達 edge (住所)** を機械が検査してよい対象は、その edge の**構造**だけとする。
呼称は **「住所 (address edge) の構造 lint」**とし、「意味検査の機械化」とは呼ばない。
効能は**非協調 drift の検出と、意図の diff への顕在化**に限り、**trust root は人間レビュー**である
(敵対監査はその判断材料を作る手順であって trust root ではない)。
「協調改変を防ぐ防壁」と書いてはならない。

**理由:**
- whole-file SHA-256 pin は期待値と異なる bytes だけを検知し、義務の意味を保証しない。安全義務の
  文を削って pin 3 箇所 (checker 定数・test 定数・test 内の逐語コピー) を同時再同期すれば検査は
  通る。実測で `check_docs` rc=0 / 違反なし、`test_check_docs.py` 357 passed / rc=0 だった。
- 期待値 (必須 edge の一覧) は同じ commit で削除できるので、edge 契約も trust root にならない。
  増えるのはレビュー時の顕著性だけである。sha256 の再同期は意味を持たない機械作業で byte 予算に
  追われた編集が自然に行うが、edge 契約から 1 行消す差分は自己記述的で「到達契約を外した」と読める。
- 「到達性は機械が守り、意味は人間が守る」は既にこの repo の実装方針である。pin 済み command の
  正本ポインタ到達性検査、`docs/archive/` の双方向到達性 lint、dispatch inventory の
  同一可視行からの typed edge 構成が既に存在する。新しいのは検査パターンではなく対象だけである。
- **検出できるのは非協調な drift だけである。**この lint は Markdown の意味を解釈しないので、
  次はすべて素通りする — 同一 commit で期待値ごと消す協調改変、inline の hidden HTML、
  4-space indented code block、link definition の quoted title、打ち消し線で消した prose、
  そして「この住所を参照してはならない」のような否定形の prose。**穴の列挙が短いことを
  検出力の証拠にしてはならない。**
- **edge の書き方を 1 つの形に固定する契約である。**同一可視行かつ backtick 込みの
  code span という**形**を要求するので、見出しと本文に分けた 2 行形、key/value の 2 行表、
  backtick の無い Markdown link は赤になる。これは偽陽性ではなく、住所の書式を 1 つに畳む副作用で
  ある。書式を変えたければ lint 側の契約を同じ commit で変える。
- 実装面は `tools/check_docs.py` (Python) にあり `TextLimit` の byte 予算の対象外である。
  「機械化は `docs/dev-wave/**` の byte 予算に阻まれている」という先行記述は誤りである。

**却下した選択肢:**
- 「意味検査の機械化」という呼称 — 自然文の意味検査は恒真化しやすく、偽陰性が防壁の錯覚を生む
  (D30 / D45 と同根)。この lint は日本語の文言を pin しない。語順・助詞を変えた正当な言い換えは
  緑のままであることを実測で確認した。
- 必須要素を token の存在へ分解する形 — 安全義務の文を削ったうえで path を別行へ足す攻撃を
  1 件も検出しない (実測)。同一可視行の共起でなければ迂回を殺せない。
- 単純な部分文字列一致 — `F260` と `archive/docs/failures.md.bak`、link definition、表セル横断、
  block raw HTML で偽の edge を作れる。ASCII 英数字に隣接しない ID と backtick 込みの
  exact code span を要求し、raw HTML block も不可視化しなければならない。
- 族一般化 (helper path の literal 固定、Skill 側、全 path の実在性、全 ID の到達性) —
  同型欠陥が独立に 2 件再現していない (`DW-G03`)。2 例目が出るまで却下する。
