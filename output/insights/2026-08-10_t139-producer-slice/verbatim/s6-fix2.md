P2 のみ [mutation spec](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer-slice/output/insights/2026-08-10_t139-producer-slice-mutation-spec.json) に追加しました。P1 は指定された単一理由帰属が成立しないため、契約どおり登録していません。

## 総括

- `P1`: candidate anchor は exact-1。ただし定数へ `a14` を足しても、対象テストは `EXPECTED_FIELDS` を明示渡しするため正常終了しました。よって KILLED にならず未登録です。
- `P2`: 登録済み、anchor は exact-1。変異後は承認済み追補から `a01,a04,a05,a08,a09,a12,a13` の7 keyしか取得できず、指定 node の exact-13 assertion が単独で失敗します。
- 既存13件の内容は不変で、検証用 SHA-256 も編集前後で一致しました。
- JSON loader で14件を正常に読み込み、schema は `izanagi-dev-wave-mutation-spec/v1` のままです。
- 登録できなかったものは `P1` の1件です。理由は指定 node を KILL しないためです。