# 発見: silo 両 no-wait=0 は validation の競合分岐が空になり無限スピン (livelock) する

- **発見日:** 2026-06-22 (Phase 2 P2-2 着手, env=linux-baremetal)
- **種別:** CCBench `silo` の**ビルド構成の縮退** (フラグの組合せが不正なコードを生む)
- **重大度:** 中 (探索空間に残すと measurable でない genome が混ざる。genome 列挙の制約で除外する)
- **還元判断:** 上流 PR は任意 (後述「上流への含意」)。Izanagi 側は genome.py の制約で対処済み

## 観測 (P2-0 の trace timeout が perf build でも再現)

P2-0 (verifier 大規模 sanity) で `NO_WAIT_LOCKING_IN_VALIDATION=0` かつ `NO_WAIT_OF_TICTOC=0`
(以下 **両 no-wait=0**) の 4 genome が trace 取得で timeout し、sanity から除外していた
(構成病理か trace I/O 特有か未確定)。P2-2 (実 fitness 全探索) の初手として **perf build (trace-disabled)**
で再確認したところ、**perf build でも同じく hang** することを確認した:

| binary | workload | thread | records | 結果 |
|---|---|---|---|---|
| 両 no-wait=0 (perf) | skew0.9 rratio50 | 48 | 1,000,000 | **90s timeout (hang)** |
| 両 no-wait=0 (perf) | uniform rratio50 | 48 | 100,000 | **30s timeout, 出力ゼロ** |
| 両 no-wait=0 (perf) | uniform rratio50 | **4** | 10,000 | **30s timeout, 出力ゼロ** |
| 両 no-wait=0 (perf) | uniform rratio50 | **1** | 10,000 | **完走 129,272 tps, abort 0.0000** |
| 対照: NWT=1 (perf) | uniform rratio50 | 4 | 10,000 | 完走 412,931 tps |

- **workload・スケール非依存** (uniform/thread4/10k でも hang)。trace I/O は無関係 (perf build で再現)。
- **thread=1 だけ完走** (abort 0)。**thread≥2 で必ず hang。** → 競合が起きると詰まる。

## 機構 (ソース確認 — `cc/silo/transaction.cc:145-178` `lockWriteSet()`)

write set の各タプルの tidword を**ループ前に 1 回だけ**読み (`expected`)、`for(;;)` で lock 取得を試みる:

```cpp
expected.obj_ = loadAcquire((*itr).rcdptr_->tidword_.obj_);   // 1 回だけ
for (;;) {
  if (expected.lock) {                 // 既に他者がロック保持
#if NO_WAIT_LOCKING_IN_VALIDATION
    this->status_ = aborted; ... return;        // 競合 → 即 abort (TicToc 由来)
#elif NO_WAIT_OF_TICTOC
    unlockWriteSet(itr); goto retry;            // 自分のロックを解放して全体 retry
#endif
  } else {                             // 空いている
    desired = expected; desired.lock = 1;
    if (compareExchange(... expected.obj_, desired.obj_)) break;   // CAS 成功で次へ
  }
}
```

**両 no-wait=0 のとき `#if`/`#elif` のどちらも展開されず、`if (expected.lock)` の分岐が空になる。**
他スレッドが同じタプルをロック保持していると:

1. `expected.lock` が真 → **空分岐** → 何もせずループ先頭へ戻る
2. `expected` は**再読み込みされない** (ループ前で固定) → 永遠に `expected.lock==真` のまま
3. → **無限スピン (busy livelock)**。相手がロックを解放しても観測できない

CAS 失敗経路も同様に縮退する (失敗時 `expected` を更新せずループするため、値が変わると CAS が
永久に失敗し続ける)。**`#else` 句が無い**ため、両 no-wait=0 は「待ちロック方式の正規 CC」ではなく
**競合処理が抜け落ちた不正コンパイル**になる。thread=1 では write set が決して競合せず
(`expected.lock` が常に偽・CAS が一発成功) 完走するのが、上表 thread=1 だけ通る理由。

## 含意 → silo の有効遺伝子空間は 12 ではなく 8 (XOR)

`(NO_WAIT_LOCKING_IN_VALIDATION, NO_WAIT_OF_TICTOC)` の 4 組合せの素性:

| 組 | 挙動 | 採否 |
|---|---|---|
| (1,0) | 競合で即 abort (no-wait locking) | **有効** |
| (0,1) | 競合で解放→retry (TicToc no-wait) | **有効** |
| (1,1) | `#if` だけ生き `#elif` は dead code → (1,0) と挙動同一 | 冗長 → 除外 (旧来の相互排他制約) |
| (0,0) | 競合分岐が空 → 無限スピン | **不正 → 除外 (本発見)** |

→ 有効なのは**ちょうど一方が 1 (XOR)** の 2 組のみ。silo の live 最適化空間は
`BACK_OFF[2] × WAL[2] × {(1,0),(0,1)}[2] = 8 genome`。これまで docs に書いてきた「silo 12」は
相互排他 (両 1) だけを除いた生の数で、**縮退 (両 0) を含んでいた**。実探索可能なのは 8。

**対処 (実装済み):** `orchestrator/campaign/genome.py` の制約を「両 1 を禁止」から
**「ちょうど一方が 1 (XOR)」**に強化。これで `enumerate()` は最初から 8 genome を返し、
両 0 が探索に混ざらない。P2-0 の `sanity_silo._trace_evaluable` (両 0 を手で弾く回避策) も不要になる。

## 上流への含意 (還元判断: 任意・ユーザー確認)

CCBench 本体としては、両 no-wait=0 は「どちらの最適化も選ばない素の silo validation」を
意図した構成でありうる。その場合 `#if/#elif` に **`#else` で待ちロック (busy-wait で再読み込み、
あるいは正規の lock-wait)** を補うのが正しい。現状は `#else` 欠落で無限スピンに縮退する。
ただしこれは Izanagi の探索には不要 (XOR 除外で足りる) なので、**上流 PR は出さず insight に留める**
(CLAUDE.md「勝手に上流へ PR を出さない」)。修正するなら別 issue として人間が判断する。
