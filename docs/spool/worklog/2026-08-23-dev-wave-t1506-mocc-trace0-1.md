---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-t1506-mocc-trace0
seq: 1
title: [T-1506] mocc の TRACE=0 前処理同一性検査を通し、計測を塞いでいた 3 箇所を解いた (コード+テスト、branch worktree-dev-wave-t1506-mocc-trace0、変異matrix = baseline PASSED・11/11 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- D673 は「trace ヘッダの include 行に旧版コメントが残る限り TRACE=0 の性能計測は一度も
  走らない」と述べていた。**主張は正しかったが必要条件であって十分条件ではなかった。**
  塞いでいた箇所は 3 つあり、そのうち 1 つは本 wave 自身が作った。詳細と実測値は
  `output/insights/2026-08-23_t1506-mocc-trace0-unblock.md` が一次資料である。
- 起点の前提が食い違っていた。台帳は「`external/ccbench` に適用済みのパッチ」と書いていたが、
  submodule の gitlink は 511c9538 のままで、ユーザーの commit `ef9328a3` は object store に
  存在するだけで checkout されていなかった。**submodule の「適用済み」は gitlink と
  object store の両方を測らないと編集面の地図が外れる。**
- 段 2 直後の probe で「1 行を直しても checker は別の gate で拒否し続ける」ことが判明し、
  gate の受理形を増やす改訂が scope へ入った。`DW-O13` が段 2 の期限後に成立したため、
  契約どおり**段 2 から巻き戻した** (brief v3、段 2 再走、段 3 再走)。旧 plan と旧 review は
  結論として流用せず、逐語根拠と実測だけを事実として引き継いだ。
- 設計判断は {{D:mocc-trace0-checker-wiring}} と {{D:mocc-trace0-gitlink-not-fatal}}。
  失敗は {{F:gate-hardening-blocked-the-measurement-path}} と
  {{F:ruling-premise-is-necessary-not-sufficient}}。
- ccbench への commit は D673 の裁定に基づき AI が行った。内容は前 wave
  (`dev-wave-t755-q2-mocc-trace`) の段 6 が確定させた逐語である。新 commit
  `058d0c4e5f237d88ec1c2ebe0739113d82906e47` はユーザーの `ef9328a3` を直接の親に持ち、
  511c9538 を祖先に持つ。**gitlink は前進させていない** (`CCBENCH_FULL_SHA` の再承認と
  再凍結を避けるため)。上流への PR・push は行っていない。
- wave の worktree と primary checkout は submodule の object store が別実体である。
  新 commit が primary から見えないままだと land 後に policy が解決不能な OID を指すため、
  bundle を作って primary の store へ取り込み、両 store に create-only の named ref
  (`refs/izanagi/ccbench/t1506/mocc-trace-include`) を置いた。移送前は primary で
  ref も object も不在であることを実測し、移送後に OID・親・祖先・差分を primary 側で
  再検証した。手順と値は job dir の `transfer-receipt.md`。
- 段 3 の敵対相談 2 レンズが real 所見を 2 件出し、両方採用した。作業 checkout で取った
  不在証明を比較対象 2 commit へ流用するのは不健全である点と、全 path へ無条件に
  `source_rel` を渡すと未登録 `.cpp` の既存正例を壊す点である。
- 段 6 の敵対レビュー 2 レンズが独立に同じ blocker を指摘した。計測 job の topology で
  checker が必ず落ちる件で、親が同じ形を再現して実測で確認した (fix 前 rc=1 / fix 後 rc=0)。
  焦点再レビューは blocker と must-fix をすべて「閉じた」と判定した。
- 変異 matrix は probe 回で M6 が SURVIVED した。注入実在を確認したうえで他層 (new 側) による
  mask と判定し、`DW-M02` / `DW-M04` に従って**両層同時変異**へ再照準した。最終回は
  11 変異すべて KILLED、SURVIVED 0、MISMATCH 0。probe 回の台帳は erratum として保全した。
- **TRACE=0 の性能値はまだ 1 件も無い。** 本 wave が解いたのは「検査が拒否する」ことであって、
  計測そのものではない。計測 script は投入前に未追跡ファイルゼロを要求し、計算ノード側は
  job 開始時にも HEAD が投入時と一致することを要求し、かつ job 自身が repo 内へ未追跡
  ディレクトリを作る。この 3 つが「記録 commit → 受入 → land」の途中での投入と両立しないため、
  **投入は land 後に行い、結果の記録は次タスクへ渡す。**
- 既存 TRACE=1 evidence は `ef9328a3` を source とする過去の pilot であり、TRACE=0 は
  `058d0c4e` を source とする。差はコメント 1 行の位置だけで前処理出力は同一だが、
  **「同じ source で正しさと性能を揃えた」とは書けない。** 規律 1 の逐語要件は source commit の
  同一を求めていないため規律 1 違反ではない。
- checker の report は 16 文脈で比較したことを記録するが、実効 define map は 4 種、
  正規化 digest は 2 種である。**「16 個の異なる macro 構成を検証した」とは書かない。**
- 段 3 と段 6 のレンズが挙げた、本 wave が広げても狭めてもいない**既存の穴 3 件**を
  ユーザー裁定へ返す。(1) 不在証明の解析が CMake の間接展開と行継続を追わない。
  (2) checker が include を展開前に除去するため `#define H "a.hh"` 経由の header 差し替えを
  false-green にしうる。(3) report が活性 hash 不一致と `identical: true` を同時に立てうる。
  いずれも今回の差分は該当しないが、mocc の TRACE=0 値が生まれる以上 依存範囲は増える。
  裏付けとして、511c9538 の tree で `MQLOCK` は 31 行すべて `#ifdef` / `#endif` / コメントであり、
  `#define` も CMake 供給も無く、初期化済み `third_party/shirakami` にも該当 file は 0 件と実測した。
- 本 wave は commit tree 走査を足したため checker 1 回あたり `git show` の起動が 488 回増える
  (tree あたり 244 supply file x 2 commit)。genome ループの外なので文脈数には比例しない。

## 次の一手差分

### 完了

- [T-1506] mocc の trace include 行を前 wave 確定形へ直して commit し、checker の配線漏れ
  2 箇所と gitlink の過剰拒否も解いた。実 checker は通常経路・計測 job topology とも rc=0。
  TRACE=0 の計測投入と結果の記録は {{T:mocc-trace0-measurement}} が引き取る。
  remaining: none
  base: a31b400714bceea753da5ccc174ec8f185ca703681cfd96f4badd548da0a5dfd

### 新規

- {{T:mocc-trace0-measurement}} **P1・新規**:
  land 済みの `058d0c4e` を source として TRACE=0 の性能計測を実施し、receipt と
  throughput を記録する。投入は HEAD が凍った checkout から
  `bash tools/pegasus/submit_mocc_trace.sh --trace-mode 0` で行う。
  **投入前に未追跡ファイルがゼロであること、投入後は job 終端まで HEAD を動かさないこと、
  job が repo 内へ作る `output/env/pegasus/mocc-trace/{attempts,job-staging}` を証拠として
  repo 外へ退避してから tree を clean へ戻すこと**が要件である (いずれも本 wave で実測)。
  結果は pilot-only であり `official_certification: false` / `eligible_for_refreeze: false` の
  ため certified 選択結果は変わらない。既存 TRACE=1 evidence とは source commit が異なるので
  same-source pairing とは書かない。
- {{T:dev-wave-docs-budget-review}} **P2・新規・ユーザー裁定待ち**:
  `docs/dev-wave/**` の 3 層予算が満杯で、本 wave の段 8 が routing しようとした 5 件の
  手順知見が**どれも 1 文も入らなかった** (実測: L1 が 10882 > 10625 bytes、
  L1.5 が 9732 > 9566 bytes、`DW-C01` と `DW-O13` の単節が 1111 > 1000 bytes)。
  自己改善契約は「予算値を上げる変更は通常の自己改善に含めず、理由付きの独立審査対象にする」と
  定めるため、本 wave は予算を上げず memory へ routing した (5 件)。
  memory は `docs/dev-wave/**` と違い子エージェントへ射影されないため、
  **子の作法に関わる知見は実質的に親だけの記憶になる**という劣化がある。
  裁定してほしいこと = (a) 予算を上げるか、(b) 既存節を圧縮して枠を作るか、
  (c) memory 経由の routing を正式な逃がし先として認めるか。
- {{T:trace0-checker-known-holes}} **P2・新規・ユーザー裁定待ち**:
  TRACE=0 前処理同一性検査に残る既存の穴 3 件を裁定する。(1) 不在証明の解析が
  `set(VAR MACRO)` + `${VAR}` の間接供給と行継続 `#define` を追わない。
  (2) checker が include を展開前に除去するため、`#define H "a.hh"` を変えて不変な
  `#include H` を残す差分を false-green にしうる。(3) report が `old_active` / `new_active` を
  別々に hash 化しながら `identical: true` を固定するため、hash 不一致と identical が
  同時に立つ証拠が出うる。いずれも本 wave 以前から存在し、本 wave は広げても狭めてもいない。
  段 3 と段 6 の敵対レンズが独立に real と判定した。
