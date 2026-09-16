---
authority: none
default_effect: no-state-change
---

# [T-2638] 裁定パッケージ — Codex 実装子 worktree の終端所有者と終端契約

本書は**裁定を求める資料**であり、可変状態の正本ではない。ここに書かれた案はどれも未採用で、
本 wave は `.codex/worktrees/` を 1 byte も変更していない (読み取りのみ、`--no-optional-locks`)。

- 一次資料: 同ディレクトリの `s1-brief.md` (親の brief)、`measurements.md` (実測の取得方法と限界)、
  `s4-adjudication.md` (段 4 裁定)、`data/` (計測結果の表)、
  `verbatim/` (子の出力を無改変で凍結 — `s2-plan.md`、`s3-lens1.md`、`s3-lens2.md`)。
- **計測スクリプトの実物は repo へ入れていない。** `.sh` は実装面にあたり、入れると
  docs-only でなくなって Codex `role=author` が要るためである (`docs/ai-provenance.md`)。
  実物は job directory `/home/SFC/tanab/.claude/jobs/2b4c302e/wave/materials/` にあり、
  判定に関わる部分は `measurements.md` へ逐語で引用してある。
- 取得日時: 2026-09-16 04:20〜05:30 JST、Pegasus login node。
- **`verbatim/` は子の出力を 1 byte も変えずに凍結してある。** markdown の改行記法 (行末 2 空白) を
  含むため `git diff --check` が末尾空白を指摘するが、逐語性を優先して正規化していない。
  凍結の同定は次のとおり (sha256 / bytes)。

| file | sha256 | bytes |
|---|---|---|
| `verbatim/s2-plan.md` | `9f10a17393221fc6fbddac4b9269fff92637e42a5c9f227a1918e667f77c40db` | 23931 |
| `verbatim/s3-lens1.md` | `3db98836b948c5127effd9e1df2a7dbb63ef25da198ea62d280e0db371acc93c` | 12399 |
| `verbatim/s3-lens2.md` | `2b0272557f25942f68783908b24a8ce1443fd57f7cc8cf19873dc4c335d1753d` | 18111 |
| `data/xy.txt` | `fb5ccb78153b0140bc8a2c36908651758cad12de41e5916879fa1238e45e47ed` | 107 |

## 1. なぜ AI が決められないのか

**D703 (ユーザー裁定、2026-08-23) が自動削除の射程を明示的に閉じている。** 逐語:

> 対象は同一 invocation の exact な wave worktree path と wave branch ref だけ。
> (中略) その他の branch には D204 をそのまま維持する。**対象を特定したユーザー指示なしに
> AI が branch を削除してよい範囲は、この例外の外へは広がらない。**

実装子の worktree と branch は「自 wave の worktree と branch」ではない。したがって

- 子を段 9 で自動撤去する契約を作ること自体が D703 の射程拡大であり、
- 既存 67 件を一括処理することも、対象を特定したユーザー指示にあたらない。

**AI が単独で進めてよいのは、案の提示と実測までである。** 本 wave はそこで止めている。

## 2. 何を裁定してほしいか

| # | 択一 | AI の推奨 | 選ばないと何が起きるか |
|---|---|---|---|
| R1 | 段 9 の自動撤去を**記録に束縛した子**へ広げるか / 現行どおり wave 本体だけに保つか | 広げる | 保つなら流入は止まらない。掃除の高速化 ([T-2641]) は件数増加に追い越され続ける |
| R2 | 通常経路を**案 C (着地証明) + 限定 B** にするか / **案 A (子へ commit)** にするか | C + 限定 B | A は patch 中心の統合契約そのものを変えないと成立しない (下記 5.1) |
| R3 | 不採用物の破棄を**毎件ユーザー裁定**にするか / **限定した破棄権限を親へ与える**か | 限定権限 + 例外は停止 | 毎件裁定なら人間手番が件数に比例する。限定権限なら誤破棄の残余リスクを負う |
| R4 | 不採用物は**理由と hash だけ**残すか / **内容も保存**するか | 理由と hash + 対象を特定した裁定 | 内容保存は一時 probe を恒久化する。hash だけでは bytes を復元できない |
| R5 | 既存 67 件を**対象を名指しした migration** で減らすか / **将来分だけ先に閉じる**か | 名指し migration を別 wave で | 将来分だけなら 67 件は残り続ける。掃除の所要も減らない |
| R6 | `DW-O20` の `git worktree lock` の**解錠責任**を所有親に置くか / 現状のまま放置か | 所有親に置く | 放置なら汚れを解決しても locked 8 件は永久に残る (下記 4.3) |
| R7 | 親が**正式停止**した後の子の責任を、元親の保留事項として残すか / 明示した担当者へ引継いで親を閉じられるようにするか | 引継ぎを認める | 元親に残すと、停止した親は二度と動かないので子が永久に宙に浮く |
| R8 | 流入対策として、旧 67 件を**固定 cohort** として閉じ新規分の契約を先行させるか / 新規投入を一時止めて旧分を処置するか | 固定 cohort + 新規先行 | どちらも選ばないと、処置している間に増え続けて収束しない (下記 9.6) |

R1 が否なら R2〜R8 は起動しない。R1 が是なら、R2〜R8 は独立に裁定できる。

**R1 を是とする場合でも、本 wave は実装可能であることを示していない。** 着手前に満たすべき前提を
第 9 節に 7 件挙げた。特に「gate 全体を通る正例が 1 件も無い」(9.3) は、機構を足しても
全件保留のままになる可能性を排除できていないという意味である。

## 3. 現況 — 誰が作り、誰も撤去しないか

| 段階 | 現行契約 | 途切れている点 |
|---|---|---|
| 親が編集単位ごとに子 worktree を用意する | `DW-S05-A` (`docs/dev-wave/workers.md`) | 作成に対応する撤去が書かれていない |
| 子が編集し、親が所有 path 限定 patch を抜く | `DW-S05-A`。`git add -A` → `git diff --cached` → `git apply` | **内容の移送であって、子の branch を main の祖先にする処理ではない。** 子の index と作業木が残る |
| 走行中の木を保護する | `DW-O20` が `git worktree lock` を要求 | **解錠する契約がどこにもない** |
| 親が main へ land する | `DW-O23`。Claude/Codex worktree へ**非接触**と明記 | land に掃除を期待できない。非接触は維持すべき |
| 親が自分を撤去する | `DW-O28` / D702 / D703 | 対象は **wave 自身**。子集合を処置する契約がない |
| 明示 cleanup が残骸を調べる | `/cleanup-branches` §2 | ahead=0 かつ status 空のみ削除。§3 は locked/occupied を**そのまま引き渡す** |

**3 つの機構がそれぞれ正しく「自分の仕事ではない」と判断している。** 所有グラフの穴であり、
どれか 1 つのバグではない。

## 4. 実測 (2026-09-16 JST、Pegasus login node)

詳細と取得方法は `measurements.md`。要点だけ。

### 4.1 母集団

- `.codex/worktrees/` = **67 件** (依頼時 2026-09-15 は 58 件)。
- branch 接頭辞: `impl-*` 37、`fix-*` 21、`codex-*` 5、`acceptance-*` 1、`merge-/mut-/mut2-*` 3。
  **段 5 実装子と段 6 fix 子が 58 件 (87 %) を占める。** これは `DW-O28` の対象外そのものである。
- 1 件 = 734 MB / 26188 file。67 件で約 49 GB。
  **ただし filesystem は 4 % 使用・inode 17 % 使用。容量は律速ではない。**
  費用は掃除の所要と land の詰まりであって、ディスクではない。
- 差分 file の mtime は 2026-09-13 22:50 〜 2026-09-15 23:25 に収まる。**3 日より古いものは無い。**

### 4.2 穴は wave の死亡率ではなく契約の射程にある

名指しの実例で示す。`t1643-impl` は現存するが、その wave 作業木
`dev-wave-t1643-has-include-pair` は `.claude/worktrees/` に無く、T-1643 は着地済み
(worklog 1498)。同型が `t1706-impl`、`prov-batch` (1518)、`t1994-*` 21 件 (1519) にもある。

**wave は段 9 へ到達し、`DW-O28` で自分だけを畳み、子を残している。**

**ただし段 9 だけでは閉じない** (敵対レビューの所見、採用)。届かない経路が少なくとも 4 つある。

1. 子 worktree を作った後、起動前検査で停止し、記録がまだ無い。
2. 段 5 / 6 の子が終わった後、親が timeout・正式停止し、段 7 にも段 9 にも到達しない。
3. land 成功後、cleanup を呼ぶ前に親が終了する。
4. 別 command が作った木は、この wave 親の記録に入らない。

したがって段 9 は**正常終了時の発火点**であり、中断分と別 producer 分には別の担当を立てる必要がある。
また「親木が無い + 着地済み」は `DW-O28` が実行された証拠ではない (推論であって観測ではない)。

(件数比 67 対 17 は根拠に使わない。`.claude/worktrees/` は 04:20 に 9 件、04:55 に 17 件で
時点依存が大きい。)

### 4.3 錠 — 独立した第二の原因

`DW-O20` は子 worktree の `git worktree lock` を命じるが、**解錠する義務はどの節にもない**。
`/cleanup-branches` §3 は locked を「detach・unlock・削除・prune を行わず、そのまま引き渡す (F51)」
と定める。実測で **8 件が locked**。うち `prov-batch`、`t1706-impl`、`t2288-impl`、`t2591-impl`
は wave 本体が既に存在しない。

**汚れを解決しても、この 8 件は錠だけで残り続ける。**

なお**解錠の機構は既にある** — `tools/dev_wave_cleanup.py` は対象が locked なら
`git worktree unlock` を実行する。欠けているのは機構ではなく、子へ適用する契約である。

### 4.4 所有記録は存在するが寿命が足りない

`tools/codex_worker_launch.py` は wave ごとに `manifest.json` を書き、各 session の
`recorded_cwd` が子 worktree の絶対 path を持つ。実例:

```
dev-wave-t1643-has-include-pair-author-0 | /work/1/SFC/tanab/izanagi/.codex/worktrees/t1643-impl
```

しかし `/work/1/SFC/tanab/dev-wave-jobs/` の 1190 job dir のうち manifest を持つのは 183 本で、
**現存 67 件と一致したのは 2 件だけ**だった。(走査範囲は同ディレクトリのみ。背景 job 配下は
未走査なので、**「65 件に所有記録が存在しない」ではなく「限定探索では所有者を回復できなかった」**が
正しい。)

原因: **背景 job の wave は artifact root を job dir の中
(`~/.claude/jobs/<id>/dev-wave-jobs/`) に置くため、job を消すと記録ごと消える。**
記録の寿命が worktree の寿命より短い。

現存する durable な符号化は branch 名で、**61/67 (91 %)** が `<種別>-dev-wave-<wave slug>` 形式。
外れるのは `codex-*` 5 件と `acceptance-*` 1 件。ただし**命名は手掛かりであって所有の証明ではない。**

**さらに重い問題がある。** `.codex/worktrees/` 配下という**位置からは所有権を導けない**。
Codex が manager として dev-wave を回す経路では、同じ container に **wave 本体**が置かれる
(`tools/check_docs.py` が pin する Codex skill の起動手順)。したがって「配下にあるから子」と
判定する設計は、**稼働中の manager 本体を消す経路**を持つ。実測でも branch 接頭辞は 7 系統あり、
producer が一様でない。

## 5. 三つの案

### 5.1 案 A — 子の作業木を branch へ commit する

**単独では掃除を塞がない。** `/cleanup-branches` §2 と `DW-O28` はどちらも branch 削除を
`git branch -d` に限り、`-D` を禁じている。子へ commit すれば branch は ahead>0 になり、
`-d` が拒否する。**汚れた作業木という障壁が、未 merge branch という障壁へ移るだけ**である。

成立させるには、`DW-S05-A` の patch 中心の統合 (`git add -A` → `git diff --cached` → `git apply`)
を、**子 commit を祖先として保持する統合**へ変える必要がある。これは段 5 の所有・投入契約の
本体を変える。

さらに、**採用しなかったものまで commit すると一時 probe が歴史に残る**。実例は `t1643-impl` の
475 行 probe で、T-1643 自身は「docs のみ・実装面差分ゼロ」で着地している。後から削除しても
履歴からは消えない。

### 5.2 案 B — 破棄を記録して撤去可能にする

記録は**新しい台帳を作らず**、wave の insight 成果物へ「子 worktree 終端」項目として統合する。
記録単位は子 1 件、項目は所有者 / 対象 (絶対 path・Git admin・branch・HEAD) / producer の終端証拠 /
index と作業木を区別した対象一覧 / 各 path の種別・mode・OID・処置 (`landed` / `discard-approved` /
`hold`) / 理由 / 裁定の参照。

**「不明だから破棄」は認めない。** 破棄の正当性は、内容を特定したうえで元の採用判断・成果物影響・
ユーザー裁定と照合して初めて成立する。`t1643` の「docs のみ着地」は破棄候補の根拠になるが、
それだけで 475 行を消す権限にはならない。

理由と hash だけを残す設計は、**bytes を復元できない**ことを受け入れる選択である。

### 5.3 案 C — 着地証明を条件にした撤去

「変更 file の内容 blob が着地 main から到達可能」を**必要条件**にする。

**十分条件にはできない** (敵対レビューで確定)。file ごとの blob が別々の時点に存在したことは、
変更一式が採用された証明ではない。加えて次を同時に満たす必要がある。

- 対象集合の**完全性** — index と作業木を独立に列挙し、削除・rename・mode・symlink・
  未追跡・ignored・submodule 内・未解決 stage を落とさない。
- **採用対応** — その内容が親の patch として実際に採用されたことの記録との突合せ。
- HEAD reflog の全 commit が main の祖先 (既存 `_assert_reflog_commits_reachable` を維持)。
- 所有・producer 終端・非占有・解錠権限。
- 証明後に状態が変わっていないことの再確認。

**gate は恒真ではない。** 止める入力が実測で 2 型実在する — 稼働中 wave の子 (`prov-incr-impl`)、
どの commit にも保存証拠が見つからない内容 (`t1643-impl` の probe)。
**ただし通す側の正例はまだ 1 件も確認できていない** (下記 8 を参照)。

## 6. 推奨

**通常経路は C + 限定 B、発火点は段 9 の正常終了、中断分は別担当。**

理由は 3 つある。

1. **「main から到達可能なものだけ捨ててよい」はユーザーが既に批准した原理である。**
   D703 の理由節が逐語でそう述べている — 「ancestry を必須にするため、削除された commit は
   main から到達可能なまま残る。」`tools/dev_wave_cleanup.py` はこれを commit 粒度で実装済み。
   C はこの原理を、どの commit にも入っていない**作業木の内容**へ広げるだけである。
   **新しい原理を導入しない。**
2. **A は障壁を移すだけで、しかも一時 probe を歴史へ焼き付ける。** A を成立させるには段 5 の
   統合契約そのものを変える必要があり、本件の目的 (残骸の終端) に対して代償が大きい。
3. **B は C が証明できないものの受け皿として必要**だが、単独では「不明だから破棄」への傾斜を
   止められない。C を通常経路にし、B を**明示裁定された例外**に限る組合せが、
   絶対規律 2 (判定不能を受理へ倒さない) と整合する。

**ただし本 wave は、この推奨が実装可能であることを示していない。** 下記 8 と 9 が未了である。

## 7. 既存 67 件の扱い — 救出が要るのは 1 件だけである

修正版照合 (`reach2`) が 67 件・251 entry を完走した。**worktree 単位の最悪判定**で分類する。

| 判定 | 件数 | 意味 |
|---|---|---|
| CLEAN | 1 | 変更が 1 件も無い (`t1851-c3c-detail`) |
| LANDED-CURRENT | 17 | 全 file が main の**現行内容**と 1 byte 違わない |
| LANDED-HIST | 44 | 現行とは違うが main の履歴に同一 blob がある |
| OTHERREF | 1 | main に無く別 ref にある (`prov-incr-impl`) |
| NOWHERE | 4 | どこにも保存証拠が見つからない |

entry 単位では LANDED-CURRENT 70、LANDED-HIST 103、NOWHERE 62、DIR-ENTRY 14、OTHERREF 1、CLEAN 1。

### 7.1 NOWHERE 62 entry の正体 — ほぼ全部が再生成可能物

| 対象 | entry 数 | 正体 | 救出 |
|---|---|---|---|
| `t2566-fix3` / `t2566-c` | 58 | **pytest の一時出力** (`.tmp/pytest-of-tanab/pytest-0/...` の `campaign.lock`、`wal.jsonl`、`*-execution.json`) | **不要。** テスト scratch であり再生成可能物 |
| `t2596-impl` | 2 | `stage5-owned.patch`、`fix-spawn-sites.patch` — **`DW-S05-A` の patch 抽出手順が作った成果物そのもの** (親が `git diff --cached --output=` で出したもの) | **不要。** 中身は差分で、適用済みの変更として着地している |
| `t1643-impl` | 1 | `tools/t1643_has_include_pair_probe.py` (475 行)。T-1643 は「docs のみ・実装面差分ゼロ」で着地 (worklog 1498) | **判断が要る。意図的に落とした一時 probe と読める** |

`DIR-ENTRY` 14 件はすべて pytest の `-current` **symlink** である
(`.tmp/pytest-of-tanab/pytest-current` 等)。計測器の `[ -f ]` がリンク先の directory を辿って
落ちたもので、内容としては再生成可能物である。

### 7.2 分類

| 分類 | 件数 | 対象 | 根拠 |
|---|---|---|---|
| **触るな** | 1 | `prov-incr-impl` | 稼働中 wave `dev-wave-prov-incremental-audit` の子。差分は別 ref にのみ存在 |
| **判断が要る** | 1 | `t1643-impl` | 唯一の「実際の未着地ソース」。ただし意図的に落とした 475 行の一時 probe である |
| **保存物としては撤去可の候補** | 65 | 残り | 全 file が着地済み、または未着地分が pytest scratch と抽出 patch だけ |

**ただし「撤去可の候補」は「撤去してよい」ではない。** 内容の保存が確かめられたというだけで、
所有・producer の終端・非占有・解錠権限・reflog ancestry・D703 の許可はどれも満たしていない。
とくに次の 3 点が残る。

- **8 件は `git worktree lock` 済み**で、`/cleanup-branches` §3 はそのまま引き渡す。
- **`LANDED-HIST` 44 件の証拠 SHA は無効**である (下記 8.2)。撤去の根拠に使うには
  `ls-tree` による tree 直接照合で取り直す必要がある。
- **占有は時点で変わる。** 全走査の終了後に取り直すと 71 件中 3 件が occupied で、
  その 3 件 (`t2545-impl`・`t2586-impl`・`t2639-impl`) はいずれも**今動いている wave の実装子**だった。
  走査と同時に測った初回の occupied 3 件は親自身の走査による自己マッチで、走査を止めたら free に
  なった。**撤去判定に使う占有検査は、自分の走査と同時に行ってはならない。**
  なお D391 のとおり rc0 は必要条件にすぎず、TOCTOU の窓は撤去の終了まで開いたままである。

### 7.3 依頼の前提への訂正

依頼は「差分の中身は再生成可能物ではなく実際の未コミットのソース編集」と述べている。
**追跡済みの変更 173 file についてはそのとおり**で、実際のソース編集である。
**ただしそれらは既に着地している** — 親が patch を抜いて main へ入れた後の写しが残っているだけである。
逆に、どこにも保存されていない 62 entry の方は、**1 件を除いて再生成可能物**だった。

**つまり `.codex/worktrees/` に溜まっているのは、失われた作業ではなく、着地済み作業の複製である。**

## 8. 本 wave が自分の計測器に見つけた欠陥 (開示)

**この節は隠さずに読まれるためにある。** 親の計測は 2 度作り直した。

### 8.1 取り下げた版 — `--find-object` の偽陰性

`git log --find-object` は**既定で merge commit の差分を作らない**。本 repo は `merge(main): …` を
多用するので、merge 経由で main へ入った blob は「どこにも無い」と誤判定される。
実証: 同じ blob が `-m` / `--diff-merges=first-parent` を付けると merge commit `9f2f8d3a3` に見つかる。
**初版の「着地していない」判定は全部無効**で、v2 で `git rev-parse main:<path>` との直接比較
(O(1)、厳密) へ直した。

### 8.2 残っている欠陥 — 修正版にもある

敵対レビューが v2 からさらに 2 件を見つけた。**本 wave では直さず、開示したまま凍結する。**

1. **`LANDED-HIST` の証拠 commit が無効。** 実例 = `t1338-u1` の `s8b_v2_freeze_fixture.py`
   (blob `a41252dfa…`) を `LANDED-HIST:9f2f8d3a3` と記録したが、その commit の差分は
   `a41252dfa → b3d0c3794` で、**blob は消された側**である。復元先として使えない SHA である。
   ただし消された側の blob は親 commit の tree にあり、その親は main の祖先なので、
   **「main から到達可能」という結論自体は保たれる。** 是正は `ls-tree` による tree 直接照合。
2. **fail-closed でない。** status の rc を見ず、`cat-file` の失敗を「main に path が無い」と読み、
   timeout を `NOWHERE` へ畳んでいた。**検査不能を安全側・破棄側へ倒す作り**だった。
   実装 wave では subprocess ごとに rc を保持し、非ゼロ・timeout・不完全は `UNKNOWN` で停止する。
3. **index にだけある新規 file (`AD`) を `DEL-LANDED` と誤判定しうる。**
   ただし厳密走査で**削除は 67 件中 0 件**だったので、本母集団に該当例は無い。

### 8.3 数え落とし — 未追跡が 13 倍

初版は `git status` の既定で未追跡 directory を 1 entry に畳んでおり、未追跡 file を
**6 件と数えていたが実際は 77 件**だった (`t2566-fix3` の `.tmp/` 1 行の裏に 70 file)。
権威ツールと同じ `--untracked-files=all --ignore-submodules=none` で取り直して確定した。
同条件で**削除 0 件・submodule 汚れ 0 件**も確定している。

### 8.4 証拠価値の無かった検査

初版の「内容 blob が object DB に存在するか」列は**恒真に近い**。親の抽出手順が
子の作業木で `git add -A` を打つため、子の変更は必ず index に入り blob が書かれる。
`git cat-file -e` は常に成功する。**この列を根拠に使ってはならない。**

## 9. 実装 wave が着手前に満たすべき前提

裁定が R1 を是とした場合でも、次が揃うまで実装へ進めない。

1. **全層の対応表** — producer (子を作る全経路) → 永続記録 → 正常終了時 consumer →
   中断時 consumer → 権限 → cleanup → 結果記録 → checker / tests。
2. **既存 CLI が使えないことの解決。** `tools/dev_wave_cleanup.py` の `_assert_clean_and_head` は
   対象 worktree の HEAD が landing tip と一致することを要求する。**子の HEAD は分岐元に留まる**ので
   そのままでは通らない。子の HEAD を親の tested tip と偽って渡す設計にしてはならない。
3. **gate 全体を通る正例 1 件。** 止まる例は実測済みだが、所有・終端・reflog・権限・非占有を
   すべて満たして撤去まで到達する例が 1 件も無い。**「常に保留」は機構を足して何も変えないのと同じ。**
4. **所有 path 抽出集合と子全体の変更集合の差集合**を、救出・明示破棄・保留のいずれかへ必ず振る
   規則。`DW-S05-A` は `-- <所有パス>` で抽出するため、所有外の編集は index にありながら落ちる。
5. **producer 種別の束縛。** `.codex/worktrees/` 配下には Codex manager の wave 本体も入る。
   位置で子と判定しない。
6. **流入を含む完了条件。** 本 wave の走査中にも増えている — 04:55 の 67 件が 05:18 に **71 件**
   (23 分で +4、約 10.4 件/時)。依頼が記録する 12.6 件/時と同じ桁で、**流入は独立に確認できた**。
   処置の完了率がこれを上回らない限り残存数は収束しない。旧対象は固定 cohort として閉じ、
   新規 producer の終端契約を先に効かせる。
   (2 時点の観測であって誤差付きの率推定ではない。また、この移動のせいで
   走査ごとに母集団が異なる — **本書の件数はすべて時点値である**。)
7. **計測器の是正** — 8.2 の 3 件。
