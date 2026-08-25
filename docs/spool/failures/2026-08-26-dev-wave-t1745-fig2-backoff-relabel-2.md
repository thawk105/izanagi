---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1745-fig2-backoff-relabel
seq: 2
---

## 新規

### {{F:gate-not-wired-to-landed-artifact}}. 新設 gate が着地する実成果物に接続されず、合成 fixture だけで緑になった [恒真ゲート]

- 事象: [T-1745] の段 5 が provenance 検査を新設し、焦点走 41 件が緑になった。しかしその gate は
  すべて一時ディレクトリの合成 fixture を検査しており、**論文へ載る実 provenance を開く test が
  1 つも無かった** (親実測: 成果物 path で grep して 0 hit)。着地物の値・path・bytes が
  何に変わっても、この 41 件は赤にならなかった。
- 根本原因: gate の設計時に「述語が正しいか」だけを検査対象にし、「その述語が守る対象が
  実在するか」を検査対象にしなかった。合成 fixture は述語の正しさを示すが、
  **守るべき現物との接続は示さない。**
- 恒久対応: `orchestrator/tests/test_backoff_figure_provenance.py` に、着地した
  `docs/paper-story/figures/fig2b_backoff_sweep_3workload.provenance.json` を実際に開いて
  validator へ通す test を置いた。成果物が不在なら赤になる (skip にしない)。
- 再発検知: 同 test は成果物 file の実在を要求するため、成果物の削除・改名・値変更で赤になる。

### {{F:drawn-figure-and-recorded-provenance-can-diverge}}. 図に描いた label と provenance に記録した label が別経路で作られ、乖離しても検査を通った [恒真ゲート]

- 事象: [T-1745] が是正しようとした旧事故は「横破線の label が `stock adaptive`、値は無 backoff」
  という**図の表示と実データの食い違い**である。ところが新設した provenance は
  描画とは別の関数が値を再計算して書いており、図中 label だけを書き換えても
  provenance は自己整合のまま緑になった。段 6 レビューが実測で示した。
  同じ穴で、出力 PNG/PDF を無関係な図へ差し替えて digest も同時に更新すると通る、
  `facts` が検査対象外で図の主要数値を偽れる、といった受理も成立していた。
- 根本原因: 「記録は描画の写しである」という不変条件を、**同じ値を 2 回計算する**設計で
  表現しようとした。2 経路ある限り、片方だけを壊す変更が必ず作れる。
- 恒久対応: 描画関数が「実際に `axhline` へ渡した y」と「実際に `axt.text` へ渡した label」を
  返し、provenance はその返り値だけから組み立てる形へ一本化した
  (`tools/plotting/plot_backoff.py`)。別経路の再計算関数は削除した。
  加えて `orchestrator/tests/test_plot_backoff_ci.py` が実 figure の text object と
  axhline の y を provenance の記録と照合する。
- 再発検知: 描画側の label だけを変える変異が上記照合 test で赤になることを段 6 で確認した。
