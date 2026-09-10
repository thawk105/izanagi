## 所見一覧

### B-1 — `real / major`

`make_packets` は schedule descriptor がない場合、旧来の `len(grouped) != 10` fail-closed 検査を失っています。現行は `tools/codex_reasoning_ab.py:6848` 以降で代替検査を行わず、空・欠落 slot・任意数の packet を生成できます。親commitにはこの拒否が存在しました。既存テストは10 slotのみです。

### B-2 — `refuted / blocker`

Wave C境界の変更件数は次のとおりです。

- `supervise_pair`: 3行。ただし全て補助関数docstring内の旧記述削除
- `_supervise_one`: 0
- `_verify_launch_receipt`: 0
- `collect_run`: 0
- `add_argument`: 0
- `add_parser`: 0

`_replay_manifest` 内の `expected_requested_model=...` も親commitと同一で、許可された越境は再編集されていません。

### B-3 — `refuted / major`

既存assertionの値は維持されています。`test_zero_component_total_only_aggregate_counts_by_arm_and_case` は、旧 `total_count` と `by_arm_case` の値を個別に保持し、新しい `by_axis` のみ追加しています。fake関数の変更は新keyword引数を受けるためのものです。xfail、skip、反転、期待値の緩和はありません。

### B-4 — `refuted / major`

指定grepは汎用名・test node文字列により複数ファイルを出力しましたが、意味上は誤検出です。対象外に `codex_reasoning_ab` のimport、`_aggregate_verified` 呼出し、`make_packets(` 呼出しはありません。その他の `_validate_schedule` は別モジュールの別関数です。DW-G05の機能的consumerゼロは維持されています。

### B-5 — `refuted / blocker`

`not-applicable`、`routing_evidence_status`、`confirmatory-go`、`apparatus_diagnostic` は実装ファイルにも追加diffにも存在しません。変更6・7のscope限定は守られています。

### B-6 — `refuted / major`

`MODEL_ALLOWLIST` は `tools/codex_reasoning_ab.py:3054` で `MODEL` と `"gpt-5.6-luna"` の双方を含みます。`_slot_dimensions` は省略時に `MODEL` を補完するため、POS/NEGのlegacy fixtureは新検査で意図せず拒否されません。`_schedule`、`_aggregate_rows`、replay、packet fixtureを含む6件以上を追跡し、shapeの整合性を確認しました。

### B-7 — `refuted / blocker`

`git show ... | grep -n "^-.*_LEGACY_\|^-.*sha256"` ではhash関連の汎用検査行だけが出力され、`_LEGACY_*`定数の削除や値変更はありません。`TASK_MANIFEST`と定数群も差分前半から不変です。

## 総括

- commitはコードとテストの2 fileだけを変更しています。
- Wave C所有面、CLI、legacy hash・session値は保全されています。
- 既存のPOS/NEG assertion値も保全されています。
- scope外のcache抑止・routing判定ロジックは追加されていません。
- 唯一の実所見は、schedule descriptorなしの`make_packets`経路で旧slot数拒否が消えたことです。
- pytest・mutationはユーザー指示どおり実行していません。worktreeはcleanです。