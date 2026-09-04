# [T-2226] inert (stock) 比較を「差を取ってから置き場所由来かを判定する」形へ直した

wave: `dev-wave-t2226-inert-root-diff` / branch `worktree-dev-wave-t2226-inert-root-diff`
裁定: D1523 (ユーザー裁定済み)。設計の確定形はこの wave の decisions エントリ。
実装 commit: `4ad505f2ce823fee6b728f97f9686eca9c690c12`

## 何が問題だったか

A-2 の inert (stock) 比較は、patch 済みの木と素の木を前処理して **bytes が一致すること**を
緑の条件にしていた。ところが

- `capture_define_inputs` は 2 つの木が**別 path にあること**を要求し、
- CCBench の `include/debug.hh` が `__FILE__` を使う `ERR` を定義し、
  owner TU (`cc/silo/transaction.cc`) がそれを実際に展開する

ため、前処理出力には必ず 2 つの異なる絶対 path が現れる。`preprocess-root-dependent-builtin` は
**構造的に常時発火**し、A-2 の inert cell はどうやっても緑にならなかった。常に赤の検査は
情報を 1 bit も持たない。

## どう直したか

D1523 に従い、**畳んでから比べる形は採らず**、差を取ってから分類する形にした。

1. 前処理 bytes をそのまま比べる。完全一致なら従来どおりの緑 (理由コードも判定経路も不変)。
2. 一致しなければ行に割り、対応行を 1 対 1 で突き合わせる。片側が足りない対は残差。
3. 差のある行だけ、requested 側の `<requested root>/<相対 path>` を `<control root>/` へ写す。
   写してよいのは (a) 直前の byte が path 文字でない、(b) root の直後が `/`、
   (c) 相対 path を字句正規化した結果が requested の依存閉包に実在する、の 3 条件をすべて満たす位置だけ。
4. 写した後に 1 byte でも残差があれば `stock-inert-mismatch` で赤。行数差・root に改行を含む・
   置換 0 件・code-owned な `__FILE__` 不在もすべて赤。
5. 置き場所由来だけのときに限り、新しい理由コードで緑にする。

control 側と出力全体には一切触れない。build root は置換対象に含めない。

## この wave で確定した事実 (実測)

`g++-12 -E -P` を repo の外で直接叩いて確かめた 2 点が、設計の分かれ目を決めた。

- **`__FILE__` は相対 include 経由だと正規化されない。**
  `#include "../../include/backoff.hh"` から入った header の `__FILE__` は
  `<root>/cc/silo/../../include/backoff.hh` と出る。したがって相対 path の `..` を禁止できない。
- **`__FILE__` は「その語を含む file」ではなく「その語が展開された file」の path になる。**
  CCBench では `ERR` の定義が `include/debug.hh`、展開が `cc/silo/transaction.cc` なので、
  出力に出るのは transaction.cc の path である。root 依存 builtin を持つ file の一覧
  (`root_dependent_builtin_paths`) へ置換先を縛る設計は、実物では成立しない。

## 4 本の独立検査が収束した 1 点と、その裁定

段 3 の 2 本 (計画への検査) と段 6 の 2 本 (実装への検査) が、独立に同じ指摘へ到達した。

> 閉包に同じ名前の file があることは証明しても、**その出力 span が `__FILE__` の展開であることは
> 証明していない**。閉包内の path と同じ bytes を持つ普通の文字列リテラルでも置換が起きる。

**指摘は real と裁定した。影響の主張は成立しないと判断し、fix は採らなかった。**

- 判定が保証するのは「差のある行が root 文字列の差し替えだけで control 行と byte 完全一致する」
  ことである。検査が通す差は、requested 側が `<自分の root>/X`、control 側が `<相手の root>/X` で
  **X が同一**の形に限られる。X が違えば残差が出て赤になる。
- source に実行時の一時 directory の絶対 path は書き込めない。出力へ絶対 root が入る経路は
  compiler の `__FILE__` と build system による source dir の埋め込みだけで、どちらも置き場所由来である。
- 反例を本物の意味差にするには**素の木 (stock 側) にも対応するリテラルが要る**。
  patch を書ける側からは作れない。素の木を書き換えられる相手は本関門の防御対象ではない。

**却下した対案の理由は費用ではない。** 段 6 の検査は `-fmacro-prefix-map` で compiler に root を
正規化させ、追加でもう 1 回 preprocess して byte 完全一致を要求する案を推奨した。精度としては
明確に上だが、**生成の時点で畳む形であり、D1523 が却下した「比較の前に情報を捨てる」形そのもの**
である。inert arm ごとに preprocess が 1 回増え、compiler 未対応時の fail-closed 枝を発火させる
実在の成果物も名指しできない。裁定パッケージ候補として残した。

採った fix は 1 件だけ — 置換位置の**左 token 境界**の要求。実際の展開は必ず引用符の直後に来るので、
実運用の緑を 1 件も落とさずに受理集合を狭められる。

## 明記する限界

本関門は「差が置き場所だけで説明できる」ことを、requested 側の差分行に対する root 置換で
control 行と byte 完全一致することによって判定する。
**置換した span が compiler の `__FILE__` / `__BASE_FILE__` 展開であったことは証明していない。**
依存閉包にある file を指す絶対 path が build system の埋め込み等で出力に現れた場合も同じ扱いになる。
両側で相対 path が同一の差だけを通すため、通す差は置き場所を揃えれば消える差に限られるが、
生成元までは束縛していない。

## 裁定で反転した親の判断

- **build root を置換対象から外した** (brief の当初方針は含める側だった)。
  発火条件を満たす実在の成果物 path も計測 ID も名指しできないため。外す方が受理集合が狭い。
  副次効果として「置換対応が競合したときの順序」という未検査分岐が消えた。
- **差分アルゴリズムを線形の対応行比較へ置き換えた。** 段 2 の計画は `difflib.SequenceMatcher` を
  使う形で、実 CCBench 規模 (数十万行) では最悪二乗になる。行数一致を先に要求して 1 対 1 で
  突き合わせれば同じ判定が線形で得られ、行数差は残差として赤になるので判定は弱まらない。

## 訂正した親 brief の前提

| 記述 | 実際 |
|---|---|
| 前処理出力に行番号の目印が残る | 誤り。実装は `-E -P` を使う |
| A-2 の inert arm は 1 本 | **6 本** (2 workload x stock 2 arm + adopted 1 arm) |
| 理由コードを exact 一致で読む consumer は 3 件 | 7 箇所 4 file。ただし挙動が変わる既存テストは 0 件 |

正例を 2 macro (`BACKOFF_FIXED=-1` / `BACKOFF_NOINLINE=0`) で回す形にしたのは 2 行目の訂正による。

## 変異

実装前に 6 件を事前登録し、段 6 の fix に合わせて 1 件足して 7 件にした。

**probe を全件 SURVIVED 期待で先に回し、観測した落ち先をそのまま本走の期待に固定した。**
予測を書いて後から辻褄を合わせていない。台帳は `mutation-probe-ledger.json` (probe) と
`mutation-ledger.json` (本走)。

| # | 変異 | 落ちたテスト数 | 単一理由 |
|---|---|---|---|
| n01 | 置換許可の閉包束縛を外す | 1 | その条件専用の負例 |
| n02 | 残差判定を無効化する | 3 | 残差は 3 負例に共通する下流 |
| n03 | root 依存 builtin 非空の要求を両層で外す | 1 | その条件専用の負例 |
| n04 | 置換で control root でなく requested root を書く | 4 | 正例 2 + 負例 2 |
| n05 | bytes 完全一致の枝を分類経路へ回す | 4 | **既存**の緑 4 件 |
| n06 | 記録した root 対と configure argv の束縛検査を外す | 1 | その条件専用の負例 |
| n07 | 置換位置の左 token 境界検査を外す | 1 | その条件専用の負例 |

本走 **7/7 KILLED**、SURVIVED 0、MISMATCH 0。

- **n03 は二層同時変異である。** 同じ「root 依存 builtin が非空であること」の要求が判定器と
  記録検査の両方にあり、片層だけ外すともう一方が代わりに赤を出す。冗長 gate に守られたまま
  kill と数えないため、両層を同時に外して登録した。
- **n01 の負例は「閉包束縛の拒否が残差を生む」という単一の因果鎖で赤になる。** 段 6 の検査は
  「membership と residual の 2 条件がそれぞれ green を作るので非単一」と指摘したが、
  この 2 つは独立した 2 層ではなく上流と下流である。冗長 gate ではない。
- **登録しなかった候補と理由:** 「置換回数 > 0 の要求を削除」は、元 bytes 不一致なら置換 0 で
  必ず残差が出るため残差判定と冗長で単一理由が立たない。「行数一致の要求を削除」は
  `zip_longest` で残差へ畳んだので独立した述語が存在しない。「build root 対応の削除」は
  build root 対応を実装しないので変異対象がない。

## 検査していない面

- 置換した span の生成元 (上記「明記する限界」)。
- build root 由来の差。実装は残差として赤にするが、発火する入力を作れないため負例もない。
  将来 build tree の生成 header が `__FILE__` を展開すれば、本来同じ inert 個体が赤のまま残る。
  そのときは赤として観測される。
- sandbox backend の probe は新しい理由コードを受け取っても条件関門を通せない。
  **現状も通っていないので後退ではない**が、この変更では前進もしない。ユーザー裁定へ返した。

## 実走した検査

すべて計算ノード (`gen_S`)。measured checkout は `4ad505f2c` (変異) と、
main 取り込み後の記録 tip (受入全走)。

| 走行 | 結果 |
|---|---|
| `test_condition_meaning_gate.py` (fix 前) | 94 passed |
| 新設 6 case を node 名で個別確認 (fix 前) | 6 passed |
| consumer test 10 file (fix 前) | 692 passed |
| `test_condition_meaning_gate.py` (fix 後・main 取り込み後) | 95 passed |
| consumer test 10 file (fix 後・main 取り込み後) | 692 passed |
| 変異 probe (7 件、全件 SURVIVED 期待) | 7 MISMATCH = 全件が赤を出した |
| 変異 本走 (7 件) | **7/7 KILLED** |
| 受入全走 | 別記 (worklog) |

## 計算資源の観測 (この wave の外にも効く事実)

- dispatch が `queue-wait-timeout` で 2 度落ちた。D612 の上書き
  (`IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=5400`) で通った。
  **変異 harness 経由でも 5400 秒設定なら通った** (probe 9 分、本走 12 分で完走)。
- **取り消し時に orphan hold が 2 か所へ作られる。**
  `output/pegasus-dispatch/orphan-holds/<request>.json` と `output/pegasus-dispatch/orphan-hold.json`。
  下位だけ消して上位を残すと、次の投入が `orphan-hold` で**起動そのものを拒否**する。
  どちらも消す前に qstat での不在確認、tracked 0 件の確認、HEAD と作業ツリーの確認を行った。
- 段 5 と段 6 の実装子はどちらも投入が通らずテストを 1 件も実走できなかった。
  両者とも「実装済み・未実走」と正直に申告し、緑と書かなかった。親が全部実走した。

## 凍結前の機械走査

- placeholder gate: `python3 tools/check_docs.py` → 違反なし。
- 三軸 conjunction: 権威実装 `orchestrator/campaign/s8b_holdout_freeze.search_repository` の
  `files` 注入 API へ、本 wave が凍結する 17 file を渡して走査した。
  **rr80 / rr20 とも conjunction hit 0 件。**
  検査器の生存は正例対照で確かめた — 三軸すべてに当たる既存 file 5 件を同じ呼びへ混ぜたところ
  `positive_control.hit_count = 5` になり、走査が実際に発火することを確認している
  (混ぜない走では正例対照も 0 になり、生存を示せない)。
- defang は不要だった。

## 逐語

`verbatim/` に段 1 から段 6 までの子の出力と親の裁定を凍結した。
