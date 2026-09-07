---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-t2140-b4-prereg-fields
seq: 2
---

## {{D:b4-primary-outcome-cell-cites-source-closure}}. B-4 事前登録 §5 の primary outcome 欄は分析 source closure の path と sha256 で埋める

**決定:** §5.1 が primary outcome 欄へ要求する「その artifact path と sha256」を、
分析実装の source closure — `orchestrator/campaign/p3_b4_analysis_path.py` の
`_SOURCE_CLOSURE_PATHS` が並べる 5 member — の path と sha256 と読み、その順序で記入する。
consumer が成功時に返す source-closure receipt の path とは読まない。

**理由:**
- §5.1 は 2 つの実体を名指す。「raw な試行記録から §5.1.1 の入力型を作る経路」と
  「その実装が §5.1.1 の定義と一致することを検査する consumer」である。前者は
  `p3_b4_analysis_adapter.py` (raw artifact JSON から contract 入力型へ)、
  後者は `p3_b4_analysis_prereg_consumer.py` であり、いずれも実在する。
- `_SOURCE_CLOSURE_PATHS` は consumer 自身が AST で pin する機械権威の並びなので、
  値は親の選択ではなく機械導出になる。欄の値が恣意になる余地を残さない。
- receipt と読む場合、現行 consumer は receipt object を返すだけで path へ永続化しないため、
  **この欄は原理的に埋められない**。§5.1 が本欄を解除可能な欄として書いている以上、
  その読みは文書と整合しない。
- §5.1 の警告「定義への参照だけで埋めると、実装が無いまま他の欄が揃った時点で関門が開く」は、
  **参照だけで埋めること**を塞ぐものである。本決定が書くのは実装 artifact の bytes 束縛であり、
  実装は実在するので警告の射程に当たらない。

**限界 (主張しない):**
- consumer が §5.1.1 との一致を検査するのは contract / ledgers / path の 3 source であり、
  adapter の contract 一致は挙動検査していない。consumer 自身が宣言する AST 検査の限界も残る。
  本決定はそれらが閉じたとは主張しない。
- 記入後に closure member の bytes が変われば 5 値は同時に陳腐化する。実走前検査は
  この欄の意味も freshness も検査しないので、parser 通過を新しさの証拠にしない。

**却下した選択肢:**
- 欄を空のまま残す — 解除条件の 3 conjunct がいずれも現物で満たされており、
  未充足を理由にできない。
- raw record producer を 6 番目の member として書き足す — §5.1 が名指す「経路」は
  raw artifact JSON を入力型へ変える adapter であり、producer はその raw 記録を作る上流である。
  機械権威の closure 並びを親の判断で拡張することになるので採らない。

## {{D:preregistration-errata-are-append-only}}. 発効前の事前登録の陳腐化は、既存記述を消さず追記の erratum で訂正する

**決定:** B-4 事前登録の記述が現在地と食い違ったときは、既存の文を削除・書き換えせず、
直後へ日付と task ID を付けた追記を置き、何が変わって何が変わっていないかを両方書く。

**理由:**
- 同文書 §1 が「発効後の変更は旧版を git 履歴に残したまま新しい commit で行い、
  変更理由と変更時点を本書へ明記する」と定める。発効前でも同じ形を採れば、
  発効の前後で訂正の作法が変わらない。
- 陳腐化の訂正は「解消済み」を増やす方向に働くため、消してしまうと
  何が未決のまま残っているかを読み手が復元できない。追記なら旧記述が残り、
  差分が読める。
- 実測: §11 の 2 か所は「生成器は本書を読まず無条件に floor 不在を渡す」と書くが、
  現行の生成器は §5 を読む。**ただし §5 が未記入なら従来どおり floor 不在を渡す**ので、
  旧記述の結論部分 (「floor 行を埋めるだけでは正規経路は変わらない」) は
  「有効な pin でない記入では変わらない」という形でなお真である。
  消していれば、この「なお真である部分」が失われていた。

**却下した選択肢:**
- 旧記述の in-place 書き換え — 上のとおり未決の輪郭が失われる。
- 訂正を worklog だけに書き文書は放置 — 文書を単独で読む consumer と人間が誤った現在地を読む。
