git-load md_1: output/ の価値の低いファイルを、履歴を残したまま HEAD から外す (作業ツリーを軽くする)

(2026-09-29、ユーザー依頼により親セッションが作成。CLAUDE.md の絶対規律と dev-wave の契約はこの file より常に優先する)

■ 背景 (2026-09-29 14:2x JST の実測)
- 並行 session の git が Lustre (/work) の metadata 待ちで詰まった: git 54 本のうち 42 本が D 状態、1 分 load 63。
  主因は同時の `git worktree add` (約 10 本、各 8〜13 分) と、掃除の同時 `git status` (29 本と 25 本)。
- repo の追跡 file 34,735 のうち output/ が 31,291 (約 90%)、うち output/insights/ が 26,816。拡張子では md 11,026・json 7,227・raw 3,499・txt 2,144・gz 1,773・stdout 1,145・stderr 1,103・log 725・rc 689。
  最大の insight dir は 2026-08-03_t361-t362-cluster-probes (3,744 file)、2026-08-29_t2033-axis1-retake (2,127)。
- 作業ツリーを 1 本作るたびに約 3.5 万 file を書き出し、`git status` のたびに約 3.5 万 file を stat する。作業ツリーは 212 本登録されている。
- ユーザー指示: 「output/ 配下にある価値の低すぎるファイルは削除した方が良いのでは。例えば『これやってみたけどこうだった』というようなもの、claude / codex から見てその知識はなくても自明と思えるもの、そういうのは掃除しても良い」。

■ 守ること (既存の決定)
- D577: output/ の tracked bytes 削減は履歴を保全した方法で行い、破壊的な履歴書き換え (filter-repo・rebase・force-push) は使わない。本 wave は `git rm` で HEAD から外すだけで、過去の commit には残る。
- D2211 項 9 (ユーザー裁定 2026-09-21): sparse-checkout と「木の本数を減らす運用」は採らない。本 wave はどちらもしない。
- 絶対規律 7: 記録された測定・判定は事実として残る。HEAD から外しても「どの commit のどの path にあったか」を引けるようにする (下の索引)。外したことを理由に過去の判定を無効にしない。
- 絶対規律 2・3: 正しさゲートの材料 (verifier の入力・正例負例・受領証・事前登録・凍結・pin で束縛された file) は外さない。

■ やること
1. 権威ある参照閉包を作る: output/ の各 file について、repo の追跡 file (docs/・tools/・orchestrator/・hooks/・patches/・tests・.claude/・output/ 自身の README や JSON) から path・basename・sha256 で参照されているかを全数走査する。
   sha256 や blob id で束縛された file、fixture・inventory テストが読む file、campaigns/・env/・s1-*/s6-*/s8*/t189-* の凍結・事前登録系は削除候補から外す。走査の方法と件数を一次資料に残す。
2. 分類する (2 レンズの codex 相談で割る — 「消してよい」を攻めるレンズと「消すと困る」を攻めるレンズ):
   (A) 参照されていない機械出力 (raw・stdout・stderr・rc・log・中間 json・gz の束、同一内容の重複)、
   (B) README から参照はあるが、README 本文に結論と数値が要約済みで原本を読む必要が低い生ログ、
   (C) insight dir 全体の価値が低いもの (ユーザーの言う「やってみたけどこうだった」で、claude / codex から見て自明な知識、論文にも設計判断にも使われていない)、
   (D) 残すもの。
   C は dir 単位で、その insight が decisions / worklog / failures / paper-story / 論文稿から主張の根拠として引かれていないことを確かめる。引かれていれば D。
3. 外し方: 第 1 段は A (と、確信度の高い B) だけを `git rm` する。C は候補一覧と理由を一次資料に載せ、件数の多い上位から段階的に外す (同じ wave で外すのは自信のあるものに限る)。
   外した file の索引を 1 本だけ置く (例: output/PRUNED-INDEX.jsonl に path・blob sha・最後に存在した commit・分類・理由)。README の参照が切れる場合は、README に「HEAD から外した、commit <sha> の path で引ける」と 1 行足すか、索引で引けることを README 冒頭に書く。
4. 効果を測る: 外す前後で追跡 file 数、作業ツリー作成 (`git worktree add`) の所要、`git status` の所要を、同時刻の対照を置いて計算ノードではなく同じ login 条件で数回ずつ測る (混雑の影響を明記)。
5. 検査: `python3 tools/check_docs.py`、関連テスト、受入全走。inventory テストや path を読むテストが落ちたら、テストの前提を正しく直すのか、その file を残すのかを段 4 で裁定する (テストを弱めて通さない)。

■ 成果物
- `git rm` した file (第 1 段)、output/PRUNED-INDEX.jsonl (または同等の索引 1 本)、必要な README の 1 行追記。
- 一次資料: output/insights/<着手日>/output-pruning/README.md (参照閉包の走査方法と件数、分類の基準と件数、外したもの・残したもの・次段の候補、効果の実測、限界)。
- decisions fragment (output/ の整理方針 = 何を外してよく何を外さないか、索引の置き方、ユーザー指示の引用)。worklog fragment (次段の item)。

■ 注意
- 並行 wave が多数走っている。外す file を他 wave が編集中でないか、編集面の重複検査を作業ツリーの未 commit まで含めて行う。
- 一度に数千 file を外す commit は受入・land が重いので、段を分けてよい。
- ユーザーは起きている。C の基準に迷う境界例は、判断を codex の 2 レンズで決め、決めた根拠を decisions に残す。
