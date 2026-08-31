---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: worktree-dev-wave-stranded4-recheck-20260901
seq: 1
title: 取り残し branch 4 本を base main で再判定し、3 経路すべてで着地済みと確定して取り込み 0 件で閉じた (docs のみ、branch worktree-dev-wave-stranded4-recheck-20260901、実装面の差分ゼロにつき変異 matrix は DW-S04 の免除)
---

## 本文

ユーザー起票。「main へ未着地のまま残っている branch 4 本を回収する」。**取り込みは 0 件で閉じた。**
一次資料は `output/insights/2026-09-01_stranded4-branch-recovery/`。

- **依頼の前提 (4 本が未着地) を段 1 前の実測が覆した。** 4 本とも内容は既に main にある。
  同じ判定は 2026-08-29 の wave (archive エントリ 1094) が下していたが、本 wave はその結論を
  引用せず base main `24014bdb2` で独立に再導出して一致を確認した。
- **着地判定の経路は 3 つあり、本件では 3 つとも実際に使われていた。** (1) canonical へ fold し
  `docs/spool/FOLDED.md` に content_sha256 の受領証が残る、(2) archive worklog へ別文言で吸収され
  受領証にも canonical の逐語にも一致が出ない、(3) insight の `sources/` へ原文 blob として保存され
  canonical にも受領証にも現れない。**1 経路だけを見た判定は 4 本とも「未着地」と誤る。**
  経路 3 は本 wave が 2 度目の往復の末に見つけた。
- **未着地量は fork 点からの file 閉包で測った。** commit が触る file だけを数えると、競合解消で
  内容を入れた merge を取りこぼす。`git diff --name-only $(git merge-base main <branch>) <branch>` で
  19 / 8 / 9 / 1 file を得て、distinct 22 path を 1 本ずつ blob 照合した。三点 diff の
  file 数・行数は根拠に使っていない。
- **実装面はゼロだった。** T-080 process-memo grouping の追加 `2ffb32a0e` と撤去 `1bafd884a` は
  対象 2 file について差し引きゼロで、fork 点からの file 閉包に test file が 1 本も現れない。
- **取り込まない理由は「既に在る」だけではない。** `6f5de08ce` の insight README を取り込むと
  main 側の後継 `d1b9a2a75` が前身 `c778863e1` へ退行する。4 branch の merge は、エントリ 1081 が
  「source tip・旧 merge・実装・撤去・停止 tip を非祖先のまま保つ」と記録した意図を崩す。
  `df20d3631` の逐語 land は D1149 で決着済みの裁定待ちを live state へ戻し、かつ断片が持つ
  `[T-1273]` への更新操作は同 ID が active でないため fold が `transition-target` で拒否する。
- **file 閉包 22 path のうち、main のどの path にも無いのは 2 blob だけだった。**
  停止した reconciliation の spool 断片 `bee4d47fd` と、その insight README `c778863e1`。
  エントリ 1081・1094 の先例に従い原文のまま insight の `sources/` へ保存した。
  **廃案となった手順の記録であって正本ではない**と明記し、記述にある merge commit
  `60c758a86` `8b677a197` が main の祖先でないことを添えた。`docs/spool/` の外に置くため
  fold の入力にはならない。
- branch の削除はユーザー指示に従い 0 件。4 本とも ref のまま残した。
- **受入全走は本 wave と無関係の決定的赤で止まり、land していない。** 赤は
  `orchestrator/tests/test_codex_reasoning_ab.py` に集中し、**26 件 (21 error + 5 failed)** である。
  原因は repo 外の絶対 path
  `/home/SFC/tanab/.codex/sessions/2026/07/29/rollout-2026-07-29T15-49-14-...jsonl` の消失で、
  **Codex のセッションログ・ローテーション**による (`~/.codex/sessions/2026` の mtime =
  2026-09-01 00:54:20 JST、`07/` ごと不在)。`find` で `/work/1/SFC/tanab` と `/home/SFC/tanab` を
  探したが複製は 1 件も無い。本 wave の差分は docs 4 file の追加だけで、これらの test にも
  `tools/codex_reasoning_ab.py` にも触れていない。**赤は本 wave に帰属しない。**
- 内訳。21 error は fixture setup 段階の
  `ValidationError: session ... rollout count is 0, expected 1` (`tools/codex_reasoning_ab.py:633` の
  `_find_rollout`) が `_prepare_snapshot_case → derive_independent_golden` 経由で波及したもの。
  5 failed のうち 4 は直接 `_REAL_ROLLOUT` を読む 2 関数 (`FileNotFoundError`) である。
  決定的であることは焦点走 (request `963131.nqsv`、10 秒) で確認した。
- **件数と hold について、本 wave は最初 2 つの誤りを記録し、後から実測で訂正した。**
  初版は「被害は 2 関数 4 item」「fixture を使う 21 関数は既存 hold で skip される」と書いた。
  どちらも誤りである。(a) 「4 item」の出所は受入 shard-0 の failure digest
  `failures=5 failed=4 errors=1 selected=5 omitted_failures=0` だが、**その shard は
  `acceptance shard report finalization failed: ShardError` で中断しており、全 node を
  実行し終える前の会計だった。** `omitted_failures=0` が「完全な会計」に見えるのが罠で、
  実際には digest 自身の選択に切り捨てが無いと言っているだけである。(b) 「21 関数が hold」は
  fixture 利用テストを 1 本だけ焦点走し、それが skip されたのを 21 関数へ全称化したもの。
  選んだ 1 本がたまたま held 2 件のうちの 1 件だった (抽出の偏り)。
- **訂正の根拠は自分の worktree での全 file 走である** (base main `24014bdb2`、
  request `963575.nqsv`、26 秒)。`5 failed, 598 passed, 2 skipped, 21 errors` /
  `IZANAGI_FAILURE_DIGEST_ACCOUNT failures=26 failed=5 errors=21 selected=10 omitted_failures=16`。
  他 8 セッションの独立観測と一致した。`IZANAGI_GROWTH_HOLD_V1` の発火は **2 node だけ**で、
  `_HOLD_ROWS` は静的な tuple literal、適用側 (`growth_test_holds.py:744-748`) は
  filename の純粋な filter である。**hold 集合は worktree 非依存で全環境同じ 2 件**であり、
  `hold_axis="output_artifacts"` は hold を作った理由のラベルであって発火条件ではない。
- **rc=16 は撤回しない。** 本走行の `IZANAGI_ACCEPTANCE_ATTEMPT_V1` は
  `"normalized_child_rc":16` / `"raw_child_rc":16` / `"reason":"dispatch-attestation-missing"`、
  終端は `stage=acceptance-command rc=70 source_rc=16`、shard-0 の `result.json` は
  `"child_rc": 16` である。別セッションの 05:47 の走行が `raw_child_rc=1` だったのは別走行で
  矛盾しない。**誤っていたのは値ではなく、それを blocker の intrinsic な性質として一般化した点**で、
  rc=16 は shard が report finalization に失敗した結果であり、完走すれば rc=1 になる。
- `DW-O18` の「決定的赤は main 既存 F を証拠に hold へ登録、F 不在なら登録せず裁定送り」に従い、
  hold は登録せず裁定パッケージとして返して `DW-STOP` で停止した。
- **ユーザー指示「codex と相談して決めて」に従い read-only codex 2 レンズへ並列相談し、
  親が段 1 で書いた推奨を撤回した。** 逐語は `verbatim/s3-consult-a-sol.md` と
  `verbatim/s3-consult-b-luna.md`、裁定は `adjudication-rollout-blocker.md`。
  両レンズとも `check_codex_output.py` rc=0。所要は 1 本あたり約 4 時間。
- 親の当初推奨「現存 rollout へ pin を張り替える」は不採用。両レンズが独立に退けた。
  レンズ A は「規律 7 の第一 bullet 単独では禁じない。効くのは『記録はやめない』と
  『過去の判定は追記でのみ訂正する』の 2 条」とし、**親の禁止根拠の当て方が拡大解釈**
  だったと指摘した。結論は同じだが理由づけが誤っていた。レンズ B は、POS hash を変えると
  manifest 全体の SHA が変わり 33 production 関数の既定 manifest と全 receipt の
  `task_manifest_sha256` が連鎖し、既存 digest 成果物が `_require_task_manifest_sha256` に
  拒否されること、`snapshot.numstat` が rollout から導出されない別の frozen literal である
  ことを示した。**張り替えは局所修正ではなく別測定である。**
- **親は「レンズ B の BLOCKER 2 件を実測で上書きした」と一度書いたが、これが誤りだった。**
  (1)「依存閉包は 24 test 関数」を親は推測として退けたが、**レンズ B が正しかった。** 実測は
  21 error + 5 failed = 26 件で、閉包の見積もりとほぼ一致する。親が上書きの根拠にした
  `failures=5` は中断した shard の会計であり、**悪い測定で正しい推論を否定し、しかも
  「実測が推測に勝つ」という形で権威づけした。** 数字が付いていることは母集合が正しいことを
  意味しない (`DW-O18` の精神と同型の誤り)。(2)「案 1 に使える既存 hold は無い」は契約の
  批判として正しく、親の指摘は否定ではなく補足だった — 形の先例 (裁定 ID・exact node id・
  解除条件・`correctness_gate`・barrier nodes の名指しを持つ機械可読 JSON) が同じ file 内で
  動いており、機構をゼロから設計する必要は無い、という点だけを足す。
- **レンズ A が親の見落としを 1 件出した (BLOCKER)。** `prompt_source` は `sha256` しか literal
  固定されておらず `replacements` が固定されていない。`replacements` を {0,9,10} の外へ変えると
  parametrize 3 case すべてが負例になって通る。hold を入れるだけではこの穴が残るため、
  同じ変更単位で `prompt_source` の dict 全体を固定する。
- 親の裁定は案 1 だった — T-181 の凍結 literal は 1 bit も変えず、原本を読む 2 関数を素の skip でなく
  明示 hold にし、失うのは「SHA `9b90d510...` の 16 行目が golden だった」の**再検証可能性だけ**
  と明記する。production の replacement 検査は合成 rollout で hermetic に走らせ続ける。
- **この裁定は採用されなかった。** ユーザー指示により裁定 ID をユーザーへ直接求めず並行セッションへ
  引き渡したところ、修正の所有権は `compiler manifest path binding` にあり実装済み、
  **hold は使わない**方針だと `parallel session red triage` が回答した。理由は `FlakyTestHold` が
  `green_observation` と `green_run_count >= 1` を必須とし、一度も緑でないこの赤は正直に
  登録できないためである。裁定 ID も不要になった。所有者側は修正だけで受入 attempt 2 が
  `1 failed / 19043 passed / 92 skipped` になり赤 26 件が消えたと報告している。
  **以上は peer の報告であり本 wave は独立検証していない。** 本 wave が確かめたのは、
  記録時点の local main が `24014bdb2` で**修正がまだ着地していない**ことだけである。
- レンズ A が出した `prompt_source.replacements` の穴だけは件数の議論と独立に有効で、
  恒久タスクへ引き渡された。本 wave の正味の貢献はこの 1 点である。

## 次の一手差分
