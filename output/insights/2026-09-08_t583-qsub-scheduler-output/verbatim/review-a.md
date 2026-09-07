## 所見 1: `mkdir -p` の失敗は握り潰されない

根拠 (tools/pegasus/submit_certify.sh:3,88-91)

`mkdir -p` は条件式、`||`、subshell 内ではなく、`set -Eeuo pipefail` 下の単独 simple command である。通常 file との衝突、親 component が file、permission error のいずれも非ゼロで即時終了し、91行目以降へ進まない。ERR trap も存在しない。既存 symlink が directory を指す場合は成功するが、これは失敗の握り潰しではなく `mkdir -p` 自体の成功であり、裁定が symlink 走査を禁止している残余である。

影響

失敗時は hash、staging、preflight、qsub のすべてが実行されない。専用 rc はなく `mkdir` の終了値が外へ出る。

推奨 (不採用)

修正不要。失敗伝播は成立している。

## 所見 2: preflight 前と dry-run に空 directory を残す新しい副作用はある

根拠 (tools/pegasus/submit_certify.sh:88-103,119-131,186-190; ruling.md:64-76)

directory 作成は `JOB_SCRIPT_SHA256`、nonce 生成、staging、preflight より前で、`DRY_RUN` 分岐よりも前である。このため、後続の hash、Python、staging、preflight が失敗しても外部 root は残り、`--dry-run` でも作られる。一方、dry-run は従来から submission directory と capture、JSON を作るため、無副作用の契約ではない。今回残る追加物は共有 root directory だけである。

影響

失敗した投入でも空の `calibration-certify` directory が残り、作成不能なら preflight より前に終了する。job、certified 選択、レポート、台帳は作られない。

推奨 (不採用)

観測可能な副作用だが、裁定が指定した位置と `mkdir -p` そのものであるため変更しない。

## 所見 3: `$NONCE` の未定義または空値で `-o` が directory になる経路はない

根拠 (tools/pegasus/submit_certify.sh:93-107,178-181)

`NONCE` は93-97行目で `secrets.token_hex(16)` から定義され、scheduler path の179-180行目より十分前にある。生成 command が失敗すれば `set -e` で終了する。仮に成功しながら空文字を返す異常実装でも、104行目の `mkdir "$SUBMISSION_DIR"` が既存の `submissions/` directory と衝突して終了するため、qsub 構築へ到達しない。

影響

通常経路では32桁 hex nonce を持つ file path だけが `-o/-e` に入る。

推奨 (不採用)

定義順序に欠陥はない。

## 所見 4: 指定された特殊文字は argv を壊さないが、追加テストはそれを明示的に束縛していない

根拠 (tools/pegasus/submit_certify.sh:88-90,178-184; orchestrator/tests/test_pegasus_calibration_workload.py:162-208)

root と scheduler path は一貫して二重引用され、`qsub_cmd` は Bash array なので、空白、`,`、`:` を含んでも `-o` の次の単一 argv として渡る。scheduler path は `export_spec` に含まれず、`,` 区切りとの相互作用もない。`printf '%q'` の表示はこれらの文字について `shlex.split` で復元できる。ただし fixture は通常の `tmp_path` 名だけで、空白、`,`、`:` を明示的に生成していない。

影響

現実装の argv は壊れないが、将来 quoting を退行させても、文字種によっては追加テストが緑のままになる。

推奨 (nit)

実装修正は不要。特殊文字の明示的な test case がない点だけを test coverage の弱点として記録する。

## 所見 5: 指定外の既存挙動に byte 差分はない

根拠 (tools/pegasus/submit_certify.sh:5-39,84-91,118-181,186-247; git diff)

script の差分は88-90行目の導出と作成、179-181行目の scheduler path と qsub argv だけである。`usage()`、引数解析、RRATIO 検査、`':(exclude)output'`、4 capture の順序、preflight 失敗後の qsub 停止、両 JSON payload、schema、field、dry-run 分岐、`export_spec` は変更されていない。変更 file も script と指定 test の2件だけである。

影響

既存の受理集合と成果物 schema に、必要な scheduler 出力 directory の利用可能性以外の変更はない。

推奨 (不採用)

指定外差分は見つからない。

## 所見 6: 裁定を超える機構は混入していない

根拠 (ruling.md:62-89; tools/pegasus/submit_certify.sh:88-90,178-181)

追加は裁定の2点に一致する。containment gate、新 CLI、`realpath`、symlink 走査、専用 error message、専用 rc はない。

影響

裁定が禁止した新しい拒否条件は導入されていない。

推奨 (不採用)

scope 超過の攻撃は不成立。

## 所見 7: 追加テストから実運用 evidence root を汚す経路はない

根拠 (orchestrator/tests/test_pegasus_calibration_workload.py:165-228; tools/pegasus/submit_certify.sh:88-90,186-190)

fixture repo は `tmp_path/repo`、Git common dir は `tmp_path/repo/.git` になるため、導出先は `tmp_path/izanagi-job-evidence/calibration-certify` である。attempts root も `tmp_path/attempts`。実行対象は複製した script であり、dry-run 分岐により qsub 自体も呼ばれない。実 repo の `tools/pegasus` は copy 元として読み取られるだけである。

影響

追加テストが `/work/1/SFC/tanab/izanagi-job-evidence/` に directory または file を作ることはない。

推奨 (不採用)

本番証拠置き場の汚染は認められない。

## 所見 8: `copytree` は無関係な file 群へテスト成否を結合している

根拠 (orchestrator/tests/test_pegasus_calibration_workload.py:165-185,231-259)

`ROOT/tools/pegasus` 全体を各 test ごとに複製し、除外は `__pycache__` だけである。policy、全 policies、probes、他の submit script も複製・commit される。追加テストから実際に参照されるのは submit script、共通 policy、calibration policy、job script に限られ、他の script や probe は実行されない。しかし、将来追加される巨大 file、読めない file、symlink の参照先まで `copytree` の成否と時間に影響する。

影響

本番成果物には影響しないが、対象機能と無関係な tree 変更で test が遅くなる、または失敗する可能性がある。さらに helper は2 test から別々に呼ばれるため複製コストも2回発生する。

推奨 (nit)

現時点の正しさを阻害してはいないが、fixture の過剰な複製範囲は脆弱性として記録する。

## 所見 9: 追加テストは `mkdir -p` の存在と失敗伝播を検査していない

根拠 (orchestrator/tests/test_pegasus_calibration_workload.py:231-268; tools/pegasus/submit_certify.sh:90,186-190)

正例は path の形と親 directory の文字列だけを検査し、`expected_root.is_dir()` を確認しない。負例も lexical containment だけである。90行目を削除しても dry-run は qsub を実行しないため、両 test はそのまま通り得る。`mkdir` 失敗ケースもない。

影響

現実装は静的には正しいが、将来 directory 作成が削除されても緑になり、実投入では qsub が出力先を開けず job の受理集合が欠落し得る。

推奨 (nit)

現在の実装に対する must-fix ではないが、緑が directory provision を証明していない点を記録する。

## 総括

must-fix は0件。最重は、1) `copytree` による無関係な tree 全体への test 結合、2) `mkdir -p` 削除を捕捉できない test gap、3) preflight 失敗や dry-run でも外部 root が残る裁定済み副作用である。`mkdir` の失敗伝播、nonce 順序、argv quoting、既存挙動、scope、実運用 evidence の非汚染には破壊経路を確認できなかった。