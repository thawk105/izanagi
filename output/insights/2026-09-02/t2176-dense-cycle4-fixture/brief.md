# 段 1 brief — [T-2176] 密な txid の手製 fixture と長さ 4 巡回の clean 負例

対象 repo (worktree): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture`
起点 main: `24b31d2a37353d63a4f715ed2170d13e25df3fe3`

## scope (純増だけ)

足すのは 4 つ。(1) `orchestrator/tests/fixtures/` に密な txid の手製 fixture 1 個。
(2) `orchestrator/tests/test_verifier.py` にその負例テスト。(3) 新 fixture の trace file を同 file の
在庫 `_V2_FIXTURE_FILES` へ登録。(4) `orchestrator/tests/fixtures/README.md` の表へ 1 行 (親が編集)。
足さないもの: `orchestrator/verifier/` の production 変更 (差分 0 が目標)、gate・検査・台帳・一般化の新設、
byte 級 hash pin。T-2177 (r5 と D799 の射程の訂正) は別 task で、本 wave では触らない。

## 確定済みユーザー裁定

D1455 (逐語 `refs/d1455.md`)。密な txid の手製 fixture を足し、clean な入力で長さ 4 以上の巡回を
捕まえる負例を張る。実装面は Codex `role=author`。新負例が実際に certified 判定を落とすことを
変異の KILLED で示し、恒真な assert にしない。絶対規律 2 を緩めない。

## 親の実測 (現物、上記 HEAD)

- 全 18 fixture を `verify_trace_dir` に通した。長さ 4 の anomaly を持つのは `r5_nonlatest_transitive`
  だけで `integrity.clean()=False` (`missing_txids=46`)。clean な fixture の最長巡回は `r3_cycle3` の 3。
  D1455 の前提は現物で成立する。
- 生死確認 (DW-G01): 4 txn・txid 0..3 密・rw 1 本の trace を repo 外 tmp に作って verify したところ
  `verdict=non-serializable` / `certified=False` / `clean=True` / anomaly `G2` len=4 / cycle=[0,1,2,3]。
  **狙う形は実在する。**
- 同 trace に「長さ 4 以上の anomaly を落とす」変異を当てると `verdict=serializable` `certified=True` へ
  倒れた。同じ変異で r5 は `indeterminate` 止まり、r1/r3/r8 は無影響。新負例だけが certified 経路を殺す。
- **模擬と実の差:** 上の変異は親 probe の `DSG.anomalies` monkeypatch = 模擬。帰属は段 6 の
  `tools/mutation_harness.py` が `orchestrator/verifier/dsg.py` の source を変異させて確定する。

## 不変条件

- 新 fixture の integrity は完全に clean (missing_txids=0・version mismatch 0・framing violation 0・
  orphan read 0・malformed key 0・genesis commit 0)。
- 巡回はちょうど 1 本、長さ 4 以上。長さ 3 以下の巡回を含めてはならない (含むと変異が素通りし負例が恒真化する)。
- realizable であること。rw 辺を 1 本以上含み、rw 以外の辺は commit 順方向 (fixtures README「なぜ赤
  フィクスチャが全部 G2 か」の構造的事実に反しない)。
- 負例は `certified` を直接 assert する。`serializable` 単独を通過扱いにしない (model.py の警告どおり)。
- production コード (`orchestrator/verifier/*.py`) を変更しない。要ると判明したら段 4 へ戻す。

## 成果物の形

fixture dir 1 個と `trace_<thid>.log` (形式は `include/trace.hh` / `parse.py` docstring と一致)。
test_verifier.py の新テストは最低限 (a) clean かつ non-serializable かつ `certified=False`、
(b) anomaly が G2 で length>=4、(c) 長さ 3 以下の巡回が無いこと、(d) 在庫登録、を担う。

## (P1) 親の provisional 裁定・攻撃対象

- (P1-1) fixture 名は `r9_dense_cycle4`。既存命名 (`r` = 赤) に従う。
- (P1-2) 4 本目の rw 辺を genesis 読み (`R <txid> <key> 1 0`) で作る。producer 不在かつ `rv == GENESIS`
  なので orphan にならない、という parse/dsg の規則に依存する。実版 producer を置く設計に替えるべきか。
- (P1-3) 4 txn を 1 file (`trace_0.log`) に置く。複数 thread file へ割る必要は無いと判断した。
- (P1-4) fixtures README の「長さ 4 以上の巡回を無視する (どの fixture も担っていない)」は本 wave の
  追加で偽になるため、新 fixture を名指す形へ直す。r5 と D799 の射程 (T-2177) には触れない。
- (P1-5) 巡回長はちょうど 4 にする。5 以上にしない。

## 並列分割

段 2 = plan 子 1 本。段 3 = 敵対相談 2 本 (レンズ A: 負例の恒真化と realizability / レンズ B: 在庫 pin 閉包と
scope 越境)。段 5 = 実装子 1 本 (編集面が fixture + test_verifier.py の 1 単位で分割不能)。
段 6 = 敵対レビュー 2 本、必要なら fix 1 本。
