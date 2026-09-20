単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する (射影 file 限定の停止規則であり、自分が推測して探した path が不在でも停止理由にしない)。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/s4-adjudication.md` — **親の段 4 裁定 (確定指示)。§2.3 と §2.5 が本単位 (A2) の実装仕様、§3 の M16 / M17 が本単位の変異。** 読めなければ即停止
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/codex/s5-author-A1.md` — **A1 (core module) の報告。§「台帳 schema と handshake の確定形」を正とする (台帳の読み手はこの schema に従う)**
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/codex/s2-plan.md` §8 (report consumer)、`.../codex/s3-consult-A.md` 所見 11 / 14、`.../codex/s3-consult-B.md` B10 / B11 / B12 — 参考 (裁定が上書き)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/verbatim/prereg-s6.md`、`prereg-s7.md` (同 dir) — **B-5 事前登録 §6 (endpoint と score) と §7 (母集団・floor・検定・判定順) の逐語。実装が逐語で守る規則**
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a2/orchestrator/campaign/b5_generator_contrast.py` — 読むだけ (台帳 schema・定数・`classify_*` の enum を import して使う。触らない)
- 読むだけ: `.../orchestrator/tests/test_b5_generator_contrast.py` (台帳の合成 helper があれば流用可、触らない)、`.../orchestrator/tests/test_p3_s4_loop_job_contract.py:1927–1934` (`__main__` harness の型)、`.../orchestrator/campaign/s8b_floor_stats.py` (統計関数の既存の書き方の参考、触らない)、`.../orchestrator/tests/test_official_perf_closure.py:495–535` (perf 名で分岐すると inventory に載る述語。report は `perf` 名の条件分岐を避ける)。

repo root は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a2` とする。上記以外も repo 内を読んでよい。

## この単位 (A2) の仕事

裁定 §2.3 の解析 consumer を実装し、M16 / M17 が**独立した根拠**で kill される test を書く。編集するのは次の 2 file だけ (両方新設):

1. `orchestrator/campaign/b5_generator_contrast_report.py` — `build_report(ledgers, *, purpose: Literal["pilot","registered"]) -> dict`、`exact_sign_flip_p(differences) -> Fraction` (全 2^n 符号反転の片側 exact permutation、観測平均以上を tail に含める、n ≤ 12)、`holm_six(raw_p: Mapping[ComparisonKey, Fraction|float]) -> dict` (族 6 固定、判定不能 / 規約不適合は p = 1)、`stock_cv_floor(block_stock_sessions) -> {cv_all, cv_block[3], cv_stock, f, delta}` (CV = 標本標準偏差 (n−1) / 算術平均、`f = max(0.03, cv_stock)`、`δ = ln(1 + f)`)、`pair_differences(...)` (`d_r = ln(score_LLM,r / score_b,r)`)、`decide_comparison(...)` (§7.4 の順 1〜8 で先に該当した結末で止める、fallback 対の主 / 副解析切替 (副解析は残った対だけで p・median・block median を再計算、残り < 6 または block に < 1 で対不足)、精度 gate `CV_endpoint > 2f`)、anomaly の横断失格集合 (`(workload, value)` を全台帳から先に作り、他 arm・他系列の既確定 endpoint も不採用へ訂正、元 event は保持し「結果の訂正」として報告)、pilot 経路 (`registered_judgment="not-applicable-pilot"`、優越 / 同等の判定を出さない、記述統計 = A / B・論理 session・物理 attempt・品質 round・stock / endpoint / score・fallback・anomaly・欠測・stock 5 件の記述 CV (「本走の f(w)」とは呼ばない)・session 所要分布と max・build / bench / verify 区間・job Elapse・LLM 手番 (台帳の timing から))、`main(argv)` (`--ledger-root` 複数 + `--block-stock-root` + `--purpose` + `--out JSON` + 表を stdout)。consumer は build・qsub・追加測定を行わない。schema 不整合・slot 重複・attempt の所属不明・endpoint 固定前の score・非有限 score を区別して報告 (例外で落とさず `report["invalid"]` に列挙、判定は規約不適合)。
2. `orchestrator/tests/test_b5_generator_contrast_report.py` — `__main__` harness。合成台帳 (A1 の schema に従う JSON を tmp に生成) と純粋関数の固定例: 12 対 × 3 block の明瞭な正差 / 零差 / 逆差、片 baseline だけの勝利、floor の 4 CV の最大、精度境界の等号、fallback 1 → 2 の解析切替、残存 5 対で対不足、block 空、判定不能の p = 1 穴埋め、**等絶対差で 11 正 / 1 負 → p = 13/4096、10 正 / 2 負 → p = 79/4096 の固定例** (実装から期待値を作らない)、Holm の段階閾値 (0.05/6, 0.05/5, …) で有意が族内の他 p に依存する例、pilot 台帳 (n = 1、block stock 5) で `not-applicable-pilot` と記述統計だけが出る例。

必ず守る点:

1. **触らない file:** `orchestrator/campaign/b5_generator_contrast.py` (A1)、`orchestrator/campaign/p3_s4_loop.py`、`tools/**`、`orchestrator/tests/test_b5_generator_contrast.py`、`orchestrator/tests/test_p3_s4_loop*.py`、`orchestrator/tests/test_official_perf_closure.py` (report が述語に該当したら「該当する」と報告し親が扱う; 該当しないように `perf` 名の条件分岐を避けるのが既定)、`docs/**`、`hooks/**`、`.claude/**`、`.codex/**`、他のすべての file。新規 file は上記 2 つだけ。job dir へ書かない。
2. **絶対に `git add` / `git commit` / `git stash` / `git checkout` / `git reset` / `git rm` を実行しない。commit は親が行う。**
3. import 方向は report → `b5_generator_contrast` (定数・schema・enum) のみ。`p3_s4_loop` / `pipeline` / `loop` を import しない。`run_campaign` / `evaluate` / build / subprocess を呼ばない。WAL を直接読まない (台帳が正本)。
4. §6 / §7 の逐語を守る: endpoint 選択は台帳の `endpoint-fixed` を読む (consumer が選び直さない)、score は 5 fresh session の median、探索の最大値を流用しない、fallback = 同 workload・同 block の block stock 5 session median (共有を明記)、anomaly を 0 tps / −100 % へ変換しない、機械欠測 / 品質欠測 / 対不足 / 精度不足 / 生成不成立 (certified endpoint 数 < 6 の片方 / 双方) / 規約不適合を区別、条件付き優越には「登録した独立性の仮定の下で」の限定文を report に添える、副解析で判定した比較は除いた対の数と除いた側の arm を添える。
5. **テストを甘くしない:** 固定例の期待値は実装から生成せず test 内の定数 (13/4096 など) と手計算 (小さい n で全列挙を test 内で独立に書く) から。M16 (族 6 → 5) は Holm 固定例で、M17 (pilot で優越) は pilot test で殺す。判定順の前後交換・fallback 閾値 2 → 3・標本 CV → 母 CV・片 baseline 勝利の採用、の各変異も殺す test を置く (報告に変異 → test 名の対応表)。
6. 規模の目安: report 500〜800 行、test 400〜700 行。
7. **実走:** `cd <repo root> && PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 -B orchestrator/tests/test_b5_generator_contrast_report.py`。`python3 -B orchestrator/tests/test_official_perf_closure.py` (report が inventory に掛からないことの確認)。`test_campaign_import_invariant.py` の campaign CLI 形の検査 (`-k` で絞る)。実走 nodeid・件数・結果を報告に列挙。走らないなら「実装済み・未実走」。
8. 新 test 名は ASCII。docs を書かない。報告は最終メッセージ本文。予算が尽きそうなら途中結論を出力形式どおり書いて終わる。

## 出力形式

- 見出しはすべて `##`。節: `## 変更の要約`、`## 逐語適合の確認` (§6 / §7 の各規則 → 関数)、`## 新 test 一覧` (名前・根拠・殺す変異)、`## 実走結果`、`## 波及` (perf inventory 述語への該当有無・A1 schema への要望)、`## 未了・懸念`、`## 総括`。
