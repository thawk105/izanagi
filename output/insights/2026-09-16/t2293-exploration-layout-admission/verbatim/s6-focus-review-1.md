## 所見ごとの対応表 (closed / partial / regressed / n/a)

**review B の must-fix は closed** と判定します。以下は静的レビューです。親が報告した実走結果と、こちらで独立に確認した結果は区別しています。

参照略号：

- A＝[review-A.md](/home/SFC/tanab/.claude/jobs/955ee86e/tmp/wave/review-A.md)、B＝[review-B.md](/home/SFC/tanab/.claude/jobs/955ee86e/tmp/wave/review-B.md)
- U＝[test_reflux_result_evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-exploration-layout-admission/orchestrator/tests/test_reflux_result_evidence.py)、E＝[reflux_result_evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-exploration-layout-admission/orchestrator/campaign/reflux_result_evidence.py)
- PA＝[patch-author1.diff](/home/SFC/tanab/.claude/jobs/955ee86e/tmp/wave/patch-author1.diff)、PF＝[patch-fix1.diff](/home/SFC/tanab/.claude/jobs/955ee86e/tmp/wave/patch-fix1.diff)
- P＝[plan-v2.md](/home/SFC/tanab/.claude/jobs/955ee86e/tmp/wave/plan-v2.md)、S＝[mutation-spec.v2.json](/home/SFC/tanab/.claude/jobs/955ee86e/tmp/wave/mutation-spec.v2.json)、F＝[fix-1.md](/home/SFC/tanab/.claude/jobs/955ee86e/tmp/wave/fix-1.md)

表中の `n/a` は「refuted・unverified で対応不要」を表します。未検証事項が検証済みになったという意味ではありません。

| 出所・所見 | 元の分類 | 対応 | 根拠・判断 |
|---|---|---|---|
| A:3 仕様外の型の受理 | refuted | n/a | 両 gate は exact identity 判定を維持。E:447、E:1219 |
| A:21 別層の拒否による負例の恒真化 | refuted | n/a | projection 負例は内側へ直接到達。正例同居は解消。U:1202、E:539 |
| A:43 既存防壁の迂回・弱体化 | refuted | n/a | fix は test helper と新設正例のみ。PF:3、PF:15 |
| A:53 既存期待値・fixture の弱体化 | refuted | n/a | 負例の digest・例外・match を維持し、正例を分離。U:1203、U:1209、U:1221 |
| A:59 統合検証範囲・compiler skip の留意事項 | real・修正不要 | closed | 差替えの範囲と非 skip 条件は既知の制約。親から非 skip 完走の報告あり。PA:357、PA:362、P:18 |
| A:67 裁定・Q2〜Q4・所有外への越境 | refuted | n/a | 提示 production 差分は import・両 gate・注釈のみ。PA:3、PA:12、PA:28、PA:38 |
| A:75 静的変更内容・nodeid・件数の食い違い | refuted | n/a | 当時の集計に加え、fix の新規2 node は明示済み。F:8、U:1220 |
| A:79 実走履歴と射影外への波及 | unverified | n/a | 過去の直接実行・所有外調査は独立確認対象外のまま。A:81 |
| B:5 mkdir・import 不足 | refuted | n/a | import と directory 作成を維持。U:7、U:19、U:1134、U:1311 |
| B:6 namespace・process pin 不成立 | refuted | n/a | 明示 output_root と実 `ensure()` を維持。U:318、U:1313 |
| B:7 親 runner の実効 tmp 配置 | unverified | n/a | 親の baseline 成功報告はあるが、resolved path 自体は未確認。P:17 |
| B:8 snapshot 対象・digest 不一致 | refuted | n/a | 両 root の snapshot と無加工 prefix の SHA-256 を維持。U:1204、U:1321、E:1484 |
| B:14 属性不足等による型負例の恒真化 | refuted | n/a | subclass・duck・impostor は実 WAL を参照する構造を維持。U:1144、U:1151、U:1174 |
| B:15 impostor の比較契約不足 | refuted | n/a | `__eq__`・`__hash__`・identity／tuple 所属 assert を維持。U:1165 |
| B:16 単一理由性の適用範囲 | real／nit・修正不要 | closed | 外側だけの緩和を登録せず、属性不足の値を受理拡大観測点に含めない設計を維持。P:55、P:56、P:62 |
| B:20 anchor・nodeid の整合 | 不整合なし | n/a | 全6変異の anchor は現物で各1回。unit の関数名・id も一致。E:447、E:1219、S:11、S:66 |
| B:22 M3 期待集合不足・負例への正例同居 | real／must-fix | **closed** | helper から正例呼出しを除去し、独立正例へ分離。U:1202、U:1221、P:70 |
| B:41 M1 集合 | refuted | n/a | subclass 2件で一致。U:1251、S:11 |
| B:42 M2 集合 | refuted | n/a | subclass・duck・impostor 計6件で一致。U:1251、U:1267、U:1299、S:28 |
| B:43 M5 集合 | refuted | n/a | impostor 2件で一致。U:1165、U:1299、S:49 |
| B:44 M3 集合 | real・同一 must-fix | closed | 独立正例追加を含む3件へ理由付き改訂。P:70、S:66 |
| B:45 M4 集合 | refuted | n/a | 探索発行・統合正例・root 外負例の3件を維持。U:1325、E:1219、S:84 |
| B:46 M6 集合 | refuted | n/a | identity 比較の順序交換で等価、空集合。E:447、S:102 |
| B:52 統合対象経路の stub 化 | refuted | n/a | 統合差分は探索指定で既存 driver を呼ぶ。fix の変更なし。PA:377、PA:388 |
| B:53 root 束縛・record path 不一致 | refuted | n/a | 共通 root、導出 record、探索 content／WAL の検査を維持。PA:367、PA:399、PA:424 |
| B:54 compiler 不在なら skip | real／nit | closed | 親から対象 node の非 skip 完走報告あり。skip 条件自体は維持。PA:357、P:18 |
| B:55 実際の統合完走 | unverified | n/a | 親の成功報告を受領。本レビューでの実走・ログ検証は未実施。B:55 |
| B:59 helper 署名変更による既存 caller 破壊 | refuted | n/a | official 既定値を維持。fix は署名を変更しない。U:314、PF:3、PF:15 |
| B:80 既存正例の nodeid 変更 | real／nit・修正不要 | closed | author 段の仕様どおりの parameterize。fix による再変更なし。P:44、U:1339 |
| B:84 author の nodeid・件数 | refuted | n/a | author 時点の集計と fix の追加2件を区別できる。B:84、F:12 |
| B:85 直接呼出し等の実走主張 | unverified | n/a | fix 報告も直接実行と pytest 未実走を区別。F:19 |
| B:86 登録集合外の赤化の報告漏れ | real・同一 must-fix | closed | 原因・分離・新期待集合を記録済み。全変異の実測確認は別途未確認。P:70、F:22 |

**must-fix の成果物影響：** 修正前は M3 の負例2 node が補助正例の過剰拒否で赤化し、登録集合と変異レポートが不一致になっていました。fix 後はその混入がなく、独立した探索 projection 正例を含む3件へ期待集合が整合しています（U:1202、U:1221、S:66）。

## fix の副作用

**既存 test の期待値・parametrize id・関数名・match 文字列の変更はありません。** fix の逆適用をメモリ上で照合し、既存関数の AST 差分は `_assert_layout_projection_rejected` だけ、新設関数は `test_ordered_wal_projection_accepts_exact_layouts` だけでした。author patch の unit／production 各 hunk の適用後内容とも一致しました（PF:3、PF:15、PA:111）。

新設正例は成立しています。

| 点検 | 判断・根拠 |
|---|---|
| exact layout | official は `CampaignLayout(...).ensure()`、exploration は factory の `ensure()` に加え exact 型を assert。U:314、U:1226 |
| `source_ref` digest | WAL の先頭から最終 frame の `byte_end` までの無加工 bytes を SHA-256 化。production の snapshot・digest 規則と一致。U:1227、E:473、E:503、E:1484 |
| `json.loads` の対象 | `produce_ordered_wal_projection` が実際に返した `projection` bytes。U:1233、U:1237 |
| assert | 非空 bytes、JSON dict、attempt ID、`ordered-wal-projection/v1` を確認。production の出力と一致。U:1236、E:551 |
| 正例分離の効果 | 負例 helper は digest 構築後、拒否対象だけを `pytest.raises` 内で呼ぶ。U:1202 |

`source_ref.path` は fixture の WAL path です。この正例は projection API の型受理と返却 bytes を検査する範囲では妥当です。immutable snapshot の発行・resolve は既存発行正例が検査します（U:1230、E:542、U:1358、U:1377）。

## 変異 spec v2 の期待集合の再導出

以下の略記は node の集合展開です。

- `S[k]`＝`U::test_ordered_wal_projection_refuses_layout_subclasses[k]`
- `D[k]`＝`U::test_ordered_wal_projection_refuses_duck_layout[k]`
- `I[k]`＝`U::test_ordered_wal_projection_refuses_type_equality_impostor[k]`
- `P[k]`＝`U::test_ordered_wal_projection_accepts_exact_layouts[k]`
- `C[k]`＝`U::test_campaign_producer_issues_real_wal_projection_and_resolves_interval[k]`
- `R`＝`U::test_campaign_producer_refuses_exploration_root_outside_evidence_root_before_writes`
- `T`＝`orchestrator/tests/test_reflux_campaign_issuer.py::test_real_run_campaign_exploration_issues_rejected_record`

| 変異 | 静的に導出した赤 node 集合 | spec v2 との比較・根拠 |
|---|---|---|
| M1 | `{S[official], S[exploration]}` | **2件、一致。** `isinstance` が subclass を通す。U:1144、U:1251、S:11 |
| M2 | `{S[official], S[exploration], D[frozen], D[namespace], I[official], I[exploration]}` | **6件、一致。** 6入力は実 WAL の `wal_file` を持つ。U:1144、U:1151、U:1174、S:28 |
| M3 | `{C[exploration], P[exploration], T}` | **3件、一致。** exact 探索型の正例だけが旧内側 gate で拒否される。U:1233、U:1358、E:1296、PA:377、S:66 |
| M4 | `{C[exploration], R, T}` | **3件、一致。** `R` は root 包含エラーより前に型エラーとなり match 不一致。直接 projection 正例は外側 gate を通らない。E:1219、E:1289、U:1325、S:84 |
| M5 | `{I[official], I[exploration]}` | **2件、一致。** tuple 所属の等価比較が impostor を通す。U:1168、U:1180、U:1299、S:49 |
| M6 | `∅` | **0件、一致。** 副作用のない identity 比較の順序交換。E:447、S:102 |

M3 の赤集合は指定された次の **ちょうど3件**です。

```text
orchestrator/tests/test_reflux_result_evidence.py::test_campaign_producer_issues_real_wal_projection_and_resolves_interval[exploration]
orchestrator/tests/test_reflux_result_evidence.py::test_ordered_wal_projection_accepts_exact_layouts[exploration]
orchestrator/tests/test_reflux_campaign_issuer.py::test_real_run_campaign_exploration_issues_rejected_record
```

`test_ordered_wal_projection_refuses_*[exploration]` に該当する subclass／impostor の2件は、M3 でも期待する型エラーが `pytest.raises` 内で発生するため、**静的には緑を維持する予測**です。helper 内に exact 探索 layout の projection 呼出しは残っていません（U:1209、U:1256、U:1304）。root 外負例も包含検査が内側 gate より先なので M3 の赤集合には入りません（E:1289、E:1296）。

統合 node の判定は、提示された author patch とレビュー資料、および baseline 非 skip 成立を前提とします。統合 test の現物は今回の射影に含まれないため、現物との独立照合はしていません（PA:353、PA:377、B:52）。

## 残る所見

**新たな所見：なし。** fix による既存 test の退行、digest 不整合、M1〜M6 の期待集合の過不足は見つかりませんでした（PF:3、U:1202、U:1221、S:11）。

fix 後の pytest と全変異の実測結果は、本レビューでは未検証です。fix 子の直接実行報告を pytest 成功とは扱っていません（F:19）。

## 総括

**must-fix は closed。新規 blocker・must-fix・nit はありません。**

M1〜M6 の静的な赤 node 集合は spec v2 と一致します。M3 は探索正例3件だけが赤になる予測で、探索 projection 負例への正例混入は解消しています。ファイル変更・テスト実行は行っていません。