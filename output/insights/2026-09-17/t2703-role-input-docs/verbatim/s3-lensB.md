## 所見 (番号・real/refuted/判定不能・file:line・成果物影響 1 行)

以下のパスは、特記がなければ指定 worktree 相対。pytest・checker・変異は実行していない。

1. **real — verify の説明を全手動経路へ一般化できない。**
   `orchestrator/campaign/p3_s4_loop.py:1494` の設定には verify key がない。一方、`p3_s4_loop_sort.py:304` と `p3_s4_loop_trigger_gating.py:599` は `VERIFY_LEGACY_PLUS_S2` を指定する。`orchestrator/campaign/loop.py:153` はこれを追加 S2 pass に変換する。plan は legacy 限定を追記しているが、共有 inline 文書の実利用先である sort／trigger の説明が欠ける。
   **成果物影響:** coder に渡る検証条件が legacy の小規模検証だけに見え、実際の追加 S2 検証を反映しない。

2. **refuted — perf preflight receipt が PerfConfig を差し替える、という攻撃仮説。**
   `orchestrator/campaign/loop.py:150` の返値は receipt と bool。`orchestrator/calibrator/perf_preflight.py:261` は `available` を返し、records／threads／reps を構成しない。sort と trigger はそれぞれ `p3_s4_loop_sort.py:331`、`p3_s4_loop_trigger_gating.py:624` で同じ `L.default_perf` を使う。100k／t4／extime1／reps2 は**配線用既定値として正しい**。calibration 後の一般値ではない。

3. **real — 手動 baseline の恒常性を「確認済み事実」とする根拠が不足。**
   `docs/phase3-s4b-runbook.md:52,71` と `docs/phase3-s5-sort-runbook.md:44,67` は `<baseline>` と書くが、初回に固定し以後更新しないとは規定していない。plan.md:156 はその規定を新たに追加する案である。D410 の逐語は 8c の機械射影を規定しており、手動実績の証明ではない。
   **成果物影響:** 手動役割入力の値の選択規則を新設する変更が、既存挙動の説明訂正として記録される。

4. **refuted — reject 世代が planner／coder の凍結 baseline を上書きする。**
   `p3_autonomous_workload_trial.py:4440` は `current_metrics` を更新し、欠測なら `:1994` の射影で None になる。しかし凍結 snapshot は `:4102` で一度だけ作り、`:2051,2063,2075` は世代更新値を捨てる。reject 後の metrics 更新は残るが、役割 baseline の上書きには到達しない。文書は「初期 metrics 定数（現行は全 null）」が正確。

5. **判定不能 — consumer 一覧の完全閉包。**
   指定の `git grep` と provider／fixture 参照検索では、plan の主要 consumer 列挙を覆す実 role bytes の漏れは確認できなかった。追加ヒットの `test_codex_jsonl_line_split.py:16` は events、`test_profiler_directive.py:341` は policy の参照であり、本文 consumer とする根拠はない。ただし全 helper の二段閉包を完全に証明したとは報告しない。
   `tools/check_docs.py:169` は runbook を living-doc 検査へ登録し、`:6721` 以降で行番号参照、pin literal、D 番号、パスを検査する。今回の runbook／leakproof／4 role 本文について専用 byte・行長予算は確認できず、一般予算処理 `:5980` の存在だけを保証に数えてはいけない。

6. **refuted — adapter の変化 field と manifest 不変の説明。**
   plan の4 field は正しい。`spec.py:806,820,837,869` により、`source.sha256`、`review_ledger.source_file_sha256`、`semantic_digest`、`developer_instructions` が変わる。semantic digest は `:790` の本文にも依存する。manifest pin は `:566` の manifest entry hash で、本文 hash は別の `:583`。
   checker は `load_role_specs()` の source／ledger 比較（`:587`）と、`_validate_adapter_inventory()` の renderer 出力との全文比較（`tools/check_codex_agents.py:224,242`）を行う。

7. **real — M1 の単一 node 失敗から、単一原因性は導けない。**
   `test_reflux_originless_compatibility.py:1280` の対照は現行出力同士を比較し、`:1293` の node が固定 baseline を比較する。静的には helper 呼出し除去で後者だけが赤になる見込み。しかし planner・critic・coder の各 SHA 不一致がそれぞれ同じ比較を失敗させ得る。plan.md:271 の「個別寄与とは解釈しない」は適切だが、それだけで DW-M01 の単一理由性を証明したことにはならない（`docs/dev-wave/mutation.md:7,19`）。
   **成果物影響:** mutation receipt が、3 role の集約追随漏れの検出を独立した単一原因の証拠として過大評価する。

8. **refuted — M2 が個別 test node の FAIL になる。**
   plan の修正は正しい。`test_codex_agents.py:27` → `tools/check_codex_agents.py:44` → `spec.py:587` で import 時に拒否される。`test_review_ledger_independently_pins_all_fourteen_sources_and_io_contracts`（`:134`）には到達しない。実測前に「この node を KILLED」と登録しないこと。

9. **real — adapter 単独 commit にも実装 author 要件が掛かる。**
   `tools/check_ai_provenance.py:75` は `.codex/` を実装面に含め、`:1599` は AI 関与の実装 commit に Codex `role=author` を要求する。親 integrator だけの trailer で adapter commit を分離すると、この検査に抵触する。
   **成果物影響:** 最終 tree が正しくても履歴 provenance 監査が不受理になる。

10. **判定不能 — fix 子の見出し欠落への再発防止。**
    trigger-gating の7箇所漏れは plan.md:205–221 の coder entry と件数 assertion で対策されている。一方、先例 README:31 の「rc=0 でも必須見出し欠落で未受理」への明示的対策は plan にない。実際の子 dispatch／出力検査が未提示なので再発回避は確認できない。

## brief の実配線節への判定 (事実ごとに 確認/反証)

| 事実 | 判定 |
|---|---|
| bench の 100k／t4／extime1／reps2 | **確認。ただし配線用既定値限定。** 3 driver で共有。receipt による規模差し替えという推論は反証。 |
| verify は legacy 200 records／1 rep | **段4bでは確認、全手動経路への一般化は反証。** sort／trigger は legacy＋S2。 |
| throughput は `statistics.median` | **確認。** `pipeline.py:1458` ← `calibrator/stability.py:81` の `noise_floor()` ← `calibrator/analyze.py:252`。有効値2件なら平均。 |
| 8c の初期全 None が凍結される | **確認。** `p3_autonomous_workload_trial.py:146,4102`。`current_perf` の数値は現行全 null。leading の contention は descriptor 由来。 |
| 手動 `<baseline>` は毎 iteration 同一 | **確認済みという主張を反証。** placeholder はあるが固定規定・実績証拠がない。 |
| online digest は共通実装で latency 列なし | **確認。** `online_digest.py:45,57`、`digest.py:65,1265`。 |
| P2-5 結果が critic-experiment の現行 bytes を束縛する | **現存集計では確認できない。** `output/campaigns/p2-5-summary.json:528` は raw WAL 削除済みと明記。過去 WAL の束縛は判定不能。過去結果の再解釈・再生成は避ける。 |
| `last_delta_pct` の runbook 残存 | **確認。** s4b:52、sort:44。削除案は対象と一致。 |
| 8c の固定短文と手動 inline の区別 | **plan の区別は妥当。** 手動 inline は s4b:69、sort:64。trigger 入力例の別 drift は未修正として残る。 |

## 推奨する plan v2 への修正

- Measurement 節に「段4b＝legacy、段5 sort／段8a＝legacy＋S2」を明記する。bench は配線用既定値と、その走行で確定した設定を区別する。
- 手動 baseline 凍結を既存実績と書かない。「今回の適用版から明文化する運用規定」なのか、既存の権威ある規定を説明するのかを明示する。
- M1 は「3 role の追随漏れをまとめて検出」と記録する。個別原因を証明するなら role ごとの追随欠落を分離して観測する。未実測の失敗 node 集合を確定扱いしない。
- docs・ledger・互換 baseline・adapter は、実際の author／integrator の寄与を正しく trailer に記録した**一つの整合 commit**にまとめるのが明快。分割するなら adapter commit にも実装 author 要件を満たす必要がある。
- `campaign_lock.py:49` の `CONTRACT_LOADER_RELATIVE_PATHS` に review_ledger・role 本文・adapter は含まれない。今回の分割を contract-loader の HEAD blob 不一致問題と混同しない。ただし HEAD を読む検査は最終 commit 後に実施する。
- 子の受理条件に必須見出し検査を明記し、CLI rc=0 と受理完了を分ける。T-2528 と同じく helper 外の比較処理が変わっていないことも監査対象にする。

## 総括

plan は pin 追随・adapter 差分・M2 の扱いを概ね正しく捉えている。修正が必要なのは、**verify の適用範囲、手動 baseline の根拠、M1 の証明範囲、adapter commit の provenance 要件**である。

静的検査のみ。テスト成功・変異 kill・consumer 完全閉包は未確認。