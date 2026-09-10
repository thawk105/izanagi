```text
**所見 1**: S1 の短縮は fixture には効くが、受入 wall が短縮される保証はない。
根拠: orchestrator/tests/test_codex_reasoning_ab.py:350-399、orchestrator/tests/conftest.py:228-244,398-414、tools/run_tests.py:6-8,394-399、orchestrator/tests/test_real_repo_serialization.py:1221-1231、docs/decisions.md:15596-15607。
反例の構成: 標準の `--dist loadgroup` では 17 consumer が `real-repo` の 1 worker に集約され、fixture は 1 worker で 1 回だけ構築される。しかし別 worker の所要が最大なら、fixture を 52 秒から約 5 秒へ縮めても suite wall は不変になる。`--dist load` を使えば逆に worker ごとの重複構築も起きる。なお現行 runner の既定上限は 48 ではなく 32 (`tools/run_tests.py:60-62,215-229`)。
深刻度: MAJOR
成果物影響 (DW-G05): certified 選択値は変わらないが、受入 wall、lease 窓、改善率の報告値は短縮を保証できず、S1 の wall 効果を過大記録する。

**所見 2**: 現在の測定計画と base-only probe は、D357 準拠の受入改善を証明できない。
根拠: docs/decisions.md:15594-15607、measurements.md:3-5,89-106、brief-addendum-1.md:73-76、brief-addendum-3.md:67-69、tools/codex_reasoning_ab.py:770-811,1650-1724。
反例の構成: 非受入形を前後 1 走だけ行い、198 秒から 158 秒になっても改善とは書けない。3 走ずつ同一条件で測っても、中央値が 100.0 秒から 109.0 秒なら差は 9% なので D357 上は「変化なし」。受入 wall は別形状なので、fixture 3 走だけでは代用できない。さらに現行前値は別 job 並行中で、D357 の「測定中に他 job を走らせない」に反する。git-init で commit-graph が最初から無くなるため、cleanup 呼出しの wiring 変異も既存の不在 assert だけでは殺せず、plan-s1b.md:84-92 の追加検査が必要である。追補 2 の literal manifest pin 懸念自体は refuted で、manifest_sha256 は実行時導出値である。
深刻度: BLOCKER
成果物影響 (DW-G05): certified 選択値は変わらないが、受入 wall の前後値・改善主張・memory 窓を certified report と台帳へ記録できない。

**所見 3**: `_derive_snapshot_from_base` の copytree と固定 artifact 書込みは commit 成長比例ではないが、prepared golden を省略する経路は session corpus 比例である。
根拠: tools/codex_reasoning_ab.py:45-48,93-121,321-369,648-692,1449-1458,1491-1508,1511-1552、orchestrator/tests/test_codex_reasoning_ab.py:362-384。
反例の構成: `BASE_COMMIT` と `ARTIFACT_COMMIT` を固定したまま root に 100 commit を追加し、fixture と同じく `prepared_golden` を渡せば、base の copytree、固定 6 artifact の `git show`、verify の対象集合は増えない。一方、`prepared_golden=None` で呼び、session corpus の rollout ファイルを 10 倍にすると `_find_rollout` の `rglob` が増え、POS の準備費は増える。したがって「derive 全体が定数」とは書けず、「benchmark fixture の prepared 経路では base 部分が定数」と限定すべきである。
深刻度: MAJOR
成果物影響 (DW-G05): output_artifacts 軸を誤って no-hold にすると、session corpus の増加分が受入 floor と hold inventory から漏れる。固定 base の copytree 8.21 秒は残るが、certified 選択値自体は変わらない。

**所見 4**: submodule 約 12.3 秒、または S1 後に約 88%という帰属は成立しない。
根拠: brief-addendum-3.md:11-20、measurements.md:46-67、plan-s1b.md:94-104、tools/codex_reasoning_ab.py:715-762,791-846,1123-1141。
反例の構成: pack 経路では root seal 0.38 秒、submodule seal 合計 2.03 秒、init 0.47 秒であり、全列中央値 5.01 秒に対する submodule は約 41%である。約 88 は root seal の 33.64 秒から 0.38 秒への速度倍率であって、submodule 比率ではない。submodule は外部 pin の固定費なので、再帰 seal の risk を増やして同じ wave で直す根拠にはならない。
深刻度: MAJOR
成果物影響 (DW-G05): scope 外に残る固定 submodule 税約 2 秒と copytree 費を明記しない限り、受入 wall の残余費用を誤記する。certified 選択値は変わらない。

**所見 5**: snapshot 3 node の全 hold は D335 の費用規律と規律 2 の検出力を同時には満たさない。
根拠: brief-addendum-4.md:6-64、docs/decisions.md:14957-14979,15662-15685、orchestrator/tests/test_codex_reasoning_ab.py:1134-1163,1963-1975,3254-3282、tools/codex_reasoning_ab.py:1330-1420,1603-1702。
反例の構成: `test_snapshot_submodule_object_store_is_recursive`、`test_git_answer_object_reinjection_is_rejected`、`test_supervisor_launches_pair_and_scrubs_git_environment` を追加 hold すると、17 consumer 全てが skip され fixture payer は消えるが、clean `verify_snapshot` を呼ぶ唯一の既定 node、forbidden git object reason、pair ordering/GIT 環境 scrub/sandbox 検査を失う。`_one_git_closure_reasons` の refs、remote、reflog、replace refs、alternates、grafts、packed-refs、pseudo ref、commit-graph、fsck の reason 集合も既定走行で守られない。逆に 3 本を全て no-hold にすると、`_prepare_snapshot_case` の session corpus scan は残る。2 本だけ hold しても残り 1 本が module fixture 全体を構築するため payer は下がらない。
深刻度: BLOCKER
成果物影響 (DW-G05): 全 hold なら既定受理集合から closure・reinject・環境防壁が消え、no-hold なら成長比例費用が残る。親の no-hold は運用上は妥当だが、S2 完了とは記録できず、fixture 分割またはユーザー裁定が必要である。

**所見 6**: S1 後に陳腐化する理由文は 16 件ではなく 14 件で、reason・axis・digest の更新範囲が異なる。
根拠: orchestrator/tests/growth_test_holds.py:58-81,304-323、orchestrator/tests/test_growth_test_holds_contract.py:39-41,114-129,256-283,493-565、orchestrator/tests/test_hold_inventory.py:26-166,217-220,319-322,442-499、dev-wave-growth-tests.md:134-136。
反例の構成: `_CLONE_REASON` は 14 行、`_ROLLOUT_REASON` は 2 行なので、S1 で clone を除去しても陳腐化するのは前者だけである。reason だけを訂正しても `growth_test_hold_key_digest` は key だけ、row digest は key/axis/ruling/correctness だけなので動かない。しかし `test_hold_inventory.py` の reason 完全 oracle と human 出力は赤になる。14 件の axis も `commits` から `output_artifacts` へ変えるなら row digest が動き、行追加なら count/key digest/held-module literal も動く。handoff の 29 entry/digest は現行 contract の 30 件 (`test_growth_test_holds_contract.py:39-41`) と既に不一致である。
深刻度: MAJOR
成果物影響 (DW-G05): 更新を省けば台帳理由が実装と食い違い、更新を誤れば contract test、inventory、受理集合の参照が不整合になる。既存 hold を自動解除してはならない。

**所見 7**: S2 の「47 件で全件判定」は全成長比例テストの完了主張にならない。
根拠: brief-addendum-1.md:36-60、dev-wave-growth-tests.md:29-39,86-89,120-125、orchestrator/tests/test_check_docs.py:9017-9025、orchestrator/campaign/s8c_preregistration.py:1124-1145、orchestrator/tests/test_s8c_preregistration_invariant.py:216-226、orchestrator/tests/test_silo_ladder_rung1_evidence.py:1216-1234、orchestrator/tests/test_silo_ladder_rung1_driver.py:927-945。
反例の構成: `test_s8b_ratified_verify.py`、`test_check_docs.py::test_real_repo_clean`、`test_s8c_preregistration_invariant.py`、`test_silo_ladder_rung1_evidence.py`、`test_silo_ladder_rung1_driver.py` は実在するが registry と REAL_REPO_SERIAL_NODES の外にある。check_docs の実 repo 読込、s8c の `rev-list`、silo の実成果物読込は別の成長経路である。silo 2 件は先行 wave が t816 land 後の再測定へ繰り越したため、本 wave で実装せず裁定候補に分離すべきである。
深刻度: MAJOR
成果物影響 (DW-G05): 未登録の growth floor が通常走行に残り、受入 wall と lease 窓は改善せず、hold inventory と「全件判定」の台帳主張が過大になる。今回の実装面へ混ぜず、別裁定パッケージとして起票する。
```

## 総括

NO-GO。BLOCKER は 2 件（D357 未充足、snapshot 3 node の hold 衝突）。
S1 の方式 B は base 部分の候補として妥当だが、fixture 全列と受入 wall は未証明。
S2 は 47 件で閉じず、理由訂正・残余候補・snapshot 検出力の裁定が必要。