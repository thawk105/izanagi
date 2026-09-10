判定は **NO-GO** です。案 1 は D63 の排他保証を、fail-open な receipt memo と実行順へ置き換えています。

### 1. D63 の競合閉包を保存していない

- **重大度**: Critical
- **主張**: ungrouped payer は実 working tree・untracked・ccbench submodule を読むため、D63 の literal な競合閉包へ入るべきです。さらに「binding barrier」は cache path・lock open・cache store の失敗時に排他として機能せず、後続 writer と別 worker の実 repo 解決が並走できます。案 1 は実装してはいけません。
- **根拠**: D63 は可変状態へ触る node 全体を単一 group に置くと決定し、read/patch 分割を明示却下しています (`docs/decisions.md:2406-2423`)。payer は `_run()` の既定で memo resolver を使います (`orchestrator/tests/test_s8b_oracle_driver.py:1520-1536,2471-2488`)。その miss は `verify_receipt()` から live repository scan と current ccbench HEAD 検査へ到達し (`orchestrator/campaign/t080_freeze_migration.py:1924-1985,2031-2034`)、scan は untracked と submodule worktree を列挙・読取します (`orchestrator/campaign/s8b_holdout_freeze.py:197-212,297-327`)。一方 memo は cache path 不明・lock open 失敗で `_resolve_now()` へ倒れ (`orchestrator/tests/real_repo_receipt_memo.py:144-168`)、store 失敗も握り潰します (`同:116-126`)。それでもプランは payer を ungrouped のまま CLI と並走させます (`s2-plan.md:52-60,97-99`)。
- **成果物影響**: writer の patch 窓を receipt/holdout reader が観測して偽赤・偽緑になり、producer / pilot / 本走の受入参照が certified 選択・材料レポート・試行台帳の proof chain として使えなくなります。

現行で payer と CLI が実際に重なったかは、JUnit に開始時刻がないため確定不能です。現行 baseline では binding が CLI より先に同一 group で実行されており (`junit-baseline.xml:1`)、671 秒の payer と 680 秒の binding から「CLI 開始前に cache が公開された」は推測できます。案 1 は CLI を barrier より前へ移すため、payer–CLI の意図的な並走は新規です。なお ungrouped payer 自体は現行でも D63 リスト外であり、早い位置の writer と重なる既存穴があります。

### 2. 順序 gate が実際の安全条件を固定していない

- **重大度**: Major
- **主張**: 現行 pytest-xdist 3.8.0 では group 内 FIFO は実装上確認できます。しかし collection 順は cross-worker の開始順ではなく、提案された marker・順序 control は memo の fail-open 分岐を一切発火させません。全 meta-test が緑でも所見 1 の競合は残ります。
- **根拠**: 3.8.0 は collection 順で work-unit dict を作り、同順で index を送信し FIFO queue で実行します (`.../xdist/scheduler/loadscope.py:263-282,367-382`; `.../xdist/remote.py:74-98,165-168,200-228`)。一方 scope 自体は既定で testcase 数順へ並べ替えられるため (`.../xdist/plugin.py:130-151`; `loadscope.py:374-398`)、collection の payer 先頭化だけでは開始先頭を保証しません。runner は 3.8.0 を pin せず任意の `>=2.5` を許し、未導入時は無指定で最新版を入れます (`tools/run_tests.py:236-264`)。プランの synthetic 負例は marker 形だけで、cache path/lock/store failure を含みません (`s2-plan.md:142-159`)。また優先順の期待値を SUT の同じ定数から導出しないという独立 oracle の指定もありません。digest 実装には parameter ID 内の `@` を suffix と誤認する既知の罠もあります (`analyze-out.md:147-148`)。
- **成果物影響**: gate が緑のまま実行順または barrier が壊れ、受理された全走の参照と約 876 秒という材料レポート値の両方が虚偽になり得ます。

必要なのは、独立 literal golden、実 acceptance shape での開始・終了証拠、優先順反転での恒久的な負対照です。ただしそれでも memo fail-open を D63 排他へ昇格させることはできません。

### 3. T-553 所有中の s8c marker 変更を直列化していない

- **重大度**: Major
- **主張**: T-553 の land・所有解放前に対象ファイルを変更してはいけません。merged tip 上で T-553 の関連検査・48-worker 全走・T-692 計測を再実行する順序がプランにありません。
- **根拠**: s8c の session fixture は worker ごとの session scope であり (`orchestrator/tests/test_s8c_preregistration_invariant.py:118-121`)、現在は同じ専用 marker を3 nodeへ付けています (`同:29,124-127,190-207`)。canonical list への追加漏れや decorator の残存が1件でもあると、conftest は既存 marker を見て canonical marker を付けません (`orchestrator/tests/conftest.py:243-250`)。並行 T-553 の裁定は「invariant の xdist group を変えない」と固定し、R3 group 統合は別起票へ送っています (`dev-wave-t553-git-budget/.../s4-ruling.md:60-69,86`)。その T-553 の測定・裁定は旧 group での48-worker負荷を根拠にしています (`.../MEASUREMENT.md:11-18,44-54`)。
- **成果物影響**: T-553 の git 予算受入と T-692 の `S=58.35`・wall projection が同じ merged checkout を指さず、`git-timeout` による generation/activation report 欠落を certified 選択・台帳が見逃します。

3 nodeが完全に canonical groupへ移れば candidate commit 一回生成自体は維持できます。危険なのは部分統合と、旧 checkout の検査値を merged tipへ流用することです。

### 4. T-438 helper 置換は「受理集合不変」ではない

- **重大度**: Major
- **主張**: helper 置換で検出力は落ちません。逆に、既存 untracked directory 内への2個目の file 追加を新たに捕捉するため、brief の「pass/fail を変えない」という不変条件が破れます。正しさ gate の強化として明示裁定・記録すべきです。
- **根拠**: 現行 T-438 は既定の untracked directory 圧縮を使う status 比較です (`orchestrator/tests/test_ruleops.py:2036-2040,2064-2069`)。共有 helper は `--untracked-files=all` の raw bytes を比較します (`orchestrator/tests/repo_tree_util.py:16-23,56-87`)。その差が実際に効く positive controlとして「既存 scratch dir 内へ second file」を検出します (`orchestrator/tests/test_s8b_protocol_builder.py:466-493`)。これは brief の `s1-brief.md:51-52` と、プラン自身の「snapshot 強化」 (`s2-plan.md:46,99`) の矛盾です。
- **成果物影響**: 全走の受理集合が狭まるのに「不変」と記録すると、材料レポートと試行台帳が gate 強化前後の受入結果を同一契約として誤参照します。

### 5. `-n 0` の 428 秒は bnode055 の観測ではない

- **重大度**: Major
- **主張**: 親の M7 は観測ホストを誤記しています。428 秒は Pegasus ログインノード上の local bounded runであり、bnode055 の48-worker baselineとの差を「競合による428→670秒」と分解できません。
- **根拠**: baseline は bnode055 と記録されています (`s1-measurement.md:8-10`)。対して `measure2.log:2` は明示的に「ログインノード」での実行と記録し、JUnit も `hostname="pegasus02"` です (`junit-serial3.xml:1`)。実行順は payer 427.58秒→cache hit 3.27秒→binding 2.08秒でした (`measure2.log:15-20`)。それにもかかわらず M7 は428秒を bnode055 の一回観測としています (`s1-measurement.md:78-80`)。
- **成果物影響**: 428秒、競合倍率、cache-hit本体値を使った材料レポートの機序説明と約875.67秒の予測参照が、異なる機体を混ぜた値になります。

この走行が証明するのは「指定順では最初の1本だけが解決を払い、後続はcache hitになる」までです。48-worker条件で誰がlock ownerだったか、解決自体が何秒だったかは証明していません。

### 6. 約876秒の選択と P2 は未測定の外挿に依存する

- **重大度**: Major
- **主張**: `max(C,M)` は、二つの全履歴解決を同時に走らせても互いを遅くしないという未測定仮定です。また過去の32/48比較だけで16/24 workerを除外しており、より安全な並列度調整を捨てています。
- **根拠**: projection は単一走の `C=653.50` と testcase durationにすぎない `M=671.55` を同時開始したものとして `max()` に畳み、旧 scheduler余剰19.17秒もそのまま足します (`s2-plan.md:64-93`)。lock owner・開始時刻は未記録です (`同:28-30`)。二解決同時実行による filesystem/git 競合増加は**推測**ですが、同時実測はありません。P2 の根拠は別時点の32/48二点だけで、16以下は未取得です (`s1-brief.md:19-21,66-67`)。現行 ungrouped 総和は15001.78秒なので (`analyze-out.md:23-35`)、16 worker時の均等下界は約937.6秒です。receipt競合が減れば選択肢になり得ますが、未測定です。さらに「個別テスト全般は別所有」という brief の境界は、実際には `_any_history_touches_path` と T-553 R1/R2しか所有根拠を示していません (`s1-brief.md:34-36`)。
- **成果物影響**: 875.67秒を根拠に案1を certified な実装候補として選ぶと、実際の全走が予測を外してwall超過し、certified 選択・材料レポート・試行台帳の更新経路が停止します。

## 総括

- **NO-GO**
- **Critical 1 / Major 5 / Minor 0**
- 最も危険な1件: fail-open な test memo を D63 の writer barrier として転用し、ungrouped live-repo readerを競合閉包外へ残すこと。
- 現プランから無条件に採ってよい部分: **なし**。T-438 の helper 置換単体は検出力を落としませんが、受理集合強化として brief を訂正・独立裁定してから採る必要があります。