## A-1: `VerifyResult` と terminal WAL が結合されていない

- **主張**: P2 の単独 `VerifyResult` 導出と S3 の構造的 projection 作成を別々に成功させても、同じ物理結果を表す保証がない。計画どおりなら consumer が FC07 で拒否する record を producer が発行できる。
- **根拠**: accepted の具体例は `VerifyResult(serializable=True, n_txns=1, anomalies=[], total_cycles=0, integrity=I0)` (`I0.clean() is True`) で、`verdict="serializable"`、`certified=True` となり S1 は accepted を返す。しかし同じ `build_attempt_id="A"` の projection terminal が `abort`、または `commit` でも `verify_configs=["wrong"]` なら、consumer は `reflux_formal_consumer.py:1274-1281` で FC07 にする。rejected も、有効な単一 anomaly を持つ `VerifyResult(serializable=False, n_txns=2, anomalies=[A], total_cycles=1, integrity=I0)` から record を作り、WAL terminal を `reason="indeterminate"` または別 anomaly `B` の verify にすれば `reflux_formal_consumer.py:1282-1394` で落ちる。S2 の予定署名には terminal や `ordered_verifiers` がなく、S3 は連続性しか検査しない (`s2-plan.md:50-52,84-101`)。accepted は実際には複数 pass 全通過後に成立するため、単一 `VerifyResult` では不足する (`pipeline.py:1444-1448,1594-1605,1695-1727,1818-1837`)。
- **帰結**: producer 由来 record と ledger digest は生成されるが、formal terminal は期待する `P6Unavailable` でなく FC07 となり、成果物列全体が不受理になる (DW-G05)。
- **推奨**: **修正案**。issuance 時に resolved WAL と verifier policy を必須入力にし、rejected は `terminal.verify == result_to_dict(vr) minus trace_dir`、terminal stage、reason、attempt を同時検査する。accepted は単一 `VerifyResult` でなく commit と exact `verify_configs` から導く。これを本 wave に入れられないなら S1 は「候補導出 helper」に格下げし、production issuer を名乗らない。
- **確度**: real 確定。

## A-2: `total_cycles` は class 数ではなく SCC 数

- **主張**: `total_cycles == anomaly_count == 1` は「witness class が 1 件」を証明しない。1 個の SCC 内に複数 cycle、従って複数 digest が存在しても、verifier は都合のよい 1 cycleだけを報告する。
- **根拠**: `_sccs()` は非自明 SCC を列挙し (`dsg.py:429-478`)、`_shortest_cycle()` は各 SCC から最初に見つかった 1 cycleだけを返す (`dsg.py:481-502`)。`anomalies()` の `total` は `len(sccs)` であり、各 SCC につき anomaly を 1 件だけ追加する (`dsg.py:569-595`)。例えば adjacency `{1:{2,3}, 2:{1}, 3:{1}}` は SCC が 1 個だが cycle `[1,2]` と `[1,3]` の 2 class を持つ。それでも具体的な出力値は `serializable=False, n_txns=3, total_cycles=1, anomalies=[A12], integrity.clean=True` となり、producer と consumer の双方を通る。これは設計の「複数 class から 1 件を選ばない」(`verbatim-design-s3.md:65-71`) と矛盾する。
- **帰結**: FC07 は通る一方、record の `constraint_sha256` は物理結果に存在する複数 class のうち選択された 1 件となり、設計上の受理集合が実質的に広がる (DW-G05)。
- **推奨**: **scope 外へ裁定送付**。class を「verifier が各 SCC から出す代表 witness」と再定義するか、全 class 数または uniqueness proof を verifier 出力へ追加するかを裁定する。現行 §3.4 を維持するなら、producer 単独では uniqueness を証明できず、rejected 発行を開始できない。
- **確度**: real 確定。

## A-3: 枝の一致は概ね正しいが、恒真条件が混在する

- **主張**: 同一 report snapshot に限定すれば、計画の dirty、indeterminate、切詰め、複数、空 anomaly の拒否は consumer と一致する。一方、いくつかの条件は `VerifyResult` と `result_to_dict()` の定義から恒真で、入力防護や独立な変異点ではない。
- **根拠**:

  | 具体的な `VerifyResult` 値 | producer / consumer |
  |---|---|
  | `serializable=False, n_txns=2, anomalies=[A], total_cycles=1, integrity.orphan_reads=1` | verdict は non-serializable だが clean false。双方拒否 (`model.py:503-515`, consumer `1341-1354`) |
  | `serializable=True, n_txns=2, anomalies=[], total_cycles=0`, dirty integrity | indeterminate。双方拒否 |
  | `serializable=False, anomalies=[A], total_cycles=4`, clean | `anomaly_count=1 < total_cycles`。双方拒否 (`report.py:134-135`, consumer `1384-1390`) |
  | `serializable=False, anomalies=[A,B], total_cycles=2`, clean | anomaly 2 件。双方拒否 (`consumer:1378-1383`) |
  | `serializable=False, anomalies=[], total_cycles=1`, clean | `max_report=0` 型。双方拒否 |
  | `certified=True, serializable=False` | exact `VerifyResult` では構築不能。`certified` の定義が serializable を要求する (`model.py:518-521`) |

  `anomaly_count == len(anomalies)` は `result_to_dict()` 自身が作るため恒真 (`report.py:134`)。exact key 集合も同関数から作る限り恒真で、schema drift detector ではあっても入力防護ではない。rejected で `serializable is False` が成立すれば `certified is False` も派生する。consumer では wire の各値が独立なので同じ検査が保護になるが、producer typed 経路では独立ではない。
- **帰結**: 恒真な条件を防護数や mutation 被覆へ算入すると、実際の受理集合を広げる変異が残っていても検査済みと誤認する (DW-G05)。
- **推奨**: **修正案**。恒真条件は drift assertion と明記する。実防護として `serializable=0`、stats の `True`、cycle txid の `True`、version の `1.0` を使う直接負例を追加する。consumer は exact int を要求する (`reflux_formal_consumer.py:1163-1223,1301-1330`) ため、T-2438 を一般論として scope 外にしても、この parity test は外せない。
- **確度**: real 確定。

## A-4: shared digest だけでは同一性を保証しない

- **主張**: P1 の式共有は「同じ Python 値」への hash 式 drift を防ぐだけで、producer が見た anomaly と WAL に凍結された anomaly の同一性、および構造 validator の同一性を保証しない。
- **根拠**: `canonical_json_bytes()` は dict key を sort し、list 順序を保持し、有限 float と bool も符号化する (`reflux_origin_artifacts.py:42-69`)。有効 anomaly では consumer が数値を exact int に限定するため float/bool は hash 差ではなく事前拒否対象 (`reflux_formal_consumer.py:1155-1235`)。`trace_dir` は anomaly 外で、pipeline が WAL 前に除去する (`pipeline.py:1601-1603`)。従って、同じ valid snapshot なら key 順、`trace_dir`、WAL 往復による差はなく、canonical bytes 一致は導ける。しかし model は mutable (`model.py:364-390,471-500`)。WAL に anomaly `A` を書いた後に `vr.anomalies[0]` を coherent な `B` へ変更する、または別 run の `vr_B` を producer に渡すと、shared helper でも record は `H(B)`、WAL は `H(A)` となり consumer `reflux_formal_consumer.py:1391-1394` が FC07 にする。計画の「同じ run を一度使う」は test 手順だけで API 不変条件ではない (`s2-plan.md:151,232`)。
- **帰結**: digest helper が共通でも、snapshot の取り違えや mutation により rejected record の class が WAL と乖離し、FC07 terminal と後続 digest が変わる (DW-G05)。
- **推奨**: **修正案**。P1 は採用するが、共有単位を bare hash でなく「構造検査済み anomaly の digest」まで広げる。さらに issuance で typed report の wire snapshot と terminal `verify` の byte-equivalent JSON 値を比較する。複製案は単一 r9 pin では不十分なので却下する。
- **確度**: real 確定。

## A-5: P3 は live WAL の追記寿命を閉じていない

- **主張**: P3 の全 WAL digest は、projection 発行後に同じ WALへ 1 frame でも追記されれば既発行 record を壊す。計画自身が最大の不確実点としているため、「裁定候補なし」は支持できない。
- **根拠**: 計画は区間でなく `layout.wal_file` 全 bytes を `source_wal_ref.sha256` にする (`s2-plan.md:100`)。resolver は現在の全 file bytes の digest を再計算する (`reflux_result_evidence.py:528-544,657-678`)。WAL writer は `O_APPEND` で追記する (`wal.py:1266-1275`)。具体的に発行時の bytes を `W`、後続 frame を `L` とすると、record は `sha256(W)` を保持するが resolver は `sha256(W || L)` を観測し、FC05B で拒否される (`reflux_formal_consumer.py:883-895`)。
- **帰結**: campaign root が複数 query で WAL を共有する topology なら、後続 query が過去の全 result record を不受理化する (DW-G05)。
- **推奨**: **修正案**。各 source WAL が terminal 後に不変となる topology を file identity 単位で pin し、発行後追記の負例を追加する。保証できなければ immutable な create-only source snapshot を参照する設計へ変更し、P3 は裁定へ送る。
- **確度**: 要実測。追記時の破損は real だが、33 query の実 topology が同じ WAL を再利用するかは投影資料だけでは確定しない。

## A-6: P4 は局所 API としてのみ成立する

- **主張**: 派生例外 1 型は fail-closed な S1 API として採用できるが、それだけでは §3.4 の「当該行以降を tombstone、origin aborted」を実現しない。
- **根拠**: `map_absent_result_to_*` は単一 member を tombstone に写すだけ (`reflux_result_evidence.py:820-872`)。親 brief は production caller と `run_origin_trial` 配線を scope 外にしており (`brief-s1.md:26-29`)、例外を捕捉して suffix 全体と origin terminal を変える主体が本 wave にない。P4 の説明文字列も test では安定契約として pin しない予定 (`s2-plan.md:107-109`)。
- **帰結**: 本 wave 単独では拒否時に record がないことしか成立せず、ledger suffix と origin terminal の成果物は設計どおりには生成されない (DW-G05)。
- **推奨**: **条件付き採用**。例外型 1 個は維持してよいが、「§3.4 mapping を実装した」とは扱わず、caller 配線を明示的 carry にする。理由文字列を機械分岐に使わない。
- **確度**: real 確定。

## A-7: fixture 走査からの一般化は成立しない

- **主張**: brief の 8 fixture からの不在一般化は実際に反証されており、22 fixture への拡張後も production 入力全体や class uniqueness の証明にはならない。
- **根拠**: brief 自身が「8 件は `total_cycles <= 1`」から複数 class 不在とした直後 (`brief-s1.md:22`)、r8 の `total_cycles=4` で訂正している (`brief-s1.md:23`)。さらに `total_cycles` は SCC 数なので、値が 1 でも class が 1 とは限らない。read-only の DSG 列挙では r8 の SCC `[200,201,202,206]` に 3 simple cycle、SCC `[3,4,5,6,7,8]` に 4 simple cycle があり、verifier はそれぞれ 1 anomaly へ縮約する。既存 test が固定するのは anomaly/SCC が 4 件という結果だけ (`test_verifier.py:1663-1686`)。
- **帰結**: fixture に現れなかった受理境界を「存在しない」と扱うと、単一 SCC 内の複数 class を選択する producer が正例 test を通る (DW-G05)。
- **推奨**: **修正案**。r8 full と `max_report=1` は維持するが、「synthetic 不要」(`s2-plan.md:139`) は撤回する。少なくとも単一 SCCに 2 cycle を持つ graph-level counterexample を追加し、仕様上どう扱うかは A-2 の裁定へ接続する。
- **確度**: real 確定。

## 総括

real 確定は 6 件、要実測は 1 件。  
最重は A-1 で、現計画は typed result と terminal WAL を結合せず、consumer が FC07 で落とす record を発行できる。  
A-2 はさらに、producer と consumer が一致しても §3.4 の複数 class 禁止を満たさない。  
P1 は validator と snapshot 束縛まで共有する条件で支持、P2 と P3 は修正、P4 は局所 API としてのみ支持する。  
pytest は実行しておらず、現状のプランは支持しない。