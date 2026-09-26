## 対応表

| 所見 ID | 判定 | 根拠 |
|---|---|---|
| RA1＝RB1 | closed | P の実際の `T2273_PRECOPY` を記録し、未設定の `T2273_LOCAL_OUTPUT_SOURCE` は `None`。照合側も一致する。[runner:650](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_runner.py:650)、[analyze:899](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:899) |
| RA2 | partial | import と写し生成は thread 内へ移った。import 失敗は、directory 作成後なら `failed.json` に届き、worker は失敗・180 秒超過時に例外を出して直接複製へ戻らない。ただし directory 作成自体が失敗すると marker の書込みも失敗し、worker は上限まで待つ。[plugin:481](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_plugin.py:481)、[plugin:289](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_plugin.py:289) |
| RA3 | closed | file digest と directory path 集合 digest を分離し、件数を含む両方を A/P 比較している。[plugin:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_plugin.py:38)、[analyze:857](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:857) |
| RB2 | closed | 全 builder key について A/P 各 1 件の digest を要求する。[analyze:858](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:858) |
| RA4 | closed | 必須欠測を有効性に入れ、P の該当 `copy.list` だけを除外する。[analyze:937](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:937) |
| RA5＝RB3 | closed | 有効対だけで集計し、3 対未満では判定保留として (b) を名指ししない。[analyze:959](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:959)、[analyze:1004](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:1004) |
| RA6＝RB4 | partial | analyzer は構造化された失敗文を読むが、指定された conftest にその prefix・reason の実文はない。conftest は別 memo module に処理を委ねるため、この射影だけでは実例外との一致を確認できない。[analyze:901](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:901)、[conftest:2478](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/orchestrator/tests/conftest.py:2478) |
| RB5 | closed | 有効対の key・条件・phase 別中央値から候補を選び、key と値を出力する。[analyze:972](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:972)、[analyze:1002](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:1002) |

## 新規所見

- **FN1 — 中:** thread の `begin()` は `try` の外、directory 作成失敗後の `failed.json` 書込みも保護されていない。[plugin:485](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_plugin.py:485)、[plugin:503](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_plugin.py:503)。放置すると P の初回失敗が marker に残らず、180 秒待って無効になる。**修正:** thread 全体の例外を確実に記録し、marker を置けない失敗も controller の記録から判別できるようにする。
- **FN2 — 中:** 出力に判定結果と `pre_outside_55_80_s` はあるが、事前登録の基準式と「pre が範囲外なら外れ」という説明文がない。[analyze:949](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:949)、[analyze:1004](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:1004)、[analyze:1013](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:1013)。放置すると結果単体で判定根拠と外挿上の外れを読み違える。**修正:** 3 対すべて Δ>0・r 中央値≥10% と、A の pre が 55〜80 秒外なら外れである旨を明記する。

## 総括

**修正後 GO。** 主要な A/P 同一性検査と有効対限定の集計は直っている。RA6 の実例外照合は指定資料だけでは確証がなく、FN1・FN2 も残る。計算ノードでの実走は未確認であり、今回の判定は静的検査に限る。