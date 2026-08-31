# 段 1 brief — [T-2027]/[T-2043] D1192 択 (1)

## scope

- D1192 択 (1) 本体だけを実装する。compiler input manifest に**根の分類 (root tag) と根相対
  path** を持たせ、cache hit と binary admission receipt 発行の時点で**現在の canonical base
  へ束縛し直して hash を再検証する**。
- 対象は D1192 の裁定文が名指しする **build cache の作業用 directory 配下の FetchContent
  masstree source (実測 31 件クラス)** だけ。
- 出発点は branch `worktree-dev-wave-t2027-t2043-external-input` の code / test 8 file。
  内容監査 (規律 6) の結果は下記のとおりで、docs 12 file は採らない。
- 監査で実測確定した欠陥 3 件を Codex author が直す。

## 確定済みユーザー裁定

- 択 (1) 本体だけ実装する。**射程の拡大 (job 専用作業領域 `/scr/0_<jobid>.nqsv/…` の 7 件
  クラス) は混ぜない** — ユーザー裁定待ち。
- 仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外 (`DW-G05`)。
- 実装面は Codex `role=author` が書く (D95)。親は直接編集しない。

## 不変条件

- 規律 2: v1 / v2 いずれの経路でも anomaly 検出時の即 reject を緩めない。受理集合を裁定の
  外へ広げない。
- v1 は read-only の互換形式のまま。migration も cache-miss fallback も作らない。
- 既存の凍結成果物 bytes を変えない。実測: `output/` 配下に compiler input manifest の
  bytes は 0 件 (`grep -rln "s8b-compiler-input" output/` が空) なので `DW-O09` は不成立、
  したがって `DW-O10` も不成立。`DW-O08` は成立し submodule 初期化済み。
- 新しい性能測定はしない。受入は Pegasus 計算ノードへの dispatch 経由の全走 1 回。

## 内容監査 (規律 6) — file 単位の採否

**採る (8 file、実装面):** `orchestrator/campaign/` の `s8b_compiler_input.py`,
`buildcache.py`, `s8b_binary_admission.py`, `s8b_floor_campaign.py` と、
`orchestrator/tests/` の `test_s8b_compiler_input.py`, `test_buildcache_v2.py`,
`test_s8b_binary_admission.py`, `test_s8b_floor_campaign.py`。

**捨てる (12 file、docs):** `docs/spool/` の worklog / failures fragment 5 件と
`output/insights/2026-08-28_t2027-t2043-external-input/` の 7 件。前者のうち fragment -1 は
「recovery land」を主張するが実測では未着地 (main は今も v1) であり、採ると台帳へ虚偽の
着地記録が入る。後者は別 wave の brief・裁定・変異事前登録であって本 wave の裁定ではない。
本 wave は自分の記録を書く。

**すでに main にある (再取得しない):** `aaffa71a6` の
`test_growth_test_holds_contract.py` の anti-hang 予算 (`timeout=120.0`) は main に着地済み。

## 監査で実測確定した欠陥 (must-fix)

- **(A) 受理境界で uncaught IndexError。** v2 の入力 path が `"."` のとき
  `_normalized_relative_posix` を通過し (`PurePosixPath(".").parts == ()`)、
  `_hash_relative_nofollow` の `parts[-1]` が `IndexError` を投げる。実測: 公開 API
  `validate_compiler_input_manifest` から `IndexError: tuple index out of range` が漏れる。
  v1 は同じ入力を `compiler input names the snapshot directory` で構造化拒否していた。
  `CompilerInputError` でない例外は `s8b_binary_admission` と `buildcache` の
  `except CompilerInputError` を素通りし、receipt 発行器が構造化拒否でなく crash になる。
- **(B) masstree root 解決の無条件化。** `_masstree_source_root_from_cmake_cache(staging)`
  の呼出しが `dependency_receipt is not None` から `source_snapshot_sha256 is not None`
  の全件へ広がった。同関数は解決 key と `masstree_build.dir/DependInfo.cmake` の実在を
  要求して `BuildCacheError` を投げるため、masstree FetchContent を解決しない
  descriptor-bound build があれば、今の赤が別の無条件赤に置き換わる。
- **(C) snapshot root の symlink 表記を拒否。** `_strict_root` は
  `realpath != abspath` を拒否する。旧経路は `allow_symlink_root=True` で許して解決して
  いた。実測: `/work/SFC/tanab/izanagi` は `/work/1/SFC/tanab/izanagi` への symlink で
  拒否される。D1192 が要求していない絞り込みなので、実 campaign の snapshot root 表記で
  発火しないことを確かめるか、拒否せず解決する側へ寄せる。

## 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)

- **(P1)** branch の実装は択 (1) の忠実な実装であり、受理集合を裁定の外へ広げていない。
- **(P2)** 欠陥 (B) は実 S8b では発火しない (masstree FetchContent は常に解決できる)。
- **(P3)** cache identity への `compiler_input_manifest_schema` 追加は、D1192 が却下した
  「base の絶対 path を identity へ入れる」案とは別物であり、schema 遷移時 1 回だけの
  cache miss に留まる。run 間の再利用は v2 内で保たれる。
- **(P4)** v1 を read-only 互換として残す設計は、v1 経路の受理集合を 1 bit も変えていない。

## 成果物影響 (`DW-G05`)

放置すると床値 job は binary admission receipt を 1 件も発行できず、床値 cell の certified
選択が 0 件のまま残る。31 件クラスを根相対化すると staging 由来の赤は消える。**7 件クラス
(job 専用作業領域) は残るため主経路はこれだけでは緑にならない** — これは裁定待ちの射程で
あって本 wave の欠落ではない。この事実を段 4 裁定と段 7 記録に明記して返す。

## 分割方針

正しさ防壁 (binary admission の受理境界) に触り受理集合が変わるため**軽量版にしない**。
段 2 plan 1 本、段 3 敵対 2 本、段 5 author 1 本、段 6 review 2 本 + fix、段 6 変異 matrix。

## 実測環境

受入全走は `tools/dev_wave_wait.py acceptance` 経由で計算ノードへ dispatch。build /
benchmark / 床値 job の投入は本 wave では行わない。
