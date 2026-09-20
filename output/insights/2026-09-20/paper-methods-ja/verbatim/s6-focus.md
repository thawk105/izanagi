## 対応表

照合基準は HEAD `482f19b88dbbe255fc2bb0dcc95b14c1681c1a83`。gitlink と submodule HEAD はともに `e9e477ca1b55348ab4530de0b1cf663ce4555290`。指定射影ファイルはすべて読めた。

以下、M は [methods.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/output/insights/2026-09-20/paper-methods-ja/methods.md)、I は [implementation.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/output/insights/2026-09-20/paper-methods-ja/implementation.md) を指す。

| 番号 | 判定 | 根拠（対応文・一次資料） | 残るなら対案 |
|---|---|---|---|
| 1 | **closed** | M §2 は「内蔵の適応 backoff (`BACK_OFF=1`、`BACKOFF_FIXED=-1`)」。D2183、T-2795 README §0・§2、`p3_s4_loop.py::_run_stock_control_resolved` の genome と一致。実装済み・投入ゼロの区別も維持。 | — |
| 2 | **closed** | M §4、I の A-2/A-6 行は admission record と参照先の元 record を区別。列挙した4 field は `_CONDITION_ADMISSION_KEYS` に存在する。全6 field はこれらと `admission_id`、`admission_digest`。保存 JSONL、writer、story §8 限定 (iv) と一致。 | — |
| 3 | **closed** | M §6、I「実走・契約・未了の境界」に3点と正式選択への接続未完を復記。raw producer の `O_EXCL`、material report の `section_7_1_four_classifications_operationalized=False`、launcher の単一 `--arm` を確認。D1936 項9・D2016・D1408 の引用も適切。 | — |
| 4 | **closed** | I の温度述語行は pin 前進を承認済み・実施済みとし、探索・正式な軸採用を未解禁とする。D2150 項1、D2159 項8・9、T-2304 README、現 gitlink と一致。初回対案の「未実施」を後続着地で更新したのは正しい。 | 表記の nit は後述。 |
| 5 | **closed** | I の B-10 grid 行は実行日を 2026-09-05、記録・D1678 裁定日を 2026-09-07 とする。T-1905 README §0、B-10 results 稿 §1・限定17と一致。 | — |
| 6 | **closed** | I の追加機構表の導入は「未掲載だけを未使用の根拠とせず」へ修正。nodes=5 probe も追記。T-2489 README の実走・`collect` 未実施と一致。「A-2 の attempt に数えない」は、この文脈では取得済み認証 attempt に含めない意味として読める。 | — |
| 7 | **closed** | M §5、I の cell certified 行に campaign lock／pipeline constructor による束縛と実 argv の独立記録不在を明記。D1257、story 限定 (ii)、A-2 成果物4 cell の `workload_argv_observation="not-independently-recorded-by-existing-pipeline"` と一致。 | — |
| 8 | **closed（refuted 維持）** | M §4、I の story 未反映段落は g1 発効を維持し、oracle 実走・床の科学的十分性と区別。T-2724 README の批准 loader 成功と launch validation 未達に対応。 | — |
| 9 | **closed（refuted 維持）** | I の verifier 容量行は検証相が変更前 verifier で走ったと明記。M §3 も追加検証と後日の内部表現改修を分ける。検証相・verifier-capacity 両 README と一致。 | — |

## pin 前進の反映の検査

一次資料は [T-2304 README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/output/insights/2026-09-20/t2304-pin-advance/README.md) §0・§1・§4。

| 項目 | 判定 | 根拠 |
|---|---|---|
| 両稿冒頭の基準 SHA | **一致** | 現基準 `482f19b88` と起草時 `fec4a8187` を区別している。実 HEAD と一致。ただし I 内部に旧基準表示が残る（新規所見1）。 |
| M §1 の実施・非解禁 | **一致** | D2150 の承認と T-2304 の実施を記載し、「前進は探索の解禁を含まない」と限定。承認・実施を取り消す記述ではない。 |
| M §2 の identity 層 | **一致** | `build_admission._new_policy()` の pre-image は `repo_stock_pin=CURRENT_PIN` を含む。campaign ID・cache key・builder bytes・受領証 identity の更新と、較正 record・凍結 protocol・比較 policy・歴史 golden の据置きを区別している。 |
| 旧系列の固定 checkout／新 main での再開条件 | **一致** | T-2304 §4 A・B・「止まる作業」に対応。固定 submit-tree の継続と、新 main での再開・再投入を区別する。g1 launch は実走済みとは書かず、I で既存不整合も明記している。 |
| M §3 の X/P 計装と G2 witness | **一致** | 現 pin の `transaction.cc` に G2 witness の環境変数切替が `#if TRACE` 内に存在する。X/P の追加コードは `instr-mocc-lock-coverage.patch` にあり、現 tree にはない。 |
| G2 witness／軽量 witness の区別 | **一致** | T-2774 の `e9-instr-wit` は e9 pin＋X/P＋witness on。軽量版は e9 を親とする hook commit `5b02546f`。`mocc-witlight-arm-run` README の実装・合成 source と矛盾しない。 |
| I の MoCC 2行 | **一致、表記留保あり** | trace-hook 行は正しい。温度述語行の上限欄も `PIN = pin.CURRENT_PIN` の追随を正しく説明する。ただしアンカー欄の「探索用 `PIN` 不変」は曖昧（新規所見1）。 |
| I の fail-closed 経路 | **一致** | `p3_s4_loop.py` は旧 full OID と `assert_pinned_clean(fixed_sub, PIN)` を保持。`resolve_current_floor_protocol()` は現契約候補が複数の場合に HEAD gitlink exact を要求する。T-2304 が記録した新 pin での停止と対応。 |
| 探索・certified 系列・性能比較への昇格 | **一致** | pin 前進をこれらの開始とする文は見つからない。MoCC の観測は非 certifying、根因未同定という限定を維持している。 |

量化・件数の再確認結果：

- 両稿の D 番号は現在 **39種**。初回の37種に **D1257・D1408** が加わった。
- entry は **19種**で維持。
- I の表は主要対応 **19行**、追加機構 **15行**、読み分け **13行**（見出し・区切り行を除く）。brief の「7機構」は機構群の数であり、表の行数ではない。
- M は **6節**を維持。
- 「D37種・entry19種」は実際には README §2・§5 の初回検査記録にある。歴史記録として37は正しく、現稿の件数としては39になる。

## 新規所見

**新規 must-fix は無し。** 次の2件は凍結を妨げない編集上の nit。

1. **real / nit — pin 更新後の基準表示に旧表記が残る。**

   I「正本の優先関係」は現在も「本稿の基準 `fec4a8187`」、追加機構表の見出しも「main `fec4a8187`」。温度述語アンカー欄には「探索用 `PIN` 不変」が残る。一方、冒頭と同じ行の上限欄は新基準・追随を正しく説明している。

   **放置時の影響:** 起草時の基準と再照合後の基準、参照式の不変と評価値の変更を取り違えやすい。

   **対案:** 現基準の表示を `482f19b88` に揃え、「`PIN = pin.CURRENT_PIN` の参照式は不変、指す commit は前進」とする。README §0 の現状主張も同様に揃える。履歴を記す brief は変更不要。

2. **real / nit — wave 記録の現況メタデータに更新漏れがある。**

   README 冒頭の行数は221／142だが、現在は M **237行**／I **162行**。§6 の「witness の環境変数4箇所」は、現 `transaction.cc` の `getenv` 参照としては **3箇所**（有効化1、出力先2）。D37種の記録には修正後の39種が追記されていない。

   **放置時の影響:** 本文の科学的主張には影響しないが、再検算で記録と現物が一致しない。

   **対案:** 行数を更新するか削除し、環境変数参照を3箇所へ訂正する。初回のD37種は保持したまま、「修正後39種、entry19種」と追記する。

## GO / NO-GO

**GO。稿2本の凍結を妨げる must-fix は残っていない。**

所見1〜7は閉じ、8・9の適切な限定も維持されている。上記 nit の修正は推奨するが、認証の意味・比較対象・実装限界・pin 前進の状態を覆す問題ではない。

## 総括

初回の must-fix 4件・should-fix 3件はすべて closed。
pin 前進は承認済み・実施済みとして正しく反映され、探索解禁とは分離されている。
G2 witness と軽量 witness、旧系列の固定 checkout と新 main の停止条件も整合する。
現稿は D39種・entry19種、表19／15／13行、方法節6節。
新規 must-fix はなく、編集上の nit 2件を付して GO。
静的照合のみ実施。書込み・commit・push・pytest・build・測定は行っていない。