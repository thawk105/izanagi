# 全体判定: GO

実装上の must-fix は閉じています。残るのは変異登録から除外すべき冗長変異と、検出力の弱い補助 assert です。私は pytest を再実行していません。実測値は親の `593 passed / 0 failed` のみを引用します。

## 所見対応表

| 所見 | 判定 | 最終形の根拠 |
|---|---|---|
| A-01 | closed | `p3_autonomous_workload_trial.py:208-224` の `WORKLOADS` は ycsb-a/b/c のみ。正式 entry は `:225-232` の `FORMAL_WORKLOADS` に分離。selector 省略時も `:3566-3568` の逐語 `unknown = sorted(set(selected) - set(WORKLOADS))` により rr80/rr20 は拒否される。 |
| A-02 | closed | Layer-3 は `autonomous_trial_completeness.py:2980-2981` の逐語 `workload not in producer.WORKLOADS` で正式 workload を resolver 呼出し前に拒否する。探索 identity による正式 artifact の受理経路は消えた。 |
| A-03 | closed | 明示 selector は `p3_autonomous_workload_trial.py:867-872` で source record を作り、独立 consumer を通した後、`:873-875` の逐語 `formal launch is not admissible` で停止する。consumer は `autonomous_trial_completeness.py:2741-2758` で legacy を再ロードし、`:2778-2791` で module、legacy、producer の四 key を再比較する。selector 省略経路は A-01 で complete 不能。 |
| A-04 | closed | `p3_autonomous_workload_trial.py:227-231` は逐語 `ycsb=copy.deepcopy(_formal_authority["ycsb"])`。`test_p3_autonomous_workload_trial.py:462-469` も `formal_ycsb is not module_ycsb` と片側変更後の非波及を確認する。 |
| A-05 | closed | 無効比較は残っていない。3 sink は `p3_autonomous_workload_trial.py:699-700`、`:748-749`、`:763-764` で正式 scale 不一致を実際に `raise AutonomousTrialError` する。`:472-492` の negative test は同一不正 entry を3 sinkすべてへ渡す。 |
| A-06 | closed | `test_autonomous_trial_completeness.py:3008-3026` は descriptor、binding、campaign lock、campaign ID、perf scale を変異後 scale で自己整合させ、producer entry だけを不一致にする。拒否点は `autonomous_trial_completeness.py:611-617` の新しい四者比較に限定される。 |
| A-07 | closed | module、producer、legacy、arm の不一致をそれぞれ実入力へ注入する negative test が `test_p3_autonomous_workload_trial.py:495-560` にある。実 guard は `p3_autonomous_workload_trial.py:802-825`。ただし digest 単独比較の変異帰属は B-04 のとおり partial。 |
| A-08 | closed | 旧設計性質は `test_p3_autonomous_workload_trial.py:6264,6297` の逐語 `"rr80" not in A.WORKLOADS` のまま維持。正式参照は `:5870-5872`、`:5943-5947` で `FORMAL_WORKLOADS` の ycsb/scale 面へ追随した。親実測は `s6-parent-measurements.md:141-151` の `593 passed / 0 failed`。 |
| A-09 | partial | 弱い自己整合 assert は依然 `test_p3_autonomous_workload_trial.py:428-431` にあり、逐語 `source_record["sha256"] == legacy.sha256`。ただし独立 consumer の再ロードと tamper test が `test_autonomous_trial_completeness.py:3107-3153` に追加され、成果物境界の検出力は別経路で確保された。 |
| B-01 | closed | `_prepare_campaign_identity` と manifest helper は `p3_autonomous_workload_trial.py:1043-1049`、`:1090-1096` で実際の `_perf_for(entry)` を保持する。cell は同じ object の値を `:3018-3022` へ記録し、実 driver も `:3329-3333` でその `perf` を消費。Layer-3 は `autonomous_trial_completeness.py:611-617` で descriptor、cell perf、campaign、entry を完全一致させる。 |
| B-02 | closed | 正式 entry の `WORKLOADS` 混入は解消。Layer-3 の `autonomous_trial_completeness.py:2980-2981` が正式 workload を探索 supported set 外として拒否する。単一 resolver はその後の `:2999` でのみ使われる。 |
| B-03 | closed | A-06 と同じ自己整合 fixture により既存 descriptor digest gate の mask は除去された。campaign lock の `descriptor_sha256` も `test_autonomous_trial_completeness.py:3022-3026` で再構築されている。 |
| B-04 | partial | M8 の四 key guard と M10 の consumer 本体には直接 negative test がある。一方 M9 の digest 比較は `p3_autonomous_workload_trial.py:821-823` の同じ if 内で `producer_bytes != arm_bytes` に包含される。M11 を外しても `trial_registry.py:1390-1395` の `u4-holdout-workload` と `p3_autonomous_workload_trial.py:3566-3568` の unknown gate が同じ入力を拒否する。 |
| B-05 | closed | structured entry の探索 consumer は ycsb 面へ追随し、正式 entry は別表化された。`test_campaign.py:9227-9230` の `list(autonomous.WORKLOADS)` も探索3件だけになる。親の焦点走7で関連5 fileは全件通過済み。 |

## 変異帰属

| 対象 | 判定 | 単一理由性 |
|---|---|---|
| F-4 `_perf_for` scale | 登録可 | 実際に driver へ渡す `perf` と cell の `perf_config_scale` が同一 object 由来。Layer-3 の四者比較だけが差を拒否する。 |
| F-5 / M7 | 登録可 | descriptor、binding、campaign lock、campaign ID、perfを自己整合済み。producer entry だけが異なる。 |
| M5 workload flags | 登録可 | `test_autonomous_trial_completeness.py:3046-3056` は flags だけを変更し、最初の producer比較に帰属する。 |
| M6 campaign scale | 登録可 | `:3079-3104` は正式 descriptor、perf、entryを維持し、campaign recordsだけを変更する。 |
| F-6 / M8 四 key guard | 登録可、期待 node は複数 | module側とproducer側の2 direct testが同じ guard削除で赤になる。理由は一つだが、期待 node 完全集合には両方が必要。 |
| M9 digest conjunct | 登録不可 | canonical bytes 比較が前置され、digest比較だけの削除は等価変異になる。 |
| M10 consumer本体 | 登録可 | tampered source と tampered producer entry が consumer を直接攻撃する。ただし `_preflight_workload_profile` から consumer call だけを削る変異は現テストで pin されないため、call-edge変異は登録不可。 |
| M11 formal fail-closed | 登録不可 | U4 holdout gateと、登録経路後の `WORKLOADS` closed-set gateに maskされる。現テストが殺すのは拒否順序と診断文字列。 |
| M12 conjunction | 登録可、期待 node は複数 | source hit は局所 testに加えて `test_s8c_preregistration_invariant.py:292-309` も検出する。`:572-578` の scale-only負対照は records/threadsだけでは赤にならない。 |

## fix 4 回帰検査

fixture は恒真化していません。`test_trial_registry.py:559,574,578` は campaign/perf scale を resolver から導出しますが、封印 descriptor は `:516-525` の独立した `1_000_000 / 48` のままです。consumer は四者を独立比較するため、resolver が誤れば descriptor との不一致で赤になります。

campaign ID は fixture helperが manifestとreportの双方へ生成しますが、Layer-3は exact search key集合、固定 spec、identity preimage hashを別実装で検査します。探索側にはさらに `test_autonomous_trial_completeness.py:3171-3189` の固定 `4b75e24e` pinがあります。

探索不変も静的に維持されています。

- baseline hashは `test_p3_autonomous_workload_trial.py:379-381` が `m3-baseline.json:3,48,93` と逐語一致。
- campaign IDは `test_autonomous_trial_completeness.py:146-155` に `4b75e24e`、`136086b0`、`4ac6e6a4` が固定されている。
- 新しい `perf_config_scale` は cell の別 keyであり、`_campaign_for` の identity preimageには入っていない。

裁定2.7も遵守しています。`autonomous_trial_completeness.py:125-130` の exact search key集合に `workload_profile` はなく、正式専用 keyは拒否されます。`:591` は探索 `pilot_scope` 固定、`:625-630` は探索 spec固定で、正式 `pilot_scope` / `spec_content` の受理枝はありません。

## 残る所見

- 深刻度: should-fix、変異証拠のみ。M9、M11、consumer call-edgeを KILLED 登録から外すこと。成果物影響: 外さない場合、試行台帳が実効 gate の検出力を過大表示する。
- 深刻度: nit。A-09 の同一 loader 由来 hash assert は単独では無効に近い。成果物影響: 受理集合への影響はなく、独立 consumer testが実効保証を担う。

## 総括

最大の残存懸念は実装ではなく変異台帳の過大申告である。  
M9、M11、consumer call-edgeは単独 killとして登録してはならない。  
正式 runの無 selector迂回、正式 Layer-3混入、scale不可視、mutable aliasは閉じた。  
親の済ませた実測以外は走らせていない。全体判定は **GO**。