## 判定と検査範囲

**NO-GO（現状の草稿の確定に対して）。実測値の訂正や再走は必要ない。** must-fix は、投入前条件の証拠範囲と、草稿で脱落した smoke の受入保留条件の2件。

以下、`J`＝`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run`、`I`＝`J/insight-README-draft.md`、`R`＝`J/probe/t2779_probe.py` とする。必読資料はすべて読取り可能だった。

本走240走と smoke 4走の個別 JSON、保存 raw、manifest を読み、標準ライブラリで独立集計した。runner／親の集計関数は実行していない。ファイル変更、pytest、build、benchmark、verifier／discriminator の再実行はしていない。

## real・must-fix

**M1：B-M4 の「投入直前の確認」を、提示証拠からは確認できない。**

`J/s4-ruling.md:26,59` は、base git dir を含む開始条件と、各 launch 直前の同一 worktree の稼働 dispatch 0件の実測を要求する。しかし `J/check-base-dirs-2.log:1–32` にあるのは HEAD・gitlink・submodule HEAD・pin・hold・dirty で、base git dir、実施時刻、`ps` の結果はない。`J/codex/launch-block.sh:11–21` と `launch-smoke.sh:7–20` にも、その確認は組み込まれていない。

各 result の `bindings.base_dir/base_git_dir` と dispatch log は、**今回の5 request の投入元と相互の非重複**を裏付ける。一方、それ以外の同一投入元 dispatch が当時存在しなかったことは未実測である。`I:175` の「全件 real・採用」と、実施を裏付ける証拠を区別すること。当時の保存記録を提示するか、なければ未確認の事前条件として明記する。現在の `ps` では遡及検証できない。

**成果物影響：** k/m は変わらないが、「B-M4 の開始条件を満たした実験」という受入根拠の被覆が変わる。

**M2：草稿の smoke 合格集合から、blocker／入力拒否時の受入保留が脱落している。**

`J/s4-ruling.md:58` は、on の rc=1 で blocker／入力拒否なら原因を記録して技術的受入を保留し、再試行しないと定める。ところが `I:106–108` は「on arm なら discriminator 正常完了」までで、この保留条件がない。`I:101` 自身が blocker を正常完了に含めるため、草稿だけ読むと blocker でも合格になる。

保留条件を明記し、同じ箇所に空集合一致を合格にしない条件も戻すこと。今回の smoke は4走とも verifier rc=0 なので、実測の合否は変わらない。

**成果物影響：** 放置すると、事前登録より広い smoke 受理集合が再現資料に残る。

## real・should

**S1：`decisive_m` を草稿と親会計に明示する。**

`J/s4-ruling.md:48` は併記を要求するが、`I:122–131` と `J/arm-W/parent-accounting.json` の arm 集計には明示がない。`summary.json` と独立再計算では全 arm **60**。草稿に「各 arm `decisive_m=60`」を足せば足りる。

**成果物影響：** 今回の数値は不変だが、事前登録した分母の区別が成果物から直接読めるようになる。

**S2：親会計の `phenomenon` 欄を、現象名照合の証拠として扱わない。**

`J/codex/accounting.py:87–91` は、runner が縮約した `r["verifier"]` から `anomalies/phenomena` を取得する。そのため `parent-accounting.json` の正例2件は両 field が `null` であり、保存済み verifier の `results[0].anomalies[].phenomenon` を検査していない。今回の独立読取りでは両件とも G2 と確認できた。親会計にも原本からの現象名を残すか、別検査であると明記するとよい。

**成果物影響：** 今回の k・CP・Fisher は不変だが、非 G2 混在を検出したという監査証拠の被覆が明確になる。

**S3：低検出力を「率差を判定できない設計」と断定しない。**

`I:160` の「率差の判定には至らない設計」は強すぎる。`I:95–97` の設計仮定では検出力は約0.105であり、検出不能ではない。「設計仮定下の検出力が低く、今回も率差を検出しなかった」とする。`I:22` の0.105にも off率0.0417の条件を添える。

**成果物影響：** p値は不変だが、設計上の確率と今回の結果を混同した主張を避けられる。

## real・nit

**N1：`I:20` の「4 node 同一 block」を「4 node の4 block、それぞれに4 arm」へ修正する。**

原本の `block_id` は W1〜W4。同一 block 内の対照という意味は `I:92–93` が正確である。

**成果物影響：** 数値は不変だが、実験単位の誤読を防ぐ。

## refuted・実走数、回転、binding

**欠測や分母の取り違えという疑いは refuted。**

`J/arm-W/W{1..4}/result.json` はすべて `planned_runs=60`、`rounds=15`、`status=completed`、`not_started=0`。各60件の `runs` と `runs/` の directory 集合、ordinal 1〜60、個別 `run.json` が一致した。

各 arm の欠測会計は、**計画60＝(a)保存済み60＋(b)開始証拠あり未収載0＋(c)未開始確認済み0＋(d)状態不明0**。benchmark rc=0 が240件、verifier rc=0 が238件、rc=1 が2件。全件で process timeout／error なし、保存 verifier の verdict・集約 counter・integrity と整合した。

| block | request | Elapse秒 | `.done`／child rc | 各 arm 保存数 |
|---|---:|---:|---|---:|
| W1 | 10827 | 1471 | 0／0 | 15 |
| W2 | 10828 | 1468 | 0／0 | 15 |
| W3 | 10835 | 1461 | 0／0 | 15 |
| W4 | 10837 | 1466 | 0／0 | 15 |

根拠は各 `dispatch-W*.log:3,6,9,37–41` と `dispatch-W*.done`。dispatcher終端、runner完了、個別走成功を別々に確認した。

**回転の偏りという疑いも refuted。** 各原本の `runs[].order` から再計算した位置1／2／3／4の頻度は次のとおり。ordinal と round 内の実行順も一致した。

| block | on | off | on-bo1 | off-bo1 |
|---|---|---|---|---|
| W1 | 4/3/4/4 | 4/4/3/4 | 4/4/4/3 | 3/4/4/4 |
| W2 | 3/4/4/4 | 4/3/4/4 | 4/4/3/4 | 4/4/4/3 |
| W3 | 4/4/4/3 | 3/4/4/4 | 4/3/4/4 | 4/4/3/4 |
| W4 | 4/4/3/4 | 4/4/4/3 | 3/4/4/4 | 4/3/4/4 |
| 合計 | 15/15/15/15 | 15/15/15/15 | 15/15/15/15 | 15/15/15/15 |

親会計の `positions` と一致。欠測がないため予定と実現の差はない。

**binding の食い違いという疑いも refuted。**

- runner現物の SHA は `7907a545…`。本走4 log の stdout に wrapper 行はなく、launcher は v5 本体を指定している。
- node1〜4 JSON の raw SHA は順に `ba740887… / f5e80223… / 8db96f21… / ab0e84b2…`。name順・key順の正規化結果は全件 `a4af0e8a…`。
- patch現物の SHA は `[e9e65b78…,0648e2c6…]` と一致。
- 全 block と smoke の arm binding は source file SHA `d22b8e43…`、pin `e9e477ca…`、期待どおりの witness 値、`observational_only=false`。
- arm別 `configure_argv/configure_defines` は bo1 のみ `BACK_OFF=1`。その他の CCBench define は一致。
- policy現物 SHA `66ea7135…`、記録された toolchain digest `b713e6ab…`、`bindings.repo_head=a99425b66…` は全 block と smoke で一致。

**成果物影響：** 上記の疑いによる分母・位置頻度・arm帰属の訂正は不要。compilerや削除済み binary の再実測はしていない。

## refuted・正例と識別表

正例原本は次の2件だけだった。

| 保存済み verifier.json | phenomenon／length | cycle txid | rw reason数 |
|---|---|---|---:|
| `J/arm-W/W1/runs/018-e9-witlight-nowit/verifier.json` | G2／2 | 452883 ↔ 452884 | 2 |
| `J/arm-W/W3/runs/005-e9-witlight-nowit-bo1/verifier.json` | G2／2 | 243580 ↔ 243582 | 3 |

`results[0].anomalies[].edges[].types/reasons` はすべて rw。key と version は `I:136–138` と一致した。非 G2 混在はなく、G2件数による統計訂正は不要。

各 `trace-manifest.json.files` と現物の集合・サイズ・SHAを全件照合した。W1は48ファイル・261,786,377 byte、W3は48ファイル・341,192,067 byte。計602,978,444 byteで草稿と一致。manifest の root・binary SHA・pin・workload も対応する verifier／result と一致した。

両走の `discriminator.json` は `status="not-run"`、`reason="witness-off"`。`rc/conclusion/blockers/comparisons` は field 自体がなく、実行結果が空だったという意味ではない。

on arm の G2 は0件で、呼出成功・正常完了・識別成功、supported／contradicted／blocker／input-rejected はすべて0件。comparisons表の対象も0件で、`I:140` と一致する。識別率を0%とはせず、対象なしとするのが正しい。

`orchestrator/campaign/mocc_g2_discriminator.py:600–624` では blocker が比較に優先し、S の不一致は同 file:375–376 の `witness-post-store-token-mismatch`。草稿はこれを contradicted に読み替えていない。

**成果物影響：** 現象名・識別到達件数の訂正は不要。「onで正例がないため実験全体が失敗」という疑いも refuted。ただし問い(ii)は未到達のまま。

## smoke、投入元、保全の検証

smoke原本は `planned_runs=4`、`rounds=1`、`status=completed`。4走とも benchmark／verifier rc=0、cycle=0。4 arm の build後 binding・binary SHA があり、実行成功と、R:472–478,568–578 の成功時だけ後続へ進む経路が整合する。

`J/arm-W/smoke-evidence/capture-manifest.json` の4 run・288ファイルについて、保存集合・サイズ・SHAを全件照合した。wrapper SHA `65017778…` も記録と一致する。

on 2走の raw を独立に読み、次を確認した。

| smoke run | C件数 | S＝W＝C write数合計 | L＝R＝C read数合計 |
|---|---:|---:|---:|
| 001-on | 613,418 | 3,014,285 | 2,968,147 |
| 003-on-bo1 | 800,450 | 3,933,687 | 3,873,346 |

両走とも witness 48ファイルすべてで先頭Hが正確に1行。S/WとL/Rのidentity・多重度が一致し、Sの保存producer値は全件writer txidと一致した。空集合による合格ではない。`check-smoke-witness-001.log`／`003.log:2–10` と一致する。保存値の異常値 pass-through のruntime注入は未実測で、草稿の限定は適切。

提示された `dispatch-smoke.log:3` の受理requestは **10799の1件**で、再投入の記録はない。`arm-W` 内の result も smoke 1本と本走4本だけだった。ただし launcher は固定logを上書きするため、これを保存範囲外の実行履歴まで否定する証拠とは扱わない。

smokeは22:32:31終了、同じ wave worktree のW1は22:35:18作成。W2〜W4のlogはそれぞれ node2〜4の別 worktree を指す。**記録された5 request間の同一投入元並行dispatchはない。** 他のdispatchの不存在はM1のとおり未実測。

本走の非cycle正238走では trace／witness directory は残っていない。これは R:359–363 の削除条件と一致する。今回の本走G2は全件offなので、保全されたG2 witnessは0件。smokeのrawは別途保全されている。「全 witness 保全」という主張は草稿にはなく、その疑いは refuted。

**成果物影響：** 保存済みsmokeの技術的合否やraw保全量は訂正不要。M1・M2の証拠範囲と受理集合の記述は修正が必要。

## 主張上限の照合

`I:15–16,25–27,98–104,154–167` は、率差と識別到達の分離、過去T-2779の5/120との非合算、旧heavyweight on不在による因果推定の制限、規律2／7、`certified=true`／`observational_only=false` の限定を維持している。indeterminateを「G2なし」とする記述もない。

非G2混在時のk・CP・Fisher訂正規則は裁定にあり、今回は全正例の現象名照合により適用不要。草稿§7の実装・identity・provenanceに関するレビューAの結論は、このレビューBでは独立再認定していない。

**成果物影響：** S3を除き、今回の観測結果から認証・根因・同等性・軽量化の因果効果へ主張を拡張した所見はない。

## 総括

**(a) NO-GO：草稿の現状確定に対して。観測値は一致しており、再走・補充を求めない。**

**(b) must-fix**

1. **M1：** 投入直前チェックの当時の証拠を補うか未確認範囲を明記する — B-M4充足という受入根拠の被覆を訂正する。
2. **M2：** smokeのblocker／入力拒否時の受入保留条件を復元する — 事前登録より広い受理集合を残さない。

**(c) should：** S1＝`decisive_m=60` の明記、S2＝親会計の現象名照合証拠の補足、S3＝低検出力を検出不能と表現しない。

**(d) nit：** N1＝「4 node同一block」を4 blockの設計に即して修正する。

**(e) 独立再計算値：**

| arm | k/m | decisive_m | CP両側95% |
|---|---:|---:|---|
| on・BACK_OFF=0 | 0/60 | 60 | [0, 0.0596294922862] |
| off・BACK_OFF=0 | 1/60 | 60 | [0.000421874452342, 0.0893990500575] |
| on・BACK_OFF=1 | 0/60 | 60 | [0, 0.0596294922862] |
| off・BACK_OFF=1 | 1/60 | 60 | [0.000421874452342, 0.0893990500575] |

全armで failure＝indeterminate＝未収載＝0。CPは二項確率の直接和の反転、Fisherは超幾何確率で独立計算した。主比較・副比較とも実表 **`[[0,60],[1,59]]`、片側 Fisher（on < off）p＝0.5**。親会計・runner summary・草稿の値と一致する。
