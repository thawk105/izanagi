# [T-809] 8c trial の workload 単位 fan-out — 評価と裁定パッケージ (2026-08-11)

`authority: none` / `default_effect: no-state-change`

可変状態の正本ではない。**評価と設計だけを行い、本番コードもテストも 1 byte も変更していない。**
可変状態の正本は `docs/worklog.md` 末尾と `docs/phase3.md`。

同 directory の凍結逐語: `brief.md` (段 1)、`facts.md` (事実表)、`s2-plan.md` (段 2 codex)、
`s3-lensA.md` / `s3-lensB.md` (段 3 敵対 2 レンズ)、`s4-adjudication.md` (段 4 裁定)。

---

## 0. 問いと答え

> [T-809]: `p3_autonomous_workload_trial.py` の `for workload in selected:` を workload 単位で
> fan-out できるか。run root / provider・journal / receipt / wall 予算の分離設計と、
> 部分成功・再投入の定義を実測付きでまとめ、実装可否の択を返す。

**答え: 「本体 loop を割る実装」は要らない。要るのは、割ってよい条件の明文化である。**

理由は 3 つ。

1. **正式 (registered) 経路は既に leaf 分解されている。** 1 trial = 1 workload は機械強制で
   (`trial_registry.py:1024`, `:1272`)、受入は report をちょうど 6 本要求する (`:2189`)。
   複数 workload の逐次 loop が使えるのは探索 (未登録) pilot だけである。
2. **探索 pilot も、今日そのまま割れる。** `--workloads` を 1 個にして N 回起動すればよい。
   **実測で 3 process 同時実行が衝突ゼロで完走した。**
3. **割ったときに消えるのは「機構」ではなく「保証」である。** 期待集合の被覆検査、共有 wall、
   session 相異検査、trial 単位の start-once がいずれも 1 process 内へ縮む。
   これを埋める group 検証器は存在せず、正しく作れば数百行規模になる。

---

## 1. 実測 (2026-08-11, gen_S `bnode019`, request 903110)

条件: `--provider fixture --no-build --max-generations 1 --allow-unregistered-exploratory`。
**LLM 4 役も build も bench も含まない、supervisor 配線だけの計測である。**

| arm | 形 | wall (s) | rc | status |
|---|---|---:|---:|---|
| A | 1 process = 1 workload | 1.122 | 0 | complete |
| B | 1 process = 3 workload 逐次 (現行) | 2.006 | 0 | complete (3 cell) |
| B2 | B の再走 | 2.027 | 0 | complete (3 cell) |
| C | **3 process = 各 1 workload 同時** | **1.189** | 0,0,0 | 3 本とも complete |

- **衝突ゼロ。** run root・journal・campaign root・provider・namespace marker のいずれも競合しなかった。
- **この 1.69× を本番の利得として使ってはいけない。** 測っていないのは、queue 待ち、job prologue、
  LLM role の実所要 (定数の上限 1200 秒しか分かっていない)、build、verify、bench、cross-node 配置。
  本番 1 世代は role 4 呼びと build+verify+bench (既存 WAL n=51 で p50 147.0 s / max 406.3 s) が支配する。
- 途中で 2 本の probe を空費した。原因は (i) `PBS_JOBID` がコロンを含み `PATH` 上の shim を壊すこと、
  (ii) `IZANAGI_EXPLORATION_OUTPUT_ROOT` が git 配下を拒否し、`dev-wave-jobs/` が `.git` を持つこと。
- **login ノードでは trial 自体が走らない** (`site='PEGASUS_LOGIN'` で env contract が拒否)。

## 2. 分離設計 — 何が要って何が要らないか

| 資源 | fan-out 時 | 新規機構 |
|---|---|---|
| run root / journal / report | process ごとに完全分離。report は自分の journal hash と 1:1 束縛 | **不要**。ただし既定 run root は repo 内なので、外部 output root の指定が運用条件になる |
| provider | `run_root/provider/<role>` 配下で分離 | **不要** |
| campaign root | build 経路は共有 root 下の別 dir。identity は spec_content + commit + search_tag + search_config + trial で、**execution contract は入らない**。workload が違えば必ず別 id | **不要**。ただし同一 workload を 2 本立てると freshness 検査の race (保証対象外) に入る |
| transport receipt | process ごとに取得して journal 先頭と report へ投影 | **不要**。ただし別 job の receipt を 1 個で代表させてはならない |
| build context | process-local が仕様 | **不要** |
| lifecycle 台帳 | `flock(LOCK_EX)` + trial_id 単位の start-once / terminal-once | **不要** (並行安全) |
| **wall 予算** | 1 process 1 予算。N 本に配ると **N 個の独立予算**になる | **要る**。旧 1 trial と同じ総枠を主張するなら共有 deadline か group ledger |
| **期待集合の被覆** | `_check_workload_coverage` は cell が要求 workload の**接頭辞**であることと、欠けた分を終端事象が名指しで説明することを要求する。fan-out すると 1 workload 分へ縮む | **要る**。正式経路の受入 (report 6 本 exact) が担う役割を、探索側は誰も担わない |
| **session 相異検査** | `CrossRoleSessionTracker` は process-local。逐次では 1 trial 内の全 workload × 全 role を 1 集合として検査する | **要る**。しかも report 間の valid `child_id` 比較では代替できない — parse 失敗 attempt の session id は valid provenance に現れない |
| build cache | **claim は衝突しない** (identity に process ごとに一意な `source_root` が入る)。代わりに **run 内の cache 再利用が消える** | 不要だがコストが乗る |
| ccbench 作業木 | 呼び出しごとの使い捨て worktree で分離済み | 不要。ただし `git worktree add/remove/prune` は共有 base の登録簿を触る |

## 3. 部分成功と再投入 (現状の正確な姿)

- **外側 loop を止めるのは例外と wall 切れだけ。** `role-invalid` は当該 cell を止めるが
  **次の workload へ進む**。したがって現行も「全部 fail-stop」ではない。
- `status` は科学的成功ではなく**実行投影の完全性**を表す。`complete` を certified 選択と読まない。
- **resume は無い** (`run_root` は新規 dir 必須)。
- **registered の再投入は同一 trial_id では不可** (`lifecycle-start-once`)。
  **新 trial_id を 1 本足すだけでも足りない** — manifest は exact 6 trial で、受入は
  manifest hash との一致を要求する。clean な再実験は新しい exact-six manifest と新しい 6 ID を要する。
  **ただしそれは「やってよい」ではない。** 8b の裁定は crash 後の再走なし・実験全体を判定不能とする。
  失敗系列を残したまま成功するまで新系列を作れば repeat-until-success になる。
- **exploratory** は lifecycle を使わない。no-build なら同一 ID でも技術上は動くが、
  build は同じ trial/workload が同じ campaign id となり freshness gate で拒否される。
  常に新 ID・新 run root を使うべきである。

## 4. 交絡 — ここが本当の分岐点

runbook §7.5 / D289 決定 (2) は、**job 内で閉じる比較は無条件で許し、job 間で性能値を比較する
fan-out は protocol が node を block / randomization 因子として定義した場合だけ許す**と定める。

- **job 内で閉じる**: 1 leaf 内の correctness verdict、bench rep の median / CV、
  同一 node で測る stock / variant の対。→ node は共通因子として相殺される。
- **job を跨ぐ**: 正式系列 (H1 rr80 / H2 rr20 × descriptor on/off/swapped) の arm 間性能差。
  → **6 trial を 6 node へ散らすと処置と node が完全交絡する。**
  現 manifest は `{trial_id, arm, holdout, campaign_id}` しか持たず node 因子が無い。
- **現行 A/B/C の探索 pilot は `scientific_claim=false` の配線 pilot** であり、
  job 間で性能値を比較しない。**したがってこれを node 交絡を理由に禁止することはできない。**
  親の初稿はここを広く禁止しており、敵対 2 レンズが独立に撤回を求めた
  (worklog 418 で撤回した「未測定量を根拠に広く禁止する」の再発)。

---

## 5. 裁定を求める問い

### RP-1. 8c の workload 単位 fan-out を実装するか

- **(a) 実装しない。** 探索 pilot を割りたいときは `--workloads` 単数 × N 起動で足りる。
  割ってよい条件 (§6) を docs へ明文化するだけにする。 **← 推奨**
- (b) 薄い launcher を `tools/` に作る (N 起動 + rc / hash 回収)。実装面 = Codex author 必須。
  純 launcher で 80〜200 行、exact validator まで作るなら 300〜700 行 + テスト。
- (c) 本体 loop を撤去し 1 process 1 workload を強制する。既存の複数 workload CLI・共有 wall・
  report 内 session 相異検査・fail-stop 意味論を失う。中〜大 (production 250〜500 行)。
- (d) 二層の group supervisor を新設する (group manifest / report / receipt)。大 (600〜1200 行以上)。
- (e) **fan-out ではなく律速そのものを解く。** 予算設計メモは worst-case envelope の 77% が
  role timeout であり、最短経路は role cap の低減だと書いている。

**推奨理由 (親の独立評価):** 割るために足りない機構は「起動側」ではなく「検証側」である。
N 本を旧 1 trial と同値な成果物として扱うには、期待集合・共通 wall・session 相異・
scheduler receipt を束ねる検証器が要り、それは (b) の「薄い」範囲を超える。
一方で今すぐ得られる利得は、実測できた範囲では supervisor 配線の 1.69× だけで、
本番の律速 (role 呼び + bench) には効かない。**作る価値が立つのは、no-build pilot を頻繁に
回すようになり人手照合が実害になったときである。** (e) は本タスクの外だが、
「fan-out すれば速くなる」という前提自体を検査するために択へ残す。

### RP-2. build を伴う fan-out を許すか

- **(a) 許さない (現時点)。** 同一ノードでは他 process の compiler が bench を汚し
  (`bench_lock` は bench だけを排除し、`competing_bench_pids` は compiler を見ず、
  `settle()` は timeout で `settled=false` を返すだけで計測は進む)、別ノードでは §4 の交絡と
  cache 再利用の喪失が乗る。 **← 推奨**
- (b) 別ノード限定で許す (性能値を job 間比較しない用途に限る)。
- (c) 同一ノードでも許す。

**注:** 親の初稿は「別 workload が同じ変異を合成すると build cache の claim が衝突して落ちる」を
禁止理由に挙げていたが、**これは誤りだったので撤回する。** cache identity には process ごとに
一意な `source_root` が入るため、標準経路で claim は衝突しない。禁止理由は計測汚染と交絡である。

### RP-3. 正式系列 6 trial のノード配置

- (a) **同一ノードで走らせる** (現行 protocol の含意を維持する)。
- (b) prereg 側で node を block / randomization 因子として定義してから fan-out する。
- **(c) いま決めない。** 正式系列は前提条件が未充足で着手できないので、着手時に (a)/(b) を
  再評価する。 **← 推奨**

**推奨理由:** 6 本を散らす利得は大きい (1 request 24 時間上限に対し 6 本直列は最悪 6 日) が、
prereg は AI が自律改訂してよい文書ではなく、いま触る必要もない。**ただし
「6 process だから 6 node へ散らしてよい」という読み方だけは今のうちに潰しておく必要がある** —
それが本 wave で最も危険な誤読である。

### RP-4. 部分成功の意味論

- **(a) 現状維持。** leaf report の定義を変えない。 **← 推奨**
- (b) fan-out 前提で group 意味論 (exact N 本が揃って初めて terminal) を導入する。

**推奨理由:** (b) は受理集合の変更であり D96 手続きを要する。RP-1 (a) を採るなら不要。
なお **(b) を将来採る場合でも「成功した leaf だけで集計する」形にしてはならない** —
現行の受入が partial report も含めて exact 6 本を要求しているのと同じ原則である。

### RP-5. 再投入の定義

- **(a) 経路別に明文化して現状維持。** registered = 新しい exact-six 系列 (= 再凍結と
  ユーザー裁定が要る)、exploratory = 新 trial_id + 新 run root。旧 request と新 request の
  対応を残す。 **← 推奨**
- (b) lifecycle に retry を入れる (start-once の一回性が壊れる)。

### RP-6. 条件の明文化をどこへ書くか

- (a) `docs/pegasus-runbook.md` §7.5 に 8c の項を足す。
- (b) `docs/phase3-s8c-autonomous-trial-runbook.md` の既知の限界へ足す。
- **(c) 両方に 1 行ずつ (運用規範は §7.5、trial 固有の条件は 8c runbook)。** **← 推奨**
- (d) 書かない。

---

## 6. 「割ってよい条件」(RP-1 (a) を採る場合に明文化する内容)

探索 pilot を N 本に割ってよいのは、次を**すべて**満たすときに限る。

1. `--no-build` で、holdout を含まない exploratory 起動であること。
2. 1 process 1 workload、一意な `--trial-id` と `--run-root`。
3. exploration output root を **repo 外かつ非 git** の job 専用 path に指定すること。
4. 投入前に期待集合 (N、trial_id、workload、run_root、request ID) を書き出すこと。
5. 完了時に全 N 本の rc・report・journal hash を照合すること。
   **先に終わった成功分だけで集計しない。**
6. N 本を「旧 1 trial と同値な 1 成果物」と呼ばないこと。性能主張・正式主張・
   同値性主張へ流入させないこと。

**これは人手確認であって機械保証ではない。** 汎用の N-job verifier は存在しない。

## 7. 本 wave の scope 外だが real な所見 (別タスク候補)

1. **正式受入 (`assert_trial_registry_acceptance`) は Layer-3 chain を必須経路で呼ばない。**
   `trial_registry.py` は `assert_autonomous_trial_completeness` しか import せず、
   証拠契約 (`s8c_preregistration_evidence_contract.v1.json`) は acceptance 自身からの
   Layer-3 呼び出しを要求している。また registry は「宣言 arm が実際に走った arm だとは
   認証しない」と自ら明記し、6 report 間で `measurement_head` の一致も検査しない。
   **fan-out とは独立の既存 gap である。**
2. **運用事実 2 件** (`PBS_JOBID` のコロンが `PATH` 上の shim を壊す /
   `IZANAGI_EXPLORATION_OUTPUT_ROOT` は git 配下を拒否し `dev-wave-jobs/` は `.git` を持つ) は
   runbook への追記候補。

## 8. 成果物影響

本 wave の実装差分は 0 byte なので、certified 選択・レポート・台帳の値・受理集合・参照は
いずれも変わらない。**ただし「コード差分ゼロ」と「fan-out 運用をしない」は別である** —
実際に N 回起動すれば、探索 report は 1 本の multi-cell report から N 本の leaf report へ変わる
(certifying 入力にはならない)。RP-1 (b)〜(d)、RP-2 (b)(c)、RP-4 (b) を採った場合に変わる値は
各問の下に書いたとおりである。
