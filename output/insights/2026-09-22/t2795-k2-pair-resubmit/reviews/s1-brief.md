# 段 1 brief — [T-2795] K2 同 job pair 再投入 (+ 成立時 4 巡目 1 job) (2026-09-22 08:5x JST、mtime で確認)

- **研究前進:** 論文ストーリー B-6 (K2 手動 loop) の「同 job stock 対照は未達」(3 巡 + pair 初投入、critic R0 が 4 度) を、修復済み pair driver (D2205) の実機 1 走で初めて埋める。
  完了判定 = pair 走の WAL で候補 certified ∧ stock `outcome=certified-stock` (variant = stock genome の id ∧ BUILD_START `src_token == "stock"` ∧ certified ∧ 非 abort)。成立時は 4 巡目 1 job の WAL で同判定。
- **確定裁定:** D2211 項 1 (pair 再投入 1 job を認可、成立時 4 巡目 1 job、不成立は D2187 の停止規則、経路 H = D1777、node 時間見積り、epoch 差と派生入力の限定の開示)、
  D2194 項 2 (4 巡目入力 = 択 A)、D2205 (pair mode)、D2172 項 3 (4 巡目 = 新規生成 1 回 + 同 job stock 1 本、再投入なし)、第 31 回 項 1 (見積りは job Elapse の実測、2 未満は確認待ちにしない)。
- **scope:** (1) 着手時の local main 固定 SHA から job root に submit-tree 2 本 (pair 用・4 巡目用、別 out_root = claim / WAL を分ける) を切り、submodule だけ PIN `511c9538…` へ checkout (gitlink は commit しない)、third-party hydrate。
  (2) pair job 1 本 (候補 = round 3 `materials/proposal-4.json` value 10、K2 env は前回と同じ、`IZANAGI_S4_STOCK_CONTROL=1`)。(3) WAL で判定。
  (4) 成立なら択 A で planner-5 / coder-5 入力を production 関数で組み、登録 role (planner-v4 / coder-v4-autonomous-k2) へ 1 回ずつ送付、proposal-5 を login の production 検査 3 本に通して pair job 2 本目。
  (5) 不成立なら 4 巡目を投げず停止・報告。(6) 記録 (insight 新 dir、round 3 README 末尾に追記、phase3 に 1 行、worklog fragment)。
- **scope 外:** gate・検査・台帳の追加、launcher / claim / harness の変更、critic-4・AO 取込み・層 3 レポート (次の一手へ)、`tools/pegasus/README.md` §7 の pair 記述 (旧 2 起動のまま、観測として記録のみ)、`submit-tree-pair` (lock 済み原本) への接触。
- **不変条件:** 規律 2 (verifier certified が gate、anomaly 即 reject、判定は WAL outcome で job rc から作らない)、規律 6 (役割入力の射影は data)、規律 7 (3 巡・pair 初投入の記録は不変)、再投入なし、claim / WAL / lock 原本を削除・退避しない。
- **(P1)** 4 巡目入力は択 A 厳守: whiteboard は run-summary の `loop_state` を `state_from_dict` で読んだ状態から harness の射影関数で作る (checkpoint として driver に load させない)。
  `current_perf` / baseline = run-summary の bench (815,983 tps / 9.065 %)、診断 = critic-3 逐語、knowledge-input = round 3 materials、leakproof_context = round 3 `coder-input-4.json` の同 field。**pair 再投入の結果は planner-5 / coder-5 に渡さない** (択 C の混在回避)。
- **(P2)** coder-5 の提案は production 検査 3 本を通れば値に関わらずそのまま評価する (既知値 10 / 20 / 25 でも再抽選・除外しない、既知値かどうかは記録する)。検査で拒否されたら再生成せず 4 巡目は投げない。
- **(P3)** `prior_critic_reverse` は親の解釈で False (proposal-4 = decrease、critic-3 R1 = decrease)。classification env は coder-5 の自己申告値、de novo は false。
- **(P4)** 見積り: pair job は prologue (前回 34 秒) + 候補評価 + stock 評価 (別 checkout)。構成要素の実測 (候補のみ job 69〜432 秒) から 1 job 3〜15 分と置く (外挿を含む仮定、D2211 の注意どおり実測扱いしない)。
  受入 1 回 ≈ 0.25 node 時間 × 最大 3 回。合計 ≈ 0.35〜1.25 node 時間 < 2 → 確認不要。pair 1 本目の実測 Elapse で 4 巡目投入前に見積りを取り直し、2 以上なら確認を取る。LLM 直列時間 = role 2 回 + read-only review 1 本。
- **段構成:** 軽量版。実装差分ゼロ・受理集合不変なので段 2・3 は省略、段 4 は「実装しない」、段 6 は read-only レビュー 1 本 (一次資料から事実を再抽出する docs のため DW-C00 で必須)。変異は免除 (DW-S04)、受入全走は行う。
- **受入・実測環境:** 実測 = Pegasus 計算ノード (gen_S、1 node)、投入は login から。受入 = `tools/dev_wave_wait.py acceptance` (門番付き)。
- **分割:** 子は段 6 の read-only レビュー 1 本だけ。role 呼出し (planner-5 / coder-5) は登録 role の新規 context で行う (実装子ではない)。
