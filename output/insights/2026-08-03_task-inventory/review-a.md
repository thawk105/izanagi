判定は **NO-GO**。現 fragment のまま fold すると、生存作業 3 件が消える。69 件すべてについて最終実体を解決し、現行 worklog と 66 archive の後続言及を静的検索した。pytest は実行していない。

## 所見

### T-126 — A5

一次資料:

- ユーザー裁定は「qualification-first amendment」を採用し、live control と machine-readable receipt を先行すると明記している。[worklog archive:543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/archive/worklog-phase3-0729-59-0730-67.md:543)
- 現行 phase doc も「現時点は実装待ち」としている。[phase3.md:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/phase3.md:42)
- ところが完了記録自身が「live qualification は scope 外」「未実施」と認める。[worklog archive:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/archive/worklog-phase3-0801-86.md:49)、[同:125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/archive/worklog-phase3-0801-86.md:125)
- fragment はこれを「必要になった時点で新規起票」に書き換えて `remaining: none` としている。[fragment:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/spool/worklog/2026-08-03-dev-wave-task-inventory-1.md:105)

誤り: 「実施待ち」のユーザー裁定を、後続の親が「将来必要なら」に弱めている。別 ID が所有するとの記録もない。親自身の「裁定済み→実装待ちは落とさない」基準への直接反例である。

推奨: **落とすな**。T-126 を「裁定済み→実施待ち」に戻す。分離するなら、live qualification 用の安定 ID と明示的な所有移管が先に必要。

### T-316 — A3・A5

一次資料:

- ユーザー裁定は択 (a) の「意味 gate」で、auditor の echo と想定外構文を機械検査する内容だった。[worklog archive:660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/archive/worklog-phase3-0802-113-116.md:660)、[同:683](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/archive/worklog-phase3-0802-113-116.md:683)
- 実装 wave は AST/DSL と sandbox の「どちらも採らず」、未分類 source の build 拒否という別案を実装した。[worklog archive:642](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/archive/worklog-phase3-0802-117-121.md:642)
- 同じ記録で、`std::system`、`execl`、無限ループ等の意味注入と auditor echo が依然通ると確認している。[同:655](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/archive/worklog-phase3-0802-117-121.md:655)
- D127 は採らなかった二案を「別 wave へ分離する」とするが、安定 ID を一つも指定していない。[decisions.md:6235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/decisions.md:6235)
- fragment が分離先とする T-342〜T-344 は、実際には provenance capability、cache/replay identity、旧成果物の地位を扱う項目である。[worklog archive:713](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/archive/worklog-phase3-0802-117-121.md:713)、[同:722](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/archive/worklog-phase3-0802-117-121.md:722)、[同:728](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/archive/worklog-phase3-0802-117-121.md:728)。三件とも既にその範囲で完了している。[worklog archive:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/archive/worklog-phase3-0803-136.md:60)
- fragment は T-342〜344 を残余所有者として `remaining: none` とする。[fragment:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/spool/worklog/2026-08-03-dev-wave-task-inventory-1.md:42)

誤り: T-342〜344 は実在するが、ユーザー裁定済みの意味 gate を所有していない。採らなかった本体は「別 wave」という無 ID の行き先に消えている。

推奨: **落とすな**。T-316 を継続へ戻すか、意味 gate 専用 ID を起票して、ユーザー裁定の明示的な supersede／所有移管を記録する。

### T-276 — A3

一次資料:

- T-276 の完了記録は、valid-schema 意味注入の残余を明示的に T-316 へ送っている。[worklog archive:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/archive/worklog-phase3-0802-113-116.md:153)
- fragment は T-276 と T-316 の両方を `remaining: none` で落とす。[fragment:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/spool/worklog/2026-08-03-dev-wave-task-inventory-1.md:48)、[同:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/spool/worklog/2026-08-03-dev-wave-task-inventory-1.md:42)

誤り: 分離先 T-316 が誤って終端化されるため、T-276 の残余所有関係も切れる。これは T-316 欠陥の波及であり、T-276 本体の実装完了を独立に否定するものではない。

推奨: **文言を直せ**。T-316 を継続へ戻したうえで、T-276 の残余所有者として明記する。

### T-160 — A5

一次資料:

- 完了 item 自身が「陳腐化候補 7 節」の削除実施を「ユーザー裁定待ち」と明記する。[worklog archive:646](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/archive/worklog-phase3-0728-33-37.md:646)
- insight §5 はユーザー向け裁定パッケージであり、本 wave では削除ゼロ、分析上の推奨は全件維持である。[insight:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/output/insights/2026-07-28_t160-reference-layering.md:83)
- fragment は裁定待ちを省いて `remaining: none` とする。[fragment:219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/spool/worklog/2026-08-03-dev-wave-task-inventory-1.md:219)

誤り: 「全件維持」という親の推奨を、記録のないユーザー裁定へ読み替えている。全後続 worklog を検索したが、T-160 の当該裁定を受けた記録はなかった。

推奨: **落とすな**。ユーザー裁定を得るか、裁定待ちを新しい安定 ID に分離するまで継続。

### T-136 — A5

一次資料:

- 完了 item は「残余は insight §7」と明記する。[worklog archive:326](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/archive/worklog-phase3-0728-33-37.md:326)
- 本文では残余を未観測のため新規タスク化しないとしている。[同:311](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/archive/worklog-phase3-0728-33-37.md:311)
- 参照先 §7 の見出しは「残余リスク (worklog 次の一手へ)」で、固定短窓、無界 WAL/fsync、0.5 秒 durability 窓を列挙する。[insight:93](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/output/insights/2026-07-28_t136-timing-flake-generalized-limits.md:93)
- fragment はこの残余を省いて `remaining: none` とする。[fragment:141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/spool/worklog/2026-08-03-dev-wave-task-inventory-1.md:141)

誤り: 「未観測なので今は実装しない」は残件なしではなく、親基準でいう「発火条件つきで未成立」である。完了 sink ではなく見送り台帳へ残すべき内容を消している。

推奨: **見送りへ回せ**。T-136 の観測済み機序の完了は維持してよいが、§7 の残余を安定 ID と発火述語つきで台帳化してから終端化する。

### T-173 — A4

一次資料:

- fragment は thread pool と祖先 bitset の双方を `tools/check_ai_provenance.py:717-798` で確認したとする。[fragment:240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/spool/worklog/2026-08-03-dev-wave-task-inventory-1.md:240)
- 祖先 bitset は実在する。[check_ai_provenance.py:715](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/tools/check_ai_provenance.py:715)、[同:739](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/tools/check_ai_provenance.py:739)
- thread pool は引用範囲外の `_audit_history()` にあり、`ThreadPoolExecutor` は 850 行目である。[同:833](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/tools/check_ai_provenance.py:833)、[同:849](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/tools/check_ai_provenance.py:849)

誤り: 実装達成の実体は静的に確認でき、T-173 の完了分類自体は崩れない。ただし提示行範囲では thread pool を確認できず、「実測確認」という証拠表現もコード参照だけでは支えられない。

推奨: **文言を直せ**。静的根拠を `715-798, 833-853` とし、実測を主張するなら T-205 の計測記録を別途参照する。

## 総括

- 誤りと判定したものは **6 ID**。保存・分類上の誤りが T-126 / T-316 / T-276 / T-160 / T-136、A4 の証拠文言誤りが T-173。
- **落とすな**と結論した ID は **T-126、T-160、T-316**。
- 攻撃したが崩せなかった点:
  - A2 の独立した見落としはゼロ。T-057 の再成立は実在するが、記録自身が T-201 へ所有移管しており、T-201 は継続している。[worklog archive:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/archive/worklog-phase3-0731-74.md:86)
  - T-243→T-318〜323、T-291→T-310〜313、T-277→T-330/331、T-193→T-222、T-180→T-183/184/186、T-182→T-189、T-152→T-167、T-157→T-159、T-117→T-119〜122 の所有先は実在し、継続・見送り・正当な完了のいずれかへ保存されていた。
  - T-173 の thread pool＋祖先 bitset 化は実物と整合し、崩れたのは引用範囲だけ。
  - T-297 の発火記録追記と T-356 の 4 終端／8 active の仕分けは fragment・台帳上で確認できた。
- 検査は全件静的。pytest その他のテストは実行しておらず、緑は主張しない。