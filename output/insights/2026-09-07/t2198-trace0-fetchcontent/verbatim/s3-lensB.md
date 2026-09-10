## 所見

1. 認証用 `<base>/<name>-src` の生成経路が欠落

- 判定: **real**
- 根拠 file:line: `tools/pegasus/fetch_third_party.py:605-679` は `<staging>/<source_name>` を作る。`s2-plan.md:118-132,329-332` は既存の `<name>-src` root を受け取って再コピーするだけで、最初の生成者を持たない。
- 再現または反例の具体形: `hydrate` が返す `.source_root` を計画どおり submitter へ渡すと、`<root>/masstree-src` が存在せず qsub 前に拒否される。一方、実在する変換経路は `tools/pegasus/p3_s4_loop_pegasus.sh:323-355` の `<root>/<name>` から scratch の `<name>-src>` へのコピーと、`tools/pegasus/submit_floor.sh:490-512` の payload 作成である。S8b はさらに `s8b_floor_campaign.py:3138-3266` で payload を job-local root へ複製する。
- 成果物影響: qsub または preflight より前で止まり、certified 選択は発生せず、A-6 report は更新されず、新しい submission receipt・台帳参照も作られない。
- scope: shell 2 本と job contract test の変更範囲内で修正可能。ただし login 側供給手順と `tools/pegasus/README.md` は現プランの scope 外で、裁定パッケージ候補。

2. S8b private verifier の pin 出所と import

- 判定: **refuted**
- 根拠 file:line: `_verify_pristine_floor_dependency_sources` は `expected_pins=None` のとき `_floor_third_party_policy_pins(repo_root)` を呼ぶ (`s8b_floor_campaign.py:2624-2635`)。その pin は `tools/pegasus/policy.json` の共有 `third_party_sources` 由来 (`s8b_floor_campaign.py:2281-2361`)。`fetch_third_party.py` も同じ `silo_ladder_rung1.third_party_policy` を使う (`fetch_third_party.py:52-90`)。
- 再現または反例の具体形: hydrate 元と verifier は同じ 3 pin を読むため、正しく変換した clone なら pin 集合の差で全 cell が落ちることはない。verifier は base と各 source が repo 外であることも検査する (`s8b_floor_campaign.py:2606-2614,2660-2668`)。S8b の production import 群には A2 module への逆 import がなく (`s8b_floor_campaign.py:90-164`)、提案された依存は一方向である。
- 成果物影響: pin 集合または循環 import による一律 preflight 拒否は生じず、成果物の値・受理集合・参照は変わらない。
- scope: scope 内。実装時は verifier の運用失敗を `CertificationError` に変換すること。固定引数の誤実装を示す `ValueError` まで科学的な拒否へ隠さない方がよい。

3. dependency receipt の観測時点

- 判定: **refuted**
- 根拠 file:line: observer が必要とするのは Git HEAD と `config.h` (`buildcache.py:938-984`)。`prepare_masstree_fetchcontent` は configure 後に `masstree_build` target を完走してから返る (`buildcache.py:2009-2085`)。同 target は `config.h` と `libkohler_masstree_json.a` を output とする (`external/ccbench/cmake/ThirdParty.cmake:57-78`)。
- 再現または反例の具体形: プラン順の「prebuild成功 → condition configure完了 → observer」なら、observer 呼出し前に `config.h` が存在する。archive も prebuild target が作るが、この2-key receipt 自体は archiveを読まない。
- 成果物影響: 計画した時点で receipt 生成が全 cell 共通に失敗することはなく、buildcache は同じ receipt を build 後に再観測できる (`buildcache.py:2793-2815`)。
- scope: scope 内。時点変更は不要。

4. F808 の configure と condition gate の全 configure 被覆

- 判定: **refuted**
- 根拠 file:line: F808 の `configure-failed` は `_configure_compile_commands` の CMake 実行から発生する (`condition_meaning_gate.py:1643-1675`)、失敗情報が供給 arm に運ばれる (`:1804-1902,2498-2566`)、A2 が `macro:arm:reason` として拒否する (`paper_story_a2_certification.py:687-698`)。
- 再現または反例の具体形: `capture_define_inputs.configure_args` は `_configure_compile_commands` の全呼出しで argv に展開される (`condition_meaning_gate.py:1654-1670`)。供給 arm の requested/control configure と、conditional runtime meaning の configure は同じ captured input を使う。これとは別に、A2 の prebuild は capture 前にある (`paper_story_a2_certification.py:608-622`)。プランの2変更面で network に触れる configure を覆っており、未被覆の3つ目は見つからない。
- 成果物影響: 両配線が正しければ F808 と同じ理由による `indeterminate` は解消対象になる。追加の condition configure 欠落による空 cells/report は生じない。
- scope: scope 内。

5. qsub env key による過去 receipt の再受理

- 判定: **real**
- 根拠 file:line: submission validator は `set(variables) == _qsub_environment_keys(policy)` を要求する (`paper_story_a2_certification.py:1275-1294`)。この validator は acquisition/collect (`:1684-1749,4639-4647`)、record (`:1799-1809`)、finish-group (`:1931-1937`)、full/partial raw finalize (`:3688-3698,3738-3747`) で再実行される。
- 再現または反例の具体形: 新 key を持たない既存 v4 submission receipt を現行 validatorへ渡すと exact key 集合で拒否される。ただし今回の policy hash と job body bytes も同時に変わるため、旧 attempt は既に `protocol_sha256` または `job_body_sha256` でも拒否される (`:1209-1232`)。これは新しい単独の historical artifact 破壊ではない。
- `-v` の具体形: mapping は引き続き argv 1 tokenなので `len(argv) == 18` は維持できる。submitter は `-v "$variable_arg"` と引用している (`submit_paper_story_a2_certification.sh:258-263`)。空白は shell 分割されず、`,` と `=` は mapping 文法と衝突するため計画どおり拒否が必要。
- 成果物影響: 既存の凍結 artifact bytes は変わらないが、旧 receipt を現行 collect で再 materialize する受理集合は狭まる。
- scope: scope 内。受理を緩めず、D1693 の旧 protocol 非一致注記に「旧 submission receipt も現行 exact env 契約では再受理しない」と追記すべき。

6. job-local copy の Git/verifier 機構

- 判定: **refuted**
- 根拠 file:line: S8b は `shutil.copytree(..., symlinks=True)` で Git tree 全体をコピーする (`s8b_floor_campaign.py:3247-3255`)。verifier はコピー後 root が Git top-level と一致すること、HEAD、tracked/untracked/ignored clean を検査する (`:2678-2788`)。
- 再現または反例の具体形: 通常 clone の `.git` directoryを含む `<name>-src` を `cp -a` すれば Git metadataも保持され、`rev-parse --show-toplevel --verify HEAD` の検査を通せる。hydrate も ignored file を拒否している (`fetch_third_party.py:648-677`)。copy先 `/scr/...` は `repo_root=POLICY_PATH.parents[2]` の外なので repo外検査にも適合する。
- 成果物影響: `.git` がコピーされないことや repo内判定による一律拒否は生じず、certified/report/台帳値は変わらない。
- scope: scope 内。

7. 3依存の実サイズ、scratch容量、copy所要時間

- 判定: **未確定**
- 根拠 file:line: 現 job は `/scr/${USER}/paper-story-a2-certification/<jobid>` を作り、既に dependency prefix を `cp -a` する (`paper_story_a2_certification.sh:281-291`)。policy walltimeは job body上で A2が6時間 (`:2-6`)。プランには3 Git treeのdisk bytes、`/scr`空き容量、copy elapsedの実測値がない (`s2-plan.md:329-334`)。
- 再現または反例の具体形: 指定された worktree外読取り禁止により、永続 cacheへの `du` と `/scr` の `df` は実施していない。repo内の過去記録は hydrate の memory peakを示すだけで、disk footprintやcopy時間の反例にはならない。
- 成果物影響: 容量または時間不足なら全 cell 前に driver_rc=2となり report は `indeterminate` になるが、現資料だけではその発生を認定できない。
- scope: runtime mechanismの変更提案はしない。採用前の実測証拠が未確定であることだけを残す。

8. 必須 CLI 引数の呼び手漏れ

- 判定: **real**
- 根拠 file:line: production CLI caller は job body 1箇所 (`paper_story_a2_certification.sh:303-310`)、Python wrapper は `_run_workload_command` (`paper_story_a2_certification.py:4703-4709`)。直接関数 caller は `test_paper_story_a2_certification.py:4082,4103,4280,4427,4548` の5箇所。
- 再現または反例の具体形: プランの更新範囲 `s2-plan.md:143` は `:4048-4438` までで、`:4548` の source-role rejection testを漏らす。必須引数だけ追加すると `TypeError`、引数だけ渡しても verifierを差し替えなければ intended role predicateより前で落ちる。`run-workload` 文字列の実 production callerはjob bodyだけである。live docs に投入コマンドはなく、`output/insights/2026-08-27_t1647-a2-cert-fanout/README.md:85` は既に古い拒否実証の歴史記録で更新対象ではない。
- 成果物影響: production成果物の値は直接変えないが、焦点 testが赤になり、実装成果物を受理できない。
- scope: scope 内。test範囲を少なくとも `:4559` まで広げる必要がある。

9. 実効層の scope 閉包

- 判定: **real**
- 根拠 file:line: プランは submitter、job body、job contract testを追加した (`s2-plan.md:118-148`) が、標準 hydrate rootから認証入力を作る層と、そのoperator手順を含めていない。さらに D1693 が要求する旧結果と現行 protocol hashの不一致注記について具体的な出力先がアンカーされていない。
- 再現または反例の具体形: 現プランだけを実装しても、operatorが持つ実在入力は `<hydrate>/<name>`、CLIが要求する入力は `<root>/<name>-src` のままで接続されない。既存 `p3_s4_loop_pegasus.sh:323-355` と同様に job bodyで綴りを変換すれば既存層内で閉じられる。
- 成果物影響: producer欠落のままでは新しい certified 選択・report・receipt参照は一件も作れず、実装済みに見えても発火不能のままになる。
- scope: job body変換は現scope内。operator契約を記す `tools/pegasus/README.md` とD1693注記の出力先は現プラン外で、裁定パッケージ候補。

## 親 brief への反証

- `s1-brief.md:53-66` の変更面表は不完全。実 production入口は submitterからqsub envを作り (`submit_paper_story_a2_certification.sh:238-263`)、job bodyが `run-workload` を呼ぶ (`paper_story_a2_certification.sh:303-310`)。shell 2本とjob contract testは必須変更面であり、プラン自身も `s2-plan.md:1-4` でこれを認めている。
- `s1-brief.md:103-105` の「capture が F808 の実際の落下点」は歴史的F808の説明としては正しいが、現行mainの最初の落下点へ一般化すると偽。現行コードでは network依存の prebuildが captureより先に走る (`paper_story_a2_certification.py:608-622`)。
- 「`run_campaign` は既に5引数を持つ」は反証されなかった。定義は `loop.py:240-252`、pipelineへの転送は `:562-571` と `pipeline.py:1298-1307` に実在する。
- F808の「`run_campaign` に引数がない」が現行mainでは偽という訂正も正しい。

## プランへの推奨

- 最優先で入力契約を変更する。`--third-party-source-root` は実在する hydrate出力 `<root>/<name>` を受け、job bodyが `<scratch>/fetchcontent/<name>-src` へ `cp -a` する形を推奨する。認証buildが使う実効綴りは引き続き `<base>/<name>-src` で一意に保てる。
- `<name>-src` をlogin入力にも要求し続けるなら、`submit_floor.sh:490-512` 相当の自動producerをsubmitterへ入れ、いつ誰が作るかをscopeへ明記する。人手のrename/copyを発火条件にしない。
- `test_paper_story_a2_certification.py:4548` のcallerも更新し、verifierとobserverが intended source-role predicateを遮蔽しないfixtureにする。
- `tools/pegasus/README.md` に hydrate `.source_root` から認証submitterへの実行形を追加し、D1693の注記先と旧submission receiptの再受理不可を明示する。
- S8b verifier、receipt観測時点、condition gateの2配線、qsub argv長は計画どおりでよい。
- disk容量とcopy時間は本資料では未確定。推測値を採否根拠にしない。

## 総括

最も重い所見は、認証CLIが要求する `<name>-src` 入力のproducer欠落である。
既存helperが生成するのは `<name>` であり、計画したsubmitterとjob bodyは既存の `<name>-src` を再コピーするだけである。
S8bとP3には自動変換の実在例があるため、同じ変換をjob bodyへ配線すれば新しい一般機構なしで閉じられる。
verifierのpin、receipt時点、condition configureの被覆は成立している。
加えて test caller 1箇所とoperator文書層がscopeから漏れている。