# [T-2642] 段 4 裁定 — 実装しない (後発として降りる)、設計成果だけ残す

wave: dev-wave-t2642-cleanup-cd-guard
基準 commit: 61e0e9c4a48d08c92526f5026c4cd017b150b898
裁定時刻: 2026-09-16 05:12 JST

## 主裁定: 実装しない。段 5・6 を飛ばし `4→7→8→9`

依頼は「[T-2641] が同じ面を触るので、着手前に稼働 wave の編集面重複を作業ツリーの未 commit まで見て
確認し、重なれば後発が降りる」と定めていた。

- **着手前検査 (≈04:33 JST)**: `git worktree list` の全 74 worktree について
  `.claude/commands/cleanup-branches.md` と `tools/check_docs.py` の未 commit 差分・branch tip 差分を
  取り、**0 件**。`ps` でも T-2641 の稼働プロセスは 0 件だった。この時点では重複が観測できなかった。
- **04:47 JST に T-2641 の稼働を検出**。`ps` に `--wave t2641-cleanup-gate-order` の plan 子が現れた。
- **先後の実測**: `.git/worktrees/` の birth time は
  `dev-wave-t2641-cleanup-gate-order` = **2026-09-16 04:34:10**、
  `dev-wave-t2642-cleanup-cd-guard` = **04:34:38**。**T-2641 が 28 秒先発**。
- 編集面は完全衝突。T-2641 は §1/§2 の手順を再構成し (安い gate 先行・高い gate は残った対象だけ・
  読み取り probe の並列化・`git cherry` は ahead>0 だけ)、`tools/check_docs.py:753`
  `CLEANUP_COMMAND_SHA256` を同時更新する。本 wave の文面案も §1・§2・§3 を触り、同じ定数を更新する。
  両方が land すると、後発は相手の版の上で全文を再縮約し、逐語 pin 7 群を再追従する必要がある。

**よって後発である本 wave が実装を降りる。** 04:52 と 05:12 JST に peer session
`git status parallelization t-2641 [dfcc24]` へ実測データ (pin 閉包・予算・SKILL digest の要否) を
送り、続行を促した。

本 wave の成果物は `output/insights/` と `docs/spool/` だけで、T-2641 の編集面と衝突しない。

## 実装面の差分ゼロ → 変異 matrix 免除、受入全走は実施

`DW-S04` に従う。本 wave はコード・テスト・実行可能物・機械設定を 1 byte も変えない
(成果物は `output/insights/**/*.md` と `docs/spool/*.md` のみ)。変異 matrix は免除。
受入全走は免除されないので段 7 の記録 commit 後に投入する。

## 所見の裁定

### 段 3 sol (安全義務の実効性レンズ) — must-fix 2 件

| # | 所見 | 裁定 |
|---|---|---|
| S1 | 「撤去対象へは cd せず」だけでは、**撤去対象が確定する前の棚卸し中**の `cd` を許す読み方が残る。2026-09-15 の実経路 (§1 の status/untracked 確認で入った) と一致する | **real / 採用せず持ち越し**。文面案の欠陥として insight に記録し、実装 wave への入力にする。禁止対象に「棚卸し候補を含む」と明記する必要がある |
| S2 | セッション cwd の確認方法の制限 (別 cwd を指定した一時シェルの `pwd` では確認完了と扱わない / checker rc0 を退避の証明と扱わない) がプラン本文へ転記されていない | **real / 同上**。文面に載らなければ実行者へ届かない |
| S3 | 「gate 新設なし」は機械 gate の話であって、手順の停止条件は増えている。受理集合の意味では新設に当たる | **real / 裁定パッケージ候補**。機械 gate は変えず共通手順の停止条件だけを明文化することを許すかは、実装 wave の段 1 で親が明示的に裁定すべき |

### 段 3 sol — 親の実測値への反証

親 brief の (P1) 「既存 `check_worktree_occupancy.py` で足りる」は **一部 refute された**。

- confirm: checker は自己 PID の cwd を除外しない (`:586` が全列挙 PID を走査、`:453` の自己除外は
  cmdline だけ)。`seen = {self_pid}` は祖先探索の循環防止であって cwd 走査の除外ではない。
- **refute**: 「対象内に居れば必ず rc=1」は成立しない。rc0 になる経路が 4 つある —
  (i) 別 PID namespace の process、(ii) cwd 読取権限不足 (`:403` は非阻害診断)、
  (iii) `resolve(strict=True)` の PermissionError (`:422` は非阻害)、
  (iv) 対象外の deleted cwd (`:430`)。加えて対象自体が不存在・非 directory なら `invalid-target` で
  rc2 (`:533`、`:716`)。**rc0 は進入防止でも退避証明でもない。**
- よって (P1) は「新しい checker は作らない」までは維持できるが、「既存 checker だけで足りる」は
  言い過ぎ。文面側で「rc0 を退避の証明として扱わない」を明示する義務が生じる (= S2)。

### 段 3 luna (pin 閉包・予算レンズ) — must-fix 0 件、nit 2 件

| # | 所見 | 裁定 |
|---|---|---|
| L1 | 親の 10 アンカーは pin 閉包の全数ではない。独立した逐語依存が **7 群**ある (`commit graph` の一意性 / `## 4. 事後検査` の見出し / §2 見出し全文の一意性 / checker 呼出し〜「停止。」の部分逐語 / F26 住所表現 / description 行全文 / `CLEANUP_COMMAND_SHA256` の代入書式) | **real / 採用**。親の閉包主張を訂正する。05:12 JST に T-2641 へ追送した |
| L2 | 「3 file を 1 本の author へ」は担当分割であって commit 分割の指定ではない | **real / nit**。実装しないので本 wave では発火しない。実装 wave の段 1 で確定させる |

### 段 3 luna — 親の実測値への検算

- **予算**: プランの byte 算術は独立検算と一致。改訂後 **5897 bytes / 84 行 / 最長 105 文字**、
  末尾 LF あり、CR なし。予算余りは 3 bytes。110 は `len(line)` の文字数判定であり byte ではない
  (プランは取り違えていない)。
- **pin 閉包**: 親の 10 アンカーは全数でない (L1)。ただし **command の固定行番号・総行数を assert する
  pin は 2 file 内に存在しない**ことも実測された (行番号・数値・digest・値文字列で検索)。
  81 → 84 行の変化自体は赤にならない。
- **SKILL digest**: command だけを変えた場合に `CODEX_CLEANUP_BRANCHES_SKILL_SHA256` の更新が要る
  経路は無い (`tools/check_docs.py:5183`・5219 は SKILL 自身の文字列だけを hash、command は 6571 で
  別に hash する)。**依頼文が「2 定数の同時更新」を編集面としていた点は、実測で 1 定数に訂正される。**
- **「74 worktree で重複 0 件」**: luna は再現手順が brief に無いことを指摘した。**real**。
  本裁定では手順を明記した (上記「着手前検査」)。ただし **この検査法自体が不十分だった** —
  相手が worktree を作った直後・編集前だと差分も `ps` も 0 件になる。先後の判定には
  `.git/worktrees/*` の birth time か `ListAgents` の peer 一覧が要る (段 8 の改善候補 2)。

## 持ち越す成果 (実装 wave への入力)

1. 文面案 (§1 冒頭へ進入禁止 1 行 68B、§1 31-32 行と §2 41-42 行の縮約で 108B 捻出、
   §2 46 行の退避指示を §3 へ移設・強化 143B、改訂後 5897 bytes) — ただし S1・S2 の是正が要る。
2. pin 閉包 17 群 (親の 10 + luna の 7) と、それぞれの破損時の症状。
3. checker の rc0 が退避証明にならない 4 経路 (段 3 sol の反証表)。
4. S3 の裁定 (機械 gate を変えずに手順の停止条件だけ増やすことの可否)。

## 裁定パッケージ (ユーザー裁定へ返す項目)

1. **S3**: `/cleanup-branches` の手順に、機械 gate (checker の rc) と独立した停止条件
   (「セッション cwd が対象配下または不明なら停止」) を置くことを許すか。許す場合、
   その停止条件は機械的に検証されない (実行者の遵守に依存する) ことを明記する必要がある。
2. **観測不能な harness まで含めた機械的保証**を求めるか。求めるなら checker か実行基盤の変更が要り、
   [T-2642] の scope を超える。D821 が既に「観測ベースの discharge は正の証拠でしか作れない」と
   裁定しており、lease 等の正の証拠と対で入れる必要がある。
