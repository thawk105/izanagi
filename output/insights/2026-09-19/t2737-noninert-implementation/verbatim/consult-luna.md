## 総括

**NO-GO（planの局所修正後は実装へ進める）。** helper接続とa〜d、e維持という範囲は妥当です。ただし、予定するheader変更が既存unit testを壊す点を計画へ追加してください。静的検査のみで、編集・実走はしていません。

**must-fix：study headerの条件化とtest側のdefineを整合させる。**

- [patch:871](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2737-noninert-codex/patches/ss2pl-lock-protocol-study.patch:871)では、`study_lock_test`にもcache由来の`SS2PL_LOCK_IMPL`を渡します。既定値は0です。
- [patch:991](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2737-noninert-codex/patches/ss2pl-lock-protocol-study.patch:991)付近のfixtureは、`ss2pl_control`・`SS2PLTxControl`を無条件に使用します。
- planどおりstudy headerの宣言全体を`IMPL==1`で囲むと、既定設定でtestsを有効化したbuildは型・関数を解決できなくなります。
- 最小修正は、**`study_lock_test` targetだけIMPL=1を単一定義として渡す**ことです。既存のIMPL=0へ重複追加せず、target別に選択します。productionの軸・意味論は変更不要です。

そのほかの判断は以下です。

- **親P1は予測として適切。** 過去の成功はf/g込みのrevSであり、a〜d限定版の成功証拠にはなりません。planの参照先はHANDOFF:26ではなく[29行](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-noninert-codex/HANDOFF.md:29)です。
- **既存策で足ります。** helper本体、gate、登録簿、receipt schemaへの拡張は不要です。helper用baseと、実際に生成物を書き込む`thirdparty_root/masstree`は別なので、実走では後者も実験専用複製にします。
- **検証を少し削れます。** 計器呼出し保存の比較は旧版の実configure・全target TU前処理で行えます。その目的だけの旧版binary buildは不要です。新版phase1 buildとWFG=0実不在検査は残します。
- **変異の帰属を固定してください。** helper削除と後置は同じ欠落を検出するため一方で十分。毎回config.h不在の複製から開始し、非zero終了だけでなく、意図した欠落・driftが拒否理由であることを確認します。13.7秒や過去の前処理bytes長を今回の固定期待値にしません。

検証候補は、①pristineからproduction `build_target(phase1)`の4軸・実build、②計器呼出し保存、③WFG=0の既存不在検査とabort所有権、④既定IMPL=0でtests有効時の`study_lock_test` buildです。controls全体成立やinert認証へ結果を一般化しない方針は維持してください。