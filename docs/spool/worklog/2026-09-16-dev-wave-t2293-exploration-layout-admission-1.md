---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2293-exploration-layout-admission
seq: 1
title: [T-2293] 起点試行の証拠発行器の受理型に探索 layout を加え、維持する拒否述語を負例で固定した (コード、branch worktree-dev-wave-t2293-exploration-layout-admission、変異 matrix = baseline PASSED・5/5 KILLED・等価変異 1 件 SURVIVED (登録どおり)・MISMATCH 0・期待 node 完全一致)
---

## 本文

- **依頼の scope**: D2044 項 2 (2026-09-16 ユーザー裁定) の Q1 だけ — 証拠発行器の受理型に探索 layout を加え、
  加えるときは維持する拒否述語と負例を同時に確定する。Q2〜Q4 (台帳遷移の責任境界・起点専用 entry point・完了判定の
  書き換え) は D1875 の整合が決まるまで着手しない。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
  受理集合が変わる段なので軽量版にせず、段 2 plan・段 3 相談 2 本・段 6 レビュー 2 本 + focus 再レビュー 1 本を回した。
  実装は Codex author 1 本 + fix 1 本 (D95)。稼働中の [T-1232] wave (`autonomous_trial_completeness.py`) とは編集面が
  重ならないことを段 1 で照合した。残骸 worktree `dev-wave-t2293-origin-producer` (7ecf1ed66) は引き継いでいない。
- **段 3 が段 2 plan の述語を real で覆した**: plan の `type(layout) not in (CampaignLayout, ExplorationCampaignLayout)` は
  tuple 所属 (`is` または `==`) なので、metaclass の `__eq__` を持つ別型が通る。親が最小再現で確認し、identity 比較
  (`is not ... and is not ...`) へ改め、impostor 負例と変異 M5 を加えた。設計判断は
  {{D:origin-evidence-issuer-admits-exploration-layout}}。
- **段 6 レビュー B の must-fix 1 件を fix で閉じた**: 負例 helper に `layout=real` の正例が同居していたため、変異 M3
  (内側 gate を旧形へ戻す) で負例 node 2 件が「正例の過剰拒否」という別理由で赤化する。正例を独立 test
  `test_ordered_wal_projection_accepts_exact_layouts[official|exploration]` へ分離し、M3 の期待集合を実走前に 3 件へ
  改訂した (理由は一次資料 §4)。レビュー A は所見ゼロ。focus 再レビューは全所見 closed、新規所見なし。
- **親の記述を訂正した**: 「`_context_roots` の root 包含は探索でも維持される」は brief の probe では観測できておらず
  (型 gate が先に発火)、実装後の負例で初めて発火を観測した。「record bytes 不変」は「既存入力に対する生成規則と
  schema が不変」に限定する (root が違えば ref path・projection・record bytes は違う)。「pin 閉包 hit なし」は
  `git grep` の申告であって probe の帰結ではない。brief の「探索 layout は WAL 5 frame まで通る」は test helper が
  WAL を作ったことであり producer 内の消費ではない。
- **統合正例は skip ではなく実走した**: `test_real_run_campaign_exploration_issues_rejected_record` は焦点走で PASSED
  (skip 0)。`loop.run_campaign(declared_use_class="exploration", result_evidence_context=...)` を stub 無しで通り、
  探索 physical root 配下に source-WAL / projection / provenance が置かれ、record が resolve できた。
- **変異 matrix**: probe 走 (全件 SURVIVED 登録) で観測 node を集め、spec v2 の期待集合と 6 変異すべて一致した
  (M1=2、M2=6、M5=2、M3=3、M4=3、M6=0)。本走 (spec sha256 1450ebb8…、repo_head ef5491bf8) は baseline PASSED、
  5/5 KILLED、等価変異 M6 SURVIVED、MISMATCH 0、期待 node 完全一致。足した実効 gate は「探索 layout の受理」(M3/M4 の
  過剰拒否正例) と「identity 同一性の維持」(M1/M2/M5 の緩和負例) の 2 つ。外側 gate 単独の緩和は内側が重複拒否するので
  登録していない (冗長 gate として残す)。台帳は一次資料 `mutation/`。
- **検査 (記録前の実走)**: 焦点走 4 file (変更 2 + consumer `test_reflux_formal_consumer.py` /
  `test_p3_autonomous_workload_trial.py`) 554 passed / 赤 0 / skip 0 (Pegasus 1932.nqsv)。変更 2 file の単独走
  104 passed と 16 passed。`check_ai_provenance.py --range main..HEAD` rc=0。
- **手順の事故 1 件 (実害なし)**: 変異本走の detach 起動を `&&` 連結で叩いた直後、起動していないと誤認して launcher 経由で
  再投入し、2 本目が harness の flock で rc=2 即死して pid file / log / `.done` を上書きした。1 本目は生きていたので
  pid file を合わせ、死んだ 2 本目の `.done` を除いて待ち直した。「起動直後の ps 実測」を `&&` 連結の出力欠落で
  省いたのが原因である。
- **受入全走**は本記録 commit を含む tip に対して land 前に 1 回だけ投入し、child-green でなければ land しない。
  本エントリの作成時点では未実施である。
- 工数: codex 子 7 本 (plan 1 = medium 269.6 s / 9 call、consult 2 = medium 158.1 s / 7 call と 161.7 s / 7 call、
  author 1 = medium 436.0 s / 20 call、review 2 = medium 128.4 s / 6 call と 176.3 s / 7 call、
  fix 1 = medium 108.2 s / 6 call、focus 1 = medium 191.8 s / 6 call)。

## 次の一手差分

### 更新

- [T-2293] **P1・Q1 着地 → Q2〜Q4 は D1875 の整合待ち**: 証拠発行器の受理型に探索 layout を加え、維持する拒否述語
  (subclass・impostor・duck・非 layout 値・evidence root 外の探索 root) を負例で固定した
  ({{D:origin-evidence-issuer-admits-exploration-layout}}、一次資料
  `output/insights/2026-09-16/t2293-exploration-layout-admission/README.md`)。前 wave の結線障害 B1 は解除。
  **B2〜B6 (Q2〜Q4) は未着手のまま** — 台帳の予約から封印までの production FSM、q の候補を実 source へ適用する
  起点専用 entry point (検疫・auditor veto を保つ形)、completion / report の起点分岐は、D1875 が定める整合
  (承認済み generation 予算 1 と還流設計 D106 残余 1) が決まるまで諮らない。発行 3 条件は 0/3、本番 authority 0 件、
  certified 選択・材料レポート・試行台帳の現在値は変わらない。
  base: b00f9b70572b41539945d3f2ee46804625ef86e1eb08c4ed75405540cda61010
