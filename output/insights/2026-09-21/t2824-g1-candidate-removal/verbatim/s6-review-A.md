## must-fix

- **[real：提示資料内の権限根拠不足] held 真値の更新依頼を、held 6 node の診断走・変異走の明示許可と扱う根拠が不足しています。** `s4-adjudication.md:13–14` は親の解釈です。D2194 項 5 は load / reverify 再実測と真値の追随を指示していますが、held test の解除には明示的に触れていません。`docs/decisions.md:66385`（D2125）は解除 env を「ユーザー明示専用」としています。既存セッションに実行許可があるなら、その逐語を紐付ければ解消できます。T-2810 の運用実績だけでは今回の許可を証明しません。
  
  台帳への影響：恒久 hold の変更は不要ですが、一時解除の権限根拠を記録する必要があります。  
  レポートへの影響：根拠のない実行を「ユーザー明示指示による検証」と報告できません。  
  受理集合への影響：production の受理述語には影響しません。検証手続きの問題です。

## should

- **[real・予定済み] 現行状態文の更新を完了してください。** `docs/phase3-8b-restart-runbook.md:329,337–341` は「候補込み hit 4 / 4」「historical が候補 hit で停止」「削除が残手番」のままです。段 7 の更新予定で解消できます。過去の insight・実測ログを書き換える必要はありません。
- **[real：説明の限定] 「production の受理集合を変える変更が無い」は「production の受理述語は不変」と書く方が正確です。** 候補削除によって実 checkout の historical 判定は拒否から成功へ変わっています（`reverify-*.json` の `reverify_published_freeze.ok`）。コード不変と実入力の判定不変は別です。

## nit

- **[real] D 番号の参照違い。** 現在の D2105 は path 参照の境界判定です（`docs/decisions.md:65229`）。解除 env の明示専用を直接述べる箇所は D2125（同 `66385`）、解除機構の規定は D360（同 `15663` 以降）です。

## 反証した懸念

- **[refuted] 真値の弱体化。** AST から定数を取り出して比較し、`p3-after-delete-g1.json.refusals` と UTF-8 bytes の集合一致、双方 2 要素を確認しました。`_assert_exact_refusals` は長さと集合の双方を比較します（`test_s8b_oracle_driver.py:305`）。6 node の assertion は差分に含まれず、部分一致・旧新どちらでも可への変更はありません。固定 official run の path は従来からの値で、elapsed・一時 path などの揮発 payload は追加されていません。

- **[refuted] 候補の tracked 存在への依存。** 指定の `git grep` を実施しました。writer は親 directory 不在時にも作成し、leaf は `O_EXCL` で拒否します（`s8b_holdout_freeze.py:2141`）。CLI の固定出力も維持されています（同 `2239`）。削除で既存 leaf 拒否が発火しなくなる帰結は裁定済みで、create-only 規則の撤去ではありません。

- **[refuted] fixture の取り残し。** replay 除去は現在の tree に存在する対象だけを選択します（`test_s8b_floor_campaign.py:2339`）。output 複製も可視集合から対象を除きます（`test_s8b_oracle_driver.py:847`）。合成候補を自分で作る検査は残っています（floor `11536`、driver `1945`、holdout `3117,3154`）。候補削除でこれらが空振りになる構造ではありません。

- **[refuted] scan 除外・pin の拡張。** clean scan は全件走査後の拒否を維持（`s8b_floor_campaign.py:5515`）、active exemption は V1・世代・approval・pointer の exact 集合（`s8b_ratified_freeze.py:3118`）、段階 8 は hit 集合の完全一致です（同 `3693`）。hooks に候補 path の存在を要求する参照は見当たりません。B-10 は固定した `output/s1-freeze` と `output/s8b-freeze` を走査し、候補 directory は対象外です（`b10_backoff_grid.sh:585`）。

- **[refuted] 不変条件の破壊。** Git 差分を独立確認しました。`58ec3e928` は候補 1 file の D のみ、`ce84ed8da` は test 定数と直上コメントのみです。production・hooks・B-10 pin・G/A/X・floor_source の bytes は変更されていません。削除前候補 bytes と現世代文書の一致も確認しました。

- **[refuted] 実測差分の過大な一般化。** before の拒否文字列から候補 path を取り除き、hit 件数を 4→3 にしたところ、g1・v1 とも **JSON 全 payload が after と一致**しました。live の `launch_validate.detail` も byte 不変です。ただし reverify evidence 全体では activation head・elapsed・historical 成否も変化しています。「候補除去だけ」は P3 拒否内容の差に限定すべきです。

- **[refuted] historical 成功の昇格扱い。** `s4-adjudication.md:8–9` と新コメント（driver `134–137`）は、historical 成功を certified・live admission・W-4/W-5 の許可と分離しています。提示資料に取り違えはありません。

## 変異の評価

- **M0：妥当。** コメントだけの等価変更は意味を変えず、SURVIVED の対照になります。
- **M1：単一理由の設計として妥当。** 定数の直接 consumer は driver 4 node（`4094,4574,4607,5468`）と binding driftguards 2 node（`287,326`）です。全て exact 比較なので、正常 baseline・実行済み・同一 checkout なら旧値への差し戻しで 6 node 全てが不一致になります。他 node がこの定数変更だけで赤になる依存は見当たりません。
- **結果は未確認です。** skip、fixture/setup 失敗、CLI 異常終了などでは exact assertion に到達しません。親の実走では「6 node が赤」だけでなく、失敗箇所が refusal exact 比較であることを確認してください。
- **diagnostic sensitivity pin の別枠は正しいです。** M1 は production の受理述語を変えず、期待値照合の感度を示します。受理集合の kill には数えられません。
- **追加の production 変異は必須とは認めません。** 今回は述語変更がなく、候補復元時の拒否は削除前 evidence、再生成物の clean-scan 拒否は既存合成 test が対応します。ただし M0/M1 だけで production 全体の検出力を証明したとは書けません。

## 総括

**NO-GO：held 実行の権限根拠の記録について。2 commit のコード・データ差分自体は GO。**  
既存の明示許可を紐付け、予定済みの状態文更新と親の検証を完了してください。本レビューは静的検査であり、テスト・変異走の成功は報告していません。