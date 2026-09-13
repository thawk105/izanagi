---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: dev-wave-t758-docs-corrections
seq: 1
title: [T-758] 既存 docs の誤り 3 件を現物で裏取りして訂正した (docs のみ、branch worktree-dev-wave-t758-docs-corrections)
---

## 本文

- 3 件とも 2026-08-10 の指摘に頼らず、`external/ccbench` の現物と `orchestrator/campaign/genome.py`
  から独立に数え直してから直した。逐語と根拠は
  `output/insights/2026-09-14/t758-docs-corrections.md`。
- **carry の字面は一次資料と 1 か所ずれていた。** carry と一次資料 V3 は「mocc の自由軸は 2 つ」だが、
  V3 の 2 つは protocol 固有 option だけの数で、全 protocol 共通の `BACK_OFF` を含めていない。
  同じ insight の s2-plan と `MOCC_SPACE` の実装はどちらも 3 軸である。anatomy の探索空間の列は
  他 protocol でも `BACK_OFF` を数えている (ermia 4 = `KEY_SORT` × `BACK_OFF`) ため、
  doc へ書いた数は 2^3=8 とした。carry の数字をそのまま写していたら誤りを別の誤りに置き換えていた。
- **自分の探索でも一度同じ型の誤りを踏んだ。** `grep ... | head -20` で ccbench を数えて
  `KEY_SORT` の live site を取り逃し、死にフラグと誤判定した。切らずに数え直して是正した。
- 子エージェントは起動していない (docs のみ・実装面の差分ゼロ)。DW-S04 により変異 matrix は免除、
  受入全走は実施した。
- **受入の経過。** 初回 (tested_main 75bea8e5f) は 23310 passed / 68 skipped で完全緑 (verdict
  child-green) だったが、land が 2 手で止まった — 1 手目の rc=29 は provenance 違反ではなく
  「監査中に main/wave head が動いた」、2 手目が `stale-main` で、並行 wave が先に main を
  abbef52d5 へ進めた。この wave の進行中に local main は 75bea8e5f → abbef52d5 → 30efab0c4 →
  12fbe0919 と前進しており、受入全走が 20 分以上かかる一方で受領証は tested_main を束縛するため、
  取り込むたびに受入をやり直す形では追いつかない。以後は D987 に従い、受入後に clean な
  forward-main merge を足して同じ受領証で land し直す形へ切り替えた (runner blob は tested_main と
  新 main で同一であることを毎回確認する)。
- **やり直した受入で踏んだ赤はすべて非帰属と判定した (DW-O18)。** 観測した赤は
  `test_t1259_qsub_env_delivery_probe.py` の setup error 群、
  `test_env_contract_activation.py::test_historical_calibration_is_verified_only_when_resolved_in_source_stage[modified]`、
  `test_pegasus_floor_tools.py::test_floor_checkpoint_filesystem_hang_has_a_wall_clock_bound[write]` で、
  **走行ごとに別の test が落ちている。** 判定根拠は 4 つ。(i) merged main に対する本 wave の変更面は
  docs 4 file だけで、落ちた test file はどれもそれを参照しない (path 検索で hit 0)。(ii) 同じ wave
  tip と旧 main の組では赤 0 だった。(iii) 落ちた test を単独再走すると毎回 rc=0 で全件が非再現
  (7 件で 53 passed、floor の 1 件で 3 passed)。(iv) 赤の本文が時間依存である —
  floor の 1 件は `diagnostic timeout did not interrupt the syscall` で、5 秒 sleep を診断 timeout が
  中断できるかを見る test であり、96 core のログインノードで load average 88〜133 のときに落ちる。
  テストの弱体化・deselect・flaky hold 登録はしていない。
- **自分の作りの誤り。** 受入と land を連結した script が「赤なら受入をやり直す」を自動でやる形に
  なっており、DW-O18 が要求する「赤ごとに帰属判定を下してから再走する」順序を script が飛ばして
  いた。判定は親が下すものなので、走行を止めて判定し直し、記録をこの形へ書き換えた。判定を
  script に委ねると、帰属する赤も同じ経路で再走に流れてしまう。
- 設計択一は生じなかったため decisions への追記はない。

## 次の一手差分

### 完了

- [T-758] 3 件を現物で裏取りして訂正した。ermia は active な `ssn_parallel_commit()` が raw cstamp を
  書くので si の写像がそのまま流用でき、`cstamp<<1` は呼ばれない `ssn_commit()` と sstamp 側だけである。
  mocc の探索空間は 2^3=8 (`RWLOCK` は bare define で軸に数えない)。trace-hook は silo と si の
  2 protocol に既存で、si は 2026-06-19 追加である。
  remaining: none
  base: 8c6fb83ae0fc52fc6b76f3934056b98e4ee3793860698ec5b5686055a22cf39f

### 新規

- {{T:anatomy-search-space-tictoc-cicada}} **P2・新規**: anatomy の探索空間サイズのうち tictoc
  (doc 2^4=16 / `TICTOC_SPACE` は 5 軸) と cicada (doc 2^6=64 / `CICADA_SPACE` は 5 軸) の項を
  現物で数え直して訂正する。あわせて `orchestrator/campaign/genome.py` の module docstring が
  引く旧合計 (≈ 258 binaries) を直す — こちらは実装面なので Codex author が要る。
  T-758 は 3 件を名指しした課題だったため本 wave では触らず、doc 側へ未検証と明記して送った。
