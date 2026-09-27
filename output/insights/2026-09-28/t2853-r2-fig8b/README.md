# [T-2853] R2 fig8b — B-10 静的右 tail (fig8 を含む) を元の driver で Pegasus に測り直す

`authority: none` / `default_effect: no-state-change`

- 作成: 2026-09-28 JST。wave `dev-wave-t2853-r2-fig8b` (背景 job)、着手時の基準 = local main `51f896352`。
- 前段: `output/insights/2026-09-27/t2853-repro-rest/README.md` §3.3 (投入単位 = 図 1 本、fig8b は 1.40 node 時間で確認不要と確定)、
  `output/insights/2026-09-23/t2853-figure-rerun-plan/README.md` (図ごとの経路)。

## 0. R2 attempt の地位 — 結果より前に固定する (投入前に commit)

**この節は R2 の job を投入する前に書き、commit してから投入する。** D2050 は、完走済み cohort のある事前登録に
次の cohort を足すとき、地位と報告方法を結果より前に明記することを求める。事前登録
`docs/b10-backoff-static-tail-preregistration.md` の 2026-09-19 追記の項 4 は「第 3 cohort の実施・地位は本追記では定めない」とする。
本節がその明記であり、事前登録の bytes は変えない (R2 の job は原 cohort と同じ事前登録 commit の文書 bytes を束縛して走るため、項 2)。

1. **地位。** R2 attempt は、fig8b の測定設計 (事前登録 §4〜§7 の格子・動作点・反復数・判定式・正しさ検査) を固定 genome・LLM なしで
   1 回測り直す**再現パッケージの試行**である。cohort 1 (主結果、group `b10-backoff-grid-20260915T061814Z-545445`) の置換でも、
   cohort 2 (独立再現、group `b10-backoff-grid-20260919T131526Z-2235286`) の置換でもない。事前登録の cohort 系列へ加える第 3・第 4 cohort としても扱わない。
2. **形。** fig8b の 2 cohort × 各 3 job に合わせ、2 group (以下 R2-a・R2-b) × 各 3 job (write-heavy / balanced / read-heavy) を、
   元の driver `tools/pegasus/submit_b10_backoff_grid.sh --run-kind t2500-tail-formal` で同時に投げる。各 group は原 cohort が記録した
   source commit の checkout から投げる: R2-a は cohort 1 の測り直しで source `0600887d9`・事前登録 commit `cad6f46d8`、R2-b は cohort 2 の測り直しで
   source `8737cacb4`・事前登録 commit `8737cacb4` (いずれも reservation.json の `repository_commit` と集団報告の束縛から)。CCBench は両方 `511c9538`。
   探索走 campaign は cohort 2 と同じ path を渡す (事前登録 2026-09-19 追記の項 6)。
3. **合成しない。** R2-a・R2-b・cohort 1・cohort 2 の 4 group の標本・区間推定・verdict を互いに合成しない。統合 verdict、プール推定、
   group をまたぐ有意水準の保証を作らない。§4.5 の結末表は group ごとに独立に適用する。数値の近さを再現精度として評価しない。
4. **原 cohort は不変。** cohort 1・2 の稿・図 (fig8、fig8b)・集団報告は凍結物のまま保持し、R2 の結果で書き換えない。
   R2 の値は本 insight で原 cohort の値と並べて記録するだけである。
5. **結果にかかわらず報告する。** R2 の verdict が原 cohort と一致しても、不一致でも、`invalid` でも、未完走でも、そのまま本 insight に書く。
   失敗した group は取り下げず、得られた観測値と失敗理由を記述的に開示する。機械生成 verdict が無い場合はその不在と理由を明記する。
   起動時の検査で測定前に落ちた job (campaign・WAL・測定なし) は、新しい nonce・新しい request で同じ group 形のまま投げ直し、落ちた request ID と理由を記録する。
6. **正しさ。** anomaly が出た候補は即 reject とし (規律 2)、正しさ検査は原 cohort と同じく job 内の trace 有効 build で行う (規律 1)。
   検査を緩めて描く・記録することはしない。
7. **図が描けない場合。** 原 cohort と同じ生成器 (`tools/plotting/plot_b10_static_tail_formal.py`、bytes 不変) が R2 の入力を検査で拒否した場合
   (verdict が `not-observed-in-any-workload` でない等)、検査を外して描かない。完走・`invalid`・未完走・描画拒否のいずれの場合も掲載し、
   図が出ないときは group ごとの集団報告・得られた値・拒否理由を表で並記する。
   R2-a が旧 commit 固有の環境要因で測定前に起動できないと判明した場合に限り、R2-a を `8737cacb4` の checkout から投げ直し、その旨と理由を記録する。
8. **主張の範囲を増やさない。** R2 の verdict ごとに事前登録 §4.5 の分類と表現制約を守る。原 cohort と同じ verdict でも「飽和しない」へ読み替えない。
   性能は未認証のまま (`performance_certified: false`)。
