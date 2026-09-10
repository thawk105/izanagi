# 段 1 brief — Pegasus では重い処理を必ず計算ノードで、最大並列で

## ユーザー依頼 (逐語 2 件、確定済み裁定)

1. 「hostnameがpegasusであった場合、ビルドやテストなどマシンに負荷のかかる処理は全て計算ノードで
   行うようにしてください」
2. 「計算ノードで行うんだけど、それは計算ノードのマシンリソースを最大限使って最大限並列でやる
   ようにしてください」

これは `docs/pegasus-runbook.md` §7 の 2026-07-27 ユーザー裁定 (「ビルドとテストはログインノードで
走らせてよい」) の**再反転**である。最新のユーザー直接指示を正とし、runbook §7/§8 と decisions を
同時に置換する。

## scope (実装面)

- **S1 policy 単一正本**: hostname から site を判定する 1 モジュール。区分 = pegasus ログインノード /
  pegasus 計算ノード / その他。割当コア数 (affinity 尊重) と fail-closed メッセージも同モジュール。
  `tools/run_tests.py` と `orchestrator/campaign/buildcache.py` の両方から import でき、hostname 判定を
  二重実装しない。
- **S2 test 経路**: `tools/run_tests.py` は pegasus ログインノードでのテスト実行を fail-closed で
  拒否し、計算ノードへ自動 dispatch する。pegasus 計算ノード内では並列度上限 `_NPROC_CAP` を適用せず
  割当全コアを使う。
- **S3 dispatcher**: 重い argv を gen_S へ qsub し、python 版数 gate (計算ノードの既定 `python3` は
  3.9)・計算ノード network 不可 (pip 導入なし)・`.o`/`.e` 収集・子 rc 伝播・F49(ii) 有効性検査
  ((a) 出力 dir 永続 (b) qstat 可視 (c) 会計痕跡) を持つ。
- **S4 build 並列度**: `buildcache.py` の `jobs` 既定 (16) と coverage 4 モジュールの literal `-j 16` を
  policy 由来の割当全コアへ。実 cmake build を起動する経路は pegasus ログインノードで fail-closed。
- **S5 機械執行**: `hooks/guard_bash.py` に「pegasus ログインノードでの直接重量コマンド (bare pytest /
  cmake --build / make -j / ninja / ctest / 計測バイナリ) 拒否」規則を追加する。sanctioned な
  dispatch 経路 (`tools/run_tests.py`、`tools/pegasus/*`、`qsub`) は通す。新 hook ファイルは作らない。
- **S6 docs (親)**: runbook §7/§8、decisions の新 D、worklog。

## 不変条件

- **非 pegasus 環境の挙動は不変**。hostname が pegasus 系でない環境では現行どおり (テスト cap 32 と
  build `-j 16` を含む)。環境判定は hostname と PBS 環境変数だけに依存させ、他環境へ漏らさない。
- 正しさ規律 1〜6 と既存 gate を緩めない。テストを甘くして緑にしない。受理集合の変更は D96 の
  手続義務 (新しい設計判断の記録 + 境界テストの同時更新) に従う。
- 凍結 bytes・`cache_key()` 入力・env_contract registry・proof chain に触れない。`jobs` が
  `cache_key()` の入力でないことは段 2 で file:line 裏取りする。
- push と remote branch 操作はしない。

## 成果物影響 (DW-G05)

- S2/S5 未実装: 3,900 件級の受入全走が共有ログインノード (96 コア) を掴み続け、他利用者と自分の
  計測への外乱源になる (F3 型)。**受理集合の変化** = 実装後は pegasus ログインノードでのテスト実行が
  新 gate rc で赤になり、受入全走の rc=0 は計算ノード上でしか成立しない。**台帳の変化** =
  `task_run` 記録の実行環境が計算ノードになる。
- S4 未実装: 計算ノードでも build が `-j 16` に留まり「最大限並列」を満たさない。variant build の
  wall-clock だけが変わり、binary bytes・`bin_sha256`・COMMIT 値は変わらない。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 拒否だけでなく自動 dispatch まで作る。拒否のみでは、ログインノード上の作業者に準拠経路が
  無く「全て計算ノードで行う」が達成不能になる。
- **(P2)** 「重い」の線引きは *テスト実行全般* と *実 cmake build*。テスト件数の閾値は作らない
  (恣意的で回避可能)。`--collect-only` 等の非実行形は対象外。
- **(P3)** gate を無効化する escape hatch (env var) は作らない。dispatcher の内側は hostname が
  計算ノードなので自然に通る。
- **(P4)** 「最大限並列」= 割当 affinity コア全数 (gen_S で 48)。`_NPROC_CAP` は pegasus 計算ノードでは
  適用しない。2026-07-19 実測 (-n 32 が -n 96 より速い) に基づく反論があっても、指示どおり全コアを
  既定とし、-n 48 対照との実測差は正直に記録する。
- **(P5)** guard_bash への規則追加は「新 hook の追加」(規律5 と衝突) ではなく既存 hook の規則追加。
- **(P6)** scope 外: env_contract 登録段、floor/oracle driver、CCBench build flag、新 hook ファイル、
  campaign 実測経路の再設計。

## 環境

受入全走と実測は **Pegasus 計算ノード (gen_S)** で行う (今回の依頼の dogfood でもある)。
docs 検査と静的検査はログインノードで行う。

## 分割方針

U1 (S1 policy module) を先行完了 → 所有パス限定 patch を配布 → U2 (S2+S3)・U3 (S4)・U4 (S5) を並列。
docs (S6) は親が担当。
