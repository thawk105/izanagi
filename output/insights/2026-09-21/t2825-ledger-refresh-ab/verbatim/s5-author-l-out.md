## 実施

既存生成器の `--refresh` で台帳のみ再生成しました。入力4ファイルの SHA256 は一致、生成 rc=0。git add・commit は未実行です。

検算記録: [verify.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2825-ledger/t2825-author-l/verify.md)、[verify.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2825-ledger/t2825-author-l/verify.json)。

## 検算結果

- (a) PASS：凍結426件の集合・値・該当行 bytes が完全一致。
- (b) PASS：指定 `@real-repo` entry は 0.19 秒を保持。
- (c) PASS：schema 正常、24,379→26,605件、全値が有限・非負。
- (d) PASS：T-2724 の8件は入力期待値と一致。shared_base=0.004、active_v2_delegation=190、active_v2_preserves=190、delegated[changed]=190、delegated[missing]=39、rejects_late_hit=44、failed_launch=48、v1_gate=41秒。
- (e) PASS：marker53行等を除いた26,808 node に対し26,587件被覆（99.1756%）、check rc=0。
- (f) PASS：同じ入力の `--refresh --check` は rc=0、台帳 bytes 不変。
- (g) PASS：removed=140件、main collection 内0件、凍結0件。全名前を `removed.txt` に保存。
- (h) PASS：added=2,366件、main collection 外0件。
- (i) PASS：tracked 変更は所有台帳1ファイルのみ。untracked は指定ディレクトリ内のみ。
- (j) PASS：SHA256 は変更前 `1edbb7929a7b341e050fd37ea32f19c93f4d63d8f95afd760018b7cf7ac3273a`、変更後 `27fd84c265373b4039a978ebb074d5b4f71c2d78d935fa76446534881448040f`。

## 親の試走との差

差なし。preserved_frozen=426 / replaced=23813 / added=2366 / removed=140 / excluded_frozen_suite=629。

## 所有外への波及

以下は静的確認であり、実走結果ではありません。

- conftest の台帳読込：schema・値の条件を満たし、3,435,562 bytes は16 MiB制限内。
- `tools/acceptance_shards.py::allocate`：有限・非負の重みとして読める形式を維持。shard 割付と順序は変わり得ます。
- `test_acceptance_schedule_order.py` g5：被覆99.1756%で閾値90%を上回るため通る見込み。
- 同 g6：base key 不在、suffix key=0.19、比較相手=15秒を確認。group・unit の実装は不変で通る見込み。
- `test_update_acceptance_duration_ledger.py` g7e：schema・全値検算が条件を満たすため通る見込み。
- 同 t1574：凍結426件の集合・値が不変で、既存 pin を保持するため通る見込み。
- `test_paper_story_a1_headline.py`：非接触検査は固定 commit 区間が対象で、今回の変更は区間外。

所有外の tracked file 変更はありません。

## 未実走

pytest は一切実行していません。上記テスト、変異試験、受入・A/B性能測定は親側での実行待ちです。

## 総括

台帳の再生成と検算(a)〜(j)を完了しました。
生成件数は親の試走と一致し、凍結426件を完全保持しています。
1走の190秒群・40秒群が新順位を決めますが、builder / waiter の役割や性能改善は断定しません。
成果物は台帳1ファイルと `t2825-author-l/` に揃っています。