単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2

あなたは段 6 の fix 子 (Codex `role=author`、段 5 実装子契約 DW-S05-A/B/C を全文継承) である。作業 worktree は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-t080-fix1` (branch `impl-dev-wave-t2724-t080-defer-active-v2-fix1`、基点 = 統合 commit `7a763575f` = main `24ede1d11` + 段 5 の実装 13 file)。コードとテストだけを編集する。

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/s4-adjudication.md` — 段 4 裁定 (確定仕様、変異 m0〜m11)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/s6-fix1-findings.md` — **親の fix 指示 (所見の裁定と対応表)。これが本巡の正本**
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/artifacts/dev-wave-t2724-t080-defer-active-v2/s5-author-1.md` — 段 5 実装子の最終報告
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/artifacts/dev-wave-t2724-t080-defer-active-v2/s6-review-a-1.md` — 段 6 レビュー A (正しさ境界)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/artifacts/dev-wave-t2724-t080-defer-active-v2/s6-review-b-1.md` — 段 6 レビュー B (実効性・test 品質)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/focus-nochain-1.log` — chain 無し木の焦点走 (9 failed の assertion 本文は `IZANAGI FAILURE EXCERPT` 節)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/focus-chain-1.log` — chain 有り木の焦点走 (10 failed)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/focus-nochain-2.log` — consumer 回帰 (1 failed)

現物は作業 worktree の path を `grep -n` / `sed -n` で 200 行以内ずつ読む。差分の全体は `git diff 24ede1d11 HEAD --stat` と `git show HEAD -- <path>` で読める。chain 有り木の現物は `git show 229982652:<path>`。

## 権限境界と権威順序

- 権威順序: 親が凍結した契約 (s4 / s6-fix1-findings) > 段 4 裁定 > 段 5 実装。
- **「既存 test」= tracked で land 済みの test (基点 `24ede1d11` にある test)。その期待値は変更しない** (反転・緩和・skip・削除・xfail 化を禁ずる)。赤なら実装側が誤り。期待値が誤りと考えるなら実装を変えず報告して止まる。
- **同じ wave の段 5 が作った未 land の test (7a763575f で追加・変更された test) は本巡の編集対象**であり、s6-fix1-findings の指示に従って直してよい。
- テストの代役 (double) の signature・入力を直すのは許される。**呼び先の signature を検査して安全側の引数を落とすような、production を代役へ合わせて緩める互換分岐を入れてはならない。**
- `git add` / `git commit` / `git stash` / `git checkout` / `git reset` を実行しない (commit は親)。docs を編集しない (`docs/` 配下、handoff、README、runbook を含む)。`output/` 配下の tracked file を書かない・消さない。走査除外・growth hold・allowlist・`clean_scan_digest` の拒否・`_make_gate_decision` の集約・`_campaign_t080_value` の拒否・`launch_validate` の C2-4・`_t080_epoch_identity` の要素を変えない。skip flag / env / 引数で層 2 を無条件免除する経路を作らない。
- 検査対象の機構 (`search_repository`、`_assert_search_pass`、`launch_validate`、`resolve_active_generation`、`verify_receipt` の内部) を monkeypatch しない。新規 test file を作らない。gate・検査・台帳・tool の新設や一般化、互換層を足さない。三軸の値を literal で書かない。
- pytest / `tools/run_tests.py` は走らせられない (sandbox)。走らせていない結果を緑と書かない。

## 自己検証 (必ず行う)

(1) 変更した test module を import し対象 test 関数を直接呼び出して fixture の成立を確かめる (`tmp_path` は `tempfile.mkdtemp()`)。接続 fixture は socket 拒否で直接呼出しできない場合があるので、その場合は「呼出し不能 (理由)」と書き、代わりに fixture 構築の各段 (basis → R → selector seed → protocol → C → G → A → X) を個別に静的検算する。(2) 委譲 predicate の負例は process 内の属性差替えで反実仮想を取る。(3) `git diff --check`、全変更 file の AST parse。(4) 所有外 caller・共有 fixture・consumer test への波及を静的列挙 (`grep -rn`)。(5) 行番号 pin (`test_ccbench_spawn_sites.py` の driver sink 2 箇所) は**最終差分の行番号**で確認する。

**実走と報告を最優先にし、残り時間が少ないと感じたらその時点の結論を出力形式どおりに書いて終わる。無出力が最悪。**

## 出力形式

**出力は file に書かず、最終メッセージの本文に全文を書け。** 見出しはすべて `##` (H2)、最後の節は必ず `## 総括`。

節の順:

## 所見ごとの対応表 (closed / partial / regressed、所見 ID → 変更箇所)
## 実装した変更 (file ごと)
## 接続正例 fixture の結果
## 自己検証の結果
## 所有外への波及
## 変異事前登録への対応 (m0〜m11 の anchor 更新、位置の一意性)
## 未完・未実走・懸念
## 総括
