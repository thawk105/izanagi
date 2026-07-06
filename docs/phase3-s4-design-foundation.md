# 後続段 4 (coder 自律期) — 設計基盤 (調査で確定した骨子)

**位置づけ:** 2026-07-06 の焦点調査 (5 レンズ・457k トークン、wf_e2036fe9-dc2) が写像した後続段 4 の
設計基盤。**まだ decisions ではない** — 次セッションで design v1 に統合 → 敵対検証 (段 3 と同型) →
実装 → 実走 の入口。段 4 完了時に D39 + phase3.md に畳んで本文書は凍結/削除する
(phase3-main-experiment.md と同様の分離運用)。正典は phase3.md 後続段 4・main-experiment・
decisions。矛盾があれば正典が勝つ。

後続段 4 = coder が初めて変異の値・方向を**自律生成**する段。reward hacking 圧力が最も高く、
coder リーク制御が airtight でないと主実験の妥当性 (「合成できた vs 答えを読んだ」の区別・
失敗条件 c) が崩れる。3 点セット (coder.md 自律版改訂 / planner.md / diff 検疫層) + D38 残消化。

## 1. diff 検疫層 (段 4 の核・新機構)

- **正体:** 現行「検疫層」(guided.py cmd_evaluate) は P2-5 の**選択空間検疫** (8 列挙 genome ラベルの
  どれを選ぶか) でコード diff を見ない。段 4 の diff 検疫は別物 = coder 自律 diff の**構造**を parse 検証。
- **新規で塞ぐ唯一の機械穴 = digest 不感なフレーム改変:** 合成枝 (#if BACKOFF_FIXED>=0) を選ぶ genome
  では #else 枝・骨格 (#if/#else/#endif)・BEGIN/END マーカーが preprocess で落ち、source_digest の
  identity がその領域の変更を**構造的に見ない**。coder が #else 枝や骨格条件を書き換えても src_token が
  動かず素通り (phase3.md 残存リスク・coder.md:21 が「auditor/人間レビュー領域」と明記)。
- **設計 = フレームのバイト同値検査 (位置 parse、content 意味検査ではない):** 「骨格 (マーカー + #if/#else/
  #endif + #else 枝) が template 適用済み HEAD と byte 同一 ∧ 変更行 ⊆ #if 合成枝内部 (hole)」を、
  unified diff の @@ ハンクヘッダ (厳密仕様の行域) と固定テンプレ行 (BEGIN/END コメント・#if <AXIS>/#else/
  #endif) の exact-match で照合。backslash-newline splice 等の C++ レキサ回避が効かない (diff 行構造と固定行
  を見るだけ) ので **robust = 一次防壁級**。working-tree diff (結果) を見るので Edit/Bash のツール経路に
  不感 = hook 迂回 (攻撃 f) を構造的に無効化。
- **既存で覆う分は再実装しない (D30/D33):** #include 追加/TRACE 混入/任意バイト変更は source_digest
  (assert_includes_match_head / assert_trace_diff_matches_head / preprocess 後ハッシュ / -Werror=undef) が
  既に fails-closed。diff 検疫でテキスト再検査すると二重計上 + D33 の破れるテキスト検査の再来。
- **content 逸脱 (枝内の生 #if/#define/computed include・環境判別述語) は auditor + 規律6 に据え置き** —
  diff 検疫は advisory 信号として auditor へ渡すのみ (text-gate しない、D30/D33 の線引き)。
- **配置:** 新規 `orchestrator/campaign/diff_quarantine.py` (source_digest/patchharness と同格の fails-closed
  モジュール)。**guard_write (hook) には入れない** (PreToolUse で呼出元エージェント識別不能、content 検査は
  D33 削除)。patchharness.patch_files は file 粒度で行域を見ないので、ハンク行域 parse を新設。
- **配線 (規律3、片肺を作らない):** 段 4 で verify-red が正規経路で初発火する (D37 決定3) ので、diff-reject を
  S4 rejection digest の**新型**として配線し critic/次手に届ける。

## 2. coder リーク制御 (P2-5/D21 の Phase 3 版・最重要)

- **急所 (主実験妥当性):** decisions.md:319/338 等に sweet-spot literal (+38.3/+11.3%, 0-10us) が存在し、
  coder は Read tool を持つため coder.md:26 の「output/docs を読むな」は **prompt 規律のみで機械執行されて
  いない**。airtight でないと失敗条件 c (利得が機械 sweep で再現 = LLM 固有価値なし) の判定が汚れる。
- **critic-experiment の 4 層構造 (テンプレート):** (1) critic.md から最適解 literal を物理削除した専用 .md、
  (2) 誘導専用 WAL layout (評価済みだけ育つ)、(3) 全 8 入り digest を import しない物理分離、(4) tools=Bash
  のみ + fresh context。coder は CODE を書くので遮断対象が質的に違う (勝ち筋 VALUE・機序・利得・grid fitness)。
- **最強の構造障壁 = coder に filesystem browse を与えない:** critic-experiment がラベルを返すのと同型で、
  coder は**提案枝コードを構造化出力で返す** → Python ハーネスが挿入 + diff 検疫 + evaluate。これで
  「output/docs/WAL を読む」経路が構造的に閉じる (Read tool で徘徊させない)。見せる = spec/API/designated
  ソース、遮断 = 勝ち筋値・機序・WAL fitness・過去 variant の性能。
- **遮断対象の所在 (物理削除/入力射影で除く):** output/insights/2026-06-22_p2-case-study-backoff-synthesis.md、
  backoff-sweep campaign の WAL/reports、profile JSON、phase3.md 残存リスク節、main-experiment §24/§59、
  decisions D21/D22/§319/§338。
- **coder.md 自律版改訂:** kickoff 版「値を発明しない・WAL/output/docs を読まない」(prompt 規律) を、
  critic-experiment 同型の物理分離 (専用 .md + fresh context + 提案を構造化出力で返す) に格上げ (coder.md:41
  footer が既に予約)。
- **主実験との対:** §36-38 = coder リーク制御と機械 sweep (baseline 4) の軸命名手順を**対で事前登録**。命名の
  情報源記録 (どこまでの既知知見を見たか) が (c) 判定の前提。

## 3. planner.md 生成

- **予約仕様 (agent-architecture §planner):** spec cards + leading-indicator を消費し設計方向を提案・コードに
  引きずられない・whiteboard memory で却下設計を再提案しない・実装しない・強モデル。
- **read-only + 構造化出力 (段 3 auditor と同型、D38):** guard_write は PreToolUse で caller 非識別ゆえ
  per-agent path 制限が hook で表現不能 → planner も tools=read-only、提案を構造化出力で返し orchestrator が
  人間レビュー gate 下で反映。雛形 = auditor.md (opus/high)。
- **planner のリーク制御は coder より緩くない:** planner が軸/方向を提案する行為そのものが LLM 価値の実証点
  (baseline 4 の帰無仮説判定軸)。勝ち筋 literal を読むと「提案した」が「答えを読んだ」に化けて主実験の
  妥当性が崩れる。
- **whiteboard memory:** 却下設計を「評価済みのみ・事実 + uncertainty」で記録し planner に見せる。P2-5 の
  自信ある早期停止 (誤収束 8/12, D21) を再演しない narrow scope。

## 4. 自律ループ駆動 + D38 残 + 主実験配線

- **駆動 = ハイブリッド (headless CLI 不在):** ループ主導権 = メインセッション (orchestrator 役) が Task で
  毎 iteration fresh に planner→coder→auditor→critic を spawn。Python 側は決定的機械ゲート (diff 検疫 parse・
  mutation-red・COMMIT = pipeline.evaluate 唯一経路) を所有。ループ形 = planner(方向)→coder(#if 枝を構造化
  出力で提案)→Python が挿入 + diff 検疫→pipeline.evaluate(verify+bench)→critic(帰属)/auditor(監査)→whiteboard
  更新→次 iteration。
- **D38 残の段 4 消化:** (d) auditor が追加する assert の mutation 非恒真性を driver が毎回機械確認する
  mutation-red 汎用ゲート。(e) **auditor 直接 Write は read-only 据え置きが正解** — path-scoped 執行は原理的に
  不能 (guard_write は caller 非識別・subagent の tools 欄は Write の all-or-nothing)。段 3 の read-only を維持。
- **主実験配線:** 段 4 の中間結果は main-experiment 事前登録に従い「暫定」として報告 (headline は段 6)。
  段 4 で仕込む: baseline 3/4 の操作的定義・LLM ablation (critic 帰属あり/なし系列)。floor 流用禁止・失敗条件。
  検証相 (seed×N + 長 extime) は main-experiment §65-66 が明示的に**段 6** (段 4 でやらない)。

## 5. 敵対検証にかける Open Questions (次セッションの入口)

1. diff 検疫のフレーム byte 同値検査の正確な形 — template 適用済み HEAD をどう錨にするか (patch 適用後の
   working-tree を基準にするか、HEAD の #else/骨格を baseline にするか)。マーカー id 複数化への拡張。
2. coder に filesystem browse を与えない駆動 — coder が API 確認に CCBench ソースを読む必要 (coder.md 現行で
   許可) とリーク遮断の両立。構造化出力形 (提案枝コードのスキーマ) の設計。
3. リーク制御の物理削除 vs 入力射影 — 勝ち筋 literal が decisions/docs に散在するのを coder から遮断する形
   (専用 .md + fresh context で「読むな」を構造化。Read tool を外すと API 確認もできない矛盾)。
4. planner/coder/critic/auditor の 4 ロール自律ループの iteration 予算・停止条件・whiteboard の粒度。
5. diff-reject の S4 rejection 新型の形 (verify-red・liveness・integrity・lock 被覆に次ぐ第 5 形状か)。
6. 段 4 で実走する最小変異軸 (sort は段 5 なので、段 4 の coder 自律変異の題材は何か — backoff 値の自律発案?
   それとも別軸? kickoff は backoff で人間が値を与えた。段 4 は同じ backoff 軸で coder が値を自律発案する形か)。
