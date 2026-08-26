### 所見 1: 独立 archive hash は生成元の正当性を束縛せず、任意の archive を自己認証できる

- 深刻度: blocker
- 壊れる経路: clean な `masstree-src` から prebuild を開始するが、環境の `PATH` に細工した `make`、`ar`、`ranlib`、`autoreconf`、または `CXX` を置く。CMake 自体には検証済み compiler を渡しても、custom command は plain な `./bootstrap.sh`、`./configure`、`make`、`ar`、`ranlib` を継承環境で実行する。細工した tool は fixture と同じ `config.h` を残しつつ、悪性の `*.o` を `libkohler_masstree_json.a` へ格納できる。floor binding は生成後の archive hash を初めて観測し、その値自体を権威として buildcache へ渡すため、canonical root、manifest、HEAD、config、archive の全照合が通る。ycsb はその archive を link するが、oracle は archive も生成 tool も一切見ていない。
- 根拠: `external/ccbench/cmake/ThirdParty.cmake:66-87`、`orchestrator/campaign/buildcache.py:1750-1826,2824-2837`、`orchestrator/campaign/s8b_floor_campaign.py:2913-2928`、`s2-plan.md:96-113,136-145`
- 成果物影響: 悪性 ycsb binary が certified 選択へ入り、材料レポートと試行台帳には canonical manifest/config、自己観測された archive hash、悪性 binary hashが相互整合した値として残る。
- 提案: prebuild が使う `CC`、`CXX`、`make`、`ar`、`ranlib`、autotools 群を検証済み absolute tool identity へ束縛して recipe に明示するか、archive に独立した期待権威を設ける。この範囲を本 wave から外すなら、因果束縛を閉じたという主張を撤回し、裁定パッケージとして分離する。

### 所見 2: 「受理集合を 1 bit も広げない」は合成された floor 経路では偽である

- 深刻度: must-fix
- 壊れる経路: 従来は 196 file の実 source root を直接渡すため必ず `dependency-file-set-mismatch` だった。同じ実 source を入力しても、新経路は 101 file へ射影して PASS する。したがって primitive な `_verify_dependency_root` の受理集合は不変でも、`実 source root → floor PASS` の合成受理集合は空集合から拡大する。この拡大を正当化できるのは、canonical の全 file が実効 build root の working-tree bytes と一致し、config、archive、HEAD、実効 CMake rootが束縛され、宣言外入力が最終 build に影響しない条件下だけである。所見 1、3、4、5 の状態では正当化できない。
- 根拠: `BRIEF.md:10-11,31-41`、`s2-plan.md:7-10,136-151`、`orchestrator/campaign/sort_swo_oracle.py:1827-1848,1900-1902`
- 成果物影響: certified 選択の受理集合が意図的に空から非空へ変わり、従来存在しなかった PASS receipt、build 記録、試行台帳行が生成される。
- 提案: 「oracle 単体の root predicate は不変」「floor の合成受理集合は等価射影に限って拡大」と分けて規定し、等価性の前提と未閉鎖境界を成果物にも明記する。

### 所見 3: 宣言外の configure、GNUmakefile、object を使う A→B→A build は全再照合を通過する

- 深刻度: 裁定パッケージ候補
- 壊れる経路: oracle と configure 後検査が材料 A を確認した後、同一 UID の別 process が archive または config を削除し、`GNUmakefile`、`configure`、`config.h.in`、`*.o` を B に差し替える。`cmake --build` は `masstree_build` の custom command を再実行し、B の archive/config から ycsb を作る。link 完了後、検査前に全生成物を A へ戻す。プランの検査はすべて A を再観測して通り、binary だけが B 由来になる。これは安定した改変なら二根照合で拒否されるが、build 中だけの改変では拒否されない。
- 根拠: `external/ccbench/cmake/ThirdParty.cmake:57-87`、`orchestrator/campaign/buildcache.py:2318-2361`、`s2-plan.md:147-151,211-213`、`ADJACENT-ITEMS.md:9-21`
- 成果物影響: certified 選択は B 由来 binary を受理し、材料レポートと試行台帳は A の manifest/config/archive と B の binary hash を正当な組として記録する。
- 提案: なし。本件は T-1799 の書込み権威と T-1805 の compiler input 証明に属し、本 wave で先取りできない。ただし本 wave の保証境界から明示的に除外する必要がある。

### 所見 4: mimalloc の持続的改変は新しい二根 gate の外を通る

- 深刻度: 裁定パッケージ候補
- 壊れる経路: staged 3依存の初回 clean 検査後、oracle 実行前後に `mimalloc-src` の source または生成物を改変する。新 helper と buildcache の完全検査は `masstree-src`、canonical root、masstree archive しか再観測しない。ycsb は `ccbench::mimalloc` を直接 link するため、改変が持続しても全 masstree gate が通る。
- 根拠: `external/ccbench/cmake/ThirdParty.cmake:90-116`、`orchestrator/campaign/s8b_floor_campaign.py:2570-2735,3551-3600`、`ADJACENT-ITEMS.md:25-30`
- 成果物影響: certified 選択、材料レポート、試行台帳はいずれも改変 mimalloc 由来 binary を masstree 材料が正しいという理由だけで受理する。
- 提案: なし。これは既起票 T-1800 の範囲である。masstree の宣言外中間物とは、最終 archive/config の持続改変が検出される点で完全な同型ではない。

### 所見 5: resume は新 gate を一度も通らず禁止前 binary を再受理できる

- 深刻度: 裁定パッケージ候補
- 壊れる経路: 禁止前に作られた durable manifest と binary/store hash を用意し、resume 経路へ入る。resume は `build_v2` を呼ばないため、canonical materialization、二根検査、post-oracle capability の必須化が一度も発火しない。既存 hash の自己整合だけで古い binary が再利用される。
- 根拠: `ADJACENT-ITEMS.md:22-23`、`s2-plan.md:104-113`
- 成果物影響: certified 選択と試行台帳は新 gate 導入前の binary を引き続き受理し、材料レポートにも canonical/source equivalence の実行記録が増えない。
- 提案: なし。T-1804 のユーザー裁定待ちである。

### 所見 6: portable 成果物は actual-to-canonical 等価検査を永続化しない

- 深刻度: 裁定パッケージ候補
- 壊れる経路: live run では二根照合が成功しても、lease cleanup 後に残る portable SWO receipt は canonical の manifest/config と binary hashしか持たない。actual HEAD、archive、tracked bytes 等価検査の結果や検査 policy IDは portable built recordへ入らない。後段 consumer は「その二根検査が実行された run」と、同じ公開値を合成した記録を独立に区別できない。
- 根拠: `s2-plan.md:102-124,202`、`orchestrator/campaign/s8b_sort_swo_receipt.py:49-56,188-216`、`orchestrator/campaign/s8b_binary_admission.py:40-58,348-359`、`orchestrator/campaign/s8b_floor_campaign.py:4387-4416`
- 成果物影響: certified 選択は producer の live gate に依存する一方、材料レポートと試行台帳からは canonical-to-actual の因果辺を再検証できず、参照は oracle receipt と binary hashで途切れる。
- 提案: なし。正式受入が実行事実まで証明する変更は T-1805 に属する。現 wave では少なくとも `producer-execution-contract` として保証水準を限定して記述する。

### 所見 7: config.h の一致は機体依存であり、別環境では成功集合が再び空になる

- 深刻度: must-fix
- 壊れる経路: libnuma や header の有無、32/64 bit、endianness、compiler の builtin/C++ feature、autoconf/autoheader の生成形式が現在機と異なる機体で prebuild する。生成 `config.h` の digest が fixture と変わり、生成 `SHA256SUMS` の hashが pin と一致しない。設計は `_prepare_verified_dependency` で fail-closed になるため悪性 PASSにはならないが、対象 production 機で `sort_best` 到達数が再び 0 になる。
- 根拠: `orchestrator/tests/fixtures/sort_swo_masstree/configure.ac:12-21,123-215,297-312,337-369`、同 `config.h:22-76,258-291`、`orchestrator/campaign/sort_swo_oracle.py:1900-1902`、`MEASUREMENTS.md:139-157`
- 成果物影響: certified 選択に床値 armが入らず、材料レポートは canonical manifest mismatch、試行台帳は build/bench 未到達となる。
- 提案: 実際に floor を走らせる各機体/toolchain classで、prebuild 後の `<effective_base>/masstree-src` から生成器までを正例実測する。現在機の二 base 一致を他機体へ一般化しない。

### 所見 8: 同一 bytes でも oracle から完全に区別不能ではない

- 深刻度: nit
- 壊れる経路: oracle は root の symlink/type、realpath、path containment、読み取り可否を観測し、compile commandにも private root の絶対 pathを `-I` として渡す。raw receiptには `dependency_root_realpath` が入るため、同じ bytes の二走行でも private root pathが異なれば raw receiptとその commitment hashは異なる。owner、mtime、inode、mount identity自体は比較しないが、それらによる permission/path resolution失敗は結果へ反映されうる。
- 根拠: `orchestrator/campaign/sort_swo_oracle.py:1796-1848,1945-1971,2631-2639`、`orchestrator/campaign/s8b_sort_swo_receipt.py:162-186,211-213`
- 成果物影響: certified 選択の PASS/REJECTは通常変わらないが、private 材料レポートの root参照と portable receiptの `receipt_sha256` は同一 bytesでも変わりうる。試行台帳の portable content authority自体は manifest/configで不変。
- 提案: 「受理判定に必要な file bytesについて同値」と限定し、「oracleから区別不能」という表現を使わない。

### 親 brief への攻撃 (実測値とその一般化を含む)

`MEASUREMENTS.md:103-109` の訂正どおり、`dependency.source_root` と buildcache の `<base>/masstree-src` は同じ pathである。旧記述の basename 食い違いは所見に採用しない。

tracked 改竄について、プランは index から path名を得るが bytes は root fd経由で working treeから読む。したがって tracked fileの working-tree改竄は canonicalへそのまま褭写され、manifest pin mismatchで停止する。indexだけの path追加・削除も path集合を変えて停止する。この範囲では汚染を洗い流さない。一方、untracked/ignored fileは明示的に捨てるため、`configure`、`config.h.in`、`GNUmakefile`、`*.o`、archiveを実 source側に残したまま canonicalだけを清浄化する。その正当性は、それらの効果が検査済み config/archiveへ完全に縮約される場合に限る。所見 1と3がその前提を壊す。

manifest pin一致が直接証明するのは `SHA256SUMS` bytesが固定値と一致することだけである。宣言外 regular fileがないことは `_verify_dependency_root` の actual/declared 集合照合が証明する。さらに verifierは宣言外の空 directoryや mount identityを拒否せず、scan間の一時改変も証明しない。プランが `_prepare_verified_dependency` を必須再利用する限り、永続する追加 regular fileは fail-closedだが、pin単独を inventory保証と説明してはならない。

101/196 の line listには隠し path自体は含まれている。しかし line形式は改行を含む filenameを表現できず、hardlink関係、同一 inode、mount境界、Unicode正規化関係を記録しない。新 generatorの NUL出力・UTF-8 strict検査は異常な tracked pathを拒否するので黙った PASSにはなりにくいが、hardlinkなど実 sourceの topologyは canonical copyで失われ、実 build側には残る。従って「100 pathの bytes一致」は topologyを含む build同値性の証明ではない。

### scope 判定

T-1798 の scope内で閉じるべきなのは、canonical exact verification、実 sourceの working-tree bytes/config/HEADとの等価照合、実効 CMake source root、archive continuityである。ただし所見 1の archive生成権威は、この waveが掲げる因果鎖の構成要素そのものであり、未解決のまま「archiveまで束縛した」とは受理できない。

T-1799、T-1805の immutable build snapshot/A→B→A、T-1804の resume、T-1800の mimalloc/googletestは隣接項目として scope外である。これらは実装したふりをせず裁定または既存 ticketへ残す必要がある。portable成果物による実行事実の独立証明もT-1805側である。

## 総括

プランの canonical verifierと working-tree二根照合は、持続する tracked/config改変には fail-closedである。しかし composed floor受理集合は明確に拡大し、archive生成 toolの未束縛によって、oracleが見ていない悪性 archiveを正規材料として固定できる blockerがある。加えて、build中の再生成、他依存、resume、durable証明は既起票境界に残る。

pytestその他の実走は行っていない。指定資料とコードの静的検査のみである。