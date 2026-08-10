# [T-201] 択 (a) — freeze receipt 履歴走査の置換と受入下限の測り直し

wave: `dev-wave-suite-floor-recheck` / branch `worktree-dev-wave-suite-floor-recheck`
base main `b0b84837` / 実装 commit `525ccb61`

## 1. 何が律速だったか

`orchestrator/campaign/t080_freeze_migration.py` の `_history_touches_path` は、freeze receipt が
改竄されていないことを確かめるために descendant commit ごとに

```
git diff-tree --root --no-commit-id --name-status -m -r -M -C --find-copies-harder <commit>
```

を撃っていた。`_any_history_touches_path` は descendant を**全件** 8-thread pool へ submit し、
`any()` は戻り値の意味論だけで投入済みの仕事を打ち切らない。したがって

**receipt 検証 1 回の `diff-tree` 発火数 = descendant commit 数**

である。その数は receipt 導入 commit `8bec195d` からの `--ancestry-path` descendant であり、
日を追って線形に増えていた。

| 日付 | HEAD | descendant 数 | `output/` tracked files |
|---|---|---|---|
| 2026-07-24 | 0c03609d | 14 | 1819 |
| **2026-07-31 (D104)** | 4ce3bc83 | **298** | 3489 |
| 2026-08-04 | ffeebd49 | 805 | 4922 |
| **2026-08-09** | ee2da0bf | **1529** | 9435 |

**298 → 1529 = 5.13 倍。** `--find-copies-harder` は未変更ファイルまで copy 元候補として読むため、
単価は tracked bytes に比例して伸びる。**費用の主因は CPU ではなく I/O** である
(HEAD 1 commit で wall 4.2〜7.6 秒に対し user+sys は約 1.0 秒)。

そして全 2183 commit のうち **receipt path を触った commit は導入 commit 1 個だけ**である
(`git log --format=%H -- <RECEIPT_REL>` が 1 行)。現行は毎回 1529 commit を全走査して
「何も見つからない」ことを確認していた。

**D104 決定 (2)「真の律速は本番の履歴走査」は現規模でも成立し、当時より強く効いていた。**

## 2. 何をしたか

argv を `--name-status` から **`--raw`** へ変え、同じ 1 回の呼び出しから destination blob OID を取る。
`--find-copies-harder` を外し、従来の述語 (status ∈ {M,D,R,C,T} かつ対象 path が path 欄に出現) は
そのまま維持したうえで、**destination blob OID が対象の期待 OID と一致し、かつ path が対象自身でない**
entry を exact copy として検出する clause を足す。期待 OID は callsite から `duplicate_oid` として渡す。

受理集合の変化は 1 点だけである。**「対象を未変更のまま、中身を変えた別ファイルへコピーした commit」**
(旧 `-C --find-copies-harder` が拾っていた 50〜99% 類似の copy) を検出しなくなる。exact copy は
新しい OID 検査が従来どおり拒否するため、既存の
`test_state_rename_copy_type_change_and_worktree_loss_are_rejected` は**無改変で緑**である。
この縮小は 2026-08-09 のユーザー裁定による意図的なものである (詳細は `verbatim/s4-amendment.md`)。

## 3. 効果 (同一 allocation・同一ノードの paired 実測)

`critical-path-verdict.json` が一次資料。request `898551.nqsv`。
測定対象は [T-692] が critical path の 96% と実測した 2 node。

| arm | commit | 2 node の所要 |
|---|---|---|
| BEFORE-1 | `bcda1c02` | 1278.49 秒 |
| **AFTER** | `7aa7902a` | **77.01 秒** |
| BEFORE-2 | `bcda1c02` | 1311.57 秒 |

- BEFORE 2 本の相対差 **2.55%** (事前登録閾値 7% 未満 → 判定有効)
- **mean(BEFORE) − AFTER = 1218.02 秒、16.8 倍**
- 判定 `効果あり`。全区間で競合プロセスなし (`interval_competitors` 空)。`source_repo_restored: true`

受入全走 (最終 tip `b57cfcea`、request `898574.nqsv`):
**7845 passed / 20 skipped / 623.29 秒 / rc=0**。
直前の [T-692] 実測は 1247.95 秒 / 7746 passed であり、**件数が 99 件増えて wall は半分**になった。
ただしこれは別ノード・別 commit の比較であり、**因果の一次証拠は上の paired 実測のほう**である
(同一コードでノード間 wall が 1.8 倍開くことが D104 の材料に記録されている)。

## 4. 検出力の担保

- **positive control matrix** (`test_history_touches_path_positive_control_matrix`): 合成 git 履歴で
  M / D / rename の両方向 / symlink・submodule の typechange / 2 親・3 親 merge / root /
  追加のみ / exact copy / 近似コピー / `duplicate_oid` 既定値 / 過剰検出しない正例 /
  集約の error precedence / 空集合 を固定。**`True` を返すケースが 1 件以上あることを
  テスト自身が assert** して恒真化を防ぐ。
- **変異 7 本中 6 本 KILLED、1 本 (M1) は等価変異** (`mutation-ledger.json`)。
  M1 は「argv から `-M` を落とす」で、実 commit で検証すると `-C` だけでも `-M -C` と同じ
  323 件の rename を検出する (git の `-C` は rename 検出を含む)。gate の穴ではない。
  M7「OID 重複 clause を消す」は既存テストと matrix の両方を落とし、exact copy 検出が
  恒真でないことを直接示した。
  **erratum**: M2 / M4 は KILLED だが事前登録より多い node が落ちた (既存テストも検出する
  過剰決定) ため harness は MISMATCH と記録した。

## 5. 却下した候補と、その理由

| 候補 | 速度 | 受理集合 | 裁定 |
|---|---|---|---|
| `diff-tree --stdin` で 1 process に畳む | 節約 1% 未満 | 完全に安全 | **不採用** (D104 決定 3: 効果を示せない機構は land しない) |
| pathspec `-- <path>` 限定 | 300 倍 | 変わる (copy 元を見失う) | 不採用 |
| 逆引き `git log -- <path>` | 速い | 変わる (history simplification、copy 元) | 不採用 |
| `--find-copies-harder` 除去のみ | 250 倍 | exact copy も検出しなくなる | 不採用 (ユーザー裁定で退けた) |
| 走査そのものを消す | — | 縮小 | 不採用 (直前の blob OID 検査とは冗長でない) |

## 6. 段 3 敵対レンズが倒した親の裁定

- **「全史 equivalence を positive control にする」は恒真になる。** 実 repo は receipt を触った
  commit が導入 commit 1 個だけなので、新旧とも全件 False で「一致」してしまう。
  これにより control の中核を全史比較から**合成 matrix** へ移した。
- **本番 entrypoint は `verify_receipt` 1 本ではない。** `s8b_oracle_report.py:209` が WAL の任意の
  `validation_head` で `inspect_receipt_history` を呼ぶ。親 brief の「直接 callsite 1 箇所」は
  正しいが「production entrypoint 1 箇所」は誤りだった。

## 7. 破棄したもの (規律 5)

旧 scope (内訳の帰属推定) 用に段 5 で作った probe 6 ファイル (pytest plugin / cgroup sampler /
解析器 / PBS driver / microbench / 静的棚卸し) は、敵対レビュー 2 本で所見 19 件・NO-GO を受け、
裁定が「argv から 1 token を除く」に確定した後は不要になったため**採用しなかった**。repo に入れていない。
また複製 checkout で BEFORE/AFTER を測る先行 driver は、複製環境で 59 failed / 19 errors を出して
arm 無効となり (request `898290.nqsv`)、critical path 2 node を wave worktree 上で測る形へ作り直した。

## 8. 残る材料 ([T-201] の残余)

択 (b) `output/` tracked bytes 削減は未実施のまま残る。本 wave の実測
(費用は tracked bytes への I/O に比例する) が直接支持する。(c) session 跨ぎ cache と
(d) xdist grouping は不採用裁定のままで、それを覆す新事実は本 wave では得られなかった。
