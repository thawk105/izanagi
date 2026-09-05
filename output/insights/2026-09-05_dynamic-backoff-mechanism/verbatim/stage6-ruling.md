# 段 6 裁定 — レビュー A (must-fix 7 / nit 2) とレビュー B (must-fix 8 / nit 3) (2026-09-05 09:00 JST)

親が現物で裏取りした事実: `orchestrator/campaign/pin.py` の `CURRENT_PIN` は短縮 `511c953` (B-MF5 real)、
`plot_dynamic_backoff.py:681` は 7 block の hostname 一意を要求 (B-MF8 real)、probe は `trace_events` /
`trace_summary` / `successes` と文字列 enum を書き plot は `events` / `summary` / `hits` と整数を読む (A-MF2 = B-MF1 real)。

| 所見 | 裁定 | 担当 |
|---|---|---|
| A-MF1 counter 走査と時刻の観測点 | real・採用 (走査後に `sample_now` を取り check/update に渡す) | fix A |
| A-MF2 / B-MF1 診断 schema 不一致 | real・採用 (producer の現行 field 名を正本、fixture は producer round-trip) | fix C |
| A-MF3 診断 exact (rep 0、event ≥1) | real・採用 | fix B |
| A-MF4 既発行 group receipt の再検証と trace 削除 | real だが **不採用**: T-2189 が main に置いた既存機構で本 wave は触っていない。仮想リスク向け gate の追加は scope 外 (ユーザー引数)。裁定パッケージへ | — |
| A-MF5 / B-MF4 / B-MF5 repo clean・driver/PBS sha・argv・full pin | real・採用 (最小: `.pbs` の clean 検査、JSON に `driver_sha256`/`pbs_sha256`/`driver_argv`/`repo_status_clean`、plot へ転送)。凍結 prereg SHA の literal 照合は不採用 (改訂で自己参照になる。親が commit と JSON を照合) | fix B / C |
| A-MF6 動的認証の namespace と performance artifact identity | real・採用 | fix B |
| A-MF7 変異台帳の単一理由 | real・採用: M3' (cap 項のみ無効化)、M6' (負勾配で上限が増える。floor test は緑)、M1/M10 は冗長 gate と明記して単独証拠から外す、M8 は test が使う 3 つ目の cell 文字列で定義、M12 は削除 (PBS の検査は文字列 pin のみで意味変異を検出できない = 正直に記録)。遷移 test の被覆 (上限倍増・clamp 1000、±勾配の stock 同値、K=0 で counter を読まない) を fix A で追加 | 親 / fix A |
| A-Nit1 static_assert の関係制約 | 採用 | fix A |
| A-Nit2 docstring 25→32 | 採用 | fix B |
| B-MF2 欠測規則 (6〜7 block、点欠落、n<6) | real・採用。partial journal の表は親が insight で作る (prereg §6 を明確化) | fix C / 親 docs |
| B-MF3 perf の exact 7 cell 束縛 | **不採用**: 親の `submit-perf.sh` が exact 文字列を渡し、JSON の `cell_order` と plot の構成値検査で腕 identity は閉じる。費用面の話 | — |
| B-MF6 forest の複合判定表示・三値規則 | real・採用 (図に複合判定、H2/H6 の非判定点を弱調、三値規則を prereg v1.1 に明記) | fix C / 親 docs |
| B-MF7 abort の対内 pp 差 | real・採用 (provenance `abort_contrasts`) | fix C |
| B-MF8 投入 helper・distinct host | 一部採用: hostname 一意要求を撤去し記録 + 重複列挙。投入 helper は親の `submit-perf.sh` / `submit-certify.sh` (job dir) | fix C / 親 |
| B-Nit1 parser の整数 µs 検査 | 不採用 (patch の static_assert が build 前に止める。費用のみ) | — |
| B-Nit2 遷移 test の被覆 | 採用 (A-MF7 と同じ) | fix A |
| B-Nit3 prologue 時間 | 採用 | fix B |

**投入済み canary (977999 / 978000) の扱い:** patch B (A-MF1) が変わるので、この 2 job は Pegasus 経路の生死確認
(build・journal・診断 flush の実動) に格下げし、正式 7 block と診断は fix 後の最終 commit から投げ直す。
canary の性能値は事前登録の block に数えない (結果 JSON の値は親も見ない。insight には job ID と用途だけ書く)。

**事前登録 v1.1 (性能値を見る前):** §3 hostname 重複の扱い、§4 複合判定の三値規則、§5 診断 exact (rep 0、event ≥1)、
§6 partial journal の表は親が作る、§8 入力は 6 または 7 complete block + 診断 1、束縛 field の追加。
