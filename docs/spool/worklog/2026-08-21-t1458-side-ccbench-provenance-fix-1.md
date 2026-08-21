---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: t1458-side-ccbench-provenance-fix
seq: 1
title: external/ccbench の dirty submodule commit が S8b floor campaign 認証機構と衝突し、調査の末に revert した (docsのみ、branch worktree-t1458-side-ccbench-provenance-fix)
---

## 本文

- 発端は /dev-wave T-1458 起動 (T-1458 の実タスクは別セッションが既に着手済みと roster で
  検出したため、CLAUDE.md の重複検出規律に従い編集せず即停止した — この部分の詳細判断は
  本セッション冒頭の対話に残る)。停止後、ユーザーから `external/ccbench` submodule が
  dirty (`git status` で `M external/ccbench`) だと相談を受け、そこから本 wave が始まった。
- dirty の正体は gitlink pin (511c9538) と実 checkout (ef9328a3、ユーザー本人が書いた
  MOCC 向け correctness trace v2 hook、`#if TRACE` で inert、D16 の trace-hook 分類に
  該当) のズレだった。D16 準拠・祖先関係・inert 性を検証した上で、ユーザー自身に
  `git add && git commit` を実行してもらう形で解消した (commit 09ce607b)。AI (Claude) は
  診断・検証・手順提示のみで commit の実行はしていない。
- `09ce607b` は AI-Agent trailer を持たない (`missing-ai-agent`)。`dev_wave_land.py` の
  land gate がこれを直接呼ぶため、放置すると稼働中の全 wave の land をブロックする状態
  だった。known-violation 台帳へ登録して解消した (Codex role=author、commit 89ab8093)。
- 続けて、`09ce607b` の gitlink 前進が `orchestrator/campaign/s8b_approved.CCBENCH_FULL_SHA`
  との不一致を生み、S8b floor campaign の認証機構を赤にしていることが判明した。
  `test_ccbench_full_sha_matches_real_gitlink` (受動的 canary) と
  `build_protocol_document()` の C4-4 gate (能動的な凍結発行防御、fail-closed) の
  **2つの独立した検査**が影響を受けており、後者は無関係な `test_s8b_protocol_builder.py`
  の10テストまで巻き添えにしていた。
- 対応として3方針を検討した: (a) CCBENCH_FULL_SHA 再承認 + campaign-id golden 53件超の
  連鎖修正、(b) canary だけを既存の `freeze_verification_hold.py` 同型の hold へ切替
  (build_protocol_document の gate は fail-closed のまま維持できるためこちらは有効だが、
  それだけでは(a)の10件が残り不十分と判明)、(c) `09ce607b` 自体の revert。
  ユーザーが並行セッション (T-755 `mocc trace performance validation`,
  MOCC trace hook の当事者) に確認を求め、T-755 から「自分の wave は outer gitlink を
  参照せず commit OID を直接束縛する設計のため revert されても無影響、revert 推奨」との
  回答を得たため、(c) revert (commit 13101ab3) を採用した。MOCC trace hook の正式統合は
  T-755 側の wave で D16 の正規プロセス (izanagi-trace ブランチ経由) を通して後日行う。
- revert commit (`13101ab3`、`git revert --no-edit` で Claude が直接実行) も
  AI-Agent trailer を持たないため known-violation 登録が必要だった。当初
  `MISSING_CODEX_AUTHOR` として登録したが、`check_ai_provenance.py` 自身の自己整合性検査
  (known-violation-stale) が「登録した finding kind が実際の判定と一致しない」と検出し、
  `MISSING_AI_AGENT` が正しい分類 (trailer が一切存在しない) だと訂正した
  (`missing-codex-author` は AI-Agent trailer が存在するが `role=author` 行だけ欠落する
  場合の分類であり、trailer 皆無の場合とは異なる — 台帳内の既存 `_T316_GITLINK` 前例が
  実は `role=integrator` 行を持っていたことを裏取りして気づいた)。commit fdbb549b で
  確定・全走 (`tools/run_tests.py`) = 14183 passed, 96 skipped, 3 warnings, 全緑を確認。
- 本 wave 進行中、CCBENCH_FULL_SHA の赤が fleet 全体の受入をブロックしていたため、
  ListAgents で確認できた並行 17 セッションへ状況共有・方針転換のたびに更新連絡を行った。
  複数セッション (`stage 7 optimization catalog research`, `dev-wave codex failure
  recovery`) が独自に同種の provenance fix を用意していたが、こちらが先行していると
  分かり重複対応を取り下げた。fleet は約2時間ブロックされていたと見られる。
- 受入全走 (`tools/dev_wave_wait.py acceptance`) は1回目、無関係な `test_s8b_approved.py`
  の赤で `child-verdict` 失敗 (rc=70)。原因調査・revert・修正後の2回目で
  `verdict=child-green` を得て land した。

## 次の一手差分
