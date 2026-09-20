単独段 dispatch: stage=consult; lane=luna; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 親 brief: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/brief.md
- 段 2 plan (検査対象): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/codex/s2-plan.md
- 親 brief 追補 1 (plan 受領後の親の provisional 判断 (P9) と新事実 = peer の claim 衝突、検査対象): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/brief-addendum-1.md
- 依頼文の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/verbatim/T-2797-origin.md
- ユーザー裁定 D2172 項 4 の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/verbatim/D2172-item4.md
- 前 wave の設計判断 D2183 の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/verbatim/D2183.md
- B-5 事前登録の逐語 (§4 生成器、§5 評価経路、§10 照合表、§11〜§12 費用と発効束): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/verbatim/prereg-s4.md, prereg-s5.md, prereg-s10.md, prereg-s11-12.md
- repo 内 (worktree の path、read-only): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/ 配下の
  `tools/pegasus/p3_s4_loop_pegasus.sh` (621 行)、`orchestrator/tests/test_p3_s4_loop_job_contract.py` (逐語 pin :176–474、stage order :548、driver 呼出し回数 :1866–)、
  `orchestrator/campaign/p3_s4_loop.py` (`main` :2938–3410、`_run_stock_control_resolved` :1931、`_run_one_iteration_resolved` :2020、`drive_iteration` :2598)、
  `orchestrator/tests/test_p3_exploration_namespace.py`、`orchestrator/tests/test_p3_b4_wiring_probe.py` (静的 inventory pin)、`orchestrator/tests/test_campaign.py` (:5418, :5500)、
  `orchestrator/tests/test_official_perf_closure.py` (:44–75, :495–535)、`tools/pegasus/admission_registry.json` (:112)、`tools/pegasus/README.md` (§7 :331–420)、
  `tools/pegasus/dispatch_compute.py` (qsub argv の先例 :4010–4030)、`orchestrator/campaign/layout.py` (`exploration_campaign_layout` :594)、
  前 wave の insight `output/insights/2026-09-20/t2795-pair-launcher/README.md` §0〜§2 と K2 round 3 の insight `output/insights/2026-09-19/k2-loop-round3/README.md` (§「実測」の job Elapse 69 秒、`materials/` の JSON 形)。

## 前置き — この依頼の性質

対象は研究用 repo の CC 合成 campaign の実験基盤 (B-5 生成器対照 §10 残部品の実装と、上限付き試走 launcher の設計) である。セキュリティでも
攻撃でもない。あなたは段 3 の敵対相談 (レンズ B) であり、**plan を守らず検査する**。親 brief 自身も検査対象である。

# 依頼 — レンズ B: launcher / job 契約 / pin 閉包 / 実効性と過剰

段 2 plan と親 brief を、実装の実効性 (実機で動くか)・job 契約・既存 pin との整合・過剰実装 (要求外の gate・台帳・一般化)・削除可能性の
観点で攻撃せよ。各所見は **real / refuted / 根拠不足** に分け、real には must-fix / should / nit の格と、放置時に成果物 (試走の成立・台帳・
既存経路の既定挙動・受理集合) がどう変わるかを 1 行で添えよ (示せない must-fix は nit)。

## 攻撃対象 (最低限)

1. **job body の B-5 mode (P5)。** 既存 file に mode を足す案と別 file 案の比較 — 既存 3 経路 (fixture / proposal / stock-control) の argv が bytes 不変か、
   TJ の逐語 pin (:176–474) と stage order (:548)、driver 呼出し回数 test (:1866–) のどこが赤になり、author が更新すべき行は何か。`set -Eeuo pipefail` と
   EXIT trap (compute-result.json) の下で系列 driver 1 起動 + rc 集約が成立するか。`#PBS -l elapstim_req=03:00:00` は pin されており、親が qsub CLI
   `-l elapstim_req=08:00:00` で上書きする (probe `13465.nqsv` で CLI 優先を実測済み) — この形の落とし穴 (contract test が walltime を前提にしていないか)。
2. **LLM arm の job 内 handshake (P4)。** 計算ノードは外部ネットワーク不在、`/work` は共有 FS — proposal file の poll (間隔 15 s、上限 45 min) と atomic rename の
   受渡しが成立するか、親が死んだときの job 側の終端 (timeout → 台帳記録 → job 終了) と、その分類 (§3.3 の機械故障か候補起因か) の妥当性。
   node を待機で占有することの費用 (48 core × 待機) と、代案 (1 評価 1 job、stock だけ先行 job) の費用 (queue 待ち × 11)。§5.4 の「同 job」を試走で
   逸脱してよいかは親裁定事項として返してよい。
3. **試走の job 分割と walltime (P8)。** random / sweep を 1 job に 16 session 直列で置く案 vs 分割案。1 session の所要見積り (brief) の出所と、
   見積りが外れたときの上限 (60 論理 session) の守り方。block stock 5 を別 job にする案。同時 4 node の投入が queue (19:16 時点 46 run / 143 req) で
   現実的か、投入順序 (block stock を先に) の是非。
4. **pin 閉包。** 新 module が `run_campaign` を直接呼ぶ / 呼ばないの選択と `test_campaign.py:5418` の caller inventory、perf 名分岐と
   `test_official_perf_closure.py` の `_REVIEWED_PERF_FILES`、p3_s4_loop の静的 import 閉包 (49) と layout 呼出し数 (11) を動かさない形、
   `tools/pegasus/admission_registry.json` の登録 (同 file 拡張なら不変)、新 test file の `__main__` harness と `PYTHONDONTWRITEBYTECODE`。
   plan が列挙していない pin を repo で検索して足せ (`git grep` は使えないので `rg` / `grep -rn` で)。
5. **private seam の跨ぎ。** 新 module が p3_s4_loop の `_` 始まり関数 (`_run_stock_control_resolved` / `_run_one_iteration_resolved` /
   `_campaign_cfg_for_site` / `_admit_env_contract` ほか) を呼ぶことの是非と、public seam を足す場合の最小形 (既存関数への委譲、既定経路の bytes 不変)。
6. **過剰実装と削除候補。** brief / plan の要素のうち、依頼 (逐語) と §10 の「実装が要る」に無いもの (例: 汎用の retry 機構、複数 workload の schedule、
   本走用の 108 系列 schedule 生成、仮想リスク向けの gate) を列挙し削除を提案せよ。逆に、依頼にあるのに plan に無いもの (較正・verify の job body 配線、
   解析 consumer、verifier wall の実測記録) を列挙せよ。
7. **解析 consumer (A2) の実効性。** n = 1 の試走で consumer が「判定不能 (対不足)」を返す以外に何を出すべきか (記述統計、session 所要の分布、
   verifier wall)。本走の統計 (2^12 permutation、Holm) を今実装する価値と費用 — 合成データ test だけで正しさを担保できるか、簡略化 (試走に要る
   記述統計 + 判定順の骨格だけ) を提案するならその境界。
8. **変異 matrix の帰属。** plan の変異候補が各単位の負例として「その単位の test だけが殺す」形か (kill が他 test の連鎖に依存しないか)、恒真な test
   (自分の定数を自分で読む) が無いか。
9. **親 brief の実測値。** brief の「gen_S 46 run / 143 req」「Elapse 上限 86400 s」「verifier ≈ 115 s」の適用域と、試走の walltime を決める根拠として
   十分か (DW-O13 の「max への倍率」)。

## 出力形式

- 見出しは `#` 1 段だけ (`##` は `## 総括` のみ)。所見ごとに: 対象、判定 (real / refuted / 根拠不足)、格、成果物影響 1 行、根拠 (file:line)、代案。
- 実行できない検査は「未実走・静的読解」と明記。sandbox は read-only で pytest 緑は要求しない。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。出力は最終メッセージ本文に全文。
- 末尾に `## 総括`: must-fix の一覧、(P1)〜(P9) の支持 / 反証 ((P9) = 追補 1 の subprocess 案 vs plan の in-process seam + 新 entrypoint 案を、pin 閉包・実効性・費用で必ず判定)、削除候補の一覧、親裁定が要る未確定事項。
