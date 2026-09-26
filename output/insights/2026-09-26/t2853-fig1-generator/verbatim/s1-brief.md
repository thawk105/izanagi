# 段 1 brief — [T-2853] 残り (5'') fig1 の生成器と後継図

- 研究前進: VLDB EA&B の再現パッケージ (D2212) で、値を持つ論文ストーリー図のうち生成器が無いのは fig1 だけ (計画稿 §3.1)。完了 = 後継図 3 点 + 生成器 + test が着地し、旧 fig1 と値が一致することを記録。
- 実測済みの前提 (login pegasus02、`probe_replay2.log`): 既存 `search_baselines.run_workload` は P2-2 campaign が verifier epoch E0 のため CERTIFIED_ACCEPTANCE で拒否される (新事実)。
  HISTORICAL_RAW で landscape を組み既存関数へ渡すと、3 workload とも greedy 統計・p_lt・tied 集合・random/oracle 期待値が summary 凍結値と一致、A (0.5813 / 0.2304) と厳密 p (2.521e-4) も一致。1.3 秒。
- 旧図の画素読み取り (`old-fig1-pixel-read.json`): 参照線・中央値棒・ひげ・個別点は summary と一致。greedy の四角は 0.04〜0.05 低く読める (読み取り側の偏りか要対照)。旧 script は履歴・job dir に無い。
- 既存被覆: decisions / failures / archive に fig1 の決定・事故なし。fig1・summary の bytes を束縛する pin なし (`test_guided.py` は値を参照)。裁定 inbox の最新 2 本に関連なし。

## 親の provisional 裁定 (攻撃対象)
- (P1) 名前: 後継 `docs/paper-story/figures/fig1b_phase2_negative.{png,pdf,provenance.json}`、生成器 `tools/plotting/plot_p2_5_search_cost.py`、test `orchestrator/tests/test_plot_p2_5_search_cost.py`。
- (P2) 値: guided の試行コスト・未到達数・n は summary の凍結値 (原 WAL は削除済みと summary 自身が記録)。greedy は P2-2 の 3 WAL を HISTORICAL_RAW で読み、生成器内で landscape を組んで既存の `search_baselines` 関数で再計算。orchestrator/ は変更しない。記録上の certified が 8 genome すべて true・空間被覆を要求。
- (P3) 描く値 (k・tied・random_E・oracle_E・greedy 平均/四分位・A・厳密 p) が summary の記録値と一致しなければ出力せず rc≠0 (fig13 の再計算一致要求と同じ型、描く値に限る)。
- (P4) 視覚符号は旧図を継承 (3 panel・色・記号・参照線・注記・題)。FIGURE_CONVENTIONS §9 の重なり検査を保存前に fail-closed、§6 provenance に入力 sha256・epoch・測定条件・描いた値、§10 実寸 fixture。
- (P5) 旧 fig1 と summary の bytes は不変。figures README に行と節 (再現・入力・キャプション・proof chain) を親が書く。論文ストーリー各版は触らない。
- (P6) 旧図との照合は親の使い捨て画素読み取りを旧図・新図の両方へかけ、要素ごとの表と注記文字の目視を insight に記録。

## scope 外
search_baselines / replay の改修、ストーリー本文・fig3 の数字、R2・再生のやり直し (LLM)、図の一般化・新しい台帳や検査。

## 不変条件
規律 2 (判定経路に触れない、図は現行 verifier で再検証していない E0 の記録と明記)、新規計測 0、凍結 bytes 不変。

## 分割・環境
Codex author 1 本 (生成器 + test)。親: 描画 (login、計測機の外)、照合、docs、記録。受入は `tools/dev_wave_wait.py acceptance` (計算ノード)。段 2・3 は軽量版で省く (DW-C00: 設計択一が割れず正しさ防壁・受理集合に触れない)。段 6 は値の再抽出を伴うので read-only レビュー 1 本を残す。
- 成果物影響 (G05): 無いと fig1 の値が repo から再現できず、再現パッケージの図が 1 枚欠ける。
