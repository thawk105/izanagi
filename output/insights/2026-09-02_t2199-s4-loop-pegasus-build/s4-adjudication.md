# 段 4 裁定 — T-2199 段 4 loop のビルド系を Pegasus で通す

親が段 2 プランと段 3 の 2 レンズを real / refuted に裁定し、plan v2 を確定する。

## C1 — 実行場所: Pegasus を継続する (段 2 の cygnus 推奨は不採用)

段 2 は「cygnus (`linux-baremetal`) の方が安い」と推奨した。**不採用**とする。根拠は 3 つ。

1. 段 2 の費用比較は、cygnus 側に**過去の成功 4 iteration** を、Pegasus 側に**目的の異なる 6 投入**を
   置いた比較であり、現在の限界費用の比較ではない。段 2 自身が「現在の cygnus 到達性は未確認」と
   書いている。沈んだ費用を将来費用として読んでいる (レンズ B 所見 11 が同じ指摘)。
2. 親の実測: この session の `~/.ssh/config` に cygnus の entry は無い。到達手段を今から作る費用は
   計上されていない。**「cygnus では不可能」とは言わない** — 費用の項が欠けていると言う。
3. ユーザーの確定方針は「cygnus は使えるが使わない。新規 evidence は Pegasus」である
   (worklog 2026-08-05 の裁定)。これを覆すには実測の根拠が要り、1 と 2 によりその根拠は無い。
   レンズ A も「Pegasus 選択は支持される」と独立に判定した。

## C2 — 本 wave では実装しない (段 5・6 を飛ばし 4→7→8→9)

**目的 (Pegasus 計算ノードで段 4 loop を build へ到達させる) は、許可された編集面では到達不能である。**
親が現物のコードで確認した。

- `p3_s4_loop.py:1428-1433` は `authorization_contract=env_contract.authorize(ENV_TAG)` を渡す。
  `ENV_TAG` は同 file 111 行で `"linux-baremetal"` に固定されている。
- `loop.py:_authorize_measurement` が `execution_guard.require_certified_writer_authorization()` を
  build より前に呼ぶ。
- `execution_guard.py:136-159` は、site が Pegasus compute のとき
  「activation state 内で `attestation_mode == "required"` の契約がちょうど 1 つで、
  提示された契約がそれと同一」であることを要求する。`linux-baremetal` の attestation_mode は
  `"none"` なので、この条件で拒否される。**build へ到達しない。**
- 直すには `p3_s4_loop.py` の 111-113 / 1019-1021 / 1347-1349 / 1428-1433 / 1965-1968 を
  site-aware にする必要がある。**編集面の外であり、稼働中の t2145 wave の所有である。**

編集面の内側に残る唯一の前進策 (job-private な CMake wrapper を PATH 先頭に置き、
`FETCHCONTENT_SOURCE_DIR_*` を configure 時だけ注入する) も**採らない**。レンズ A 所見 1 が real:
condition gate は wrapper を CMake 実体として実行するのに、gate の記録は
**CMake の path も wrapper の hash も実効 configure argv も保存しない**。
`condition_meaning_gate.py` を 1 byte も変えなくても、これは実質的な受理集合の変更である
(絶対規律 2)。束縛を足すには gate 側の変更が要り、それも編集面の外である。
**したがって安全な部分実装が存在しない。**

## C3 — brief (P1) を訂正する: 「登録済み」は正しく、「4 前提が充足済み」は誤り

`env_contract.py:248-311` に `pegasus` g1 / g2 が実在し、g1 が current activation である
(g2 は登録済みだが未 active。**この 2 つを混同しない**)。ここまでは親の (P1) が正しい。

しかしレンズ A が反証したとおり、D59 の 4 条件のうち条件 3 (計測ごとの単独性・静定確認) は
**実行のたびに再成立させる義務**であり、条件 4 (対象 job の toolchain・pin・script の追跡) は
**この job について未実装**である。「登録簿に entry がある」から「4 前提が充足済み」を導けない。
引数と T-2182 の「4 前提が未了」は、登録の層では反証されるが、**対象 job の層では正しかった**。

## C4 — brief (P2) は不採用: 「job script 側だけで解ける」は受理集合に中立でない

`config.h` の問題そのものは job script 側で解けるが、解き方 (PATH wrapper) が C2 の理由で採れない。
gate の判定は PATH・ambient `CMAKE_PREFIX_PATH`・compiler launcher・生成された compile command に
依存する。**code file を変えないことは、受理集合を変えないことと同じではない。**

## C5 — brief (P4) を撤回する

(P4) は「env_tag ラベルと物理環境の不一致は block 理由にしない」と書いた。**これは誤りである。**
現行の guard は不一致を意図的に block しており、その目的は Pegasus の値が `linux-baremetal` の
系列へ混入するのを防ぐことである (レンズ A・B が独立に反証)。

**「ラベルの不一致で作業を止めない」という一般則と、本件は別である。** ここで止めているのは
ラベルではなく、現に効いている防壁であり、迂回すれば測定記録が壊れる。防壁は守る。

## C6 — preprocess 失敗の診断: config.h 不在で確度を上げた (literal stderr は未取得)

段 2 の仮説 (確信度 0.85) を、親が**前 wave の残存 artifact**で裏取りした。

- `external/ccbench/cmake/ThirdParty.cmake:57-78` — `config.h` と archive は
  `add_custom_command` / `add_custom_target(masstree_build)` の**ビルド時**生成物である。
  configure は `FetchContent_Populate` で source を置くだけ。
- `external/ccbench/include/masstree_wrapper.hh:20` — `#include <config.h>` を無条件で行う。
  owner TU `cc/silo/transaction.cc` は `common.hh:12` 経由でこれに到達する。
- **T-2182 の投入 6 が残した configure 木**
  `/work/1/SFC/tanab/izanagi-exploration-t2182/configure-probe3` を親が実見した。
  `FETCHCONTENT_SOURCE_DIR_MASSTREE` は**空**、`FETCHCONTENT_FULLY_DISCONNECTED=OFF`、
  `_deps/masstree-src` は clean clone として populate されており (`configure.ac`・`bootstrap.sh` あり)、
  **`config.h` はこの木のどこにも存在しない。**
- condition gate は configure 直後に owner TU を preprocess する。`masstree_build` を建てない。

**言えること:** gate が preprocess する木には、owner TU の include 閉包が要求する `config.h` が
実在しない。**言えないこと:** これが観測された `preprocess-failed` の literal な原因であること。
前 wave は stderr を保存していない。レンズ B が数えたとおり、同じ reason code へ落ちる条件は
7 つある。**確度は上がったが確定ではない。** 記録にはこの区別を残す。

## C7 — 引き継ぎ: site-aware 配線の先例が repo 内にある

`p3_s4_loop_trigger_gating.py` は**既に site-aware である**。
`_admit_env_contract()` (442-455 行) が site を契約へ写像し (未知 site は fail-closed)、
`_campaign_cfg_for_site()` が identity へ束縛し、815 行が
`authorization_contract=env_contract.authorize(contract.env_tag)` を渡す。
**p3 を所有する wave は、この兄弟 file の形をそのまま `p3_s4_loop.py` へ写せばよい。**
新設ではなく移植である。

## C8 — 変異事前登録

本 wave の実装面 (D95 決定 2) の差分は**ゼロ**である。記録は docs / insights / spool fragment のみ。
`DW-S04` により変異 matrix を免除する。**受入全走は免除しない。**

## scope 外の real 所見 (裁定パッケージとしてユーザーへ返す)

- レンズ A 所見 2: wrapper が trace 有効化と strip を同時注入できると、`nm -C` による
  `izanagi_trace` symbol 検査 (`buildcache.py:3445` が strip 済み binary は素通りと明記) を
  抜ける経路がある。**本 wave は wrapper を採らないので発火しないが、将来 PATH wrapper を
  導入する設計は絶対規律 1 の穴を開けうる。**
- レンズ A 所見 3: `p3_s4_loop` の CLI は build 後に `outcome=aborted` でも一般検査が通れば rc=0 を
  返し、condition gate の canonical record を保存しない。**terminal verdict の証拠が
  成果物に残らない。** 編集面の外 (p3 所有)。
- レンズ A 所見 5: p3 経路の単独性確認は canary 付き probe ではなく plain `pgrep` である。
  D59 条件 3 の充足度に関わる。編集面の外。
- レンズ B 所見 3・4・5: 計算ノードでの `python3 -> python3.10` PATH shim、raw qsub の
  `-o` / `-e` の repo 外転送、README の tagged qsub command 同期。**将来 job script を作る wave の
  必須項目**として引き継ぐ。

## plan v2

1. 実装しない。段 5・6 を飛ばす。
2. 段 7 で記録する: worklog / decisions / failures の fragment、insight 1 本 (逐語 3 本を同梱)。
3. 段 7 の記録 commit 後に受入全走を計算ノードへ投入する。
4. 段 8・段 9 を通常どおり行う。
