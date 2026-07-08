# 後続段 4 (coder 自律期) — Design v1

**位置づけ:** 設計基盤 (調査で確定した骨子) + handoff の記憶 (Model Y 裁定・密結合発見) を統合した実装設計。段 4 完了時に D39 に畳んで本文書は凍結。正典は phase3.md 後続段 4・main-experiment・decisions。矛盾があれば正典が勝つ。

後続段 4 = coder が初めて変異の値・方向を**自律生成**する段。reward hacking 圧力が最も高く、3 点セット (diff 検疫層 4a / coder リーク制御 4b / planner 4c) + D38 残消化。

---

## 0. 核発見: Model Y 裁定と 4a-4b 密結合

前セッションの重要発見：**4a (diff 検疫) と 4b (リーク制御) は密結合。** coder の**出力インタフェース**が diff 検疫の役割を決める。よって「4a を先に単独実装」の順序は誤り — 一体で設計する。

### Model X (却下) vs Model Y (採用)

**Model X = coder が filesystem を Edit**
- coder が Edit tool でファイルを直接編集 → diff 検疫が `git diff` のフレーム byte 同値を検証 (主ゲート)
- **急所:** coder は Read tool を持つため、`output/docs/WAL` を徘徊して勝ち筋 literal を読める = リーク

**Model Y (採用) = coder は fresh subagent・提案を構造化出力で返す**
- coder は filesystem browse なし。合成枝 (#if 合成軸 >= 0) のコードを構造化出力で返す
- orchestrator (Python harness) がテンプレフレームに挿入 + diff 検疫 + verify+bench
- フレームは構成上保存される (不変箇所)
- **browse 経路が構造的に無い** = リーク閉。critic-experiment が tools=Bash のみで guided.py 出力だけ見るのと同型

### Model Y の情報遮断

orchestrator が context を射影して coder に渡す：
- **許可:** フレーム + hole 位置 (新規ファイル: `src/coder-spec.md`) / coder が呼んでよい silo API surface の curated snippet
- **遮断 (物理削除/context 除去):** decisions.md:319/338・output/insights/2026-06-22_p2-case-study-*・backoff-sweep WAL・main-experiment §24/59 (勝ち筋の値・機序・利得・grid fitness)

---

## 1. diff 検疫層 (4a・新機構)

### 役割の位置付け (Model Y では)

フレーム byte 同値検査 = defense-in-depth (構成上保存されるため)。**主 gate 価値は hole エスケープ検査** (hole 内の生 #if/#else/#endif 指令・マーカー文字列を reject = フレームを壊す挿入を止める)。

唯一防壁にしない：
- #include 追加・TRACE 混入・任意バイト変更 → source_digest (assert_includes_match_head / assert_trace_diff_matches_head / preprocess 後ハッシュ / -Werror=undef) が既に fails-closed
- content 逸脱 (枝内の生 #if/#define/computed include・環境判別述語) → auditor + 規律6 に据え置き (text-gate しない、D30/D33)

**敵対検証で指摘: Baseline diff の取得が仕様未確定**
- unified diff を「HEAD vs working-tree」で取得する際、template を既に HEAD に適用しているか、original HEAD を基準にするか明記が必要
- #else 枝 (stock 枝) への改変が unified diff で「+」行に見えるため、hunk parse で hole 境界を正確に計算する必要
- 対策: diff_quarantine.py で以下を明文化 (D39 に参照):
  1. `git diff HEAD -- <file>` を取得 (template 適用済み HEAD vs current working-tree)
  2. @@ ハンク行域から #if/#else/#endif の行番号を解析
  3. 検証: 「変更行がすべて hole (#if 枝) の範囲内に収まるか」を 1 行ずつ検査
  4. Stock 枝 (#else 枝) への改変を検出 → frame-altered-stock-branch reject

### 実装仕様

**位置:** 新規 `orchestrator/campaign/diff_quarantine.py` (source_digest/patchharness と同格の fails-closed モジュール)

**動作:**
1. coder が返した提案枝コードを harness が template に挿入 → edit
2. `git diff` を unified diff format で取得
3. unified diff の @@ ハンクヘッダ (行域) + 固定テンプレ行 (BEGIN/END コメント・#if <AXIS>/#else/#endif) の完全一致で照合
   - 骨格 (マーカー + #if/#else/#endif + #else 枝) が template 適用済み HEAD と byte 同一 ✓
   - 変更行 ⊆ #if 合成枝内部 (hole) ✓
4. backslash-newline splice 等の C++ レキサ回避が効かない (diff 行構造と固定行を見るだけ) = 頑健

**実装で追加した硬化 (2026-07-07 敵対 red-team、詳細は worklog 2026-07-07 (2)):** 実装後の
red-team で「ハンクヘッダの行番号を信じると詐称・desync でフレーム/領域外を hole に誤帰属
できる」「未パース/不正 diff を空 diff と取り違えて fails-OPEN」「_same_file の過剰一致」の
3+1 クラスを発見・修正。追加機構 = (a) **HEAD アンカー検証** (context/削除行を申告行番号の
HEAD 内容と byte 照合。ハンクヘッダを信頼せず行番号を実体に錨づけ)、(b) **fail-closed パース**
(未パースヘッダ・カウント不整合・ハンク外 body を malformed で reject)、(c) _same_file を
normpath 完全一致 + traversal 拒否に厳密化、(d) rejection に第 4 subtype `malformed` 追加。
本節の「@@ ハンクヘッダ (行域) で照合」は正確には「HEAD アンカーで行番号を検証した上で照合」。

**rejection 新型 (S4 rejection):**

structured digest 形式 (D37 パターンに従う、規律3):
```json
{
  "rejection_type": "diff-quarantine",
  "subtype": "frame-altered" | "hole-escape" | "outside-region",
  "reason": "<explicit sub-type explanation>",
  "diff_region": "<unified diff hunk spec (line range)>",
  "template_diff_id": "<axis identifier>",
  "evidence": "<concrete violation (e.g., '行 X が hole 外にある')>"
}
```

具体例：
- `subtype: "hole-escape"` + `reason: "#else 枝 (stock 枝) への改変を検出"` + `evidence: "行 73 (#else 枝の新作処理) が hole 範囲外"`
- `subtype: "frame-altered"` + `reason: "マーカー行が template と一致しない"` + `evidence: "BEGIN マーカー行が期待値と異なる (byte offset)"`
- `subtype: "outside-region"` + `reason: "template 領域外のコードに変更あり"` + `evidence: "ファイル末尾の YCSB_SILO_TPCC_WORKLOAD 定義が改変"`

**配線 (規律3、片肺を作らない):**
- verify-red が正規経路で初発火する (D37 決定3) ので、diff-reject を S4 rejection digest の新型として配線
- critic/次手に structured reason で形状別の推奨方向を返す (型が明示されているので推論不要)

**hook 配線:** guard_write には入れない (PreToolUse で呼出元エージェント識別不能、content 検査は D33 削除)

---

## 2. coder リーク制御 (4b・最重要)

### 急所

decisions.md:319/338 等に sweet-spot literal (+38.3/+11.3%, 0-10us) が存在。coder が Read tool を持つため、**遮断が完全でないと失敗条件 c (利得が機械 sweep で再現 = LLM 固有価値なし) の判定が汚れる。**

### 実装戦略: Model Y (filesystem browse なし)

**coder の約束:**
- Read tool なし (filesystem browse 経路を構造的に閉じる)
- fresh context (本会話・prior turn history を見ない)
- 提案枝コードを構造化出力で返す (harness が挿入)

**敵対検証で指摘: Bash tool によるリーク可能性**
- Read 削除しても、Bash tool で `cat`, `grep` などのシェルコマンドが実行可能
- 現行設計は Read + Bash 両方削除と誤認する可能性がある
- Remediation (D39 で詳細決定):
  1. Bash tool は「許可」（orchestrator の Python harness 起動等で必要）
  2. ただし: coder は subagent として独立した read-only filesystem view で起動（orchestrator が seccomp/chroot で制限）
  3. OR: Bash tool を削除し、coder は「提案を構造化出力で返す」のみ（orchestrator 側で template 適用）
  4. 現行 design v1 は「Bash=削除」前提で進める。必要に応じて段 5 で緩和

**工数推定:** Bash 完全削除は coder の API 確認機能に影響するため、段 4 では削除、確認は orchestrator の入力に curated snippet で補う

**遮断対象 (物理削除または新規 .md で精選):**

新規 `src/coder-spec.md` に含める：
- Template 定義 (フレーム + hole マーカー)
- CCBench API surface (backoff 軸の型・関数シグネチャのみ。実装や具体値なし)
- 現行 config とテスト Workload の仕様

新規 `src/coder-leakproof-context.md` から除外：
- decisions.md:319/338 の sweet-spot value・機序・利得
- output/insights/2026-06-22_p2-case-study-backoff-synthesis.md (全文)
- backoff-sweep campaign の WAL/reports/profile JSON
- phase3.md 残存リスク節
- main-experiment §24/§59
- coder.md の kickoff 時の具体値例

**代わりに planner から受け取る (次節):**
- 方向のみ (値でなく「増加」「低下」の方向)
- uncertainty を含む (「検討価値あるが未検証」)

### coder.md 改訂

現行「値を発明しない・WAL/output/docs を読まない」(prompt 規律) を、critic-experiment 同型の物理分離に格上げ：
- 専用 context (`coder-leakproof-context.md`)
- fresh subagent (agent(prompt, {agentType: 'coder-v4-autonomous'}) で新規ロール)
- 提案を structured output で返す

---

## 3. planner.md (4c・読み方の設計)

### 位置付け

planner が設計方向を提案・coder が具体コード合成。これは **LLM 価値の実証点** (baseline 4 の帰無仮説判定軸)。planner が勝ち筋 literal を読むと「提案した」が「答えを読んだ」に化けて主実験の妥当性が崩れる。

### 実装仕様

**ロール (agent-architecture.md reserve から生成):**
- read-only + structured output (段 3 auditor と同型)
- tools=Read のみ (output/insights・ccbench-anatomy・API reference は OK)
- 強モデル (opus/high)

**入力:**
- CCBench backoff 軸の silo-local measurements (現行 baseline・last-run 性能)
- leading-indicator (cache miss rate・lock 被覆・IPC)
- whiteboard memory (評価済み設計 + uncertainty)

**出力:**
```json
{
  "proposals": [
    {
      "axis": "backoff",
      "direction": "increase" | "decrease" | "explore_both",
      "magnitude": "small" | "medium" | "large",
      "justification": "<leading-indicator に基づく推理。具体値なし>",
      "uncertainty": "<根拠の薄さ・競合仮説>"
    }
  ]
}
```

**ルールプロンプト:**
- "過去の評価済みだけを whiteboard で見る (未評価設計を再提案しない)"
- "具体値を提案するな (方向のみ)"
- "数字・個別 measurement は見るが、勝ち筋設計の要約・比較グラフ・後知恵の利得は見るな"

**whiteboard memory:**
- 却下設計を「評価済みのみ・事実 + uncertainty」で記録
- planner に見せる (P2-5 の自信ある早期停止誤収束 8/12, D21 を再演しない狭い範囲に絞る)

---

## 4. 自律ループ駆動 + D38 残 + 主実験配線

### iteration フロー (ハイブリッド)

ループ主導権 = **メインセッション** (orchestrator 役) が毎 iteration Task で fresh に planner→coder→auditor→critic を spawn。

```
1. planner: 方向を提案 (structured output)
2. coder: 提案枝コードを構造化出力で返す
3. orchestrator (Python):
   - 提案をテンプレに挿入 (edit)
   - diff 検疫 → S4 rejection? 
   - → YES: 「hole-escape」を structured reason で critic に報告・次 iteration へ
   - → NO: pipeline.evaluate (verify+bench)
4. verify: red?
   - → YES: mutation-red ゲートで assert 恒真性確認 (D38 残タスク)
   - → NO: bench run
5. critic: 帰属 (whiteboard を消費・次方向を推奨) + 停止条件の判定
6. auditor: 監査 (任意・決定3 段 4 では mutation-red 駆動役が主)
7. whiteboard 更新 + 次 iteration または停止判定
```

**停止条件の形式 (D39 で詳細決定):**

**収束:**
- planner が同一軸・同一方向・magnitude ≤ small の proposal を 3 回連続 → 段 4 完了
- 異なる magnitude (small→medium→large) の段階的変化は「異なる提案」と扱う (同一方向但し magnitude 変化を追跡)

**逆方向:**
- critic が段階的に「逆方向有望」を 2 回以上推奨 (且つ前回の方向で性能改善なし) → exploration 枯渇

**予算枯渇:**
- Iteration budget = 10 iterations OR wall-clock 3600 sec (いずれか早い方)
- Budget 枯渇時の partial result: whiteboard を checkpoint で段 6 に継承 (段 6 で再開可能)
- 部分結果は「未査証」として記録 (certified finding の最終版ではない)

**whiteboard の粒度 (敵対検証で指摘: 構造的推論リスク):**
- 記録対象: 提案番号・評価結果 (成功/失敗)・performance delta (性能変化率, 具体値ではない)
- 記録禁止: なぜ失敗したかの機序的説明 (例: "hard margin を課す → 棄却理由から採用方法を逆算可能" リスク)
- Critic の帰属は「次方向の提案」+ leading-indicator のみ (棄却理由の技術的説明は含めない)

### D38 残消化

**(d) auditor が追加する assert の mutation 非恒真性:**
- mutation-red 汎用ゲート (orchestrator が毎回機械確認)
- ガード: `assert condition != invariant` (恒真条件は reject)

**(e) auditor 直接 Write は read-only 据え置きが正解:**
- path-scoped 執行は原理的に不能 (guard_write は caller 非識別)
- 段 3 の read-only を維持
- 提案を structured output で返し、orchestrator が人間レビュー gate 下で反映

### 主実験配線 (D39 事前登録との対応)

段 4 の中間結果は main-experiment 事前登録に従い「暫定」として報告：
- 段 4 で仕込む: baseline 3/4 の操作的定義・LLM ablation (critic 帰属あり/なし系列)
- floor 流用禁止・失敗条件の具体化
- **検証相 (seed×N + 長 extime) は main-experiment §65-66 が明示的に段 6** (段 4 でやらない)

---

## 5. 敵対検証: Open Questions

次セッションで以下を検証 (段 3 と同型)：

1. **diff 検疫のフレーム byte 同値検査の正確な形**
   - template 適用済み HEAD をどう錨にするか (patch 適用後の working-tree を基準にするか、HEAD の #else/骨格を baseline にするか)
   - マーカー id 複数化への拡張 (backoff 軸が 2+ に増えた場合)

2. **coder に filesystem browse を与えない駆動**
   - coder が API 確認に CCBench ソースを読む必要 (coder.md 現行で許可) とリーク遮断の両立
   - 構造化出力形 (提案枝コードのスキーマ) の正確な設計

3. **リーク制御の物理削除 vs 入力射影**
   - 勝ち筋 literal が decisions/docs に散在するのを coder から遮断する形
   - 専用 .md + fresh context で「読むな」を構造化。Read tool を外すと API 確認もできない矛盾の解法

4. **planner/coder/critic/auditor の 4 ロール自律ループの iteration 予算・停止条件・whiteboard の粒度**
   - ループをいつ止めるか (収束したか、逆方向になったか、予算尽きたか)
   - whiteboard に何を記録するか (評価済みだけか、提案全履歴か)

5. **diff-reject の S4 rejection 新型の形**
   - verify-red・liveness・integrity・lock 被覆に次ぐ第 5 形状か
   - reject の digest → critic feedback 経路の信号体

6. **段 4 で実走する最小変異軸**
   - kickoff は backoff 値 50 で人間が与えた
   - 段 4 は同じ backoff 軸で coder が値を自律発案する形か
   - 別軸 (sort など) は段 5 に据え置き

---

## 6. 実装順序

1. **コア (4a + 4b を密結合で):**
   - `src/coder-spec.md` (template + API + hole spec)
   - `src/coder-leakproof-context.md` (curated input)
   - `.claude/agents/coder-v4-autonomous.md` (新ロール定義)
   - `orchestrator/campaign/diff_quarantine.py` (diff 検疫 + S4 rejection)

2. **後続:**
   - `.claude/agents/planner-v4.md` (設計方向提案)
   - orchestrator loop (Python harness・iteration 制御)
   - mutation-red ゲート (D38 残)

3. **実走:**
   - 最小変異軸 (backoff 自律発案) で 1 iteration 実証
   - Open Questions 敵対検証
   - 中間結果を main-experiment に報告

---

## 人間待ち

- submodule `izanagi-trace` 028f34d の push (後続段 3 の write_set 被覆 assert) — この環境に認証なし (D16)
