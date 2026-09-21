# 段 6 レビュー所見の対応表 (DW-O16)

レビュー A (正しさ境界) / B (過剰・削除・(P2) の根拠) はいずれも **NO-GO**。
**実装面の real 所見は 0 件** (A-2〜A-7、B-5・B-6 はすべて refuted)。must-fix はすべて親の文書
(裁定の根拠の書き方、実測資料の断定、要約の説明) に帰属する。したがって Codex fix 子は起動せず、
親が job dir の文書と段 7 の記録で閉じる。コード・test は 1 byte も変えない。

| 所見 | 判定 | 対応 | 状態 |
|---|---|---|---|
| A-1 corpus 条件を wave の解釈で免除したまま確定するのは不足。明示的な裁定パッケージにせよ | real / must-fix | 裁定 §2 に「追補」を足し、**wave の政策判断**であることと、既裁定から必然的には導けないことを明記。insight §8 の裁定パッケージ候補 (択 A / B / C と撤去手順) へ格上げ。decisions fragment も同じ枠で書く | closed |
| A-2 exact-85 の certified 流入 | refuted | 対応不要 (不変条件 1・2 の裏取り) | closed |
| A-3 validator の禁止条件の破れ | refuted | 対応不要 (84 / 86 / 同数別集合 / 順序違い / 96 / 95 の拒否を独立確認) | closed |
| A-4 scope 凍結・path 対応・固定値 | refuted | 対応不要 (変更前 blob との bytes 一致、固定 4 値の独立再計算) | closed |
| A-5 未知 grammar 負例の衝突 | refuted | 対応不要 (「96 − 末尾 11 本」は負例に使われていない) | closed |
| A-6 既存テストの緩和・新 11 本の到達可能性 | refuted | 対応不要 (42 ハンク全確認、反転・skip・xfail 無し) | closed |
| A-7 焦点走の赤 | refuted | 対応不要 (赤 0) | closed |
| B-1 25 本は同一 pre-85 固定木の反復で、exact-85 について同じことが起きる独立証拠ではない。観測・生成可能性・予測・政策判断を分離せよ | real / must-fix | 裁定 §2 追補で 4 層に分けて書き直す。「空白が再発する」を「再発しうる (機序は支持、発生は未確認)」に弱める。mtime は発行時刻でないと明記 | closed |
| B-2 corpus 未確認の収載の費用 (合成入力も読める / 恒久保守 / 先例) | real / should | 裁定 §7 と insight の「言えないこと」へ 3 点を追記 (A-3 の限界と統合) | closed |
| B-3 採用済みの「未検出」への訂正が元資料に残っていない | real / must-fix | `measured-facts.md` §2 と `brief.md` (P2) に訂正注記を追記 (追記で訂正し、元の記述は消さない) | closed |
| B-4 DW-G05 の値への影響が不足 (receipt の validator.sha256、B-4 projection、dirty 拒否の射程) | real / should | 裁定 §7 と insight の成果物影響へ追記。dirty 拒否は中央 capture 経路に限ると明記 | closed |
| B-5 scope 外の実装追加・局所追随漏れ | refuted | 対応不要 | closed |
| B-6 名乗りと D2081 適合 | refuted | 対応不要 | closed |
| B-7 「16 秒以上」の位置づけ | refuted / should | 「部分外挿による下限寄りの初期見積り、未追認」と書き換え、受入実走で追認する | closed |
| B-8 skip 9 件の説明が不正確 (growth hold を含む) | real / should | `focus-f1-summary.md` に内訳の訂正を追記。焦点走の緑を受入・変異の完了と扱わないと明記 | closed |

**3 巡上限 (DW-O16):** 本 wave の NO-GO は実装の赤ではないため fix を重ねない。親が文書を訂正し、
変異 matrix で実装側の検出力を裏取りして閉じる。根拠は worklog と insight に書く。
