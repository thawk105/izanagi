単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- 作業 root (read-only。実装が入っている木): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2`
- **本 wave の全差分**: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/wave-full.diff`
- **親の段 4 裁定 (受入基準の正本)**: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s4-adjudication.md`
- **親がユーザーへ返す裁定パッケージ**: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/ruling-package.md`
- 契約の正本: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md`
- 過去の失敗の型: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/failures.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/CLAUDE.md`

# 段 6 敵対レビュー B — 閉包・帰属・射程の正直さ

**実装を守らせない。壊しに行く。** 対象は段 2 の plan ではなく**実際に入ったコード**である。

作業 root は read-only で書込み可能な tmp が無い。**pytest 緑を要求しない。**
静的読解と grep による実測だけで結論を出す。**走らせていないものを緑と書かない。**
**file を 1 つも作れない。成果物は最終メッセージの本文へ全文を書くこと。**
予算が尽きそうなら**途中結論を出力形式どおりに書いて終わること** (無出力が最悪)。

## 親が実測済みの事実 (再測不要。誤りと判れば指摘すること)

- 対象 3 file (`test_s8b_floor_stats` / `test_s8b_floor_campaign` / `test_s8b_terminal_evidence`)
  の親による独立実走: **675 passed / 3 skipped / 0 failed**。
- runner の 2 file: **70 passed / 0 failed**。
- `FORMULA_ID` は変更していない。改版要否はユーザー裁定へ返してある (裁定パッケージ参照)。

## このレンズが見るもの — 閉包・帰属・射程

1. **pin 閉包が本当に閉じたか。**
   rep 証跡が 7 key になったことで赤くなるはずの箇所を、**自分で全部見つける**こと。
   識別子検索だけでは閉じない。**file 全体の sha256 golden・件数 assert・AST 走査・
   exact frozenset・canonical bytes の literal** を別々の手で探すこと。
   - `orchestrator/tests/test_official_perf_closure.py` の
     `_REVIEWED_PERF_FILES` (`:44`) / `_production_perf_files()` (`:533`) / 集合等値 (`:905`)
   - `orchestrator/tests/test_t671_source_binding.py` の 63 path exact tuple と件数 (`:267-269`)
   - `orchestrator/tests/test_frozen_artifacts.py` の `FROZEN_MANIFEST`
   - `missing_perf_events` / `rep_observations` / `execution_failure` を参照する全 file
2. **consumer 取り残し。** 6 key を前提に書かれた読み手のうち、
   本 wave が触っていないものを列挙すること。
   `_derive_rep_integrity()` の返値 arity が変わったので、**全 callsite を自分で再走査**すること。
3. **射程の正直さ。** 親は成果物に「実環境の値域を供給した」と書かないと決めている。
   **差分と裁定パッケージのどこかに、測っていないものを測ったと読める記述が無いか**を探すこと。
   とくに commit message と test 名と docstring を疑うこと。
4. **`FORMULA_ID` を据え置いたまま診断 counter が変わることの扱いが正直か。**
   親は characterization test で差分を exact に固定したと主張している。
   **その test が本当に差分を固定しているか、それとも恒真か**を検査すること。
   直積の網羅範囲が縮められていないかを数えること。
5. **成果物影響 (DW-G05)。** 本 wave の各変更について、
   放置したとき成果物 (certified 選択・レポート・台帳) の値・受理集合・参照が
   どう変わるかを 1 行で言えるか。言えないものは nit へ落とすこと。
6. **変異の照準。** 親の段 4 裁定 7 節の変異事前登録について、
   **実装後のコードで単一理由性が成立するか**を検査すること。
   「新しい前段をすべて通り、対象述語だけを外すと受理される入力」が実在するかを、
   実装後のコードで確かめること。成立しないものは名指しすること。

## 実装面の著者

**実装面のハンクに Codex `role=author` が無いものがあれば、レビューで代替せず停止して報告すること。**

## 過去の型の再発検査

`docs/failures.md` の型タグを攻撃面に含めること。とくに
**説明と実装の食い違い・consumer 取り残し・恒真な保証**を疑うこと。F 番号を引くこと。

## 禁止

- 実装を擁護しない。「概ね妥当」で終わらない。
- file を作らない。`git` の状態を変えない。
- 走らせていないテストを緑と書かない。
- 出力に結合文字 U+0300〜U+036F を使わない。

## 出力形式 (この見出しをこの順で使う。本文へ全文を書く)

## pin 閉包の残り (file:line)
## consumer 取り残し
## 射程の正直さ — 測っていないものを測ったと書いていないか
## characterization test は恒真か
## 成果物影響を言えない変更
## 変異の単一理由性
## 過去の型の再発
## blocker と nit の仕分け
## 総括
