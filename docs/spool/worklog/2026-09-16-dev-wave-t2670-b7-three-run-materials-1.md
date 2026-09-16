---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2670-b7-three-run-materials
seq: 1
title: B-7 の材料へ [T-1998] の詳細を足し、3 走行を退行込みで併記する統制稿を一次資料から作り直した (docs のみ、branch worktree-dev-wave-t2670-b7-three-run-materials、実装面の差分 0 につき変異 matrix は DW-S04 の免除)
---

## 本文

- **成果物は `docs/paper-story/results/2026-09-16-b7-three-run-materials.md`。** 入口
  `docs/paper-story/README.md` の results 表へ 1 行足した。**新しい測定は 1 件も行っていない。
  既存の凍結物の bytes は 1 byte も変えていない。**
- **依頼の前提が着手前に覆った。** 依頼は「B-7 を材料化する」だったが、**材料化は 2026-09-14 に
  実施・着地済み**である (エントリ 1488、`results/2026-09-14-b7-all-workload-regression.md`)。
  **ただし既存稿は [T-1998] を明示的に対象外にしている** (同稿 §0.1)。3 走行として数えた要約は
  版 §8 が持ち、results 系列には [T-1998] の詳細材料が無かった。**そこだけが純増である。**
  既存稿は 2 attempt・6 cell の材料として有効なまま残し、訂正版とは呼んでいない。
- **活動ごと止める裁定を段 1 で探して 0 件だった。** 検索語は `B-7` (0 件)、`退行込み` (0 件)、
  `統制稿` (D1631 と D1993 のみ)、`材料化` (D779 / D813 / D1410 / D1631、いずれも別対象)、
  `結果節` (D1631 のみ)、`results 系列` (D1631 / D1993)。
- **段 3 の敵対相談 2 本が親の案を 2 か所で直した。所見 15 件を全て real として採り、棄却は 1 件。**
  (a) 「results 系列に [T-1998] の材料が無い」は広すぎた — 既存稿は言及と導線を持つので、
  純増は「詳細材料と併記」に限る。(b) **3 走行を 1 file に収めるのは規則の要求ではなく編集判断**で
  あり、[T-1998] 単独稿も規則上は開いている — そう本文に書いた。(c) 再導出の対象は 3 走行の報告単位
  全体で、A-2 / A-6 を既存稿から引き継がない。(d) `certification.json` は median と `effects` を
  持つが**生標本・abort 率・ばらつきを持たない**ので、親の一次資料表が不足していた。
  (e) **[T-1998] の `result.json` に `correctness` 欄が無い。** (f) consumer 是正で
  **受理集合が広がった**事実が限定から落ちていた。
- **棄却した 1 件**は、相談子が「差分改訂禁止の引用帰属は未検証なので追認できない」としたもの。
  子の射影に逐語資料が入っていなかったための保留であって所見の否定ではない。親が現物で確かめ、
  当該逐語が `docs/paper-story/README.md` の results 系列節にあることを確認して採った。
- **段 6 のレビュー 2 本が must-fix 1・should-fix 8・nit 1 を出し、親が全件反映した。**
  must-fix は「D1631 の全体再導出と、稿が開示した未照合範囲が整合しない」。**この所見を受けて
  durable authority の現物まで降りた。**
- **降りた結果、3 つ新しく分かった。** (1) **A-2 / A-6 の raw JSON と campaign WAL は raw manifest の
  束縛と 9 件すべて一致する** (親が現物から SHA-256 を実計算)。生標本は raw JSON の
  `performance.samples_tps` にあり記載順まで一致する。(2) **[T-1998] の正しさの記録は campaign WAL に
  ある** — `verify_done` が 8 genome に各 1 件あり、登録 2 arm はいずれも `verdict` =
  `serializable`、`certified` = `true`、`anomalies` = 0、`workload.tag` = `legacy`。
  **ただし A-2 / A-6 と同じ強さではない** (あちらは legacy 1 回 + 性能条件側 5 回、こちらは legacy 1 件だけ)。
  (3) **3 走行の WAL は同じ `cv` field を持ち、その値は 8 arm とも
  `標本標準偏差 (分母 n−1) / 標本平均` と倍精度の全桁で一致した** (生標本から再計算して確認)。
  A-6 の insight README が載せる 1.18% / 1.06% は別の統計量 (母標準偏差 / median、再計算値
  1.1827% / 1.0560%) なので同じ列に置いていない。
- **[T-1998] の走行 argv も campaign WAL にあり、A-2 / A-6 の `performance_common` と 6 項目が一致する**
  (スレッド数 48、レコード数 1,000,000、実行時間 3 秒、skew 0.9、rmw 0、read 比率 50)。
  `max_ope` は argv に現れず、`base` と `WAL` は policy 層の key なので argv からは確かめられない。
  **したがって稿は「3 走行の測定設定が全部同じ」とは書いていない。**
- **焦点再レビューは 2 巡した。** 1 巡目が closed 9・partial 1・新規 should-fix 2、
  2 巡目で **3 件とも closed・新規 0 件**。数値・field 名・引用・SHA-256 の検算では
  **性能値・40 標本・13 file の SHA-256 に不一致 0 件**だった。直したのは解析回数の書き間違い、
  表の行数、`同名 field` という不正確な言い方、事前登録の引用 2 か所の非逐語、
  arm 別 source digest の帰属先、限定の広すぎた採用禁止、A-5 限定の欠落、identity 実値の不足である。
- **B-7 の充足は宣告していない。** 稿は限定 20 件を持ち、「3 走行そろった」は掲載対象がそろったという
  文書作業の完了までだと明記する。**[T-2610] (B-7 の要件充足の扱い) は未裁定のまま触っていない。**
  D1993 項 6 に従い 3 走行をプールせず、D1986 項 5 から引くのは A-1 本走の認可据え置きまでとし、
  本走未投入と `formal=false` は版 §8 の記述で独立確認はしていないと書いた。
- **実装面 (コード・テスト・script・機械設定) の差分は 0 である。** 変異 matrix は `DW-S04` の免除。
- **wave の branch slug に未採番の T 番号を入れてしまった。** `docs/spool/worklog/README.md` は
  「wave slug と branch 名にも未採番の T 番号を使わない」と定めている。branch 名に含まれる数字は
  wave 開始時に数えた暫定値であって**採番された ID ではない。fold は同じ数字を無関係な項目へ
  独立に割り当てうるので、branch 名と T 番号を同一視してはならない。**
  稿にも本エントリの題にも角括弧の T 番号は書いていない。
- **運用の記録。** `tools/dev_wave_submodule_init.py` は 1 回目に
  `runtime-io-failure: update-no-fetch` で落ち、同じ引数の 2 回目で成功した
  (`DW-O08` が想定する一過性の範囲)。
- 工数: codex 子 7 本 (plan 1 / consult 2 / review 2 / focus 2)。**全件 `outcome=accepted` /
  `stop_reason=completed`、`gpt-6-astra` / `medium`。** wall の合計は約 1,481 秒、model call の合計は
  68。読み取りだけの子なので実走はすべて親が行った。計算ノード job は使っていない。
- 逐語と資料は `output/insights/2026-09-16/b7-three-run-materials/`。生 log と受領証は
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/`。

## 次の一手差分

### 新規

- {{T:t1998-standalone-results}} **P3・新規**: [T-1998] の balanced stock-inline 対の単独 results 稿を
  書く。2026-09-16 の横断稿は同走行の詳細材料を持つが、8 genome 分の campaign 記録を含む一次資料
  全体からの結果節ではない。[T-2611] (A-6 単独稿) と同型で、同系列の規則どおり権威 bytes・
  campaign WAL・事前登録・裁定の全体から作り直す。段 3 の相談が「単独稿は依然として有効な対抗案」
  と判定したものを起票する。
