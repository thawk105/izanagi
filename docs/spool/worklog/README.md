# worklog fragment

`docs/worklog.md` の 1 エントリ分。共通規則は `docs/spool/README.md` を正本とする。

本文の H2 は **`## 本文` と `## 次の一手差分` のちょうど 2 つ**、この順でなければならない。

```markdown
---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-02
wave: dev-wave-parallel-docs-spool
seq: 1
title: 並行 docs 衝突を spool + fold で解消する (コード + docs、branch ...)
---

## 本文

- ユーザー裁定・協議の決着、棄却 finding、セッション異常、エージェント工数など
  **git に入り得ない情報だけ**を書く (`docs/worklog.md` 冒頭の書式契約に従う)。
- 設計判断は {{D:parallel-doc-spool}}、失敗は {{F:partial-fold}} のように参照する。

## 次の一手差分

### carry

- [T-298]

### 完了

- [T-288] 単位修正を完了し、受入結果を記録した。
  remaining: none
  base: <対象 item の現本文の sha256>

### 更新

- [T-304] **P1・ユーザー裁定待ち**: 二択に第三案を足して再提示する。
  base: <対象 item の現本文の sha256>

### 新規

- {{T:fold-crash-recovery}} **P2・新規**: fold の crash resume を追加監査する。

### 見送り

#### プロセス文書系

- [T-305] live role 文面の整理 — 理由: 多世代開放まで発火しないため別 wave 所有とする。
  base: <対象 item の現本文の sha256>

### 見送り追記

- [T-059] 2026-08-02 に D128 で再発火。追加裁定はせず記録のみ。
```

## 規則

- **`carry` 節は任意である。** 触れなかった active な T は fold が自動的に carry する。
  item は ID だけの 1 行 (`- [T-NNN]`) とする。
  **明示 carry と暗黙 carry が同じ出力を生むのは、fold の時点でその T がまだ active なときに限る。**
  fold は明示 carry を `完了`/`更新`/`見送り` と同じ「active な item への操作」として扱うので、
  別 wave が先に land してその T を `完了`/`見送り` で active から外していると、fold は
  `transition-target` (active でない操作対象) で止まる。この停止は land lock の内側で起き、
  受入全走を通した後に初めて分かる。作業木に取り込んでいない main 側の完了・見送りは
  `--dry-run` にも映らない。暗黙 carry にはこの失敗が無い (非 active な T は走査に現れないだけ)。
  したがって並行 wave では、自分が `完了`/`更新`/`見送り` に置かない T を `carry` へ列挙しない
  (節ごと省く) のが安全側である。同一 fold 内で先に適用された別 fragment が外した場合も同じ (F233)。
  暗黙 carry は並行 wave のために必要である — 他の wave が新しい T を先に fold しても、
  先に書かれた fragment がそれを知らないまま畳める。
- 脱落は fold の**保存則 postcondition** が塞ぐ。
  「出力 active 集合 == 入力 active 集合 − 完了 − 見送り + 新規」を実際に突き合わせて検査する。
- `完了` は**残件なしの終端**にだけ使う。部分完了は `更新` に書く。
  - **`  remaining: none` を 1 行必須とする** (値は `none` だけ)。語の不在ではなく構造 field で
    終端性を判定するためであり、書き手に明示的な宣言を求める。
  - この行は **item 末尾から連続する機械 field 行** (`base:` と同じ枠) の中になければならない。
    本文中・fenced code block 内・HTML comment 内に同じ形の行を書いても field とは数えず、
    欠落として拒否される。
  - 本文に「残件あり」「一部完了」を含む `完了` は従来どおり拒否される。
  - **どの ID を `完了` に置くか**: 依頼が名指す active T に加え、本文が「実装した」「閉じた」と書く
    作業に対応する active T を全て置く。作業を裁定の項番号 (例: D2104 項 33) で書いたときは、その項を
    引く carry の T へ写す。同じ wave で実装した兄弟項も同時に置く。fold は保存則どおり触れなかった T を
    永久に運ぶので、ここで閉じ損ねると済んだ作業が次の依頼として再起動する (F428)。
- `見送り追記` は見送り台帳の**既存項目へ 1 行を追記する**任意節。台帳の慣行 (何を書くか) は
  変えない — 書く手段だけを与える節である。
  - `見送り` が無くても `見送り追記` 単独でよい。**両方あるときだけ `見送り` の後**に置く。
    使わないなら節ごと書かない (空の `見送り` / `見送り追記` を置くと拒否される)。
  - item は `- [T-NNN] <追記本文>` の 1 物理行だけ。`base:` と H4 と継続行は付けない。
    追記本文は空白以外を含む必要がある。
  - 追記は対象 item の**先頭行の行末**へ入る。対象が無い・可視な重複がある・
    同じ追記が既に入っている場合は拒否される。
  - **日付・発火回数・「発火記録:」は書き手が本文に書く。fold は補わない。**
  - 追記本文の placeholder は fold 時に解決される。
- `完了` / `更新` / `見送り` の item には **`  base: <sha256>`** を 1 行付ける。
  対象 item の現本文の digest であり、これが一致しないと fold は停止する。
  対象が carry stub (`- [T-NNN] (N)`、凍結済み過去エントリでは `- [T-NNN] 変わらず ((N) 参照)`)
  のときに fold が照合するのは
  **stub 自身の digest ではなく、carry 鎖を遡った実体 item の digest** である。
  別 wave が先に同じ項を書き換えていた場合に、古い本文から作った更新で上書きするのを防ぐ。
  この digest は `python3 tools/spool_fold.py --base-digest '[T-NNN]'` で読み取り専用に取得できる
  (非 carry item にも使える)。fold の受理・land 検証を代替する gate ではなく、値の lookup だけを行う。
  **この lookup は起動した作業木の台帳を読む。** wave の作業木は wave 開始時点で止まっており、
  その間に別 wave が同じ item を書き換えていることがあるので、**digest は land 先の
  local main の現物に対して取る**。作業木の値で書くと fold が停止する。
  **base は 1 fragment 内でしか連鎖しない。** 同じ branch 上の連続した wave が同じ item を
  `完了`/`更新`/`見送り` に置くと、後発の base が先発の適用後の本文と一致せず `base-mismatch` で
  止まる。**次の一手は後発の fragment へ 1 度だけ書き、先発側は `carry` へ直す** (2026-09-03 実測)。
  **wave 用 worktree を作る前に main の作業木で取っておけば、以下の借用は要らない。**
  背景 job のように worktree 隔離から始める wave では、隔離の前に lookup を済ませるのが最も安い。
  main を取り込まずに取るなら `docs/worklog.md` だけでは足りない。carry 鎖が
  過去エントリを指すため `docs/archive/` も同時に借りないと `carry-reference` で
  invalid になる。`git checkout <main> -- docs/` で一式を借り、lookup 後に
  `git checkout HEAD -- docs/` と、main にだけ在る path の除去で作業木を戻す。
- `見送り` は `docs/phase3.md` の見送り台帳に**実在する H3 名**を H4 として指定し、`理由:` を必ず書く。
- item の継続行は 2 space インデントにする。
- エントリ番号・日付・carry stub `- [T-NNN] (N)` の N は **fold が付ける**。fragment に書かない。
- `title:` の先頭に `[T-NNN]` を書けるのは、その ID が同エントリの `次の一手差分` で
  `完了`/`更新`/carry のいずれかとして扱う既存 active item であるときだけ。次の一手として
  一度も登録されていない wave 自身 (ユーザーが直接起票した課題等) を、fold 未実行時点の想像で
  数字を割り当てて `title:` へ書いてはならない。fold が別の `新規` item へ同じ番号を独立に
  割り当てうるため、見出しの番号がそのエントリ自身とは無関係な後続 item を指す食い違いを生む
  (2026-08-21 実測)。該当しない場合は角括弧 ID なしで題を書く。
  **同じ理由で、wave slug と branch 名にも未採番の T 番号を使わない。** `title:` は慣行として
  branch 名を含むため、branch 名に置いた想像の番号がそのまま見出しへ入る (2026-09-02 実測)。
  該当しない wave は主題だけの slug にする。
