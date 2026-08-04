| 項目 | 判定 | 根拠 file:line |
|---|---|---|
| G-1 | **partial** | 三値判定・CPU 別 residual・IRQ 等の除外は実装済み（[probe.py:1874](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1874)、[probe.py:2005](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:2005)）。ただし child 全生存期間の strict 帰属と snapshot 時間窓が未閉鎖（[probe.py:1960](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1960)、[probe.py:2080](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:2080)） |
| G-2 | **closed** | band の数式一致（[probe.py:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:112)）と外部 literal・直外拒否（[test:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/tests/test_t419_probe_causality.py:159)） |
| G-3 | **closed** | seed permutation、flat/by-pin 順を照合（[probe.py:767](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:767)、[test:314](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/tests/test_t419_probe_causality.py:314)） |
| G-4 | **partial** | 算術・identity・5/1・3/8 は実装済み（[probe.py:498](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:498)、[probe.py:962](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:962)）。ただし sham の `1 tick` inclusive 境界が未固定（[test:406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/tests/test_t419_probe_causality.py:406)） |
| G-5 | **partial** | total wrapper は入った（[probe.py:1007](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1007)）が、MHz/CPU ID の coercible な異常型を受理する（[probe.py:152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:152)） |
| G-6 | **closed** | A4 29/30 の単一理由 fixture（[probe.py:1352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1352)、[test:252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/tests/test_t419_probe_causality.py:252)） |
| G-7 | **closed** | `probe_rc` へ改名（[probe.py:2837](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:2837)）、wrapper.rc→done の順（[PBS:191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.pbs:191)）。`.o/.e`・会計 receipt は親 scope |
| G-8 | **partial** | final hash・scheduler binding・dirty 除外は実装済み（[probe.py:2522](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:2522)、[probe.py:2803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:2803)）。ただし final mismatch の INVALID が wrapper rc へ伝播しない |
| G-9 | **closed** | `lateness_ns` と半 interval の開境界（[probe.py:1532](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1532)、[test:660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/tests/test_t419_probe_causality.py:660)） |

## 所見

### F2-01 / A2 child の strict 帰属が全生存期間を覆わない — must-fix

- **主張:** completed child へ帰属するのは readiness 後から terminate 前までの `cpu_ticks_delta` だけで、fork→start snapshot と end snapshot→reap の tick が残る。
- **file:line:** [probe.py:1960](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1960)、[probe.py:2239](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:2239)、[probe.py:2268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:2268)、[probe.py:2299](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:2299)
- **失敗シナリオ:** busy child が start snapshot 前または end snapshot 後に 1 tick 消費すると、`/proc/stat` には入るが child 帰属には入らない。A2 reader は全 tick が reader CPU へ帰属済みなので、その 1 tick が `COMPETITOR` になる。
- **成果物影響:** 単独 job が A2 で偽 INVALID となり、A3+A2 を走らせず唯一の投入結果が無価値になる。
- **強度:** 強。範囲欠落は静的に確定。ただし実機で 1 tick 発生する頻度は未実測なので、その点は弱い。
- **最小の是正案:** child の誕生から reap までの全 tick を pin CPU へ束縛し、非零 `start_cpu_ticks` と終了端 tick を含む単一理由 fixture を追加する。

### F2-02 / process delta と CPU delta の境界時間窓が一致しない — must-fix

- **主張:** arm 開始・終了とも process snapshot の後に CPU counter を採るため、self delta は CPU delta より早く始まり、早く終わる。
- **file:line:** [probe.py:2079](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:2079)、[probe.py:2115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:2115)、[probe.py:1988](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1988)
- **失敗シナリオ:** start scan 中の self tick が `self_unattributable_total` にだけ入り、その過大な上界が短命 competitor の residual を覆って `ATTRIBUTION_UNRESOLVED` に落とす。逆向きのずれでは偽 COMPETITOR も作る。
- **成果物影響:** 汚染 arm を VALID として偽 CONFIRMED に使うか、単独 arm を偽 INVALID にする。
- **強度:** 中。時間窓のずれは確定しているが、tick 差の実量は未実測なので弱い。
- **最小の是正案:** 開始は CPU-before→process-before、終了は process-after→CPU-after とし、process delta が CPU window 内に包含されるようにする。

### F2-03 / CPU 横断相殺禁止をテストが固定していない — must-fix

- **主張:** 実装は CPU 別 `max(0, …)` だが、isolation の全 fixture が実質 1 CPU で、総和後に self tick を引く回帰が生存する。
- **file:line:** [probe.py:2005](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:2005)、[test:543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/tests/test_t419_probe_causality.py:543)、[test:583](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/tests/test_t419_probe_causality.py:583)
- **失敗シナリオ:** CPU0 の余剰 self 帰属で CPU1 の competitor tick を相殺する global-subtraction 変異でも現行テストは赤にならない。
- **成果物影響:** 将来の相殺回帰を mutation matrix が緑にし、汚染 armを VALID に戻す。
- **強度:** 強。静的に生存を確認できる未登録変異。
- **最小の是正案:** 2 CPU で「CPU0 self 過剰、CPU1 residual 正」の単一理由 fixtureを追加し、CPU1 residual が必ず残ることを固定する。

### F2-04 / sham の inclusive 1-tick 境界が未固定 — backlog、G-4 closure 前には必要

- **主張:** 現行実装の `delta > 1` は正しいが、テストは定数値と 2 tick の拒否だけで、1 tick の通過を検査しない。
- **file:line:** [probe.py:560](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:560)、[test:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/tests/test_t419_probe_causality.py:70)、[test:406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/tests/test_t419_probe_causality.py:406)
- **失敗シナリオ:** `>`→`>=` 変異は現行 suite を通り、sham=1 を INCONCLUSIVE にする。
- **成果物影響:** 許容された sham が3対あるだけで A2 が偽 INVALID になる。
- **強度:** 強。ただし実機で sham=1 となる頻度は未実測で弱い。
- **最小の是正案:** sham=1 の evidence が VALID、3対でも A2 VALID の正例を追加する。

### F2-05 / coercible な異常型が validity を通る — must-fix

- **主張:** CPU key と MHz 値を検査前に `int()` / `float()` へ変換するため、`"0"`、`"110.0"`、`True` を想定外型として拒否しない。
- **file:line:** [probe.py:152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:152)、[probe.py:688](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:688)、[fix2-prompt:69](/work/1/SFC/tanab/dev-wave-jobs/t419-probe-experiment/s6-fix2-prompt.txt:69)
- **失敗シナリオ:** A1 target MHz を数値文字列に替えても validity reason が出ず、帯外 evidence として causal metrics に入る。
- **成果物影響:** 破損 observation が INVALID にならず、0.95/0.05/46 と causal verdict を変え得る。
- **強度:** 契約違反は強。実 producer は float を生成するため、今回の発生可能性は未実測で弱い。
- **最小の是正案:** bool を除く厳密な数値型・厳密な int CPU ID を coercion 前に検査する。なお [test:283](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/tests/test_t419_probe_causality.py:283) は3引数を同時に壊して最初の gate しか通らないため、引数別 fixture に分ける。

### F2-06 / final binding INVALID が wrapper rc=0 になり得る — must-fix

- **主張:** final hash mismatch は payload を INVALID にするが finalizer は 0 を返し、PBS は元の `PROBE_RC` を wrapper/done へ書く。
- **file:line:** [probe.py:2827](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:2827)、[probe.py:2867](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:2867)、[probe.py:2900](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:2900)、[PBS:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.pbs:185)
- **失敗シナリオ:** probe は VALID/rc=0、終了時 hash 再照合だけが失敗すると、result は INVALID だが `probe.rc`、`wrapper.rc`、done-marker はすべて 0。
- **成果物影響:** proof chain が自己矛盾し、rc/done を見る consumer が INVALID 成果物を成功物として採用できる。
- **強度:** 強。分岐は静的に確定。
- **最小の是正案:** finalization-induced INVALID を非零 wrapper rc へ伝播し、その最終値を manifest・wrapper.rc・done-markerで一貫させる fixtureを追加する。

テスト順依存は静的には見つからない。`synthetic_fixture()` は呼出しごとに `_synthetic_base()` を再生成し、monkeypatch も pytest scope 内である。

## 変異耐性

実走ではなく静的な赤予測である。

| 変異 | 最終判定 | 赤になる node |
|---|---|---|
| M1 | KILLED | [test_paired_contrast_only_fixture_kills_m1:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/tests/test_t419_probe_causality.py:97) |
| M2a | KILLED | [test_a4_primary_count_gate_has_a_single_reason_fixture:252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/tests/test_t419_probe_causality.py:252) |
| M2b | KILLED | `test_invalid_fixtures_are_not_evaluated[exception_only]`（[test:224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/tests/test_t419_probe_causality.py:224)） |
| M3 | KILLED | [test_in_band_non_nominal_uses_canonical_band:205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/tests/test_t419_probe_causality.py:205) |
| M4 | KILLED | [test_alpha_converges_by_positional_cumulative_minimum:210](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/tests/test_t419_probe_causality.py:210) |
| M5a | KILLED | [test_contention_invalidates_execution_and_verdict:288](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/tests/test_t419_probe_causality.py:288) |
| M5b | KILLED | residual は [test:543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/tests/test_t419_probe_causality.py:543)、PID 分岐は [test:643](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/tests/test_t419_probe_causality.py:643) |
| M6 | KILLED | [test_should_reject_rows_are_not_replaced_by_constant_reject:535](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/tests/test_t419_probe_causality.py:535) |

列挙された変異の生存は **なし**。ただし未登録の「CPU 横断 global subtraction」と「sham `>`→`>=`」は現行 suite を生存する。

## 閾値・契約の不変性

| 契約 | 判定 |
|---|---|
| 0.95 / 0.05 / 46 | 値・inclusive 比較とも不変（[probe.py:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:41)、[probe.py:434](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:434)） |
| 445 | arm 合計 assert、登録値、manifest、provenance とも445（[probe.py:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:61)、[probe.py:2889](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:2889)） |
| canonical band | median±tolerance、inclusive endpoint とも不変 |
| INVALID ⇒ NOT_EVALUATED | 明示的な全 INVALID 生成経路で維持（[probe.py:1067](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1067)、[probe.py:2827](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:2827)）。ただし F2-05 の過少 INVALID は残る |

## 総括

(a) **NO-GO** — 現状で計算ノードへ1回だけ投げる価値はない。  
(b1) G-1 は child 全生存期間と process/CPU snapshot 窓を正しく帰属できず、偽 INVALID と見逃しの双方が残る。  
(b2) G-5 は coercible な異常型を VALID に通し、親の total validity 契約を満たさない。  
(b3) final hash mismatch で result は INVALID でも wrapper/done が rc=0 になり、証拠鎖が矛盾する。  
(c) 列挙された M1/M2a/M2b/M3/M4/M5a/M5b/M6 の生存はなし（静的判定）。  
(c) 未登録生存は CPU 横断相殺変異と sham inclusive-boundary 変異。  
(d) 修正後、親は計算ノードで全 pytest と mutation matrix を実走すること。  
(d) 実機では child の start/end 端 tick、snapshot 窓、三値継続・停止、residual/self 上界を照合すること。  
(d) final hash mismatch を強制し、result・probe.rc・wrapper.rc・done・manifest・`.o/.e`・最終会計 receipt の一致を確認すること。  
静的 read-only レビューのみで、pytest・self-test・PBS・probe は実行していない。