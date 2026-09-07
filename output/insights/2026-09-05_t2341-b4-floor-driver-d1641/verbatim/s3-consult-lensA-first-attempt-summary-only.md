指定先への書込みは read-only sandbox に拒否されたため、`s3-lens-a.md` は作成できませんでした。静的検査は完了しており、結論は以下です。

- blocker 4 件、must-fix 7 件、nit 1 件。
- (P1): 却下。既存 driver という未見事実は決定本文と適合条件を変えるため、ユーザー再裁定が必要。
- (P2): 条件付き。base/sort では `site_projected_cfg` が `null` であり、現述語は不正。probe は失敗証拠も発行しない。
- (P3): 採用。新 policy だけを受理し、旧 strict policy は残さない。
- (P4): 却下。3-role sample と残 role の `not_run` は条件付き採用。pair 合算分母と `binary_binding_failed` の dropout 扱いは不採用。
- (P5): 条件付き採用。gen_S と rc=16 停止は妥当だが、再裁定と P2 の freeze 後に限る。
- (P6): 条件付き採用。検査時点で対象 6 path は不存在だが、全候補の完了 ledger も必要。
- 「欠測だけが実差」は誤り。driver/axis、PerfConfig 全項目、同一 session、journal、exact 2×59/24h、命名、環境不一致、予定外 retry に未達がある。
- 5% を window 全 pair で合算すると、ある pair の大量欠測を他 pair で希釈できる。少なくとも `(window,pair)` ごとの判定が必要。
- n=59 で最大 2 drop を許すと残数57となり、標本最大値の被覆信頼度は約94.6%で、95%に届かない。n、欠測許容、信頼度のどれを変えるか再裁定が必要。
- 現行 finalizer は status の閉集合所属しか検証せず、先行失敗のない `not_run` や高 D sample の status 改変を排除する因果 state machine がない。
- `binary_binding_failed` を5%枠へ入れると、現行の全体棄却を少数許容へ緩め、binary束縛の受理効果を後退させる。
- 現在の HEAD は `97ee3cd3a...`、local main は `103c32e30...` で、親 brief の「同一」は検査時点では成立しない。
- 親の51 testは正しい。planの42 testが誤り。§5の対象行記入後に sentinel が残るのは9行でなく8 value cell。
- 全文 SHA-256 の exact pin が0件という限定主張は正しいが、§5.1.1部分にはraw/semantic pinがある。`p3_b4_analysis_prereg_consumer.py` は§5表を読まない。
- 「同一セッション」は、3-role blockを裁定上のsessionと定義し直すか、candidateとreferenceを低水準paired sessionへ再設計するか、ユーザー裁定が必要。