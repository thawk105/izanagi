## 段1 brief
- 研究前進: VLDB 差分分析 P5 (介入で結果の理由を説明) の実験を S3 (LLM×IR) で行う前提の事前登録を S3 版にする。完了 = 草稿が S3 版 (4 cell × n = 4 本線、§11.0 単価、露出の棚卸し入り) で land、未発効のまま。
- scope: 当該草稿の改版 + 起草 insight への S3 改版節の追記 (起草の記録・棚卸しの実測 log) + worklog fragment。n の確定・発効・実装・投入はしない。gate・検査・台帳・一般化の追加はしない。
- 確定済み裁定: D2322 項 5 (S3・write-heavy・LLM×IR のみ、4 cell 正-あり/伏せ-あり/入替-あり/正-なし × n=4 を向き、換算 21.4〜24.7 node 時間、LLM 直列 15〜64 h)、D2283、D2305 項 3 (T-2867 本走の後)、D2212 項 4、D2249 追加項 (時間帯 block なし)、D2256 項 4 (coder 入力 firewall)。
- 不変条件: 規律 2 (verifier・即 reject は全 cell で外さない)、規律 3 (構造化された失敗理由は全 cell で coder に届く)、本書は未発効の草稿。
- (P1) 親の provisional 裁定・攻撃対象: critic なしの cell は critic を呼ばないだけとし、性能の機械的な写しは足さない (D2256 項 4 を変えない)。推定対象は「critic の呼出し全体 (解釈 + coder への性能の唯一の還流経路)」。写し案はユーザー確認事項に並べる。
- (P2) S1 版の「失敗理由の写し」は S3 では作らない — 自系列履歴の verifier_digest が critic と独立に構造化された失敗理由を coder へ届ける。
- (P3) 記述の表示は、coder 文脈の Measurement Setup の標準 workload 塊 (現状 rr50 配線規模) を全 cell で水準の表示に差し替え、critic prompt に水準の動作点表示を足す (実装は後続 wave)。T-2867 の LLM×IR 系列は C-on 相当でない (正しい名が表示されていない) ので標本に入れない。
- (P4) 統計は S1 版の Bonferroni t 区間 (族 3、δ = ln 1.03) を継承。n=4 の符号反転 exact は最小片側 p = 1/16 で使えない。
- 既知結果の開示: T-2867 本走の完了と commit 題 (4 比較とも floor 内の同等) を見た。score の値は読んでいない。本走の coder 入力から露出欄だけを抽出した (baseline abort 12.56%、projection、文脈の rr50 行)、critic 出力の断片を grep で見た。
- 成果物の形: 草稿の全面改版 (同 path、§16 に改訂履歴)。分割: 子による実装なし。段 2・3 省略 (軽量版)、段 6 は一次資料の再抽出 + 設計択一ありのため read-only codex 2 本 (事実照合レンズ・設計/統計レンズ)。
- 受入: docs のみ (実装面差分ゼロ) → 変異 matrix 免除。check_docs と関連テスト、受入は land の規定に従う。

