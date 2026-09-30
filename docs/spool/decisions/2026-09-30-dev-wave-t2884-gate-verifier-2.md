---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-30
wave: dev-wave-t2884-gate-verifier
seq: 2
---

## {{D:gate-witness-verifier-v2}}. 判定器の意味の版を 2 に上げ、手順列・刻印の照合は gate file の在否と呼び出し側の要求で起動する

**決定:**

1. **記録の形:** CCBench の trace build は、判定器の trace parser が読まない別 file `gate_<thid>.log` に、手順列 `Q` (commit した取引の R/W/M と key・観測刻印・書いた刻印) と据えた値の刻印 `V` を書く。設計資料 (`output/insights/2026-09-29/gen-opt-correctness-gate/README.md`) の「`A` 行」は abort 要因の tag と衝突するので使わない。刻印は `YCSB::id_` の 64 bit (書き手 = `((thid+1)<<48) | 通し番号`、初期 load は key id)。手順列を出すのは Silo の YCSB 経路の commit が txid を渡した thread だけで、他 protocol の trace build は gate file を作らない。置き場は CCBench の local branch `izanagi-gate-witness-trace` (F `25898d00` の子、D16 の trace 計装)。gitlink は動かさない。
2. **判定器の意味の版:** 本決定より前の `orchestrator/verifier/` を意味の版 1、gate の照合 (D1 手順列と trace の key 集合、D2a 読んだ版と値、D2b 取引内の値を全 key、D5 emitter の証拠面) を足したものを意味の版 2 とし、定数 `MEANING_VERSION = 2` を gate の照合が有効な判定結果に載せる。
3. **起動の仕方:** gate の照合は、trace dir に gate namespace の file が 1 つでも在るか、呼び出し側が `require_gate_witness=True` を渡したときに有効になる。有効なら照合の入力が欠ける・読めない・食い違う場合は certified にしない。要求しない呼び出しで gate file が無ければ、判定は版 1 と同一 (結果の投影も同一)。D5 (Q・V の emitter と txid の受け渡しが literal な `#if TRACE` 内に在り、Silo の YCSB 翻訳単位が同じ `include/ycsb.hh` を include する) は要求時だけ certified の条件にする。
4. **再検証の発火条件 (結果の前に `output/insights/2026-09-30/gen-opt-gate-verifier/prereg.md` として commit 済み):** 版 1 の判定は再判定も昇格もしない。版 2 で読み直す対象は gate file を持つ trace に限る。gen-opt の候補の certified は版 2 以上・要求あり・D5 成立・D1/D2a/D2b の違反 0 をすべて要する。版が上がるたびに、それより前の版の記録は昇格させず、新しい版を要する主張は保持した trace と gate の archive から読み直す。

**理由:**

- U0 の実測で、今の判定器は読みを読み集合に載せない壊れた Silo を certified にしていた。手順列と trace の突き合わせ (D1) だけがそれを赤にする。本決定の実装で、同じ壊しが D1(b1) で赤になり違反取引数が壊しの発火数と完全に一致し、Silo 修正を当てた stock は D1・D2 とも 0 件で certified になることを計算ノードで確かめた。
- 既定を「要求なし」にしたのは、生成器対照 (pin C 固定で本走中) を含む現行の campaign の trace が gate file を持たず、要求を既定にすると全部 indeterminate になるためである。gate file が在れば要求の有無に依らず照合するので、U1 を含む pin に進んだ後は Silo の trace は常に照合される。
- 意味の版を結果全体でなく gate の節にだけ載せるのは、gate の無い既存の判定の投影と receipt の入力を 1 byte も変えないためである。

**却下した選択肢:**

- **要求の keyword を既定値なしにする (D422 の型)** — 呼び出し約 120 箇所 (大半は test) を変える割に、要求を渡すべき gen-opt の呼び出し元がまだ無く、効果を確かめられない。gen-opt の driver を繋ぐ wave が `True` を渡す義務を負う。
- **D5 を既存の証拠面 (X/P) と同じく Silo で常に要求する** — pin C の全 campaign が indeterminate になる。
- **D2b を stock に合わせて「最初の書き」と照合する** — 標準より弱い意味を正と固定し、取引内の書きの消失を見逃す (設計資料 §3.2・§3.5)。
- **capability 経路・build の source snapshot に今 D5 を束縛する** — 今回の受理集合を変えずに互換面だけが増える。gen-opt の driver の接続と同時に行う。
