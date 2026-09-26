# 段 1 brief — [T-2865] silo-function-policy 軸 段階 E (2026-09-26、親)

repo path はすべて worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e` 配下 (起点 local main `6d198ca8a`)。

## 研究前進
関数単位の合成空間 (D2212 項 3、D2214) で LLM が方策を書き、pipeline.evaluate で毎回検証されるループの入口を作る。これが無いと LLM 候補がこの軸の pipeline に入れず、段階 F (実 LLM 系列、ComSys 向け最初の LLM×C++ 結果の候補) が始められない。
完了判定: (1) 兄弟 driver が C++ 形と IR 形の proposal を、検疫 → effect gate → 型付き構文検査 → 単独 TU compile → auditor digest gate → pipeline.evaluate (legacy + 性能構成 verify) の順に通す。(2) coder role 2 本と auditor 改訂がユーザー承認のうえ登録簿に載る。(3) runbook が F の実走前ゲートと 1 iteration の手順を持つ。(4) §7.4 型の test が緑。

## 確定済み裁定 (変えない)
- D2214 全項 (特に決定 7・8: planner を外す、coder は C++ 版と IR 版、justification は台帳のみで critic と次の coder に渡さない、LLM 由来は auditor digest gate、`.claude/agents/` はユーザー明示承認)。
- D2243 項 1: E へ進める。小比較 (D2240) の点 ID・因子・比・順位は coder / planner の入力へ渡さない。後段へ渡すのは段階 D の `output/env/pegasus/calibration/silo_function_policy_recon/projection.json` の二値と射程文だけ。E の計算投入は図 1 枚あたりの node 時間を示し、検査込み合計 2 node 時間以上なら投入前に確認。
- 設計 §4 の build admission: LLM×C++・LLM×IR の候補は CLI opt-in 付き `CODER_AUTHORED`。`HUMAN_REVIEWED` にしない。
- 段階 F (実 LLM iteration) は別 session。本 wave で LLM を spawn して系列を回さない。

## 不変条件
- 規律 1〜3: anomaly は即 reject、trace は compile 時除去、verify は毎候補・結果は構造化して次の入力へ。新しい reject 閾値を作らない (設計 §3.2)。
- 既存 3 軸 (backoff・sort・trigger) と段階 C/D の診断経路の受理集合を変えない。共有 `quarantine()` への追加は marker `silo-function-policy` の分岐に閉じる。
- submodule pin・`pin.CURRENT_PIN`・骨格 patch・api header・`silo_policy_grammar` / `silo_policy_compile` の受理契約は変えない。
- coder 入力は構造で閉じる: projection.json から読むのは `binary` と `scope` だけ。段階 D の aggregate / initial / compare、D2240 の insight は driver が読まない。
- 仮想リスク向けの gate・検査・台帳・一般化は足さない (公平性の機械観測、候補ごとの sanitizer、TRACE 計数、非 LLM IR arm・比較 harness は scope 外)。

## 親の provisional 裁定 (攻撃対象)
- (P1) 構文検査と単独 TU compile は、共有 `p3_s4_loop.quarantine()` (p3_s4_loop.py:737-875) に `marker_id == axis.MARKER_ID` の分岐として足す (sort の :851 と同型、設計 §4)。段階 C の `silo_policy_coverage.prepare_policy` (:279-305) は変えない。
- (P2) planner が無いので停止は予算 (iteration / walltime) と reverse 枯渇だけ。収束判定 (p3_s4_loop.py:1386-1389、direction / magnitude 依存) は使わない。whiteboard (`L.project_whiteboard` は planner 必須) は使わず、自系列の履歴 (候補本文・結果分類・reject code・verifier の構造化 digest・critic 診断) を driver 専用の記録から射影する。`LoopState` に軸固有 field を足さない。
- (P3) IR 形は `silo_policy_ir` に JSON codec (parse / serialize、未知 key・型違反は例外) を足し、parse → `validate_ir` → `render_policy` → C++ 形と同じ 4 段検査 → auditor gate の順に通す。
- (P4) proposal schema は planner なしの閉じた top `{coder, auditor}` (+ `prior_critic_reverse` 任意)。`projection_guard` に C++ 形・IR 形の coder 契約を足す。value は存在しない。
- (P5) firewall の機械化 = coder 入力を組む関数を driver に 1 つ置き、projection.json は key 集合を完全一致で検査して `binary`・`scope` だけ出す。自系列履歴から justification を落とす。test で「入力の key 集合」「justification 不在」「段階 D の他 file を変えても入力 bytes 不変」を固定する。字面 tripwire は足さない。
- (P6) `default_cfg` の verify は `VERIFY_LEGACY_PLUS_PERFORMANCE` (pipeline.py:173、loop.py:322)、性能構成は設計 §7 の動作点 (1M records / 48 threads / skew 0.9 / 3 秒 / 5 rep、write-heavy 初手)。worktree 隔離は既定 ON。
- (P7) role は `coder-v4-autonomous-policy` (C++) と `coder-v4-autonomous-policy-ir` (IR) を新設、auditor.md は設計 §4 の型 22〜26 追加と型 17〜21 免除段落の射程修正。codex_roles の manifest / adapters / review_ledger (EXPECTED_ROLE_COUNT 14→16 ほか) / policy / check_codex_agents / test を追随。具体差分は段 5 で Codex author が書き、ユーザー明示承認の後にだけ統合する。
- (P8) live 確認: 手書き方策 (C++ 形 1・IR 形 1、非 LLM) で `--run-iteration` を計算ノードで各 1 回。auditor は既存登録の auditor role を実 spawn (自己生成しない)。見積りは段 4 で job Elapse の実測単価から出す。

## 成果物の形
driver `orchestrator/campaign/p3_s4_loop_policy.py` + test、`silo_policy_ir` の JSON codec + test、`p3_s4_loop.quarantine` の分岐と `projection_guard` の契約 + test、role 2 本と auditor 改訂と登録簿 (承認後)、runbook `docs/phase3-s9-policy-runbook.md` (名前は plan で確定)、insight と台帳 fragment。

## 分割方針
単位 A = IR codec (silo_policy_ir.py と test)。単位 B = 共有面 (p3_s4_loop.quarantine 分岐・projection_guard 契約と test)。単位 C = driver と test (A・B の interface に依存、interface は plan で固定)。単位 D = role 2 本・auditor・codex_roles 登録簿 (C の入力 schema に依存、承認待ち)。runbook と docs は親。

## 既存被覆 (純増の確認)
decisions: D2214 (設計)・D2226 (段階 C)・段階 D の D・D2240・D2243。failures: 型タグ [恒真ゲート] [ドリフト] [consumer 取り残し] を攻撃面に含める。p3_s4_loop_sort.py (895 行) と test (1998 行) が型。driver・role・runbook はこの軸で未作成 (棚卸し実測)。

## 受入・実測環境
Pegasus。焦点走と受入は計算ノード (`tools/dev_wave_wait.py acceptance --lease-optional`)、login では build しない。
