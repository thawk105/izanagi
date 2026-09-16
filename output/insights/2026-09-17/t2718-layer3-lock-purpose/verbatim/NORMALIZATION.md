# 逐語 file の可逆最小正規化 (DW-S07、`git diff --check` 抵触の行末空白)

規則: 各行の行末に連続する空白 (U+0020 / U+0009) を除去した。可視文字・改行数は不変。
元 bytes は親の job dir (`wave-t2718/`) の同名 file に保全。復元は下表の original_sha256 に対する照合で行う。

| file | original_sha256 | original_bytes | normalized_sha256 | normalized_bytes | 除去した行数 |
|---|---|---|---|---|---|
| verbatim/s2-plan.md | 46ee7833c1849656a5214c586f6324cc89bd6aef5197f69bd5cc3999f7388def | 15836 | cd062abf170f51c59dd6c3dcac0a1b1b1b78272888c8c9ea57d054036c79c78d | 15828 | 4 |
| verbatim/s3-a.md | 40dc36d5714643379f608a824df066741358b0c39527275d0bf0fb85e180d03e | 11408 | 1d783fdd462f20a2bf7ef6ec2542ec1172a02ed7fa7904c29e1be9cfa70fd0e3 | 11396 | 6 |
| verbatim/s5-author.md | 61059f3be7b6abac3798f0e8fb39a9073ee0930727eefa091d78a7fbd808a0ba | 5953 | bc3bd7077a0a02d91273651f3d2ff263047803a3bb3bb118abc6c79ca598a498 | 5951 | 1 |
| verbatim/s6-b.md | e6d3656e2aefbede41976c41c4bc21a85681873cf4db4a894d76eb7be098ce6e | 10242 | 636f54af5feecceba99cb6e721454fa9dc96003d177e72e0da1a8f2ace52eeff | 10236 | 3 |
