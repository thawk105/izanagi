---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: worktree-dev-wave-vhash-cicada-version-measure
seq: 1
title: [T-2875] stock Cicada の版探索と版保持を診断計器 patch で実測した — update tx の読み取りはほぼ先頭の版で終わり、深い探索は read-only (固定 snapshot) から来る。長い tx は MinRts の公開そのものを止め、境界年齢は待機長に応じて伸びた (patch + driver + 作図 + insight、計算 0.68 node 時間、branch worktree-dev-wave-vhash-cicada-version-measure)
---

## 本文

- 依頼: 並行 wave の投げ文 md_2 (VHash 論文、出典メモ §29 段階 1)。ユーザー就寝中につき、判断はマネージャー session の指示 (codex と賛否を検討して自分で決める) に従った。
- 一次資料 = `output/insights/2026-09-29/vhash-cicada-version-measure/README.md` (図 3 枚、gzip raw、解析表、変異台帳、裁定と所見の逐語)。
- 素材: YCSB・48 worker・N=1M・3 秒・24 条件 × 3 反復で、update read が最新版より奥へ行く割合は A (読み 50%・skew 0) で約 1e-5、B (読み 95%・skew 0.9) で約 0.9〜1.4%。read-only read は B で 24〜48% が奥へ行く。観測時点の楽観的 forwarding 候補率は B の K=1 で 2〜5%、K=8 で 67〜86% (分母小)。worker 1 が 10 ms 待つと MinRts 公開は 3 秒あたり 14,176 回から 290 回 (長い tx の試行 292 回) へ減り、境界年齢 p50 は 32 µs から 32768 µs の bucket になった。1000 操作の長い update tx は A の gc 10/1000 µs と B の全条件で commit 0。値は計器入り build の診断値で、性能・正しさの主張はしない。
- 依頼との食い違い: md_2 の「patches/ledger.json の entry」は作らなかった (同台帳は D18 第 4 類 ability probe 専用で `silo_ladder_rung1_contract.py` が entry 数 1 を要求)。`patches/README.md` に登録し、マネージャー経由で他 wave に共有した。
- stock の欠陥 (insight §3、上流修正は人間判断): `WORKER1_INSERT_DELAY_RPHASE=1` は compile error 3 件、`batch_*` flag は表示だけで YCSB が操作数を変えない。
- commit: 7a4f9a592..52bea740c (実装 1 + fix 6 本)、283ecf1a8 (一次資料)。patch base = gitlink 68106660。既定 build の `.text`・`.rodata` は stock と一致 (smoke4、33984.nqsv)。
- 相談・レビュー: 段 2 plan 1、段 3 相談 1 (条件付き GO)、段 6 レビュー 1 (NO-GO、must-fix 6 real) と焦点再レビュー 3 (残 3 → 残 1 (成果物影響なしの nit へ格下げ) → 残 1 real)。計算ノード smoke で実機 blocker 2 件 (compile_commands の 4 行、condition gate の meaning が owner TU しか見ない) → F139 の再発として記録。
- 変異: MUT-1〜10 + 等価 1 を login probe で登録どおり確認後、計算ノード 1 job (34027.nqsv) で本走。台帳は KILLED 10・SURVIVED 1 (等価) で完全一致、wrapper は走行中の他 wave の land で共有木検査だけ rc=125 (child_rc=0)。
- 受入 1 走目 (tip f5c726138、claimed main f1c633b9b): 2 failed / 27919 passed。2 件とも自分起因 (新 2 macro の登録漏れ): `test_p3_s4_loop.py::test_all_naked_izanagi_macro_patches_are_registered_or_allowlisted` (裸 `IZANAGI_*` トークン、出力名 `IZANAGI_CICADA_VLIFE_JSON` も拾う) と `test_screening_driver.py::test_screening_condition_requests_cover_exact_define_specs` (`_CONDITION_DEFAULTS` == DEFINE_SPECS)。段 2 plan の「_CONDITION_DEFAULTS は不要」が誤りで、login の在庫 test では検出されなかった。fix 2 本 (codex) で前例 `IZANAGI_SILO_POLICY_PROBE` と同形に登録し、受入を取り直した。
- 訂正: merge commit f5c726138 の件名「local main 43a239294 を取り込む」は誤りで、実際の第 2 親は f1c633b9b (件名を書いた後、merge までに main が進んだ)。
- 工数: codex 15 本 (plan 1・consult 1・author 1・review 1・fix 8・focus 3)、Explore (sonnet) 1 本。計算ノード 10 job、Elapse 合計約 2,450 秒。

## 次の一手差分

### 完了

- [T-2875] 診断計器 patch (`patches/instr-cicada-version-lifetime.patch`) と driver (`orchestrator/campaign/vhash_cicada_vlife.py`) で 24 条件 × 3 反復を実測し、一次資料と図 3 枚を `output/insights/2026-09-29/vhash-cicada-version-measure/` に置いた。
  remaining: none
  base: 385796dab08ceae346e79d4df3038efe4306bf5df0665b37167c09b4c013d285
