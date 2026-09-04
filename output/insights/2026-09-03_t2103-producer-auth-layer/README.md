# [T-2103] 凍結 closure 外 raw-record producer の認証層 — 比較実験の一次資料

wave `dev-wave-t2103-producer-auth-layer`、branch `worktree-dev-wave-t2103-producer-auth-layer`。
2026-09-03。裁定 D1345 が要求した比較実験である。

`verbatim/` に段 1〜6 の全成果物 (brief、plan、敵対相談 2 本、裁定、追補 3 本、実装子報告、
敵対レビュー 2 本、fix 6 巡、親の実測記録 2 本) を逐語で置く。
`shards/` に候補 x phase の 6 shard の生結果、`comparison.json` に合成結果を置く。

## 問い

凍結された analysis source closure (5 file) の外にある raw-record producer を、
どの層で認証するか。候補は D1345 が挙げた **issuer / raw assembly / frozen consumer** の 3 つ。
同一の変異集合を 3 層へ当て、拒否能力を数字で比較する。

## 測定した checkout

- base commit: `fb79e633e73df3578363de1b96a7213239da85d9`
- producer bytes: `orchestrator/campaign/p3_b4_raw_record_producer.py` の SHA-256 は
  `6399e5e3b467bfa36cf9e7fe8db64f6e2dbb4268bf8c8a1e515d5024de6e71b0` (T-2141 着地後)
- 6 shard (候補 x phase) を並列実行し rc=0、`combine` で合成 rc=0
- 焦点走: **47 passed in 44.05s** (rc=0)

## 結果

分子は層を分離しうる C1 系 3 件 + R 系 3 件の計 6 件。
C0 系 3 件・D 系 3 件・POS-1 は対照であり分母外である (測定前に固定した)。

| 候補 | 増分 KILLED | production file | pin site | test 波及 file | 非後退 29 node |
|---|---:|---:|---:|---:|---|
| issuer | **0 / 6** | 2 | 1 | 2 | 緑 |
| raw assembly | **3 / 6** | 2 | 1 | 2 | 緑 |
| 一時的 6-member expanded closure prototype | **3 / 6** | 4 | 3 | 5 | 緑 |

`decision.complete_candidate_exists` は false。6 件すべてを殺す候補は無い。
`decision.leaders` は `raw_assembly` 単独である。

### 層別に何が起きたか

- **C0 系 (対照、3 件): 3 候補とも KILLED。** issuance 前に正規 path の source を書き換える形は
  source-hash 比較が動く層ならどこでも捕まる。層を分離しない。
- **C1 系 (分子、3 件): issuer だけが SURVIVED。** issuance 後・assembly 前に producer が
  差し替わる形を issuer は観測できない。これは issuer 自身が
  `p3_b4_prerun_issuer.py` の非保証に書いている性質と一致する。
  raw assembly と frozen prototype は自分の guard で `producer_auth_mismatch` を出した。
- **R 系 (分子、3 件): 3 候補とも `BASELINE_REJECTED`。** baseline と prototype の観測が
  `evidence_binding:source_rederivation` で完全に一致した。拒否しているのは**既存の
  source rederivation gate** であって、新設した guard ではない。よってどの候補にも
  増分を与えない。段 2 plan の事前期待 (raw 9/12) はここを取り違えていた。
- **D 系 (対照、3 件): 3 候補とも SURVIVED。** assembly 後に raw analysis の判断値だけを
  書き換える形は 3 候補共通の穴である。
- **POS-1 (対照): 3 候補とも受理。** 過剰拒否は起きていない。候補が有効な状態でも
  既存 producer test 29 node は 3 候補とも緑である。

### D1345 への答え

**拒否能力は raw assembly と 6-member expanded closure prototype で同一である** (ともに 3/6、
かつ殺した case 集合も同一)。差がついたのは変更閉包だけであり、closure を広げる案は
production file 4 / pin site 3 / test 波及 5、raw assembly は 2 / 1 / 2 である。

したがって **5-file pin を広げる案は最小ではない。** D1345 が pin 拡張を採る条件
(「比較の結果それが最小と示された場合」) は満たされない。

## 測定の途中で判明した、より重い事実

**B-4 の production 経路は現時点でいかなる入力に対しても有効な分析を返さない。**

- `orchestrator/campaign/p3_b4_material_report.py:225` が `evaluate_b4_artifacts` へ
  `floor=None` を渡す。
- `orchestrator/campaign/p3_b4_analysis_contract.py:323-325` が `None` の floor に対し
  `FLOOR_DOMAIN_ERROR` を立てる。
- これは事故ではない。`p3_b4_material_report.py:6` の docstring が
  「`floor=None` を凍結 evaluator へ渡し、結果の protocol violation を報告する」と明記し、
  同 file は `"floor_availability": "absent"`、
  `"expected_analysis_reason": "floor_domain_error"` を報告 field に持つ。
  権威ある floor 成果物が未発行だからである。

このため本測定は `floor=0` を供給している (既存の 201-block 正例と同じ値)。
frozen 候補の値は「floor が供給された場合の拒否能力」であり、現行 production の挙動ではない。

併せて、**closure receipt には production の呼び手が存在しない**ことも実測した。
`generate_verified_analysis_source_closure_receipt` を呼ぶのは test だけであり、
`p3_b4_material_report.py:224` は receipt を渡さずに evaluator を呼ぶ。
frozen 候補を本採用するなら、この配線を新設する変更が要る (上表の production file 4 に計上済み)。

## 非保証 (`comparison.json` の `non_guarantees` に逐語で載る)

1. KILLED / SURVIVED は C0 / C1 / R / D の 4 投入位置と P / T / C の 3 判断値、POS-1 にだけ適用され、
   他の判断値・任意のコード変異・coordinated rewrite・path race へ一般化できない。
2. path と SHA-256 の一致は各層が検査した時点の repository bytes しか示さず、
   その bytes が対象 artifact を生成したという因果を証明しない。
3. frozen の値は一時的 6-member closure と追加 gate の値であり、
   現行 5-file consumer の拒否能力でも本採用の根拠でもない。
4. R 系の raw 拒否は既存 source rederivation gate によるもので、追加 guard の増分ではない。
5. D 系が全候補で生存するため、どの候補も post-assembly 改変を含む end-to-end authenticity を
   保証しない。
6. issuer は issuance 後の producer 交代を観測できない。
7. 現行 5-file receipt は現在の bytes を hash 化するだけで、固定期待 digest と比較しない。
8. 本測定は `floor=0` を供給している。production は `floor=None` を渡し
   `floor_domain_error` を返す。

## 測定機構自体の変異検査 (DW-M01)

比較実験の matrix とは別に、本 wave が新設した測定機構へ W01-W09 を事前登録して当てた。
W01-W08 は適用可能な exact mutant を持ち、`test_wave_mutant_kills_exactly_one_registered_node[w01..w08]`
が**各 mutant がちょうど 1 つの登録 node を殺す**ことを実測している。W09 は正例で mutant を持たない。
8 件とも焦点走 (47 passed) に含まれて緑である。

## 2 つの producer 版で同じ答えが出た (再現)

測定は途中で 1 度やり直している。wave の実行中に T-2141 が着地し、
`p3_b4_raw_record_producer.py` が +376 / -14 行変わったためである
(SHA-256 は `55e264f05eef...8411e17b1c790` から
`6399e5e3b467...d5024de6e71b0` へ)。

| 測定 | producer | base commit | issuer | raw | frozen | leader |
|---|---|---|---:|---:|---:|---|
| 1 回目 | T-2141 着地前 | `3e6fe8d97` | 0 / 6 | 3 / 6 | 3 / 6 | raw_assembly |
| 2 回目 (本記録) | T-2141 着地後 | `fb79e633e` | 0 / 6 | 3 / 6 | 3 / 6 | raw_assembly |

**producer の 2 つの版に対して同じ結論が出た。** 1 回目の値は超越されたが、
測った内容に束縛された事実としては有効である (規律 7)。
本 README の表と `comparison.json` は 2 回目の値である。

2 回目では 39 組すべてで期待と観測が一致した (`expected != observed` は 0 件)。

## 経緯 — 事前期待が 2 回覆った

1. 段 2 plan の事前期待は issuer 3/12、raw 9/12、frozen 6/12 であった。
   実測は issuer 0/6、raw 3/6、frozen 3/6 で、**raw と frozen は同点**であった。
   差の主因は R 系の帰属で、plan は既存 gate の拒否を候補の能力として数えていた。
2. 段 6 の敵対レビュー 2 本が独立に、初版の測定機構が**実際には測っていない**ことを指摘した。
   raw の probe が認証不一致以外の拒否を潰していたため、attempt artifact を作らずに assembly を
   呼んだ結果の既存拒否が「受理」と読まれ、raw の増分 3 件が偽陽性になっていた。
   fix でこれを閉じた結果、R 系は正しく `BASELINE_REJECTED` に落ちた。

## 実行しなかったこと

正式な B-4 実走、qsub による性能測定、認証層の本採用実装は行っていない。
5-file pin (`_SOURCE_CLOSURE_PATHS` / `_CLOSURE_PATHS`) の恒久変更も行っていない。
候補の一時差分は repo 外 scratch の使い捨て tree の中だけに存在し、
主 worktree の bytes は測定中も一度も変わっていない。
