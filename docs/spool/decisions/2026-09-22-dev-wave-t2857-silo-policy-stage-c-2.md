---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-22
wave: dev-wave-t2857-silo-policy-stage-c
seq: 2
---

## {{D:silo-policy-stage-c}}. silo-function-policy 軸の段階 C を、診断 driver の実走と型付き検査器で閉じる — 受理契約は仮引数名の省略を許す明確化だけを足し、焦点試験は YCSB と probe で到達を実測し、機構変異は赤の集合の完全一致と出口別の到達証拠で判定する

**決定:** D2214 の必須条件どおり、軸 `silo-function-policy` の段階 C (骨格 patch・api header・型付き構文検査・単独 TU compile・焦点試験・既存 3 負例の軸 ON 積み直し・機構の変異・UBSan harness 1 回・手書き方策の生死確認) を実装・実測した。記録の正本は `output/insights/2026-09-22/t2857-silo-policy-stage-c/README.md`、段 4・段 6 の裁定の逐語は同 dir の `verbatim/`。

1. **受理契約 policy-C++ v1 の明確化:** 全関数定義で仮引数名の省略を許す。`-Wextra -Werror` の unused-parameter は単独 TU compile と実 build の両方で掛かるので、使わない引数を名前つきで書く方策は build できない。型付き署名は D2214 決定 4 のまま変えない。
2. **焦点試験は YCSB の既存 workload + probe build + 焦点方策で到達を実測する。** 実 `TxExecutor` を直接呼ぶ専用 fixture は作らない。到達しない check は緑にせず「未到達」と数える。
3. **hook の実呼出しの検出は、焦点方策が各 hook の呼出し回数を他 hook の戻り値の下位 bit へ符号化し、probe が骨格側の独立計数と照合する形にする。** 符号の連動により、1 か所の解除で赤になる照合は 1 種とは限らない (abort 解除 {abort, lock, commit}、lock 解除 {abort, lock}、commit 解除 {commit})。各集合は互いに異なるので、判定は宣言した赤・緑の集合との完全一致とする。段 4 裁定の「その照合だけが赤」は誤りとして訂正した。
4. **機構変異の判定には、変異が壊す経路への到達の証拠を同構成の probe 走で要求する。** prefix unlock の変異は出口ごとに 1 枚ずつ (action-abort 出口 × `abort0`、上限出口 × `retry`) とし、それぞれ prefix を保持したままの到達 > 0 を同方策・同 workload の probe 走で確かめる。到達の証拠は別走のものであり、変異走そのものの到達ではないと結果に書く。
5. **C 段の診断 driver は既存 coverage driver と同じ経路をとる。** condition gate は 1 回に macro 1 個で companion を混ぜず、cache 経路の前提 flag は configure 引数で渡す。最初の gate の前に gate なしの依存物準備 build を 1 回行う (masstree の `config.h` は build 時に生成される)。診断 build は NON_ADMISSIBLE で、生死確認は `pipeline.evaluate` を使わず certified 候補と称さない。E 段の build admission 写像 (設計 §4) は変えない。

**理由:**
- 1: 省略を許さないと、合法な方策が実 build で落ち、受理契約と実 build の受理集合が食い違う。署名の型は変えないので、D2214 の封じ込めは弱まらない。
- 2: YCSB の既存 legacy workload (200 records / 4 threads / skew 0.9 / RMW / 1 秒) で、retry 後の取得成功・上限 abort・成功後の状態継続・要因記録のすべてに到達した (coverage で到達数 > 0 を実測)。専用 fixture は初期化・link の構成が未確認で、新しい test framework になる (DW-G05)。
- 3: 赤の集合の完全一致なら、赤が多すぎても少なすぎても不合格になり、どの hook が外れたかを一意に識別できる。
- 4: 両出口を同時に壊す変異や、到達しない方策 (`maxwait` は上限出口にほぼ届かない) の変異は、検出したように見えても対象の unlock の実行機会を示さない (F247 の型)。
- 5: 既存 driver が実機で通っている形に揃えることで、実走ごとに 1 件ずつ欠陥が出る往復 (F139 の型) を断つ。

**却下した選択肢:**
- 実 `TxExecutor` を呼ぶ専用 C++ fixture で焦点試験を決定的にする — 構成が未確認の新 framework。YCSB で到達を実測できた。
- 生死確認を `pipeline.evaluate` + 認可 + campaign layout + GeneratorId で行う — C 段の診断のために登録簿と layout を増やす。E 段の仕事である。
- hook 変異ごとに照合を 1 種だけにする符号化 — 戻り値 1 個に複数の回数を載せる以上、固定値への置換は複数の符号を同時に消す。完全一致の判定で足りる。
- prefix unlock の変異を 1 枚のまま方策だけで出口を分ける — CAS 失敗の連続で `abort0` でも上限出口に届きうるので、出口の独立性が言えない。
