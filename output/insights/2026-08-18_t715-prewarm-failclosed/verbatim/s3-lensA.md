## 所見

1. **[Critical] `pytest_collection_finish` は xdist worker でも発火し、現 plan は worker ごとに prewarm する**

   plan は serial seam を `pytest_collection_finish` に置く一方、worker 除外を定めていない（[s2-plan.md:18](/work/1/SFC/tanab/dev-wave-jobs/wave-t715-memo-failclosed/s2-plan.md:18)）。xdist 自身が worker で同 hook を実行してから controller へ IDs を送る（[remote.py:256](/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/remote.py:256)）。controller hook はその後である（[dsession.py:274](/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/dsession.py:274)）。

   全 worker が同じ consumer を collect するため、最初の worker が解決・storeし、他 workerとcontrollerは plan の `cache-preexists-before-prewarm` で赤になる。これは可能性ではなく構造的な順序である。

   修正は、既存の並べ替えを残したまま、prewarm 部分だけを `hasattr(session.config, "workerinput")` なら無効化すること。meta-testには「worker hook → controller hook」の実順序と、worker resolver count 0 を入れる必要がある。

   成果物影響: xdist 全走が collection/session errorになり、certified 選択、レポート、試行台帳のいずれも生成されない。

2. **[Critical] 公開 consumer 経路の fail-closed は、取り除いても全 planned test が緑になりうる**

   plan の動的検査は独立 `_ReceiptMemo.get()` を直接呼び（[s2-plan.md:194](/work/1/SFC/tanab/dev-wave-jobs/wave-t715-memo-failclosed/s2-plan.md:194)）、静的検査は `_resolve_now` の直接 callerだけを見る（同 `:131-135`）。例えば module-level `real_repo_receipt()` に「`get()` の例外を捕まえ `_PRODUCTION_RESOLVE(root=ROOT)` へ戻す」fallbackを置けば、

   - `_resolve_now` caller allowlistは緑
   - private memo の miss testは緑
   - 通常全走はprewarm済みなのでfallback未発火で緑
   - M1〜M10にも該当しない

   となる。公開 gateを実質撤去しても緑になる具体経路であり、F366型である。

   `memo_resolver(root=ROOT)` を未prewarmの差替え singletonへ通し、公開端で同じ structured error、resolver count 0 を要求する必要がある。`_PRODUCTION_RESOLVE`、resolver alias、例外fallbackの各変異も要る。

   成果物影響: prewarm miss時だけlive working treeを再走査し、certified材料の値が走行順で変わる一方、meta-testと全走は緑を主張できる。

3. **[Major] 別 module singleton の危険は real。plan は現行差分を直すが、同一性を機械固定していない**

   現在のconsumerはtop-level importである（[test_s8b_oracle_driver.py:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t715-memo-failclosed/orchestrator/tests/test_s8b_oracle_driver.py:34)、[test_s8b_binding_driftguards.py:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t715-memo-failclosed/orchestrator/tests/test_s8b_binding_driftguards.py:44)）。read-only import probeでも、`real_repo_receipt_memo` と `orchestrator.tests.real_repo_receipt_memo` は異なる module/function objectだった。

   plan `:152` のcanonical import統一は現行事故を閉じる。しかしmeta-test `:187-207` と変異M1〜M10は、conftestと2 consumerが同じsingletonを保持することを検査しない。三者の `receipt_memo is ...`、module key、top-level alias不在を固定し、importを片方だけ戻す変異が要る。

   成果物影響: importが一箇所でも戻ると32関数・35 itemのconsumerがfail-closedで赤になり、レポートと台帳が全欠落する。

4. **[Major] conftestでのeager canonical importは既存経路を壊し、consumerなし走行の1.1倍規則も破りうる**

   conftestはrepo root外から単体importされる既存契約を持ち、`orchestrator` 不在を意図的に許している（[conftest.py:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t715-memo-failclosed/orchestrator/tests/conftest.py:41)）。[test_pytest_failure_digest.py:335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t715-memo-failclosed/orchestrator/tests/test_pytest_failure_digest.py:335) はその実 subprocess 経路を固定する。eager importならconftest読込時点で落ちるが、このfileはplanの波及集合にない。

   またmemo importは実測0.84秒（[s1-measurement.md:31](/work/1/SFC/tanab/dev-wave-jobs/wave-t715-memo-failclosed/s1-measurement.md:31)）。3.9秒のconsumerなし焦点走なら約1.22倍である。planの「追加実解決0回」はimport cost 0を意味しない。

   canonical memoはconsumer検出後にlazy importし、consumerなしhookではmoduleをimportしないことを固定すべきである。

   成果物影響: failure digestの参照経路が壊れて赤の構造化レポートを失い、短い焦点走はwall規則違反でland不能になる。

5. **[Major] prewarmは汚染を一回に閉じると同時に、その結果を全consumerへ配る**

   resolverは先にHEADを捕捉し（[t080_freeze_migration.py:2288](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t715-memo-failclosed/orchestrator/campaign/t080_freeze_migration.py:2288)）、後でlive scanする。列挙対象はtracked working bytes、non-ignored untracked、submodule tracked filesである（[s8b_holdout_freeze.py:367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t715-memo-failclosed/orchestrator/campaign/s8b_holdout_freeze.py:367)）。

   例えばnon-ignoredファイル一個にH1の三軸literalを置けば、`conjunction_hits` が非空となり拒否される（同 `:645-665`）。prewarm後は、その時点の `validation_head`、`held_checks`、refusalsがpickle経由で全workerへ配布される。scan回数は一回になるが、汚染も全nodeへfan-outする。

   なお兄弟worktreeやrepo外job dir自体は直接列挙されない。影響するのは、このworktreeへコピー・stageされた成果物、non-ignored生成物、またはこのsubmodule worktreeのbytesである。

   成果物影響: 一個の生成物で全consumerの`allowed`、refusals、`held_checks`が同時に変わり、certified材料レポートの値と参照HEADが一斉に変わる。

6. **[Major] pickleの型検査は信頼境界上のfail-closedになっていない**

   現行は `pickle.loads` を実行した後に型を見る（[real_repo_receipt_memo.py:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t715-memo-failclosed/orchestrator/tests/real_repo_receipt_memo.py:107)）。pickleは型検査前に任意のreduce処理を実行できる。planのpreexisting-cache拒否は初期注入を防ぐが、controller store後からworker loadまでの決定的な窓で、同一UIDの別session・同一user processが置換できる。

   安全なclosed-schema codecへ替えるか、少なくともこの既存trust holeをscope外のまま許すか段4裁定が要る。単なる`isinstance`強化では直らない。

   成果物影響: forged `ReceiptResolution` が`active-valid`、`validation_head`、refusalsを偽造でき、certified選択とレポートを偽緑化しうる。

7. **[Major] fail-open廃止は、正当なxdist用法を新たに拒否する**

   xdistの`--testrunuid`は任意のidentifierを受理し、hex制約を持たない（[plugin.py:200](/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/plugin.py:200)）。`ci-job-42` は正当だが、planのUID妥当性検査で赤になる。同じUIDを同HEADで再利用すると、`cache-preexists-before-prewarm`でも赤になる。

   またxdistはremote `--tx ssh=...` を正式に持つ（同 `:156-165`）。controllerとworkerが同じ`/tmp`を共有しないため、planが「素の`pytest -n N`」全般を被覆するという主張は成立しない。

   一方、通常cloneやsubmodule未初期化は独立のmemo infrastructure破損ではない。本番resolverが既存どおりinvalid resolutionへ翻訳する（[s8b_oracle_driver.py:116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t715-memo-failclosed/orchestrator/campaign/s8b_oracle_driver.py:116)）。新事実として戻すべきなのはUID値域と非共有cache transportである。

   成果物影響: validなCI/remote-xdist構成がsession赤となり、その環境のレポート・台帳を一切作れなくなる。

8. **[Major] planの1.1倍静的上界は、自身の計算ノード実測で既に反証されている**

   planはlogin nodeの`q=15.3秒`を使う（[s2-plan.md:235](/work/1/SFC/tanab/dev-wave-jobs/wave-t715-memo-failclosed/s2-plan.md:235)）が、計算ノード実測は19.70秒（[m8-q-compute.md:14](/work/1/SFC/tanab/dev-wave-jobs/wave-t715-memo-failclosed/m8-q-compute.md:14)）。保守上界は `173.10 + 19.70 = 192.80秒`、比率約1.114で、閾値190.41秒（[m5-baseline.md:17](/work/1/SFC/tanab/dev-wave-jobs/wave-t715-memo-failclosed/m5-baseline.md:17)）を超える。

   実際にはstarvation削減で速くなる可能性があるが、それは段6実測でしか示せない。さらに保留3件解除後はqが増え、prewarm qとscope外CLI qの重なり方が変わるため、現baselineの結論を一般化できない。

   成果物影響: S4の合格主張が偽になり、lease占有と全waveの試行台帳遅延を過小報告する。

9. **[Major] prewarm失敗時の診断優先順位と伝播が未固定で、F389を再発しうる**

   既存hookには隣接する広い `except Exception: pass` がある（[conftest.py:475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t715-memo-failclosed/orchestrator/tests/conftest.py:475)、同 `:492`）。prewarmをその内側へ置けばstore/lockの原診断が消え、後のconsumerは`cache-missing`だけを報告する。

   またcontroller prewarmは最初のworker collection通知時であり、全workerのcollection一致確認より前である。prewarm errorとcollection mismatchが同時にあると、新gateが既存collection診断を奪う。planのfake hook testは、例外objectの伝播、test body不発火、success state未publishを検査しない。

   成果物影響: レポートの失敗理由と台帳のinfra分類が実原因から`cache-missing`またはinternal errorへ変わる。

10. **[Major] planは確定briefの「worker起動前」を「worker collection後」へ弱めている**

   brief S1/P1はsession開始・worker起動前を要求する（[s1-brief.md:15](/work/1/SFC/tanab/dev-wave-jobs/wave-t715-memo-failclosed/s1-brief.md:15)、同 `:68-73`）。planはこれを「test scheduling前」で十分と読み替える（[s2-plan.md:24](/work/1/SFC/tanab/dev-wave-jobs/wave-t715-memo-failclosed/s2-plan.md:24)）。

   その時点ではworkerのtest module importとcollection side effectは既に完了している。現行memo consumerはtest body内だけだが、その閉包を維持する機械検査と、collection-time writer不在の保証はない。これは段2が単独で変更できるscopeではなく段4裁定事項である。

   成果物影響: collection時のread/writeがprewarm入力を変えれば、全nodeへ配るsnapshotとcertified材料の参照がbrief想定と異なる。

11. **[Major] 親briefのT-813引用は直接証拠でなく、110 nodeもpayer数ではない**

   T-813で実測した汚染bytesは`output/pegasus-dispatch/`（[package.md:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t715-memo-failclosed/output/insights/2026-08-11_t813-acceptance-sharding/package.md:113)）。同pathは`.gitignore:26`でignoredであり、T-080列挙の`--exclude-standard`から外れる。T-813は「並行writerが存在する」証拠ではあるが、「そのbytesがholdout live scanを変えた」直接証拠ではない。

   また110は対象2 fileのungrouped母数で、planが特定した実consumerは32関数・35 item（[s2-plan.md:34](/work/1/SFC/tanab/dev-wave-jobs/wave-t715-memo-failclosed/s2-plan.md:34)）。正しさ結論は変わらないが、blast radiusと性能説明は訂正が要る。

   成果物影響: certified材料の非決定性を支えるproof-chain参照と、レポート記載の影響node数が誤る。

## プランの穴

段4へ進む前の最低条件は次である。

- workerではprewarmしない負例を追加し、実順序を固定する。
- public `memo_resolver` missを通すend-to-end負例とalias fallback変異を追加する。
- conftest・2 consumerのmodule identityをpinし、conftest側はlazy importにする。
- prewarm例外を既存の握り潰しから外し、診断優先順位を決める。
- snapshot時点とpickle transportの信頼境界を裁定する。
- arbitrary `--testrunuid` とremote xdistを支持するか、非対応として明示裁定する。
- S4は計算ノードのpaired実測だけで判定し、保留解除時を再評価条件にする。

## 親 brief の穴

- 「本番resolverの戻りobjectそのものだから受理集合不変」は時点を落としている。正しくは「固定snapshot Xに対して全memo consumerが同じ `R(X)` を観測する」である。
- xdist worker生成前とcollection条件は両立していない。planの弱化を採るならbrief S1/P1を段4で明示訂正する必要がある。
- `memo_receipt=False` は2関数だがparametrize後は3 itemである。単独選択時はprewarmなしだが、通常consumerと同時選択したserial走行では実resolverが一回余分に先行する。
- q、13,565 files、120/110はいずれもHEAD、worktree bytes、file総量、保留状態、worker数に依存する一時点値である。結論を固定できるのは現HEAD・現hold状態でのpaired測定だけである。
- T-813は並行writerの存在証拠としてだけ引用し、T-080 scan汚染の直接実測とは書けない。

## 総括

**NO-GO。段4でplan v2へ差し戻すべきである。**

親が挙げた二危険は、worker hookが **realかつ未閉鎖**、module singletonが **realで実装方針は部分閉鎖、機械固定は未了** である。特にworker hookを直さない限り、xdist全走は構造的に成功しない。

pytestは実行せず、静的検査とread-only import identity probeのみを行った。既存の未コミット3ファイルを含め、workspaceは変更していない。