## 総括

推奨は **S3**。M4 は「非 silo だけが生産不能」という wave の承認前提を覆しており、`DW-STOP` に従って実装前に段 4 の再裁定へ返すべきである。  
M4 と現行コードが正しければ、候補 `{silo,mocc,tictoc,cicada}` に対する現行認定経路の生産可能集合は、条件付きながら正直に **空集合 `∅`** と書ける。  
ただし M1/M2 が示すのは build・define 到達性であり、plan の P1-d も較正・登録を走らせないため、正の「record 生産可能」証拠にはならない。  
Acquisition receipt への `calibration` 必須化は依頼が除外した gate・検査・台帳追加であり、削除すべき scope 膨張である。

## 所見

### 1. 承認前提が覆ったまま実装へ進む計画

- 重大度: **blocker**
- 成果物影響 1 行: 現行 gate では全候補が登録較正を生産できず、正の protocol 集合や A-4 解禁を記録すると虚偽になる。
- 根拠の file:line: `tools/pegasus/certify_calibration.sh:380-395,526-549`、`external/ccbench/cmake/Options.cmake:13-24,60-68`、`external/ccbench/include/backoff.hh:94-107`、`docs/dev-wave/core.md:34-39,50-53`、`measured-facts.md:49-77`
- 再現手順または反例: M4 の実測どおり clean detached source には `CCBENCH_BACKOFF_FIXED` と対応分岐がなく、`run_condition_gate` は rc=2。`set -e` 下の裸呼出しが configure/build より前にあるため、protocol 引数だけ増やしても後段へ進まない。

### 2. 「生産可能」の実測が実際の producer を通っていない

- 重大度: **blocker**
- 成果物影響 1 行: plan の green 集合は最大でも「較正直前まで到達可能な集合」であり、`registered/calibration-*.json` を生産できる集合としては引用できない。
- 根拠の file:line: `stage2-plan.md:194-205,317-405,423`、`orchestrator/calibrator/cli.py:978-1028,1078-1088`
- 再現手順または反例: 仮に手順 1〜8 が全緑でも、plan は `calibrate_fn`、quality 判定、candidate 作成、content-addressed publish を一度も実行しない。また、実測表を durable insight に書く具体的な producer/path も plan にない。共通 gate が赤なら `∅` は確定できるが、正の要素は確定できない。

### 3. Cicada alias は brief の「受け手は一般」と矛盾する実在欠陥

- 重大度: **must-fix**
- 成果物影響 1 行: alias 正規化がなければ Cicada は receipt 受理で落ちるか、未使用 cache 変数を実際に効いた軸として記録する。
- 根拠の file:line: `external/ccbench/cc/cicada/CMakeLists.txt:1-9`、`orchestrator/campaign/genome.py:178-186`、`orchestrator/calibrator/cli.py:429-464`、`brief.md:13-16`
- 再現手順または反例: `-DCCBENCH_INLINE_VERSION_OPT_CICADA=0` を含む正直な build argv は、現行 parser では flag 名が `_CICADA` のままなので `INLINE_VERSION_OPT` 欠落として `cli.py:455-460` で拒否される。逆に汎用名を渡すと M2 の未使用警告経路になる。

### 4. Acquisition receipt の `calibration` 必須化は scope 外

- 重大度: **must-fix**
- 成果物影響 1 行: 現在受理される genome 付き calibration/v2 の受理集合を縮める一方、floor が protocol 別較正を選ぶ経路は増えず、本題の生産集合を変えない。
- 根拠の file:line: `stage2-plan.md:131-140,244-255`、`orchestrator/calibrator/schema_v2.py:445-469,562-569,613-629,770-789`、`orchestrator/calibrator/cli.py:373-464,740-759`、`orchestrator/campaign/env_contract.py:253-281`、`orchestrator/campaign/s8b_floor_campaign.py:7340-7350`
- 再現手順または反例: `test_schema_v2.py:172-178` の genome 付き文書は現在 `acquisition_receipt.calibration` なしで受理される。protocol は build target、軸は configure argv、workload は最終 artifact の top-level から既に記録できる。新 field を必須化しても floor は env contract の単一 `calibration_ref` を読むだけである。

### 5. 手作業 probe は登録済み launcher の実効性を証明しない

- 重大度: **must-fix**
- 成果物影響 1 行: 手作業で再構成した argv が成功しても、実際の env default・receipt・quoting・実行順を持つ launcher が成功した証拠にならない。
- 根拠の file:line: `stage2-plan.md:319-367`、`tools/pegasus/certify_calibration.sh:15-45,534-549`、`tools/pegasus/admission_registry.json:34-38`、`hooks/guard_bash.py:1205-1215,1248-1249`、`tools/README.md:22-23`
- 再現手順または反例: plan は login node で直接 `cmake --build` を実行するとしているが、重量 command gate はその形を拒否する。`/scr` の場所や detached worktree はこの判定を変えない。また、既存 script の入力面変更は既存規律上再分類対象であり、「既登録だから確認不要」ではない。

### 6. brief の伝播アンカーが不足している

- 重大度: **must-fix**
- 成果物影響 1 行: brief の表だけを実装すると、明示 protocol/workload が submit receipt に残らず、job 側の再照合または provenance が壊れる。
- 根拠の file:line: `brief.md:71-84`、`tools/pegasus/submit_certify.sh:133-171,178-181,218-247`、`tools/pegasus/certify_calibration.sh:188-219`、`tools/pegasus/README.md:123-160`
- 再現手順または反例: brief の `submit_certify.sh:8-40` と `export_spec` だけを変更すると、`pre-submit.json` は依然 `calibration_rratio` だけ、`submit-receipt.json` も rratio だけで、job は protocol/skew/rmw を receipt と照合できない。stage2 の詳細手順はこの一部を拾っているが、brief の実アンカー表にはない。

## 検査した 6 項目への回答

### 1. Scope の膨張

- `orchestrator/calibrator/cli.py` の Cicada alias 正規化: **本題に必要**。これがないと正しい cache 名を使った Cicada receipt が `cli.py:455-460` で missing axis になる。

- `tools/pegasus/make_acquisition_receipt.py` の `calibration` 対応: **scope 外**。新しい台帳 field の追加であり、build argv と最終 workload が既に実値を持つ。

- `orchestrator/calibrator/schema_v2.py` の `calibration` 必須化: **scope 外**。明示除外された gate・検査・台帳追加そのもので、受理集合を変更する。

- `test_calibrator_certify.py` の Cicada alias 正例・重複負例: **必要**。変更する実在 consumer の直接テストであり、既存の receipt genome 検査は `test_calibrator_certify.py:431-452` にある。

- `test_schema_v2.py` の新 acquisition binding 検査: **scope 外**。不要な schema 変更にだけ従属する。

- `test_pegasus_tools.py:1068-1086` の writer round-trip を新 field 必須へ変える部分: **scope 外**。launcher の protocol/軸伝播テスト自体は必要だが、acquisition field-drop gate は別物。

- shell 表と `SPACES` の完全一致を将来 drift 用に検査する案 (`stage2-plan.md:169-178`): 現在の4 protocolに対する具体的な機能テストを超える一般 drift gate は **scope 外**。

### 2. 依頼に答えているか

| 証拠 | 答えている範囲 | 答えていない範囲 |
|---|---|---|
| plan の手順 | configure、gate、build、binary、receipt、canonical genome の到達性 | 実 launcher行、quality 判定、registered publish、実 launcher 全体 |
| P1-d | 2時間計測を省くことで、共通 gate 赤なら空集合を確定できる | green protocol の「record 生産可能」証明 |
| M1 | 同一 default configure から4 targetをbuild可能 | protocol別軸、launcher、gate、登録 |
| M2 | 3 protocolの全軸とCicada 4軸の configure-time define 到達 | build、Cicada alias、launcher、登録 |

M4 が正しい場合の正直な答えは、母集合を明示して次のとおりである。

> 候補集合 `{silo,mocc,tictoc,cicada}` に対し、現行 pin・現行必須 condition gate を通る認定較正 producer の生産可能集合は `∅`。これは「4 protocol の binary が build 不能」という意味ではない。

完了判定は次のように書かなければならない。

> T-2224 は再裁定待ちで未完了。現行共通 gate の赤により正の end-to-end 生産証拠は 0 件で、A-4 の非 silo embargo は継続する。

### 3. Wave を止めるべきか

**S3**。`docs/dev-wave/core.md:36-38,50-53,99-101` は、承認済み前提を覆す未見事実を不採用にせず、ユーザー再裁定へ戻すよう要求している。

S1 は再裁定後にユーザーが選び得るが、現時点で親が自律選択して閉じるのは停止規律違反。S2 は CCBench 改変または gate 側変更を同 wave に取り込み、明示 scope を越える。

### 4. Byte 互換の主張

コマンド argv に限定すれば、設計上は成立可能である。

- qsub argv: 新3引数を省略したとき `export_spec` を現行 `nonce,rratio` のままにするため、同じ動的 nonce/path を固定して比較すれば一致する。明示 `--protocol silo` は省略と同値でも env が追加されるため一致しないが、主張の対象外である。
- configure/build/calibrate argv: `stage2-plan.md:231-235,257-261` を逐語的に守り、Silo define 順序と workload 文字列を維持すれば一致可能。
- receipt bytes: **一致しない**。plan は省略時も protocol/skew/rmw を常時記録するため、`pre-submit.json` と `submit-receipt.json` は意図的に変わる。したがって「run 全体が1 byteも変わらない」とは書けない。
- 検査強度: plan どおり receipt が常に実効値を持ち、job が4値を照合するなら、env transport は非対称でも検査強度は非対称にならない。job default が submit default とずれれば receipt 照合で赤になる。

### 5. F660 と所有

「新しい `tools/pegasus/` 実行 script は不要」「`certify_calibration.sh` は `dispatch-required` 登録済み」という限定命題は正しい。根拠は `tools/pegasus/admission_registry.json:34-38`。

ただし既存 script の入力面変更は `tools/README.md:22-23` の再分類対象なので、既登録というだけで確認を省けない。`/scr` の mktemp と detached worktree は、編集・patch 適用をしない限り現行 launcher と同型で、防壁迂回ではない。一方、plan の login 直 `cmake --build` は path 非依存の重量拒否対象であり、登録済み launcher の代替証拠にもならない。temp source に patch を当てれば、CCBench 改変禁止と測定対象 pin の双方が変わる。

### 6. 親 brief の抜け

plan が明示した `cli.py`、schema/writer、追加テスト、README 以外に、brief のアンカー表には次が抜けている。

- `tools/pegasus/submit_certify.sh:133-171`: pre-submit request への実効4値の記録。
- `tools/pegasus/submit_certify.sh:218-247`: submit receipt への4値伝播。
- `tools/pegasus/certify_calibration.sh:188-219`: job env と submit receipt の4値再照合。
- `tools/pegasus/certify_calibration.sh:394`: `condition-gate.stderr`。現 wave の予想結果が赤なので、失敗根拠を構成する実生成物である。
- 実際に較正を走らせる場合だけ、`certify_calibration.sh:811-813` の `calibrate.stdout/stderr`、`cli.py:1006-1028` の candidate/calibration/publish、`collect_receipt.py:153-180,191-205` の final receipt にも protocol/workload由来の bytes が波及する。P1-d の範囲では生成しないため、現 wave の write-path には数えない。

Consumer 側では、`tools/pegasus/README.md:123-160` は直接変更が必要。`docs/pegasus-runbook.md:784-820` は既存経路と歴史的事実の記述で、今回必須の新 CLI 契約は持たない。`floor_campaign.sh:1172-1228` と `s8b_floor_campaign.py:7340-7350` は env contract の calibration を読むだけで protocol 別選択をしないが、これは明示 scope 外の T-2225 側である。したがって T-2224 単独で「非 silo floor が公式成果物へ入るようになった」とは主張できない。

## 親の実測への反論

- **M1**: 「default configure で4 targetがbuildできた」は正しい。ただし生産可能集合へ一般化できない。launcher、condition gate、receipt、calibrator、publishを一つも通っていない。
- **M2**: 「軸をすべて既定と違う値」は誤り。Cicada の `INLINE_VERSION_OPT=0` は `Options.cmake:53` の既定0と同じで、未使用の汎用 cache 名が実体へ届いた反証になっていない。結論は記載どおり4/5まで。
- **M3**: 射程内では反論なし。`INLINE_VERSION_OPT_CICADA=1` という一点のbuild不能を示すだけで、default Cicadaを集合から除外しない。
- **M4**: Silo の実測自体への反論なし。ただし「全 protocol 赤」は4 protocol実測ではなく、同じ source・同じ固定 `BACKOFF_FIXED` gate を全分岐が通ることからの静的推論である。その限定を明記すれば、空集合判断の必要条件として十分。
- **M5**: 宣言された検索面に限れば反論なし。
- **M6**: 現在の `registered/` の母集合については正しい。過去やrepo外を含む「非 silo record が一度も存在しなかった」までは示さない。
- **M7**: 2 fileについての競合否定に限れば正しい。stage2 が追加した `cli.py`、schema/writer、README、追加テストの所有は走査対象として報告されておらず、拡張後の変更面全体へ一般化できない。現に競合がある証拠はないため、この点自体は nit 相当である。