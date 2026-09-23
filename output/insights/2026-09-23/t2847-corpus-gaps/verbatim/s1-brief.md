# 段 1 brief — [T-2847] 残り (1) 小履歴コーパスの未被覆 2 案と B06 の G1c 分類 assert (2026-09-23)

- 研究前進: VLDB 差分分析 P0 (verifier の検出力) の「期待結果つきコーパス」の未被覆 3 点 (設計 §3 の区分集計で未被覆 2 + B06 の分類) を手で導いた期待値の test で閉じ、論文の射程文 (§7) の「コーパスで確かめた」範囲を 27 案すべて被覆済みにする。完了判定 = 新 test が緑、§3.1 の対応する verifier 側の壊れ方 3 種の変異で赤。
- scope: 新規 file `orchestrator/tests/test_verifier_corpus_gaps.py` だけ。中身は F03・F06・B06 の 3 案 (test 内の合成 v2 trace)。
- no-touch: `orchestrator/tests/test_verifier.py`・`orchestrator/tests/fixtures/`・`orchestrator/verifier/` (T-2854 存在履歴 wave と並走)。変異は DW-O19 の一時変異で即復元。
- 確定裁定: D95 (実装面は Codex author)、D799 (期待値は verifier の出力から取らず、辺・版から手で導く)。規律 2 を緩めない。
- 期待 (設計 §3 の表、手で導いた値):
  - F03: T0@v1:W(x)；T1@v2:R(x,v1),R(x,v1) (C の R 件数 2)。辺集合 = {0→1} (wr 1 本)。verdict serializable・certified、n_edges 1、anomalies 0。
  - F06: T0@v1:W(x)；T1@v2:W(x)；T2@v3:R(x,v1),R(x,v2)。辺集合 = {0→1 (ww), 0→2 (wr), 1→2 (wr), 2→1 (rw)}、n_edges 4。verdict non-serializable、巡回 {1,2}、分類 G2、2→1 の理由に rw (key x、読んだ版 v1、直後版 v2)。
  - B06: T0@v1:R(y,v2),W(x)；T1@v2:R(x,v1),W(y)。辺集合 = {0→1 (wr, x), 1→0 (wr, y)}、rw・ww なし。verdict non-serializable、分類 G1c、巡回辺の種類が wr だけ。
- 辺集合の比べ方: 本番経路 (verify_trace_dir が使う compact 構築 = DSG.from_compact) の隣接を読む。結果の n_edges・anomalies と併せて assert する。protocol は silo、証拠面は test 内で作る合成 silo source (test_verifier.py 冒頭と同型、import はしない) に束縛する。
- (P1) 親の provisional 裁定・攻撃対象: 辺集合を見るために内部 API (core の compact parse + DSG.from_compact の adj) を test から呼ぶ。本番経路と同じ構築なので採る。
- 変異の当て所 (事前登録は段 4): packed 読み辺 loop・compact 隣接の replay・DSG._classify。
- 成果物: 新 test file 1 本、insight (変異台帳・逐語)、worklog fragment、phase3 の T-2847 行の更新 (該当すれば)。
- 分割: 実装子 1 本 (Codex author)。軽量版: 段 2・3 と段 6 review 子を省く (設計択一は設計書で確定、正しさ防壁は触らず test を足すだけ、受理集合は不変)。
- 受入・実測環境: 焦点走は login、受入は tools/dev_wave_wait.py acceptance (worklog の既定所在)。計算は開発検査だけ (< 2 node 時間)。
- 期待と合わない場合: verifier を直さず、欠陥として構造化して insight に記録し返す。
