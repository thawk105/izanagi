# D297 header 差分の条件つき受理規則 — 設計 plan

## 第 1 部 — 規則の設計

### 1. 現行の拒否点と差し込み点（P1）

現行検査器は `git diff-tree --raw -r` で差分を列挙し、空差分、M 以外の status、mode 変更、通常ファイル以外を拒否する。その後、header 拡張子を一律拒否する。`.cc` 等は変更 file **単体**を比較する。比較は include 行列、`-E -P -dD -nostdinc` による正規化出力、include marker の活性を対象とし、mocc の `trace.hh` 一行追加だけに既存の例外がある。比較文脈が空なら拒否し、file ごとの期待 16 件と実件数も照合する。[checker](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/tools/check_trace0_preprocess_identity.py:131) [差分検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/tools/check_trace0_preprocess_identity.py:180) [単体比較](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/tools/check_trace0_preprocess_identity.py:516) [件数検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/tools/check_trace0_preprocess_identity.py:636) [全体制御](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/tools/check_trace0_preprocess_identity.py:651)

実装位置は次のように限定する。

1. `_validate_diff()` の header 一律拒否だけを「M・mode 不変の既知 header 拡張子」として分類する分岐に替える。A/D/R/C、mode 変更、非 C/C++ の拒否は残す。`.cc` の `_compare_file()` と mocc 一行例外もそのまま呼ぶ。[checker](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/tools/check_trace0_preprocess_identity.py:180) [checker](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/tools/check_trace0_preprocess_identity.py:421)
2. `check()` 内で header が一つでもあれば、旧・新 commit の固定 source tree と build 文脈から compile database を得て、consumer 選定、TU 比較、件数照合を行う関数群を追加する。複数 header を読む同じ entry は一度だけ比較し、report には header 別の依存関係を残す。`.cc` 差分が同居すれば既存の単体比較も必須とする。[checker](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/tools/check_trace0_preprocess_identity.py:673)
3. `SCHEMA` を v3 に上げ、既存 `files` の単体比較結果と、新しい `consumer_tus`、文脈・compiler・依存列挙・期待件数・実件数を区別して記録する。`--expect-paths` は引き続き raw diff 全 path の厳密照合とする。既存 report v2 の意味を黙って変えない。[checker](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/tools/check_trace0_preprocess_identity.py:43) [checker](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/tools/check_trace0_preprocess_identity.py:204) [checker](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/tools/check_trace0_preprocess_identity.py:708)
4. CLI には header 経路用の build 作業 root、依存 source/prefix の固定入力、build 文脈の選択を明示する引数を足す。既存 `--cxx` は一走一 compiler のままとし、GCC 11.4 と 12.3 の二走を要求する手順・report 照合にする。header が無い既存呼出しは新引数を要しない。既存 pilot は `--expect-paths cc/mocc/transaction.cc` を指定しており、この経路は維持できる。[CLI](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/tools/check_trace0_preprocess_identity.py:728) [pilot](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/tools/pegasus/mocc_trace_pilot.sh:1895)

### 2. consumer TU の母集合（P2）

母集合は、選定した各 CMake configure の **compile database の全 entry** とする。`file` だけではなく target と compile argv を含む entry を鍵にする。同じ `transaction.cc` が ycsb、tpcc、bomb、sbomb の別 target に現れるためである。旧・新それぞれで、全 entry に実 argv を基礎として `-M -MG` を実行し、TRACE=0 と TRACE=1 の依存集合を取る。各変更 header を旧・新 × 両 TRACE 値のいずれかで読む entry の和集合を consumer とする。**文脈ごとに**依存を取り直す。条件付き include が genome define で変わるため、stock 一構成の依存集合を他の文脈へ流用できない。[親実測](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/s1-brief.md:21) [実測 script](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/evidence/consumers.py:28) [probe の entry 鍵](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/run_probe.py:317)

依存列挙では `-c`、出力指定、既存の依存出力指定を除き、コンパイラ・include path・define・言語指定を保持する。TRACE=1 の照会では argv 中の既存 `-DTRACE=0` を明示的に取り除くか上書きの順序を検証し、最終的な TRACE 値を記録する。`-MG` は欠落 header も依存として出せるため、終了コード、依存出力の parse、変更 header の実在、後段の完全前処理成功をすべて要求する。未知の response file や `-Wp,` のような不透明 argv は推測して処理しない。単位 11 の probe には出力 option 除去の参考実装があるが、consumer 選定は直接 include の正規表現なので流用先を分ける。[probe argv](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/run_probe.py:357) [probe consumer](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/run_probe.py:317)

変更 header **ごと、選定文脈の和集合で consumer 0 件なら拒否**する。各文脈では consumer 0 件があり得るが、その文脈の全 entry の依存走査を省略した結果であってはならない。旧新の compile database は source/build root を置換して entry 集合と argv を比較し、意図しない target・define・flag の変化を拒否する。ただし root 正規化は確認済みの prefix に境界を付けて行い、任意の同名部分文字列を消さない。親の stock 実測では両側 135 entry、78 file、変更 header の consumer は 21 entry、12 file、依存列挙 error 0 である。これは選定した一構成だけの事実である。[brief](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/s1-brief.md:23) [C 側一覧](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/evidence/consumers-c.txt:1) [C2′ 側一覧](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/evidence/consumers-c2p.txt:1)

compile database に存在しない TU は保証範囲外と明記する。configure されない target は現れず、生成 source は生成後に entry と実 file を確認できる場合だけ扱える。FetchContent の第三者 source は database に含まれても、変更された CCBench header への依存が無ければ consumer ではない。外部 source が依存すると判明した場合は黙って除外せず、その固定 source と argv で比較するか、未対応として拒否する。全 `.cc` の前処理から探す方式は未 configure target を増やせるが、実 argv を失い、生成 source を含む完全な母集合にもならない。全 database entry を完全比較する方式は列挙漏れには強いが、header 非依存の第三者 TU まで比較して費用と環境由来の不一致を増やす。本案は**選定された configure の変更 header 消費者**に保証を限定する。[CMake target 登録](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/external/ccbench/CMakeLists.txt:78) [D780](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/verbatim/D780.md:5)

### 3. TU ごとの文脈（P3）

production の `_v2_commands()` は Release、sanitizer OFF、指定 C/C++ compiler、`genome.cmake_defines()`、`-DCCBENCH_TRACE=0` を configure に渡し、必要に応じ dependency prefix、FetchContent の固定 source、binary path policy の `-fmacro-prefix-map` を加える。通常の build target は `ycsb_<protocol>.exe` だが、CMake configure 自体は TPC-C target の compile entry も生成する。検査器の header 経路はこの configure 条件を再現し、`CMAKE_EXPORT_COMPILE_COMMANDS=ON` を追加して得た **target ごとの実 argv** を使う。TPC-C の entry は比較対象に含める一方、production が TPC-C binary を build したという主張はしない。[buildcache](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/orchestrator/campaign/buildcache.py:1949) [prefix map](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/orchestrator/campaign/buildcache.py:1916) [CMake target](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/external/ccbench/cmake/ProtocolHelpers.cmake:29)

文脈集合は `SPACES` に登録された silo 8、mocc 8、tictoc 24、cicada 24 の有効 genome を基礎にする。それぞれの genome で configure し直し、**その protocol の target entry** に当該文脈を対応させる。空間を持たない ermia、mvto、oze、si 等は stock configure を使う。`ccbench_common` のような共有 target が変更 header の consumer になれば、選定 configure ごとの実 argv を別文脈として扱う。全 configure の全 target を無差別に「その target の production 文脈」と呼ばない。これは費用を抑える選択でもあり、異 protocol の configure による偶発的な define 組合せは保証に含まない。[genome](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/orchestrator/campaign/genome.py:20) [空間](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/orchestrator/campaign/genome.py:106) [登録](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/orchestrator/campaign/genome.py:208)

現行の 16 文脈は silo 8 × `GLOBAL_VALUE_DEFINE` 無／有で、実 compile command 16 本ではない。TU 比較では source 冒頭の `#define GLOBAL_VALUE_DEFINE` を実前処理が読むため、その人工的な無／有 overlay は外れる。一方、silo 以外の protocol と実 target define、TPC-C target、実 include 順が加わる。mocc の `RWLOCK` 等も target argv から得る。workload 別 define は現行 CMake に無く、共有 `transaction.cc` を workload だけで別 macro 文脈とみなさない。target ごとに entry は比較する。これは D2225 の切替理由と一致する。[現行 16](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/tools/check_trace0_preprocess_identity.py:678) [overlay](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/orchestrator/campaign/source_digest.py:1712) [D2225](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/verbatim/D2225.md:11)

### 4. 比較と実行場所（P4・P5）

選ばれた各 consumer entry を、旧・新の対応する argv で `-E -P -dD` により**include を残した完全展開**として比較する。別に `-E` の line marker から、include file への入場・退出を示す flag 1/2 と file の順序列を抽出して比較する。通常の行番号 marker は完全展開の `__LINE__` 等への効果に委ねる。source/build root は対応する絶対 prefix だけを同じ論理 root に置換し、第三者依存 root は同一固定 source に結び付ける。`__FILE__` と `__BASE_FILE__` は `-fmacro-prefix-map` と root 正規化の双方の効き方を試験する。`__DATE__`、`__TIME__`、`__TIMESTAMP__` が出力へ混入するなら、その値を安易に消して緑にせず、再現条件を固定できなければ拒否する。空出力や前処理失敗も拒否する。単位 11 の stream 正規化は出発点になるが、line marker の厳密 parse と root 衝突の試験を要する。[probe](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/run_probe.py:377) [D297](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/verbatim/D297.md:13)

GCC 11.4 と 12.3 は、それぞれの compiler を指定した **別の CMake configure と database** を作り、一 compiler 一 report で両方 pass を求める。既存 database の argv[0] だけを別 compiler に差し替えると、compiler 固有の flag、system include、CMake 検出結果を取り落とす。report には compiler 実 path・版・文脈・entry 鍵を残し、二走の期待集合を照合する。D2150 の先例もこの二版で足りるとしたが、admission toolchain の同一性は主張していない。[checker compiler](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/tools/check_trace0_preprocess_identity.py:227) [D2150](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/verbatim/D2150.md:22)

期待件数は比較ループの結果から逆算しない。まず全文脈の database entry 集合と、旧・新 × TRACE=0/1 の依存結果から header→consumer の予定表を固定する。その予定表の unique `(compiler, context, target, source)` を期待 TU 比較集合とし、実行済み集合と厳密一致させる。header ごとの consumer 数、文脈ごとの entry 数、両 compiler の report 数も記録する。現行の比較 0 件・期待 16 件の拒否と同じ意図を TU 側にも持たせる。[checker](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/tools/check_trace0_preprocess_identity.py:636) [D297](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/verbatim/D297.md:20)

source は二つの一時 Git worktree から取り出し、比較 OID の tree と tracked file の blob/mode/path を照合する。`git archive` は `export-ignore` のため `cc/oze` を落とすので使えない。FetchContent の masstree、mimalloc、googletest は双方で同じ固定 source/OID と receipt を使い、動く tag やネットワーク取得結果へ委ねない。`masstree_build` は `config.h` を生成するため、configure の後にその target を build してから依存列挙・前処理を行う。親の login 上の全 TU 前処理は `config.h` 不在で失敗した。全 TU・複数文脈の走行は計算ノード job として設計し、login での本走を要求しない。[brief](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/s1-brief.md:21) [ThirdParty](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/external/ccbench/cmake/ThirdParty.cmake:57) [buildcache の固定 source 引数](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/orchestrator/campaign/buildcache.py:1964)

### 5. 保証名（P6）

docstring、`GUARANTEE`、v3 report には「**選定した build 文脈の変更 header 消費者 TU における TRACE=0 完全展開と include 活性の同一性**」と書く。`.cc` 単体比較の既存保証も report 内で別名・別欄として残す。成果物側には D780 項 1 の「この検査は D297 の保証を証明するものであり、計測ビルドからの trace 完全除去に対しては必要条件の一つである」を継承する。これは source を比較する pin 前進検査であり、admission build の全 TU、link object、trace symbol/data、build receipt を一つに結ぶ D780 項 2 の別防壁ではない。[checker 冒頭](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/tools/check_trace0_preprocess_identity.py:3) [D780](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/verbatim/D780.md:5)

D774 の「静的に解決できない CMake 間接値を供給と主張しない」限界は据え置く。実 database は選定 configure の実効 argv を示すが、すべての実 build define の不在証明にはならない。D297 制定時の「`-E -P` は `#define` を残さない」は現行 `-dD` で部分的に解消済みであり、header 拒否の残る理由は consumer の文脈と include 順である。D2207 の mocc `.cc` include 行を緩めない裁定も維持する。header の条件つき受理は D297 の新しい裁定を要するが、`.cc` include 例外を拡大しない。[D774](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/verbatim/D774.md:3) [正規化実装](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/orchestrator/campaign/source_digest.py:1666) [D2207](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/verbatim/D2207.md:1)

## 第 2 部 — 受理集合の変化と偽緑の面

新たに受理されるのは、M・mode 不変の header 差分があり、選定文脈の consumer が存在し、その全 TU の TRACE=0 完全展開と include 活性が一致する場合である。C→C2′ の `trace.hh` の TRACE 側 helper、`tpcc.hh` の条件付き include・setter・`#if !TRACE`・`#line` はその候補形であり、**この設計だけでは合格を確定しない**。親の stock 21 entry の実測と単位 11 の一走は、GCC 12.3 と genome 文脈の正例を代替しない。[header 差分](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/external/ccbench/include/tpcc.hh:24) [brief](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/s1-brief.md:23)

| 攻撃面 | 止める規則／残る穴 |
|---|---|
| 間接 include の consumer を直接 include 検索から漏らす | 全 database entry の依存列挙で止める。単位 11 の直接検索がこの stock 構成で 21 件一致した事実は、一般的な閉包証明ではない。[probe](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/run_probe.py:317) [実測](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/evidence/consumers-c2p.txt:1) |
| TRACE=1 にだけ現れる依存、または旧側だけの依存を漏らす | 旧・新 × TRACE=0/1 の和集合で止める。C2′ では TPC-C 9 file が TRACE=1 で `trace.hh` も読む。[実測](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/evidence/consumers-c2p.txt:4) |
| genome、target、build type、compiler の選び漏れ | 登録 genome の protocol 別 configure、target entry、Release、GCC 二版で選定範囲を止める。未登録 genome、Debug、別 compiler、将来の production option は残る穴。[buildcache](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/orchestrator/campaign/buildcache.py:1949) [genome](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/orchestrator/campaign/genome.py:208) |
| header の `#if !TRACE` 側を変え、性能 build の code を変える | TRACE=0 の完全展開差で拒否する。`#line` を外して `__LINE__` が変わる形も単位 11 の H-line で検出済み。[D2225](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/verbatim/D2225.md:6) [H-line](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/output/insights/2026-09-26/t2854-unit11-combined/README.md:77) |
| header の `#define` を変えるが、現在の consumer では未使用 | `-dD` は有効枝の定義を残すため多くは拒否する。ただし未選定 TU・別文脈で初めて使う定義は残る穴。[source_digest](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/orchestrator/campaign/source_digest.py:1666) |
| root 置換で異なる `__FILE__` 等を同一化する | prefix 境界・置換前後の記録・`-fmacro-prefix-map` の再現で過剰置換を抑える。意図的に論理 root へ畳んだ実 path 差自体は比較対象外。[buildcache](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/orchestrator/campaign/buildcache.py:1916) |
| `#line` で line marker を操作する | 完全展開上の `__LINE__` 等の変化は検出する。入退場以外の marker を捨てる設計では、診断位置だけの差は保証外。flag 1/2 の偽装や parser 曖昧性は合成試験で拒否側に倒す。[probe](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/run_probe.py:390) |
| configure されない target、生成 source、第三者 TU | 選定 database に無ければ覆わない。変更 header が第三者 entry に到達した場合は比較または拒否し、無言で除外しない。[CMake](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/external/ccbench/CMakeLists.txt:78) |
| `CCBENCH_TRACE`→`-DTRACE` の経路を迂回し、比較と性能 build の値をずらす | configure argv と entry の最終 TRACE=0 を検査し、依存照会の TRACE=1 切替も確認する。それでも実 admission build・receipt との結合は D780 項 2 の未実装防壁に残る。[Options](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/external/ccbench/cmake/Options.cmake:13) [D780](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/verbatim/D780.md:7) |

現行の `.cc` 単体比較が拒否する include 行変更、未知マクロ、比較 0 件などは新規則でも拒否し続ける。header と `.cc` が同時に変わる場合に `.cc` 単体比較を省略すると、従来止めた変更を通すため、**両検査の積**を必須にする。他方、現行は header のコメントだけの変更も拒否する。新規則はそのような差分も条件を満たせば受理し、これは意図した受理集合の拡大である。[単体比較](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/tools/check_trace0_preprocess_identity.py:539) [条件 macro 検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/orchestrator/campaign/source_digest.py:1844)

## 第 3 部 — 実装時の検査・変異と費用（P7）

合成 fixture では小さな CMake project の複数 target と間接 include を用意し、旧新 database の対応、TRACE 両値の依存和集合、同一 source の target 別 argv、consumer 0 件、欠落 header、期待件数、root 正規化、`#line`、compiler 切替を個別に検査する。既存の header 拒否 test は「consumer を構成できない header は拒否」と「構成できた header は条件つき受理」に分け、A/D/R/C・mode・非 C/C++・`.cc` include 行・mocc 一行例外の既存 test を残す。実 CCBench の C→C2′ は二版の GCC、選定 genome 文脈で正例を取り、各 report の予定表と実行済み集合を照合する。[既存 fixture](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/orchestrator/tests/test_check_trace0_preprocess_identity.py:110) [既存 header test](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/orchestrator/tests/test_check_trace0_preprocess_identity.py:623) [既存件数 test](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/orchestrator/tests/test_check_trace0_preprocess_identity.py:638)

変異は実装前に期待する**最初の拒否理由**を登録する。依存列挙や build の失敗を、本来の比較による kill と取り違えない。[単位 11 の変異記録](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/output/insights/2026-09-26/t2854-unit11-combined/README.md:73)

| 変異 | 期待する拒否理由 | 間接 consumer の合成 |
|---|---|---|
| header の TRACE=0 側の値、`#define`、`#if !TRACE` 内の値を変える | 完全展開不一致 | 不要 |
| 必須 include を `#if TRACE` 内へ移す | 完全展開または include 活性の不一致 | 不要 |
| `tpcc.hh` の `#line 56` を削除する | TPC-C consumer の完全展開不一致 | 不要。実 CCBench H-line を再利用可 |
| 直接 include を持たず、別 header 経由だけで変更 header を読む TU を作る | 値変更は完全展開不一致。直接 include 列挙へ劣化させた実装を殺す | **必要** |
| 変更 header の consumer を全文脈で 0 件にする | header 別 consumer 0 件 | 不要 |
| 比較予定表から一件を実行時に落とす | 期待集合と実行済み集合の不一致 | 不要 |
| CMake file を変更する | 非 C/C++ 差分の拒否 | 不要 |
| `.cc` の既存 include 行を変え、header 差分も同居させる | `.cc` include 行不一致 | 不要 |

費用は**上限ではない推測**である。実装、合成 fixture、実 CCBench 正例、変異、敵対レビュー・修正で Codex author **1 wave を起点に、修正を含め 1〜2 wave 以上**を見込む。単位 11 の stock・GCC 11.4 の結合 job は 243 秒、約 0.07 node 時間だったが、今回は 64 genome 文脈の configure、二 compiler、旧新、依存走査が加わる。重複 argv の安全な集約と FetchContent の再利用次第で変動が大きく、初回の計算予算は**数 node 時間の暫定枠**として実測後に改めるべきで、0.07 node 時間の単純な倍率を確定費用とはしない。既存 probe の compile argv 除去、前処理・marker 正規化、source tree 照合は部品として参照できるが、直接 include 列挙と stock 一構成の固定 21 件は受理器へ流用できない。[insight の実績](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/output/insights/2026-09-26/t2854-unit11-combined/README.md:53) [probe](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/run_probe.py:317)

## 第 4 部 — 承認事項案（P8）

裁定には三つの問いを**順番を付けて別々に**出す。[D2249 項 2](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/verbatim/D2249.md:46)

1. **規則案を承認するか。** 承認なら D297 の「header 一律拒否」を、上記の選定 consumer TU・選定 build 文脈による条件つき受理へ改訂する。却下なら現行 D297 を維持し、C2′ は拒否されたまま。修正指示なら母集合・文脈・保証名を確定してから再審査する。[D297](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/verbatim/D297.md:3)
2. **承認した規則の実装を委任するか。** 委任なら検査器・既存 test の追随・合成 fixture・事前登録変異・計算 job・敵対レビューを実装 wave の範囲にする。委任しなければ設計承認だけを記録し、検査器と pin は現状のまま。[request](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/request.md:3)
3. **C2′ pin 前進を承認するか。** 実装済み検査器で C→C2′ が GCC 11.4/12.3 の選定文脈を pass し、別途 pin 更新の波及が確認された**結果を見てから**問う。承認なら gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` を同一変更で前進させる手番へ進む。否認なら pin C を維持する。条件つき事前承認は推さない。未実測の GCC 12.3・genome 文脈や D2184 の policy 波及を合格前に引き受けることになるためである。[D2150 の先例](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/verbatim/D2150.md:26) [D2184](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/verbatim/D2184.md:3)

## 総括

- **P1・P2・P4・P6:** 条件つき採用。header だけを新分岐にし、実 database の依存和集合と完全 TU 比較を使う。`.cc` の既存拒否は併用する。[checker](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/tools/check_trace0_preprocess_identity.py:180)
- **P3:** 概ね賛成。ただし genome configure 全体の全 target を production 文脈と同一視せず、protocol・target に対応付ける。現行 16 文脈との保証差を明記する。[buildcache](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/orchestrator/campaign/buildcache.py:1949)
- **P5:** 賛成。`masstree_build` と固定 FetchContent source を含む計算 job が必要。[ThirdParty](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-d297-header-review/external/ccbench/cmake/ThirdParty.cmake:66)
- **P7・P8:** 賛成。変異には間接 consumer を必ず含め、規則承認、実装委任、pass 後の pin 承認を分ける。費用見積りは上限ではない。[brief](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/s1-brief.md:18)
- **残る穴:** 選定 database 外の TU・文脈、別 compiler、実 admission の全 TU・link object・trace symbol/data・receipt との未結合。従って trace 完全除去の証明とは呼ばない。[D780](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/verbatim/D780.md:5)
- **未確定事項:** GCC 12.3 と genome 文脈の C→C2′ 正例、compile argv の安全な集約率、全 job の実費。これらは実装 wave の計算実測で確定する。今回の作業は指定どおり静的審査のみで、編集・build・test は行っていない。[brief](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-d297-header-review/s1-brief.md:26)