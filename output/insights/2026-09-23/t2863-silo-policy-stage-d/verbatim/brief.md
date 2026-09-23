# 段 1 brief — [T-2863] silo-function-policy 段階 D (IR の機械偵察)

基準: wave worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/t2863-silo-policy-stage-d` (branch `dev-wave/t2863-silo-policy-stage-d`、起点 local main `cadaf3805`)。以下 C/ = orchestrator/campaign/、Q/ = orchestrator/tests/。

- **研究前進:** 関数単位の合成空間 (VLDB 方針 D2212 項 3) が、骨格内の最小方策 (待機 0・即 abort) に対して床 3% を超える地形を持つかの二値を得る。これが段階 E (LLM ループ) と比較試走 (設計 §5 の比較 A / B) の継続 / 見直しの人間判断の材料になる。完了判定 = 偵察結果 JSON + insight に二値と限定を凍結し、ユーザーへ提示。
- **scope (実装する):** (1) 設計 §5 の型付き有限 IR (入力 = abort 要因・lock 試行番号・状態 scalar、状態 ≤ 4 field、式 = 定数・比較・条件式・min/max・飽和加減算・有界 shift、深さ ≤ 4・node ≤ 64、出力 = 待機量・lock の action + 待機量・次状態) と、決定的な描画器 (出力は policy-C++ v1 の部分集合)。(2) 偵察用の有限部分空間の機械列挙 (16 点、下の P2)。(3) 偵察 driver: 段階 C の診断経路 (C/silo_policy_coverage.py の `prepare_policy` 4 段検査 → trace build → legacy verify + 性能構成 verify → TRACE=0 build → bench) を再利用し、bench を 5 rep にする。(4) login の機械検査: 列挙全点が構文検査・単独 TU compile を通り、UBSan harness (C/silo_policy_compile.py) を列挙全点に 1 回。
- **scope 外:** 乱択・進化・BO の演算子、比較試走、段階 E の driver・coder role・`.claude/agents/`、`pipeline.evaluate` / campaign layout / GeneratorId への接続、新しい gate・検査・台帳・reject 理由、balanced / read-heavy、既存 3 軸の受理集合の変更、push。
- **確定済みユーザー裁定:** 計算は投入前にタスク合計の node 時間 (job Elapse 単価) を示して確認 (D2212 項 4、2 node 時間以上は必須)。正しさゲート不変・規律 2 不変。偵察の具体勝ち点・順位・実装は後段 (coder/planner 入力) へ流さない、二値だけ (手順書 §3-D firewall)。継続 / 見直しは人間判断。実装面は Codex author (D95)。
- **不変条件:** 全点に legacy + 性能構成の verify、anomaly (非 certified) の点は即除外し地形に数えない。trace は compile 時除去 (TRACE=0 build の既存確認を流用)。診断 build は NON_ADMISSIBLE で certified 候補と称さない (D2226 項 5)。IR は §2.7 の受理契約を緩めない (IR の出力は契約の部分集合、契約側は不変)。上限 1000/50/32 は骨格のまま。

**親の provisional 裁定 (攻撃対象):**
- (P1) driver は新 module (例 C/silo_policy_recon.py) とし、段階 C の `prepare_policy` / `_build_variant` / `_run` / `_verify` を import して使う。`_source` は手書き方策の file 名しか受けないので、本文文字列を受ける形へ最小の一般化をする (既存 coverage / smoke の挙動と test は不変)。
- (P2) 列挙 = IR の構成要素に対応する 4 つの 2 値因子の完全要因 16 点。候補因子: lock 競合応答 (即 abort / 有界 retry)、abort 後待機の状態依存 (静的 / 連続 abort で増やし commit で戻す)、要因依存 (一様 / lock_conflict だけ待つ)、大きさ (小 / 大)。定数は段階 C の手書き方策の値 (5/10 µs、retry 上限) から結果を見る前に固定する。因子と定数は段 2 plan が IR の定義から導出し、段 3 が攻撃する。
- (P3) 対照 3 = (a) 骨格内の退化点 abort0 (待機 0・即 abort、比較の基準。軸 OFF の `B0-L-W0` と同じ意味論に骨格コストが乗る形 = trigger 偵察の ident_all に当たる)、(b) 軸 OFF の既知最良 `B0-L-W0` (BACK_OFF=0、骨格コストの別掲)、(c) 軸 OFF の stock (`s3_lock_coverage.STOCK_G`、BACK_OFF=1)。
- (P4) 二値 (結果を見る前に固定): 「床超地形あり」⇔ 両 verify certified かつ high-abort でない (abort 率が基準比 2 倍以下、D46 の判定不能規則の流用) IR 点のうち、5 rep 中央値が同 job の基準 (a) を 3% 超上回る点があり、その点と基準を別 job で再測しても 3% 超が再現する。再測は条件成立時だけ 1 job (trigger 偵察 D48 の cross-run 必須化の流用)。床超点がなければ「なし」。
- (P5) 動作点 = write-heavy (rratio 5、skew 0.9、1M records、48 threads、3 秒、5 rep、B-5 と同じ)、Pegasus、1 ノード 1 job。19 case を 2 job に割り (各 job に IR 8 点 + 対照 3)、同時投入する (1 ノード直列で 1 時間超を流さない規律)。
- (P6) 見積り (段 4 でユーザーへ): smoke の実測 793 秒 / 5 方策 ≈ 160 秒/方策 (bench 1 rep) を単価とし、bench 5 rep と write-heavy の verify 増を上乗せする。確定値は段 4 で出す。

**成果物の形:** C/silo_policy_ir.py (IR・描画・列挙)、C/silo_policy_recon.py (driver)、Q/test_silo_policy_ir.py、Q/test_silo_policy_recon.py、必要な既存登録簿 (spawn site・materializer 登録簿・build authority) の追随。結果 JSON = `output/env/pegasus/calibration/silo_function_policy_recon*.json`、insight = `output/insights/2026-09-23/t2863-silo-policy-stage-d/README.md`。

**分割方針:** 単位 A (IR + 列挙 + test、login 検査) → 単位 B (driver + 登録簿追随 + test、A に依存)。所有 path は素集合。受入・実測環境 = Pegasus (worklog の所在どおり)、焦点走は run_tests の dispatch。
