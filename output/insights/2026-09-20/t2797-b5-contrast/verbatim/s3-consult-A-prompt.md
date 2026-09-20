単独段 dispatch: stage=consult; lane=sol; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 親 brief: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/brief.md
- 段 2 plan (検査対象): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/codex/s2-plan.md
- 親 brief 追補 1 (plan 受領後の親の provisional 判断 (P9) と新事実 = peer の claim 衝突、検査対象): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/brief-addendum-1.md
- 依頼文の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/verbatim/T-2797-origin.md
- ユーザー裁定 D2172 項 4 の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/verbatim/D2172-item4.md
- 前 wave の設計判断 D2183 の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/verbatim/D2183.md
- B-5 事前登録の逐語 (§3, §4, §5, §6, §7, §10, §11〜§12): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/verbatim/prereg-s3.md, prereg-s4.md, prereg-s5.md, prereg-s6.md, prereg-s7.md, prereg-s10.md, prereg-s11-12.md
- repo 内 (worktree の path、read-only): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/ 配下の
  `orchestrator/campaign/p3_s4_loop.py`、`orchestrator/campaign/pipeline.py` (verify の repetition :2115–2215、`_run_bench` :1301–1470)、`orchestrator/campaign/loop.py`、
  `orchestrator/campaign/ident.py`、`orchestrator/campaign/backoff_hole_grammar.py` (`validate_backoff_value`)、`orchestrator/campaign/backoff_extended_sweep.py` (:55–58)、
  `tools/pegasus/p3_s4_loop_pegasus.sh`、`orchestrator/tests/test_p3_s4_loop.py`、`orchestrator/tests/test_p3_s4_loop_job_contract.py`。

## 前置き — この依頼の性質

対象は研究用 repo の CC 合成 campaign の実験基盤 (B-5 生成器対照の事前登録 §10 残部品の実装と、上限付き試走 launcher の設計) である。
セキュリティでも攻撃でもない。あなたは段 3 の敵対相談 (レンズ A) であり、**plan を守らず検査する**。親 brief 自身も検査対象である。

# 依頼 — レンズ A: 事前登録の逐語適合と正しさ境界

段 2 plan と親 brief を、B-5 事前登録の逐語 (§3〜§7、§10) と既裁定 (D2172 項 4、D2183) に対して攻撃せよ。各所見は
**real (現物で成立) / refuted (現物で不成立) / 根拠不足** に分け、real には must-fix / should / nit の格と、放置時に成果物
(台帳の値・endpoint・score・判定・受理集合) がどう変わるかを 1 行で添えよ (示せない must-fix は nit)。

## 攻撃対象 (最低限)

1. **A / B の消費点。** plan の対応表 (proposal 受理 → schema → 値域 → 文法 → 検疫 → build → verify → bench → COMMIT) が §3.1 / §3.3 の逐語
   (文法・検疫・Tier0 不通過は A のみ、投入後 (correctness の build・verify・性能の build・bench) の失敗と anomaly は B、walltime 超過の投入前 / 後) と
   一致するか。「Tier0 不在」の扱い。品質欠測 (§5.3) が B も A も返さないことが plan で機械化されているか。retry (§3.3、機械故障のみ +2、同 slot) の分類が
   plan で「分類不能を無料 retry にしない」形か。
2. **停止の不適用と B 完走。** `drive_iteration` を迂回して `check_stop` を呼ばない形が、§3.4 の「checkpoint の改変や初期化による迂回は適合ではない」に
   抵触しないか (迂回ではなく別 driver であることの根拠)。B 完走を機械で保証する台帳 + ループの形は §10 の「運用だけでは不足」を満たすか。
3. **重複の fresh 評価。** slot key による identity 分離で `_resolve_duplicate` / terminal skip が構造的に発火しないという主張を
   `loop.run_campaign` の skip 経路と `ident.campaign_id` の preimage で検算せよ。発火した場合の fail-closed (成功捏造なし) は plan にあるか。
4. **系列開始 stock と current_perf (§5.4 / §4.1)。** stock の成功条件 (certified ∧ source STOCK、D2183) と不成立時の系列の扱い (§6 末尾) が plan で
   決まっているか。LLM arm の初回 planner 入力に stock の値を渡し、random / sweep には渡すが分岐に使わないことが機械で保証されるか
   (random / sweep の生成器が台帳を読まないこと)。
5. **whiteboard の継承検査 (§4.1)。** 評価 k の planner 入力 whiteboard = 台帳の評価 1〜k−1 のちょうど k−1 件、を検査する関数の入力 (何と何を比べるか、
   `delta_pct=None` の維持、`direction` / `magnitude` / `result` の値域) が plan で file:line まで決まっているか。親が性能を見て助言・修正・再抽選しないことを
   機械で担保できない部分は「担保しない」と明記されているか。
6. **random 生成器 (§4.2)。** `m_v = floor(2^128 × ln((v+1)/v))` の算出精度・床の確定・`M` の計算・`L = floor(2^256 / M) × M` の引き直し・
   累積重みへの写像・preimage 形式 (`b5-generator-contrast-v1|random|w|r|a|c`、c は 0 始まり、整数は先頭ゼロなし十進) が逐語どおりか。
   「候補生成後の重複や不成績を理由とする再抽選は禁止」を破る経路が plan に無いか。
7. **sweep (§4.3)。** 28 点 (0 除外) と hash 順 (同 hash は v 昇順)、先頭 10 点、候補起因の不通過は次点、機械故障は同点 retry、格子枯渇の記録、
   `MEASUREMENT_SEEDS` 順を使わないこと。
8. **endpoint と score (§6)。** 選択規則 (certified・session median 最大・同値は v 昇順 → slot 昇順)、台帳へ書いてから再計測、anomaly の波及
   (同 v は同 workload の全 arm で資格喪失)、N_eval = 5 の fresh session、fallback = block stock 5 session median、品質欠測 / 機械故障の score 欠測、
   「探索・score・block stock の session は互いに再利用しない」が plan で守られているか。
9. **正しさ (§5.5)。** legacy + performance verify の順・回数 (`reps` = 5)・anomaly の即 reject → B 消費 → endpoint 不採用の経路が既存 pipeline で
   閉じていること。plan が pipeline.py / loop.py / build_admission.py に触れないこと。
10. **親 brief の実測値と一般化。** brief の所要見積り (verifier 3 s ≈ 115 s write-heavy、1 session ≈ 12〜14 分) の出所と適用域 (母集合・regime)、
    53 論理 session の数え方 (§11 の表との対応)、上限 60 を driver 定数で守る形。

## 出力形式

- 見出しは `#` 1 段だけ (`##` は `## 総括` のみ)。所見ごとに: 対象 (plan / brief の箇所)、判定 (real / refuted / 根拠不足)、格 (must-fix / should / nit)、
  成果物影響 1 行、根拠 (file:line または逐語の引用)、代案 (あれば file:line)。
- 実行できない検査は「未実走・静的読解」と明記。sandbox は read-only で pytest 緑は要求しない。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。出力は最終メッセージ本文に全文。
- 末尾に `## 総括`: must-fix の一覧 (番号・1 行)、(P1)〜(P9) それぞれの支持 / 反証 ((P9) = 追補 1 の subprocess 案 vs plan の in-process seam + 新 entrypoint 案の優劣を必ず判定)、親裁定が要る未確定事項。
