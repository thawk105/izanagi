# 段 4 裁定 — B-10 欠測 7 反復の射程

親が段 2 プラン子 1 本と段 3 敵対相談 2 本 (正しさ射程レンズ / 数量と帰属の整合レンズ) の
所見を real / refuted に裁定した記録である。**子が出した数値・path・行参照は親がすべて独立に
確かめた。一致しなかったものは無い。** 子の指摘のうち親の実測が誤っていた 3 件は、
下記のとおり親の側を訂正した。

## 結論

**所見はすべて real。refuted は 0 件。** 親の provisional 裁定 (P1) は 3 件中 2 件が
書いたとおりでは成立せず、置き換えた。実装面の差分は 0 のままとし、段 5・6 を飛ばして
`4 → 7 → 8 → 9` で進む。変異 matrix は実装面差分 0 につき免除 (DW-S04)。受入全走は行う。

## 親の実測のうち誤っていた 3 件

| 項目 | 親が書いていたこと | 実測 | 訂正 |
|---|---|---|---|
| M7 / M14 | 「`git grep` で正式走の識別子は docs のどこにも引かれていない (0 件)」 | `docs/archive/worklog-phase3-0902-1186.md` に `e3de15eb` と `965564.nqsv` が実在する | 親が検索結果から `docs/archive/` を除外していた。**この文は削除する。** 図の非帰属は figure provenance の入力 field だけを根拠にする |
| M8 / M10 | 「read-heavy の撤去理由は scheduler 受領証で確定」 | 受領証は `Terminated` と残余 22250 秒しか書かず、送信主体を記録しない | **二段の証拠**にする。受領証が「壁時計ではない」を確定し、worklog エントリ 1187 の `qdel` 記録がユーザー裁定による撤去を確定する |
| M9 | 「欠測変種が入っている下流集計は 238 反復回帰の 1 件だけ」 | 直接集計のほかに派生記述が 4 件ある (下記) | **「直接集計」と「その派生記述」の 2 段**に分ける |

## 最も重い所見 — 「7」は条件付きの数である

両レンズが独立に同じ点を指摘し、親が実測で確かめた。

- 事前登録は 3 workload それぞれに 15 点を登録する
  (`POINTS_PER_BLOCK = 3 + len(MEANS_US) * len(SHAPES) = 3 + 6 * 2 = 15`、
  `MEANS_US = (2, 5, 10, 25, 50, 100)`、`SHAPES = (("constant", 0), ("symmetric-modulo", 1))`)。
  campaign は `run_campaign(cfg, genomes(), ...)` に 15 点全部を渡す。
- ところが read-heavy は 15 点のうち **4 点しか `build_start` していない**。
  残り 11 点 × 6 枠 = 66 枠は、そもそも開始されていない。
- したがって `294 = 49 build_start × 6` は**開始済み attempt に条件づけた事後の分母**であり、
  登録格子の予定数ではない。

**分母は 3 つあり、どれを使うかで欠測数が変わる。**

| 母集団 | 予定 | 完了記録 | 差 |
|---|---:|---:|---:|
| 開始済み 49 attempt に条件づけた分 | 294 | 287 | **7** |
| 登録された 3 workload の組 (write-heavy は完走した `e3de15eb` を採る) | 270 | 197 | **73** |
| 4 campaign の履歴すべて (先行 write-heavy `068fd2cd` を含む) | 360 | 287 | **73** |

73 の内訳は balanced 5 + read-heavy 68 (未開始 11 点 × 6 = 66 と、開始済み constant-mu2 の 2)。
タグ別には legacy が 11 枠、performance が 62 枠である。

**裁定:** insight は 3 つの分母を階層で並べ、「欠測 7」を単独の完全性の数として書かない。
worklog エントリ 1189 の「予定 294 反復」も追記で訂正する。

## 「実行されずに終わった」は書けない。ただし親は子より強い上界を出せる

- `verify_done` は検査器が返った後にだけ emit される (`pipeline.py` の `emit(layout, v, STAGE_VERIFY_DONE, ...)`)。
  **反復の開始を記録するイベントは無い。** したがって WAL が証明するのは「完了記録が無い」までである。
- 最後の完了記録から job 終了までの空白は、balanced が 80 秒 (11:00:56 → 11:02:16)、
  read-heavy が 264 秒 (06:52:31 → 06:56:55) である。
- **両レンズは「未開始か途中終了か判別不能」で止めたが、親はもう一段詰められる。**
  反復は `for _repetition in range(workload.reps): _run_one_repetition(...)` で厳密に逐次に走る。
  完了記録が 1 件も増えていない以上、**空白の中で開始できた反復は attempt あたり高々 1 件**である。
  よって **7 枠のうち開始されたのは高々 2 件、少なくとも 5 件は一度も開始されていない。**
- 完了記録は 7 枠のいずれにも無い。検査器が返ってから emit するまでの間に落ちた窓は原理的に残るが、
  その窓は返り値取得から WAL 書き込みまでに限られる。

**裁定:** 「実行されずに終わった」を「**完了記録が無い**」へ全面的に置き換える。
そのうえで上記の上界 (開始は高々 2 件、少なくとも 5 件は未開始) を実測として書く。
7 枠のどれにも verdict・anomaly・integrity の主張を付けない。

## 打ち切り理由 — 二段の証拠にする

| campaign | request | 経過上限 | Elapse | Remaining | 一次資料の文言 | 帰属 |
|---|---|---:|---:|---:|---|---|
| balanced | `963545.nqsv` | 21600 s | 21609 s | 0 s | `Batch job received signal SIGKILL. (Exceeded per-req elapse time limit)` | **壁時計打ち切り**。受領証単独で一意 |
| read-heavy | `965996.nqsv` | 43200 s | 20950 s | 22250 s | `Terminated` | **壁時計ではない**。ここまでが受領証の射程 |

read-heavy の撤去主体は worklog エントリ 1187 が確定する — ユーザー裁定を記録し、
`qdel` を実行したと明記している。claim 競合は WAL 作成前の `acquire_claim` で止まるので、
22 件の完了記録まで進んだ read-heavy の終端原因にはならない。

**裁定 (P1-3 = real):** balanced 5 枠は壁時計、read-heavy 2 枠は壁時計ではない。
ただし「受領証だけで撤去まで確定」とは書かず、受領証 + 同時代 worklog の合成証拠として書く。

## `certified` の意味を 4 項に縮めない

`Integrity.clean()` は orphan read、version 重複、txid 重複、genesis commit、txid 欠番、
write-version 不一致、不正 key、framing、lock coverage、write intent、permutation、
commit witness の **12 項の連言**である。`certified` はさらに `n_txns > 0` と `serializable` を
要求する。commit witness は expected / observed が両方 None でも clean を通るが、
B-10 の pipeline は witness の存在と batch count 0 を先に要求してから expected を検査器へ渡す。

**裁定:** worklog エントリ 1189 が挙げた 4 条件は**代表例であって全条件ではない**と追記で訂正する。
既存 bytes は変えない。これは正しさゲートを**強い側へ**言い直す訂正であり、規律 2 を緩めない。

## 45 cell の射程 (P1-1)

**P1-1 は書いたとおりでは refuted。** 「一切限定しない」は広すぎる。

- **real な部分:** 45 record は今も 45/45 が `correctness_certified=true` / `missing=false` であり、
  欠測はこの値を 1 件も降格させない。45 cell は単一 request `965564.nqsv`、
  workload は write-heavy、認証単位は distinct `(variant_id, build_attempt_id)` 15 組に閉じ、
  欠測 2 attempt はその認証元ではない。
- **refuted な部分:** 45 cell はもともと 1 workload・1 request の記述的成果であり、
  正式系列の完全性も他 workload の認証も担っていない。top-level `official_certification` は
  `false` であり、3 族のうち balanced と read-heavy は `pairs=0 / indeterminate` である。
  「射程を一切限定しない」と書くと、この局所的な事実が 3 族の confirmatory 結論へ誤って移送される。

**裁定:** 「欠測は保存済み 45 record の各 field を変更しない。ただし 45 record は
もともと 1 workload・1 request の記述的成果であり、正式系列の完全性や他 workload の認証を
担わない」と書く。

## どの主張・図・集計に入っているか (P1-2)

**P1-2 は refuted。** 単位を分けると入り先が 3 層ある。

1. **未完了の 7 枠そのもの:** どの集計にも入らない。
2. **観測済みの 5 反復** (balanced `c7c331ebe662` の legacy 1、
   read-heavy `292d58f1dad8` の legacy 1 + performance 3): 287 件の完全性集計に入る。
   performance 3 件は 238 反復回帰の read-heavy 18 件のうち 3 件を占める。
3. **同じ `variant_id` / point:** `variant_id` は genome 由来で workload 共通なので、
   `c7c331ebe662` = symmetric-modulo-mu100 と `292d58f1dad8` = constant-mu2 は
   **write-heavy の 45 cell に各 3 record 実在する** (build attempt は別)。

**さらに直接集計の下流に派生記述が 4 件ある** (レンズ B が挙げ、親が全件確認した)。

- 正式走 insight の「read-heavy の commit 1690 万件」と検査 1 回の所要。
- 現行 worklog の T-2191 (直列性検査の並列化) — 238 反復回帰から
  70.0-87.0 マイクロ秒/commit と 15 認証単位を導いている。
- `docs/b10-multinode-formal-run-design.md` の read-heavy 5 時間・3 変種・約 25 時間の外挿。
  job の壁時計には、commit へ到達しなかった 4 変種目で使った時間も含まれる。
- `docs/decisions.md` の D1485 が「直列性検査 1 回 23 分」を優先順位判断に使っている。

**図には 1 件も入らない。** `fig2b` の入力 campaign は `backoff-sweep-*`、
`fig2c` は `b10-backoff-grid-*-sweep-*` で、正式走 4 campaign
(`b10-backoff-shape-silo-*-formal-*`) はどちらの入力にも現れない。

**裁定:** 帰属を「直接集計」と「派生記述」の 2 段の表で書く。
`docs/paper-story/` と `docs/b10-multinode-formal-run-design.md` と `docs/decisions.md` は
本 wave では**変更しない** (成果物は insight と worklog のみ)。派生記述の扱いは次の一手へ送る。

## 事前登録の欠測規則と反実仮想

事前登録の `analysis.missingness` は
`conditions = [missing, performance-error, correctness-not-certified, unstable, underexposed]`、
`pair_action = invalidate-entire-family`、`family_action = indeterminate` を定める。

- **実際に起きたこと:** balanced と read-heavy が indeterminate なのは 7 枠のせいではない。
  両 campaign は性能相を一度も走らせておらず、`reports/` と `variants/` と `spec/` が空で、
  18 pair 全部が missing である。7 枠が関わるのは balanced mu100 の 3 pair と
  read-heavy mu2 の 3 pair だけで、残り 15 pair ずつの欠落は 7 枠と無関係である。
- **反実仮想:** 他がすべて揃っていたとしても、両 attempt が認証へ到達していないので
  その点の 3 block record は `missing` または `correctness-not-certified` になり、
  `pair_action = invalidate-entire-family` により 2 族とも indeterminate になる。
  **「欠測 7 枠は無害だった」とは書けない。**

**裁定:** 反実仮想は**発効 spec と、そこへ束縛された解析実装の合成**として書く。
spec の字義だけからは出ないことを明記し、必要な前提 (attempt を全反復通過まで commit しない、
commit 済み attempt だけが cell の認証源、workload を跨いで認証を移送しない、
認証不在なら cell が missing / correctness-not-certified になる、
残り 15 pair がすべて usable) を列挙する。
また「7 件全部が必要」ではなく「**各 attempt に未完了枠が 1 件でもあれば足りる**」と書く。

## scope 外だが real な所見 (裁定パッケージ候補 — 本 wave では実装しない)

1. `docs/b10-multinode-formal-run-design.md` の「主張しないこと」に
   「1 反復 175 秒の頭打ちを確定値として使わない。トレース切り捨ての疑いが残っている」が残る。
   この疑いは worklog エントリ 1189 が既に決着させており、記述が古い。
2. T-2191 の単価 (70.0-87.0 マイクロ秒/commit) と D1485 の「23 分」は、
   commit へ到達しなかった read-heavy attempt の 3 反復を含む母集団から出ている。
   値の向きは変わらないが、母集団の但し書きが付いていない。
3. 完全性の開示に使う分母を、開始済み条件付き (294) ではなく登録格子 (270) で書き直す必要が、
   本 insight の外にもありうる。

いずれも `docs/paper-story/` を含む他 wave の編集面に触れるので、次の一手へ送る。

## 段 5・6 を飛ばす根拠

実装面 (コード・テスト・実行可能な probe / harness / script・機械設定) の差分は 0 である。
成果物は新規 insight 1 本と worklog fragment 1 本だけで、いずれも docs である。
DW-S04 に従い変異 matrix を免除し、`4 → 7 → 8 → 9` で進む。受入全走は免除しない。
