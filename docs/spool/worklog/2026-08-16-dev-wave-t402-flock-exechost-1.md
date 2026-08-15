---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t402-flock-exechost
seq: 1
title: cross-node flock は排他された — Execution Host 照合まで通して dangerous を確定、真因は parser の文法不一致 (コード + docs、branch worktree-dev-wave-t402-flock-exechost、実測 = Pegasus gen_S request 912550、変異 matrix = 6/6 KILLED)
---

## 本文

- 依頼は「[T-362] と [T-361] の残り実測を 1 wave で走らせる」。**段 0 の一次資料照合で依頼の
  前提 1 件が stale と確定した** — [T-362] の mitigation / split-warning は request 887918 /
  887919 として**投入済み**で、エントリ (191) が [T-399] として決着させていた。以後
  [T-471] (206) → [T-486] deferred 確定 (223) → [T-503] へ論点が移っている。
  **本 wave で投げる T-362 実測は存在しなかった。** 残るのは [T-402] の 1 本だけだった
- **[T-402] は肯定側で決着した。** `dangerous: false`、`overall_verdict: BLOCKED_EXPECTED`、
  `valid_for_safety_conclusion: true`、`errors: []`。凍結した 5 条件 A/H/S/E/B が全成立。
  exact host pair は `bnode003` / `bnode004` で、qstat の Execution Host と job marker が
  job number ごとに一致した (`one_to_one_job_number_host_binding: true`)。
  `/work`・`/home` とも raw outcome 6/6 `BLOCKED`、`localflock` なし。
  正本 = `output/insights/2026-08-16_t402-flock-execution-host/RESULT.md`
- **真因は controller の実行時欠陥ではなく parser の文法不一致だった ({{D:qstat-grammar-mismatch}})。**
  実際の `qstat -J -f` は `Request ID:` block 内に**単数形** `Execution Host = <host>` を出すが、
  旧 parser は見出し `Execution Hosts(JSVNO):` を fullmatch で要求し、`=` を含む行で走査を
  打ち切っていた。**この語は保存 evidence 全体で出現 0 件。** 決定打は
  「**健全に完走し authoritative と判定された request 887918 でも
  `monitor.execution_hosts_raw_order` が `[]` だった**」ことで、
  2026-08-03 の attempt は保存 raw が 3 command だけで qstat に一度も到達していない。
  **段 1 brief の (P3)「NameError が原因」は誤りで、素の再走は何度でも `null` に終わっていた**
- **親が凍結済みの事前登録に反する指示を出し、焦点再レビューに検出されて撤回した
  ({{F:parent-violated-own-preregistration}})。** 段 6 fix 2 巡目で「1 block に 2 組の job/host も
  受理せよ」と指示したが、`verdict-preregistration.md` の `H` は「対象 block が**ちょうど 2 件**」と
  **親自身が直前に凍結していた**。実測は凍結どおりの 2 block 形式で通った
- 段 6 fix 2 巡目は `_saved_submission_validation` の意味も変え、wave 開始時から存在した
  fail-closed テストを赤にした (`1 failed / 120 passed`)。**期待値ではなく実装を戻す**契約どおり
  fix 3 巡目で HEAD の意味へ復元した
- **敵対検証の収量:** 段 3 の 2 レンズが blocker 11 / must-fix 13、段 6 のレビュー 2 本が
  blocker 2 / must-fix 5、焦点再レビュー 2 巡が blocker 4 を検出した。
  **DW-O16 の 3 巡上限をすべて使った。** 最終巡の GO 判定を得てから投入している
- **資源:** request 5/6、requested node-min 29/40、flock one-shot 1/1 を消費。
  投入は `912550.nqsv` の 1 本だけで、`t362-mitigation` の authority は無傷。
  `t362-default` / `t362-split-warning` は投入していない
- **単独性は未確認。** `#PBS -b 2` は 2 job の要求であってノード専有の証明ではなく、
  同居 job の snapshot を取得していない。専有を主張しない。
  `flock` の排他観測はノード占有に依存しないため結論は弱まらないが、時間・性能の材料には使えない
- **結論の射程:** exact host pair `bnode003`/`bnode004`・当日 kernel・当該 mount
  (`/work` は Lustre `rw,flock,user_xattr,lazystatfs,encrypt`) に限る。**gen_S 全体へ一般化しない。**
  **これだけでは D130 条件 2 も D131 共通前提 1 (移行窓) も閉じない**
- **受入全走は対象外。** production コードの差分はゼロで、変更は
  `output/insights/**/driver/` 配下の使い捨て probe と test・README、および新 insight だけ。
  射程はエントリ (128) / (149) / (191) と同じ。判定の証拠は本項のこの 1 行である
- **検査:** driver 評価器テスト 126 passed (計算ノード dispatch、request `912494.nqsv`)。
  変異 matrix は M1/M2/M3/M5/M7 と過剰拒否検出の正例 P1 の **6/6 KILLED・期待 node 完全一致**
  (`mutation-ledger-final.json`)。初回は期待 node 未確定のため probe とし、M1 (3 件) と
  M3 (2 件) の完全集合を実測で確定して再登録・再走した (erratum は RESULT §10)。
  `check_docs` / 全史 provenance はいずれも緑
- **運用で詰まった点:** (a) `tools/run_tests.py` は `dispatch_compute.dispatch()` を既定の
  `overall_grace_s = 300` で呼び**待ち時間上限を渡す口が無い**ため、gen_S が QUE 76 で滞留した
  ときに `queue-wait-timeout` で rc=16 になった。`tools/pegasus/dispatch_compute.py` を
  `--queue-wait-timeout` / `--overall-grace` 付きで直接叩いて回避した。
  (b) 待ち手を子の投入直後に張ると pid file 生成前に読みにいって**「producer 死亡」と誤判定して
  即座に空振りする**。成果物実在 + `.done` + producer 死の 3 点照合が捕まえた
- エージェント工数: codex 子 9 本 (段 2 プラン 1、段 3 敵対 2、段 5 実装 1、段 6 レビュー 2 +
  焦点 2 + fix 3 のうち 2 巡目以降)。実際は fix 3 本を含め計 11 本。
  Pegasus request 4 本 (テスト 3 + probe 1、うちテスト 2 本は基盤失敗)

## 次の一手差分

### 完了

- [T-402] `qstat -J -f` の Execution Host 照合まで通し、[T-361] の `dangerous` を
  `false` で確定した。既存 raw からの `resolve` 再構成は不可能 (qstat raw 不在・request 消滅) で
  再走が要ると先に判定し、そのとおり再走した。
  remaining: none
  base: 4b83b5619ab94dfe7b103b296e0e5cff0f7a39cbc00f4f0577602c3bf4457507

### 更新

- [T-361] **P1・実測確定 (exact tuple)**: `bnode003`/`bnode004` 間で `/work`・`/home` とも
  cross-node 6/6 `BLOCKED`、`localflock` なし、自己検査全通過、**Execution Host の一対一照合も成立**し
  `dangerous: false` を確定した ([T-402] 完了)。**射程は exact host pair・当日 kernel・当該 mount に
  限り gen_S 全体へ一般化しない。** 単独性は未確認 (同居 job snapshot 未取得)。
  **これだけでは D130 条件 2 も D131 共通前提 1 (移行窓) も閉じない。**
  条件 2 を閉じるには「同一 repo で同時 1 本」の保証を bnode 一般で示す設計判断が要る。
  base: 25ec94b90b13670e446c97de9c78a3fb2a719160cef7d1fba38886d214490ee1
- [T-362] **P1・追記のみ**: mitigation / split-warning の投入は (191) で完了済み。
  本 wave で新たに測ったものは無い。D130 条件 3 の閉じ方は [T-471] → [T-486] (deferred 確定) →
  [T-503] へ移っている。
  base: f7ef122a77ace67ea2007dff00a709008d3202914c069814cdcbf87b6ace6b08
- [T-360] **P1・裁定済み → 前提の残りは条件 3 側だけ (条件 2 は exact tuple で前進)**: 択 (a) は不変。
  **D130 条件 2 は [T-402] の実測で「1 host pair・1 回の観測では fail-open していない」まで前進**したが、
  **閉じてはいない** (射程が exact tuple に限られる)。条件 3 は [T-503] 系のまま。
  着手は D131 前提 6 点 + D105 supersede の次 wave で、ユーザー裁定に従う。
  base: 95da48df7274c0e488c0c01eea945c0ce857b36a927c16019d807231d34a7f23

### 新規

- {{T:flock-generalization-decision}} **P2・新規**: D130 条件 2 を「exact tuple の実測」から
  「gen_S で使ってよい保証」へ引き上げる方法を決める。候補は (a) host pair を変えて N 回測る、
  (b) 測定でなく設計で閉じる (lock を node-local に置かない / 単一ノード内へ閉じる)、
  (c) 条件 2 を supersede して別の安全機構へ置き換える。**測定を増やす前に (b)(c) を検討する** —
  [T-402] の実測は 1 tuple あたり request 1 本・node-min 10 を要し、族一般化には
  `DW-G03` の独立 2 例では足りない (host pair の組合せが多い)。
- {{T:run-tests-queue-grace}} **P2・新規**: `tools/run_tests.py` から dispatch の
  `--queue-wait-timeout` / `--overall-grace` を渡せるようにする。現状は
  `_default_dispatch` が既定 300 秒固定で、キュー滞留時に**テストが走らないまま rc=16** になる。
  回避策 (`dispatch_compute.py` 直接) は判明済みだが、`run_tests.py` が受入形の正規経路である以上
  滞留時に使えないのは運用上の穴である。
- {{T:waiter-pid-file-race}} **P2・新規**: `tools/dev_wave_wait.py producer` が
  **pid file 不在を「producer 死亡」と解釈して即座に正常終了する**。子の投入直後に待ち手を張ると
  必ず空振りし、`.done` も成果物も無いのに完了通知が届く。pid file 不在は「未起動」として
  bounded に待つか、待ち手側で pid file の実在を要求して起動前に停止する。
