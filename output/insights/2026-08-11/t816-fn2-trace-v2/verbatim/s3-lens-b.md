指定された brief、段2 plan、裁定パッケージと関連実装を読了しました。read-only のため変更はありません。

## 所見

### 1. bundle の再取得・復元手順が未定義

severity: must-fix

根拠: `s2-plan.md:138-139` は bundle の保存・検証と旧 HEAD への復元を要求するが、fresh clone での bundle import、new SHA の checkout、再検査までの手順がない。`external/ccbench/.git:1` は worktree 固有の gitdir であり、`.claude/commands/cleanup-branches.md:29-38` の cleanup 後には利用できない。保存先自体は repo 外で正しい（`docs/pegasus-runbook.md:736-754`）。

`git bundle verify` を現在の repository で通すだけでは、worktree 撤去後に実際に new SHA を復元できることを証明しない。指定パス `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/izanagi-trace-t816-<newsha>.bundle` に対する作成、fresh clone への取り込み、new SHA の再検査を明記すべき。

放置時の値（1行）: worktree 撤去後に new SHA を再取得できず、レポート中の候補 commit は orphan になり、certified 選択・台帳は d706650 のまま進まない。

### 2. submodule の dirty state が narrow gate では見えず、land で拒否される

severity: must-fix

根拠: `s2-plan.md:140` の見立てどおり `orchestrator/tests/test_s8b_approved.py:34-64` は committed gitlink だけを読むため、新 HEAD checkout 中でも緑になる。一方、`tools/dev_wave_land.py:832-850`、`875-889`、`1295-1320` は submodule dirt を拒否する。通常の `checkout/restore` も `hooks/guard_bash.py:141-163,1459-1480,1512-1520` の防護対象である。

`guard_write.py:36-38,143-156` から見る限り、A の `cc/silo/transaction.cc` 直接編集は許可面内であり、scratch copy、hook 改変、sandbox 昇格の迂回は含まれていない。問題は迂回ではなく、復元操作を hook-safe な実行手順として定義していない点である。

放置時の値（1行）: `test_s8b_approved=green` でも `dev_wave_land=reject` となり、受入済み certified 行・レポートの完了状態・台帳の land 状態は更新されない。

### 3. 必須 compiler 条件が現環境で成立しない

severity: blocker

根拠: `s2-plan.md:118` は admission build と同じ `g++-13` を要求し、`s2-plan.md:137` は real-build control の SKIP を成功と数えない。しかし実テストは `orchestrator/tests/test_s8b_oracle_driver.py:4154-4157` で `g++-13` 不在時に skip し、runbook も `docs/pegasus-runbook.md:619-625` で login/compute の双方に `g++-13` がないと明記している。brief は `g++ 11.4.0` を実走環境としている（`brief.md:74-77`）。

`g++-13` を要求し続けるなら現 wave の C 実走は不可能。`/usr/bin/g++` 11.4.0 を使うなら、checker の compiler identity と admission build 同一性の主張を変更し、同一 compiler を old/new 両方に明示的に渡す必要がある。

放置時の値（1行）: C 実走証拠が SKIP/欠落となり、new SHA の候補レポートは certified 選択へ昇格できず、台帳の承認可能数は 0 のままとなる。

### 4. mutation harness の成立条件が plan に登録されていない

severity: must-fix

根拠: `s2-plan.md:120-142` には pytest と受入の記述はあるが、mutation spec、対象置換、期待 node、単一理由性、mask 検査がない。`tools/mutation_harness.py:193-319` は `KILLED` に非空の `expected_nodes` を要求し、`945-986` は node の実在を collection で検証し、`1177-1193` は失敗 node 集合の完全一致でのみ KILLED とする。`docs/dev-wave/mutation.md:5-20` は前後層の mask がないことを事前確認する契約である。

対象 checker 自体は `tools/` の tracked file になるため harness の対象範囲には入る。ただし、例えば raw diff rejection を変異させても、include/mode/commit 検査が先に落とせば、別層の赤を checker の kill と誤帰属できる。worklog 428 でも同型の診断層変異・後段 mask が発生している（`docs/worklog.md:659-674`）。

再照準先は、受理判断を直接変える diff allowlist、TRACE=0 byte mismatch、compiler failure の各分岐。それぞれ単一の不正要因だけを持つ fixture、実在する nodeid、期待失敗集合を事前登録し、mask が疑われるものは二層同時変異として別扱いにすべき。

放置時の値（1行）: 報告される `KILLED` 件数が過大または未証明となり、fail-closed 保証の値が偽になって、将来の certified 選択に不正な new pin が混入し得る。

### 5. 合成 fixture は実 submodule の運用形を再現していない

severity: must-fix

根拠: `s2-plan.md:124-130` の fixture は一時的な通常 git repo であり、実物は `.git` file から worktree 固有 gitdir を参照する（`external/ccbench/.git:1`）。実物には `.gitmodules` の submodule 配置・detached HEAD・親 gitlink があり（`.gitmodules:1-4`）、cleanup も通常 repo と異なる（`.claude/commands/cleanup-branches.md:31-38`）。

fixture は parser、mode、unknown macro の単体検査には有効だが、bundle、linked gitdir、実 CMake/Options、実 compiler、親 acceptance との相互作用を検証しない。plan は pytest 外で一度 real commit を走らせるとしているが、bundle を fresh 環境から再取得した後の再走までは要求していない。さらに現在は前項の `g++-13` 不在で real-build control が skip される。

放置時の値（1行）: fixture の `8/8` 成功だけが残り、実 submodule の復元・CMake・compiler 経路で失敗しても、レポートの TU 同一判定を誤って green にできる。

### 6. “TU 同一”という名称が、実際に比較する証拠より強い

severity: must-fix

根拠: `s2-plan.md:106,118` は TRACE=0 翻訳単位同一を主張するが、再利用する `source_digest._cpp_normalize` は `#include` を除去し、`-nostdinc` と固定 `BUILD_FLAGS` で preprocess する（`orchestrator/campaign/source_digest.py:320-352`）。defines も Options/CMake から抽出した集合であり、実 CMake の全 compile command そのものではない（`source_digest.py:632-637`）。

この設計は「既存 source_digest モデル上の normalized source identity」としては成立し得るが、実際の CMake translation unit byte identity と同一ではない。レポート名をモデル保証に限定するか、実際の compile command / include path / flags を用いた old/new preprocess に強化すべき。

放置時の値（1行）: レポートの `TU_same=true` が実 build の条件差を含まない値になり、TRACE=0 の性能・throughput を使った certified 選択を誤る可能性が残る。

### 7. checker 成功と certification の境界を durable に記録していない

severity: must-fix

根拠: checker は enforcement source closure 外の独立ツールである（`s2-plan.md:81`）。現在の wave は gitlink、`CURRENT_PIN`、`CCBENCH_FULL_SHA` を変えず（`brief.md:49-55`）、人間の push・承認後に初めて受理集合が変わる（`ruling-package.md:70-84`）。一方、成功証拠は stdout JSON と worklog への記録だけである（`s2-plan.md:107,130`）。

この wave で機械的に検証できるのは、old/new の全差分、8 genome の TRACE=0 比較、実 commit の preprocess/build、bundle の保存・復元、復元後の clean/acceptance である。これらを `certified_delta=0`、候補 new SHA、bundle path、bundle SHA256、compiler identity、raw checker JSON の hash として repo 外 artifact に固定し、worklog から参照する指定が必要。

放置時の値（1行）: 現在値を変えていない証拠と新しい certified 選択を区別できず、台帳の certified 件数またはレポートの承認状態を誤って +1／未記録にする。

### 8. `run_tests.py` の full acceptance 形が曖昧

severity: nit

根拠: `s2-plan.md:142` は `python3 tools/run_tests.py ...` とだけ書くが、`tools/run_tests.py:505-563` は default target と許可された引数だけを acceptance run と認識する。checker pytest や verifier characterization の node指定は targeted run であり、full acceptance とは別物である。

放置時の値（1行）: targeted run を full acceptance と記録してしまい、レポートの acceptance 値だけが green で、certified 選択・台帳の受入値は未検証のままになる。

## 問題なし

- hook 迂回: `transaction.cc` だけを直接編集する A は `guard_write.py:36-38,143-156` の許可面に一致する。scratch copy、`git apply` 迂回、hook 改変、sandbox 昇格は plan にない。
- FN-1/FN-2 重複: FN-1 は trace 外 `commit_counts_` による個数 witness、FN-2 は C 行の R/W 件数と E による transaction 内構造検査であり、`docs/worklog.md:631-644` の区別どおり機構は重複していない。
- ファイル所有: A の submodule source と B の checker/test は tracked file の素集合として分離されている（`s2-plan.md:135-148`）。ただし real run、bundle、復元、acceptance は共有 submodule state に触れるため、A→B の SHA確定後に直列化すべきである。

## 総括

blocker は、現環境に存在しない `g++-13` を必須実走条件にしている点です。bundle の配置は正しいものの、fresh 環境での復元証明と durable receipt は must-fix です。

実装単位の分割には賛成します。synthetic B は並列化できますが、new SHA を使う実走、bundle 検証、旧 HEAD 復元、full acceptance は共有状態を持つため直列の統合段に分けるべきです。