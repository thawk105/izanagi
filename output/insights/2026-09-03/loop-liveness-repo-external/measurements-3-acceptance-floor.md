# 受入 5 分上限の律速 — 親が duration ledger から出した分解

一次資料は `orchestrator/tests/acceptance_duration_ledger.json`
(key `duration_seconds_by_nodeid`、19519 entry)。
**この値は LPT 割付のための scheduling hint であり、権威ある性能測定ではない。**
値が整数へ丸められている (140.0 / 94.0 / 79.0)。傾向を読むために使い、
性能の一次証拠として引用しない (D104 決定 4)。

## 総量と、並列度の限界

```
総仕事量            : 11956.5 s (3.32 CPU 時間、19519 node)
144 worker 完全詰め : 83.0 s     (48 worker x 3 shard)
最長単体 node       : 140.0 s
```

**最長単体 node (140.0 秒) が完全詰めの理論値 (83.0 秒) を上回っている。**
したがって shard 割付・詰め込み・worker 増加のどれでも、受入 wall を 140 秒より下へ持って行けない。
これは 2026-09-01 の床分解 (`output/insights/2026-09-01_t2097-acceptance-floor-decomposition/`) の
結論 5「割付・詰め込みで取れるのは 9.54 秒だけ」と独立に整合する。

## 5 分上限に対する現況

床分解が測った共通 report 外費用 56.3 秒と shard-0 固有 21.9 秒を足すと、

| 走 | 最長単体 | 合計 wall | 分 |
|---|---:|---:|---:|
| 最良観測 | 118.6 s | 196.8 s | 3.28 |
| 中央付近 | 126.1 s | 204.3 s | 3.40 |
| **最悪観測** | **219.3 s** | **297.5 s** | **4.96** |

最長単体は 14 走で 118.6〜219.3 秒に動く (床分解の「閉じていないもの 2」)。
**最悪の走はすでに 5 分の線に触れている。** 上限超えは運の問題になりつつある。

## 最も重い node と file

| 秒 | node |
|---:|---|
| 140.0 | `test_p3_autonomous_workload_trial.py::test_role_sink_bytes_vary_only_at_declared_declassifications` |
| 94.0 | `test_codex_reasoning_ab.py::test_verify_replays_complete_fake_codex_experiment` |
| 79.0 | `test_s8b_floor_campaign.py::test_real_output_snapshot_excludes_git_ignored_real_output_changes` |
| 75.0 | `test_trial_registry.py::test_s8c_acceptance_registered_build_reports_reach_receipt_for_h1_h2_workloads` |
| 72.0 | `test_p3_b4_raw_record_producer.py::test_positive_201_block_certified_preserves_decimal_and_all_pair_protocol_bindings` |

| 秒 | node 数 | file |
|---:|---:|---|
| 903.6 | 59 | `test_p3_b4_wiring_probe.py` |
| 776.0 | 259 | `test_autonomous_trial_completeness.py` |
| 742.7 | 467 | `test_s8b_floor_campaign.py` |
| 697.8 | 226 | `test_trial_registry.py` |
| 675.6 | 134 | `test_s8b_oracle_driver.py` |

## 既存の試みとの関係

[T-1933] (`output/insights/2026-08-28_t1933-acceptance-longest-node/`) が最長 node の短縮を
2 本試みて**どちらも負結果**だった。ただしその wave が攻めたのは
`test_s8b_oracle_driver.py` 系の 4 node (T-080 single-defect 86.57 秒、draft-finalize 51.93 秒 等) で、
手段は **cache 共有と process-memo grouping** だった。
**現在の最長 node である `test_role_sink_bytes_vary_only_at_declared_declassifications` (140 秒) は
その対象ではなく、また「分割」という手段自体は試されていない。**

## 本 wave の位置づけ (D312 に従い達成/未達の二値にしない)

- 本 wave の単位 A が動かすのは **collection 側**であり、上表の「共通 report 外費用 56.3 秒」の
  内訳の一部である。**最長単体 node には触れないので、5 分問題そのものを解決しない。**
- 何から何になるか: 単一 process の discovery 走査が 1.676 秒 → 0.245 秒。
  file collector 合計 12.542 秒に対して最大 23.4 percentage point 相当の削減余地
  (これは上限寄りの試算であり、48 並列の wall への転移は測っていない)。
- 残っている律速: **最長単体 node (118.6〜219.3 秒)** が第一、collection (約 51.7 秒) が第二。
- 次に何を削れば届くか: 最長単体 node の**分割**。上位 5 件はいずれも 70 秒超で、
  1 件を半分にすれば最悪走の wall がそのぶん直接下がる。

## 最長 node の中身 — 単一 node 内の 32 反復ループ

`orchestrator/tests/test_p3_autonomous_workload_trial.py:1836`
`test_role_sink_bytes_vary_only_at_declared_declassifications` の本体は
`for value in range(32):` で、32 本の wire を 1 node の中で順に回している
(`:1844` 以降、`do_build is False` なのでビルドは含まない)。

ledger の 140.0 秒を 32 で割ると 1 反復あたり約 4.4 秒である。
**この node を 32 個へ parametrize すれば、最長単体は約 4.4 秒になり、
仕事は 48 worker へ分散する。** 受入 wall の床 (最長単体) から 140 秒がそのまま消える。

**保留登録簿にも flaky 登録簿にも載っていない** (実測)。したがって毎回の受入で実走している。

ただし parametrize は node id を変える。`acceptance_duration_ledger.json`、shard 割付、
既存の受領証と焦点走の対象集合に波及するため、**本 wave の scope 外**とし次の一手として起票する。
親はこの node の本文を読んだだけで、分割が正しさを保つかは検査していない
(32 反復が互いに独立か、ループ外の共有状態に依存していないかは未確認)。

## 訂正 — 素朴な parametrize では分割できない

上の節で親は「32 個へ parametrize すれば最長単体が約 4.4 秒になる」と書いた。**これは誤りである。**
node の末尾 (`:1941-1952`) にループを跨ぐ assertion がある。

```
assert len(set(sink_bytes["planner"])) == 1
assert len(set(sink_bytes["coder"])) == 1
assert len(set(sink_bytes["auditor"])) == 32
assert len({_canonical_without_json_pointers(raw, _AUDITOR_D_POINTERS)
            for raw in sink_bytes["auditor"]}) == 1
assert _critic_relation_equivalent(sink_bytes["critic"])
assert len(set(trusted_variants)) == 32
```

このテストの目的は 32 ケースを個別に検証することではなく、
**32 本の role sink 出力を互いに突き合わせて非干渉性 (宣言された declassification 以外では
byte が変わらないこと) を確かめること**である。32 node へ素朴に割ると、
反復間比較がどの node からも消え、**検査を消して速くする形 = 絶対規律 2 が禁じる reward hack** になる。

分割するなら、32 本の sink 生成を並列 node へ出し、比較を集約 node が行う形になる。
xdist を跨ぐ集約が要るため難度が高い。[T-1933] が cache 共有と grouping で 2 度負けたのと
同じ難しさの側にある。

**したがって「最長単体 node の分割」は次の一手として起票してよいが、
「32 個へ parametrize する」という具体案は誤りであり書かない。**
起票する内容は「反復間比較を保ったまま 32 本の生成を並列化できるか」の生死確認 (`DW-G01`) である。

## 本 wave の実行中に観測した、もう一つの律速 — 計算ノードのキュー待ち

2026-09-03 の本 wave 実行中、焦点走 1 本を投入したところ次が起きた。

- 1 回目: 既定の queue-wait 900 秒を超えて `rc=16 queue-wait-timeout`。**テストは 1 行も走らなかった。**
- 2 回目: D612 の opt-in 上書き (`IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=3600`) を付けて再投入。
  15 分経過時点で依然 QUE。
- 同時刻の `qstat`: **7 本が QUE、実行中 0 本。** gen_S に空きノードが無い。

**これは依頼の「開発ループが回らなくなる」の第 2 の実体である。**
受入全走が 5 分を超えることの害は「1 本が遅い」だけではない。
**1 本あたりのノード占有が長いほど列が詰まり、並行する全 wave の待ちが伸びる**という増幅がある。
実行中 0 本・待ち 7 本という状態は、その飽和が実際に起きうることを示す。

したがって 5 分上限は、単走の所要としてだけでなく**列の回転率を決める量**として読むべきである。
本 wave はこの点について新しい機構を作っていない。観測として記録するに留める。

### 追記 — 待ち行列は wave の投入とともに伸び続けた

本 wave の焦点走を投入してからの `qstat` の推移 (同一ログインノード、2026-09-03)。

| 経過 | QUE 本数 | 実行中 |
|---|---:|---:|
| 投入直後 | 7 | 0 |
| 約 25 分後 | 7 | 0 |
| 約 28 分後 | **10** | **0** |

**実行中が 0 のまま待ち行列だけが伸びている。** 並行する wave が投入を続けるためである。
この状態では、1 本あたりのテスト所要が何秒であっても開発ループは進まない。

**5 分上限の意味はここで二重になる。** 単走の所要を短くすることは、
(a) その 1 本の待ち時間を短くし、(b) ノード占有を短くして列全体の回転を速める。
後者は並行 wave 数に比例して効く。受入全走が 5 分から 40 分へ伸びれば、
列の回転率は 8 分の 1 になる。
