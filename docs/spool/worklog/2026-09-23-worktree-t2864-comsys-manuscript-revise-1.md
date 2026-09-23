---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-23
wave: worktree-t2864-comsys-manuscript-revise
seq: 1
title: [T-2864] ComSys 原稿の改訂 2 — ADRS を一次資料で判定し (近傍、位置づけの 1 文は逐語で残す) 原稿の「判定していない」3 か所を判定結果へ、4 巡目の還流を T-2860 どおりに直し 15 頁で再組版 (docs のみ、branch worktree-t2864-comsys-manuscript-revise)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`): D2227 項 5 (ADRS を正典で判定し 1 文を残すか書き直す)、[T-2860] の着地 (entry 1832) の反映、15 頁のまま再組版 (項 4)。著者・所属と送信は触らない (項 3・6)。
  起点 local main `65fd1422f`、開始 gate rc=0。段 2・3 は省略 (軽量版)、段 6 は独立 read-only レビュー 1 本 (Codex)。計算なし。
- ADRS の判定: 一次資料 arXiv `2510.06189` HTML v3 (2026-09-23 取得) を読み、1 文の 3 条件ごとに「LLM が」= 満たす、「並行性制御を対象として」= 一部だけ (対象は取引の実行順序、
  実行中の競合を待たせる・中断させる判断は書かない、評価は単位時間の模擬器の makespan で直列化可能性の検査の記述なし)、「アクション空間自体をコードで拡張」= 一部だけ
  (方策は任意の Python だが対象への動作は順序のまま) と判定した。結論 `近傍` — 反例ではないが条件の狭い読みに依存する。1 文は逐語で残した。軸 1 は `RW1` のまま (新しい検索ではない)。
  記録 = `docs/related-work/claim-survey/2026-09-23-adrs-adjudication.md`、原稿の記録 = `output/insights/2026-09-22/comsys2026-manuscript/README.md` §10。
- 親の誤りと訂正 (記録の commit 前): 語の走査の `lock` 18 件の内訳を文脈を数えずに書き、部分一致 (`blocks`・`block_id` など) を取り違えていた。数え直して判定記録を直した。
  SMF の方策が競合の費用を見積もる点を「競合検出が現れない」と書いていたのを、「実行中の競合を待たせる・中断させる判断は現れない」へ狭めた。
- 依頼外で気づいた古い記述 (反映していない): 原稿 7 節 (a) の TPC-C の certified 判定 (entry 1843 で存在履歴の検査が実装された) と (c) の B-5 本走の未認可 (D2227 項 2 で認可)。README §10.4 に記録し、[T-2864] の更新に含めた。
- 段 6 (Codex read-only 1 本): 1 回目 NO-GO、must-fix 1 = ADRS を「最も近い」研究と順位づけた表現 (軸 1 は RW1 で世界順位を書かない、正典 7.1)。real と裁定し 5 か所を直した。条件別の判定・転記・語の件数は覆らなかった (件数は独立に再計算して一致)。 焦点再レビュー (fix commit 対象) は GO、新規所見なし。near miss は {{F:superlative-rank-in-rw1-adjudication}}。
- 受入: 1 回目 (tested main `65fd1422f`) は終了時の検査の競合 (terminal-postcheck) で rc=70、門番が自動で戻した。2 回目 (main `620a6bb13` を post-claim merge、tip `b53a72889`) は赤 4 件で rc=70。
  赤は `test_env_contract_activation` の historical calibration 2 件 (git archive の 30 秒 timeout)、`test_codex_worker_launch::test_t2620_orphan_mixed_is_rejected` (/proc の一過性の読取失敗で residual が None)、
  `test_dev_wave_cleanup::test_remove_child_checks_initialized_submodule[dirty]` (占有走査中に他 pid の cwd が消え indeterminate)。いずれも負荷・時間依存で、本 wave の差分 (tex・pdf・md のみ、コード無変更) は到達しない。非帰属と判定した (DW-O18)。
- 受入 2 回目の走行中に rulings 第 34 回の収集 session から、[T-2864] の更新版が D2235 項 2・3 の 2 点 (noauthor を外した再組版と頁数確認、参考文献の採録版照合) を落としていると連絡を受けた。
  local main `620a6bb13` の現物で確かめて real と判定し、2 点を残した形に書き直した (base も取り込み後の値へ)。
- 組版は 15 頁 (エラー 0・警告 0・Overfull 0、Underfull 2 件は改訂前と同数)。改訂段落の出現を頁ごとの文字抽出と画像で確かめた。`grep -n "^%.*．"` は 0 件。

## 次の一手差分

### 更新

- [T-2864] **P2・一部裁定済み (D2227 項 3〜6、D2235 項 2・3) → 著者・所属の記入 (ユーザー手番) → 差し込み・再組版 (AI) → 発表申込・原稿送信 (人間手番)**:
  ComSys 原稿 (`output/insights/2026-09-22/comsys2026-manuscript/manuscript.tex`) の残り。頁数 15 頁のまま (D2227 項 4)、ADRS の判定 (D2227 項 5) と 4.7 節ほかの 4 巡目の反映は
  改訂 2 で済んだ (同 dir `README.md` §10)。(1) 著者・所属 (`\affiliate` / `\author` の差し込み欄) はユーザーの記入内容を受け取ってから差し込む (AI は推定しない)。差し込みでは
  `\documentclass` の `noauthor` 指定を外して再組版し、頁数を確かめ直す (16 頁以上になれば D2227 項 4 の前提が変わるので再提示)。(2) 投稿前に参考文献を採録版の書誌で照合する
  (原稿 README §3.4)。(3) 改訂 2 の起点で古くなっていた 7 節 (a) (TPC-C の存在履歴の検査、entry 1843) と (c) (B-5 本走の認可、D2227 項 2 と [T-2797] の発効) を一次資料と照合して直す
  (README §10.4)。(1)〜(3) は 1 本の改訂に束ねなくてよい。(4) 発表申込 10/16・原稿締切 10/30 の送信は人間手番 (収載は送信の承認ではない)。一次資料 同 dir の `README.md` §3.4・§6・§10。
  base: 7c99d8bf6e71d4acf0b90784280503e85d16a6fd7a46d50eea78e41ddedafac1
