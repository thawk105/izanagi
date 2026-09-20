## 所見

静的レビューの判定は **GO**。実装の must-fix は見つからない。以下の所見はすべて nit であり、親による受入試験・正式変異 matrix・docs 完成の代替にはならない。行番号は統合 commit `dc5b0f39b` 基準、`codex/` と `evidence/` は指定 job directory 基準。

**RB-1 — 同じ分岐を直積で覆う試験に削減余地がある。分類: nit**

- 対象: `orchestrator/tests/test_s8b_ratified_verify.py:2972`、`:2988`、`:2995`。
- 問題: 数値 7 field × 不正値 3 種の 21 ケース、および件数・順序の binding 有無は、共通述語を繰り返し通る。各ケースで無変異対照も構築する。
- 放置時の帰結: production の受理集合・成果物の値・参照は変わらず、Git fixture の構築と検証が重複する。
- 推奨対処: 下記「過剰と削除」の縮約を任意に検討する。裁定で指定した被覆と変異検出を保つことを優先し、本 wave の必須修正にはしない。

**RB-2 — author 報告の「17関数」「AST一致」は厳密には限定不足。分類: nit**

- 対象: `codex/s5-author.md:6`、`:29`。
- 問題: 新規は **test 関数 17 + helper 5 = 22 関数**。63 ケースは正しい。また、追加引数と分岐を除去しても docstring が異なるため、AST 全体は一致しない。docstring も除外すると一致する。
- 放置時の帰結: 受理集合・成果物の値・参照は変わらないが、関数数と比較条件の記録が実体より曖昧になる。
- 推奨対処: 親の集約記録では「新規 test 17 関数・63 ケース、helper 5 関数」「追加引数・分岐と docstring を除いた既存処理の AST が一致」と書く。

**RB-3 — PBS binding の保証境界は comment にあり、指定された docstring にはない。分類: nit**

- 対象: `orchestrator/campaign/s8b_ratified_freeze.py:2064`、`:2237`。
- 問題: 裁定 §2-1 項6は docstring への記載を指定したが、実装は構造検査直前の comment に「外部認証ではない」と記載している。内容自体は正しい。
- 放置時の帰結: 受理集合・成果物の値・参照は変わらず、関数 docstring だけを読む場合に保証境界を見落とし得る。
- 推奨対処: 文言上も裁定へ揃えるなら `_validate_journal` の短い docstring へ移す。重複記載は不要。

**RB-4 — T-2304 の追随経緯は実装 comment から削減可能。分類: nit**

- 対象: `orchestrator/tests/test_s8b_oracle_driver.py:132`。
- 問題: 「T-2304 統合時の追随を T-2810 で補完する」は裁定 §2-3 項5どおりで不適切ではないが、期待値の意味を理解するためには不要な作業経緯である。
- 放置時の帰結: 受理集合・成果物の値・参照は変わらない。
- 推奨対処: 今回は維持してよい。簡潔化するなら経緯を worklog に置き、comment は policy epoch、live 拒否、historical 到達点に絞る。

## 過剰と削除

追加された production 検査に、裁定 §2 で明示されていないものは見当たらない。

| 追加内容 | 裁定との対応 | 評価 |
|---|---|---|
| reservation の型検査 | §2-1 項3 | 明示された受理文法 |
| reservation の件数・順序 | §2-1 項4、A-1 | 明示された構造制約 |
| binding の型・claim・値一致 | §2-1 項2〜4 | 明示された記録内整合 |
| artifact の一意・非 merge・下限 | §2-2 項2 | 区間受理の制約 |
| 上限 `i ≤ G` | §2-2 項2 | 重複検査と明記して残す裁定 |
| 世代文書の導入集合 `{G}` | §2-2 項3 | wrong_g 拒否を保つ局所的置換 |

削減候補は次のとおり。

- `test_t2810_reservation_invalid_integer` (`:2972`): 21 ケースを、7 field に対する代表不正値 + 代表 field の残る2境界の **9 ケース**へ縮約可能。field の列挙漏れ、`0`、bool/int 区別、文字列拒否を維持できる。ただし裁定の直積指定と解釈され得るため、変更するなら縮約理由を記録する。
- `test_t2810_reservation_duplicate` (`:2988`) と `test_t2810_reservation_after_campaign` (`:2995`): binding を参照しない同じ分岐なので、各2ケースから unbound の各1ケースへの縮約候補。
- `test_t2810_binding_invalid_type` (`:2947`): 12ケース中、単独 event の8ケースは裁定 N-9 の指定被覆。`both` の4ケースは M4 を値不一致検査に遮らせないための追加であり、単なる無意味な重複ではない。M4 用を代表1ケースへ減らす余地はあるが、全削除は勧めない。
- `_t2810_journal_negative` (`:2882`): 51負例で対照を毎回構築する。裁定は隣接 test の対照も認めるので共有可能だが、変異時に各 node 単独で対照を確認できる利点がある。今回は維持が妥当。

`_assert_artifact_introduction_interval` (`s8b_ratified_freeze.py:657`) は裁定で明示された private helper であり、public API を増やしていない。public 経路では段階3が先行する上限負例を単体検査する役割もある。抽出を戻す必要はない。

旧 docstring の `∀i in I_entry: C<i …` の削除は正しい。新たに `i=C` を受理するため、旧文は成立しない。現在の docstring は区間全体と上限の重複性を正しく説明している。

## 記録の限定

**書ける主張**

- validator は、裁定された journal の2形と、一意・非 merge の `C ≤ i ≤ G` を受理する実装になった。
- 統合 commit の実 repo で loader は generation 1、sha256 `7e1114068433b40dc459e5e9c5ffcfa9a38cd360fc798904b7a9842382e19c06` を返した。
- historical reverify は段階4〜7を通過し、段階8で rr80 の未申告候補 path により `closure-hit-mismatch` となった。**段階8到達であり、検証成功ではない。**
- live `launch_validate` は `manifest-invalid` / `binary-admission`、現行 policy 不一致で拒否された。
- P3 の g1 は `allowed: false`、拒否2件が更新後の定数と完全一致。v1 は `allowed: false`、既知4件。両者とも held checks は3件残る。
- これらは提供された、統合 commit の特定 checkout における観測である。

根拠は `evidence/reverify-after-impl.json:3`、`:11`、`:18`、`evidence/p3-after-g1.json:1`、`evidence/p3-after-v1.json:1`。

**書けない主張**

- full launch validation 成功、historical reverify 全体の成功、P3 通過。
- rr20 を含む scan 全体の成功。提示された historical 結果は rr80 で停止している。
- W-4 承認、W-5 開始許可、certified 選択の更新。
- 候補 hit の解消、T-2812 の policy 移行完了。
- 旧 checkout に修正が適用済み、または移植後も同じ結論になること。
- fixture の成功による loader・批准 chain 全体の成功。
- `assert_g1_floor_selection_identity → None` の確認。この結果は今回渡された JSON に含まれない。
- 焦点走・正式変異 matrix・全回帰の成功。親の結果は本レビューに渡されていない。
- elapsed 値から一般的な性能を主張すること。

差分の docstring、comment、test 名、author 報告に、live 成功・W-4/W-5 許可・旧 checkout 適用を主張する表現は見当たらない。

## docs 反映の設計案

runbook を「判定規則 + 観測正本への参照」に直す案を支持する。journal 拒否を policy 拒否へ単純置換すると、現在値の重複が残る。

- `docs/phase3-8b-restart-runbook.md:163`: 段階表との照合、全 gate 成立時だけ `allowed: true`、拒否時は進まないという規則を維持する。日付付き拒否原因は削り、worklog 末尾と一次資料へリンクする。
- 同 `:330`: A/X の履歴事実と参照は維持し、発効と launch admission 成功を区別する。historical reverify の到達は live admission の代替ではないと記す。
- 同 `:337`: 「launch validation の不整合2件の解消」が残る手番として残らないよう、併せて更新する。今回の編集予定箇所に隣接するため見落とさないこと。

一次資料 README は次の表で十分であり、新しい gate や台帳は不要。

| 表 | 必要な列・内容 |
|---|---|
| 受理集合の変化 | 対象、旧条件、新条件、維持する制約。現物だけでなく中間導入・分岐合流も明記 |
| 実測5件 | loader、historical、live、P3 g1、P3 v1。root/HEAD、入力、結果、証拠ファイル、証明範囲 |
| 変異 matrix | M0〜M14、変異、期待 node、実測 node、結果、赤理由、証拠。author probe と親の正式実測を区別 |
| scope 外4件 | N1/T-2812、N3、旧 checkout 移植、W-4/W-5 |
| 限界 | fixture/core、loader、helper、historical/live、未実測事項の区別 |

N3 の行には、候補削除は未実施・別裁定であること、削除すれば hit 集合と create-only の存在拒否が変わること、再生成で hit が戻ること、履歴保存と削除後の再検証が必要なことを記す。

worklog fragment の「限界・言わないこと」には、少なくとも以下を入れる。

- historical は候補 hit で失敗したまま、live は policy 拒否のまま。
- W-4/W-5、certified、測定値・認証結果は更新しない。
- 旧 checkout は未移植・未確認。撤回された「同じ結論しか出ない」を再掲しない。
- fixture は launch core、M13 は重複上限検査の単体証拠。
- binding は PBS 外部認証ではなく、DAG の記録順は実時間順を保証しない。
- 正式 matrix、焦点走、identity の結果は実際に得られた証拠だけを書く。

## 説明と実体の照合

提供 diff は `git diff 800178b39 dc5b0f39b` と byte 一致。HEAD は指定 commit、working tree は clean だった。

| 項目 | 照合結果 |
|---|---|
| production 差分 | `+99/-10`、報告と一致 |
| verify test 差分 | `+309/-3`、報告と一致 |
| oracle test 差分 | `+7/-5`、報告と一致 |
| 新規 test | 17 test 関数、parameter 展開63ケースで一致。helper は別に5関数 |
| 既存 production 関数の変更 | `_validate_journal` と `_launch_validate` のみ |
| 既存 event 集合 | 全て不変。campaign は15 key、reservation は新規10 key |
| 段階4、cert block、段階7 | byte 不変 |
| 既存 test 関数本文 | byte 不変。既存 wrong_g/C=G 期待値も維持 |
| default fixture | docstring 等を除いた処理 AST が一致。RB-2の限定が必要 |
| refusal 第1要素 | 文字列を UTF-8 bytes として比較して不変 |
| refusal 第2要素 | 提供された `p3-after-g1.json` の第2拒否と完全一致 |
| g1 拒否集合 | 定数と実測の2件が完全一致 |
| `git diff --check` | rc=0 |

author の `p3-before-g1.json` との一致主張は、そのファイルが今回の射影にないため独立確認していない。代わりに指定された after 証拠との一致を確認した。

変更は指定3ファイルだけ。`output/**`、候補文書、driftguards、docs、hooks、設定に差分はない。policy 照合の変更、scan exemption 拡張、旧 checkout 移植、W-4/W-5 の開始処理も含まれない。

author 報告の試験成功数・失敗数・変異結果は報告として読んだものであり、本レビューによる再実測ではない。全回帰失敗と正式 matrix 未実施を明示しており、全件緑と偽ってはいない。

## 判定

**GO — レンズBの静的設計・実装レビューとして。**

実装を戻す、または scope を削る必須修正はない。RB-1〜4は任意の整理である。

wave 完了の条件は、親が裁定 §5 の受入結果を記録し、runbook・一次資料・worklog を上記の限定で完成させること。未提示の試験結果を、この GO で代替してはならない。

## 総括

変更は裁定の範囲内に収まり、研究前進は **validator の互換性修復と、統合後 checkout の historical reverify の段階8到達**まで確認できる。候補 hit と live policy 拒否は残る。必須の実装修正はなく、残作業は親の受入検証と、効能を広げない記録の完成である。