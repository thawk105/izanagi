---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-23
wave: dev-wave-real-silo-fixture
seq: 2
---

## 新規

### {{F:derived-value-pin-is-not-generator-gate}}. 別経路で再計算される派生値を pin して「生成器を検査した」と裁定した (near miss) [恒真ゲート] [テスト代表性]

- 事象: 実データ fixture の検出力を上げるため、親が段 4 で「辺の型組合せ別の `(src,dst)` 組数を
  exact に固定すれば、ww 辺の生成を止める回帰を撃てる」と裁定した。段 6 の焦点再レビューが
  NO-GO を返し、この pin が ww 生成器を一切検査していないと指摘した。**land 前に捕まえたので
  実害は無い。**
- 根本原因: pin が読む値が、検査したい生成器とは**別経路で再計算される派生値**だった。
  `DSG.adj` は型を持たない `(src,dst)` の set で、型は `DSG._reasons()` が版列と write-set から
  後から再構成する。したがって `_add_ww_edges()` が辺を追加したかどうかと型の再構成は独立である。
  さらにこの fixture では ww の 2,996 組がすべて wr の組に重なるため、ww 生成器を止めても
  `adj`・辺総数・型組合せ・verdict のどれも変わらない (等価変異)。親は
  「型別に固定すれば型別の脱落を撃てる」という素朴な対応関係を確認せずに裁定していた。
- 恒久対応: 規律は `docs/dev-wave/mutation.md` の `DW-M01` (事前登録時に「無効化時の赤理由が
  一つに絞れることをコードで確認する」) が既に要求している。本件はその派生値版であり、
  **pin 対象が別経路で再計算される値でないかを、生成器まで辿って確認する**ことを同節の
  適用範囲に含める。docs への明文化は L1.5 集約予算 (9,566 bytes) が満杯のため
  {{T:devwave-mutation-docs-budget}} で裁定待ち。あわせて
  `orchestrator/tests/fixtures/README.md` に「型組合せ別の pin は rw 側の脱落は撃つが
  ww 生成器の脱落は撃たない」と限界を明記した (誇張の撤回)。
- 再発検知: **同じ変異を無条件版と条件版の対で事前登録する。** 本 wave では
  無条件の ww 停止が手製 fixture 4 node に KILLED、規模条件付きが SURVIVED となり、
  pin の射程が機械で露出した。片方だけを登録すると、この差は見えない。

## 再発

### F273

- **再発: 2026-08-23** — 受入全走 attempt 4 (tested tip 414dc1e1) が 8 failed で戻り、
  失敗 node は全件 `orchestrator/tests/test_codex_worker_launch.py` だった。
  失敗の中身は `stop_reason='wall_clock_admission_bound_s'` で、
  `codex_exit_code=0` / `validator_rc=0` / `termination_verified=True` と launcher の時間切れである。
  本 wave の差分 (verifier の trace fixture とテスト、docs) からこのファイルへの到達経路は無い。
  台帳の再発検知どおり実測した — 並行 launcher は 1 本、login node の load average は 15.99、
  同ファイルの単独走 (`--force-dispatch`) は **170 passed / 7.11 秒 / rc=0** で緑。
  よって実装差分へ帰属させない。
