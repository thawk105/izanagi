# 段 6 裁定 3 — 計測で壊し 3 走が 180 s の打ち切り (rc 124) になった件 (date 実測 18:2x の後に起草)

## 事実 (計測 raw `out/run1/raw-trace-0.json` の各 record の rc・elapsed、統合 3 = 69f7033dc の binary)
- trace job 0 の 18 走のうち、正例 10 走 (stock・B-k1・B-k8・post-k1・post-k8 × T1・T2) は rc 0・判定器 rc 3 (indeterminate)・clean。
- 壊し: post-B1 T1 = rc 0 (判定器 rc 1 non-serializable)、post-B2 T1・T2 = rc 0 (判定器 rc 1)、B2 計器版 T1・T2 = rc 0 (判定器 rc 1)。**post-stale-gap T1・T2 と post-B1 T2 は driver の 1 走 180 s の打ち切り (rc 124)** (stale-gap T1 は elapsed 180.06 s、stderr の末尾まで changed event を出し続けていた)。
- 集計 `aggregate` は `invalid broken trace run` (rc 124 の壊しを fail-closed で拒否) で止まった。perf 3 job・count・trace job 1 は rc 0。

## 原因の見立て (コードを読んだ親の推定、実測で確かめてはいない)
- post-B1 は hot の hit のたびに (壊しの条件 = ro・key の奇偶・選んだ版が確定、を確かめる前に) `ver->next_` を確定版に当たるまで辿る。選んだ版が GC の切り離し点なら、その先は切り離されて REUSE_VERSION で再利用されうる (段 6 焦点再レビューの F2)。再利用中の版の next_ を辿る走査と、再利用中 (status unused) の版を返した後の第 2 段の待ち (committed でも deleted でもない間回る) は、どちらも終わらない可能性がある。
- post-stale-gap は hot への書き足しを省くので、§3 の再利用の論証 (切り離し点は読み手の copy に居る) が成り立たない。隣接確認を外した読み手は切り離し点より古い X を選びうり、X が再利用中 (unused) なら第 2 段が終わらない。
- どちらも壊しの中だけの現象で、正例 (B・B-post の本体) の 10 走 + T3 の 5 走は終わっている。

## 裁定
| 項 | 採否 | 内容 |
|---|---|---|
| R1 post-B1 の走査 | 採用 (U1) | 壊しの条件を先に確かめ、条件が成り立つときだけ `older = ver->next_` の 1 段だけを見る (確定版でなければ壊さない)。md_23 の B1 の「1 つ古い」に合わせ、疎な hot でも物理の直後にする。 |
| R2 再利用中の版で第 2 段が終わらない | 採用 (U1) | post-B1 と post-stale-gap の 2 本で、第 2 段の待ちの中で status が unused か invalid になったら、その読みを「dead」と数えて latest からの stock の走査へやり直す (壊しの選択は捨てる)。終了時に `CICADA_BREAK_DEAD slug=<slug> dead=<n>` を stderr に 1 行。 |
| R3 stale-gap の X の検証 | 採用 (U1) | 隙間を越える hit で X を使う前に、X の実際の wts が hot の wts[i] と一致することを確かめる。違えば dead と数えて stock へ。 |
| R4 driver の DEAD 行と打ち切り | 採用 (U2) | post-B1 と post-stale-gap では DEAD 行を必須にして observed に `dead` を残す。**壊しの走が rc 124 のときは aggregate を止めず、分類 `hung` (判定なし) として記録する。正例 (trace-*) の rc 124 は従来どおり fail-closed。** 受理と拒否の含意: 壊しの打ち切りは検出力の証拠にならない「判定なし」として残り、正例の打ち切りは集計全体を止める。通る正例: 壊し 1 走が rc 124、他が rc 0 → aggregate は通り、その壊しの status は hung。 |
| 変異の追加事前登録 | 採用 | M14: 正例の rc 124 を hung として受理する → test が kill。M15: DEAD 行が無くても受理する → test が kill。 |

## 計算の再見積り
これまでの Elapse の和 4,379 s (焦点走 166 + 133、smoke 351、build 291、perf 1,558、count 86、trace 859 + 23、集計 9、変異 448 + 455。焦点走 focus2 は login で走り job の記録なし)。追加の見込み: build 約 300、trace job 0・1 の再走 約 400、集計 10、変異 final の再走 約 460、焦点走 約 150 → 合計 約 5,700 s。上限 7,200 s 未満なので続ける。perf と count の raw (run1) は perf / count の binary の patch が変わらないので使い続け、trace だけ新しい build (run2) で取り直す。
