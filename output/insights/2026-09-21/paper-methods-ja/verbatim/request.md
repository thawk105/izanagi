本体論文 (日本語) の方法節と実装対応メモを改稿する (docs-only、軽量版、台帳 ID 未起票の執筆依頼)。前稿
  `output/insights/2026-09-20/paper-methods-ja/{methods,implementation}.md` (起点 fec4a8187) は B-5 / B-8 を「2026-09-20 までに事前登録 v1
  が作られたが、いずれも未発効」と書いたままで、翌日発効し 3 値判定 `pass` になった B-8 (D2202、entry 1791) の方法 — 発効束・検証 runner
  v5・校正段と本走段・3 値判定の規則 — を持たない。結果考察・要旨結論・限界の 3 草稿は entry 1801
  で反映済みで、方法節だけが対象外だった。主対象は B-8 の方法の追加。付随して同じ方法節内で直接関係する状態記述だけを揃える: K2 の stock
  対照口は D2187 (同 job pair の初投入の不成立) と D2205 (pair mode の修復) を区別し成功を示唆しない、B-5 は D2200 項 1 の段階認可
  (本走は未認可) として B-8 と分けて書く。09-20 以後の着地全般の総点検には広げない。出所は一次資料
  (`docs/paper-story/results/2026-09-21-b8-final-candidate-longrun-verify.md`、`output/insights/2026-09-21/t2807-b8-effective/README.md`、D
  本文) とし、版や要約を出所にしない。B-8 の件数は「本走 24 枠 (独立 8 反復 × 3 workload・extime 10 s) + 校正の完走 6 枠」と 1
  文に並べる。新しい日付の dir に置き、前稿の bytes は変えない (前稿 README に前方 pointer だけ足す)。段 6 は read-only レビュー 1 本 +
  焦点再レビュー。本題の執筆だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。規律 2 は緩めない。着手直前の local main から
  fresh worktree を作る。
