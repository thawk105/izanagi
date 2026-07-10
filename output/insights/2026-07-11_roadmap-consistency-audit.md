# roadmap.md 整合監査 (2026-07-11) — 一次資料

**依頼:** roadmap.md が最新状況を反映しているか + 現状の作業が roadmap から逸脱していないかの双方向調査 (ユーザー依頼)。
**基準:** main = f0008b6 (clean)。roadmap 最終更新 = 95b6a70 (2026-07-10 08:38, D44 反映)。worklog 末尾 = 2026-07-10 (20)。
**方法:** 独立コンテキスト 7 レンズ照合 (節別 5: §1-2 / §3 / §4-6+10 / §7-8 / §9、逆方向 2: D44 以後の設計判断 / リポジトリ実態) + finding ごとの敵対検証 8 本 (反証優先、D35 誤検出チェック込み)。計 15 エージェント、約 68 万 token。実行記録 = workflow run wf_bf2812c5-518 (セッション transcript)。
**判定基準:** 可変状態 (完了状況・現在地) が roadmap に無いのは仕様 (D35) — 指摘対象は戦略・設計レベルの不整合のみ。

## 総括

- **逸脱 (deviation) = 0 件。** 現状の作業 (段 5〜8a、tools/plotting/ 新設含む) は roadmap の方針・スコープ (§10) の内側。
- **D45〜D49 はいずれも戦術決定** (段 8a は §2 の D44 予約の実装・具体化) で、roadmap 改訂を要する未反映の戦略決定は無い。
- **改訂セレモニーも正当** — v1 以後の roadmap 改訂 (約 19 コミット) はすべて協議改訂の類型 (版凍結不要、roadmap-history/README.md の免除規約どおり)。
- 見つかったのは roadmap 側の**局所的な陳腐化 4 件 (real) + 軽微 2 件 (partially-real)**。中核は D19 と D38/D43 への未追随の 2 箇所 (いずれも medium、下記 1・2)。

## real (4 件)

### 1. [contradiction / medium] §4 — noise floor の within-run / between-run 分離 (D19) 未追随
- roadmap.md:250 (§4) は calibrator の noise floor (「確定条件で baseline を**連続 N 回**」= 構造上 within-run) を「§3.6(4) の分布比較が『差なし』に丸める閾値の根拠になる」と直結させている。
- しかし §3.6(3') (roadmap.md:183-184) と D19 (decisions.md「BETWEEN_RUN_CV = 0.030」) で、採否 floor は between-run に分離済み — within-run の流用は「偽 faster」を出すとして D19 が塞いだ当の経路。正本側 (.claude/agents/calibrator.md:33、orchestrator/campaign/between_run_floor.py) は分離済みで、**roadmap 内部 (§3.6 対 §4) の矛盾**として残存。
- 修正案: §4 の当該文を「within-run CV は 1 測定の品質ゲート用。採否の丸め閾値は between-run floor (§3.6(3')、別ドライバで確定) を使う」に改める。

### 2. [stale / medium] §3.4 item2 — auditor 記述が D38 決定 3 (read-only 構造隔離) 未追随
- roadmap.md:159 は「adversarial auditor — …不変条件違反を見つけて**テストを追加**」と書くが、確定設計では auditor は read-only で**提案のみ**返し、反映は orchestrator の人間レビュー gate (D38 決定 3、.claude/agents/auditor.md)。
- 「auditor が既存テストを弱める書き込みを構造的に不能にする」ことが reward hacking 防壁の核であり、§3.4 (防壁を説く当の節) がその核と逆に読める記述を残すのは読者 (将来の実装者) を誤導する。同 §3.4 item4 が verifier のツール隔離を戦略レベルで明記している以上、auditor の隔離も同じ高度に属する。
- 修正案: 「違反を検出し、それを捕らえる positive control テストを設計・**提案**する (read-only。反映は orchestrator の人間レビュー gate)」。

### 3. [stale / low] §9 — Phase 3 のサブエージェント枚挙に axis-proposer が無い
- roadmap.md:317 は「+ planner/coder (分離), auditor (reward hack監査)」。§9 は Phase ごとにサブエージェントを名指しで枚挙する体裁 (P1: verifier/calibrator、P2: +critic/profiler) を取るのに、段 8a で常設化した axis-proposer (agent-architecture.md §axis-proposer、D47) が漏れている。機構自体は §2 の D44 予約 (8a) にあるため low。
- 修正案: 「, axis-proposer (軸提案のループ内化、8a)」を追記。

### 4. [stale / low] 冒頭「版: v1 (初期設計)」の表示と実態のずれ
- 改訂はすべて協議改訂で版凍結不要 (規約どおり、違反ではない)。ただし「版: v1 (初期設計)」+「過去の版は凍結保存されており」という冒頭文は、実質 19 コミット改訂され続けた文書の実態に対して読者の期待とずれる (roadmap-history/ には v1-initial.md のみ)。
- 修正案 (任意): 「版: v1 系 (協議改訂は版番号を上げない — 改訂履歴は git log、自律改訂のみ roadmap-history/ に凍結)」のような一文に。

## partially-real (2 件 — 検証で範囲が縮小、修正後 low)

### 5. [stale / low] §7 — 関連研究の括弧内列挙が D35 分離時 (2026-07-05) の 11 件のまま
- roadmap.md:281-282 の列挙に、以後 related-work/ に加わった ShinkaEvolve (最直接の比較対象)・ATCC (最新競合)・DGM 等 (現在 19 件) が無く、この 3 つは roadmap 全文にも痕跡なし。§7 は related-work/ へのポインタなので致命ではないが、列挙を索引として読むと見落とす。
- 修正案: 列挙に「など」を付すか、主要追加分 (ShinkaEvolve/ATCC) だけ足す。

### 6. [stale / low] §8 —「誰も single-node の CC プロトコルの serializability を対象にしていない」(roadmap.md:290)
- 文脈上は bespoke 自動合成系譜 (Jitskit/IDS/VibeServe) 内の空白の話で、学習型 CC (Polyjuice/CCaaLF→NeurCC/ATCC) は §2 で認知済み + 精密な差別化は related-work 7.1/7.6 が担う (真の空白は「対象」でなく「方式の交点」)。ただし §8 単独で読むと過大主張に見える。
- 修正案: 当該文に「(bespoke 合成系譜内。学習型 CC との差別化は related-work 7.1/7.6)」の限定を付す。

## refuted (2 件 — 棄却)

- §3.4 item2 の「N iteration ごと」という周期的枠付けが機構化 (per-variant 機械 gate、D43) と矛盾 → **棄却**: 助言的記述と機械 gate 化は矛盾せず、詳細は phase doc 層の管轄。
- §2 層3 の説明生成例が移植 (b2) 一色で b1 実証と齟齬 → **棄却**: D32 が移植/カタログ化を層3 の説明生成資産として意図的に narrative へ温存した (decisions.md D32)。例示の温存は設計判断どおり。

## 還元判断

roadmap の修正 6 点 (real 4 + 縮小後 2) はいずれも「学んだ事実の反映」= 軽微改訂の類型 (セレモニー不要・確認不要で進めてよい類) だが、本セッションは調査依頼のためまず未修正で報告した。**→ 2026-07-11 ユーザー承認により 6 点すべて反映済み (協議改訂 — 版凍結不要の類型)。**
