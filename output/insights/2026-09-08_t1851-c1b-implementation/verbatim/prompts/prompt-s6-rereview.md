単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/s6-adjudication.md

## 前提 (read-only)

**書込可能な tmp が無いため pytest 緑を要求しない。静的検査でよい。** テスト実測は親が行い、
**親は所有 5 file の 400 件と consumer 7 file の緑を実走で確認済みである。**
**file を書けないので、成果はすべて最終メッセージ本文に全文で書け。** 予算が尽きそうなら、
そこまでの結論を出力形式どおり書いて終われ。無出力が最悪である。

## 必読事項の射影

作業 repository は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-rereview`
(detached HEAD、commit `2cb24ead5`) である。**読めなければ即停止**し、path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/s6-adjudication.md` — **親の段 6 裁定。R-1〜R-8 が閉じるべき所見である。**
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/s6-review-a.md` — レンズ A の逐語 (失敗シナリオ)
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/s6-review-b.md` — レンズ B の逐語
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/refs/s6-fix1-report.md` — fix 子の自己申告 (**これは主張であって証拠ではない。裏取りせよ**)
5. `<repo>/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md` — 契約の正本

審査対象は commit `d03b26773`、`d52b2f833`、`2cb24ead5` の 3 本
(`git log -3 -p` で読める。fix 単独は `git show 2cb24ead5`)。

## 依頼 — fix が本当に閉じたかを裏取りし、fix 自身が入れた新しい穴を探す

### 1. R-1〜R-8 の対応表 (必須)

**所見ごとに `closed` / `partial` / `regressed` を判定し、現物の file:line を根拠に書け。**
表が無い判定は受け付けない。fix 子の自己申告をそのまま写すな。

特に次を疑え。

- **R-2 の snapshot は本当に「副作用より前」か。** `seal_terminal_evidence()` は 3 引数の公開
  signature を保ったまま、certified 経路では private snapshot 型を受け取る形になっている。
  **legacy の 3 引数経路 (snapshot でない `reservation` を渡す形) が残っているなら、そこから
  R-2 の攻撃が再現しないかを確かめよ。** 誰がその経路を呼べるか。
- **R-4 の「同一 snapshot」は本当に同一か。** launcher の facts 検査と sealer が、
  同じオブジェクトを見ているか。canonical bytes から復元した「別 tree」を builder へ渡す実装が、
  復元の過程で値を落としたり型を変えたりしていないか。
- **R-1 の launcher-origin capability は偽造できないか。** 束縛先 (reserve state と handle
  fingerprint) は呼び手が選べないか。`_launch_floor_attempt_for_test()` から到達できないか。
  **契約 6.4 の除外 (reflection / private issuer の直接呼出し) の内側にある経路は所見にするな。**
- **R-5 の 3 検査は発行時と durable replay の双方で発火するか。** 片方だけなら `partial`。
- **R-8 で座標検査を緩めたことで、本来落ちるべき経路が通るようになっていないか。**
  受理集合を意図せず広げていないか。
- **R-7 の正規化が v1 経路へ漏れていないか。**

### 2. fix が入れた新しい穴 (これが本題)

fix は production +604 / test +901 行を足している。**この差分自身を敵対的に読め。**

- 追加された snapshot 群のうち、**どれか 1 つでも builder 実行後に取られていないか。**
- snapshot 化の過程で、**元の検査が落ちていないか** (例: canonical 化で型情報が失われ、
  以前 exact type で弾いていたものが通るようになっていないか)。
- **恒真になった gate はないか。** 追加された述語が候補集合に含意されて常に真になっていないか。
- **新設テストのうち、実体を名指しせず性質だけを見ているものはないか** (依存先を stub すると
  両層 stub で機構を通らない緑になる)。
- **既存テストの期待値が緩められていないか。** 親が許可した意味変更は
  `test_v2_profile_is_rejected_before_any_registry_side_effect` と
  `test_v2_profile_is_additive_empty_retryable_and_budgeted_by_cell` の **2 箇所だけ**である。
  それ以外の反転・緩和・skip・削除・golden 更新を diff 全体で探せ。
- **v1 の受理集合が 1 bit も変わっていないこと**を再確認せよ
  (event key exact 24、retryable reason 集合 空、既定 `retryable_reason_field="failure_reason"`)。

### 3. 変異の帰属 (F1〜F7)

親は fix 前に F1〜F7 を事前登録した (裁定 5 節)。fix 子は「すべて単一理由で kill できる」と
申告している。**各変異について、その変異を入れたときに赤くなる test が本当に 1 つの理由に
帰属するか**を静的に確かめよ。**同じ入力を拒否する層が前後にも内側にもあるなら、それは
冗長 gate であり kill に数えられない。** 該当があれば実効 gate への再照準案を書け。

## 出力形式

節見出しはすべて `##` で統一する。

**まず `## 対応表` を置き、R-1〜R-8 の closed / partial / regressed を file:line つきで書く。**

次に新規所見を、1 件ごとに (a) 一文要約 / (b) 現物の file:line / (c) 失敗シナリオ /
(d) 修正案 / (e) 重大度 (`blocker` / `must-fix` / `nit`) の 5 点で書く。

最後に `## 総括` を置き、次を書く。

- 判定: `go` (このまま変異走と受入へ進んでよい) または `no-go`
- R-1〜R-8 のうち closed / partial / regressed の件数
- 新規所見の blocker / must-fix / nit 件数
- F1〜F7 のうち帰属が単一だと確かめられたもの、確かめられなかったもの
- **攻撃したが破れなかった箇所**も明記する

## 制約

- 出力へ結合文字 U+0300〜U+036F を使わない。
- **`IZANAGI_RUN_GROWTH_HELD_TESTS` を設定して hold を解除するな。**
- 実装・編集・commit をしない。
