---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-29
wave: dev-wave-output-pruning
seq: 1
---

## {{D:output-pruning-policy}}. output/ の低価値 file は参照閉包で参照 0 か README 要約済みのものだけを `git rm` で HEAD から外し、外した file は索引 1 本で引けるようにする

**決定:**
1. output/ の file を HEAD から外すのは `git rm` による通常の commit だけで行う。履歴は書き換えない (D577)。sparse-checkout と木の本数削減は採らない (D2211 項 9)。
2. 外してよいのは次の 2 種だけとする。(A) 参照閉包で参照が 0 の機械出力。参照閉包は、固定 commit の全 blob を参照元とする 7 軸 (full path・dir 相対 path・一意な basename・sha256・blob id・root より下の祖先 dir・glob) に、gz 化前の名前・配置移行前の旧 path・同じ root の md 本文での言及を加えたものとする。(B) README 本文が結論と数値を要約済みで、名前では引かれていない生出力。
3. 次のものは外さない: sha256 / blob id で束縛された file (自 root の manifest だけの束縛を含む)、事前登録・受領証・凍結・正しさ材料 (verifier 入力・正例負例・変異の spec と台帳)、テスト・道具が読む file、root 名がコード (tools・orchestrator・hooks・.claude・.codex) に現れる root、README.md、実装面の拡張子 (削除も実装面の差分になる)、未着地 branch が触る path、並行 wave が書いている新しい root。
4. 外した file は `output/PRUNED-INDEX.jsonl` 1 本に、path・blob・size・最後に存在した commit・分類・理由を追記する。原本は `git show <commit>:<path>` で引ける。外したことを理由に過去の判定を無効にしない (規律 7)。README から名前で引かれている file を外すときは、その README に索引で引ける旨を 1 行足す。
5. insight dir を丸ごと外す (C) ことは、README.md を残す規則と両立しないので行わない。価値の低い dir の整理は README を残した file 単位で行う。
6. 依頼の保護条件そのものに当たる大きな塊 (自 root manifest の hash 束縛、事前登録が dir ごと引く生ログ、別 insight の台帳が path で列挙する生出力) は、AI の裁定では外さない。一覧と効果の実測を一次資料に置く。

ユーザー指示 (2026-09-29): 「output/ 配下にある価値の低すぎるファイルは削除した方が良いのでは。例えば『これやってみたけどこうだった』というようなもの、claude / codex から見てその知識はなくても自明と思えるもの、そういうのは掃除しても良い」。

**理由:**
- 第 1 段の走査 (output/insights 27,176 file) では、保護条件を守って確信を持って外せたのは 6 file だった。file 数の大半は束縛された証拠で、名前や拡張子だけで「低価値」と判定すると事前登録の根拠や変異台帳を外してしまう (段 3 の「消すと困る」側レンズが A 候補 131 件から 44 件の gz 別名参照・20 件の変異 spec / 台帳・6 件の正例負例などを指摘した)。
- 索引を 1 本にすると、外した file の所在を 1 回の検索で引け、README の旧名参照も索引経由で辿れる。
- 一次資料: `output/insights/2026-09-29/output-pruning/README.md`。

**却下した選択肢:**
- 拡張子や file 名 (raw・stdout・log) だけで一括して外す — 事前登録の根拠・正しさ材料・README が概念で指す証拠を外す。
- blob 重複だけを理由に外す — 重複の大半は守る証拠の内部にある (最大は事前登録が引く 0 byte の生ログ 2,118 件)。
- insight dir を丸ごと外す — README を残す規則と両立しない。
- 自 root manifest だけの sha256 束縛を AI の裁定で束縛でないとみなす — 依頼が明示した保護条件であり、境界例ではない。
