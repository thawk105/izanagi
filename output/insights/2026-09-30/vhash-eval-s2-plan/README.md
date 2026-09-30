# VHash md_40: U0 の確認段 S2 を先に発効できる評価計画にする — 前提の更新、発効単位、f_M,c の段、node 時間の積算

VHash 論文 (`docs/paper-story-vhash/`) の評価計画の草稿 `docs/vhash-evaluation-preregistration-draft.md` (未発効) を改訂し、
U0 (前進を回収境界へ反映する保持の側、D2322 項 1 で論文の芯) を判定する確認段 S2 (H4) を、S1 を待たずに発効できる形にした。
**計画だけで、計測・計算投入はしていない (0 node 時間)。発効もしていない。** 発効はユーザーの確認の後に別の wave が行う。

計画の本体は草稿の §16 (発効単位・門・f_T の当て方・S0-M 段・走行の行列・発効に残る条件・変えたこと・諮る論点) と §11.1 (前提 P1〜P10・P2′ の現在の状態) である。
本書は、その数値の出所と、本 wave が自分で確かめたこと (区間の被覆の計算、patch の重ね適用) の生の出力を置く。

## 0. 結論

1. **S2 は S1 を待たずに発効できる形にした。** 族は m = 19 のままで、S2 が判定しない 13 個は族に残る (語は §5.1 の順序で決まる)。S2 の 6 個は水準 0.05 / 19 で判定する。
   S2 の発効の後に足す判定 (H5・H6 など) は別の族にする。1 つの族として読み直した場合に S2 の語が変わらないのは m′ ≤ 25 まで (§2 の計算。反例は有効 round 10・m′ = 26) で、これは参考に留めた。
2. **比較相手は A_fix (ro-gcflag 修正入り、主) と A_stock (対照) を同じ round に置く** (D2322 項 2)。E の土台も A_fix と同じ ro-gcflag 入りにする。
   E 系 3 本の patch と ro-gcflag の patch は、pin の tree の写しに fuzz なしで重なった (§3)。build と条件 gate は確かめていない。
3. **最大の待ちは md_39 (構成 E の書き込み検査の走査中の回収の穴の修理)。** md_36 がこの穴を示したので、E_sp の GC 安全の根拠 (P6) は今は成り立たない。
   さらに、修理が「書き込み key を持つ tx に公開させない」型なら、L-w の長い tx (1 write を持つ) で E_sp が E_hb と同じ動きになり S2 の cell で機構が働かない。
   この場合は S2 をこの形で発効しない、という規則を md_39 の結果の前に登録した (草稿 §16.2)。
4. **段ごとの node 時間 (参考単価、上限側):** S0-M (f_M,c) 0.31、S2 の門 0.37、S2 本走 1.34、計 2.02。下限側 (u = 5.8 s) は計 1.76 (§4)。
5. S2 は C_now (H3)、H1 の再挑戦 (md_37)、H2a の共通計器、H5・H6、P5 の生成器を待たない。f_T (md_35) と pin の前進は、草稿 §16.5・§16.3 の推奨の読みなら待たない。

## 1. 読んだもの (local main `d79fd3524`、2026-09-30 18:45 JST の fold)

| wave | 一次資料 | main に入った commit (最初の追加) | 本 wave で使った内容 |
|---|---|---|---|
| md_18 | `output/insights/2026-09-29/vhash-interval-gc/README.md`、D2323・D2324 | `2ebacda6b` (2026-09-30 12:27) | 長い read-only tx の生成器 `CICADA_INTERVAL_LONGTX` の `ronly_wait`、build job 178 s |
| md_29 | `output/insights/2026-09-30/vhash-workload-space/README.md`、D2329 | `4449cd02a` (13:20)、結果 `daae17f78` (15:18) | batchR は計器 patch の中、1 走行の実時間 3.6〜5.0 s、build 1 binary 22.6 s |
| md_31 | `output/insights/2026-09-30/vhash-early-abort-policy/README.md`、D2320 | `d5dd187df` (14:28) | 待機型の長い tx の完了率 (skew 0.9 で中央値 0.12)、job 194〜207 s、壊し (pending) の不到達 |
| md_32 | `output/insights/2026-09-30/ccbench-cicada-promotion-uaf-fix/README.md`、D2327 | `9accc3ca1` (16:36) | 修理 4 件の経路、local branch `izanagi-cicada-promotion-uaf-fix` は push していない |
| md_34 | 草稿 §15、D2325 | `f9b158862` (15:36) | p\* = c、K\* = 1、E_sp(c) の knob |
| md_36 | `output/insights/2026-09-30/vhash-proof-assumptions-vs-impl/README.md` | `1deffba38` (16:00) | 構成 E の書き込み検査の走査中の回収の穴 (§3.2)、直し方の候補 (a)(b)(c) (§6) |
| md_14・md_20・md_21・md_22・md_23 | 草稿 §0.1・§15.1 の各一次資料、D2317 | (既着地) | 単価、門の所要、壊しの検出、ro-gcflag の門の範囲、`CICADA_VHASH_WL` |

main に一次資料が無いもの (branch の commit と依頼文 `/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_N.txt` の範囲でだけ読んだ): md_33 (M、branch `worktree-dev-wave-cicada-certified-m`、patch だけで README なし)、
md_35 (floor、branch `worktree-dev-wave-cicada-between-run-floor`、時間窓 1 の Y5・Y50・Y95 の生データ `bc02cf0d8` だけ)、md_37 (hot 配置の書き込み側、branch `worktree-dev-wave-vhash-hot-block-v2`)、
md_39 (branch `worktree-vhash-econn-wscan-fix` の tip は main と同じ `d79fd3524` で固有 commit なし、19 時台 JST)。

事実の抽出には読み取り専用の子 3 本 (sonnet) を使い、S2 の設計に効く点 (md_21 の壊しの検出、md_20 の門の走行数、D2310・D2327 の修理の経路、md_18・md_29 の build 所要) は親が一次資料を開いて確かめた。

## 2. 区間の被覆と族の大きさ (S2 の発効の後に族が増えた場合)

§8.2 の順序統計量の区間 [d_(r), d_(n+1−r)] の被覆は 1 − 2 P(Binom(n, 1/2) ≤ r − 1)。これが 1 − 0.05 / m 以上になる最大の m を n・r ごとに計算した。
スクリプト `/work/SFC/tanab/tmp/vhash-eval-s2-plan-2026-09-30/coverage.py` (sha256 `3d4c22b9…6a`)、出力 `coverage.stdout.txt` (sha256 `399c2de6…a9`) の逐語:

```
n= 9 r=1 coverage=0.996094 max_m=12
n= 9 r=2 coverage=0.960938 max_m=1
n=10 r=1 coverage=0.998047 max_m=25
n=10 r=2 coverage=0.978516 max_m=2
n=11 r=1 coverage=0.999023 max_m=51
n=11 r=2 coverage=0.988281 max_m=4
n=12 r=1 coverage=0.999512 max_m=102
n=12 r=2 coverage=0.993652 max_m=7
n=13 r=1 coverage=0.999756 max_m=204
n=13 r=2 coverage=0.996582 max_m=14
n=14 r=1 coverage=0.999878 max_m=409
n=14 r=2 coverage=0.998169 max_m=27
m=19 level 1-0.05/m = 0.997368
m=20 level 1-0.05/m = 0.997500
m=27 level 1-0.05/m = 0.998148
m=28 level 1-0.05/m = 0.998214
```

読み方: m = 19 のとき §8.6 の規則が使う区間は、n = 14 で順位 2、n = 10〜13 で順位 1。これらがそのまま有効なのは、n = 14 で m′ ≤ 27、n = 11〜13 で m′ ≤ 51 以上、n = 10 で m′ ≤ 25。
したがって「S2 の語が族の拡大で変わらない」と書けるのは m′ ≤ 25 までで、「m ≤ 27 まで変わらない」は反例 (n = 10・m′ = 26 で欠測に落ちる) があるので書かない。
草稿は、段 6 の review を受けて、S2 の発効の後に足す判定を別の族にする形を登録し、この境界は「1 つの族として読み直した場合」の参考に留めた (草稿 §16.1)。
草稿 §16.10 の「本案の効果を族に入れると m = 23」でも区間は変わらない (n = 10 の順位 1 の被覆 0.998047 ≥ 1 − 0.05 / 23 ≈ 0.997826)。

## 3. patch の重ね適用 (文字の上だけ)

pin C (`68106660686232781bca3be792a750d3e19d7a8a`) の `cc/cicada` を worktree から repo 外へ写し、`git apply` (fuzz なし) で順に当てた。repo は変えていない。
スクリプト `/work/SFC/tanab/tmp/vhash-eval-s2-plan-2026-09-30/apply_check.py` (sha256 `b023754c…a6`)、出力 `apply_check.stdout.txt` (sha256 `057fe4f4…24`) の逐語:

```
== E_series
  cicada-forwarding-variant.patch: rc=0 last_stderr='Applied patch cc/cicada/ycsb_cicada.cc cleanly.'
  cicada-forwarding-gc.patch: rc=0 last_stderr='Applied patch cc/cicada/ycsb_cicada.cc cleanly.'
  cicada-forwarding-target.patch: rc=0 last_stderr='Applied patch cc/cicada/transaction.cc cleanly.'
  result=applied
== E_series+ro_gcflag
  cicada-forwarding-variant.patch: rc=0 last_stderr='Applied patch cc/cicada/ycsb_cicada.cc cleanly.'
  cicada-forwarding-gc.patch: rc=0 last_stderr='Applied patch cc/cicada/ycsb_cicada.cc cleanly.'
  cicada-forwarding-target.patch: rc=0 last_stderr='Applied patch cc/cicada/transaction.cc cleanly.'
  cicada-ro-gcflag-variant.patch: rc=0 last_stderr='Applied patch cc/cicada/transaction.cc cleanly.'
  result=applied
== ro_gcflag+E_series
  cicada-ro-gcflag-variant.patch: rc=0 last_stderr='Applied patch cc/cicada/transaction.cc cleanly.'
  cicada-forwarding-variant.patch: rc=0 last_stderr='Applied patch cc/cicada/ycsb_cicada.cc cleanly.'
  cicada-forwarding-gc.patch: rc=0 last_stderr='Applied patch cc/cicada/ycsb_cicada.cc cleanly.'
  cicada-forwarding-target.patch: rc=0 last_stderr='Applied patch cc/cicada/transaction.cc cleanly.'
  result=applied
== ro_gcflag_only
  cicada-ro-gcflag-variant.patch: rc=0 last_stderr='Applied patch cc/cicada/transaction.cc cleanly.'
  result=applied
== trace+E_series+ro_gcflag
  instr-cicada-trace.patch: rc=0 last_stderr='Applied patch cc/cicada/ycsb_cicada.cc cleanly.'
  cicada-forwarding-variant.patch: rc=0 last_stderr='Applied patch cc/cicada/ycsb_cicada.cc cleanly.'
  cicada-forwarding-gc.patch: rc=0 last_stderr='Applied patch cc/cicada/ycsb_cicada.cc cleanly.'
  cicada-forwarding-target.patch: rc=0 last_stderr='Applied patch cc/cicada/transaction.cc cleanly.'
  cicada-ro-gcflag-variant.patch: rc=0 last_stderr='Applied patch cc/cicada/transaction.cc cleanly.'
  result=applied
```

`last_stderr` は各 patch の最後に当たった file だけを示す (`--verbose` の最終行)。言えるのは「文字の上で重なる」ことだけで、build が通ること、条件 gate (`condition_meaning_gate.py`) を通ること、
TRACE=0 の命令列が trace patch の有無で一致すること、ro-gcflag と E の意味の相互作用 (E は待機の安全点で公開し、ro-gcflag は ro の commit で `mainte()` を呼ぶ) は確かめていない。
md_39 の修理 patch は存在しないので含めていない。

## 4. node 時間の積算の出所

計画の表は草稿 §16.7。単価の出所:

| 量 | 値 | 出所 |
|---|---|---|
| 待機型の job の 1 走行 (build・待ち込み) | 5.79〜5.88 s | md_14: 72 走行 (3 GC × 4 腕 × (性能 3 + 計数 3)) の job の Elapse 417〜423 s (一次資料 §4 の表、`data/gc-aggregate-compact.json` の腕数で走行数を確認) |
| 同上 | 5.93〜5.99 s | md_21: 待機型の job の Elapse 427〜431 s ÷ 72 走行。job と走行数の対応は README に無く、`data/target-aggregate-compact.json` の腕数 × rep から復元した |
| 上限側 | 6.5〜6.9 s | md_31: 6 job の Elapse 194〜207 s ÷ 30 走行 (性能 5 腕 + 計数 5 腕 × 3 rep と推定) |
| 1 走行の実時間 (build 抜き) | 3.6〜5.0 s | md_29 の所要 probe (28 走、Elapse 336 s) |
| build | 1 binary 22.6 s / 複数 binary の build job 178 s | md_29 / md_18 |
| 門 (48 thread・1M 件・走行 1 秒) | 41 s | md_20 の J2: 8 走行、Elapse 330 s (build・判定器込み)。判定器だけの最長は 41.6 s (15,109,669 行) |
| 門 (小さい cell) | 24 s | md_14 の検査 job 237 s / 10 走行 (草稿 §10.1) |

積算 (u = 5.8 s / 6.9 s、node 時間): S0-M 160 走行 → 0.26 / 0.31。S2 の門は 20 × 41 + 10 × 24 + 4 × 24 + 178 = 1,334 s → 0.37。S2 本走 700 走行 → 1.13 / 1.34。計 1.76 / 2.02。
S2 本走から副次の計数用 A_fix・A_stock (112 走行) を外すと 588 走行 → 0.95 / 1.13。

「30 秒走行の追加計測」(D2322 項 2 が見積りを求めた) の見積りは、md_22 にも D2322 にも数値が無い (`docs/paper-story-vhash/2026-09-30.md` にも「未試算」とある)。
本 wave は S2 を 3 秒のまま計画し、30 秒にすると 1 走行の実時間が約 6〜9 倍 (3 秒の走行の実時間 3.6〜5.0 s に対し 30 秒 + 約 1〜2 秒) になることだけを書いた。30 秒走行そのものの見積りは S2 の範囲外として残す。

## 5. 発効に残る条件 (S2) と段ごとの node 時間

条件と計画値の正本は草稿 §16.8・§16.7 である (本書に同じ一覧を複製すると改訂のときに食い違うので、項目名だけを挙げる):
md_39 の着地、修理の型の条件 (smoke)、重ねた build と条件 gate、CCBench の修理の到達の確認、f_T の択一、M の範囲、ユーザーの確認 (node 時間・削る順・本案の効果を族に入れるか)、発効の決定。

| 段 | 走行数 | node 時間 (u = 5.8 s〜6.9 s) |
|---|---|---|
| S0-M (f_M,c) | 160 | 0.26〜0.31 |
| S2 の門 | 34 | 0.37 |
| S2 本走 | 700 | 1.13〜1.34 |
| 計 | 894 | 1.76〜2.02 |

## 6. 確かめたこと・確かめていないこと

- **確かめたこと:** 区間の被覆の計算 (§2)。E 系 3 本・ro-gcflag・trace patch が pin の tree の写しに fuzz なしで重なること (§3)。md_21 の壊し (既読不一致を無視した E-now) が到達し、
  保持版検査が検出したこと (md_21 §5 の表、判定器の巡回は 0)。md_20 の J2 が 8 走行・330 s であること。D2310・D2327 の修理の説明が削除・scan・insert・promotion の経路を指すこと (決定文の読み)。
  草稿を参照する Python の test が無いこと (`grep -rln` で 0 件)。`python3 tools/check_docs.py` rc 0。
- **確かめていないこと:** 計測・build はしていない。重ねた build の compile、条件 gate、TRACE=0 の同一性、ro-gcflag と E の意味の相互作用。修理の hunk が S2 の build で実際に到達しないこと (§16.3 は推測)。
  md_39・md_33・md_35・md_37 の結果 (main に無い)。md_21 の job と走行数の対応 (復元) と md_31 の走行数 (推定)。48 thread・3 秒の門の所要。L-w の gate の小さい cell (thread 1・4、200 件) で生成器が意図どおり動くこと。
  S2 の cell で A_fix の修正の経路 (ro の commit) が踏まれる頻度 (rr50 の 10 操作 tx が read-only になる割合は小さい。門の走行全体の合計で 0 回なら、D2317 決定 4 により A_fix の門は完了しない。thread 1 の門の cell では read-only の commit が起きない)。
  M を重ねた場合の実走 (md_33 は main に無い)。条件 gate が重ねた組み合わせを受理するか。

## 7. 工程

- dev-wave 軽量版 (段 2・3 なし、実装面なし、変異 matrix は実装面の差分ゼロで免除)。段 6 の read-only review 1 本と焦点再レビュー 2 巡の結果は §8 に書く。
- 子: 事実抽出の Explore 3 本 (sonnet、read-only)。計算ノードは使っていない。

## 8. 段 6 レビュー

Codex (gpt-6-sol、medium、read-only) の review 1 本と焦点再レビュー 2 巡。出力は job dir の `stage6/review-out.md`・`focus1-out.md`・`focus2-out.md`。

| 巡 | call / 秒 | 判定 | 所見と親の裁定 |
|---|---|---|---|
| review | 7 / 299 | NO-GO (must-fix 2・should 3・nit 1) | A1: S2 の発効の後に族へ判定を足して読み直す手順が §8.4 (数え直しは発効の前に限る) と両立しない → real。発効の後に足す判定は別の族にし、m′ ≤ 25 は参考に下げた。A2: §7.2 規則 4 と「測らない判定も m に残す」の衝突、門の範囲 → real。§7.2 の読みを §16.1 に明記。A3 (判定器の rc)・A4 (A_fix の経路の到達を門の走行全体の合計で)・B1 (smoke 0 回の調べ方) → real。B2 (草稿と本書の重複) → 本書 §5 を縮めた |
| 焦点 1 | 6 / 223 | NO-GO (must-fix 1) | 前回 6 件は closed。新規: smoke の通過条件「前進の成功」は公開への到達を保証しない → real。「開始時より上げた公開の回数 ≥ 1」に替え、計数用 build がこの回数を出すことも条件にした |
| 焦点 2 | 3 / 82 | GO (must-fix 0) | 前回の 1 件は closed |
