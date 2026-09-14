## 受理集合への所見

1. **nit —「受理集合不変」が、固定 bytes の検証と時間変化するファイルの拒否を区別していない。**
   **file:line:** `brief.md:34`、`stage2-plan.md:46`、`tools/codex_reasoning_ab.py:8974`。
   **成果物への影響:** 不変条件を文字どおり満たしたという完了報告はできない。

   descriptor 照合後にファイルが消える例では、現行 replay／packets は JSON 再読時に `RC_AGGREGATE / cannot read JSON object ...` で拒否する。案は取得済み bytes を解析して進む。これは一度読みに伴う観測契約の変更であり、固定入力の検証を緩めたこととは区別する必要がある。

   姉妹 helper の指定順序は、現行 `:9012` の dict 判定、`:9014` の解決、`:9015` の root 包含、`:9020` の SHA 型・長さ、`:9023` の read／OSError、`:9027` の SHA 比較と対応している。ただし `stage2-plan.md:21` は全文実装ではないため、**姉妹 helper 同士の行単位比較はまだ不可能**。指定どおり実装した場合の固定入力の反例は構成できなかった。

## supervisor の SHA 帰属への所見

2. **must-fix — frozen の観測を source で代用し、現行が拒否する破損状態から launch を生成できる。**
   **file:line:** `stage2-plan.md:55`、`tools/codex_reasoning_ab.py:7634`、`:7637`、`:7639`、`:7741`、`:7517`。
   **成果物への影響:** disk の frozen schedule が不正でも、source の SHA を持つ launch receipt と実行が生成されうる。

   具体例は、正当な source A を保存・比較した直後、現行 `:7638` より前に frozen を malformed JSON B に上書きすること。現行は B を読み、`:8975` で `RC_AGGREGATE / cannot read JSON object ...` を返す。案は A を hash・解析し、その後の条件が満たされれば launch へ進む。

   不一致の成立条件は次のとおり。

   - **部分書込み失敗:** `write_bytes` が例外を送出すれば両方停止する。それ自体は反例ではない。正常 return 後に内容が不完全・変更済みとなる場合が差分。
   - **書込み後の上書き:** 上記の直接反例。
   - **既存 frozen の一致比較後の差し替え:** `:7634` の比較を残しても、その後の破損は案では読まない。
   - **並行 supervisor:** fresh 判定・存在確認・書込みは不可分ではない（`:7626`、`:7633`、`:7637`）。両者が確認を先に通過すれば、一方の source と他方が残した frozen が食い違いうる。ただし、その後の ledger closure による停止もあり、両者の完走までは断定しない。

   下流も「必ず捕まえる」とはいえない。

   - B が replay の取得時まで残れば、descriptor SHA、manifest SHA、launch SHA のいずれかとの不一致で検出できる（`:11137`、`:11153`、`:11366`）。
   - replay が A を取得した後に B へ変更されれば、案の `:11152` は取得済み A の再 hash にすぎない。mtime を維持すれば `:11364` も検出しない。
   - launch 時には B、replay 時には A を復元し mtime も戻す場合、これらの照合は launch 時点の不一致を証明できない。

   `_load_json_object(frozen_schedule, data=source_schedule_bytes)` は、この反例で**現に frozen の path を名乗って source を解析する**。ただし hash と解析はともに A なので、元の「A を hash・B を検証」と同型の認証不整合が残る、とまではいえない。残るのは frozen 帰属と拒否動作の変更である。

   修正対象は source authority の採用。保存・比較後の **frozen を一度取得し、その同じ bytes を hash と解析へ使う**局所案を検討すべき。これは保存後の永久不変性までは保証しないが、今回失われる frozen の観測を維持する。

## 親 brief の不在の主張への所見

3. **nit —「live consumer 0 件」の母集合が検索手法だけで記されている。**
   **file:line:** `brief.md:37`、`:40`、`output/insights/2026-08-09_t181-certified-rerun/apparatus-pin.json:4`。
   **成果物への影響:** pin 更新漏れの実例は未発見だが、worktree 外まで閉包したという根拠にはならない。

   今回、worktree 内の `tools / orchestrator / docs / output / .claude / .codex` を hidden 込み・通常の ignore 適用で現行 SHA の完全一致検索を行い、hit はなかった。歴史 pin の `:5` は旧 SHA だった。

   ignored ファイル、外部実行環境、別 worktree、文字列リテラル以外で構成される pin は、この検索の母集合外。外部 repo は指定に従って読んでいない。「0 件」は確認した範囲に限定して記述する必要がある。

4. **nit — validator の呼出数から導ける全数性を超えている。**
   **file:line:** `brief.md:53`、`:59`、`stage2-plan.md:288`。
   **成果物への影響:** 第四の対象入口は未発見だが、repo 全体の schedule consumer 不在を証明したとは報告できない。

   validator 名からの検索とは別に、I/O・JSON loader・artifact resolver の呼出引数を AST で抽出し、`tools / orchestrator` の非テスト Python に対する schedule path 検索と突き合わせた。直接のファイル取込みは指定の3関数に集まった。この確認は動的参照や外部 consumer の不存在まで保証しない。

   非攻撃時の bytes について、空白・末尾改行・BOM・UTF-16／32・重複 key は、同じ `json.loads(bytes)` と原 bytes 保存を使う限り変更例を構成できなかった。不正 encoding も既存の例外処理が残る。所見2の I/O・並行変更を、これらの固定 bytes の互換性と混同しないこと。

## scope 境界への所見

5. **nit — P1-b の修正を「追加防壁」と扱って scope 外へ落としてはいけない。**
   **file:line:** `brief.md:58`、`stage2-plan.md:293`、`tools/codex_reasoning_ab.py:7638`。
   **成果物への影響:** 所見2の解消方針を誤ると、既存拒否動作を失ったまま統合する。

   **裁定パッケージ候補は「source authority を撤回し、frozen の一度読みを authority にする」**。既存3入口内の観測対象を維持する変更であり、新しい台帳・一般化・恒久ロックの追加とは異なる。SHA 計算の重複許容自体に検査脱落はない。問題は hash 回数ではなく、supervisor が frozen を観測しなくなる点である。

## 総括

- **blocker: 0 件、must-fix: 1 件、nit: 4 件。**
- 最も危険なのは、source authority 化で、破損した frozen を現行どおり拒否せず launch できること。
- 下流照合は永続する差異を検出するが、launch 時点の disk 内容までは証明しない。
- 元の hash／解析不一致と、今回変わる frozen 帰属は分けて扱う必要がある。
- 静的検査のみ。ファイル変更・pytest 実行はしていない。