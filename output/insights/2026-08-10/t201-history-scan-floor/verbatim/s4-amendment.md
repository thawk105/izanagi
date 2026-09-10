# 段 4 v2 裁定の補正 (2026-08-09、実測とユーザー裁定による)

## 発端 — 親の実測が裁定の前提を覆した

段 5 単位 A の変更 (`--find-copies-harder` 除去) を入れて `test_t080_freeze_migration.py` を
計算ノードで実走したところ、**既存テスト 1 件が落ちた** (1 failed / 41 passed)。

```
test_state_rename_copy_type_change_and_worktree_loss_are_rejected
AssertionError: copy
assert 'invalid' == 'issued-but-missing'
```

このテスト (`orchestrator/tests/test_t080_freeze_migration.py:807-830`) は
**「receipt を未変更のまま、同一 bytes の `copy.json` を追加した commit」が拒否されること**を
既に pin していた。段 4 の期待表ケース 12 と同じものであり、**既存の受理集合に明示的な pin が
あった**ことになる。段 4 裁定はこれを見落としていた。

さらにコードを追うと、`inspect_receipt_history` の "invalid" / "issued-but-missing" は
どちらも終端の refusal だが、**受理判定は別関数の `state = "active-valid" if not refusals else ...`
(`t080_freeze_migration.py:2024`) で行われる**。整合的な repo では、除去だけを行うと
copy 改竄は refusal を 1 つも生まないため **`active-valid` = 受理**へ倒れる。
すなわち「検出が狭まり、受理が広がる」。段 4 で親が使った「受理集合が狭まる」という表現は誤りであり、
**ゲートが弱くなる方向**である。

## 親の追加実測 (同一 20 commit、ログインノード)

| 形 | 20 commit | 1529 commit への外挿 |
|---|---|---|
| 現行 (`--find-copies-harder`) | 45.31 秒 | 3470 秒 (8-thread で約 434 秒) |
| 除去のみ (`--name-status`) | 0.180 秒 | 約 14 秒 |
| **`--raw` (OID 付き)** | **0.075 秒** | **約 6 秒** |

`--raw` は `--name-status` と同じ 1 回の git 呼び出しで **destination blob OID まで返す**。
すなわち **exact copy の検出を、除去案より速い形で取り戻せる**。

## ユーザー裁定 (2026-08-09、本セッションで直接)

**「OID 重複検査を足す」を採用。** すなわち:

- `_history_touches_path` の git 呼び出しを `--name-status` から **`--raw`** へ変え、
  `--find-copies-harder` は除いたままにする。
- 従来の述語 (status ∈ {M,D,R,C,T} かつ対象 path が path 欄に出現) は**そのまま維持**する。
- **加えて**、追加/変更エントリの destination blob OID が **対象 path の期待 blob OID と一致し、
  かつその path が対象 path 自身でない**場合を検出する (= exact copy)。
- 結果として **既存テストは書き換えず緑のまま**になる。
  検出が消えるのは「中身を変えたうえでのコピー (`-C --find-copies-harder` が拾っていた
  50〜99% 類似の copy)」だけに縮む。

## 段 5 fix の指示 (単位 A2 / B2)

### 単位 A2 — production (`orchestrator/campaign/t080_freeze_migration.py` の 1 枚だけ)

1. `_history_touches_path` の argv を
   `diff-tree --root --no-commit-id --raw -m -r -M -C <commit>` にする
   (`--name-status` → `--raw`、`--find-copies-harder` は入れない)。
2. `--raw` の行形式を**正確に**解析する。メタ部は空白区切りで
   `:<srcmode> <dstmode> <srcsha> <dstsha> <status>`、その後に TAB 区切りの path が 1〜2 個続く。
   **既存の `fields[0][:1]` を status とみなす解析は `--raw` では誤りである** (先頭が `:`)。
3. 従来の述語を維持する: status の 1 文字目が {M,D,R,C,T} で、対象 path が path 欄のいずれかに一致。
4. **新しい clause を足す**: 引数 `duplicate_oid: Optional[str] = None` を追加し、非 None のとき、
   destination blob OID が `duplicate_oid` と一致し、かつその entry の path が対象 path でない
   entry があれば `True` を返す。全 0 の OID (`0000...`) は destination 不在なので除外する。
5. `_any_history_touches_path` にも `duplicate_oid` を通す引数を足し、
   callsite (`t080_freeze_migration.py:1753` 付近) から `expected_oid` を渡す。
   **既定値は None** とし、既存の呼び出し形が壊れないようにする。
6. docstring を更新する。「検出しなくなったのは中身を変えたうえでのコピー (50〜99% 類似) だけ」
   であること、2026-08-09 のユーザー裁定であること、上の実測値を書く。

**変えないもの**: 集約規則 (True が error に勝つ、error は sorted commit 順の最初)、
thread pool の並列度、`-M -C` の有無、`-m` `--root` `-r`、既存の状態名と refusal 文字列。

### 単位 B2 — positive control (`orchestrator/tests/test_t080_freeze_migration.py` の 1 枚だけ)

段 4 の期待表を次のとおり改める。**既存テストの期待値は 1 つも変えない。**

| # | ケース | 期待 |
|---|---|---|
| 12 | 対象を未変更のまま**同一 bytes** の別ファイルを追加 (exact copy) | **`True`** (裁定変更により復帰) |
| 12b | 対象を未変更のまま**中身を変えた**別ファイルを追加 (近似コピー) | **`False`** ← 本裁定で変わる唯一のケース |

ケース 12b のコメントに「ここが `True` へ戻ったら 2026-08-09 裁定の逆行である」と明記する。
他の 15 ケースは段 4 の表のまま。非 vacuous 自己検査も維持する。

## 変異事前登録の改訂

| ID | 変異 | 単一理由で落ちるテスト |
|---|---|---|
| M1 | argv から `-M` を落とす | rename (source / destination) |
| M2 | argv から `-m` を落とす | 2 親 / 3 親 merge |
| M3 | argv から `--root` を落とす | root commit |
| M4 | 述語の status 集合へ `"A"` を足す | 対象を追加しただけの commit = False |
| M5 | `path in fields` を `path == fields[0]` にする | rename source |
| M6 | error より True を優先する規則を反転 | `{false, error}` / `{error,false,true}` |
| M7 | **OID 重複 clause を消す** | **ケース 12 (exact copy)** と既存の `test_state_..._rejected` |
| M8 | OID 重複 clause から「path が対象自身でない」条件を消す | 通常の receipt 更新が誤検出される正例 |
