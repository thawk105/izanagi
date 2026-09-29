## 1. 所見

1. **major｜plan §3・§5、brief P3・P5｜`mainte()` 全体では介入が二つになる。** `mainte()` は GC flag を立てる前に `GCExecuteFlag` を消費し、`gc_versions()` と `gc_records()` を実行する（`external/ccbench/cc/cicada/transaction.cc:859-888`）。ro 専用になった worker でも、過去の update が残した `gcq_` を ro commit で処理しうる（同 `transaction.cc:708-719`、`include/transaction.hh:45-47`）。従って生存版や throughput の差を「flag による公開前進」だけに帰属できない。slot が正しい限り、この追加回収そのものによる誤回収の反例は見つからなかった。**修正案:** flag だけを立てる腕も設けるか、公開・`GCExecuteFlag` 消費・版切断を別々に計数して効果を分ける。

2. **major｜plan §2｜小モデルの正例は、発火する時系列まで固定する必要がある。** (i) の slot 引上げで既読版を壊すには、その版を上書きする版の確定と GC queue の処理が要る。(ii) の slot を ∞ にする例も、次の `begin()` の `ThreadWtsArray` store、leader の slot 走査、`MinRts` 公開、回収、低い `rts_` の store と後続 read という順序が要る（`transaction.cc:39-43,806-842`、`util.cc:290-321`）。計画の固定版と探索上限で両 witness に到達するかは**未確認**。**修正案:** 各正例に具体的な最短 witness を要求し、到達しなければ正例合格としない。安全版の GC 判定には、保持 pointer と将来選択版を版鎖・回収操作から独立に導く oracle を使う。既存 `judge.py:84-109` の `gc_floor` 判定をそのまま自己照合に使わない。

3. **major｜plan §3・§5｜計器なし workload の同一性は、提案された追加 patch だけでは確定しない。** 元の YCSB は各操作を独立に READ にするため、`rratio=95` は「ro tx 95%」ではない（`external/ccbench/include/ycsb.hh:55-79`）。vlife は初回 `begin()` で手続きを書き換え、retry では維持する（`patches/instr-cicada-version-lifetime.patch:346-390`）。新 workload patch を計器 build にも重ねるなら、vlife 側の書換えとの二重適用、長い worker の指定、乱数系列、retry の扱いを決める必要がある。**修正案:** 両 build で同一の手続き生成経路を一つだけ有効にし、指定率に加えて実現 ro 試行率・commit 率と長い worker の ro 件数を照合する。

4. **major｜plan §3｜分割 patch と condition gate の帰属が弱い。** 計画は通常版 patch を `_DEFINE_SPECS` に登録するが、計器 build には別の vlife 用 patch を適用する（plan:42-44）。gate の patch 参照は変更 path の列挙を行い（`orchestrator/campaign/condition_meaning_gate.py:2532-2549`）、その登録だけでは二つの patch が同じ ro 分岐を作った証明にならない。**修正案:** 両 preimage で macro=1 の ro 分岐を前処理後に比較し、比較した patch SHA と build SHA を gate receipt・raw record に結び付ける。macro=0 は触れた TU の token と行番号を stock と照合する。三形への厳密適用は現時点で**未確認**。

5. **minor｜plan §3｜登録簿更新を条件付きにしている。** 新 driver は自前 materializer と build subprocess を置く計画（plan:46,52）なので、`materializer_admission.py` の登録と `test_p3_build_authority_cli.py` の `MANUAL_BUILD_FILES`・`EXPECTED_NON_ADMISSIBLE` は必須である（`materializer_admission.py:108-116,199-215`、`test_p3_build_authority_cli.py:159-185,1242-1271`）。新しい subprocess site も `test_ccbench_spawn_sites.py:80-102` の閉じた台帳に分類が要る。裸 macro patch は `test_p3_s4_loop.py:8547-8557`、新テストの自走面は `orchestrator/tests/README.md:114-129` の検査対象になる。**修正案:** 「`--build` の字面を持つなら」ではなく、実際の build 関数・起動 site・新テストを実装した時点で各台帳を更新する。workload 用 macro を増やす場合は、その owner TU と branch witness も別途登録する。

6. **minor｜brief:21・plan:42｜既存二 patch の重なりに関する証拠の言い方が強い。** `probe-stack.sh:13-19` は一方向だけ実際に `git apply` し、逆方向は `git apply --check` にとどまる。`set -u` だけなので失敗しても続行する。提示された script だけから「どちらの順でも適用成功」とは確定できず、実行ログもここでは**未確認**。**修正案:** 両順序で `--check` と実適用の終了値、最終 tree の hash を保存する。

7. **minor｜brief:8、plan §5｜md_15 の値は局所的な観測である。** 76〜77% は gc 10 µs・S95/T95・長い tx なしの D-C 時刻分割であり、既定 R95 は 8.7%、gc 100 ms は 1% 未満（`output/insights/2026-09-29/vhash-readonly-share/README.md:185-202`）。長い ro の公開 0 回も計器付きの 45 走・各 3 秒に限られ、介入による改善量ではない（同 `README.md:204-208,243-250`）。**修正案:** 新資料で条件と「公開待ちの観測上の割合」を常に併記し、variant の因果効果とは分ける。

## 2. P1〜P5 への判定

| 仮裁定 | 判定 | 理由 |
|---|---|---|
| P1 | **修正** | 対象 YCSB、`group_commit=0`、slot 不変なら、flag 追加だけによる誤回収の反例は見つからない。begin の二手の間も旧 slot が保守的に残る。ただし flag は公開と回収を起動する。`INLINE_VERSION_PROMOTION` は ro を update に切り替える（`include/transaction.hh:199-213`）。delete と group commit まで一般化しない。全メモリ順序の証明は**未確認**。 |
| P2 | **修正** | (i)(ii) は候補として妥当。(iii) の flag 単独を陰性対照とする判断にも同意する。ただし正例には回収・再利用まで到達した witness が必要。 |
| P3 | **修正** | clear 後の `mainte()` は保持参照の観点では妥当だが、GC 実行時機も変える。flag の効果を単独で主張するには分離計数が要る。 |
| P4 | **修正** | 二 patch 分割は合理的。両者の macro=1 の実効分岐一致と macro=0 の stock 一致は、厳密適用後の照合で確定する必要がある。 |
| P5 | **反対** | 元の計器なし YCSB に ro 指定率はない。段 2 の独立 workload 案は必要だが、計器版との二重書換えを解決して初めて同条件比較になる。 |

## 総括

現時点の最大の整合問題は、`mainte()` 全体の追加が**公開を早める変更と GC 実行を早める変更を同時に含む**こと、および計器あり・なしで同じ ro 手続きを生成する契約がまだ具体化されていないこと。版安全については限定条件下で P1 を支持するが、小モデルの正例発火、分割 patch の実効一致、判定器での変更経路の発火は実測前の**未確認事項**である。