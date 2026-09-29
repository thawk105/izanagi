---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-29
wave: dev-wave-vhash-cicada-baseline-tuning
seq: 2
---

## {{D:cicada-baseline-tuning-design}}. VHash 論文の比較相手 Cicada の較正は、stock のまま新規の診断 driver で測り、floor にも採否にも接続しない

**決定:** VHash 論文の主 baseline (最適化と GC 設定を調整した Cicada) を決める計測を、次の形で行った。

1. 既存の between-run floor driver (D1373 の関門で Cicada を拒否する) を変えず、新規の診断 driver `tools/vhash_cicada_tuning/` で測る。得た job 間ばらつきは「Cicada control の job 間 session-median CV (複数投入束)」と名乗り、D145 の floor とは呼ばない。floor artifact (`output/env/*/calibration/between_run_noise_*`)・compare・採否には接続しない。関門の射程は floor の生成であり、診断値として一次資料に書くことは迂回ではない (段 3 相談 A も「関門を理由に診断測定を止める必要はない」と判定)。
2. CCBench は改変しない (stock のまま測る)。stock で compile できない設定 (INLINE_VERSION_OPT=1 かつ INLINE_VERSION_PROMOTION=1 の 8 genome、WORKER1_INSERT_DELAY_RPHASE の待機型) は欠測として記録し、CCBench 還元候補の insight にする。
3. 条件の binding は build ごとの compile command の -D 照合と binary sha256 で行う。Cicada は `#ShowOptParameters()` を呼ばない (定義だけ) ので、起動時表示は binding に使えない。
4. 探索 (J1) と確認 (J2) を分け、最良と候補集合は J2 だけから計算する。候補集合の規則 (score ≥ score_best × (1 − cv)) は結果を見る前に段 4 で固定した記述的なリストで、統計的同等性の主張ではない。
5. 計算は合計 2 node 時間未満に収めるため、J0 の実測単価で事前登録の縮小梯子 (R1〜R3) を結果前の式どおりに適用した。

**理由:**
- 弱い baseline に勝っても論文の主張にならない。実測で、CCBench の既定の Cicada は観測最良より rr50 で約 4.5 倍遅かった (一次資料 `output/insights/2026-09-29/vhash-cicada-baseline-tuning/README.md` §6)。
- D1373 の関門は source の trace hook 証拠が無い protocol の floor 生成を拒否するもので、Cicada の hook は patch にしか無い (md_3)。関門を変えず、floor を作らない経路で測るのが最小である。
- 1 投入束 (実質 1 時間窓) の値を floor と呼ぶことは D145 が禁じている。

**却下した選択肢:**
- `between_run_floor.py` の BASELINES に Cicada を足す — D1373 の関門で止まり、足しても測定は開通しない (D2083 項 4 と同じ)。
- 既定 (CMake cache 既定) の Cicada を比較相手にする — 最良から 2〜4.5 倍離れた弱い baseline になる。
- build できない 8 genome を patch で直して測る — 依頼の所有制約 (cc/cicada を改変しない) に反し、stock の比較相手としても使えない。
