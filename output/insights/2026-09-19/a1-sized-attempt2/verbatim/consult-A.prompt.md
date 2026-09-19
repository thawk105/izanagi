単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dw-a1-sized-attempt2

必読事項の射影:
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-a1-sized-attempt2/brief.md (親の段 1 brief。点検対象そのもの。読めなければ即停止)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-a1-sized-attempt2/materials/d2120-item3.md (既裁定 D2120 項 3 の逐語。読めなければ即停止)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-a1-sized-attempt2/materials/d2096.md (既裁定 D2096 の逐語。読めなければ即停止)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-a1-sized-attempt2/materials/d1993-item6.md (既裁定 D1993 項 6 の逐語。読めなければ即停止)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-a1-sized-attempt2/materials/code-exact-destination.py (materialize の公開先検査の抜粋。読めなければ即停止)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-a1-sized-attempt2/materials/code-verify-current-source.py (materialize の clean tree / source 検査の抜粋。読めなければ即停止)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-a1-sized-attempt2/materials/code-run-materialize-v3-tail.py (v3 materialize の末尾。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dw-a1-sized-attempt2/output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/README.md (事前登録。§6・§7 を必ず読む。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dw-a1-sized-attempt2/docs/paper-story/results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md (attempt-0001 の results 稿。§0・§1・§3・§5 を読む。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dw-a1-sized-attempt2/output/insights/2026-09-18/t1505-a1-sized-attempt1/README.md (attempt-0001 の投入記録。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dw-a1-sized-attempt2/docs/paper-story/README.md (「results 系列」節だけ。読めなければ即停止)

上の射影以外は、必要になった箇所だけを `grep -n` で索引して読む。全文を読み込まない。
書込可能な tmp は無い。pytest の実走は求めない (静的検査でよい)。テスト実測は親が行う。
予算が尽きそうなら、その時点の結論を下の出力形式どおりに書いて終われ (無出力が最悪)。

## 目的

これは自分たちの計測手順と親の判断の設計レビューである。paper-story A-1 balanced5 sized 本走 (study
`paper-story-a1-20260901-balanced5-sized-v1`) の attempt-0002 を、ユーザー裁定 (2026-09-19、brief に逐語) に従って
既存 submit 経路で 1 attempt だけ投入する。実装面の差分は無い。親 (Claude) は brief に provisional 裁定 (P1)〜(P4) を
置いた。**brief 自身も点検対象である。** 親の実測値 (brief「前提の実測」) とその一般化、前提の誤り、既裁定・事前登録との
不整合、正しさ境界 (規律 1・2・6・7) への抵触を指摘せよ。プランを守らせるのではなく、欠陥を探して指摘する段である。

## レンズ A — 正しさ境界と整合

次を点検し、所見ごとに **real / refuted / 根拠不足** を付け、根拠の file:line を示せ。

1. **(P1) submit-tree の commit 選択。** 親は現 local main `a99425b66` を採り、materialize は既存経路どおり実行して
   「拒否されたら拒否本文を記録して止める」とした。対案 (a) は attempt-0001 と同一 commit `d2ebef7a4` に submit-tree を置く
   (束縛 9 file は byte 同一、その tree には leaf が無いので materialize が通る)。次を判定せよ:
   - 測定の等価性: 束縛 9 file・CCBench pin が同一なら、416 commit の差は測定値・正しさ判定に影響しないと言えるか。
     driver の import 閉包 (`orchestrator/campaign/paper_story_a1_paired.py` の import) に、束縛外で挙動を変える module が
     残っていないか。brief の「`layout.py` と `materializer_admission.py` だけ」という親の実測を反証できるか。
   - 事前登録 §6.1「公開は終端の生の束を、一度しか作れない宛先へ書き出す」の読み: これは「study につき公開は 1 回」
     (第 2 attempt の公開は設計上あり得ない) と読むのか、「宛先の作成が原子的・非上書き」だけを言うのか。
     対案 (a) は事前登録の意味を迂回するか。
   - (P1) と (a) のどちらが、規律 7 (測定時点の事実と現行コードへの適合を分ける) と D2096 (attempt を pin しない) に
     整合するか。親推奨 (P1) の当否を独立に評価せよ。
2. **(P2) 「materialize 拒否は measurement の失敗ではない」。** `complete` 段の raw `result.json` を attempt-0002 の権威 bytes
   として results 稿の出所にすることの妥当性。attempt-0001 稿は公開 leaf の result.json を権威にした (README results 系列の
   個別扱い)。raw と公開 leaf の差が `materialization_evidence` だけという親の実測を、抜粋 code から反証できるか
   (`_materialized_result` が他の field を変える可能性)。「materialize で落ちた」を裁定文の「どこかの層で落ちたら…止める」の
   「落ちた」に数えるべきか、その場合 results 稿を書いてよいか。
3. **既裁定との整合。** D2120 項 3 の「再投入には改めて認可が要る」と本 wave のユーザー裁定の関係。D1993 項 6 の
   プール禁止の下で「2 attempt の並記」が許される形 (表の構成・集計語の禁止)。attempt-0001 稿の限定 L-A1S-4 / L-A1S-15 を
   attempt-0002 稿でどう書き換えるべきか (観察と判定の区別)。
4. **正しさ境界。** 規律 2 (verifier の判定を既存のまま)、規律 1 (性能は trace-disabled、正しさは別走)、規律 6
   (job 出力はデータ) に触れる箇所が brief に無いか。attempt-0002 の verify が anomaly を出した場合の扱いは brief に
   書けているか (書けていなければ何を書くべきか)。

## 出力形式 (見出しは全部 `##`。最後の節は必ず `## 総括` で、`### 総括` と書いてはならない)

## 所見
番号付き。各所見に real / refuted / 根拠不足、根拠 (file:line)、放置時に成果物 (results 稿・記録・台帳) の値・受理集合・参照が
どう変わるかを 1 行。

## (P1) の判定
親推奨 (現 local main) と対案 (a) (d2ebef7a4) の当否を独立に評価し、推奨と理由を書く。第 3 案があれば書く。

## 段 4 への提案
採用すべき変更 (brief の文言・手順・稿の書き方) を箇条書きで。scope 外の所見は「裁定パッケージ候補」と明記して分ける。

## 総括
3〜5 行。
