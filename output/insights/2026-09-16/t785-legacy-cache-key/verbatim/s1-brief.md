# [T-785] 段 1 brief — legacy buildcache.cache_key の既定 toolchain 省略による偽 hit

基準: worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t785-legacy-cache-key` の HEAD `0c292eff6` (= local main、clean)。以下の file:line はこの木のもの。

- **研究前進 (土台):** legacy build 経路 (s1/s2/s3/s5 の stock control、pipeline・backoff_profile・between_run_floor・pegasus_floor_scoping) の正しさ検査・性能値が、既定 toolchain を替えた後に旧 compiler の binary を黙って再利用し、新 compiler の configure argv を記録する偽 hit を塞ぐ。現時点で止まっている研究は無い (既定 `gcc-13`/`g++-13` は `9cde78124` (2026-07-02) 以来不変)。ユーザー明示依頼による着手。完了判定 = 修正前に実編集で偽 hit を再現した実測 JSON、修正後に同手順で miss になる実測 JSON、回帰テストの変異 KILLED。
- **成果物影響 (DW-G05):** 放置すると既定変更後、legacy 経路の `BuildResult.configure_argv` の compiler と実 binary の compiler が食い違ったまま、較正・検査結果や性能値が台帳・レポートへ入る。
- **依頼と既裁定:** 台帳 [T-785] (起票 `docs/archive/worklog-phase3-0811-402.md`、根拠 `output/insights/2026-08-11_t8b-restart-integration/package.md` M4、同 `verbatim-adv-b.md` B-12)。依頼 = 実在する production caller の手当て / 床値の build_v2 へ広げない / まず偽 hit を実際に再現してから直す / 仮想リスク向けの gate・検査・台帳・一般化は scope 外 / 規律 2 不変 / 実装面は Codex author (D95)。D293 (床値 compiler の site 依存化) は build_v2 側で対象外。decisions / failures に本欠陥の既存被覆なし。
- **実測済み事実:**
  1. `orchestrator/campaign/buildcache.py:622` `DEFAULT_CC, DEFAULT_CXX = "gcc-13", "g++-13"`。`:639` の `tc = "" if (cc, cxx) == (DEFAULT_CC, DEFAULT_CXX) else ...` は**呼出時の module global** と比較する。
  2. `:3410-3411` の `build()` 既定引数 `cc=DEFAULT_CC, cxx=DEFAULT_CXX` は**定義時束縛**。s1 (`s1_verify_extime_calibration.py:390`)・s2 (`s2_verify_calibration.py:354-355`)・s3 (`s3_lock_coverage.py:258`)・s5 (`s5_permutation_coverage.py:293`) は cc/cxx を渡さない。pipeline (`pipeline.py:1945`→`:2002`)・backoff_profile (`:273`,`:307`→`:857`)・between_run_floor (`:317`→`:324`)・pegasus_floor_scoping (`:214`→`:218`) は `compilers_for_current_site()` (`buildcache.py:1861-1865`、compute 以外は DEFAULT を返す) 経由。`tools/pegasus/probes/t2187_adaptive_const_probe.py:3925,4346` は `cache_key` を直接呼ぶ。
  3. stock admission (`build_admission.py:615-675`) の receipt は nonce も toolchain も含まず決定的。legacy hit 経路 (`buildcache.py:3474-3512`。`:3585` は publish 直前に同名 entry の出現を拒否するだけで hit ではない) は sidecar・source evidence・trace diff・trace symbol を見るが toolchain を見ない → key 衝突はそのまま hit になる。
  4. よって monkeypatch で `DEFAULT_*` だけ替えても定義時既定は動かず、s1/s2/s3/s5 型の caller では衝突しない。**既定変更の再現は実編集が要る** (DW-S01)。
  5. legacy key の golden: `orchestrator/tests/test_campaign.py:11178-11197` (`_T816_GOLDEN_CK0`)。compiler 名分離テスト `:3184-3202`。hit 経路の既存 fake: `orchestrator/tests/test_build_site_gate.py:290-331` (`_fake_legacy_build`)。
  6. 環境: 本 host は Pegasus login (`pegasus02`)。`g++-13` 不在、`g++-12` (12.3.0) と `g++` (11.4.0) は在る。login では `_run` の configure/build が `require_heavy_work_site` で拒否される (`buildcache.py:3795-3796`)。compute での legacy 実 build は T-2000 probe が 3 投入とも到達していない (`output/insights/2026-08-28_t2000-legacy-build-probe/RESULT.md`)。
  7. 編集面重複: [T-548] の branch 差分と 4 worktree、[T-2237] (sort 軸、worktree 作成 17:32:40 で本 wave 17:30:42 より後発) の worktree とも、`buildcache.py`・`test_campaign.py`・`test_build_site_gate.py` は main と byte 一致 (未編集)。
- **(P1) 親の provisional 裁定・攻撃対象:** 修正は `cache_key` の省略条件を可変の `DEFAULT_*` から切り離し、歴史的既定の literal 組 (`gcc-13`,`g++-13`) のときだけ省略する。現行の全入力で key 不変 (golden 不変、cache 無効化なし)。対案 A「常に toolchain を key に含める」は既定 key 全部と golden を動かし、legacy cache を全無効化する。
- **(P2) 同:** 再現 probe は repo 外 (job dir) に置き Codex author が書く。production の `buildcache.build()` を実 ccbench checkout・実 `resolve_evidence`・実 admission で呼び、差し替えるのは cmake を起動する `buildcache._run` だけ (login の重処理拒否のため。模擬と実の差はここだけ)。差し替え側は configure argv が要求した compiler で極小 C++ を実コンパイルし、ELF `.comment` に実 compiler を残す。親が DW-O19 で `DEFAULT_*` を `gcc-12`/`g++-12` へ実編集 → seed 相 → `gcc`/`g++` へ実編集 → hit 相 → 復元。修正後も同手順で miss を確認する。
- **(P3) 同:** repo 内回帰テストは `test_campaign.py` の cache_key 節へ追加する。module の `DEFAULT_*` を差し替え、cc/cxx を明示して渡す形 (key 計算上は実編集と等価)。修正を戻すと赤になる変異で歯を確かめる。
- **不変条件:** build_v2 / `_v2_identity` 不変。hit 時の検査を緩めない (規律 2)。既存テストの期待値不変。現行入力の key 不変。caller は編集しない (P1 が成立する限り)。
- **scope 外:** resolved compiler (realpath/version) を legacy key へ入れる、hit 時の toolchain 照合 gate、caller の compiler 解決変更、[T-548] の依存調達面、一般化。
- **分割:** 単位 P (probe、repo 外) → 親が修正前再現 → 単位 F (`buildcache.py:625-644` + `test_campaign.py` cache_key 節)。所有素集合、直列。
- **受入・実測環境:** probe は login node (cmake 不起動)。受入は `tools/dev_wave_wait.py acceptance --lease-optional` (Pegasus dispatch)。

## 段 2 後の親追記 (plan 子の検算を親が現物で確認したもの)

- **衝突の前提は未実測。** stock admission の receipt は `source_bytes_sha256` を含み、それは `source_digest.resolve_evidence` (`source_digest.py:2408-2410`) が `compute(genome, sub, cxx)` = 要求 compiler の `-E -P -nostdinc` 出力 (`:1646-1678`) から作る。したがって key が衝突するのは「旧既定と新既定の compiler で EVOLVE-BLOCK source の前処理出力が byte 一致」するときだけ。一致しなければ現行でも key は分かれ、偽 hit は起きない。**brief の事実 3「key 衝突 = hit」は、この一致を前提にした条件付きの主張に訂正する。**
- login node の compiler 在庫 (親実測): `g++-9`、`g++-11`、`g++-12` (12.3.0)、`g++` (11.4.0)、`clang++`。`g++-13` は不在。
- between_run_floor (`between_run_floor.py:316-323`) は Pegasus 分岐だけ site 解決し、それ以外は `build()` の定義時既定を使う (brief の事実 2 を訂正)。
- 本 worktree の既定 cache root `external/ccbench/build-variants` は不在。brief の「legacy cache を全無効化」は「全 root にある歴史的組の entry が新 key から参照されなくなる」に訂正。
- plan: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t785-legacy-cache-key/artifacts/dev-wave-t785-legacy-cache-key/s2-plan.md`
