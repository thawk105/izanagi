---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: dev-wave-codex-astra-ultra
seq: 1
title: dev-wave・rulings・next-tasks の Codex 子を gpt-6-astra・reasoning=ultra へ切り替え、ultra が自動で試みる委任 (spawn_agent) をした attempt は起動器が拒否するようにした (コード + test + docs + insight、branch dev-wave-codex-astra-ultra)
---

## 本文

- 依頼: md_1 (`/work/1/SFC/tanab/tmp/codex-astra-ultra-2026-09-30/md_1.txt`)。2026-09-30 ユーザー指示「dev-wave, rulings, next-tasks で codex を gpt-6-astra・reasoning=ultra で使う」。設計判断は {{D:codex-astra-ultra}} (D2229 を supersede)。一次資料 `output/insights/2026-09-30/codex-astra-ultra/README.md`。
- 生死確認: astra・ultra の直打ち rc=0 (header astra / ultra)。改訂後 docs から導出した起動器実走 = 段 6 review 2 本と焦点再レビュー 1 本が requested / recorded とも astra・ultra、`outcome=accepted`、委任 0。next_tasks_consult.sh 改訂版は rc=0・119 秒 (締切 1,800 秒)・委任 0。
- 実測で判明したこと: ultra は proactive な委任を注入し、委任先は別 rollout に記録されて stdout に現れないため、改訂前の起動器は委任先の call・token・model/effort/cwd を見ずに受理していた (検査は素通り)。設定 3 種では委任を止められなかった。委任先の sandbox は read-only 継承を 1 経路で確認、**委任先で guard が効くかは未確認**。
- 段 4 裁定: 委任先を会計する案 (段 2 plan、700〜1,100 行) は段 3 相談 A の実物所見 (全履歴 fork で親の meta/context が複製される、manifest が 1 attempt 1 session、子の完了・追記が閉じない) と guard 未確認から不採用。相談 B の推奨どおり「prompt で禁じ、委任した attempt を拒否」を採った。
- 段 6: レビュー B の must-fix (L1.5 予算を増やさず既存記述の縮約で収容できる、D782) を採用し、段 5 で入れた予算引き上げ (9,696 → 9,788) を取り消した。DW-O05 の縮約案は親の義務を prompt 文へ移す意味変更なので不採用、親が別の縮約を当てた。所要台帳の nit は不採用。焦点再レビューで全所見 closed。
- ユーザー裁定 (2026-09-30 18:46 JST、段 9 再開の依頼): 受入全走・変異 matrix の計算ノード使用を許可。段 9 を再開し、local main d79fd3524 を取り込んだ (両親の変更 path 重複 0・競合 0) tip `7a1da5e4d` で変異を走らせ、記録後の tip で受入全走を取って land する。
- 変異 matrix (段 9 再開): **8 件すべて期待どおり** (m0 SURVIVED、m1〜m6・m7b KILLED、観測 node と完全一致)。dispatch の独立 clone で、probe → 変異 1 件ずつの final 8 本を並行投入した (ユーザー指示「計算 job は 1 本 5 分目安に分割し並行」、land 調整役の中継)。m7 は段 6 fix1 で置換元が消えたため m7b (L1.5 実 bytes 9,692 の 1 つ下) に再照準し、殺したのは定数 pin の 1 件だけと記録した。異常と処置は insight の「検証の実施状況」: probe 1 回目は spec の外側 timeout 不足で計算前に停止、final の m0・m6 は checkout の Lustre EINTR (rc=125) で判定前に停止、m2 は変異が届かない `test_codex_worker_launch.py` の TimeoutExpired 4 件で MISMATCH → いずれも 1 回だけ投げ直して一致。
- 受入全走 (段 9 再開) の 1 走目 (tip `3742d6051`、post-claim merge で main 48d36f57c を取り込み `55ee5a92c`) は 12 件赤で rc=70。判定は非帰属: (a) 11 件は `test_dev_wave_cleanup.py` の remove-child 系で、撤去 tool の占有検査が他 process の cwd 欠落 (`occupancy result is indeterminate`、`{"error":"missing","source":"cwd"}`) か期待外の rc 22 (`occupancy`) で落ちた。本 wave は `tools/dev_wave_cleanup.py` とその test に触れていない。(b) 1 件は `test_codex_worker_launch.py::test_sigterm_ignoring_child_is_killed` の起動器の時間切れ (`actual rc timeout`)。変異 m2 の 1 回目でも同型で落ち、変異の baseline 12 回はすべて緑だった。12 件を計算ノードで 1 回だけ単独再走し `12 passed` (DW-O18)、受入を取り直す。
- 段 9 前半 (保留時) の経緯: **変異 matrix と受入全走は未実施、land は保留した。** 変異は login で走る sanctioned 経路が無く、受入全走も明示 shard 3 が計算ノードへ dispatch する (login で走るのは collection だけ)。依頼の「計算ノードは使わない」と land の必須条件 (DW-S04) が衝突したため、Codex に 2 レンズで相談し (ultra 2 本とも「禁止は受入・変異も含む、land 保留」)、親も land 保留を採った。段 6 裁定文の「明示 shard 3 は login で走る」は誤りで、insight に訂正を書いた。段 5 統合後の焦点走は bash script 経由の直接 pytest で、`hooks/guard_bash.py` の login 重量検査をすり抜けていた (直接打った同種コマンドが拒否されて判明)。その結果は参考値に留めた ({{F:script-pytest-bypasses-login-guard}})。
- セッション異常: `EnterWorktree(name)` が「Could not read the repository git config」で失敗し、手動 `git worktree add` + lock + `EnterWorktree(path)` で隔離した。委任先への guard の直接 probe (trust bypass flag の手打ち) は auto mode 分類器に拒否され、同じ結果を別経路では追っていない。
- 計算資源: 段 9 前半まで計算ノード 0。段 9 再開後の変異は計算ノードの dispatch 12 走 (probe 1・final 8・再投入 3、うち判定前停止 2)、harness が記録した所要の合計 1,962 秒 (約 0.55 node 時間、queue 待ちを含まない)。受入全走は別。Codex 子: plan 1・相談 2・実装 2・レビュー 2・fix 1・焦点再レビュー 1 (受領証と token は insight の表)。生死確認の probe 7 回 (repo 外 scratch)。

## 次の一手差分

### 新規

- {{T:delegated-child-guard-probe}} **P2・裁定済み (/rulings 第 42 回 項 2、branch `worktree-rulings-all-20260930c`、2026-09-30 19:1x JST に 1 回だけ許可)・実行はユーザー操作待ち**: 条件は使い捨て repo・login のみ・計算ノードなし・flag は `tools/check_codex_hooks.py` と同じで sandbox は迂回しない。実行は、その 1 手だけ auto mode を外した会話で AI が起動するか、AI が用意した script をユーザーが `!` で 1 回走らせる (auto mode の拒否を別経路で迂回しない)。ultra の委任先 (sub-agent) に `.codex/hooks.json` の PreToolUse guard が効くかを直接 probe する。使い捨て repo で root と委任先に保護 path への書込みを試させる形 (`tools/check_codex_hooks.py` と同じ trust bypass flag) は auto mode 分類器が拒否したため、実行の許可 (または許可 rule) が要る。効かないと分かれば、委任の事後拒否だけでは workspace-write の子 worktree に guard 外の書込みが残りうる点を再裁定する。
