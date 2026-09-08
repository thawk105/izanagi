単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/9218ced6/tmp/t2380/brief.md (親の段 1 brief。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/9218ced6/tmp/t2380/artifacts/dev-wave-t2380-b5-successor-freeze/plan.md (段 2 の plan。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md (親が起草中の後継凍結物 1/2 の草稿。未 commit。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md (凍結済み部分登録。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-05-backoff-axis-registration.md (軸登録。§3 が候補 3 群の定義元。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/README.md の「7.7 主張軸別の調査状態と、不在主張の成立条件」(7.7.3〜7.7.6。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/decisions.md の D351、D384、D1206、D1207、D1208 (`grep -n "^## D351\.\|^## D384\.\|^## D1206\.\|^## D1207\.\|^## D1208\."` で位置を引く。読めなければ即停止)

## 役割 — レンズ A: 正しさ境界と受理集合

あなたは dev-wave 段 3 の敵対相談者である。**plan と親 brief と後継凍結物 1/2 の草稿を守らず、攻撃する。** 親 brief 自身も検査対象である。
read-only sandbox なので pytest は走らせなくてよい。外部 network は使わない。

主題は文献検索の事前登録であり、正しさ防壁は「凍結した完走述語・positive control・停止条件を、結果を見た後に緩めない」である。
本 wave は凍結済み部分登録の §4.2 gate 項目 3 を、後継凍結物の erratum E-1 で 3 値 (収録 / 非収録 / 不達) へ改める (brief の P1、草稿 §2.4〜§2.5)。

攻撃すること (各所見に real か refuted かの自己判定と、根拠の file:line または節番号を付ける):

1. **E-1 は受理集合をどこまで広げるか。** 草稿は「非収録は当該索引の包含 control から外す」「(slot, 索引) で収録 0 なら `適用不能` と記録し軸全体の `未完走` にはしない」とする。
   これは部分登録 §4.2 項目 3 が明示的に禁じた「不達の索引を control の適用対象から外して論理積を通す」の言い換えになっていないか。
   なっているなら、どの文をどう直せば「索引を母集合から外さない」と「構造的に閉じない述語を D1207 の型で改める」の両方が成り立つか、具体的な代替文を出せ。
   `適用不能` が実質的な宣言的除外 (D1207 が禁じる) になる経路を探せ。
2. **anchor 集合 (草稿 §2.2、16 件) の選定が D351 の逆向き reward hack (通りやすい anchor を選ぶ) になっていないか。逆に、包含枝の語彙で構造的に届き得ない anchor ばかりで、control が必ず失敗し軸が永久に `未完走` になる設計になっていないか。** 両方向を検査し、
   部分登録 §4.2 の表 (slot ごとの包含枝) と §3.1 の語彙を突き合わせて、各 anchor がどの枝に届く見込みがあるかを **静的に** 評価せよ (結果は見ていないので見込みでよいが、根拠の語を書け)。
   選定規則 (草稿 §2.1) 自体の穴 (例: 「必ず含める」対象の解釈で恣意が入る余地、閉集合の宣言が amendment で骨抜きになる経路) を挙げよ。
3. **草稿 §2.3 の主キー確定手順は 7.7.6 (名称で引かない・主キーは DOI / arXiv ID・alias record) を満たすか。** 手掛かりの著者・題で「同定候補を見つける」ことと「主キーを名称で決める」ことの境界が守られているか。Crossref 404 時の代替 (landing page の表示書誌) は一次資料として十分か。
4. **草稿 §2.4 の「実行前 = live preflight」(E-2) の読みは、部分登録 §4.2 項目 3 と §5.3 の文面から許されるか。** 本 wave で OpenAlex / arXiv だけ lookup し DBLP を `不達` と記録する非対称が、後で「DBLP は見ていない」を隠す経路にならないか。
5. **親 brief の実測とその一般化を攻撃せよ。** brief §「段 1 前の実測」の「OpenAlex は arXiv ID を鍵として引けない」「arXiv は DOI を鍵として引けない」「DBLP は本ホストから不達」は、それぞれどの request で測り、どこまで一般化してよいか。
   OpenAlex に arXiv ID を鍵にする別経路 (例: filter や別の ID 形式) が公知にあるなら、それを試さずに `鍵不適用` と凍結するのは早計かを論じよ (network は使えないので知識と文書だけで、断定せず「検証すべき経路」として列挙せよ)。
6. **草稿 §4 の 3 経路の読み** (前方引用・著者は全頁取得後に client 側で主キー辞書順の先頭 N 件) は、部分登録 §4.5 の「上限で打ち切った `完走`」「上限内の選択順序を固定する」と整合するか。これが部分登録 §5.4 の意味的 amendment に当たるなら、そう明記すべきかを判定せよ。
7. **規律 2 (正しさゲートを緩める変異を採用しない) の観点で、本 wave の変更のうち「凍結した判定を結果を見た後に緩める」に該当しうるものを 1 つでも探せ。** 該当が無いなら、無いことの根拠 (何を見ていないか) を書け。

## 禁止

- ファイルを書かない・変更しない。git 操作をしない。外部 network を使わない。
- 凍結済み 2026-09-07 / 2026-09-05 文書の変更を提案しない (訂正は後継文書で)。
- 新しい gate・検査・台帳・一般化の追加を推奨しない。scope 外の real 所見は「裁定パッケージ候補」として分けて書け。
- 出力に結合文字 U+0300〜U+036F を使わない。

## 出力形式

見出しは全部 H2 (`## `) で書く。所見ごとに `A-<番号>`、`real` / `refuted` の自己判定、根拠 (file:line または節)、推奨対応 (1〜3 行)、scope 内/外。
最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。予算が尽きそうなら途中結論をこの形式で書いて終われ。

## 所見
## 裁定パッケージ候補 (scope 外)
## 総括
