## レンズ A

必読資料はすべて読めた。以下では test file を **T**、`t080_freeze_migration.py` を **M** と略記する。pytest・probe・Git の挙動実験は実行していない。Git の機序は実装知識と公開一次資料で照合したが、計算ノードの実バージョンでの確認は selftest に残る。

**must-fix A1 — `.git-ref` の退避場所が worktree を汚染し、submodule の再初期化も自己完結になっていない。**

- **根拠:** brief「計測設計」2・3、T:1520〜1528、T:1015 前後の `copytree(..., symlinks=True)`。
- **成果物への影響:** fixture 直下の `.git-ref` は `.git` のような特別除外ではない。A/C1 の `add -A` がその内容を取り込み、参照 tree 不一致または status 非空で試行が失格になる。modules symlink のコピーは外部参照・共有変異も残す。
- **是正案:** 参照 `.git` は fixture worktree **外**に置く。各試行では modules を元の `.git/modules` 位置へ実体コピーして、必要な config も復元する。この共通復元費用は別計上して timed 外に置ける。

現案どおり同じ深さの `.git-ref/modules` にリンクするなら、gitfile の相対参照と submodule の `core.worktree` が直ちに壊れるとは断定できない。Git による実パス解決後も相対深さが保たれれば動く。しかし、参照を worktree 外へ移すだけでは `core.worktree` が壊れ得る。selftest で gitlink OID、submodule の top-level、内部変更の status 検出まで確認すること。

`update-index --cacheinfo 160000` は gitlink 登録の代案にはなるが、submodule の有効な gitdir を復旧する代案にはならない。production の `--ignore-submodules=none` を通す以上、内部変更検出が必要である。

**must-fix A2 — C2 が参照する fixture 固有 blob の供給が欠落している。**

- **根拠:** brief「計測設計」2・4、T:1490〜1528、Git `update-index --index-info` / `write-tree`。
- **成果物への影響:** source に無い OID を「件数と path の記録」だけで済ませると、C2 は存在しない blob を index に登録する。`write-tree` または後続検査が失敗し、「下限」を測れない。
- **是正案:** source に無い blob は fixture の現物から正しい変換条件で生成し、その読み取り・ハッシュ・書き込みを **C2 の timed 区間に含める**。生成 OID が参照 OID と一致しなければ失格にする。参照 object store から補充する案なら、その移送費用を含め、実装候補では利用できない参照を使った模型と明示する。

`.gitmodules` だけに限定してはならない。historical basis の復元、distinct descriptor、source index と working tree の差もある。C1 は `add -A` が不足 object を生成するので、この欠落を自然に処理する。

同じ集合問題が「ハッシュ参照」にもある。参照 index 全 path をそのまま `hash-object --stdin-paths` に渡すと、gitlink はディレクトリなので失敗する。regular file を分離し、symlink は Git の blob 化と同じ意味で扱うこと。path の quoting、attributes/filter、実際の file 数・総 bytes も記録する。この値は純粋な SHA-1 時間ではなく、読み取り・変換・プロセス費用を含む参考値である。

**must-fix A3 — C1 の実用費用から OID 選定費用が抜け、pipeline と C2 の合計定義も曖昧。**

- **根拠:** brief P2・P5、「計測設計」2・4。先例 T-2708 §3-2 では source 側列挙が一般解の大部分だった。
- **成果物への影響:** 完成済み A の参照 index を無料で利用すると、採用位置では必要な path→OID 選定・存在確認を省いた値で「食わない」と判定し得る。
- **是正案:** 次の二量を区別する。
  1. 現仕様の「既知の OID 集合を与えた移送＋index 化費用」。
  2. 採用候補の「source 列挙・選定・存在確認＋移送＋add＋commit＋status1」。

裁定パッケージを返す主指標には後者が必要。前者だけ測るなら、**好条件での候補抽出**に結論を限定し、実用符号確認とは書かない。選定を session ごとに償却するなら、その共有方法と回数は未実装の模型として分ける。

`pack-objects | index-pack` は並行動作するため、両 subprocess の経過時間を足して移送 wall にしてはいけない。起動前から両方の終了までの外側 wall を主値にし、双方の rc・stderr を保存する。C2 の総計には仕様4にある `update-ref HEAD` も含める。Python 側の入力準備なども外側総時間との差として残す。

**must-fix A4 — main 初回を cold の代理と呼べない。**

- **根拠:** brief P4・P5、「計測設計」1・2・5・6。
- **成果物への影響:** 事前実験6回で同じ object を読んだ後の初回 C1 を cold と表示すると、受入の初回費用を過小評価した裁定パッケージになる。
- **是正案:** 「main 初回」「反復」とだけ呼ぶ。初回移送を取りたいなら事前実験より前に別記録するが、それも builder・存在確認・他プロセスによる cache 状態が未知なので **cold 未保証**とする。

A も builder の copy だけでなく、既存の `add`・commit・history 検査を済ませた同一 worktree を再利用している。受入は直前の copy でデータが温まりやすい点は同じだが、48 worker の競合、copy 後の処理、cache eviction は再現していない。交互5 round は同一環境での比較には有用だが、cold の被覆にはならない。

**must-fix A5 — P1 の機序は概ね正しいが、「真の下限」「それ以下は存在しない」は反証される。**

- **根拠:** Git `refresh_cache_ent` / `ie_modified` / `update_index_if_able`、`checkout-index -u`。
- **成果物への影響:** C2 を普遍的下限とすると、C1/C2 の結果だけで別の自己完結経路まで不採用と一般化してしまう。
- **是正案:** 「複製済み worktree を変更せず、空 stat の index を通常設定で検証する経路の参考費用」に限定する。

三段の主張は次の評価になる。

| 主張 | 評価 |
|---|---|
| 空 index に `--index-info` で作った entry の stat は未充足 | 支持。実際の入力方式は selftest で確認 |
| `GIT_OPTIONAL_LOCKS=0` の status は通常の任意 refresh 書き戻しをしない | 支持。メモリ内 refresh とディスク保存を区別する |
| したがって毎回24k file全部を再ハッシュ | 条件付き。通常の未充足 regular entry は再走査するが、gitlink・symlink、途中の明示書き込み、racy 判定等を区別する |

通常の regular file では stat 不一致から内容比較に進む。明示 `update-index --refresh` は必要な index 更新を行うので、optional locks の無効化だけでは保存を抑止されない。その後、未変更で非 racy な entry は stat 比較で済む。ただし「以後必ず lstat だけ」は過剰である。[Git の index refresh 実装](https://raw.githubusercontent.com/git/git/v2.43.0/read-cache.c)

反例候補は `checkout-index -u -f` による **blob からの再配置と stat 記録**である。任意の既存 bytes を未検証で信用するのでなく、Git 自身が書いた内容に stat を対応させる。別途の worktree 再ハッシュを必要条件にはできない。ただし展開・書き込み費用、filter、既存の source working tree 変更を上書きしない設計が必要で、今回の固定配置比較へ無料で挿入できるものではない。[Git checkout-index](https://git-scm.com/docs/git-checkout-index)

他の候補は以下の扱いが妥当。

- `--assume-unchanged` / skip-worktree：変更検出を弱めるので却下。
- `core.checkStat=minimal` / `core.trustctime=false`：stat の比較条件を変える。今回の同一検査条件から除外。
- `index.skipHash`：index ファイル自体の checksum の話で、worktree 内容検証を省く機能ではない。
- `--really-refresh`：assume-unchanged による省略を越えて調べる側。無料の stat 充填ではない。
- `read-tree --index-output`：出力先を変えても、新しい inode と blob の対応を無検証で証明しない。
- production status の迂回：M:1833・2012 に必要な検査があり、fixture 最適化だけで省けない。

機序の確信度は高い。実測 corpus の再走査件数と checkout 経路の適用可能性は未確認。

**should A6 — P2 は通常経路を支持するが、圧縮回避・object 集合の同一性に条件がある。**

- **根拠:** Git `write_object_file_flags` / `freshen_packed_object` / streaming・bulk check-in 経路、T:1527。
- **成果物への影響:** 「pack があれば圧縮・書き込みゼロ」と説明すると、観測された C1 費用の解釈を誤る。
- **是正案:** 通常の buffer 経路では、内容から OID を計算してから packed object を freshen し、成功すれば loose 作成を省く、と記述する。大きな blob の streaming/bulk 経路、freshen 失敗、Git バージョンによる差は別に確認する。

通常経路でも、空 index からの `add` は file を読み、変換後 bytes の OID を求める必要がある。freshen は pack の時刻更新とプロセス内の済フラグを伴い、失敗時の fallback もある。「常に mtime 更新以外の I/O は無い」とは言えない。[Git object-file 実装](https://raw.githubusercontent.com/git/git/v2.43.0/object-file.c)

同じ worktree・空 index・config・attributes・ignore 条件なら、pack の有無は `add` の path 選択を変えず、A/C1 の tree 一致を期待できる。delta 表現も blob identity を変えない。ただし、余分な blob の移送や異なる commit 時刻があれば **全 object 集合**は一致しない。commit metadata を固定し、必要集合と実在集合を検査すること。

**should A7 — P4 の「読取り支配」は仮説。設定選択は移送全体で行う。**

- **根拠:** Git `pack-objects` / `index-pack`、brief「計測設計」5。
- **成果物への影響:** producer だけで設定を選ぶと、受信側の展開・検証や pack 肥大化で総時間が逆転する。
- **是正案:** 事前実験も producer＋consumer の外側 wall で比較し、pack bytes、CPU、最大メモリ、双方の所要を副次記録する。

source pack は index と mmap window を使い、選択 object の offset 周辺を読む。21ファイルだから順次21回の I/O という意味ではない。loose 読取り、delta chain の展開、圧縮・delta 探索も入り、Lustre 読取りが支配的かは未測定である。thin pack を使わない通常の選択転送では、出力集合外の base を外部依存として残せない。[Git pack-objects 実装](https://raw.githubusercontent.com/git/git/v2.43.0/builtin/pack-objects.c)

既定と `--window=0 --depth=0` の比較は有用だが、後者を単に「既存圧縮 bytes を再利用するだけ」と説明しない。再利用できない delta は展開・再圧縮を要し得る。`--window=0` 単独とも区別する。

`--no-reuse-delta` は既存 delta の再利用を禁止し、`--no-reuse-object` は再圧縮も強制する。compression は再利用 bytes に一律適用されない。threads は自動値と CPU allocation の対応を記録する。これら全部の sweep は不要。[Git pack-objects](https://git-scm.com/docs/git-pack-objects)

`index-pack` の受信・delta 解決・object OID 計算と検証・index 作成は timed に含める。`unpack-objects` は loose 化の別候補だが、ファイル数削減を失うので本 wave の必須比較ではない。[Git index-pack](https://git-scm.com/docs/git-index-pack)

OID の直接列挙は集合を限定しやすい。`--revs` は履歴走査を導入し、filter はその選別なので、単純な置換ではない。blob-only の保証を保つには、直接列挙＋型確認が適切。

**should A8 — 過去の値は条件付き参照値であり、9.5秒は今回の上限ではない。**

- **根拠:** D2086、D357、accept-speed §2-1・2-2、T-2708 §3。
- **成果物への影響:** 古い合計値を固定上限にすると、今回の C1 利得や wall 模型の尺度を誤る。
- **是正案:** 次の限定を README と裁定パッケージに付ける。

| 値 | 読めること／持ち込めないこと |
|---|---|
| Git 11回・9.5秒 | bnode050 の旧 tip・直列・cProfile 条件での合計。add＋commit 単独値ではない。その実行内での粗い包含上限 |
| output 複製52.9秒 | 同 run の列挙・stat・copy 等の合計。object 転送の見積値ではない |
| base→test 2.85〜3.0秒 | worktree と `.git` 全体の複製。P6 の `.git` 単独時間とは別量 |
| pack 21本480 MB・loose 5,914 | source store の時点 inventory。必要 blob の読取量・出力 pack量ではない |
| login 79〜191秒 | D2068 の外乱を含む別環境。計算ノードの判断尺度には使わない |
| builder 163.8秒 | T-2708 の bnode028 単発参考値。今回の上限保証ではない |

5 key 平均も独立した warm 反復実験ではない。48 worker・3 shard・別 node では競合と critical path が変わる。今回の A を分解実測し、過去の9.5秒は整合性確認に留める。conftest は TMPDIR を設定しないだけなので、実行時の temp 環境、実パス、fstype を記録して P3 を確認する。

## レンズ B

**must-fix B1 — 現在の不変条件は「観測上区別できない」を証明しない。**

- **根拠:** D2068(B)、M:636〜650、T:984〜1016、brief「不変条件」。
- **成果物への影響:** 到達可能 tree が同じでも、余分な履歴 object や copy 後の外部依存を見逃し、誤った等価性を裁定パッケージに載せる。
- **是正案:** 同値性を「fixture の必要な観測」に限定し、次を補う。

1. **移送集合:** 入力を一意な blob OID に限定し、型を確認する。受信 pack の実 object 集合・型も照合する。blobだけの通常の非thin転送に commit/tree が暗黙追加されるとは考えにくいが、それを invariant として検査する。
2. **非到達 object:** `rev-list --objects HEAD` は unreachable な実 repo commit を検出しない。recorded commit の fixture での不在を明示確認する。件数だけでなく、固定metadata下の到達集合を比較する。
3. **独立性:** 参照退避領域を見せずに検査し、fixture を別場所へ全体コピーした後も status・submodule・必要 blob の読み出しが動くことを確認する。
4. **変更検出:** regular file の変更、mode変更、追加・削除、submodule 内変更を A/C で同じように検出する。遅いからといって status を省かない。

`fsck --connectivity-only` は完全な blob 内容検査ではない。転送時検証と合わせた保証範囲を明記する。

指定された M の `_capture_head` 周辺には alternates・grafts・replace refs・shallow の拒否があるが、pack/loose 配置の一致要求はない。指定 test file の検索では、pack 数や `count-objects` を assert する箇所は見つからなかった。`.git` の直接操作は cleanup の `gc.pid` 消失試験（T:1260前後）。`_tree_file_snapshot`（T:6039）の確認した呼出先は output 領域であり、fixture `.git` の bytes 同一検査ではない。repo 全域についての不存在証明ではない。

したがって pack 化自体を意味変更とする根拠はない一方、`count-objects` や `.git` bytes では当然区別できる。`gc.auto=0` では不足 blob・tree・commit の loose と pack が混在する。全面的な観測同値ではなく、必要観測の同値を主張するべきである。

**must-fix B2 — P5 は候補抽出規則には使えるが、「符号確認済み」の二値事実にはできない。**

- **根拠:** D2068(C)、D357、D1260、brief P5。
- **成果物への影響:** 小差や不安定な結果を「食わない」、規則未達を「食う」と断定し、既裁定の根拠を書き換えてしまう。
- **是正案:** 行動は二値でも、観測結果は **改善候補／悪化観測／未確定** に分ける。

5 round 中4勝は、独立・対称な符号だけの帰無モデルでも片側確率が6/32であり、強い符号確定ではない。さらに cache 共有により独立性も保証されない。中央値比較に加え、paired差 `C1−A` の全件、中央値、範囲、順序別の偏りを載せる。

D2068 は「符号だけ分かれば採用」と裁定したのではない。1秒未満でも一貫した差は探索上の候補になり得るが、「実用費用を食わない」と断定するには A3 の欠落費用を含める必要がある。実用的な最小効果量を使うなら、測定前に絶対秒または比率を決めること。D357 の10%を per-base に機械移植する根拠もない。

C2 を主判定から外すことは、対象を **C1 の候補抽出**に限定すれば妥当。ただし C2 が良く C1 が悪い場合に「必要 blob 移送案全体が符号確認済み不採用」と閉じてはいけない。

P6 を主判定へ混ぜない設計も妥当だが、それなら結論は base 構築区間についてだけである。copy の利得を含む総費用については未評価とする。

**should B3 — JSON に timed 境界と失格処理を再計算できる情報を残す。**

- **根拠:** brief P5・「計測設計」4・8、規律2。
- **成果物への影響:** 部分費用の除外、軽い status、成功試行だけの選別を、結果だけから発見できなくなる。
- **是正案:** 少なくとも以下を保存する。

- source tip・対象ファイルの指紋、probe hash、Git version、object format、実効config、fstype、CPU allocation、temp環境。
- path数、unique blob数、型別件数、bytes、source に無い OID/path、移送集合の指紋。
- 各コマンドの argv・cwd・環境上書き、開始終了、rc・stderr、外側総時間と段階時間。
- 事前実験を含む全実行順、設定選択根拠、pack bytes、status1/2の生出力。
- 参照/実測 tree、固定commit情報、到達集合、pack inventory、alternates等の検査、copy後検査。
- 失格・timeout・欠測を含む全試行、集計採否理由、paired差、判定規則の版。

規律2への主な攻撃面は、選定・不足blob補充・refresh・update-ref を timed 外へ逃がすこと、producerだけ測ること、status の弱化、試行前の無料refresh、失敗を中央値から黙って落とすことである。

author への禁止文案：

> 選定・移送・不足 object の生成・index の検証と保存に必要な処理を timed 外へ移して、自己完結経路の総費用と記述してはならない。production の status 引数・環境・変更検出を弱めてはならない。失格・timeout・欠測を黙って除外または再試行し、成功分だけで事前登録判定を満たしたと報告してはならない。main 初回を cold と断定し、per-base の差を受入 wall の改善へ読み替えてはならない。

**should B4 — P6 は `.git` コピーの副次量として有用だが、コピー後の費用を表さない。**

- **根拠:** T:1015前後の全体 `copytree`、P1、brief P6。
- **成果物への影響:** pack化によるメタデータ削減を、base→test 全体や production status の削減と誤認する。
- **是正案:** `.git` copy・objects bytes・file数を副次量として報告する。採用候補では全fixtureのcopyとコピー先statusも別途測る。

`copytree` 後には inode・ctime等が変わり、保存した index stat が再び一致しなくなり得る。`GIT_OPTIONAL_LOCKS=0` により、その先の再走査も繰り返され得る。これは A にもある現行費用であり、Cの主比較へ一方的に加算すべきではないが、「明示refresh一回で全testのhashを解消」とは言えない。

**should B5 — 採用 wave の影響と、不採用記録の範囲を先取りして明記する。**

- **根拠:** D2068、D1260、T:1490〜1528。
- **成果物への影響:** 計測用の完全な OID 参照を、そのまま採用可能な実装と誤認する。
- **是正案:** 裁定パッケージ候補として、採用 wave に次を引き継ぐ。

採用面は、現行 `add -A` 直前の移送、source `ls-files -s` 等による候補選定、historic/fixture固有bytesとの不一致処理、移送失敗時の現行addへのfallbackである。fallbackは半端なpackや外部参照を残さず、費用と発生理由を可視化する。C1では最後の通常addが現物を採用することを維持する。

正負例・変異は、source indexと現物の不一致、missing blob、distinct/historical blob、ignored/untracked file、symlink・mode・submodule、破損転送、fallback、copy後独立性を含める。alternates変異はproduction拒否、assume-unchanged変異は内容変更の負例、不要commit持込みはmissing-commit観測で殺す。

結果が悪い場合も、D2068(C)全体を無条件に「符号確認済み不採用」へ更新しない。**測った設定・集合・環境でのC1**について記録する。規則未達だけなら「未確定のため現行維持」。新gate・台帳、共有資源削減の別目的採用、10%基準変更は本wave外の裁定候補に分離する。

**nit B6 — 試行数削減は可能だが、26試行という数だけで過剰とは言えない。**

- **根拠:** brief「計測設計」5〜7、T-2708のbuilder参考値。
- **成果物への影響:** 現時点では、削除によって結論が改善するとは断定できない。
- **是正案:** 必須修正後の一試行費用からbudgetを見積もる。

builder164秒とA約50秒を引いても、移送16回、ハッシュ5回、検査・copyが残る。C2固有処理等を無視しても、1時間には移送平均約212秒未満が必要であり、余裕の証明ではない。段階timeout、失敗時の部分JSON保存、失格時の停止条件を先に決める。

C2を合成本体確認＋実corpus少数回に減らす案は、C1が主判定なら合理的。ただし下限の反復分布は得られない。事前実験を落として `--window=0` 固定にする案は安価だが、その設定の不振を移送案全体へ一般化できない。全設定sweepの追加は不要。

**nit B7 — selftest の「1秒」は目標とし、機序検査を時間差のassertにしない。**

- **根拠:** Git index refresh、freshen、brief「計測設計」8。
- **成果物への影響:** 小repoの所要だけでは再ハッシュ有無を証明できず、1秒保証にも根拠がない。
- **是正案:** 数個のblobの合成repoで次を確認する。

- 空stat indexにproduction形statusを2回実行し、index bytes/stat未保存を確認する。利用可能ならTrace2のrefresh scan件数で再走査を観測する。
- 明示refresh後の保存と、非racy条件下のscan減少を確認する。内容変更を隠さない負例を入れる。
- packed blob既在のC1で、そのblobのlooseが新設されないことを確認する。pack無しでは生成される対照を置く。
- source欠落blobの補充、tree不一致・alternates・余分なcommitの失格、submodule復元を確認する。

Trace2等の観測可否はGit版依存。index不変だけで「実際にhashした」と断定しない。大型blob経路は、この軽量selftestで覆えない限界として残す。

## 総括

**must-fix は7件：A1〜A5、B1〜B2。**

| provisional裁定 | 判定 |
|---|---|
| P1 | **条件付き**。未保存statによる再走査は支持。普遍的な「移送＋必須hash一回」という下限は反証 |
| P2 | **条件付き**。C1は合理的。圧縮回避の例外、選定費用、object集合、C2不足blobを修正する必要がある |
| P3 | **支持**。計算ノードのAを基準にする。ただし実配置を記録し、過去9.5秒を固定上限にしない |
| P4 | **条件付き**。Lustre→localという配置は整合。読取り支配とcold初回は未立証 |
| P5 | **条件付き**。候補抽出には使えるが、費用境界・欠測処理・結論の語彙を修正する必要がある |
| P6 | **支持**。副次量として適切。全fixtureコピーとコピー後statusの効果は別途必要 |

親の「計測を予定どおり行う」は、**目的と計算ノードjob方針には賛成、現briefのままの実行には反対**。7件を修正してから実行すべきである。特に参照退避、C2不足blob、無料のOID選定、cold表記を直さなければ、失格か過小見積りになり、採用再検討の根拠として使えない。