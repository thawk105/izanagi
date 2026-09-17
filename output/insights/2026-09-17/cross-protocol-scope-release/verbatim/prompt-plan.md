単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cross-protocol-scope-release

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/parent-brief.md — 親 brief (研究前進・scope・確定済み裁定・不変条件・provisional 裁定 P1〜P4)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/user-utterances.md — 本 wave のユーザー発話 3 件の逐語 (裁定の一次資料)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/worklog-2026-07-27-25.md — 2026-07-27 (25) worklog entry (ユーザー裁定 8 件の原文)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/phase3-2026-07-27-revision.md — phase3.md の 2026-07-27 / 07-31 / 08-01 改訂節 (改訂節の書式の先例)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/phase3-stage7-and-related.md — phase3.md の現行チェックポイント該当行・must 表 S1 行・後続段 7・[T-023]・見送り台帳 [T-167]。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/D579.md — mocc trace-hook は編集面へ開くが変異探索面にはしない。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/D1360.md — 段 7 cross-protocol に残るのは裁定ではなく実装。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/D1373.md — 測定を許す protocol の判定 (規律 2 の関門)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/D1603.md — pin 前進は材料 3 点を揃えてから裁定。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/D2083.md — 非 silo within-run floor の登録と between-run 未実施の必要条件。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/D2104-head-and-item13.md — 今日 (2026-09-17) の一括裁定の冒頭と項 13 (非 silo between-run 実測の保留)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/paper-story-2026-09-17-excerpts.md — 最新論文ストーリーで Silo 固定と C-1 (クロスプロトコル比較) を扱う 5 箇所。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/roadmap-excerpts.md — roadmap 層1・層2 (b1/b2)・§8・§9 (Phase 3 E の順序)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/paper-story-README-after-latest-section.md — paper-story README「最新スナップショット以後に確定したこと」節の現状 (0 件)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/spool-README.md — spool fragment の書式 (decisions / worklog / T 起票)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/roadmap-history-README.md — roadmap 改訂セレモニーの正本 (P4 の判定材料)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cross-protocol-scope-release/docs/phase3.md — 改訂対象 (改訂節の挿入位置、段 7 の発火条件文、見送り台帳の [T-167] 行、8b 節の非 silo 較正登録)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cross-protocol-scope-release/orchestrator/campaign/between_run_floor.py — `BASELINES` と `_protocol_source_has_trace_hook_evidence_only` の所在 (D2083 項 4 の関門)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cross-protocol-scope-release/orchestrator/campaign/source_digest.py — `EVOLVE_BLOCK_SOURCES` / `ALLOWLIST` (D579 の編集面)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cross-protocol-scope-release/tools/check_docs.py — docs 改訂が当たる exact pin・閉包検査の所在。読めなければ即停止。

## 依頼

親 brief の docs-only 裁定パッケージ「silo 固定スコープの解除 (cross-protocol 対応を可能にする)」の plan を file:line 粒度で起草せよ。あなたは read-only で、書込み可能な tmp が無いので pytest の実走は不要 (静的検査でよい)。テスト・check_docs の実測は親が行う。repo 内の path は上の worktree のものを使う。

**背景 (親が段 1 で確定した事実):** 2026-07-27 のユーザー裁定 (1)「スコープを Silo ベースに固定、複数プロトコルから選ばせる問題設定は当面採らない」は phase3.md 2026-07-27 改訂として生きており、失効宣言は無い。2026-08-11 裁定で cross-protocol 比較の成立方法 (trace-hook 移植、初手 mocc) は確定 (D1360)。実装は 2026-09-02 以降に tictoc/cicada の genome 空間登録・非 silo 較正 4 件・within-run floor 登録 (D2083) まで進んだが、between-run floor は D1373 の関門 (mocc hook が現行 pin 511c9538 の祖先でない、tictoc は BASELINES に無い) で未実測、性能比較 0 件、D579 で mocc は変異探索面外。今日の D2104 項 13 は「主経路は現行 pin で設計」を理由に非 silo between-run 実測を保留し「再開を求めるときは pin 更新の再承認として別途諮る」とした。ユーザーは本 wave で「論文のパンチが弱いのでクロスプロトコル対応を可能にしておきたい。CCBench 側へ近年の新手法を追加するのも優先度が高いかも」と述べた。

**親 brief の provisional 裁定 P1〜P4 と不変条件を前提に、次を書け:**

1. **事実の裏取り (file:line):** 親 brief が述べる事実のうち次を repo の現物で確認し、誤りがあれば訂正せよ — (a) tictoc/cicada の genome 空間登録 (登録箇所の file:line と、それを記録した D または T 番号)、(b) `between_run_floor.py` の `BASELINES` の鍵集合と D1373 述語の所在行、(c) `source_digest.py` の EBS/ALLOWLIST に mocc が含まれる行、(d) 層 3 の floor 照合キーに protocol 軸が無いこと (D1360 の実測が今も真か、file:line)、(e) 現行 CCBench pin (gitlink SHA) と mocc hook branch 名。
2. **docs 改訂一覧 (file:line 粒度):** phase3.md への「2026-09-17 改訂」節の挿入位置と本文骨格 (2026-07-27 改訂 (1) の「当面」終了の射程 — 何を解除し何を据え置くか、段 7 発火条件の付け替え先、D2104 項 13 との関係、roadmap 本体を改訂しない旨)、段 7 項の発火条件文の書き換え箇所、見送り台帳 [T-167] 行の状態語、paper-story README「最新スナップショット以後に確定したこと」への 1 項 (C-1 の位置づけ変更を指す一次資料)。**各改訂が `tools/check_docs.py` のどの exact pin・閉包検査に当たるか**を静的に列挙せよ (当たるなら回避の形か、pin 更新の要否)。
3. **spool fragment の骨格:** decisions 1 件 (見出し案・決定・理由・却下案)、worklog 1 件 (見出し案・記録項目)、T 起票 (下記 4 の鎖)。spool README の書式に従い、採番は暫定 (T/D 番号は fold が振る) と明記。
4. **pin 非依存で今から進められる準備の T 鎖:** 各 T について 目的・完了判定・依存・実アンカー (file:line または成果物 path)・pin 前進を要するか (要/不要) を表にせよ。候補: (i) D1603 材料 3 点 (候補 commit、D297 同一性検査の結果、承認済み定数への波及範囲) を揃える wave — 材料 (2) を出す既存 tool の所在、(ii) tictoc の trace-hook 移植 (段 7 Group B (e)(f)) を submodule branch 上で行う wave、(iii) `between_run_floor.py` の BASELINES を protocol 汎用にする (tictoc 追加) wave、(iv) mocc を EVOLVE_BLOCK hole (変異探索面) にするための auditor-live 相当の機械実証設計 (D579 が要求)、(v) 層 3 floor 照合キーへの protocol 軸、(vi) CCBench への近年手法追加 (ユーザー方向 B) の候補選定を文献調査 (D1760 / D1931 で停止中) の再開として起票する形。**pin 前進そのものは T-167 の再承認 (D2104 項 13) として独立の裁定項目に分ける。**
5. **P1〜P4 への異議:** それぞれ「同意 / 異議 (根拠 file:line)」で答えよ。特に P2 (pin 前進が主経路の凍結物を無効化するか) は、事前登録・campaign.lock・identity 層のどの file が CCBench pin SHA を束縛しているかを grep で列挙して答えよ (見つからなければ「見つからない」と書く)。P3 (silo+mocc で言える主張の文面) は paper-story の主張階層 (評価器 / システム / LLM 固有 / 無人自律) のどこに効くかで答えよ。
6. **リスク:** phase3.md の byte 予算や exact pin、D2104 項 13 (今日の裁定) を同日に覆す記録の書き方 (「推奨通り」一括承認の 1 項をユーザーの直接発話で上書きする旨の明記)、paper-story 凍結版を書き換えない規則、spool fold との衝突。

予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式

Markdown。先頭に `## 総括` (10 行以内: 訂正した事実の数、改訂 hunk 数、T 鎖の本数、pin 前進を要する T の数、親 brief への異議の有無)。続けて上の 1〜6 を見出しにして書く。file path は worktree の絶対 path または repo 相対 path で書き、行番号を付ける。
