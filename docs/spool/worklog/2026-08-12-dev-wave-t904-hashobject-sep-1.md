---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t904-hashobject-sep
seq: 1
title: git hash-object の引数区切り欠落を是正し受理集合の差で固定する (コード + テスト、branch worktree-dev-wave-t904-hashobject-sep)
---

## 本文

第 4 束の裁定「[T-904] = バグ是正 + 敵対検証」を執行した。確定形どおり引数区切りの欠落として
直し、正例テストと独立の敵対検証を受入条件にした。

**欠陥は一方向ではなく双方向だった。** 段 3 の敵対レンズ (sol) が、ファイル名が `--stdin` の
ような**有効 option 名**の場合、git が stdin を読んでファイル自身の blob を検査しないことを
指摘した。つまり本欠陥は「正当な名前を拒否する」だけでなく **fail-open にも倒れる**。
`--` の挿入は両方を塞ぐ。親の当初 brief はこれを「一方向の受理集合拡大」と書いており誤りだった。

**production 到達性についての親の記述も誤りで、撤回した。** 段 3 の敵対レンズ (luna) が、
production の untracked は必ず `<ARTIFACT_DIR>/<name>` 形なので、artifact 名が `-answer` でも
argv token は `-` で始まらないと指摘した。したがって「将来 artifact 名で到達する」は成立しない。
到達面は `_git_closure_reasons` の直接呼び出しと `spec=` 経路 (いずれも現状 test) だけである。
本 wave は今日の certified 選択・レポート・台帳の値を 1 つも変えない。

**段 6 のレビューが最初のテストを BLOCKER として潰した。** 混入相が `hash-object -w` で
dangling blob を作っていたため、`git fsck --unreachable` が汎用 reason を先に出し、
引数区切りの有無に関わらず `reasons` は非空 = 拒否のままだった。差は診断文字列だけで、
`DW-M03` が kill に数えないと定める形である。混入 blob を HEAD から到達可能なもの
(tracked な `root.txt` と同一 bytes) へ変え、reason を完全一致で検査する形に直した。
これで「引数区切りを外すと `--stdin` 相が `reasons == []` になり本来拒否すべき混入を受理する」
という**受理集合そのものの差**が固定された。

段 3 のレンズ B が挙げた「fixture が重い」は親の実測で否定した (該当 node は call 0.16 秒)。
新 fixture は発明せず既存 helper を使った。

**未閉鎖として残る点を正直に記録する。** `aggregate` / `verify` の replay 統合テストは
成長比例テストとして恒久保留済みで、`test_codex_reasoning_ab.py` 全体走でも受入全走でも
skip される。保留解除はユーザー明示命令のみという裁定に従い opt-in しなかったため、
この経路は**テストで検証していない**。通常名の OID が `--` の有無で同一である
(親実測: `975fbec8256d3e8a3797e7a3611380f27c49f4ac`) ことから回帰の余地は小さいが、
「検証済み」とは書かない。

段 3 のレンズ (sol) が挙げた leading-dash symlink の所見は real だが scope 外と裁定し、
{{T:leading-dash-symlink-spec-gate}} としてユーザー裁定へ返す。塞ぐと通常名を含めて
受理集合を**狭める**ため、規律 2 の「緩めない」と対称の「勝手に強めない」に当たり、
[T-903] で強化 3 案を全て見送った先例と同型である。

wave 運営では codex 子 1 本を丸ごと失った ({{F:codex-web-search-invalidates-evidence}})。

## 次の一手差分

### 完了

- [T-904] 引数区切りの欠落を是正し、受理集合の差を固定する二相テスト 2 本と
  変異 2 件 (2/2 KILLED) で裏取りした。
  remaining: none
  base: 623c62b762aa4702a8c3201c933a61a69eb6289ad4cb472b3d8c95e976fc7036

### 新規

- {{T:leading-dash-symlink-spec-gate}} **P3・ユーザー裁定待ち**: `_git_closure_reasons` の
  `Path.is_file()` は regular file を指す symlink にも真を返すため、custom `spec=` 経路では
  先頭 `-` の symlink が snapshot 外の可変 bytes を参照したまま pass しうる。
  塞ぐ形 (正規化・非 symlink 要求・snapshot 内包の明示検証) は通常名を含めて受理集合を
  狭めるので、[T-903] と同じ「勝手に強めない」の対象として裁定を仰ぐ。
  現行 built-in spec からは到達しない。
