## 総括

NO-GO。

- プランは `report.json` 生成までの主要経路を押さえるが、走 a の既存 `partial-generation` と、提案する `pending-pre-invoke-failure` が衝突する。
- 選択 workload が `[ycsb-a,ycsb-b,ycsb-c]` で cell が `ycsb-a` だけの場合、現行 coverage 検査はまだ停止する。
- 走 b は report 化できる可能性があるが、`build_start` の欠陥自体は未修正である。
- 診断 report は parse error と payload/envelope path は持つが、raw response への直接参照を持たない。
- 基本テストは旧実装を赤くできるが、F332 が要求する multi-workload の実在 report 検査までは不足している。

## 関門の完全列挙

(a)〜(d) を通過したとしても、`_write_json_atomic` までは次の関門が残る。

1. 後処理状態の fail-closed 検査。

   - pending critic が残っていれば `:2172-2173` で停止する。
   - build cell の `admission_decision` が無ければ `:2174-2177` で停止する。
   - `status`、generation accounting、origin projection、fatal error の組み立てが `:2161-2241` にあり、型不整合や欠落で停止しうる。
   - `honest_accounting` の集計は `:2180-2186`、origin terminal projection は `:2225-2230`、transport receipt は `:2231-2234` で例外を投げうる。

2. run-finish journal の永続化。

   - `run-finish` の `journal.append` は `p3_autonomous_workload_trial.py:2242-2253`。
   - `AttemptJournal.append` は journal が failed 状態なら `:590-605` で停止し、ファイル書き込み、flush、fsync、close でも `:614-632` の例外がありうる。

3. journal hash の作成。

   - `attempts.jsonl` の read と hash は `p3_autonomous_workload_trial.py:2254`。
   - 読み取り失敗、journal の同時変更、パス異常があればまだ report は書かれない。

4. `assert_autonomous_trial_completeness` の全検査。

   `autonomous_trial_completeness.py:1774-1842` は次の順で全て失敗しうる。

   - journal の改行、JSON framing、object 形状: `:194-211`
   - journal hash: `:1779-1782`
   - closed event set: `:1783`、実体は `:727-731`
   - sequence: `:1784`、実体は `:734-739`
   - transport admission: `:1785`、実体は `:742-854`
   - run envelope、run-start/run-finish の位置、path、status: `:1786`、実体は `:1015-1168`
   - origin projection: `:1789`、実体は `:974-1012`
   - cell の admission decision: `:1790-1818`
   - terminal projection: `:1819`、実体は `:1175-1241`
   - budget: `:1820-1822`
   - journal 側 attempt の一意性、role session isolation: `:1823-1827`、実体は `:696-725`
   - report 側 attempt の metadata、role prefix、stop reason、harness: `:1828-1831`、実体は `:1367-1523`
   - attempt sequence と journal/report bijection: `:1832-1836`
   - workload coverage: `:1837`、実体は `:1537-1605`
   - generation accounting: `:1838-1840`、実体は `:1627-1772`
   - status projection: `:1841`、実体は `:1608-1624`
   - payload validation receipt: `:1842`、実体は `:578-593`

5. workload coverage の第 5 関門。

   走 a のように requested が `[ycsb-a,ycsb-b,ycsb-c]`、actual cell が `[ycsb-a]`、terminal event が無い場合、現行コードは `:1581-1582` で `requested workload suffix is unexplained` になる。

   `_check_terminal_projection` 自体は role-invalid だけなら terminal 無しを許す。`autonomous_trial_completeness.py:1183-1200` は fatal error、supervisor-error、wall-budget cell の場合だけ terminal を要求する。しかし coverage 側が別に suffix を要求するため、admission decision の受理集合を広げるだけでは走 a は通らない。

6. Layer 3 chain。

   `p3_autonomous_workload_trial.py:2259-2268` で chain が呼ばれ、`autonomous_trial_completeness.py:1996-2123` が campaign root、persisted `reports/layer3_report.json`、独立 admission、decision 一致、fresh rebuild を検査する。

   失敗 cell のみ免除し、admitted peer は全検査するというプランは妥当だが、failure-only report を chain に渡す場合の root と呼び出し条件を明示しないと、ここで止まる。

7. completeness 後の hash 再検査。

   `p3_autonomous_workload_trial.py:2269-2274` で journal bytes が変化していないことを再確認する。ここも failure decision を journal に追加する設計へ変える場合の再計算順序が必要になる。

8. 最終 writer。

   `_write_json_atomic` は `p3_autonomous_workload_trial.py:1283-1293`。JSON serializable 性、NaN、temporary path の symlink、exclusive open、write、fsync、`os.replace` のいずれも例外点である。

したがって、failure cell が通るには、少なくとも role scan、accounting、coverage、terminal projection、chain の同時成立が必要である。admission の一箇所だけを緩めても report は到達しない。

## 成立した攻撃

1. 主張: 走 a はプランの accounting 条件で止まる可能性が高い。

   根拠: プランは `plan.md:20-22` で failure generation accounting を `pending-pre-invoke-failure` とし、completeness でも同状態を要求する。しかし `_run_workload` は `:2684-2691` の `finally` で active accounting を既に journal へ append する。親の走 a は seq5 が `partial-generation` である。`_append_generation_accounting` は `:1152-1154` で一度だけ確定を要求し、journal は append-only である。

   成果物への影響: finalizer で後から pending state を追加すると duplicate pair で `:1665-1668` に止まる。既存 event を変更できないため、走 a は `:2275` に届かない。

   提案する塞ぎ方: `:2684-2691` の確定境界を failure decision まで延期して一度だけ pending にするか、role-invalid の既存 `partial-generation` を exact failure cell に限って受理する。後処理だけで再分類する設計は成立しない。

2. 主張: 選択 workload 数より cell 数が少ない走 a を受理する仕様がまだ不十分である。

   根拠: 実際の job は `live.pbs:145-149` で三つの workload を選択する。現行 coverage は `:1549-1551` で requested prefix を確認し、terminal 無しの suffix を `:1581-1582` で拒否する。プランは `plan.md:22` で suffix を説明可能にすると述べるが、exact failure decision、最終 cell、`stop_reason`、後続 cell 不在を結びつける受理条件と producer 統合テストが明示されていない。

   成果物への影響: 一 workload fixture だけでは green でも、親が実測した三 workload の report は completeness で失敗する。

   提案する塞ぎ方: `[ycsb-a,ycsb-b,ycsb-c]` を実際に選択し、最初の cell を failure にして suffix を残す producer テストを追加する。failure cell が唯一の最終 cellで、後続 cellがなく、status が partial であることを report と disk の両方で検査する。

3. 主張: 走 b の report 化は可能だが、`KeyError` を直したことにはならない。

   根拠: trigger の `_wal_binding_commitment` は `p3_s4_loop_trigger_gating.py:524-526` で `records[STAGE_BUILD_START]` を直接参照する。skip/variant 経路も `:614-626` でこの関数を呼ぶ。`build_start` が無い records map では直接 `KeyError` になる。

   走 b は `p3_autonomous_workload_trial.py:2039-2051` でその KeyError を supervisor-error として記録し、`:2073-2077` で admission finalizer に入る。プランの catch が finalizer 由来の `AutonomousTrialError` に限定されるなら、元の `fatal_error` は保持したまま failure decision を追加できる。ただし finalizer 自身が bare `KeyError` を投げた場合は意図どおり伝播して report は出ない。

   成果物への影響: report が出ても、次回以降の trigger 実行は同じ `build_start` 欠落で止まる。

   提案する塞ぎ方: trigger 側で stage 欠落を明示的な recovery error に変換するか、`build_start` が無い WAL shape を正式に扱う。これは本 wave に混ぜず裁定へ返す。

4. 主張: report の診断性は部分的であり、raw coder response の参照が欠ける。

   根拠: parse error は `_redacted_transport_error` の本文として `p3_autonomous_workload_trial.py:1368-1386` に残る。coder の invalid event は `:2545-2564` で generation record に入り、report の cell projection に現れる。payload/envelope の path と hash も `:1502-1524` で `error_artifacts` に入る。

   一方、raw response は `:1497-1500` で `raw/raw_<invocation>.txt` に保存されるだけで、invalid event の `error_artifacts` には raw path/hash が入らない。

   成果物への影響: report から parse error と payload/envelope は追えるが、失敗した coder の実際の raw response を直接指せない。「なぜ落ちたか」を含む成果物という brief の主張は最低限満たすが、完全な診断成果物とは言いにくい。

   提案する塞ぎ方: raw response の path/hash を明示的な参照として invalid event と report に追加し、必要なら completeness 側で path の安全性を検査する。

5. 主張: 基本テストは恒真ではないが、再発検知としては不足がある。

   根拠: プラン `plan.md:68-72` は旧テストの `pytest.raises` と report 不在期待を、disk 上の `report.json` 実在と返却値一致へ変更する。旧 production は `:2106` または `:2073` 後の finalizer raise で report を書かないため、このテストは旧実装で赤くなる。F332 も実在する verified partial report の producer テストを要求している `docs/failures.md:8118-8124`。

   しかし一 workload のままなら suffix branch、既存 `partial-generation`、failure-only chain、root 引数なし verifier の変異は生き残る。chain の peer テストだけでは producer が実際に report を書いたことを固定しない。

   成果物への影響: 「検査が緑」を固定しても、親の三 workload 走で report が無い回帰を検出できない可能性がある。

   提案する塞ぎ方: 実際に `report.json` を `is_file()` で確認し、disk bytes を decode して返却 report と比較する producer 統合テストを、正常復帰側・supervisor-error 側の両方で三 workload fixture にする。期待値は production の定数から導出せず、failure schema、partial、非 admitted、run-finish をリテラルで固定する。

6. 主張: 親の DW-G03 の独立二例という数え上げは成立しない。

   根拠: `docs/dev-wave/core.md:55-58` は、族一般化に「異なる producer/consumer で独立に 2 件」を要求する。走 a と走 b は同じ `_finish_trial` と同じ `_finalize_build_cell_admission` を共有し、違うのは `:2106` と `:2073` の呼び出し点だけである。走 b の差分は trigger の別欠陥でもある。

   成果物への影響: 二つの control-flow smoke case としては有効だが、「admission failure 一族を一般化して閉じた」という証拠にはならない。

   提案する塞ぎ方: claim を「同一 consumer の正常復帰側と supervisor-error 側を確認した」に下げるか、異なる producer/consumer と独立 artifact shape の二例を追加する。

## 反証された懸念

- F332 の歴史的な「`transport-admission-error` が `_EVENTS` に無い」という欠陥は、現 tree では成立しない。`autonomous_trial_completeness.py:39-53` に `_EVENTS` と `_TERMINAL_EVENTS` の双方が既に存在する。failure decision を新 journal event にしない限り、F332 の event 追加面を再実装する必要はない。
- `_check_terminal_projection` が role-invalid の terminal 無しを直ちに拒否する、という懸念は反証される。`autonomous_trial_completeness.py:1183-1200` は role-invalid だけなら通す。走 a の主な失敗点は terminal projection ではなく workload coverage `:1581-1582` である。
- failure cell を `admitted` として certifying 経路へ流す懸念は、プランどおりなら成立しない。`plan.md:56-64` は `layer3_report.py:236-242,584-603` と completeness `:1969-1983` の admitted 完全一致を維持している。
- admitted peer まで Layer 3 免除される懸念も、exact failure cell だけを免除するなら成立しない。プラン `plan.md:64` は admitted peer の persisted report、decision、fresh rebuild を維持している。
- 基本の既存境界テストが production を参照して必ず緑になる、という懸念も成立しない。旧実装は report を作らないため、disk 上の実在を固定する変更は旧実装で赤くなる。

## 親 brief の誤り

- **P1: 誤り。** 四つは admission-specific な主な停止点ではあるが、全関門ではない。`p3_autonomous_workload_trial.py:2172-2177` の pending critic と decision 欠落、`autonomous_trial_completeness.py:1774-1842` の複数の内部検査、`p3_autonomous_workload_trial.py:2269-2275` の再 hash と writer が残る。F332 `docs/failures.md:8113-8124` が示すように、完全性検査の周辺面を一つだけ直しても閉じない。

- **P2: 概ね正しい。** finalizer は workload 実行後の `:1725-1774` にあり、provider/build/benchmark 起動前の D431 型 gate ではない。positive control 不要という分類は支持できる。

- **P3: 半分正しいが不十分。** 受理集合変更なので decision、completeness、chain、既存境界テスト、新 D を同じ変更単位にする判断は妥当。ただし raw response の診断参照、独立 verifier、trial registry、job script の rc 解釈までを含めて「成果物が効く全層」とするなら、P3 の scope は不足している。

- **P4: 静的には誤りと断定できない。** 実測を親が行うこと自体は妥当。ただし本レビューでは pytest も実測もしていないため、P4 の bounded test と mutation matrix を完了済みの根拠として扱うことはできない。

## scope 外だが real な所見

- `build_start` の `KeyError` は T-1175 の admission report 欠落とは別欠陥である。`p3_s4_loop_trigger_gating.py:524-526` の直接 indexing を修正する裁定パッケージ候補として返す。
- `verify_autonomous_trial_files` は `do_build=True` かつ cell 非空なら `campaign_output_root` を要求する `autonomous_trial_completeness.py:2140-2152`。failure-only report の独立検証を root 無しで許すかは別裁定である。プラン自身も `plan.md:123` で scope 外としている。
- `run-finish` event は `p3_autonomous_workload_trial.py:2242-2253` で status、report path、accounting は持つが、failure decision そのものを独立 event として束縛しない。journal による改ざん検出まで要求するなら、新 event、event set、terminal projection、registry snapshot の別設計が必要である。
- `trial_registry` は partial でも `run_root/report.json` と `attempts.jsonl` を読み、hash を保存する `trial_registry.py:1829-1845`。report path が従来どおりなら主に統合テストの不足だが、実際の lifecycle terminal まで確認する必要がある。
- live job は `live.pbs:145-155,166-168` で partial の CLI rc=2 をそのまま保存して exit する。report が存在しても scheduler 上は失敗扱いになりうる。rc=2 を診断可能な partial として収集・受理するかは job script 側の裁定候補である。