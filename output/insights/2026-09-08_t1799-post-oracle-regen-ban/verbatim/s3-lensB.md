## 所見 (real/refuted 付き)

- **real — plan はこのまま採用不可。** `make_snapshot_non_writable()` は masstree root だけでなく、その parent である共有 `FETCHCONTENT_BASE_DIR` の write bit も外します。元 mode は process 内の `SnapshotPermissionState` にしか残らず、hard kill 後の回復経路はありません。[s8b_expected_materialization.py:126-134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_expected_materialization.py:126) [s8b_expected_materialization.py:541-610](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_expected_materialization.py:541)

- **real — 並行する 2 つの protection context は相互排他でない。** A が RW→RO、B が RO mode を記録、A が RW へ復元、B が build、B が RO へ復元、という順序が可能です。B の build 中に書込み可能へ戻るため禁止が破れ、正常終了だけでも最後に RO が残ります。mode の採取、chmod、exact 復元はそれぞれ [s8b_expected_materialization.py:568-580](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_expected_materialization.py:568) と [s8b_expected_materialization.py:523-533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_expected_materialization.py:523) にあり、process 間 lock はありません。同じ base を public API で共有可能であることは plan 自身も認めています。[s2-plan.md:39-55](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1799-post-oracle-regen-ban/codex/s2-plan.md:39)

- **real — plan の「同じ判定済み根へ書く build だけが拒否される」は誤り。** parent の write bit も消えるため、masstree と無関係な `<base>/new-dependency-src` や prebuild directory の新規作成も失敗します。prebuild は `<base>/izanagi-masstree-prebuild` を作成先にします。[buildcache.py:2040-2051](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2040) CCBench も各依存を `FetchContent_Populate` / `MakeAvailable` します。[ThirdParty.cmake:42-55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/external/ccbench/cmake/ThirdParty.cmake:42) [ThirdParty.cmake:106-136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/external/ccbench/cmake/ThirdParty.cmake:106)

- **real — 絶対規律 2 に反する弱化が plan に混ざっています。** 現行は build 後に `effective_root` を取得し、期待根との一致を検査します。[buildcache.py:2717-2725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2717) [buildcache.py:2793-2807](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2793) plan は configure 直後の値を後段でも再利用するとしています。[s2-plan.md:90-92](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1799-post-oracle-regen-ban/codex/s2-plan.md:90) すると `if effective_root is None` が偽になり、build 後の CMakeCache / DependInfo 再読込が消えます。コード行を残しても検査時点を前へ移すので、build 中の実効根変更を新たに受理し得ます。

- **refuted — build 前の exact effective-root 一致自体は、新しい最終受理 gate ではありません。** 同じ一致述語は既に build 後に存在します。[buildcache.py:2801-2807](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2801) 前へ追加することは、実効根 B を使う build の前に A だけを保護する空振りを防ぐために必要です。ただし、build 後の再読込も別変数で維持しなければなりません。

## 復元されない終わり方と共有 base への影響

- **real — SIGKILL。** catch も `finally` も実行されず、全 regular file、directory、`.git` 配下、masstree root、base の mode が RO のまま残ります。fd は kernel が閉じますが、mode tuple は消失するため exact 復元不能です。[s8b_expected_materialization.py:448-480](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_expected_materialization.py:448)

- **real — OOM kill。** 受入 runner 自身に `MemoryMax` と scope 単位の OOM 判定経路があります。[run_tests.py:1895-1906](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/tools/run_tests.py:1895) SIGKILL と `memory.events` の組を `CAP_OOM` と判定しています。[run_tests.py:2093-2113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/tools/run_tests.py:2093) したがって OOM は仮想経路ではありません。

- **real — PBS walltime と TERM。** floor job は 10 時間の walltime と `--accept-sigterm=yes` を宣言しています。[floor_campaign.sh:1-6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/tools/pegasus/floor_campaign.sh:1) shell には TERM trap がありますが、Python 内の permission state を復元する処理はありません。[floor_campaign.sh:441-462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/tools/pegasus/floor_campaign.sh:441) Python process へ TERM または後続 KILL が届けば context の `finally` に依存できません。

- **refuted — `_run()` の timeout 単独では poison は残りません。** `subprocess.run(..., timeout=...)` の例外は build 側で包まれ、Python 親が生きていれば context が unwind して復元されます。[buildcache.py:3483-3496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:3483) [buildcache.py:2704-2713](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2704) ただし timeout の直後や処理中に親も TERM、SIGKILL、OOM で死ねば復元されません。

- **real — 同じ base の次回利用は壊れます。** 読むだけなら通り得ますが、masstree 内への open-for-write、root 内 rename、新しい `<base>` child の作成は permission error になります。次回の protection は RO mode を「元 mode」として記録するため、正常終了しても RW へ戻せません。

- **refuted — default official floor の「次の wave 全体」が必ず壊れるわけではありません。** official job は PBS job ID ごとの `/scr/...` を create-only で使い、default base もその下の固定 child に作ります。[floor_campaign.sh:267-273](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/tools/pegasus/floor_campaign.sh:267) [s8b_floor_campaign.py:3209-3237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_floor_campaign.py:3209) official mode は caller 指定 base を非 default seam として拒否します。[s8b_floor_campaign.py:7203-7207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_floor_campaign.py:7203) 次 wave が新しい job-local base を使う限り旧 poison は波及しません。pilot、direct API、明示 base の再利用では波及します。

- **real — 既存 cleanup は流用できません。** `admitted_build_snapshot()` も復元は `finally` だけです。[s8b_expected_materialization.py:876-927](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_expected_materialization.py:876) ただし対象は一意な disposable worktree で、通常 cleanup と手動 stale-worktree 復旧が用意されています。[patchharness.py:345-383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/patchharness.py:345) floor の cleanup は canonical lease を `rmtree` するだけで、FetchContent base の mode は復元しません。[s8b_floor_campaign.py:4706-4726](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_floor_campaign.py:4706) [sort_swo_dependency_material.py:577-588](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/sort_swo_dependency_material.py:577)

## 受理集合の変化

- **real — 束縛なし configure argv は、plan の条件分岐どおりなら不変です。** disconnected token は `post_oracle_dependency_binding is not None` の場合だけ加わります。[buildcache.py:1940-1971](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:1940) plan も protection を同条件に限定しています。[s2-plan.md:86-98](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1799-post-oracle-regen-ban/codex/s2-plan.md:86)

- **real — 束縛なし cache identity と receipt schema に予定上の byte 変更はありません。** `_v2_identity()` は argv や実装 file hashを含まず、post-oracle policy field は binding がある場合だけです。[buildcache.py:1295-1384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:1295) completion は引き続き `buildcache/v2` で、plan は field 追加を指定していません。[buildcache.py:2853-2882](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2853) これは未実装 plan の静的判定であり、実 patch の byte 実測ではありません。

- **real — A-1 paired と A-2 certification の exact argv は直接は変わりません。** A-1 は引数列全体を closed grammar と比較します。[paper_story_a1_paired.py:4826-4914](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/paper_story_a1_paired.py:4826) A-2/A-6 も exact v2 grammar を要求します。[paper_story_a2_certification.py:2091-2142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/paper_story_a2_certification.py:2091) いずれも今回の post-oracle capability を渡す経路ではありません。

- **refuted — 「同一 bytes を再生成した集合だけが縮む」は誤りです。** helper は source 内容以外に「root、全 `.git` 配下、全 node、parent を caller が chmod できる」という新しい実行前提を課します。[s8b_expected_materialization.py:448-480](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_expected_materialization.py:448) 現行の canonical 照合は tracked paths と `config.h` の bytes を検査し、source 内の無関係な untracked special node や所有権を受理述語にしていません。[sort_swo_dependency_material.py:439-480](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/sort_swo_dependency_material.py:439) 既に read-only の mount、別 owner の共有 checkout、unsupported node を含むが build 入力にはしない tree など、再生成しない正当 build も新たに拒否されます。

- **real — plan の `effective_root` 再利用は逆に受理を広げます。** configure 時に A を読み、build 中に CMakeCache / DependInfo が B へ変わっても、後段が保存済み A を使えば現行の build 後 root drift rejection が消えます。これは「縮むだけ」という主張への直接反例です。

## scope 逸脱の判定

- **refuted — build 前の effective-root exact equality は scope 内です。** 現行でも最終 predicate は同じであり、build 前へ置かなければ検査根 A と実効根 B の場合に B は writable のままです。[buildcache.py:1094-1103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:1094) D984 の禁止を実効 build root へ掛けるために不可欠です。ただし build 後再読込は維持が必要です。

- **real — parent、つまり base 全体の chmod は scope 外です。** brief の対象は masstree の判定済み材料を source tree 内で作り直す経路です。[brief.md:3-13](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1799-post-oracle-regen-ban/brief.md:3) sibling dependency entry の作成権限まで奪うことは D984 の禁止に不可欠ではなく、無関係な正当 build を巻き込みます。

- **real — 全 untracked node の型と chmod 可否を新たな受理条件にする部分も scope 外です。** これは post-oracle regeneration の禁止ではなく、既存 snapshot primitive の一般的な tree policy をそのまま持ち込んだ副作用です。

- **real — process 間 lock の追加は必要性が実在しても、この wave で推奨すべきでありません。** D953 は process 間 lock を別審査に属すると明記しています。[rulings-verbatim.md:64-68](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1799-post-oracle-regen-ban/rulings-verbatim.md:64) このため broad chmod を lock で補修するのではなく、D984 が既に許可した private snapshot 案へ戻すのが scope に沿います。

- **real — permission 案を残すなら、少なくとも plan の `effective_root` 変数再利用は撤回必須です。** build 前の `protected_root` と build 後に再取得する `observed_effective_root_after_build` を分け、既存 post-build assert を実際に再実行する必要があります。これは新 gate ではなく既存 gate の維持です。

## 既存 test 破損予測の反証

- **refuted — 現行 test から「既存 test が少なくとも 1 件壊れる」という反証は得られませんでした。** post-oracle test は各 test の `tmp_path/fetchcontent` を使い、同じ base を共有する例も同一 test 内の直列実行です。[test_buildcache_v2.py:1199-1223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/tests/test_buildcache_v2.py:1199) 正常な `finally` 復元が実装される限り、この test はそのまま通る形です。

- **refuted — xdist worker 間で同じ FetchContent base を共有する既存 fixture は見つかりませんでした。** runner は xdist を使いますが、該当 post-oracle tests は function-local `tmp_path` から base を作ります。[tests README:40-56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/tests/README.md:40) real material test も共有された設定元を直接 chmod せず、各 `tmp_path` へ copy します。[test_sort_swo_dependency_material.py:329-340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/tests/test_sort_swo_dependency_material.py:329)

- **real — したがって plan の「既存 test 破損予測 0 件」は静的には維持されますが、提案 test では本件の主要な失敗を検出できません。** 正常時と通常例外時の復元だけでは、SIGKILL/OOM、2 context の交差復元、base sibling 作成の巻き添えを検査しません。[s2-plan.md:94-102](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1799-post-oracle-regen-ban/codex/s2-plan.md:94) テストは実走していません。

## 親 brief の誤り

- **real — P1 の中心命題は正しいが、時間窓の表現が広すぎます。** outputs が oracle 後から最初の assert までに消えれば build は始まらず拒否されます。実在する再生成窓は、最後の build 前 assert 後から `cmake --build` までです。[buildcache.py:2687-2706](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2687) また custom command に `DEPENDS` はなく、両 OUTPUT が存在するだけなら通常は再走しません。[ThirdParty.cmake:66-78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/external/ccbench/cmake/ThirdParty.cmake:66)

- **real — P2 は public API について正しいが、official floor では通常一致します。** floor は base から 3 source root を固定導出して渡します。[s8b_floor_campaign.py:4441-4471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_floor_campaign.py:4441) 一方 `build_v2` 自体は base A と SOURCE_DIR B を拒否せず、実効根は cache の SOURCE_DIR を優先するため、API 面の穴は実在します。[buildcache.py:2435-2453](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2435) [buildcache.py:1094-1103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:1094)

- **refuted — P3 の「書込み不能化が安い」という採択判断は、既存 primitive をそのまま使う条件では成立しません。** shared parent poison、交差復元、hard-kill 非復旧が追加されます。D1663 の `cp -a` は private scratch だけを汚すために採用されたもので、むしろ private snapshot の安全性を支持します。[rulings-verbatim.md:102-109](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1799-post-oracle-regen-ban/rulings-verbatim.md:102)

- **real — P4 は正しいです。** `external/ccbench` は `.gitmodules` 登録された submodule で、index 実測は mode `160000`、pin `511c9538e4e8efa54b45cda62e72389ed3b706ec` でした。[.gitmodules:1-3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/.gitmodules:1) ThirdParty.cmake を既定で触らない判断は妥当です。

- **real — brief の DW-G05 因果は誇張です。** A-2/A-6 の実 build は `run_workload()` から generic `run_campaign()` へ進み、FetchContent base、receipt、post-oracle binding を渡していません。[paper_story_a2_certification.py:3434-3479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/paper_story_a2_certification.py:3434) 直前の `prepare_masstree_fetchcontent()` は condition-gate 用の固有 `TemporaryDirectory` であり、今回の floor post-oracle build ではありません。[paper_story_a2_certification.py:599-621](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/paper_story_a2_certification.py:599) A-6 も同じ driver の別 policy shapeです。[paper_story_a2_certification.py:472-479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/paper_story_a2_certification.py:472) よって T-1799 が直接改善するのは S8b floor の proof chain であり、A-2/A-6 certification の材料同一性ではありません。

- **real — brief の確定裁定一覧も不整合です。** supplied rulings の重要な D954 を一覧から落とし、代わりに射影にない D95 を載せています。[brief.md:15-22](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1799-post-oracle-regen-ban/brief.md:15) D954 は configure 後、build 前の実効値と材料再検査を明示した本件の直接前提です。[rulings-verbatim.md:70-90](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1799-post-oracle-regen-ban/rulings-verbatim.md:70)

## 総括

- **real — plan は差し戻しが必要です。** `make_snapshot_non_writable()` の as-is 再利用は、共有 base の parent まで凍結し、hard kill 復元不能かつ並行 context で禁止自体が破れます。

- **real — D984 を scope 内で閉じる推奨案は private snapshot です。** 既裁定済みの選択肢であり、異常終了時に残るのは disposable private treeだけです。process 間 lock、復旧台帳、一般化 gate を新設する必要もありません。

- **real — effective-root equality は build 前に必要ですが、build 後の fresh 再読込も必須です。** configure 後の値を後段へ再利用する plan の一文は削除すべきです。

- **refuted — 束縛なし argv、cache identity、receipt schema、A-1/A-2 exact argv が変わるという反証は得られませんでした。** また既存 test の静的破損予測 0 件も反証できませんでした。ただし post-oracle の受理集合が「同一 bytes 再生成だけ縮む」という広い主張と、A-2/A-6 への成果物因果は反証されました。