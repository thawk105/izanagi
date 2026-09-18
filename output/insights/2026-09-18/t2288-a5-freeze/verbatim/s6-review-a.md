**must-fix 1 件、nit 3 件です。凍結値の不一致や、撤回した過大主張の復活は見つかりませんでした。** 指定資料の静的照合と、メモリ上での hash 再計算を行いました。ファイル変更・binder・検査コマンドの実走はしていません。

参照略号：

- **D**：[決定 fragment](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-a5-freeze/docs/spool/decisions/2026-09-18-dev-wave-t2288-a5-freeze-1.md)
- **I**：[insight](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-a5-freeze/output/insights/2026-09-18/t2288-a5-freeze/README.md)
- **W**：[worklog fragment](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-a5-freeze/docs/spool/worklog/2026-09-18-dev-wave-t2288-a5-freeze-1.md)
- **V**：同 insight の `verbatim/`

1. **［must-fix］検査の実施状態と結果の参照先が不整合です。**  
   W:40 は検査を「実走した」と書き、結果を insight 表と fragment 末尾へ案内します。しかし I:141・144–145 は結果を今後記録する表現で、W は `base:` 行で終わり、予告した追記がありません。現状では実施済みという記録を確認できません。  
   **修正案：** 未実施なら予定形に直し、親の実走後に rc・結果・証拠参照を記録してください。追記は `## 本文` 内に置き、更新 item 末尾の `base:` を崩さないでください。根拠：W:40–46・59、I:137–147、worklog fragment 形式契約。

2. **［nit］directory の「兄弟」という説明が誤っています。**  
   D:15 の `output/env/pegasus/floor-pair/t2288-f1/` は `output/env/<env_tag>/` の子孫です。  
   **修正案：** 「`output/env/pegasus/` 配下。`floor-pair/` は `calibration/`・`binaries/` の兄弟」とするか、括弧説明を削除してください。path 自体は正しいため、spec の変更は不要です。

3. **［nit］既決値まで「既決値ではない」と一括しています。**  
   D:34 の見出し直下には、D1641 決定 3 の site と、D2089 が確定した `env_tag=pegasus`・`clocks_per_us=2100` が含まれます。数値は正しいものの、由来の説明が矛盾します。I:37 の表にも同じ括りがあります。  
   **修正案：** 「実行設定（既決値の継承と本 wave の運用選択）」とし、120/30 秒・空 argv 等の選択と区別してください。

4. **［nit］insight の非保証列挙に module bytes の項目が明記されていません。**  
   V/s3-lens-a.md:87–94 は、D と insight の双方に「実行中 module bytes の commit 対応」を残すよう求めています。D:85 にはありますが、I:116–119 は docstring への包括参照だけです。  
   **修正案：** I の列挙にも同じ非保証を一文追加してください。現状でも保証を主張しているわけではありません。

5. **［情報］三軸値の再掲が、生証拠側に残っています。**  
   V/s4-ruling.md:15 は holdout の三軸値を同一行に列挙しています。I 本文と spec には同様の列挙を見つけませんでした。  
   **推測：** scanner の正規表現と対象範囲によっては、この転載が hit 元になります。scanner 本体は射影外なので、実際の hit は断定しません。親の既存 search でこのファイルを含む結果を確認してください。hit した場合は、原本を job dir に保存し、repo 側は転載範囲と省略を明示して整理するのが妥当です。逐語資料を黙って改変したり、scanner を緩めたりする必要はありません。

6. **［情報］数値・識別子・hash の照合結果は一致しました。**  
   spec 実 bytes から再計算した SHA-256・seed は、D:44–46、I:41–43、V/specs.sha256.txt と全桁一致しました。bytes 数は rr95/rr50 が各 **4,306**、rr5 が **4,286**。段 2 JSON は、裁定された w2 日時の変更を適用すると現物と全 field が一致します。窓日時・各 ID・出力名・62 標本にも不一致はありません。  
   plan hash 3 本、248 session・496 測定・各窓124、負対照の `…0618` / `…0619` は指定一次資料と一致します。集約名の二つの20桁 hash も再計算で一致しました。  
   ただし、stdout bytes 数・各 rc・stderr 空は、指定された集計資料だけでは独立確認できません。plan 全文と実行 receipt は親の確認対象です。

7. **［情報］授権・責任境界・後続申し送りは、指定一次資料と整合しています。**  
   D2120 項4、D1641 決定1〜3、D1974 項2・3・6、D2069、D2088〜D2090との間に、値の変更や人手責任の実装への移転は見つかりません。D2088 の訂正も記録先だけです。七つの申し送りは両レンズの実装照合結果に対応し、今回の実装追加や新 gate・台帳を要求していません。根拠：D:24–38・50–59・64–86、I:90–119。  
   fragment の frontmatter・H2・同 wave の D slug・末尾 `base:` の配置も形式契約に適合します。ただし、**T-2288 の active 状態と base digest、D1695/D1697・事前登録各節の原文、commit 内訳、実装本体は射影にないため独立確認していません。** これらまで検証済みとは扱いません。

## 総括

**(a) must-fix 一覧**

- **M1：検査状態の不整合** — W:40 と I:141・144–145を実態に合わせ、親の実走結果と証拠参照を記録する。

**(b) nit 一覧**

- D:15 の directory「兄弟」を正しい階層関係へ訂正する。
- D:34／I:37で既決の環境値と今回の運用選択を区別する。
- I の非保証列挙へ module bytes と commit の対応を追加する。

**(c) land 可否**

**現状のままは不可。M1 是正後、親の既存検査で三軸転載・active item/base・fold・受入を確認できれば、記録 3 点は land 可です。** 今回の照合から、凍結 spec の値・hashを変更する理由はありません。