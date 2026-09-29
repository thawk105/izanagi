# Cicada の書き込み側 rts 検査に、小モデル v0 の穴 (PENDING の直前版で検査を打ち切る) は無い (VHash 論文、[T-2882])

- 着手: 2026-09-29 (dev-wave `dev-wave-vhash-cicada-rts-check`、背景 job、Pegasus login)
- 依頼: `/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_8.txt` (並行 VHash wave の md_8)
- 対象: [T-2882]。根拠は md_4 の一次資料 `output/insights/2026-09-29/vhash-forwarding-model/README.md` §7.1 (以下「md_4 資料」)
- 読んだ実物:
  - CCBench の Cicada。gitlink `68106660686232781bca3be792a750d3e19d7a8a` の `cc/cicada/transaction.cc`・`cc/cicada/include/transaction.hh`。以下の行番号はこの版のもの
  - Cicada の原論文。Lim, Kaminsky, Andersen, "Cicada: Dependably Fast Multi-Core In-Memory Transactions", SIGMOD 2017。関連研究 wave が取得した PDF (sha256 `4f6c5118a51ffbae3c5795e457f5cca91012a07a7e96dada32c115bedf176dd4`) のテキスト抽出 `/work/1/SFC/tanab/tmp/vhash-related-work-2026-09-29/src/cicada-nolayout.txt` (sha256 `499bf066f106bc480beca1e90efcfcde292c8ed21c21a740f76db1117a3fc5b7`)。以下の「論文 N 行」はこのテキストの行番号
  - md_4 の小モデル `tools/vhash_forwarding_model/model.py`。import しただけで、編集していない
- 実装面の変更: なし。repo 外の probe 2 本で小モデルを動かした (§4、§7)

## 0. 結論

1. **CCBench の Cicada (上記 gitlink の静的な読み) は v0 の穴の形を持たない。** 最終の書き込み検査 (validation の (b)) は、自分が設置した版の次から下へたどる。PENDING に当たると、確定するまで spin で待つ。ABORTED は飛ばし、最初の COMMITTED または DELETED 版に着いたら止まる。COMMITTED ならその rts を見て、DELETED なら検査は失敗する (§2 の表)。v0 のように「PENDING の直前版 1 つの rts を見て通す」経路は、この検査には無い。
2. **原論文も同じ規則と読める。** 書き込み検査の対象は「現在の可視版」である (§3.4 (b))。可視版の探索は PENDING を待つ (§3.2)。付録 A の定義 1 も、可視版を確定済みの版に限っている。書き込み側で PENDING を待つという読みは、これらの組み合わせによる。付録 A 補題 2 の待ちの記述は読み側についてのものである。
3. **v0 の規則は md_4 のモデルが独自に決めたもので、Cicada の規則ではない。** 出典メモ §4 は validation の順序を要約し、PENDING を待つことも書いている (§3)。穴の出所は、md_4 がその順序を模すときに、書き込み検査の対象を「PENDING でもよい直前版 1 つ」と決めた点にある。メモが v0 の規則を述べているわけではない。
4. **同じ小モデルに Cicada の待ちを入れると、S8 の閉路は消えた** (§4。固定場面の有界モデルでの全探索の結果)。
   - 待ちの 2 規則を入れた構成を vC と呼ぶ。書き込み検査・読み検査とも、他 txn の PENDING は確定まで待つ。
   - 「窓」と呼ぶ状態に到達した: W が PENDING の P:A に待たされ、しかも A10 の rts が W の時刻を超えている。v0 なら W がここで検査を通ってしまう。
   - 窓から到達した 12 個の終端は、次の 2 種類だけだった。
     - P が確定し、T が abort し、W が確定する
     - P が abort し、T が確定し、W が abort する
   - 窓から到達した状態のうち、T と W が両方 commit している状態は 0 だった。
   - forwarding を外した構成でも同じ結果だった。
5. **md_8 項 2 の再現走行 (実 Cicada を trace 付きで走らせて判定器に掛ける) は行っていない。** 項 2 の発火条件「同じ形を持つなら」が成立しないためである。したがって実 Cicada の直列化可能性について、本資料が新たに言えることは無い。§5・§6 に書く範囲の外については結論しない。

論文 (次の版) に書ける結論の文言案:

> md_4 の小モデル v0 に出た閉路は、書き込み側の rts 検査を「PENDING でもよい直前版 1 つ」で打ち切るという、モデル独自の規則による。Cicada の原論文の可視版の定義と、CCBench の最終書き込み検査は、PENDING の確定を待ち、ABORTED を飛ばしてから確定版を調べる (削除済みの版なら失敗する)。したがって、この経路を比較相手 Cicada の欠陥とは言えない。同じ小モデルに待ちを入れると、固定場面 S8 の全探索では、窓から到達した終端はすべて T か W の一方が abort しており、閉路は出なかった。実装全体の直列化可能性と進行性は、この照合と探索からは結論しない。

## 1. 問い

md_4 資料 §7.1 の v0 反例 (場面 S8、30 step) は、W の書き込み検査が「直前版」として PENDING の A40 だけを見て通るものだった。その下の確定版 A10 には、T が時刻 70 で読んだ印 (rts 70) が付いている。これが Cicada の原論文や CCBench の Cicada にも当てはまるなら、比較相手 (基準線) の正しさの問題になる。

## 2. 対応表 (v0 の書き込み検査の各要素)

| 要素 | md_4 モデル v0 / v1 | 原論文 | CCBench |
|---|---|---|---|
| 検査する版 | v0 は wts 未満の最大版 1 つ (PENDING でもよい)。v1 (R9') は最初の COMMITTED 版までの全版の rts を見る (`model.py` の w_check 節、md_4 資料 §2.2) | 書き込み集合の「現在の可視版」の rts ≤ tx.ts (§3.4 (b)、論文 737-740 行)。可視版は wts 降順の探索で選ぶ (§3.2、論文 649-653 行) | 設置した新版の next から下へたどり、最初の COMMITTED または DELETED 版に着いたら、その 1 版の rts を見る。DELETED なら失敗 (`transaction.cc:576-593`)。**v0 とも v1 とも違う** |
| PENDING に当たったとき | v0 はその版の rts を見て検査を終える。v1 はその版の rts も見て下へ進む。**どちらも待たない** | "For PENDING, it spin-waits until the status is changed." (§3.2、論文 649-650 行) | 確定まで spin で待ち、その後に探索を続ける (`transaction.cc:579-580, 584-585`)。**v0 の穴を塞ぐ手順はこれ** |
| ABORTED に当たったとき | 版の並び (`_ordered`) から最初から除く | "For ABORTED, it ignores this version and proceeds to an earlier version." (§3.2、論文 650-651 行) | 飛ばして次へ進む (`transaction.cc:581-585`) |
| 可視版の定義 | — | 付録 A 定義 1: 「確定済みの版のうち wts が最大で、tx の時刻より小さいもの」(論文 2076-2079 行) | — |
| 検査の順序 | 設置 → 既読版の rts 更新 → 読み検査 → 書き込み検査 → 確定 | 設置 → rts 更新 → version consistency check ((a) 読み、(b) 書き込み) (§3.4、論文 732-740 行) | precheck → 設置 (`transaction.cc:473-531`) → rts 更新 (536) → 読み検査 (543-570) → 書き込み検査 (572-593)。同じ順序 |
| 設置時の rts 検査 | 無い | 設置の段で可視版の rts ≤ tx.ts を満たさなければ abort (§3.4、論文 741-746 行) | 設置のループ (488-529) では rts を見ない。最終検査で見る |
| 設置前の早期 abort | 無い | 書き込みに使う可視版の rts ≤ tx.ts を早めに調べうる (§3.2、論文 663-672 行) | `update()` の 276-283 は、選んだ版が COMMITTED で rts が超過したときだけ abort する。PENDING なら待たずに通すが、最終検査が改めて待つ |
| precheck | 無い | — | 書き込み集合の前半を走査し、INSERT を除き、`continuing_commit_` が閾値未満の要素だけを調べる (`transaction.hh:247-293`)。通常 update の分岐は PENDING と ABORTED を待たずに飛ばし、最初の COMMITTED / DELETED 版の rts を見る (274-288)。RMW / DELETE の分岐は先頭版の wts と rts を見る (269-273)。失敗時に早く止めるだけで、成功しても最終検査へ進む (`transaction.cc:473-476`)。最終検査の代わりにはならない |
| 読み検査で、可視位置に他 txn の PENDING | `_validation_visible` が他 txn の PENDING を返し、読んだ版と違うので abort (待たない) | 付録 A 補題 2 の証明: "tx is blocked in the version consistency check step while v0 is PENDING" (論文 2092-2094 行) | 確定まで待ち、ABORTED を飛ばしてから読んだ版と比べる (`transaction.cc:543-569`) |

根拠の割り当てについて:

- 書き込み側で PENDING を待つことの原論文の根拠は、§3.2 の探索規則と §3.4 (b) の「現在の可視版」の組み合わせ、それに定義 1 である。
- 付録 A 補題 2 の待ちの記述は、読み側の検査についてのものである。
- 付録 A は insert と delete の証明を省いている (論文 2075 行)。

関連研究の一次資料 (`output/insights/2026-09-29/vhash-related-work/README.md` §2 末尾) によると、CCBench 論文 §3.3 は、原作の Cicada の version consistency check の不備を直したと書いている。これは読み検査 (`transaction.cc:561-565` のコメント) の話である。本資料は原作の実装コードを読んでいない。

## 3. 食い違いの出所

- 出典メモ §4 は validation の順序を「pending 版の設置 → read 版の rts 更新 → version consistency check」と要約している。表の下の段落には「対象 timestamp 以下の PENDING 版を単に飛ばすのではなく、その状態確定を待つ」とある。
- 関連研究の一次資料 §3 は、この 2 点を原論文 §3.2・§3.4 と一致すると確認している。
- md_4 のモデルは、通常の read (R1) では PENDING を待つ。一方、commit 時の書き込み検査 (R9) の「直前版」は「ABORTED を除く wts 未満の最大版 1 つ (PENDING でもよい)」と定めた (md_4 資料 §2.2)。

したがって、v0 の穴の規則はメモにも原論文にも無い。md_4 がメモの順序の要約を模したときに、書き込み検査の対象と PENDING の扱いを独自に決めたことから生じた。md_8 の「モデルの前提がメモの要約に由来する」は、順序については正しい。一方、書き込み検査の対象については当たらない。md_4 資料は §2 冒頭で「Cicada の実装と一致するとは主張しない」と断っており、その断り書きのとおりだった。md_4 資料は本 wave の所有外なので書き換えず、訂正はここに置く。

## 4. 小モデルでの確認 (repo 外 probe)

### 4.1 作り

`/work/SFC/tanab/tmp/vhash-cicada-rts-check-2026-09-29/probe_vc.py` (sha256 `590e3c43b5898d8ec361053953b098343385058dfc2bb49b0b2a9edee77f991e`)。

- md_4 のモデルを import し、探索器が呼ぶ `enabled_steps` だけを差し替えた。v0 と v1 は元の関数へそのまま渡す。
- 構成 vC は v1 を土台に、次の 2 か所だけを変える。
  - 書き込み検査: wts 未満の版を降順に見る。他 txn の PENDING に当たったら、検査している txn 自身の step を無効にする (= 確定まで待つ)。最初の COMMITTED 版の rts ≤ 自分の時刻を要求する。
  - 読み検査: 可視位置に他 txn の PENDING があれば、検査している txn 自身の step を無効にする (待つ)。
- 構成名の末尾 `nf` は forwarding なしを表す。Cicada には forwarding が無いので、R4 の候補を常に「なし」にした。
- 探索器 (`explore`) は、どの txn も進めない状態を deadlock として、閉路・GC 違反とは別に数える。

v1 と vC は別物である。v1 は PENDING 版の rts も見て、さらに下へ進む (待たない)。vC は待ってから、確定した版 1 つの rts を見る。v1 に反例が無いことを、vC (Cicada の規則) の結果と同じものと扱わない。

### 4.2 S8 の結果

生出力は `raw/probe-summary.json`・`raw/window-vC.json`・`raw/window-vCnf.json`・`raw/S8-v0nf.json`。表の値はこれらから写した。

| 構成 | 探索 | 訪問状態数 | 閉路 (J1) | 時刻順の不一致 (J2) | GC 違反 (J3) | deadlock | 最短反例 |
|---|---|---|---|---|---|---|---|
| v0 | 完了 | 47,448 | あり | あり | なし | 0 | 30 step (forwarding の step 0) |
| v0nf | 完了 | 44,692 | あり | あり | なし | 0 | 30 step (forwarding の step 0) |
| v1 | 完了 | 51,952 | なし | なし | なし | 0 | — |
| v1nf | 完了 | 49,196 | なし | なし | なし | 0 | — |
| vC | 完了 | 26,132 | なし | なし | なし | 0 | — |
| vCnf | 完了 | 23,472 | なし | なし | なし | 0 | — |

- **probe が元のモデルを変えていないことの確認:** v0 と v1 の全 10 場面の訪問状態数と J1 / J2 / J3 は、md_4 資料 §5.1 の表と全行一致した。
- **穴は forwarding と無関係:** forwarding なしの v0nf でも、反例は md_4 資料 §7.1 と同じ形だった。step 28 で W が PENDING の P:A の rts だけを見て通り、閉路 T →rw(A)→ W →rw(B)→ T ができる。S8 の穴は v0 の書き込み検査だけで生じる。

### 4.3 窓に入った後の決着 (vC / vCnf)

窓の定義: W が A の書き込み検査にいて、P:A が PENDING で、A10 の rts が W の時刻 (50) を超えている状態。v0 なら W がここで P:A の rts (40) だけを見て通り、閉路へ進む。

解析には `/work/SFC/tanab/tmp/vhash-cicada-rts-check-2026-09-29/window_outcome.py` (sha256 `36376e36a5f503761915e203a9c36643e2565aa7cd9728fce17f1a6fdfe620d7`) を使った。全到達状態を列挙し、窓状態から先を数えた。vC と vCnf は同じ値だった。窓は状態の述語であり、「待った」という出来事を直接記録したものではない。窓状態では W の検査 step が無効になっている (待っている)。

| 項目 | 値 |
|---|---|
| 窓状態の数 | 336 |
| 窓から到達できる状態の数 | 3,660 |
| そのうち、T と W が両方 COMMITTED の状態 | **0** |
| 窓から先の終端状態 | 12 (未完了の txn を残す終端は 0) |
| 終端での決着 | 「T=ABORTED・W=COMMITTED・P=COMMITTED」6、「T=COMMITTED・W=ABORTED・P=ABORTED」6 |

初期状態から窓を通って W が決着するまでの最短列を、両方の決着について取った (`raw/window-vCnf.json` の `shortest_via_window_to_w_aborted`・`shortest_via_window_to_w_committed`。vC も同じ列)。どちらも 30 step である。

**W が abort する側:**

1. T が A10 を読み、B に T:B を設置し、A10 の rts を 70 に上げる (step 1〜7)
2. W が B11 を読み、A に W:A を設置し、読み検査を通る (step 8〜17)
3. P が A に P:A を設置する (step 21)。ここで窓に入る。W は P:A の確定を待つ
4. P の書き込み検査が A10 を見る。rts 70 > 40 なので失敗し、P は abort する (step 25〜27)
5. 待っていた W の書き込み検査が、ABORTED の P:A を飛ばして A10 を見る。rts 70 > 50 なので失敗し、W は abort する (step 28〜30)

**W が確定する側:**

1. T が A10 を読み、T:B を設置する (step 1〜6)。T はまだ A10 の rts を上げていない
2. W が B11 を読み、W:A を設置し、読み検査を通る (step 7〜16)。P が P:A を設置する (step 20)
3. P の書き込み検査が A10 を見る。この時点の rts は T が上げる前なので通る (step 24)
4. その直後に T が A10 の rts を 70 に上げる (step 25)。ここで窓に入る
5. P が確定する (step 27)。待っていた W の書き込み検査は、確定した P:A (rts 40 ≤ 50) を見て通り、W は確定する (step 28〜30)

この列は W の確定で終わっており、T の決着は列に含まれない。窓から到達した終端のうち W が確定したものは、すべて T が abort していた (上の表)。モデルの読み検査の規則から読むと、T (時刻 70) の A の可視版は、この時点で確定した W:A (時刻 50) になる。これは T が読んだ A10 と違うので、T は abort する。T の abort の経路は列ではなく、終端の分類とこの読みによる。

以上は固定場面 S8 の有界モデルの到達状態についての結果である。実 Cicada のすべての実行について言うものではない。

### 4.4 他の場面 (補助)

S1〜S10 の 10 場面 × {v0, v1, vC, v0nf, v1nf, vCnf} の 60 構成は、すべて探索完了・deadlock 0 だった。閉路は S8 の v0 と v0nf だけに出た (`raw/probe-summary.json`)。

- 次の場面の nf 構成では、場面が狙った割り込み (場面 witness) に到達していない: S2・S3・S6・S7・S10。これらの場面は forwarding を前提にしている。したがって、これらの nf 行の「反例なし」は、狙った割り込みを検査した結果ではない。
- S9 の場面 witness は、md_4 の危ない版 U2 の step を要求する。そのため、どの構成でも未到達である (md_4 資料 §5.1 と同じ)。
- 待ちで step が無効になった (到達状態, txn) の組の数は、`raw/probe-summary.json` の `blocked_w_check`・`blocked_v_check` にある。例: S8 の vC では 648 と 1,944。これは待ちが実際に起きたことを示す延べの数で、状態の数や待ち時間ではない。

## 5. 確かめたこと・確かめていないこと

確かめたこと:

- CCBench (上記 gitlink) の最終書き込み検査・読み検査・設置・precheck・早期 abort が PENDING と ABORTED をどう扱うか (§2、静的な読み)。
- 原論文の該当節と付録 A (§2)。
- 小モデルの固定 10 場面で、Cicada の待ちの 2 規則を入れた構成に閉路・GC 違反・deadlock が無いこと。S8 の窓から到達した 12 終端はすべて T か W の一方が abort しており、T と W が両方 commit する到達状態は 0 であること (§4)。

確かめていないこと (結論しないこと):

- **実 Cicada の実行での再現・非再現。** trace 付きの走行は md_8 項 2 の発火条件を満たさないので行っていない。md_3 の stock 7 走行 (200 キー、thread 1 / 4、rmw false を含む。`output/insights/2026-09-29/vhash-cicada-verifier/README.md` §3) は巡回 0 だった。ただし判定の上限は indeterminate で、PENDING に当たった検査の経路を通ったかどうかも記録していない。
- 探していない条件: 少数キー・多 thread・rmw false の狙い撃ち、設置から確定までを意図的に遅らせた高衝突の走行、PENDING の待ちの実機での頻度と所要時間。
- **モデルと実装の差。** vC は版を wts で整列して選ぶ。CCBench は設置した新版の next から連結リストをたどり、途中挿入・切り離し・版の再利用がある。vC の読み検査の待ちは、CCBench の `later_ver_` からの走査の近似である。insert・delete・inline 版・read-only 経路・GC の回収は、vC の結果から評価できない。
- **C++ の記憶模型上の相互見落とし (段 3 相談の指摘、要検証)。** 次の 2 つの組が互いに古い値を読み合う形 (store-buffer 形) を、acquire / release の指定だけでは排除できない可能性がある。
  - 読み手の「rts の CAS → 版列の読み」
  - 書き手の「版列の CAS → rts の読み」

  x86 では lock 付きの命令が全順序の fence になるので、本 wave の実行環境 (Pegasus、x86) では到達しないと親は推定している。ただし検証していない。v0 とは別の形であり、本資料の結論 (v0 の形は無い) の範囲外である。
- CCBench の原作 (Cicada の作者の実装) のコード。
- 実装全体の直列化可能性と進行保証 (lock-free 性、spin の飢餓)。

## 6. md_8 の各項への対応

| md_8 の項 | 対応 |
|---|---|
| 1. 原論文と CCBench を読み、v0 の規則と同じか違うかを表にする | §2 |
| 2. 同じ形なら、trace と判定器で再現する | 発火せず (同じ形を持たない)。探していない条件は §5 |
| 3. 持たないなら、実物のどの手順が穴を塞ぐかと、モデルの前提との食い違いを書く | 塞ぐ手順: 書き込み検査の PENDING の待ち (`transaction.cc:579-585`、論文 §3.2)。食い違い: §3 |
| 4. 穴が確定したら直し方は別 item | 穴なしのため item を作らない |

## 7. 再現

```bash
# repo 外。md_4 のモデルがある作業木を probe_vc.py の WORKTREE に指定する
python3 -u /work/SFC/tanab/tmp/vhash-cicada-rts-check-2026-09-29/probe_vc.py <出力 dir> --protocols v0,v1,vC,v0nf,v1nf,vCnf
python3 -u /work/SFC/tanab/tmp/vhash-cicada-rts-check-2026-09-29/window_outcome.py <出力.json> vCnf
```

60 構成の探索所要の合計は 47.0 秒 (`raw/probe-summary.json` の `seconds` の和、Pegasus login)、窓の解析は各数秒だった。計算ノードは使っていない。

## 8. 工程

- 段 2 の plan 1 本、段 3 の相談 2 本 (正しさ境界 / 実効性・過剰・削除)、記録前の独立レビュー 2 本と修正後の焦点再レビュー 1 本 (§9)。いずれも read-only の codex (gpt-6-sol)。
- 相談の所見はすべて文言・根拠の割り当て・限界の明記として採用した。中心の結論を覆す所見は無かった。
- 相談 B の要求 (窓から abort への因果を示せ) に応えて、§4.3 の解析を足した。

## 9. 記録前の独立レビュー

2 本 (レンズ: 事実照合 / 過大主張・過剰・削除) とも、中心の結論を覆す不一致は無かった。§2 の file:line・論文の行番号と引用、§4 の数値 (訪問状態数、30 step、窓 336、窓後 3,660、両 commit 0、終端 12 の内訳、blocked の 648 / 1,944、所要の和 47.0 秒、witness 未到達の場面) は、照合元と生出力に一致した。直した点は次のとおり。

| 所見 | 種別 | 直し方 |
|---|---|---|
| W が確定する側で、T が待つ相手は P:A ではなく、より新しい W:A (時刻 50) | must-fix (事実照合) | 解析に両決着の最短列を足し、実際の列から §4.3 を書き直した |
| 「どの割り込みでも」「必ず」が、固定 S8 モデルの到達状態の範囲を超えて読める | must-fix (過大主張) | §0・論文向け文言・§4.3 を「窓から到達した終端・状態」の数に限定した |
| 「最短列」は、1 つの窓状態からの最短で、全窓状態についての最短ではなかった | should-fix | 初期状態から窓を通る最短列に取り直した |
| W が確定する側の列が生出力に無い | should-fix | 同上。T の abort は列ではなく終端の分類による、と明記した |
| precheck は `continuing_commit_` の条件で要素を省く | should-fix | §2 の表を直した |
| §0 と論文向け文言で、DELETED なら失敗することが抜けていた | should-fix | 追記した |
| §0 で、原論文の書き込み側の根拠が組み合わせによる読みであることを示していなかった | should-fix | 追記した |
| §4.1 の「その txn の step」が P と W のどちらか曖昧。窓が状態の述語であることの明記 | should-fix | 直した |
| x86 での到達性の推定と、工程の記述は削ってよい | 削除候補 | 残した (推定は未検証と明記済み、工程は数行) |

修正後に焦点再レビューを 1 本行った。全所見が closed、新しい must-fix はなかった。should-fix 2 件も直した。

- 件数の数え違い (worklog fragment)
- precheck が INSERT を除くことの記述 (§2)
