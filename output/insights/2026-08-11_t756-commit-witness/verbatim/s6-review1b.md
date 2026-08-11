結論は commit 前 blocker ありです。静的検査のみ実施し、pytest・実測・書き込みは行っていません。

主な問題は、S2 経路の witness parser が裁定どおり厳格化されていないことと、既存 characterization assert が反転されていることです。

## 裁定 B / E 対応表

| 要件 | 判定 | 根拠 |
|---|---|---|
| B1: main/batch counter を各ちょうど1行・非負整数だけ受理 | **部分的** | pipeline は満たす [pipeline.py:230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/pipeline.py:230)。一方、S2 は `.search()` で重複を受理し、batch を読まない [s2_verify_calibration.py:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/s2_verify_calibration.py:88)。 |
| B2: YCSB basename allowlist | **満たす** | `basename.startswith("ycsb_")` 以外を専用例外にする [pipeline.py:322](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/pipeline.py:322)。 |
| B3: 空 trace_dir 前提 | **部分的** | 残骸検出自体は実装済み [pipeline.py:316](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/pipeline.py:316)。ただし directory 不在は未分類 `FileNotFoundError` になる。 |
| B4: CLI flag・単一 dir 制約・S2 結線 | **部分的** | CLI と S2 の引数結線は満たす [cli.py:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/verifier/cli.py:48)、[s2_verify_calibration.py:155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/s2_verify_calibration.py:155)。ただし渡す値の抽出が B1 未達。 |
| B5: 3 reason を critic と workload/witness に結線 | **満たす** | 閉集合 [digest.py:119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/critic/digest.py:119)、extra/workload [digest.py:315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/critic/digest.py:315)、hint [digest.py:562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/critic/digest.py:562)。 |
| B6: `_run_trace` は NamedTuple、属性で読む | **満たす** | 型定義 [pipeline.py:262](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/pipeline.py:262)、consumer [pipeline.py:950](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/pipeline.py:950)。 |
| E/L1-11: 実効 gate に変異を再照準 | **部分的** | verifier の M01–M03 相当は実効 gate を検査するが、残骸 M11 のテストは guard 無効化後に別の `FileNotFoundError` で赤になる。 |
| E/L1-2: ladder 外側照合、凍結 JSON 不変 | **満たす** | 外側 gate [silo_ladder_rung1.py:832](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/silo_ladder_rung1.py:832)、呼び出し [silo_ladder_rung1.py:2852](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/silo_ladder_rung1.py:2852)。 |
| E/L1-3: 既存 WAL は scope 外 | **満たす** | 既存 replay の受理集合は変更していない。正本の scope 外指定 [s4-adjudication.md:90](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-trace-v2/s4-adjudication.md:90)。 |
| E/L1-4: CLI/S2 のみ採用、coverage 4 driver は scope 外 | **部分的** | 選択した範囲は守るが、S2 の strict parsing が不足。coverage 非変更自体は裁定どおり。 |
| E/L1-6: parser 一意性 | **部分的** | pipeline と ladder は一意性を検査するが、S2 は重複を受理する。 |
| E/L1-7: “独立 witness” と誤称しない | **満たす** | 実装コメントは「trace 外 counter」と表現 [core.py:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/verifier/core.py:27)。 |
| E/L1-8: abort contract・非直列化時の integrity 可視化 | **満たす** | 閉集合 [s8b_abort_reason_contract.py:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/s8b_abort_reason_contract.py:18)、renderer [digest.py:623](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/critic/digest.py:623)。 |
| E/L1-9: consumer/output-shape pin | **部分的** | consumer 更新漏れはないが、専用 byte regression がなく、既存 assert も1件反転している。 |
| E/L1-5: 診断順序の対照 | **満たす** | matching witness と既存 missing-txid の共存を検査 [test_verifier.py:743](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/tests/test_verifier.py:743)。 |
| E/L1-12: immutable carrier・both-or-none | **満たす（B6で型を上書き）** | NamedTuple は immutable。通常 API は `replace` 一回で expected/observed を同時設定 [core.py:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/verifier/core.py:30)。手書き部分状態も `clean=False`。 |
| E/L1-10: FN-2 は scope 外 | **満たす** | no-witness FN-2 characterization を維持 [test_verifier.py:626](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/tests/test_verifier.py:626)。 |
| E/L1-13: batch 非0は既存緑を壊さない | **満たす** | guard [pipeline.py:987](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/pipeline.py:987)。凍結実データは batch=0。 |

## 所見

### R1-1 / S2 は重複・batch witness を fail-closed にできていない

主張: S2 calibration の commit witness 抽出は裁定 B1 を満たさず、不完全 trace を certified にできる経路が残っています。

根拠: [s2_verify_calibration.py:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/s2_verify_calibration.py:88)、[s2_verify_calibration.py:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/s2_verify_calibration.py:96)、[s2_verify_calibration.py:130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/s2_verify_calibration.py:130)。

具体的な失敗経路: stdout が `commit_counts_: 1`、正規の `commit_counts_: 2` の順で重複し、trace が1件しか残っていない場合、`.search()` は1を採用し `--expected-commits 1` を渡します。verifier の observed=1 と一致して偽緑になります。また `batch_commit_counts_ != 0` も S2 では検査されません。

深刻度: **blocker** — S2 correctness/calibration 成果物が破損・重複 stdout や未帰属 batch commit を certified と記録し得ます。

処方: pipeline の `_parse_commit_witness` を S2 でも共有し、main/batch の両方が一意かつ batch=0 の場合だけ CLI を起動してください。重複・欠落・負数・非整数・batch非0の S2 回帰テストも必要です。

### R1-2 / trace_dir 不在は構造化 reason にならない

主張: `_run_trace` の `os.listdir(trace_dir)` が投げる `FileNotFoundError` は production caller 内で捕捉されません。

根拠: 送出点 [pipeline.py:316](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/pipeline.py:316)。唯一の production 呼び出しは [pipeline.py:917](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/pipeline.py:917) で、捕捉対象は timeout・`_TraceDirNotEmpty`・unsupported のみ [pipeline.py:921](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/pipeline.py:921)。上位 `run_campaign` は generic `eval-exception` に畳む [loop.py:266](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/loop.py:266)。

具体的な失敗経路: `mkdtemp` 後に directory が消える、または direct `evaluate` caller が消失 path を渡すと、`FileNotFoundError` が `_run_one_pass` を抜けます。`run_campaign` 経由では `eval-exception`、直接 `evaluate` では生例外となり、witness/trace-dir 帰属が失われます。fail-open ではありませんが、規律3の診断が崩れます。

深刻度: **must-fix** — variant は安全側に落ちるものの、原因が `other` 集計へ消え、再試行判断と成果物監査を誤らせます。

処方: `trace_dir` の存在・directory 性を明示検査し、専用例外または `_TraceDirNotEmpty` と同じ構造化 witness-attribution reason へ落としてください。

### R1-3 / `_TraceDirNotEmpty` の reason 相乗りは妥当だが、M11 の赤理由が一意でない

主張: `trace-no-commit-witness` への相乗り自体は妥当ですが、現在の残骸 guard テストは変異の単一理由性を満たしません。

根拠: 相乗り処理 [pipeline.py:924](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/pipeline.py:924)、critic の統合 hint [digest.py:572](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/critic/digest.py:572)、直接テスト [test_campaign.py:6259](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/tests/test_campaign.py:6259)。

具体的な失敗経路: M11 のように `if existing_traces:` を無効化すると、テストは `/not/executed/ycsb_silo.exe` の実行へ進み、`FileNotFoundError` で赤になります。残骸 guard を失ったことだけを理由に赤にはなりません。また `_mock_pipeline` の `preexisting_trace` seam [test_campaign.py:5150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/tests/test_campaign.py:5150) は、実際の test から一度も使われていません。

reason 判定: 独立した4番目 reason は不要です。残骸も「stdout witness と trace の run 帰属を確定できない」という同じ分類に入り、`preexisting_trace_files` により原因は構造化されています。裁定が要求する3 reason の閉集合とも整合します。ただし guard の変異検査は修正が必要です。

深刻度: **must-fix** — 本番は fail-closed ですが、M11 が誤った理由で killed と判定され、guard の実効性を証明できません。

処方: 実行到達時に明示失敗する subprocess spy を使い、「残骸があるため subprocess は0回」を直接固定してください。併せて `_eval(..., preexisting_trace=True)` から WAL reason・files・workload を検査してください。

### R1-4 / 既存 characterization assert が反転されている

主張: 既存の「witness 無しでは FN-1 が certified」という assert が削除・反転されており、指定されたレビュー規約上 blocker です。

根拠: 現在は同じ test を改名し、`expected_commits=2` を追加して `assert not res.certified` に変更しています [test_verifier.py:606](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/tests/test_verifier.py:606)。`HEAD^` では同 fixture を `verify_trace_dir(d)` で検査し `assert res.certified` でした。

具体的な失敗経路: optional API の no-witness 互換性が実装ミスで変わっても、旧 characterization が存在しないため検出できません。新 witness test が緑でも、旧 API の受理集合が意図せず変化した可能性を排除できません。

深刻度: **blocker** — 既存 assert の反転に該当し、凍結成果物・直接 API の後方互換性を守る証拠を失っています。

処方: 旧 no-witness test と `assert res.certified` をそのまま復元し、witness 付きの indeterminate test を別 nodeid として追加してください。その他の削除 assert は NamedTuple の同値な属性 assert への機械的置換で、緩和ではありません。skip/xfail の追加・削除はありません。

### R1-5 / no-witness byte 不変性は実装上成立するが、専用 byte pin がない

主張: `result_to_dict` の no-witness 出力は静的には完全同一ですが、裁定が要求した literal byte regression は追加されていません。

根拠: no-witness 時は `replace` と note 追加を通らない [core.py:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/verifier/core.py:26)。`clean()` は None/None を旧条件と同値に扱う [model.py:148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/verifier/model.py:148)。serializer は明示 key 列挙で変更されていない [report.py:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/verifier/report.py:42)。一方、追加 test は現在値同士の key/dict 比較だけです [test_verifier.py:710](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/tests/test_verifier.py:710)。

具体的な失敗経路: `result_to_dict` の key order、JSON options、値を baseline/witnessed の両方で同じように変える変異は、現在の比較を通過できます。旧 bytes の literal fixture がないため byte drift を直接 kill できません。

byte 検算結果: key 集合・挿入順・値・`notes` は no-witness で旧実装と同じです。`expected_commits`/`observed_commits` は report に列挙されず漏れません。repository 内に `Integrity` を対象とする `asdict`、`astuple`、`dataclasses.fields`、`vars`、`__dict__` serializer は見つかりませんでした。

深刻度: **must-fix** — 現 commit の成果物 bytes は変わっていませんが、裁定済みの回帰防壁が不足しています。

処方: 安定した `trace_dir` と固定 JSON options で、旧 literal bytes との完全一致を検査する専用 test を追加してください。

### R1-6 / consumer と binary prefix は検算したが取り残しはなかった

主張: `_TraceRunResult` と `verify_trace_dir` signature の consumer 更新漏れ、および実行可能な非YCSB fake path は見つかりませんでした。

根拠:

- `_run_trace` の production caller は `pipeline.evaluate._run_one_pass` の1件 [pipeline.py:917](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/pipeline.py:917)。
- 直接 test caller は [test_campaign.py:5900](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/tests/test_campaign.py:5900)、[test_campaign.py:6206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/tests/test_campaign.py:6206)、[test_campaign.py:6221](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/tests/test_campaign.py:6221)、[test_campaign.py:6252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/tests/test_campaign.py:6252)、[test_campaign.py:6264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/tests/test_campaign.py:6264)、[test_build_site_gate.py:407](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/tests/test_build_site_gate.py:407)。
- return fixture は campaign、S1、S8b、P3 red の全てが `_TraceRunResult` へ更新済み。
- `verify_trace_dir` の production consumer は CLI [cli.py:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/verifier/cli.py:66)、pipeline [pipeline.py:995](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/pipeline.py:995)、ladder [silo_ladder_rung1.py:2864](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/silo_ladder_rung1.py:2864)。ladder は意図的に optional API のまま外側 gate を使用します。

非YCSB名では `/not/executed/ycsb.exe` が1件ありますが、site gate が先に拒否する test です。`tpcc_silo.exe` は専用例外の正対照です。`/nonexistent/ycsb.exe` や `/fake/ycsb` は `_run_trace` 自体を mock 済みの fixture 内だけで使われます。実 build は `ycsb_<protocol>.exe` を生成します [buildcache.py:835](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/buildcache.py:835)。

具体的な失敗経路: 検算した範囲ではなし。`s3_lock_coverage` 等の同名 `_run_trace` は別関数であり、本返り値の consumer ではありません。

深刻度: **nit（問題なし）** — 成果物影響なし。

処方: なし。将来 `_run_trace` を公開面に広げる場合は symbol-level inventory test が望まれます。

### R1-7 / `dataclasses.replace` の共有参照は問題を起こさない

主張: `replace(dsg.integrity, ...)` の shallow copy は `notes` list を共有しますが、現行の参照関係と順序では副作用になりません。

根拠: `DSG` は Integrity を1参照だけ保持して構築を完了する [dsg.py:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/verifier/dsg.py:35)、その後 core が参照を一度差し替える [core.py:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/verifier/core.py:30)。旧 Integrity を外へ返す参照はありません。後続の field 代入・note 追加はすべて差し替え後の `dsg.integrity` に対して行われます [core.py:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/verifier/core.py:40)。

具体的な失敗経路: 検算したが破れませんでした。DSG 構築時の既存 notes は新 Integrity に保持され、witness note がその後へ追加され、parse issue の各 field/note も同一の新オブジェクトへ載ります。

深刻度: **nit（問題なし）** — 診断欠落・別オブジェクト汚染ともになし。

処方: なし。将来旧 Integrity 参照を外部公開するなら `notes=list(dsg.integrity.notes)` の明示 copy を検討してください。

### R1-8 / ladder 外側 gate は実データで有効

主張: ladder gate は凍結 verifier JSON を変更せず、実データ一致を通し、不一致を拒否します。

根拠: raw stdout は `commit_counts_=480595`、`batch_commit_counts_=0`、verifier は `stats.txns=480595`。`verifier.json` の SHA-256 は `d8e84423…898c2` で raw manifest の pin と一致し、対象 commit の diff に同ファイルはありません。照合は batch非0とcommit不一致の双方で `DriverError` [silo_ladder_rung1.py:836](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/silo_ladder_rung1.py:836)。

具体的な失敗経路: 一致時は recompute へ進みます。不一致 fixture は raw manifest を再生成したうえでも `raw_bundle` failure になります [test_silo_ladder_rung1_driver.py:1849](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/tests/test_silo_ladder_rung1_driver.py:1849)。

深刻度: **nit（問題なし）** — 凍結成果物 bytes と既存 certified evidence を維持しつつ、保存済み witness の破棄を防いでいます。

処方: なし。

## 総括

commit 前判定は **blocker** です。

- blocker: S2 の重複/batch witness が fail-closed でない。
- blocker: 既存 no-witness characterization assert が反転され、互換性 pin が失われた。
- must-fix: trace_dir 不在の構造化例外処理、M11 の単一理由性、専用 byte regression。

verifier 本体の count 一致 gate、NamedTuple consumer、`result_to_dict` の実際の no-witness byte不変性、`replace` の順序、critic/s8b reason 結線、ladder 外側 gateについては、静的に検算した範囲で破れませんでした。