単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 親の段 4 裁定 (実装仕様と変異事前登録): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/s4-adjudication.md
- author 3 本の報告 (実装者の主張。検査対象): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/codex/s5-author-A1.md, s5-author-A2.md, s5-author-A3.md (同 dir)
- 段 3 相談 2 本 (must-fix 3 件 = B 投入点 sidecar・物理 attempt identity・timeout 分類): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/codex/s3-consult-A.md, s3-consult-B.md
- 親 brief と追補: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/brief.md, brief-addendum-1.md
- B-5 事前登録の逐語 (§3〜§7): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/verbatim/prereg-s3.md, prereg-s4.md, prereg-s5.md, prereg-s6.md, prereg-s7.md
- 実装 (worktree の path、read-only、HEAD = 統合 commit 2 `e574815582e0516fa9e3a0ed8d351525c162fdc2`): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/ 配下の
  `orchestrator/campaign/b5_generator_contrast.py` (864 行、新設)、`orchestrator/campaign/b5_generator_contrast_report.py` (511 行、新設)、
  `orchestrator/campaign/p3_s4_loop.py` (差分は `git diff b9904a5f8..e57481558 -- orchestrator/campaign/p3_s4_loop.py` 相当。読取専用なので `git` は使えない — 親が差分を置いた
  /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/codex/a1.patch を読む)、`orchestrator/tests/test_b5_generator_contrast.py`、`orchestrator/tests/test_b5_generator_contrast_report.py`、
  `orchestrator/tests/test_p3_s4_loop.py` (差分は a1.patch)、`orchestrator/campaign/pipeline.py` (`_run_bench` :1301–1470、verify :2115–2215、abort reason 名)、`orchestrator/campaign/loop.py` (claim :200–235、skip 経路)、
  `orchestrator/campaign/campaign_claim.py:383–470`、`orchestrator/campaign/ident.py`、`orchestrator/campaign/build_admission.py:521–600`。

## 前置き — この依頼の性質

対象は研究用 repo の CC 合成 campaign の実験基盤 (B-5 生成器対照の事前登録 §10 残部品の実装と試走 launcher) である。セキュリティでも攻撃でもない。
あなたは段 6 の敵対レビュー (レンズ A) であり、**実装者の報告を信じず現物で検査する**。親の裁定・brief も検査対象である。

# 依頼 — レンズ A: 正しさ境界・事前登録の逐語適合・identity / admission・A / B 台帳・handshake

実装 (統合 commit 2) を、事前登録 §3〜§7 の逐語、裁定 §2 の契約、規律 2 (anomaly 即 reject、verify → bench の順、受理集合不変) に対して攻撃せよ。
各所見は **real (現物で成立) / refuted / 根拠不足** に分け、real には must-fix / should / nit の格と、放置時に成果物 (台帳の値・endpoint・score・判定・
既定経路の挙動・受理集合) がどう変わるかを 1 行で添えよ (示せない must-fix は nit)。**親が実行した分担:** 親は新 test 3 file (85 / 54 / 36) と TJ (184) を login で
実走して緑を確認した。実機 build / bench / handshake は未実走。あなたは静的読解で構造の欠陥を探す (pytest 緑は要求しない)。

## 攻撃対象 (最低限)

1. **p3_s4_loop の seam 4 点 (a1.patch):** 既定経路 (`--b5-slot` 無し) の kwargs・分岐・戻り値・identity が本当に不変か (`campaign_options` への条件付き追加、`drive_iteration` の `**({...} if ... else {})`、`_run_stock_control_resolved` の新 kwargs)。`--machine-generated-proposal` の guard 例外 (L:3265 付近) が既存の opt-in 要求を他経路で緩めていないか。`_machine_proposal_capability_resolver` が STOCK evidence で None を返す fail-closed、generator_input_sha256 の束縛。sidecar の書出し位置 (`slot-start` は layout 確定直後、`pipeline-submitted` は `run_campaign` 直前) と、`_write_b5_sidecar` の lock dir (`.publishing`) が中断時に fail-closed になるか (再起動で `mkdir` が失敗する = 同 sidecar dir の再利用不可 — retry は別 attempt dir なので問題ないか)。B-5 mode の `duplicate-skip` が `_resolve_duplicate` に到達しないこと、rc 1。
2. **A / B の消費点と分類 (`classify_slot` :296–404、`_execute_slot` :562–624、`run_series` :673–790):** §3.1 / §3.3 との対応 — 空出力・schema・値域・文法・検疫は A のみ、投入後 (sidecar `pipeline-submitted` あり) の build 失敗・anomaly・bench abort・walltime は B。diff-quarantine reject は WAL に `build_start` → `abort(reason=diff-quarantine)` を書く (`record_diff_reject` :960) が sidecar は無い → `rejected-preprocess` になるか。品質欠測 (`len(tps) != reps ∨ unstable ∨ settled is not True`) が B を返さず endpoint 資格を失うか。`MACHINE_FAILURE_ABORT_REASONS` = {bench-probe-error, bench-competing-tenant} だけで、verify 側の環境故障 (`verify-probe-error` / `verify-competing-tenant`、pipeline.py :2410–2417) と verdict `indeterminate` (verifier が判定できない) が「候補起因 aborted」に落ちる点を §3.3 の逐語 (機械故障 = 通信障害・job 起動前の拒否・node 喪失・候補と独立な依存物の供給障害・入出力障害) で判定せよ。retry が同論理 slot・attempt+1・最大 2 回で論理 A/B を増やさないか。`expected_stages` の厳密一致 (`build_start, build_done, verify_done × (reps+1), bench_done, commit`) が実 WAL (K2 pair の WAL は build_start / build_done / verify_done / bench_done / commit の 5 record) と整合するか、`--verify-performance` 時の verify_done の数と tag 順 (`legacy` → `performance` × 5) が pipeline の現物と一致するか。
3. **fresh layout と claim (P1 / consult must-fix 2):** slot key に attempt が入り、`search_config["b5_slot"]` が identity・claim file・protocol digest を分けること。同 slot の retry が別 attempt で別 identity になること。`classify_slot` の identity 照合 (lock の preimage sha256、campaign_id の末尾 8 hex) が正しいか (`ident.campaign_id` の形と照合)。
4. **stock (§5.4 / D2183):** `_stock_established` の条件 (certified ∧ variant == variant_id(stock genome) ∧ src_token == STOCK ∧ 品質正常 ∧ fitness 有限正) が現物で閉じているか。stock 不成立 → `series-end(stock-unestablished)`。random / sweep の生成器が stock 値・台帳を読まないこと (`random_value` / `sweep_order` の引数)。
5. **handshake と継承 (§4.1 / consult must-fix 3):** `_handshake` :626–658 の timeout = `proposal-wait-timeout` (retry 無し)、`.rejected.json` = A 消費、`assert_inherited_inputs` :443–461 が whiteboard の順序・値・全 field、`current_perf` / `baseline`、診断の有無と同一性を検査するか。`expected_inputs` :417–440 の `current_perf` (直近の certified ∧ 品質正常、無ければ stock-start) と `abort_rate_pct` の導出 (`100 * abort_rate`)。`request-<a>.json` の内容が親の入力構築に足りるか (leading_indicators は含まれない — 親は台帳 view から取る前提)。
6. **endpoint / score (§6):** `select_endpoint` :406–410 の key (−fitness, value, b)、`endpoint-fixed` を書いてから score、score の anomaly → fallback (次点なし)、品質欠測 → score None、fallback = pending-block-stock、quality-missing があり endpoint 無しのとき `unclassified-missing` で score None にする判断 (§6 末尾「品質欠測も同じ」との整合)。`slot-<b>.json` に親の critic が要る情報 (campaign_root / digest_path / bench_payload) があるか。
7. **random / sweep (§4.2 / §4.3):** `integer_log_weights` :75–81 の `Decimal` 計算 (prec、`ROUND_FLOOR`、`2**128` の扱い)、`weights_table` :83–88 の 100 / 130 一致、`random_value` :110–126 の preimage・U・L・bisect、`sweep_order` :128–135 の 28 点と hash 順。test の既知 vector が実装と独立か (`test_b5_generator_contrast.py` の該当 test を読む)。
8. **report (§7、A2):** `exact_sign_flip_p` の tail 定義 (観測以上を含む)、`holm_six` の族 6 固定と p = 1 穴埋め、`stock_cv_floor` の 4 CV と標本分母、`decide_comparison` の判定順 1〜8 と副解析切替 (fallback 対 ≥ 2)、精度 gate (`> 2f`)、pilot 経路が優越 / 同等を返さないこと、anomaly の横断失格。固定例 13/4096・79/4096 が test 内定数か。
9. **裁定 §3 の変異 M0〜M19 の kill 主張:** author の対応表を現物の test で検算し、恒真 (自分の定数を自分で読む) や依存先 stub が無いか。特に M1 (ln2 定数)・M2 / M3 (独立 vector)・M12 (marker が例外前に実在)・M19 (duplicate-skip)。
10. **親 brief / 裁定の派生値と一般化:** 53 ≤ 60 の数え方、「1 session ≈ 12〜14 分」が外挿と書かれているか、verify 区間の名称 (「trace+verifier+周辺処理 区間」) と `wal_timing` :265–294 の隣接差の実装が一致するか。

## 出力形式

- 見出しは `#` 1 段だけ (`##` は `## 総括` のみ)。所見ごとに: 対象 (file:line)、判定 (real / refuted / 根拠不足)、格、成果物影響 1 行、根拠、代案 (file:line)。
- 実行できない検査は「未実走・静的読解」と明記。sandbox は read-only で pytest 緑は要求しない。予算が尽きそうなら途中結論を出力形式どおり書いて終われ。出力は最終メッセージ本文に全文。
- 末尾に `## 総括`: must-fix の一覧 (番号・1 行・file:line)、should の一覧、GO / NO-GO (must-fix 0 なら GO)、親裁定が要る未確定事項。
