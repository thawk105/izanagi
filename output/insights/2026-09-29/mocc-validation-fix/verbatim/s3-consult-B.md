## 所見 — 事前登録と対照・費用 (1・2)

- **must-fix — 対照の成功条件が二通りに読める。** 親 brief は「F で同形の class A と G2 が出る」を完了判定に置く一方、plan は F の G2 が 0 件でもそのまま報告するとする（`s1-brief.md:3,12`、`s2-plan.md:91`）。0 件なら「修理前後で G2 を対照できた」とは書けない。**直し方:** 投入前に、F の G2 は観測結果として報告し、0 件なら同時刻の G2 対照は不成立、という判定に統一する。T_X の 112 走は固定し、結果を見て延長しない。

- **should — F の全 arm を X と同数にする必要はない。** 28 batch 案は T・N を F/X 各112走、P を各56走にして計560 benchmark と224 trace verifyを要求する（`s2-plan.md:91`）。依頼で112走が必要なのは修理後 T_X の陰性判定であり、N と P の同数反復は指定されていない（`request.md:28–31`）。このままでは費用が増え、2 node 時間の線を越えやすい。**直し方:** T_X=112を保持し、F の G2 対照に要る T_F の数を結果前に固定する。N は両側の class A、P は両側の TRACE=0 commit 数を観測できる小数の対でよい。T_F を減らすほど G2 を見られない確率が上がることを記す。

- **must-fix — smoke の外挿式が固定費を二重計上する。** plan は「一 batch の Elapse ×28」に六 build と verifier の固定費を足す（`s2-plan.md:93`）。旧完走 smoke の267秒にも build と当該 batch の verify が含まれる。旧本走は2 jobで計6,328秒、28 batch 当たり約226秒だった（`t2872-mocc-g2-split/README.md:55–58`）。**直し方:** smoke 内で build等の固定費 \(B\) と benchmark・verify の batch 費 \(M\) を分け、予定 job 数の \(B\) と予定 batch 数の \(M\) を足す。変更後六 arm の実測 Elapse が出るまでは、2 node 時間未満と確定しない。旧本走を単純に倍にした約3.52 node 時間は目安に留まる。

- **should — 順序の記述が実装条件になっていない。** 旧 runner は arm 名の配列を batch ごとに回転する（`t2872_probe.py:80–82,580–587`）。六 arm 化だけでは各 F/X 対が隣接し、先後が交替する保証はない。build と cache の温まり方も先後に依存する。**直し方:** F/X の対ごとに実行順を明示し、batch ごとに逆転させる。実行順、arm 別 source SHA、binary SHAを結果に残す。P の commit 差は観測値とし、修理の性能効果と断定しない。

## 所見 — 計器・runner・CI・D297 (3〜5)

- **should — X の V3 は F の V3 と同じ条件で採れない。** F では V3 が元の `max_rset_` の後、X では修理の V2 比較を通過した後に置かれる（`s2-plan.md:85–87`）。X の V3 は追加 abort を生き残った取引だけの値となる。class A の位置を揃える方針は妥当だが、class B の F/X 件数を同じ母集団の比較値にすると insight の解釈が変わる。**直し方:** Vmid と L の位置を揃え、判定には commit 側 class A を使う。class B は各版内の補助観測として表示し、F/X の率比較をしない。

- **must-fix — runner の source 固定は「arm に SHA を持たせる」だけでは完了しない。** 旧 runner は単一 pin を全 clone に checkoutし、verify時も `sources['T']` を渡す（`t2872_probe.py:498–525,621–627`）。六 arm 化でここが残ると F の traceをXのsourceで検査し得る。**直し方:** 各 arm の full OIDで detached checkoutし、HEADの完全一致を検査する。buildとverifierの両方へそのarmのsourceを渡し、対応するprobeのSHAとbinary SHAも記録する。template→probeを各々 `git apply --check` 後に適用して失敗時停止、F の P/N とXの P/N を別々に macro off 比較するplan（`s2-plan.md:89`）は正しい。

- **must-fix — D297 の `rc=1` だけでは予測した不一致を実証できない。** 検査器は正規化出力が違う最初の context で例外を投げ、CLI は他の失敗も同じ `rc=1` にする。失敗時に pass report は出ず、include 活性の比較まで進まない（`check_trace0_preprocess_identity.py:596–615,1179–1192`）。**直し方:** GCC 11/12 それぞれの stderr に `cc/mocc/transaction.cc` の「TRACE=0 正規化 preprocess 出力が不一致」があることを記録する。`git diff-tree --raw -r F X` で変更 path が `.cc` だけ、header が0と記録する。結果名は **D297不合格（意図した修理差分）** とし、include 活性合格とは書かない。F→Xのsource diffが修理hunkだけなら、全contextの前処理差を別途列挙する必要はない。D297をpass扱いできない点をpin前進waveへ渡すplanは妥当。

- **nit — formatの二重実行は受入条件より厚い。** CI `:latest` image のclang-format 14.0.6で全対象を通せば、指定のformat CI相当を満たす。loginの14.0.0は編集時の即時確認には有用だが、両方を成果物の必須判定にすると記録と実行が増える（`s2-plan.md:60`、`D2293.md:8`）。**直し方:** image側のrc・対象数・versionを本判定にし、login側は任意の補助記録にする。buildはFへの親OID固定、clean依存供給、`--userns`、CIとの差の明記という先例の改作が必要であり、planの範囲は適切（`run_ci_build.sh:9,24,34–41,71–89,92–105`）。

## 所見 — patch 棚卸しと過剰・削除 (6・7)

- **should — 既存不適用の内訳を表で分ける。** Fでは10本中5本が失敗するが、Cでも計器3本は既に失敗し、C→Fで新たに失敗したのは early-unlock と hot-update-unlock の2本である（`inventory/C/result.tsv:3–12`、`inventory/F/result.tsv:3–12`）。planの **F=0→X≠0** だけを「今回新たに外れた」とする判定は正しい（`s2-plan.md:97`）。**直し方:** C→Fの2本、Cから既に失敗した3本、F→Xで新たに失敗したものを別欄にする。親の「Fで既に外れる2本」をFの全失敗数と一般化しない。

- **should — `git apply --check` は壊しpatchの意味を証明しない。** `broken-mocc-lockskip-validation.patch` はread setのlock検査ではなくwrite setのlock取得を条件付きで飛ばす（`patches/broken-mocc-lockskip-validation.patch:4–15`）。planはこの読み違いを正している（`s2-plan.md:99`）。**直し方:** Xに適用できたpatchについて、macro有効時に狙った経路がなお残るかをsource上で判定し、静的に決められないものは「意味未確定」と記す。「修理後もG2を実際に起こす」等の実測主張まで行う場合だけ実走が要る。依頼の棚卸しと段4裁定のためにpatch自体を直す必要はなく、planも修正を提案していない。

- **nit — 成果物を増やす検査は削れる。** planのP_F/P_X各56走、N_F/N_X各112走、loginとimageのformat二重本判定、D297失敗後の全context前処理差の別途立証は、指定された判定値を増やさず費用と記録を増やす（`s2-plan.md:60,79,91,103`）。一方、T_Xの112走、欠測・溢れを含むR0、F/Xそれぞれのmacro off一致、armとsourceの固定、F/Xのpatch適用表を削ると、G2 0/112・class A 0・棚卸しの主張が崩れる。**直し方:** 前者を縮小し、後者を維持する。

## 推奨する実測構成と見積り

事前登録案は **T_X 112、T_F 56、N_X/N_F 各8、P_X/P_F 各8**、計200 benchmarkと168 trace verify。T_Fを56にすると、旧観測のG2率5/112を仮に使った場合、Fで0件となる確率は約7.7%である。0件ならFのG2対照は不成立と報告し、延長しない。NとPは対で交互に走らせ、commit数は観測として記す。

旧本走の約226秒/batchを六armへそのまま外挿して2時間以内とは言えない。新runnerのsmokeで **build等の固定費、arm別benchmark時間、batch後verify時間**を分けて測り、予定回数で合算する。見積りが2 node 時間以上なら、既裁定どおり投入前に確認を取る。

## 総括

planの中心であるT_Xの112走固定、F/Xの同時刻対照、macro offの版内比較、F=0→X失敗のみを新規patch不適用とする判定は妥当。修正が必要なのは、FのG2が0件だった場合の完了表現、smoke費用の計算式、runnerのarm別source保証、D297の`rc=1`の読み方である。今回は指定資料の静的検査のみで、build・テスト・benchmarkは実行していない。