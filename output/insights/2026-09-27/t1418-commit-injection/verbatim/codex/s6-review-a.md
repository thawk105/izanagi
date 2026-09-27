## 所見 1 — must-fix: orphan 判定より先に復元へ進み得る

根拠: [tools/mutation_harness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:2400)、[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:2462)。

dispatch runner が `timed_out=True` または `job_may_remain=True` を返し、同時に touched file の bytes が M blob から変わっている場合、直後の blob 検査が例外を出します。後続の `_dispatch_orphan_stop` に到達しないため hold が作られず、`finally` は `reset --soft H` と restore を実行します。残存し得る job が参照する木を復元してしまい、次回起動を拒否する hold・sidecar も残りません。

**推奨修正:** runner の結果を受けたら、HEAD・bytes の再検査より先に orphan 判定と hold の確立を行ってください。その後、hold 保全経路で M の状態を検査します。`job_may_remain` と bytes 不一致が同時に起きる test を追加してください。現行 T7 は runner 内で先に hold を作るため、この経路を覆いません。

## 総括

**NO-GO。must-fix は所見 1 の orphan 判定順序です。**

静的検査では、plan v2 の CLI、起動前の残留 commit・detached 検査、M の親・path・blob 検査、H/M を判別する復元、commit 専用 policy 文言、および T1〜T9 の追加を確認しました。git hook の無効化、既定 file-swap の処理・ledger 文言、既存 test の期待値変更は差分にありません。提示された M1〜M8 の anchor は各対象箇所を指しています。wrapper・fanout の呼出しと既定 ledger を読む経路にも、静的に確認できる破綻はありません。

テストと変異 probe は実行していません。commit metadata による誤 KILLED の排除は、このコードだけでは証明できず、裁定どおり dogfood の失敗 assertion の確認が必要です。