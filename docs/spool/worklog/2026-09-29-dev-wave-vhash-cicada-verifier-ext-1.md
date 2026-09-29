---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-vhash-cicada-verifier-ext
seq: 1
title: [T-2874] Cicada の正しさ検査を TPC-C (trace v3) と insert へ広げた — stock の TPC-C 5 走行は巡回 0、insert を壊した版は orphan read と巡回で検出・帰属、TRACE=0 は tpcc / bomb / sbomb の TU も命令列一致。Delivery を含む全 mix × 4 thread では stock Cicada 自体が gc_records の ERR で毎回落ちる (patch 2 本 + insight、計算 3 job 約 6 分、branch dev-wave-vhash-cicada-verifier-ext)
---

## 本文

- 依頼: VHash 並行 wave md_17 (`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_17.txt`)。T-2874 の (4) の一部 (insert / delete・TPC-C・tpcc TU の TRACE=0 比較)。結果・設計・限界の正本は一次資料 `output/insights/2026-09-29/vhash-cicada-verifier-ext/README.md`、判断は {{D:cicada-tpcc-trace-v3-overlay}}。
- 実際に行った手順: 段 1 brief → 段 2 plan (Codex) → 段 3 相談 2 本 → 段 4 裁定 → 段 5 author T (重ね patch と起動器) → 親レビューで `#line` の 1 ずれ (ERR の `__LINE__` が TRACE=0 の即値になる) を見つけ fix 1 回 → 統合 → 生死確認 L0 → **停止条件成立** (stock の Delivery を含む全 mix × 4 thread が `gc_records()` の ERR で異常終了) → 段 4 追補 (原因切り分け job と正例 cell の差し替え) → author B (insert の正例と帰属解析) → GC-PROBE と J1 を別 node で同時投入 → 段 6 レビュー 2 本 (must-fix 1: α の帰属で表を照合していなかった) → fix 1 回 (保存済み原本からの再計算 mode) → 親が原本で再計算 → 焦点再レビュー 1 本。
- 棄却・読み替え: 段 2 plan の壊し候補 (insert / delete を含む取引に絞って read 検査を壊す) は、相談 2 本が一致して「insert / delete の検出力を示さない」とし不採用。依頼の「巡回として検出」は、insert の意味の壊し (orphan read で事前登録) と既存の壊しの TPC-C 版 (巡回) の 2 本で満たす形に読み替えた (理由は D)。結果として insert の壊しでも巡回 1 件が出て、辺も壊した insert に帰属した。delete を壊した正例は作っていない。
- セッション異常: 16:19〜16:37 JST、land 調整役 (別 session) からの依頼で、ユーザーの git push のため git の書き込みを止めた (受領・再開とも返信)。`EnterWorktree` は name 形が filter driver 文言で、path 形が `worktree list` の 10 秒 timeout で失敗し、手動 add と Bash の cd で木に入った (既知型)。
- エージェント工数: Codex (gpt-6-sol、medium) plan 1・consult 2・author 2・fix 2・review 2・focus 1。計算ノード job 3 本 (l0-a 35456、gc-a 35506、j1-a 35507、合計約 6 分)。

## 次の一手差分

### 更新

- [T-2874] **P2・更新 (VHash 前提 G0 の後続)**: Cicada の trace (D2279) は YCSB point read / update に加え、TPC-C を trace v3 で判定器に掛けられる (`patches/instr-cicada-trace-tpcc.patch` を CCBench C1' 以降に重ねる、{{D:cicada-tpcc-trace-v3-overlay}}、一次資料 `output/insights/2026-09-29/vhash-cicada-verifier-ext/README.md`)。insert の正例 `patches/broken-cicada-insert-past-ts.patch` を判定器が検出・帰属する。TRACE=0 は tpcc / bomb / sbomb の TU も命令列一致。残り: (1) forwarding 試作を instr patch に重ねて同じ起動器で検査する (巡回なしは indeterminate であって certified ではない)、(2) certified を要する campaign の門へ入れるなら Cicada 用の証拠面と campaign 側の trace 供給の設計 (研究前進の裁定候補)、(3) pin を C から進めたら計装 2 本・壊し 4 本の厳密適用と生死確認の取り直し、(4) 未対応 = scan の phantom と不在の読み (判定器の S / Q 行と初期キー集合)・並行下の delete (stock が落ちる、{{T:cicada-gc-records-err}})・版昇格 (`#error`)・`group_commit>0`・BOMB / SBOMB の trace、(5) trace hook の `izanagi-trace` 枝への移送は人間の判断。
  base: 02ddf00b7acbf0251fc355aae403eefa8eaa9f0bcb2970376665896eaaaaa868

### 新規

- {{T:cicada-gc-records-err}} **P2・新規**: stock Cicada (CCBench pin C) の TPC-C 全 mix (Delivery を含む、F cell = 43 / 4 / 4 / 4) × 4 thread が、`gc_records()` の `if (latest->ldAcqStatus() != VersionStatus::deleted) ERR;` (`cc/cicada/transaction.cc:853`) で trace の有無に依らず毎回 (11 回中 11 回) 異常終了する。thread 1 は完走。原因を特定してから CCBench の Cicada を直す (仮説は Delivery 同士の同じ NewOrder 行の削除競合で、abort した側の削除版が aborted のまま最新版に残る形、未実証)。CCBench の変更は Codex author で上流 CI (build・format) を通す (D2277 項 1・2)。他の cell・thread 数・warehouse 数での発生は未測定。直るまで delete を含む並行 TPC-C の Cicada は評価にも正しさの門にも使えない。根拠: 一次資料 `output/insights/2026-09-29/vhash-cicada-verifier-ext/README.md` §5。
