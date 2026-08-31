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
- **受入全走は本 wave と無関係の決定的赤で止まり、land していない。** tip `f3093622b` の受入
  (01:18 JST 投入) は shard 3 本のうち shard-0 だけが赤で、rc は 16
  (`dispatch-attestation-missing` / `acceptance shard report finalization failed`) だった。
  内訳は failed 4 + errors 1。failed 4 は `orchestrator/tests/test_codex_reasoning_ab.py` の
  `_REAL_ROLLOUT` で、repo 外の絶対 path
  `/home/SFC/tanab/.codex/sessions/2026/07/29/rollout-2026-07-29T15-49-14-...jsonl` を読む。
  **この path は Codex のセッションログ・ローテーションで消えた** —
  `~/.codex/sessions/2026/` の mtime は 2026-09-01 00:54:20 JST で、`07/` ごと無い。
  errors 1 は `test_s8c_preregistration_predicates.py` の real-repo fixture lock の
  `BlockingIOError` (並行 wave との競合)。
- **決定的であることを単独走で確認した。** 該当 2 test を焦点走 (request `963131.nqsv`、10 秒)
  したところ同じ `FileNotFoundError` で赤。`find` で `/work/1/SFC/tanab` と `/home/SFC/tanab`
  を探したが当該 rollout の複製は 1 件も残っていない。本 wave の差分は docs 4 file の追加だけで、
  これらの test にも `tools/codex_reasoning_ab.py` にも触れていない。
- rc が 1 でなく 16 のため `non-attributable-only` の受領証経路も使えない。`DW-O18` の
  「決定的赤は main 既存 F を証拠に hold へ登録、F 不在なら登録せず裁定送り」に従い、
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
- **レンズ B の BLOCKER 2 件を親の実測が上書きした。** (1)「依存閉包は 24 test 関数」は
  推測で、受入の failure digest が `failures=5 selected=5 omitted_failures=0` と切り捨てゼロを
  示し、fixture 利用テストの代表 1 本の焦点走は skipped だった。skip の理由は原本の不在ではなく
  既存の `IZANAGI_GROWTH_HOLD_V1` (`ruling=2026-08-12 rulings 第 3 束`) である。被害は
  guard を持たない 2 関数 4 item に限られる。(2)「案 1 に使える既存 hold は無い」は契約の
  批判としては正しいが、**形の先例は同じ file 内で現に動いていた** — 裁定 ID・exact node id・
  解除条件・`correctness_gate`・**barrier nodes の名指し**を持つ機械可読 JSON である。
  新しい axis と field 契約の追加は要るが、機構をゼロから設計する必要は無い。
- **レンズ A が親の見落としを 1 件出した (BLOCKER)。** `prompt_source` は `sha256` しか literal
  固定されておらず `replacements` が固定されていない。`replacements` を {0,9,10} の外へ変えると
  parametrize 3 case すべてが負例になって通る。hold を入れるだけではこの穴が残るため、
  同じ変更単位で `prompt_source` の dict 全体を固定する。
- 裁定は案 1 — T-181 の凍結 literal は 1 bit も変えず、原本を読む 2 関数を素の skip でなく
  明示 hold にし、失うのは「SHA `9b90d510...` の 16 行目が golden だった」の**再検証可能性だけ**
  と明記する。production の replacement 検査は合成 rollout で hermetic に走らせ続ける。
  原本 bytes を回収できたら repo 内へ固定して hold を解除する。

## 次の一手差分
