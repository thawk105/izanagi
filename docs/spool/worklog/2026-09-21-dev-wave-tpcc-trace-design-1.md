---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-tpcc-trace-design
seq: 1
title: TPC-C を trace verifier で直列化可能性まで認定する設計と工数見積りを返した — 段 1 (NewOrder / Payment) は表識別子・v3 frame・trace build 限定の commit 計数で閉じ、段 2 (全 5 取引) は範囲読みを述語読みとし「見えなかった key が挿入前か削除後か」を直接の証拠で決める (cycle を作らない側を選ぶ草案の規則は偽認定するので撤回)。認定対象は silo と mocc (X/P 計装の着地後)、si は検出専用。必須 11 実装単位・暫定 6 wave、trace は百万 commit あたり段 1 約 1.37 GB / 全 5 取引約 3.15 GB (試算) (docs のみ、branch dev-wave-tpcc-trace-design)
---

## 本文

- 依頼 (台帳 ID 未起票、主題 slug) は precheck で実装差分ゼロ。VLDB 方針の裁定控え項 2 (TPC-C 必須) を受けた設計と工数見積り。段 2 plan (codex read-only) 1 本 → 段 3 敵対相談 2 本 (正しさ境界 / 実効性と過剰) → 段 4 で「コードは実装しない」と裁定 → 親が insight を起草 → 段 6 read-only review 1 本 (NO-GO) → 訂正 → 焦点再レビュー。変異 matrix は実装面の差分ゼロで免除 (DW-S04)。成果は insight `output/insights/2026-09-21/tpcc-trace-certification-design/README.md` (段 1〜6 の全文は同 `verbatim/`)。
- 依頼の前提の照合: 検証前拒否の実体は `orchestrator/campaign/pipeline.py:434` (依頼文の `orchestrator/pipeline.py` は実在しない)。3 CC とも R/W 行に表識別子が無いが、read / write set の要素は `storage_` を持つ。表なしで NewOrder 表と Order 表の key が同じ 8 byte になり、Warehouse と Item も一致しうる (実衝突)。D295 の計数不一致は `include/tpcc.hh` が commit 成功後に `quit_` を見て counter 加算前に return することが原因。Payment / OrderStatus の姓検索は CC を通らず索引を読むが、索引の書き手は初期ロードだけ。
- 新事実: (1) X/P の証拠面の emitter は silo にしか無く、`Integrity.clean()` が要求するので、現 pin で certified に届くのは silo だけ (mocc は稼働中の [T-2844] が計装を作成中)。(2) si の trace は v1 形式で、現行 parser が拒否する (`orchestrator/verifier/parse.py:323-326`) ので、si は今どの workload でも検証できない。(3) si の update / delete は read set の要素を消すので R 行が落ちる。
- 段 3 の核心 (レンズ A): 草案の「既存辺の到達可能性で不在の観測版 (挿入前 / 削除後) を決める」規則は、実在する G2 を非巡回にして偽認定する (反例: 挿入前の空読み → 挿入と y 更新 → 削除 → 読み手が y を読む)。観測版は直接の証拠 (scan の物理候補ごとの観測記録、silo / mocc は走査区間を挟む trace build 限定の通し番号) で決め、決まらなければ indeterminate にすると親が段 4 で採った。
- 段 6 review は NO-GO (must-fix 5)。親の判定: M1 (si は snapshot 時刻と最終 cstamp だけでは読取り時の不可視を再構成できない) real、M3 (通し番号の境界を node 検証の終了にしたため反例が重なりで indeterminate になり本文の「赤」と矛盾 → 境界を走査区間へ) real、M4 (通し番号の保存・順序・保護の契約が未定義、Masstree の split を含む走査保証は未証明) real、M5 (約 7 億は依存理由の候補数で、取引対の辺は約 7,200 万) real、**M2 (挿入のみ・初期存在 + 削除の不在にも直接証拠が要る) は refuted** — 不在の版が 1 つしか無い key では結果が観測版を一意に決め、Adya の定義どおりの辺になる (認定するのは直列化可能性で実時間順序ではない)。S6 (mocc の高温・RLL 経路は absent 判定を通らない) と S7 (計算確認は合計 2 node 時間以上だけ) も反映。焦点再レビュー 1 本は GO (8 所見すべて closed。M2 への再攻撃は 2 通りの履歴とも cycle として検出され不成立、訂正による回帰なし)。GO は設計文書に対する判定で、Masstree の走査保証・通し番号の実装契約・実 CC での control は実装の完了条件として残る。
- 付随して見つけた CCBench の問題 (insight §9、還元判断: ユーザー確認待ち): 挿入 tuple の公開後・write set 登録前の return (3 CC、現行 5 取引では非到達)、abort による挿入 tuple の即時解放 (全 5 取引で静的に到達しうる)、OrderLine の番号が初期ロードと実行時で食い違う、OrderStatus が最古の order を読む、Delivery の delete_record の NOT_FOUND 無視。
- login での小規模 build: `cmake -S` (TRACE=1) は rc 0。`cmake --build` は hook `guard_bash` が「Pegasus ログインノードでは重い処理を実行できない」で拒否し、依頼の制約 (計算ノードへ投げない) に従って build 確認はしていない。
- TPC-C 段 1 / 段 2 の実装 T は、並走中の VLDB 方針記録 wave (branch `worktree-dev-wave-vldb-direction-revision`) が起票するので、本 wave は新規 T を作らない。本 insight はその 2 件の設計入力。
- 記録前検査: `check_docs` 違反なし。三軸語走査 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`) は rc 1 だが、hit は既存の tracked file 3 本 (`output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/` の journal / manifest / result、commit cc82edc8c) だけで、本 wave の file は 0 件。codex 逐語 1 file (`s3-consult-A.md`) の行末空白 2 行を可逆に除去し `verbatim/NORMALIZATION.md` に原文 sha256・bytes・位置を記録。
- 工数: codex 子 = plan 1 + consult 2 + review 1 + focus 1 の 5 本。wave の壁時計は開始 gate (2026-09-21 21:4x JST、`startup-gate.log`) から記録 commit まで。受入全走と land の結果は本 entry にも insight にも書けない (受入は記録 commit の後に走り、land の結果は fold の後に確定する)。

## 次の一手差分
