## 前提の検算

指定された5ファイルと必要な一次測定記録を読んだ。静的レビューのみで、ファイル変更・pytest・監査・性能測定は実施していない。以下の `refuted` は「指摘した非等価化が計画上は回避されている」の意味であり、実装の合格を意味しない。

参照略号：

- **B**：[s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2637-offrepo-parallel-scan/s1-brief.md)
- **P**：[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2637-offrepo-parallel-scan/artifacts/dev-wave-t2637-offrepo-parallel-scan/s2-plan.md)
- **R**：[rulings-verbatim.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2637-offrepo-parallel-scan/rulings-verbatim.md)
- **A**：[tools/audit_dangling_commits.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2637-offrepo-parallel-scan/tools/audit_dangling_commits.py)
- **T**：[orchestrator/tests/test_audit_dangling_commits.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2637-offrepo-parallel-scan/orchestrator/tests/test_audit_dangling_commits.py)
- **E2／E3**：`output/insights/2026-09-16/t2637-offrepo-scan-yield/parent-measurements-{2,3}.md`

**主要な結論は、plan の走査分割と順序付き merge は成立するが、brief の性能値・受理条件・代表選択の記述は修正が必要、というもの。** 計画どおりの処理が安定した filesystem 上で抑止を増やす具体的経路は見つからなかった。ただし、複数 root と失敗回数の被覆は、現状のテスト記述だけでは十分に固定されていない。

## os.walk 意味論の等価性 (反例つき)

ローカルの `/usr/lib/python3.10/os.py:345` も確認した。走査途中の `OSError` では、その directory の iteration を返さず `onerror` を呼んで終了する。同ファイル:408 の yield 後、:418 で子 path の `islink()` を確認する。

以下の構成で `R` は探索根、`x.py` は basename・size・mode が候補と一致する regular file とする。

| 点検対象・反例構成 | 判定・根拠 | 成果物への影響 |
|---|---|---|
| root が file、または `R` の read／execute bits が0 | **refuted**。P:37、51 は A:889 の root 検査を主 thread に保持し、子には再適用しない。 | root 失敗の `failures=1` と findings 保持を維持できる。 |
| `R/x.py` と `R/a/x.py` が存在 | **refuted**。P:29、63 は root iteration を先に処理し、閉じた iterator を再開しない。 | root 直下候補の欠落・二重走査を回避する。 |
| `R/link -> /outside`、`/outside/x.py` だけが一致 | **refuted**。単に `os.walk(R/link, followlinks=False)` とすると top を辿るが、P:31、43 が入口の `os.path.islink()` を明記。 | この確認を落とすと探索外の一致で suppression が増え得るが、計画は防いでいる。 |
| `R` の scandir が `x.py` と `a/` を返した後で `OSError` | **refuted**。現行は root iteration 自体を返さず、候補0・失敗1。P:53、55 も部分 entry を救済しない。 | 途中取得した file／子だけを処理して、確認不能を成功扱いする変更を防ぐ。 |
| `R/a/deny1`、`R/a/deny2`、`R/b/deny3` の各 scandir が失敗 | **refuted（設計）**。A:902 は callback ごとに加算。P:40、129 は worker 内の回数を合算する。 | 正解は失敗3。worker ごとの失敗有無に丸めると2になり、確認不能件数を過少報告する。 |
| `R/a/x.py` と `R/b/x.py` が hardlink | **refuted**。P:48、63 は `(OID, dev, ino)` で merge し、代表は a、owners／aliases は union。 | 比較1回・両 alias 配布を維持できる。 |
| `R1/a/x.py` と `R2/b/x.py` が hardlink | **refuted（設計）／unknown（被覆）**。A:888 の root 順と A:945 の全 root 共通 group を P:36、63 が保持。P:170 は複数 root の fixture を明記していない。 | root ごとに group を分断すると比較回数・失敗数・alias 配布が変わる。 |
| roots が `(R, R/a)`、file が `R/a/x.py` | **real（被覆不足）**。A:589 の検証は worktree との重なりと同一 root の重複を扱うだけで、root 同士の包含を拒否しない。 | 正解は1 group に `(path,R)` と `(path,R/a)` の2 alias。訪問済み path の省略は alias と失敗回数を変える。 |
| `R/a` が directory、名前だけ候補 basename と一致 | **refuted**。P:42 は `filenames` だけを処理し、P:46 は `S_ISREG` を保持。 | directory を候補列へ混ぜて余計な `lstat`・失敗を発生させない。 |
| `R/a/x.py` の候補 `lstat` が失敗、symlink file／FIFO も存在 | **refuted**。P:44–46 は lookup 後の `lstat`、失敗加算、regular 判定を保持。 | 候補読み取り失敗の隠蔽や非regular実体による抑止を防ぐ。 |

入れ子 root の最小追加 witness は、上記 `(R,R/a)` に加え、`R/a/deny` の scandir を失敗させる構成でよい。同じ directory は両 root から走査されるため、現行の失敗数は **2**。物理 directory の重複排除は最適化として入れてはいけない。

P:57 の「安定した filesystem と同じアクセス結果」という限定は妥当。rename・chmod・削除と並走する場合まで、逐次版と並列版の同一観測を保証することはできない。

## 受理集合の不変

**real／must-fix：brief I4 の「path 昇順最小でもよい」は現行と非等価。**
根拠：B:41、A:943、A:989、P:61。放置すると、代表 path の変更が比較成功・`scan_failures`・suppression を変え得る。

例えば、`R/x.py` と `R/a/x.py` が hardlink なら現行代表は `R/x.py`、path 昇順最小は `R/a/x.py`。`os.open(R/x.py)` にだけ固定した `PermissionError` を注入すると、現行は比較失敗、最小 path 版は比較成功する。参照条件も満たせば findings が消える。これは同じ bytes・inode でも代表を自由に変えられない反例である。

P:63–73 は、代表 `_ExternalCandidate` と metadata を保持し、owners／aliases だけを union するので、この問題を正しく修正している。**brief 側も first-seen 保存へ揃える必要がある。**

**refuted：失敗件数の減少が必ず suppression 増加になる、とは言えない。**
根拠：A:1563、1592、1714、1820。`scan_failures` 自体は抑止の全面禁止条件ではなく、報告項目である。放置時の直接効果は確認不能件数の過少表示であり、同時に候補や代表が変わった場合には findings／suppression も変わる。両者を分けて検査すべきである。

**refuted：`possible == {}` を未走査と扱う計画にはなっていない。**
根拠：A:874、962、P:9、53。候補 metadata が空なら `({},0,False)`、候補があって全 root が失敗・一致なし・root 集合が空なら列挙関数は `scan_performed=True`。ここを混同すると未実施／確認不能の表示が変わるが、plan は区別している。

**real／must-fix：brief I6 の例外と rc の説明が広すぎる。**
根拠：B:44、A:1808、P:12、131。`ValueError`・`AssertionError` は現行の rc=2 捕捉対象ではない。plan の伝播方針を採り、brief を修正する。任意例外を rc=2 へ包むと、異常終了の契約が変わる。

## 決定性と test の恒真化

**refuted：置換案が単なる逐次／並列の相互一致だけになる疑い。**
P:159、170、179、183 は、独立の期待集合、代表と初期 stat、比較順、非空の report を要求している。共有 helper に同じ誤りが入って両経路が一致するだけでは合格できない設計である。

**refuted：小 tree では複数 thread の証拠を得られない、という一般論。**
P:181 の timeout 付き Barrier が実 worker を包み、2 task が同時に到達すれば、部分木数が workers 未満でも複数 thread の実発火を検査できる。workers 以上の部分木数は必須ではない。

ただし、**unknown／nit：複数回の task 回収・merge の被覆**は残る。P:170 は部分木数を固定していない。workers=4 に対し5個以上の有効部分木を置けば、待機 task が後から動く場合も検査できる。現在の記述だけから、その欠陥が成果物に出るとは断定しない。

**unknown／nit：wrapper が本物を呼ぶことは実装確認待ち。**
P:181 は「実worker」と書いており、P:183 は列挙・実 file 比較・抑止集約を実コードで通す。両層 stub の計画とは読めない。ただし実装時には、wrapper が保存した production worker を呼び、executor を置換していないことを確認する必要がある。thread ID だけを作る stub なら、実走査の欠落を見逃す。

**real／must-fix：失敗数テストの具体性が不足。**
P:162 は root 開始時・部分木内部・候補 `lstat` 失敗を列挙するが、以下は明記していない。

- root scandir が **entry を返した後**に失敗する場合。
- **同じ worker 内で2回以上** `onerror` が呼ばれる場合。
- **入れ子 root から同じ失敗を2回観測**する場合。

各1失敗の fixture だけでは、部分 entry の救済や worker／path 単位への誤った丸めを見逃す。上記の最小 witness を既存の予定テストへ含めればよく、新しい検査制度は不要である。

**refuted：並列禁止の静的 assert を残す計画。**
T:1183 の2つの文字列不在 assert は、P:153、187 で置換対象として明示されている。R:9 の「削除でなく等価性検査へ置換」と対応している。

## 変異の帰属

以下は登録候補の静的判定であり、KILLED の実測ではない。

| 変異 | 判定・単一の赤理由 | mask／最小是正 |
|---|---|---|
| **M0** docstring 言い換え | **refuted**：非等価変異ではない。P:214。SURVIVED が整合的。 | findings・rc に影響なし。 |
| **M1** worker walk failures を合算しない | **refuted（帰属可能）**：P:215 の failure-count node で件数不足。 | 有効 root・非空 candidates の下で worker 内 scandir を失敗させる。root 拒否だけでは変異箇所へ届かない。 |
| **M2** 最後の部分木を skip | **unknown／登録前修正**：P:216。末尾が symlink、空 directory、候補なしなら結果差がない。 | 最後の有効部分木に固有候補を置き、その group 欠落だけで赤にする。 |
| **M3** root 直下 filename 処理を skip | **refuted（帰属可能）**：P:217、T:1035。root 直下の固有候補が消える。 | 主要 fixture の直下候補を別部分木で代替できなくする。T:1035 が赤になるかは変異の分岐位置にも依存するため、専用の候補欠落 assert を帰属先にする。 |
| **M4** worker walk の `followlinks=True` | **refuted（帰属可能）**：P:218、170。worker 内 symlink 先の固有候補が増える。 | 直下 symlink だけでは入口チェックで mask される。plan は内部 symlink も明記しており、この点は満たす。 |
| **M5** 代表を後着結果で上書き | **refuted：「報告に出ないため kill 不能」ではない。** P:163、179、219 は内部代表を直接検査する。 | root直下／異なる部分木に同一 inode を置き、代表 path の不一致を赤理由にする。報告一致だけを期待 node にしてはいけない。 |
| **M6** worker 例外を空結果へ置換 | **refuted（帰属可能）**：P:164、220。注入した worker 例外が再送出されない。 | 有効 task で固有の例外を発生させる。Barrier timeout 等を赤理由にしない。 |
| **M7** worker から progress callback を呼ぶ | **refuted（帰属可能）**：P:165、221。callback の thread ID が caller と異なる。 | callback 到達を確実にし、thread ID assertion を赤理由にする。別の件数 assertion に先に落とさない。 |
| **M8** 既定16→0 | **refuted（帰属可能）**：P:112、166、222。env 未設定・非空候補の正常系が設定エラーになる。 | env override、空候補、root 未指定の report 早期 return では mask される。直接列挙の既定値ケースを使う。 |
| **M9** 空候補 return 前に executor 生成 | **refuted（帰属可能）**：P:125、167、223。executor 生成 trap が発火する。 | `audit_with_offrepo` の無候補結果だけでは不足。plan の直接列挙テストなら到達を固定できる。 |

**M2 は現状の文面のまま KILLED 予定を確定しない。** 他の変異も、表の到達条件と単一 assertion を実装後に確認してから登録する。M5 は登録不能ではなく、内部代表を直接検査するという現在の計画で帰属可能である。

## 親 brief の provisional 裁定と実測値の一般化

**P1：real／must-fix。改善すれば上限超過でも land 可、は逐語から導けない。**
B:49、P:14、290 に対し、R:133 は変更 wave の最大所要を受理条件として明記する。R:97 は「実装して実測し、足りなければ次段を有効化」という順序を許可するが、上限超過版の land を明示的に許可していない。実装・測定の実施と最終受理を分け、超過時の受理根拠として P1 を使用しないこと。放置すると未達の wave を受理済みとする。

**P2：refuted（plan が補正済み）。**
B:52 の「onerror は dir 1回」は root／worker 全体で1回という意味ではない。P:40 の callback ごとの計数、P:31 の入口 symlink 判定、P:63 の merge 順まで含めれば、安定入力に対する現行の値を再現できる。

**P3：unknown／nit。16 は試す値としては妥当だが、Python の最適値・倍率の根拠ではない。**
B:55、R:118、E3:80 が根拠。bfs の16 thread は Python の per-entry 費用や分割の偏りを測っていない。P:292 は転移を否定しているため、plan に性能保証の過剰断定はない。放置して保証値と扱えば、性能未達や掃除所要の見込み違いにつながる。

**実測値：real／must-fix。warm 455＋113 秒は異なる条件の混合。**
B:8、49 は修正が必要。[E2:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2637-offrepo-parallel-scan/output/insights/2026-09-16/t2637-offrepo-scan-yield/parent-measurements-2.md:8) は warm 全体 **478.123秒**、E2:21 は列挙 **455.376秒**。差は **22.747秒**。[E3:73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2637-offrepo-parallel-scan/output/insights/2026-09-16/t2637-offrepo-scan-yield/parent-measurements-3.md:73) は cold 残余113.5秒／warm残余22.7秒と区別する。約570秒を同一 warm 走の実測として使うと、必要倍率・改善率・上限達成見込みを誤る。478.123秒でも上限超過という結論自体は変わらない。

**3.8〜4.4倍：refuted（引用値の誤り）／real（標本説明の混同）。**
E3:29–39 の比率は概ね一致する。ただし「単一 thread 3走」は **GNU find 1走＋bfs 2走**であり、bfs 同一実装の3走ではない。file 数も各走で増えている。bfs 2走だけの平均でも約4.37倍なので丸めた4.4倍は変わらないが、D958 形式の独立3走や固定集合の等価性証拠にはならない。成果物への影響は性能根拠の強さの誤表示であり、この波の再測定を代替しない限り nit。

**P4：refuted。**
P:153–183 の独立期待集合＋report＋実 worker 発火は R:9 の置換要求に対応する。上記の fixture 不足を補えばよい。

**P5：unknown／nit。**
B:59、P:257、R:20 は別 node 初回走を試す点で対応する。別 node でも server cache は残るため cold の保証にはならず、plan はその限定を記載している。持越しを未測定のまま記録する限り、監査結果への影響はない。

**計測場所：real／must-fix、plan は補正済み。**
B:64 の login node 性能測定は `docs/pegasus-runbook.md:345` の現行方針と不整合。P:254 はこれを指摘している。個別例外の根拠が提示されていない以上、brief を計算 node 上の測定へ揃える。比較 node が変わるなら性能比較の条件として記録する。

## 既存 test の見落とし

指定された各 test について、plan どおりなら期待値変更は不要。ただし、既存の被覆範囲を並列全体の証拠へ拡張して読んではいけない。

| 既存 test | 判定・現物で確認した意味 | 成果物への影響／限界 |
|---|---|---|
| **T:1014** 空 directory heartbeat | **refuted**。非空 candidates、空 root、間隔0。root iteration の pulse で成立する。 | 元の heartbeat 契約は残る。worker heartbeat の証拠にはならない。 |
| **T:1035** flat filename heartbeat | **refuted**。monotonic は3値だけ。P:94 の pool／追加pulseなしを守れば維持。 | 余計な時刻取得は `StopIteration`、filename pulse 消失は期待行不一致で検出できる。 |
| **T:1538** 到達不能 symlink | **refuted**。Git symlink が metadata 候補から外れ、未走査になる検査。 | 意味は失われない。ただし外部 symlink directory の追跡禁止は検査していない。 |
| **T:1728** candidate basenameなし | **refuted**。walk trap と `scan_performed=False` は有効。 | executor 作成だけの回帰は捕まえないが、P:125 の追加 trap が補う。 |
| **T:1746** unreadable root | **refuted**。mode bits を root 検査で拒否するため失敗1。 | worker 内の unreadable 子 directory や複数失敗の証拠にはならない。 |
| **T:2056** 比較中 mtime 変更 | **refuted**。比較段の対象 inode に対する2回目の `fstat` を変更。 | 比較段は逐次のままなので、findings保持・失敗1の意味を維持。 |
| **T:2102** 比較中 ctime 変更 | **refuted**。上記と同じ構造で ctime を変更。 | thread 分割で意味を失う経路は見つからない。 |
| **T:2207** basename／size／mode prefilter | **refuted**。flat tree で OID 集合と cat-file 要求を独立に固定。 | 共通 helper の選別誤りを検出するが、worker 分岐固有の欠落は追加テストが必要。 |
| **T:2249付近** prefilter 後の mode 変更 | **refuted**。列挙終了後に chmod、比較時に失敗1。 | 再検査契約は残る。列挙自体の mode 選別を代替する検査ではない。 |
| **T:2280付近** same-OID hardlink fan-out | **refuted**。root file＋子1個、実比較1回、全 owners に両 alias。 | root／worker merge は検査するが、worker 同士・複数 root の merge は検査しない。 |
| **T:2343付近** 異 inode・同 bytes | **refuted**。2部分木、2 group、cat-file1回、両 path 配布。 | worker 結果の集約を検査できるが、同 inode の競合 merge と代表順は別検査が必要。 |

既存 test が計画上必ず赤になる、あるいは本来の意味を失って恒真になる例は見つからなかった。**不足は既存 test の期待値ではなく、新しい並列境界を被覆したとみなせない点にある。**

## 所見一覧 (real / refuted / unknown、must-fix / nit)

| ID | 判定 | 根拠 | 放置時の影響・最小是正 |
|---|---|---|---|
| A1 | **real／must-fix** | B:8、49；E2:8、21；E3:73 | warm基準値を約570秒と誤認する。478.123秒／残余22.747秒へ訂正。 |
| A2 | **real／must-fix** | B:49；P:290；R:97、133 | 未達 wave の受理を既裁定扱いする。実装・実測と land 判定を分ける。 |
| A3 | **real／must-fix** | B:41；A:943、989；P:63 | 代表変更で確認不能が一致になり抑止が増え得る。brief を現行 first-seen 保存へ統一。 |
| A4 | **real／must-fix** | B:44；A:1808；P:131 | 例外／rc 契約を変える。捕捉対象外は既存どおり伝播と明記。 |
| A5 | **real／must-fix（被覆）** | A:589、902、956；P:162、170 | 入れ子 root の alias・重複失敗、worker 内複数失敗を落としても見逃す。具体的 witness を予定テストへ追加。 |
| A6 | **unknown／登録前修正** | P:216、170 | M2 が等価変異になり得る。末尾部分木の固有候補欠落を単一の赤理由に固定。 |
| A7 | **real／must-fix** | B:64；P:254；runbook:345 | 計測場所の規律と比較条件が不整合。brief を plan の補正へ揃える。 |
| A8 | **real／nit** | R:106、212；E3:29 | 「bfs単独3走」と誤認する。GNU findを含む3走と明記。 |
| A9 | **unknown／nit** | B:55；P:292；E3:80 | Python の16 threadの速度は未確認。保証値へ転用しない。 |
| A10 | **refuted／修正不要** | P:29–55、61–73 | symlink top、途中scandir失敗、first-seen を計画は明示的に処理する。 |
| A11 | **refuted／修正不要** | P:163、179、219 | M5 は内部代表の直接 assertion で帰属可能。kill不能ではない。 |
| A12 | **refuted／修正不要** | P:181、183；R:9 | 実workerのBarrierと独立期待値は置換要求に対応。実装時の呼出先確認は残る。 |

## 総括

**P2 の部分木分割と現行順 merge は、安定入力に対する等価性を保てる計画である。全面的な設計変更は不要。**

実装前には、brief の warm 実測値、P1 の受理解釈、I4／I6、計測場所を訂正する。テスト計画には入れ子 root、途中 scandir 失敗、worker 内複数失敗の具体例を追加し、M2 の赤理由を固定する。

静的に非等価化を退けられた箇所と、実装・変異・性能測定で確認すべき箇所は分離した。テスト成功、実根での同一性、性能受理はいずれも未確認である。
