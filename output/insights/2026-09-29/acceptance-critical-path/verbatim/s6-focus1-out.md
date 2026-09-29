| 所見 | 判定 | 根拠 file:line | 残る問題 |
|---|---|---|---|
| 1. shard 対応付け | closed | [run-pair.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/acp-author/scratch-acp/run-pair.sh:112) | `command=` を JSON 解析し、正規化した tests path と完全一致で照合する。実物の 1 行目もこの形式。 |
| 2. fresh 木・commit | partial | [run-pair.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/acp-author/scratch-acp/run-pair.sh:19) | 両 HEAD と期待 commit は照合するが、期待値が投入直前の local main か、4 本が fresh で指定ツールによる submodule 初期化済みかは runner から検証できない。親の木作成 log が必要。 |
| 3. 実効 env | partial | [aggregate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/acp-author/scratch-acp/aggregate.py:83) | 判定は予定値を使わず、実物と一致する `request.json` の `environment` と終了後 pyc を使う。ただし段 4 が求めた **login collection 自体の実効 env** は独立に記録していない。 |
| 4. 取り直し選択 | closed | [aggregate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/acp-author/scratch-acp/aggregate.py:157) | ID・重複を制限し、p1 系と p2 系から各 1 対を選ぶ。原対が invalid の場合だけ取り直しを選ぶ。 |
| 5. 出力先・pid | closed | [run-pair.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/acp-author/scratch-acp/run-pair.sh:8) | 木内出力を拒否し、pid を排他的に作成する。 |
| 6. 他の受入 leader | partial | [run-pair.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/acp-author/scratch-acp/run-pair.sh:42) | `pid,etime,args` と候補行は残るが、K/H **それぞれの投入時刻**の他 leader 数は確定していない。 |
| 7. 秒精度の境界 | closed | [aggregate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/acp-author/scratch-acp/aggregate.py:46) | mtime の ±1 秒を `uncertain` として支持判定から除外し、件数と shard 番号を出す。 |

### 新規所見

1. **must-fix — 4 本の独立性が検証されない。** [run-pair.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/acp-author/scratch-acp/run-pair.sh:4): K と H に同じ木を渡せ、対をまたぐ再利用も拒否されない。同じ木で K/H を同時起動すると env と pyc の対照が成立しない。親の木作成 log で 4 本の一意性・fresh 性・submodule 初期化・local main の commit を照合し、少なくとも runner では K/H の正規化 path の一致を拒否する。

2. **should — JSON 配列中の任意の一致要素を対象 path とみなす。** [run-pair.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/acp-author/scratch-acp/run-pair.sh:119): pytest の実対象が別 path でも、別オプションの値に `<K>/orchestrator/tests` があれば K に対応付く。実物の `command=["/usr/bin/python3","-m","pytest","<worktree>/orchestrator/tests",…]` に合わせ、pytest の位置引数を取り出して比較する。

段 4 の数式は、shard ごとの `pre(K)−pre(H)`、`W_max(K)−W_max(H)`、適格 H shard の全件で `Δpre≥30`、2 対とも `ΔW>0` の場合だけ W 短縮観測、という点で [aggregate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/acp-author/scratch-acp/aggregate.py:107) と一致する。赤・shard 欠落、投入前 pyc、fix 裁定で追加された K/H の request env と終了後 pyc の無効条件も実装されている。login env の独立記録と投入時の他 leader 数は段 4 の記録条件を満たし切っていない。

## 総括

**NO-GO。** 数値判定式は概ね裁定どおりだが、4 本の独立性と段 4 の記録条件に未充足がある。受入本走は未実施で、対照効果はまだ判定できない。