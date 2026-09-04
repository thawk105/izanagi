---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-05
wave: dev-wave-t1905-b10-trial-cell
seq: 2
title: [T-1905] B-10 の 1 セル試し打ち phase を driver へ足し、balanced 45 セルを系列限りの限定受理で集約に残した — 試し打ちは formal と別 campaign 同一性に置き、成功は今回書いた record と WAL の認証に束縛する (コード + docs + insight、branch worktree-dev-wave-t1905-b10-trial-cell、変異 18/18 KILLED + 等価 1 SURVIVED)
---

## 本文

- **D1617 の裁定 (2) を実装した。** driver・投入 script・job script の phase 閉集合へ `trial-cell` を
  足し、block-1 の登録順で最初の登録 shape cell (現 spec では `constant-mu2`) を 1 変種だけ
  build → 全 verify path → 認証 → perf binary の SHA 照合 → 測定 → cell 記録 → trial 専用 report まで
  同一 job で通す。campaign 同一性は `search_tag=trial` と submission nonce で formal から分け、
  report は write-heavy 旧系列・balanced 旧系列・read-heavy 現行 formal の 3 campaign しか読まない。
  設計判断は {{D:b10-trial-cell-identity-and-balanced-legacy}}。
- **D1509 決定 2 は改訂して要件を外した** ({{D:b10-d1509-decision2-revised}})。満たしたとは書かず、
  D1605 の「測定を行ったうえで選んだとは主張しない」はそのまま残した。
- **balanced 974207.nqsv の完走を現物で確認した** (driver_rc=0、失敗記録なし、15 変種 committed、
  45 record すべて correctness_certified・missing=false・perf SHA あり・execution_host=bnode015、
  scheduler 実所要 13,186 秒)。campaign 143a3f74 の lock は 7 key の束縛、WAL は 135 record・15 変種で読めた。
  現行 driver bytes (sha256 f6246360…) は balanced 走行時と同一だったため、driver を 1 byte でも
  変えれば集約から外れる。D1597 の形 (campaign ID・旧 analysis commit/sha・旧 binding sha・
  45 件の内容 digest の exact 集合) で balanced 専用の限定受理を書き、write-heavy の限定受理
  (execution_host 不在を要求) とは共通化しなかった。**取り直していない。**
- **段 3 の相談 2 本が独立に、試し打ちの設計 2 点を real と指摘し親が採った。** (a) 設計 §5.2 は
  「レポートの生成まで」を要求するが plan v1 は cell 記録で止めていた → trial 専用 report を足した。
  (b) 固定 campaign ID では create-only の missing record が再投入を永久に失敗させ、逆に古い成功
  record だけで新 job が rc 0 になる → identity に nonce を入れ、成功述語を WAL の certified attempt と
  今回の submission identity に結んだ。レンズ B は「試し打ちの cell を `none` (BACK_OFF=0) にすると
  backoff 実動経路を踏まない」も挙げ、親は最初の登録 shape cell を選ぶ規則に変えた。
- **段 6 レビュー A が NO-GO を出し、fix 1 子で閉じた。** 事前配置した自己 hash の record と正当な WAL
  だけで測定を省いた成功が作れた穴 (trial は fresh のみ + 今回書いた record digest への束縛で塞いだ)、
  trial report に workload が無い点 (phase/workload を明示)、変異 spec の帰属 (m01 は `missing` だけが赤、
  m07 は nonce guard で fail-closed になるため両行を formal へ変える形に改訂)。焦点再レビューは GO。
  レビュー A が「trial-cell を read-heavy 限定にせよ」とした点は採らなかった — D1480 条件 2 は残り
  workload 一般の条件で、D1617 は balanced 完走を read-heavy の代替にしないと言うだけであり、
  誤認の経路は report の workload 明示と投入手順 (read-heavy の試し打ち成功だけを前提にする) で塞ぐ。
- **焦点走:** test_b10 + spawn_sites で 181 passed、consumer 4 file を足して 774 passed / 1 skipped
  (いずれも dispatch、30 秒未満)。実装子・fix 子は `qstat -Q` preflight rc=1 で pytest を 1 件も
  実走できず、親が実走した。
- **変異:** probe (全件 SURVIVED 期待) で観測 node を集めてから本走。**18 negative すべて KILLED
  (期待 node 完全一致)、等価変異 1 件は登録どおり SURVIVED**、baseline 緑。driver の行数を変える変異
  5 件は spawn_sites の行番号 pin 3 node も赤になる (drift mask、冗長 gate と明記)。m05 は正例 test の
  過剰拒否で kill (受理集合が変わる)。台帳と spec は `output/insights/2026-09-05_t1905-b10-trial-cell/`。
- **試し打ちを投入した** — 2026-09-05 00:25 JST、request `977483.nqsv` (trial-cell / read-heavy、
  24 時間枠、prereg `77b33e37d`、source `2a338449b`、nonce `b7539bc8…`)。投入元は専用の固定 checkout
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1905-b10-trial-cell/submit-tree` (detached、clean、
  submodule 初期化済み)。**受入が wave branch へ main を merge して HEAD を動かすため、wave worktree からは
  投入できない。** docs commit は driver bytes を変えないので、この tip の driver blob がそのまま land する。
  投入時の gen_S は QUE 275 / RUN 65 で、queue 待ちは既知リスク。read-heavy (verify-perf) は試し打ちの
  `job-result.json` (driver_rc=0) と trial report (`success_predicate=true`、workload=read-heavy) を
  確認した後に同じ固定 checkout から投入する。
- **段 2 の初回子が成果物ゼロで終わった** (同名 wave の並行起動、{{F:duplicate-wave-artifact-root-moved}})。
  新 job-id で再投入して回復。F841 は本 wave で supersede した。
- 事前登録文書 `docs/b10-backoff-shape-preregistration.md` は 1 byte も変えていない ([T-2311] の erratum は
  本 wave の完了後)。3 族 Holm の判定は書いていない。
- 工数: codex 子 = plan 1 (+ 全損 1)、consult 2、author 1 (1372 秒、103 calls)、review 2、fix 1、focus 1。

## 次の一手差分

### 更新

- [T-1905] **P1・試し打ち実行面は着地、試し打ち 977483.nqsv は投入済み → 完了確認後に read-heavy を投入**:
  試し打ちの job-result (driver_rc=0) と trial report (success_predicate=true、workload=read-heavy) を
  確認したら、同じ固定 checkout (`dev-wave-jobs/dev-wave-t1905-b10-trial-cell/submit-tree`、
  detached 2a338449b) から `verify-perf read-heavy` (24 時間枠) を投入する。job 完了まで固定 checkout を
  触らない。report phase は 3 campaign (write-heavy e3de15eb、balanced 143a3f74、read-heavy 現行 formal) が
  揃った後、同じ driver bytes の checkout から 1 回だけ走らせる。試し打ちが失敗したら、その理由
  (trial report と driver.stdout) を読んでから直し、新しい nonce で投げ直す。
  base: 31c81d4755d99600c58e56c36773b216f84c7caa5f18c27643ac209824dc97c5

### 新規

- {{T:b10-trial-cell-integration-test}} **P3・新規**: `run_formal(phase="trial-cell")` の制御本体
  (1 genome、1 schedule、do_settle、record 再読、trial report、rc) を stub 無しで通す統合 test を足す。
  段 6 レビュー B の nit。成果物の値は変えない。
- {{T:b10-trial-report-path-in-job-result}} **P3・新規**: job script の job-result.json に trial report の
  path と SHA を持たせ、driver.stdout を介さず submission ledger から辿れるようにする。
  同一 receipt の driver 再実行が非対応 (fresh-only 拒否) であることを runbook に明記する。
