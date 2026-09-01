---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t2115-cross-protocol-impl
seq: 1
title: [T-2115] 段 7 cross-protocol の実装残余を protocol 対応にする (コード + docs、branch worktree-dev-wave-t2115-cross-protocol-impl)
---

## 本文

- D1360 が名指しした実装残余 3 点 (genome 空間の登録が silo 1 件、between-run floor の baseline が
  silo 固定、層 3 の floor 照合キーに protocol の軸が無い) と公式成果物への接続を実装した。
  裁定は 2026-08-11 に決着済みで、本 wave は設計択一を作り直していない。詳細は
  `output/insights/2026-09-01_t2115-cross-protocol-impl/README.md`。
- **編集面は起票時の 4 file ではなく production 8 file だった。** `screening_driver` と 3 caller を
  外すと、同一 workload の第 2 protocol floor が置かれた瞬間に既存 silo screening が
  `matches=2` で全部落ちる。段 2・段 3 が独立に同じ結論へ到達した。
- **段 3 検査 A の指摘で設計を 1 点変えた。** 測定を許す protocol を固定リストにすると
  「hook が無いから拒否している」という主張がコードの事実に束縛されず、移植完了後も拒否し続ける
  恒真な検査になる。source を実際に読む判定へ変えた ({{D:floor-admission-bound-to-compiled-source}})。
- **述語は段 5 の初版から 3 つの穴を実測で塞いだ。** いずれも親の probe が再現した —
  コンパイルされない file を 1 つ置くだけの反転、フック呼出しがコメントアウトされていても通る、
  `#if 0` の中に `#if ... #endif` が入れ子だと後半が残る。塞いだ後も正例
  (実 submodule の silo、CMakeLists の SOURCES に載る実フック) は真のままである。
- **棄却した所見:** 段 6 レビュー A の「コメント内の include も受理する」は誤りで、
  3 行すべてコメントなら実測で False だった (正規表現が行頭を要求する)。同レビューが
  「凍結成果物の source SHA pin を新たに破る」とした帰結も棄却した — `known_axes_freeze` の
  live tree 検証は base commit の時点で既に赤 (生成器自身の SHA 不一致で source 一覧に到達しない)、
  参照先 3 file は既に drift 済み、live-bytes 検査群はユーザー裁定で保留中
  (`freeze_verification_hold.HELD = True`、21 件)。**現に緑である gate は 1 つも赤にしていない。**
  ただし「path を key にする pin だけを見た」という方法論の批判は real として受け入れ、
  段 1 brief の誤りとして裁定文書に訂正を残した。
- **親の brief の誤りを 3 件訂正した。** 編集面の数、凍結影響の根拠の狭さ、並行 wave との
  衝突を「重なりうる」と推測で書いたこと (段 3 検査 B が実測し、tracked 差分は無かった)。
  「mocc の live 軸 3 本」も用語として不正確で、正しくは「現行 CMake から直交操作できる軸が 3 本」。
- **子はテストを 1 件も実走できなかった** (`rc=16 / child_started=false`、dispatch は `EACCTAUTH`)。
  create-only test の fixture が書き込み先と違う directory を使っており機構を一度も通っていない、
  という欠陥は親の初回実測でだけ出た (F242 の再発として記録)。
- **セッション異常:** 共有 `/tmp` に空の `.git` が置き去られており、pytest の一時ディレクトリが
  repository 内と誤判定されて `test_screening_driver.py` の 8 件が赤になっていた。
  この計算機で走る全 wave を同時に赤にしていた。`rmdir` で撤去し全緑を実測した
  ({{F:stray-git-dir-in-shared-tmp}})。本 wave の差分には帰属しない。
- **エージェント工数:** codex 子 9 本 (plan 1、段 3 相談 2、実装 1、段 6 レビュー 2、fix 2、
  焦点再レビュー 1)。model は全段 `gpt-5.6-sol`、effort は docs 権威由来で `xhigh`。
  段 6 の fix は 2 巡で収束した (`DW-O16` の上限 3 巡以内)。
- **変異 matrix:** 事前登録 4 件すべて KILLED、baseline PASSED、
  spec `c970b9ba8d64813551807ff2b910978b9b1304542de91f3157a8635cf23e5f8c`、
  対象 HEAD `0567282e7911668d6f43d9fffaff1ee46191ec99`。probe を全件 SURVIVED 期待で先に回し、
  観測 node を完全集合として登録してから本走した (`DW-M07` / `DW-M08`)。
- **測定していないこと:** mocc の floor も較正も実測していない。実測は人間の qsub 手番である
  (D87/D86(3))。`space_for()` に production caller は無く、mocc の登録は探索空間の宣言であって
  certified な mocc campaign を成立させるものではない。

## 次の一手差分

### 完了

- [T-2115] D1360 が名指しした実装残余 3 点と公式成果物への接続を実装した。mocc の genome 空間
  (現行 CMake から直交操作できる 3 ブール、YCSB で 8 通り) を登録し、between-run floor の baseline を
  protocol から引くようにし、層 3 の floor 照合キーへ protocol の軸を足した。silo の baseline・
  出力 stem・既存 4 件の floor JSON の bytes は変えていない。tictoc/cicada の登録は D1360 の
  初手 mocc に従って行わず、下記の新規項目へ分けた。
  remaining: none
  base: d7585f8e057f2a2d11423699b27e264adb13ed808be47796740d07e92fed746d

### 新規

- {{T:cross-protocol-tictoc-cicada-space}} **P2・新規**: tictoc / cicada の genome 空間を
  `SPACES` へ登録する。現行 CMake から直交操作できる軸を protocol ごとに導出し、
  bare define と計測撹乱ノブを除外した理由を `notes` へ書く。cicada は真の多版 MVCC で
  既存 playbook が通用しないため、軸の導出自体が調査を伴う。これを終えるまで
  `docs/phase3.md` 段 6 dormant (b) は閉じない。
- {{T:within-run-floor-protocol-provenance}} **P2・新規**: within-run 較正の producer
  (`orchestrator/calibrator/`) へ protocol を記録させ、層 3 を certified calibration
  (`output/env/*/calibration/registered/`) へ接続する。現状の producer は binary の path を
  手渡しで受け genome を記録せず、層 3 は calibration directory 直下しか走査しない。
  この 2 つが残る限り、非 silo の within-run floor は根拠付きで公式成果物へ入らない。
- {{T:screening-floor-match-records-threads}} **P3・新規**: screening の between-run floor 照合に
  records と threads を加え、層 3 の 4 field 照合と揃える。現状は workload だけで絞るため、
  同一 protocol・同一 workload で別の動作点の floor が 1 件あると誤った CV を採る。
  本 wave が作った欠陥ではなく、protocol 軸の追加でも悪化しない。
