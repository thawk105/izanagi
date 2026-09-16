---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-next-tasks-codex-authority
seq: 1
title: /next-tasks の codex 相談規定を「事実は claude・判断は codex」の役割分担へ書き換えた (command + 実 bytes pin、branch worktree-dev-wave-next-tasks-codex-authority、変異 matrix = baseline PASSED・KILLED 2・SURVIVED 0・MISMATCH 0・期待 node 完全一致)
---

## 本文

- **ユーザー是正を受けた wave である。** 逐語は「codex の方が基本的に賢いモデルを使っている。
  だからそちらの判断のほうが影響力強い期待がある」。裁定内容と却下案は
  {{D:next-tasks-fact-claude-judgment-codex}}。
- **直した対象の実測。** 同日の `/next-tasks 10` で claude の採用 10 件と codex の上位 10 件が
  一致 4・不一致 6 になり、claude が押し切った。弱かったのは 2 経路で、(a) codex が「研究を
  止めている証拠がない」として外した 3 件を、claude は同意と書きながら 10 件の枠を満たすため
  順位を下げて残した、(b) codex が下位に挙げて自ら「機構実在は未確認」と書いた 3 件を、claude は
  実測せずに外して自分が見つけた候補と差し替えた。codex の見解が結論を変えたのは 1 件だけだった。
- **旧規定は「独立に評価する。右から左に流さない」だった。** これが止めなかったのが要点である。
  独立評価の要求は、結果として claude の単独決定と同じ出力を許す。権威の所在を書いていなかった。
- **段 3 の 2 レンズが独立に同じ中核欠陥を出した。** 「実測で示せるときだけ覆せる」は制約に
  ならない — claude は repo をいくらでも実測できるので、判断と無関係な実測を口実にできる。
  両者の是正は同じで「その判断の**前提事実**を反証する実測」。この一致は、片方のレンズだけでは
  親の provisional 裁定 (P1-a) を通してしまったことを意味する。
- **棄却した所見はない。** 段 3 の 9 件と段 6 の 3 件はすべて real として採った。段 6 の 3 件は
  いずれも新しい権威分担と既存規定の矛盾で、出力形式の並び順が独自の第三キー (所要の小さい順) を
  持っていたこと、母集合の収集節が「枠へ入れる」と書いて採用と読めたこと、除外候補の不一致
  開示先が出力形式に無かったことである。**新しい規定を足すと、既存規定の言葉遣いの緩さが
  抜け道に変わる。**
- **byte 予算は 46 bytes しか無かった** (上限 27,100 に対し着手前 27,054)。上限は上げず、日付付き
  逸話 4 件 (main 再取得・carry 着地・実走可能・三点 diff) を圧縮して相殺した。4 件とも義務は
  本文に残し、SHA・件数内訳・task ID 列挙などの詳細だけを落とした。段 6 レビューが 4 件とも
  「維持」と判定している。着地 26,903 bytes = 残り 197 bytes。
- **段 2 の byte 収支は親が全件検算した。** 現行側 375 / 204 / 553 / 669、置換側
  476 / 272 / 172 / 536 / 229 がいずれも申告と一致した。子の算術を鵜呑みにしていない。
- **受入 attempt 1 が赤を返し、段 1 の pin 閉包の漏れを暴いた。** 落ちたのは
  `test_next_tasks_command_budget_literal_is_exact` 1 件 (23960 passed) で、本 wave に帰属する。
  同 test は実 bytes を `27_054` の literal で pin していた。**漏れた原因は
  `git grep ... | head -40` の `head` が 40 行で切り、`orchestrator/tests/` の hit が
  その外にあったこと。** `| cat` で取り直すと hit は 8 件、生きた pin は 3 つだけだった。
  **閉包検索の出力を `head` で切ってはならない** — 段 1 で「pin は 2 箇所」と断定した根拠が
  切られた一覧だった。
- **pin の更新で実装面の差分が出たので、変異 matrix の免除 (`DW-S04`) が外れた。** `DW-M01` に
  従い変異 2 件 (実 bytes pin・上限 pin) を**実装前に**凍結し、Codex `role=author` の実装子に
  書かせた。実装子は現物を自分で数えて書き、login node の hook で pytest が走らないことを
  「実装済み・未実走」と正直に申告した。親が焦点走で `1 passed`、file 全体で
  `574 passed, 3 skipped` を実測した。
- 子は段 2 plan 1 本、段 3 敵対 2 本、段 6 焦点レビュー 1 本、段 5 実装 1 本の計 5 本で、
  いずれも受理検査 rc=0。実装子だけ workspace-write、他は read-only。
- **実装子の初回投入は射影 file の不在で正しく停止した。** 親が変異登録を実装子 worktree へ
  置き忘れていたためで、子の側の誤りではない。file を配置し `--job-id` を変えて再投入した。
- 逐語・run-card は `output/insights/2026-09-16_next-tasks-codex-authority/`。
- **段 8 の自己改善候補は 2 件で、どちらも不採用と裁定した。** (i) 受入の投入形
  (`-- python3 tools/run_tests.py` が必須) が dev-wave の reference から辿れず、`--help` が
  rc=2 なので `docs/pegasus-runbook.md` を grep して見つけた。`DW-O27` は L2 上限 1,000 bytes に
  ほぼ張り付いており追記余地がなく、予算のために既存の安全義務を削ることは禁じられている。
  正本は実在し 1 手で辿れたので、防壁の欠落ではなく探索コストと判断した。(ii) EnterWorktree で
  作った worktree は既に lock 済みで、`DW-O20` の lock 義務は自動充足されていた (手動 lock を
  試みて `already locked` を実測)。欠落がないので記録だけにとどめる。
- **scope 外として手を付けなかった既知の未反映が 1 件ある。** D1890 (1) が
  `docs/skill-self-improvement.md` と checker の終端 pin へ next-tasks を加えると裁定しているが、
  同文書に `next-tasks` の出現は 0 件のままである (main で実測)。本 wave は codex 相談規定の
  書き換えだけを引数で指定されていたため触っていない。

## 次の一手差分

### 新規

- {{T:next-tasks-self-improvement-contract-registration}} **P2・新規**: D1890 (1) の未反映を閉じる。
  `docs/skill-self-improvement.md` の共通自己改善契約と `tools/check_docs.py` の command 終端 pin へ
  `.claude/commands/next-tasks.md` を登録する。現状は同文書に `next-tasks` の出現が 0 件で、
  裁定と実装が食い違っている (2026-09-16 に main で実測)。
