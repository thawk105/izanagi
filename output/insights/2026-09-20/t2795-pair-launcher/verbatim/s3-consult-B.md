## 判定と読解範囲

**must-fix は 1 件です。** stock 入口・較正 CLI・既存 verify 接続という構成は実装可能です。ただし既存 shell 構造検査の変更漏れがあり、現 plan のままでは正常な実装もテストに拒否されます。

指定資料はすべて読めました。以下は静的評価であり、pytest・build・実測・ファイル書込みは行っていません。新テストの kill は予測であり、実証済みとは扱いません。

略記は plan と同じく、L＝driver、J＝job body、C＝loop、TJ＝job contract test、TL＝driver test、TV＝verify retention test とします。

## must-fix

**M1 — 既存 TJ の変更対象が不足している。**

- **根拠:** TJ:496–503 は shell ソース内の driver 呼出しを `len(driver_positions) != 2` で拒否します。stock を加えると静的な呼出し箇所は 3 個です。また TJ:915–935 は fixture コマンド全体の連続文字列を使います。plan:134 の measurement 配列挿入によって、その文字列は一致しなくなります。
- **成果物への影響:** 正しい pair 実装でも static contract が赤になり、fixture の順序変異は本来の順序違反ではなく fragment 不在で止まります。
- **是正:** TJ:499 の期待数を 3 に更新し、全呼出しが依存 prefix export・prebuild より後である条件は維持する。measurement 配線を残す場合は TJ:917–923 の fragment も更新する。plan の「helper 履歴化・stage-order・TL:8057 だけ」という変更一覧へ、この 2 箇所を追加してください。

これは実行回数の既定を 3 にする変更ではありません。**ソース上は proposal・fixture・stock の 3 箇所、既定実行は 1 回、pair 実行は 2 回**です。

## should

**S1 — stock の terminal 復元は削り、skip を非成功として報告する。**

- **根拠:** D2172 項 3 は fresh layout を前提としています。C:695–706 は terminal を skip します。plan:78–86 は今回不要な既存 certified 復元と rc=0 を追加しています。
- **成果物への影響:** 新しい stock 評価がない呼出しも stock CLI の成功集合へ入ります。候補側 duplicate 処理にも変更が波及します。
- **是正:** stock は terminal skip 時に `outcome=skipped`、rc=1、確定済み ID があればそれを報告するだけにする。ID 不明時は捏造しない。既存 `_resolve_duplicate` は変更せず、二層分離・復元専用テスト・変異 7 の新規追加を削る。候補側の既存 duplicate テストは保持する。

**S2 — 変異 6 の kill を driver identity テストへ帰属させない。**

- **根拠:** plan の変異 6 は「shell が stock へ manifest を渡さない」変更です。一方、`test_stock_and_candidate_share_manifest_campaign_identity` は両 main に直接入力する計画です。
- **成果物への影響:** shell が manifest を落として別 campaign を作る実装でも、driver 単体の identity テストは緑になり得ます。
- **是正:** kill の主担当は実 shell を通る `test_pair_job_runs_candidate_then_stock` とし、stock argv に同じ manifest があることを直接比較する。driver identity テストは、入力された manifest が cfg/layout に反映される別の契約として残す。

**S3 — shell helper は履歴だけでなく、失敗結果の観測まで変更する必要がある。**

- **根拠:** TJ:1230–1237 は最後の呼出しを上書きし、TJ:1315 は rc=0 を固定要求します。TJ:1284–1292 は新 env を除去しません。
- **成果物への影響:** 予定する非零 rc ケースを観測できず、env 不在テストも実行元の環境に左右されます。
- **是正:** 呼出し履歴・プロセス rc・`compute-result.json` の内容を返せるようにし、新 env を既定環境から除去する。既存成功ケースの期待値は維持する。履歴化自体は過剰ではありません。

**S4 — anomaly 即停止テストは bench 到達可能な設定で検査する。**

- **根拠:** TV:35–44 の既存 helper は `do_bench=False` です。plan はこれを拡張して「後続 rep・bench・COMMIT はなし」を検査するとしています。
- **成果物への影響:** `do_bench=False` のままでは、anomaly 後に bench へ進む回帰を「bench 未実行」で検出できません。
- **是正:** 新ケースでは bench を有効にし、その外部実行境界を呼出し禁止にする。legacy は実 verifier で pass、performance の最初の trace は実 verifier で reject とし、後続 repetition と COMMIT の不在を検査する。停止判断自体を stub に置換しない。

**S5 — README は追記だけでは既存説明と矛盾する。**

- **根拠:** `tools/pegasus/README.md:368–371` は manifest・classification・de-novo を「proposal 分岐だけへ渡す」と説明しています。
- **成果物への影響:** pair 起動後の実際の identity 転送と運用文書が食い違います。
- **是正:** 「coder-role は proposal のみ、manifest と宣言値は pair 有効時に stock にも渡す」へ既存文を置換する。併せて stock env の値域、候補優先 rc、fresh layout、stock 後 digest、別 worktree の意味を明記する。既存 qsub fence は TJ:1740–1764 が **1 個**と固定しているため、第二の投入例を追加せず既存例を更新するか、本文で opt-in の追加を説明する。

## nit・過剰実装の整理

以下は、削除しなければ必ず成果物が壊れるとは言えないため nit とします。

| 対象 | 根拠・影響 | 推奨 |
|---|---|---|
| 較正・verify の 3 env | 原依頼 (2)(3) は CLI と接続の実装。D2172 項 4 (α) は実装を認可しており、env 配線が禁止とは読めない。ただし今の K2 pair に必須ではない | 今回は stock env だけに絞り、較正・verify の job 配線と対応 TJ pin/test は β 用 launcher 設計時へ送る。driver CLI は今回実装 |
| stock 終了時の digest 再生成 | L:3164–3176 の既存成果物。省くと WAL に stock があるのに digest は候補までのまま | **削らず残す。** 新台帳ではなく同 campaign の表示更新。LoopState 非更新とは両立 |
| token/projection の新テスト | plan 自身が compiler inert の証明ではないと認めている | 今回の受入から削除可。残す場合も分類規則の単体確認に限定し、stock 成立の証拠に数えない |
| README「25〜40 行」 | 行数は契約ではない | S5 の置換対象・必須説明を指定し、行数目標を外す |
| 「誤った組合せは事前構築前に拒否」 | plan:132 は workload choices を driver に委ねる。未知 workload は末尾の driver 起動まで判定されない | env 配線を残すなら、事前拒否できる組合せと driver 判定の値域を文章で分ける。追加 gate は不要 |
| 「pipeline production 変更が必要」 | C:153–161、782–792 に既存接続がある | brief の主変更を production 2 file＋test に更新。pipeline を変更すること自体を完了条件にしない |

## 正しいアンカー表

指定された主要な plan アンカーは概ね正確です。**大きなずれは親 brief の `perf` と `run_campaign`**、不足は TJ の固定呼出し数・移動変異です。

| 対象 | 現物の正しいアンカー | 判定・補足 |
|---|---|---|
| L `default_cfg` | 1552–1583 | 一致。search_config 本体は 1560–1564 |
| L manifest identity | 1597–1628、特に 1611–1618 | 一致 |
| L `default_perf` | 1631–1636 | 一致 |
| L `_resolve_duplicate` | 1794–1864 | 一致。whiteboard 更新は 1846、1858 |
| L genome 組立て | 1929–1930 | 一致 |
| L candidate campaign 呼出し | **2012–2021** | brief の 2019–2052 は不正確 |
| L argparse 宣言 | 2797–2854 | 一致。parser 作成は 2796 |
| L `supplied` 構築 | 2855–2864 | 一致 |
| L ingestion 排他 | 2865–2879 | 一致 |
| L manifest/coder-role 条件 | **3013–3023** | `a.run_iteration` が条件に含まれる |
| L `perf = default_perf()` | **3044** | plan は正しい。brief の 3040 は誤り |
| L worktree/cache | 3046–3055 | stock もこの context を使用 |
| L proposal 分岐 | 3058、実評価 3111–3125 | fixture LoopState 作成は 3137 |
| L digest 更新 | 3164–3176 | 一致 |
| C verify 接続 | **153–162**、515、782–792 | 152 は空行 |
| C terminal skip | 589–610、695–706 | plan の引用範囲で要点は読める |
| J K2 env/argv | **54–97** | brief の 53–96 は境界がずれる |
| J EXIT trap | 138–157 | 一致 |
| J proposal/fixture 起動 | 580–593 | 一致 |
| TJ required fragments | 154–427 | 一致。検査・例外生成は 428–448 |
| TJ driver 箇所数固定 | **496–503** | plan の変更一覧から欠落 |
| TJ stage-order | **525–558** | 550–558 はその末尾のみ |
| TJ mutation matrix | 611–780、runner 782–790 | 一致 |
| TJ fixture 移動変異 | **915–935** | measurement 挿入時に更新必須 |
| TJ 実 shell helper | 1153–1324 | 一致 |
| TJ 既存 helper consumer | 1327–1379 | plan の 1380 は空行 |
| TJ K2 proposal-only 検査 | 1382–1390 | 一致 |
| TL resolver 構造検査 | 8057–8063 | 一致 |
| TL prebuild 関連群 | 8375–8985 | 一致。ただし単一テストではない |
| TL 実 loop→evaluate 観測 | 8742–8789 | 一致 |
| TL terminal skip fixture | 8921–8985 | 一致 |
| TL plain harness | **9653–9666** | fixture 注入なしで各関数を直接呼ぶ |
| TV local helper / harness | 35–44 / 239–240 | 後者は pytest へ委譲 |
| plain coverage | 35–41、60–86 | harness の実行可能性全体までは検証しない |

## P5：shell と stock 起動の実装性

`cmd || candidate_rc=$?` は成立します。外部 Python コマンドの非零終了は OR-list 左辺なので `errexit` で shell を終了させず、代入の `$?` はそのコマンドの rc を捕捉します。成功時は右辺が動かないため、**candidate_rc と stock_rc の両方を事前に 0 初期化**する必要があります。plan は candidate の初期化だけを明記しているので、stock も追記してください。

最後に集約 rc で明示的に exit すれば、J:139 の `rc=$?` はその値を受け取り、J:146–147 の `driver_rc` に入ります。通常完了時の関係は次です。

| candidate | stock | job / `driver_rc` |
|---:|---:|---:|
| 0 | 0 | 0 |
| 7 | 0 | 7 |
| 0 | 9 | 9 |
| 7 | 9 | 7 |

trap 内のファイル操作自体が失敗した場合まで、この関係を保証するものではありません。新 env を J:97 後で拒否すると trap 登録前なので、既存 K2 preflight と同じく `compute-result.json` は作られません。

`${IZANAGI_S4_STOCK_CONTROL-0}` は**未設定だけ**を 0 にし、設定済み空値を保持します。したがって空値を不正値として rc=2 にできます。`${VAR:-0}` は空値も 0 にするため、plan の契約に反します。

stock に coder-role を渡さない案も成立します。L:3013–3023 の必須条件には `a.run_iteration` があり、stock と run-iteration の排他を先に検査すれば発火しません。`k2_argv` 自体を流用せず、manifest と任意宣言だけの別配列にする方針は妥当です。

`--isolate-worktree` は残してください。候補と stock は **同じ PIN から作った別の使い捨て worktree**になります。「同条件」は同一ディレクトリではなく、同 allocation・pin・compiler・依存関係・perf・verify 条件です。L:3046–3055 の cache 共有だけで同条件を証明することはできません。source の意味的同等性と STOCK token の実成立は、計画どおり後続実走で確認する必要があります。

## 変異 1〜12 の帰属

「1 理由」は **TJ の static runner が返す missing label が 1 個**という契約です。全テスト集合で失敗が 1 件だけという意味ではありません。

| # | 主担当テスト・単一の kill 理由 | 静的評価 |
|---:|---|---|
| 1 | `test_stock_control_reaches_campaign_under_applied_template`：捕捉 genome の `BACKOFF_FIXED` 不一致 | 新 stock 関数を実行し、run_campaign の引数を観測すれば可能 |
| 2 | 同テスト：`BACK_OFF` 不一致 | 「adaptive stock exact test」という別名は一覧にない。上記へ統一 |
| 3 | `test_stock_control_does_not_touch_loop_state`：禁止された state 更新の呼出し | **実 main＋実 stock 関数**が必要。stock 関数ごと stub にすると内部変異を逃す。checkpoint bytes/不在も検査 |
| 4 | `test_stock_control_cli_rejects_conflicting_modes`：所定の排他拒否が消える | 実 main。後段の別例外を kill に数えない |
| 5 | `test_fixture_value_minus_one_remains_rejected`：既存値域拒否が消える | 実 main＋実値検査。run_campaign 未到達も検査 |
| 6 | **TJ `test_pair_job_runs_candidate_then_stock`**：stock argv の manifest 欠落 | TL identity test 単独では kill 不能。S2 |
| 7 | terminal 復元を残す場合は resolver 構造検査：再 resolve 参照の混入 | 二層化すると両層を検査する必要。S1 採用時は新規変異から削除 |
| 8 | `test_calibrated_cli_binds_effective_perf_before_layout`：実効 perf と cfg の不一致 | 実 main。期待値を捕捉 cfg 自身から作らない |
| 9 | `test_default_cli_preserves_preimage_bytes`：変更前 bytes との差 | 変更前 fixture が固定されていれば有効 |
| 10 | TV の pass 順序／anomaly テスト | 「legacy 除去」と「赤後継続」は**別変異**に分ける。S4 の実 verifier と bench 到達可能性が必要 |
| 11 | TJ `test_default_job_invokes_driver_once`：env 不在なのに履歴が 2 件 | 実 shell が必要。env 不在を helper で保証。driver stub は適切な外部境界 |
| 12 | TJ `test_pair_job_runs_stock_after_candidate_failure`：stock 未起動、または最終 rc 不一致 | 捕捉削除と優先順位破壊を別変異にする。実 shell と実 EXIT trap を通し、JSON の rc も確認 |

TJ の新 pin は、**proposal/fixture それぞれの末尾を含む一意な fragment**にしてください。短い `|| candidate_rc=$?` だけでは 2 箇所に一致します。stock-prebuild・stock-mode・measurement の pin が同じ変更箇所を重複して要求すると、missing label が複数になります。最終の逐語 fragment がまだないため、現段階では TJ:786・790 の成立を認定できません。

stub の適否は層で分かれます。shell テストで driver を模擬するのは rc/argv の検査として妥当です。loop テストで evaluate を観測するのも転送確認として妥当です。ただし、それらを pipeline の正しさ・実 compiler の inert 成立の証明へ格上げしてはいけません。

## 既存期待値・テスト配置・段 5

M1 と S3 のほか、次を明示してください。

- **ingestion:** L:2869 の集合差は新 argparse destination も自動で拒否します。既存エラー文の変更は不要です。TL:9113 以降の評価オプション排他ケースに新 flag を追加するだけでよく、ingestion 分岐より前に新しい組合せ検査を置かないでください。
- **既定 identity:** TL:573–604 は既定 campaign ID を固定しています。`default_cfg()` を変更せず opt-in 時だけ replace するなら、期待値更新は不要です。赤になった場合に golden を更新して済ませる箇所ではありません。
- **CLI 略記:** 現在 `--v` は `--value` の略記ですが、`--verify-performance` 追加後は曖昧になります。L:2855 は略記を明示的に考慮しています。既定 argv/identity 不変と、全略記の受理集合不変は同じではありません。この狭い互換差は plan に明記し、必要なら既存略記の扱いを具体的に決めてください。
- **README fence:** 第二の bash 投入例を追加すると TJ:1746 が赤になります。S5 のとおり既存例を使います。

TL は 9,666 行ですが、行数だけでは焦点走時間を見積もれません。さらに TL:9653–9666 の harness は pytest fixture/parametrize を処理せず直接 `fn()` を呼びます。これは既存の問題で、plain coverage が緑でも直接実行の成功を保証しません。

**今回は既存 TL/TJ/TV へ追加し、pytest 経由の焦点走を明示する案を推奨します。** 新規ファイルが速いとする実測根拠はありません。新規ファイルを切るなら TV 型の pytest 委譲 `__main__` を付け、owned_paths と焦点走対象へ追加する。tests README の allowlist 追加と harness 追加を同時に行ってはいけません。

段 5 は、削減後なら **author 1 本で (1)→(2)→(3)** を推奨します。shell/driver 間の CLI・manifest・rc 契約を同じ作者が一巡で揃えられ、TV は既存接続の回帰確認に留まるためです。ただし概算行数から「一巡で必ず完了」とは判断できません。

分割する場合の所有集合は次のように閉じます。

| 単位 | 所有 path |
|---|---|
| driver | L、TL |
| job body | J、TJ |
| verify 回帰 | TV |
| 親 | `tools/pegasus/README.md` |

分割前に CLI 名・既定値・manifest 転送・skip rc・集約 rc を短い共通契約として確定し、統合後に TJ と TL を合わせて確認する必要があります。path が重ならないことだけでは producer-consumer の整合は保証できません。

## 親 brief の閉包

提供された brief 本文には、**「編集面重複 0 件」「owned_paths 6 file」の具体的な一覧・検査結果はありません**。原依頼にある「現在 3 file とも非占有」を、test や README まで含む非重複確認として一般化できません。

plan の実編集集合は、author が **L・J・TL・TJ・TV の 5 file**、親が README の 1 file です。元の 6 owned_paths が「production 3＋test 3」なら、未変更となる pipeline が含まれ、README は含まれない計算です。

これは提示資料から所有違反を断定する所見ではなく、**nit／未確認事項**です。親は具体的な path 集合で照合し、「author 5、親 README 1、pipeline/loop 変更なし」へ brief を更新してください。新 test file を切るなら、その時点で集合を追加更新する必要があります。

## 総括

**must-fix は 1 件：TJ の driver 呼出し箇所数固定と、measurement 挿入で壊れる fixture 移動変異の更新漏れです。**

削る推奨要素は、stock terminal 復元の二層化・その専用テスト／変異、今回不要な較正・verify の shell env 配線、inert 成立を証明しない token/projection テストの受入項目です。digest 再生成と argv 履歴化は残します。

段 5 は削減後の **author 1 本、(1)→(2)→(3)** を推奨します。実装箇所と既存検査の修正には、上の **「正しいアンカー表」**を使用してください。