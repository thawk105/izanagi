# 段 4 裁定 — 受入門番の待ち時間診断 (2026-09-21 07:5x JST)

段 3 consult (`codex/s3-consult-out.md`、gpt-6-astra / medium / read-only、受理 rc=0) の 12 所見を親が現物で検算して裁定する。

## 1. 所見の裁定 (real / refuted、採否)

| # | 判定 | 採否 | 親の検算・裁定 |
|---|---|---|---|
| A-1 | real | 採用 | 母集合は「残存門番 log の最終 mtime 順 20 wave」と明記し、選択キーの期間 (9/20 21:29〜9/21 05:20) と実際の観測区間 (各 wave の全 attempt を含む) を別掲。landed は選択条件にせず列。9/19 以降の広域集計と T-2610 の事例検証を併記 |
| A-2 | real | 採用 | 親が確認: T-2610 log は 09:41:31 `recount leaders=2` の次行が 12:29:58 で同じ `attempt=1`。起動回 (log file) → 観測区間 (segment) → 投入 attempt を別 ID にし、tick 間隔が 600 秒超の空白で区間を分割、GO の無い区間は打切りとして分布に混ぜない |
| A-3 | real | 採用 | 親が確認: chain 型 script は `attempt N: main=… behind=` の直後に `git merge --no-ff --no-commit` → `dev_wave_wait.py` 起動 (script 68〜99 行)。門番観測待ち (最初の tick → GO / `attempt N:` 行) / 再試行準備 (rc → 次 tick) / GO 後の投入準備 (merge、started.txt まで) / 待ち手起動後 (started → finished) の 4 区間に分ける。wave 値は門番観測待ち区間の和 |
| A-4 | real | 採用 | (P2) 却下。「長時間混雑待ち」(観測待ち ≥ 30 分) と「再カウント拒否」(連続成立後の recount で leaders > maxl、chain 型は `gate closed at recount`) を別指標にし、飢餓候補 = 同一区間で観測待ち ≥ 30 分 ∧ 再カウント拒否 ≥ 2 (事例探索条件、一般定義ではないと明記)。T-2610 初回区間が候補 1 件・拒否 2 回・再起動後 0 件になることを正例照合 |
| A-5 | real | 採用 | leaders 値による同時待ち数の補正を削除。全残存 log (9/15 以降 192 file) の観測区間の和集合から「確認できた同時待ち数」(wave 単位で重複排除) を出し、log の leaders 値 (走行側観測) と欠測 (log の無い待ち手) を別列 |
| A-6 | real | 採用 | 日付復元: 日付付き記録 (chain 型 started.txt、loop 型の `acceptance-<tag>-N.started.txt`) を優先し、無ければ log mtime を最終行の日付として時刻の逆行で日を戻す。24 時間超の空白や逆行の多重は欠測。spawn log / .pid mtime は補助 |
| A-7 | real | 採用 | leaders 判定方式 (部分文字列 grep / argv 先頭一致 / 未確認) を起動回の列に持ち、差分だけで偽陽性と断定しない。走行区間 (started〜finished) との照合は「照合可否」列で示す |
| A-8 | real | 採用 | 条件 (maxl / maxload / maxpigz / 再カウント対象 / 連続回数 / grep 方式 / gate.conf の有無) を起動回ごとに出所付き (log 行 / script / 不明) で保持。chain 型は tick の `(cond …)` を優先。(P5) は記録 tick 列上の「条件成立機会の感度分析」(2 周連続 + 記録 recount 値の再適用、maxl ∈ {1,2,3} × maxload ∈ {60,80}) に縮小。1 段伝播模型は採らない。jitter / 位相 / FIFO には数値効果を付けない |
| A-9 | real | 採用 | 参照誤りを訂正 (9/18 12:40〜12:55 帯の同時投入は t2484 `gate-loop-acc.log` に無い。probe が全 log から同時 GO の帯を機械抽出する)。lease dir の「stale ticket 1 件」は親の `ls` 実測 (07:39 JST) であり、code (`wave_land_window.py` は単一 lease の作成・更新・削除のみ) の保存仕様と区別して書く。「receipt に時刻無し」は実物 JSON の key 一覧 (producer receipt: artifact/done の mtime_ns のみ、acceptance receipt: 24 key に時刻 field 無し) で書く |
| B-1 | real | 採用 | 主表に標本数・打切り数・欠測数・再投入回数・再カウント拒否数・閉門理由の内訳 (leaders 超過のみ / load のみ / 両方 / pigz)・時間帯 (JST 時間 bin) を追加。wave 種別 (paper / 実装 / 診断 / rulings) は slug から機械分類し「確認可能な範囲」と書く。tick 間の分数配分は推定と明記し因果寄与と呼ばない |
| B-2 | real | 採用 | 裁定パッケージは各択を独立した未裁定案として提示。FIFO / slot 機構は D2148 項 12 が「現時点では採らない」とした scope 外の設計判断として別枠 (数値効果無し)。閾値変更には適用対象・期間・検証条件を付し、D2185 は限定先例であって一般許可ではないと書く |
| B-3 | real | 採用 | author 射影に DW-O03 逐語を足す。probe は job dir で実行し JSON / MD を job dir に出す。repo (insight) へは probe の写しと生出力を `.md` 逐語でのみ置く。親の inline 集計実装は禁止 (前提実測の inventory_summary.py は母集合の列挙のみで数値を出さない — 数表は全部 probe から) |

## 2. 前提の判定 (v2)

- (P1) 要修正 → 上記 A-3 の 4 区間。門番観測待ち = 区間の最初の tick → 同区間内の GO (loop 型 `GO attempt=`) / `attempt N: main=` (chain 型)。GO の無い区間は打切り (censored)。
- (P2) 却下 → A-4 の 2 指標。
- (P3) 要修正 → A-5。
- (P4) 要修正 → A-8 (条件は起動回別・出所付き、不明を ≤1 型へ混ぜない)。
- (P5) 却下 (効果見積りとして) → 感度分析に縮小。
- 新 (P6) 区間分割の空白閾値 600 秒 (周期上限 140 秒 + jitter 45 秒 + 再試行準備 60 秒 + rc 待ちの余裕)。正例: T-2610 の 168 分空白で分割される。負例: 通常 tick 間隔 (100〜140 秒) と再試行準備 (60 秒 + 1 周期) では分割されない。

## 3. probe の仕様 (段 5 author への正本)

1. 入力: `--jobs-root /work/1/SFC/tanab/dev-wave-jobs` と `--claude-jobs-root /home/SFC/tanab/.claude/jobs` (両方走査)、`--since 2026-09-15`、`--recent-n 20`、`--out-json`、`--out-md`。標準 library のみ。
2. 走査: 各 wave dir (root 直下の dir、`~/.claude/jobs/*/tmp` とその直下 dir) の `*.log` (2 MB 未満) から、行頭 `HH:MM:SS` の後に `gate: load=` または `attempt=<n> leaders=` を持つ file を門番 log とする。同 dir の `run-acceptance-gated.sh` / `gate-acceptance-loop.sh` / `gate.conf` / `acceptance-*.started.txt` / `*.finished.txt` を読む。
3. 起動回 = log file 1 本。行の種類: tick (loop 型 `attempt=N leaders=L load1=X load5=Y ok_load=Z streak=S [maxl= maxload=]` / chain 型 `gate: load=l1/l5/l15 leaders=L workers=W [pigz=P] (cond leaders<=M l1<=X [pigz<=Q])`)、recount (`recount leaders=L` / `gate open twice -> jitter Ns then recount` の次の gate 行)、拒否 (`gate closed at recount` / loop 型は recount 値 > maxl)、GO (`GO attempt=N tag=` / `attempt N: main=… behind=B`)、merge (`merged: tip=`)、rc (`attempt N: rc=R` / `attempt=N rc=R "classification":"…"`)。未知行は種類 `other` として数え、落とさない。
4. 日付: A-6 の規則。各行に日付付き時刻を付け、失敗した file は `date_status=unresolved` として分布から除外し件数を報告。
5. 区間 (segment): 起動回内で、tick 間隔 > 600 秒、または rc 行、で分割。区間の種類: `observed-wait` (最初の tick → GO/attempt 行、GO あり)、`censored` (GO 無し)、`retry-prep` (rc → 次 tick)、`submit-prep` (GO/attempt 行 → started.txt)、`run` (started → finished)。
6. 条件: 起動回ごとに maxl / maxload / maxpigz / recount_scope (leaders-only / leaders+load+conf) / streak_required / leaders_grep (substring / argv-anchored / unknown) / gate_conf_present を、出所 (`log` / `script` / `unknown`) 付きで持つ。chain 型は tick の `(cond …)` を優先。
7. 指標 (区間ごと): 観測待ち秒、tick 数、閉門理由の内訳 (各 tick を leaders>maxl のみ / load>maxload のみ / 両方 / pigz 超過 / 開 に分類)、再カウント拒否回数、GO 直前 tick の leaders / load1 / load5 と recount 値、時間帯 (開始時刻の JST 時)、同時待ち数 (区間の各 tick 時刻に observed-wait / censored 区間を持つ他 wave の数、wave 単位で重複排除、最大値と GO 時点の値)、同時 GO 帯 (GO 時刻が 120 秒以内に並ぶ他 wave の数)。
8. 集計: (a) 直近 20 wave (最終 log mtime 順) の wave 表 (attempt 系列を全部含む)、(b) 区間分布 (中央値 / p90 / 最大 / 標本数 / 打切り数 / 欠測数)、(c) 9/19 以降の広域分布 (同じ列)、(d) 飢餓候補 (観測待ち ≥ 30 分 ∧ 再カウント拒否 ≥ 2) と長時間混雑待ち (≥ 30 分) の一覧 (両母集合)、(e) 時間帯別、(f) 条件変種の内訳、(g) 感度分析: 各 observed-wait 区間の記録 tick 列へ maxl ∈ {1,2,3} × maxload ∈ {60,80} を再適用し、「2 周連続成立 → recount (記録値があればそれ、無ければ直前 tick の値) が maxl 以下」を満たす最初の時刻と実際の GO との差 (秒) の分布。`sensitivity (仮定付き参考模型、効果見積りではない)` と label する。
9. 正例照合: T-2610 (`dev-wave-t2610-fig10/gate-loop-final.log`) が「区間 2 本 (50 分 21 秒 censored、600 秒超の空白を挟んで 14 分 13 秒 observed-wait)、再カウント拒否 2 回、飢餓候補 1 件 (初回区間)」になることを probe の self-check として出力 (一致しなければ非 0 で終了)。負例: T-2814 `gate-loop-final.log` は attempt 1 (12 分 25 秒 observed-wait、拒否 0) と attempt 2 (2 分 02 秒、拒否 0) に分かれ、飢餓候補 0。
10. 出力 MD の順: 母集合と観測区間 / wave 表 (直近 20) / 区間分布 / 閉門理由内訳 / GO 時点値 / 同時待ち・同時 GO / 飢餓候補と長時間待ち / 時間帯 / 条件変種 / 感度分析 / 欠測・打切り・未知行 / self-check。

## 4. 成果物と scope (再確認)

- 実装面 0 行 (repo)。probe は `tools/gate_wait_probe.py` として author 子 worktree に書かせ、親が job dir へ複製して実行。repo へは insight README と `verbatim/*.md` (probe 逐語 + 生出力逐語) のみ。
- 裁定パッケージ (insight §): 択 1 maxl ≤ 2 (対象・期間・検証条件つき、感度分析の値を添える)、択 2 maxload の再設定 (同)、択 3 jitter 幅 / 周期の位相 (数値効果無し、機序のみ)、別枠: FIFO / slot 機構 (D2148 項 12 の scope 外設計判断)。lease primitive・待ち手・TTL は択に含めない。
- 変異 matrix 免除 (実装面差分 0)。受入全走は免除しない。
