---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-26
wave: worktree-t2849-mocc-insertion
seq: 2
---

## {{D:mocc-slot-campaign-pin-c}}. 比較 harness の MOCC は protocol 引数で差し込み、MOCC の slot だけ campaign pin を X/P 計装のある C に移す。動作点は pin C の較正 3 件 (records は silo と同じ 1,000,000) で、意味検査は build する protocol の翻訳単位で行う

**決定:** D2220 項 6 の S2 (MOCC の差し込み口) を次の形で実装した。insight `output/insights/2026-09-26/t2849-mocc-insertion/README.md`。

1. **選択の口。** protocol は silo (既定) と mocc の 2 値だけ。単回評価 (`p3_s4_loop --protocol`)・系列制御 (`t2849_comparison_harness run-series / run-block-controls --protocol`)・job body (`IZANAGI_S4_T2849_PROTOCOL`) に通す。silo 既定では argv・search_config・genome・header・呼出しの形を変えない。mocc は silo と別の cohort 名・cohort root で走らせる運用とし、混在の拒否検査・aggregate の protocol キー化は足さない。
2. **MOCC の genome。** stock = `BACK_OFF=1, KEY_SORT=0, TEMPERATURE_RESET_OPT=1, BACKOFF_FIXED=-1`、候補 = 同 flags + `BACKOFF_FIXED=<v>` と、silo と同じ hole (`include/backoff.hh` の合成枝を `double now_backoff = <v>;`、template patch `patches/silo-backoff-fixed.patch`)。hole の marker 名 `silo-backoff-magnitude` は改名しない。参照 genome は silo 専用のまま。MOCC の block 対照は stock だけで、参照値は null。
3. **動作点。** pin C で MOCC の認定較正 record を rr5・rr50・rr95 の 3 件取り、いずれも records = 1,000,000 (D15 の下限基準) で S1 と同値だった。`calibrated_perf` の値は変えず、出典の record を記す。D2150 項 1 (iv) により旧 pin の MOCC record は旧 pin の取得事実として残す。
4. **campaign pin。** `p3_s4_loop.PIN` (D1936 項 1、511c9538) は silo の campaign pin のまま据え置き、MOCC の slot だけ C (`68106660686232781bca3be792a750d3e19d7a8a`) を使う。C は literal で持ち、gitlink・`pin.CURRENT_PIN`・`CCBENCH_FULL_SHA` から導出しない。job body の照合も harness mode の MOCC のときだけ C に切り替える。
5. **意味検査。** `BACKOFF_FIXED` の意味検査を、mocc の評価では owner `cc/mocc/transaction.cc`・target `ycsb_mocc.exe` で行う。検査の条件は変えない。
6. **K0 LLM。** 巡 tool の coder 文脈は mocc のとき固定 flags・動作点・背景節を MOCC のものにする。役割定義・`src/coder-leakproof-context.md`・role adapter・出力 schema は変えない。

**理由:**
- pin C への前進 (D2227 項 1・D2236) は D2150 項 1 の ①④⑦ に限られ、driver の campaign pin は「③ 移行する driver は各新系列の着手時」に委ねられていた。D2227 項 1 は C を承認する理由に S2 の X/P 前提を挙げている。511c9538 の mocc には X/P 計装が無く、現行 verifier は旧 pin の mocc trace を certified にできない (D2236)。MOCC の slot を C に移すのはこの範囲の driver 移行で、silo は [T-2850] 試走 (D2245 が 511c9538 に固定) と合わせて動かさない。
- 意味検査の `BACKOFF_FIXED` spec は silo の翻訳単位に固定されていて、MOCC を build しても silo の証拠で通っていた。MOCC 候補が適応 backoff のまま走っても値 <v> の候補として台帳に載りうる。
- 計算ノードで系列 1 本 (開始 stock・初期点 5 / 10 µs・探索 1・endpoint) の 5 slot と block 対照 1 slot が certified・品質 normal・anomaly 0 で通り、値ごとに throughput が変わった (literal の実効)。変異 12 本は final で全件 KILLED。

**却下した選択肢:**
- `p3_s4_loop.PIN` 自体を C へ進める — silo の S1 と [T-2850] 試走の登録 (511c9538) を動かす。
- MOCC の campaign pin を gitlink から導出する — gitlink が将来動くと MOCC の campaign pin が黙って動く。
- `MOCC_RECORDS` の表を置く — 3 件とも S1 と同値で、同値の定数を二重に管理するだけ。
- harness 外での mocc の拒否、job env の孤立拒否、aggregate の protocol キー化 — 成果物の値を変えない仮想リスク向けの追加 (依頼の scope 外)。
- MOCC で BACKOFF_FIXED の macro だけを使う — D2220 のとおり値の意味が S1 と違う。
