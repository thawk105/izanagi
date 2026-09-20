静的検査のみ実施しました。以下、T は `orchestrator/tests/test_codex_worker_launch.py`、L は `tools/codex_worker_launch.py` の統合後行番号です。

## must-fix

**B1. 共有 helper の signature を変更している。**

- **根拠:** T:1124–1151 に `on_completed` 引数と callback 呼出しを追加。author.md:8 も申告している。本依頼の評価条件 1 は共有 helper の signature 変更を明示的に禁止している。
- **成果物への影響:** 負例表の数値は変わらなくても、裁定パッケージが「既存共有 helper 不変」という受入条件を満たさない。
- **是正案:** 共有 helper を元に戻し、rc 検査前の観測収集を T-2620 専用の起動・所有処理へ閉じる。変異時にも全観測値を採取してから比較する性質は維持する。

**B2. harness timeout 時、内側の launcher を所有・回収できていない。**

- **根拠:** T:1630 で harness が launcher を起動するが、その PID は test 側に登録されない。T:4623–4625 の `subprocess.run` が timeout で停止する直接の対象は harness。finally の対象は fake leader と `child.pid` だけ（T:4630–4640）で、内側の launcher が含まれない。T:4648–4650 の zombie 検査も待つだけで回収処理ではない。段 4 B2 は timeout・receipt 不在でも所有を要求している。
- **成果物への影響:** 異常経路で launcher が残り、後続走行や job 終了を汚染する可能性がある。「失敗時も後始末済み」という裁定材料にはできない。
- **是正案:** 専用 harness に launcher の PID 登録と終了要求への cleanup を持たせ、test 側は終了・回収を確認してから harness を終了させる。launcher 停滞／receipt 未生成の故障を注入し、元の失敗を保持しつつ所有対象が消えることを確認する。

## should

**B3. N4 は生存子がいるため、harness の 3 秒待機を通常経路でも使い切る。**

- **根拠:** T:1634–1648 は終了済み養子だけを回収する。N4 の生存子は test の finally（T:4634–4640）まで停止されないため、Z を回収した後も `waitid` が待機対象なしを返し続ける。harness の終了まで観測 callback に進めない。
- **成果物への影響:** N4 の所要と受入予算に、観測値を増やさない約 3 秒が上乗せされる。
- **是正案:** launcher 終了後、必要な state と Z 回収を記録できた時点で観測結果を通知し、test と cleanup を同期する。単に timeout を短縮するより、B2 の所有処理と併せて固定待機を除く。

## nit

**B4. author.md の計数箇所の行番号が統合後ソースと一致しない。**

- **根拠:** author.md は PGID 一致による加算を L:1727–1728 とするが、実際は L:1722–1723。
- **成果物への影響:** 負例表・結論は変わらないが、根拠の追跡先が読取失敗処理になる。
- **是正案:** 統合後の行番号、または関数名と該当式へ修正する。

評価した残りの項目は次のとおりです。

- **変更範囲:** author.patch の file 集合は T のみ。production 変更、既存 test の期待値変更、既存 fake mode の挙動変更は見当たらない。共有 helper 変更は B1 のとおり。
- **削除・統合:** 5 本とも維持が妥当。N1 は正常終了後の生存残存、N2a は正常終了後の Z、N2b は F973 の強制停止経路、N4 は混在、N3 は residual 単独の checker 束縛を検査する。既存 unknown 系 unit test、別 PGID の setsid escape（T:7576）、limit を改変する truth table（T:7618）では代替できない。観測処理は既に共通化されている。
- **再利用・命名:** 指定された既存 helper は用途に応じて再利用されている。N1〜N4 で `_run_case` を避ける理由も、起動前からの finally と rc 検査前の観測確保で説明できる。test 名はすべて `t2620` を含み、receipt 由来の dict key は field 名と一致する。harness は tmp_path に生成される。chmod はないが、`sys.executable` 経由なので実行上の欠陥ではない。
- **実走申告:** author の現行受理・拒否表は assertion と一致する。親ログの `216 passed in 11.55s` と終了時 sweep の `clean` は確認できた。ただし同ログは nodeid 別結果や author の「5 本 19.04 秒／12 本 9.34 秒」を掲載しておらず、その個別申告までは独立検証できない。未実走を実走とした証拠は見つからない。変異走・受入全走は別途必要であり、焦点走の緑で代替できない。

所要の静的内訳は以下です。上限値は通常所要ではありません。

| 負例 | `max_wall` | 主な待機 |
|---|---:|---|
| N1 | 10 秒 | PID 登録 poll 最大 5 秒、正常回収 poll 0.5 秒 |
| N2a | 10 秒 | Z 確認 poll 最大 5 秒、正常回収 poll 0.5 秒 |
| N2b | 3 秒 | wall 発火、TERM grace 0.05 秒、残存 poll 1 秒 |
| N4 | 10 秒 | PID／Z 確認が各最大 5 秒、正常回収 0.5 秒、harness 約 3 秒 |
| N3 | 3 秒 | 正常起動 1 回、checker 3 回（各 timeout 10 秒） |

N1〜N4 の外側 timeout は各 20 秒、PID 消滅確認は各最大 3 秒です。author の追加分 19.04 秒を台帳と同じ尺度と仮定すると、117.6 秒から約 136.6 秒、約 16% 増です。ただし計測条件の同一性は未確認です。10 秒の `max_wall` 自体を毎回消費する構造ではなく、現資料から全体 5 分超過とは判断できません。明確な無駄は B3 です。

## 総括

**NO-GO — 5 本は維持し、共有 helper の signature 変更と harness timeout 時の launcher 所有漏れを修正して再確認する。**