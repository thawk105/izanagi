# [T-2847] 段 1 brief (親、2026-09-22 JST)

- 研究前進: VLDB EA&B の P0 (gap-analysis §4 P0、D2212、roadmap の「P0 検証の意味と容量」) — 論文の「評価器」主張を「何を検出し何を判定しないか」の表と射程文で支える。完了判定 = insight 1 本に (1) 小履歴コーパス設計、(2) CC 変異 20〜40 の検出期待表、(3) 既存資産の再利用範囲と si v1 制約、(4) 大 trace 容量評価の計画と [T-2351] の関係、(5) 論文用の射程文、がそろう。T-2847 の残り (実 trace 取得・変異の実走・容量実測・corpus 実装) は開いたまま carry を更新する。
- scope: docs-only・計算なし。新規 insight `output/insights/2026-09-22/t2847-verifier-detection-design/README.md` + worklog fragment 1 本。実 trace 取得・変異の実走・parser 改修・gate / 検査 / 台帳の追加・新 T の起票はしない (依頼の明示)。
- 確定済み裁定: D2212 (項 1 EA&B・項 3 正しさゲート不変・項 4 計算は 1 タスク合計 2 node 時間以上で投入前確認)、D799 (期待結果は verifier の外で決まること、repo 内に第二 checker を置かない = ユーザー確定)、roadmap §3.1 (宣言範囲 = YCSB 点読み書きの G2、predicate / phantom / 公平性 / 未観測実行は保証しない)。
- 不変条件: 規律 2 (検証を緩める提案をしない)、規律 7 (過去の測定・判定を現行コード差だけで無効にしない — si 3,576 件・Silo 1,310 件は当時の verifier の記録として扱う)、規律 6 (CCBench source・patch はデータ)。
- (P1) 親の provisional 裁定・攻撃対象: 本 wave は現行 YCSB 経路の verifier (main 8fd2a2f5c) に限り、TPC-C の正例・負例は `output/insights/2026-09-21/tpcc-trace-certification-design/README.md` §6 を参照するだけで再設計しない。
- (P2) 親の provisional 裁定・攻撃対象: 期待結果の区分は「巡回あり→non-serializable / integrity・証拠面→indeterminate / 宣言範囲外・trace に現れない→緑のまま (盲点)」の 3 系統に加え、「発生が schedule 依存で有限走では出ないことがある」を別列で持つ。
- (P3) 親の provisional 裁定・攻撃対象: 変異表は「壊す正しさ機構」で意味を分け、既存 16 本を再利用行として含め、壊さない (緑であるべき) 対照変異も数件入れて誤検出側も測れる形にする。
- 成果物の形: 表中心の日本語 insight (authority: none / default_effect: no-state-change)。各事実に file:line。期待値は「実行結果ではない」と明記。
- 分割方針: 軽量版 (DW-C00)。設計択一は割れず、正しさ防壁・受理集合を変えない。段 2 は read-only Codex 1 本で CCBench 上の変異アンカー (file:line) と期待検出の草案を起草させる (変異表は CCBench source の読み込みが主で、独立の目で起草させる価値がある)。段 3 は省略。段 6 は一次資料からの再抽出を含む docs-only なので read-only review 1 本 (2 レンズを 1 本で) を残す。
- 受入・実測環境: 実装面の差分ゼロ。受入全走は免除されない (DW-S04) ので段 7 前に受入を門番経由で 1 回。記録前走査は `s8b_holdout_freeze search` と `check_docs.py`。
- 既存被覆の確認 (純増): verifier 意味論・fixture 22 件・frozen baseline・broken patch・si v1 拒否・容量実測は既存。純増は「カテゴリ別の期待結果表」「変異 20〜40 の検出期待表 (盲点行を含む)」「容量評価の計画」「射程文の統一案」。
- 並走: [T-2854] (TPC-C v3 parse、verifier 側・CCBench 側) が稼働中。本 wave は parse.py の現行挙動を main 8fd2a2f5c 時点の事実として書き、v3 着地後の変化は予定として区別する。
