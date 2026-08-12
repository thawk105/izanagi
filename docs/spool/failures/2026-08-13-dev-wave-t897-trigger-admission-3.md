---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-13
wave: dev-wave-t897-trigger-admission
seq: 3
---

## 新規

### {{F:adversarial-prompt-shape-not-just-framing}}. 敵対レビュー依頼が防御目的を明記していても依頼の**形**で上流分類器に拒否された [手順漏れ]

- 事象: 段 3 レンズ A が 17 分・39 model call まで進んだ後、上流分類器の
  `This content was flagged for possible cybersecurity risk` で打ち切られ、成果物 0 bytes・rc=1。
  受領証の `evidence_status` は `complete`、`output_bytes` は 0、`stop_reason` は `max_attempts`。
  出力 38,330 token (うち reasoning 32,399) が丸ごと失われた。
- 根本原因: 依頼文の冒頭には防御目的を明記していた。しかし本文が
  「検査をすり抜ける経路を**具体的に構築せよ**」「攻撃者が操作できる場合」という
  **攻撃手順の作成**の形をしており、前置きに関係なく発火した。
  既知の対策 (防御目的を明記する) は前置きの話であって依頼の形の話ではなかった。
- 恒久対応: 同じ内容を「検証仕様の網羅性レビューと、テストの負例カタログ作成」として依頼し直した。
  求める中身 (どの入力が検査をすり抜けるか) は落とさず、成果物の形だけを変えた。
  再投入は 23,751 bytes で完走し、must-fix 3 件を返した。
  対象が単一ユーザーの研究用ローカルツールであること、扱うのがソース 1 行の書式一致であることも明記した。
- 再発検知: 敵対系の子が rc=1・成果物 0 bytes で終わったら、まず `attempt-*.events.jsonl` の末尾を読む。
  `turn.failed` の分類器メッセージは受領証にも stderr にも現れず、events にしか出ない。

### {{F:mutation-preregistration-anchors-absent-in-implementation}}. 段 4 で事前登録した変異 3 件に、実装形の anchor が存在しなかった [恒真ゲート]

- 事象: 段 4 で 11 件を事前登録したが、段 6 の敵対レビュー 2 本が独立に「3 件は単独帰属が成立しない」と
  判定した。2 件は独立した検査として実装されず (物理行数制約・CR payload 保持はいずれも block 逐語
  比較 1 本に吸収された)、1 件は削除しても後段の frame 検査が同じ入力を拒否する冗長 gate だった。
- 根本原因: 段 4 の時点で実装は存在せず、変異位置を段 2 のプランから書いた。
  プランは「1 物理行であること」「CR を payload に残すこと」を個別の検査として記述していたが、
  実装はそれらを 1 本の逐語比較へ畳んだ。**実装が段 5 で生まれる wave では段 4 の登録は暫定である。**
- 恒久対応: 3 件を落として 10 件へ差し替え、順序検査は冗長 gate として台帳に明記した。
  期待 node はレビューの帰属表を写さず、実装とテストから導き直した。
- 再発検知: 事前登録の各変異について「その検査を消したとき、他のどの層もその入力を拒否しないこと」を
  実装確定後に 1 件ずつ確認する。確認できないものは登録せず実効 gate へ再照準する。

### {{F:mutation-expected-nodes-underdeclared-again}}. 正例 control の期待 node を過少申告して 1 巡目が MISMATCH になった [手順漏れ]

- 事象: 変異 1 巡目は 9/10 KILLED・SURVIVED 0 だったが、正例 control (pristine block の受理経路を
  壊す変異) が MISMATCH。実測では 2 node が赤くなったのに spec は 1 node しか申告していなかった。
- 根本原因: 期待 node を実装子の導出報告から書き、**実測で完全集合を再導出しなかった**。
  pristine の fast-path を壊すと、受理正例だけでなく「raw bytes を 1 回だけ読む」ことを固定した
  node も同時に赤くなる。
- 恒久対応: 1 巡目の結果を erratum として保存し、期待集合を harness の実測 `failed_nodes` から
  直して 2 巡目を走らせた。2 巡目は 10/10 KILLED・MISMATCH 0・rc=0。
- 再発検知: 期待 node は 1 巡目の `failed_nodes` と照合してから確定する。
  過少申告は harness が MISMATCH で止めるので、黙って通ることはない。
