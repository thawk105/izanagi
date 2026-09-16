## 数値・定義・語順の照合

**63／162／99 と commit は一致。除外句の係り先に should-fix が 1 件あります。**

- `closure-head-a1b40608c.json:3` の commit は `a1b40608cbbdefb62846e6224313d12c2bce9dae`。`:4`・`:70`・`:71` の件数は 63／162／99。配列の長さ・一意件数も一致し、`discovered − enrolled = unenrolled` を確認しました。
- JSON の収載集合を seed に `edges` を反復展開すると、発見集合と完全一致します。新定義はこの構造、および `stage3-lensB.md` が記録した静的 import・package 初期化の probe 定義と整合します。probe 本体の再実行はしていません。
- JSON に日付 field はありません。`2026-09-16` は `stage4-ruling.md:1,5` の測定記録と一致します。JSON の commit 自体から測定日まで検証できたとは扱いません。
- `artifact_admission.py:77` の現在の収載数は、`:79` の日付付き実測と分離されています。後半の「うち収載 63」には日付が係りますが、冒頭の収載数まで過去の snapshot に限定する書き方にはなっていません。
- `artifact_admission.py:82` の「同発見集合に入らない module」は、集合外も除外する意味で読めます。verifier 3 path は JSON 上すべて集合外かつ未収載です。個別列挙は重複しますが、矛盾しません。

## 変異検出力の照合

全 M0〜M7 の置換元は、対象 file にそれぞれ **1 箇所**存在します。

| 変異 | 文言不一致を検出する照合 |
|---|---|
| M1：63→62 | `test_artifact_admission.py:1371` の `identity_scope` 全文一致 |
| M2：非推移閉包の句を削除 | 同 `:1371` |
| M3：99→69 | 同 `:1376` の `excluded_scope` 全文一致 |
| M4：source bytes の限定を削除 | 同 `:1376` |
| M5：完全性非主張を削除 | 同 `:1376` |
| M6：test literal の 162→161 | 同 `:1371`。production を変えず期待値側だけで不一致 |
| M7：test literal の集合外句を削除 | `test_s1_9pair_figure_provenance.py:385` の辞書完全一致、`:386` → `:155` の例外 |

M1〜M5 は、S1 の同じ辞書照合でも検出対象です。その照合への test 経路は以下です。

- `test_p1_independent_real_wal_projection_matches_frozen_report`：`:829` → `_real_inputs()`。
- `test_p3_real_provenance_closes_bytes_admission_caption_and_freeze_chain`：`:857` → `validate_real_provenance()` → `:694` → `_real_inputs()`。
- `test_p8_production_caption_matches_independent_parent_text`：`:1016` → `_real_inputs()`。

これらが M7 の静的な検出候補でもあります。P3 は出力 bytes 等の先行検査があるため、実走では失敗位置の確認が必要です。

**M0 の失敗 node を M1〜M5 から差し引く設計は妥当です。** production file の bytes 変更による失敗を、説明文への感度と混同しないためです。差し引き後にも、E0 の診断を独立 literal と比較する `test_artifact_admission.py:1371,1376` が残る構造です。静的に見て delta が空になる登録変異は見つかりません。

ただし、node 集合の差分だけでは失敗理由を証明できません。`stage4-ruling.md:67` の「各変異の赤は literal と定数の不一致だけ」は、差し引き前の赤全体には適用できません。実測記録では M0 共通核と、上表の照合で落ちた残差を分ける必要があります。これは今回指定された対照設計で扱えます。

`test_s8b_oracle_report.py:1007,1008` は定数参照なので、旧文言を独立に検出する照合ではありません。ここで production 変異が赤になっても、文言への感度とは即断できません。

以上は静的な検出経路の確認であり、KILLED・SURVIVED の実測判定ではありません。

## 所見

**1. should-fix — source bytes の例外が非 import 委譲全体に係ることを明示する。**

根拠：`orchestrator/campaign/artifact_admission.py:84`、`stage4-ruling.md:11,37,46`。

「収載 path の source bytes を除く data/schema、生成物、subprocess、…」は、「除く」が直後の `data/schema` だけを修飾し、後続の subprocess 等は無条件に対象外、と読む余地があります。「収載 path に関する data/schema 全般を除く」という読みは文法上自然ではありませんが、例外の係り先は一意ではありません。

裁定の意味を維持する最小案は、後半を次のようにすることです。

> および data/schema、生成物、subprocess、外部 command/Git、toolchain、binary、動的 import を含む非 import 委譲（ただし、収載 path の source bytes はこの除外に含めない）は本 map の外であり、完全性を主張しない

**成果物影響：放置すると材料レポートの `excluded_scope` が、収載済み subprocess 委譲先の source bytes まで対象外と読まれ得ます。台帳の値・参照や受理判定は変わりません。** 実装は裁定の逐語どおりであり、実装逸脱ではなく裁定文面への改善提案です。

範囲・所有外への波及には追加所見ありません。commit 差分は指定された 3 file・4 アンカーのみで、gate・検査・台帳機構・被覆拡大・docstring 再掲を含みません。

指定された production 10 file と consumer test を検索し、旧文言の独立 literal は見つかりませんでした。`s8b_oracle_report.py:597,600` は定数を直接参照し、残る 9 file は epoch/view の field を転記しています。例は `layer3_report.py:332,333`、`critic/digest.py:1261,1262`、`plot_s1_9pair.py:537,538` です。凍結済みの歴史 literal は変更されていません。

## 総括

**must-fix 0 件、should-fix 1 件。** 数値・集合定義・commit・変更範囲は整合しています。独立 literal による検出経路も維持され、静的に生き残りそうな登録変異は見つかりません。

除外句の係り先だけ明確化を推奨します。必読資料はすべて読取可能でした。ファイル変更・pytest・変異実走は行っていません。