# [T-1798] 床値 SWO oracle の依存材料を規則で導出した canonical root へ束縛する

- wave branch: `worktree-dev-wave-t1798-floor-oracle-manifest`
- base main: `9463bcbc`
- 実装 commit: `3e81c730` (canonical material + 二根検査)、`d97e9513` (一括再検査 + 偽緑の解消)

## 何が問題だったか

起票は「production 側で `SHA256SUMS` を生成・配置する経路が存在しない」としていたが、
実測すると真因はより深い。

floor の preflight は依存 root が **VCS の top-level であること**を要求する。したがって
その root には必ず VCS metadata と prebuild 生成物が入る。一方 oracle は root 直下再帰の
**全 regular file 集合が宣言集合と exact 一致すること**を要求する。実測では実 root 196 file に
対し宣言は 101 で、差の 95 件は VCS metadata (26)、`.deps` (26)、`autom4te.cache` (7)、
object file と archive と configure 生成物 (36) だった。

すなわち **実 source root に manifest を置く設計には、成功する入力が存在しない。**
生成器を実 root へ置く案は着手前に死んでいた。

## どう解いたか

実 source root から**規則で**宣言集合を導出した canonical root を作り、oracle にはそれを渡す。

- 宣言集合 = VCS の tracked 一覧 ∪ `config.h` ∪ 生成した `PIN`
- `PIN` は検証済み HEAD と改行から生成する。実 source の `PIN` は読まない
- test fixture を production から参照しない
- pin 比較は既存の `_prepare_verified_dependency` を再利用し、第二実装を作らない

build 境界は canonical root への単純な付け替えではなく**二根検査**にした。
canonical には既存 exact verifier、実 source には canonical との等価検査 (tracked 集合・
宣言 path の bytes・HEAD・`config.h`)、archive には従来どおり独立 hash。

設計判断の正本は decisions の該当エントリ (fold 時に採番)。

## 親が着手前に実測したこと

一次資料は `verbatim/s1-measurements.md`。すべて repo 外で実行した。

| 実測 | 結果 |
|---|---|
| 規則導出集合 = fixture 宣言 101 path | 独立な 2 つの実 root で完全一致 (両方向の差 0 件) |
| 共通 100 path の bytes | 全一致 (mismatch 0 / missing 0) |
| `config.h` の再現性 | 別 base で recipe を完走させても bytes 一致 |
| 生成 manifest | 凍結 fixture と byte-identical、pin と一致 |
| oracle 本体 | `check_materialized_sort_swo` が `OracleStatus.PASS` (compile + execute 実走) |

fetch のみ済みの実 root を複製して
`bootstrap.sh` / `configure --disable-assertions` / `make` / `ar` / `ranlib` を完走させると、
regular 196・symlink 0・tracked 99 になり、親が最初に測った root と同型になった。
そこから規則だけで canonical root を作って oracle を通した。

## 本 wave が束縛しないもの (保証水準の限定)

**因果鎖を閉じたとは主張しない。**

- **archive の生成権威は束縛しない。** recipe は `make` / `ar` / `ranlib` / autotools を継承環境から
  plain な名前で解決し、floor は生成**後**の archive hash を初めて観測してそれ自身を権威にする。
  細工した tool は pin 一致する `config.h` を残したまま悪性 archive を作れる。
  本 wave が作った欠陥ではなく、tool identity の束縛は実行権威の変更として別項目へ送った。
- 宣言外の生成物 (`configure`、`config.h.in`、`GNUmakefile`、object file) は検査していない。
- 同一 uid の別 process が build 中だけ材料を差し替えて戻す経路は閉じていない (既存項目の範囲)。
- 最終 postflight から成果物化までの区間は再確認しない (既存項目の範囲)。

## 受理集合の変化 (二段に分けて述べる)

- **oracle 単体の root 述語の受理集合は不変。** `sort_swo_oracle` の検証器・pin・fixture の bytes を
  1 行 / 1 byte も変えていない。
- **「実 source root から floor が PASS する」合成述語の受理集合は空集合から非空へ拡大する。**
  これが依頼そのものであり、拡大は等価射影に限る。

## 敵対レビューが見つけたもの

段 3 で 15 件、段 6 で 8 件。重いものだけ挙げる。

- **合成 root では pin 一致に原理的に到達できない。** 生成する `PIN` の中身は実 HEAD であり、
  合成 checkout の HEAD が pin 済み commit になることはない。親の段 4 裁定はこの壁を知らずに
  「同一実行で production 全系列を通す試験」を必須にしており、**要求が実装不能だった**。
  実装子と fix 子は VCS probe を monkeypatch で置換して迂回した。裁定を訂正し、合成系列は
  fail-closed の確認に限り、pin 一致から先は実 checkout を要する明示 opt-in が担う形にした。
- **二根検査が全 file を一つの安定状態として再確認していなかった。** 並び順の前半 file を
  読み終えた直後に bytes を一方向へ変えるだけで通る。往復すら要らない。一括再検査を足した。
- **親の疑義 3 件はすべて refuted された。** 共有 fixture の値変更・build 境界からの receipt 再観測の
  削除・`elif` による archive 検査の消失。2 本のレビューが独立に根拠つきで否定した。

## 実測できなかったこと

floor 配線の real-root 系列 node は、親が 5 回試したがすべて計算ノードへ振られ、
`IZANAGI_SORT_SWO_REAL_MASSTREE_ROOT` が dispatch の env allowlist に無いため伝播せず skip した。
**受入全走でも同じ理由で skip される。** 対策は稼働中の別 wave と編集面が重なるため実施せず起票した。

generator から post-oracle build の cache miss / hit までの系列と phase marker は、
親が実走して緑を確認した。

## 変異 matrix

- spec: `mutation-spec.json` (本走で使った最終版)
- 台帳: `mutation-ledger.json` (fix 3 後の最終 commit で、契約どおりの argv で走らせた 2 回目)
- 1 回目の本走 (erratum): `mutation-ledger-prefix3.json`。親が `DW-M07` を読み落として
  `--force-dispatch` と `--wrapper-attempt` を欠いていた。結果は 2 回目と同じである
- probe 巡の初回結果 (erratum): `mutation-probe.json`

期待 node は完全集合でなければならないため、初回は 8 件中 6 件が MISMATCH になった。
観測集合へ登録し直した本走で **baseline PASSED (赤 0)、8/8 KILLED、SURVIVED 0、MISMATCH 0、TIMEOUT 0**。

M08 (VCS 一覧取得の失敗握り潰し) は複数行の構造変更を要して単一理由性を保てないため登録から落とした。
その gate は既存の負例テストが守っている。

変異 baseline では、`output/runs` が新しい作業ツリーに実在しないことに由来する既存の非帰属赤 1 件を
根拠つきで deselect した。

## 逐語

`verbatim/` に段 1〜6 の親資料と子成果物を置いた。親の裁定 2 件 (`s4-adjudication.md`、
`s6-adjudication.md`)、親の監査メモ (`s6-parent-audit.md`)、敵対レビュー 4 本を含む。
