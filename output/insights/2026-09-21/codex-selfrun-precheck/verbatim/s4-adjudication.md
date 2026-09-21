# 段 4 裁定 — codex 子の login self-run precheck (2026-09-21 08:1x JST、親)

入力: 段 1 brief (`brief.md`)、段 3 consult 1 本 (`codex/s3-consult-out.md`、gpt-6-astra / medium、所見 11 件、高 5)。

## 所見の裁定 (real / refuted、採否)

| # | 所見 | 判定 | 採否・扱い |
|---|---|---|---|
| 1 | 案 A を「迂回でない」とする根拠が不足 (hook 非拒否 ≠ 規律上実行可) | real | 採用。裁定パッケージは「hook の射程」と「login 実行の許可 (admission 外)」を別の欄に分け、後者はユーザー裁定。案 A は条件付き候補、既定 (裁定前) は案 B |
| 2 | 「1 file・数秒・数十 MB」を新設・変更 file 一般へ一般化できない (T-2814 は 1 file 580 件 302 秒) | real | 採用。案 A の文に資源除外文を足し、「天井に対し無視できる」を削除。MAXRSS は単一 process の代理値と明記 |
| 3 | コマンド 7 (`run_tests.py`) は local scope / dispatch へ進みうる | real | 採用。削除。rc=16 は T-2792 / T-2803 の引用に留め「今回の sandbox では未測定」 |
| 4 | 「新設 test file は自走できることが契約上保証」は誤り (meta-test は文字列 signal のみ) | real | 採用。文を置換 |
| 5 | コマンド 6 (子に `-m pytest` を試させる) は証拠設計が弱く、不発火時は実走してしまう | real | 採用。削除。hook 発火の live 証拠は正規の計器 `tools/check_codex_hooks.py` (allowed / protected control) で親が取り、pytest 綴りの拒否は静的判定 rc=2 で示す |
| 6 | fixture の代表性は部分的 (tmp・git・subprocess は含む、socket・`/run/user` は未測定) | real (限定) | 採用。README に「既存 3 harness における tmp・git・subprocess を含む実行例」と限定 |
| 7 | 「編集ゼロ」の定義と確認手段 (ignored の pyc / cache、`wc -l` の rc) が噛み合わない | real | 採用。禁止対象を「作業 repo のソース・index・HEAD」に限定し、fixture の一時 repo 操作を区別。前後で HEAD と `git status --porcelain=v1 --untracked-files=all` を rc 付きで取る。ignored bytes 不変は主張しない |
| 8 | 「往復 1 巡削減」は断定が強い | real | 採用。「変更 test 自身で再現する fixture / assert 誤りを先に見つけられれば往復を減らせる可能性がある。頻度・削減時間は未測定。7〜26 分は別走種の待ち込みの参考値」へ置換 |
| 9 | fix 子は役割別の再現確認であって独立 2 例ではない。author 1 本で足りる | real | 採用。fix probe は走らせない。author / fix の起動 argv は `--dry-run` で stage 名と job-id 由来の path 以外同一 (`codex/dryrun-{author,fix}.txt` の diff、sandbox=workspace-write、max-model-calls 100) を README に記す |
| 10 | 案 A〜D は「全件承認」の形でない (A/B 排他、C 不採用、D scope 外) | real | 採用。「今回の裁定対象は A か B の択一、C は不採用、D は今回対象外 (将来の択として記録)」と明記 |
| 11 | 報告形式が機械的でない | real | 採用。コマンドごとに固定欄 (`attempted` / `started` / `process_rc` / `hook_verdict` / `wall_s` / `maxrss_kb` / `executed_count` / `evidence`)、未取得は `null` |

(P1) conditional → probe で「現在の exact な子経路・対象での rc / 所要 / 変更状態」だけを測る (能力の初発見とは書かない)。(P2) refuted → 案 A の対象を「新設・変更 file のうち親が許可根拠を明示できるもの」に縮め、資源除外文を足す。(P3) conditional → `-c pytest.main` の不採用は維持、「F121 同族」は推論と明記。(P4) conditional → 効果量の文を置換。(P5) conditional → 境界を本 wave で定義しない方針は維持。

## probe の授権と限定

- probe 自体の授権: ユーザー依頼 (「実装差分ゼロの probe で実測」) と、親の対照走 (同 3 file が login で 1.5〜3.4 秒 / 35〜57 MB、D2195 が親に許した形) による。子が走らせる対象は既存 3 file (a)(b)(c) に固定し、新設 file 一般へは広げない。
- 削除: コマンド 6・7。追加: 前後の HEAD / status を rc 付きで、`/usr/bin/time` の可否を事前確認 (不可なら未取得、別 wrapper で再試行しない)。
- 子の禁止: 作業 repo のソース・index・HEAD を変える操作 (file 編集、`git add/commit/stash/checkout/reset/worktree`)。test の fixture が tmp 内で行う git 操作は対象外。

## プラン v2 (段構成)

段 5 = author probe 1 本 (unit worktree `selfrun-probe-unit` @ `5efd69367`、prompt v2)。親は並行して `tools/check_codex_hooks.py` を live 実行 (hook 発火の正規計器)。段 6 = 親の README 後に read-only review 1 本 + 焦点再レビュー。段 7 = insight + spool fragment (worklog)。段 8 → 段 9 (受入 1 走 + land)。

## 変異事前登録

実装なし (docs / insight のみ)。登録する変異は 0 件。
