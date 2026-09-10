# [T-525] holdout 完全条件束縛 — 変異証拠と裁定パッケージ

wave: `dev-wave-t525-holdout-binding` / 実装 commit `f36dde4b`、テスト追加 commit `bd4d3576`

## 何を閉じたか

ratified freeze は holdout ごとに完全条件 (candidate_id / `ycsb_zipf_skew` / `ycsb_rratio` /
`ycsb_rmw` / records / threads) を持つのに、束縛は workload 名と `ycsb_rratio` の 2 field
だけだった。名前と読み取り比率の一致だけで、別条件の測定が H1 として receipt 化されうる。

純増となる面は実測で 1 つに絞られた。**実行 argv の関門**である。
producer 表と freeze の一致 (`autonomous_trial_completeness.assert_legacy_workload_profile_source`)
も、report と producer 表の一致 (`_check_arm_digest_chain` / `_check_campaign_chain`) も既にあった。
一方 report の `workload_flags` は argv でなく producer 表からの複製
(`p3_autonomous_workload_trial.py:3581` の `dict(entry["ycsb"])`) なので、
report 側の検査では argv の乖離を構造的に見られない。

## 段 6 の敵対レビューが出した 2 つの blocker (親が原典で裏取り)

1. **gflags のハイフン正規化。** `FlagRegistry::FindFlagLocked` は
   「If the name has dashes in it, try again after replacing with underscores.」と実装コメントに
   明記している。完全一致 argv の後ろへ `--ycsb-rmw=1` を足すと関門は別 key として無視し、
   CCBench は `ycsb_rmw=1` で実行する。保護 5 field すべてで成立する。
2. **`batch_th_num` による worker 追加。** `external/ccbench/cc/silo/util.cc:35` が
   `TotalThreadNum = FLAGS_thread_num + FLAGS_batch_th_num;`、
   `cc/silo/include/common.hh:40` が `DEFINE_uint64(batch_th_num, 0, ...)`。
   `--batch_th_num=48` を足すと凍結 threads=48 のまま実 worker は 96 になる。

値の照合だけでは、名前の綴りと「条件を変える別 flag」を塞げない。
CCBench の direct flag を棚卸しすると条件を変えうるものは他にも
`batch_ratio` / `batch_tuples` / `batch_max_ope` / `batch_rratio` / `batch_simple_rr` /
`ronly_ratio` / `ycsb_max_ope` / `ycsb` / `epoch_time` があり、個別対応では保たない。
そこで (a) 分類前に gflags と同じ名前正規化、(b) 保護 run の **閉じた allowlist** の 2 段にした。

allowlist は 2 要素だけである。

| flag | 根拠 |
|---|---|
| `clocks_per_us` | 呼び出し元の環境契約に束縛された換算値。自由な workload / scale 軸を足さない |
| `extime` | 呼び出し元の protocol に束縛された観測窓。自由な workload / scale 軸を足さない |

過剰拒否の不在は実測した。`p3_autonomous_workload_trial._perf_for` は
`PerfConfig(workload=dict(entry["ycsb"]))` として freeze の 3 key しか渡さないため、
`runner.measure_point` が組む正式 holdout argv は
`thread_num` / `ycsb_tuple_num` / `extime` / `clocks_per_us` + 3 軸 の 7 本で、
`ycsb_max_ope` は現れない (あれは `pipeline._correctness_workload` の rr50 経路であり
非保護 ratio のため allowlist の対象外)。

## 変異 matrix

`mutation-spec.json` と `mutation-ledger.json` が現物。後者は harness result の射影で、raw stdout は
凍結 holdout の三軸値を逐語で含み repo へ置くと未知性検索の conjunction に当たるため除いてある
(原本は wave の job directory)。
baseline PASSED (544 件)、**12 件登録・12 件 KILLED・SURVIVED 0・MISMATCH 0・PARSE_ERROR 0**。
期待 node はすべて実測値で、推測で書いたものは無い。

| id | 無効化する関門 | 落ちる node 数 |
|---|---|---|
| M01 | ハイフン別名の拒否 | 1 |
| M02 | 非 canonical 形の拒否 | 12 |
| M03 | `--` 終端後の拒否 | 6 |
| M04 | 閉じた allowlist | 4 |
| M05 | allowlist 要素の綴り要求 | 2 |
| M06 | 保護 field の値照合 | 1 |
| M07 | gflags 名前正規化 | 2 |
| M08 | 束縛表の不変化 | 1 |
| M09 | lock 非依存の scale 照合 | 1 |
| M10 | **過剰拒否の正例** (allowlist から `clocks_per_us` を削る) | 10 |
| M11 | run-once の条件比較 | 1 |
| M12 | **M06 と M11 を同時に** | 1 |

M10 は受理集合を縮める wave が要求する逆向きの登録である。正当な走行が誤って拒否されると
呼び出し元 4 経路の正例テストが落ちる。

## 変異だけが見つけた穴 (erratum を含む)

初回の probe では **M06 / M11 / M12 がすべて SURVIVED** した (544 件緑のまま)。
単独変異 2 件の生存は当初 masking を疑ったが、**両層同時変異 (M12) でも生存した**ため
masking ではなくテスト集合の穴と確定した。

既存テストは (a) 形が非 canonical な argv と (b) 値の**書式**が不正な argv しか置いておらず、
**「書式は妥当で値だけ freeze と違う」argv** — H1 admission を持ったまま
`--ycsb_rratio=20` や `--thread_num=24` で走る形 — を直接検査したテストが 1 件も無かった。
これは wave が閉じようとしている中心シナリオそのものである。
焦点走 1670 件の緑も敵対レビュー 2 本もこれを見つけられなかった。

`test_canonical_value_mismatches_reach_both_binding_layers_and_are_rejected` を追加し、
3 変異すべてが KILLED になった。詳細は failures 台帳の該当エントリ。

### 手続きの erratum

- 初回 probe は期待 node を単独 node で登録しており、DW-M08 の「期待 node は完全集合」を
  満たしていなかった。probe として扱い、実測集合で再登録して最終巡を権威とした。
- harness の dispatch 経路で M07 が 2 回連続して出力を取れず停止した。
  同じ変異を手元で当てると毎回 2 node が落ちたため、変異ではなく捕捉側の失敗と判定した。
  local runner mode へ切り替えると harness の node 列挙が通らなくなり、dispatch へ戻した。

## 保存形式は変えていない

段 3 の両レンズが独立に「保存形式を変えるなら schema 世代交代が要り、旧 artifact を
失効させるか二世代 reader を持つかの裁定が要る」と指摘した。これはユーザー裁定事項なので、
本 wave は次をすべて現状のまま据え置いた (段 6 レビュー B が 1 項目ずつ確認済み)。

- `launch_admission.binding` の key 集合 (11 key)
- `_LAUNCH_BINDING_KEYS` などの exact key 集合
- canonical JSON の preimage
- report / run-start (v3)、acceptance receipt (v3)、attempt registry (v2)、lifecycle (v2)
- `HOLDOUT_BINDINGS` の既存 key の名前と意味、`HOLDOUT_WORKLOADS` の値集合
- `output/s8b-freeze/holdout_freeze.json` の bytes (`315b1eb8…`)

## 未知性検出器との関係 (正直な記録)

段 3 レビュー B は「完全条件の値を名前付き定数へ分割する方式は、`search_repository` の
三軸 conjunction 検索から見えないという意味で**形式上は検出器回避である**」と指摘した。
親の裁定が明示した方式であり、`holdout_observation` 側の freeze との exact 比較が補うが、
評価はそのまま残す。`test_s8b_repo_scan_invariant.py` の
`KNOWN_CONJUNCTION_HITS == {"rr80": [], "rr20": []}` は緑のままである。

## 裁定パッケージ (ユーザー裁定待ち)

worklog の「次の一手」へ新規 T として登録した。推奨は次のとおり。

1. **受入 receipt の freeze 再錨付け。** `s8c_acceptance_receipt.py` は freeze を一切読まない。
   nested condition と cell と descriptor を同じ誤値で自己整合させた receipt を H1 として
   検証済みに出来る。**推奨: 昇格する。** ただし 2 が前提になる。
2. **schema 世代交代。** report / run-start / receipt を v4 へ上げるか。
   **推奨は保留** — 旧 artifact を失効させる判断を含むため、1 を採るときに同時に決めるのが良い。
3. **正式起動の配線。** 現在 `_preflight_workload_profile` が無条件拒否し、
   `loop.py` に admission 引数が無いため token が `pipeline.evaluate` へ届かない。
   binding / report / 受入層の関門は production で発火しない。**推奨: [T-527] と束ねて 1 wave。**
4. **C01 述語の扱い。** p3 の 3 関数に scale リテラルを残すか、
   shared constructor の到達性検査へ更新するか。**推奨: 現状維持** (リテラルを残す)。
   二重の真実は `assert_legacy_workload_profile_source` の bytes 一致検査が塞いでいる。

別件として `tools/codex_worker_launch.py` の JSONL 分割 (`splitlines()` → `split("\n")`) を
独立審査へ回した (F540 supersede)。
