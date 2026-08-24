# [T-139] 段1 brief — CC 自動合成の投入経路

1. scope は、既存 `orchestrator/preregistration/approval_payload.py` と `orchestrator/submission_gate/` を再利用し、manifest・effective approval resolver・writer・semantic validator・conformance vectors の結線を実装することに限る。
2. worklog entry 874 の [T-139] 択 (a) を最終裁定として採り、旧 ruling 控え単体の NO-GO は採らない。
3. D574/D597/D626 が正本であり、D574 決定(3)の raw `CMakeCache.txt` 再 parse、申告値の reject-only 性、決定(4)の approval payload 側 vector trust edgeを不変条件とする。
4. D292 の `pilot_submission = forbidden` / `main_submission = forbidden`、計算資源投入、pilot/main 実走、解除 decision の先行 land は scope 外で、1 bit も動かさない。
5. `submit_pilot`、PBS driver、collector、Pegasus registry、D264 の4名前 export は本 scope の完成条件かを段2/3で再検証するが、明示裁定なしに投入可能 API を開かない。
6. `orchestrator/tests/test_spool_fold.py` と canonical worklog entry 874 の [T-139] 本文/digest 面は no-touch とする。
7. 起動時に Claude 7件、Codex 5件、30 worktree、38 local branch、残 handoff 8件を照合した。対象候補と重なる他 branch は known-violation wave の `test_spool_fold.py` だけで、所有を分離した。
8. 既存 conformance index は `orchestrator/tests/fixtures/t338_submission_gate/conformance/index-v1.json`、42 vectors（正例1・拒否/API 41）で、現状は test 自身の digest だけを持ち外部 trust edge が無い。
9. 現行 `ApprovedManifest` は D282 exact 6 role固定で vector authorityを持たず、`_writer._assert_vector_authority()` は構造的に常時拒否する。D626当時の発火artifact不在を entry 874 の実装可が解消するかが攻撃対象である。
10. durable な vector-bearing manifest / approval payload は未発行であり、既存 index は live test asset、D282/D574/D626 は独立 trust roots / 歴史記録として分類する。凍結済み bytes は変更しない。
11. (P1) provisional: 新しい authority は module-private token で seal し、`base_approval_fold_commit` と `approval_fold_commit` を二段に分け、D282 loaderを二重実行せず下流へ渡す。段3の攻撃対象とする。
12. (P2) provisional: manifest自身の index pin、source-only自己pin、caller申告を受理根拠にせず、外部 pin された approval payloadから index三つ組を得て manifest宣言と照合する。外部 pin の具体的な anchor/commit順序は段2/3で攻撃する。
13. (P3) provisional: writer は既存 `_publish_receipt(*, repository_root, raw_bytes, binding)` の caller-selected path禁止・create-only publicationを保ち、sealed bindingが運ぶ一度解決済み authorityを再検査してから同一 bytesを publishする。
14. producer write-path は現行の固定 receipt namespace `output/receipts/t139/<study>--<series>--<stage>.json` だけを維持する。manifest/payload/vectorは create-only runtime出力にせず、versioned tracked artifactとして扱う。
15. 成果物は、外部 pin済み manifest/payload authority、resolverとbindingへの配線、writerの恒常拒否解消、既存 semantic validatorの独立 raw再読維持、正例1本以上と各 trust-edge 負例、既存42 vectorsの実行可能性・digest閉包である。
16. DW-G05: 実装しない場合、semantic正例が通っても writer は `vector_authority_unavailable` で常時拒否し、受領証を正規 namespaceへ発行できないため、RF studyの材料レポート/試行台帳へ到達する受理済み証拠が0件のままになる。
17. 並列分割は plan/consult をread-onlyで行い、段5は approval/manifest/resolver と writer/vector/tests のfile所有が素集合になる場合だけ複数authorへ分ける。重複があれば単一authorへ戻す。
18. 性能測定・本走は行わない。焦点テスト・変異・受入は `tools/run_tests.py` / dev-wave acceptance 経路だけで実行する。
