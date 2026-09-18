## 変更点

指定3 fileのみ変更。差分は作業ツリーに残しています。

| file | 旧行 → 新行 | 変更 |
|---|---|---|
| `tools/pegasus/mocc_trace_pilot.sh` | 1534 → 1564–1591 | HYDRATE_PY gateとhydrateへの配線 |
| 同上 | 1684 → 1742–1806 | T1943限定patch適用、touch-set検査、5 artifact生成 |
| 同上 | 2225–2231 → 2348–2357 | verifierへmode別sourceを渡す |
| 同上 | 412・625 → 413–437・651–655 | artifact分類とgeneral漏れ検査 |
| 同上 | 2512・2541・2984–3107 → 2638–2669・3113–3269 | 3引数、実bytes／sidecar照合、5 field binding |
| 同上 | 3164・3261・3346–3352 → 3326・3424–3428・3514–3540 | receipt v2、artifact登録、job-result専用検査 |
| `orchestrator/tests/test_mocc_trace_job_contract.py` | 1514直後 → 1515–1737 | hydrate／patch／verifier配線の3 test追加 |
| 同上 | 2058・2735・4194 → 2282・2960–2963・4455–4458 | 既存fixture変数補完、marker追加 |
| 同上 | 3111–3554 → 3339–3804 | schema改変helperとfinalization fixture更新 |
| 同上 | 3933–3957・4576 → 4184–4217・4840–4856 | 分類とreceipt binding検査 |
| 同上 | 4656直後 → 4936–4951 | digestを再束縛した旧v1の拒否test |
| `orchestrator/tests/test_pegasus_tools.py` | 560・586 → 560・586–589 | hydrate逐語pinとgate順序 |

既存testの削除・改名なし。CHECKER_PY／VERIFIER_PY markerは`grep -c`で各1件。

## 実走

このworktreeで以下を全件実行しました。

```bash
PYTHONPATH=. python3 -c "import sys, pytest; sys.exit(pytest.main(['orchestrator/tests/test_mocc_trace_job_contract.py','-q','-rf']))"
```

**149 passed / 0 failed、18.60秒。failed nodeidなし。**

```bash
PYTHONPATH=. python3 orchestrator/tests/test_pegasus_tools.py
```

**72 passed / 0 failed、3.97秒。failed nodeidなし。**

新規3 testの先行選択走も計3 passed。`git diff --check`成功。

変異は次の形で各nodeidを選択し、各回 **0 passed / 1 failed**。

```bash
PYTHONPATH=. python3 -c "import sys, pytest; sys.exit(pytest.main(['orchestrator/tests/test_mocc_trace_job_contract.py::<下表の関数名>','-q','-rf','--tb=short']))"
```

未実走：PBS実job、実patch適用・build、TRACE=0前処理同一性witness、所有外consumer tests、repo全受入・完了checker・provenance監査。

## 変異の単一理由性

表中のnodeidはすべて`orchestrator/tests/test_mocc_trace_job_contract.py::`配下です。

| 変異 | 赤になったtest::assertion | 単一か |
|---|---|---|
| M1：hydrateをpython3へ戻す | `test_mocc_trace_hydrate_interpreter_gate_selects_and_fails_closed`：1594、`returncode == 0`に対し3 | 抽出実行では単一。全件では別の逐語pinも検出する |
| M2：version条件除去 | 同test：1578、probe argvの`sys.version_info >= (3, 10)`不在 | 単一 |
| M3：rejected追記除去 | 同test：1590、`rejection in failure`不成立 | 単一 |
| M4：実applyコマンド除去 | `test_mocc_trace_instrumentation_patch_block_applies_and_binds`：1677、sourceがpostimageでなくpreimage | 抽出実行では単一 |
| M5：awk検査除去 | 同test：1689、two-filesで`returncode == 2`に対し0 | 抽出実行では単一。pipeline全体ではreceiptも同じnumstatを拒否する |
| M6：mode guard除去 | 同test：1672、generalで`recorded == []`に対しgit呼出3件 | 抽出実行では単一。後段にもgeneralの非空patch値拒否がある |
| M7：verifier sourceをBASEへ戻す | `test_mocc_trace_verifier_source_root_follows_t1943_mode`：1733、期待buildに対しbase | 抽出実行では単一 |
| M8：receipt binding除去 | `test_t1943_receipt_binds_trace_witness_discriminator_and_trace0_absence`：4838、`returncode == 0`に対し2 | **登録理由には絞れない**。field assertionより先にjob-result writerがbinding欠落を拒否 |

M4は構文を維持して実applyコマンドだけ除去しました。M4／M7の実pipelineでは未計装sourceによるverifier拒否もあり得ますが、今回未実測です。登録の取り下げは行っていません。

各変異後に保存した写しから復元し、最後に3 fileすべてのSHA-256一致を確認しました。

## 波及

- `test_hooks.py:3180,3338`のpilot分類は引き続き`dispatch-required`。変更不要。
- finalization fixtureとschema改変helperのcallerは同test file内のみ。既定のv3改変とgeneral v4正例を維持。
- `mocc_trace_pair.py`のv4 exact pin、`mocc_g2_repro_ledger.py`の歴史的v3 pinに変更なし。
- productionのT1943 v1 literalはv2へ置換済み。v1は拒否testだけに残ります。
- verifier／discriminatorの判定規則、rc=3拒否、既存cleanupは変更なし。
- fakeによる検証はshell配線の観測です。hydrate実行失敗時の既存stage=`shell`、実Python旧版の推移import、実buildの成立は今回の新規testでは実証していません。
- receiptのsource digestは適用後とfinalization時の一致記録であり、binary生成元の独立証明ではありません。

## 総括

- **実装済み**：A／B／C全部。全件221 passed、変異8件すべて赤、復元確認済み。
- **未実装**：依頼された3 fileの範囲ではなし。
- **未実走**：PBS実job、実build・同一性witness、親担当の正式変異harness・全受入・監査。wave全体をclosedとはしていません。

`git add / commit / stash / checkout`は実行していません。所有外fileの変更なし。

復元後SHA-256：

```text
ebe744e674464fd2cc7d7faaad01e69acb16b66f800cc9eefc90d4e0c365e3a3  tools/pegasus/mocc_trace_pilot.sh
8b20a59b499c70f35c48d92cd37b6a1c0e3ee332a308cbc31c0c6d3af40b8d08  orchestrator/tests/test_mocc_trace_job_contract.py
7c5cbf934cc3c72a961218ea2cf49a90bb2a6962f9fd518c389dfe9eb3560f04  orchestrator/tests/test_pegasus_tools.py
```