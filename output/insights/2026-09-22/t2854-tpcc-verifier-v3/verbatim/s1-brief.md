# [T-2854] 単位 4 — verifier の v3 parse と (table, key)、anomaly の表・取引種別 — 段 1 brief (親)

wave: dev-wave-t2854-tpcc-verifier-v3 / branch worktree-dev-wave-t2854-tpcc-verifier-v3 / 起点 local main eef04f5a7
(worktree 作成は 8fd2a2f5c から、作成中に main が進んだので ff-only。8fd2a2f5c..eef04f5a7 に verifier・test_verifier.py の差分なし。開始 gate fresh rc=0)
worktree: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3
job dir: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3

## 研究前進
D2212 項 2 (第 31 回裁定 項 2 で確定) の TPC-C 段 1 認定の verifier 側。本単位が無いと、単位 1〜3 の v3 trace を
verifier が C 行 10 token で ParseError にし、単位 5 (pipeline allowlist・witness・段 1 の正例負例) を始められない。
完了判定: 設計 §3.1 の v3 frame に従う合成 fixture が object 経路と compact 経路 (packed / tuple) の両方で同じ結果になり、
表だけが違う同一 key bytes (例: Warehouse(1) と Item(1)、NewOrder と Order の同じ key) が別 object として扱われ、
cycle の anomaly に表番号と取引種別が載る。YCSB (v2) の受理・拒否・判定・result_to_dict の bytes は不変。

## scope (本題だけ)
- 変更面 (実アンカーは下表): orchestrator/verifier/{parse,model,dsg,core}.py と orchestrator/tests/test_verifier.py。
- scope 外: 実 emitter との結合、pipeline allowlist (orchestrator/campaign/pipeline.py)、witness 試験、段 1 の正例・負例 (単位 5)、
  §3.3 の存在履歴の意味 (insert 前の unborn・delete 版の読み・genesis 誤用の integrity) — これは本単位の列挙に無いので後続へ残す、
  S/Q 行 (段 2)、CLI・pipeline への新出力の配線、gate・検査・台帳の追加、CCBench の編集。

## 確定済みユーザー裁定・前提
- D2212 項 2・第 31 回項 2: TPC-C は段 1 → 段 2 の順で必須。本 wave は依頼で単位 4 に限定。
- 設計 output/insights/2026-09-21/tpcc-trace-certification-design/README.md §3.1 (v3 frame、verifier 変更表) と §7.1 単位 4。
- 並走 wave [058df1] (単位 1・2、CCBench 側) の返信 (外部データ、向こうの段 4 で確定): C 10 token・R/W/X に table、段 1 は nS=nQ=0 固定、
  tx_type は 1..5 で 0 を出さない、I 行は v3 でも出さない、P/E は v2 と同形、A 行は silo から出ない。
- 一次資料で確認: Storage 列挙 Warehouse=0, District=1, Customer=2, CustomerSecondary=3, History=4, NewOrder=5, Order=6,
  OrderSecondary=7, OrderLine=8, Item=9, Stock=10 (Size=11 は番兵、external/ccbench/include/tpcc/tpcc_tables.hh:16-28)、
  TxType None=0, NewOrder=1..StockLevel=5 (include/tpcc/tpcc_query.hh:19-26)。現 pin の X emitter は silo の 3 箇所だけ、I emitter は無い。

## 不変条件
1. v2 (C 7 token) の受理・拒否集合、verdict、integrity の各値と notes の文言、result_to_dict の bytes、witness の選択順は不変。
   既存テストの期待値を変えない (反転・緩和・skip・削除禁止)。
2. v1 (C 5 token) の拒否を維持。C の token 数は 7 と 10 だけ受理。
3. orchestrator/verifier/report.py は編集しない (silo_ladder_rung1 の verifier_module が bytes を束縛、設計 §3.1)。
4. 1 run の中で v2 と v3 の混在は拒否 (ファイルを跨ぐ場合を含む。compact は親の merge、legacy は逐次で)。
5. v3 の object 経路 (_LegacyTrace → DSG(txns)) と compact 経路 (packed / tuple の両方) は同じ verdict・integrity・辺集合・witness を返す。
6. 規律 2・3: 形式違反は ParseError か integrity (indeterminate) に倒し、certified を今より広げない。anomaly は構造化して返す。
7. orchestrator/verifier/ に新 module を足さない (campaign_lock.py の CONTRACT_LOADER_RELATIVE_PATHS 等の source closure に
   verifier の各 file が列挙されているため。新 module は closure 改訂 = scope 外)。
8. 新しい test file・fixture dir を足さない (inventory / 全 fixture を回す baseline test を動かさない)。合成 fixture は既存の
   _tmp_trace 形で test 内に書く。
9. 既存 golden の実測 (段 1 の閉包検索、Explore 子): test_verifier.py:2657-2663 が EdgeReason の dataclass 自動 repr を文字列で
   固定しているので、EdgeReason (と repr / eq が固定されうる基底 dataclass) に field を足さない。EdgeReason.key は生の hex 文字列の
   まま (同 file の 12 箇所が "key": "<hex>" を固定)。verifier 4 file の sha256 を固定比較する test は 0 件、source closure
   (campaign_lock.py ほか) は実行時 hash なので中身の編集では赤にならない (path の増減・順序は不可 → 不変条件 7)。

## 親の provisional 裁定 (攻撃対象)
- (P1) schema 判定は C の token 数 (7=v2, 10=v3)。最初の C が run の schema を決め、以後の異なる schema の C は ParseError。
- (P2) v3 frame 内の R=6, W=7, X=5, I=5 token。v2 形の行は ParseError。table は 10 進整数で 0..10、tx_type は 1..5、
  v3 の W op は U/I/D のどれか。違反は ParseError (表番号の欠落・範囲外は拒否、設計 §3.1)。v2 の op は従来どおり検査しない。
- (P3) 段 1 では nS / nQ は 0 だけ受理 (非 0 は ParseError「段 2 未対応」)。S/Q tag は未知 tag のまま ParseError。
- (P4) v3 の I 行は X と同形で受理し write_intent_violations へ (実 emitter は出さないが、出たら indeterminate に倒す)。
- (P5) object identity は v2 = key 文字列のまま (内部 map・順序を変えない)、v3 = (table, key_hex)。表現は plan が決める。
- (P6) 表・取引種別は基底 dataclass に field を足さずに持つ: v3 だけが作る派生型 (例: EdgeReason を継承し table を足した型) か、
  Anomaly と並ぶ別構造。v2 の object は型・repr・eq・result_to_dict とも今と同一。v3 用の構造化出力 (理由ごとの表、cycle 節点ごとの
  取引種別) は report.py でない既存 module (core.py など) の新関数に置く。CLI・pipeline への配線は単位 5。Read/Write/Txn に
  field を足すかも同じ基準 (repr / eq を固定する既存 test の有無を plan が実測) で決める。
- (P7) §3.3 の存在履歴 (op の意味) は本単位で実装しない。v3 でも op は辺に使わない (v2 と同じ)。本 wave の verifier は
  v3 trace に certified を返しうるが、pipeline が tpcc binary を trace 前に拒否するので本番の認定経路には乗らない
  (親の実測: verify_trace_dir の本番側の呼び手は orchestrator/campaign/pipeline.py:44,506 (capability 版、_run_trace が :434-437 で
  `ycsb_` 以外を _TraceWitnessUnsupportedWorkload で拒否) と silo_ladder_rung1.py:3048-3058 (既存 YCSB trace の再検証) の 2 つだけ)。

## 変更面 (実アンカー、main 8fd2a2f5c)
| file | anchor | 変更 |
|---|---|---|
| model.py | :314-339 Read/Write/Txn | table / tx_type / schema |
| model.py | :352-389 EdgeReason/Anomaly/CycleEdge | table、節点の tx_type |
| parse.py | :296-470 _parse_file | v3 分岐と厳格検査、run 内 schema 固定 |
| parse.py | :181-201 _ParsedFileColumns, :520-544 _txn_from_columns, :547-620 _parse_file_to_columns | (table, key) の interning と列 |
| parse.py | :716-785 _merge_issues_and_winners, :788-805 _finish_legacy_parse | ファイル跨ぎの schema 混在 |
| dsg.py | :344-370 _build, :645-679 辺 | object 経路の identity |
| dsg.py | :388-490 _build_compact_packed, :492-527 _build_compact_tuple, :198-303 _edge_candidates_for_task | compact 経路の identity |
| dsg.py | :764-803 _txn_for_id/_reasons, :826-849 anomalies | 表・取引種別の復元 |
| core.py | :28-190 verify_trace_dir | X/I の notes (v2 文言不変)、v3 構造化出力の置き場 |
| tests | orchestrator/tests/test_verifier.py | v3 の正例・負例、両経路一致、v2 不変 |

## 分割・環境
- 実装子は Codex author 1 本 (4 file が同じ identity 表現を共有する一枚岩)。
- 受入は tools/dev_wave_wait.py acceptance。焦点走は test_verifier.py + DW-O26 の consumer (critic digest、commit_receipt、pipeline 系) + inventory 4 群。
- 計算: 受入 1〜2 回 (1 回 ≈ 0.25 node 時間) + 焦点走・変異で合計 2 node 時間未満の見込み (D2212 項 4 の確認不要域)。
- 全 9 段: 受理集合が変わり正しさ防壁 (verifier) に触るので独立の敵対検証子が必須 (DW-C00)。
