---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-07
wave: dev-wave-acceptance-speedup-20260905
seq: 1
---

## {{D:git-index-output-snapshot}}. 実 repo `output/` の内容 snapshot は git 索引を同一性の出所にする

**決定:** `orchestrator/tests/` が実 repo の `output/` を「変えていないこと」を確かめるための
内容 snapshot を、**全 file を毎回 open して sha256 する形から、git の索引を同一性の出所にする形へ
変える。** 返り値のタプル (entry 集合・順序・sha256 の値) は 1 bit も変えない。

実装は `orchestrator/tests/output_snapshot_ignores.py` の
`git_indexed_output_snapshot()` に置き、`test_s8b_floor_campaign.py` の
`_real_output_snapshot` から使う。手順は次の 4 段である。

1. `git ls-files -s -v -z` で追跡 file の index blob sha と index flag を得る (stat 不要)
2. `git status --porcelain=v1 -uall -z` で作業ツリーと index の差分集合を得る
3. clean な追跡 file は **`(index blob sha, repo 相対 path)` をキーに sha256 を
   プロセス内キャッシュ**して再利用する。dirty / 未追跡は従来どおり実体を読む
4. 空 directory と symlink は従来どおり walk から取る (git は空 dir を追跡しない)

**次のいずれかが成立するときは高速路を使わず、従来の全 file 読取へフォールバックする。**
索引と設定だけで判定し、作業ツリーは読まない。

- 対象が git work tree の外にある
- `git ls-files -v` の flag に小文字 (assume-unchanged) または `S` (skip-worktree) がある
- 対象部分木に追跡された `.gitattributes` がある
- `core.autocrlf` が変換を有効化する
- repository 直下の `.gitattributes` が変換を有効化する記述
  (`text` (先頭 `-` 無し)・`eol=`・`ident`・`working-tree-encoding=`・`filter=`) を持つ

**理由:**

- 現行実装は実 repo の追跡 18,126 file (478.7 MB) を毎回すべて開いて sha256 を取る。
  この呼び出しは `test_s8b_floor_campaign.py` の 10 test (parametrize 展開後 11〜12 nodeid) が
  各 2 回、計 **22 回**行う。ログインノード実測で 1 回 cold 90.85 秒 / warm 10〜13 秒。
- **費用を占めるのは内容のハッシュではなく Lustre への stat (18,126 回、約 9 秒/回) である。**
  digest だけを `(path, size, mtime, ino, dev)` でキャッシュしても 15% しか減らない (実測)。
- この作りは repo の成長に比例して伸びる (D335 が禁じる型)。実際、対象 12 nodeid の
  合計所要は直近の走行で 1,403〜2,499 秒 (1 本平均 117〜208 秒) の幅で動いている。
- git の索引は同じ判定を stat なしで返せる。ログインノード実測で
  `ls-files -s` 0.013 秒、`status --porcelain` 2.1 秒、`ls-files -v` 0.032 秒。
  実 `output/` に対し独立参照オラクルとの**返り値完全一致 (19,686 entry)** を確認した。
  定常 3.84 秒 (参照オラクル 12.25 秒)。

**却下した選択肢:**

- **チェック回数を減らす (per-test を per-module へ集約)** — 22 回を 2 回にでき最も効くが、
  「test A が汚し test B が戻す」経路を検出できなくなる。**受理集合の実質的な拡大であり、
  速さのために正しさを削る変更にあたる。**
- **mtime や size だけの軽い検出器へ置き換える** — 同上。
- **digest を stat でキャッシュする** — 実測で 484→413 秒 (15%) にとどまる。stat が残るため。
- **blob sha だけをキャッシュキーにする** — `.gitattributes` の `eol` / `ident` /
  `working-tree-encoding` / filter により同じ blob が異なる working bytes へ展開されうるため、
  path を含めないキーは衝突する。相異なる blob は 12,074 / 18,126 file なので、
  path を含めると初回だけ約 6.7 秒増えるが、定常は不変であり**この費用を払う。**
- **実 repo 全体を参照オラクルと比較する常設テスト** — repo 成長比例の node を受入へ常設し、
  本決定が返済している債務を作り直す。代わりに repo の大きさに依存しない
  **性能モデルのテスト**を置き、初回 digest 回数・2 回目 0 回・別プロセスでの再 miss・
  `ls-files`/`status` の起動各 1 回・5 種のフォールバック条件での挙動を固定する。

## {{D:acceptance-floor-is-a-band-not-a-single-test}}. 受入の床は単独テストではなく 180〜290 秒の帯である

**決定:** 受入全走の最遅 shard の wall を論じるとき、**「最長の単体テスト 1 本」を犯人として
名指ししない。** 一次資料 (`/work/1/SFC/tanab/.izanagi-acceptance-shards/*/junit.xml`) を
固定窓で集計し、(a) 最長 node の分布、(b) 対象を除去した反実仮想での残存最長 node、
(c) 3 shard それぞれの wall と最遅 shard の identity、の 3 つを併記する。

**理由:**

- 固定窓 2026-09-04 03:07〜09-07 03:07 の 63 走で、最長単体 node は中央値 191.690 秒 /
  p90 293.859 秒 / 最大 369.238 秒。一方、`_real_output_snapshot()` を呼ぶ 11 node の各走最大は
  中央値 133.501 秒で、**全体最長だったのは 4 走 (6.3%) だけ**である。
- **対象を全部消しても、残る最長 node は中央値 191.690 秒で変わらない。**
  すなわち 180〜290 秒の帯に複数の node が並んでおり、単独の犯人はいない。
- wall 中央値は 324.326 秒、300 秒超過は 37/63 = 58.7%。
  246 秒を引く反実仮想でも wall 中央値は 223.419 秒 (1.268 倍) で、
  2 倍以上になるのは 1/63 走だけである。ある走では短縮 0 秒だった。
- したがって「この 1 本を直せば受入が速くなる」という形の主張は、**一次資料で否定される。**
  次の床は `test_t080_stub_free_e2e_single_defects...[ccbench-current...]` (44/63 走) と
  `test_role_sink_bytes_vary_only_at_declared_declassifications` である。
