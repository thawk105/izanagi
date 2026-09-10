必須入力はすべて読めた。静的検査のみで、pytest は実行していない。

結論は **land 不可**。live `run_block` の current admission 自体は維持されているが、C4 report に実受理へつながる fail-open と、manifest 単位の一回解決違反が残る。

確認できた防壁：

- driver の production 呼出しは引き続き `launch_validate` だけである（[s8b_oracle_driver.py:511](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_driver.py:511)、[同:1066](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_driver.py:1066)）。
- `launch_validate` は current resolver、historical resolver は `reverify_published_freeze` に固定されている（[s8b_ratified_freeze.py:3234](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:3234)、[同:3244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:3244)）。
- C2/C3/result/occurrence はすべて必須 `contract` 引数で同一 object を受け、内部 current fallback はない。
- `ReverifiedFreeze` の docstring は、偽造耐性を主張しない限界を正しく記載している（[s8b_ratified_freeze.py:781](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:781)）。
- commit は指定3コード＋2テストだけを変更しており、floor campaign、loop、pipeline、trigger gating、fuse、registry には触れていない。

## 所見 R1-1 — declared `run_contract` の不正形が legacy 扱いで receipt 検査を迂回する

**根拠 (path:line)**

`_receipt_expectations` は `run_contract` が Mapping でも、`env_tag` または `contract_sha256` が欠落・空・非文字列なら resolver を呼ばず `None` を返す（[s8b_oracle_report.py:1197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_report.py:1197)、[同:1202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_report.py:1202)、[同:1224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_report.py:1224)）。caller は `None` の場合に execution receipt 検査を課さない（[同:1387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_report.py:1387)）。

Legacy manifest の事前検査は `run_contract.reps` しか見ず、env/hash の必須性を検査しない（[同:394](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_report.py:394)）。schema-less document は `run_contract` が存在しても `LegacyManifest` になる（[s8b_oracle_artifacts.py:131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_artifacts.py:131)）。

追加テストの “malformed” は非空文字列 `"not-a-sha256"` だけで、resolver に到達する場合しか覆わない（[test_s8b_oracle_report.py:1980](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/tests/test_s8b_oracle_report.py:1980)）。空文字列、`None`、field 欠落は未検査である。

**成立条件**

schema-less legacy manifest が正しい `reps` と不正な `env_tag`／`contract_sha256` を持ち、WAL・manifest hash を内部整合させている場合、contract、calibration、execution receipt の束縛なしに row が `completed` へ到達できる。

**成果物 (certified 選択・レポート・台帳) への影響 1 行**

contract/receipt 未検証の completed row が OfficialObservations と judge の eligible 集合へ入り、certified 選択を変え得る。

**推奨 (must-fix)**

`run_contract` が完全に欠落する真の legacy だけを `None` とし、field が宣言されているのに env/hash が欠落・空・非文字列なら manifest-global `ReportError` にする。public report と judge まで、missing／empty／non-string の負例を追加する。既存 legacy 方針として残すなら、段4の fail-closed 主張を明示的に再裁定する必要がある。

## 所見 R1-2 — C4 は manifest 1件を campaign 数だけ再解決する

**根拠 (path:line)**

resolver と calibration load は `_assess_campaign` 内で実行される（[s8b_oracle_report.py:1379](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_report.py:1379)、[同:1205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_report.py:1205)、[同:1218](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_report.py:1218)）。`build_observations` は manifest の各 campaign について `_assess_campaign` を繰り返す（[同:1652](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_report.py:1652)）。

2 campaign manifest は既存の受理形である（[test_s8b_oracle_report.py:3440](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/tests/test_s8b_oracle_report.py:3440)）。新しい call-count test は1 campaign fixtureしか使わない（[同:1919](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/tests/test_s8b_oracle_report.py:1919)、[同:1950](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/tests/test_s8b_oracle_report.py:1950)）。

さらに campaign terminal 異常時は resolver より前に return するため、その campaign では contract 拒否分岐自体が発火しない（[s8b_oracle_report.py:1334](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_report.py:1334)）。

**成立条件**

manifest が2 campaign 以上を所有する場合は同じ記録 hash を複数回解決する。terminal 異常 campaign では解決を完全に飛ばす。

**成果物 (certified 選択・レポート・台帳) への影響 1 行**

同一 manifest の各 row が単一の contract/calibration snapshot に束縛されず、report と台帳の一回解決 proof chain が成立しない。

**推奨 (must-fix)**

`build_observations` 冒頭で expectations を厳密1回だけ解決し、その同一 object または manifest-global error を全 `_assess_campaign` へ渡す。2 campaign の resolver/load call-count=1 と、terminal early-return を含む全 row taint を固定する。

## 所見 R1-3 — historical 型を standalone driver gate へ直接渡せる

**根拠 (path:line)**

`_gate_check_core` の `launch_validated` は注釈上 `LaunchValidatedFreeze` だが、runtime exact-type 検査なしに `.ratified` を消費する（[s8b_oracle_driver.py:311](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_driver.py:311)、[同:349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_driver.py:349)）。`ReverifiedFreeze` は同じ field shape を持つため、private core への直接受渡し、または `gate_check` が呼ぶ module-level `launch_validate` の patch で historical token が到達する（[同:511](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_driver.py:511)、[同:524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_driver.py:524)）。

一方、`run_block` 本線は `_gate_check_validated` の exact type 検査で閉じている（[同:538](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_driver.py:538)）。

**成立条件**

in-process caller が `_gate_check_core(..., launch_validated=reverified)` を直接呼ぶか、standalone `gate_check` 中の module attribute を historical 戻り値へ patch した場合。

**成果物 (certified 選択・レポート・台帳) への影響 1 行**

standalone gate は誤って `allowed` を返し得るが、現行 run_block の exact-type gate が WAL・予算・certified 成果物への流入を止める。

**推奨 (nit)**

`_gate_check_core` の入口でも `type(...) is LaunchValidatedFreeze` を要求し、`ReverifiedFreeze` を渡す負例を追加する。これは未封印型の偽造耐性ではなく、own-consumer の型分離を閉じる補強である。

## 所見 R1-4 — 非一意・dishonest 分岐は production artifact からは到達しない

**根拠 (path:line)**

registry は index 構築前に全世代・全envで hash 一意性を強制する（[env_contract.py:278](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/env_contract.py:278)、[同:302](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/env_contract.py:302)、[同:347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/env_contract.py:347)）。したがって resolver の `len(candidates) != 1` は、valid production registry では恒偽である（[同:366](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/env_contract.py:366)）。

C4 の ambiguous test は private `_CONTRACT_SHA256_INDEX` を不正な値へ patch して到達させている（[test_s8b_oracle_report.py:1986](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/tests/test_s8b_oracle_report.py:1986)）。dishonest-resolver も production resolver ではなく test callable の注入である（[同:2001](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/tests/test_s8b_oracle_report.py:2001)）。

未知 hash、cross-env、calibration 欠落、calibration hash 不一致は production artifact/filesystem 状態から到達可能である。非一意と dishonest は trusted-code 故障に対する defense-in-depth である。

**成立条件**

非一意は registry 検証または private index を迂回した場合、dishonest は resolver 実装を差し替えた場合に限る。

**成果物 (certified 選択・レポート・台帳) への影響 1 行**

product の受理集合には直接影響しないが、台帳が両者を artifact-reachable な独立 kill と数えると検証強度を過大表示する。

**推奨 (nit)**

テストは残しつつ「patch-only structural defense」「production artifact 負例ではない」と明記し、mutation の受理集合 kill 数には含めない。

## 所見 R1-5 — 周辺 docstring が旧 current-bound 経路を主張したまま

**根拠 (path:line)**

`ReverifiedFreeze` 自身の限界説明は正しい。一方、共有 core は historical 戻り値も作るのに「実走型へ昇格」と記述する（[s8b_ratified_freeze.py:2840](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:2840)）。また manifest verifier は公式 report CLI が `load_ratified_freeze → launch_validate` を使うと記述しているが、現物は `reverify_published_freeze` である（[s8b_oracle_manifest.py:818](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_manifest.py:818)、[s8b_oracle_report.py:1731](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_report.py:1731)）。

**成立条件**

docstring を report の current-bound admission 保証または台帳記述の根拠として使う場合。

**成果物 (certified 選択・レポート・台帳) への影響 1 行**

レポート再検証を live/current admission 済みと誤記し、台帳上の保証が実装より強くなる。

**推奨 (nit)**

共有 core を中立な「full validation core」に直し、公式 CLI の説明を `reverify_published_freeze` と historical contract 境界へ更新する。

## 総括

最も重い所見は次の3件。

1. **R1-1:** 不正な declared `run_contract` が `None` fallback で receipt 検査を迂回し、completed／eligible へ到達できる。
2. **R1-2:** C4 が manifest 単位でなく campaign 単位に再解決し、一回解決と単一 snapshot を満たさない。
3. **R1-3:** standalone driver gate の内部 consumer に historical 型を渡せる。ただし run_block 本線は exact-type gate で閉じている。

`launch_validate` の production受理集合、run-block の current admission、指定された floor/loop/pipeline/trigger/fuse/registry の入口には、静的に historical leakage を認めなかった。上流の [s8b_ratified_freeze.py:976](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:976) に current `lookup` は残るが、env_tag の存在確認だけで記録 hash の再解決・calibration fallbackではなく、段4が不変とした層である。

ただし R1-1 は実受理集合の fail-open、R1-2 は明示された一回性違反なので、**このままの land は不可**。両 must-fix を塞ぎ、計算ノードで対象 pytest／変異を実走してから land 判定をやり直すべきである。