単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/stage1-brief.md — 親 brief (P1〜P7、攻撃対象)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/s2-plan-r2.md — 段 2 のプラン (攻撃対象)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/request.md — 依頼の逐語。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/d2194-item3.md — 本 wave の裁定の逐語。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/insight-t2632-s7.md — 一次資料 §7。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/insight-t2632-s2.2-2.3.md — 一次資料 §2.2 / §2.3。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/insight-t2632-s4.md — 一次資料 §4。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/prereg-s5.1.1-reference.md — 凍結事前登録 §5.1.1 共通参照点 (逐語)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/prereg-s5.1.1-population.md — 同 母集合・適格性述語 (逐語)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_s4_loop.py — 読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_s4_loop_trigger_gating.py — 先例。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_b4_prerun_caller.py — 読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/campaign_lock.py — 読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/wal.py — 読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/agent_outputs.py — 読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/tests/test_p3_s4_loop.py — 読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/tests/test_p3_b4_prerun_caller.py — 読めなければ即停止

## レンズ A: 正しさ境界・整合・実効性

プランを守らせず検査する。**親 brief 自身も検査対象**である。brief の file:line、前提 (P1〜P7)、所有範囲、変異の帰属不成立、
**親自身の実測値とその一般化**を疑う。攻撃面に `docs/failures.md` の型タグ [恒真ゲート] [テスト代表性] [誤前提] [ドリフト]
[consumer 取り残し] [変異帰属] [防壁の射程誤認] を含める。次を必ず検査し、各項目を real (欠陥あり) / refuted (欠陥なし) で判定して根拠 (file:line) を示す。

1. **束縛の正しさ (辺 A):** side channel の `initial_proposal_sha256` は、harness が実際に評価した proposal (load_proposal_file が読んだ
   bytes) の canonical hash か。main で計算して drive_iteration へ渡す経路で、読んだものと評価したものが食い違う窓 (再読・別 path・
   B-4 receipt key の除去の有無) はないか。`variant` / `build_attempt_id` は、その iteration の評価を WAL 上で一意に指すか
   (重複解決・retry・複数 attempt・reject の `diffq-*`・dry-pass の variant 無し)。`wal_refs` の構成規則 (brief P6) は
   attempt 境界を正しく切るか。
2. **規律 2 と D39 決定 3:** side channel の追加が correctness 判定・reject / certified の経路・whiteboard 5 field・planner 射影
   (`project_whiteboard` / `whiteboard_for_planner` / critic digest) を 1 bit でも変えないか。side channel の内容が planner / coder /
   critic の入力へ流れる経路 (leak) が新たにできないか。
3. **fail-closed の意味 (P4):** 書けない・壊れた side channel で停止するとき、評価済みの WAL と checkpoint の関係はどうなるか
   (評価は終わったが checkpoint が進まない → 再開時に同 iteration を再評価するか、重複解決に落ちるか)。先例 trigger driver と同じ
   性質か。停止が新たな正しさ上の穴 (評価済みなのに whiteboard に載らない等) を作らないか。
4. **caller の受理域 (項 4、DW-O13 の対象):** codec 経由化で受理が広がるのは v2 lock だけか。v1 lock (tracked 3 campaign) は引き続き
   同じ結果を返すか。`decode_campaign_lock` が拒否する形 (非 canonical v2、未知 schema、non-certifying lock) で caller が
   `campaign_input_unreadable` になり、黙って空 batch へ進まないか。v1 / v2 の独自救済分岐を足していないか。
5. **参照点の定義 (2) と凍結事前登録:** プランが書く定義文は §5.1.1 の凍結文 (祖先無し・同着・PerfConfig / env_tag 不一致は不適格、
   代替基準へ切り替えない) と矛盾しないか。「同一 campaign 内の時間順」の祖先を side channel から一意に引けるか (duplicate が
   既存 attempt を指す場合の祖先の扱い、同じ variant を 2 回指す行)。reps / ycsb_max_ope を不足として残す書き方になっているか。
6. **親の実測と一般化:** brief の「実物 v2 lock 10 件は B-5 試走の campaign」は B-4 の供給源になる新規 base campaign にも一般化できるか
   (B-4 mode の lock の identity は同形か)。「stock 対照は whiteboard に触れない」「certified-writer 目録は登録不要」は正しいか。
   「未 commit の注入で 114 node が落ちる」を踏まえた test の組み方と変異の帰属は成立するか。
7. **[恒真ゲート] / [テスト代表性]:** プランの test 案と変異候補は、欠陥があるとき実際に落ちるか。先例 trigger の test を写しただけで
   base の分岐 (duplicate / dry-pass / b5 早期 return / pair mode) を通っていない test はないか。

## 制約

- sandbox は read-only で書込可能な tmp が無い。**静的検査だけでよい。** テスト実走は親が行う。実走していないことを「確認した」と書かない。
- 新しい gate・検査・台帳 (admission への base provenance 検査など) を提案する場合は、依頼の scope 外であることを明記し、裁定パッケージ候補として分けて返す。
- 予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終える。

## 出力形式

項目 1〜7 を見出しで分け、各項目に判定 (real / refuted) と根拠を書く。real には must-fix / should-fix / nit の別と、放置時に成果物
(B-4 の適格行・参照点・台帳・certified 判定) がどう変わるかを 1 行で添える。最後に `## 総括` を置く。
