# レンズB — 実効性と過剰・削除

静的検査のみ。書込み・テスト・計算投入はしていない。以下、`brief.md`・`plan.md` は指定された親 job の資料、`設計README.md` は `output/insights/2026-09-22/t2849-comparison-harness-design/README.md` を指す。

## B1 — must-fix：P2 は既知の実装課題を理由に、依頼された手法を変更している

**根拠:** `brief.md:35–36`、`plan.md:285–294,477`、`設計README.md:90,104,130,154–156,356`。

親は K2 限定の役割契約を「D2220 裁定時に未見」とするが、設計正本は既にその制限を記載し、**K0 へ適用範囲を広げることを実装単位4に含めている**。新しく分かったのは SHA 束縛の影響範囲であり、契約変更の必要性そのものではない。

P2 を採ると、LLM は初期点全件・投入前拒否・critic 診断を受け取れない。latest baseline 一件は `(v, fitness)` の初期点一覧の代替にならない。「部分実装と記載する」だけでは、単位1〜7の完了や「T-2850 の値を入れれば投入できる」を満たさない。

修正は、単位4を依頼どおり実装する計画に戻し、役割改訂に必要な所有範囲を具体化すること。別Tへ送るなら、親の provisional 判断ではなく、完了条件を変更する明示的な裁定が必要になる。還流を捨てたまま critic の生成・実行費用だけ残す案も避けたい。

なお、`brief.md:35` の「両fileがB-5束に束縛」は過大。束の `files_sha256` は planner と **K2 coder** を含むが、通常の `coder-v4-autonomous.md` は含まない（`b5-effective-bundle.draft.json:222–224`）。

**放置時の影響:** certified の判定規則は同じでも、LLM の提案列・endpoint・役割費用が設計済み構成と変わり、レポートの「D2220の5手法比較」という参照が成立しない。

## B2 — should：P3 の必要性の説明を訂正し、lock と起動接続を分ける

**根拠:** `brief.md:39`、`plan.md:357–384,478`、`orchestrator/campaign/lock.py:24–34`、`orchestrator/campaign/b5_generator_contrast.py:536–538`、`tools/pegasus/p3_s4_loop_pegasus.sh:643–669`。

「job body 分岐が無いと単位7の置き場が無い」は不成立。既存 lock は `IZANAGI_BENCH_LOCK` を読み、既存 `default_runner` は環境を継承する。harness の CLI プロセスで、slot 起動前に既存の job 固有 `TMPDIR/bench.lock` を指定すれば足りる。新 runner・新 lock API は不要。

一方、**既存 job body が作る prebuild 受領証を同じjobの harness へ渡す接続**には最小分岐を残す理由がある。driver 側に lock を移すだけでは、この接続までは代替しない。job body 分岐を丸ごと不要とは判定しない。

削減対象は次のとおり。

- 固定 `[5,10]` とするなら、shell側の `INITIAL_VALUES` 環境入力と分割処理（`plan.md:373–376`）。
- `test_t2849_job_contract.py` での全5 armの重複検査（`:395`）。armの網羅は driver 試験に置き、shellでは引数輸送・排他・rc・環境を検査する。
- lock 設定を driver と shell の両方には置かない。

**放置時の影響:** 最終scoreを変える必然性はないが、不要な設定面が増え、lock の継承漏れでは並列実行時の失敗・費用・欠測が変わる。

## B3 — should：endpoint の tie-break を理由とする再実装は削れる

**根拠:** `plan.md:16,301`、`orchestrator/campaign/b5_generator_contrast.py:441–445`、`設計README.md:183–194`。

初期点の `b=0` が二つあることだけでは、既存 `select_endpoint` を使えない理由にならない。比較順は fitness → v → b であり、初期点は **異なる値の5と10**。両者は v の比較で決着する。同じvの初期点と探索点では初期点が先、探索同士ではb順となり、計画の実slot順と一致する。

現在の固定初期点仕様なら、初期点・探索点をまとめ、全系列の失格値集合を渡して既存 `select_endpoint` を直接呼べる。独自の資格フィルタ・sort関数を削除できる。

一方、random/sweep の namespace、K0継承照合、参照分類の再実装への攻撃は**不成立**。既存コードには実際に固定接頭辞、K2必須、参照を候補と判定する結合がある（同ファイル `:124,137,338–363,486–497`）。

**放置時の影響:** 現仕様では選択値は変わらないが、certified・品質正常・失格値除外の条件を二重実装し、将来の修正で受理集合が分岐する余地を増やす。

## B4 — should：critic 費用の保存先から集約までの参照が未定義

**根拠:** `plan.md:100–101,132–138,340–345`、`設計README.md:239–244`。

proposal/reject の費用は handshake provenance へ渡す一方、critic 費用は「実行後の materials に残し、集約で取り込む」とある。しかし、materials root は独立したCLI入力で、aggregateには cohort root と job costs しかない。台帳から critic materials への参照fieldも固定されていない。

次のproposalに費用を載せるだけでは、最終評価後や系列終了前後のcriticが落ちる。既存headerまたはprovenanceに materials の所在を一つ残し、既存の役割記録を集約する契約を決めればよい。費用専用台帳・registryは不要。

**放置時の影響:** certified 選択は不変だが、レポートのLLM役割回数・wallが欠落し、保存された実行記録と費用表が一致しない。

## B5 — should：変異を単一変更にし、不自然な変異とshell側の重複を削る

**根拠:** `plan.md:433–446`、`brief.md:51`。

次の組は一度に適用せず、独立した変異として扱う必要がある。

| 行 | 分離する変更 |
|---|---|
| 435 | 保全前の削除／保全失敗後の削除 |
| 437 | 初期点のB加算／retryのB加算 |
| 439 | kernel入力をvへ変更／EIへ観測雑音を加算 |
| 442 | anomalyの波及範囲縮小／欠測のfallback化 |
| 444 | machine印の付加／K2 roleの付加 |
| 445 | exit削除／lock削除 |

`plan.md:436` の「保全処理でanomalyを成功へ変更」は削除候補。予定helperは保全成否を返すもので、verdictを書き換えない。存在しない責務を新たに注入する変異より、cleanup条件と例外処理を壊す方が変更箇所に対応する。anomaly不変・bench非実行の通常回帰試験は残す。

**放置時の影響:** 複合変異のkillを個々の防御の証拠と誤認し、予算・欠測・argvのどの誤りを検出できたかが検査記録から判別できない。

### 実行場所と費用

上記変異は、生成器の固定入力、合成WAL、stub runner、stub shell、圧縮失敗の注入で検査できる。**変異自体に計算ノード必須のものは見当たらない。** login self-run可能かは既存 `tools/run_tests.py` の資源判定に従う。

親の実測単価をそのまま使うと：

| 開発検査 | 回数 | node時間 |
|---|---:|---:|
| 受入 | 2 | 0.50 |
| U-A/B/Cの焦点走 | 計3 | 0.18 |
| 修正後の追加焦点走 | 1 | 0.06 |
| loginで成立する変異 | 必要分 | 0 |
| **合計** | | **0.74** |

追加受入1回でも0.99 node時間。これは予定回数による見積りで、親の「≤1.2」を無条件に保証しない。各変異を個別dispatchすれば、20回でさらに約1.2 node時間になる。単価自体を疑う静的根拠はない。

## 保全口：過剰という攻撃は不成立

**根拠:** `plan.md:140–158,172–174,185–190`、`orchestrator/campaign/pipeline.py:2149–2178`。

env一つのopt-in、保全先に反復ごとのinventory、WAL/proof chain不変更は妥当。campaign・variant・build attempt・反復の識別は、全量保全を元の評価へ結び付けるために必要である。

失敗処理の最小形は以下で足りる。

- zstd不在・書込不能・容量不足・圧縮失敗では、未保全原本を削除しない。
- inventory自体が書けない場合も、その例外で元のverdictや検証例外を置き換えない。stderrに失敗と原本pathを残す。
- 部分圧縮を「保全完了」と扱わない。

容量予測gate、全archiveの再展開検査、自動別領域探索、新しいproof記録は不要。原本が `TMPDIR` に残るだけの場合を「永続保全済み」と報告しないことは必要だが、障害時にも保存成功を保証する仕組みまでは依頼されていない。

## 行数評価

`plan.md:466–469` の総量を、静的検査だけで過大とは断定できない。B-5固定結合を外す系列制御、参照分類、GP数値計算には実装量がある。

具体的な削減余地は次の程度。概算であり、上限ではない。

| 単位 | 削減案 |
|---|---|
| U-A | 保全の追加gateを作らない。現計画から大きく削れる根拠なし |
| U-B | endpoint選択を直接再利用。数行〜20行程度 |
| U-C | 固定初期点のshell設定を削除し、arm検査をdriverへ集約。数十行程度 |
| tests | shellでの全arm重複と不自然な保全変異を削除。数十〜100行程度 |

P2の必要機能を落として行数を減らすことは、削減として数えない。

## 総括

- **所見5件：must-fix 1、should 4、nit 0。**
- **P1：条件付きで成立。** 対象4fileのSHAは今回も束と一致した。束`:18`に従い、承認対象landからstatus/effectiveだけを変える発効commitなら整合する。main先端への承認の一般化は不可。旧checkoutに今回の保全口が入るわけでもない。
- **P2：不採用。** K0への契約拡張は設計時点で明記済み。別Tへの移送は依頼された単位4と完了条件の変更になる。
- **P3：必要性の主張は不成立、最小起動分岐は許容。** lockはdriver側でも置ける。job body分岐を残す理由はprebuild受領証との接続であり、単位7そのものではない。
- launcher・schedule・汎用runner・新監査台帳を追加しているという攻撃は、現計画には**不成立**。