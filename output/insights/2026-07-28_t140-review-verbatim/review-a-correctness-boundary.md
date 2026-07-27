必読 4 点はすべて読めた。静的検査の裁定は、**現プランを「条件付き採用」にしてはならず、再設計まで reject** である。任意 C++ 完全型を合成対象にする限り、提示された finite law test・trace shadow・preprocess 差分では正しさ境界を閉じられない。

以下、`plan.md` / `brief.md` は指定された `/tmp/claude-31609/.../scratchpad/wave-t140/` 配下を指す。

### A-1

- **深刻度**: blocker
- **主張**: G2 が支持するのは pointer iterator を使う簡約型の一部式が構文解析できることだけで、「骨格改変は alias 化 2 種で足りる」「データ構造 hole は構造的に実現可能」までは支持しない。
- **裏取り**: `probe_contract.cc:19-35` の `Elem` は実 `WriteElement<Tuple>` ではなく、`probe_contract.cc:39-40` の `SmallVec` はコメントに反して `TxExecutor` の nested type ではない。`probe_contract.cc:42` は iterator を単なる `T*` にして iterator traits・proxy reference・segmented iterator の問題を消している。`brief.md:46` の条件は `-Wall -Wextra -fsyntax-only` で `-Werror` がない。実 target は `external/ccbench/cmake/CompileOptions.cmake:30-32` で `-Werror`、`external/ccbench/cc/silo/CMakeLists.txt:1-13` で複数 workload TU を持ち、header は `ycsb_silo.cc:8`、`tpcc_silo.cc:8`、`bomb_silo.cc:8`、`sbomb_silo.cc:8`、`util.cc:18`、`transaction.cc:7` から参照される。さらに `plan.md:17` は、`brief.md:48-49` が撤回した「37 use site」を再掲している。
- **なぜ問題か**: `#if TRACE` の追加走査、`#if ADD_ANALYSIS`、`Linux`、TU 固有マクロ、大域 using-directive、実 `TupleBody` の ownership/alignment、他 TU の ODR 文脈を未モデル化のまま契約を確定すると、偵察の受理集合に「probe は通るが production target は build-error、または一部 TU だけ異なる定義になる」候補が入る。試行台帳の build-abort 数と代表 panel の生存率が設計欠陥で歪む。
- **最小の直し方**: 実 `WriteElement<Tuple>` と実 nested `WriteSet` を使い、TRACE/ADD_ANALYSIS の 0/1、production の全定義、全 Silo workload TU を同一 manifest で確認する。結論はそれまで「選択した式と pointer iterator surrogate の構文成立」に格下げする。

### A-2

- **深刻度**: blocker
- **主張**: `transaction.hh` を単体 preprocess して identity に加える設計は実 TU のマクロ文脈を覆わず、別コードを `"stock"` に alias できる。
- **裏取り**: `source_digest.py:129-145` は include 行を除去したファイル単体を preprocess し、`source_digest.py:187-194` はその出力だけを hash する。一方 `external/ccbench/cc/silo/ycsb_silo.cc:3-8` は `GLOBAL_VALUE_DEFINE` を定義してから `transaction.hh` を include する。`#ifdef GLOBAL_VALUE_DEFINE` は単体 preprocess では死ぬが実 ycsb TU では生きる。`assert_includes_match_head` は `source_digest.py:208-216` の raw include 行比較に限られる。
- **なぜ問題か**: header への file-wide direct edit で `#ifdef GLOBAL_VALUE_DEFINE` 内だけにコードを置けば、include 行不変・単体正規化結果不変のまま実 TU だけが変わる。既存 cache があれば変更は一度も compile されず、古い binary の hash・fitness・verifier verdict が新コードの certified record として記録される。これは G1 と同じ F29 型を identity 核で再発させる。
- **最小の直し方**: header は raw bytes hash も identity に必ず含め、単体 preprocess の semantic hashだけに依存しない。加えて actual target の compile-command/TU 文脈を binding するか、後述の mandatory confinement gate で raw directive を全入口から拒否する。

### A-3

- **深刻度**: blocker
- **主張**: プランは編集面の 3 定義を列挙したが、提案する包含検査では「許可されるが hash されないファイル」を防げない。
- **裏取り**: `source_digest.py:68` の `EVOLVE_BLOCK_SOURCES` と `source_digest.py:71` の `ALLOWLIST` は別定数で、`source_digest.py:187-194` が hash するのは前者だけである。`ALLOWLIST` 内の `Options.cmake:23` は `VAL_SIZE` を定め、同 `:60-67` が実 target の定義へ渡すが、実使用は `external/ccbench/include/ycsb.hh:40-43` にある。現在の hash 対象である `transaction.hh:64-66` の `VAL_SIZE` はコメントだけである。cache key は `buildcache.py:121-135` の genome・commit・trace・src token・toolchainだけ。`plan.md:238-240` の B03 は `EVOLVE_BLOCK_SOURCES ⊆ ALLOWLIST` しか要求しない。
- **なぜ問題か**: 例えば working-tree の `CCBENCH_VAL_SIZE` だけを変えると、実 YCSB のレイアウトは変わるが対象ソースの正規化結果は変わらず、同じ cache keyを共有し得る。EBS への header 追加漏れは偽 cache hit、ALLOWLIST への追加漏れは fail-closed abort、hook 定数への追加漏れは client/経路依存の許可差となり、certified 集合・abort 集合・試行台帳参照が独立に腐る。これは F2/F10/F35 型のドリフトである。
- **最小の直し方**: 単一 manifest から各集合を導出し、`ALLOWLIST = hash対象 ∪ 明示された非source入力` を exact に検査する。`Options.cmake` を丸ごと identity に含め、各定義を一つずつ落とす public-path mutation を置く。

### A-4

- **深刻度**: blocker
- **主張**: `transaction.hh` を `guard_write` の許可集合へ加えることは coder に必要な権限ではなく、header 全体への静かな権限拡張である。
- **裏取り**: `guard_write.py:98-111` は designated file の行位置・marker・内容を見ず全面許可する。Codex への hook は `hooks/README.md:15-24` で未配線である。通常 coder 経路は `p3_s4_loop.py:141-151` が hole だけを合成し、`p3_s4_loop.py:640-650` が quarantine 後に build する。一方、直接の `pipeline.evaluate()` は `pipeline.py:441-449` で `source_digest.resolve()` しか呼ばず、`source_digest.py:347-349` に shape/quarantine 検査はない。
- **なぜ問題か**: 同じ header 差分でも、loop 経由なら拒否、直接 pipeline・別 driver・直接 Edit なら identity に載せて評価可能、という受理集合差が生じる。後者では hole 外で verifier shadow・型骨格・マクロ枝を同時変更でき、certified record が「hole 内だけの variant」という provenance を失う。prompt の tool-less 宣言や hook 定数の存在は F7/F16/F17/F21 が既に否定した権限証明である。
- **最小の直し方**: `DIGEST_SOURCES` と `DIRECT_WRITE_SOURCES` を分離し、header の直接 Write/Edit は許可しない。実 diff の marker/shape attestation を `pipeline.evaluate()` またはそれより下の必須入口に置き、どの caller も迂回不能にする。

### A-5

- **深刻度**: blocker
- **主張**: 任意 `WriteSet` は TRACE 固有の追加走査を実行時に識別できるため、diff-of-diffs が一致しても trace build と perf build の意味論を分岐できる。
- **裏取り**: プランは `plan.md:52-55` で coder に完全な class 実装を許し、`plan.md:72` が禁じるのは mutable static/thread-local 等であって per-instance 状態ではない。TRACE build は `transaction.cc:403-405`、`:421-425`、`:601-623` で perf build にない `size()/begin()/end()`・range traversal を行う。`source_digest.py:240-269` は preprocess 後のソース差分しか比較せず、それにもかかわらず同 `:243-245` は data-structure observer effect も捕えると主張している。
- **なぜ問題か**: 許可された class に per-instance の呼出回数状態を持たせ、`begin()/end()/size()` が走査列に応じて集合を変えれば、`#if TRACE` を class 内へ書かずに両 build を区別できる。trace 側だけ正しい集合を verifier に見せ、perf 側で write/lock を落として高い fitness を出す構成が可能であり、certified verdict と選択対象の実挙動が別物になる。
- **最小の直し方**: 任意メソッド本体の合成を捨て、trusted 実装群を選ぶ宣言的パラメータ／有限 DSL に狭める。全 lock・trace・write consumer は coder iterator ではなく trusted snapshot を共有する。

### A-6

- **深刻度**: blocker
- **主張**: B07～B10 は発火点・出力 schema・公開経路が未定のため、現状の条件リストは安全 gate ではなく恒真化可能な願望リストである。
- **裏取り**: shape gate は `plan.md:75` と `:195-197` で「未実装・方式未定」。現在実際に赤を出すのは、別ファイル／hole 外変更に対する `diff_quarantine.py:417-457`、raw directive 等に対する同 `:459-493`、その `passed=False` を build 前に止める `p3_s4_loop.py:640-650` だけである。`friend`、per-instance call counter、型依存の操作改変は同 `:495-496` の通過側に落ちる。新 trace tag/Integrity field は `plan.md:116` で未定で、現 verifier の field は `model.py:126-142`、report は `report.py:58-70` に conservation/body/lifetime 欄を持たない。
- **なぜ問題か**: B08 の有限列を通過後だけ挙動を変える class、B09 の未注入 broken patch、private helper 直呼びだけで赤になる検査でも「条件達成」と記録できる。これは対象不在の F9、無効 flag の F14、live 配線なしの F21、checker/fixture 同時改変の F27、公開経路で受理集合が変わらない F28、復元恒真の F32、変異未注入の F33、空証明の F36 と同型である。
- **最小の直し方**: 各 gate の実装位置、入力、失敗例、Integrity field、WAL reason、build-spy の公開経路を先に仕様化する。注入 diff 自体の digest と各検査への一意帰属を固定し、未知・未配線は達成扱いにしない。

### A-7

- **深刻度**: blocker
- **主張**: 提案 shadow は body を保存せず検査も validation 前の一回だけなので、lost update と op/key 改変を verifier の外へ残す。
- **裏取り**: `plan.md:116` の shadow tuple は `(storage,key,rcdptr,op)` で body がないのに、B09 は `plan.md:262-264` で body corruption が赤になると約束する。UPDATE body は `transaction.cc:524-547` で write set に入り、lock は `:156-158` で INSERT を除外する。writePhase の INSERT 分岐 `:653-656` は body を copy しない。trace は `:601-606` で op 文字を出すだけで、parser は `orchestrator/verifier/parse.py:116-126` で op の値を検証せず、DSG は `dsg.py:61-70` で key と commit しか使わない。
- **なぜ問題か**: conservation 照合後に UPDATE の `op_` を INSERT へ変えれば、lock を取らず、body を書かず、版だけ進めて trace には正常な write として載せられる。DSG が非巡回なら certified になり、実 DB では acknowledged update が失われる。body だけの破壊は trace に値が存在しないためさらに完全に不可視である。
- **最小の直し方**: API intent の op・key・payload digest を trusted shadow に保持し、実 write 直前と完了後に照合する。op schema 検証と payload/state oracleを Integrity・report・WAL に配線する。

### A-8

- **深刻度**: blocker
- **主張**: M11 を「erase 後に break」だけで直すと、insert→delete が absent+locked の ghost tuple を index に残す既存の正しさ違反を温存する。
- **裏取り**: `transaction.cc:83-109` は新 Tuple を Masstree に挿入してから INSERT 要素を追加し、`tuple.hh:50-53` はその Tuple を `absent=true, lock=true` にする。delete は `transaction.cc:123-127` でその INSERT 要素を erase し、続く `:129-136` で同 Tuple を取得して `absent` のため `WARN_NOT_FOUND` を返す。abort cleanup は `transaction.cc:27-34` の write set 内 INSERT しか消さない。プランの修正は `plan.md:147-150`、B05 は `:246-248` の iterator pattern/ASan だけである。
- **なぜ問題か**: erase された INSERT の pointer/ownership 情報が失われ、Masstree には absent+locked の到達可能 object が残る。後続 insert は `transaction.cc:77-81` の non-null 判定で恒久的に `WARN_ALREADY_EXISTS` となり得る。残った write がなければ trace `:601-607` に操作は出ず、現 YCSB workload は `ycsb.hh:121-147` で read/write/RMW しか行わないため verifier も calibration も見ない。
- **最小の直し方**: prior INSERT の cancellation を専用遷移にし、index 除去と Tuple ownership 解放を一体で行う。insert→delete→commit/abort→再insert を独立 index oracle で検査し、この死角を軸定義シートへ追加する。

### A-9

- **深刻度**: blocker
- **主張**: 「成功した update と write-set 要素の 1 対 1 対応」という不変条件は stock 実装自身と矛盾し、提案 shadow は API intent でなく container 呼出しを自己照合している。
- **裏取り**: `plan.md:85-89` は成功操作との 1 対 1 を要求する。しかし `transaction.cc:524-554` は同じ key の既存 write を見つけると新 body を格納せず `FINISH_WRITE` へ飛び、`Status::OK` を返す。YCSB の key は `external/ccbench/include/ycsb.hh:55-75` で replacement 付きに生成され、update 呼出しは同 `:128-143` にある。shadow は `plan.md:116` の emplace/erase 点しか観測しない。
- **なぜ問題か**: API 成功数を数えれば stock control が赤になり、emplace 数だけを数えれば二回目の acknowledged update 欠落を見ない恒真 gateになる。前者は受理集合を空にし、後者は値の lost update を certified 集合へ残す。first-write-wins が意図仕様かどうかもプランには裏取りがない。
- **最小の直し方**: 1 対 1 を撤回し、同一 key の coalescing・insert/delete cancellation を含む形式的状態遷移を定義する。重複 key 列で「どの body/op が最終 intent か」を trusted oracle と照合する。

### A-10

- **深刻度**: blocker
- **主張**: 安全に構成的列挙できない任意 C++ 空間を「bounded representative panel」で採用する裁定は、axis-onboarding の差戻し条件そのものに反する。
- **裏取り**: `plan.md:123-125` は全空間が非列挙型で panel も未定、`plan.md:270-272` は B11 が現在赤だと認める。`docs/axis-onboarding.md:147-154` は構文契約から有限列挙と構成的安全保証ができない軸を B へ差し戻し、E へ昇格させないと定める。さらにプラン自身が `plan.md:23`、`:136-138` で性能地形を未実測としているのに、`:27` と `:278` では格納形式を条件付き採用している。
- **なぜ問題か**: B decision に `adopt_with_conditions` が残ると、後続作業は個別 checkbox の達成をもって任意 class 合成を正規の受理集合へ入れられる。実際には A-5 の動的偽装を有限 panel で排除できず、certified 選択結果・fitness 順位・trial ledger が安全性を証明しない探索空間を正当化する。
- **最小の直し方**: 現案は reject とし、trusted 実装の有限選択または宣言的レイアウト DSL へ軸を再定義する。それができないなら、既存編集面内で構成的列挙可能な下位軸へ戻す。

## 親 brief 自体への攻撃

- **M2**: 「編集面の定義は3箇所」は core enforcement に限定すれば近いが、スコープ未記載では過大である。例えば `orchestrator/campaign/s6_proposal_rounds.py:120-123` に opened 集合の独立 hard-code がある。歴史的凍結物として更新不要でも、「編集面の表現が3箸所だけ」とは言えない。

- **M5**: use-site の式一覧を container concept の確定と呼ぶのは過大である。probe の `iterator=T*` が iterator traits、proxy、swap、invalidation、実型の ownership/alignment を肩代わりしており、完全な契約を測っていない。

- **M7**: 「両 set 約5要素」は期待値であって実 set size ではない。重複 key と `searchWriteSet()` による coalescing があり、`plan.md:132` 自身が固定値ではないと訂正している。「定常 allocation は起きない」も vector の backing capacity に限られ、`WriteElement`/`TupleBody` の payload allocation や warm-up 前は覆わない。

- **M9**: `CompileOptions.cmake:1` が裏取るのは C++20 要求だけで、pegasus02、g++ 11.4、g++-12、g++-13 不在はその一次資料からは裏取れない。親が別途 shell 実測した可能性はあるが、brief の「すべて file:line 裏取り済み」という表現とは不一致である。

- **G2**: caveat は付いたが、`SmallVec` を「hole 内 nested type」と呼ぶ事実記述が誤っている。実体は `probe_contract.cc:39-40` の namespace-scope template である。したがって緑が支持する範囲は brief 自身の caveat よりさらに狭い。

- **訂正後結論**: alias 化 2 種という数え方は、現存する `std::vector<WriteElement<Tuple>>` の型綴りを置換する分類としてのみ支持される。実 nested type、全 TU、macro matrix、iterator/lifetime、M11 の意味修復まで含めた「構造的実現可能性」の証拠にはならない。

- **P1**: 「難所が濃いから第一候補」は採用理由になっていない。性能機序は未実測で、最も広い信頼境界を先に開く選択になっている。

- **P2**: 単一 marker の物理配置は可能でも、任意 C++ 型を安全に隔離できることは示していない。alias 化の個数と正しさ防壁の成立を混同している。

M1、M3、M4、M6、M8、M10、訂正後の M11、および撤回後の G1 の lookup 結論には、記載された限定範囲を超える追加の過大表現は見つけなかった。

テストは実行しておらず、緑の主張はしていない。