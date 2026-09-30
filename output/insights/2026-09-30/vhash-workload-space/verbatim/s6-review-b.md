## 総括

**NO-GO。** 実読した統合 commit `4449cd02a` では、計測 driver が出す raw と作図器が受け付ける raw の schema が一致せず、全点の地図を生成できません。裁定 R11 の W 条件用 smoke も未実装です。以下は指定資料と repository の静的検査による所見で、実走はしていません。

## 所見

1. **must-fix｜raw schema が接続しない。** driver は `measure` の最上位 `schema_version` を常に `1` として出力しますが、作図器は `3` 以外を拒否します（[driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/orchestrator/campaign/vhash_cicada_vlife.py:932)、[作図器](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/tools/plotting/plot_vhash_workload_space.py:166)）。**影響:** 実測が成功しても成果物を生成できません。**推奨:** W の raw 契約を両側で統一し、driver が生成した形の fixture を作図器に通す結合検査を加える。

2. **must-fix｜裁定 R11 の投入判定が未接続。** 現行 smoke は旧条件の build・短走と旧式の時間見積りだけを実行し、全 `(genome, val_size)` build キー、操作 1000・値 1000 B・batchU/R の極端条件、maxrss による見積りを測りません（[smoke](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/orchestrator/campaign/vhash_cicada_vlife.py:814)、[見積り](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/orchestrator/campaign/vhash_cicada_vlife.py:884)）。**影響:** 504 走の予算と縮小判断を裁定どおりに行えません。**推奨:** W 専用 smoke と見積り・縮小記録を実装してから本計測に進む。

3. **should｜候補の意味付けが一律。** 選んだ全領域に同じ五つの機構を付け、用途も S/O 別の定型文にしています（[regions](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/tools/plotting/plot_vhash_workload_space.py:277)）。**影響:** 第 2 段で各領域の何を確かめるか、現実の用途に対応するかが決まりません。**推奨:** 実測後、領域ごとに根拠付きで機構と用途を記述する手順を成果物へ明示する。

4. **should｜測定値の集計が依頼より狭い。** 全点表の算出値は主に合算 read の `h1`・`depth8` と H2/H4 述語で、依頼が挙げた update read・write・validation 別の ≥1/≥4/≥8、K=1/2/4/8、生存版 bytes の地図は生成していません（[metrics](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/tools/plotting/plot_vhash_workload_space.py:206)、[全点表](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/tools/plotting/plot_vhash_workload_space.py:465)）。**影響:** md_29・md_28 が求めた偏りの読み方を、raw を手作業で再解析せずには報告できません。**推奨:** 既存 `position`・`deep`・サイズ field から必要な site 別列を出す。

5. **should｜反復判定の test が実体を通らない。** MB2 は `state()` を直接呼ぶだけで、`evaluate()` の反復から状態表への配線を行使しません。また `_install_parser()` は何もしません（[test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/orchestrator/tests/test_plot_vhash_workload_space.py:70)、[MB2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/orchestrator/tests/test_plot_vhash_workload_space.py:107)）。**影響:** 登録した MB2 型の配線変異が見逃され得ます。**推奨:** 2 反復の run から `evaluate()` まで通し、無処理 helper を削る。

## 削れるもの

- [作図器](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/tools/plotting/plot_vhash_workload_space.py:279) の未使用 `by_point` と、[H2 判定](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/tools/plotting/plot_vhash_workload_space.py:230) の直後に上書きされる最初の代入は削れます。いずれも実読上、結果を変えません。
- 追加の schema 定数辞書は field 名を同じ文字列へ写すだけです（[SCHEMA3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/tools/plotting/plot_vhash_workload_space.py:24)）。直接参照にすると検査量を減らせます。

## 足りないもの

- driver 出力をそのまま入力する結合検査と、裁定 R11 の W 専用 smoke。
- site 別の深さ・K 別候補率・生存版 bytes の集計出力。
- **後段の作業として**、実測値に基づく候補 3〜5 領域の個別解釈、生出力の所在、md_29・md_28 が指定する spool fragment。今回の commit は事前登録段階なので、これらの結果自体がまだ無いことは単独では不備と判定していません。