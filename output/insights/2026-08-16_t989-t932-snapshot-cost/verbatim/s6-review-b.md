実走は行わず、wave の 2 commit のみを静的検査した。

所見に至らなかった照合:

- 所有外 oracle は静的には赤にならない。`REAL_REPO_SERIAL_NODES` と独立 golden は 66/66 件一致し、fixture consumer 閉包の対象も不変。hold は 57 件、key digest・row digestとも再計算値に一致。held module guard は 13/13 module、inventory の reason・collateral・human 投影も 57 件一致した。根拠: `orchestrator/tests/conftest.py:170-261`、`orchestrator/tests/test_real_repo_serialization.py:38-103,724-737`、`orchestrator/tests/test_growth_test_holds_contract.py:39-41,229-258,590-609`、`orchestrator/tests/test_hold_inventory.py:315-332`
- S2 は裁定どおり 27 件追加。過剰 0 件（nodeid なし）、欠落 0 件（nodeid なし）。snapshot 3 node はいずれも未登録。根拠: `orchestrator/tests/test_growth_test_holds_contract.py:250-258`
- 既存 14 node の `output_artifacts` 軸は成立する。fixture は derive より前に `_prepare_snapshot_case` を呼び、POS が `derive_independent_golden` から `_find_rollout` の corpus `rglob` と `_session_meta_rows` の走査へ到達する。根拠: `orchestrator/tests/test_codex_reasoning_ab.py:350-384`、`tools/codex_reasoning_ab.py:232-252,321-369,648-664,1450-1458`
- scope 外 3 群を本 wave が壊した証拠はない。列挙された対象 file は差分に含まれず、submodule fail-open と remote・dangling symlink の検査経路も変更されていない。

- **所見 1**: `ffe74a1f` は root seal の単発値まで「3 走中央値」と誤表示している
- 根拠: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t989-t932-snapshot-cost/measurements.md:61-73`、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t989-t932-snapshot-cost/s4-adjudication.md:191-195`。commit 本文は全 bullet を「3 走中央値」と導入するが、33.64 秒・0.38 秒は「委譲 wrapper」の代表値であり、3 走表があるのは fixture・build・derive だけである。禁止された「完全切離し」「受入 wall 短縮」「derive は定数」「submodule 支配」は使っていない。
- 反例の構成: 同じ root/submodule wrapper 計測を静かな窓で3回実施する。中央値が33.64秒・0.38秒と一致しなくても、現 commit 文面ではその値を中央値として再現したことになる。
- 深刻度: MAJOR
- 成果物影響 (DW-G05): certified 選択値は不変だが、材料レポートと試行台帳の root seal 前後値・倍率・測定回数の provenance が過大になる。

- **所見 2**: S1 の fixture 短縮を受入 wall 短縮として帰属できず、現時点では wall 実測自体がない
- 根拠: `tools/run_tests.py:62,215-229,394-399`、`orchestrator/tests/conftest.py:170-268,398-402,449-465`、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t989-t932-snapshot-cost/measurements.md:194-196`
- 反例の構成: 32 worker・`--dist loadgroup` で real-repo 66 node を1 workerへ集約し、別 workerへ60秒の非 group nodeを置く。real-repo workerを43秒から21秒へ短縮しても suite wallは60秒のままになる。`REAL_REPO_EXECUTION_PRIORITY` は group 内の2 nodeを並べ替えるだけで、groupを最長 workerにもしなければ開始順も保証しない。さらに前後を両 commitで測れば、S2による27 skipも混入してS1単独効果を識別できない。
- 深刻度: MAJOR
- 成果物影響 (DW-G05): certified 選択値は不変だが、受入 wall、改善率、lease窓をS1効果として記録するとレポートと台帳の帰属が誤る。

- **所見 3**: 「残る約8秒は copytree」という律速帰属は未計測で、`BASE_COMMIT` 固定だけを固定費条件とする記録も広すぎる
- 根拠: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t989-t932-snapshot-cost/measurements.md:119-128`、`tools/codex_reasoning_ab.py:1491-1508,1511-1552,1330-1425,715-762,791-804`
- 反例の構成: `shutil.copytree`、前後の relocation preflight、`_finish_snapshot_case`、`verify_snapshot`を別々に計時する。現8.02秒はこれらの合計なので、copytreeが例えば3秒でも現記録は8秒と誤帰属する。また現在の外部 submodule pinへ新しい nested submoduleを追加し、BASE側を固定したまま再構築すると、初期化はlive sourceのindex・`.gitmodules`を再帰参照するため、固定BASEだけでは同じbaseの生成さえ保証されない。単純な外部pin前進による余分なobjectはsealのref削除・repack・pruneで通常は落ちるため、「object storeが必ず増える」とまでは静的に立証できない。
- 深刻度: MAJOR
- 成果物影響 (DW-G05): certified 選択値は不変だが、残余費用のcomponent名と固定費判定がレポート・台帳で誤り、将来のgrowth floorを受理集合外として扱う根拠が過大になる。

## 総括

NO-GO  
BLOCKER: 0件、MAJOR: 3件