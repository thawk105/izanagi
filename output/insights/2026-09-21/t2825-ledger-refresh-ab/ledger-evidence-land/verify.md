# land refresh 検算

main: d99c556dfa23e446987ef3ccbb5c018986fe10b5
main sha256: `0009601d0a6f182bfe0ce28df36b23f6ffe85a906bae9217b126a21f5f2af97b`
生成件数: 24,812 → 26,605; nodeid_count 一致: True
入力 SHA256: JUnit 3本と collection log の4件すべて一致 (input-check.json)。

- (a) PASS: 生成 sha256 `27fd84c265373b4039a978ebb074d5b4f71c2d78d935fa76446534881448040f` は測定 B と一致。
- (b) 一致
- (c) PASS: 落ちた node 312件、T-2344追加由来 172件 / 追加全433件、その他 140件、凍結prefix 0件。全名前は dropped.txt。
- (d) PASS: 凍結 426件、集合・値一致=True、行bytes一致=True。
- (e) PASS: --refresh --check rc=0、bytes不変=True。
- (f) FAIL (要求の1行に不一致): tracked変更0行、untracked10件 (所有dirのみ)。生成結果が HEAD / index と bytes 一致するため。所有外変更0件。詳細 status.txt。

pytest・性能測定・git add/commit/merge は未実行。
