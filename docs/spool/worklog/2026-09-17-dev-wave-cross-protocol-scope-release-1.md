---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-cross-protocol-scope-release
seq: 1
title: Silo 固定スコープを解除して mocc 第 2 例の準備に着手し、pin 再承認は D1603 / D2104 項 13 の手続きに残した (docs のみ、branch worktree-dev-wave-cross-protocol-scope-release、変異 matrix = 実装面差分ゼロにつき免除)
---

## 本文

- **起点 = ユーザーの `/dev-wave` 引数「今もスコープはsiloベースに固定されている？それ解除した方が良いのでは？」**
  と補足 2 件 (「2026-07-27の裁定かな」「今の所論文のパンチが弱いから、クロスプロトコル対応を可能にしておいた
  方が良いのかなと思う。他方、クロスプロトコルの道具としてccbench側に近年の新しい手法を追加するとかも優先度
  高いかなぁ」)。逐語と裁定の一次資料 = `output/insights/2026-09-17/cross-protocol-scope-release/README.md`
- **答え: 3 面とも固定されていた。** 裁定 = phase3.md 2026-07-27 改訂 (1) に失効宣言なし。実装 = 基盤
  (genome 空間・floor の protocol 別 baseline・層 3 の protocol 照合・較正 4 件) は 09-01 / 09-02 に進んだが、
  between-run floor は D1373 の関門 (mocc hook が現行 pin の非祖先) で未実測、非 Silo (mocc / tictoc / cicada) の
  性能比較は 0 件、mocc は変異探索面外 (D579)。論文 = paper-story 2026-09-17 版が C-1 を「Silo 固定した以上、必要条件ではない」と将来スコープに置く
- **決定 = {{D:cross-protocol-scope-release}}。** 方向 (合成対象を Silo に限定しない、cross-protocol 対応を可能に
  しておく) はユーザーの直接発話、射程・順序・準備の鎖は親の裁定として分けて記録した。発話は pin 前進の
  再承認・A→B の厳密順序・C-1 の必須化までは含まない。D2104 項 13 (今日の一括承認の 1 項) の実測保留と pin
  再承認の手続きは維持し、同項に「主経路完了まで」の期限が無いことを訂正した
- **親 brief の誤り 3 件を段 2 / 段 3 が訂正した:** 層 3 の protocol 照合キーは [T-2115] で実装済み、文献調査は
  一括停止でない (D2095 / D1760 / D1931 の射程)、D2104 項 13 に期限なし。「較正 4 件・性能比較 0 件」は
  protocol (mocc / tictoc 各 2 件、cicada 0 件) と用途を添えて書き直した
- **段 2 plan を段 3 の 2 レンズ (論文価値 / 主経路衝突) で検討し、親が段 4 で裁定した。両レンズの P1〜P4 の
  判定ラベルは一致** (修正して採用 / 却下 / 修正して採用 / 修正して採用)。plan の C-1 の B 群化案は採らず、
  第 2 例の証拠と C-1 を分離した。レンズ A 13 件 (real 10 / refuted 3)、レンズ B 10 件 (real 7 / refuted 3)。
  最重要 3 件: (1) pin の full SHA 束縛は実在し D297 合格では置換できない — ただし過去の certified 判定は
  無効化されず、新 pin 系列の登録・identity・凍結の更新が要る (親の P2 を却下)、(2) 第 2 例の合成実証
  (mocc variant 対 名指し stock) と C-1 (protocol 横断の stock 最良比較) は別項、(3) 近年手法の候補は
  literature map に NeurCC (2025) / ATCC (2026) が調査入口として実在 (「候補 0 件」は誤り)
- 素材: 第 2 例で強まる主張の上限は「指定した二つの CC 実装で合成・評価手順を実証した」まで。LLM 固有・
  descriptor 因果・無人自律は増分なし。**論文のパンチの主因は第 2 例だけでは埋まらず、B-1 / B-5 / A-1 側にも
  ある** (レンズ A R3、本 wave の scope 外)
- docs 変更: phase3.md (2026-09-17 改訂節、現行チェックポイント・must 表 S1 行・後続段 7 の発火条件の二分)、
  paper-story README (stale 注記 1 件)、decisions fragment 1 件、insight (SHA 束縛表・観測した候補 OID
  `e9e477ca1b55348ab4530de0b1cf663ce4555290`・T 5 本の完了条件・逐語 9 file)。roadmap 本体は非改訂
- 段 6 = docs 差分への敵対レビュー 1 本。受入全走 = (受入後に記入)。`check_docs` rc=0。変異 matrix は
  実装面差分ゼロにつき免除 (DW-S04)
- エージェント工数: codex 4 本 (plan 1、consult 2、review 1)。計測ゼロ、build ゼロ

## 次の一手差分

### 新規

- {{T:cross-protocol-pin-evidence}} **P1・新規** ({{D:cross-protocol-scope-release}} 項 3): D1603 の材料 3 点を揃え、
  見送り台帳の ccbench pin 更新項の再承認として提示できる状態にする — (1) 候補 full OID の確定 (初回は mocc
  単独: hook branch `izanagi-t1943-mocc-g2-readfrom-witness` の先端 `e9e477ca1b55348ab4530de0b1cf663ce4555290`
  を観測済み、採用の確定は本項)、(2) `tools/check_trace0_preprocess_identity.py` による D297 検査の結果
  (前処理比較、実 build 不要、login node 可。checker の保証範囲 = SILO_SPACE の context・mocc trace.hh 1 行
  特例を材料に明記)、(3) 承認済み定数・事前登録・identity・凍結への波及表 (骨格 = insight §5)。検査が拒否した
  場合も「前進可能」とは判定しない。superproject の gitlink は動かさない
- {{T:mocc-mutation-proof-design}} **P1・新規** (同 項 1、D579): mocc を変異探索面へ入れるために D579 が要求する
  独立の auditor-live 相当の機械実証を設計する — hole 位置、auditor 入力、X/P/I・hot/cold lock 被覆、陽性 /
  陰性 control と期待拒否を後続実装者が使える形で固定。設計完了で変異探索を解禁しない。チェックリストの再掲に
  留まるなら実証 wave の plan 段へ統合する
- {{T:recent-cc-candidate-selection}} **P2・新規** (同 項 4): 近年 CC 手法の候補表 (一次資料・実装可用性・
  ライセンス・YCSB 適合・trace 移植費用・証明面・既存 CC との差) と追加対象・棄却理由を提示する。入口 =
  literature map の NeurCC (2025) / ATCC (2026)。D2095 と重複取得しない。CCBench への実装追加とは分け、
  A (mocc 第 2 例) に従属させない
- {{T:tictoc-trace-hook}} **P2・新規** (同 項 4、mocc 達成の必須鎖外): submodule branch 上で `TsWord` 版 ID の
  trace-hook と positive / negative control を用意し、branch commit と control 証拠を保存する。TicToc の正式
  編集面認可が前提 (D579 の mocc 限定認可は流用不可)。push は人間。初回の pin 候補には積まない
- {{T:tictoc-floor-baseline}} **P2・新規** (同 項 4): `orchestrator/campaign/between_run_floor.py` の `BASELINES`
  に根拠つき TicToc baseline を追加し、引数解析・protocol 別出力・hook 不在時拒否を確認する。完了条件に実測を
  含めない (単独では測定は開通しない — hook と pin 再承認が別途要る)

### 見送り追記

- [T-167] 【2026-09-17 追記: {{D:cross-protocol-scope-release}} により材料整備 ({{T:cross-protocol-pin-evidence}}) へ着手。pin 更新は未承認のまま。材料 3 点が揃った時点で本項の再承認として提示する。旧候補 `c9c1a9c` (2026-07 承認) を今回の採用候補とはみなさない】
