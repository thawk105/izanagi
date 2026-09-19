78行の再抽出・分類・集計の照合は**不一致0件**でした。ただし、取得件数の表現に must-fix 1件、nit 2件があります。

## 所見 R-1: 「取得済み78 leaf」は未走1件を取得済みに含めている

- **主張:** 表題とREADME一覧行の「取得済み78 leaf」は誤り。78は登録数で、取得証拠があるのは77。
- **根拠 (file:line):** [新記録:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2035-axis1-materials-record/docs/related-work/claim-survey/2026-09-19-axis1-search-execution.md:1)、[claim-survey README:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2035-axis1-materials-record/docs/related-work/claim-survey/README.md:61)。同じ新記録の155行目では `Q6-SY2026` が `leaf_not_run`・完了pass `[]`、208行目では取得頁なしと明記されている。一次資料とも後者が一致する。
- **判定:** **real / must-fix**。
- **修正案:** 両箇所を「登録78 leafの全列挙（取得証拠あり77・未走1）」へ変更する。
- **成果物影響:** 材料レポートの入口が示す取得済み集合から `Q6-SY2026` を除き、取得済み数を78から77へ訂正する。材料に数える61は不変。

## 所見 R-2: 先行記録2本のSHAが省略形しかない

- **主張:** 18・18bのSHA-256は、本文中に完全値が一度もない。
- **根拠 (file:line):** [新記録:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2035-axis1-materials-record/docs/related-work/claim-survey/2026-09-19-axis1-search-execution.md:33) は `f4c7f288…`・`63140879…` のみ。静的にSHA-256を再計算し、省略部分までの一致を確認したが、完全値の記載は見つからない。
- **判定:** **real / nit**。今回の「少なくとも1か所は完全値」という確認条件は未充足。ただし31行目の完全commitと入力pathでblobを特定でき、実際に入力8ファイルすべてがそのcommitのblobとbyte一致したため、身元喪失を理由とするmust-fixにはしない。
- **修正案:** 2本とも完全なSHA-256を記載する。
- **成果物影響:** 入力同一性を文書だけで照合できるようになる。導出元・材料集合・分類値は変わらない。

## 所見 R-3: 起動ゼロの表と残件列挙は短縮できる

- **主張:** §1の全ゼロ表と§7の残件再掲は、追補の成果条件に対して重複が多い。
- **根拠 (file:line):** [新記録:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2035-axis1-materials-record/docs/related-work/claim-survey/2026-09-19-axis1-search-execution.md:45)、[同:224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2035-axis1-materials-record/docs/related-work/claim-survey/2026-09-19-axis1-search-execution.md:224)。起動・requestゼロは冒頭でも宣言し、残件は18b §5を参照した直後に再掲している。
- **判定:** **real / nit**。
- **修正案:** §1は起動・request・probeゼロの1文へ、§7は先行記録への参照へ短縮できる。限定を同じ場所に置く§4は削除対象にしない。
- **成果物影響:** 値・受理集合・参照先は不変。可読性だけの改善である。

照合した件数と方法は次のとおりです。

- Markdown表を読み取り専用Pythonで解析し、leaf接頭辞・接尾辞、`—`、checkpoint略記を復元。JSONのOpenAlex **78件×指定7フィールド＝546値**を全件比較した。欠落・重複・余分なleaf・列値不一致はすべて0。
- A〜Gは **8 / 53 / 3 / 6 / 2 / 5 / 1**。Eの2件は窓4 README:71・73、Fの5件は窓3 `cond5-detail.txt`:1・4、窓5 `evidence-detail.txt`:43・97、窓6同ファイル:8以降の申告総数とdistinctで裏づけた。
- §3の6枝と合計を§2から再集計し、全セル一致。材料61、数えない16、未走1。**再抽出・集計上の所見はゼロ**。
- §0の登録commit・catalog SHA・cutoff・bundle root・manifest SHAは18bの値と逐語一致。manifest未照合とprobe換算の断りもある。
- 限定は再配置・要約されており完全な逐語再掲ではないが、指定された先行記録から意味が弱まった箇所は確認しなかった。新しい世界の不在主張や、取得件数を調査済み件数とする文もない。
- consult A-1は充足。backoffの「関係」節に導線があり、B5の`RW0`・保留を維持している。B-2の中心要件も充足し、省略SHAだけがR-2として残る。
- `git status`はclean。`git diff main`は新規1＋README追記2のみ。主論文README、既存凍結物、実装面の変更や新しいgate・検査・台帳はない。

ファイル変更、外部request、bundle接触、pytest・検査器の実走は行っていません。

## 総括

最も危険なのはR-1：入口の「取得済み78」が未走leafを取得実績へ混入させる。
採否は **条件付きGO**。表題と一覧行を「登録78・取得証拠あり77・未走1」へ訂正すること。
78行の全列照合と枝別再集計は不一致0件。材料61・RW1・B5保留・凍結契約は維持されている。