## 所見

**A-1 — must-fix｜生成器 `CAPTION_SCOPE`、provenance、figures README「入力」**

`authority_scope` は稿を **“not … the floor judgment”** と明示的に判定の出所から除外しています。しかし、`RECORDED_JUDGMENT` の出所は稿 §2.1 であり、README「proof chain」もそう記述しています。certification が持つのは effects で、今回の床値判定ではありません。fig9 型の説明をそのまま適用できない箇所です。

既存の scope 文言を「限定・条件の言い方と記録済み床値判定の出所」に訂正し、対応 test・provenance・README を揃えれば足ります。新しい参照機構は不要です。

**DW-G05:** 放置すると、図の判定が参照する稿を provenance 自身が出所から除外し、判定の参照説明が矛盾したまま着地します。

**A-2 — should｜生成器 `_caption`、figures README「キャプション正文」**

床の説明には次の限定が不足しています。

- CV の対象は **8 session の各 median**。現文の “coefficient of variation … across 8 sessions of 5 repetitions” では、40標本の CV と区別しきれません。
- “same settings” は設定上の一致であり、旧床値測定との binary・toolchain・node の同一性を証明していません。稿 §4 項3の「下限」という位置づけも落ちています。
- correctness について、稿 §4 項12の「workload argv は独立に記録されていない」が落ちています。“recorded check configuration” に添える限定として有用です。

既存の説明文を短く置換すれば十分です。√2 補正や新しい検査を追加する必要はありません。

**DW-G05:** 数値・判定は変わりませんが、caption 単独では床の統計量と条件同一性、correctness の観測範囲を広く読めます。

**A-3 — should｜生成器 `_authority_data`、段4 P2、README の「生成器は判定を作らない」**

実装は `effect < -cv` を評価して `computed` を作っています。したがって「判定計算をコードに入れていない」という説明にはなりません。一方、描画に使う値は `RECORDED_JUDGMENT` であり、certification を書き換えず、CLI の入力も固定 pin に閉じています。**新しい研究判定を出力する経路や certification gate ではなく、作図入力の整合検査**です。

P2 の「転記と照合」という根拠はこの区別を説明できますが、D2162 の「床値判定はコードに入れず稿で計算」を緩める根拠として、fig9 との類似だけでは弱いです。固定された今回の bytes では検査結果は常に同じなので、述語照合と専用負例を削り、既存の稿との転記一致 test を残す方が依頼に忠実です。

**DW-G05:** 放置しても今回の図・研究上の受理集合は変わりません。追加された拒否条件は `expected_hashes` 注入時の作図入力集合を狭めます。このため scope 上の整理事項であり、成果物を止める must-fix にはしません。

**A-4 — should｜figures README「何を示す図か」**

「区間推定を含めない」は、実際に描く標本平均の t95 CI と無限定では矛盾します。「効果・median・床値判定の区間推定を含めない」に限定すれば、caption と一致します。

**DW-G05:** 図は変わりませんが、README が実際の誤差棒を否定する説明になっています。

**A-5 — nit｜figures README「作図規約への適合」「入力」「proof chain」、tools/plotting README**

規約全文の逐語再掲ではなく、本図への適用説明になっている点は適切です。ただし拒否条件、判定照合、固定文9件の列挙が複数箇所に重複しています。tools README はコマンド・入力・出力と fig10 節への参照、figures README は図の意味・caption・出所に絞れます。

**DW-G05:** 正本への参照と caption を残せば、重複説明の削除で図の値・受理集合・参照関係は変わりません。

## 削除候補

| 候補 | 削除後の DW-G05 上の影響 |
|---|---|
| 未使用の `DF = 4` | **変わらない。** CI 計算は `T975_DF4` と `REPS` を使い、表示も literal です。 |
| README 間の拒否条件・固定文9件の重複列挙 | **変わらない。** caption 正文・出所・正本への参照を残す条件です。 |
| P2 の述語照合、`computed_matches_recorded`、専用負例・m5 | **変わる。** 注入 seam の受理集合と provenance 項目が変わります。ただし固定 pin の本番入力、図の値・判定、certification の受理集合は変わりません。 |
| pin 済み tracked JSON に対する schema・固定条件等の意味検査 | **注入 seam では変わる。** 本番の固定 bytes では重複ですが、丸ごと削除を「完全同値」とは扱えません。大規模整理は本 wave に不要です。 |
| raw の束縛、標本再計算、layout 検査、着地検査 | **変わるため削除しない。** 標本の由来・描画値・成果物欠落の検知を担い、作図規約と受入要件に対応しています。 |

## 親 brief / 裁定への所見

**P1 は妥当です。** certification の `performance` は `median_tps` と `status` のみで、5標本は durable raw にあります。repo closure と外部 raw の hash 検査を分ける設計も明示されています。ただし repo closure 単独を raw 標本との独立な再照合と呼んではいけません。

**P2 は A-1・A-3 の修正対象です。** 転記判定の権威が稿である点と、照合用とはいえ述語をコード化している点を区別する必要があります。

**P3 は妥当です。** workload 別の上段尺度、median 比の下段、平均 CI と effect の区別は稿・作図規約に沿っています。有意差、優越、B-7 充足、機序、同一 binary、文字どおりの同時実行への昇格は見当たりません。

**実測記載は今回の読み取り照合と一致しました。**

- tracked 入力7件、raw 6件、PNG/PDF の SHA-256 は provenance と一致。
- raw 30標本と provenance、median 6値が一致。
- README の caption は provenance と逐語一致し、着地3件の hash も一致。
- 現環境は matplotlib **3.10.9** / numpy **2.2.6**。これは当該環境の確認であり、他環境の bytes 再現保証ではありません。
- raw correctness 記録には anomaly 件数がありません。caption に anomaly 0 を載せない裁定は適切です。paper-story README の既存記述を、図が検査した事実へ読み替えてはいけません。

**軽量版の判断:** certification 経路やその受理集合を変更していないため、段2・3省略を直ちに不適切とはしません。ただし「設計択一は閉じた」という理由は P2 について強すぎます。今回の独立レビューで局所修正へ戻せば足り、追加 gate やレビュー制度は不要です。

**変異13件の単一理由性：**

| id | 静的評価 |
|---|---|
| m0 | docstring 変更は動作同値。生成時 generator hash を現行 source の pin にしない設計とも整合。 |
| m1・m2 | 改行追加による hash drift なので、JSON の意味検査による二重拒否を避けています。 |
| m3 | 両 arm の標本を同率変更し、後段の effect 比を維持。author の対処は妥当です。 |
| m4 | 実装の rr5 effect `.4` は正のままで、前段の記録判定照合には抵触しません。 |
| m5 | 実装の rr95 floor `.2` は他の床条件を満たし、判定照合だけを狙えます。 |
| m6・m7・m12 | 変更 field を他の検査が同じ条件として再拒否する経路は見当たりません。意味負例は hash を再封印しています。 |
| m8 | 全 adopted token と対応 raw を揃え、token 間一致・raw identity の二重拒否を回避しています。 |
| m9 | 重なる figure text を注入する形で、指定した overlap 拒否を狙っています。 |
| m10 | 欠落による失敗と skip を区別しており、skip 復活を検知する構造です。 |
| m11 | 対象 literal の欠落を直接検査しています。 |

**疑わしい変異 id は、事前登録の代替案として残る m5（effect 符号反転）です。** その変更では後段の effect crosscheck も拒否し得ます。現在の floor 変更版なら、この懸念は解消しています。m3・m8 も実装では対処済みです。変異を実走していないため、KILLED／SURVIVED は未判定です。

## 総括

must-fix は **1件**：稿を床値判定の出所から除外する provenance の `authority_scope` を訂正すること。
plan v2 をこのまま採る判定は **NO-GO**。修正は既存文言・対応 test・provenance・README の局所変更で足ります。
P2 の述語照合は削除推奨。新 gate・台帳・一般化の追加は不要です。
数値・hash の読み取り照合は一致。pytest・描画・変異実走は実施していません。