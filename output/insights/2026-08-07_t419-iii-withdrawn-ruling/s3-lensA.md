[所見 1] 最終 receipt への binding が fail-open である

根拠: brief は外部検証と final receipt binding を完了条件にしている（[s1-brief.md](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-iii/s1-brief.md:18>) 18–21）が、plan は collector を変更せず、ファイルが存在すれば generic manifest に入るだけとしている（[s2-plan.md](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-iii/s2-plan.md:118>) 118–127, 216）。現行 collector は ID と `calibrate_rc` の型しか必須化せず、列挙できたファイルを manifest 化する（[collect_receipt.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/tools/pegasus/collect_receipt.py:107) 107–180）。したがって検証 artifact が欠落しても収集成功する。`test_collect_receipt_manifest_binds_external_verification_artifact` は fixture にファイルを置く正例だけなら、実ジョブがそのファイルを一度も生成しなくても緑のままである。

**成果物影響:** verification を含まない final receipt が正式台帳に入り、certified 選択結果が外部検証済みであるかのように参照されうる。

推奨: [collect_receipt.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/tools/pegasus/collect_receipt.py:107) で job-result v2、`verification_rc == 0`、検証 artifact ちょうど1個、subject hash 一致を必須化する。plan 184–186 に「検証ファイル欠落」「拒否 artifact」「hash 不一致」の collector 負例 nodeid を追加する。collector を変更しないなら T-419 (iii) の完了を主張しない。

[所見 2] Base64 receipt replay は将来ジョブについて自己成就している

根拠: plan の replay は receipt 内の Base64 を復号して再計算し、`registered/` を読み直さないと明記している（[s2-plan.md](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-iii/s2-plan.md:89>) 89–102）。そのため、receipt の複製 bytes と checks を一緒に作り直せば常に自己整合する。`test_receipt_replay_detects_tampering_and_recomputes_acceptance` と `test_subject_bytes_are_canonical_base64_and_not_plain_probe_corpus` は、実ファイルだけを差し替えても赤くならない。94a4 の中央 artifact については `test_registered_94a4...regenerates_central_artifact_exactly` が独立に実ファイルを読む実装なら差異を検出できるが、753f と将来の staging/final receipt には同等の照合が明記されていない。実測サイズは 94a4 が 31,645 bytes、753f が 31,571 bytes、Base64 本文だけで合計 84,292 文字である。

**成果物影響:** receipt が指す bytes と `registered/` の選択対象が別物になり、同じ certified 参照から異なる受理判定を再生できる。

推奨: [s2-plan.md](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-iii/s2-plan.md:54>) の schema を `subject.relative_path`、`sha256`、`byte_count` に変更し、replay は毎回その実ファイルを strict-read する。両現行 artifact と将来 staging receipt に対し「receipt は不変、実ファイルのみ1 byte変更」で拒否する nodeid を追加する。

[所見 3] locator と実際に較正・公開した subject の同一性が証明されない

根拠: verifier は `publish.json.target` を locator として読み、receipt には basename と複製 bytes を持つだけである（[s2-plan.md](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-iii/s2-plan.md:59>) 59–76, 118–125）。現行 producer には attempt の `calibration.json`、`publish.json.target`、`published-self-comparison.input_sha256` があるが、plan はこれらと verifier subject の hash が同一であることを gate にしていない（[cli.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/calibrator/cli.py:791) 791–853）。locator を既知の良品 94a4 に差し替え、別 artifact B を生成・公開したケースでも検証だけ通せる。

**成果物影響:** job が公開した B ではなく A の判定で `overall_rc=0` となり、レポートと台帳が誤った calibration hash を certified 選択に結び付ける。

推奨: [certify_calibration.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/tools/pegasus/certify_calibration.sh:742) で、attempt bytes hash = publish target filename digest = published-self-comparison input hash = verifier subject hash を明示的に照合する。2つの有効 artifact を用いた locator-swap 負例 nodeid を追加する。

[所見 4] policy mismatch が未登録で、D191 決定6の最重要境界が無検査である

根拠: canonical 述語は `input_valid && policy_matches && band_pass` の唯一の判定経路である（[execution_guard.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/campaign/execution_guard.py:183) 183–196）。一方、現物2件はいずれも tolerance 2.0 であり、plan の負例にも schema-valid・quality accepted・全サンプル band 内だが tolerance だけが 3.0 の入力がない。`test_canonical_predicate_is_the_only_acceptance_signal` の monkeypatch は「関数を呼んだ」ことしか証明せず、preimage の expected policy を実ファイルではなく process policy で上書きするバグには全15 nodeidが反応しない。plan 通り実装されれば直接の D191-6 違反は見当たらないが、その保証が恒真に近い。

**成果物影響:** site policy と異なる calibration が `checks.effective_clock_self_consistent.passed=true` となり、受理集合が policy 非適合 artifact まで広がる。

推奨: plan 148 付近に `test_policy_mismatch_rejects_even_when_band_passes_and_preimage_uses_artifact_tolerance` を追加する。artifact tolerance=3.0、policy=2.0、band_pass=true とし、canonical=false、receipt preimage の両値が3.0/2.0であることを別々に固定する。

[所見 5] Python 3.9 nodeid は、3.10 上だけでは互換性を証明しない

根拠: compute test dispatcher 自体が Python 3.10 候補を選ぶ（[dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/tools/pegasus/dispatch_compute.py:128) 128–132, 401–423）。login node は 3.10.12 で `python3.9` は見つからなかった。3.10 の `ast.parse(feature_version=(3,9))` は `match` を拒否できるが、`int | None` や3.9に存在しない runtime API の import 成否までは証明できない。したがって `test_module_import_surface_is_python39_and_does_not_import_calibrator_cli` は、3.10 import や文字列検索だけなら3.10専用 runtime 依存を加えても緑のままである。job 892707 の `calibrate_rc=0` は、IntelPython module 下で当時の CLI import chain が動いたことまでは示すが、解決された executable/version/hash、今回の verifier、将来の3.9 import は示さない。

**成果物影響:** calibration 公開後に外部 verifier だけが compute node で import 失敗し、公開済み artifact と final receipt/台帳が分断される。

推奨: 実ジョブ側で default `python3` を使った独立 import probe を実行し、`sys.version`、`sys.executable`、実体 hash を receipt に記録する。静的検査も残すなら3.9 grammar の負の対照を置くが、それを実 runtime probe の代替にしない。

[所見 6] 変異表の4行は KILLED の帰属が成立しない

根拠:

- `validate_calibration_v2(raw)` → `json.loads(raw)`（plan 194）は、後段が typed object を要求して別例外で拒否すれば `test_schema_invalid...` が緑のままで、schema 検出力を測れない。
- Base64 → plaintext（197）は受理集合を変えず、正しさ変異ではなく表現上の diagnostic pin である。これは `nit` として分離すべきである。
- `|| rc=$?` → `|| true`（200）は、その後の post probe が落ちれば別層に mask される。
- plan 192 と195は本文で `CLI 753` 等の追加赤を認めながら期待赤列に1 nodeidしか書いていない。mutation harness は観測した失敗集合の完全一致を要求する（[mutation_harness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/tools/mutation_harness.py:1177) 1177–1193）。

**成果物影響:** mutation ledger が「狙った防壁が変異を殺した」と誤記し、実際には mask・例外・追加失敗だった無効な検査を受理できる。

推奨: schema 変異は duplicate-key raw を `validate_calibration_v2(json.loads(raw))` に渡す形にする。shell 変異 fixture は post probe と cleanup を成功させる。各行に実際の完全な expected-red set を事前登録し、Base64 行は correctness score から除外する。

[所見 7] 「registered を列挙する既存 test はない」は誤りだが、94a4 の意味的被覆ゼロは正しい

根拠: brief 32 の列挙不存在は、[test_pegasus_tools.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/tests/test_pegasus_tools.py:632) 632–638 の `glob("calibration-*.json"); next(...)` に反証される。ただしこれは先頭1件を acquisition fixture にするだけで、94a4 の verdict を固定しない。production の `load_verified_calibration` 呼出しと env-attestation test はすべて [env_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/campaign/env_contract.py:265) 265–270 が指す旧 753f を読む。94a4 hash の意味的 assertion は既存コード・test に見つからなかった。新機構が純増で拒否できる具体例は、filename/hash 不一致、post-publish duplicate key、quality rejected、policy tolerance mismatch、自己矛盾する旧753f、fresh-process 時だけ消える process-local rebind である。

**成果物影響:** 現状のままでは新しい94a4が永久検査なしで activation 候補になり、また nondeterministic な `next(glob)` により既存 test の参照対象も将来変わる。

推奨: [test_pegasus_tools.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/tests/test_pegasus_tools.py:632) の fixture は active contract を明示参照させる。別に `registered/` 全件を読み、外部に手書きした期待 verdict と照合する inventory nodeid を追加する。

[所見 8] Base64 複製は監査から意図的に見えにくい第三のコピーになる

根拠: 同一内容は既に `registered/` と attempt output に各1コピー存在する。中央 artifact への Base64 内包で約85 KBの第三コピーが増える。plan は既存 plaintext corpus scanner を刺激しないことを設計理由にし、その不在を nodeid で固定している（[s2-plan.md](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-iii/s2-plan.md:131>) 131–135, 164–165）。その結果、grep、marker scan、freeze、fold、audit は内包された artifact を通常の calibration として発見できない。

**成果物影響:** pin/freeze が実ファイルと receipt 複製の片方だけを固定し、監査件数・参照 hash・再生結果が経路によって分岐する。

推奨: hash と locator のみを receipt に置き、実ファイルを都度読み直す方が現在の選択対象に対する検出力は高い。履歴の自己完結 snapshot が必要なら、inline Base64 ではなく単一の content-addressed blob store を別契約として設計する。

[所見 9] 「別 process」は memory 分離だけで、検証コードの権威を固定していない

根拠: source clean の確認は job 冒頭だけである（[certify_calibration.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/tools/pegasus/certify_calibration.sh:172) 172–179）。plan は working-tree hash pin を明示的に対象外としている（[s2-plan.md](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-iii/s2-plan.md:216)）。receipt の authority は関数名等の文字列であり、`execution_guard.py` や policy module の commit/blob hash を保持しない。別 process は monkeypatch を消すが、job 中の checkout 変更や別 checkout の同名関数までは識別しない。

**成果物影響:** 同じ authority 名の異なるコードが異なる受理集合を作っても、certified レポートと台帳上は同一判定器として扱われる。

推奨: verifier receipt に source commit と verifier/canonical/policy module の blob hash を記録し、起動直前にも clean/HEAD を再確認する。実装しない場合は成果物上の表現を「process-memory independent」に限定する。

[所見 10] `overall_rc` は cleanup 前に確定するため名前が事実より強い

根拠: plan は verifier 後の値を `overall_rc` として job-result に書く（[s2-plan.md](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-iii/s2-plan.md:19>) 19–25）が、現行 script は job-result を cleanup より先に出力する（[certify_calibration.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/tools/pegasus/certify_calibration.sh:742) 742–770）。従って `overall_rc=0` の後に cleanup や scheduler job 自体が失敗しうる。892707 の `calibrate_rc=0` からも job 全体・最終収集成功は導けない。

**成果物影響:** ledger/report が pipeline 内部成功を job 全体成功として集計し、存在しない final receipt を certified 成功件数に含めうる。

推奨: cleanup 前の値は `verification_pipeline_rc` に改名するか、cleanup 後に final job-result を原子的に確定する。collector は scheduler accounting と final result の双方を照合する。

## 総括

**NO-GO。** 現 plan のままでは receipt replay と final receipt binding が fail-open である。  
最小是正は次の3点。

1. Base64 自己再生を廃止し、hash付き locator から実 `registered/` bytes を再読して照合する。  
2. collector に検証 artifact・subject hash・成功状態の必須 gate と欠落負例を追加する。  
3. policy mismatch、locator swap、実 Python 3.9 import の3負例を追加し、変異表の完全な赤集合を再登録する。  

pytest / `run_tests.py` は実行していない。所見は静的検査と artifact bytes/hash の読み取りに基づく。