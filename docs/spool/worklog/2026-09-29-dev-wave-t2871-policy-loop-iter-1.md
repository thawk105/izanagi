---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-t2871-policy-loop-iter
seq: 1
title: [T-2871] 方策 loop を Pegasus で job をまたいで複数 iteration 回せるようにした — pair を系列の iteration ごとの計測 campaign で測り (claim は iteration ごとに one-shot、stock skip も解消)、本番入口の pair job 2 本を同じ系列で連続して通した (コード + test + runbook + insight、branch worktree-dev-wave-t2871-policy-loop-iter)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = insight `output/insights/2026-09-29/t2871-policy-loop-iter/verbatim/request.md`): claim leaf と one-shot 性を変えず、claim を手で退避せず、driver 側で解く。記録 = 同 insight、設計判断 = {{D:policy-loop-per-iteration-measurement}}。
- 起点 = local main `51f896352` (開始 gate rc=0、2026-09-28 07:58 JST)。設計択一が割れるので段 2 (plan 2 本)・段 3 (2 レンズ) と段 6 のレビュー 2 本 + 焦点再レビュー 1 本を回した。
- **段 1 の新事実:** claim を解いても、同じ campaign の WAL で終端済みの variant は skip されるので、2 本目の pair を同じ loop campaign で測ると同じ job の stock が付かない。先例の実測: K2 (T-2795) は job ごとに新しい submit checkout (別 out_root) を使い、loop 状態は継続していなかった。確認した K2・B-5・T-2849・T-2850・方策系列 A/B に job 間で loop 状態を継続した例は無い。
- **セッション異常:** Pegasus の保守 (9/28 09:00〜21:00、/etc/motd) で段 6 の途中から中断し、9/29 02:27 JST にユーザーの「続けられる？」で再開した (resume gate rc=0)。焦点走 1・2 回目は保守前後の queue-wait 打ち切り (rc=16、child 未起動)。9/29 03:10 頃にマネージャーセッションから「ユーザー就寝中、判断待ちで止まらず codex と決める」の連絡があり、生死確認の形 (混雑で 2 本目が系列の walltime 予算に当たる見込み) を codex の 2 立場で相談して決めた (insight `verbatim/liveness-decision.md`)。
- **段 6:** 焦点走 3〜5 回目の赤はすべて本 wave の結合検査の代役・配線 (子 process の import 経路、namespace inventory の pin、backoff の 2 checkout fixture を写した代役) で、実 admission・実 auditor gate は正しく拒否していた。fix-2〜4 で直し 6 回目 393 passed。失敗の型は {{F:test-double-copied-sibling-driver-flow}}。変異 M1〜M5 は 5 / 5 KILLED (dispatch final)。期待 node の収集は dispatch probe が混雑で 2 回中止したので login の実 pytest で行った (手順の逸脱、insight §4)。login の `/tmp/.git` 偽赤は F763 の再発。
- **生死確認 (本番入口の job body、liveness 専用系列):** 新しい submit checkout (`d7161a2a1`) で t2865 の proposal 2 本を `33730.nqsv` → `33800.nqsv` (`qsub --after`) の直列で流し、2 本とも候補 certified・同じ job の stock `certified-stock`・別の claim・系列 iteration 1 → 2・履歴 2 行を現物で確かめた。値は 1 回ずつの観測 (prop-3 = critic の推奨 A は同じ job の比 1.41、abort 55%)。
- 計算: 受入を除き約 2,080 秒 (約 0.58 node 時間、焦点走 169 秒・変異 final 379 秒・pair 793 + 741 秒)。2 node 時間の線の下なのでユーザー確認なしで投入した。
- 受入: 記録時点では未実施。
- 工数: Codex 子 = plan 2、consult 2、author 1、review 2、fix 4、焦点再レビュー 1、生死確認の相談 2 の計 14 本。Claude 子 = Explore 1 (先例の実測)。

## 次の一手差分

### 完了

- [T-2871] 方策 loop を Pegasus で複数 iteration 回せるようにした。pair は系列の iteration ごとの計測 campaign で測り ({{D:policy-loop-per-iteration-measurement}})、本番入口の pair job 2 本を同じ系列で連続して通した (記録 `output/insights/2026-09-29/t2871-policy-loop-iter/README.md`)。
  remaining: none
  base: 8f561fd41f023660af2e881f977a608763a7f4207de219b7a1054409d595ec48

### 更新

- [T-2865] **P1・Pegasus で 2 iteration 目以降を回せる状態になった ([T-2871]) → 次は研究系列を複数 iteration 回す (AI)**: silo-function-policy 軸 (D2214、段階 F = D2270) の系列 B は評価済み 1 iteration と、critic 診断を受けた未評価の iteration 3 proposal で閉じている (D2274、記録 `output/insights/2026-09-27/t2865-silo-policy-iter2/README.md`)。[T-2871] で pair を iteration ごとの計測 campaign で測るようにしたので、同じ submit checkout で pair job を直列に投入すれば 2 本目以降も通る (2026-09-29 に liveness 専用系列で 2 本連続を実測、`output/insights/2026-09-29/t2871-policy-loop-iter/README.md` §5)。系列 B は walltime 予算で閉じているので、新しい系列 (新 submit checkout、bootstrap stock から) で coder・auditor・critic を回す。単価は pair Elapse 741〜793 秒・bootstrap stock 309 秒、LLM は 1 iteration 約 4〜5 分。walltime 予算 3,600 秒は待ち行列の時間を含むので、2 本目以降は `qsub --after` で先に待ち行列へ入れる ({{T:policy-loop-walltime-includes-queue}})。LLM 対 非 LLM の対照は [T-2867]、固定文面の改訂は [T-2870]。
  base: 912ccba88a434e4f965cbf48447316cadac9164ab14466c4baf58dc0f1b72ee4

### 新規

- {{T:policy-loop-walltime-includes-queue}} **P2・新規 (ユーザー裁定: 予算の数え方)**: 方策 loop の walltime 予算 `MAX_WALLTIME_S = 3600` は系列の `loop_state.json` の作成 (1 本目の job の driver 起動) から数え、待ち行列の時間を含む (D2256 項 3)。混雑した Pegasus では claim が解けても 2 本目以降が予算で `stopped-before` になりうる。2026-09-29 は gen_S の予定開始が 1 本目 07:13・2 本目 14:42 と出ており、`qsub --after` と `qalter -p` で 2 本目を系列開始の約 36 分後に始められたが保証ではない (`output/insights/2026-09-29/t2871-policy-loop-iter/README.md` §5・§8)。予算を計算ノード上の実行時間で数えるか、現行のまま運用で詰めるかを決める。
