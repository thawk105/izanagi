## 変更前の受理・拒否挙動

正常系の受理集合は維持しています。

- `PEGASUS_LOGIN` / `PEGASUS_SUSPECT`: local-ok 5本のみ ALLOW。残り19本と未登録 `tools/pegasus/**` は DENY。
- local-ok は `dispatch_compute.py`、`fetch_third_party.py`、`submit_certify.sh`、`submit_floor.sh`、`submit_silo_ladder_rung1.sh`。
- `OTHER` / `PEGASUS_COMPUTE`: 登録24本すべて ALLOW。
- 非 Pegasus sanctioned の `tools/run_tests.py` と `tools/check_ai_provenance.py` は維持。
- 保証範囲は現行 parser が実行 target と認識する綴りに限定し、parser の既知の穴は変更していません。

## 変更内容

### `tools/pegasus/admission_registry.json`

[admission_registry.json:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-A/tools/pegasus/admission_registry.json:1)

- 24 entry の4フィールドを機械可読正本へ移設。
- 内訳は `local-ok=5`、`dispatch-required=10`、`unknown=9`。
- 変更前 literal との静的比較で、pathごとの4フィールドに差分なし。
- UTF-8・BOMなし・2-space indent・昇順・末尾1 LF の canonical bytes。

### `tools/pegasus_admission_registry.py`

[pegasus_admission_registry.py:9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-A/tools/pegasus_admission_registry.py:9)

- 公開面を指定された3シンボルに限定。
- [36行目](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-A/tools/pegasus_admission_registry.py:36)で `O_NOFOLLOW` / `O_CLOEXEC`、同一fdの `fstat`、regular-file確認、1 MiB bounded readを実装。
- [62行目](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-A/tools/pegasus_admission_registry.py:62)で duplicate key、schema、path、entry fields、class閉集合、canonical再serializeを検証。
- [103行目](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-A/tools/pegasus_admission_registry.py:103)で全失敗を `AdmissionRegistryError` に正規化。
- exact-24 は要求せず、非空でschema適合する1 entryも受理する設計。

### `hooks/guard_bash.py`

[guard_bash.py:191](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-A/hooks/guard_bash.py:191)

- literal registryをexact-path loader importへ置換。
- `sys.dont_write_bytecode` と `sys.modules` を `finally` で復元。
- loaderの返値を `Mapping`、entryを `Mapping`、classを文字列として最小再検証。
- registry確定と `_SANCTIONED_PATHS` 導出を同じ `try` に配置。
- [226行目](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-A/hooks/guard_bash.py:226)で `SystemExit` を含む `BaseException` を吸収し、空registryと非Pegasus sanctioned 2本へ縮退。
- site-policy importも [74行目](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-A/hooks/guard_bash.py:74)でmodule初期化から `BaseException` を漏らさないようにした。
- `_pegasus_admission_entry` の未登録prefix fallbackは [501行目](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-A/hooks/guard_bash.py:501)で維持。

### `orchestrator/tests/test_hooks.py`

[test_hooks.py:1140](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-A/orchestrator/tests/test_hooks.py:1140)

- `_PEGASUS_EXPECTED_CLASSES` は独立literalのまま維持。
- [1166行目](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-A/orchestrator/tests/test_hooks.py:1166)に24 entry×4フィールドの独立literal goldenを追加。
- [1318行目](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-A/orchestrator/tests/test_hooks.py:1318)から、不在・空・不正JSON・duplicate・型違い・未知class・BOM・schema違反・loader欠落・`SystemExit(0)`・`None`・list・scalar entry・例外を投げるMappingを網羅。
- [1539行目](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-A/orchestrator/tests/test_hooks.py:1539)で各異常時に24 direct commandをLOGIN/SUSPECTで全拒否し、非Pegasus sanctioned 2本を維持。
- [1562行目](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-A/orchestrator/tests/test_hooks.py:1562)に実hook subprocessのrc=2検査を追加。
- [1607行目](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-A/orchestrator/tests/test_hooks.py:1607)でlocal-ok 5本の `./`、内部 `//`、末尾slash、絶対path、interpreter prefixをliteral bitで固定。
- 既存のOTHER/COMPUTE全24本ALLOW検査は [1625行目](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-A/orchestrator/tests/test_hooks.py:1625)に維持。

## 検査結果

- `python3 -m py_compile` を3 Pythonファイルへ実施し、rc=0。pycache出力は `/tmp` に隔離。
- `json.tool` 再serializeとのbyte比較は一致。先頭bytesは `7b 0a 20` でBOMなし。
- 変更前literalとのpath別4フィールド静的比較は差分なし。
- SHA-256やworking-tree hashなどの揮発値は追加していません。
- pytest、`tools/run_tests.py`、`check_docs.py` は実行していません。実行済みnodeidは0件です。
- 新設テスト名を制約するmeta-testは静的検索で見つかりませんでした。既存のファイル全体runnerとsubprocess smokeはありますが、名称・件数を固定していません。
- docs・Markdownは未編集、git操作・commitも行っていません。

## 波及可能性

- 所有外caller: `.claude/settings.json` からのhook subprocess起動。
- 共有fixture: `_load_hook()`、`_REPO`、`_PEGASUS_EXPECTED_CLASSES`、`_PEGASUS_DIRECT_COMMANDS`。
- 既存consumer test: registry schema/class、LOGIN/SUSPECT bit、sanctioned導出、execution inventory、fetch spellings、hook subprocess smoke。
- 将来consumer: B単位の `tools/check_docs.py` exact-path loader import。
- JSONは実行体拡張子でなく、loaderも `tools/pegasus/` 外なので、24本のexecution inventoryを増やしません。
- 親docs未landに起因する想定外findingは静的にはありません。B checkerだけが先行landした場合のdocs投影findingは既知の統合リスクです。

## 総括

- A-1/A-2/A-3を指定4ファイルだけに実装した。
- 正常系の24分類・4フィールド・local-ok 5本・受理集合は不変。
- 異常時は全Pegasus directをDENYし、非Pegasus sanctioned 2本だけを維持する。
- loaderはexact-24を要求せず、hook初期化は`BaseException`を漏らさない。
- 静的構文・canonical形式検査は成功した。
- **実装済み・未実走**であり、pytestの緑は主張しない。
- 残る主リスクは計算ノードでの新旧consumer testと親docs/B単位との統合未確認。