# T-080 E2E fixture の worker 間共有を実装し、実測と敵対検証の末に却下した ([T-131])

2026-07-27 / cygnus (96 core、共有ノード) / worktree `dev-wave-t128-t080-scan`
(branch `worktree-dev-wave-t128-t080-scan`、基準 `83d991c`)。

**結論: [T-131] は却下する。コードは 1 byte も land させない。** 2 つの異なる方式で実装し、
敵対レビュー計 6 本を通したが、いずれも「正しさ基盤を性能のために弱める」blocker を残した。
得られる効果は全走 CPU work −13%、**全走 wall はゼロ**である。本文書はその実測と裁定の記録で、
次 wave の判断材料である。

測定はすべて worktree checkout (F41 に従い併記)。実装差分の着脱は patch の apply / reverse で
行い、cygnus は共有ノードのため A/B 交互測定とした。

---

## 1. 段 1 の前提実測 — worklog の前提は過少だった

worklog 2026-07-27 (22) の [T-131] は「T-080 E2E の 8 node が別 worker に散ると同じ base を
8 回組み直す。推定 work −170 秒」としていた。実測すると数字も構造も違った。

一時変異 (計測プローブの挿入) は `DW-O19` の復元規律を借り、`git diff` 確認と
`git checkout --` で復元した。

| 項目 | worklog の前提 | 実測 |
|---|---|---|
| node 数 | 8 | **11** |
| key 種類 | (記載なし) | **5** |
| build 回数 (`-n 32`) | 8 | **11 (cache hit 0 件)** |
| 削減余地 | 推定 −170 秒 | **−134.2 秒 (elapsed 合計)** |

`-n 32 --dist loadgroup` の targeted 走行で **11 node すべてが別 pid** に散り、
`_T080_E2E_BASE_CACHE` は **1 度も hit しなかった**。プロセス内 cache は現状まったく効いていない。

| key | 引数 | node 数 | build 1 回 |
|---|---|---|---|
| A | `distinct_basis_blob=True` | 1 | 22.45s |
| B | 既定 | **7** | 約 22.4s |
| C | `r_trailer="AI-Agent: codex"` | 1 | 20.69s |
| D | `extra_r_path=True` | 1 | 20.74s |
| E | `issue_receipt=False` | 1 | 0.92s |

合計 221.4 秒。key ごとに 1 回なら 87.2 秒。

### build 22.4 秒の内訳 — コストは fixture 構築ではない

| 段階 | 秒 |
|---|---|
| git-init / copy-orchestrator / copy-basis | 各 0.01 以下 |
| copy-output | 0.23 |
| submodule-add / submodule-checkout | 0.05 / 0.03 |
| git-add / git-commit / inspect-history | 0.51 / 0.03 / 0.01 |
| **子 python (draft→finalize→verify→gate)** | **21.22 (95%)** |

子の内訳は `draft_receipt 4.89 / validate_draft 4.77 / finalize+commit 6.36 /
verify_receipt 1.60 / gate_check 3.28`。**すべて本番の T-080 発行・検証経路**である。
[T-128] で塞いだ scan 膨張とは別物で、copytree でも submodule でもない。
[T-122] (`verify_receipt` の `search_repository` 重複) の射程がここに当たる。

---

## 2. 効果の上限 — wall はゼロ、CPU work だけが減る

実装版と baseline を patch で着脱し、交互に測った。

| 指標 | baseline (A) | 実装 (B) | 差 |
|---|---|---|---|
| targeted 11 node wall | 35.47 / 30.42 | 36.70 / 30.46 | **差なし** |
| 全走 wall | 70.88 平均 | 70.23 平均 | **不変** |
| 全走 CPU work (user) | 692.4 平均 | 596.0 平均 | **−96.4 秒 (−13.9%)** |
| 全走 user+sys | 777.5 | 677.6 | −99.9 秒 (−12.8%) |

**targeted wall が改善しないのは正しい挙動である。** 96 コアあるため、baseline でも 11 本の
build が並列に走り、wall は 1 build 分 (約 22 秒) + テスト本体しか消費していない。共有しても
critical path は同じ 1 build のままで、減るのは並列に浪費されている CPU だけである。

**全走 wall も動かない。** worklog 2026-07-27 (22) が確定したとおり、全走 wall の下限は直列 group
`dev-waves-integration` の 68.2 秒が支配しており、CPU work を減らしても下限は変わらない。

> **教訓: 性能改修の効果指標 (wall / CPU work / durations 総和) を、実装前に確定しておくこと。**
> 本 wave は wall で測れば「改善ゼロ」、CPU work で測れば「−13.9%」だった。
> 指標を後から選ぶと、水増しにも過小評価にもなる。

---

## 3. 方式 1 (自前 session 管理) — 複雑性が爆発した

段 4 で親は当初「key 単位の `xdist_group`」を推したが、**段 3 の敵対相談 2 本がこれを棄却し、
親は裁定を撤回した**。棄却の理由が本 wave で最も価値のある知見である。

- 親は「flock 共有は待つだけで work が減らない」と主張したが、**誤り**だった。flock 待ちは
  pytest durations には計上されるが、21 秒の子 python を 6 本起動しないので CPU・subprocess・
  git 走査・I/O の実作業は確実に減る。critical path も group 案が `22.4 + Σ post_i`、
  flock 案が `22.4 + max(post_i)` である。
- 親は「flock 案は複雑すぎる」とも主張したが、同 repo の `real_repo_receipt_memo.py` が
  **同一の問題** (「xdist では worker 数だけ実解決が走る。`-n 32` で 1 回 22 秒が 129 秒へ膨らむ」)
  を **同一の手法** (run UID + flock + atomic replace + fail-open) で既に解決していた。
- 決め手は group 案固有の危険だった。xdist は複数の group 名を集合化・ソートして `_` で結合する
  ため、function/module marker と param marker が混ざる。さらに `test_s8b_oracle_driver.py` には
  conftest の real-repo 正本 node が 7 個同居しており、module 全体へ marker を付けると hook が
  「既存 marker あり」で real-repo を付けずに素通りし、**既知の real-repo 競合が再開する**。
  親が根拠にした「group 名を間違えても build が余分に走るだけ」という失敗様式の非対称性は、
  この経路で成立しない。

そこで方式 1 = 「repo 外の一時領域に自前で session 共有領域を作る」を実装した。結果は
**1193 行**。session 束縛のための ROOT content identity 計算、publish manifest の照合、
stale prune、容量 budget、session lease、deadline が芋づる式に必要になった。
敵対レビュー 2 本 + 焦点再レビュー 1 本が blocker 2 件・must-fix 5 件を検出し、その大半が
**自前管理が生んだ新しい壊れ方**だった (ENOSPC の非決定的赤、prune と lock の race、
multiprocessing control の child 残留、prune が lock inode を消して排他が分裂する経路)。

---

## 4. 方式 2 (pytest の session ディレクトリ) — 単純になったが前提が崩れる

親は実測で逃げ道を見つけた。pytest-xdist の各 worker の `tmp_path_factory.getbasetemp()` は
`<...>/pytest-of-<user>/pytest-<N>/popen-gw<K>` であり、**parent の `pytest-<N>` は全 worker で
共通**である (`-n 4` で gw0〜gw3 すべてが `pytest-403` を共有することを実測)。pytest がこれを
session ごとに新設し世代管理するので、identity・manifest・prune・budget・lease が**すべて不要**に
なる。差分は **570 行**まで縮み、複製回数も旧版 22 回に対し 16 回へ減った。

しかし焦点再レビューが中心前提を崩した。**`getbasetemp().parent` は無条件の session 境界ではない。**

1. 明示 `--basetemp=/X` の並行 session は、両方の parent が `/X` になる
   (`tools/run_tests.py` は `--basetemp` を禁止していない)。
2. 外側 xdist worker の環境変数を継承した内側 `pytest -p no:xdist` では、内側の basetemp が
   `pytest-of-user/pytest-N` になるため、**parent は全 session 共通の `pytest-of-user`** になる。
   実装は plugin の実在を確認せず環境変数だけを見ていた。
3. `tmp_path_retention_count=0` / policy `none` では cleanup lock を作らず、番号が再利用される。

そして published の loader は「`.git` がある・必要 file が存在する・receipt が dict」しか
見ていないため、境界が崩れたときに **別 checkout の旧 verifier を正規 fixture として受理する**。
exact refusal 検査が偽緑になる経路であり、絶対規律 2 / 3 への直接攻撃である。

---

## 5. 却下の裁定

| 観点 | 判断 |
|---|---|
| 効果 | 全走 CPU work −13%、**全走 wall ゼロ**、targeted wall ゼロ |
| 費用 | 2 方式・6 本の敵対レビュー・のべ 1893 行を書いても blocker が残った |
| 対象 | T-080 の oracle gate stub-free 検査 = **正しさ基盤そのもの** |
| 規律 | 規律 2 (正しさゲートを性能のために緩めない) / 規律 5 (盛らない) |

**2 つの独立した方式が同じ壁に当たったことが本質である。** 共通の根因は、
「テスト fixture を worker 間で共有すること自体が、各 node が現在の ROOT から作られた正しい
base を使うという前提を弱める」ことにある。共有の正当性を保証しようとすれば複雑性が爆発し
(方式 1)、保証を省けば偽緑経路が残る (方式 2)。中間はなかった。

wall を 1 秒も縮めない改修のために、正しさ基盤へこの種の機構を持ち込むのは割に合わない。

**実装差分がない (コード 0 byte) ため、変異 matrix と受入全走は [T-131] の受理判断の対象外**
である。記録 commit 後の repo 全体の受入全走 (F34) は §7 に記す。

---

## 6. 却下しても残る、より有望な代替 (次 wave の裁定材料)

段 3 の敵対相談が指摘した案で、**共有機構を一切必要としない**。

`_build_t080_stub_free_e2e_repo` の子 python は、key C (`bad-trailer`) と key D (`extra-r-path`)
のために draft→validate→finalize の全経路を最初から通している。しかし両者が分岐するのは
receipt commit の直前だけで、production verifier も C は commit message、D は introduction commit
の diff だけから拒否する。したがって **C と D は canonical な B の receipt を作った後、
receipt commit を amend するだけで再現できる**。高価な子 pipeline は 4 回から 2 回になり、
build 合計は 87.2 秒ではなく **約 45.8 秒**まで下がる。

**ただしこれは検出力に触る。** C/D が本番の draft→finalize を通らなくなるため、
現在の stub-free 契約 (「production builder/verifier/gate を一度も stub しない」) を弱める。
採否はユーザー裁定事項であり、本 wave では実装しない。

なお **wall を実際に縮める道は [T-131] でも [T-130] でもなく [T-132]** (直列 group
`dev-waves-integration` の分割、実測 wall 69.99 → 59.40 / 61.06 秒 = −15%) である。

---

## 7. 記録 commit 後の受入全走と、負荷依存フレークの帰属確定 ([T-136])

`DW-S07` (F34) に従い、記録 commit の後に repo 全体の受入全走を実施した (worktree checkout)。
**このとき作業ツリーのコード差分は 0 byte である。**

| 走行 | load average | 結果 | wall |
|---|---|---|---|
| 1 回目 | **28.41** | **2 failed** / 3087 passed / 14 skipped | 103.90s |
| 再走 1 | **21.91** | **1 failed** / 3088 passed / 14 skipped | 71.10s |
| 再走 2 | 14.89 | **3089 passed** / 14 skipped / 0 failed | 70.90s |
| 再走 3 | 12.15 | **3089 passed** / 14 skipped / 0 failed | 71.04s |

`check_docs` rc=0、`check_ai_provenance` 409 件違反なし。

赤くなったのはすべて `test_dev_waves_integration.py` の timing 依存 node で、reason は
期待値ではなく `TIMEOUT` / `INVALID_RUN` だった。当該テスト群は `total_timeout=10` で
supervisor の実走を待つ。

**帰属は確定した。** 実装測定の段階では実装版の全走 12 回中 2 回でのみ観測され、baseline は
12 回すべて緑だったため、「新設 control が spawn する process の瞬間負荷が押し出した」可能性を
疑っていた。しかし**コード 0 byte の HEAD そのもので再現し、負荷との単調な相関が出た**ことで、
**実装差分とは無関係**と確定した。負荷源は他ユーザーの process であり (cygnus は共有ノード)、
こちらから制御できない。

`DW-O18` に従い負荷依存フレークとして [T-136] に起票する。**これは衛生ではなく実害である** —
共有ノードでは受入全走の判定そのものが汚れ、本 wave でも記録 commit 後の 1 走目が偽赤になった。
同ファイルの flake は worklog 2026-07-27 (21) にも既報である。

---

## 8. 作業物の所在

破棄した 2 方式の patch と、敵対レビュー 6 本の全文は job tmp
(`/home/tanab/.claude/jobs/498f8730/tmp/wave-t131/`) にある。**session 専用領域であり生存保証が
ないため、再挑戦する場合は本文書の §3・§4 に要約した blocker を出発点とすること。**

| 成果物 | 行数 |
|---|---|
| `attempt1-selfmanaged.patch` (方式 1、段 6 fix 適用後) | 1257 |
| `attempt2-basetemp.patch` (方式 2) | 693 |
| 敵対相談 2 本 / 敵対レビュー 2 本 / 焦点再レビュー 2 本 | — |
