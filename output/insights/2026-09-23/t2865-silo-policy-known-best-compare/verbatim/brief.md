# [T-2865] 段 1 brief (親) — silo-function-policy 軸の既知最良との小比較

- 研究前進: D2235 項 7。段階 D (D2234) の二値は退化点 abort0 比で易しく、固定 16 点に既知最良 (stock・B0-L-W0・調整済み静的 backoff) を超える点があるかは未測。同じ 8 job で同 job 比較を 1 回とり、段階 E (D2214、LLM ループ) へ進むかのユーザー判断材料にする。完了 = insight に「16 点のうち同 job の最良参照を 3% 超えた点の数 (再測の扱い込み)」と限定を書き、ユーザーへ再提示。
- 確定裁定: D2235 項 7 択 (b) (authority user)、D2234 (IR・16 点・8 組割付 job_of・計測構成・firewall)、D2212 項 4 (検査込み 2 node 時間以上は投入前にユーザー確認)、D2214 (段階 E・.claude/agents/ は scope 外)。
- 不変条件: 規律 2 (両 verify certified でない点は比較から除外、verifier・4 段検査・trace0 確認は不変)。規律 1 (bench は TRACE=0)。firewall: 比較の点 ID・比・順位は insight と repo 内の詳細 JSON だけに置き、projection.json は変えず新しい投影も作らない。段階 D の記録 (initial-*.json・aggregate.json・projection.json) は書き換えない (規律 7)。
- 実測で確かめた前提:
  - 調整済み静的 backoff = write-heavy で 10 µs (`BACK_OFF=1, BACKOFF_FIXED=10` + locks._BASE)。出所 = output/s1-freeze/known_axes_freeze.json の write-heavy backoff_fixed_best、A-2 正式認証 rr5-fixed10、D2160、docs/unseen-condition-transfer-preregistration.md の R2。いずれも旧 pin (d706650c / 511c9538)。設計 insight 2026-09-21/silo-function-synthesis-space §5 が「元の適用方法で再評価」と定める → 本走が現 pin e9e477ca での再評価になる。
  - 「元の適用方法」= patches/silo-backoff-fixed.patch (cmake/Options.cmake + include/backoff.hh) を stock 木へ当てる macro 経路。現 pin へ `patch --dry-run -p1` rc=0 (offset・fuzz なし)。関数方策の骨格 patch は当てない (D2160 の identity と同じ)。
  - 現行の build 経路は BACKOFF_FIXED を扱えない: silo_policy_coverage.py `_source` (stock は無 patch) と `_build_variant` (stock_backoff ∈ {0,1}、genome に BACKOFF_FIXED なし)。patch 未適用で `-DCCBENCH_BACKOFF_FIXED` を渡しても無言で適応 backoff に落ちうる (推測) → 適用済み木の marker 確認 (backoff_extended_sweep._assert_backoff_fixed_materialized と同じ marker) と owner TU の compile command に `BACKOFF_FIXED=10` があることの記録を行に残す。
- 変更面 (実アンカー):
  | file | 箇所 | 変更 |
  |---|---|---|
  | orchestrator/campaign/silo_policy_coverage.py | `_source` (policy=="stock" 分岐) | stock 木へ silo-backoff-fixed.patch を当てる引数 |
  | 同 | `_build_variant` (stock_backoff guard・stock_genome) | stock 時だけ BACKOFF_FIXED を足す引数 |
  | orchestrator/campaign/silo_policy_recon.py | `_cases`・`_one`・`main` | phase `compare` (job 0..7 = job_of の 2 点 + abort0 + stock + B0-L-W0 + fixed10)、role `fixed10` |
  | 同 | 新 subcommand `compare-aggregate` | 8 job の照合 (段階 D aggregate と同じ照合) と同 job 比の集計、投影は作らない |
  | orchestrator/tests/test_silo_policy_recon.py (+ coverage の test) | — | 上記の test |
- (P1) 親の provisional・攻撃対象: 比較 = 各 IR 点の 5 rep 中央値 ÷ 同 job の参照 3 本の中央値の最大。「超える」= 比 > 1.03 (段階 D と同じ暫定床、較正なし)。除外は段階 D と同じ (両 verify certified・trace0 clean・5 rep 有効・high-abort は同 job abort0 比 2 倍超)。参照のどれかが欠測なら「最良参照」は null で false にしない。
- (P2) job 内の実行順は job 番号で 6 方策を巡回 (位置の交絡を避ける)。段階 D は制御を末尾に置いた。
- (P3) 再測: 「超える」点が 1 つ以上なら比の最大の 1 点だけを別 job (6 方策、順序反転) で 1 回再測し、再現の有無を併記。0 点なら再測しない。この択はユーザーの計算確認に含めて諮る。
- (P4) 計算見積り (投入前にユーザー確認): 段階 D 実測 = 3 方策 job 428〜436 秒、4 方策 job 506〜564 秒 → 1 方策 ≈ 70〜130 秒。6 方策 job ≈ 650〜830 秒 × 8 = 1.45〜1.84 node h、再測 1 job ≈ 0.23、焦点走 ≈ 0.07、変異 matrix ≈ 0.3〜0.56、受入 ≈ 0.25 → 合計 ≈ 2.1〜2.9 node h (walltime 上限 30 分 × job で上限 ≈ 5 超)。2 を越えるので計測の投入前に確認する。実装・焦点走・変異は線の下 (累計 < 1) で先に進める。
- 却下: 段階 D の結果 JSON の参照値を流用 (stock・B0-L-W0 は 2 job にしか無く fixed10 は無い)。新しい job body / 投入 script (admission 未登録、D2234 と同じ理由)。投影 JSON の新設 (firewall 上不要)。
- 分割: 実装子 1 本 (所有 = 上記 3 file + test)。計測木 8 本 (+再測 1) は段階 D と同じ detached worktree + generic dispatch。
- 受入・実測環境: Pegasus gen_S (runbook docs/pegasus-runbook.md)、焦点走・変異・受入は dispatch。
