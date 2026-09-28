---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-28
wave: dev-wave-t2852-p5-prereg
seq: 1
title: [T-2852] VLDB 差分分析 P5 (workload 記述 × critic の介入) の事前登録を草稿で置き、試走 v2 の実測単価で見積りを取り直した — 一次資料の 120〜240 評価は 48.2〜96.4 node 時間 (換算の約 2.8 倍、LLM の待ちの node 占有が主因)。親の推奨は S1-wh の本走を今は投入せず S3 の後に回す (草稿 + insight、計算投入 0、branch dev-wave-t2852-p5-prereg)
---

## 本文

- 正本: 草稿 `docs/workload-description-critic-intervention-preregistration.md` (未発効)、起草記録 `output/insights/2026-09-28/t2852-p5-intervention-prereg-draft/README.md`
  (実測の file:line・見積りの計算・ユーザー確認の束・段 2〜6 の経緯)、設計判断 {{D:p5-intervention-prereg-draft}}。
- 見積りの単価は試走 v2 の score を含まない集計 (`section8.json`・`failures-noscore.json`) だけから取った。親は試走 v2 の score を見ていない。
- 段 3 の相談 2 本 (統計・事前登録適合 / 実行可能性・規律・過剰) の所見 16 件はすべて real・採用。主なものは、critic なしで失敗理由の返却が消える件 (現行 K0 では
  構造化された失敗理由が critic 診断経由でしか planner・coder に届かない) への対処として失敗理由の写しを両水準に渡すこと、P3 登録の規模の規則を継承しないこと、
  表示の外に残る workload の露出の列挙、人手分類を 3 母集団に分けること、「2.8 倍」「66%」の言い方の訂正。
- 段 6 の read-only レビューは NO-GO (must-fix 2)。親が段 4 で足した「予備の観察」(記述の表示が coder の最初の提案を動かすかを記録入力から呼び直して見る) を、
  選び方の規則が固定されず依頼 (草稿と見積りだけ) を超えるとして外した。ほかに anomaly 0 件の出典の誤り (`section8.json` には件数の欄が無い) を直した。
  焦点再レビュー 2 巡で GO。
- 受入全走の 1・2 回目 (2026-09-28 08:36・08:55 JST) は Pegasus の定期保守 (9/28 09:00〜21:00 JST、全 queue が DIS/INA) に当たり、shard の queue 待ち
  900 秒の打ち切り (rc=70 source_rc=16) でテストは 1 件も走らなかった。本 wave に帰属しない。保守明けの 9/29 に投げ直した。
- エージェント工数: Claude 調査子 1 (sonnet、K0 への workload 情報と critic の経路の棚卸し)・Codex plan 1・consult 2・review 3 (初回 + 焦点再レビュー 2)、全 Codex は gpt-6-sol / medium。
- 全史 provenance 監査 (commit 1 の後): 13,125 件、新規違反なし。

## 次の一手差分

### 更新

- [T-2852] **P1・ユーザー確認待ち (VLDB 差分分析 P5: 介入による理由の説明)**: 事前登録の草稿 `docs/workload-description-critic-intervention-preregistration.md`
  (未発効) と、試走 v2 の実測単価による見積りを置いた ({{D:p5-intervention-prereg-draft}})。発効に要るのは次のユーザー確認 (D2212 項 4、一括承認にしない)。
  (1) 進め方の択一: (a) S1-wh で本走 (6 cell × n = 3 / 4 / 5 で 72.3 / 96.4 / 120.5 node 時間、LLM の直列 48.0 / 64.0 / 80.0 時間、中央値の単価) か、
  (c) 介入と出力コードの分類を S3 (関数方策軸、[T-2867]) の生成器対照の後に別の登録で行うか。親の推奨は (c) (D2272 項 2 の 3 理由が本書にも残り、
  S1 の coder 出力は数値 1 行で機構の変更を読めない)。(2) (a) なら規模と評定者 (人 2 名)。発効には草稿 §13 の実装 (Codex author。役割文書の入力節の改訂は
  ユーザー承認事項) と計算確認が要る。材料は `output/insights/2026-09-28/t2852-p5-intervention-prereg-draft/README.md` §5。
  base: dfae11c49aa72c3ef0e8ffdff0ff804586d79e447610ac2148e6988d0d9c2370
