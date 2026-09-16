## 所見一覧

静的検査の結論は、**差し込み位置と修正条件は妥当。ただし正例 P の構築手順と brief の説明に訂正が必要**です。ファイル変更・テスト実行・probe 再実行はしていません。

以下、`V` は [s8c_acceptance_receipt.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1789-empty-cell-descriptor-proof/orchestrator/campaign/s8c_acceptance_receipt.py)、`T` は [test_s8c_acceptance_receipt_v2.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1789-empty-cell-descriptor-proof/orchestrator/tests/test_s8c_acceptance_receipt_v2.py) を指します。

| 点検した疑義 | 判定 | 根拠 |
|---|---|---|
| 新判定で既存 node の期待値が変わる | **refuted** | E は既存 mandatory-reasons で先に拒否。その他の対象 fixture は descriptor 証明あり、または v1。V:2018–2076、T:906–928 |
| 正例 P は「C02 保持」だけで構築できる | **real：手順の欠落** | fixture に C02 はなく、upgrade helper も追加しない。T:288、425–536 |
| 新規負例が別 gate で先に落ちる | **refuted** | plan の hash 更新・upgrade 順を守れば no-build leaf と observed terminal が整合。T:492–536、V:1715–1727 |
| すべての変異が単一理由である | **real：順序変異は例外** | E は新旧両条件を満たす。plan 自身も明記している |
| 新 node の duration 台帳登録が必須 | **refuted（読解）** | 未登録 node を許容し、shard は1秒を割り当てる |
| v2〜v5 共通適用は D1757 に直ちに違反する | **refuted** | 今回は再現済みの共通 descriptor 欠落経路。legacy leaf 再導出や campaign 現物要求を追加しない |

## brief の誤り

- **real：全 case が `do_build=False` という記述は誤り。** [brief:15](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1789-empty-cell-descriptor-proof/s1-brief.md:15) は同26行の C4 と矛盾します。C4 は build 経路で既存 gate に拒否されています。実測結果も [run1-result.json:144](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1789-empty-cell-descriptor-proof/probe/run1-result.json:144) にその診断を記録しています。「C4 を除く」と訂正すべきです。

- **real：P3 の「実行を名乗らない」は過大な説明。** T:403–409 は terminal-failure にも observation-start を作り、arm_execution も残します。保証は「完了・観測成功を名乗らない」です。status だけで未実行や過去の証拠削除不在を証明できません。V:1715–1727 が検査するのは terminal status と report hash の対応です。

- **real：P1 の根拠には selected 非空の補足が必要。** 長さ一致だけなら空同士でも成立します。ただし登録 trial は workload singleton に束縛され、launch 入力も非空です（`trial_registry.py:3764,3961–3963`）。したがって、**登録済み production 経路では complete＋cells=[] を出さないという結論は refuted ではなく維持可能**です。driver の完全な式は `p3_autonomous_workload_trial.py:3816–3834`。

- **real：「status を見ない」は不正確。** brief:53 に対し、V:1421–1422 は report と receipt の status 一致を検査しています。欠けているのは **complete と descriptor 証明の対応検査**です。

- **real：subprocess pin の説明は静的呼出し箇所数に限定すべき。** brief:48 の pin は動的実行回数ではありません。`test_ccbench_spawn_sites.py:2664–2671` は呼出し箇所 inventory を比較します。新判定で早期拒否すれば後続 Git 呼出し回数は減り得ます。

- **refuted：P6 producer node が今回の正例を既に verifier まで保証している、という読み。** `test_trial_registry.py:3005–3030` は receipt を発行して parse するだけです。plan が追加する verifier／capability 正例には独立した役割があります。

## 既存 node への影響

実際の評価順は次です。

1. parse、tracked bytes、共通参照・履歴検査。
2. per-trial loop：report/journal hash → descriptor・三者一致 → expected digest → **v5 cross-binding leaf**。
3. mandatory-reasons。
4. **提案された新判定**。
5. cross-binding aggregate。
6. v5 attempt registry。

根拠は V:1976–2076。cross-binding は aggregate だけでなく、leaf が新判定より前にあります。

**期待値変更が必要な既存 node は、確認した参照集合ではありません。**

- `test_partial_receipt_cannot_drop_c02_reason_without_descriptor_proof`：T:918 は cells だけを空にします。C02 不在のため V:2039–2052 が先に発火し、例外型 `AcceptanceReceiptError` と既存全文言を維持します。
- `test_p1_v5_accepts_observed_and_terminal_failure_mix`：partial 化しても cells は残り、proof=True。新条件は不成立です（T:425–434、1275–1289）。
- aggregate／attempt registry の既存負例：元 fixture の cells と descriptor を保持するため、新判定で診断が横取りされません（T:1120–1290、1328–1341）。
- producer receipt を実際に verify する `test_p5_six_complete_terminal_reports_pass_acceptance` と `test_s8c_acceptance_registered_build_reports_reach_receipt_for_h1_h2_workloads`：complete report に descriptor があるため影響なし（`test_trial_registry.py:1652–1783,1823–1909`）。
- `test_s8c_acceptance_receipt.py` と `test_layer3_report.py` の verifier fixture は v1。新条件の対象外です（前者:124–132、後者:637–671）。

参照検索で得た consumer test files は plan:158–162 の4ファイルと一致しました。新 import・subprocess 呼出し・保存形式変更も不要です。

## 変異とテストの実効性

**real：P の C02 追加を明文化する必要があります。** [plan:105](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1789-empty-cell-descriptor-proof/codex/t1789-empty-cell-descriptor-proof/s2-plan.md:105) の「保持」を、N2 と同じ「sorted unique 集合へ追加して保持」に直してください。T:288 の初期値は approval-authority 理由だけです。追加しなければ、P は正常実装でも mandatory-reasons で落ちます。

この補足後は helper を利用できます。T:425–434 が row/report を partial にして hash を更新し、455–473 がその hash の terminal-failure と registry prefix を作ります。先に生成する no-build leaf は status・report hash を含まず、cells 数を含むため、**cells 変更を upgrade 前に行う**順序が適切です（`autonomous_trial_completeness.py:4165–4188`）。

指定6 node 内の赤集合は次のとおりで、plan の静的予測と一致します。

| 変異 | 赤になる全 node | 判定 |
|---|---|---|
| 新判定削除 | N2v2、N2v5、N3 | 別 gate の競合疑義は **refuted** |
| `!= "complete"` | N2v2、N2v5、N3、P | 同上 |
| `== "partial"` | N2v2、N2v5、N3、P | 同上 |
| `== "completed"` | N2v2、N2v5、N3 | 同上 |
| mandatory-reasons より前へ移動 | E | 二重成立は **real**。診断順の検査 |
| v5 限定へ変更 | N2v2 | 別 gate の競合疑義は **refuted** |

N3 の最初の descriptor mismatch と最後の空 cells 拒否は、**異なる入力への別々の呼出し**です。最後の入力では矛盾 descriptor が消え、主張 digest は期待値のままなので、descriptor mismatch／freeze mismatch は競合しません（V:1461–1481、1322–1341）。

順序変異は既存 E が検出するため、新規テストの検出力として数えられません。また、反転2種は指定 status 集合では同じ振る舞いです。変異件数を独立した欠陥数に読み替えない扱いが必要です。

**duration 台帳追加は不要（読解）。** `conftest.py:1532–1538` の件数確認は台帳内部の整合です。未登録 node は同1675–1695で `None` となり、collection から消えません。`tools/acceptance_shards.py:392–404` は1秒を割り当てます。

## scope 判断

**P2・P5 と production 1 file＋test 1 file の所有範囲は妥当です。** 新条件は既に再読した report の status と descriptor proof だけを用い、実測 A2/B2/C2/C3 の受理を狭めます。D949 の恒真な冗長照合には当たりません。

**P4 の共通適用を D1757 違反とする疑義は refuted と判断します。** D1757 の決定対象は legacy cross-binding leaf の現物再導出であり、到達不能性と失われた campaign 現物への追加要求を理由にしています（[逐語:93–125](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1789-empty-cell-descriptor-proof/rulings-verbatim.md:93)）。今回、その再導出範囲も追加資料要求も変更しません。v2 では既に verified の反例が実測され、同じ descriptor 検査経路が v2〜v5 にあります（V:1999–2025）。

ただし、**v3/v4 も実測済みとは書けません**。提供結果の実測世代は v2/v5 です。v3/v4 への効果は共通経路の読解に基づくものです。「版分岐が不要だから」だけではなく、この区別を根拠に残すべきです。

partial の追加制約、未知 status の拒否、capability での C02 一律拒否、台帳追加は不要です。将来 certifying 世代への影響も、現在の実測結果として一般化できません。

## scope 外候補

今回、新たに実測で確定した scope 外欠陥はありません。

legacy parser が任意の非空 status を許すことは静的に確認できます（V:918–919）。ただし、その形の実在・被害は今回再現されていません。plan の scope 外列挙を、新しい検査を追加する根拠にはしない判断が適切です。

## 総括

**plan の実装方針は支持します。必須の補足は、正例 P で C02 を明示的に追加することです。** 既存 node の期待値変更は見つかりません。変異赤集合は指定6 node 内で整合し、順序変異だけは既存診断契約の検査として区別できます。

brief は C4 の例外、partial の意味、status 検査の現状、subprocess pin の射程を訂正してください。成功・赤集合はいずれも静的判断であり、親の実測で確定する必要があります。