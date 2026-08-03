実装を working tree に残しました。docs・所有外ファイル・Git index・commit・branch は操作していません。

### 対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| 1. overlay 配置換え | closed | ID/path に加え lock SHA・WAL SHA・BUILD_START 件数を照合。同一 bytes の改名・移設も overlay-denied、強い部分一致は mutation 拒否 |
| 2. historicity 自己申告 | closed | ledger の pre-policy commit における exact path＋lock/WAL bytes でのみ歴史性を証明。未知 receiptless は拒否 |
| 3. WAL variant 未束縛 | closed | canonical genome を parse し、`pipeline.variant_id()` で再導出。後続 record も BUILD_START 由来 variant に限定 |
| 4. shallow immutable | closed | record・payload・nested dict/list を再帰 immutable DTO へ射影 |
| 5. registry 二重化 | closed | `materializer_admission.py` を唯一の disposition registry とし、S8b AST view をそこから導出 |
| 6. registry docstring | closed | registry 自身が閉包を担うこと、producer 埋め込みが一律でないこと、silo ladder 例外と理由を明記 |

主な変更は [artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-g1/orchestrator/campaign/artifact_admission.py)、[legacy_admission_overlay_v1.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-g1/orchestrator/campaign/legacy_admission_overlay_v1.json)、[materializer_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-g1/orchestrator/campaign/materializer_admission.py)、[s8b_materialization.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-g1/orchestrator/campaign/s8b_materialization.py) です。

### 所見 1・2 の構文クラス

所見 1で塞いだもの:

- 同一 lock/WAL bytes の別 directory・別 basename への移設
- ID/path を維持した lock/WAL mutation
- lock SHA または WAL SHA が既知値に一致する部分 mutation
- exact hash tuple だが BUILD_START 件数・framing が異なる場合

残るもの:

- ID/path と両 SHA を同時に変え、件数だけ一致する入力は overlay mutation には帰属しません。ただし receiptless なら所見2の historicity gate で拒否されます。
- current policy と canonical receipt を持つ完全な新 artifact は、意図どおり新 schema として評価されます。

所見 2で塞いだもの:

- `build_admission` key 欠落による自己申告 historical 化
- tmp・コピー先・未登録 path の receiptless artifact
- snapshot 後に変更された旧 path の lock/WAL

残るもの:

- pre-policy Git snapshot に存在しない真正な歴史成果物は選択へ通りません。
- `.git` または `git` command を利用できない環境では歴史性を証明できず、fail-closed になります。
- 全歴史 artifact index と read-only 専用 view は本修正では作っていません。

### 所見 4

「immutable 射影」を採用しました。`ImmutableWalRecord` と再帰的な mapping/tuple 射影により、発行後の stage、payload、nested receipt の変更を拒否します。

### テスト・検査

pytest nodeid実行: なし（0件）。

`hostname=pegasus02` のため、AGENTS.md のログインノード規律に従い、所有 test fileを含め pytest は実行していません。したがって緑は主張しません。

実施済み:

- 所有 production/test 6 Python ファイルの `python3 -m py_compile`: 成功
- 所有差分の `git diff --check`: 成功
- pre-policy snapshot と既知歴史 campaign の lock/WAL SHA照合: 一致

未実施:

- `test_artifact_admission.py`、`test_layer3_report.py` の全 nodeid
- registry 関連の所有外テスト
- acceptance/full suite、mutation、build、campaign 実走

テスト期待値は、未知 tmp artifact を歴史扱いしないため Layer 3 fixture を policy-bound に変更し、fake variant 名を独立 literal の canonical ID に置換しました。ledger raw SHA は historicity rule 追加に伴う変更です。

### 直さず報告した項目

- `critic/` の validated-view caller、`guided.py`、autonomous capability、S8a characterization receipt、qualification、mutation harnessなど、指定所有外の所見は未修正です。
- `silo_ladder_rung1.py` は裁定どおり変更せず、registry docstringだけを訂正しました。
- 既存の所有外 working-tree 差分には触れていません。

## 総括

1. overlay membership を配置 identity から artifact bytes/topologyへ移し、移設迂回を閉じました。
2. historicity を成果物の欠落 keyではなく、trusted pre-policy Git snapshotで証明する方式にしました。
3. WAL variantを canonical genome・source identityへ束縛し、validated viewは実際に deep immutableにしました。

既知限界は、snapshot外の真正な歴史成果物が fail-closedになること、Git非搭載環境では歴史性を証明できないこと、pytest・受入・変異が未実測であることです。