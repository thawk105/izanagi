---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-03
wave: dev-wave-cross-protocol-search-20260903
seq: 1
title: 証明面を持たない protocol が certified を名乗れないようにした — クロスプロトコルの手前に正しさの非対称があった (コード + テスト、branch worktree-dev-wave-cross-protocol-search-20260903、変異 3/3 KILLED)
---

## 本文

依頼は「クロスプロトコルを進化探索へ組み込む」だったが、一次資料を当たると**方向はすでに
ユーザー裁定で決着していた** (2026-08-11 の T-755 Q1〜Q3 全問 (a)、D1360)。したがって推定の
やり直しはせず、実装残余の特定へ切り替えた。

**当初の見立て「塞いでいるのは compiled-source の束縛だけ」は、親が段 2 待機中に自分で覆した。**
手前に mocc の正しさ証明の非対称があった。`Integrity.clean()` は 11 個のカウンタが 0 かだけを見て、
その検査が当該 protocol に存在したかを見ていない。lock 被覆 (`X` 行) と permutation 保存 (`P` 行) の
emitter は silo にしか無く、si と mocc では構造的に 0 になる。**両者は「検査を通った」のではなく
「検査が無い」まま certified を名乗れていた。**

**`I` (write-intent) 面は silo も持たない。** `patches/README.md` の write-intent shadow の節が
「実装 commit は izanagi-trace ブランチ側 (pin 前進はユーザー裁定待ち — それまで pinned producer は
I を emit しない)」と明記する。したがって `I` を連言に加えると silo の正例が消えるため、
gate は `X`/`P` の 2 面に限り、`I` は 3 面評価に含めて記録だけする形に裁定した。
**`I` の閉鎖は gitlink の pin 前進に依存する。**

**手続き:** `DW-O13` (gate・検証の新設) の成立が段 2 待機中に判明し、最遅読了段 (段 2 前) を
過ぎていたため、読み込み契約に従って**段 2 へ巻き戻した**。段 3 レンズ B がこの巻き戻しを
「過剰な自縛ではない」と独立に裁定した。巻き戻し前の plan と 2 レンズは成果物として流用せず、
確立した事実だけを裁定として残した。

**段 6 の敵対レビュー 2 本が独立に同じ迂回口へ到達した。** 証明面の判定が build 終了後に
source root の可変ファイルを読み直しており、判定の入力と build がコンパイルした bytes の同一性が
無かった。build の後で対象 source へ呼出しを書き足せば、emitter を持たない binary でも
証明面ありと判定されえた。capability の発行も genome と source evidence に束縛されていなかった。
fix でこれを閉じた。**これは親の段 4 設計には無かった防壁である。**

レビューは**裁定外の受理集合縮小**も 1 件見つけた。共通化の際に旧 D1373 には無かった制限
(protocol の文字種、絶対 path と `..` を含む CMake source path の拒否) が混入しており、
floor admission の受理集合が裁定外で縮んでいた。fix で戻した。

**この wave は安全前提であって cross-protocol の実装完了ではなく、論文の主張も 1 行も動かない。**
段 3 レンズ B の判定をそのまま受け入れる。mocc への計装 (RWLOCK と CLL を真実源とする。silo の
Tidword ベース計装は転用不可) と `I` 面の閉鎖は後続である。

**受入は緑で終えた。** 最終 tip `aeafac37b` で全走 **20110 passed / 92 skipped / 赤 0** (518 秒)。
途中の 400 赤は未 commit の enforcement closure による contract-loader-drift で、実装の回帰では
なかった (`contract_loader_binding` 55 hit、`contract-loader-drift` 22 hit を実測して確認)。
commit 後は 9 赤 → 6 赤 → 2 赤 → 0 と閉じた。全走時間は 483 秒 → 780 秒 → 518 秒で元の水準へ戻した。

**変異 matrix は緑である。** baseline PASSED、**KILLED 3/3、MISMATCH 0、SURVIVED 0、
期待 node 完全一致 3/3**。走行後に作業ツリーが commit と一致することを確認した。

**erratum (`DW-M08`)。** 初回の本走は runner argv を全走にしたため、期待 node が単一 file 前提の
登録と食い違い 3 件とも MISMATCH になった。機構自体はそのとき発火しており
(`test_campaign.py::test_pipeline_records_mocc_missing_proof_surfaces_and_does_not_commit` が
M01 で落ちた)。この初回を probe と明記し、観測した実態から期待 node を確定して再登録・再走した。
訂正は M02 だけで **1 件 → 21 件**。`P` の matcher を壊すと silo 側が広く落ちるためで、
M01 (4 件) と M03 (1 件) は当初登録のままである。

**変異 harness の起動条件で 3 回、道具の噛み合わせで 3 回落とした。** 起動条件は
`-rf` 必須 (`DW-M08`)、`--runner-mode local` は login node で拒否 (`site_policy.PEGASUS_LOGIN`)、
`category` は `negative` / `positive` / `both-layers` の閉集合、の 3 つで、**1 投入につき 1 件ずつ**
しか表に出ない。噛み合わせの方は次である。

- `tools/run_tests.py` は負荷に応じて local 実行と計算ノード dispatch を自動で選ぶ。
  単一 file 指定かつ低負荷では local に倒れ、その場合 dispatch 用の受領証表示行を出さない。
- `tools/mutation_harness.py --runner-mode dispatch` は受領証表示行がちょうど 1 本あることを
  要求する。0 本だと `artifact_error: receipt 表示行が exactly one でない: 0` となり、
  `stdout` が空のまま `PARSE_ERROR` で停止する (実測: `rc=0` でも停止する)。
- **正しい回避は `run_tests.py --force-dispatch`** である。親は当初これを
  「強制 dispatch はしない」という混雑時の規律に引きずられて採らず、全走 argv で迂回した。
  その規律は「login node で足りるのに計算ノードへ投げるな」という話であり、
  harness の dispatch mode が受領証行を要求する場面には適用されない。**親の適用範囲の誤りである。**
  全走 argv でも baseline は通るが、1 変異あたり約 8 分かかるうえ node 集合が過剰決定になる
  (`DW-M03`)。単一 file + `--force-dispatch` なら単一理由に絞れて速い。

**工数。** 子は 11 体 (plan 2・consult 4・author 1・fix 3・review 2)。全 `gpt-5.6-sol` / `xhigh` / 受理。
実数は受領証 (`receipt.json`) が正本。実装子と fix 子はいずれも計算ノード dispatch の
preflight 失敗で pytest を 1 件も実走できず、**テストの実走はすべて親が行った** (全走 5 回)。

**ユーザー裁定 (本 wave 終盤、直接発話)。** pin 前進の可否を問うたところ「やれば」と承認された。
同時に「そこに束縛されるのはダサい、効率が悪そうな割にメリット薄そう」という評が付いた。
親は次を返し、「推奨通りで」と合意された。

- 束縛のコストは台帳より小さい。D642 の「golden 50〜60 件」は当時の記述で、直近の実測
  (2026-08-28) は衝突 11 件。pin を参照する 334〜384 file の大半は `output/` の歴史記録と docs で
  そもそも変更してはならないもの。**pin 前進で実際に発火する production の関門は 1 つだけ**
  (`s8b_floor_campaign.py` の C4-4)。D642 が名指しした能動 gate の片方は現在 production に無い。
- **しかし今 pin を進めても得るものが無い。** 本 wave の gate により、mocc は X/P 計装が入るまで
  certified を名乗れない。pin だけ進めても候補集合は空のままである。
- したがって**順序は「mocc 計装 → pin 前進 1 回」**とする。先に進めると儀式を 2 回払う。
  1 回にまとめれば trace-hook・X/P 計装・`I` 面が同時に閉じる。
- 効率を殺しているのは束縛の存在ではなく、前進のたびに人間の再承認を要求する儀式の方である。

## 次の一手差分

### 新規

- {{T:mocc-proof-surface-instrumentation}} **P2・新規**: mocc に lock 被覆と permutation の
  計装を入れる。真実源は RWLOCK と CLL であり silo の Tidword ベース計装は転用できない。
  これが入るまで mocc は certified を名乗れない。
- {{T:write-intent-surface-closure}} **P2・新規**: `I` 面は pinned producer が全 protocol で
  emit しない。閉鎖には gitlink の pin 前進が要る。
- {{T:proof-surface-receipt-evidence}} **P3・新規**: receipt が新旧どちらの証明面で認証されたかを
  判別できない残余。本 wave は VERIFY_DONE への記録に留め、receipt schema と digest domain は
  変えていない。
