# [T-142] 段 1 brief — テスト価値の二層化 (進化探索ループの評価順序)

repo (git worktree): /home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate
基準コミット: 78eedcb (clean)。branch: worktree-dev-wave-t088-python-gate

## scope

進化探索ループ (p3_s4 系 3 loop → `campaign/loop.py:run_campaign` → `campaign/pipeline.py:evaluate`) の
評価を二層化する。安い層 (legacy verify ≈12 s + bench ≈2.5 s) は毎 iteration、重い層 (S2 verify ≈111 s) は
良い候補だけに走らせる。受理集合 (certified の判定基準 = 全 verify 構成 AND) は変えない。
開発テストスイート (orchestrator/tests) の二層化は scope 外。

## 確定済みユーザー裁定

- T-142 採用 (docs/worklog.md エントリ (36)、裁定 (3))。**条件 = 省略する検査が受理集合を
  変えないことを機械的に示せる範囲に限る**。出自 = output/insights/2026-07-27_external-consultation-scope-and-axes.md
  提言 3 (提言 8 の lazy 検証保留と区別: 通過基準を下げるのは禁止、同じ基準へ至る検査の順序最適化は可)
- D36 (docs/decisions.md:869): S2 構成は perf 完全一致・縮小なし。verify 2 本立て (legacy=検出力担当、
  S2=データパス被覆担当)。COMMIT payload に通過 verify 構成タグ列を焼き込み、AND 判定は wal/replay の
  共通ヘルパ 1 箇所。S2 on/off は search_config 経由で campaign_id に反映 (別 campaign 化)
- D58 (docs/decisions.md:2268): bench-first screening v2 実装済み。適用先は偵察 sweep / 8b の opt-in に
  限定、「S-1、検証相、LLM loop、基準点・floor 再実測には適用しない」。適用先拡大は別裁定を要する —
  **T-142 の採用裁定がこの「別裁定」に相当し、上記条件がその制約**

## 実測 (裁定前提、既存 WAL の ts 差分)

output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/runs/wal.jsonl (2 variant):
- S2 verify ≈ 111〜116 s / iteration が支配的
- legacy verify ≈ 12 s、bench ≈ 2.5 s (bench_max_rounds=1 系)、build cached 0.3 s / uncached 45 s
- D58 の記録値とも整合 (verify 120〜250 s、bench 〜18 s / variant)

## 不変条件 (絶対規律 2/3、D36、D58)

1. S2 構成そのものは縮小しない (D36 決定 1)。verifier の検査内容・閾値も不変
2. certified/COMMIT は全 verify 構成通過後だけ (D36 決定 4-2 の AND ヘルパ)
3. legacy verifier は毎 iteration 走り、構造化 red (どの構成でどう壊れたか) を critic へ返す (規律 3)
4. screen/defer された未認証の性能値を正式結果・探索射影・critic の勝ち筋へ混入させない (D58)
5. 二層化 on/off は search_config 焼き込みで campaign-id 分離 (D36 決定 4-1、ident.verify_screening_preimage の流儀)
6. 既定 off・明示 opt-in (test_screening_opt_in.py の既存境界と同じ流儀)

## provisional 裁定 (P 採番 = 親の暫定であり攻撃対象)

- (P1) 実装対象は campaign 進化ループであり dev テストスイートではない (根拠 = 裁定文言「進化探索の毎ループ」)
- (P2) 実装形の第一候補 = evaluate() の pass 順序を legacy → bench → S2 へ再配置し、S2 省略は D58 の
  screening 機構 (ScreeningConfig / SCREEN_REJECTION_REASON) を再利用して p3 loop 系へ opt-in 配線
- (P3) 「機械的に示せる」の充足形 = COMMIT AND ゲートの既存機械保証 + positive control
  (legacy 緑 + bench 良 + S2 赤 → COMMIT 不能) + 未認証候補の選択/報告不参入 assert。既存被覆との差分だけ純増
- (P4) 番人テスト orchestrator/tests/test_screening_opt_in.py:19
  test_autonomous_loop_has_no_screening_wiring は裁定 (3) を根拠に「既定 off・opt-in・campaign-id 分離」を
  assert する形へ意図的更新 (無言で削除しない)

## 主要コード所在 (2026-07-28 時点、基準コミット 78eedcb)

- orchestrator/campaign/pipeline.py:363 evaluate() 本体。:424 passes 構築 (legacy が先頭、extra が後)。
  :539 _run_one_pass。:604-644 screening 経路 (baseline 鮮度、bench 先行、floor/high-abort 棄却)。
  :76 SCREEN_REJECTION_REASON。:97 ScreeningConfig。:65-84 S2 定数と s2_correctness_workload
- orchestrator/campaign/loop.py:43 run_campaign (screening 引数なし = 番人テストの対象)。:59 S2 組み立て
- orchestrator/campaign/ident.py:52 verify_screening_preimage、:100 campaign_id
- orchestrator/campaign/screening_driver.py (D58 の既存 opt-in driver、evaluate 直呼び)
- orchestrator/campaign/p3_s4_loop.py:590 run_one_iteration (run_campaign 呼び出しは :597 コメント参照)。
  p3_s4_loop_sort.py:184 / p3_s4_loop_trigger_gating.py:342 が VERIFY_LEGACY_PLUS_S2 を search_config に設定。
  p3_s4_loop_trigger_gating.py:384 run_campaign 呼び出し
- orchestrator/tests/test_screening_opt_in.py:19 番人テスト。ほか被覆: test_campaign.py、
  test_bench_first_real_wal.py (consumer 回帰 fixture)、test_p3_s4_loop*.py、test_s8a_trigger_sweep.py 等
- critic 帰属系: orchestrator/critic/digest.py (rejection の読み手。screen 棄却の扱いは D58 の混入禁止に従う)

## 成果物の形

コード (pipeline/loop/p3 loop 配線 + テスト) + docs (worklog/insight、必要なら D 追補)。push なし。
受入全走 = 本 checkout の tools/run_tests.py。新規重計測なし (既存 WAL の ts 実測で足りる、規律 4)。
