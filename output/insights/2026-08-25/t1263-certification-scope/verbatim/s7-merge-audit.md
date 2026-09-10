## main 側の変更内容

- `_REAL_REPO_SERIAL_NODES_GOLDEN` は変更していない。main 版では基準と同じ 69 要素である。
- 別集合 `_S8C_PREDICATE_SNAPSHOT_NODES_GOLDEN` から次の 2 件を削除している。基準版 `test_real_repo_serialization.py:136-137`、削除後は main 版 `test_real_repo_serialization.py:132-136`。

  - `test_current_repository_c12_registry_reports_unwired_allocation_consumer`
  - `test_current_repository_c12_allocation_binding_helper_reports_unwired_consumer`

- これに合わせ、S8C の収集 item 固定件数を 5 から 3 へ変更している。基準版 `test_real_repo_serialization.py:1064-1066`、main 版 `test_real_repo_serialization.py:1062-1064`。
- main 側の `orchestrator/tests/conftest.py` は基準から変更されていない。`git diff` は空で、`REAL_REPO_SERIAL_NODES` は 69 要素のままである。

## wave 側の変更内容

- `_REAL_REPO_SERIAL_NODES_GOLDEN` に指定の 2 node を追加している。wave 版 `test_real_repo_serialization.py:107-108`。69 要素から 71 要素になり、重複はない。
- 同じ 2 文字列を `REAL_REPO_SERIAL_NODES` にも追加している。wave 版 `conftest.py:414-415`。こちらも 71 要素で重複はない。
- S8C の集合と固定件数は変更していない。wave 版 `test_real_repo_serialization.py:134-140,1066-1068` では従来の 5 件である。

## 合成結果の判定

**安全。**

実変更範囲は重ならない。ゼロ文脈差分では、wave は基準行 106 の直後への挿入だけであり、main は基準行 136-137 の削除と基準行 1064、1066 の変更である。同じ基準行を双方が編集していない。

合成後は次の状態になる。

- `_REAL_REPO_SERIAL_NODES_GOLDEN` は wave の 2 件を含む 71 要素。main はこの集合を変更していない。
- `_S8C_PREDICATE_SNAPSHOT_NODES_GOLDEN` は main の意図どおり 3 要素。削除対象は `test_s8c_preregistration_predicates.py` の node であり、wave が追加した `test_codex_reasoning_ab.py` の 2 node とは別集合かつ別 node である。
- `conftest.REAL_REPO_SERIAL_NODES` も wave の 2 件を含む 71 要素。main は conftest を変更していないため、完全一致は維持される。

変更対象に関係する検査は次のとおり。

- S8C の集合完全一致: main 版 `test_real_repo_serialization.py:1054-1060`。
- S8C の生 item 数が厳密に 3 件であること: main 版 `test_real_repo_serialization.py:1062-1064`。集合比較と生件数比較の組み合わせにより、欠落、余分、収集重複を検出する。
- real-repo golden と conftest の完全一致: wave 版 `test_real_repo_serialization.py:1071-1077`。合成後も双方が同じ 71 要素なので成立する。
- `benchmark_snapshots` を含む共有 fixture consumer 閉包: wave 版 `test_real_repo_serialization.py:911-940`。golden に含まれる consumer を seed として、同じ共有 fixture の未登録 consumer がないことを検査する。今回の 2 件追加はこの閉包を満たす方向の変更である。
- collection report の nodeid 重複禁止: wave 版 `test_real_repo_serialization.py:1136-1139`。
- 各 golden node の収集存在、全 instance の marker 数一致: wave 版 `test_real_repo_serialization.py:1142-1176`。
- marker 自体の重複禁止: wave 版 `test_real_repo_serialization.py:846-875` で、1 node 当たり最大 1 個を要求する。
- 実行順序: wave 版 `test_real_repo_serialization.py:1002-1043`。検査対象は 2 priority node の前後関係と 4 writer の barrier 後配置だけで、新規 2 node はいずれにも含まれない。`_REAL_REPO_SERIAL_NODES_GOLDEN` 自体は `frozenset` なので literal 順序には意味がない。

なお、real-repo golden 自体に固定要素数 assertion はない。また `frozenset` と `set` による一致検査は literal 内の同一文字列重複を単独では検出しない。ただし今回の 3 版を静的に数えた結果、real-repo golden と conftest は各版とも重複 0 件で、wave 合成後も各 71 要素で一致する。

## 残る懸念

無し。意味的な union 固有の不整合は見つからなかった。指示どおり pytest は実行しておらず、実 collection の確認は親の受入実測に委ねる。

## 総括

- main の削除は S8C の別集合 2 件、wave の追加は real-repo 集合 2 件で、変更行と意味領域の双方が独立している。
- 合成後は S8C が 3 件、real-repo golden と conftest がともに重複なしの 71 件になる。
- 完全一致、fixture 閉包、収集重複、marker 数、相対実行順序の各検査とも矛盾しない。
- よって、この自動合成は意味的に安全と判定する。