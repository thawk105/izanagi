---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t1179-official-trust-root
seq: 1
title: official 解禁の信頼根を durable admission 台帳へ移し、crash 復帰の袋小路を手順書へ書き出した — 親が自分の裁定と指示の誤りを 3 件撤回した (コード + テスト + docs、branch worktree-dev-wave-t1179-official-trust-root)
---

## 本文

[T-1179] の残 2 件を 1 wave で扱った。裁定は 2026-08-16 /rulings 全件 第 3 回で 2 問とも確定済み。

### 親が自分の誤りを 3 件撤回した

いずれも子または実測が突き、親が撤回した。3 件とも「親が一次資料を見ずに書いた」型である。

1. **段 1 brief の「下流 2 消費者」は数え落としだった。** 実際は 3 caller で、加えて
   `render_result_md` が共有 verifier を通らず bit を読む別経路だった。段 3 レンズ B が突いた。
2. **fix 巡 2 への指示が自分の裁定と逆だった。** 「部分発行の backfill でも `entry_kind` は
   既存 claim に合わせる」と書いたが、段 4 裁定は「混在は marker があるときだけ許す」で
   混在を許していた。fix 子が「確定仕様と既存 expectation が両立しない」と**実装せずに停止**し、
   それで発覚した。子の停止判断が正しかった。
3. **段 4 裁定が marker identity に manifest hash を含めさせたのは行き過ぎだった。**
   段 3 レンズ B の提案文をそのまま採ったせいで、main 由来テストが期待する既存の拒否理由を
   新 reason が横取りした。焦点走の赤 1 件がこれを出した。

### 焦点再レビューの NO-GO を親が refuted に裁定した

段 6 の焦点再レビューは「M-finalize-pending が eligible な official result を永久失格化する。
**main 比の回帰**である」として NO-GO を返した。親はこれを **refuted** と裁定した。
根拠は main 自身のテストである — `git show 699c9cae:orchestrator/tests/test_s8b_floor_campaign.py`
の同 test が、この publish-only 再開が `staged bytes が再計算と不一致` で拒否され
`result.json` が現れないことを固定している。**回帰ではなく main の既存挙動**だった。

**親はこの refuted 判定に至る前に、レビューの主張を検証せずに fix 巡 4 を投入していた。**
その巡は main 由来の期待値を「成功する」へ書き換えさせた。子が
「test 関数と旧失敗期待は main に存在した」と報告し、親が一次資料で確かめて **fix 巡 4 を全破棄**した。
レビュー所見を一次資料で裏取りする前に fix を投げてはならない、という教訓である ({{F:review-claim-unverified-before-fix}})。

なお、この袋小路自体は本 wave が塞いだのではなく元からあり、裁定 (2) が扱う対象そのものである。
手順書 §3.6 へ crash 点分類として書き出し、解消の択一を §5 R-5 として裁定へ返した。

### 変異の登録から 2 件を外した

変異 1 (`entry_kind` 項の削除) と変異 8 (marker 件数 guard の緩和) は、実装子・段 6 レビュー A・
段 6 レビュー B の三者が独立に「単一理由性を満たさない」と判定した。DW-M01 に従い登録から外し、
defense-in-depth として記録する。焦点再レビューもこの判断を「正しい」と再確認した。
変異 5 (derived 値の受け渡し削除) は型 gate が比較より先に落とすため、DW-M08 に従い
kill matrix から外して diagnostic sensitivity pin へ別枠記録する。

### DW-O16 の 3 巡上限について

fix は 4 巡投入したが、**巡 1 は編集ゼロ**である (親の許可リスト書き漏れで
`s8b_holdout_freeze.py` に触れず、子が正しく全体停止した)。実質の fix 巡は 2・3 の 2 巡で、
巡 4 は破棄した。したがって上限には抵触していない。

### 変異 matrix の実測

**baseline PASSED、9/9 KILLED、MISMATCH 0、SURVIVED 0、TIMEOUT 0** (計算ノード dispatch)。
probe (全件 SURVIVED 期待) で観測 node を集め、期待 node の完全集合を実測から確定してから本走した。
m02 は 101 node、他は 1〜3 node。

到達までに 2 走を無駄にした。1 走目は親が走行中に docs を書いて harness を止め、
2 走目は node ID の 2 空間問題で m02 が MISMATCH になった。後者は
**回避策が既に failures 台帳に載っていたのに走行前に引かなかった**もので、
台帳どおりに直したら一度で通った ({{F:review-claim-unverified-before-fix}} と同じ規律の破れ)。

### 子の実行環境

**codex 子は 6 回とも pytest を 1 度も実走できなかった** (実装子 1・fix 子 3・spec 子 1・
レビュー系は元から静的)。`tools/run_tests.py` が dispatch preflight `qstat -Q rc=1` で
`rc=16` になる。実測はすべて親が行った。親の焦点走は計算ノード dispatch で 30〜37 秒、
ローカル bounded で 1058 秒だった。

**変異 probe を親自身が壊した。** 走行中に手順書 (`docs/phase3-8b-restart-runbook.md`) を
編集したため、`mutation_worktree.py` の事後検査が「共有木の観測 bytes が変化した」で
`rc=125` 中止した。docs 執筆も tree への書き込みである ({{F:docs-write-during-mutation-run}})。

設計判断は {{D:durable-admission-trust-root}} と {{D:finalize-pending-not-a-resume}}。

## 次の一手差分

### 更新

- [T-1179] **P1・部分完了**: (1) official 解禁の信頼根を durable admission 台帳へ移した。
  floor cell claim を v2 へ上げて `entry_kind` と非既定 seam 集合を exact 記録し、
  fresh 後の resume は claim を書き換えず create-only の run-wide marker で表す。
  live inspector が claim と marker から eligibility を必ず再導出し、共有 live verifier が
  artifact の申告値と双方向で照合して不一致を拒否する。どちらの値も他方で上書きしない。
  **買えたものは狭い** — 測定前の create-only な事前 commitment、生成後 artifact の書換と
  resume 後の付け替えの検出、台帳と artifact が食い違うときの下流拒否である。
  同一 interpreter 内の code substitution への耐性は引き続き主張せず、既知限界を狭めて残した。
  (2) crash 復帰は **docs のみ**で閉じた。再生成を実行可能にする手段が現行 HEAD に無いことを
  一次資料で確定し、crash 点 6 分類と判定手順を手順書 §3.6 へ、択一 3 案を §5 R-5 へ書いた。
  **残るのは R-5 のユーザー裁定**であり、それが決まるまで official campaign は crash 点 2〜6 で
  死ぬと当該 protocol / env で二度と床値を出せない。
  base: 63a01175ebe07866564662776ad8a7fe5e6e92ee6456270f80c24c550fa43d87
