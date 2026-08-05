---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-t487-design
seq: 1
title: [T-487] grace 予算に依存しない変異復元を設計起草した — 転換は既存 D/A doctrine の適用に還元でき、裁定軸 10 本を返す (docs のみ、branch worktree-dev-wave-t487-design)
---

## 本文

- **中心結論: この転換は新しい耐久化方針の提案ではなく、既存 doctrine の適用である。**
  `docs/orchestrator-design.md` §D/§A (ログ先行 + append 毎 fsync、commit record なき評価は
  復旧時に破棄、状態を保存せず入力だけから id を再現) に campaign 層は既に従っており、
  正準実装 `orchestrator/campaign/wal.py` の `append` は tail-gate・完全 write・file/dir fsync・
  慎重な close まで持つ。`docs/spool/` の fold は修復側の契約 (冪等・transaction・
  第三の状態で停止) を既に定式化している。**`mutation_harness` は共有状態 (checkout) を
  書き換える唯一のコンポーネントでありながら、この doctrine から唯一外れている。**
  ユーザーに問うべきは「新方針を採るか」ではなく「例外を続ける理由があるか」になった。
- **段 2 の最重要指摘 (親の分析になかったもの): journal + fsync + 再開時修復の 3 点では足りない。**
  現行の変異・復元はどちらも `Path.write_text` = in-place truncate + write であり、
  途中で死ぬと**部分 bytes** が残る。部分 bytes は hash では人間の編集と区別できないため、
  修復器が「触ってよい file」を判定できない。**4 点目「原子的 target 置換」が必須**である。
- **段 3 の敵対 2 レンズ (A=耐久性 15 所見 / B=安全性・射程 12 所見) は両方とも「採用不可」判定。
  親は 27 所見すべてを real と裁定し、refuted はゼロ。** 両レンズが独立に到達した致命所見:
  (1) **quiescence の欠落** — durable lock の解放は runner・dispatch job の死を証明しない。
  login ノードの harness だけ OOM kill され計算ノードの job が生き残ると、修復して `clean` を
  書いた後に生存 child が再汚染しうる。(2) 一般 worktree の自動修復は破壊的 (byte 単位で一致する
  人間編集と TOCTOU は識別不能)。(3) 自由値の state root は split-brain を作る。
  (4) `AttemptJournal` を基礎にすると `wal.py` が既に持つものを作り直し三方言が並立する。
- **親自身の分析の誤りを 2 件、レンズが突き、親が一次資料で検算して採用した。**
  (a) **「予算の 3 桁下」は 10 s 清掃予算に対しては誤り** — `10/0.07179 = 139 倍 = 2.14 桁`。
  3 桁になるのは nominal grace 60 s に対して (836 倍 = 2.92 桁)。以後どの予算に対してかを
  書き分け、裸の「3 桁下」は使わない。(b) **`_assert_clean_tracked` は全 dirt を検出しない** —
  worktree に ignored file を 1 つ置いて実測したところ、harness と同じ
  `git status --porcelain=v1 --untracked-files=all --ignore-submodules=none` は**出力ゼロ
  (clean 判定)**、`--ignored` を足すと現れた。`*.o`/`build/`/`*.so` のようなテスト結果を
  左右する生成物と skip-worktree entry に盲目である。probe は撤去し木の clean を再確認した。
- **`git replace` refs が P1 を破ることも実装で確認した。** `_git_env` は `GIT_*` を濾過するため
  `GIT_NO_REPLACE_OBJECTS` も落ち、replace は有効なまま残る。一方 git 呼出しは
  `--no-replace-objects` を渡していない。よって `refs/replace/<記録 HEAD>` を作れば
  `rev-parse HEAD` は一致したまま `git show` が別 blob を返す。
- **転換が消す grace 依存の射程を限定した。** 消えるのは木の汚染依存だけで、しかも
  durable repair + quiescence + consumer quarantine が実装され**実機受入されてから**である。
  子 process の後始末は quiescence lease へ置換できるが消えない。`H_head` は意味検査として残る。
  → **D130 条件 3 を「T-487 の設計を採用した」だけで closed にしてはならない。**
- **親の暫定裁定は P1 修正採用・P2 採用 (強化)・P3 撤回・P4 修正採用・P5 採用 (不足あり)。**
  P3 (変異後 hash 一致 file だけ触る) は必要条件だが権限の証明にならないため撤回した。
  P5 の「何もしない」は単独では安全でなく、**無書込 + checkout の durable quarantine +
  sanctioned consumer の fail-stop** が要る。
- **親が自分で候補を反証した例:** journal を git admin dir (`--git-dir`) へ置く案は発見可能性が
  最も強く `git status` にも映らないが、`git worktree prune` や worktree 削除で
  **journal だけ巻き添えで消える**。汚染された作業木を残して記録が消えるのは現状より悪いので却下した。
- **`DW-G03` を適用して一般化を止めた。** consumer 協調契約の族一般化には独立 2 例が要るが、
  明示できる exact pair は `mutation_harness → run_tests / 受入投入` の 1 件だけである。
  今は当該 1 pair の局所修復に留め、一般化は第二例かユーザーの例外裁定を待つ。
- **段 8 自己改善: 候補 2 件を実測し、1 件採用・1 件は予算で阻まれて裁定へ回した。**
  採用分は `docs/spool/README.md` の運用手順 — fragment の `base:` を 1 文字壊して両検査に
  かけたところ、正本が指示する `check_docs.py` は **rc=0 で通し**、
  `spool_fold.py --dry-run` だけが `base-mismatch` を返した (変異は `git checkout --` で復元し
  木の clean を再確認)。base が古いまま land すると fold は land の協調 lock の**中で**赤になる。
  回した分は `DW-S01` への「再利用先も性質で検索した正準実装で特定する」追記で、
  **`docs/dev-wave/**` の合計上限 25,200 bytes に対し既存が 25,198 bytes、余裕 2 bytes** のため
  収まらなかった。予算値の引き上げは通常の自己改善に含めない規約に従い、編集を撤回した。
- **射程:** 本 wave は実装ゼロ・実測ゼロの docs-only であり、段 4 で「実装しない」と裁定して
  `4→7→8→9` とした。**実装差分がないため変異 matrix と受入全走は対象外である。**
  受入は `python3 tools/check_docs.py` (違反なし) のみ。
- エージェント工数: codex 3 本 (段 2 プラン 1、段 3 レンズ 2)。claude 子なし。計算資源: 未使用。
  親の独立解析メモ 10 件 (N1〜N10) を段 3 レンズへ明示的に渡した。
- 逐語 = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t487-restore-design/`
  (brief.md / s2-plan.md / s3-lensA.md / s3-lensB.md / s4-adjudication.md /
  parent-independent-notes.md)。

## 次の一手差分

### 完了

- [T-487] grace 予算に依存しない変異復元設計を起草し、裁定パッケージを返した。設計は
  `docs/mutation-restore-durability-design.md`、裁定軸 10 本は同書 §9、
  裁定がどう転んでも満たすべき必須条件 6 点は §9.1 が正本。
  remaining: none
  base: a938807ec7551cad5fb3dd90a9ecb9b7add89c2af6c3828b166baff0f303c249

### 更新

- [T-486] **P1・ユーザー裁定待ち ([T-487] 起草完了により論点が確定)**: [T-360] 条件 3 を
  閉じる probe leg の扱い。[T-487] の設計は「転換が消すのは木の汚染依存だけで、それも
  実機受入の後」と射程を限定したため、**設計採用だけで closed にはできない**。
  推奨は `deferred` (実装と実機受入まで保留) であり、転換が実機受入まで到達しなければ
  probe leg は再び必要になる。裁定軸は `docs/mutation-restore-durability-design.md` §9 の U-9。
  base: c62c880831a12187c09f6c8bf4696dda5d8977cbab35ebb7853c715dd6f7d7c4

### 新規

- {{T:mutation-restore-durability-impl}} **P1・新規・ユーザー裁定待ち**:
  変異復元の耐久化を実装する。着手は `docs/mutation-restore-durability-design.md` §9 の
  U-1〜U-10 の裁定が前提。裁定後もまず `DW-G01` の生死確認実験 (§8.1、100 行以内の
  使い捨て driver、SIGKILL leg と node-death leg) から始め、
  **journal だけ残って target が部分 bytes になるなら NO-GO** とする。
  必須条件 6 点 (§9.1) を満たさない実装を「転換完了」と呼ばない。
- {{T:clean-gate-ignored-blindness}} **P2・新規**: `_assert_clean_tracked` の盲点を塞ぐ。
  実測で確認済み — harness と同じ `git status` 引数は **ignored file を報告せず**、
  skip-worktree / assume-unchanged entry にも盲目である。`*.o`/`build/`/`*.so` は
  テスト結果を左右しうるため、cleanliness gate が「測定は汚染されていない」を
  主張する根拠として不足する。`--ignored` の追加と `git ls-files -v` による
  skip-worktree 拒否、および ignored 生成物の受理集合の明示が要る。
  [T-487] の修復器設計もこの盲点を継承してはならない
  (`docs/mutation-restore-durability-design.md` §10)。
- {{T:dev-wave-budget-headroom}} **P3・新規・ユーザー裁定待ち**: `docs/dev-wave/**` の
  byte 予算に空きが無い問題を裁定する。実測で合計 25,198 / 上限 25,200 bytes、**余裕 2 bytes**。
  本 wave の段 8 で実害のある是正 ([T-487] で brief の不変条件が正準でない実装を参照先に
  指名し、段 3 の両レンズが「brief 自身の不変条件に抵触する」と指摘した — `DW-S01` へ
  「再利用先も性質で検索した正準実装で特定する」を足す案) が、この上限で入らなかった。
  予算値の引き上げは通常の自己改善に含めない規約なので撤回してある。選択肢は
  (a) 陳腐化した L2 節の削除で空ける (削除の実施はユーザー裁定に限る)、
  (b) 上限の独立審査、(c) 当該規律を諦める。**(a) を推奨**するが、
  削除候補の選定には「発火実績なし × 機械検査で義務代替済み」の両条件検査が要る。
