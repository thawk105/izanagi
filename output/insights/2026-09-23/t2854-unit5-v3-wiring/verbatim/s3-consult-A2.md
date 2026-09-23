### A1 — must-fix：flag の受理と実際の段 1 取引が結び付いていない

**根拠:** plan §2 は `tpcc_*.exe` という名前と 4 flag の文字列だけを判定する。v3 parser は取引種別 1〜5、W の `D` を受理する。[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit5-v3-wiring/codex/s2-plan.md) §2、[parse.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/parse.py:353)、[parse.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/parse.py:375)。

**反例:** plan 自身が予定する `tpcc_fake.exe` に、指定の 4 flag を渡し、直列な v3 trace と一致する stdout 計数を出させる。その trace を `tx_type=4` の Delivery、`W ... D` を含む正常な存在遷移にしても、提案された述語は取引種別も op も見ない。X/P の source 証拠を満たす結合試験の条件下では certified に届く。これは設計 §3.5 の「段 1 の 57:43」に対する反例であり、D2232 項 4 が段 2 への適用を留保した範囲にも入る。段 1 の認定を主張するなら、少なくとも trace に種別 3〜5 と `D` が無いことを受理条件に含める必要がある。なお、任意の binary による取引種別の虚偽申告まで、この検査で証明できるわけではない。

**放置時の成果物:** 段 1 の契約外の trace に certified と受領証を発行できる。

### A2 — should：名前と flag は v3 emitter・計数修正の証拠ではない

**根拠:** 現 pin の `tpcc.hh` は commit 成功後、計数前に `quit_` で return する。[tpcc.hh](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/external/ccbench/include/tpcc.hh:482)。設計 §3.5 は修正版 binary に allowlist を限る。一方、plan §2 は binary の中身を識別しない。[設計](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/output/insights/2026-09-21/tpcc-trace-certification-design/README.md:92)。

現 pin の通常の v2 出力は、plan §3 の `existence_violation_details is not None` で拒否される。**推測:** 旧計数順のまま v3 emitter だけを持つ binary では、短い走行で quit 直後の数え落としが偶然 0 件なら witness が一致して通り得る。この一致は計数修正を証明しない。plan の完成条件は「指定 flag を持つ v3 run を受理」と「修正済み producer を認定」の区別を明記すべきである。

**放置時の成果物:** witness が一致した一走を、計数修正済み binary の認定として扱う余地が残る。

### A3 — should：既発行 v3 capability の digest は変わる

**根拠:** 現行 capability は旧射影を hash する。[core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/core.py:284)。切替後は v3 の存在件数・詳細、anomaly の表・取引種別が加わる。[core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/core.py:194)。既存 API は既に v3 capability を発行できる。したがって、同じ v3 結果でも旧 digest と新 digest は異なる。plan もこの点は認識している。[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit5-v3-wiring/codex/s2-plan.md) §1。

v2 では存在詳細が `None` で追加がなく、旧 anomaly もそのままなので、提案どおりの切替なら辞書は同一。digest の JSON は key を sort するため挿入順も影響しない。[commit_receipt.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/commit_receipt.py:38)。存在詳細を hash に含める判断は、既存の framing・permutation 詳細を除外する判断と技術的には両立するが、v3 の同一結果について新旧 digest を再現するときは射影の版を区別する必要がある。receipt consumer は digest を 64 桁 hex として束縛し、結果から再計算しないため、domain 据え置きだけで取り違えて認定する経路は見当たらない。[commit_receipt.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/commit_receipt.py:465)。

**放置時の成果物:** 既発行 v3 受領証の digest を新射影で再計算すると一致しない。

### A4 — should：不正な v3 射影は reject 診断にならず例外になる

**根拠:** `result_to_dict_v3` は cycle と取引種別の個数不一致、または表のない reason で `ValueError` を投げる。[core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/core.py:204)。CLI は verify 時の `ParseError` だけを捕捉し、JSON 射影はその外にある。[cli.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/cli.py:68)。pipeline も verifier 呼出しでは `ParseError` だけを捕捉し、reject 診断の射影は後段にある。[pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:613)、[pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:654)。capability 射影で起きれば発行自体が例外になる。

これは不正な内部 `VerifyResult` に対する静的な経路であり、正規 parser 入力から到達する証拠は見つからなかった。したがって must-fix とはしない。plan は「reject」と記述せず、例外で停止する契約として扱うのが正確である。

**放置時の成果物:** 該当する不正結果では certified のまま進まず、CLI 出力または pipeline の reject 診断が例外で失われる。

## 総括

plan の v3 信号は、通常の v2 では `None`、v3 では空リストを含む list となる。空 trace は verifier 前に拒否され、v2/v3 混在は parser が拒否するため、この信号だけによる偽の v3 判定は見つからなかった。
`"043"`、`"43 "`、必須 flag の欠落は文字列比較で拒否される。同じキーの二重指定は `Mapping` からの argv 生成では表現できず、非ゼロ batch 計数も拒否される。
最大の境界は、4 flag が実際の取引内容や emitter の実装を証明しない点にある。
B0 は 2 thread・1 倉庫・1 秒の一走で、取引種別 1/2、計数一致、v3 frame を示す。その観測を `tpcc_*.exe` 全体の十分条件へ一般化する根拠にはならない。
v2 の JSON と digest の bytes は、提案どおりの射影切替なら維持される。v3 digest は意図的に変わる。
本回答は指定資料の静的検査であり、テスト実測は行っていない。