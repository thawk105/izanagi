# [T-2639] 救出検査の landed 判定を path 一次判定へ寄せ、未証明理由を人へ運ぶ

2026-09-16。wave `dev-wave-t2639-branch-rescue-path-first`、branch
`worktree-dev-wave-t2639-branch-rescue-path-first`、実装 commit `99125e783`。
base main `61e0e9c4a`。

## 何を解いたか

`tools/check_branch_rescue.py` の landed 判定が本 repo の規模で解けず、rc が常に 2 (可視化不完全)
になっていた。**常に不完全を返す gate は警告として情報を運ばず、無視する習慣を作る。**

原因は 2 つに割れた。どちらも実測で特定した。

1. **遅さの正体は履歴の走査ではなく subprocess の起動だった。** `_find_exact_state` は
   `git log --full-history` で候補 commit を列挙したあと、**候補ごとに `git ls-tree` を 1 本ずつ
   起動**していた。path `orchestrator/tests/test_check_ai_provenance.py` (候補 361 commit、
   main の commit 数 10608) で測ると、候補列挙は 0.48 秒、逐次 `ls-tree` 361 本が 10.92 秒、
   一括 `git cat-file --batch-check` が 0.09 秒だった。
2. **spool fragment は fold 受領記録の内容ハッシュだけで引いていた。** 記録が無いと
   exact-state の履歴探索へ落ちず、永久に未証明で残った。

## 実測 (main 61e0e9c4a、固定 OID)

`check_branch_landed.py` 単体。**判定・閉包・unit の理由内訳は 4 走とも完全一致。**

| 対象 | verdict | closure | unit | git 子 process | 秒 |
|---|---|---:|---:|---:|---:|
| `aae713e1de…` 改修前 | indeterminate | 7 | 10 | 2005 | 26.55 |
| `aae713e1de…` 改修後 | indeterminate | 7 | 10 | **92** | **11.35** |
| `559bcbc29c…` 改修前 | indeterminate | 15 | 41 | 1190 | 51.29 |
| `559bcbc29c…` 改修後 | indeterminate | 15 | 41 | **244** | **32.77** |

`check_branch_rescue.py --branch worktree-dev-wave-t2515-calib-rr95-rr5`。

| 予算 | | 判定不能 7 件の内訳 | 全体秒 | assessment 秒 |
|---|---|---|---:|---:|
| 60 秒指定 | 改修前 | — | 261.44 | 209.09 |
| 60 秒指定 | 改修後 | — | 206.69 | 150.36 |
| **既定 (8 秒)** | 改修前 | **`checker-timeout` 7 件** | 102.61 | 57.08 |
| **既定 (8 秒)** | 改修後 | **`one-or-more-states-unproven` 4 件 + `checker-timeout` 3 件** | 87.34 | 36.19 |

**掃除コマンドが実際に使う既定予算では、改修前は 7 件すべてが「見終えていない」だった。**
改修後は 7 件中 4 件が実質的な理由を返し、それが `unproven_unit_details` で rescue の JSON まで
届く。これが依頼への直接の答えである。

## 主張しないこと

- **rc は 0 にならない。** D1231 は「`indeterminate` があっても rc=0 を返す」を明示的に却下して
  いる (ユーザー要求「判定できないものが残る間は通さない」)。1 件でも未証明が残れば rc は 2 の
  ままである。本 wave は受入条件から「rc=0」を外した。
- **「main 側の改版で価値が取り込まれた」は機械判定していない。** D922 の決定的証拠 (a)(b) の
  枠内では判定できない。証拠契約の変更が要るので裁定パッケージへ返した。
- **速さは端から端で 121 倍ではない。** 121 倍は候補参照だけの局所比であり、候補列挙を含めると
  約 20 倍、mode 再確認と他の処理を含めると実測で 2.3 倍 (26.55 → 11.35 秒) である。
- **exact-state 履歴の一致は fold 完了そのものの証明ではない。** 証明しているのは
  「その内容状態が main から到達可能だったこと」である。
- **spool fragment の負例が「未着地」であることは証明していない。** 候補 0 件は `indeterminate`
  の根拠であって、未着地の確定ではない (D922 点 5)。

## 変異 matrix

probe を全件 `SURVIVED` 登録で走らせて観測 node を集め、それを期待値にして本走した。
**baseline 緑 (176 passed)・11/11 KILLED・SURVIVED 0・MISMATCH 0・期待 node 完全一致。**

**N01 は過剰決定である。** spool の未証明を `not-landed` に変える変異は 12 本を赤にし、そのうち
10 本は wave 開始前から在ったテストである。よって N01 の KILLED は、本 wave が足した負例
(`test_unlanded_pure_add_spool_stays_indeterminate`) が効いていることの証明にはならない。
単一理由で効いているのは N03 / N06 / N07 / N09 / N10 (各 1 node) と、N02 (既存 1 + 新規 1)、
N04 (予測どおり lf / tab / space / cr の 4 件)、N07 (colon 1 件) である。

## 敵対レビューが縮めさせた主張

- **偽の「着地済み」を作る経路は、段 3 の 2 レンズも段 6 の 2 レンズも見つけられなかった。**
  batch の行検査・順序検査を抜けても、最後に同じ commit を読み直して四要素を突き合わせる層が
  残るためである。ただし「全入力で受理集合が不変」までは言えない — S2 は意図的に、receipt が
  無くても exact 証拠のある spool を受理する方向へ広げている。
- 親 brief の誤りを 5 件突かれた。M3 は blob 一致しか測っておらず四要素の正例実測として不足、
  121 倍は局所比、symlink の object type は blob で差は mode、「rc=2 が削除 gate を止める」は
  `/cleanup-branches` §2 が rc を使わない事実と矛盾、「18 件取りこぼす」は「18 種類の状態」で
  あって merge commit 18 個ではない。いずれも採用して訂正した。
- 段 6 レビュー B が **S4 が spool の探索事情を落とす**ことを突いた。正常 receipt 不在 + exact
  不一致では exact 層が非 decisive になり S4 から除外されるため、rescue の JSON だけでは
  「候補 0 件」と「複数候補を調べたが不一致」を区別できなかった。探索が実際に走った層は非
  decisive でも運ぶよう直した。
- 段 6 レビュー A が **運ぶ層に `decisive` が無いと「全部が判定を決めた」と誤読される**ことを
  突いた。各層に `decisive` を付けた。

## 実在 path の発見

追跡 path 25475 件のうち、**`:` を含む path が 1,653 件実在する** (例
`output/env/pegasus/calibration/job-staging/0:867863.nqsv/allocation-unavailable.json`)。
`<commit>:<path>` を `split(":")` で分解する実装は禁止である。空白・改行・復帰・タブを含む path は
今回の index には無いが、`%(rest)` が入力を最初の空白で割るため legacy 経路へ退避させている。

## 受入 — 10 回走らせ 10 回とも赤。すべて非帰属。land できず正式停止した

同一 tip・同一差分で受入全走を 10 回走らせた。**10 回とも赤で、receipt は 1 度も発行されていない。**

| attempt | 通過 | 赤 | 備考 |
|---:|---:|---:|---|
| 1 | 23833 | 2 | |
| 2 | 23832 | 3 | |
| 3 | 23842 | 1 | 赤は F300 名指し集合のみ |
| 4 | 23835 | 8 | うち setup error 7 |
| 5 | 23841 | 2 | 赤は F300 名指し集合のみ |
| 6 | 23842 | 1 | F300 が機序を明示した node |
| 7 | 23841 | 2 | 赤は F300 名指し集合のみ |
| 8 | 23841 | 2 | |
| 9 | 23841 | 2 | 赤は F300 名指し集合のみ |
| 10 | 23949 | 3 | 赤は F300 名指し集合のみ |

**帰属の実測。** 赤になった 9 種の test はいずれも `check_branch_landed` / `check_branch_rescue` を
**0 回**参照する (`grep -c` で実測)。単独再走はすべて緑 (3 passed / 3 passed / 2 passed、いずれも
rc=0)。親の worktree は全走の前後とも `git status --porcelain=v1 --untracked-files=all` が **0 行**で
残骸も無い。落ちる検査はこの status を処理の前後で撮って一致を要求するので、**変化の出所は走行の
内側**である。

**機序は F300 に記録済み。** 同日に別 wave ([T-2638]) が同じ機序で 5 走赤・6 走目で緑になっている。
本 wave はその独立 2 例目であり、10 走でも緑に当たらなかった。

**hold 登録は試みて撤回した。** `DW-O18` は「main 既存 F を証拠に Codex `role=author` が
`orchestrator/tests/flaky_test_holds.py` へ登録」と定める。F300 を証拠に 4 node を登録し、
登録簿自身の validator は通ったが、`test_flaky_test_holds_contract.py` が
**登録簿をちょうど 1 件・`evidence_id="F57"`・`reintroduction_task_id="t-1079"`・sha256 まで逐語で
固定**しているため赤になった。この pin は **wave が自分を緑にするために除外集合を広げることを、
wave 開始前から在るテストの期待値を書き換えないと不可能にする防壁**である。よって pin を書き換える
側 (= 本 wave の登録) が誤りと裁定し、`git checkout --` で撤回して clean を実測した。

**主張しないこと:** 「10 走赤だから実装が正しい」とは言わない。言えるのは
「赤が本 wave の変更面へ帰属する証拠が 1 件も無く、単独走では緑である」までである。
受入全走の緑は**取れていない**。

## 裁定パッケージへ返した設計択一

1. **候補上限超過時の正例優先と D922 逐語の不整合。** 実装は上限超過を検出する前に正例を受理する。
   D922 点 4 の逐語は打ち切りをすべて `indeterminate` へ倒すと書く。D922 を書いた [T-1239] wave
   自身が `test_history_match_at_candidate_33_wins_before_65_plus_truncation` で現行挙動を逐語
   固定しているため、本 wave では変えていない。
2. **「main 側の改版」の扱い。** rc を 0 にするには、exact 証拠が無いケースに何を認めるかを
   決める必要がある。証拠契約の変更であり AI が単独で決めない。
3. **rc=2 の定義が正本どうしで割れている。** `docs/unreachable-object-ledger.md` の rc 表は
   rc=2 を「timeout、上限超過、root 移動、期限算出不能、台帳 parse 不能などで技術的に不完全」と
   定義し、**`indeterminate` verdict を挙げていない**。一方 D1231 の却下項は
   「`indeterminate` があっても rc=0」を却下している。実装は後者に従う
   (`check_branch_rescue.py` の `complete = expected_conclusive`)。**実装は変えていない。**
4. **削除 spool fragment の exact 証明対象。** required の不在と old blob の過去存在のどちらを
   証明するのかは、削除の意味と整合させる必要がある。本 wave は新しい fallback を足していない。
5. **親子 timeout の終了余裕。** rescue の子 deadline と外側 subprocess timeout が同値で、
   Python 起動・JSON 出力の時間差により子の理由 JSON より先に親が kill しうる。
6. **`DW-O18` の hold 登録手順と、登録簿を 1 件へ固定する契約テストが正面から衝突する。**
   手順に従うと `test_flaky_test_holds_contract.py` が赤になり、契約テストを守ると手順を使えない。
   どちらも main に在り、どちらも自分の側では正しい。正本どうしの選択であり AI が単独で決めない。

## 成果物の所在

- 実装 commit `99125e783` (4 file、686 挿入 / 10 削除)
- branch `worktree-dev-wave-t2639-branch-rescue-path-first`
- 変異 spec / 結果: 本 dir の `mutation-final-spec.json` / `mutation-final-out.json` /
  `mutation-probe-spec.json`
- 子の逐語 12 本: `verbatim/`

## 次の律速

`559bcbc29c…` の改修後 32.77 秒の内訳は exact-tree-state 15.67 秒、any-path 0.48 秒、
ledger_corpus 0.27 秒、task_index 0.0 秒、verbatim 0 秒。**残り約 16 秒は closure 列挙と
`_introduced_states` の per-parent diff 側**にある。既定予算で残る 3 件の `checker-timeout` は
ここが原因である。
