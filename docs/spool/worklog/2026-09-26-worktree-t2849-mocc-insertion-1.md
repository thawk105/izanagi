---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-26
wave: worktree-t2849-mocc-insertion
seq: 1
title: [T-2849] 残り (2) 単位 8 — MOCC の動作点を pin C で較正し (3 workload とも records 1,000,000)、比較 harness の 1 slot 経路に MOCC を差し込んだ。計算ノードで MOCC の stock と literal 候補 5 slot が全部 certified。harness の campaign pin が pin 前進の範囲外だったので MOCC の slot だけ C に移した (較正記録 + コード + test + insight、branch worktree-t2849-mocc-insertion)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = insight `output/insights/2026-09-26/t2849-mocc-insertion/verbatim/request.md`): [T-2849] 残り (2) = 単位 8。同じ wave の先頭で MOCC の動作点を較正。残り (3) の疎通は含めない。1 タスク 2 node 時間以上なら実測単価で見積もって確認。実装は Codex author。仮想リスク向けの追加は scope 外。
- 起点 = local main `42d148868` (fresh worktree、開始 gate rc=0)。wave 中に main は docs だけで 25 commit 進んだ (実装面の変更なし)。
- **計算投入のユーザー確認:** 較正 583 秒を使った後、生死確認 2 job を含めて「実測単価で約 1.3〜1.7 node 時間、walltime 上限込みで最大約 2.8」と示し、回答は「生死確認込みで進める (推奨)」。実績は受入前で約 1.57 node 時間 (insight §7)。
- **生死確認で判明した新事実:** 評価入口の campaign pin (`p3_s4_loop.PIN`) は D1936 項 1 で 511c9538 に固定され、pin C への前進は D2150 項 1 の ①④⑦ に限られていた。依頼の「pin 前進は済み」は gitlink には正しく、harness の campaign pin には及んでいなかった。D2150 項 1 ③ と D2227 項 1 の範囲として MOCC の slot だけ C に移した ({{D:mocc-slot-campaign-pin-c}}、{{F:pin-advance-scope-misread-as-driver-pin}})。
- 生死確認は 4 回止まってから通った (insight §6 の表)。1 回目は submit-tree を AI の worktree 置き場に置いた、3 回目は third-party の cache を直接供給元にした、4 回目は 1 本の submit-tree を 2 job で共有した — いずれも親の投入の組み方の誤りで、[T-2850] が先に踏んでいた形。2 回目が上の新事実。4 回目の系列は bench の静定判定 (load ≤ 4.0) 未成立で stock 不成立になり、系列番号 2 で 1 回だけ再投入して通った。
- **棄却・縮小した所見:** 相談 B の削除提案 (`MOCC_RECORDS` 表・harness 外の mocc 拒否・orphan env 拒否・aggregate の protocol キー化) を採用して作らなかった。レビュー B の「`make_define_request` の mocc で他 macro を拒否する分岐を削る」は不採用 (拒否は受理集合を広げない向きの 1 行)。レビュー A の「T1 が新実装同士の比較」は既存の loop golden が固定しているとして refuted。
- 焦点走 1 回目の赤 7 件は自分起因 (silo 既定の呼出しにも `protocol=` を足し、既存試験の代用関数が受けなかった)。fix 1 で silo の呼出しを変更前の形に戻した。
- 工数: Codex 子 = plan 1、consult 2、author 1、review 2、fix 2、焦点再レビュー 1 の計 9 本。Claude の調査子 1 本 (Explore、sonnet、較正機構の所在)。

## 次の一手差分

### 更新

- [T-2849] **P1 (VLDB 差分分析 P2: 公平な比較基盤と第 2 プロトコル)**: 設計は D2220 と insight
  `output/insights/2026-09-22/t2849-comparison-harness-design/README.md`、(1) 実装 (単位 1〜7、S1 = silo の backoff 値空間) は D2233 と insight
  `output/insights/2026-09-23/t2849-comparison-harness-impl/README.md`、(2) MOCC の差し込み (単位 8) と pin C での MOCC の動作点の較正は {{D:mocc-slot-campaign-pin-c}} と insight
  `output/insights/2026-09-26/t2849-mocc-insertion/README.md` で済んだ (`--protocol mocc` / env `IZANAGI_S4_T2849_PROTOCOL=mocc`、MOCC の slot だけ campaign pin C、較正 3 件とも records 1,000,000、
  計算ノードで MOCC の stock と literal 候補 5 slot が certified)。残りは (3) 第 2 プロトコルでの疎通 (20〜40 候補 × 3 workload、検証だけで約 8〜16 node 時間、準備・build・性能測定は別。
  MOCC の write-heavy の slot は子の wall 288〜332 秒の実測あり)。MOCC は silo と別の cohort 名・root で走らせ、stock 比で報告し既知最良の参照が無いことを明記する (D2220 項 6)。
  harness mode の直接 qsub は、submit-tree を AI の worktree 置き場の外に job ごとに 1 本置き、third-party は submit-tree 内 staging へ hydrate する (insight §6)。
  有限空間だけで LLM が負けてもコード合成一般の結論にしない ([T-2848] が要る理由)。完了 = 5 手法が同じ口で走る基盤 (S1) と第 2 プロトコルでの疎通。
  計算: 1 タスクの job 合計が 2 node 時間以上なら、job Elapse の実測単価で見積りを示してユーザー確認後に投入する (D2212 項 4)。一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P2。
  base: e80bb41efa2dbe7f7d9d4dc8fa00fa1e8b36eb417d88e61fed6a283454c22f76
