---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2385-t2437-record-producer
seq: 1
title: [T-2437] result-evidence record の producer core API を新設し、rejected の witness class を consumer と同じ規則で導く — [T-2385] は D1768 で解消済みと確認 (コード + テスト + insight、branch worktree-dev-wave-t2385-t2437-record-producer、変異 16/16 KILLED・期待 node 完全一致・登録 SURVIVED 2)
---

## 本文

- **依頼の前提が 1 点、着手前の local main で既に覆っていた。** [T-2385] が指す「8c formal consumer が
  rejected 側で `candidate_attributable` / `truncated` / `witness_class_sha256s` を要求する」状態は、
  D1768 (2026-09-08 着地) が consumer を WAL の `reason` と `verify.*` を読む形へ修理して解消済みで
  あった。`orchestrator/campaign/` に 3 field の producer 側出現は無く、WAL 側の「producer を書くか
  consumer を合わせるか」は再度開かなかった。残る鎖は [T-2437] (record 層 producer の不在) だけで、
  これを本題にした。一次資料は `output/insights/2026-09-08_t2437-record-producer/README.md`。
- **方向は「record 層 producer を書く」。** record の `constraint_sha256` は FC04 / FC07 / FC09 の
  3 等式と ledger の必須条件で束縛され、consumer 側を合わせる余地が無い (段 2 が file:line で裏取り)。
  設計判断は {{D:result-evidence-producer-core-api}}。
- **「producer が書く boolean が恒真にならない」は 3 方向分岐の実証として読み替えた。** 現行契約に
  boolean は無く、`physical_result` は `outcome ∈ {accepted, rejected}` と `constraint_sha256` である。
  synthetic Silo source 束縛の実 verifier 走で、accepted (g4/g1/p1 等)、rejected + class
  (r9/r3/r1)、発行拒否 (integrity_orphan・m2 = indeterminate、r4/r5 = dirty で cycle あり、
  r8 = 4 class、r9 `max_report=0` = 切詰め) の 3 方向すべてに実 fixture で到達することを示した。
  複数 class の実 fixture (`r8_silo_broken_norw`、total_cycles=4) は親の初回走査 (8 件) では
  見つからず、全 22 fixture の走査で見つけた。8 件からの「無い」の一般化は誤りだった。
- **段 3 の敵対相談が親の provisional 裁定を 2 点覆した。** (1) typed `VerifyResult` 単独の導出では
  terminal WAL と結合されず、consumer が FC07 で落とす record を発行できる → producer は
  projection の bytes を第一入力にし、typed 結果には WAL に凍結された snapshot との canonical bytes
  同値を要求する形へ変えた。(2) ordered WAL projection の producer (S3) は source WAL の追記寿命を
  本 wave 単独で閉じられない → issuer 配線と同じ carry へ送った。さらに `total_cycles` は SCC 数で
  class 数ではない (1 SCC 内の複数 simple cycle は verifier が代表 1 件へ縮約する) と指摘され、
  現物 (`dsg.py`) で確認した。class の定義は D1768 のままとし、uniqueness の再定義はユーザー裁定へ返す。
- **段 6 の敵対レビュー 2 本が独立に同じ穴を見つけた。** 導出結果と record が参照する projection が
  digest で束縛されておらず、同じ attempt の別 projection を参照する record を正常発行できた。
  加えて consumer の `_wal_field()` が top-level を優先するのに producer は payload しか読まないため、
  root shadow で両者が乖離する点、変異 M2〜M5 が typed 層と wire 層の重複検査に mask される点、
  `verify_configs` の境界負例 (空・prefix・逆順・重複) と実 issuer 経由の統合 test の欠落を指摘した。
  fix 1 巡で閉じ、焦点再レビューは closed 10 / partial 0 / regressed 0 / pending-parent 1 (台帳、親)。
- **consumer の bytes は変わったが受理集合は不変。** witness の構造検査と class digest を
  `reflux_result_evidence.py` へ逐語移動し、consumer は wrapper で呼ぶ。既存 FC07 test 全件緑、
  変更した既存 test は monkeypatch の owner 移動 1 件だけ。fixture builder・baseline JSON・
  golden 4 個・`wal.py`・`pipeline.py`・verifier は 1 byte も変えていない (`git diff --exit-code`)。
- **子はどの段でも `tools/run_tests.py` を通せなかった** (sandbox の `qstat -Q` preflight で rc=16)。
  実走はすべて親が計算ノードで行った: 焦点走 8 file を 2 回 (853 → 865 passed、いずれも赤 0)、
  新規 36 node は JUnit に実名で存在。受入所要台帳へはこの 36 node だけを実測値で `--add-only` した
  (同じ JUnit には base 時点で未登録の他 file 95 node も含まれていたが、main が台帳を進めているため
  本 wave の node に絞った)。
- **変異検査は負例変異 16 件すべてを殺した** (probe → 本走の 2 段、HEAD 8b26f3246、baseline PASSED、期待 node 完全一致、MISMATCH 0)。M2〜M4 は typed 層と wire 層の重複検査に mask されるため両層同時の複合変異で登録した。登録 SURVIVED 2 件: MP1 (拒否文言だけの正例) と **M14b** (cycle 節点の exact int を `isinstance` へ緩める変異。負例 `cycle-bool` が txid 0 の位置に `True` を置くため ring 位置検査が先に拒否する過剰決定で、[T-2438] と同族)。
- **受入全走:** 本記録 commit の時点では未実施。本 commit の後に投入し、結果は追記 commit と受入再走で確定する。
- **段取りのつまずき:** 同名 wave が別 session で約 1.5 分遅れて重複起動した。job dir の作成時刻で
  先後を実測し、後発が降りた (共有 path は未作成)。

## 次の一手差分

### 完了

- [T-2385] consumer が要求していた rejected 側の 3 field は D1768 で廃止され、consumer は WAL の
  `reason` と `verify.*` を読む。producer 側の 3 field は書かない。record 層の残余は [T-2437] へ。
  remaining: none
  base: c2dcf3f151aad77ad77bca638eff1c08241eeedff9b5bcfb63230f50e5d9f671

### 更新

- [T-2437] **P2**: record 層の producer core API (`derive_physical_result` / `assemble_result_evidence_record` /
  `issue_result_evidence_record`、{{D:result-evidence-producer-core-api}}) を新設し、rejected の
  `constraint_sha256` を consumer と同じ規則 (共有 `witness_class_sha256`) で導き、導出を terminal WAL
  projection の bytes へ束縛した。**残るのは production issuer への配線**: `EvalResult` への
  `VerifyResult` 保持、`run_campaign()` 最終化点での issue 呼び出し、ordered WAL projection を
  `wal.jsonl` の 1 attempt 区間から作る producer (per-query WAL の不変性を前提、D1616)、
  `run_origin_trial` の production 呼び手。設計 §9 の V-8/V-9 と同じ束。
  base: d0b7682197172b739e76726b3f582a7f531e487131c856e787ed8bfa8d7b8a80

- [T-2438] **P3**: witness anomaly の `length` と edge 端点の型検査を `type(x) is int` から
  `isinstance` へ緩めても現行の負例 (float を使う) では検出できず、開くのは bool の穴だけである
  (変異 `b060.m23` / `b060.m24` は登録 SURVIVED)。**2026-09-08 追記: producer 側
  (`reflux_result_evidence.py`) でも同型が再現した。** 変異 M14b (cycle 節点の `type(x) is int` を
  `isinstance` へ) が生存。負例 `cycle-bool` は txid 0 の位置に `True` を置くため ring 位置検査が先に
  拒否する過剰決定で、登録 SURVIVED のまま。bool 負例を足すか、厳密さを要求しない設計に改めるかを決める。
  base: efed5e00a783ac687c3904d9bd359d09a4730ca7b4018fbbd6cba543815cc0d8

### 新規

- {{T:witness-class-scc-representative}} **P3・ユーザー裁定待ち**: witness class の定義。現行
  (D1768) は「verifier が SCC ごとに報告する代表 witness 1 件の canonical JSON digest」で、
  `total_cycles` は SCC 数である。1 SCC 内の複数 simple cycle は代表 1 件へ縮約されるため、
  設計 §3.4 の「複数 class から 1 件を選ばない」は SCC 単位でしか成立しない。選択肢: (a) 現行維持し
  設計 §3.4 に「class = SCC 代表 witness」を追記 (推奨、機構追加なし) / (b) verifier 出力へ
  SCC 内 cycle 数または uniqueness proof を追加 (verifier の出力 bytes が変わる) / (c) 構造同値類を
  定義 (D1768 限界の再訪)。
