## 所見

1. **must-fix — `tuned` と `cw-as-dyn` の claim が裁定外に変更されている。**  
   成果物影響: 両 cell の group receipt の `claim` が既発行 literal から変わり、新 literal も published receipt の受理集合へ入る。  
   根拠: 旧 literal は `t2187_adaptive_const_probe.py:145-158`。一方、共通 builder は両 cell にも `認証対象は 48 threads...BACKOFF_TRACE=0...` を追加する (`:416-465`)。live row はその値を保存し (`:3404-3407`, `:3478`)、group も同じ値を要求・発行する (`:2463`, `:2824`, `:2866`)。これは親裁定の「1 文字も変えない」に反する。  
   最小修正: `_certification_claim` の `tuned` は `ALLOWED_GROUP_CLAIM`、`cw-as-dyn` は `DYNAMIC_GROUP_CLAIM` をそのまま返し、R7 の追加文は cohort 2 の p1/p2 だけに限定する。

2. **must-fix — R6a の新 singleton 検査に producer が適合せず、24 件そろっても group が発行されない。**  
   成果物影響: certified request 24 件が存在しても `group.json` がなく、認証済み group、レポート、台帳参照を作れない。  
   根拠: group は `binary_sha256` と `build_cache_key` の singleton を新たに要求する (`t2187_adaptive_const_probe.py:2741-2746`)。親の実測対象では fake build の binary は全件同じ (`test_t2187_adaptive_const_probe.py:222-247`) だが、`buildcache.cache_key` は stub されず、各 request が新しい build context/admission から算出する (`t2187_adaptive_const_probe.py:3583-3607`; test の反復は `:1353-1359`)。したがって追加検査で残る不一致は `build_cache_key` である。拒否は `_try_finalize_group` が無条件に握り潰して `False` にする (`t2187_adaptive_const_probe.py:3163-3175`)。  
   最小修正: singleton gate は緩めず、24 request が同じ決定的 `build_cache_key` を記録するよう producer をそろえる。テスト固有の admission 差なら helper で共有 `_t1` key を返す。実機でも key が異なるなら campaign 投入前に producer 側を直す必要がある。

3. **must-fix — R3/R4 の raw literal → parse → singleton → membership が CLI で強制されていない。**  
   成果物影響: 非 canonical seed や重複 option から `not-yet-group-certified` の certified request と claim を生成でき、重複 thread optionでは最終 group まで最後の値だけで通り得る。  
   根拠: thread は先に parse され (`t2187_adaptive_const_probe.py:1561-1563`)、raw literal 検査は後 (`:1574-1580`)。テストも `49` が raw gate でなく parser の `ValueError` になることを固定している (`test_t2187_adaptive_const_probe.py:1962-1969`)。seed parser はゼロ埋め decimal を受理する (`t2187_adaptive_const_probe.py:756-762`)。`argparse` の `--threads` と `--step-policy-seed` は重複回数を保存せず最後の値を採る (`:3232-3242`)。p2 seed の membership はその後だけである (`:1587-1598`)。claim は直後に生成される (`:3404-3407`)。p2 の重複 seed は group row 検証でようやく検出される (`:2492-2504`)。PBS 側の raw 閉表は正しい (`t2187_adaptive_const_probe.pbs:137-147`, `:189-228`)。  
   最小修正: custom argparse action などで option の重複を拒否し、seed は raw が `str(parsed)` と一致することを parse 前後で要求する。thread も raw 検査を `_parse_threads` より前へ置く。

4. **must-fix — 既発行 receipt 互換が exact artifact ではなく値の組による generic legacy 分岐になっている。**  
   成果物影響: 新規に置かれた同形 receipt が旧い狭め不足の claim で再受理され、レポートや台帳の既発行 receipt 参照を置換できる。  
   根拠: `_legacy_published_claim` は `threads=48` と p2 default seed だけで旧 claim を返す (`t2187_adaptive_const_probe.py:469-480`)。published consumer はそれを一般に受理する (`:2990`)。互換テストは実在する `c2-p1-a1` / `c2-p2-a1` を読まず、空の任意 result file と合成 receipt を作り (`test_t2187_adaptive_const_probe.py:2046-2170`)、その新規 artifact が通ることを確認している (`:2171-2179`)。これは段 3 sol 6 が指摘した形そのもの。  
   最小修正: generic axes 分岐をやめ、既発行 2 receipt の正規 path と既知の receipt 全体 SHA-256 など、置換不能な byte identity にだけ旧 claim 互換を限定する。テストも実 artifact bytes またはその凍結 fixture を使う。

## 実測赤 2 件

1. `test_group_receipt_requires_exact_24_terminal_request_set`  
   根本原因は上記所見 1。receipt は共通 builder の新 claim を持つ (`t2187_adaptive_const_probe.py:2866`) のに、テストは不変であるべき `ALLOWED_GROUP_CLAIM` を要求する (`test_t2187_adaptive_const_probe.py:1092`)。テスト期待値を変えるのではなく builder を旧 literal へ戻すのが最小修正。

2. `test_public_certification_creates_group_only_after_all_24_requests`  
   このテストの各 row は producer と consumer が同じ新 claim builder を使うため、所見 1 の claim 不一致ではない。新しい `build_cache_key` singleton (`t2187_adaptive_const_probe.py:2745-2746`) が拒否し、その `CertificationReject` を `_try_finalize_group` が `False` に畳む (`:3163-3175`) ため `group.json` がない。singleton は残し、producerまたは fixture の key を同一化するのが最小修正。

## R1〜R7 照合

| 裁定 | 状態 | 現物 |
|---|---|---|
| R1 | gate 部分は充足、実 artifact は未作成 | 対象 thread row 実在は `t2187_adaptive_const_probe.py:2210-2238`。p2 実 seed/genome は `:2252-2278`。`expected_repo_head` は exact equality のまま (`:2227`)、caller も現在 HEAD を渡す (`:3428`, `:3433-3445`)。13 performance job の生成・実走は未実施。 |
| R2 | 充足 | cell 別閉表 `:362-367`、凍結値検査 `:381-399`、request membership `:1574-1608`、PBS `t2187_adaptive_const_probe.pbs:221-227`。 |
| R3 | 値集合は充足、raw/singleton は未充足 | 12+1 表 `t2187_adaptive_const_probe.py:110-123`, `:368-370`。missing/mismatch/conflict `:1547-1554`, `:1587-1602`。raw 問題は所見 3。 |
| R4 | consumer の新 claim 経路は充足、CLI 順序と legacy は未充足 | frozen axes `:373-413`、builder `:416-466`、row `:2446-2463`、group `:2742`, `:2824`、published `:2942-2966`。document 生値から新 claim を直接作る call site はない。ただし所見 3、4 が残る。 |
| R5 | 充足 | `result["anomalies"] == []` を要求 (`:2062-2073`)。 |
| R6 | gate は実装、実運用適合は未充足 | row group `:2745-2746`、published `:3075-3078`。12 group 間 hash 相異確認は裁定どおり親の段 7。所見 2 が blocker。 |
| R7 | cohort 2 は充足、既存 2 cell は違反 | p1/p2 claim に seed と診断計装制限を記載 (`:440-465`)。build は実 seed を使う (`:3431`, `:3570`)。ただし同じ builder が `tuned` / `cw-as-dyn` まで変更する。 |

## 閉表と claim 経路

thread の membership 自体は exact だが、実行順は `_parse_threads` → raw/singleton/membership であり、裁定順ではない。p2 seed は argparse parse → membership で、canonical raw と option singleton がない。

row、group、published の新 claim はすべて `CertificationAxes` を経る。静的に確認できた claim call site は `t2187_adaptive_const_probe.py:2463`, `:2824`, `:2866`, `:2990`, `:3407` だけで、document 生値を直接補間する別経路はない。ただし published の旧 claim は `_legacy_published_claim` という別経路を持つ。

## 受理・拒否挙動の変更

裁定が許した拡張は、p2 の 12 preregistered seed と default seed、p1/p2 の 24 threads、PBS から certify への seed forward である。これに伴う p2 performance artifact の実 seed 受理と p1/p2 の新 R7 claim も裁定内。

裁定外の追加受理は次のとおり。

- p2 seed のゼロ埋め raw literalと、重複 `--step-policy-seed` の最後が閉表内である request。
- 重複 `--threads` の最後が p1/p2 の 24 または48である request。raw axis 全体は singleton ではない。
- `tuned@48` と `cw-as-dyn@48` の新しい R7 追記 claim。
- exact 既発行 artifact に限定されない、同形の新規 published receipt に対する旧 claim 互換。

一方、非 p2 seed conflict は維持される (`t2187_adaptive_const_probe.py:1547-1554`)。anomaly 非空、wrong performance HEAD/thread/seed、group 内 binary/cache 混在、published genome drift は新たな narrowing であり、既存拒否の削除ではない。

## 12 seed の転記

probe の 12 値 (`t2187_adaptive_const_probe.py:110-123`) は正本の `PREREGISTERED_SEEDS` (`backoff_counterfactual_cohort2_analysis.py:77-92`) と全値一致する。default seed は正本集合に含まれない。

テストは同じ literal を再記述していない。正本モジュールから直接 import し (`test_t2187_adaptive_const_probe.py:21-23`)、probe 集合との一致と default seed の非包含を検査する (`:1864-1870`)。PBS の数値集合も probe と比較する (`:3050-3057`)。

**nit:** PBS テストは literal を `int` 化するため、同じ値へのゼロ埋め表記変異を検出できない。現物の PBS literal は正本と canonical decimal で一致しているが、将来その変異を殺すなら文字列集合を比較すべきである。

## M1〜M8 と負例

| 変異 | 判定 | 単一理由性・実経路 |
|---|---|---|
| M1 seed 閉表 | KILLED | 正本との集合一致 `test:1864-1870` と閉表外 seed `:1923-1949`。ただし raw spelling と重複 option は未被覆。 |
| M2 thread 閉表 | KILLED | `tuned@24` だけを変異した負例 `:1910-1916`, `:1941-1949`。 |
| M3 raw claim builder | 部分的 | 型制約は `:1992-2011` が殺す。現物に raw document builder はないが、consumer 側へ別 builder を追加する変異を殺す spy 型テストはない。 |
| M4 anomaly | KILLED | real serial fixture の anomaly だけを非空にする `:778-805`。別 gate の先行拒否はない。 |
| M5 PBS forward | KILLED | certification exec 内の exact expansion を静的検査 (`:3037-3041`, `:3070-3071`)。shell 実行テストではないが、指定された行の削除変異は殺す。 |
| M6 performance seed | KILLED | prereg seed の正例後、seed field だけ default へ変更 (`:3222-3268`)。default 比較へ戻すと正例が赤になる。 |
| M7 group axes singleton | KILLED | 個別には有効な seed/thread の混在だけを直接 helper へ渡す (`:2227-2243`)。他層を通らないため理由は一意。 |
| M8 performance thread | KILLED | 正例後、唯一の row thread だけを48から24へ変更 (`:3269-3275`)。対象 row 実在検査だけが落ちる。 |

R6a の binary/cache 負例は、変異値が個別 row 検査を通る形になっており、本来は singleton を一意に殺す (`test_t2187_adaptive_const_probe.py:1206-1211`; probe `:2511-2516`, `:2745-2746`)。ただし現在は同じ test が先に claim assertion `:1092` で停止するため、親の実走ではこの負例部分まで到達していない。

stub による実機構の迂回が重大なのは既発行 receipt 互換テストである。実 receipt を再検証せず合成 receipt を直接 published validator へ渡しているため、`c2-p1-a1` / `c2-p2-a1` の実互換を証明していない。

## 既発行 receipt と R6a

コード上、旧 p1/p2 claim、48 threads、default seed は再受理候補である。しかし実 receipt の binary/cache singleton、現行 genome、path/hash をこの射影では照合できず、合成テストも代替証拠にならない。したがって「既発行 2 receipt の互換確認済み」とは言えない。

R6a の検査式そのものは恒真ではない。row group と published group の両方に実 predicate があり、単独変異も設計上は到達可能である。ただし現状は所見 1 と 2により正例が通らず、テスト上も実 group 上も保証として成立していない。

## 総括

must-fix は 4 件。最重要は `tuned` / `cw-as-dyn` の claim を裁定外に変更したこと。  
実測赤 1 は共通 claim builder による旧 literal 破壊。  
実測赤 2 は新 `build_cache_key` singleton 拒否を `_try_finalize_group` が握り潰したもの。  
受理集合は raw CLI bypass、新 tuned/dynamic claim、generic legacy receipt の点で裁定を超えている。  
pytest は実行しておらず、以上は指定 7 ファイルの静的照合である。