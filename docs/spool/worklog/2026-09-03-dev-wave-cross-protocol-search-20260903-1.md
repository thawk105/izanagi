---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-03
wave: dev-wave-cross-protocol-search-20260903
seq: 1
title: 証明面を持たない protocol が certified を名乗れないようにした — クロスプロトコルの手前に正しさの非対称があった (コード + テスト、branch worktree-dev-wave-cross-protocol-search-20260903、未 land・受入 2 赤)
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

**未了。** 受入全走は 2 赤で終わっている。`test_ccbench_spawn_sites.py` の 2 件で、fix が入れた
`silo_ladder_rung1.py` の `_pinned_patched_source_model` が新しい process 起動点を 2 つ作り、
審査済み spawn site 目録に未登録なため弾かれている。**防壁が正しく発火している形**であり、
目録へ登録すれば閉じる。**変異 matrix (M01〜M03) は未実施、land も未実施。**

**工数。** 子は 8 体 (plan 2・consult 4・author 1・fix 2)。全 `gpt-5.6-sol` / `xhigh` / 受理。
実数は受領証 (`receipt.json`) が正本。実装子と fix 子はいずれも計算ノード dispatch が
`qstat -Q` 失敗の rc=16 となり pytest を 1 件も実走できず、**テストの実走はすべて親が行った**。

## 次の一手差分

### 新規

- {{T:proof-surface-spawn-site-registry}} **P1・新規**: `silo_ladder_rung1._pinned_patched_source_model`
  が作る 2 つの process 起動点を審査済み spawn site 目録へ登録し、受入全走を緑にする。
  これを閉じないと本 wave の実装は land できない。branch は
  `worktree-dev-wave-cross-protocol-search-20260903`、対象は
  `orchestrator/tests/test_ccbench_spawn_sites.py` の 2 件。
- {{T:proof-surface-mutation-matrix}} **P1・新規**: 本 wave の実装に対する変異 matrix を走らせる。
  事前登録済みの 3 件 = M01 (証明面の連言を無条件 true にする)、M02 (`P` の matcher を
  silo の実 site を認識しない token へ置換する過剰拒否の正例)、M03 (到達不能・非活性 block 内の
  token を証拠ありと数える false-positive)。
- {{T:mocc-proof-surface-instrumentation}} **P2・新規**: mocc に lock 被覆と permutation の
  計装を入れる。真実源は RWLOCK と CLL であり silo の Tidword ベース計装は転用できない。
  これが入るまで mocc は certified を名乗れない。
- {{T:write-intent-surface-closure}} **P2・新規**: `I` 面は pinned producer が全 protocol で
  emit しない。閉鎖には gitlink の pin 前進が要る。
- {{T:proof-surface-receipt-evidence}} **P3・新規**: receipt が新旧どちらの証明面で認証されたかを
  判別できない残余。本 wave は VERIFY_DONE への記録に留め、receipt schema と digest domain は
  変えていない。
