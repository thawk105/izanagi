## 所見一覧 (番号・real/refuted/判定不能・file:line・1 行要旨)

以下、`T`＝`orchestrator/tests/test_s8b_oracle_driver.py`、`H`＝`orchestrator/campaign/s8b_holdout_freeze.py`、`M`＝`orchestrator/campaign/t080_freeze_migration.py`、`G`＝`orchestrator/campaign/s8b_oracle_driver.py`。brief・plan・逐語資料の相対名は、指定された `/home/SFC/tanab/.claude/jobs/268b85b6/tmp/wave/` 基準。

1. **real** — `s2-plan.md:83,91,99`、`H:373`：可視性だけなら remove/add で戻せるが、比較開始状態の再現には保存した A/B index の復元が適切。
2. **refuted** — `H:374`、`orchestrator/tests/fixtures/sort_swo_masstree/.gitignore:8`：index から除いた config.h が untracked 側で再出現する懸念は、現在の ignore 規則下では成立しない。
3. **real** — `H:334,383`：プロセス全体への `GIT_INDEX_FILE` 注入は submodule 列挙にも伝播する。回避理由は正しい。
4. **判定不能** — `s2-plan.md:106`、`verbatim/T2559-insight-s4.md:29`：N=20 対で ms〜秒級差を分離できる根拠はない。既存値は copy の変動で、scan の対差分散ではない。
5. **refuted** — `M:1727,1731,1757,2022,2035,2343,2490`：正常な default 経路の「13 scan」は検算と一致する。
6. **real** — `T:1452,1453,1596`、`M:1790,2068,2122`：「取り込み＋13×scan 差」は部分モデルであり、発行全体の増分実測ではない。
7. **real** — `s2-plan.md:87,94`、`T:1451`：一般解は419 pathを指定する。ただし418件すべての再 hash・blob 再生成が必須という説明も誤り。
8. **判定不能** — `T:49,961,1364`、`s2-plan.md:144`：直接 import を阻む必然的経路は確認できないが、import 成功・退避後の module 解決は未実走。
9. **refuted** — `s2-plan.md:144`、`tools/__init__.py` 不在：cwd の `tools/` が先にあるという理由だけで、job dir の probe が必ず隠れるわけではない。
10. **real** — `s1-brief.md:9,12`：login node 指定は提示された性能測定規律と不整合。「ms 級」は静的には根拠不足であり、秒級だと反証できたわけでもない。
11. **real** — `s1-brief.md:10`、`T:1380`：419/418件の集計は再現したが、これだけで射影後の全集合一致は証明できない。「untracked 0」は非 ignored に限る。
12. **refuted** — `s2-plan.md:154,155`、`verbatim/D2086.md:5`：一般解が文字どおり1行でないこと、hard-code が追加 snapshot 集合を要しないこと、10%基準を自動転用できないことは妥当。

## index 切替と統計設計 (攻撃点 1・2)

**scan 比較には保存した A/B index の切替を推奨する。**

A は builder の `issue_receipt=False` 戻り時点の index、B は A に取り込み操作を施した index とする。各 index を fixture 外へ保存し、Git 子プロセスが終了した状態で復元する。timed 区間は `search_repository(root)` だけとし、復元・集合検査は外へ置く。

`git rm --cached -- <path>` と `git add -f -- <path>` でも、現在の config.h の membership は往復できる。ただし index の stat・拡張情報まで元通りになる保証はない。`git update-index --force-remove -- <path>` は実体を残して index entry を除けるため、可視性操作として明確である。いずれも対象は disposable fixture に限定する。

A では次の両方から消える。

- tracked 側：`H:358` の `ls-files -s` に entry がない。
- untracked 側：コピー済み `.gitignore:8` の `/config.h` が `H:374` の `--others --exclude-standard` から除く。

B では regular entry として tracked 側から入る。したがって、現在の規則では期待する集合差を作れる。

`GIT_INDEX_FILE` 回避理由は成立する。`H:334` の subprocess は環境を継承し、`H:383` の ccbench 列挙にも同じ指定が届く。加えて、**Git 操作用 subprocess だけを sanitize しても scanner の環境は sanitize されない**。probe 自体も `GIT_DIR`、`GIT_WORK_TREE`、`GIT_INDEX_FILE` 等を持ち込まない環境で起動する必要がある（`T:369` と `H:334` の相違）。

なお、B は既存 HEAD に対して staged addition を持つ。これは scan 単体比較には使えるが、`M:1833` の clean 条件を満たさず、そのまま発行 A/B へ流用できない。

**N=20 は探索的な規模としては使えるが、精度保証ではない。**

D2086 の53.3秒÷13＝約4.1秒は、scan 以外も含む発行 subprocess wall を割った概算であり、scan 単体の実測値ではない。まして対差の分散は得られない。

必要 N の桁は、独立・概ね正規な対差という仮定下なら、対差の標準偏差を \(s_d\)、中央値の95%区間半幅を \(h\) として、おおよそ

\[
N \simeq (2.46s_d/h)^2
\]

となる。例えば、仮に \(s_d=40\) ms なら、半幅10 msに約97対、1 msに約9,700対を要する。\(s_d=400\) msなら、それぞれ約9,700対、約97万対となる。これは計画用の仮定例であり、必要 N の確定値ではない。N=20の半幅は同じ近似で約 \(0.55s_d\)。

AB/BA交互は順序効果を均すが、長周期負荷・自己相関・cache の持越しを消さない。順序別の対差も返し、中央値・IQRだけで「許容値以下」と判定しない。固定予算で分離できなければ、その事実を成果とする。

**実走場所は計算ノード。login 先行の二段案は採らない。** 性能測定の場所に関する提示規律に反するうえ、初回を捨てれば構築費も重複する。仮に構築200秒、scan約4.1秒なら、40 scanで約164秒、warm-up込み44 scanで約180秒、合計約380秒である。ただし `issue_receipt=False` は発行を省くため、構築200秒という値自体も今回の probe 用には未確定。queue待ちの現在値は資料になく、大小比較は判定不能。queue待ちは利用者の待ち時間として別記し、処理時間へ混ぜない。

## 13 scan と所要モデル (攻撃点 3・4)

| 呼出し | 静的な経路 | 回数 |
|---|---|---:|
| draft | `T:1571 → M:1959 → M:1727`、`M:1731 → H:1029`、`M:1985 → M:1891` | 3 |
| 明示 validate | `T:1574 → M:2022 → M:1757` から上記2 scan、`M:2023 → M:1891` | 3 |
| finalize | `T:1575 → M:2035` の validate 3 scan、`M:2048 → M:1891` | 4 |
| verify | `T:1600 → M:2343 → M:2201` | 1 |
| gate | `T:1601 → G:599 → G:169 → M:2343`、`G:465 → G:299 → M:2490` | 2 |
| 合計 | 正常な default 発行・検証経路 | **13** |

`_rerun_draft_reconstruction` は1回の呼出しで holdout reconstruction を1回呼び、その内部に明示 scan と verifier 内 scan の2回がある。「rerun 関数自体が2回呼ばれる」という意味ではない。また明示 validate と finalize 内 validate の双方から呼ばれる。

gate の adapter は `G:245,258` の条件付きである。13は正常経路の回数であり、早期拒否や別モードへの一般化は不可。

所要モデルには少なくとも以下が残る。

- basis commit の tree/object 作成・index refresh、activation commit（`T:1452,1596`）。
- dirty 検査の `git status --porcelain`（`M:1790,1833,2012`）。
- history の graph/tree/blob 読出しと receipt の working bytes 検査（`M:2062,2068,2122`）。
- receipt の basis OID変更に伴う bytes・hash等の処理差。
- draft/receipt の存在、別 subprocess、cache 状態による scan ごとの差。

特に、`inspect_receipt_history(check_worktree=True)` を「全 worktree の status 走査」と説明してはいけない。該当箇所は receipt path の存在・bytes 検査であり、porcelain 走査は別経路である。

したがって `取り込み + 13 × 対差中央値` は**部分的な換算値**としてなら提示可能だが、全発行 wall の中央値でも、その上限でもない。

一般解の419 path中418件が既に index にあり、bytes/stat が一致していれば、Git は必ずしも内容の再 hash を行わない。一方、path の照合・stat 確認・必要な refresh と、config.h追加による index 更新は発生しうる。stat が古い、racy な状態なら内容確認も増える。

hard-code案との差は測る価値がある。一般解には source側の列挙もあり、1 path案にはない。ただし plan の A index は **commit後**（`T:1452`）で、採用位置は **add -A直後・commit前**。index の refresh/cache 状態が異なり得るので、取り込み操作の測定値にもこの限界を付す。初回 object 作成と、A復元後も object が残る反復値は分ける。

## import と起動形 (攻撃点 5)

- **temp：planを支持。** `T:49` は3環境変数すべてを検査する。`TMPDIR`だけ直しても、`TEMP`か`TMP`が実 output 配下なら拒否される。import前に全て整える。先行 import による `tempfile` の選定 cache にも注意する。
- **xdist：planを支持。** `T:961` は import時に参加処理を呼ぶ。`PYTEST_XDIST_TESTRUNUID`をimport前に除去する。builder を直接呼ぶだけでもこの副作用は避けられない。
- **sealed decorator：懸念を反証。** `s8b_v2_freeze_fixture.py:105` の wrapper実行時にforkする。importそのものではforkせず、`T:1364`のbuilderにも付いていない。
- **conftest：自動実行の懸念を反証。** 通常のmodule importはpytestのconftest探索・autouse fixture実行を行わない。直接参照したfixture/test module群にもconftestへの明示importは見つからなかった。`orchestrator/tests/conftest.py:28`も素のPython経路を区別している。ただし、conftest自体を明示importすれば`同:52,61,107`等のトップレベル処理は動く。「副作用がないファイル」とは言えない。

退避後の起動について、worktreeの `tools/__init__.py` は存在しない。したがってcwdの `tools/` はnamespace package候補であり、job dirにも `tools/` があれば、その部分を合成できる。**cwdが先だから退避先は必ず見えない、という反証は成立しない。**

ただし、以下は実行条件になる。

- worktree側の同名probeを残すと、そちらが先に解決され得る。
- 別の検索先に通常package `tools` があると、namespace探索結果を上書きし得る。
- `PYTHONPATH`はprobe実行開始前に設定する必要がある。probe内部で設定しても自身の発見には間に合わない。
- 起動時に `__file__` の解決先が退避先であることを確認し、source HEAD・実装moduleの由来も記録する。

`python3 -B -m tools.<probe>` の実成功は未確認。静的に成立可能であることまでの判断である。

## 時間許容値と親 brief の誤り (攻撃点 6)

一般解は、NUL転送・空集合・非コピー対象・snapshotとの対応を扱うため、文字どおりの1行修正ではない。hard-codeはコピー済みconfig.hを指定するだけなので、新たな可変path集合のsnapshotを要しない。D2086のprotoを将来採る場合も、この差は残る。

D2086の10%は**高速化を採るための改善幅**であり、忠実性を1 file増やすために許容する退行幅ではない。200〜222秒の10%、すなわち20〜22.2秒を自動的に許容する根拠はない。

依頼文の「受入300秒上限」「e2e 200〜222秒」「shard-0 span 231秒」を前提とするなら、推薦する裁定案は次のとおり。

- **費用許容値案：critical pathへの追加を1秒以内。** e2eの約0.45〜0.5%、231秒spanの約0.43%に相当する、小さい予算として事前に置く。既存裁定ではなく、本件への提案である。
- 300−231＝69秒は、その観測の見かけの余裕にすぎず、本件の使用可能予算にしない。別shard・負荷変動もある。
- scan換算だけなら、取り込み時間を無視しても1秒÷13≒77 ms/scanが目安。非scan項の余地が必要なので、77 ms以下というだけで採用確定にはしない。
- 区間が許容値をまたぐ、または未測定項が結論を左右するなら「費用上限未確認」として裁定へ返す。差を検出できないことと、許容値内であることを区別する。

親 brief の個別主張は次の評価となる。

**419/418件：再確認できた。** sanitized Git環境で `ls-files -ci -- orchestrator output` は419件、`check-ignore --no-index` の内訳は `.gitignore:25` が418件、fixture内 `.gitignore:8` が1件だった。ただし、これは当該範囲・当該時点の集計であり、basis復元等を含む最終集合の証明ではない。

**config.hの三軸語0件：再確認できた。** 10,448 bytesに対し、`H:64`の `ycsb_rratio`、`ycsb_zipf_skew`、`ycsb_rmw` は各0件。現在のbytesが三軸hitを追加するという反証はない。file_countと、採用時のbasis tree/commit OIDまで不変にはならない。

**untracked 0件：限定が必要。** 非 ignored untracked は0件だが、ignored untracked は9件あった。全て `__pycache__/*.pyc` で、`T:1382`のcopy除外に該当する。今回の追加欠落を示す証拠ではないが、「untracked実体が全くない」という一般化は誤り。

**login node：実施条件として誤り。** 交互対比較でも、性能測定を計算ノードで行う規律は解除されない。

**ms級：未証明。** 追加のread/decode/prefilterが小さいという方向の根拠はあるが、一般解の列挙・index処理・環境変動を時間へ換算できない。静的に否定できるのは断定の根拠であり、真の増分がms級である可能性ではない。

## 裁定パッケージ候補 (scope 外)

採用が裁定された後の別wave候補として、実builder由来fixtureで config.h のindex membership・production列挙membership・bytes一致を検査し、取り込み処理の削除変異を殺すテストを置く。

一般解を選ぶ場合に限り、snapshot集合との対応や非コピー対象の扱いを設計する。追加helper・gate・恒常的docs整備は本調査waveに混ぜない。

## 総括

planの13 scan、indexによる可視性切替、直接import案は静的には成立する。修正が必要なのは、**N=20の精度保証、post-commit indexで測る取り込み費用の代表性、部分モデルから発行全体への一般化、起動moduleの由来確認**である。

段5へは、計算ノードで実builderを1回構築し、保存indexによる対比較、集合差、一般解とhard-codeの取り込み費用、生データと不確実性を返す形で進められる。静的検査と読取専用の集合確認のみを行った。pytest、fixture構築、import、性能測定は実行しておらず、緑は主張しない。