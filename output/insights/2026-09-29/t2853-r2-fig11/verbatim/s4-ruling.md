# 段 4 裁定 — [T-2853] R2 fig11 (2026-09-29 JST、親)

段 4 直前の裁定 inbox 再走査: 開始後に T-2853 / fig11 / A-6 に関わる新裁定なし (decisions の fig11・a6-r2 grep 0 件、ListAgents に fig11 の並走なし)。

| ID | 所見 | 判定 | 採否 | 処置 |
|---|---|---|---|---|
| plan-1 | P5 は git 不要だが materialize は durable base の cohort 衝突も調べる。旧 2 attempt は pin 511c953 なので通る見込み | real | 採用 | insight §1 に理由として書く |
| plan-2 | caption 差し替えは provenance の closure 再計算にも同じ差し替えが要る | real | 採用 | wrapper の要件 (段 5) |
| plan-3 | 結果稿の「図は無い」は現状と食い違う (fig11 は後で追加) | real (記述のみ) | 採用 | 陽性対照に既存 fig11 provenance を使う。結果稿は不変 |
| plan-4 / s3 L1-F1 | 再投入の地位と費用が未確定 | real (must-fix) | 採用 | §0 項 5 に費用条件を追記: 測定前に落ちた request の Elapse × 5 node を実費として足し、再投入後の見込み合計 (実費 + 1.47 + 受入 0.25) が 2.0 未満のときだけ 1 回投げ直す。2.0 以上ならユーザー確認まで投げない |
| s3 L1-F2 | override した hash は自己計算値で canonical pin ではない | real (should-fix) | 採用 | insight に「collect 後の bytes を束縛する自己計算値。受理根拠は receipt chain と生成器の照合」と明記 |
| s3 L1-F3 | login で patch の当たりを事前確認、「記録 0 件」の射程を限定 | real (should-fix) | 採用 | 親が実施済み (`precheck-patch.log`、rc=0)。condition gate・実 compiler・fanout は未実測と記す。「0 件」は durable base の preregistration と insights/worklog の grep の範囲に限定 |
| s3 L2-F1 | 図の負例の新作は削れる | real | 採用 | wrapper は陽性対照 (原 metadata で既存 fig11 の artist_series 完全一致) と R2 実入力の実行だけ。負例は作らない |
| s3 L2-F2 | §0 は足りている | nit | 受入 | 変更なし |

## プラン v2 (確定)

1. §0 を commit (項 5 に費用条件) → submit-tree (035fc11fa detached、submodule 再帰) → hydrate → login precheck → submit (argv は s2-plan §A)。
2. 待機中に段 5: Codex author が repo 外 wrapper (`/work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig11-20260929/tools/t2853_r2_fig11_plot.py`) を書く。生成器 bytes 不変、main に expected_hashes、caption の地位・役割語だけ差し替え (出現回数 assert)、provenance closure と再現 command を wrapper 経由で成立、`table` サブコマンドで元 attempt と R2 を load_measurements で読んだ対照表。陽性対照 = 原 metadata で描いて既存 fig11 provenance の artist_series と完全一致。
3. 完走後: finish-group → collect (--repo-root = 出力親/collect-root、cwd = submit-tree) → wrapper で描画・表 → insight。
4. 変異 matrix: repo の実装面の差分ゼロ (wrapper は repo 外、repo 変更は insight と spool のみ) なので DW-S04 により免除。受入全走は 1 回 (DW-S04)。
5. 段 6: review 2 本 (一次資料照合・正しさ境界 / 過剰・削除)。
6. node 時間: 本走 1 request 1.47 ((a) a6-20260909b) + 受入 0.25 = 1.72 < 2 → ユーザー確認不要と裁定。
