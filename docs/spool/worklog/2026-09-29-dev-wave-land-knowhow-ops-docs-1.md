---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-land-knowhow-ops-docs
seq: 1
title: land 調整で分かった 3 点 (他 wave の撤去は land を落とさない・受入後の commit と前進 merge の競合・共有文書の同位置追記) を dev-wave の運用文書 DW-O11 / DW-O12 へ短く反映した (docs のみ、branch dev-wave-land-knowhow-ops-docs)
---

## 本文

- 依頼: 共有 repo の git 操作の手入れ (並行 3 wave) の md_3 (`/work/1/SFC/tanab/tmp/git-maint-2026-09-29/md_3.txt` と共通指示 `common.txt`、land 調整役 session が作成)。台帳の「次の一手」に対象項目は無かったので、完了分は本エントリで記録し、残りを新規項目にした。
- 事実は `tools/dev_wave_land.py` で確かめてから書いた。land の前後比較 (`_worktree_snapshot`) が見るのは自 wave の木と、着地差分の path (`_target_paths`) に重なる登録木だけで、他 wave の撤去では rc=21 にならない。tested tip の後ろに通るのは main を取り込む 2 親の前進 merge だけで、通常 commit と、機械 merge の再演が非 clean になる merge (手で競合を解いた merge) は rc=23 で拒否される (`_forward_main_merge_topology`・`_reject_nonclean_replay`)。
- 置き場の判断: 依頼は「land / 受入の節」だったが、段 9 で必ず読む DW-O23 は L1 層に属し、L1 層は 10,619 / 10,625 bytes で入らない。DW-O12 (段 7 で読む) に「前進 merge の競合は abort し解いた tip で再受入」と「共有文書の追記位置は稼働 wave と分ける」を、DW-O11 (ファイル削除、worktree 登録残置の影響を扱う) に撤去の項を置いた。項目 2 の前半 (記録 commit は受入の前) は DW-O12 に既存の文があったので足さず、言い回しを縮めて残した。DW-O12 は単節予算 1000 bytes ちょうどに収めるため、既存文を意味を変えずに詰めた (D730 / D782 の「既存記述の削減を先に試す」)。
- 項目 3 の「段 1 で見る」は、段 1 で必ず読む DW-S01 (`docs/dev-wave/core.md`) が本 wave の所有外で L1 層も満杯のため、そこには入れていない。代わりに背景 job + worktree 隔離の wave が開始時に読む DW-O20 に「共有文書追記は段1で`DW-O12`。」を置き、DW-O12 に「段1で稼働waveの編集と重なれば追記位置を分ける」と書いた。
- 並行 session (land 調整役) から 17:5x JST に追加の事実を受けた: 撤去の途中で `gitdir` を欠く管理 dir が残ると、他 wave の受入で `orchestrator/tests/test_t810_coordinator.py` の 3 件が `cannot read worktree registration: file is absent` で落ちる (t-2288 wave の報告)。`tools/pegasus/t810_coordinator.py` の `repository_roots_from_git_identity` が共有 git dir の worktrees 配下を全走査し `gitdir` の無い管理 dir で失敗することは読んで確かめた。受入での発生そのものは報告に依る。DW-O11 に「受入の走行中は撤去を避ける」として入れた。
- セッション異常 (実害なし): `EnterWorktree` の名前形が filter driver の読取エラーで失敗し、手動の `git worktree add` (4 分 53 秒) の後に path 形で入った。add の間に main が 8 commit 進み、開始 gate が `HEAD != local main` で rc=1 になったので `--ff-only` で揃えて rc=0 を得た。review 子の 1 回目は operations.md が未 commit で `working tree が authority commit と異なる` の rc=2 で即終了し、commit してから新しい job-id で投げ直した。
- 段 6 の read-only review 1 本 (事実照合と過剰・削除の 2 レンズ) は NO-GO で must-fix 3・should-fix 3 を出した。採用: rc=21 の断定を着地差分に重ならない撤去へ限定、撤去を絞る理由 (Lustre 混雑) と受入の走行中は避けることを別文にして「赤にしうる」へ弱めた、段 1 で気づけるよう wave 開始時に読む DW-O20 に DW-O12 への参照を足した、rc=23 の範囲を tested tip 後に限定、「競合しうる」、縮約で落とした「dispatch した」を戻した。不採用: 「spool 経由」の選択肢 — 3 台帳は既に spool 必須で、docs/phase3.md には spool の経路が無く、書いても選べないため。must-fix 2 の「依頼文は理由を Lustre だけとしている」は、依頼文の作成者 (調整役) が依頼の後で受入の件を足すよう求めたので、内容は残して書き分けた。焦点再レビュー 1 巡目は GO (6 件中 5 件 closed、spool は親の不採用理由を妥当として partial)。新規 should-fix 1 件 (段 1 で稼働 wave の編集と重なるかを見てから分ける) は提案文どおりの局所修正なので、2 巡目は起動せず親が照合して閉じた。
- 予算の原資: DW-O12 は既存文の冗語 (「実際に」「記述」「目的」「突き合わせる」→「照合する」など) を削り、DW-O20 は全角括弧を半角にし「に従い」→「で」「取り込み」→「取込」とした。最終の可視 byte 数は DW-O11 997、DW-O12 998、DW-O20 994 (上限 1000)。L1・L1.5 層の合計は変えていない。
- エージェント工数: Codex review 1 (1 回目は起動前に rc=2、上のセッション異常)・focus 1 (いずれも read-only)。実装子なし (実装面の差分ゼロのため変異 matrix は免除)。

## 次の一手差分

### 新規

- {{T:land-knowhow-docs-rest}} **P3・新規**: land 調整の知見の運用文書反映の残り。段 1 で必ず読む `DW-S01` に「触る共有文書 (docs/phase3.md 等) を稼働中の他 wave も触るかを見る」を、段 9 で読む `DW-O23` に「他 wave の撤去は land を落とさない」の要点を置くか判断する。現状は背景 job の wave だけが開始時に DW-O20 から DW-O12 を辿る。いずれも L1 層 (残り 6 bytes) の予算に阻まれ、D730 に従い既存記述の削減で原資を作れなければ実施しない。現行の記述は `docs/dev-wave/operations.md` の DW-O11・DW-O12・DW-O20。
