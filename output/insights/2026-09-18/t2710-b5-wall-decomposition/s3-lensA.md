## 判定と参照記法

**must-fix は 3 件です。最も重大なのは、B/C の collection 変更が xdist への collection 送信後になる点です。** plan は親 brief の多くの誤解を訂正していますが、この実装位置では対比較が成立しません。

指定資料と関連コードを静的に確認しました。pytest・計測・ファイル書込みは実施していません。

以下、`P`＝段2 plan、`Bf`＝親 brief、`T`＝`test_s8b_oracle_driver.py`、`F`＝`conftest.py`、`AS`＝`acceptance_shards.py`、`RT`＝`run_tests.py`。`LS`・`Remote` は指定環境の xdist `scheduler/loadscope.py`・`remote.py`、`V` は指定 verbatim ディレクトリです。

## must-fix

**M1．B/C の `pytest_collection_finish(trylast=True)` は遅すぎる。**

- **根拠：** P:130、140。F:2193、2263–2275 は wrapper の復帰側で reorder するため、通常の `collection_modifyitems(trylast=True)` では後段にならない、という指摘は正しい。しかし Remote:256–262 の通常 `pytest_collection_finish` は、その時点の `session.items` の nodeid 一覧を controller へ送信する。probe の trylast はその後になる。controller は送信済み collection の index を渡し（LS:275–282）、worker は変更後の `session.items[index]` を実行する（Remote:211–222）。
- **成果物への影響：** B は予測した node と実行 node が食い違い、C は index のずれや範囲外参照を起こしうる。B−A/C−A を pairing・除外の効果として解釈できない。
- **是正案：** B/C の変更を **worker の `pytest_collection_finish(tryfirst=True)`** に置く。この別 hook に入る時点で F の modifyitems wrapper は復帰済みで、Remote の通常 finish より前に変更できる。より明示的には finish wrapper の yield 前でもよい。全 worker の変更後 collection と controller が受信した collection の一致を確認する。AS の元 allocation を C の診断資料として保持する方針は維持できる。

**M2．分割・縮約 model の式が、現行の相方まで改善として消してしまう。**

- **根拠：** P:259–261、271–274 は `max(L,D/48)+F`。一方、P:210–214 は実測 A を `W=L+P+F` と分解する。D2121 と V/t2750:28 は、前者が相方・開始遅れ等を含まない下限 model であることを明記している。
- **成果物への影響：** 変更で `L` も平均負荷も下がらなくても、実測 A と model を直接引くと約20秒の「改善」を作れる。縮約の採否・費用対効果が過大評価される。
- **是正案：** 同じ走から現行の `W_A_model=max(L_A,D_A/48)+F_A` も計算し、候補との差はまず **model 同士**で示す。`W_A−W_A_model` を model が説明しない残差として併記する。候補 wall の数値は下限参考値と明記し、相方・配布・待ちの変化を別の感度として扱う。C の診断実測をこの欠落の補正値に流用しない。

**M3．観測 overhead を「未実測の限界」とするだけでは、本体／固定費の優劣を決められない。**

- **根拠：** P:73–78、98–102。`item.module.shutil.copytree` は共有 module の属性なので、採録対象を限定しても再帰呼出しは wrapper の判定を通りうる。controller の観測は M だけでなく全 node の全 phase に及ぶ。JSONL を node 終了後にまとめても、書込み時間が次の配布・終了を遅らせれば `W−O` 側に現れる。
- **成果物への影響：** copy/build の比率や shard 固定費に観測コストが混ざり、小さい pairing 差や分割 model の順位を変えうる。
- **是正案：** 採録 span 数だけでなく wrapper 総通過回数、controller report 数、JSONL bytes・flush 所要を取る。計算ノードで時計取得・通過判定・記録処理の単価を評価し、少なくとも
  `H ≈ 通過回数×判定単価＋採録数×記録単価＋書込み時間`
  の感度を示す。並列 worker の H の総和を wall へ足さず、律速 worker と controller の経路を分ける。これは間接的な I/O・cache 擾乱を保証する上限ではないため、結論がこの不確実幅で反転する場合は同条件の観測 on/off 対比較を各3走以上追加するか、当該結論を保留する。静的読解だけから「無視できる数ms」とは言えない。

## should

**S1．replica の D357 適合と、実受入への適用可能性を別判定にする。**

- **根拠：** D357:3–6、Bf:39、P:51–60、361。plan の「replica に限定した結果」という判断は妥当。歴史93 session は同一 tip の反復ではなく、land の1走も3反復を補わない。
- **成果物への影響：** 歴史範囲内というだけで A を受入 shard-0 の代表値にすると、実受入 wall の改善を未実証のまま裁定パッケージへ載せる。
- **是正案：** 歴史照合は次の式で**記述的診断**として固定する。指標 \(j\) は W/O/F/L、歴史値を \(h_{ij}\)、A の値を \(a_{rj}\) とする。

  \[
  I=\bigwedge_{r=1}^{3}\bigwedge_j
  [\min_i h_{ij}\le a_{rj}\le\max_i h_{ij}]
  \]

  percentile は、例えば \((\#\{h<a\}+0.5\#\{h=a\})/93\)、中央値比は \(\mathrm{med}(a_j)/\mathrm{med}(h_j)\) と事前固定する。**I が真でも同等性合格ではない。** min–max は極端に広く、周辺分布の包含は同時分布・因果的忠実度を保証しない。

  A の値を実受入の推定として使うには、同一入力・同等環境の実受入形 R を3走以上取り、A/R の対比較、事前に決めた許容差、走間変動を示す必要がある。D357 の単発10%規則は同等性マージンではない。費用を払わない場合は P:361 の限定を維持し、「受入 shard-0 の値」と呼ばない。

**S2．同一 tip でも replica と実受入の I/O 条件は一致しない。**

- **根拠：** RT:1495–1532、AS:895–920、F:2122–2125・2173–2178、T:827–872・943–1000・1379–1385、P:24–35・108–116・189–199。
- **成果物への影響：** base build/copy が短くなった理由を、本体・同 host 競合だけに誤帰属する。
- **是正案：** 差分表を次の粒度まで具体化する。

| 面 | 静的確認結果と必要な扱い |
|---|---|
| 選択 | 本物の AS と同じ universe・台帳なら allocator は再現できる。M の file が同じだけでは universe 一致にならない。 |
| 並べ替え | F の cost 順に加え、LS の cardinality 順も同じである必要がある。 |
| plugin/spec | `-p tools.acceptance_shards` と有効 spec が必要。spec 無しでは F の shard 状態確認・controller collection 判定が変わる。 |
| argv/env | replica の `-B`、`PYTHONPATH`、明示 basetemp は実 child との差。実 interpreter、plugin 集合、pytest 設定も記録する。 |
| temp | shared base は `tempfile.gettempdir()`、複製先は `tmp_path`。両方の実 path と filesystem が同等か確認する。「TMPDIR を設定した」だけでは足りない。 |
| 共有形 | base は ROOT と testrunuid の hash で同一 session の worker 間共有。3 shard 間で一つの base を共有する構造ではない。 |
| 3 shard 不在 | 他 shard による Lustre の source 読み・metadata アクセス等の負荷が消える。node-local へのコピーでも source は共有 FS を読み、base build に効きうる。 |

なお、各 run の TMPDIR 分離は既存 base の再利用を防ぐが、OS page cache・Lustre 側 cache の温まりは防がない。

**S3．Latin square は位置を均等化するが、対差の中央値の位置効果を必ず消すわけではない。**

- **根拠：** P:168–201、238–240、D357。各条件は各 job・各位置に1回ずつ現れる。しかし job 1 の S1×3→S×3 は条件と実行時期が完全に重なる。
- **成果物への影響：** cache の温まりを S1/S 差や B−A の中央値に混ぜ、「位置効果を打ち消した改善」と誤記する。
- **是正案：** 「加法的な job 効果・位置効果を平均で均衡化する設計」と限定する。例えば位置効果が 0/10/20秒なら、ABC/BCA/CAB の B−A は 10/10/−20秒となり、**中央値は10秒**で、真の条件差0でも残る。P:240 の全対差・中央値は残してよいが、条件別中央値の差、実行位置、host を必ず併記し、完全補正済みと呼ばない。順序依存の carryover もこの3系列では均衡化されない。

  S1/S の比較も重視するなら、同じ6走を交互に配置する。1 job 内3走は D357 の最低反復数を満たすが「当該 host の逐次反復」であり、別 job 3走の host 間変動を代表しない。job を分けても同じ host が割り当たる可能性はある。

**S4．B は初期相方の軽量化と、worker 全体の tail 短縮を分けて評価する。**

- **根拠：** LS:238–251、308–336、367–402、P:142–162。
- **成果物への影響：** 初期相方を軽くできても、後続 unit の追加で wall が変わらないことを「pairing 未発火」または「改善」と誤判定する。
- **是正案：** P の cardinality sort 再適用確認は採用する。ただし初回追加配布は pending **item 数≤2** の worker にだけ行われる。最初の48 unit に大 group があれば、次の unit の対応は k→48+k にならない。

  最長 node 完了時に `mark_test_complete` が `_reschedule` を呼び、queue が残っていれば3個目が追加されうる。したがって「初期相方の cost」「実相方 duration」「当該 worker の全後続 node」「最忙 worker の移動」を分ける。G11 の cardinality sort は collection 側の49〜96位操作を打ち消しうるが、P:156–160 の固定点確認で検出できる。M1 修正後の設計は、この条件付きで現物と整合する。

**S5．歴史資料は定義が概ね一致するが、母集団・完走状態・例外の扱いを揃える。**

- **根拠：** V/sessions-shard0:1・99–105、V/t2750:17–19、V/sessions-m11-and-shards:3–23、V/sessions-fixed-cost-breakdown:3–11、AS:948–972・1129–1133。
- **成果物への影響：** 未観測 node・異なる tip・異なる collection を一つの同条件分布に見せ、忠実度と相方の安定性を過大評価する。
- **是正案：** W＝JUnit testsuite time、O＝worker の phase duration 合計最大、F＝W−O は T-2750 と同じ定義。ただし JUnit testcase time が total 設定であること、対象 session の成否・selected/finished を確認する。95 session 表の worker 数49は、AS が `unobserved` を occupancy entry にするため、直ちに49実 workerを意味しない。M の多くが94件、g7だけ95件という差も説明する。93/95/97件の表を無条件に結合しない。

  shard 固定費は、資料の記号なら厳密には
  `W−O=(C−T0)+(Ffirst−C)+(Llast−Ffirst−O)+(E−Llast)`。
  実行区間内の空白も含む残差であり、collection＋終了処理だけではない。列の和が W に戻る検算は恒等式なので、timestamp の timezone 解釈の正しさまでは証明しない。

## 個別論点の確認

**観測 wrapper と lock 分解は、P の包含関係を守れば成立する。**

T:918–940 の get は flock 取得後に必要なら build し、marker を読み戻す。`get−build` 全体を lock 待ちと呼ぶのは誤り。P:78–87 の `flock(LOCK_EX)` 前後の計時は適切だが、名称は厳密には「lock 取得呼出し時間」で、非競合 syscall の時間も含む。寿命 lock は別にする。

`verify_receipt` 本体（`t080_freeze_migration.py`:2284–2391）に自己再帰・内部 retry はなく、`_gate_check_call`:2239–2246 も check を1回実行する。トップレベル verifier wrapper 自体による再帰的二重計上の根拠はない。ただし builder 内の処理・子 process の verifier は別で、span の包含関係を守る必要がある。T:876–891 の削除 retry を verifier retry と混同しない。

**S1 の `-n 1` は process memo 条件ではない。**

Remote:416–425 は worker 数に関係なく `PYTEST_XDIST_TESTRUNUID` を設定する。Remote:392–400 は `--dist loadgroup` を worker の `loadgroup=True` へ反映するので、F:1867–1873 の分岐も成立する。したがって S1 も T:946–983 の shared-base 経路を使う。process memo は testrunuid のない非-xdist 条件の話である。

S は最大11 worker が複数 key の build・同一 key の待ち・copy を並行する条件。必ず11本が同時に get へ到達するとは限らない。P:242 の「実行 regime 差」は適切で、Bf:49 の「競合なし」「競合の膨らみ A−S」は採らない。比較は shard wall と同名 node の成分差を分ける。

**C は実装改善の上限ではない。**

P:289 の訂正を支持する。除外で build 担当・競合・queue が変わるため、C の wall に無条件な上下界の意味はない。

次の律速候補は `draft_finalize`。95 session 資料では中央値266.8秒で、ccbench-current の273.3秒に近い。ただし中央値の順位は各走の次点を確定しない。T:1735–1738 は `distinct_basis_blob=True`、ccbench-current は既定 False なので、**共有機構は同じでも base key は別**。C で default key の待ちが減っても draft_finalize の build は残る。

## 親 brief の一般化の監査

| 主張・根拠 | 判定／成果物への影響／是正 |
|---|---|
| 「91/92 が ccbench-current、例外は g7」Bf:31 | 頻度は旧窓の値。指定93件では92/93、例外は historical-oracle（一覧:68・104）。plan:367 は訂正済み。g7を代替律速とする推論を残さない。 |
| 「関連 file 不変→test 内容同一」Bf:32 | 条件付き。T:794–824 は untracked output も入力にする。docs・ccbench checkout 等も固定されなければ同条件ではない。歴史分布を同一入力反復と呼ばない。 |
| 「固定費67秒」Bf:7・31 | 当該窓の残差中央値として妥当。定数ではなく65.0〜103.3秒。成分表には各走の値を用いる。 |
| 「相方20秒、上限5.8%」Bf:19・40 | 特定分布・固定 duration 下の目安。T-2750:17 は20走中17走が約20秒、3走は7.5〜8.7秒。全走の改善上限にしない。 |
| 「verify 5回 vs 他3 param各2回」Bf:34 | **誤り。5/2/2/1回**。unknownness は T:1899 の分岐に入らない。plan:367 の訂正を採用する。 |
| 「台帳差が小さい→base/copy主体の可能性」Bf:34 | 仮説としてのみ可。台帳は実成分測定ではなく、verify 回数・検査経路も異なる。成分実測前に本体優劣を決めない。 |

## nit と所要・費用

**N1．env 名・既存行番号の訂正を成果物へ統一する。**

根拠は P:39・367、AS の `PLUGIN_SPEC_ENV`。plan は既に `IZANAGI_ACCEPTANCE_SHARD_PLUGIN_V1` へ訂正済み。これに従う限り測定結果への追加影響はないため nit。親資料の旧表記を実装へ転記しない。

**所要計算は算術上正しい。** P:168–177・374 の実行見積は `30〜54＋3×(21〜27)=93〜135分`、予約は270分。A/B/C を歴史最大677.1秒で各3走としても約33.9分なので、60分予約には約26分の余裕がある。ただし B/C と S の最大値を保証する数字ではない。

queue 待ちは未見積であり、4 job 分の待ちと dispatch・回収を別枠にする必要がある。費用対効果表には「実行93〜135分＋queue等」、land 受入1 session別、と書く。queue timeout/grace の未確定値を確定所要に含めない。

C′ を追加しない判断は妥当。各条件3走は削らない。S1 を削れば単独 builder の成分が、S を削ればM内共有・待ちが失われるため、現在の分解目的では安易な削除を勧めない。B が実 collection の cardinality 制約から実現不能なら、同じ失敗条件の本走3回を払う必要はなく、「指定 B は実現不能」と報告して後続設計へ返す。

## 総括

- **must-fix：3件。** B/C の hook 位置、model と実測 baseline の不整合、観測 overhead の評価不足。
- **D357：実受入形も要る。** 「受入 shard-0 の値・改善」と主張する場合の判定。replica 内の反復実測に限定するなら replica×3で最低反復要件を満たし、追加の実受入3走は必須ではない。歴史93件と land 1走では代替できない。
- **B の設計：現 plan のままでは不整合。** `collection_finish(trylast=True)` を送信前へ修正し、cardinality sort・pending item 数・後続再配布を含めれば条件付きで整合する。49〜96位の軽量化だけでは wall 改善を保証しない。