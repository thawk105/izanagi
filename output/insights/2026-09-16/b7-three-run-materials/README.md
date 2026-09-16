# B-7 の材料を 3 走行そろえて結果節へ落とした wave の記録

- `authority: none`
- `default_effect: no-state-change`
- 可変状態の正本は worklog 末尾と現行 phase doc であり、本稿ではない。
- wave branch: `worktree-dev-wave-t2670-b7-three-run-materials`
- 基底 commit: `262c2993eae89f452dcea35fc61f97e41a689e8e`
- 成果物: `docs/paper-story/results/2026-09-16-b7-three-run-materials.md` (新規) と
  `docs/paper-story/README.md` の results 系列の表への 1 行追加。
- **新しい測定は 1 件も行っていない。既存の凍結物の bytes は 1 byte も変えていない。**

## 1. 着手前に覆った前提

依頼は「論文ストーリー §8 の B-7 (全 workload の退行込み報告) を材料化する」だった。
**B-7 の材料化は 2026-09-14 に実施・着地済みである** (worklog 1488、成果物
`docs/paper-story/results/2026-09-14-b7-all-workload-regression.md`)。

**ただし既存稿は [T-1998] を明示的に対象外にしている** (同稿 §0.1)。3 走行として数えた要約は
版 §8 が持ち、results 系列には [T-1998] の詳細材料が無かった。**そこが本 wave の純増である。**

活動ごと止める裁定の有無も段 1 で調べた。検索語と結果は次のとおりで、止める向きの裁定は無い。

| 検索語 (`docs/decisions.md`) | hit |
|---|---|
| `B-7` | 0 件 |
| `退行込み` | 0 件 |
| `統制稿` | 4 件 — D1631 と D1993 のみ |
| `材料化` | D779 / D813 / D1410 / D1631 — いずれも別対象 |
| `結果節` | D1631 のみ |
| `results 系列` | D1631 / D1993 |

隣接する未決は [T-2610] (B-7 の**要件充足**の扱い、P2・未裁定) と [T-2611] (A-6 単独稿、P3)。
**どちらも本 wave の scope ではなく、稿は充足を宣告していない。**

## 2. 段 3 の敵対相談が親の案を 2 か所で直した

2 レンズ (sol = 配置・単位・系列規則・凍結境界 / luna = 数値の出所・限定・規律抵触)。
**所見は全 15 件を real として採り、棄却は 1 件だけである。**

主要なものを挙げる。

- **純増の主張が広すぎた (sol、must-fix)。** 「results 系列に [T-1998] の材料が無い」は、既存稿が
  §0.1・§4.4 で [T-1998] へ言及し導線を持っているので偽である。**正しくは「詳細材料と併記が無い」。**
- **3 走行を 1 file に収めるのは規則の要求ではない (sol、should-fix)。** [T-1998] 単独稿も規則上は
  開いている。**併記を選んだのは編集判断であると本文に書く**ことにした。
- **再導出の対象は 3 走行の報告単位全体である (sol、must-fix)。** A-2 / A-6 を既存稿から引き継がない。
- **親の一次資料表が不足していた (luna、must-fix)。** `certification.json` は median と `effects` を
  持つが、**生標本・abort 率・ばらつきを持たない。**
- **[T-1998] の `result.json` に `correctness` 欄が無い (luna、must-fix)。** 全 key の静的確認で判明。
- **consumer 是正で受理集合が広がった事実が落ちていた (luna、must-fix)。**

**棄却した 1 件** — luna の「差分改訂禁止の引用帰属は未検証なので追認できない」は、luna の射影に
逐語資料が入っていなかったための保留であり所見の否定ではない。親が現物で確認し、
当該逐語が `docs/paper-story/README.md` の results 系列節にあることを確かめて採った。

## 3. 段 6 のレビューが 10 件、焦点再レビューが 3 件を出した

レビュー 2 本 (逐語と数値の検算 / 主張の過大さと限定の欠落)。**must-fix 1・should-fix 8・nit 1。**

- **D1631 の全体再導出と、開示した未照合範囲が整合しない (must-fix)。** 親は当初、A-2 / A-6 の
  raw JSON と campaign WAL を照合せず、転記済み insight までで止めていた。
  **この所見を受けて durable authority の現物まで降りた** (下記 §4)。
- 数値・field 名・引用・SHA-256 の検算では、**性能値・40 標本・13 file の SHA-256 に不一致は 0 件**
  だった。直したのは解析回数の書き間違い、表の行数、`同名 field` という不正確な言い方、
  事前登録の引用 2 か所の非逐語、arm 別 source digest の帰属先である。

焦点再レビュー 1 巡目は **closed 9・partial 1・新規 should-fix 2**。2 巡目で **3 件とも closed、
新規 0 件**になった。

## 4. レビューを受けて親が降りた先 — durable authority の現物

**この wave で新しく分かったことが 3 つある。**

1. **A-2 / A-6 の raw JSON と campaign WAL は、raw manifest の束縛と 9 件すべて一致する。**
   親が現物から SHA-256 を実計算して突き合わせた。4 + 2 cell の生標本は raw JSON の
   `performance.samples_tps` にあり、掲載値と記載順まで一致する。
2. **[T-1998] の正しさの記録は campaign WAL にある。** 走行成果物には無いが、WAL の `verify_done` が
   8 genome それぞれに 1 件あり、登録された 2 arm はいずれも `verdict` = `serializable`、
   `certified` = `true`、`anomalies` = 0、`workload.tag` = `legacy` である。
   **ただし A-2 / A-6 と同じ強さではない** — あちらは legacy 1 回に加えて性能条件側の正しさ検査を
   5 回観測した記録を持つが、[T-1998] の WAL にあるのは `legacy` タグの 1 件だけである。
   この非対称を稿の §2.4 に書いた。
3. **3 走行の campaign WAL は同じ `cv` という field 名でばらつきを記録しており、その値は
   8 arm とも `標本標準偏差 (分母 n−1) / 標本平均` と倍精度の全桁で一致した。**
   生標本から計算し直して確かめた。A-6 の insight README が載せる 1.18% / 1.06% は
   別の統計量 (母標準偏差 / median) で、生標本から計算すると 1.1827% / 1.0560% になる。
   **稿は `cv` を 8 arm そろえた列で載せ、1.18% / 1.06% は同じ列に置かない。**

**併せて、[T-1998] の走行 argv が campaign WAL に記録されていることも確かめた。**
`-thread_num=48 -ycsb_tuple_num=1000000 -extime=3 -clocks_per_us=2100 -ycsb_zipf_skew=0.9
-ycsb_rratio=50 -ycsb_rmw=0` で、A-2 / A-6 の `performance_common` と 6 項目が一致する。
`max_ope` は argv に現れず、`base` と `WAL` は policy 層の key なので argv からは確かめられない。
**したがって稿は「3 走行の測定設定が全部同じ」とは書いていない。**

## 5. 稿が守った線

- **D1993 項 6 に従い 3 走行をプールしない。** 主表は 1 行 = 1 対比較で、総合 status・平均改善率・
  全体の標本数・成功した workload の数を作らない。A-2 の outer status が 2 workload の論理積である
  ことを両行に書いた。
- **B-7 の充足を宣告しない。** 「3 走行そろった」は掲載対象がそろったという文書作業の完了までで、
  [T-2610] を閉じるものではない。
- **D1986 項 5 から引くのは A-1 本走の認可据え置きまで。** 本走が未投入であること、探索走と pilot が
  `formal=false` であることは版 §8 の記述であり、稿は独立に確かめていないと明記した。
- **既存稿を訂正版と読ませない。** 2026-09-14 稿は 2 attempt・6 cell の材料として有効なまま残る。
- **旧 fig5 の用途制限 (期限なし) を緩めない。**
- **性能値を採用の根拠にしない。** 限定 19 は、規律 2 が禁じるのが「正しさを破る variant を採ること」
  であることを書いたうえで、併記が採用の許可ではないと書く。**性能値を判断材料に使うこと自体を
  禁じる文書ではない**と明示した (レビューの指摘による狭め)。

## 6. 記録しておく運用上の事実

- `tools/dev_wave_submodule_init.py` は 1 回目に `runtime-io-failure: update-no-fetch` で落ち、
  同じ引数の 2 回目で成功した (`DW-O08` が想定する一過性の範囲)。
- **wave の branch slug に未採番の T 番号を入れてしまった。** `docs/spool/worklog/README.md` は
  「wave slug と branch 名にも未採番の T 番号を使わない」と定めている。branch 名に含まれる数字は
  wave 開始時に数えた暫定値であって**採番された ID ではない。fold は同じ数字を無関係な項目へ
  独立に割り当てうるので、branch 名と T 番号を同一視してはならない。**
  稿にも worklog の題にも角括弧の T 番号は書いていない。

## 7. 逐語

`verbatim/` に子 7 本の prompt と出力、および親の段 1 brief を置いた。
段 2 plan 1 本、段 3 consult 2 本、段 6 review 2 本、焦点再レビュー 2 本である。
生の log と受領証は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/` にある。
