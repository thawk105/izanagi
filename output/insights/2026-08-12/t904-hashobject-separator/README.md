# [T-904] git hash-object の引数区切り欠落 — 是正と敵対検証

- **日付**: 2026-08-12
- **wave**: `dev-wave-t904-hashobject-sep` (branch `worktree-dev-wave-t904-hashobject-sep`)
- **裁定**: 2026-08-12 第 4 束 (authority: user)「[T-904] = バグ是正 + 敵対検証」。
  確定形は「引数区切りの欠落として直す。受理集合が広がるため、正例テスト (先頭 `-` の
  正当ファイル名) + 独立の敵対検証 1 本を受入条件にする」。

## 欠陥

`tools/codex_reasoning_ab.py` の `_git_closure_reasons` は、untracked artifact が git の
object store へ混入していないかを検査するために
`git hash-object --no-filters <path>` を呼んでいた。path を option 位置へ直接置いていたため、
先頭が `-` のファイル名が option と誤認される。

**倒れ方は 2 方向ある。** これは段 3 の敵対レンズ (sol) が親の当初理解を覆して見つけた。

| ファイル名 | 修正前 | 修正後 |
|---|---|---|
| `normal` | 正常に path を hash | **同じ OID** (挙動不変) |
| `-answer` (未知 switch 名) | rc=129 `error: unknown switch 'a'` → `ValidationError` で検査が異常終了 | path を hash |
| `--stdin` (有効 option 名) | **git が stdin を読み、ファイル自身の blob を検査しない (fail-open)** | path を hash |

## 親の実測 (git 2.34.1、使い捨て repo)

```
$ git hash-object --no-filters -answer
error: unknown switch `a'          rc=129
$ git hash-object --no-filters -- -answer
587be6b4c3f93f93c489c0111bba5596147a26cb   rc=0
$ git hash-object --no-filters normal        → 975fbec8256d3e8a3797e7a3611380f27c49f4ac
$ git hash-object --no-filters -- normal     → 975fbec8256d3e8a3797e7a3611380f27c49f4ac
```

## 是正

`tools/codex_reasoning_ab.py:1330` の 1 行のみ。

```python
-object_id = _git(snapshot, "hash-object", "--no-filters", relative).decode().strip()
+object_id = _git(snapshot, "hash-object", "--no-filters", "--", relative).decode().strip()
```

同型欠落の網羅: repo 全体の `hash-object` 呼び出しのうち production は 2 箇所で、
`tools/spool_fold.py:3208` は `--stdin` 形 (path 引数を取らない) のため該当しない。
同ファイル内の他の git 呼び出しは `--` 済みか `<rev>:<path>` 形。単発事故なので
`DW-G03` に従い族一般化 (全 git 呼び出しへの一斉挿入) はしていない。

## production 到達性 (親の当初記述を撤回)

段 3 の敵対レンズ (luna) の指摘により撤回した。production の `untracked` は
`_snapshot_spec` が `f"{ARTIFACT_DIR}/{name}"` を作るため、**artifact 名が `-answer` でも
argv token は `-` で始まらない**。`verify_snapshot` の production caller 6 箇所は
いずれも `spec=` を渡さない。したがって本 wave は今日の certified 選択・レポート・台帳の
値を 1 つも変えない。到達面は `_git_closure_reasons` の直接呼び出しと `spec=` 経路
(いずれも現状 test) だけである。

## テストが受理集合の差を固定するまで (段 6 の BLOCKER)

最初のテストは混入相を `hash-object -w` で作っていた。この blob は unreachable なので
`_one_git_closure_reasons` 内の `git fsck --unreachable` が汎用 reason を先に出し、
**引数区切りの有無に関わらず `reasons` は非空 = 拒否**のままだった。差は診断文字列だけで、
`DW-M03` が「kill に数えない」と定める形である。

混入させる blob を HEAD から到達可能なもの (tracked な `root.txt` と同一 bytes) へ変えた。
fsck は鳴らず reason は専用の 1 件だけになるので、`reasons` を完全一致で検査できる。
これで受理集合そのものの差が固定された。

- `-answer` 相: 引数区切りを外すと、本来受理される snapshot が rc=129 の `ValidationError` で拒否される。
- `--stdin` 相: 引数区切りを外すと、git が空 stdin (harness は `/dev/null` に固定) を hash して
  `reasons == []` となり、**本来拒否される混入 snapshot を受理する** (fail-open)。

## 変異 (2/2 KILLED)

`mutation-spec.json` / `mutation-ledger.json` を同ディレクトリに置く。

| id | 変異 | 結果 | 失敗 node |
|---|---|---|---|
| `t904-drop-separator` | `"--"` を削除 (修正前の形) | KILLED (期待一致) | 新設 2 node |
| `t904-misplace-separator` | `"--"` を `--no-filters` の前へ移動 | KILLED (期待一致) | 新設 2 node |

baseline rc=0。runner は dispatch recipe、scope は新設 2 node。
harness が runner の stdin を `DEVNULL` に固定するため `--stdin` 相は hang しない
(段 6 レビュー A が `tools/mutation_harness.py:1387` を読んで確認)。

## 未閉鎖として残る点

- **`aggregate` / `verify` の replay 経路はテストで検証していない。** 該当統合テストは
  成長比例テストとして恒久保留済みで、全走でも受入全走でも skip される。保留解除は
  ユーザー明示命令のみという裁定に従い opt-in しなかった。通常名の OID が不変である
  ことから回帰の余地は小さいが、「検証済み」とは書かない。
- **leading-dash symlink** (段 3 レンズ A の MAJOR): `Path.is_file()` は regular file を指す
  symlink にも真を返すため、custom `spec=` 経路では snapshot 外の可変 bytes を参照したまま
  pass しうる。塞ぐと通常名を含めて受理集合を狭めるため scope 外と裁定し、ユーザー裁定へ返した
  (worklog の新規項)。

## 逐語

`verbatim/` に段 2 プラン、段 3 敵対 2 レンズ、段 5 実装、段 6 レビュー 2 本、段 6 fix を置く。
段 3 のレンズ A は 1 回目の投入が `web_search` 起因で全損しており (failures 台帳の新規エントリ)、
`verbatim/s3-lens-a.md` は Web 検索を禁じた 2 回目の成果物である。
