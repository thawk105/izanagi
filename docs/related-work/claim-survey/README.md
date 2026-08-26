# claim-survey — 主張軸別の調査状態の凍結スナップショット

**規則の正本は `docs/related-work/README.md` の「7.7 主張軸別の調査状態と、不在主張の成立条件」である。**
本ディレクトリはその規則を当てた**時点ごとの実測**を凍結して束ねる。
`docs/related-work/literature-map/` (監査前の生データ)、`docs/related-work/notes/`
(個別論文の精読記録)、`docs/related-work/shinka-deepdive.md`
(単発の深掘り) とは役割が違い、ここに置くのは**軸を横断した棚卸しと監査記録**だけである。

## 読む時

論文の positioning を書くとき、関連研究を追加したとき、主張軸を改訂したときだけ読む。
日常セッションのブート対象にしない (D35)。

## 決まりごと

- **各ファイルは日付付きの凍結物であり、書いた後は上書きしない。** 内容を更新したいときは
  新しい日付のファイルを足す (`docs/paper-story/` と同じ原則)。
- **各ファイルは入力 path、入力 commit、入力 digest の所在、文献 cutoff、作成日を持つ。**
  その文書だけで「いつの何から導いたか」を復元できるようにする。
- **現在値をここへ書かない。** 進行中の可変状態 (どの軸が今どの段階か、未充足の残件) の正本は
  `docs/worklog.md` の末尾エントリである。本 README も一覧以外の状態を持たない。
- ここに置いた判定は `docs/related-work/README.md` と同格の正本ではない。
  矛盾したら `docs/related-work/README.md` が勝つ。

## 一覧

| 日付 | ファイル | 中身 |
|---|---|---|
| 2026-08-26 | `2026-08-26-inventory.md` | 5 つの主張軸 × 検索記録の成熟度の初回棚卸し。軸 1 の分類 pilot、軸 1 の主張履歴を含む |
| 2026-08-26 | `2026-08-26-correction-5-audit.md` | Polyjuice / CCaaLF→NeurCC の特徴づけについて、paper-story 最新版・`docs/related-work/README.md` 7.1・`docs/related-work/literature-map/` の Markdown と CSV の四者を突き合わせた監査 |
| 2026-08-26 | `2026-08-26-cir-cvn-adjudication.md` | `2604.09318` (CIR+CVN) の `要裁定` を一次資料で解いた記録。軸 1 への接地判定と、`docs/paper-story/` §3 の 1 が落としてはならない 2 つの限定 |
| 2026-08-27 | `2026-08-27-axis1-search-preregistration.md` | 軸 1 の 7.7.4 事前登録。索引 3 つの実測、共有の暦境界による cutoff、6 枝 × 3 索引の query catalog、完走述語、停止条件、母集合の外。**登録であって実行ではない** |
