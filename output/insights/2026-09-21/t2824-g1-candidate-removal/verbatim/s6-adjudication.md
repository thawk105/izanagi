# 段 6 裁定 — レビュー A / B の所見 (2026-09-21 09:00 JST、tip ce84ed8da)

レビュー B (`codex/s6-review-B-1.md`、過剰・削除 + 記録の限定): GO、must-fix 0。
レビュー A (`codex/s6-review-A-1.md`、正しさ境界・規律 2): コード・データ差分は GO、held 実行の権限根拠の記録について NO-GO。

| 所見 | 判定 | 処置 |
|---|---|---|
| A must-fix: held 6 node の解除 env 使用の権限根拠が提示資料では親の解釈だけ | **real (記録の不足)**。実行の差止め理由にはしない | 権限根拠を insight に明記: (1) 依頼の逐語 (`verbatim-origin.md`) がユーザーの直接メッセージで「held 真値 `_ACTIVATED_G1_REFUSALS` を現在値に更新する」を指示している。held node は受入全走で走らないので、実走せずに真値を書くことは F10 再発型 (held 真値が静かに古くなる、failures の「再発: 2026-09-20」節) そのものになる。同節は「policy epoch を動かす wave は held 真値の再実測を帰結に含める」と書いている。(2) D360 は解除口を exact token 1 本に限る決定で、解除の主体は定めない。「ユーザー明示専用」の読みは D2125 の却下案 (probe から held module を import する案) にある。本 wave の使用は依頼が名指す真値の検証に限り (held 6 node の診断走 1 回 + 変異 probe / final)、hold 台帳・growth_test_holds・受入の既定は変えない。(3) 先例: [T-2724] ax-delegated と [T-2810] が同じ 6 node を同じ token で実走し、land 済み |
| A should: runbook W-3 の状態文 (候補込み hit 4 / 4、historical が候補 hit で停止、削除が残手番) | real (予定済み) | 段 7 で更新 |
| A should: 「production の受理集合を変える変更が無い」→「production の受理述語は不変」。実 checkout の historical 判定は拒否→成功へ変わった | real | 段 4 裁定の文言は凍結済みなので本裁定で訂正し、insight と worklog では「受理述語 (コード) は不変、実入力 (repo tree) の変化で historical の判定が変わった」と書く |
| A nit: D 番号の参照違い (D2105 → D2125、解除機構は D360) | real | 本裁定と insight で訂正 (段 4 裁定の文面は凍結のまま) |
| A 変異の評価: M1 の赤が refusal exact 比較で起きたことを確認せよ | real (検収の条件) | final の `-rf` 行で失敗理由が `_assert_exact_refusals` の不一致であることを確認してから KILLED と数える |
| A: 「候補除去だけ」は P3 拒否内容の差に限定すべき (reverify evidence 全体では activation head・elapsed・historical 成否も変わる) | real (文言) | insight で「P3 の拒否内容の差は候補 path の除去 (hit 4→3) だけ」と限定 |
| B should: runbook §2 P3 の「最新の一次資料」参照が T-2810 §5 (削除前の値) に固定 | real | 段 7 で本 wave の insight の実測節を参照先に加える (判定規則は不変) |
| B nit: brief の成果物影響に「certified 選択・レポート値・台帳・批准参照・live の受理条件は不変」を足す | real | insight に書く |
| B 段 7 指摘: rc=2 は JSON に無いので親の実行ログを根拠に書く / create-only の存在拒否要因が消えても生成全体の成功は保証しない | real | insight に反映 |

fix は不要 (実装面の所見 0)。焦点再レビューは不要 (fix なし)。変異 matrix は probe → final の予定どおり。
