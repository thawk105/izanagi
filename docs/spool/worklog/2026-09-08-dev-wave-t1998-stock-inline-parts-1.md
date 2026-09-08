---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t1998-stock-inline-parts
seq: 1
title: [T-1998] balanced stock-inline 対照の最小 3 部品を実装した — 第 2 部品は「純増ゼロ」の起案を覆して実装へ回した (コード + テスト + docs、branch worktree-dev-wave-t1998-stock-inline-parts、変異 matrix = baseline PASSED・KILLED 16・SURVIVED 0・MISMATCH 0・期待 node 完全一致 26)
---

## 本文

- **D1244 が採用した最小 3 部品のうち、実装面の 2 つを land した。** 第 1 部品 (producer evidence の
  read-only 到達性監査) は insight に対応表として残し、producer schema は拡張しなかった。
  第 2 部品 (薄い sanctioned launcher) と第 3 部品 (事前登録固定 2 点だけを読む consumer) を実装した。
  **測定は 1 回も走らせていない。** prospective 事前登録と正式測定認可は D1244 のとおり人間手番へ返す。

- **段 2 のプランは「第 2 部品は純増ゼロ」を起草し、段 4 でこれを覆した。** プランは既存 A-5 job body が
  非 screening で `backoff_sweep.py balanced` を 1 回呼ぶので launcher は要らないと結論した。
  段 3 の敵対相談が、既存 A-5 投入器は同じ checkout から 2 job を出し、先に終わった job の
  global `git worktree prune --expire now` が後続を壊す**構造**であることを突き止めた。
  F251 の 2026-09-07 再発記録が同じことを書いており、2026-09-07 の balanced job は
  8 genome を計測した後 rc=1 で落ちて finalizer に到達していない。**親が現物で裏を取り、
  第 2 部品は純増ありと裁定した。** 新 submitter は balanced 1 job だけを投入し、
  job body は既存 A-5 のものを 1 byte も変えずに再利用する。

- **敵対レビュー 2 本が、親の緑を通っていない入力を 9 件構成した。** 親の実走は
  consumer 16 / launcher 6 / official perf 7 / hooks 474 がすべて緑だったが、
  レビューはその緑が通っていない入力を現物で作った。重いものは 3 件である。
  (a) 型付き CMake define (`-DCCBENCH_BACKOFF_NOINLINE:STRING=1`) が診断 build 検査を素通りする。
  (b) bench executable の検査が argv 内に期待 path が 1 回現れるだけで通り、`/bin/true <path>` を受理する。
  (c) attempt に属さない `verify_done` (anomalies=1) が素通りする — 規律 2 の迂回である。
  (b) は 2 本のレビューが独立に指摘した。9 件すべてを閉じた。

- **正例 fixture 自身が不整合な root だった。** toolchain manifest の canonical digest は
  `fb534797fa4eaa063c95c782900b817701208d1954ba13c1e7cae8124a453c59` なのに、fixture は
  `"3" * 64` を `toolchain_record_sha256` に記録して accepted を期待していた。
  「toolchain manifest と record digest が一致した」という戻り値が偽だった。

- **変異 probe を 2 回回した。1 回目に 2 件が生き残り、どちらもテストの穴だった。**
  M12 (toolchain の canonical digest 再計算) は**他層の mask** で、既存負例が target だけ digest を
  変えるため arm 間比較が代わりに赤にしていた。両 arm が同じ非 canonical digest を持つ入力でないと
  再計算層を単独で試せない。M9 (launcher の repo 境界検査) は**文字列存在検査の素通り**で、
  `if False and (...)` と書き換えても元の部分文字列が残るので通った。2 件ともテストを
  挙動検査へ変えて塞ぎ、probe 2 回目で 16 件すべてが検出されるようになった。
  1 回目の結果は erratum として insight に残した。

- **訂正 (追記による)。** 実装 commit の message は、新 submitter の 1 job 化で F251 の経路が
  「構造的に成立しない」と書いた。**正しくは「同一 invocation 内では成立しない」である。**
  別 invocation どうし、あるいは既存 A-5 job と同時に走る場合は、再利用している job body の
  global prune 経路が残る。後続 commit の message と本エントリで訂正した。

- 設計判断は {{D:t1998-thin-launcher-single-job}}、{{D:t1998-diagnostic-build-rejection-by-source-digest}}、
  {{D:t1998-shape-binding-over-content-reading}} に記録した。
  失敗は {{F:substring-presence-test-walks-past-disabled-predicate}} と
  {{F:mutation-masked-by-asymmetric-negative-fixture}} に記録した。

- **裁定パッケージ (本 wave では実装しない)。** (1) A-5 job body の global prune と投入器の
  2 job fan-out は F251 として既にユーザー裁定待ちであり触れていない。(2) 3 つの Pegasus 投入器に
  共通する queue preflight の欠陥 — `gen_S` / `ENA` / `ACT` を `qstat -Q` の出力全体で独立検索するため、
  `gen_S DIS INA` と `gen_L ENA ACT` が並ぶ出力で成功と誤判定する。誤った成果物は生まれない
  (qsub が失敗するだけ) ので must-fix にしていない。3 本まとめて直すのは別 wave の所有とする。
  (3) 事前登録の実値の固定と正式測定認可。

- **段 8 の自己改善は候補 3 件を実測し、3 件とも収容できなかった。** (a) 同じ prompt の再投入は
  receipt 衝突で rc=2 になるので `--job-id` を変える必要がある。(b) HEAD blob 束縛 file が未 commit だと
  子が drift 拒否で起動できない。(c) dispatch した collection の stdout は切り詰められ、
  報告された収集件数と抽出行数がずれる (実測: 37 件収集に対し 36 行)。
  収容先は `docs/dev-wave/operations.md` の DW-O01 と `docs/dev-wave/mutation.md` の DW-M08 だが、
  **L1.5 の unique footprint 予算 9,696 bytes に対し、(a)(b) を足しただけで 9,849 bytes になる。**
  既存記述の縮約は安全義務を削らずには足りない (予算のために義務を削らない)。
  D782 が委任した D730 の手順に従い、上限を引き上げず「実施しない」で閉じた。
  3 件とも session memory には入っているので、次 wave が同じ轍を踏む確率は下がっている。

- **main 側の欠陥で受入が 1 回空振りし、並行セッションとの相談で解けた。** main の tip
  `c12e25078` が `.codex/worktrees/` の gitlink 110 件を `.gitmodules` の entry 無しで取り込んでおり、
  取り込んだ wave の受入が `stage=preflight-index-flags rc=70 source_rc=128` で
  **テストを 1 件も走らせずに**止まった。因果は切り分けた — 受入 1 回目 (取り込み前) は
  preflight を通過して merge 段まで進み、取り込んだ 2 回目だけが落ちる。
  ユーザー指示で並行セッション 3 本へ相談したところ、別 wave が同じ失敗を独立に観測しており、
  是正 (`48837186c` で index から除去、`cf837838a` で既知違反台帳の母集団 pin を追従) が
  既に着地していた。**中継された SHA は自分の ref で読み直して検算した**
  (`git ls-tree main -- .codex/worktrees/ | wc -l` = 0)。
- **この失敗型の記録は別 wave の failures fragment が既に持っているので、本 wave の重複エントリは
  取り下げた。** 1 事象に 2 つの F 番号を作らないためである。相談で得た知見として、
  `.gitignore` / `info/exclude` へ足す案は F599 により採れない
  (共有木観測が `?? .codex/worktrees/` の bytes を見ている)。これは repo の F599 本文で裏取りした。

## 次の一手差分

### 更新

- [T-1998] **P2・実装済み → ユーザー手番**: D1244 の最小 3 部品を land した。第 1 部品は insight の
  到達性対応表 (producer schema は拡張していない)、第 2 部品は balanced 1 job だけを投入する
  `tools/pegasus/submit_t1998_balanced_stock_inline.sh` (job body は既存 A-5 を無改変で再利用)、
  第 3 部品は `orchestrator/campaign/t1998_stock_inline_pair.py`。**測定は走らせていない。**
  次は prospective 事前登録の実値 (期待 commit / gitlink / 環境契約 digest / job body script digest /
  arm 別 source digest) の固定と、正式測定の認可であり、どちらも人間手番である (D1244、D1267)。
  base: cf4e2c17521219e53afba503a4e8d781eab3e950de14d1ce461db2e66ec25947

### 新規

- {{T:pegasus-submitter-queue-preflight-line-scoped}} **P3・新規**: 3 つの Pegasus 投入器
  (`submit_a5_second_boot_backoff_sweep.sh`、`submit_b10_backoff_grid.sh`、
  `submit_t1998_balanced_stock_inline.sh`) の queue preflight は `gen_S` と `ENA` と `ACT` を
  `qstat -Q` の出力全体で独立に検索するので、`gen_S` が停止していて別 queue が有効な出力を
  成功と誤判定する。誤った成果物は生まれない (qsub が失敗する) が、停止理由が分かりにくい。
  `gen_S` の行を一意に取り、その行の状態列だけを検査する形へ 3 本まとめて直す。
