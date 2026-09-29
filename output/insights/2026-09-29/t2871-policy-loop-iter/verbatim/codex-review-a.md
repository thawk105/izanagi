## 総括

**静的レビューでは、計測 identity と layout の割付に重大な不一致は見つかりませんでした。** pair の番号は系列 state から一度だけ導かれ、counter は計測前に保存されます。候補と stock は同じ計測 cfg、layout、認可 session を使い、`run_campaign` の呼出しは従来どおり2か所です。現行経路では `default_cfg` が admission policy と環境契約を束縛済みで、後段の束縛によって main の ID と claim・計測 dir の ID が変わる経路は見当たりません。裁定の正しさゲートの順序と stock の `src_token == STOCK` 判定も維持されています。

## 所見

- **should — 停止時の stdout が未計測の ID を示す。** [p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:673) で `stopped-before` にも次番号の `measurement_campaign_id` を追加しています。放置すると、stdout を読む側が存在しない claim・計測 dir を参照し、完了判定を誤ります。最小修正はこの代入を削除し、停止時は `null` または field なしにすることです。正例: 予算停止した pair は stock と claim を作らず、stdout も計測 ID を示さない。

- **should — 新しい結合検査が compiler 不在で全件 skip になる。** [test_p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:776) の共通 helper が T1〜T3 をまとめて `pytest.skip` します。放置すると、計算ノードで compiler の発見に失敗しても claim・台帳・digest の検査が緑の test 結果に含まれません。受入用の結合検査では skip を失敗に変えるのが最小修正です。正例: compiler が無い環境では T1〜T3 が明示的に失敗し、環境修復後に3件とも実行される。

- **should — M5 の予定 assert は変異の失敗点に到達しない見込み。** [p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:479) の admitted view を系列 layout に戻すと、系列 dir には候補 WAL がないため、digest 比較以前に候補処理が例外になります。放置すると、変異台帳は「2本目の WAL 由来 digest を検出した」と誤って報告します。M5 を「admitted view が計測 layout を受け取る」境界を直接確認する変異・assert に再照準するのが最小修正です。正例: 計測 layout を渡す実装が通り、系列 layout を渡す変異だけがその境界の assert で赤になる。

## 成立しなかった点検項目

実行結果は対象外であり、T1〜T3 の通過、30秒 timeout の計算ノード上での余裕、変異の実際の赤は確認していません。静的には、子 process は実 `_authorize_measurement`・`acquire_claim`・`check_reservation`・`authorization_session` を差し替えていません。`PYTHONPATH`、cwd、環境変数の引渡しは整合しており、期待値に claim の時刻などの揮発値も焼いていません。runbook に実装との明確な食い違いは見つかりませんでした。

## 変異の単一理由性の予測

| 変異 | 予測 |
|---|---|
| M1 | 2本目が同じ claim で `ClaimError`。予定どおり。 |
| M2 | 強制終了後に旧番号を再使用し `ClaimError`。予定どおり。 |
| M3 | stock WAL を系列 layout から読めず `certified-stock` にならない。予定どおり。 |
| M4 | 1本目直後の系列 state・履歴の assert で赤。予定どおり。 |
| M5 | digest の予定 assert より前に admitted view の読込みで赤。単一理由性が成立しない。 |