---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-27
wave: worktree-dev-wave-t2867-llm-contrast
seq: 1
title: [T-2867] silo-function-policy 軸で LLM (C++ 形・IR 形) と非 LLM (random・進化) を同じ評価数の上限で比べる対照の事前登録を起草した (草稿・未発効)。D2258 の実行契約は規則として継承し、コードは B-5 への結合でそのまま使えないと確かめた。推奨規模 4 arm × n = 12 で約 59〜69 node 時間 (換算)、LLM の原提案 240〜720 機会 (docs のみ、計算なし、branch worktree-dev-wave-t2867-llm-contrast)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`): D2259 の後継として関数単位の軸で「LLM 対 非 LLM 生成器」の対照を設計し、事前登録を起草する。先に D2258 の流用可否を確かめ、
  node 時間・LLM 直列時間を見積もる。計算は投入しない。driver と `tools/pegasus/` は並走の [T-2865] の担当で触れない。
- 成果: 草稿 `docs/silo-policy-generator-contrast-preregistration.md` (**未発効**)、記録 `output/insights/2026-09-27/t2867-silo-policy-contrast-draft/README.md`、
  設計判断 {{D:silo-policy-contrast-draft}}。コード・テスト・`.claude/agents/` は変えていない。
- 段 1 の途中で上位の被覆 (比較基盤 D2220、T-2850 の試走の事前登録) を見つけ、brief の provisional 裁定 2 つを改めた (比較族を族 A・B に分ける、共通の初期点を job 1 で測る)。
- 段 2・3 は省いた (実装面なし)。段 6: Codex (gpt-6-sol、read-only) の敵対レビュー 2 本 (A 判定規則・公平性・規律 2、B 過剰・事実照合) → real 12・refuted 4。
  最重要: 初期点の性能が LLM に届かない (driver の自系列の履歴は throughput を持たず、性能は critic 経由でだけ届く → critic を job 1 の後にも回す)、
  生成不成立の規則が初期点を endpoint に含めるとほぼ発火しない (親の点検 → 探索点で数える)、週上限を律速と断定していた (→「なりうる」)。
  焦点再レビュー 1 NO-GO (must-fix 4) → fix、焦点再レビュー 2 NO-GO (must-fix 2: LLM の役割の再試行を尽くした後の結末、規模変更時の書き換え範囲の漏れ) →
  DW-O16 の上限 3 巡に達したので親が直して本文の grep で検算し閉じた。**焦点再レビューの GO は得ていない** (insight §7、裁定 3)。
- 見積りの単価は B-5 v1 の backoff 候補の実測からの換算で、政策の候補の単価は未測定。発効の前に段階 F の生死確認の job Elapse で取り直す。
- 検査: `tools/check_docs.py` 違反なし、全史 provenance 監査 12,970 件で新規違反なし (草稿 commit の後)。受入全走は本記録の commit の後に行い、結果は land の受領証に残る。

## 次の一手差分

### 更新

- [T-2867] **P2・草稿着地 → ユーザー判断待ち (規模の択一と発効) + 実装は段階 F の後**: silo-function-policy 軸の生成器対照の事前登録の草稿
  (`docs/silo-policy-generator-contrast-preregistration.md`、{{D:silo-policy-contrast-draft}}) を着地させた。未発効。発効の前に要るもの:
  (1) ユーザーが規模を選ぶ (草稿 §11.3: 推奨 4 arm × n = 12 = 約 59〜69 node 時間 / 進化を外す 3 arm 約 44〜52 / LLM×IR を外す 3 arm 約 44〜52 / n = 10 約 49〜58、いずれも換算。
  LLM の原提案は推奨で 240〜720 機会、暦時間は週上限に依存し測れていない)。
  (2) 段階 F ([T-2865]) の生死確認 (実 LLM の 1 iteration を C++ 形・IR 形で、機械生成 IR の 1 評価) の job Elapse で見積りを取り直す。
  (3) 実装 (Codex author、insight §5): 政策 driver の系列ごとの campaign identity・停止規則の切り離し・機械生成 IR の口・stock と静的 10 µs の口・初期点を
  campaign に載せる口・同時検査の key・job body (ここまで [T-2865] の担当 file)、G_rand と (1+1) 進化の生成器、系列制御と起動器、LLM の round tool と親の指示文、report。
  (4) 発効束 (草稿 §12) を埋めて、node 時間と LLM の時間をユーザーへ示し確認を得る (D2212 項 4)。
  base: 59f31b9b9b1bcaf7df84a192c01175634c12a1fe40980bcc6455c3ca564fa0e4
