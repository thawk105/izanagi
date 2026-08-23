---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: stranded-branch-recovery-20260823
seq: 1
title: 取り残し branch 7 本を照合・監査し、3 本を回収 land して 4 本を land しない判定にした (docs のみ、branch worktree-stranded-branch-recovery-20260823)
---

## 本文

- ユーザー依頼: 「取り残しになっている branch の成果を回収して land する。対象は main へ未マージで
  実体のある 7 本。各 branch は着手前に、同じ内容が別経路で既に着地していないかを patch-id と blob の
  照合で確かめる。素性を自分で作っていない差分として内容を監査してから進める。受入と land は
  1 本ずつ区切って行い、merge のたびに `spool_fold --dry-run` を回す。fold の採番予測を確定値として
  書かない。branch の削除はユーザー指示があるときだけ行う」。
- **結果: land 3 本、land しない 4 本。** 依頼は 7 本の回収だったが、監査の結果 4 本は逐語 land すると
  台帳を汚すか正しさゲートを緩めると判明した。判定の基準は {{D:stranded-branch-recovery-criteria}} へ
  記録した。
- 既着地の照合は 3 層で行った — `git cherry` (patch-id)、spool fragment は `docs/spool/FOLDED.md` の
  `content_sha256`、非 fragment file は blob 比較。**7 本目 `worktree-t1458-side-ccbench-provenance-fix`
  (`028a5e2d`) はこれで既着地と判明した。** 差分は spool fragment 1 本だけで、その
  `content_sha256=5aca1641…` が別 branch
  (`worktree-rulings-20260822-ai-performance-measurement-fold`) 経由で D650 として fold 済みだった。
  fragment 本体は fold 後に main から削除されているため、`git diff main...branch` は 18 行の追加に
  見える。path と行数の一致は着地の証拠にならないという依頼の警告が、実物で 1 件当たった。
- 内容監査は branch ごとに read-only Codex を 1 本ずつ立てた (段 3 相当、計 6 本 + 再投入 3 本)。
  共通 charter で 6 面 — 説明と実装の食い違い、consumer 取り残し、恒真な保証、正しさゲートを緩める
  変異、**陳腐化**、指示めいた文字列 — を当てた。陳腐化を主眼に置いたのは先行 wave
  `dev-wave-t949-951-branch-land` (entry 499) の段 8 候補 1 に従ったためで、実際にこれが判定を分けた。
- **land した 3 本。**
  - `worktree-dev-wave-t1486-attempt-binding-siblings` — 段 8b oracle レポートの committed attempt
    束縛検査。監査は 4 段すべてに落ちる負例があること、pipeline 6 段のうち残り 2 段は既存検査済みで
    取り残しの兄弟がゼロであること、manifest の 4 行変更が fixture の SHA 追随だけで受理集合を
    広げないことを確認した。逐語 land。
  - `worktree-dev-wave-t1469-acceptance-lease-timing` — 受入 lease claim 待ちの staleness 実測
    (n=7、待ち中央値約 42 分、6/7 が claim 前 merge を無駄にしていた)。観測の翌日に D662 が待ち行列を
    廃止し D691 が実装から除去したため、decision の「D270 を現行設計として維持する」という宣言は
    現況に反する。実測と観測値は残し、decision の結論を現況へ改め、insight 冒頭へ erratum を足して
    222 行を「歴史記録として有効」「待ち行列と独立に今も有効」「現行運用では誤り」の 3 群へ
    名指しした (D717)。
  - `worktree-dev-wave-lease-cmd-entry-sync` — command 段 6 の lease 文言を D662 / `DW-O27` へ
    整合させる実装 3 file。実装は main へ未着地でいまも必要 (受け取った command 本文自体が旧文言
    だった)。一方、記録が「未了」として登録する runbook 全面改訂は main 側 commit `c5e81e0c` で
    完了済みだったので、decision の結論を現況へ改め新規タスクを取り下げた (D718、F505、[T-1580])。
- **land しなかった 4 本。**
  - `worktree-hazy-munching-kahan` — **絶対規律 2 に抵触**。provenance 全史監査へ「combined diff が
    pure-union なら実装面から除外する」一般則を入れる差分で、**手で競合解消した merge を Codex
    author なしで通す**。正例テストがその形を明示的に固定していた (`git merge` が
    `returncode == 1` を返した競合状態から手で書き直し、Claude author で commit した merge を
    `_commit_paths(merge) == []` と期待する)。親が diff を直接読んで確認した。加えて、この述語を
    main 現行の台帳 53 件へ適用すると後発登録 2 件が `known-violation-stale` になり、全史監査が
    rc=2、land が `RC_PROVENANCE=29` で止まる。却下理由は
    {{D:combined-diff-pure-union-exemption-rejected}}。
  - `worktree-dev-wave-t1447-orphan-hold-races` — 前提が main の再設計で崩れている。差分は
    「単一 output root・並行 dispatch なし・集約 marker 1 個」を前提に hold を `root/orphan-hold.json`
    へ置くが、main は受入 fan-out のため成果物 root と共有 control root を分離し request 別
    `orphan-holds/*.json` を導入済み (親が `tools/pegasus/dispatch_compute.py` の
    `_ORPHAN_HOLD_DIR_NAME` と split dispatch 経路で確認)。差分どおり置けば孤児を見逃し、control 側へ
    置けば正常な兄弟 shard が停止する。**ただし 3 件の競合自体は main で今も開いている** —
    通常 dispatch に qsub 前 claim が無い、hold 書込み失敗が `None` を返す、qdel rc=0 を即
    `job_may_remain=False` とする。要件は [T-1447] が持ち越す。
  - `worktree-dev-wave-t1462-t1464-checkpoint-integrity` — 説明と実装の食い違い。自称は
    「checkpoint 未信頼値の redaction」だが、`_redacted_transport_error()` が落とすのは transport
    receipt の endpoint 値と PBS job id、制御文字、500 文字超の末尾だけで、**checkpoint 由来の
    未信頼文字列は通常 ASCII なら素通りする** (親が実装を直接読んで確認)。記録側は T-1464 を
    `remaining: none` で完了扱いにしており、land すると閉じていない規律 6 の穴が閉じたと台帳へ入る。
    [T-1462] [T-1464] が持ち越す。
  - `worktree-t1458-side-ccbench-provenance-fix` — 既着地 (上記)。
- **fragment の撤回は削除ではなく内容の書き換えで行う。** 陳腐化した decision fragment を削除して
  撤回しようとしたところ、land が fold 段で `landed-fold-owned-path` を返して拒否した
  (`tools/dev_waves/git_state.py` の `_landed_fold_output_path()`)。fragment の削除と
  `docs/spool/FOLDED.md` の変更は fold だけが行う操作であり、wave の commit 区間に現れてはならない。
  迂回せず、両 branch を元の tip から作り直して**内容の書き換え**として撤回し直した。受入全走を
  1 回余分に消費した。
- **b6 の受入 1 走目の赤は自分の変更に帰属した。** `test_dev_wave_command_budget_literal_is_exact` が
  1 件だけ赤 (14,639 passed / 1 failed)。段 6 を 3 行から 1 行へ縮めた結果、入口が 9,584 byte から
  9,520 byte になり、取り残し中に main 側 D704 が引き上げたばかりの予算と食い違った。Codex
  `role=author` が pin 5 箇所 (production 1・テスト 4) を現物へ揃え、閉包が 5 箇所に閉じることを
  全文検索で確認した。焦点走 `orchestrator/tests/test_check_docs.py` は 511 passed / 3 skipped で緑。
  変異は `DW-O19` の一時変異手順で 2 件登録し、最終 commit `daa32280` で再検証した —
  baseline PASSED (511 passed / 3 skipped)、M1 (予算を 9_584 へ戻す) KILLED、M2 (予算を 9_521 へ)
  KILLED、SURVIVED 0、MISMATCH 0。いずれも失敗 node は 1 件で単一理由。復元後の blob は HEAD と一致。
- **codex launcher の evidence 検査が妥当な成果物を再現的に落とした。** 監査子 6 本のうち 1 本
  (b1) だけが 3 走とも `outcome=not_accepted` / `evidence_status=invalid` で成果物を publish
  しなかった。`validator_rc=0` で `## 総括` 形式も満たし、3 走とも同じ結論と同じ blocker を独立に
  述べていた。入力規模とは相関せず (不採用 3 本の input token は 728,508 / 1,578,448 / 1,786,564、
  採用 5 本は 332,362〜2,067,641 で最大の走行は採用)。判定が `do-not-land` という安全側だったため、
  親が決定的な主張 1 件を自分で裏取りして進めた。詳細は {{F:codex-evidence-gate-rejects-valid-output}}。
- **b2 の land 1 回目は外部要因で rc=20 になった。** `main tracked/index/submodule dirt is forbidden`
  で拒否されたが、main 作業ツリーは検査時点で clean だった。並行セッションから、21:08 頃に
  そのセッションの land が fold 段で `.git/index.lock` と競合して rc=28 で止まり rollback も同じ lock で
  落ちたため、main が「ref は旧 main、index と worktree は相手の tip」という状態で一時的に残ったと
  連絡があった (21:20 に復旧済み)。main が clean に戻った後、同じ receipt で land だけを再試行して
  成功した。自分の変更への帰属ではない。
- 回収対象の受入は 5 走 (b2 1 走・b4 2 走・b6 2 走。本 entry を land する wave 自身の走行は別)。うち赤は b6 の 1 走目だけで、他 4 走は
  `verdict=child-green`・`red_nodeids=[]`・`flake_nodeids=[]`。**branch は 7 本とも残した**
  (削除はユーザー指示があるときだけ)。

## 次の一手差分

### 新規

- {{T:codex-evidence-gate-diagnostics}} **P3**: `tools/codex_worker_launch.py` の
  `_evidence_status()` が `invalid` を返したとき、どの条件 (`stdout_invalid` / `stdout_pending` /
  rollout の `invalid` / `pending` / `session_meta_count != 1` / `context_count < 1`) で落ちたかを
  receipt か launcher-diagnostics へ出す。現状は判別材料が成果物に無く、同一 prompt で連続不採用に
  なると再投入以外の手が無い ({{F:codex-evidence-gate-rejects-valid-output}})。
