## 総括

静的レビューで must-fix を1件確認した。新しい非 floor schema の exact 検査が不足している。
予約の一回性撤去、世代を跨ぐ再測定、同一世代 attempt の一回性はソース上では成立している。
旧 schema は historical inspection に限られ、新予約の権威にはなっていない。
未知 role、signature、gflags、保護比率、canonical bytes、official/refreeze gate の緩和は無かった。
既知の resume 回帰と `exact` 文言欠落は再報告していない。
pytest は実行しておらず、緑は主張しない。`git diff --check` のみ成功した。

## must-fix

### 1 新しい非 floor measurement schema が exact shape と世代 identity を検証していない
- 位置: orchestrator/campaign/s8b_holdout_admission.py:828-865, 1623-1630, 1878-1901, 2369-2418, 3512-3534
- 何が壊れているか: `_MEASUREMENT_GENERATION_LEDGER_SCHEMA` の exact key 検査は floor role にしか適用されず、oracle・legacy n-pilot・R33 は余分な key を持つ row を受理する。さらに `measurement_generation_id` から digest を再導出せず、R33 claim/ledger も ID・digest・transaction の一致を検査しない。
- 成果物影響: 未知 key または不整合な世代 ID を持つ current ledger があっても新予約が通り、R33 ではその claim/ledger bytes が receipt の参照先として受理されるため、台帳値と予約・proof-chain の受理集合が拡大する。
- 直し方: role ごとの claim/ledger exact key 集合を定義して version dispatch 直後に検査し、`measurement_generation_id + observation_role + campaign_run_id` から digest を再導出する。R33 は ID と `transaction_id` の一致も要求し、extra/missing key と ID/digest 不一致の負例を追加する。

## nit / backlog

- 新設された `orchestrator/campaign/s8b_holdout_admission.py:4274-4277` の `set(document)` 分岐は、直前で固定 key の dict を自分で組み立てているため恒真な source invariant である。防壁として数えず、削除するか既存同型と同様に明示するのがよい。

- 統合後も `orchestrator/tests/test_s8b_floor_campaign.py:6953-6960,6996-7000` が旧 `claims/`・`consumed/` に12/96件を期待している。production は新 namespace に書くため、この4 assert は静的に不整合である。これは実装子Bの「所有テストを更新した」という報告と最終作業ツリーの食い違い。

- テストの独立性が弱い箇所がある。

  - `test_floor_parallel_reservations_use_distinct_measurement_generations` は admitted 2件しか検査せず、世代 digest の相違や24行の台帳を検査しない。
  - `test_oracle_and_n_pilot_producers_use_measurement_generation_schema` は source 内の文字列存在だけなので、実際の出力 schema を壊しても死んだ参照が残れば通る。
  - `test_n_pilot_approval_argument_is_inert` は件数・schema・role だけを比較し、approval により他の台帳値が変わる実装を見逃す。
  - `_floor_expected_marker` は production helper を期待値生成にも使っており、marker projection の独立 oracle ではない。
  - legacy n-pilot と R33 は「別世代で同じ論理 attempt を双方 consume」の正例が無い。同一世代の負例だけでは marker path を effect digest に戻す変異を捕捉できない。

- 既存テスト弱体化の全体確認結果:

  - approval option/env/nonce と approval 必須拒否を固定していたテストの削除・反転はD1124の撤去範囲内。
  - parallel fresh 拒否、master-seed による再予約拒否、oracle 二回目拒否は変更された。master-seed は effect digest 同一性を新たに固定し、oracle の manifest schedule・reps・role 検査は元テスト前半に残っている。
  - resume transition、v1 preservation/backfill テストは削除された。旧 bytes を新予約権威にしない方針には合うが、`test_resume_reservation_uses_new_measurement_generation` の異世代期待は既知の修正方向と逆であり、fix と同時に同一世代再利用へ改訂が必要。
  - xfail の追加は無かった。

## 所見ゼロだった検査面

- 未知 `observation_role` は `s8b_holdout_admission.py:753-770` で fail-closed のまま。
- freeze signature exact 集合、gflags 型意味論、間接 flag 拒否、保護比率 admission は `holdout_observation.py:360-429` と `calibrator/runner.py:609-635` に残り、差分なし。
- canonical JSON helpers と `_write_exclusive` の `O_CREAT|O_EXCL` は `s8b_holdout_admission.py:441-453,970-992` で維持。
- `_assert_official_permitted`、`eligible_for_refreeze` の導出と freeze 側要求は `s8b_floor_campaign.py:453-463,6889-6902`、`s8b_holdout_freeze.py:1617-1618` で不変。
- 世代 claim の `O_EXCL` は通常経路の防壁とは説明されていない。同一世代の実効防壁は floor `:4096-4127`、oracle `:1994-2005`、legacy n-pilot `:3977-3988`、R33 `:3866-3873` の attempt marker。
- 旧 `claims/consumed` は floor historical inspector だけが読む。新予約は `:1493-1520` で旧 claim を参照せず、旧 ledger row も `:1621-1622` で予約 identity から除外される。
- field/key/schema 名に無修飾の `generation` は無く、`measurement_generation_*` と既存 `transaction_id`、`n_pilot_design_generation_id` に分離されている。
- 実装子A/Bの主要な挙動説明について、上記の非 floor schema 検査と統合テスト namespace 以外のソース不一致は見つからなかった。

## 判定できなかった点

- 既知の resume 修正子と marker 文言修正子は現在の差分に未反映なので、修正後の同一世代再導出・再利用は未確認。
- sandbox 制約に従い pytest は実行していない。したがって collection、nodeid実行結果、full suite の成否は未確認。