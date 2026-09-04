# 欠測 attempt を含む母集団から出た数値主張に、主張ごとの但し書きを付けた

- wave: `worktree-dev-wave-t2202-missing-population-caveats` ([T-2202]、ユーザー裁定 D1529 の実装)
- 起点 main: `fbd10fd6c68890f2ae22e0508118efeff50c263b` (段 4 前に `1b7822110c54536f82ecab8d058d7a9253bfd3ce` へ ff-only 取り込み。自分の commit 0 件のため D1621 で incoming 監査を省略)
- 実装面の差分 0 (docs と insight のみ)。変異 matrix 免除 (DW-S04)。
- 逐語: `verbatim/` (段 1 brief、段 2 plan、段 3 敵対 2 本、段 4 裁定、段 6 レビュー)。

---

## 1. 何をしたか

D1529 は「欠測 attempt を含む母集団から出た派生記述に但し書きを付け、**単位は文書でなく
数値主張とその母集団で切る**」と裁定した。本 wave はその実装である。

**「欠測 attempt」とは、campaign 記録上 commit (変種の認証確定。取引の確定ではない) に
到達しないまま打ち切られた実行を指す。** read-heavy の `constant-mu2` 変種 `292d58f1dad8` では
初期確認 (legacy) 1 反復と本規模 (performance) 3 反復だけが記録に残り、balanced の
`symmetric-modulo-mu100` 変種 `c7c331ebe662` では legacy 1 反復だけが残る
(一次資料: `output/insights/2026-09-02_b10-missing-iterations-scope/README.md` §2・§3)。

結果は次のとおり。

| 量 | 値 |
|---|---:|
| 編集した file | 9 (insight README 8 + 設計文書 1) |
| 但し書きの箇所 | 23 |
| 追加行 / 削除行 | 163 / 0 |
| `docs/paper-story/` の変更 | 0 (該当主張 0 件、段 3 が再帰・別表記込みで再実測) |

**形:** 既存行を 1 byte も変えない純挿入とし、各主張の段落・表・箇条の直後に blockquote
「但し書き (D1529)」を置いた。読み手が値を読んだ同じ節で但し書きに到達できることを優先した
(段 3 レンズ B の最重要所見)。例外は `2026-09-02_paper-story-a6-certification/README.md` で、
file 自身が「追記でのみ訂正する」と宣言しているため EOF に節を足し、主張ごとの項にした。
各 file の最初の但し書きで「欠測 attempt」「初期確認 (legacy)」「本規模 (performance)」を定義した。

**文面の不変条件:** 値を無効にしない。欠測を除いた再計算はしていないと明記する。既に誤りと
確定している旧値 (23 分・3.83 時間・3.1 倍、および「24 反復」) には「訂正を変えない・誤りのまま」
を添え、無限定の「無効ではない」を使わない (段 3 レンズ A、段 6 レビューの所見)。

## 2. 対象と母集団

| file | 主張 | 母集団 | 欠測の掛かり方 |
|---|---|---|---|
| `2026-08-31_t1905-b10-formal-run/README.md` | 1690 万 commit・中止 300 万・約 2000 万 | read-heavy 飽和 3 変種の本規模反復 (5・5・3) | 3 反復の 1 変種が欠測 attempt |
| 同 | 5 時間で 15 点中 3 点 | request `965996` の走行時間 | 完了 3 変種のほかに欠測 attempt の legacy 1 + 本規模 3 の時間を少なくとも含む |
| `2026-09-02_b10-trace-truncation/README.md` | r=0.9991 / 0.4044、campaign 別相関、回帰式 (84.625、-0.309)、R^2 | performance 238 反復 | read-heavy 18 反復中 3 |
| 同 | 表の read-heavy 行 87.002、全体 84.4 | 同上 | 同上 (write-heavy・balanced 行には掛からない) |
| 同 | 約 7 倍、16.83M-17.19M / 1346.9-1465.6 秒、1690 万 | 飽和 3 変種 (5・5・3)、比の分母は write-heavy の点別平均 (各 5) | 3 反復の 1 変種が欠測 attempt |
| `2026-09-02_paper-story-a6-certification/README.md` (EOF) | 1 回 23 分、帯、4.07 時間、2.95 倍 / 5 時間で 15 点中 3 点 / 旧 max 23 分・3.83 時間・3.1 倍 | 飽和 3 変種 / 走行時間 / 訂正済み旧値 | 同上 |
| `2026-09-02_t1905-b10-multinode-design/README.md` | 約 25 時間 | 走行時間 5 時間 5 分 ÷ 完了 3 変種 × 15 | 走行時間に欠測 attempt の時間を含む |
| `2026-09-02_t2229-t2230-verify-cost-erratum/README.md` | 帯と積み直し値 (24.43 分・4.07 時間・2.95 倍) / 5 時間 5 分 | 飽和 3 変種 / 走行時間 | 同上 |
| `docs/b10-multinode-formal-run-design.md` | §1 の 5 時間 5 分・15 中 3・47 コア遊休 / §4 balanced 約 6 時間半 / §4 blockquote の約 17M・帯・79.6-86.0・14.0-16.2 時間・閾値 / §4・§10 の約 25 時間 | 走行時間 / balanced 6 時間枠 ÷ 14 × 15 / read-heavy 本規模 18 反復 / 走行時間 | balanced は `c7c331ebe662` の legacy 1 反復の時間を含む |
| `2026-09-03_t1905-b10-road-and-balanced/README.md` | 表の `292d58f1dad8` 行と「24 反復」2 箇所 / T-2191 の 1.7-2.1 倍の再掲 / 換算 (1.18-1.30G、41.0-44.3us、13.4-15.6 時間、14.0-16.2 時間、閾値、+2%) / 旧 3.1 倍の再掲 / §10 の余裕 1.5 倍 | 本規模 18 反復 | 18 中 3 |
| `2026-09-02_t2191-verifier-parallel/README.md` | 傾き 87.0・68-75%・17M への 1000-1213 秒 / 17M で約 87GB / 660-840 秒・13.7-17.5 時間・1.7-2.1 倍 / 58.5-142GB | 本規模 18 反復と飽和 3 変種の帯 (17M という規模) | 合成 trace 単独の値 (59.2-65.3、5.1KB、2.2 倍、並列度別記憶量) には掛からない |
| `2026-09-04_f241-perf-attribution/README.md` | 13.7〜17.5 時間の再掲 | 飽和 3 変種の帯 | 同上 |

**対象外と裁定したもの (理由付き):**

- `16.90M commits / 1425.4 秒` (trace insight の hard cap 比較) — 完了変種 `84319b1127a6`
  (16.83-16.91M / 1374.8-1436.2 秒) の値で欠測由来でない (レンズ A、refuted)。
- 同一変種内の r=-0.0213・振れ幅 0.93% / 6.99% — 入力行を確定できず判定不能 (レンズ A)。
- road-and-balanced の「adaptive は commit が 1/3」 — 比較母集団を確定できず判定不能 (レンズ A)。
- 「287 反復」「197 反復」の完全性主張 — 観測母集団そのものの数で派生値ではなく、trace insight の
  表自身が read-heavy 22「15 点中 3 点で撤去」と balanced 85「打ち切り」を開示している (親の裁定。
  plan は対象と提案した)。
- 「15 認証単位」 — 構造数 (D1529)。
- `2026-09-02_b10-missing-iterations-scope/README.md` と `2026-09-02_b10-denominator-270/README.md`
  — 既に主張ごとに母集団と欠測の掛かり方を明示している。変更 0。

## 3. 段 3・段 6 が親を覆した点

1. **plan が brief に無い file を 1 つ、レンズ A が 3 箇所を足した。** brief の A〜H には
   `2026-09-02_t2191-verifier-parallel/README.md` (87.0・帯・17M 規模を費用・所要・記憶量へ流す) が
   無かった。さらにレンズ A が road-and-balanced の 1.7-2.1 倍再掲と 3.1 倍再掲、
   `2026-09-04_f241-perf-attribution/README.md` の 13.7〜17.5 時間再掲を閉包漏れとして出した。
   いずれも real。
2. **brief の (P5)「road-and-balanced は表の『打ち切り』で開示済み」は退けられた。** 表の開示は元観測
   についてであり、そこから離れた換算・閾値・余裕には届かない (plan、レンズ A・B が独立に同じ指摘)。
3. **plan が対象とした B11 (`16.90M / 1425.4 秒`) は帰属が誤りだった。** レンズ A が完了変種の帯で
   照合して refuted にした。親の brief も同じ誤りを含んでいた。
4. **「24 反復」は値の誤りである。** road-and-balanced の 2 箇所と設計文書 §4 の blockquote が
   「24 反復ぶん」と書くが、一次資料は read-heavy `verify_done=22` (legacy 4 + performance 18)
   で、表の本規模も 5+5+5+3 = 18 である。本 wave は但し書きに「誤りのまま」と書き、値の訂正は
   せず次の一手へ起票した。
5. **「5 時間 5 分」を request `965996` の壁時計と断定していた (段 6 must-fix 1)。** 一次資料の
   scheduler 実測は Elapse 20950 秒 (約 5 時間 49 分) で、5 時間 5 分の計測区間は現記録から確定
   できない。6 箇所の但し書きを「走行時間を指すが計測区間は判定不能。いずれの区間でも欠測 attempt
   の時間を少なくとも含む」へ直した。
6. **brief の (P1)「設計文書 F を対象に含める」はレンズ B が scope 外 (real) と判定し、親は不採用にした。**
   D1529 の理由節が名指しする「balanced 約 6 時間半」「約 25 時間」の担い手は F だけであり、
   carry [T-2202] の一覧も F を含むため、docs-only の可逆な追記として含めた。**この判断は親の
   仮定であり、ユーザーが除外を望めば設計文書の 5 箇所だけを戻せる。**
7. **EOF 追記だけでは到達できない (レンズ B の最重要所見)。** plan は全 file を EOF 追記としたが、
   値を読んだ読み手が同じ節で但し書きに届かないため、a6 README を除き主張直後の blockquote へ
   変えた。verbatim の行番号参照は削除済み worktree の絶対 path を指す歴史記録で、生きた参照は
   無いことを親が実測した (tests / tools / hooks に対象 README の bytes・見出しの pin なし、a6 の
   `artifact-manifest.json` に README.md なし)。

## 4. 段 6 レビュー所見の対応表 (DW-O16)

| # | 判定 | 所見 | 対応 |
|---|---|---|---|
| 1 | real / must-fix | 5 時間 5 分を request の壁時計と断定 | closed — 6 箇所を「計測区間は判定不能、Elapse 20950 秒」へ |
| 2 | real / must-fix | balanced の但し書きが「本規模反復は 0 件」と強く読める | closed — 「完了記録は 0 件。終了直前に 1 反復が始まっていたかは不明」へ |
| 3 | real / must-fix | 24 反復の直後に無限定の「無効ではない」 | closed — 「24 反復は誤りのまま」「24 反復を除く測定値・派生値を無効にしない」へ |
| 4 | real / must-fix | f241 の但し書きが母集団を欠測 3 反復だけで説明、commit 未定義 | closed — 飽和 3 変種 (5・5・3) と「取引の確定ではなく変種の認証確定」を追記 |
| 5 | real / nit | 約 7 倍の分母母集団が不明 | closed — 「write-heavy の点別平均 (各 5 反復) で割った比」を追記 |

fix はすべて親の docs 編集 (docs-only、D95) で、削除 0 行は fix 後も保たれている
(`git diff --numstat` 163 / 0、`git diff --check` 緑)。再レビュー子は起動していない。

## 5. 受入と検査 (実測)

| 検査 | 結果 | checkout |
|---|---|---|
| `python3 tools/check_docs.py` (編集前) | 違反なし rc=0 | `fbd10fd6c` |
| 同 (編集後・fix 後) | 違反なし rc=0 | `1b7822110` + 本 diff |
| `orchestrator/tests/test_check_docs.py::test_real_repo_clean` 単独 | 1 skipped (成長 hold `docs_bytes`、opt-in なし。test 本体に skip は無く、同じ検査器の直接実走が上記) | `1b7822110` + 本 diff、request `977072.nqsv` |
| `python3 -m orchestrator.campaign.s8b_holdout_freeze search` | rc=0、hit なし | 同上 |
| `git diff --check` | 緑 | 同上 |
| 受入全走 | 記録 commit 後に投入 (結果は worklog) | — |

## 6. 本書が主張しないこと

- 但し書きは値を無効にしない。欠測 attempt を除いた再計算は 1 件も行っていない。
- 「24 反復」と「5 時間 5 分の計測区間」の値そのものは直していない。前者は起票、後者は判定不能と
  記した。
- `docs/decisions.md` (D1480 / D1485 / D1489 / D1509 / D1554)、archive worklog
  (1186 / 1187 / 1189 / 1190 / 1197-1198 / 1211 / 1223)、`output/insights/**/verbatim/` は
  同じ主張を持つが本 wave の対象外 (command 引数の対象指定) で、触っていない。
- 「287 反復」「197 反復」の完全性主張に但し書きが要らないというのは親の裁定であり、plan は
  対象と見ていた。
