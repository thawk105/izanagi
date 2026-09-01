---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2135-tictoc-cicada-space
seq: 1
title: [T-2135] tictoc と cicada の genome 空間を登録した — tictoc は silo の XOR ではないと子が覆した (コード + テスト、branch worktree-dev-wave-t2135-tictoc-cicada-space、変異 7/7 KILLED)
---

## 本文

`SPACES` は silo / mocc / tictoc / cicada の 4 protocol になった。tictoc と cicada はどちらも
生 `2^5=32`、有効 24 通りである。軸の導出根拠・除外理由・限界は `genome.py` の `notes` と
述語 docstring に逐語で書いた。詳細は {{D:tictoc-no-wait-not-xor}} と
{{D:cicada-axis-vs-measurand}}、実施記録と逐語 7 本は
`output/insights/2026-09-02_t2135-tictoc-cicada-space/`。

- **導出できずに落とした軸は 0 本。** 依頼は「導出できない軸は無理に登録せず理由を残す」だったが、
  段 2・段 3・段 6 のいずれも判定不能な軸を報告しなかった。cicada の 5 flag は全て分類できた。
- **親の provisional 裁定 5 件のうち 2 件が覆った。** (P1) 「tictoc も silo と同じ no-wait XOR」は
  段 2 が最初に否定し、段 3 レンズ A が行番号で裏取りした。(P3) 「`SINGLE_EXEC` と
  `WRITE_LATEST_ONLY` は共に最適化軸」は前半だけ覆った。
- **親が実測を誤った / 一般化しすぎた点が 5 件、すべて子が見つけた。**
  (i) tictoc の XOR 転用。(ii) `PARTITION_TABLE` の検索範囲が `cc/tictoc/include/` 部分木と
  4 つの workload source を落としていた (全件で測り直し、結論は維持)。
  (iii) 「`space_for` の caller 0」を正しさ境界の根拠にしたこと (`Genome` は登録簿を通さず
  直接構築できるため証明にならない)。(iv) その差し替え先で拒否機構を `BASELINES[protocol]` の
  `KeyError` と書いたこと (実際は `_parse_cli_args` の `ValueError` で、添字参照へ到達しない)。
  (v) 変異 M4 の期待 pair 集合を 2 組と書いたこと (正しくは 3 組、有効数は 24 のまま)。
- **段 6 レビュー B の must-fix 3 件は全て本物の事実誤りだった。** notes の
  「列挙しない flag は fresh configure で default 0」は delay 2 件の default が空値 (unset) の
  ため一般化として成立せず、`SINGLE_EXEC` へ限定した。
- **焦点再レビューは 2 巡した。** 1 巡目は「射影不足で不在の主張を独立検証できない」として
  partial を返した。これは正当な指摘なので、tictoc の 4 workload source・専用 header 8 本・
  共通 header・cicada の workload source を射影して 2 巡目を回し、全件 closed にした。
  同型は F717 の再発として台帳へ追記した。
- **本 wave は測定を 1 件も行っていない。** 登録は探索空間の宣言であって certified campaign を
  成立させない。tictoc の `(0,0)` の競合下の完走性も未実測で、notes にそう書いた。
- **正しさ境界は SPACES から独立の 2 層で保たれる** (親の実測)。
  `between_run_floor._parse_cli_args` が `protocol not in BASELINES` を `ValueError` で拒否し
  (実測で tictoc / cicada とも拒否、選択肢は `['mocc', 'silo']`)、その先に D1373 の source 束縛
  admission がある (実測で silo=True / mocc=False / tictoc=False / cicada=False)。
  **新しい gate は足していない。** 依頼が scope 外とした範囲であり、既存 2 層で fail-closed である。
- **子は 8 体、全て `gpt-5.6-sol` / `xhigh` / 受理** (plan 1・consult 2・author 1・review 2・fix 1・
  focus 2 のうち focus は 2 巡)。工数は受領証 (`receipt.json`) が正本。
- 変異 matrix = baseline PASSED・KILLED 7・SURVIVED 0・MISMATCH 0・期待 node 完全一致 7/7。
  `--runner-mode dispatch`、固定 commit `727ca869f` の使い捨て worktree。走行後に作業木が
  commit と byte 一致することを確認した。M4 の期待値訂正は erratum として insight に残した。
- `docs/phase3.md` 段 6 dormant (b) は**閉じていない**。protocol 別 calibration と between-run
  floor の対象別再実測が残る。

## 次の一手差分

### 完了

- [T-2135] tictoc と cicada を `SPACES` へ登録し、除外理由と限界を notes へ書いた。
  導出不能な軸は 0 本だった。
  remaining: none
  base: 4874fc348fb012255bb942b7ebb9d3429435fe96d4c9c4263145f39e9ea1cb7f

### 新規

- {{T:cross-protocol-measurement-surface-audit}} **P2・新規**: 正しさ検証を経ない測定面の
  repo 全体の閉包を確認する。段 6 の 2 レンズが独立に挙げた — `measure_point_floor()` の
  直接呼出しは admission を通らず、floor CLI は通過後 `trace=False` build を測るだけで verifier を
  実行せず、screening は verifier より先に bench を実行できる。**本 wave が作った欠陥ではなく
  既存の状態**であり、official commit writer は certified 判定後に閉じている。
  tictoc / cicada を floor / campaign consumer へ接続する前に、D1360 の「未検証性能観測を
  official report・selector・順位へ入れない」をどの admission で強制するかを確定する。
- {{T:tictoc-zero-zero-progress-measurement}} **P3・新規**: tictoc の no-wait 両 0 の競合下の
  完走性・公平性・starvation を実測する。今回の「silo の livelock 機構とは異なる」は
  制御フローからの静的導出であり実測ではない。certified campaign へ入れる前の前提。
- {{T:cicada-trace-hook-promotion-semantics}} **P3・新規**: cicada の trace-hook 移植時に、
  `INLINE_VERSION_PROMOTION` が作る同値 body の内部 write を workload write として verifier に
  見せるか、内部 maintenance として区別するかを決める。段 6 レンズ B の指摘。
