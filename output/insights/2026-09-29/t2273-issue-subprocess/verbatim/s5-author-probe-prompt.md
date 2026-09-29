単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess

作業木 (あなたが書いてよい唯一の木): /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-probe
所有 path (これ以外を編集しない): 作業木内の新規 dir `probe-t2273is/` の下だけ (repo の tracked file は 1 byte も変えない。親が完成後に repo 外の job dir へ退避する使い捨ての計測 probe)。
docs は編集しない。commit しない (起動器が終端で記録する)。

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/s4-ruling.md — 親の段 4 裁定。**「計測の事前登録」2〜6 が仕様の正本。**
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/probe/ — 移植元 (前 wave の Codex author 製、読み取り専用): `t2273pi_run_series.sh`、`t2273pi_run_measure.sh`、`t2273pi_run_warm.sh`、`t2273pi_gate.conf`、`t2273pi_ab_analyze.py`。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-probe/output/insights/2026-09-27/t2273-shard0-precopy-impl/README.md §5 と verbatim/s4-ruling.md の「計測の事前登録」 — 移植元が実装している登録。

## 作ること

移植元 5 file を `probe-t2273is/` に `t2273is_` 接頭辞でコピーし、次だけを変える (投入手順・門番・台帳・tip と dirty の照合・有効性判定・E1・赤走の分類・集計量の定義は移植元のまま):

1. job dir を `/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928`、slug を `dev-wave-t2273-issue-subprocess` に替える (全 file の直書きと import 名 `t2273pi_ab_analyze` → `t2273is_ab_analyze`、`t2273pi_gate.conf` → `t2273is_gate.conf`)。
2. land 区分を s4-ruling.md「計測の事前登録」4 に合わせる: 有効 3 対がそろい series_invalid が無いとき、(i) 3 対すべて Δ = W_0(A) − W_0(B) > 0 ∧ 対率の中央値 ≥ 10 % → `land`、(ii) 3 対すべて Δ > 0 ∧ 中央値 < 10 % → `land-small`、(iii) それ以外 → `no-land`。そろわなければ `undetermined`。5 分判定 (B の W_max 3 走の中央値 ≤ 300 秒) は移植元どおり別の field (met / not-met / undetermined)。`record_line` は `land_class: <区分>; 5min: <状態>` の形にし、移植元の 4 通り区分 (`land-and-5min` 等) は出さない。land_reasons には区分の根拠 (全 Δ の正負と中央値) を残す。
3. 補助量 (事前登録 6): 各対の W_1・W_2・pre・post・O_max と対差、最遅 shard の番号を markdown と JSON に出す。移植元が既に出しているものはそのまま、欠けているものだけ足す。判定には使わない。

## 検査

- `python3 -m py_compile` を全 .py に、`bash -n` を全 .sh に通す。
- 集計器の単体確認: 移植元の前回系列 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/runs/` と同 job dir の `expected-added-nodes.json` を**読み取り専用の入力**として、作業木内の一時 dir に写して集計器を走らせ、前回 insight の値 (対差 +55.355 / +46.001 / +47.740 秒、対率中央値 12.7 %、B の W_max 中央値 317.194 秒 → 5 分 not-met) と一致し、新しい区分が `land` になることを確かめる。**移植元の job dir へは書かない。**
- 走らせられないものは「実装済み・未実走」と書く。

## 出力形式

見出し「## 作ったもの」「## 移植元からの差分」「## 検査」「## 未実走・懸念」「## 総括」。「## 総括」は 5 行以内。
