## 案 (a) の plan (file:line)

**単純な file union 削除は不可。未登録・group 無しの実 repo writer が file 閉包に依存しているため、明示的な shard affinity の補完が先になる。** 以下は実装する場合の条件付き plan。今回は静的確認のみで、書き込み・pytest 実行はしていない。

1. **成分の頂点を node にする。**
   [tools/acceptance_shards.py:325](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2750-shard0-component-granularity/tools/acceptance_shards.py:325) の `_components` で、`f:file` を `n:nodeid` に置換する。
   - group 付き node は `n:nodeid ↔ g:group` を union。
   - `:334` の宣言済み衝突辺による `g:left ↔ g:right` は保持。
   - group・affinity とも無い node は単独成分。
   - `:339` は node の root で集約し、`files` は診断情報として残す。同じ file が複数成分に現れることを許す。

2. **既存 group では表せない affinity を先に補う。**
   後述の `test_repository_candidate_uses_real_s8c_budget_module` は runtime group を変えず、`s8c-predicate-snapshot` への shard affinity を持たせる必要がある。純粋な node 方式なら、`ItemRecord`（`:106`）、record の描画・厳密 parser（`:264–294`）、collection item 変換（`:787` 付近）へ任意の affinity 属性を通す。成分では `n:nodeid ↔ g:affinity` を union する。affinity だけの接続先も頂点・衝突辺の対象に含める。
   これは追加の受入 gate・台帳ではなく、現在 file が暗黙に運んでいる制約の表現変更。ただし**三関数だけの修正では閉じない**。

3. **割付規則は維持する。**
   `allocate`（`:381–461`）の duration lookup、未知 node の 1 秒、group 優先、LPT、決定的 tie-break、K=2/3、空 shard 拒否は保持する。成分 metadata が runtime group と affinity を混同しないようにし、既存 report の再導出・照合も同じ意味へ揃える。今回、重み付け方式そのものは変更しない。

4. **閉包 gate は独立検算を維持する。**
   `assignment_closure_gate`（`:464`）から一律の `file_shards` 検査だけを除く。集合完全一致・重複拒否、group 閉包、衝突辺閉包を残し、affinity node が接続先と同じ shard にあることを直接検算する。`_components` の再呼び出しで自己証明にしない。

5. **既存 test の file 前提を更新する。**
   `test_run_tests_shards.py:728` の file による x/y 接続期待、`:809` 付近の同 file 未知 node を一成分とする期待を変更する。`:890` の closure 負例は、file split と group split を分離する。`test_real_repo_serialization.py:1735` では実 collection の全 resource・fixture consumer の affinity を確認する。

親 simulation の「188 node / 1612 秒」は、この未登録 writer の保護を含まない。安全な候補について割付を再計算する必要がある。

## 順序依存と閉包の検査設計

**最初に調べる単位は、移動する node とその fixture 依存閉包。** module/session fixture の初期化・後始末、module global、process memo、環境変更、共有出力、実 git/submodule 操作をたどる。file 閉包は従来も同一 worker を保証していないため、「今回初めて process が分かれる」とは扱わない。今回増える差は、別 host・別 shard session・別 lock namespace への分離である。

具体的な危険経路がある。

- [test_s8c_preregistration_predicates.py:4765](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2750-shard0-component-granularity/orchestrator/tests/test_s8c_preregistration_predicates.py:4765) の `test_repository_candidate_uses_real_s8c_budget_module` は group 無しで、`REAL_REPO_RESOURCE_NODES` にも無い。
- fixture（`:4736`）は parent write lock 下で `_candidate_commit_with_worktree` を呼ぶ。
- helper（`:4701–4732`）は実 `_ROOT` を cwd に `git add`、`write-tree`、`commit-tree` を実行する。`GIT_INDEX_FILE` の分離は object store の分離ではない。
- [test_real_repo_serialization.py:437](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2750-shard0-component-granularity/orchestrator/tests/test_real_repo_serialization.py:437) の golden は、この consumer が同 file の retained group に依存すると明記している。

検査は次の順で行う。

1. **marker と選択の段階を守る。**
   `conftest.py:2206` の動的 marker 付与 → 全 collection の shard record 確定 → `:2264` の検証 → suffix strip → reorder を保持する。`_validate_real_repo_shard_state` は全 resource が載る**全 collection records**を読む。selected subset に変えると、正常な別 shard 配置まで missing になる。

2. **既存 validator の限界を埋める。**
   `:2139` は正本リスト内だけを見る。上の writer は検出しない。既存の実 collection 閉包 test に、fixture consumer の明示 affinity と意図的 split の拒否を加える。実 repo 全 reader を `REAL_REPO_RESOURCE_NODES` に一括投入する設計にはしない。fixture-owned lock は既に別区分である。

3. **順序・fixture の実験を先に行う。**
   移動候補を単独、同 file の前後 node と組合せ、順序反転、shard を分けた独立 process で実行する。実共有 repo を危険な跨ホスト競合へ故意に晒す負例は使わず、その衝突は隔離した資源と独立 lock namespace で再現する。

4. **検出力は pass 件数だけで判定しない。**
   旧/新で node 集合、parameter ID、skip/xfail と理由、正例・負例の outcome を比較する。同じ single-site 変異を同じ専属 killer が両方式で殺すことを確認する。collection 不備や timeout は KILLED と数えない。

g6（`test_acceptance_schedule_order.py:721`）の歴史的な名前に注意する。現物は「全 real-repo が一つの runtime unit」ではなく、process memo・長寿命 fixture の区分を扱う。`conftest.py:1776` の reorder が各 retained unit 内の相対順序を保つことを、**各 shard の selected subset に対しても**検査する。

また、`test_s8b_oracle_driver.py:964` の T080 base は session 単位の共有を持つ。node 分割で同じ variant の構築が複数 shard に増える可能性があり、module fixture だけの点検では不十分である。

## D711 / D1618 / D1167 との整合

- **D711：裁定改訂が必要。** gate 4 は明記された「file と group の閉包」から「group・明示 affinity・衝突辺の閉包」に変わる。新しい閉包に沿った正常な file split を拒否しない正例も必要。他の五段、全 collection、独立再導出、fallback 禁止は維持する。
- **D1618：全 resource node の affinity を保持する。** 現物は shard record で `real-repo` を確定した後、runtime suffix を一部外す構造である。suffix が無いことを shard affinity 不要の根拠にしてはいけない。
- **D1167：6 辺と runtime group の分離を保持する。** exact golden を先に比較する。完全グラフの辺を一つ消しても連結性は残るため、成分一致だけでは辺削除を検出できない。
- **D358：今回、排他方式を変更しない。** 逐語の単一 worker 方針と、後続 D1618・現行コードの runtime 分割は区別する。全 node の再直列化も、未登録 writer の保護削除も行わない。

## D104 paired 測定設計

採用を検討する場合、順序・閉包検証後に、**同一 tip・同一 collection・同一台帳で旧/新を切り替える一時的な測定 harness**を用意する。恒久的な mode・gate・台帳追加は避ける。

- K=3、48 worker、同じ計算ノード allocation・host 対応で、A-B / B-A を交互に最低3対、各方式 n≥3。自分の他 job は同時に走らせない。
- primary は各全走の **`max(shard wall)`**。各 shard wall、最遅 shard identity、中央値、対内差も併記する。他 wave の近接時刻 n≥20 は外乱の背景分布として使い、無作為化された対照とは呼ばない。
- 機構発火の直接証拠は、実 report の selected/finished と JUnit worker 対応から得る「旧成分から離れて実行された node 数」「複数 shard に分かれた file 数」「各 affinity が同一 host/shard に残った事実」。再計算した予測 loads だけでは足りない。
- P2/P3 用に、最忙 worker の二本の identity・実行順、T080 群の開始/終了、同時実行仕事、base の builder/waiter と構築回数を測定用 trace で観測する。duration の低下だけを競合削減の証明にしない。
- 3対は初期判断用。brief の n≥20 に対する改善主張には精度が不足しうる。D357 の条件を満たさず、差が走間変動から分離できなければ改善と記録しない。効果を示せなければ land しない。

## 変異 matrix 候補

以下は**未実行の事前登録候補**。新設名は既存 test file 内に置く変更検証用 test で、受入 gate の増設ではない。

| single-site 変異 | 専属 killer |
|---|---|
| 同 file の全 node を再 union | 新設 `test_node_components_split_ungrouped_siblings` |
| node→group union を一箇所無効化 | 新設 `test_node_components_preserve_cross_file_group` |
| 衝突辺を一つ削除 | 新設 `test_conflict_edge_literals_are_exact`。既存 independent golden と比較 |
| closure の group 単一 shard 条件を恒真化 | 既存 `test_m3_group_closure_gate_has_independent_killer_and_positive_control` を真の group split 負例へ整理 |
| file 閉包拒否を復活 | 新設 `test_closure_accepts_split_ungrouped_file` |
| candidate writer の affinity 付与を削除 | 新設 `test_candidate_fixture_writer_keeps_snapshot_shard_affinity` |
| affinity 閉包検査を無効化 | 新設 `test_closure_rejects_split_fixture_affinity`。手書き selections で独立検証 |
| resource marker 付与を無効化 | 既存 `test_shard_assignment_preserves_live_xdist_group_components_and_split_control` |
| unit 内 items を逆順にする | 新設 `test_sharded_reorder_preserves_fixture_unit_relative_order` |
| docstring の同義変更 | 等価変異。SURVIVED を期待 |

各 killer は正常対照を持ち、変異 anchor は一箇所に固定する。既存 suite の他 test も赤になる可能性と、専属の期待 node は分けて登録する。

## 案 (b) との比較

案 (b) は allocator と D711 の file 閉包を維持でき、影響を選んだ大 file に限定できる。ただし、**real-repo marker のある関数だけ移す方法では不十分**。fixture 経由の未登録 consumer を取り残すと、上と同じ保護喪失になる。

受理集合を意味的に維持するには、test 本体・parameter・fixture scope・autouse・marker・正負例を保存する必要がある。一方、移動すれば pytest nodeid は変わるため、厳密な nodeid 集合は不変ではない。

consumer の pin にも触れる。`conftest.py:662` の resource 分類、`:668` の process memo、`:712` の receipt consumer、`test_real_repo_serialization.py:52` 以降の golden は file 名を含む。duration key も file 名を含み、移動後は未知値へ落ちうる。source hash pin の全 consumer 閉包は今回未確認であり、「file 分離なら pin 無関係」とは言えない。

(a) は nodeid を保持できるが影響が suite 全体に広がる。(b) は局所化できるが、fixture と identity の移設が必要。どちらも wall 利得の実証は別途必要である。

## 親 (P1)〜(P4) の検査 (成立 / 不成立を明記)

**P1：固定 duration モデルの算術は成立。「実 wall の期待利得が厳密に0」は不成立。**

- 現行 `7523/48 ≈156.7 <240`、変更後 `6089/48 ≈126.9 <240`。したがってモデル内の最大値は両方 `240+66.1=306.1`。
- しかし `max(最長仕事、総和/48)` は一般には下限であり、実 scheduler の makespan の等式ではない。simulation は相方約20秒、runtime group の直列和、開始遅延、fixture 再構築をモデル化していない。D1019 の「最長排他鎖」を単体 node に置換した点も条件付きである。
- 20走の原表の平均負荷は **161〜417秒**。brief の161〜221秒は誤り。ただし20走すべてで平均負荷が最長 node より小さい関係は保たれるため、この訂正だけでは親の主要根拠を倒せない。
- `nsel` は3908〜9004で異なる。20走は同一 tip・同一選択の反復ではない。さらに simulation は166 node 欠落で、全 collection の反実仮想ではない。
- 99 session を原表から再集計すると、最遅 identity は **shard-0：94、shard-1：1、shard-2：4**。直近20走でも19/1/0。「shard-0だけ」「常に最長の一本」への一般化はできない。

したがって「実装しない」は選べるが、閉じる理由は**改善未実証・固定 duration モデルで利得なし**とする。「利得0を実測で証明した」は強すぎる。

**P2：二本・約20秒という観測は成立。割付では消えないという断定は不成立。**

最忙 worker が二本を持つことは原表にあるが、初期 chunk が原因という証拠、相方 identity、実行順は提示資料にない。二本という構造が不変でも、割付・reorder 後の相方は変わりうる。tail が7.5〜20.1秒に変動する事実とも整合する。

ただし、約20秒が全て削れても中央値347.7秒の約5.8%。これだけで採用に十分な改善があるという攻撃も成立しない。

**P3：既存集計表だけでは因果分離できない、は成立。検討余地が全く無い、は不成立。**

現表には host、tip、対象 node の開始時刻、競合仕事の重なりが無い。node duration と総 duration の相関には対象自身が総和に含まれる算術的な相関もあり、因果証拠にできない。

既存 raw report/JUnit に必要な情報があれば、同一 node・tip・host・時間帯で層別し、対象自身を除いた重なり仕事と比較できる。refresh 前後で背景配置が変わった共通 node を追う方法もある。ただし今回の資料だけでは識別条件を確認できず、自然実験としての因果推定は未成立。

D357 自体が競合で duration が膨らむ実測を持つ。「duration 固定」の仮定を疑う根拠はあるが、今回の粒度変更で速くなる証明ではない。

**P4：跨ホスト排他喪失の具体例は成立。ただし必要条件の表現は修正する。**

上記 candidate writer は、実 object 書込み・group 無し・resource リスト外・file affinity 依存までコードで確認できた。別 shard へ配置可能になると host-local lock で閉じられない。

一方、module fixture を使うリスト外 node が全て危険、という攻撃は成立しない。`repository_candidate_commit[module]` の consumer は独自 group を持ち、D1167 の辺を保てば同一 shard に残る。

必要なのは `REAL_REPO_RESOURCE_NODES` 単独の完全性ではなく、**resource node、fixture-owned consumer、明示 affinity を合わせた衝突閉包**である。

## 総括

- **推奨：今回は実装しない。** 利得は未実証で、単純変更には実在する排他退行がある。docs-only の結論は「固定 duration モデルで利得なし・採用証拠不足」とし、「期待利得0の実証」とは書かない。
- **最強の反対理由：安全な試作を paired 測定すべき。** simulation は競合削減による T080 群自体の高速化と相方変更を扱わず、その効果を既存集計から排除できない。ただし現時点で支持できるのは実験までで、land ではない。