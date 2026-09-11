## 総括

**real／must-fix：0件。** 指定baseからのworking diff、新規helper・JSON・manual probeを静的レビューしました。実走成功・closedは主張しません。

- **refuted：任意差分の許容・旧clean拒否の解除。** `paper_story_a1_source.py:46`でcanonical起点＋固定patchから独立期待treeを生成し、`pipeline.py:1095`で各build直前にroot・HEAD・treeを検査。契約なしのtracked-clean検査は維持されています。
- **refuted：stock偽装・consumer取り残し。** `paper_story_a1_paired.py:5170`でpatched admissionの`tracked_clean=False`・source token・genomeを検査し、`:4974`で`-S`との一致と追加4定義の完全一致を要求。`:7092`以降では関門・campaign・初回collectionが同じmaterializer context内です。
- **refuted：T2514の全record保存喪失・既存負例の弱化。** `paper_story_a1_paired.py:6830`の全arm評価、`:6899`の全拒否record保存は維持。テスト差分に負例の反転・skip・削除は見当たりません。旧policy／prereg／patchのSHA-256も追補と一致しました。
- **未確認：F580／F855の実機解消、M1〜M8の検出感度。** `paper_story_a1_source.py:88`の依存検査・prebuildと、`paper_story_a1_paired.py:6832`の引数供給は確認しましたが、実依存で警告なく成立する証拠は未取得です。closedには関連テスト、変異検査、`manual_probes/test_t2397_a1_source.py:16`の3 workload・全6 armの関門／trace・perf build／verify実走が必要です。

最小fix：現時点で要求なし。編集・commit・submit・pytestは行っていません。