[severity: must-fix]  
[攻撃シナリオ: rep 0 が timeout または例外で抜け、rep 1・2 が成功する。`rep_returncodes` は成功分だけを append するため、`enumerate(rep_returncodes)` で観測を結合すると rep 1 の rc を rep 0 に誤結合し、失敗 rep が有効値として通る。`subprocess_runner` も条件付き伝播のため、観測有効化だけでは差し替え seam を通らない。]  
[根拠: `orchestrator/calibrator/runner.py:378-381`, `orchestrator/calibrator/runner.py:454-469`, `s2-plan.md:34-42`]  
[提案: rep 数で事前確保した indexed record に、成功・timeout・例外・未知を必ず格納する。観測 sink が指定された場合は `subprocess_runner` を常に同じ seam へ渡し、失敗記録を欠落扱いにしない。既存 monkeypatch へは新 kwargs を sink 指定時だけ渡す。]

[severity: must-fix]  
[攻撃シナリオ: `measure_point` が `ScalePoint` を返しても、計画で追加する rep 証跡の受け渡し先が `SessionRecord` まで定義されていない。`_Runner` が従来どおり `throughputs` だけを投影すると、証跡なしのカスタム `measure_fn` が 5 個の正値を返しただけで、全 rep 完備として median に入る。]  
[根拠: `orchestrator/calibrator/model.py:54-73`, `orchestrator/campaign/s8b_floor_campaign.py:2390-2403`, `orchestrator/campaign/s8b_floor_campaign.py:2454-2487`, `s2-plan.md:85-103`]  
[提案: `ScalePoint` から `_finish_session` までを通る型付きの測定結果 carrier を追加し、rep 証跡を必ず同じ呼び出しの結果として搬送する。通常測定で証跡がない場合は `unknown` として拒否し、空 list や 0 に変換しない。]

[severity: must-fix]  
[攻撃シナリオ: perf 出力に同じイベントの有効行の後で `<not counted>` 行が現れる。`parse_perf_stat` は欠損値で既存属性を消去しないため、最後の状態が欠損でも値が残り、4 イベント非 None 判定が complete になる。さらに rep 証跡が status と missing 名だけなら、producer と verifier が同じ誤った要約を共有しても検出できない。]  
[根拠: `orchestrator/calibrator/perfparse.py:59-76`, `orchestrator/calibrator/perfparse.py:97-107`, `orchestrator/calibrator/runner.py:386-397`, `s2-plan.md:44-58`]  
[提案: イベントごとの raw 値または raw 行を保存し、重複・有効値と欠損値の混在を不整合として扱う。verifier は producer の status だけを再利用せず、保存した証跡から全 `PERF_EVENTS` を独立に検証する。]

[severity: must-fix]  
[攻撃シナリオ: 計画の positive control が `_make_measure_fn` から `_FakeScalePoint` を直接返す。実際の `run_once`、perf parser、rc seam を一度も通らないため、`run_once` の rc 収集を削除する変異や、欠損イベントを一部だけで complete とする変異が生き残る。`[100,100,101,103,103]` の期待値も、旧実装の throughputs コピーが残れば同じ値で通る。]  
[根拠: `orchestrator/tests/test_s8b_floor_campaign.py:360-386`, `orchestrator/tests/test_s8b_floor_campaign.py:399-461`, `s2-plan.md:125-157`, `docs/failures.md:F9`, `docs/failures.md:F69`, `docs/failures.md:F81`]  
[提案: positive control はデフォルトの `measure_point` 経路を使い、実 subprocess だけを対象 seam で差し替える。期待する raw rc、全イベント、qualified throughput、median は実装から導出せずリテラルで固定し、旧コピー実装なら必ず値が変わる fixture にする。]

[severity: must-fix]  
[攻撃シナリオ: v3 artifact の `rep_integrity_failures` が `"0"`、`False`、または rep の `returncode` が `True` である。既存の `int(...)` や `bool(...)` 型変換を踏襲すると、異常な証跡が 0 件・成功として受理される。新 field 欠落を `[]`、`0`、`None` で補えば、正値 throughput の session が valid になる。]  
[根拠: `orchestrator/campaign/s8b_floor_stats.py:414-425`, `orchestrator/campaign/s8b_floor_campaign.py:2653-2667`, `s2-plan.md:34-40`, `s2-plan.md:107-121`]  
[提案: 変換前に `type(x) is int`、非負、`bool` ではないことを検証する。必須証跡の欠落は即時 reject とし、既定値を違反なしの意味で使わない。null を許す条件も competing・launch・preprobe skip などへ限定する。]

[severity: should-fix]  
[攻撃シナリオ: precedence テストが preprobe の competing または測定例外を使う。preprobe competing は測定前に return し、測定例外は `ScalePoint` 自体を作らないため、rep integrity と competing／launch の競合が存在しない。テストが赤くなっても、新設 gate の優先順位ではなく旧来の reason や空 throughput を検査しただけになる。]  
[根拠: `orchestrator/campaign/s8b_floor_campaign.py:2365-2375`, `orchestrator/campaign/s8b_floor_campaign.py:2381-2409`, `orchestrator/campaign/s8b_floor_campaign.py:2424-2438`, `s2-plan.md:64-81`]  
[提案: 実測を完了して rep integrity 証跡を持つ session に、後段 competing または launch 状態を注入する。検査対象は reason 文字列だけでなく、`valid`、median、cell への投影、受理集合の変化にする。]

[severity: should-fix]  
[攻撃シナリオ: 「v2 journal の新 field 欠落を既定値 0 にする」変異に対し、v2 resume reject テストを期待 node にする。現状は session field 検証以前に campaign-start の schema version 検査で停止するため、変異が新しい fail-closed 検査を壊していても同じテストが赤くなり、帰属が成立しない。]  
[根拠: `orchestrator/campaign/s8b_floor_campaign.py:3593-3604`, `orchestrator/campaign/s8b_floor_campaign.py:3632-3634`, `s2-plan.md:159-176`, `docs/failures.md:F60`]  
[提案: v2 version reject は独立テストにする。新設 field の検査は、schema v3 だが observation 欠落・未知・件数不一致の journal を用い、最初に evidence gate が発火することまで確認する。]

[severity: must-fix]  
[攻撃シナリオ: producer が `excluded`／`attempts` に `rep_integrity_failures` や `exclusion_class` を追加しても、ratified verifier の live re-projection は旧キーだけで行われる。その結果、正しい v3 result が exact comparison で拒否される。逆に producer が旧形を維持すれば、rep integrity の報告が消える。]  
[根拠: `orchestrator/campaign/s8b_ratified_freeze.py:199-248`, `orchestrator/campaign/s8b_ratified_freeze.py:2220-2260`, `s2-plan.md:85-103`, `orchestrator/campaign/s8b_holdout_freeze.py:1315-1318`]  
[提案: exact key 集合だけでなく、ratified verifier の re-projection、holdout verifier、journal／result の全 mirror を同じ v3 schema へ更新する。既存の `s8b_v2_freeze_fixture.py:109-140` と `test_s8b_ratified_verify.py:297-329` も、明示的な legacy reject fixture として扱う。]

[severity: should-fix]  
[攻撃シナリオ: `exclusion_class` だけを legacy `excluded_reason` から変更する変異を、round-trip/report テストが kill したと数える。しかし throughput、`valid`、median、floor は変わらず、変化は診断表示だけで受理集合を変えない。F86 型の「値や表示だけの変異」を gate の検証と誤認する。]  
[根拠: `orchestrator/campaign/s8b_floor_stats.py:114-152`, `orchestrator/campaign/s8b_floor_stats.py:230-281`, `orchestrator/campaign/s8b_ratified_freeze.py:2220-2260`, `s2-plan.md:159-176`, `docs/failures.md:F86`]  
[提案: mutation の合格条件を受理・拒否、median 投影、または verifier の fail-closed に限定する。report-only 変異は診断テストとして分離し、新設 integrity gate を検査した変異表へ登録しない。]

## 総括

- 最大の穴は、例外・timeout・差し替え runner を含む rep 証跡の indexed 完備性が未確定なこと。  
- 証跡の carrier が未定義で、カスタム測定関数が evidence-less な正値を返す fail-open がある。  
- perf の要約だけでは重複・途中打ち切りを独立検証できず、parser にも値の残留がある。  
- positive control は現状 production の runner と parser を通らず、重要な変異を殺せない。  
- 型変換と既定値は、欠落・不正値を成功または違反なしへ変換し得る。  
- precedence と v2 resume のテストには先取りがあり、新設 gate への帰属を壊す。  
- ratified verifier の re-projection 更新漏れは、正しい v3 artifact 自体を拒否する。  
- これは静的検査のみであり、pytest は実走していないため、緑とは判定していない。