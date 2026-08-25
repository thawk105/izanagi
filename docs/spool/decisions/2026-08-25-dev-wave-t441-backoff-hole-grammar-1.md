---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-t441-backoff-hole-grammar
seq: 1
---

## {{D:backoff-hole-tier1-grammar}}. backoff hole の受理文法は、二つの正本が同時に禁じる集合だけを Tier 1 として機械化する

**決定:** backoff 軸 (`silo-backoff-magnitude`) の EVOLVE-BLOCK hole に受理文法を新設し、
`p3_s4_loop.quarantine()` の backoff marker 分岐 1 点で執行する。ただし機械化するのは
**この hole の編集面を規定する二つの正本が同時に禁じる集合 (Tier 1) に限る**。

Tier 1 = 空実装、`double now_backoff` の exact な単一宣言 (型変更・参照束縛・多重宣言子・
括弧付き declarator の拒否)、宣言以外の `now_backoff` 出現、jump / label / 分岐 / loop /
try-catch、`static` / `thread_local` 記憶域、`coder.value` の整数性と 1..1000 値域、
type と raw-size の preflight。

**理由:**
- D39 決定 1 は「coder 編集面は #if 合成枝 (hole) の 1 行のみ」と裁定済みで、
  文の形を固定することは既決の機械化であって producer 契約の縮小ではない。
- 一方、骨格 patch のコメントは逐語で「既存 silo API を呼ぶ straight-line code のみ」と
  宣言しており、**式の中身**を絞る変更は producer 契約を狭める。D127 決定 (1) の論理が当たる。
- 二つの正本は「hole はちょうど 1 文か、straight-line な複数文か」で食い違っている。
  親はこの衝突を自分で解かず、Tier 1 を**両方の読みの共通部分**に限ることで、
  どちらが後に採られても過剰拒否にならない形にした。
- 実測: この文法の導入で、32 形の敵対コーパスに対する `quarantine()` の受理が 25 形から
  15 形へ下がった。既存の 7 形の拒否理由 (`HOLE_ESCAPE` / `HOST_EFFECT`) は subtype ごと保存される。

**却下した選択肢:**
- **literal-only の v1 を即実装する** — 段 2 プランと段 6 レビュー B の推奨。骨格コメントが
  許す関数呼び出しを拒否するため producer 契約の無承認縮小になる。role・review ledger・
  adapter・manifest の同時改訂とユーザー明示承認が要る。
- **設計凍結だけで終える** — 段 2 と段 3 の両レンズが推奨した停止点。しかし Tier 1 は
  承認を要さず、実測で 10 形を新たに閉じるため、可用な利得を捨てることになる。
- **正準十進整数の表記だけを受理する** — 親が段 6 の fix 指示で一度採ったが撤回した。
  `double now_backoff = 20.0;` は既存 test の canonical な正例であり、
  強制すると既定の正例コーパスを壊す。

## {{D:d127-consumer-narrowing-is-axis-scoped}}. D127 決定 (1) の「consumer だけ狭めない」は sort 軸固有の推論であり、軸を跨いで一般化しない

**決定:** D127 決定 (1) が退けた「producer を変えず consumer だけ狭める」形は、
**その軸の role 定義が複数行の生コードを契約上許している場合にだけ**当たる。
backoff 軸のように role が単一の代入文をテンプレートとして宣言している軸では、
**文の形を機械で固定することは同決定の禁止に当たらない**。式の中身を絞る変更には当たる。

**理由:**
- D127 決定 (1) の本文は「role 定義が複数行の raw comparator を契約上許可しており、
  consumer だけ狭めると producer 契約と非互換になり、**sort 軸では**合成が事前 allowlist からの
  選択に化ける」と、前提と射程を明示している。
- backoff 軸の role が宣言する出力は単一の代入文であり、この前提が成立しない。
- 一次資料の要約 (別 insight) がこの限定を落として一般則として引用しており、
  段 2 プランと段 6 レビュー B がその要約を継承して同じ過一般化に到達した。
  **要約でなく決定本文を引く規律 (F31) が、独立に 2 例で必要になった。**

**却下した選択肢:**
- 一般則として読み続ける — 承認不要で閉じられる穴を、承認待ちとして開けたまま残すことになる。

## {{D:backoff-attribution-reads-whole-pp-number}}. 帰属整合は数値 token 全体を C++ の値として読む。表記は狭めない

**決定:** `coder.value` と hole の数値の整合検査は、C++ の pp-number **token 全体**を消費し、
その token が C++ として実際に表す値を `value` と比較する。厳密に解釈できない token は
fail-closed で拒否する。**表記そのものは狭めない。**

**理由:**
- 従来の検査は十進の**接頭辞だけ**を正規表現で捕っていた。そのため
  `value=1` と `1e2` (実行値 100)、`value=20` と `020` (8 進で 16)、
  `value=2` と `2'0` (桁区切りで 20) が整合と判定され、台帳の genome と実行値が食い違ったまま
  全関門を通過していた。D39 決定 7 の整合規約が実質的に発火していなかった。
- 表記を正準十進整数へ狭める案は、既存の canonical な正例 (`20.0`) を壊すため採れない。
  **token 全体を読むだけで、表記を狭めずに帰属汚染だけを閉じられる。**

**却下した選択肢:**
- 正準表記の強制 — 既定の正例コーパスを壊す。表記の正準化は別途裁定へ送る。

## {{D:backoff-hole-single-occurrence-fail-closed}}. hole 内の `now_backoff` は宣言 1 回だけに限り、読み書きを区別せず fail-closed にする

**決定:** hole 全体で `now_backoff` はその唯一の宣言としてちょうど 1 回だけ出現してよい。
宣言より後の出現は、読みであっても書きであっても一律に拒否する。

**理由:**
- 実測で、次がいずれも文法・効果検査・帰属検査をすべて通り、
  `BACKOFF_FIXED=20` と記録された候補が実値 30 で走ることを確認した。
  参照引数を取る lambda への引き渡し、`(&now_backoff)[0] = 30;`、`*(&now_backoff + 0) = 30;`。
- 字句検査では読みと書きを区別できず、**参照引数経由で読みが書きに化ける**。
  規律 2 に従い fail-closed を採る。
- `helper(now_backoff);` のような読み専用の形も落ちる。これは D39 決定 7 を守るために
  必要な過剰拒否であり、裁定として引き受ける。

**却下した選択肢:**
- 代入演算子の近傍だけを見る字句検査 — 実測した 3 形すべてを取り逃す。
