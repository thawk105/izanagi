# Phase 2 — パラメータ探索

**目的:** CCBench の最適化フラグ空間を探索し、入力 workload に最速の CC 構成 (genome) を見つける。
roadmap §2 層2(a) **パラメータ粒度を主軸**。空間は有限 (silo 2^4→no-wait XOR 制約で 8、anatomy §3) なので
**初手は全探索**。全探索で得た最適を ground truth とし、LLM 誘導探索の到達速度を比較する
(roadmap §9 / 論文の図)。**この比較は P2-5 で実施済み = negative result: 誘導は機械的勾配 (貪欲) を超えず、
「論文の図」は「小空間ではフラグ探索が自明で価値は空間外の合成にある」の物語に転じた (P2-5 節・D21。
roadmap §2 に同旨の注記あり)**。

**副産物:** パラメータ variant は CCBench 由来のフラグ組み合わせなので理屈上**全部正しい** →
**verifier の大規模 sanity check** (Phase 1 verifier 信頼性の総仕上げ)。

**Phase 2 完了の定義:**
- silo 全 genome を実 fitness で評価し、workload 別の最速構成を WAL + 材料レポートで再現可能に特定できる
- 測定安定性 §3.6 (2)(4) が自動執行される (反復内 CV 閾値超で自動再測定→`unstable`、採否は分布比較)
- critic が leading indicators を読んで「次に試す方向」を構造化指示に変換できる
- 全探索 vs LLM 誘導の到達 iteration を比較したデータが出る

**サブエージェント:** + critic, profiler (`docs/agent-architecture.md` の仕様で実体化)

**環境:** 計測は linux-baremetal の確定 calibration (records=1m / 48 thread / skew0.9 / reps5、
within-run 変動係数 (CV = 標準偏差/平均) の実測 noise floor 2.28% = 1 測定の品質の目安 (remeasure/unstable
品質ゲートの発火閾値は 5% 据え置き = D19) / 採否 floor は between-run 3.0% (A2/D19)、
`output/env/linux-baremetal/calibration/`)。**性能計測は単一テナント直列**
(絶対規律4)。ビルド・trace 検証は並列可 (`lock.py` の bench_lock はベンチのみ排他)。

段階導入 (規律5): P2-0 から順に。各タスクの効果は ablation で測れるようにする。

---

## P2-0: 全 silo variant のビルド + verifier 大規模 sanity (タスク6 の残り) — 完了

パラメータ variant は理屈上全緑のはず = verifier の大規模 sanity。**計測なし** (do_bench=False)。
- [x] silo 8 genome を `genome.SILO_SPACE.enumerate()` で列挙し、loop で
      build(trace+perf)→verify→no-bench commit を回す
- [x] **8 genome 全て certified** を確認 (false-red が出たら verifier か genome 空間の不整合 →
      `output/insights/` に記録)。当初 12 から no-wait XOR 制約で 8 に縮小 (両 0=livelock を除外)。
      ※ P2-0 実行時 (2026-06-20) の sanity campaign WAL は成果物として未保存 (当時の一次記録は
      worklog と commit 15ec702)。同一 8 genome 空間の certified は P2-2 の WAL が on-disk で
      再証拠化している (Phase 2 完了監査 2026-07-03 で確認)
- [x] 規律1 再確認: 全 perf build に izanagi_trace symbol 0 (`nm`) — 一度きりの手動確認は
      Phase 1 完了監査 A4 で `buildcache._assert_no_trace_symbols` (新規/キャッシュヒット両経路の
      継続 assert、nm 不能時 fails-closed) に格上げされ吸収済み。完了監査 2026-07-03 が全 perf
      build 46 個の nm 走査 (漏れ 0、trace build では 6 シンボル = 検査の弁別力確認) で再裏取り

**完了条件:** silo 全 genome が certified。verifier が大量の正しい variant を緑と判定できる実証で、
Phase 1 の「赤を出せる」(タスク3) と対になる「緑を取りこぼさない」の大規模実証。

## P2-1: 測定安定性 (2)(4) の必須化 (§3.6) — 完了

Phase 1 で配線済みの (1)(3) (noise floor + 反復中央値・変動係数) の上に (2)(4) を積む (`orchestrator/calibrator/stability.py`)。
- [x] 外れ値→自動再測定 (`remeasure_until_stable`): 反復内の変動係数 (CV = 標準偏差/平均) > 閾値 (既定 5%)
      なら settle 後に測り直し。規定ラウンド (既定 3) で収束しなければ `unstable` フラグ
- [x] 採否は分布比較 (`compare`): noise floor 以下の差は「差なし」に丸め、超える差は Mann-Whitney U 検定で
      有意性判定 (重い統計機構は不要)
- [x] unstable variant は分布比較から除外 (呼び手が責任)。沈黙して 1 点採用しない
- [x] **A2 精緻化**: 採否の floor は **between-run** noise floor (別 run で測る variant/baseline の差の下限、3.0%)。
      within-run の変動係数の実測 noise floor (2.28%) は 1 測定の品質の目安で採否には使わない
      (remeasure/unstable 品質ゲートの発火閾値は 5% 据え置き = D19)。Mann-Whitney U は反復数が
      小さい (5) と完全分離で常に有意になる弱い sanity ゆえ、主防壁は between-run floor 丸め。floor 近傍
      (floor〜1.5×floor) の faster/slower は `near_floor` フラグを立て cross-run 再現で裏取り要とする (D19)

**完了条件:** 達成。変動係数が不安定な測定は自動で再測定/除外され、採否は点比較でなく分布比較 (between-run floor
丸め + Mann-Whitney U) で行われる。回帰テストは suite 全緑で担保 (本数はスナップショットで腐るため記載しない。最新は worklog 参照)。

## P2-2: silo 全探索 (最初の実探索) — 完了

- [x] loop を**実 fitness** (確定 calibration) で 8 genome 全評価 (直列・env=linux-baremetal)。
      3 workload × 8 = 24 評価が全て certified serializable・パイプライン abort (STAGE_ABORT) 0 件
      (トランザクション abort_rate は別物で、contention 域では当然非ゼロ — 例: write-heavy 勝者
      B0-L-W0 で 0.82。leading indicators として WAL に記録される正常な値)
- [x] 代表 workload (read-heavy=rratio95 / balanced=50 / write-heavy=5, skew0.9) ごとに最速構成を特定
- [x] 結果を D12 材料レポート (`campaigns/<id>/reports/`) + 横断 summary に射影

**完了条件:** 達成。全探索の最適構成が WAL (生 tps + 実行コマンド) + 材料レポートで再現可能に特定。
最速構成 = **read-heavy: B0-T-W0 / balanced・write-heavy: B0-L-W0** (B0-L-W0 が 2/3 で1位・read-heavy で
同点1位 = 全体最強)。知見: BACK_OFF=0 が支配、no-wait は contention 域で即abort が有利。LLM 探索 (P2-5) の
ground truth。途中で前セッションの孤児 livelock による計測汚染を検知・対処
(insight 2026-06-22_orphan-livelock-contaminated-measurement.md)。

## P2-3: leading indicators の WAL 記録 + critic 実体化 (§3.5) — 完了

throughput スカラーだけでは探索が 8-12 iteration で停滞する (Jitskit)。leading indicators を毎評価
記録し critic に渡す。
- [x] leading indicators (abort_rate / latency / llc_miss_rate / ipc) を fitness と一緒に WAL
      (STAGE_BENCH_DONE) に記録。abort_rate は no-wait/backoff の効果が直接出る CC-native 最重要指標
- [x] `critic.md` を agent-architecture 仕様で生成 (帰属→次手、**書き込みなし**) + 機械準備 `critic/digest.py`
      (genome 別 LI + フラグ軸の限界効果)
- [x] critic を実 LI に実走 → 設計選択に帰属 (BACK_OFF=1 は abort 減でも ipc 崩壊で遅い / no-wait は
      workload で L↔T 反転 / WAL は write 比率比例の純損) + recommend/avoid/uncertainty を構造化で返した

**完了条件:** 達成。critic が leading indicators (throughput 単独でない) から機序を推定し設計選択に帰属、
具体的な次手 (BACK_OFF=0 固定・no-wait 出し分け・新軸「中間 backoff」) を出した。ablation の原理
(L↔T 反転の見落としを critic が防ぐ) も提示。定量 ablation (critic 誘導 vs ランダムの到達 iter) は P2-5。
insight 2026-06-22_p2-3-critic-leading-indicator-attribution.md。

## P2-4: profiler 実体化 (二段構え) — 完了

- [x] `profiler.md` を agent-architecture 仕様で生成 (perf 実行・spin/lock/NUMA/IPC 解釈、書き込みなし)
- [x] screening 通過した上位 variant にだけ perf record (trace-disabled build, 規律1)。backoff ケーススタディの
      sweet-spot variant 群を対象に `perf record -e cycles,instructions`。診断ノブ `BACKOFF_NOINLINE` (inert patch) で
      spin を独立シンボル化し有用 IPC を分離 (`orchestrator/campaign/backoff_profile.py`)
- [x] many-core スケール懸念を診断し critic/層3 に渡した。profiler を実データで実走し
      hotspot/scale-risk/mechanism/uncertainty を構造化で返す ([P0] 機序純度を解消: sweet-spot で有用 IPC 一定 =
      total IPC 崩壊は純 spin 希釈、over-throttle で有用 IPC 二次低下。decisions D20 / insight 追記)

**完了条件:** 達成。profiler が backoff variant の many-core 機序 (spin 希釈・有用 IPC・over-throttle) を解釈して返し、
backoff ケーススタディの最後の穴 [P0]「なぜ速いか」を sweet-spot 域で機序的に閉じた。perf 下 tps は overhead 込みで
headline 非使用 (絶対値は stock build)、単一テナント直列 (規律4)。定量 ablation (profiler 有/無) は P2-5 と地続き。

## P2-5: LLM 誘導探索 vs 全探索 (Phase 2 の主実験) — 完了 (negative result)

silo 8 は実質 BACK_OFF=0 の 1 ビットで決まる自明空間ゆえ「誘導が速い」は構造的に主張不能 (read-heavy は
winner-tied set k=4=空間の半分で到達判定が無情報、k=1 でも完璧オラクル天井 = 2−k/N = 1.88 本 = 余地 2.62 本)。
よって主成果を **negative result + critic ablation** に定めた (ユーザー承認、設計を多エージェント workflow +
敵対的妥当性検証で固めた)。

- [x] critic-experiment エージェント (critic.md から最適解の literal を物理削除した中立版) で online 誘導ループを
      30 試行実走 (balanced/write-heavy 各12 + read-heavy 6)。fitness は P2-2 WAL replay で配る (新規直列計測ゼロ)。
      リーク制御 = 評価済みのみ digest + 実行時 assert + fresh context + 初手対称 (絶対規律6/D12)
- [x] 4 系列比較: 全探索 (**8 全部 = SILO_SPACE.enumerate()**、旧記述「12 全部」は誤り) / random (解析期待
      (N+1)/(k+1)) / critic 無し貪欲 (digest 勾配のみ、LLM なし) / 誘導 (LLM)。到達定義 = winner-tied set
      (equivalence class + floor 3.0%) 初到達、未到達は予算上限 N に算入
- [ ] (任意) cicada/oze 等に protocol を広げ空間拡大 — critic の価値実証の前提だが S1 (trace-hook 拡張) を要する
      ので Phase 3 隣接で判断

**完了条件:** 達成。誘導 (LLM) は機械的勾配 (critic 無し貪欲) で達成できる水準を超えず (balanced で
誘導 vs 貪欲 A=0.581・有意差なし)、deceptive 構造 (write-heavy、BACK_OFF=1 が実2位) では誤収束 **8/12**
で貪欲より有意に有害 (A=0.230, exact permutation p=2.5×10⁻⁴ — 初出の「p<10⁻⁴」は方式未記録の
過大表示で 2026-07-03 に厳密計算へ訂正、`search_baselines.exact_perm_pvalue_A`。Holm ×6 でも
有意で結論不変) = critic の「自信ある早期停止」が deceptive 帯で負債。
貪欲自体は balanced で random より有意に速い (a=0.533、ただし余地の 1 割) ので、「空間に余地が無い」の
でなく「LLM 固有の付加が貪欲から分離できない」が正確な主張。silo 8 では誘導の価値は実証できず空間拡大が
前提、という negative result を確率優越 a (D29 再校正済み — 旧 p_lt は系統バイアス) + 誤収束率で定量化。
P2-4 backoff 合成 (空間外で勝つ positive) との対比が Phase 2 の物語。
insight 2026-06-29_p2-5-guided-vs-enumeration.md (再校正追記あり) / decisions D21・D29。

---

## 当面の着手順

1. **P2-0** (verifier 大規模 sanity) — 計測なしで安全・高速。Phase 1 verifier 信頼性の総仕上げ。
2. **P2-1** (測定安定性ロジック) — machine 非依存の純ロジック + モックテスト (calibrator と同型)。
3. **P2-2** (実 fitness 全探索) — ここから本格的な実機計測 (直列)。

P2-3 以降 (critic/profiler/LLM 誘導) は探索の骨格が回り始めてから足す。

---

## Phase 3 着手前 must (Phase 1 完了監査 2026-06-28 が示した繰り延べ項目)

※ この一覧は Phase 3 引き継ぎ時点のスナップショット。消化状況の正本は phase3.md の must 表であり、
以後この一覧のステータスは更新しない (2026-07-05 の文書一貫性恒久対応)。

Phase 1 は完了条件を満たす (blocks なし) が「完璧」でなく、4軸監査で出た穴のうち **silo 探索 (Phase 2) を
脅かす H1 admission fails-closed / H2 between-run noise floor は完了** (A1 / A2 = 2026-06-28、between-run を
実測し compare/report を配線、read-heavy rank3/4 の過大主張を是正。[[decisions]] D19)。残りは **Phase 3
(LLM が別 protocol/コードを合成する) で初めて load-bearing になる**ので、段階導入 (規律5) として
Phase 3 着手の直前に消化する (今やると過剰修正):

- **S4 規律3 の配線 — 完了 (2026-06-29)**: verify-red の構造化 anomaly (cycle/edge/EdgeReason/integrity) を
  `result_to_dict(vr)` で WAL abort payload (`{"verify": ...}`) に載せ (`pipeline.py`)、次手生成が「なぜ壊れたか」を
  読む経路 `digest.load_rejections` を 1 本通した (件数潰しを解消)。**consumer** (critic/planner が rejection を
  読んで『その依存を断つ』variant を作る) は赤が出る Phase 3 で実体化 = 規律5。配線は mock/fixture テストで回帰
  (実 VerifyResult で `result_to_dict` 経路を含む、test_campaign/test_critic に各 1)。broken-silo end-to-end は
  Phase 1 で確立済 (buildcache が genome キーゆえ patch 状態と衝突する罠があり mock/fixture で回帰する)。
- **H3 hooks の実体化 — 完了 (2026-07-04、方針 A)**: `hooks/` の規律1/2 機械防壁は placeholder だった。
  **LLM が C++ variant を書く瞬間**に第二防壁が必要 (hooks/README に明示済み)。guard_write/guard_bash の
  最小第二防壁を `.claude/settings.json` の PreToolUse に配線 (D30/D33)。3 巡目敵対検証 (real 9/known 6) の
  修正と D34 (source_digest の -undef 廃止) まで消化。詳細は phase3.md の must 表。
- **S2 certify workload = perf workload の一致**: 検証 (tuple200/thread4) と計測 (1m/thread48) が別。合成 variant が
  「小 workload では踏まないデータパス」を持つと緑 certify と赤い実行が食い違う。perf 構成 (の縮小版) でも 1 回
  verify + broken-silo 同一フラグ赤検出を消化 (insight の follow-up [P1])。
- **S1 trace-hook の別 protocol 拡張**: silo+si のみ instrumented。別 protocol を探索素材に入れる Phase で同型 hook を
  追加 (ermia は cstamp<<1 の罠を worklog 記録済み)。それまでは「silo+si 以外は探索外」を維持。
- **C1 campaign-id drift (A2 で露呈) — 解消済み (2026-07-02、選択肢 a を採用)**: 6/28 の ODR-fix
  gitlink 前進 (CCBENCH_COMMIT 6656e93→dff0f1e) が content-addressed campaign-id (D13) を移動させ、
  歴史的 p2-2/backoff campaign の report が現 config では孤立した (生成器が現 commit で id を再計算する
  ため WAL を引けない)。ODR fix は ADD_ANALYSIS=0 perf build に inert なので 6/22 測定は意味的に有効。
  恒久対応は **(a) report 生成器が campaign dir を discover する** を採用 (065593a):
  `replay.discover_campaign_dir` (dir 名 prefix + WAL 実在で解決、0/複数一致は明示エラー) に読み手
  3 本 (p2_2_report / backoff_sweep_report / critic digest) を統一し、campaign-id の再計算に依存しない。
  却下: (b) 版マッピング = inert 判定の維持コスト、(c) 再 run = 計測資源の浪費 (規律4)。
  残課題 (audit §C1 が部分対応として記録): driver の宣言値は現 pin dff0f1e のまま (歴史的 campaign の
  lock は 6656e93) で、`backoff_repro.py` の自 run layout 解決だけ現宣言値の campaign_id を使う。
