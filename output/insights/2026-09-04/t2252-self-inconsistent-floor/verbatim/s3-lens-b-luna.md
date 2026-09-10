## 所見

1.
   **対象 (file:line):** [s2-plan.md:23](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2252-self-inconsistent-floor/artifacts/t2252-self-inconsistent-floor/s2-plan.md:23>)、[s2-plan.md:27](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2252-self-inconsistent-floor/artifacts/t2252-self-inconsistent-floor/s2-plan.md:27>)、[s2-plan.md:33](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2252-self-inconsistent-floor/artifacts/t2252-self-inconsistent-floor/s2-plan.md:33>)、[calibration_verify.py:2](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/calibration_verify.py:2>)、[layer3_report.py:845](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:845>)
   **何が問題か:** `KNOWN_SELF_INCONSISTENT_CALIBRATIONS` という複数要素・将来更新を前提にした共有 `frozenset` を calibration admission leaf へ置く案は、D1537 の既知 1 件を局所的に表す以上の production 例外台帳である。また材料レポートが記録する generator hash は `layer3_report.py` 自身だけなので、外部 module の集合だけが変わると、同じ generator hash で床値選択が変わり得る。
   **裁定にどう効くか:** D1538 は genome 不在 record について内容 hash allowlist を明示的に裁定したが、これは別項であり、D1537 に共有台帳を設ける許可にはならない。[D1537:5-19](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2252-self-inconsistent-floor/verbatim-decisions.md:5>) が確定したのは exact g1 を使わないことまでである。
   **性質 (real / refuted):** real
   **推奨する扱い:** 共有集合案は scope 外の裁定パッケージ候補として戻す。本 wave は D1537 の exact g1 pair を `layer3_report.py` 内の局所的な比較として表し、既存 test-local の自己比較監査は独立 oracle のまま残す。新しい manifest や台帳は足さない。

2.
   **対象 (file:line):** [s2-plan.md:23](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2252-self-inconsistent-floor/artifacts/t2252-self-inconsistent-floor/s2-plan.md:23>)、[s2-plan.md:37](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2252-self-inconsistent-floor/artifacts/t2252-self-inconsistent-floor/s2-plan.md:37>)、[env_contract.py:899](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/env_contract.py:899>)
   **何が問題か:** 新 status `self-inconsistent-awaiting-healthy-generation` は除外に不要で、g2 発効後には歴史的 g1 lock に対して事実とずれる。g1 hash は `ever_active` に残るため既存 campaign は引き続き g1 を解決し、plan は g1 pair を宣言に残すので、その within-run は一致なしのままである。一方、新 campaign は g2 を pin して採用される。
   **裁定にどう効くか:** D1537 の「発効後に値は自然に埋まる」は、immutable な authority から見て「発効後に生産される g2-pinned campaign」を指す。既存 g1-pinned campaign が後から g2 へ読み替わる意味ではない。新 status は D1537、D1374、D437 のいずれも要求せず、材料レポートへの追加表示だけを増やす。
   **性質 (real / refuted):** real
   **推奨する扱い:** 新 status とその test assert は削る。既存の `validated` は path/file/SHA 検証済みという現在の意味のまま保ち、D1537 の実効要件は within-run candidate へ append しないことだけで満たす。

3.
   **対象 (file:line):** [brief.md:36](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2252-self-inconsistent-floor/brief.md:36>)、[s2-plan.md:35](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2252-self-inconsistent-floor/artifacts/t2252-self-inconsistent-floor/s2-plan.md:35>)、[layer3_report.py:832](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:832>)、[layer3_report.py:845](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:845>)、[layer3_report.py:888](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:888>)
   **何が問題か:** 成果物影響の記述が不完全である。g1-pinned report は `value=None`、`provenance=no-matching-env-record`、`source=None` へ変わり、accepted report も同じ `build_report` を通る。さらに `layer3_report.py` の変更により、Pegasus 以外も含む今後の全 report の `meta.generator.sha256` が変わる。
   **裁定にどう効くか:** 既存 7 report は再生成されないため D1537 の「既存成果物を変えない」とは衝突しない。現 checkout に certified-selection consumer は存在せず、受理判定は floor 計算前に済むため、受理集合・試行台帳・certified 選択結果は変わらない。変わるのは新規材料/accepted report の床値投影と generator 参照である。
   **性質 (real / refuted):** real
   **推奨する扱い:** 実装追加ではなく、plan の成果物影響をこの範囲に訂正する。既存 report bytes を再生成しないことも明記する。

4.
   **対象 (file:line):** [brief.md:38](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2252-self-inconsistent-floor/brief.md:38>)、[brief.md:40](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2252-self-inconsistent-floor/brief.md:40>)、[test_layer3_report.py:1516](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/tests/test_layer3_report.py:1516>)、[test_official_perf_closure.py:44](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/tests/test_official_perf_closure.py:44>)
   **何が問題か:** brief の「schema 凍結はキー集合」という表現は広すぎる。実 test が固定するのは schema version、`runs.items.required`、`screening_disabled` の一部だけで、top-level 全キーや `contract_pin.status` 値域ではない。plan 自身の line 72 の訂正が正しい。また official closure は reviewed-file/call predicate であり、source bytes 台帳ではない。
   **裁定にどう効くか:** 新 status が schema に拒否されないことは確認できるが、それは status 追加が必要・scope 内である根拠にはならない。
   **性質 (real / refuted):** real
   **推奨する扱い:** brief の実測表現だけを狭める。production schema や新検査は追加しない。

5.
   **対象 (file:line):** [D1537:16-19](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2252-self-inconsistent-floor/verbatim-decisions.md:16>)、[s2-plan.md:35](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2252-self-inconsistent-floor/artifacts/t2252-self-inconsistent-floor/s2-plan.md:35>)、[layer3_report.py:393](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:393>)
   **何が問題か:** plan の宣言参照が「却下された自己整合性再検査」に当たる疑いを検査したが、これは当たらない。
   **裁定にどう効くか:** 一文で区別すると、再検査は層 3 が artifact の samples/tolerance を読み effective-clock predicate を再実行して判定することであり、宣言参照は authority が解決した immutable `(path, sha256)` を裁定済み exact identity と比較して既定の除外を適用することである。plan は後者で、`_validated_pin_path` は自己整合性ではなく path/file/SHA の既存検証である。
   **性質 (real / refuted):** refuted
   **推奨する扱い:** validation を先に完遂してから within-run candidate だけを除外する核は維持する。effective-clock 比較は層 3 に追加しない。

6.
   **対象 (file:line):** [s2-plan.md:48](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2252-self-inconsistent-floor/artifacts/t2252-self-inconsistent-floor/s2-plan.md:48>)、[s2-plan.md:56](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2252-self-inconsistent-floor/artifacts/t2252-self-inconsistent-floor/s2-plan.md:56>)、[s2-plan.md:58](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2252-self-inconsistent-floor/artifacts/t2252-self-inconsistent-floor/s2-plan.md:58>)、[test_layer3_report.py:3467](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/tests/test_layer3_report.py:3467>)、[test_env_contract.py:856](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/tests/test_env_contract.py:856>)
   **何が問題か:** テストが空実装・握り潰しでも緑になる疑いを検査したが、核となる案は実効的である。g1 の 2 件は実 `build_report → _contract_calibration_pin → _calibration_floors` を通り、除外が無ければ CV `0.011705…` が出て赤になる。SHA 改竄 test は membership 短絡を検出する。g2 正例は実 bytes/ref と実 `_calibration_floors` を通り、全 pin 除外を検出する。自己比較 audit も実 profile/predicate との集合完全一致なので空集合や余分な要素を許さない。
   **裁定にどう効くか:** brief P5 が認めた既存期待値変更は line 3467 と 3672 の 2 件だけで、plan に他の既存期待値反転は紛れていない。nested test が先行 gate で機構へ届かない冗長 gate でもない。ただし g2 正例は activation を通らない consumer seam test であり、「発効後の新 campaign」全鎖の証明ではない。
   **性質 (real / refuted):** refuted
   **推奨する扱い:** g2 正例、g1 の 2 負例、SHA fail-closed、自己比較 audit を維持する。新 status の assert だけは所見 2 に従い外し、g2 test を activation 全鎖の実測とは報告しない。

## brief と plan が正しかった点

- 実 registry には Pegasus g1/g2 の exact ref があり、g1 は `753f…`、g2 は `94a4…` である。[env_contract.py:253](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/env_contract.py:253>) [env_contract.py:270](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/env_contract.py:270>)。activation head は linux g1 と Pegasus g1 だけを active にしており、g2 は never-active である。[00000001.json:1](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/env_contract_activations/00000001.json:1>)

- 除外入力は campaign lock に path/SHA が直接入るのではなく、`authority.environment_contract_sha256` から世代を解決し、その contract の `calibration_ref.path` / `sha256` を得る。[campaign_lock.py:84](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/campaign_lock.py:84>) [layer3_report.py:364](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:364>)。現在の Pegasus v2 発行なら g1 pair へ実際に到達できる。repo 内の現存 30 campaign lock は静的 inventory 上すべて v1 で、既存 Pegasus v2 campaign はなかった。

- g1 artifact は accepted・notes 空だが、48 samples 中の `3080.935` が中央値 2101 の ±2% 帯を外れる。g2 は全 sample 2101 である。[g1 calibration:1](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1>) [g2 calibration:1](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json:1>) [execution_guard.py:399](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/execution_guard.py:399>)。brief の g1 false / g2 true は静的に成立する。

- plan が brief P2 の「validation 前に除外」を退け、SHA・directory・通常 file 検査後に candidate append だけを止めた点は正しい。[brief.md:65](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2252-self-inconsistent-floor/brief.md:65>) [s2-plan.md:68](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2252-self-inconsistent-floor/artifacts/t2252-self-inconsistent-floor/s2-plan.md:68>)

- 変更行と裁定の 1 対 1 対応は次のとおり。

| plan 行 | 裁定との対応 | 必要性と成果物効果 |
|---|---|---|
| 33–34 宣言/import | D1537 の exact g1 識別には必要。ただし共有集合という形は所見 1 の scope 外 | consumer を介してのみ g1 floor を除外 |
| 35 validation 後の除外 marker | D1537 と既存 fail-closed の両方に整合 | 必要。単独では出力を変えず、exact validated pin だけを filter へ渡す |
| 36 within-run append 抑止 | D1537 に直接対応。D1374 の直下 record 表示は不変 | 必要。g1 floor を null/source なしへ変更 |
| 37 新 status | 対応する裁定なし | 不要。search detail だけを変更 |
| 38 `_contract_calibration_pin` 無変更 | D1537/D437 と整合 | authority・v1・env mismatch・never-active の受理集合を維持 |
| 39 test 変更 | D1537 の実効性確認に対応 | production 成果物への影響なし。共有 import 部分だけ所見 1 に従い不要 |
| 40 env contract 無変更 | D437、D1538、D1374 と整合 | contract hash、activation、登録 ref、受理集合を不変に保つ |

- D1374 の `genome-absent-legacy-record` は直下 record 経路で維持される。[layer3_report.py:466](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2252-self-inconsistent-floor/orchestrator/campaign/layer3_report.py:466>)。D1538 の genome 不在 allowlist は本 plan が触らない。D437 に反する g2 activation もない。

- D95 に対して production/test 差分を Codex author 1 単位へ渡す分割は整合する。D387 の receipt・偽造耐性には変更がなく、衝突もない。

- 現存 7 report はすべて linux-baremetal で、within-run は 5 件 null、2 件が既存 linux record を source に持つ。したがって既存 artifact を再生成しない限り、値が変わらないという brief の主張は成立する。

## 総括

最も重い所見は、`calibration_verify.py` の共有 `frozenset` が新しい production 例外台帳になり、材料レポートの generator hash にも束縛されない点である。共有台帳を望むなら裁定へ戻し、本 wave は consumer-local の exact g1 除外へ狭めるべきである。
新 status は D1537 に不要で、g2 発効後の歴史的 g1 lock に対して語義も古くなるため外すべきである。
既存 g1 campaign は g2 発効後も一致なし、新 g2-pinned campaign だけが条件一致時に g2 値を採る。「自然に埋まる」は後者を指す。
親が実測すべきなのは、修正後の焦点 node、g1/g2 actual bytes、全 7 既存 report の値不変、および新 report の generator hash 変化である。
本検査は read-only の静的確認のみで、pytest・probe は実走していない。