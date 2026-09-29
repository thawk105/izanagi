---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-gen-opt-literature-cards
seq: 1
title: 並行性制御の最適化の文献カード化 — 本集合 49 本 295 枚を CCBench の有無と Silo への入り方で分け、段 A の試し候補を選んだ (insight のみ、branch dev-wave-gen-opt-literature-cards)
---

## 本文

- 依頼: 新規最適化の創出へ活動範囲を広げる並行 wave の md_2 (`/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_2.txt`、共通指示 `common.txt`)。背景はユーザーの相談 (2026-09-29) と、親セッションの提案の (a) への同意「この形に改めて良い」(`user-verbatim.txt`・`proposal.md`)。対象の句「並行性制御の最適化の文献カード化」を含む item は台帳に無かったので、新規 item として次の段を登録した。
- 正本: `output/insights/2026-09-29/gen-opt-literature-cards/README.md` (§0 が結論、§6 が段 A の候補、§7 が横断の注意、§11 が段 6 の訂正)。カードの正本は同 dir の `cards.json` (本集合 295 枚 + 包含条件外の参考 4 枚)。
- 結論の要点: 段 A の本枠 (CCBench に無い・関数単位の空間 v1 で書ける・今の検査器で見られる・YCSB で作れる) は、本集合 295 枚を判定した範囲では 2 つだけ (上限つき施錠待ち、乱数つき指数 backoff)。根拠の値は 2PL のもので、Silo の commit 時の施錠での効果は未測定。関数方策ループの段階 F の LLM 候補が既に両方を合わせた形を書いている。文献の最適化を正しく入れることを示す本命は空間を広げる別枠 (開始前の先送り、BCC、競合度順の施錠)。
- 横断の発見: CCBench の YCSB は書き込みで値が実質変わらない (`include/ycsb.hh`)。値の一致で検証を通す型の最適化は YCSB で効果が workload の作りの産物になりうる (正しさ関門 md_3 への申し送り)。CCBench の説明と実装の食い違い (`cmake/Options.cmake` の backoff の説明、ss2pl README の timeout、MOCC の未使用定数ほか) は insight §7 に記録のみ (上流への還元は人間の判断)。
- 段 6: read-only レビュー 1 本が NO-GO で所見 8 件 (must-fix 6・should-fix 2)。全件 real と裁定して直した (BCC の YCSB の値の取り違え、TCM の v1 扱い、TicToc の present 訂正の取り消し、Freitag 2022 を包含条件外の参考へ分離して本集合を 295 枚・49 本に、表・図番号の無い性能の数値 103 文の判定と是正、題名だけで決められない R3 の 22 件を要旨で再判定、施錠待ちの根拠が 2PL の値であることと「3 つ目は無い」の範囲の明記)。焦点再レビュー 1 本は前回 7 件 closed・1 件 partial、件数の再計算は 1 点を除き一致、新しい should-fix 3 件 (R3 見直しの内訳、対照方策の言い方、Ding の比較文) を real と裁定して直した。3 巡目は起動していない。
- 記録前の三軸語走査 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`) は rc=1 で、hit は 2026-09-16 の既存 file 3 件 (`output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/` の journal・manifest・result) だけ。本 wave の file の hit は 0 件。
- 受入全走 1 回目 (2026-09-29 12:37〜12:46 JST、tip 98987e693 = local main d4db28a94 を取り込んだ後) は 27,990 passed・3 failed。赤 3 件はすべて `orchestrator/tests/test_dev_wave_cleanup.py` (`test_remove_child_already_clean_with_receipt`、`test_remove_child_checks_initialized_submodule[default-branch-reflog]`、`test_remove_child_detached_nonancestor_skips_bundle`) で、assertion 本文はどれも占有走査の `occupancy result is indeterminate ... issues=[{"error":"missing","source":"cwd","pid":...}]` (走査中に無関係の process が消えて cwd を読めなかった)。`tools/dev_wave_cleanup.py` とその test は wave の開始点から tip まで変更が無く、本 wave の差分 (insight と spool の文書だけ) から到達しない。同じ tip で 3 件を単独再走すると 3 passed (再現せず) だったので非帰属と判定し、受入を 1 回だけ再走した。その前の 1 回 (11:29〜11:32) は main の前進との競走 (postcheck、テスト未実行)。
- セッション異常: EnterWorktree (name 指定) が "Could not read the repository git config to neutralize filter drivers" で失敗し、手動の `git worktree add` + lock + EnterWorktree(path) で回避した (並行 wave が多く checkout に約 10 分)。OpenAlex の 1 回目の走行で 6 本が HTTP 429 になり無効とした (登録の改訂 1)。親が登録の改訂の時刻を推定で書き、mtime で気づいて訂正を追記した (F1 の再発)。原典読みの子の 1 本が Polaris の source を第三者の fork から取っていた (原典 repo と SHA-256 一致を親が確認、{{F:subagent-source-from-fork}})。親が要旨の work ID を 1 件打ち間違えて無関係の論文を取った (判定に不使用)。
- エージェント工数: 原典読み Claude sonnet 10 本、CCBench 照合 Claude sonnet 3 本 (J 班は親)、分類 Claude opus 4 本、数値の是正 Claude opus 1 本、段 6 の read-only レビュー Codex 1 本 (gpt-6-sol・medium、42 call・462 秒) と焦点再レビュー Codex 1 本 (同、15 call・230 秒)。計算ノードは使っていない。

## 次の一手差分

### 新規

- {{T:gen-opt-stage-a-trial}} **P2・新規**: 並行性制御の最適化の文献カード化 (`output/insights/2026-09-29/gen-opt-literature-cards/`) の結論を受けて、段 A の試しを起票する。本枠 2 つ (上限つき施錠待ち、乱数つき指数 backoff) は、文献が推奨する機構を v1 用の更新則を明記して人が書いた名前つき方策を対照として安く作れるが、段階 F の LLM 方策とほぼ重なる。本命は別枠 (開始前の先送り = 予定 key 集合の観測と開始前の口、BCC = validation と共有状態、競合度順の施錠 = 施錠順の比較に TID word) で、どれを開くかは正しさ関門 (md_3) と roadmap の改訂 (md_1) に従属する。計算の試算は insight §6.4 (本枠 2 候補 × workload 3 点の pair で約 2.5〜2.6 node 時間、ユーザー確認の対象)。
