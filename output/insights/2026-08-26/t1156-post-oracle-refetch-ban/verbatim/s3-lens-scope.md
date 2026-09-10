**所見 1**: (P1)/(P2) の事前検査は oracle が実際に判定した内容ではなく、oracle 前の binding を検査している。

- **具体的失敗**: `s8b_floor_campaign.py:3859-3873` で内容 A の `_FloorOracleDependencyBinding` を取得した後、oracle の `_prepare_verified_dependency()` 前だけ共有 `masstree-src` を canonical な内容 B に差し替え、private copy 完了後に A へ戻す。oracle receipt は B の `dependency_config_sha256` と `dependency_manifest_sha256` を記録する一方、`build_kwargs` は A の `cache_receipt()` と archive SHA を渡す (`s8b_floor_campaign.py:3979-4003`)。計画中の helper は A を再観測して成功し、build も A を使う。`fetchcontent_base_dir` は oracle 証拠ではなく、通常の mapping receipt と同時指定されているだけである。
- **成果物影響**: `sort_swo_oracle` receipt は B を判定した PASS、`binary_sha256` は A から作った binary という不整合が portable record、manifest、result に封入される。certified floor 値の受理集合に「oracle と build の材料が違う」組が残る。
- **判定**: **must-fix**。`oracle_attempt.receipt.dependency_config_sha256` と binding の一致だけでなく、既存 `SHA256SUMS` 権威と `DEPENDENCY_MANIFEST_SHA256` を build 直前にも検証し、oracle PASS 由来の内容 receipt を build 境界まで持ち回る必要がある。

**所見 2**: producer へ token を足すだけでは、禁止前の flag 無し durable manifest を resume と ratified validator が受理する。

- **具体的失敗**: 禁止前に作った `manifest.json` が `sort_best.configure_argv` に `-DFETCHCONTENT_FULLY_DISCONNECTED=ON` を持たず、binary SHA、manifest SHA、journal が相互一致している状態で新コードへ更新する。manifest が既にある resume は `build_v2()` を呼ばず、`_load_resume_manifest()` から既存 binary を使う。`_validate_portable_built()`、`s8b_binary_admission.validate_portable_binary_record()`、`s8b_ratified_freeze._validate_portable_binaries()` は argv を non-empty `list[str]` としか検査しない。floor postflight の `s8b_floor_campaign.py:3442-3489` も新 token を無視する。
- **成果物影響**: cache identity を変更しても resume 経路には効かず、flag 無し binary の測定が続行される。既存 manifest の SHA は journal と attempt registry の `manifest_sha256` にそのまま束縛されるため、台帳も整合したまま禁止前の受理集合を維持する。
- **判定**: **must-fix**。sort_best の durable record に policy version を束縛するか、少なくとも configure argv へ新 token exact 1本を要求する validator と schema migration が必要である。非 sort record は 0本を要求すべきである。

**所見 3**: 親の (P4) identity 不変は旧 cache binary を禁止後も受理し、さらに虚偽の configure argv を生成する。

- **具体的失敗**: 同じ dependency receipt と archive SHA で、旧コードが flag 無しで作った completion entry がある。`_v2_identity()` を変えない場合、新コードはその entry に hit する。cache hit の `_v2_result()` は保存済み argv を読まず、現在の `_v2_commands()` から flag 付き argv を再生成する (`buildcache.py:2056-2065,1680-1710`)。
- **成果物影響**: flag を実行していない binary が「flag 付き configure で作られた」と記録され、floor manifest、result、ratified validation の provenance が事実と異なる。dependency bytes の receipt は内容同一性を示しても、新しい禁止 policy の実行を示さない。
- **判定**: **must-fix**。base-bound identity に内部固定の policy ID を入れ、旧 entry を必ず miss させる必要がある。これは親 (P4) への明示的反論である。

**所見 4**: 計画の「fresh 実行 argv、fresh result、cache-hit result の完全一致」テストは現コードでは成立しない。

- **具体的失敗**: fresh configure は `buildcache.py:2087-2114` で `.staging-<pid>-<nonce>` を `-B` にして実行される。fresh result は publish 後、`buildcache.py:2240-2249` から完成 digest directory を渡して `_v2_result()` が argv を再生成する。したがって configure index 4 と build index 2 は必ず異なる。cache-hit result は完成 directory 側である。
- **成果物影響**: 計画どおりのテストは常時赤になる。テストを通すため記録を staging path に変えると、削除済み path を durable provenance に残し、A1/A2 の build-directory exact 述語や portable record の意味まで変える。
- **判定**: **must-fix**。完全一致ではなく、正規化後の構造と policy token の一致を検査すること。historical 実行 argv を本当に記録するなら completion manifest への保存を含む別設計が必要である。

**所見 5**: (P5) を外すと `cmake --build` が oracle 判定済みの `config.h` と archive を再生成する実経路が残る。

- **具体的失敗**: configure 直前の helper 成功後、configure と build の間に `config.h` または `libkohler_masstree_json.a` を削除する。`ThirdParty.cmake:66-78` の `add_custom_command(OUTPUT ...)` が `masstree_build` から起動され、source tree 内で `bootstrap.sh`、`configure`、`make`、`ar` を再実行する。`FETCHCONTENT_FULLY_DISCONNECTED` はこの custom command を止めない。
- **成果物影響**: binary は oracle 後に再生成された config/archiveから作られる。既存 postflight が最終差分を拒否しても事前禁止ではなく、再生成後に元 bytes を戻す競合には十分でない。
- **判定**: **裁定行き**。題名を FetchContent 再 populate に限定するなら別 wave へ送れるが、「oracle 後の材料変更を禁止する」というユーザー裁定まで満たすなら本 wave の不足である。単なる build 直前再検査でも競合窓は残るため、書込み権威または immutable/private build root が必要になる。

**所見 6**: global な `FETCHCONTENT_FULLY_DISCONNECTED` は masstree 以外の依存まで禁止し、scope を広げる。

- **具体的失敗**: masstree は oracle binding と一致したまま、oracle 後に `mimalloc-src` だけが欠落した状態を作る。新 flag は `FetchContent_MakeAvailable(mimalloc/googletest)` にも作用し、従来なら再 populate した経路を切断して configure を失敗させる。
- **成果物影響**: SWO 材料に問題がない cell まで build 不能となり、certified 選択候補が欠落する。これは安全側の縮小だが、masstree の download 権威変更より広い。
- **判定**: **裁定行き**。CMake 3.22/3.25 の `FETCHCONTENT_SOURCE_DIR_MASSTREE` は当該依存だけを population から外し、絶対 source 不在も configure error にできるため、masstree 専用 override を代案として比較すべきである。

**所見 7**: positive control の三負例のうち missing-source と archive mismatch は production floor では既存検査と重複する。

- **具体的失敗**: floor は常に archive SHA を渡し、現行 `build_v2()` は cache lookup や configure より前の `buildcache.py:1932-1939` で archive を読む。`masstree-src` 不在なら archive read が失敗し、archive bytes 不一致ならその場で拒否される。exact 材料の正例も既存 `test_v2_fetchcontent_base_is_canonical_single_define_and_receipt_in_preimage` と archive observation の正例が既に通している。
- **成果物影響**: 新 helper の接続を外しても missing-source/archive の統合結果は既存 gate で赤になるため、新禁止機構の純増検出力として数えられない。逆に、oracle receipt と pre-oracle binding の不一致、flag 無し resume、ratified manifest の拒否は無検査のまま残る。
- **判定**: **must-fix**。純増なのは configure 前の config mismatch、flag multiplicity、policy identity miss である。さらに oracle receipt mismatch と旧 durable manifest の負例を追加すべきである。

**所見 8**: (P3) の「oracle 後の prebuild 再入拒否」は現 call graph には発火対象がなく、単純な gate は恒真化する。

- **具体的失敗**: `_prepare_floor_oracle_dependency()` の唯一の production 呼出は cell loop 前の `s8b_floor_campaign.py:3859-3873` にあり、その後の oracle/build closure から再呼出する edge はない。呼び手が `pre_oracle=True` のような定数を渡す gate を追加しても、late callsite が同じ値を渡せる。
- **成果物影響**: その実装は受理集合を変えず、「機械的に禁止した」という文書上の主張だけが増える。一方、将来 late callsite が追加された場合は現状の順序テストだけでは runtime 拒否にならない。
- **判定**: **裁定行き**。不可逆な phase capability を共有する設計まで要求するか、現行 call graph と順序テストを正本として P3 を実装対象から除くかを決める必要がある。

**所見 9**: login-node probe の「完全な configure 成否」は production regime へ転移しない。

- **具体的失敗**: 親実測は CMake 3.22.1 の単一 `FetchContent_Populate()` driver だが、登録済み Pegasus calibration は CMake 3.25.0 であり、実 CCBench はさらに mimalloc/googletest の `FetchContent_MakeAvailable()` と alias target を構成する。例えば masstree source 不在は minimal driver で rc=0でも、他 dependency 不在時の full CCBench configure 成否までは示さない。
- **成果物影響**: probe の rc や failure stage をそのままテスト oracle にすると、実 floor の拒否理由と記録される diagnostic がずれる。flag が download/update を迂回する分岐自体は、ローカルに存在する CMake 3.22 と 3.25 の `FetchContent.cmake` で静的に同形だが、full driver の rc は未実測である。
- **判定**: **nit**。保証を「対象2版の module 分岐を静的確認した」に狭め、compute node で実測済みとは書かないこと。

## 総括

段2プランのままでは採用不可である。最大の穴は、build 前 helper が oracle PASS の receipt ではなく oracle 前の binding を検査する点と、禁止前の durable manifestを resume/ratified 層が引き続き受理する点である。

親の provisional 裁定は次の結論になる。

- (P1): 不完全。oracle PASS 由来の内容 binding と durable consumer gate が欠落。
- (P2): A1/A2 の非 base exact argv を守る条件としては機能するが、base は oracle 実行の証拠ではない。
- (P3): 現 call graph には late edge がなく、非恒真な phase capabilityを要求するか裁定が必要。
- (P4): 誤り。base-bound cache identity は policy ID で分離必須。
- (P5): 再生成経路は実在する。fetch 限定なら別 wave、材料変更禁止なら本 wave の不足。

固定された23件の frozen artifact 自体には configure argv pin はない。しかし新規 floor の `manifest.json` は `binaries.configure_argv` と identity変更後の build pathを含むため bytes と `manifest_sha256` が変わり、その値は journal と attempt registry へ波及する。literal pin の更新問題ではなく、禁止前 manifest の migration/拒否問題である。

指示どおり静的検査のみで、pytest、CMake configure、compute-node probe は実走していない。