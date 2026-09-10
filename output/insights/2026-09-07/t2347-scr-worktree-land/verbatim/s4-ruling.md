# 段 4 裁定 — [T-2347] plan v2 と変異事前登録

## 親の実測 (段 4 の裁定根拠。probe: /home/SFC/tanab/.claude/jobs/b550caea/tmp/probe2.sh)

使い捨て repo (git 2.34.1) で 3 点を測った。逐語は同 probe の出力。

1. **`git worktree list --porcelain -z` は存在しない。** `rc=129`、`error: unknown switch 'z'`。
   NUL 区切りで record 境界を一意にする逃げ道はこの機体に無い。
2. **`prunable` は「path 不在」を意味しない。** worktree の directory は実在し `.git` file だけ消した登録も
   `prunable gitdir file points to non-existent location` と報告された (`dotgit-gone`)。
3. **path に改行を含む実在 worktree は `prunable` 行を偽装できる。** path `<D>/live\nprunable fake-marker` の
   実在 worktree は、porcelain 上で
   `worktree <D>/live` / `prunable fake-marker` / `HEAD <sha>` / `detached` という record になった。
   record 単位 parse でも行単位 parse でも、実在登録と prunable 登録を区別できない。

## 所見の裁定

| # | 所見 | 裁定 | 処置 |
|---|---|---|---|
| A1 | 非 `-z` porcelain で実在 worktree を prunable と偽装できる | **real (親が実測で確認)** | 設計変更で消滅 — `prunable` を一切読まない |
| A2 | `split(b"\n\n")` が record 境界を壊す | **real** | 設計変更で消滅 — record 分割をしない (現行の行単位のまま) |
| A3 | 一覧取得が隔離 dir 作成より先で TOCTOU | **real** | 設計変更で消滅 — path 不在の登録も**捨てず**比較対象に残す |
| A4 | locked かつ path 不在は prunable にならず rc=31 のまま | **real** | 設計変更で消滅 — 判定を marker でなく `FileNotFoundError` で行うため locked でも通る |
| A5 | `/scr` と `/tmp` は安定状態では重ならない | refuted (A3 で一般命題は偽) | — |
| A6 | 正規 field 名・branch 名からの marker 誤認 | refuted | — |
| A7 | fold gate 以外の受理集合は不変 | refuted (= 不変を確認) | 不変条件 4 として維持 |
| A8 | 不変条件 3 のテストは恒真化しない | refuted | — |
| A9 | 正例が main/wave だけで第三の実在登録を無視する実装を殺せない | **real** | テストに**第三の実在 worktree** を足す |
| A10 | 非 prunable の fail-closed テストが対象 record 限定でも緑 | **real** | 実 filesystem 上の実在登録を含む一覧で走らせる |
| A11 | 「marker はあるが `worktree ` 行ゼロ」の負例が無い | **real** | 不変条件 3 の負例に採用 |
| A12 | 改行を含む path の正例が無い | **real** | 実測 3 をそのままテストにする |
| A13 | prune spy が `LAND._git` 限定で迂回可能 | **real** | 観測面を registry の**事後状態**にする (spy でなく実体) |
| A14 | 変異 8 本に先行 kill する既存テストは無い | real (帰属成立) | 変異事前登録に反映 |
| A15/A16 | locked exemption、bind mount alias | real・**scope 外** | 実装しない。裁定パッケージ候補として段 7 に記録 |
| B1 | F851 の実状態で案 (a) は rc=31 を除去する | **real** | 主目的として採用 |
| B2 | `land()` まで通す end-to-end の再発検知テストが無い | **real** | ユーザー引数が名指しした負例そのもの。**採用** |
| B3 | `prunable` 除外は「実在するが linkage が壊れた登録」も落とす | **real (親が実測で確認)** | 設計変更で消滅 |
| B4 | F851 の再発検知欄を満たさない | **real** | B2 の end-to-end テストで満たす |
| B5 | a5 の異常終了残骸は共有 repo に残りうる | real・**scope 外** | 実装しない。段 7 に記録 |
| B6 | a5 は `worktree lock` を打たない | refuted (= lock しないことを確認) | — |
| B7 | fold gate 後に同じ登録で赤になる箇所は無い | refuted (= 無いことを確認) | — |
| B8 | git 版差は fail-open でなく rc=31 へ倒れる | refuted | 設計変更で marker 依存自体が消滅 |
| B9 | テストは実機構を通る | refuted | — |
| B10 | 理由 (i) は unlocked/prunable に限る | **real** | 設計変更で限定が外れる (marker 非依存) |
| B11 | 理由 (ii) (clone コスト) は未実測 | **real** | **裁定理由から外す。** 案 (a) の採用理由は (i)(iii) と、本裁定の設計が locked まで閉じることに置く |
| B12 | 理由 (iii) は即時解除の理由としてのみ有効 | real | そのとおり。理由として維持 |
| B13 | 案 (b) は共有 registry 依存そのものを切る | real・**scope 外** | F851 は「(a) または (b)」を許す。(a) を採る |
| B14 | 他 tool の同型箇所は射影外で未検査 | real | scope 外。段 7 に「未検査」と記録する |

## plan v2 — 確定した実装 (段 2 プランを置き換える)

**`prunable` marker を読まない。record 分割もしない。行走査は現行のまま残す。**
変えるのは「解決できなかったときの扱い」だけにする。

`tools/dev_wave_land.py:3449-3471` の `_registered_worktree_paths` を次の意味へ変える。

- `worktree ` 行の走査、`os.fsdecode`、`if not paths:` の空判定は**現行のまま**。
- `Path(...).resolve(strict=True)` が **`FileNotFoundError`** を上げた場合だけ、
  **その登録を捨てず**、解決しない絶対 path として `paths` へ加える。
- それ以外の `OSError` (権限・ELOOP・ENOTDIR など) と `UnicodeError` は**従来どおり `_FoldGateFailure`**。
- `git worktree prune` を足さない。`_paths_overlap_absolute` と `_execute_fold_gate` は変えない。

この設計が段 2 プランより強い理由 — **登録を 1 件も捨てない**ので、
A1 (marker 偽装)・A2 (record 境界)・A3 (TOCTOU)・A4 (locked)・B3 (linkage だけ壊れた登録) が
実装上そもそも発生しない。不変条件 3 も現行の `if not paths:` のまま自動的に保たれる。
受理集合が広がるのは「path が存在しない登録があっても fold gate が赤にならない」ただ 1 点である。

## 確定した不変条件 (段 1 から更新)

1. 実在する登録との重なりは今までどおり `_FoldGateFailure`。**第三の実在 linked worktree でも同じ。**
2. `FileNotFoundError` 以外の解決失敗 (権限、decode 不能) は fail-closed のまま。
3. `worktree ` 行が 1 本も無い一覧は今までどおり `registered worktree list is empty` で赤。
4. fold gate 以外の land の拒否 (dirt / no-touch / ff-only / provenance / lock) は 1 bit も変えない。
5. land は `git worktree prune` を実行しない。呼び出し後も registry に登録が残る。
6. **path 不在の登録も重なり比較の対象に残す。** 捨てない。

## テスト (すべて orchestrator/tests/test_dev_wave_land.py へ。新 file を作らない)

実 repo を fixture 内に作り、本物の `worktree add` と本物の porcelain を通す。合成 stdout だけで閉じない。

- T1 (不変条件 1・A9): main・wave に加え**第三の実在 linked worktree**を登録し、
  隔離 dir をその第三の worktree 配下に置いて `_execute_fold_gate` を呼ぶ →
  `fold gate isolation directory overlaps a registered worktree` の `_FoldGateFailure`。
  「main と wave だけ返す」実装ではこのテストが赤になる。
- T2 (主目的・負例): `/scr` 相当の path 丸ごと不在の登録 (本物の `worktree add` → `rmtree`) がある一覧で
  `_registered_worktree_paths` が**赤にならない**。かつ返り値に (i) 実在登録が解決済みで含まれ、
  (ii) **不在 path も含まれる** (捨てていないことを固定)。
- T3 (B3・実測 2): directory は実在し `.git` file だけ消した登録 (git は prunable と報告する) が
  **解決済みで返る**。marker で除外する実装はここで赤になる。
- T4 (A12・実測 3): path に `\nprunable fake-marker` を含む実在 worktree が**返り値に残る**。
  marker/record parse に依存する実装はここで赤になる。
- T5 (不変条件 2): `FileNotFoundError` 以外 — `PermissionError` と `UnicodeError` の 2 case で
  `registered worktree path cannot be resolved` の `_FoldGateFailure`。実在登録を含む一覧で走らせる。
- T6 (不変条件 3・A11): `worktree ` 行を 1 本も含まない stdout (`prunable ...` だけの入力を含む) で
  `registered worktree list is empty`。
- T7 (不変条件 5・A13): 不在登録を含む registry で呼び出した後、**実際の registry を読み直して**
  同じ登録と admin dir が残っていることを確かめる (spy でなく事後状態を見る)。
- T8 (A3): 不在の登録 path が fold gate の隔離 dir と一致する状況を作り
  (`tempfile.TemporaryDirectory` を差し替えてその path を返させる)、
  **重なりが今までどおり `_FoldGateFailure` になる**。不在 path を捨てる実装はここで赤になる。
- T9 (B2/B4・ユーザー引数の負例): **end-to-end `land()`**。`/scr` 相当の不在登録がある共有 registry で
  `land()` が `landed` を返す (旧 `rc=31 status=fold-gate-failed` が出ない)。
- T10 (ユーザー引数の負例の後半): 同じ end-to-end で、**実在する他 worktree に dirt がある**ときは
  **今までどおり拒否**される。T9 と同じ形の land で dirt だけを足し、期待 rc/status が現行と同じことを固定する。

## 変異事前登録 (実装前・DW-M01)

位置はすべて `tools/dev_wave_land.py` の `_registered_worktree_paths`、ただし M7 だけ `_execute_fold_gate`。

| ID | 変異 | 期待 KILL |
|---|---|---|
| M1 | `except FileNotFoundError` を `except OSError` に広げる | T5 (PermissionError case) |
| M2 | `FileNotFoundError` のとき `paths.append(...)` でなく `continue` して捨てる | T2(ii)、T8 |
| M3 | `resolve(strict=True)` を `resolve(strict=False)` にする | T5 (PermissionError case) |
| M4 | fail-closed の `except` から `UnicodeError` を外す | T5 (UnicodeError case) |
| M5 | 段 2 プランどおり `prunable` marker で record を除外する実装へ戻す | T3、T4 |
| M6 | `if not paths:` の空判定を削除する | T6 |
| M7 | `_execute_fold_gate` の重なり拒否を `if False and any(...)` で無効化する | T1 |
| M8 | 一覧取得の前に `worktree prune --expire now` を足す | T7 |

各変異は赤理由が 1 つに絞れることを実装後に確認する (F820)。絞れなければ登録を落とし、実効 gate へ再照準する。

## scope 外 (実装しない・段 7 に記録するだけ)

A15 (locked exemption の一般化)、A16 (bind mount / inode alias)、B5 (a5 の異常終了残骸の掃除)、
B13 (job 専用 clone = 案 (b))、B14 (他 tool の同型箇所)。いずれも本 wave では実装せず、
`docs/failures.md` の F851 恒久対応欄と worklog の「次の一手」へ所見として残す。
