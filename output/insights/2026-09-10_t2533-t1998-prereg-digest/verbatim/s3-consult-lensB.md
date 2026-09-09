## 前提と読んだ資料

指定された一次資料はすべて読めた。読めなかった path はない。

- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/s1-brief.md`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/s2-plan.md`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/verbatim/D1874.md`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/verbatim/D1790.md`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/verbatim/D1244.md`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/verbatim/D1267.md`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/verbatim/D1525.md`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/artifacts/probe-source-digest.json`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/artifacts/probe-env-contract.json`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/artifacts/AUTHORITATIVE-VALUES.md`

指定 worktree では、少なくとも次を現物確認した。

- `orchestrator/campaign/t1998_stock_inline_pair.py`
- `orchestrator/tests/test_t1998_stock_inline_pair.py`
- `orchestrator/tests/test_t1998_launcher_contract.py`
- `tools/pegasus/submit_t1998_balanced_stock_inline.sh`
- `tools/pegasus/a5_second_boot_backoff_sweep.sh`
- `orchestrator/campaign/{source_digest,model,env_contract,buildcache,backoff_sweep}.py`
- `orchestrator/campaign/b10_backoff_shape_sweep.py`
- `docs/b10-backoff-shape-preregistration.md`
- `docs/{README,phase3,pegasus-runbook,decisions,failures,worklog}.md`
- `orchestrator/tests/{conftest.py,test_acceptance_schedule_order.py,acceptance_duration_ledger.json}`
- `orchestrator/tests/{test_official_perf_closure.py,test_p3_build_authority_cli.py}`
- `orchestrator/campaign/materializer_admission.py`
- T-1998 insight、handoff、spool、Git branch/worktree ref

親側 checkout の作業木は読んでいない。pytest・build・qsub は実行していない。

親の実値はすべて再導出できた。

- job body working tree / HEAD blob: `dff913cb1044858b56f25721f2d0aac6539bbcf2a7ddb63b9e6b4bbcac7aecd8`
- gitlink: `511c9538e4e8efa54b45cda62e72389ed3b706ec`
- Pegasus contract: `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01`
- baseline source: `2d691b45afd02a7979b1872eeb0a5c5c58223550892331b31641599aa239a2c6`
- target source: `6454d9f34b04fdb148bc3324c5b07786d933dcc1ab0f7267aa0b91d414f70a84`

最後の二値は `source_digest.resolve_evidence(..., cxx="g++")` から再計算し、canonical genome、`genome_sha256`、`src_token="stock"`、`tracked_clean=true` まで probe と一致した。

## 所見

1. **重大度: must-fix** — plan に壊れた job body digest が実装指示として二度残っている。根拠: `s2-plan.md:74` の `dff913cb1044858bilho...` と `:100` の `dff913cb104485_CTX...` は、`AUTHORITATIVE-VALUES.md:3-12` および現物 SHA と不一致である。後続の訂正文だけでなく表・コード例そのものを正値へ直す必要がある。  
   **放置時:** 誤った箇所を写した実装は hex64 検査か正例で拒否され、新成果物を一件も受理しない。

2. **重大度: must-fix** — brief と plan は D1790 の「測定時点の事前登録 SHA」を job body SHA に置き換えており、さらに一つの `prereg_commit` を測定 commit と現行解析文書 commit の両方に使っている。根拠: D1790逐語 `:3-16` は二つとも事前登録版の SHA と定める一方、brief `:17-18,97-99` と plan `:98-105,113-124,303` は成果物側を job body SHA とする。現行の先例は `backoff_counterfactual_analysis.py:20-25,263-266,580-583` のように、成果物内の測定版 SHA と現在渡された文書 SHA を別々に照合する。plan 方式では文書改訂後、旧 `prereg_commit` を渡すと worktree/blob 不一致、新 commit を渡すと成果物の `repository_commit` 不一致になる。  
   **放置時:** 解析規則を一度改訂すると、旧 cohort は全件再解析不能になり、D1790 が防ごうとした受理集合崩壊をそのまま起こす。

3. **重大度: must-fix** — loader は optional であり、canonical 文書による consumer の受理集合束縛になっていない。根拠: plan `:136-158,223-234,314` は既存の `consume_balanced_stock_inline_pair(..., preregistered=...)` 署名を維持し、「loader を明示的に呼んだ側だけ」とする。現物の production caller はなく、直接 caller は `test_t1998_stock_inline_pair.py:411-414` だけで、任意の dataclass を手組みできる。新しい固定定数が閉じるのも job body SHA だけで、gitlink・環境・arm source は手組み値に追随できる。  
   **放置時:** canonical 文書を一度も読まず、成果物に合わせた手組み identity を渡す経路が引き続き受理され、「文書から consumer へ手写しなし」の成果物条件を満たさない。

4. **重大度: must-fix** — 新しい先行 job-body pin と既存負例の期待拒否位置が衝突する。根拠: plan `:105` は reservation 検査より先に `common.launcher_script_sha256` を定数比較するが、既存 `test_t1998_stock_inline_pair.py:502-515` は preregistered 側だけを変更し、拒否 field が `reservation.binding.script_sha256` であることを要求する。現行 reservation 比較は consumer `:915-919`。plan `:290-292` はこのテストを変更せず維持するとしている。  
   **放置時:** 正しい field で先行拒否すれば既存 acceptance node が1件赤になり、既存 field を偽装すれば拒否 provenance が誤る。

5. **重大度: should-fix** — acceptance ledger の変更は現計画では不要で、並行衝突を増やす。新 test file は作らず、既存 file に10 nodeを追加する計画である。未知 nodeid は `conftest.py:1571-1591` で既定 cost に落ち、被覆 gate は `test_acceptance_schedule_order.py:660-717` の90%だけである。静的判定では ledger を省いて赤になる件数は **0件**。一方、`docs/failures.md:23556-23570` は `nodeid_count` 衝突の実害を記録し、D1826 (`docs/decisions.md:55103-55119`) は次の ledger 変更時に count 除去比較を先に行うよう要求する。稼働中 `worktree-dev-wave-t2417-policy-arm-perf` の unique diff も同 ledger を変更している。  
   **放置時:** 受理集合を変えずに共有 ledger と `nodeid_count` を競合させ、land/acceptance の再走を発生させうる。

6. **重大度: should-fix** — 新しい canonical 文書が docs の地図から落ちている。根拠: `docs/README.md:13-38` は peer の preregistration 正本を個別に列挙するが、plan の変更面 `:207-257` に `docs/README.md` がない。`docs/pegasus-runbook.md` は既に submitter を登録済み (`:565`) で実行契約を変えないため更新不要、`docs/phase3.md` には T-1998/T-2533 の現役 anchor がないため更新不要である。  
   **放置時:** 新文書は canonical と宣言されても、正本の文書地図から到達できない。

7. **重大度: should-fix** — brief が成果物に含めた spool fragment と insight が plan から消えている。根拠: brief `:78-84` に明記される一方、plan `:207-257` の実装面は新文書・module・test・ledgerだけである。新しい decision がないなら decisions fragment は不要と brief 側を訂正すべきだが、少なくとも worklog fragment と insight の処遇は一致させる必要がある。  
   **放置時:** 完了状態と値の provenance が既存台帳・insight へ運ばれず、後続参照が brief と食い違う。

8. **重大度: nit** — `test_d1790_pins_are_distinct_exact_scalar_strings` は「独立」を「値が不等」と読み替えている。根拠: plan `:287-288`。現行 `backoff_counterfactual_cohort2_analysis.py:20-25` は別定数だが、未改訂なので両値は同一である。D1790 が禁止するのは同一定数への統合や複数版 allowlist であり、二つの値が偶然同じことではない。  
   **放置時:** 測定版と現行版が同じ正当な初版 cohort を、理由なくテストで拒否する。

## file:line の誤り

- `docs/t1998-balanced-stock-inline-preregistration.md:55-145` および plan `:211-221` が割り当てる `:1-235` は、対象 file 自体がまだ存在しない。正しい現物行はないため、`新規・行未確定` と記すべきである。
- `orchestrator/campaign/t1998_stock_inline_pair.py:184-300` は現在すでに `T1998PairRejected` と JSON helper 群が占有している。loader の正しい挿入 anchor は「既存 dataclass 終端 `:182` の後／`T1998PairRejected` の前 `:184`」であり、完成後行番号は未確定。
- brief の既存参照 `:131-182`, `:522-533`, `:707-712`, `:915-919`、`buildcache.py:1838-1842`、`backoff_sweep.py:283-296` は一致した。
- plan の既存参照では、b10 loader `:1763-1817`、fixture `:51-55,391-408`、負例 `:434-476,502-515`、全文禁止検査 `:760-767`、ledger `:22130-22159`、submitter `:43-45,89-92,172-180`、worklog `:682`、insight `:33` は一致した。
- 壊れた digest literal は行番号ずれではなく内容誤りであり、所見1の対象である。

## pin 閉包の結果

探した key:

- 新 path、basename、schema literal
- `EXPECTED_MEASUREMENT_JOB_BODY_SHA256`
- `EXPECTED_CURRENT_PREREGISTRATION_SHA256`
- `T1998_PREREGISTRATION_REL`
- job body 新旧 SHA の先頭12桁
- gitlink、環境 digest、両 arm source digest、canonical genome
- consumer/test/ledger の whole-file SHA と先頭12桁
- `path:line` 形式、docs 側、branch/worktree/spool/handoff

結果:

- 新 path と予定識別子の既存 pin は見つからなかった。
- 現行 whole-file SHA  
  `097eb447a457…`、`16086adbcf92…`、`1558b64d31c2…` の literal pin は見つからなかった。
- consumer path は `test_official_perf_closure.py:77`、basename は `test_p3_build_authority_cli.py:168` に membership pin がある。変更不要。
- `_build_dir_from_build` は `materializer_admission.py:110-114` を経由し、`test_p3_build_authority_cli.py:173-185,1228-1229` の閉集合へ間接到達する。loader 新設でこの registry 値は変わらない。
- consumer 全文は `test_t1998_stock_inline_pair.py:760-767` により禁止 import と `argmax` を走査される。loader が禁止文字列を導入しない限り pin 更新不要。
- test path は ledger に現行30 node (`:22130-22159`) がある。plan の追加は10 node。新 test file はないため acceptance harness の追加登録は不要。
- ledger は2,864,768 bytesで、`conftest.py:898-900` の16 MiB上限内。ただし `nodeid_count` と D1826/F903 の衝突 pin を plan が取り逃がしている。
- consumer/test の行番号 pin は T-1998 の凍結 insight・mutation report・verbatim に多数ある。歴史記録なので更新しない。
- `check_docs.py` に新文書へ適用される byte/最長行予算はない。worklog だけは100,000 bytes閾値 (`check_docs.py:196-201,6807-6816`) で、現物は87,094 bytes。新文書は `LIVING_DOCS` にも自動編入されない。
- 並行 wave では、`worktree-dev-wave-t2417-policy-arm-perf` が `docs/README.md`、`docs/pegasus-runbook.md`、`acceptance_duration_ledger.json` を変更中である。現planとの確定重複は ledger、本レビューで必要とした地図更新を採る場合は `docs/README.md` も重なる。T-2500 ほか同一baseの locked wave は未commitのため、変更 path までは証明できなかった。

## 無駄と判定したもの

- `test_current_arm_source_digests_are_accepted` は、fixture を実値へ変えた後の既存正例 `test_real_admission_and_receipts_accept_only_the_fixed_pair` と重複する。
- target 側 `test_each_arm_source_digest_drift_is_rejected[target]` は既存 `test_preregistered_source_digest_drift_is_rejected` と重複する。追加価値があるのは baseline 側だけである。
- D1790 の二定数に値の不等まで要求するテストは要求外である。独立した定数であれば、初版で値が同一でもよい。
- acceptance ledger の10件追記は現行 gate を赤から緑へ変えず、並行衝突だけを増やす。実走で被覆不足が観測されない限り本件の成果物には不要。
- whole-file SHA が完全一致する文書に対し、identity と無関係な field まで loader の追加 gate として再実装する部分は二重拘束になる。文書に記録することと、`T1998PreregisteredIdentity` の受理条件にすることは分けるべきである。
- 将来 cohort 用の互換層・allowlist はplanに含まれておらず、この点はD1790に沿っている。

## 総括

plan は実値そのものは再現できているが、D1790 の二版分離を job body SHA と単一 `prereg_commit` へ潰しており、このままでは文書改訂後の再解析が成立しない。  
さらに loader が optional なため、canonical 文書を経由しない手組み identity の受理経路が残る。  
即時の実装事故として、壊れた SHA literal 2件と、先行 gate に奪われる既存負例1件がある。  
新 test file はなく、ledger を省いて静的に赤となる acceptance node は0件。むしろ稼働中 T-2417 と衝突する。  
`docs/README.md` は更新が必要だが、Pegasus runbook と phase3 は更新不要である。  
pytest/build/qsub は未実走であり、検査を緑とは報告しない。