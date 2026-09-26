---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-26
wave: dev-wave-t2854-unit11-combined
seq: 1
title: [T-2854] 残り (1) 単位 11 — C1'・C2・C3 を pin C の上へ 1 系列に並べた別名の CCBench local branch izanagi-tpcc-v3-silo-mocc (C2' 40a7f4ac) を作り、計算ノード 1 走で silo・mocc の結合確認と変異 4 件を全段合格させた。D297 の検査器は header 差分で拒否するので受理方式の 4 択をユーザーへ諮る (insight + fragment のみ、branch worktree-dev-wave-t2854-unit11-combined)
---

## 本文

- 依頼 = /dev-wave [T-2854] 残り (1) 単位 11 (逐語は insight `verbatim/request.md`)。記録の正本 = `output/insights/2026-09-26/t2854-unit11-combined/README.md`、設計判断 = {{D:tpcc-v3-combined-candidate}}。
- 開始 gate rc=0 (14:03:30 JST、着手時 local main `74e6d2f23`)。記録前に main `510aaf39d` ([T-2864] の land) へ ff-only で揃えた。
- 計算: 1 job (request 29455.nqsv、bnode084、Elapse 243 秒 ≈ 0.07 node 時間)。受入を含め 2 node 時間の線の下なのでユーザー確認は不要と判断した (D2212 項 4)。
- 段構成: 受理方式が設計択一で正しさ防壁に触るので段 2 plan 1 本・段 3 相談 2 本を残した。段 5 は Codex author 1 本 (probe 改修)、段 6 はレビュー 2 本・fix 1 巡・焦点再レビュー 1 本。Codex 子計 8 本 (gpt-6-sol / medium)、model call 112、wall 合計 1,483 秒。
- 棄却・縮小した提案: 変異は段 2 plan の 7 系統から 4 件へ縮めた (単位 1〜3 で済んだ計数順序 D/M・各 protocol の `#line` は再演しない、影響しない側の PASS を kill 条件にしない、段 3 相談 B)。受理方式の推奨は「実装まで含めた択 1 の推奨」から「設計審査と実装の委任を分けた 4 択」へ改めた (段 3 相談 A)。
- 異常: author B は自己確認の `py_compile` が作った `__pycache__` を消そうとして拒否され報告途中で停止した (改修自体は入っていた)。親が差分・自己試験・anchor 照合を補い、レビューに差分を読ませた。
- near miss: 変異 H-line の判定が TPC-C consumer を target 名で選んでおり、実際の 21 entry では 12 件になって必ず「理由違い」になる形だった。selftest の合成 row が実構成を写さず、段 6 のレビュー 2 本とも見逃した。親が前例の実測 JSON (単位 3 の `C1-preprocess.json`) で見つけ、fix で source 選択と実構成の 21 組に直した (F109 の再発として記録)。
- 受入全走と land の結果は本 fragment の commit の後に走るので、ここには書けない (land の受領証と後続記録が持つ)。

## 次の一手差分

### 更新

- [T-2854] **P1・段 1 の一部完了 (D2212 項 2、D2219 項 2)、単位 11 の材料は済 → ユーザー裁定待ち (D297 の header 差分の受理方式) と人間の push・pin 前進承認、および campaign で TPC-C を評価する配線**: TPC-C 段 1 (NewOrder / Payment、CCBench 既定比 45% + 43%、
  点読み・点書き・insert のみで `tx.scan` を使わない) の合成候補を直列化可能性で認定できるようにする。設計 = `output/insights/2026-09-21/tpcc-trace-certification-design/README.md`
  (§7.1 の実装単位、§8 の親決定)。実装は Codex author、正しさゲートは不変、trace は compile 時に除去する (規律 1)。
  **済:** 単位 1・2 (CCBench 側、D2225、`output/insights/2026-09-22/t2854-tpcc-ccbench-v3/README.md`) = CCBench の branch `izanagi-tpcc-v3-trace` (pin e9e477ca の子 C1 `56b5cb70`・C2 `a6f2c741`)。
  2026-09-23 08:4x JST に人間が GitHub へ push 済みで公開のまま残し、pin 候補ではない (D2235 項 1)。単位 4 (verifier、D2224、`output/insights/2026-09-22/t2854-tpcc-verifier-v3/README.md`)。
  単位 3 (mocc、D2230、`output/insights/2026-09-23/t2854-mocc-v3-emitter/README.md`) = branch `izanagi-tpcc-v3-mocc` (C → C1' `6aa7a58f` → C3 `53f6b097`、未 push)。
  存在履歴 (entry 1843、D2232、`output/insights/2026-09-23/t2854-v3-existence/README.md`)。単位 5 (entry 1852、D2238、`output/insights/2026-09-23/t2854-unit5-v3-wiring/README.md`) = CLI・pipeline・受領証の v3 配線、
  pipeline は `tpcc_` の 57:43 の 4 flag で受理し verifier 後に v3 を要求。実 trace (silo) は pipeline の executor で certified。
  **単位 11 (本 entry、{{D:tpcc-v3-combined-candidate}}、`output/insights/2026-09-26/t2854-unit11-combined/README.md`):** 新しい local branch `izanagi-tpcc-v3-silo-mocc` =
  C `68106660` → C1' → C3 → C2' `40a7f4acb174ca43cb590f40d13847216a1564bc` (C2 の cherry-pick、新規 commit はこれだけ)。計算ノード 1 走 (Elapse 243 秒) で C を基点に、
  TPC-C の silo・mocc とも v3 の構造・witness・内容、YCSB の silo・mocc とも v2 の certified、TRACE=0 の 21 entry の前処理と 4 binary の逆アセンブルの一致、変異 4 件 (共有 header の setter、`#line`、silo の表、mocc の種別) の KILLED を確認。
  現行の D297 検査器は C → C2' を `include/tpcc.hh` の header 差分で拒否する (rc=1)。D297 の合格・TPC-C の certified は名乗らない。
  **残り:** (1) **ユーザー裁定待ち — D297 の header 差分の受理方式** (insight §5.2 の 4 択): 択 1 D297 の header 受理規則の設計審査 (推奨、審査の承認と実装の委任は別の裁定) /
  択 2 C2' に限る代替証拠での受理 (D297 合格とは呼ばない新裁定) / 択 3 header を変えない別候補 (D2225 決定 2・3・5 と D2230 の再裁定が要る) / 択 4 当面は何もしない。
  いずれも既裁定の変更か作り直しを要するので AI の判断では採らない。**人間の手番:** branch `izanagi-tpcc-v3-silo-mocc` の push (別名なので force 不要、任意の時点で可) と、
  裁定後の pin 前進の承認 (承認後の gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` の同時更新は AI の wave、先例 D2150 / D2184)。v3 emitter が pin に入るまで、現 pin の tpcc binary は v2 を出し単位 5 の v3 要求で reject される。
  (2) campaign で TPC-C の候補を評価する配線 (設計 §7.1 の単位に無い): production の build は `ycsb_<protocol>.exe` だけを作り (buildcache)、workload の登録・flag の受け渡しも ycsb だけ。
  critic の reason 説明「YCSB allowlist 外」も TPC-C の v2 reject に合わせる (単位 5 の insight §6・§9)。
  実 trace は単位 1・2 が `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3/evidence/traces-2/`、単位 3 が `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-mocc-v3-emitter/evidence/traces-1/`、
  単位 11 (C2' の silo・mocc) が `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/evidence/traces-1/` に zstd で保持。
  段 2 へは段 1 の存在契約をそのまま広げない (削除後の再挿入で版順が存在の遷移と逆になりうる、範囲読みの不在は §4.3 の初期キー一覧、entry 1843 の insight §8)。段 2 も header を変えるので、(1) の裁定は段 2 の pin 前進にも効く。
  見送り台帳 [T-156] (selector-8b descriptor への set-size 条件) の発火条件は単位 5 で再評価した (pipeline は受理するが corpus の実体は無いので着手しない、単位 5 の insight §8)。
  設計 insight §9 の CCBench 所見 (D2219 項 7): 段 1 で観測できたのは実行時の OrderLine 番号が 0 始まりであることだけ。寿命と範囲読みの所見は [T-2855]、
  si の所見は si を走らせる wave の担当。計算: 検証走・計測・開発の検査を含め 1 タスクの job 合計が 2 node 時間以上になる投入は、見積りを示してユーザー確認後に
  投入する (D2212 項 4、D2219 項 1)。一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §10、roadmap §3.1。
  base: df0931523ca1fe87af0ab3afc45c3c977928084a249c685733faf77d297bc9fa
