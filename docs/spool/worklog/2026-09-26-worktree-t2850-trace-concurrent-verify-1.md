---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-26
wave: worktree-t2850-trace-concurrent-verify
seq: 1
title: [T-2850] 案 (b) を実装した — 性能 trace 5 本を直列に取得してから fork した子で同時に検査し、同時検査の後の静定待ちの上限を本番順序の実測から 120 秒にした。計算ノードの再 smoke で 5 session すべて certified・settled=true、試走全体の見積りは 40.8〜58.2 → 22.2〜40.5 node 時間。追補 2 を書き、試走 3 block の計算確認をユーザーに問う (コード + test + 追補 + insight、branch worktree-t2850-trace-concurrent-verify)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`): [T-2850] consult-option/decision.md の決定どおり (b) を実装する (pipeline.py の検証 trace の同時検査と write-heavy の静定待ち 60 s)。変異・受入・smoke 1 job の後、追補 2 を書き、試走 3 block の計算確認を取る。
- 起点 = local main `6d198ca8a` (fresh worktree、開始 gate rc=0)。段 1〜9 を省かずに回した (正しさの受理経路に触るため)。
- **段 3 で覆った前提:** 段 2 の plan は既存の remote fan-out の受理経路を `BACKOFF_REPRO` 条件のまま使う案だったが、比較 harness の全 slot は `BACKOFF_SWEEP` で、そのままでは同時化が 0 件になる (相談 A の must-fix、親もコードで確認)。段 4 で fork した子が受領証を返す方式に改めた ({{D:concurrent-local-verify-fork-receipt}})。
- **静定の上限を 60 秒 → 120 秒に改めた:** 依頼の 60 秒で計算ノードの smoke (job 29777、205 s) を走らせると、stock は同時検査 5 本 certified だが静定待ちが上限を使い切り `settled=false` → 品質欠測 → `stock-unestablished`。60 秒の根拠の実測は本番と違う順序で取った値だった ({{F:settle-cap-from-different-order-probe}})。本番順序で測り直し (generic dispatch 2 job) 67 秒・77 秒、上限 120 秒で再 smoke (job 29854、Elapse 1,145 s) は 5 session すべて certified・settled=true・品質 normal、系列 `b-complete`。依頼の値からの変更で、根拠は insight §3。
- smoke の計算は 2 job で 1,350 s、測り直しは 2 job。いずれも 2 node 時間未満で確認不要の範囲。
- **棄却した所見:** 相談 A2 (trace 内容の digest 束縛)、レビュー A4 (同時経路の不認証で `verify_result` が None)、焦点再レビュー 2 (失敗 rep より後と finally の経路で group 消滅確認の失敗を捨てる) は、判定・記録の値が変わらないとして refuted ({{D:concurrent-local-verify-fork-receipt}} の却下欄)。焦点再レビューは 2 巡で親が裁定して閉じた。
- **焦点走の赤の帰属:** v1 (179 赤) は未 commit の木を走らせた contract-loader-drift で実装と無関係、v2 (6 赤) は新 test の fixture と起動箇所の登録簿、v5 (1 赤) は fix 3 の /proc 走査が終了途中の無関係な process の ESRCH で rep を reject していた (fix 4 で修正)。
- **変異:** final は 11 / 11 が期待と完全一致 (KILLED 10、等価変異 1 が SURVIVED)。M8 は drift に覆われ、commit 注入で値の層の生存 (test の穴) が分かった (F1037 の再発)。fix 6 で test を足し、commit 注入で落ちることを確かめた。結果の全体は insight §5。
- 焦点走の最後は `d21b870c9` で 1,439 passed。記録 commit の後の受入全走 1 回目は `test_plain_runner_coverage.py` の 1 件だけ赤 (新設 test file に自走 harness が無い、自分起因) で、fix 7 で足した。焦点走の file 集合にこのメタ test を入れていなかった (DW-O26 の「新規 test file を足す走は file 集合列挙のメタテストも含める」の漏れ)。
- 工数: Codex 子 = plan 1、consult 2、author 1、fix 8 (うち test だけ 3、報告の不受理による再投入 1)、review 2、焦点再レビュー 2、repo 外 script の author 2 (投入 glue v3・測定 script v3) の計 18 本。

## 次の一手差分

### 更新

- [T-2850] **P1 (VLDB 差分分析 P3: 探索の独立反復と費用・成果の曲線)**: 事前登録 v1 `docs/search-repetition-trial-preregistration.md` (D2231)・追補 1・**追補 2** (`docs/search-repetition-trial-preregistration-addendum-2.md`) で、
  試走は S1-wh × 5 手法 × 3 系列 + block job 3。案 (b) (trace 5 本を直列取得して同時に検査、同時検査の後の静定待ちの上限 120 秒) を実装した ({{D:concurrent-local-verify-fork-receipt}})。
  旧 block 1 (cohort `t2850-trial-v1`) は予備走で標本に数えない。時間帯の区切り (block 間 1 時間) は D2249 により外した。
  残りは 4 つ。(1) **ユーザーの計算確認:** 試走 3 block (cohort `t2850-trial-v2`、18 job) の見積り 22.2〜40.5 node 時間 (図 1 枚 4.4〜8.1、上側の大半は LLM 系列の親の待ち)、LLM の直列時間 1.9〜19.5 時間 (追補 2 §6)。
  確認が取れたら発効の決定 (本登録 §10: 固定 commit = 本実装を取り込んだ main の commit、glue v3、費用上限 200) を書いて、18 job をまとめて投入する。
  (2) 試走の後: 事前登録 §8 の規則で T_c・対差 SD・課題の集合・系列数を計算して追補に書き、本比較の上限をユーザー確認してから投入する。
  (3) 案 (a) (LLM の待ちを node の外へ) は、試走の LLM 待ちの実測を見てから、残る待ちの node 時間が導入費を上回るときだけ設計する。
  (4) MOCC (S2)・policy IR (S3) は、その空間の最初の生成より前の追補で足す。read-heavy・balanced へ同時検査を広げるときは記憶量と静定の上限を別に測る (B-5 v2 も同じ部品を使いうる、D2249 項 1)。
  **生成・選択には [T-2851] の留保条件を使わない** (`docs/unseen-condition-transfer-preregistration.md` §2.3・§3、D2223)。一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P3。
  base: fdfd141a2b23af857ec15bbca1314a13b831ed20ac78a05ff8bbfefe27f78389
