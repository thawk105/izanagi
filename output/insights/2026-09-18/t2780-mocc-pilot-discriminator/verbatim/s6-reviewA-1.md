## must-fix

**0件。** 統合差分に、verifier／discriminator の受理条件や既存の失敗停止を弱める変更は見つかりませんでした。静的レビューのみ実施し、pytest・変異・生死確認は実行していません。

以下、`pilot` は `tools/pegasus/mocc_trace_pilot.sh`、`test` は `orchestrator/tests/test_mocc_trace_job_contract.py` を指します。

## should

**S1 — M8 の正式変異では、登録した field assertion による検出と、job-result writer による先行拒否を分ける。**

- **根拠:** pilot:3521–3539 が binding 欠落を拒否するため、test:4838 の正常終了 assertion が先に赤になります。登録対象の field assertion（test:4843–4853）には到達しません。author の「登録理由には絞れない」という申告は現物と一致します。
- **成果物への影響:** 現状でも変異は赤になりますが、その結果を「receipt の field assertion が単独で KILLED」と記録すると、正式変異の検出理由が実際と異なります。
- **是正案:** receipt writer 終了時点の成果物を検査する独立ケースで、binding 欠落を直接検出してください。既存の job-result writer の検査は維持し、正式結果には各検出箇所を区別して記録してください。

## nit

**N1 — hydrate 実呼出の PYTHONPATH は、新テストの観測対象に入っていません。**

- **根拠:** test:1544–1545、1575–1581 は probe の argv・cwd・PYTHONPATH を記録・検査します。一方、hydrate 側は test:1549–1550、1597–1602 の interpreter identity・argv・cwd のみです。fixture の PYTHONPATH 代入（1558–1562）も export されていません。
- **成果物への影響:** 現行の正常成果物や M1〜M3 の検出結果を変える欠陥は確認していません。ただし「hydrate 実呼出の PYTHONPATH まで観測済み」とは記述できません。
- **是正案:** 被覆説明を上記範囲に限定してください。実呼出側の環境継承も契約に含めるなら、export した継承値を hydrate stub で別途記録・検査してください。

**N2 — 「焦点走は login 実走で完了」という説明は、提供ログと一致しません。**

- **根拠:** `focus-1.log:2–15` は bounded local の上限到達後、gen_S の request **5893.nqsv** へ dispatch した記録です。同ログ:57 は **1591 passed, 3 skipped, 3 warnings / 114.92秒**。pilot:1591 や1746以降の実ジョブ完走を示すログではありません。
- **成果物への影響:** コードや receipt は変わりませんが、検証記録の実行場所と保証範囲が誤記になります。
- **是正案:** 「login で開始、メモリ上限到達後に compute へ再送して焦点走完了」と記録してください。ログ自身が明記する「受入全走ではない」も維持してください。

## 正しさ・配線・receipt の確認

| 論点 | 静的確認結果 |
|---|---|
| 規律2 | pilot:2364–2368 の verifier rc∉{0,1} 拒否、3137–3138 の finalization 条件は維持。rc=3 を通す追加分岐はありません。discriminator の結論集合も変更されていません。 |
| verifier source | pilot:2348–2357 は T1943 だけ BUILD_SOURCE に切替。general では引用付き変数へ CCBENCH_BASE をそのまま代入しており、展開後の argv は従来と同一です。`model.py:130–176` は指定 root の実 source を読むため、これは入力配線の修正です。 |
| hydrate probe | pilot:1572–1576 の repo cwd と二つの root は、fetch:22–23、52–64 の driver import 用 root と整合します。ただし既存 sys.path によって fetch の挿入有無は変わるため、全探索順が常に同一という保証ではありません。 |
| rejected の範囲 | pilot:1568–1570 で不在・解決不能・非実行候補は continue し、1581 に到達しません。全候補不在では `rejected: none`。既存 gate と同じ限定です。 |
| hydrate 失敗記録 | pilot:1585–1588 は stderr 書込み後に `write_failure 2 third_party`。stderr は256行で登録され、manifest は665行で先に生成されます。`test_pegasus_tools.py:575,584` の stderr redirect count==1 も維持されています。 |
| hydrate 実行失敗 | pilot:1591 の非0は154–161の既存 ERR trap により stage=`shell`。新テストの被覆外である旨は author 報告に明記されています。 |
| patch touch set | pilot:1764 の `apply --numstat` は適用しません。1770–1774 の awk は一行・三列・数値二列・path 完全一致を要求します。既知の単一ファイル patch に整合します。 |
| patch 適用順 | numstat → touch set → check → apply → patch SHA再照合 → source SHA捕捉の順です（1764–1803）。 |
| patch 失敗捕捉 | realpath・hash・numstat・awk・check・apply の失敗は明示的に stage=`instrumentation_patch` で停止します。hash pipeline は pipefail で上流失敗も捕捉します。ただし1760–1762、1803の単独 artifact 書込み失敗は ERR trap に進みます。「block 内の全失敗が専用 stage」とは言えません。これは plan の限定と一致します。 |
| general の空値 | pilot:1742–1744 の初期化は marker 外ですが production では必ず実行されます。2638で三引数を全 mode に渡し、3267–3268で general の非空値を拒否します。 |
| receipt 再照合 | pilot:3113–3136 は patch／source 実 bytes、二つの sidecar、numstat を確認してから binding を構成します。3240–3246 の5 field は裁定§2項1と exact 一致し、test 識別子は含みません。 |
| job-result | pilot:3512–3539 は v4／T1943 v2 のみ受理し、v2 の5 field・型・値を検査します。指定の `grep -c "t1943-g2-v1"` は production pilot に対して **0件**でした。 |
| artifact | pilot:413–437 は3 evidence・2 diagnosticを登録し、後者の reason は normally empty。3416–3428の receipt 登録も T1943 限定。651–655の general 漏れ検査も追加済みです。 |

source digest は適用後と finalization 時点の一致を束縛します。コンパイル時の読取り bytes を独立に証明するものではない、という author の限定も正確です。

## テストと変異申告の照合

M1〜M8 の申告行は、すべて統合後の assertion 行と一致します。ただし、以下は**静的照合であり変異の再実走結果ではありません**。

| 変異 | 現物の最初の該当 assertion | 評価 |
|---|---|---|
| M1 | test:1594、正常終了 | fallback の旧 python3 が hydrate で3を返す構造と一致。identity assertion より先に赤になります。 |
| M2 | test:1578、version 条件文字列 | 一致。文字列を残した恒真化までは保証しません。 |
| M3 | test:1590、rejected 記録 | 一致。四候補を実在させるケースです。 |
| M4 | test:1677、postimage | 一致。digest だけでなく実 source bytes を確認します。 |
| M5 | test:1689、拒否rc | 一致。二ファイルの numstat で適用前停止を要求します。 |
| M6 | test:1672、git 呼出ゼロ | 一致。source 不変・五 artifact 不在も続けて検査します。 |
| M7 | test:1733、source argv | 一致。両 mode を検査します。 |
| M8 | test:4838、正常終了 | 一致。ただし先行する job-result writer の拒否による赤です。S1参照。 |

追加確認：

- hydrate の marker 一意性・順序は test:1522–1525、patch は1608–1614、verifier 抽出は1709–1714で確認しています。
- 既存 marker 列挙二本にも新二組が追加されています（2960–2963、4455–4458）。現物を数え、新 marker 四本と CHECKER_PY／VERIFIER_PY はそれぞれ **1件**でした。
- fake interpreter／git に合わせた production の受理条件緩和はありません。fake git の argv・呼出順は1679–1684で照合され、digest は実 bytes から計算されます。
- finalization fixture も3590–3598で patch／source の実 bytes から digest を計算しており、固定 hash の焼き込みではありません。
- v1 拒否テストは4936–4949で receipt・sidecarを再束縛し、schema 拒否メッセージと job-result 不在を確認します。helper は3361–3362で shell 側 digest も再計算します。
- 既存 test の削除・改名・skip／xfail 追加はありません。ただし「既存期待値の変更は二点だけ」は文字どおりには成立しません。hydrate の interpreter pin変更（`test_pegasus_tools.py:560`）もあります。その他は fixture 補完、marker・分類・binding assertion の追加であり、弱体化は確認していません。helper の既定 v3 と general v4 正例は維持されています。

## author 報告と実走証拠

変更点表は統合差分と一致し、三ファイルの SHA-256 も author 記載値と全て一致しました。波及節のうち、general v4維持、production v1置換、判定規則不変、stub の保証範囲は現物と整合します。所有外 consumer／hooks の最新現物まで独立に再監査したという意味ではありません。

author の **149＋72＝221 passed** は報告内で整合しますが、その二走の原ログは今回の入力にありません。`focus-1.log` は別の1591 passedの走行であり、author の221件・所要時間を直接裏付ける証拠にはなりません。また同ログだけでは対象14ファイルの一覧も確認できません。

## 総括

**GO — must-fix 0件、規律2への抵触なし。**

静的レビューとして統合実装を支持します。M8 の正式変異では検出理由を分離してください。正式変異 harness・受入全走・pilot の計算ノード生死確認の完了は、この判定には含めていません。