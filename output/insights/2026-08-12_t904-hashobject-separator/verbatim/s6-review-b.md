静的レビューのみ。Web 検索・pytest 実走は行っていない。dev-wave の DW-M03/DW-G05 契約で判定した。

### BLOCKER — `--stdin` テストは fail-open の受理差を検出していない

[orchestrator/tests/test_codex_reasoning_ab.py:1448](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/orchestrator/tests/test_codex_reasoning_ab.py:1448)、[tools/codex_reasoning_ab.py:1285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/tools/codex_reasoning_ab.py:1285)

テストは `hash-object -w` で blob を unreachable にするため、旧実装でも先行する `git fsck --unreachable` が generic reason を出し、`verify_snapshot` は reject のままである。変わるのは専用 reason の有無だけで、DW-M03 が禁じる「診断文字列だけの赤」に該当する。さらに有効 option 名の clean 相がなく、裁定の「有効 option 名の二相被覆」に届いていない。

commit message 8–9 行目の「有効 option 名では fail-open」は過剰一般化である。fail-open になるのは、ファイル blob が既存 HEAD 等から reachable で、stdin の OID が存在しない場合など、先行 gate に reject されない条件下に限る。

成果物影響: このままでは mutation ledger が A1 を `KILLED` と誤記し、レポートが「fail-open を二相で固定」と主張する一方、その受理集合を検査していないため certified 証拠が成立しない。

### MAJOR — `aggregate` / `verify` replay 経路は通常の全走でも閉じない

[orchestrator/tests/growth_test_holds.py:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/orchestrator/tests/growth_test_holds.py:65)、[orchestrator/tests/conftest.py:365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/orchestrator/tests/conftest.py:365)、[orchestrator/tests/test_codex_reasoning_ab.py:2487](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/orchestrator/tests/test_codex_reasoning_ab.py:2487)

replay の統合テストは growth hold 登録済みで、明示 opt-in がなければ `test_codex_reasoning_ab.py` 全体走でも受入全走でも skip される。実装子は 0 node 実走であり、段 3 lens B の B2 は未閉鎖である。

成果物影響: replay の `valid`、`RC_AGGREGATE`、failure reference、そこから生成されるレポート・台帳の受理結果が未検証のまま残る。

### MAJOR — leading-dash symlink の scope 外裁定が durable 記録にない

[s4-adjudication.md:21](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t904-hashobject-sep/s4-adjudication.md:21)

A2 は real・scope 外・段7で裁定パッケージ化と決まっているが、現 commit と repository 内の恒久記録には、custom `spec=` で外部 target bytes を参照した symlink が pass しうる事実がない。段7で insight/backlog または裁定パッケージへ必ず移す必要がある。

成果物影響: 漏れると T-904 が leading-dash 全体を閉じたように参照され、将来 custom spec の oracle が外部可変 bytes を含んだまま valid となり、certified 選択・レポート・台帳を誤って成立させ得る。

### MINOR — mutation collection の「meta-test」は実 node を確認しない

[orchestrator/tests/test_mutation_harness.py:354](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/orchestrator/tests/test_mutation_harness.py:354)、[s5-author.md:43](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t904-hashobject-sep/s5-author.md:43)

指定された meta-test は synthetic repo の不存在 node を harness が拒否することだけを検査し、T-904 の実 nodeid を収集しない。関数名との静的一致は正しいが、実 spec による collection preflight は未確認である。

成果物影響: nodeid/期待集合に不整合があれば mutation matrix が台帳生成前に停止し、certified 受入証拠とレポート参照が欠落する。

### NIT — 新設 node の時間評価は代理測定だけ

[s4-adjudication.md:30](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t904-hashobject-sep/s4-adjudication.md:30)

正確な影響は collection **+2 node**。両方とも固定サイズ `tmp_path` なので growth hold・real-repo serialization 登録外という実装子の静的判断は正しい。marker がないため通常の xdist pool に入り、並列度自体は変えない。ただし 0.16 秒は隣接 1 node の値で、新設 2 nodeは closure を計3回呼ぶため、実時間は未測定であり「無視できる」は未確認。

成果物影響: certified 値・受理集合は直接変わらず、受入所要見積りと timeout 時のレポート／台帳生成可否だけが不確実になる。

commit message の残る重点主張は整合している。未知 option の rc=129、通常名の OID 同一は Git 2.34.1 で別の通常 path でも確認できた。built-in spec の untracked は固定 prefix 付きで、production caller は `spec=` を渡さないため「production 経路には到達しない」もコード上正しい。

## 総括

- コード差分自体は裁定範囲を超えていない。
- A1 の fail-open 二相テストと変異証拠は裁定未達で BLOCKER。
- B2 replay は growth hold により通常受入では閉じない。
- A2 symlink は段7の恒久記録が必須。
- 新設 node は +2、registry/並列分類は正しいが実時間は未確認。