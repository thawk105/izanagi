# 段 1 brief — [T-809] 8c trial の workload 単位 fan-out 評価

- **scope**: 評価と設計のみ。**本番コードもテストも 1 byte も変えない** (ユーザー明示)。
  成果物は (i) 裁定パッケージ (実装可否の択)、(ii) insights の設計メモ、(iii) worklog fragment。
- **確定済み前提**: (1) runbook §7.5 / D289 (2026-08-11 ユーザー裁定) — 独立 job は既定で並行投入、
  ただし **job 間で性能値を比較する fan-out は protocol が node を block / randomization 因子として
  定義した場合だけ**許す。(2) [T-317] — repo 外の運転 script・probe は親が書いてよい。
  (3) 8c は `scientific_claim=false` の exploratory wiring pilot (`:1523-1531`)。
- **事実表**: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t809-8c-fanout/facts.md` (実測込み)。

## 不変条件 (fan-out の都合で緩めない)

1. 規律 2/3 — `assert_autonomous_trial_completeness`、cell admission、role 1 attempt / retry 禁止、
   journal と report の hash 束縛を弱めない。「N 本のうち成功した分だけ集計する」形にしない。
2. 規律 4 — fan-out が変えてよいのは投入時刻だけ。workload・世代数・レコード数・反復数を増やさない。
3. 正式経路の受理集合 (registered = 1 workload / 受入 = report 6 本 exact / lifecycle once) を変えない。
4. 計測の単独性 — bench 中に同一ノードで build や別 bench を走らせない。

## 親の provisional 裁定 (= 攻撃対象)

- **(P1)** 「fan-out すべき対象は探索 pilot の複数 workload run だけであり、正式系列は既に
  fan-out 済み (1 trial = 1 process) なので新規実装は要らない」。
- **(P2)** 「同一ノードでの fan-out は、build/bench を伴う限り採らない。bench は
  `bench_lock` で直列化されるが、他 process の build が bench 中に走ると計測が汚れる
  (`competing_bench_pids` は compiler を見ない)」。
- **(P3)** 「ノードを跨ぐ fan-out は、workload 間で性能値を比較する限り §7.5 の交絡条項に当たる。
  8c の workload-conditioned な主張は workload 間比較そのものなので、**現行 protocol では
  ノード跨ぎ fan-out を許さない**」。
- **(P4)** 「部分成功を fail-stop から独立完走へ変えるのは受理集合の変更であり、
  本 wave では実装せずユーザー裁定へ返す」。
- **(P5)** 「再投入は現状どおり新 trial_id を要求する形を維持する。lifecycle に retry を入れると
  start-once の一回性が壊れる」。

## 成果物影響 (DW-G05)

- 実装しない場合: certified 選択・レポート・台帳の値も受理集合も参照も**変わらない**
  (本 wave は 0 byte の実装差分)。変わるのは worklog の [T-809] 項が「評価済み・択を提示」に
  なることだけ。
- 逆に fan-out を実装した場合に変わりうるのは、(a) trial report の `status` の意味
  (fail-stop → 独立完走で `partial` の母集合が変わる)、(b) journal の一意性 (1 run 1 journal →
  N journal + 集約定義)、(c) wall 予算の意味 (trial 全体 → workload ごと)、(d) 計測値の
  node 交絡。いずれも成果物の受理集合に触るので、実装は裁定後に限る。

## 分割方針

段 2 = codex plan 1 本 (設計択の網羅と file:line 粒度の実装案)。
段 3 = 敵対 2 レンズ並列 (sol = 危険な許可・正しさ防壁、luna = 取りこぼしと守れない規則)。
実装面が無いので段 5/6 は無し。段 4 で裁定パッケージを確定する。
