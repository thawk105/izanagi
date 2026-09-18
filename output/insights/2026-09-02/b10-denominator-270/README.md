# B-10 完全性の分母を 270 で書き直し、欠測母集団由来の派生記述を一覧にした

- wave: `worktree-dev-wave-t2201-b10-denominator` ([T-2201] と [T-2202] の裁定不要部分)
- 起点 main: `24b31d2a37353d63a4f715ed2170d13e25df3fe3`
- 実装面の差分 0 (docs と insight のみ)。変異 matrix 免除。
- 射程の正本は worklog エントリ 1198 と
  `output/insights/2026-09-02_b10-missing-iterations-scope/README.md`。本書はそれを消費する側である。

---

## 1. 何をしたか

**(a) 完全性の分母を 270 で書き直した。** 到達先は 3 つ。

| # | file | 形 | 理由 |
|---|---|---|---|
| 1 | `docs/archive/worklog-phase3-0902-1189.md` | H2 直後へ blockquote の訂正注記 | エントリ 1189 の読み手全般。訂正が 5 件とも insight にしか無く、archive の本文からは辿れなかった |
| 2 | `docs/b10-multinode-formal-run-design.md` §6 | (4-b) として報告様式を新設 | 次の正式系列の報告様式 |
| 3 | `output/insights/2026-09-02_b10-trace-truncation/README.md` | EOF へ追記訂正 | 同じ欠陥が**生きた非 archive 文書**に残っていた (下記 §3) |

**(b) [T-2202] の裁定不要部分を直した。** `docs/b10-multinode-formal-run-design.md` の
§5.1 と §10 に残っていた「トレース切り捨ての疑い」を、エントリ 1189 で決着した事実へ置き換えた。
§10 の「1 反復 175 秒の頭打ちを確定値として使わない」という結論自体は残し、理由だけを
「切り捨ての疑い」から「横軸の取り違え」へ差し替えた。**D295 の非検出限界は閉じていない**と
明記し、判定の射程を広げていない。

**(c) 欠測母集団由来の派生記述を一覧にした** (§4)。**但し書きの文言は書いていない。
付けるかどうかも裁定していない。** それは [T-2202] の残余としてユーザー裁定に残る。

**過去の測定値そのものは 1 つも書き換えていない (絶対規律 7)。** 凍結 2 file への差分は
削除 0 行の純追記である (`git diff --numstat` で 24/0 と 30/0)。当時の判定
(トレース側だけで件数が減る切り捨ては起きていない) と 45 cell の
`correctness_certified=true` は、昇格も降格もさせていない。

---

## 2. 3 つの分母

| 母集団 | 予定 | 完了記録 | 未完了 |
|---|---:|---:|---:|
| **登録された 3 workload の組 (完全性の開示に使う)** | **270** | **197** | **73** |
| 4 campaign の履歴すべて | 360 | 287 | 73 |
| 開始済み 49 attempt に条件づけた分 | 294 | 287 | 7 |

- 270 = 3 workload x 15 変種 x 6 verify 反復 (legacy 1 + performance 5)。
- 294 = 開始済み 49 attempt x 6。read-heavy が登録 15 点のうち 4 点しか開始していないので、
  **未開始 11 点 x 6 = 66 枠が 294 の外へ落ちる。**
- 73 の内訳は balanced 5 + read-heavy 68。タグ別には legacy 11 枠・performance 62 枠。

**270 だけを書かず 3 行を併記する。** 270 のみにすると、追加で実行・完了した 90 verify と
4 campaign の参照履歴が見えなくなる。270 と 360 の差がともに 73 なのは同じ母集団だからではなく、
360 側へ完了済み write-heavy 90 枠が分母・分子の両方へ入るためである。

### 「197」は 2 通りある

同じ 197 が別の campaign 集合から出る。

- 登録格子の完了記録 197 = `e3de15eb` 90 + balanced 85 + read-heavy 22
- `2026-09-02_b10-trace-truncation` が「残る 197 反復」と呼ぶもの
  = `068fd2cd` 90 + balanced 85 + read-heavy 22 (= 287 - 90)

**数値の一致は偶然である。197 を引くときは campaign を名指しする。**
報告様式には campaign ID を分母の定義へ入れない (登録枠は
`(workload, 変種, verify タグ, 反復番号)` の論理キーで数える)。どの campaign の記録を
完了として採るかは、設計文書自身がまだ裁定していない。

---

## 3. 親の閉包が 1 件破れていた

親は着手時に「完全性の分母として 294 を使う箇所は archive 2 file だけ」と実測したが、
これは **refuted** である。`output/insights/2026-09-02_b10-trace-truncation/README.md` の
「異常終了が一つも無いとは書けない」の項が
**「予定が 49 × 6 = 294 反復なのに対し観測は 287」**と書いており、
これは archive ではない生きた文書である。

**破れた理由は grep の形である。** 親は `294 反復` や `予定 294` を引いたが、
一次資料は `49 × 6 = 294` と書いていた。**同じ分母を数式として書く形を取り逃した。**
数値そのものでなく、それを生む式で書かれた出現は、値の文字列検索では閉じない。

---

## 4. 欠測 attempt を含む母集団から出た派生記述

**この節は一覧であって裁定ではない。但し書きの文言は書かない。**

### 4.1 正典が数えた 4 件

`output/insights/2026-09-02_b10-missing-iterations-scope/README.md` の
「直接集計の下流に派生記述が 4 件ある」節が正典である。行番号は本 wave で実測し直した。

| # | 記述 | 出現箇所 | 値を出した母集団 | 欠測の掛かり方 |
|---|---|---|---|---|
| 1 | 70.0-87.0 マイクロ秒/commit (T-2191) | 元表 `2026-09-02_b10-trace-truncation/README.md` の「所要を説明する量」節の表。下流は `docs/archive/worklog-phase3-0902-1189.md` の T-2191、現行 `docs/worklog.md` は carry-forward | performance タグ 238 反復 = write-heavy 75 + 75、balanced 70、read-heavy 18 | read-heavy 18 のうち 3 反復が、commit へ到達しなかった `constant-mu2` attempt の観測分 |
| 2 | 直列性検査 1 回 23 分 (22-24 分) | `docs/decisions.md` の D1485 と **D1489**、`docs/archive/worklog-phase3-0902-1187.md`、同 1189 の T-2191、`output/insights/2026-09-02_paper-story-a6-certification/README.md` | read-heavy の高 commit 帯の 3 秒 performance 反復。観測帯は約 1350-1470 秒 | 高 commit 3 点の 1 つが、5 回中 3 回だけ観測された未 commit attempt |
| 3 | read-heavy 5 時間 5 分・3 変種と約 25 時間の外挿 | `docs/b10-multinode-formal-run-design.md`、`docs/archive/worklog-phase3-0902-1186.md`・同 1187、`docs/decisions.md` の D1480・D1489・D1509、`output/insights/2026-08-31_t1905-b10-formal-run/README.md`、同 `2026-09-02_t1905-b10-multinode-design/README.md`、同 `2026-09-02_paper-story-a6-certification/README.md` | request `965996` の job 壁時計と、commit 済み 3 変種 | 壁時計には commit へ到達しなかった 4 変種目の legacy 1 + performance 3 の時間も入る一方、除数は完了 3 変種のまま |
| 4 | read-heavy の 1690 万 commit | `output/insights/2026-08-31_t1905-b10-formal-run/README.md`、`docs/archive/worklog-phase3-0902-1186.md`・同 1187・同 1189、`2026-09-02_b10-trace-truncation/README.md` | read-heavy の飽和した 3 点の performance 反復 | 3 点の 1 つが未 commit `constant-mu2` の n=3。平均 16.928M が 1690 万への丸めに入る |

> **追記 (T-2321、2026-09-18): 記録境界と旧所要の区別。** 上の表 #3 の「5 時間 5 分」の計測区間は引き続き未同定である。
> request `965996` の Started (2026-09-02 01:07:49 JST) からの秒表示差として、3 変種目の認証確定までは
> 16,387 秒、WAL 末尾 (4 変種目の本規模 3 反復目) までは 20,682 秒、Ended までは 20,946 秒 (scheduler の
> Elapse 記載は 20950S)。欠測 attempt の本規模 3 反復を含むことは WAL 末尾まで等の区間では確認できるが、旧所要
> への帰属は確定しない。根拠と精度は `docs/b10-multinode-formal-run-design.md` §1 の同名追記を参照。既存行と
> 当時の判定を保持し、値を無効にせず、欠測 attempt の時間を除いた再計算は行わない。

### 4.2 正典の 4 件のうち 1 件は帰属が違う

**「15 認証単位」は欠測母集団由来ではない。** 正典は T-2191 の 1 件として
「70.0-87.0 マイクロ秒/commit と 15 認証単位」を並べて数えているが、
**15 認証単位は登録された 15 変種を認証単位へ写した構造数**であって、
238 反復の回帰からも欠測 attempt からも導かれていない。欠測が掛かるのは単価の側だけである。
段 3 の 2 レンズが独立に同じ指摘を返した。

### 4.3 同じ規則なら一覧へ入る、正典に無いもの

| 記述 | 出現箇所 | 欠測の掛かり方 |
|---|---|---|
| 「read-heavy の検査対象は write-heavy の約 7 倍」(6.83-7.22 倍) | `2026-09-02_b10-trace-truncation/README.md`、`2026-09-02_b10-missing-iterations-scope/README.md` が 6.83-7.22 倍を再現 | 3 飽和点の 1 つ (`constant-mu2`) が未 commit attempt の n=3。15 点格子全体の比ではない |
| balanced の「約 6 時間半」外挿 | `docs/b10-multinode-formal-run-design.md` §4、`docs/archive/worklog-phase3-0902-1190.md` | 未完 attempt の legacy 1 回を含む 6 時間壁時計を、完了 14 変種で外挿した値 |
| read-heavy の「約 23 時間」外挿 | `docs/archive/worklog-phase3-0902-1187.md` | 「約 25 時間」とは別系統の第二の外挿。同じ壁時計を別の割り方で伸ばしている |
| 84.4 マイクロ秒/commit、相関 r=0.9991 / r=0.4044、係数 -0.309 | `2026-09-02_b10-trace-truncation/README.md` | いずれも同じ performance 238 反復母集団から出る |

**したがって「4 件」は文書単位の索引としては使えるが、
欠測母集団由来の値の全数ではない。** 一覧の単位を「文書」でなく
「数値主張とその母集団」に取ると、上表の分だけ増え、構造数 1 件が減る。

### 4.4 一覧の過程で見つかった、別の裁定を要する誤り 3 件

**本 wave では直していない。** いずれも但し書きの有無とは別の、値そのものの誤りである。

1. **D1489 の「max 23 分」は保存値と整合しない。** 観測帯の上端は約 24.43 分 (1465.6 秒) で、
   23 分は上端ではなく中ほどである。10 回なら 3.83 時間ではなく約 4.07 時間、
   12 時間枠の倍率は約 3.1 倍ではなく約 2.95 倍になる。A-6 insight も同じ計算を再掲している。
   walltime 12:00:00 という結論自体は、attempt 全損の非対称性も理由なので直ちには動かない。
2. **「1 回 23 分」を「直列性検査」へ帰属させるのが誤り。** 一次資料はこの所要を
   **混合区間** (ベンチ本体・トレース書き出し・C 行の数え直し・解析・直列化可能性検査・
   一時 dir 操作・WAL 書き込み) と明記しているが、D1485・D1489・A-6 insight・T-2191 が
   揃って検査器単体の費用として引いている。
3. **`docs/archive/worklog-phase3-0902-1187.md` の「15 cell 中 3 cell」は単位が混ざっている。**
   完了したのは 3 変種の認証 attempt で、性能 `fitness_tps` は全件 null である。
   1 workload の性能 cell は 3 block x 15 点 = 45 なので、「15 cell」という母数が存在しない。

---

## 5. 本書が主張しないこと

- **但し書きを付けるべきかを裁定していない。** §4 は「どれが欠測母集団由来か」の一覧であって、
  各記述をどう書き直すかは決めていない。
- **値の向きは変えていない。** 欠測変種の 3 反復は他の read-heavy 変種と同じ帯にあり、
  外れ値ではない (正典の判定をそのまま引く)。本書はそれを再検証していない。
- **45 cell の `correctness_certified=true` を降格させない。** 欠測はこの値を 1 件も動かさない。
- **D295 の非検出限界は閉じていない。** トレースと counter は同じ実行体から出るので、
  両方が同時に落ちる common-mode failure と、個数を保存する破損は検出しない。
- **§4 の出現箇所を「全数」と主張しない。** §3 が示したとおり、値を式で書いた出現は
  値の文字列検索では閉じない。同じ取り逃しが §4 に残っている可能性を否定できない。
- **WAL の独立再集計はしていない。** 生 WAL は本 wave の読める範囲に無く、
  確かめたのは既存の表と成果物の再計算までである。

---

## 6. 一次資料

- worklog エントリ 1198 (`docs/archive/worklog-phase3-0902-1197-1198.md`) — 射程の正本
- `output/insights/2026-09-02_b10-missing-iterations-scope/README.md` — 分母 3 種と派生 4 件の正典
- worklog エントリ 1189 (`docs/archive/worklog-phase3-0902-1189.md`) — 訂正対象
- 段 2 プラン・段 3 敵対相談 2 本・段 4 裁定の逐語は `verbatim/`
