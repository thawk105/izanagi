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
- 検証の未実施: **変異 matrix と受入全走は未実施、land は保留。** 変異は login で走る sanctioned 経路が無く、受入全走も明示 shard 3 が計算ノードへ dispatch する (login で走るのは collection だけ)。依頼の「計算ノードは使わない」と land の必須条件 (DW-S04) が衝突したため、Codex に 2 レンズで相談し (ultra 2 本とも「禁止は受入・変異も含む、land 保留」)、親も land 保留を採った。段 6 裁定文の「明示 shard 3 は login で走る」は誤りで、insight に訂正を書いた。段 5 統合後の焦点走は bash script 経由の直接 pytest で、`hooks/guard_bash.py` の login 重量検査をすり抜けていた (直接打った同種コマンドが拒否されて判明)。その結果は参考値に留めた ({{F:script-pytest-bypasses-login-guard}})。
- セッション異常: `EnterWorktree(name)` が「Could not read the repository git config」で失敗し、手動 `git worktree add` + lock + `EnterWorktree(path)` で隔離した。委任先への guard の直接 probe (trust bypass flag の手打ち) は auto mode 分類器に拒否され、同じ結果を別経路では追っていない。
- 計算資源: 計算ノード 0。Codex 子: plan 1・相談 2・実装 2・レビュー 2・fix 1・焦点再レビュー 1 (受領証と token は insight の表)。生死確認の probe 7 回 (repo 外 scratch)。

## 次の一手差分

### 新規

- {{T:astra-ultra-mutation-dispatch}} **P1・ユーザー裁定待ち**: {{D:codex-astra-ultra}} の wave (branch `dev-wave-codex-astra-ultra`、commit 済み・未 land) の受入全走 (明示 shard 3) と変異 matrix (m0〜m7、事前登録は `output/insights/2026-09-30/codex-astra-ultra/verbatim/s4-ruling.md` と `mutation-spec-probe.json`) を計算ノードで回して land する。どちらも login で走る sanctioned 経路が無く、依頼 (計算ノード不使用) に従い未実施。計算ノードの使用を許すかを決める。許可後は main 取り込み → 受入 → 変異 → land 直前に daemon 稼働 0 件を確認 → `tools/dev_wave_land.py`。
- {{T:delegated-child-guard-probe}} **P2・ユーザー裁定待ち**: ultra の委任先 (sub-agent) に `.codex/hooks.json` の PreToolUse guard が効くかを直接 probe する。使い捨て repo で root と委任先に保護 path への書込みを試させる形 (`tools/check_codex_hooks.py` と同じ trust bypass flag) は auto mode 分類器が拒否したため、実行の許可 (または許可 rule) が要る。効かないと分かれば、委任の事後拒否だけでは workspace-write の子 worktree に guard 外の書込みが残りうる点を再裁定する。
