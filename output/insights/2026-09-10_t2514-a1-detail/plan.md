## 総括

T-2514はproduction 1ファイル、test 1ファイルの局所変更で実装可能です。保存先は既存の検証済み `raw_root`、すなわち `attempt/jobs/<workload>/raw/` を採用します。静的確認のみ実施し、編集・テスト実行はしていません。

### trusted rootの確認

- [paper_story_a1_paired.py:3482](orchestrator/campaign/paper_story_a1_paired.py:3482) の受領証検証は、attempt・group receipt・workload・PBS観測を照合し、repository外かつ `/scr` 外のrootsを返します。
- [同:2485](orchestrator/campaign/paper_story_a1_paired.py:2485) の `_v3_job_roots` がworkload別の `raw_root` を構成します。handoff記載の `_v3_workload_paths` は現行コードに存在せず、この関数が該当します。
- [同:6806](orchestrator/campaign/paper_story_a1_paired.py:6806) で取得したtrusted rootsは、[同:6840](orchestrator/campaign/paper_story_a1_paired.py:6840) でCLI rootsとの一致確認後に採用されています。新しい環境変数や保存先検証gateは不要です。

### production変更案

1. [同:6704](orchestrator/campaign/paper_story_a1_paired.py:6704) の関門関数へkeyword引数 `evidence_root: Path | None = None` を追加。[同:6935](orchestrator/campaign/paper_story_a1_paired.py:6935) のproduction呼び出しは必ず `Path(roots["raw_root"])` を渡します。省略時は保存しないことで既存直接呼び出しを維持します。

2. [同:6773](orchestrator/campaign/paper_story_a1_paired.py:6773) のadmission拒否分岐で、現在の拒否本文を先に確定。その後、以下を個別に保存します。

   - `supply_records` 全件
   - `meaning_records` 全件
   - `admission` 1件

   green recordも保存対象です。各recordの `canonical_json().encode("ascii")` をそのまま保存し、ファイル名は `condition-gate-{arm}-{record_digest}.json`、admissionは `condition-gate-admission-{admission_digest}.json` とします。

3. 原子保存helperを関門近傍へ局所追加。[p3_s4_loop.py:379](orchestrator/campaign/p3_s4_loop.py:379) の既存方式を参照し、同一directory内の一意な一時名へ排他的作成、write・flush・file fsync、`os.replace`、directory fsync、一時fileの後始末を行います。同digestの再試行は正常な上書きです。共有化や同moduleからのimportは行いません。

4. digest取得・canonical化・path構築・保存を各recordの `except Exception` 境界に含めます。失敗は `; evidence_write_failures=...` として元本文末尾へ追記し、残るrecordとadmissionの保存を継続。例外の文字列化に依存せず、対象識別子と例外型を記録します。最後は従来どおり `PaperStoryError` を送出します。

既存の `could not run` 分岐、reason codeの順序と重複、`admission-not-granted`、受理判定を維持します。admitted時はcanonical化も保存も呼びません。

### test変更案

[test_paper_story_a1_paired.py:4095](orchestrator/tests/test_paper_story_a1_paired.py:4095) 付近へ回帰テストを追加します。既存テスト本体・期待値は変更しません。

- **全件保存と拒否維持**：異なる値のsupply・meaning計4件とadmissionを用意し、greenを含む全5件のfilenameとcanonical bytesを照合。元拒否本文との完全一致も確認。
- **再試行と原子公開**：同digest再試行、異digest証拠の共存、file fsync → replace → directory fsync、正常終了後の一時file不在を確認。
- **保存失敗**：canonical化、部分write、replace、directory fsyncの失敗を注入。元拒否の保持、末尾追記、後続保存の継続を確認。replace前の失敗では不完全な最終fileを公開しないことも確認。
- **成功経路**：保存helperとcanonical化を呼ぶと失敗するstubで、admitted時に呼ばれないことを確認。`KeyboardInterrupt` などの `BaseException` は伝播を確認。
- **配線**：production呼び出しが検証済み `raw_root` を渡すことを確認。

D1912の回帰例は [test_p3_s4_loop.py:186](orchestrator/tests/test_p3_s4_loop.py:186) を参照できますが、T-2581所有ファイルは変更しません。

依存供給、source根治、attempt-0004、過去artifact、共通gate moduleは対象外です。実走検証は親へ引き継ぎます。