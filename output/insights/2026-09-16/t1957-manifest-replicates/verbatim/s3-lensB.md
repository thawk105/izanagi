## 所見

以下、R／T／E は plan と同じ略号。他の repo パスもすべて指定 worktree 内です。テスト成否は静的予測であり、実測ではありません。

- **real：親 brief の「単一 test file」では追随不足。** `s1-brief.md:40–42,69`、`s2-plan.md:23` に対し、`orchestrator/tests/test_p3_autonomous_workload_trial.py:7221–7227,10361–10367` と `test_reflux_origin_binding.py:65–75` に、`n` のない独立した manifest fixture がある。
- **real：欠落補完変異は編集位置によって等価変異になる。** `s2-plan.md:109` の補完を取得処理だけに入れると、先行する R:769 → R:659–662 が欠落を拒否し、指定 node は赤くならない。
- **real：bool 変異の注記が本文の検出条件と矛盾する。** `s2-plan.md:111` の「型エラーの期待を外す」をテスト変更として実行すると、`True` は下限検査で拒否されてテストが通る。同 :88 のメッセージ照合を保持する必要がある。
- **refuted：指定アンカーに行ずれがある。** 指定された R／T／E のアンカーは実コードと一致した。
- **refuted：既存 test の削除案がある。** T の既存 test 関数は AST 集計で213個、重複なし。追加予定4関数との名前衝突なし。plan に削除・改名の指示はない。
- **refuted：`n` の短さが JSON 処理と衝突する。** R:527–535、595–615、657–662 にキー長による分岐はない。
- **real・scope 外：登録 `n` と観測反復の一致は完成しない。** R:3600–3612 は初回 slot の反復添字を0に固定する。schema 正例の成功から、`n≥2` の観測受入成功は導けない。

## consumer 取り残し

plan の実アンカー表にない、赤くなる経路は次の3ファイル。

| ファイル | 取り残された経路と理由 |
|---|---|
| `orchestrator/tests/test_p3_autonomous_workload_trial.py` | `t325_registered_trial:7170` の辞書 :7221–7227 → `_t325_prepare_effective_binding:7119` → `load_trial_manifest:7120`。schema 定数は自動で v3 になるが、trial の `n` が欠けて setup が失敗する。別の手書き辞書 :10361–10367 → helper 呼出 :10386 も同じ。**2箇所とも追随が必要。** |
| `orchestrator/tests/test_reflux_origin_binding.py` | `_manifest_value:60` → `case:186` 内の生成 :313 → load :322。`n` 欠落で `case` を使うテストが本来の検証に到達しない。 |
| `orchestrator/tests/test_reflux_originless_compatibility.py` | `_bundle:48`／`_origin_enabled_bundle:133` → `p3_test.t325_registered_trial.__wrapped__` → 上記 helper／loader。直接 schema 定数を書かない、間接 consumer の取り残し。元 fixture を直せば、このファイル自体の編集が必要とは限らない。 |

`test_reflux_origin_binding.py:83–98` の `_registration_value` も `n` を欠く。ただし現コードでは定義以外の参照がなく、これを「現在の赤の原因」とするのは誤り。

production 側も2段追跡した。

- `p3_autonomous_workload_trial.py` の loader 呼出は指定どおり4箇所：`_preflight_workload_profile:988`、`_trial_launch_admission:1530`、`_prepare_s8c_budget_inputs:2148`、`main:5490`。前3者は `run_trial:4696,4776,4806,5012`、前2者は `main:5495,5503` から使われる。表には欠けているが、旧キー集合を再構築する処理ではなく、**これらの呼出自体に必須のコード変更は確認できない**。
- R 内では load → 登録生成、effective binding、launch admission、acceptance に伝播する。直接参照は R:1455,1505,1750,3733,4149,4208,5571,5883,6569,6599。registration は `_load_registry_bytes` の共用 parser に集約される。
- E:1651–1656 は属性の部分集合検査、E:1749–1756 は定数**名**の存在検査。v2 リテラルの pin ではない。`test_s8c_preregistration_predicates.py:653–675` の文字列 fixture も実 loader に渡す manifest ではないため、版上げによる赤とは認定しない。
- `s8c_acceptance_receipt.py:1989–1990` は manifest／registry の digest を検証する。:1620 の loader は **attempt core** のもの。`test_s8c_acceptance_receipt.py:68–72`、`test_s8c_acceptance_receipt_v2.py:178–183` は不透明な fixture bytes を使う。**receipt 専用2ファイルが今回の変更だけで赤になるという疑いは refuted。**

既存 T の `_manifest_value`／`_registration_value` を使う経路は plan の fixture 修正で覆えるが、上記の独立 fixture は覆えない。

## plan の file:line 検算

| 分類 | 検算結果 |
|---|---|
| **実在** | R:55–56 定数、117–119 trial keys、276–281 `TrialSpec` |
| **実在** | R:659–662 exact-key 差分、769 呼出、784–785 generations 拒否直後の挿入位置、793–794 universe 検査直後の挿入位置 |
| **実在** | R:812–817 manifest 版判定／parser、827–834 serializer、844 registration 内 serializer 呼出、864–870 registration 生成、887–917 registration 版判定／parser |
| **実在** | R:1566–1574 canonical tuple、1583–1585 説明、1589–1594 比較／拒否 |
| **実在** | T:170–185 コンストラクタと辞書、221 registration 辞書の generations |
| **実在** | T:1566–1576 既存6 cell 正例。新規 test の挿入アンカーとして成立 |
| **実在** | T:5060–5061 v2 固定の文字列置換、5481–5487 直接コンストラクタ |
| **実在** | T:6765–6783 canonical tuple 変異テスト。6774 replacement 辞書、6782 `raises` |
| **実在** | E:1650–1656 属性の部分集合検査 |
| **ずれ** | 確認したアンカーにはなし |
| **不在** | 新規予定4関数は現在存在しない。plan は未実装として明記しており、アンカー不備ではない |

test 名集合の予定差分は **削除0、追加4、既存1関数のパラメータ追加**。実装後の集合差分は未検証。

新規 test file は不要。独立 fixture の追随も既存ファイル内でできる。新規ファイルを作る場合に限り、自走 harness と所要台帳の追随が別途必要になる。

## 変異の帰属検査

実装予定コードに対する静的検査。実行順は測っていないので「最初に赤になる node」は断定しない。

| 変異 | 判定 |
|---|---|
| 欠落を2で補完 | **遮蔽あり。** 取得だけを `.get("n", 2)` にすると R:769 が先に拒否し、loader 経路では等価。欠落を本当に受理させる変異には、exact-key より前の補完など、具体的な編集指定が必要。 |
| 厳密整数検査を削除 | `2.0` は下限を通り、集合比較でも整数2と等しいため、float node は殺せる。string では `TypeError`、bool では期待メッセージ不一致も起こり、指定 node 専用ではない。 |
| `isinstance(n, int)` | bool は下限に落ちる。**型エラー照合を保持すれば殺せる。外すと殺せない。** 両 source、両 bool に影響する。 |
| `int(n)` 変換 | 変換を型検査より前に置けば string node で殺せる。検査後に置くだけなら遮蔽される。編集位置を固定すべき。 |
| 下限を1へ弱化 | index 0 だけ1なので、後続の holdout 一致検査が拒否する。指定 node は**拒否理由の不一致**で殺す。受理成功を観測する変異ではない。 |
| 下限検査削除 | 0／負値も後続の holdout 一致検査に落ちる。上と同じくメッセージ照合が必要。one や反対側 source も赤くなり得る。 |
| holdout 内一致削除 | arm-split の両 source で殺せる。既存テストの均一な `n` fixture だけでは検出できない。 |
| 全 holdout 同値要求 | H1=2／H2=3 の正例が、P2 より前の manifest load で失敗する。指定 node は妥当。 |
| parser が常に2を格納 | 正例P2で殺せる。holdout 検査が格納済み `TrialSpec` を使う案なので、arm-split 負例も赤くなる。 |
| serializer が省略／固定値化 | **分離すべき。** 省略は新規P3だけでなく、T:1607 の既存登録正例 → :325 `_registered_repo` → :303 `_append_fixture_registration` 経路でも失敗し得る。固定2は既存の均一 fixture では生存し、混在正例P3が必要。 |
| tuple から `n` 除去 | T:6780–6783 は変更後の trial を直接比較するため、holdout validator に遮られず指定 `[n]` node で殺せる。 |
| 片方だけv2 | 新規定数テストで殺せる。registration 側をv2に戻すと、v3へ更新済みの T:5060–5061 の置換が発火せず、既存重複キー負例も赤くなる。 |
| v2互換受理 | `n` を備えた旧版入力なら、版検査を通った後に欠落で遮蔽されない。指定旧版拒否 node は妥当。 |

複数 node が殺すこと自体は不備ではない。ただし、この表を「指定 node だけが赤になる matrix」として扱うことはできない。

## key 名の検査

**`n` で問題ない。別名の根拠はない。**

- R:117–119 の閉じたキー集合へ追加でき、既存キーとの重複もない。
- R:595–615 の重複キー検査は各 JSON object のキー完全一致を見る。同じ object の重複 `"n"` は拒否され、別 cell の `"n"` 同士は衝突しない。
- R:527–535 の canonical JSON は通常の辞書キーとしてソートする。
- R:659–662 の欠落診断は `missing=['n'], unknown=[]` になる。正規表現では角括弧をエスケープする必要があるが、plan :88 が要求している。
- manifest／registration のトップレベルキーと trial 内キーは別の集合であり、名前空間も衝突しない。

## 総括

plan は独立 fixture 2ファイルと、その間接 consumer 1ファイルを取り残している。
親 brief の「単一 test file」で完結する scope は修正が必要。
アンカーの行ずれ、既存 test 削除案、`n` の命名衝突は確認しなかった。
変異は欠落補完の遮蔽、bool 注記、変換位置、serializer の分離を具体化すべき。
ファイル変更・commit・テスト実行はしていない。