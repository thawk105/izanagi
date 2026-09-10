```text
[severity: must-fix]
[攻撃シナリオ: pre-probe の competing または measure 例外 session について、空の証跡と正しい excluded_reason を保ったまま exclusion_class だけを rep_integrity_failure に改変する → verifier は証跡免除分岐で classification を照合せず、整合する journal/result 投影を受理する]
[根拠: orchestrator/campaign/s8b_floor_stats.py:662, orchestrator/campaign/s8b_floor_stats.py:689, orchestrator/campaign/s8b_ratified_freeze.py:244, orchestrator/campaign/s8b_ratified_freeze.py:2224]
[成果物影響: 床値と certified 選択は同じでも、レポートの除外理由別件数と attempt 台帳が competing/launch から rep_integrity_failure へ偽装され、その参照を ratified verifier が有効として通す]
[提案: 証跡免除の外側で全 session の exclusion_class を excluded_reason と再導出 failure 数から必ず照合し、generic verifier でも同 key を必須化する。competing と launch 各 1 件の改変負例を追加する]
```

```text
[severity: should-fix]
[攻撃シナリオ: M1 を裁定どおり wave 前の _project_scalepoint 全体へ戻す → 新 consumer が rep_observations キーを読む時点で KeyError となり、median 混入 assert へ到達しない。throughputs だけを無条件コピーへ変えても、最初の throughputs assert で落ち、median/cell assert は実行されない]
[根拠: orchestrator/campaign/s8b_floor_campaign.py:2505, orchestrator/tests/test_s8b_floor_campaign.py:2713]
[成果物影響: 現行成果物値への直接影響はないが、変異台帳が「壊れた rep の中央値混入を検出した」と誤って記録される]
[提案: M1 を出力 shape を保つ単一変異へ固定し、投影検査と median/cell 混入検査を別 node に分ける。M2 は projection ではなく reps 本数 gate を緩める位置へ再登録する]
```

```text
[severity: should-fix]
[攻撃シナリオ: M1/M2 を nonzero_rc に適用する → 同じ else 節を通る missing_cycles parameter も同時に赤になる。M4 で missing counter を許すと、専用 4 parameter に加えて positive control の missing_cycles も赤になる → 申告した期待 node 集合より actual が大きくなる]
[根拠: orchestrator/tests/test_s8b_floor_campaign.py:2637, orchestrator/tests/test_s8b_floor_campaign.py:2657, orchestrator/tests/test_s8b_floor_campaign.py:2713, orchestrator/tests/test_s8b_floor_campaign.py:2722]
[成果物影響: 現行床値には直結しないが、M1/M2/M4 の変異台帳は KILLED でなく MISMATCH となり、事前登録済み耐性という参照が成立しない]
[提案: parameter suffix を含む完全 node 集合を登録する。少なくとも M1/M2 は nonzero_rc と missing_cycles、M4 は専用 4 node と positive-control missing_cycles を含める]
```

```text
[severity: should-fix]
[攻撃シナリオ: M4 の申告どおり「4 event の all を any にする」置換を試す → rep counter 完備判定には対応する all 呼び出しが存在せず、唯一近い all は throughput の有限正値判定であるため、変異を一意に注入できない]
[根拠: orchestrator/campaign/s8b_floor_campaign.py:1148, orchestrator/campaign/s8b_floor_campaign.py:1161, orchestrator/campaign/s8b_floor_stats.py:494, orchestrator/campaign/s8b_floor_stats.py:528]
[成果物影響: 現行成果物値への直接影響はないが、M4 の anchor と kill 帰属が不成立になり、counter 完備性の変異証拠を台帳へ載せられない]
[提案: 実在する単一条件、例えば incomplete を資格対象へ含める条件変更へ再登録し、producer と verifier のどちらを変異するか明記する]
```

```text
[severity: should-fix]
[攻撃シナリオ: M7 として partial 分岐を rep integrity より先へ移す → integrity 違反時は投影済み throughputs が 4 本なので derived_reason も nonfinite_or_partial_output となり、どちらの順序でも excluded_reason、valid、median、exclusion_class が同一になる。赤になるのは AST 順序 assert だけである]
[根拠: orchestrator/campaign/s8b_floor_campaign.py:2532, orchestrator/campaign/s8b_floor_campaign.py:2557, orchestrator/campaign/s8b_floor_campaign.py:2597, orchestrator/tests/test_s8b_floor_campaign.py:2824]
[成果物影響: 成果物の値・受理集合・参照は変化せず、M7 を KILLED と数えると変異台帳だけが過大計上される]
[提案: M7 を受理集合変異から外し diagnostic sensitivity pin に移す。順序に成果物上の差を持たせない現設計では、behavioral kill を要求しない]
```

```text
[severity: should-fix]
[攻撃シナリオ: M12 で returncode の exact-int 検査を isinstance へ緩め、fixture の True を投入する → True は依然 0 と等しくないため session は fail-closed のまま。それでもテストは returncode を含む診断文字列が消えたことだけで赤になりうる]
[根拠: orchestrator/campaign/s8b_floor_stats.py:484, orchestrator/campaign/s8b_floor_stats.py:548, orchestrator/tests/test_s8b_floor_stats.py:490]
[成果物影響: returncode=True の受理集合は変わらず、この parameter を M12 の kill に含めると変異台帳が診断文字列だけの赤を耐性として数える]
[提案: returncode fixture を False にして bool-as-zero の fail-open を直接作る。rep_index=False とは parameter suffix 付きの別 node として期待集合を登録する]
```

## 総括

- must-fix は 1 件で、証跡免除 session の `exclusion_class` が意味検証されず、レポートと台帳を偽装できる。
- positive control は production の `measure_point`、`run_once`、`parse_perf_stat` を通り、計測面の差し替えは subprocess に限定されている。
- TPS と期待 median は `[100, 100, 101, 103, 103]` と `101` のリテラルで、実装から導出されていない。
- M1 は node を赤にするが、median 混入より前の KeyError または throughputs assert で落ちるため、主張した帰属は成立しない。
- M2 は projection 単独の変異ではなく、後段の reps 本数 gate の変更を必要とする。
- M7 は成果物不変の構造検査、M12 の `returncode=True` は診断だけの赤であり、F86 型である。
- rc は logical index 付き observation に全 rep 分確保され、timeout・例外は `None`、完了 process は exact rc として保存される。
- counter の欠損、空、途中打ち切り、重複、小数、負値は静的には fail-closed。巨大な非負 exact int は裁定どおり complete になる。
- 既存安全テストの反転・緩和・skip・削除、および working tree hash の期待値への焼き込みは差分から認めなかった。
- pytest は実行しておらず、以上は未コミット差分の静的検査結果である。