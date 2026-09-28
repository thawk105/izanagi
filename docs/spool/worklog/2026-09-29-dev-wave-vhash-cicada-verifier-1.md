---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-vhash-cicada-verifier
seq: 1
title: Cicada の実行履歴を判定器に掛けられるようにした — trace patch・壊し patch 3 本・fixture テスト。stock は巡回 0、壊し 3 本は全部巡回を検出し壊した経路に帰属、TRACE=0 は命令列一致 (patch + test + insight、branch worktree-dev-wave-vhash-cicada-verifier)
---

## 本文

- 依頼: VHash 論文の並行 wave md_3 (ユーザー依頼により親セッションが作成、`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_3.txt`)。一次資料 `output/insights/2026-09-29/vhash-cicada-verifier/README.md`、置き場と範囲の判断は {{D:cicada-trace-prototype-patch}}。
- ユーザーは夜間不在 (マネージャー連絡)。依頼の「検査器の変更とテスト」を「判定器の production は変えず、既存の読み込みを Cicada 形の fixture テストで固定する」と読み替えたのは、段 3 相談 2 本の賛否を材料に親が決めた ({{D:cicada-trace-prototype-patch}} 項 4)。
- peer 連絡 2 件を自分で裏取りして採用: `patches/ledger.json` は entries 1 件固定なので README だけに登録、patch の新しい `#if` 条件は条件 gate の定義一覧照合 (`orchestrator/tests/test_ccbench_spawn_sites.py`) に掛かるので `TRACE` 以外を書かない。
- 事前登録の外れ: 判定器側の変異 M-V1 (版の圧縮で tid を 31 bit に狭める) は「変更前 HEAD では生き残る」と登録したが、既存の境界テストが検出した。新テストは同じ変異を追加 3 node で検出するが、新テストだけが検出する差分は示していない (一次資料 §6)。
- 工程の不具合 3 件 (いずれも判定基準は変えずに直した): (1) 生死確認 1 回目は起動器が workload 別 target の compile command 4 件を 1 件に絞れず停止、(2) 本走 1 回目は判定器の代表 witness 20 件 (終盤) と事象の先頭 200 件打ち切り (序盤) が作りとして重ならず帰属 0、(3) 本走 2 回目は gen_S の混雑で dispatch の全体時限 (待ちを含む) に当たり未開始のまま自動取消 (`--overall-grace` を足した)。
- 段 6 レビュー: 観点 A (RV-1〜3) と B (B1〜B5)。帰属の未証明 (RV-1 / B1) は全件出力の再走と親の raw 照合で閉じた。TRACE=0 の主張は YCSB target の 3 TU に限定 (RV-3)。B4 (全件出力と焦点 job の縮小) は不採用。
- 計算ノード: job 8 本で Elapse 合計 434 s (受入・変異の dispatch を除く)。Codex (gpt-6-sol、medium): plan 1、相談 2、author 3、fix 3、review 2。

## 次の一手差分

### 新規

- {{T:cicada-trace-followups}} **P2・新規 (VHash 前提 G0 の後続)**: Cicada の trace (`patches/instr-cicada-trace.patch`、{{D:cicada-trace-prototype-patch}}) は YCSB point read / update の巡回検出まで働く (一次資料 `output/insights/2026-09-29/vhash-cicada-verifier/README.md`)。残り: (1) forwarding 試作を instr patch に重ねて同じ起動器で検査する (巡回なしは indeterminate であって certified ではない)、(2) certified を要する campaign の門へ入れるなら Cicada 用の証拠面と campaign 側の trace 供給の設計 (研究前進の裁定候補)、(3) pin を C から進めたら 4 patch の厳密適用と生死確認の取り直し、(4) 未対応 = scan の phantom・insert / delete・版昇格 (`#error`)・`group_commit>0`・YCSB 以外、TRACE=0 は tpcc / bomb / sbomb の TU が未比較、(5) trace hook の `izanagi-trace` 枝への移送は人間の判断。
