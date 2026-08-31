# 段 4 裁定 — [T-2027]/[T-2043] D1192 択 (1)

## 段 2・3 の扱い

`DW-C00` の「裁定後に別 context が段 4 から再開する型は、変更面の骨格が同一なら前 wave の
段 2・3 成果物を流用でき、再検査は段 6 レビューへ寄せる」に従う。変更面の骨格は同一
(同じ 4 production file + 4 test file、同じ D1192 択 (1)、同じ root taxonomy)。
流用元は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2027-t2043-external-input/artifacts/`
の `plan/output.md`、`consult-sol/output.md`、`consult-luna/output.md`。親が全文を読んで
内容を判定したうえで流用する (`DW-O02` の「context 無しの子出力をレビュー結果と数えない」
を満たす)。**再検査は段 6 レビューへ寄せる。**

## real / refuted (前 wave 分の再確認)

- **real (再確認):** 消えた job-local 絶対 path が cache hit と receipt 発行で停止する障害。
  fresh 側で root authority の確定が collector より後だった順序問題。
- **real (再確認・実装に反映済み):** held root fd からの no-follow component 走査が要る
  (`resolve()` 後の `lstat()` では ancestor symlink を見逃す)。validator 側でも root tag の
  canonicality を検査しないと `filesystem` 詐称で snapshot 境界を迂回できる。
  `(root, path)` の順序を固定しないと同じ集合から別 digest を作れる。
  `FETCHCONTENT_BASE_DIR` 配下だが登録 root 外の入力は黙って `filesystem` へ落とさず停止する。
- **refuted (再確認):** 旧 v1 completion の `source_root_sha256` を使う移行案。実 completion に
  その field が無く、suffix と同名 file の hash 一致は root 帰属も D424 の同一 tree も証明しない。
  実装は移行を作らず、schema を cache identity へ pin して v1 と v2 を別 namespace にした。
- **scope 外 real (前 wave の判定を維持):** completion と digest を同時改竄できる主体による
  root retag、および root 検査後の rename/symlink 交換 TOCTOU。いずれも v1 に同型が存在し、
  本 wave の根相対化が新設する受理拡大ではない。本 wave の must-fix にしない。

## 親が独立監査で足した所見 (前 wave の 3 段いずれも未指摘)

| ID | 所見 | 裁定 | 成果物影響 (`DW-G05`) |
|---|---|---|---|
| A | v2 の入力 path が `"."` のとき `_normalized_relative_posix` を通過し、`_hash_relative_nofollow` の `parts[-1]` が **uncaught `IndexError`** を投げる。公開 API から実測で漏れることを確認した。 | **real・must-fix** | 呼び手は `CompilerInputError` しか捕まえないため、receipt 発行器が構造化拒否ではなく異常終了する。拒否の**形**が変わり、campaign が拒否理由を記録できない。v1 は同じ入力を構造化拒否していたので**退行**である。 |
| B | `_masstree_source_root_from_cmake_cache(staging)` の呼出しが `dependency_receipt is not None` から `source_snapshot_sha256 is not None` の全件へ広がった。同関数は解決 key と `masstree_build.dir/DependInfo.cmake` の実在を要求して `BuildCacheError` を投げる。 | **real・must-fix** | external input を admit しない descriptor-bound build では masstree root は不要なのに必須化されている。読めない build が 1 つでもあれば、今の赤が別の無条件赤へ置き換わるだけで床値 receipt は 1 件も出ない。 |
| C | `_strict_root` は `realpath != abspath` の綴りを拒否する。旧経路 `_directory(..., allow_symlink_root=True)` は許して解決していた。実測: `/work/SFC/tanab/izanagi` は拒否される。 | **real・must-fix** | D1192 が要求していない絞り込み。計算ノードの作業領域が symlink 経由で綴られていれば、修理したはずの経路が別の赤で止まる。 |

**採用する修正の向き**

- A: `_normalized_relative_posix` が空 parts (`"."`) を `CompilerInputError` で拒否する。
  受理集合は**縮む方向**であり規律 2 を緩めない。
- B: masstree origin root の取得を `allow_external_compiler_inputs` が真のときだけ行い、
  偽なら `origin/current` を `None` で渡す。external input を admit しない build の受理集合は
  従来どおり「全入力が snapshot 内」のままで、**広がらない**。
- C: `_strict_root` は非正規な綴りを拒否せず `os.path.realpath` で正規化して進む。
  非絶対・空・NUL の拒否と、正規化後の no-follow component 走査は維持する。
  manifest に入るのは根相対 path だけなので、根の綴りは記録にも hash 検査にも影響しない。
  **受理される manifest の集合は 1 bit も広がらない** (広がるのは caller が渡してよい根の綴り)。

## scope 裁定

- **scope 内:** 上記 8 file の実装 + 修正 A/B/C + それぞれの正例・負例テスト。
- **scope 外 (実装しない):** 消える根の第 2 クラス (job 専用作業領域
  `/scr/0_<jobid>.nqsv/…` の 7 件) の根相対化。ユーザー裁定待ち。
- **scope 外 (実装しない):** completion authenticity の独立 authority、fd lifetime の
  全面改訂、mimalloc / googletest の可搬 root 化、v1 completion の救済移行。

## 記録して返す制約

**択 (1) を裁定文どおり実装しても床値の主経路は緑にならない。** 消える根は 2 クラスあり、
本 wave は D1192 が名指しする 1 クラス (31 件) だけを直す。残る 7 件クラスは射程拡大の
ユーザー裁定待ちである。これは本 wave の欠落ではなく、裁定の射程そのものである。

## 変異事前登録 (`DW-M01`、B-057)

前 wave が実走・訂正済みの 6 件を、本 wave の最終 commit へ anchor し直して再登録する
(`DW-M07`: fix 後の最終 commit で anchor 逐語と期待 node を再検証してから本走)。

| ID | 実効 gate | 単一変異 | 単一赤理由 |
|---|---|---|---|
| M1-SCHEMA-PIN-OMITTED | buildcache identity | v2 manifest schema pin を preimage から除く | 旧 v1 entry を選択してしまう |
| M2-FETCH-ROOT-AS-FILESYSTEM | collector 分類 | masstree 入力を filesystem root で保存する | run-local な絶対 root が manifest へ残る |
| M3-CURRENT-BASE-IGNORED | hit validator | recorded/origin root を current root の代わりに使う | base A→B の再束縛が発火しない |
| M7-ROOT-CANONICALITY-SKIPPED | validator 分類 | filesystem tag の snapshot/FetchContent 内着地拒否を外す | tag 詐称で境界を迂回する |
| M8-RECEIPT-RECHECK-OMITTED | issuer | receipt 発行時の current root context を外す | build 後の差替えを receipt が検出しない |
| M10-NON-SORT-CURRENT-ROOT-OMITTED | floor 配線 | non-sort cell へ current root を渡さない | sort_best 以外の receipt が再束縛されない |

**本 wave で追加登録する 1 件**

| ID | 実効 gate | 単一変異 | 単一赤理由 |
|---|---|---|---|
| M11-DOT-PATH-ACCEPTED | v2 path 正規化 | `_normalized_relative_posix` の空 parts 拒否を外す | `"."` が uncaught 例外へ落ちる |

**通る正例として固定するもの (過剰拒否も不合格とする)**

- base A / base B で relative path と hash が一致する v2 の cache hit。
- snapshot 内入力しか持たない descriptor-bound build が、masstree FetchContent の
  解決 key 無しでも manifest を採取できる (修正 B の正例)。
- symlink 経由で綴った snapshot root を渡しても collect / validate が通る (修正 C の正例)。
- snapshot-only な v1 receipt の portable validation。
- system external の同一絶対 path / 同一 hash。

期待 node は完全集合として、段 6 の fix 後 anchor で実測して確定する (`DW-M08`)。

## 段 5 の分割

Codex `role=author` 1 本。編集面は採った 8 file だけ。docs 編集と commit はしない。
