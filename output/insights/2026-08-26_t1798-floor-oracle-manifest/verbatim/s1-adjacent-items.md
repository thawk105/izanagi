# 隣接する既起票項目 (本 wave の scope 判定に使う)

`docs/worklog.md` の未了一覧から、本 wave の変更面に接する項目だけを抜き出した。
**このうち「ユーザー裁定待ち」のものは本 wave で解決してはならない。** 所見がここへ落ちるなら、
実装したふりにせず「裁定パッケージ候補」として分けて返すこと。

## ユーザー裁定待ち (本 wave では解決しない)

- **[T-1805] P1**: 宣言した述語が実際に**実行される**ことを正式受入が証明できるようにするか。
  現状は文字列としての実体化までで、非到達化・別変数による実効分岐・build 中の source 差し替え
  (A→B→A)・汚染 cache binary を排除できない。**immutable snapshot からの build か
  compiler input manifest が要る**。D863 第 2 条件を文字どおり閉じるならこれが残件である。
  → 本 wave の canonical root は「複製した不変の材料を oracle に見せる」形なので、
  この項目の方向と重なる。**先取りしないこと。** 本 wave は oracle の依存 gate を
  production で成立させるところまでであり、build が実際にその材料を compile したことの
  証明は T-1805 に属する。境界がどこかを所見で明示せよ。
- **[T-1799] P2**: oracle 判定後の材料**再生成**を禁止する。`ThirdParty.cmake` の
  `add_custom_command` が `masstree_build` から起動され、source tree 内で `bootstrap.sh` /
  `configure` / `make` / `ar` を再実行して、oracle が判定した `config.h` と archive を
  作り直しうる。閉じるには依存 tree の書込み禁止か private snapshot build が要り、
  D425 が別審査とした**書込み権威の変更**に当たる。
- **[T-1804] P3**: resume 経路が禁止前の durable manifest を受理し続けてよいか。
  resume は `build_v2` を呼ばず binary/store hash の照合だけで既存 binary を使う。

## 起票済みだがユーザー裁定待ちではない隣接項目

- **[T-1800] P2**: mimalloc と googletest の内容を build 境界へ束縛する。staged mode は
  oracle 前に 3 依存を clean 検査するが、build 前後に再観測するのは masstree だけである。
  ycsb target は mimalloc へ直接 link するため、oracle 後に mimalloc を書き換えても
  masstree 側の検査は通る。
- **[T-1801] P3**: cache hit が返す `configure_argv` を historical execution の記録にするか
  recipe と明示するか。現状は保存済み argv を読まず現在の生成器から再構成する。
- **[T-1802] P3**: 明示共有 base を使う複数 job の間で、oracle 判定後に別 process が
  prebuild を再入する経路を塞ぐ。process 間 lock は書込み権威の変更を伴う。
- **[T-1803] P3**: `test_receipt_memo_real_xdist_order_has_no_worker_payer` を flake 保留から戻す。

## 本 wave が閉じるべきもの

- **[T-1798]**: 床値の SWO oracle が production で PASS できない状態を解く。
  oracle の受理集合を広げずに解くこと (絶対規律 2)。
