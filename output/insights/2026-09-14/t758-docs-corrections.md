# [T-758] 既存 docs の誤り 3 件 — 現物での裏取りと訂正

- authority: none
- default_effect: no-state-change
- 作成: 2026-09-14
- 基準: main 75bea8e5fe918e7ec9fd18c10cd0dadcf474c51a、submodule `external/ccbench` = 511c9538
- branch: worktree-dev-wave-t758-docs-corrections
- 還元判断: CCBench 側の不具合ではない (izanagi の docs の読み取り誤り) ため、上流への還元対象としない

## 何を直したか

2026-08-10 の `output/insights/2026-08-10/s1-design-choice/README.md` が副産物として挙げた
「既存 docs の誤り 3 件」を、当時の指摘に頼らず現物から独立に数え直して訂正した。

### 1. ermia の版 ID は raw cstamp (`docs/ccbench-anatomy.md` の「S1 の既知の罠」)

**旧記述:** ermia は版 cstamp が `cstamp<<1` で、写像をこの 1 ビットシフトに合わせないと
全 read が orphan 化する。si の trace-hook はそのままでは流用不可。

**現物:**

- `cc/ermia/transaction.cc` の `TxExecutor::commit()` が呼ぶ commit 経路は
  `ssn_parallel_commit()` **だけ**である。`ssn_commit()` は宣言 (`include/transaction.hh`) と
  定義があるが、`*.cc` / `*.hh` 全体を探して呼び出しが 1 つも無い。
- 生きている `ssn_parallel_commit()` は committed 版へ `ver_->cstamp_.store(this->cstamp_)` と
  **raw** を書く。`<< TIDFLAG` を掛けるのは sstamp (`verSstamp`) だけである。
- 読み側の可視版選択 (`read_internal`) も raw の `txid_` と raw の `ver_->cstamp_` を比べる。
  版 cstamp がシフト済みなら、この比較自体が成立しない。
- `cstamp<<1` を版 cstamp へ書くのは、呼ばれない `ssn_commit()` の中だけである。
- si (`cc/si/transaction.cc`) も `ver_->cstamp_.store(this->cstamp_)` と raw を書く。
  よって si の `(epoch=1, tid=cstamp)` 写像はそのまま ermia へ流用できる。

**なぜ危ないか:** 旧記述は「S1 着手時の必須知識」として書かれていた。従うと版 ID を
1 ビットずらして写像し、読んだ版が実物と一致せず全 read が orphan 化する。
つまり警告が指す結果を、警告に従うことで招く向きに反転していた。

### 2. mocc の探索空間は 2^3=8 (`docs/ccbench-anatomy.md` の「探索空間サイズ」)

**旧記述:** mocc 2^4=16、合計 ≈258。

**現物:** `cc/mocc/CMakeLists.txt` の OPTIONS は `RWLOCK`、`TEMPERATURE_RESET_OPT`、
`KEY_SORT`、`INSERT_READ_DELAY_MS`、`INSERT_BATCH_DELAY_MS`。ここに
全 protocol 共通の `BACK_OFF` (`cmake/Options.cmake`) が加わる。

- `TEMPERATURE_RESET_OPT` は生きた分岐 (`cc/mocc/transaction.cc`、`cc/mocc/util.cc`)
- `KEY_SORT` は生きた分岐。ただし live site は `include/ycsb.hh` の 1 箇所だけで、
  `ycsb_mocc.cc` はその root の header を include する (mocc 自前の include には無い)。
  よって 8 通りという数は YCSB workload での数である
- `BACK_OFF` は `cc/mocc/transaction.cc` に 2 箇所
- `RWLOCK` は CMakeLists の bare define で cache option から off にできない。
  anatomy 自身の相互排他節がそう書いており、ss2pl の `DLR1` は同じ理由で数から外れている。
  mocc だけ `RWLOCK` を数えて 2^4 にしていたのが食い違いの原因
- `INSERT_*_DELAY_MS` は計測撹乱ノブなので最適化軸ではない

→ 自由軸は 3、探索空間は 2^3=8。`orchestrator/campaign/genome.py` の `MOCC_SPACE` は
既にこの 3 軸 8 通りで実装されており、doc だけが取り残されていた。

**carry の字面との差:** worklog の carry は「mocc の自由軸は 2 つ」と書く。一次資料の V3 も
「2 つ (`TEMPERATURE_RESET_OPT`, `KEY_SORT`)」だが、これは protocol 固有 option だけの数で、
全 protocol 共通の `BACK_OFF` を含めていない。同じ insight の s2-plan は「3 つ」と書いており、
実装も 3 軸である。探索空間サイズの列は他 protocol でも `BACK_OFF` を数えている
(ermia 4 = `KEY_SORT` × `BACK_OFF`) ので、doc に書くべき数は 2^3=8 である。

### 3. trace-hook は silo と si の 2 protocol に既存 (`docs/phase3.md` must 表 S1 行)

**旧記述:** 「silo 内に閉じる現行 S-1/8b/層3には不要。trace-hook の無い protocol は verify 不能」。
si に trace-hook が既にある事実が落ちていた。

**現物:** `cc/` 以下で `TRACE` を含む protocol source は `cc/silo/transaction.cc` と
`cc/si/transaction.cc` の 2 件だけである。si の口は 2026-06-19 の commit
`fee622f0 feat: si (Snapshot Isolation) に検証用トレース口を追加` で入っており、
`#if TRACE` 枝が C (commit)・R (read)・W (write) を `(epoch=1, tid=cstamp)` で出す完全な口である。
T-758 起票 (2026-08-10) より前から存在していた。

## 本 wave では直さなかった食い違い (新規起票)

同じ「探索空間サイズ」の列を `orchestrator/campaign/genome.py` の登録軸と突き合わせると、
mocc 以外にも食い違いがある。

| protocol | doc | genome.py の登録軸 |
|---|---|---|
| silo | 2^4=16 | 4 軸 (生 16、no-wait XOR で有効 8) — 一致 |
| mocc | 2^3=8 (本 wave で訂正) | 3 軸 8 通り — 一致 |
| tictoc | 2^4=16 | 5 軸 (生 32、制約後 24) — 食い違い |
| cicada | 2^6=64 | 5 軸 (生 32、制約後 24) — 食い違い |

T-758 は 3 件を名指しした課題なので、tictoc・cicada は本 wave では触らず、doc 側に
「未検証のまま残す」と明記して次の一手へ起票した。あわせて `orchestrator/campaign/genome.py`
の module docstring が旧合計「≈ 258 binaries」を引いているが、これは実装面なので親は
編集できず (Codex author が必要)、同じ起票に含めた。

## 次に読む人への注意

- anatomy の「探索空間サイズ」の合計値は、列挙した項の単純和である。項を直したら和も直る。
- guard_bash は `$()` などの不透明構文と `external/ccbench` の path の同居を拒否する。
  ccbench の現物を読むときは素の `cat` / `grep` を使う。
- `grep ... | head -20` で ccbench を数えると件数が切れて「死にフラグ」と誤判定する。
  本件でも一度 `KEY_SORT` を死にフラグと誤読し、切らずに数え直して是正した。
