---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-09
wave: dev-wave-t313-read-budget-gate
seq: 1
title: dev-wave docs の byte 予算を層 scope の常時読量 gate へ置き換えた ([T-313]) — 集約上限を撤廃し L1/L1.5 を凍結、L2 は単節 cap のみ (コード + docs、受入 7682 passed / 20 skipped、変異 SURVIVED 0、branch worktree-dev-wave-t313-read-budget-gate)
---

## 本文

- **一次裁定の逐語まで当たって実装方向を確定した。** worklog (140) の「択 (1)」が指すのは
  2026-08-03 パッケージ `output/insights/2026-08-03_t313-read-budget/s4-ruling.md` の択 1 =
  「3 層それぞれに現在値の上限を置く。常に読む量を凍結、クラス依存も凍結、条件のみは単節 cap
  (現行最大 935 → 1,000)」である。裁定文の要約 (「常に読む層は固定上限、全体の固定文字数上限は撤廃」)
  だけを読むと L1.5 の扱いが落ちる。**要約でなく択の本文を読んだことが本 wave の前提**である。
- **剪定述語は新規に書く必要がなかった。** 一次裁定の「剪定は byte 数でなく発火実績 + 機械検査での
  義務代替」は `docs/skill-self-improvement.md` の routing 3 に既に逐語で存在する。したがって
  本 wave は `docs/dev-wave/**` の予算を 1 byte も使わずに実装できた。[T-664] が
  「依頼された 2 経路では予算が空かない」と確定させた前提の下で、これは実装可否を分ける事実だった。
- **段 3 の敵対 2 レンズも段 6 の敵対 2 レンズ + 焦点再レビューも、すべて NO-GO を返した。**
  段 3 は 16 所見 (blocker 5)、段 6 は 8 所見 (blocker 4)、焦点再レビューは blocker 1。
  **refuted は段 3 が 0 件、段 6 が 1 件** (「pytest 未実走」は親が計算ノードで 357 passed を実走済み)。
- **親 brief の成果主張が過大で、段 6 レンズ B の実測で訂正した。** brief は「予算で止まっている
  項目の解放がここに集中」と書いたが、実装後に新 gate を通るのは [T-279] A3 (`DW-O20` 489+154=643)
  と [T-317] A9 を `DW-O19` へ置く場合 (602+147=749) の **2 件だけ**である。
  [T-328] の他の従属項目・[T-665]/[T-662]・[T-648]・[T-550] はいずれも L1/L1.5 固定に当たり、
  **実装後も書けない**。本 wave の効果は「T-328 系の L2 部分だけの解放」である。
- **`DW-O16` の 3 巡上限に達したため、残存 blocker 1 件を親が裁定して閉じた。** 参照 cell の検査は
  完全な grammar parser ではなく prefix + 逐語 `の全節` の検査であり、
  `` `docs/dev-wave/operations.md` 全文: `DW-O23` `` と `AGENTS.md 全文` が `findings=[]` で通る。
  **当初の所見 A1 より攻撃条件は狭まった** (節 ID を持たない bare path は拒否される) ため
  major へ落とし、{{T:dispatch-cell-grammar}} として起票した。**「条件性の意味を全部固定した」とは
  名乗れない。**
- **本 wave 以前から存在した欠陥を 1 件見つけて直した。** {{F:range-marker-over-expansion}} —
  wave 開始時点の `tools/check_docs.py:1791` は `re.search(r"[〜~]", between)` で range を判定しており、
  `` `DW-G01`（説明〜補足）, `DW-G05` `` のような注記や URL 内の `~` でも range 展開が起きて、
  実際には読んでいない中間節を読了済み edge として捏造できた。段 6 レンズ A が実測で発見した。
- **変異 matrix: baseline PASSED、12 変異中 SURVIVED 0、KILLED 8 / MISMATCH 4。**
  MISMATCH 4 件 (M04 / M07 / M08 / M09) は**期待 node が全件発火したうえで他 node も落ちた過剰決定**で、
  `DW-M03` に従い冗長 gate と明記して単独変異の単一理由の証拠から外した。
  **期待値を実測へ合わせる書き換えはしていない** (結果に合わせた事後調整になるため)。
  初回結果は `DW-M02` に従い erratum として台帳に残す。とくに M09 で `[self-reference]` が
  落ちたのは、段 6 焦点再レビューが「mask になる」と事前に予測したとおりである。
- **変異 spec の事前登録を段 6 の実測で 3 件訂正した。** M09 の期待 node から `[self-reference]` を
  外す (path→pair 束縛を除去しても段 8 の U map 不一致で赤くなるため単一理由でない)、
  M11 は `[malformed-heading]` のみ (fence / html-comment / raw-html は 1:1 の差を作らない)、
  M05 は未知 mode でなく空 cell `||` を使う (未知 mode は別の構造検査で赤くなる)。
- **段 5 の実装子と 3 巡の fix 子はいずれも pytest を実走できなかった** (sandbox から dispatch できず
  `qstat -Q preflight rc=1` / runner rc=16)。4 本とも「実装済み・未実走」と正しく申告し、
  緑を主張しなかった。**実走はすべて親が計算ノードで行った** — 191 failed → 3 failed → 357 passed。
  191 failed の原因は 2 系統 (条件 dispatch 表ヘッダの逐語 pin と synthetic fixture のずれが 187 件、
  `_grow_test_section()` が次の H2 を破壊していたのが 4 件) で、いずれも production の欠陥ではなかった。
- **親が自分の provenance 違反を 1 件作って直した。** merge commit で
  `model=claude-opus-5[1m]` を自分で `claude-opus-5-1m` へ slug 化した。表示名の自作 slug 化は
  禁止であり、正しくは `unknown` である。**amend で直したが、同日のユーザー裁定は
  「既に書いた分は rewrite しない」であり、この amend は裁定と外れた操作だった** (対象は未 push の
  自 branch tip 1 件のみ)。以降の commit はすべて `model=unknown` で書いた。
  正本は memory `provenance-model-unknown-after-model-switch`、規約条項は別 wave が起票済み。
- **full-history の provenance 赤 23 件は本 wave の所有ではなかった。** peer 通知で [T-682] と
  [T-139] が known-violation 登録を担当中と判明し、候補から降ろした ([T-664] の
  「候補は [T-594] の所有だった」と同型)。自 range (`--range`) の監査は各 commit で実施し、
  すべて違反なし。受入直前の取り込み後は full も rc=0 (known-violations=30) になった。
- **設計判断は {{D:dev-wave-layer-read-budget}} に記録した。**
- **受入要否の判定証拠 ([T-648] fallback 義務)**: 本 wave は実 repo を読むテストを直接変更している
  (`orchestrator/tests/test_check_docs.py` は実 checkout の `docs/` と `.claude/commands/` を読む)。
  したがって受入全走を実施した。**7682 passed / 20 skipped、rc=0** (1492.92 秒、request `897902`、
  測った checkout `9e3820c7` = local main `58d1878d` を含む land 対象 tip)。
  この受入値を記録する commit 自体は、その走行の対象に含まれない (値を書く前に測る順序のため)。
  受入 lease は 30 秒周期の待ち手で 60 回目 (約 30 分) に取得した。直前の holder は
  TTL 2398 秒で失効しており、[T-684] の FIFO 待ち行列が入るまでこの待ち方が最短である。
- **段 8 の改善候補は 1 件で、新 gate の下で「見送りで確定」になった。** `tools/mutation_harness.py` は
  spec を試験対象 checkout の**外**に要求し (`--spec` が checkout 内だと rc=2)、本 wave は
  これを知らずに 1 走を空振りさせた。手順として `DW-M05` へ 1 文足す価値があるが、
  同節は L1.5 (段 6 の無条件節) にあり、**L1.5 は本 wave が 9,566 bytes で凍結して余白ゼロ**である。
  L2 へは移せない (段 6 で無条件に読む手順であるため)。したがって [T-577] の既定どおり
  **見送りで確定**し、記録のみとする。**新 gate を入れた直後の最初の自己改善候補が、
  まさにその gate の凍結に当たった実例**である ([T-664] R5(a) の既定が 2 例目として機能した)。

## 次の一手差分

### 完了

- [T-313] byte 予算を層 scope の常時読量 gate へ置き換えた。集約 25,200 と file 別 cap 4 本を撤廃し、
  L1=10,625 / L1.5=9,566 / L2 単節=1,000 を置いた。層分類は入口 command の段 dispatch 表の
  U/C marker へ機械束縛した。`DW-CTX` を wave 開始行から、`DW-O04` を段 8 行から外す位置修正も行った。
  残余は {{T:dispatch-cell-grammar}} / {{T:l2-admission-control}} /
  {{T:dev-wave-read-scope-envelope}} / {{T:dev-wave-ctx-supervisor-wiring}} へ分離した。
  remaining: none
  base: 53d4d2c41f46c1aaa945f8a1f9b27dd5923d048c9384e9d4c7a1df50e884ea5c

### 更新

- [T-328] **P1・[T-313] 実装済み → 従属 4 件の行き先が実測で決まった**: 新 gate の下で書けるのは
  [T-279] A3 (`DW-O20` 489+154=643 bytes、L2) と、[T-317] A9 を `DW-O19` へ置く場合
  (602+147=749 bytes、L2) の 2 件だけである。[T-345] A7 (`DW-S03`、L1.5) と [T-346] A8
  (`DW-S01`、L1) は層上限に当たって書けない。L2 へ移すことを解決策として扱わない
  (発火段と読み動線が変わるため)。
  base: 2338b64839c8880d357f3fe86b93008cc248f1cefc771506ce0af53f43267137

### 新規

- {{T:dispatch-cell-grammar}} **P1・新規**: 入口 command の参照 cell を完全な grammar で full-match
  する parser にする。現在は prefix + 逐語 `の全節` の検査なので、
  `` `docs/dev-wave/operations.md` 全文: `DW-O23` `` と `AGENTS.md 全文` が通り、
  規範上の全冊読了を 1 節分としてしか計上しない。段 6 焦点再レビューが実測。
  `DW-O16` の 3 巡上限で本 wave では閉じなかった。
- {{T:l2-admission-control}} **P2・新規 (裁定要)**: 新規 L2 節の admission を決める。
  受理上限は `20,191 + 1,000N` で N に上限が無く、[T-577] の見送り候補も L2 として
  再登録すれば復活できる。択は (a) 現状 (literal pin + code review) で足りるとする、
  (b) routing 3 の 3 条件を新規登録側にも課す規範を `docs/decisions.md` (byte 上限なし) へ記録する、
  (c) 節数上限を置く。親推奨は (b)。
- {{T:dev-wave-read-scope-envelope}} **P3・新規 (裁定要)**: 本 gate の指標は
  `docs/dev-wave/**` leaf の **unique byte footprint** であって event 加重読量ではない
  (unique 10,625 に対し event 加重 12,670)。また L0 command 9,443 / self doc 5,997 /
  Codex skill 3,747 は scope 外で、「dev-wave 全層の常時読量 gate」とは呼べない。
  複合 envelope を作るか否かを決める。親推奨は「作らない」。
- {{T:dev-wave-ctx-supervisor-wiring}} **P3・新規**: 入口は外部 supervisor に
  最初の `claude -p` spawn 前の `DW-CTX` 読了を課すが、`tools/dev_waves/daemon.py` /
  `worker.py` に読取処理が無い。本 wave の位置修正は分類の重複除去であって、
  実読取の結線ではない。段 6 レンズ B が実測。
