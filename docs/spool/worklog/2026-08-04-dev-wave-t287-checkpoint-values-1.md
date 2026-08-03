---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-04
wave: dev-wave-t287-checkpoint-values
seq: 1
title: [T-287] checkpoint 復元境界の whiteboard 3 値を閉じた値域で検証した — 親 brief の成果物影響が過大だったことを敵対検証が反証し、残余 4 件を裁定へ返す (コード + docs、branch worktree-dev-wave-t287-checkpoint-values)
---

## 本文

- ユーザー裁定 ((115) 択 (a)) どおり `state_from_dict()` に exact `str` + 閉値域の検査を入れた。
  値域は `direction` = increase/decrease/explore_both、`magnitude` = small/medium/large、
  `result` = success/fail/rejected。正規化 (strip・大小無視・部分一致) はしない。
  実装 commit は `02a5cf9`。閉じたのは **checkpoint 復元境界だけ**である。
- **親 brief の成果物影響は過大だった。段 3 の敵対レンズ A が反証した。** 記録として残す。
  - brief が主要な攻撃として挙げた「全 `small` + 同一 `direction` の改竄で早期 `converged`」は、
    **全値が許可域内**なので本修正では防げない。自分の修正が止められない攻撃を修正の根拠に使っていた
  - 「予算超過」ではなく「`MAX_ITER` / wall budget の**上限まで消費**」。`check_stop()` は
    予算を収束より先に検査する
  - 現行承認経路 (8c は `MAX_APPROVED_GENERATIONS=1` + fresh checkpoint 必須) では 3 連続 streak が
    成立せず、terminal report にも layer3 renderer にも `selected` field が無い。よって
    **試行数変化も「最終 selected の変化」も実行経路がない**。実害が実在するのは
    human-supervised driver の後続試行数と WAL 台帳である
  - on-disk checkpoint 3 件の走査は「**現存 tracked specimen の互換確認**」であって、
    任意 `run_root`・programmatic `CampaignLayout`・archive・別 worktree・将来 producer への
    一般化ではない
  - `project_whiteboard` の production 呼出は brief の 12 箇所でなく **15 箇所** (core 6 / sort 4 / trigger 5)
- **段 6 は敵対レビュー 2 本 + fix 2 巡 + 焦点再レビューを要した。実装ではなくテストの検出力が問題だった。**
  - 1 巡目 (レビュー B B6-01/B6-02): 負例がすべて whiteboard 1 件構成で `entry[0]` しか検査せず、
    「先頭 entry だけ検査する」変異が全 node を生存した。メッセージも部分一致だけで、
    許可値リスト削除・index 固定・値域順序入替えの 3 変異が生存した
  - 2 巡目 (焦点再レビュー F-01/F-02): 1 巡目 fix 後も「**末尾 entry だけ検査する**」変異が生存した
    (負例の破損 entry が常に末尾だったため)。完全一致メッセージも `result` + `受領型=str` の 1 形しか
    固定せず、許可値を result 集合に固定する変異と型名を `str` に誤報する変異が生存した
  - 2 巡目 fix で位置 (先頭/中間/末尾) とパラメータ (3 field × 非 str 2 型) の両クラスを閉じた
- **変異本走で事前登録の表記ゆれが露見した (F33 同型)。** 初回は M1 が MISMATCH で停止した。
  mutant 自体は kill されており (rc=1、期待 8 node がすべて赤)、原因は `drive_iteration` 系 3 node が
  記録側で `@real-repo` 接尾辞付きになることを事前登録が知らなかったことだけである。
  `DW-M08` の「突き合わせ前に同じ形式へ正規化する」に従って spec を訂正し再走した。
  初回台帳は `mutation-ledger-v1-mismatch.json` として erratum に残した (`DW-M02`)
- **段 3 / 段 6 の敵対子が独立に見つけた real 所見 4 件を実装せず裁定へ返す** ({{T:t287-producer-domain}}、
  {{T:t287-layer3-reader}}、{{T:t287-checkpoint-integrity}}、{{T:t287-error-message-redaction}})。
  裁定パッケージは `output/insights/2026-08-04_t287-checkpoint-values/adjudication-package.md`
- 受入は Pegasus gen_S 計算ノードで実測した。焦点 3 file = 154 passed、全走 = 5393 passed / 19 skipped。
  `check_docs.py` rc=0、provenance full 監査 rc=0。codex 実装子は Pegasus ログインノード規律に従い
  pytest を実走せず、緑の主張もしなかった (実測はすべて親)

## 次の一手差分

### 完了

- [T-287] `state_from_dict()` の `direction` / `magnitude` / `result` を閉じた値域と形式で検証した
  (裁定 (115) 択 (a) の射程を完了)。残余は {{T:t287-producer-domain}} /
  {{T:t287-layer3-reader}} / {{T:t287-checkpoint-integrity}} / {{T:t287-error-message-redaction}} へ分離した。
  remaining: none
  base: c946cf384bc9cd177438e8dbd23efc6446daf219a7aadd1241e13243476f4fe2

### 新規

- {{T:t287-producer-domain}} **P2・新規**: producer 側 (3 driver の `load_proposal_file` →
  `project_whiteboard` → `state_to_dict`) が値域を検査しないため、driver が自分で書いた checkpoint を
  次回 resume で拒否する非対称が残る。8c だけ `parse_planner()` で閉じており driver 間で実効境界が
  一致していない。親の推奨は `project_whiteboard()` に置く案 (3 driver の単一合流点)。
  裁定パッケージ §1
- {{T:t287-layer3-reader}} **P2・新規**: `layer3_report.py` の独立 reader と手動 runbook
  (s4b / s5-sort / s8a-trigger) の raw whiteboard 経路が `state_from_dict()` を迂回する。
  層 3 材料レポートには検証されない値が載り続け、`wb:<hash>` 参照も内容由来で変わる。
  既存 fixture が `direction="up"` / `result="ok"` を使っているのが直接証拠。裁定パッケージ §2
- {{T:t287-checkpoint-integrity}} **P2・新規**: in-domain 改竄 (`rejected` → `fail` 等) は値域検査では
  防げず、`iteration` 整合・entry 件数上限・campaign/run origin 束縛でしか閉じない。
  (99) の原問題のうち本裁定が含まなかった部分。裁定パッケージ §3
- {{T:t287-error-message-redaction}} **P3・新規**: `state_from_dict()` の**既存**エラーが未信頼の
  checkpoint 文字列 (未知キー名・`delta_pct` 値) を再掲し、`attempts.jsonl` と `report.json` の
  error message に残る。本 wave が作った defect ではなく、修正には既存テストの期待値変更を伴う。
  親の推奨は保存側での redact。裁定パッケージ §4
