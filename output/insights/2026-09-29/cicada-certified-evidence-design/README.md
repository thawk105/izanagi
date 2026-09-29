# Cicada の正しさを certified まで上げるための記録の設計と、3 案の比較・推奨 (VHash 論文 md_24、設計のみ、2026-09-29)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)。
wave `dev-wave-cicada-certified-evidence-design` (branch `worktree-dev-wave-cicada-certified-evidence-design`)、起点 local main `8fe87f852` (開始 gate fresh rc 0、2026-09-29 22:09 JST)、CCBench submodule = pin C `68106660` (動かしていない)。
台帳 item = worklog「次の一手」[T-2874] の (2)。依頼は `/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_24.txt` (逐語は `verbatim/request-md_24.txt`)。
段 1 brief・段 2 設計案 (Codex)・段 3 相談 2 本 (Codex、実装する側 / しない側)・段 4 裁定・段 6 レビューと裁定の全文は `verbatim/`。**新規の計測も実装もしていない。** 数値は既存の走行記録と、コードの読解による見積りである。

## 1. 依頼と結論

依頼 (md_24): 今の判定器では Cicada は「巡回が見つからない = indeterminate」までしか言えず、VHash 論文に「forwarding を入れた Cicada は serializable を保つ」と書けない。性能値も「未検証の診断値」のままである。Silo / MOCC と同じ水準の証拠を Cicada で取るには何を記録すればよいかを設計し、費用を見積もり、「実装する」と「今の範囲で主張する」の 2 案と推奨を出す。実装に進むかはユーザーが決める。

結論:

1. **Silo / MOCC の certified は「観測した実行の依存グラフに巡回が無い」に、「trace がその実行を忠実に写している」ことの証拠を足したものである** (§2)。X (lock 被覆) は「R 行の版 = 実際に読んだ値の版」を、P (sort の置換保存) は「書いた要素が失われていない」を担う。判定器は X・P の検査コードが TRACE ビルドのソースに**在る**ことを文面で確かめ、実行中の違反行が 0 であることを要求する。
2. **Cicada で同じ水準に要るのは、多版と GC に固有の忠実性の証拠 3 つである** (§3): **B = 読み束縛** (読んだ版 object が tx の終わりまで回収・再利用されていない)、**U = 公開の双方向照合** (公開した全版が W 行に出ており、W 行の全版が公開されている)、**P = write set の置換保存** (Silo の P を移す)。md_24 が挙げた「各 read の可視区間」「書き込みの設置順」「rts の更新と検証の順序」「read-only snapshot の境界」は、記録した履歴の 1SR (= certified が言うこと) には**不要**で、壊れたときの帰属 (規律 3) の**診断**である (§3.3)。ただし certified は「Cicada が自分の規則どおりの版を選んだ」ことまでは言わず、規則に反する選び方は巡回を生んだときだけ検出される (§3.1)。
3. **VHash の新規性の芯 (前進を GC の回収境界へ反映する U0) の典型的な失敗 = 既読版の早すぎる回収・再利用は、今の検査器の盲点そのもの**である。実物でも起きた (構成 E の仮裁定 P5 の下で、腕 E-hb は 3,938 件中 159 件、腕 E は 3,882 件中 174 件、`../vhash-gc-connection-prototype/README.md` §3.3)。今の計装は読んだ時点の wts を控えるだけで、食い違いは stderr の件数として出るだけで判定に入らない。
4. **3 案を比べ、中間案 M を推奨する** (§7・§8)。M = 既存の out-of-tree 計装を広げて B と U (と read 側の API 照合) を TRACE ビルドで実装し、repo 外起動器の合否に入れる。判定器の production と campaign は変えない。費用は計装 +150〜250 行・起動器 +50〜100 行・壊し patch 2 本・計算 0.22〜0.36 node 時間 (見積り)。段 3 の 2 レンズ (実装する側 / しない側) が独立にこの案を推した。
5. **どの案でも「Cicada 実装が一般に serializable を保つ」とは書けない。** 一般論証 (D2292) は小モデルの仕様 v1 が対象で、実装の条件 W* と GC 接続 G4〜G7 の安全性を主張していない。実走検査は検査した有限の run についてしか言えない。案ごとに書ける文の差は §7 の表にある。

## 2. 現行の X / P / I と certified の意味 (Silo / MOCC)

判定の定義 (`orchestrator/verifier/model.py`):

- `certified` = `n_txns > 0` ∧ 巡回 0 ∧ `Integrity.clean()` (`model.py:568-571`)。
- `clean()` = orphan_reads・version_dups・dup_txids・genesis_commits・missing_txids・write_version_mismatch・malformed_keys・framing・X・I・P・existence の各件数が 0 ∧ commit witness 一致 ∧ **X と P の証拠面が evidence-present** (`model.py:507-522`、`certification_gate_satisfied` は `model.py:77-82`)。
- 証拠面の評価は**文面検査**である。CMake の `ccbench_add_protocol(... SOURCES ...)` に並ぶ `.cc` だけを読み (`model.py:119-180`)、literal `#if TRACE` の第 1 枝の中に emitter の呼び出し (`izanagi_trace::emit_lock_violation(`、`"P "` の stream) が在るかを見る (`model.py:45-54, 204-302`)。docstring 自身が「到達可能性・実際の発火は証明しない」と書いている (`model.py:238-243`)。発火の歯は、D38・D41・D1686 の壊し (positive control) が別に担う。
- 対象 protocol は `{silo, si, mocc}` (`model.py:37`)。それ以外は三面とも unavailable で、巡回 0 でも indeterminate になる。

| 面 | 何を記録するか | なぜ要るか | emitter |
|---|---|---|---|
| X | write の lock 被覆違反 (`X <txid> <key> <reason>`) | lock を持たずに書くと、読み手が古い tid のまま新しい値を読む torn read が起き、R 行の版が実際の値の版と食い違う。辺が落ちて巡回が隠れる (D38) | Silo `cc/silo/transaction.cc:618-674`、MOCC `cc/mocc/transaction.cc:1183-1254` (入口・書く直前・公開直前) |
| P | write set の sort 前後の件数・多重集合の食い違い (`P <reason>`、txid なし) | 非 strict-weak-order の comparator で sort が要素を欠落・複製すると、lock 順と W 行の前提が崩れる (D41) | Silo `:403, 432`、MOCC `:991-1011` |
| I | API の write intent と write set の双方向照合の破れ | write set を再走査する W 行と X 検査の死角 (要素の喪失・捏造) を閉じる (T-152) | 現 pin に emitter が無く、**certified の連言に入っていない** (commit `e4c949f08`) |

si は trace (v2) を出すが X / P の emitter が無いので certified に届かない (D2252 項 5)。Cicada も同じ扱いである (D2279 項 4、`../vhash-cicada-verifier/README.md` §1 項 5)。

**要点:** certified が言うのは「この run の観測した読み書きは直列化可能で、その観測は (lock と sort に関して) 実行を忠実に写している」までである。protocol が一般に正しいことは言わない。

## 3. Cicada の忠実性の脅威と証拠面の設計

対象は YCSB の point read / update、`SINGLE_EXEC=0`・`group_commit=0`・`INLINE_VERSION_OPT=0`・`REUSE_VERSION=1` に限る (§3.5)。

### 3.1 理屈 — なぜ「区間」や「設置順」は必須でないか

多版の履歴は、**ある 1 つの版順**で直列化グラフが非巡回なら 1SR である (Bernstein・Hadzilacos・Goodman の MVSG 定理)。判定器は各 key の W を版 ID (Cicada では wts) の数値順に並べ、ww・wr・rw の辺を作る (`orchestrator/verifier/dsg.py:224, 455-479`)。したがって、

- **reads-from が忠実** (R 行の版 = 実際に値を読んだ版) で、
- **W 行が公開された全版をちょうど表す** (漏れも捏造もない)

なら、wts 順での非巡回は「記録した履歴が、観測した読みについて 1SR である」ことを意味する。certified が言うのはこれだけで、物理的な版の鎖の順序は要らない。

**検査しないこと (段 6 レビューの R3):** Cicada が各 read で**自分の規則どおりの版** (自分の時刻で見える最新の確定版) を選んだかは検査しない。規則に反する選び方でも、巡回にならなければ通る。例: W₂ が確定した後に R が古い W₁ を読んでも、辺が R →rw→ W₂ だけなら非巡回で、R を W₂ の前に置けば 1SR である。これは直列化可能性の違反ではないが Cicada の snapshot 規則の違反であり、巡回 0 は「版の選び方の誤り全般が無い」ことを意味しない。選び方の誤りが検出されるのは、それが巡回を生んだときだけである (壊し patch 3 本はそうなるように作ってある)。規則への適合まで言うには §3.3 の診断 (可視区間と read-only の rts) を使った別の適合検査が要る。

**限定 (段 3 相談 A の A4):** 判定器は終状態 (実行終了時に最新として見える版) を検査しない。W₁ と W₂ を数値順 1 < 2 と記録しても、物理的に最後に見える版が W₁ で、それを読む read が無ければグラフは非巡回のままである。**主張は「観測した読みについての 1SR」に限り、終状態の正しさは言わない。** これは Silo の certified と同じ限定である。

### 3.2 必須の証拠面 (certified に要るもの)

| 面 | 脅威 (放置すると壊れた variant が通る経路) | 記録と照合 |
|---|---|---|
| **B 読み束縛** | 読んだ版 object が、読み手がまだ生きている間に GC で切り離され (`gc_versions` の detach、`transaction.cc:806-843`)、`REUSE_VERSION=1` で別の書き込みに再利用される (`include/transaction.hh:173-195, 217-245`)。すると読み手の body は別の版の中身になり、R 行の版 (控えた wts) と食い違う。同じ wts・同じアドレスの再利用や、別 key の版への化けもありうる。stock では「ThreadRtsArray = tx 開始時の MinWts−1 を tx の間変えない」がこれを防ぐが (D2295)、forwarding + GC 接続はまさにここを動かす。 | **主案 (段 4 裁定):** 切り離し (`gcAfterThisVersion`)・再利用 (`newVersionGeneration`)・未設置版の返却 (`writeSetClean`) を、版 object ごとの**消えない事象**として TRACE 専用の台帳 (版の外) に積む。read 登録時 (`read_internal` の `read_set_.emplace_back`、`transaction.cc:126`) に台帳上のその版の事象の位置を控え、tx の終わり (書く tx は `writePhase`、read-only は `commit` の早期 return 前) に「登録後にその版の事象が 1 つでも積まれたか」を台帳だけで照合する。**版 object (ver_) は終わりに再参照しない。** 台帳は並行する退役・再利用と照合が同時に走っても事象を取りこぼさない順序付け (事象の追記を照合より先に見せる) を要する。**代替案 (親の追加確認、実装 wave の段 4 で選ぶ):** 版の中に TRACE 専用の単調な世代番号を置き、登録時に「世代 → wts → 世代」の一致した組を控えて終わりに世代を読み直す。§3.5 の範囲では走行中に版 object を解放する経路が今回の読解では見つからなかったので、この形でも解放済み memory を読まない**見込み**である。採るなら、実装 wave で解放経路が無いことを確かめ直すことを採用の条件にする。単純だが `REUSE_VERSION=0` へは広げられない。どちらの案でも **ver_ の wts を読み直す現行方式は置き換える** (同じ wts の再利用を見逃すため、段 2 設計案)。 |
| **U 公開の双方向照合** | W 行は write set から作るが、公開 (status を committed にする `cpv`、`transaction.cc:687-720`) は別の経路である。公開した後、emit の前に write set から要素を落とす壊れた variant では、実在する版の W 行が消え、巡回が見えなくなる (段 3 相談 A の A1 が具体列を示した: T1 `R(x₀) W(y₁)`・T2 `R(y₀) W(x₂)` で本来 T1→T2→T1)。逆に、公開していない版の W 行を出すと架空の辺ができる。 | TRACE 専用の tx ごとの記録に、設置 CAS の成功 (`transaction.cc:515-527`) と公開の store (`:710-715`) を (key・版 object・世代・wts・op) で積む。公開の直前の status が pending であることも確かめる (二重公開・pending 飛ばしの検出)。emit 時に「公開した集合」と「W 行の集合」を**双方向**に照合し、wts = C 行の版であることも見る。 |
| **P 置換保存** | Cicada も `precheckInValidation` で write set を `partial_sort` する (`include/transaction.hh:247-256`)。comparator が壊れると要素が欠落・複製し、W 行と公開が食い違う (U でも捕まるが、原因の帰属は P が直接示す)。 | Silo の P をそのまま移す。比較するのは (storage・key・tuple pointer・新版 pointer・op) の多重集合 (pointer だけでは別要素へのすり替えを識別しない、段 2 設計案)。 |

**API との双方向照合 (段 4 裁定 A3、段 6 レビューの R2):** read 側 = 成功した外部 read ↔ read set への登録、write 側 = I (成功した update / insert / delete の API intent ↔ write set)。`read_internal` は常に read set に積むが、read 経路を変える variant (forwarding がそれである) が read set を通らない読みを作ると、その読みは trace に出ず辺が落ちる。Silo の現行連言は I を含まないが、Cicada では次のように扱う。

- **中間案 M:** read 側の照合を入れる (forwarding が触るのは read 経路)。write 側は U の双方向照合で公開版と W 行の対応を見るので後回しにできる。
- **案 A (certified 化):** read 側・write 側の双方向照合を**必須**にする (連言に入れる)。

数え方 (焦点再レビューの N1 で改めた): 照合の母集団は **公開 API の `read()` が `Status::OK` を返した呼び出し全部**とし、read set への登録とは独立に、`read()` の入口と戻り (`transaction.cc:144-190`) で TRACE 専用に数える。`read_internal` を通ったかどうかで母集団を決めない — それでは `read_internal` を迂回した読みが母集団から漏れ、照合の狙いが成り立たない。数えた呼び出しは、どの分岐で body を返したかで分ける: (a) read set からの再読 (`:156-160`、同じ版の再読で R 行を出さない)、(b) read-own-write (`:161-165`、自分の書き込みで R 行を出さない)、(c) それ以外 = 外部 read。照合は件数の一致ではなく**呼び出し単位**で行う (2 巡目の焦点再レビューの F1 で改めた。件数だけでは、登録漏れ 1 件と余分な登録 1 件が同じ tx にあると一致してしまう): (c) の各呼び出しについて、その呼び出しの中で read set に新たに登録された要素がちょうど 1 つあり、その要素の key が呼び出しの key と一致し、呼び出しが返した body の pointer がその要素の版の body であること。(a)・(b) の各呼び出しについて、返した body の pointer が既存の read set / write set 要素の版の body であること。そして tx の終わりに、read set の要素のうちどの (c) 呼び出しにも対応しないもの (余分な登録) が 0 であること。これで「R 行 = 実際に body を返した外部 read」が要素ごとに対応づき、§3.1 の前提 (reads-from の忠実性) のうち「読みが漏れず、余分な R も無い」を担う (値と版の一致は B が担う)。`scan()` は 1 呼び出しで複数の body と read set 要素を返しうる (`transaction.cc:429-460`) ので、照合の単位は呼び出しでなく返した要素ごとになる。scan は本書の範囲の外で、将来の別設計とする (F2)。`NOT_FOUND` を返した呼び出しは不在の読みとして別に数え、本書の範囲 (YCSB は全 key 既存) では 0 であることを確かめる。

**却下した設計 (段 3 相談 A の A5):** 親 brief の (P4)「照合した回数を自己申告させ、R 行数と突き合わせる」は、両方が同じ read set のサイズから作られるので恒真である。照合を飛ばしても一致する。**発火の証拠は各分岐の壊し patch だけ**とし、件数の一致を発火の証明と呼ばない。

### 3.3 md_24 が挙げた 4 項目の分類

| 項目 | 分類 | 理由 | 記録するなら |
|---|---|---|---|
| 各 read が見た版の区間 | 診断 (ただし Cicada の版選択規則への適合を言うなら必要) | 記録した履歴の 1SR には不要 (§3.1)。ただし規則に反する選び方で巡回にならないものは certified でも通る (§3.1 の R3 の例)。規則への適合を主張するなら、この区間と read-only の rts を使う別の適合検査が要る。区間 1 回の観測は途中で変わる鎖の上での単発観測で、「区間の証明」と誤認しやすい | read 時の snapshot ts、選んだ版の wts、次に新しい確定版の wts、待った pending の数 |
| 書き込みの設置順 | 診断 | 判定器の版順は wts の数値順で、物理の設置順は 1SR の必須条件でない (§3.1)。ただし U の「設置した」事実とは分ける | 設置 CAS 成功時の (key・新 wts・後続版の wts・設置の通番) |
| rts の更新と検証の順序 | 診断 | 忠実な履歴が非巡回なら、この順序が守られたことを別に示す必要は無い。forwarding が壊れたときの原因説明には重要 (D2292 の論証の芯は「reader は rts を上げてから観測し直す」「writer は設置してから rts を検査する」の 2 つの順序) | `readTimestampUpdateInValidation` の前後、read の再検証、write set 側の pending 待機後に (key・観測した wts・rts・status) |
| read-only snapshot の境界 | 診断 | read-only は固定 `rts_` で読み、validation を通らない (`transaction.cc:93-97, 934-937`)。古い snapshot を読むこと自体は 1SR 違反でない | read-only の C 行に開始時と終了時の `rts_` を添える。これがあると「wts 順 (read-only は rts 順) で直列化される」という追加の適合検査が安く書ける |

診断の行は、判定器が未知の行種別を ParseError にする (`orchestrator/verifier/parse.py` の `_parse_file` 末尾) ので、出すなら判定器の対応 (通常の parser と列形式の `_parse_trace_dir_compact` の両方) が先に要る。中間案 M では診断の行を出さず、必要なときに stderr の集計行で足りるかを先に見る。

### 3.4 置き場の制約 (段 3 相談 A の A6・相談 B の B-1)

判定器の文面検査は `SOURCES` の `.cc` だけを読み、Cicada は `transaction.cc util.cc` である (`external/ccbench/cc/cicada/CMakeLists.txt:2`)。一方、`partial_sort` と既存計装の emit 本体 (`traceCommit`) は `include/transaction.hh` にある。certified 化 (案 A) には次のどちらかが先に要る。

- header を含む source snapshot (と campaign の source binding) を Cicada 用に定め、site ごとの emitter と呼び出し経路を評価する。
- 照合の本体を `transaction.cc` へ移す (`validation()` から `precheckInValidation()` を呼ぶ前後で P を見る、など)。

**`.cc` に薄い wrapper の emitter だけを置いて「在る」を満たす形は採らない** — 検査の実体が header にあるなら、文面の証拠は飾りになる。

### 3.5 対象外にする構成と理由

- `REUSE_VERSION=0`: 切り離した版を `delete` する (`include/transaction.hh:186-188`)。B の代替案 (版の中の世代番号) は解放済みの object を読むことになるので使えない。主案 (版の外の台帳) なら原理上は扱えるが、解放後に同じアドレスが別の版に割り当てられる場合の台帳の鍵の設計が要る。最初は対象外にする。
- `INLINE_VERSION_OPT=1`: inline 版を `unused` に戻して再取得する (`include/tuple.hh:54-71`)。世代番号をそこでも増やせば扱えるが、PROMOTION との組は既に `#error` (D1464・D2279 項 5)。最初は対象外。
- 不在の読み・scan・insert・delete (TPC-C): R 行に出ない読みがあり、D2232 項 4 の 2 点 (版 (1,0) は初期ロードだけ、insert は既存 key で失敗) を Cicada で確かめる必要がある。worklog [T-2874] の (4) が先。
- `group_commit>0`: 公開が `gcpv` へ移る (`transaction.cc:723-738`)。U の site が変わるので対象外。

**走行中の memory 安全 (親の読解):** 上の範囲 (YCSB、`REUSE_VERSION=1`、inline なし) では、走行中に版 object を解放する経路は今回の読解と検索では見つからなかった。解放は終了時の `deleteDB` (`util.cc:225-235`)・`~TxExecutor` (`include/transaction.hh:97-101`)、insert の失敗と abort した insert の tuple (`transaction.cc:321, 750`)、delete 済み record の `gc_records` (`:854`) だけである。abort した版は、設置済みなら status を aborted にして鎖に残し、未設置なら再利用 pool へ戻す (`include/transaction.hh:343-365`)。したがってこの範囲では、B の代替案 (tx の終わりに版の中の世代番号を読み直す) でも解放済みの memory は読まない見込みである。これは今回の読解と検索での陰性であり、全経路の不存在証明ではない (段 6 レビューも反例を見つけなかった)。代替案を採るなら、実装 wave で解放経路が無いことを確かめ直す。

**B の照合区間の前提:** CCBench の workload は commit の前に body を使い終える。YCSB は read の直後に値へ触れ、READ_MODIFY_WRITE は直後に memcpy する (`external/ccbench/include/ycsb.hh:120-143`、commit は `:161`)。TPC-C も workload の後に commit する (段 3 相談 A、`tpcc.hh:102-114`)。この前提の下で、tx の終わりの照合は「read 登録から最後の body 消費まで」を覆う。なお YCSB の READ は値への参照を作るだけで、実際に値を読むのは READ_MODIFY_WRITE である。

## 4. 観測者効果 (絶対規律 1)

- 追加するもの (B の事象台帳、または代替案の Version の世代 field、ReadElement の控え、tx ごとの公開記録、照合、違反行) はすべて `#if TRACE` の内側に置く。TRACE=0 では台帳も field も消し、既存計装と同じく `#else` 側の `#line` で行番号を保つ。
- 事象台帳の追記と照合は TRACE=1 の実行に同期を足し、スケジュール (どの tx が並ぶか) を変えうる。代替案の Version の field は TRACE=1 ビルドの struct の配置と cache の振る舞いを変える。どちらも TRACE=1 の throughput を性能値に使わないので許容する。
- 確かめ方は既存と同じ: 同じ compile command で pin と patch 適用を TRACE=0 で build し、objdump の命令列・前処理出力・`nm`/`strings` を比べる。既存の一致は YCSB target の 3 TU だけなので (`../vhash-cicada-verifier/README.md` §5)、Version を変えるなら `version.hh` を include する全 TU (tpcc・bomb・sbomb を含む) を比べる。

## 5. 費用

### 5.1 基準値 (既存の走行記録、stock、thread 4、1 秒)

原本 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-verifier/runs/j1-c/` (`result-J1.json`、`raw/J1/*.trace`):

| cell | commit 数 | trace の大きさ (`du -sb`、ディレクトリ 4,096 byte を含む) | 判定器の所要 |
|---|---|---|---|
| K (rratio 50、max_ope 10) | 175,139 | 78,823,348 byte (file 合計 78,819,252) | 4.67 s |
| R (rratio 90、max_ope 4) | 917,498 | 196,322,301 byte (file 合計 196,318,205) | 13.14 s |

### 5.2 算術の見積り (実測ではない)

| 項目 | 中間案 M | 案 A (certified 化) |
|---|---|---|
| trace の量 | 違反行だけ (正常系 0 行) + thread ごとの集計行。増分はほぼ 0 | M と同じ。診断の行 (§3.3) も常時出すと、read ごと・write ごとに 1 行ずつ増え、数十〜数百 MB 規模になりうる |
| 判定時間 | 判定器を変えないので同じ (4.67 s / 13.1 s 相当) | 違反行だけなら parser の増分のみ。診断の行を読むなら入力処理が支配的になりうる。基準値に倍率を掛けた予測はできない |
| CCBench 計装 | +150〜250 行 (B の事象台帳または世代番号、登録時の控え、公開記録、双方向照合、read 側の API 照合、集計行) | M に加えて P、write 側の API 照合 (I)、header を含む証拠の置き場の整理で +100〜300 行 |
| 判定器 | 変えない | 新しい行種別を両 parser で読む、Integrity の件数、Cicada 用の証拠面の評価と protocol 登録、fixture・凍結 capacity baseline: 本体 250〜450 行 + 試験 300〜600 行 |
| repo 外起動器 | md_3 の起動器に集計行の読み取りと合否 +50〜100 行 | M と同じ |
| 壊し patch | B・U の 2 本 | B・U・P の 3 本 + I (write 側 API 照合は必須。その壊し patch の本数は実装 wave の変異の事前登録で決める) |
| 計算 | 生死確認 + stock (K・W・R × t1・t4) + forwarding の構成 C・E + 壊し 2 本で 10〜16 run × 約 80 s = 800〜1,280 s ≈ 0.22〜0.36 node 時間 (md_3 の本走 1 job の Elapse 82 s を 1 run の目安にした算術。build の再利用や待ち行列は含まない) | M と同程度 + 受入・変異 |
| wave 数 | 1 (実装・レビュー・実走) | 2〜4 |

### 5.3 見積りに入れていない費用 (段 3 相談 B の B-4・B-5)

- **案 A だけに掛かる:** 判定器の 7 file (`core.py`・`dsg.py`・`model.py`・`parse.py`・`__init__.py`・`report.py`・`commit_receipt.py`) は campaign lock の exact 96 path の source closure に入っており (`orchestrator/campaign/campaign_lock.py:47-73`)、批准済み digest と照合される (`orchestrator/campaign/contract_loader_binding.py:540-548`)。変えると新しい lock の批准が要る。既存の silo / mocc / si の判定と fixture を変えないことの確認、変異 matrix、受入全走も要る。
- **両案に掛かる:** pin を C から進めたら計装 2 本と壊し patch の厳密適用・生死確認の取り直し ([T-2874] (3))。trace hook を `izanagi-trace` 枝へ移すのは人間の判断 (D2279 項 1)。
- **未測:** TRACE ビルドでの世代番号・公開記録の同期が実行のスケジュールをどれだけ変えるか。判定時間の実際の増分。

## 6. campaign 側の trace 供給の要点 (案 A の後段、設計のみ)

現状: campaign は protocol に関係なく trace build と perf build を作り (`orchestrator/campaign/pipeline.py:2117-2118`)、`certified` でなければ reject する (`:731-743`)。Cicada は遺伝子空間に在るが (`orchestrator/campaign/genome.py:176-188`)、証拠面の対象外、source の編集許可 (`orchestrator/campaign/source_digest.py:85-100`、silo / mocc の `transaction.cc` だけ) の外、floor の baseline (`orchestrator/campaign/between_run_floor.py:60-86`) の外であり、pin には trace hook が無い (out-of-tree patch)。したがって**今 campaign に Cicada を入れると、trace build は何も出さず、必ず不合格になる。**

Cicada を certified の門へ入れるのに要るもの:

1. trace hook の置き場を決める — `izanagi-trace` 枝へ移して pin を進める (人間の判断、D2279) か、out-of-tree patch を build の source binding に入れる新しい経路を作るか。
2. 判定器 (案 A の全層): 新しい行種別 (通常の parser と列形式の parser の両方)、Integrity の件数 (B・U・P と、read 側・write 側の API 双方向照合)、header を含む Cicada の証拠面評価、`_PROOF_SURFACE_PROTOCOLS` への登録、fixture と凍結 capacity baseline、既存の silo / mocc / si の判定を変えないことの確認。
3. 遺伝子空間の制約: TRACE=1 で `#error` になる組 (inline + promotion) と、証拠面の対象外の組 (`REUSE_VERSION=0`、inline) を build 前に fail-closed にする。
4. floor を使う campaign なら Cicada の baseline を別に作る (名前を足すだけで認定済みとは扱わない)。
5. TPC-C は §3.5 の existence の 2 点の確認が先。

**これを今実装しない理由:** 今 Cicada を certified の門に通す campaign の登録が無い (DW-G04 の発火 gate を満たす artifact path が書けない)。

## 7. 3 案と、論文に書ける文の差

| 層 | 案 B (今のまま、indeterminate の範囲で主張) | 中間案 M (推奨) | 案 A (certified 化) |
|---|---|---|---|
| 一般論証 | 小モデル仕様 v1 で forwarding は直列化可能性を保つ (D2292)。実装の条件 W* と GC 接続 G4〜G7 は主張しない | 同左 | 同左 |
| 実装の観測履歴 | 「N run・M txn の観測した実行で依存グラフに巡回は無かった。人為的に入れた誤り 3 種は検出された」 | 左に加えて「TRACE ビルドで、生存中の tx が読んだ版が回収・再利用されていないこと、公開した全版が記録されていることを全 tx で照合し、違反は 0 だった。これらの照合は、早すぎる回収と公開漏れを人為的に入れた版で発火する」 | 左に加えて「これらの照合を連言に含めた判定器で、検査した run はすべて認定 (certified) された」 |
| 限界として書くこと | 「読んだ版の取り違え (早すぎる回収による再利用) を trace が見逃す可能性を排除していない」— U0 の典型的な失敗が検査の盲点に入る。加えて M の欄の後 2 文 | 「照合の範囲は YCSB の point read / update と特定の構成。終状態は検査しない。Cicada の版選択規則への適合は検査せず、規則に反する選び方は巡回を生んだときだけ検出される」 | M と同じ |
| 性能値の地位 | 正しさが未確認の実装の測定値 (izanagi の用語では「未検証の診断値」) | 巡回 0 と B・U・read 側 API 照合の違反 0 を満たした実装の TRACE=0 ビルドの測定値。izanagi 内部の判定は indeterminate のまま (§8 判断点 2) | certified の実装の TRACE=0 ビルドの測定値 |
| izanagi の campaign | Cicada は門を通れない | 同左 | §6 の後段を足せば通れる |

**どの案でも書けない文:** 「Cicada 実装 (forwarding + GC 接続) は一般に serializable を保つ」。検査は有限の run についてであり、一般論証は実装そのものを対象にしていない (段 3 相談 B の B-2)。「certified」は izanagi 内部の語で、論文の読者には何を照合したかを書かないと意味が伝わらない — 案 A の文の増分は、読者から見ると M とほとんど変わらない。

## 8. 推奨とユーザーの判断点

**推奨: 中間案 M。** 理由:

1. VHash の新規性の芯 U0 の典型的な失敗 (既読版の早すぎる回収・再利用) は、実物で起き (§1 項 3)、今の検査器の盲点に入る。論文の中心となる機構の安全性の証拠が「巡回が無かった」だけでは弱い。M はこの盲点を直接閉じる。
2. 論文に書ける文は、M と A でほとんど変わらない (§7)。A の増分は izanagi 内部の certified という語と campaign への接続で、それを要する campaign の登録が今は無い。
3. A には判定器の production 変更に伴う lock の再批准・fixture・変異・受入の費用が掛かる (§5.3)。ユーザーの過去の裁定 (認証の本数や論文主張に使われない束縛機構に資源を割かない) にも M のほうが合う。
4. 段 3 の 2 レンズ (実装する側 / しない側) が独立に M を推した。

**M をやるときの完了条件 (提案):**

- stock と構成 C・E で B・U・read 側 API 照合の違反 0。
- 壊し B: 読み手が生きている間に既読版の退役事象が台帳へ届く最小の列を作る (例: 読み手が読んだ直後に待つ間、GC の回収境界をその版より先へ進めさせる)。**B の違反件数が 0 から増えること**を直接確かめ、異常終了・停止は検出と数えない (段 3 相談 A の A7。解放済み参照で先に落ちる列は壊しとして不適)。
- 壊し U: 公開漏れを 1 件だけ、後続の reader を pending で待たせない形で作る (例: 公開済みの要素を emit の前に write set から外す — A1 の列)。**U の違反件数が増えること**を直接確かめる。
- TRACE=0 の命令列一致 (変更した header を include する全 TU、tpcc・bomb・sbomb を含む)。
- 既存の巡回検出 (壊し 3 本) が変わらず働く。

**ユーザーに返す判断点:**

1. **どの案に進むか** — M (推奨) / A / B。
2. **M を選んだ場合の性能値の呼び方** — M の証拠 (巡回 0 + B・U・read 側 API 照合の違反 0、判定器の上では indeterminate) を満たした variant の性能値を、VHash 論文の執筆で「未検証の診断値」から格上げして扱ってよいか。格上げしないなら、M の効用は論文の正しさの節と限界の書き方だけになる。
3. **A を将来やる条件** — Cicada を certified の門に通す campaign (Phase 3 の合成素材として Cicada を使う等) を登録するときに、§6 の設計から着手する、でよいか。

## 9. 確かめたこと・確かめていないこと

確かめたこと (コードと既存記録の読解):

- 現行の certified の定義と、X / P / I の意味・emitter の位置・証拠面の文面検査の範囲 (§2)。
- Cicada の読み・書き・検証・公開・GC・再利用の経路。§3.5 の範囲で走行中に版 object を解放する経路は、今回の読解と検索では見つからなかった (陰性であって不存在の証明ではない)。
- 文面検査が header を読まないこと、未知の行種別が ParseError になること、判定器の 7 file が campaign lock の closure に入っていること。
- YCSB と TPC-C の workload が commit 前に body を使い終えること (TPC-C は段 3 相談 A の読解)。
- 費用の基準値 (§5.1) は既存の走行記録の値。

確かめていないこと:

- **設計のどれも実装・実走していない。** B・U の照合が壊し patch で実際に発火するか、TRACE ビルドの同期が実行をどれだけ変えるか、trace 量と判定時間の実際の増分は未測である。
- §3.1 の理屈 (MVSG 定理の適用) は、判定器の版順と辺の定義を読んだ上での論証で、判定器の実装に対する形式的な証明ではない。Cicada の版選択規則への適合は、どの案でも検査しない (§3.1)。
- B の主案 (版の外の事象台帳) の並行時の順序付けは設計の要件として書いただけで、具体的な実装と正しさは未検討。主案と代替案のどちらを採るかは実装 wave の段 4 に委ねる。
- 構成 C・E の forwarding patch の上で B・U がそのまま成り立つか (forwarding は未設置の書き込み版の wts を書き換える、D2287 項 4)。
- TPC-C・scan・delete・`REUSE_VERSION=0`・inline 版・`group_commit>0`。
- 今回の検索式と対象で見つからなかったもの (例: 走行中の版 object の解放経路) は、その範囲での陰性であって全経路の不存在証明ではない。

## 10. 工程

- 段 1 brief (親) → 段 2 設計案 (Codex、read-only、reasoning medium) → 段 3 相談 2 本 (Codex、read-only、レンズ A = 実装する側・設計の十分性、レンズ B = 実装しない側・過剰と費用対効果) → 段 4 裁定 (親、全所見 real・refuted 0、親 brief の (P4)・(P7) を撤回) → 本書 (親) → 段 6 独立 read-only レビュー 1 本 (Codex、レンズ = 事実の再抽出の正確さと主張の盛り) → 段 6 裁定 (所見 R1〜R5 すべて real・refuted 0) → 修正 → 焦点再レビュー (1 巡目 NO-GO: N1 read 側照合の母集団が `read_internal` 経由に限られ迂回を捕えない、N2 worklog fragment の旧見積り、N3 陰性の読解からの断定 → 修正 → 2 巡目 NO-GO: F1 read 側照合が件数の一致で登録漏れと余分な登録が相殺しうる、F2 scan への拡張の断定、N3 の残り → 修正 → 3 巡目: 既往所見はすべて closed・回帰なし、新所見 G1 (性能値を格上げする条件から read 側 API 照合が抜けていた) と G2 (案 A の I の壊し patch の書き方、nit) で NO-GO → 巡の上限 3 に達したので DW-O16 に従い親が G1・G2 を real と裁定し、文言を揃えて grep で照合して閉じた)。逐語は `verbatim/s6-*.md`。
- 段 6 の主な反映: B の方式を段 4 裁定の事象台帳に戻し、版の中の世代番号は代替案に (R1)、案 A の必須に read・write 両側の API 双方向照合 (R2)、「選び方の誤りは巡回として現れる」を撤回し版選択規則への適合は検査しないと明記 (R3)、壊しの成立条件を完了条件へ (R4)、byte 数と node 時間の算術 (R5)。
- 裁定の主な反映: U を双方向へ (A1)、B の照合区間と `REUSE_VERSION=0` の除外 (A2)、主張を観測した読みの 1SR に限定 (A4)、件数の自己申告を発火の証拠から外す (A5)、header の置き場の制約 (A6・B-1)、隠れた費用 (B-4)、推奨を案 A から中間案 M へ (B-6)。
- X / P / I の現行の意味の調査に、read-only の調査子 (Claude sonnet) を 1 本使った。
- 計算ノードの job: 0。
