# 段 6 裁定 — レビュー 2 本の所見と fix 2 巡目の指示

入力 = レビュー A (`s6-review-a2.md`、二根検査の等価性)、レビュー B (`s6-review-b2.md`、偽緑の暴露)。
対象 = HEAD `3e81c730`。

## 0. 親の疑義 3 件はすべて refuted

両レビューが独立に同じ結論へ達し、根拠も一致した。親の見立ては誤りだった。

- **A1 (共有 fixture の値変更)**: refuted。新しい値は `fake_sort_swo_pass_attempt()` の
  `dependency_config_sha256` と同一で、新設した oracle receipt と source binding の一致検査を
  通すための整合化である。偶然一致で mismatch 検査が消えたテストは無い。
  旧契約が literal `"b" * 64` を要求する 3 箇所は明示的な `dataclasses.replace` で保存されており
  一貫している。
- **A2 (receipt 再観測の削除)**: refuted。旧 `_observe_fetchcontent_dependency_receipt` の三条件
  (canonical non-symlink directory / VCS top-level 一致 / HEAD の一意取得) は
  `_canonical_source_root` と `_probe_git_source` にすべて包含されている。
  旧経路は `buildcache.py:2379` になお残るが、post-oracle fresh build では新経路が先に走るため
  判定は積集合であり fail-open ではない。
- **A3 (`elif` で archive 検査が飛ぶ)**: refuted。`build_v2` は `buildcache.py:2116` で
  `fetchcontent_archive_sha256` と `post_oracle_binding["archive_sha256"]` を先に比較して
  不一致を拒否する。`elif` へ到達する前に閉じている。

## 1. 親自身の裁定の訂正 — 段 4 差分 1 の要求は実装不能だった

段 4 で親は「同一実行で production 全系列 (canonical 生成 → oracle PASS → post-oracle capability
付き `build_v2` の cache miss → cache hit) を通す試験を 1 本必須にする」と裁定した。
**合成 root ではこれは原理的に不可能である。**

理由: `materialize_canonical_dependency` は必ず `_prepare_verified_dependency` を通り
`DEPENDENCY_MANIFEST_SHA256` をハード照合する。生成される `PIN` の中身は実 source の HEAD である。
合成 checkout の HEAD が masstree の実 commit `b3c5d054b66b08374d7a6ff5a0faeaf28b041a38` になることは
なく、したがって manifest は必ず pin と食い違う。pin 一致まで到達できるのは、その commit を実際に
持つ checkout だけである。

実装子と fix 子はこの壁に当たり、`_probe_git_source` を monkeypatch で固定値へ置換して迂回した。
迂回は誤りだが、**要求の側にも無理があった**。親は要求を次のとおり訂正する。

- **合成系列**: `_probe_git_source` の monkeypatch を外し、実 Git checkout (commit object と index を
  持つ) を使う。floor 配線と canonical 生成を production 実装で通し、
  **pin 不一致で `canonical-manifest-mismatch` に fail-closed することを assert する。**
  これが合成 root における正しい振る舞いである。
- **実系列**: opt-in real-root node を oracle PASS と post-oracle `build_v2` の miss/hit まで延長する。
  **親がこの node を 1 回実走し、結果を worklog へ書く。**

## 2. 所見の裁定

### レビュー A

| # | 判定 | 採否 | scope |
|---|---|---|---|
| 1 全 file 読取後に bytes 全体状態を再確認しない | **real** | **採用 (must-fix)** | scope 内 |
| 2 最終 postflight 後の窓と canonical 参照の消失 | real | 不採用 | scope 外 (T-1802 / T-1805) |

### レビュー B

| # | 判定 | 採否 | scope |
|---|---|---|---|
| 1 系列が 3 変異すべてで緑のまま | **real** | **採用 (must-fix)** | scope 内 |
| 2 floor の prebuild → canonical 接続が production 実装で試されない | **real** | **採用 (must-fix)** | scope 内 |
| 3 合成 root が Git 前提を満たさず monkeypatch で迂回 | **real** | **採用 (must-fix)** | scope 内 |
| 4 実 root opt-in が generator 止まりで build 未証明 | **real** | **採用 (must-fix)** | scope 内 |
| 5 manifest 変異テストが production generator を変異させていない | real (nit) | **採用** | scope 内 |
| 6 phase marker の canonical 参照が assert されていない | real (nit) | **採用** | scope 内 |

## 3. fix 2 巡目でやること

### F1 (レビュー A 所見 1): 全 file 読取後の一括再検査

`assert_source_matches_canonical` は各 source file を読取時 identity 付きで読むが、
全 file を読み終えた後に**それらが一つの安定状態だったこと**を確認しない。
sorted 順の前半 file を読み終えた直後に bytes を一方向へ変えても、最終 probe は
root / HEAD / tracked path 集合しか見ないので成功する。

- 各 source file の読取時 identity を保持し、**全 file の読取後に path と identity を一括再検査する。**
- 最終 probe の後に不一致があれば `canonical-source-drift` で拒否する。
- この修正が実際に効くことを検査する負例テストを足す (前半 file を読取後に変更する形)。

### F2 (レビュー B 所見 3): 合成系列から monkeypatch を外す

`test_buildcache_v2.py` の production 系列テストで、
`monkeypatch.setattr(sort_swo_dependency_material, "_probe_git_source", ...)` を**削除する**。
`git init` して `.git/HEAD` に hash を書くだけの飾りも削除する。

代わりに**実 Git checkout** を作る。tracked file を index へ入れて commit し、
`git rev-parse --verify HEAD` が実在 commit を返し `git ls-files --cached -z` が非空を返す状態にする。
`expected_head` にはその実 HEAD を渡す。

その結果 `materialize_canonical_dependency` は `canonical-manifest-mismatch` で失敗する。
**これが正しい振る舞いであり、それを assert する。** 生成 manifest hash と期待 pin の両方が
診断に載ることも確かめる。

### F3 (レビュー B 所見 1・2): floor 接続を production 実装で通す正例

`_prepare_floor_oracle_dependency` から production の canonical adapter と material sink までを
**置換せずに**通す正例を足す。prebuild 自体は合成してよい。

この正例は、次の変異でそれぞれ赤にならなければならない。
- `_materialize_floor_oracle_dependency` を binding の素通しにする
- `_prepare_floor_oracle_dependency` から canonical 生成の呼出しを除く
- oracle へ `oracle_root` でなく `source_root` を渡す
- post-oracle capability から canonical root を落とす

### F4 (レビュー B 所見 4): opt-in real-root node を build まで延長

`IZANAGI_SORT_SWO_REAL_MASSTREE_ROOT` で受け取る node を、generator で終わらせず
**oracle PASS と post-oracle `build_v2` の cache miss / cache hit まで**延長する。
未設定なら skip でよい。**親がこの node を 1 回実走する。**

### F5 (レビュー B 所見 5、nit): 変異テストを production generator へ照準

`test_manifest_mutations_have_one_exact_verifier_reason` は fixture の `SHA256SUMS` を直接編集して
既存 oracle verifier を呼ぶだけなので、`sort_swo_dependency_material` を丸ごと no-op にしても緑になる。
変異を **production generator の宣言集合・区切り・並び順**へ照準し直す。

### F6 (レビュー B 所見 6、nit): phase marker の canonical 参照を assert

`_write_phase_marker` へ足した `oracle_dependency_root` と `dependency_manifest_sha256` を
marker テストで assert する。今は削除しても緑である。

## 4. fix 子への制約 (段 5 実装子契約を全文継承)

- **既存テストの期待値を変更しない。** 反転・緩和・skip 化・削除・`xfail` 化を禁じる。
  赤なら実装側が誤り。期待値が誤りと判断したら実装を変えず報告して止める。
- **production の検査を monkeypatch で置換して通すことを禁じる。** これが今回の主因である。
  やむを得ず置換するなら、置換によって一度も実行されない production コードを報告に列挙する。
- 編集禁止 9 件 (段 5・fix 1 巡目と同一) を守る。
- **commit しない。`git add` もしない。** docs を書かない。push しない。Web 検索しない。
- 緑には実走 nodeid を併記する。実走できないものは「実装済み・未実走」と書く。

## 5. 変異の再照準 (DW-M01 / DW-M07)

段 4 で登録した M01〜M08 のうち、実装を読んで次のとおり具体化する。probe 巡で単一理由性を
確認してから本走する。

| ID | 位置 | 変異 |
|---|---|---|
| M01 | `materialize_canonical_dependency` | `payloads["PIN"] = ...` を削除 |
| M02 | manifest 行の組み立て | 区切りの空白 2 個を 1 個へ |
| M03 | manifest の並び順 | `sorted(payloads)` を逆順へ (書き込みループと同表現なので文脈で一意化) |
| M04 | `assert_source_matches_canonical` | 実 source bytes 照合ループを無効化 |
| M05 | `_POST_ORACLE_DEPENDENCY_BINDING_KEYS` | `oracle_dependency_root` を落とす |
| M06 | cache hit 経路 | 返却前の二根検査を省く |
| M07 | floor 配線 | oracle へ `source_root` を渡す |
| M08 | `_run_git` | 失敗を握り潰して空一覧で続行 |

F1 の修正後は **M09 (一括再検査の無効化)** を追加登録する。

段 4 の M01 は「実在集合と宣言集合の不一致で `dependency-file-set-mismatch`」を期待したが、
実装を読むと `PIN` を生成しなければ実在も宣言も無く集合は一致するため、
`canonical-manifest-mismatch` になる見込みである。probe 巡で実測して登録を訂正する。
