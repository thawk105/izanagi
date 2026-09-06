単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s4-adjudication.md

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s4-adjudication.md` — 親の段 4 裁定。**4 節 (plan v2 — C1a、規模上限) と変異事前登録 M1〜M12 が受入基準の正本**
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/prompt-s5-launcher.md` — 実装子へ渡した契約
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/artifacts/t1851-unit-c/s5-launcher.md` — 実装子の完了報告。**自己申告であり検証対象**
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s5-launcher.patch` — 実装差分の全文
5. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/artifacts/t1851-unit-c/s3-lens-b.md` — 段 3 レンズ B (所見 7 の到達可能性 matrix、所見 9 の fake 契約、所見 13 の focus 集合)
6. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/focus-0.log` — 実装前 baseline (38 file、4,717 passed / 16 skipped)

**統合後のコードは `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a` にある (未 commit の作業 tree)。所見はここの現物で裏を取れ。**

## 依頼

あなたはレビュー B である。**波及・test の実効性・fake と実体の乖離・変異の帰属**を検査する。実装子の報告を信じず、現物とつき合わせろ。

## 検査の軸

1. **所有外への波及。** `s8b_attempt_registry.py` の launcher import (`launch_floor_attempt` 以外の symbol を参照していないか)、`test_ccbench_spawn_sites.py:212` の pin、`reserve_attempt_slot` の `consumption_marker` 引数の実在と型、他 test file で launcher の public symbol (`OpenedFloorAttempt.post_probe` / `open_error`、`launch_floor_attempt(classification_authority=...)`) を参照する箇所 (`git grep`) を全件列挙せよ。
2. **fake と実体の乖離。** test の `_Token` が `ScalePoint` 同形 (`throughputs` / `notes` / `rep_observations` attribute、open 時に sink を更新) か、fake capture が launcher 私有 sink を観測するか、`_RecorderRegistry` の `reserve_attempt_slot` が `consumption_marker` kwarg を受け取って記録するか。real adapter を通す node (`test_real_adapter_creates_and_exactly_reuses_complete_genesis`) が新 signature で v1 + None を通すか。「両層 stub で機構を通らない緑」の形が無いか。
3. **test の実効性。** 各新設 node について、対象 gate を外したときにだけ赤になるか (他の gate に先に遮られないか) を静的に判定し、変異 M1〜M12 ごとに「KILLED が期待できる / 冗長 gate に遮られる / node 不在」を表にせよ。期待値の弱体化 (緩和・skip・削除・反転) が 1 件でも無いか。揮発 payload (hash 等) の焼き込みが無いか。
4. **規模上限。** production +150〜220 / −40、test +250〜400 を patch の現物で数え、超過なら差し戻し対象として明記せよ。
5. **到達可能性 matrix (レンズ B 所見 7)。** `probe_after=None` ⇔ pre 競合、opened ⇒ sink 長 = reps、failure ⇒ measurement None、が launcher の現物で成立するか。成立しない組合せが `OpenedFloorAttempt` に載りうるなら列挙せよ。
6. **親の focus 走の集合。** 本 patch で赤になりうる所有外 test (静的推定) を列挙し、baseline 38 file に含まれないものがあれば名指しせよ。
7. **実装子の報告の自己申告**のうち、現物と食い違う点 (行数、node 数、実走の有無・範囲、「不変」の主張) を全件列挙せよ。

## 出力形式

所見ごとに `所見 N` の見出しを付け、(a) 何が問題か、(b) 現物の file:line、(c) real なら放置時に成果物 (certified 選択・レポート・台帳) の値・受理集合・参照がどう変わるか 1 行、(d) 修正案 (所有 file を明記)、を書け。各主張に [実測] / [推測] を付けろ。**blocker / must-fix / nit** を分けろ。変異 M1〜M12 の帰属表を別節に置け。

## 制約

- 読取専用である。pytest の実走は要求しない。静的検査でよい。実測は親が行う。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力へ結合文字 U+0300〜U+036F を使わない。
- 出力の最後に `## 総括` 節を置き、blocker / must-fix / nit の件数、規模の実測、GO / NO-GO の判定を 10 行以内で書け。
