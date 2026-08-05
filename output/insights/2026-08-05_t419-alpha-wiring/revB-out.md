### Blocking — CPU-set drift 負例が偽 kill になる

**場所** [test_env_attestation.py:392](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/tests/test_env_attestation.py:392)、[test_env_attestation.py:505](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/tests/test_env_attestation.py:505)、[env_attestation.py:364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:364)、[env_attestation.py:373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:373)

**なぜ危険か** CPU-set drift 負例はいずれも期待 CPU を欠落させている。集合一致検査 M08 を削除しても、その後の `mhz_by_cpu[cpu_id]` が `KeyError` になり、`pytest.raises(AttestationError)` は失敗する。したがって狙った検査が消えても node は赤くなり、M08 を偽 kill できる。期待 CPU は全て残し、余分な CPU だけ追加する fixture にすれば、集合検査以外を削除した場合は正常終了し、拒否理由を一つにできる。

**成果物影響** mutation ledger が集合完全性を未検証のまま M08 を killed と記録し、land 証拠を偽装しうる。

**scope 内/外** scope 内。段 6 の must-fix。

### M12 の preregistered node と quiet fixture が不一致

**場所** [test_env_attestation.py:309](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/tests/test_env_attestation.py:309)、[test_env_attestation.py:325](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/tests/test_env_attestation.py:325)

**なぜ危険か** 段 4 は「全 K ベクトルの完全一致を要求する」過剰拒否変異を quiet positive で殺す指定だが、quiet fixture の 5 ベクトルは全て同一であり、その変異を検出できない。別の migrating-reader positive は異なるベクトルなので suite 全体では検出可能だが、期待 node と実際の kill 元が食い違う。quiet を、全 CPU が帯内のまま各読取値だけ少し異なる系列へ直すべきである。

**成果物影響** mutation matrix が `MISMATCH` または誤った node 帰属となり、段 4 の事前登録との追跡性が壊れる。

**scope 内/外** scope 内。fixture 修正または期待 node の再裁定が必要。

### Oracle の予約式が α の反復時間を含まない

**場所** [s8b_oracle_driver.py:714](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/s8b_oracle_driver.py:714)、[s8b_oracle_driver.py:921](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/s8b_oracle_driver.py:921)

**なぜ危険か** 予約式は各 row の試行上限と finalization 600 秒だけを数える一方、各 recheck の後に最低 0.20 秒の probe を実行し、safety margin は 0 である。N row なら初回を含め最低 `(N+1)×0.20` 秒が未計上で、試行が上限近くまで使われると次回 recheck が `execution-guard-lost` になりうる。上限を持つ probe allowance の導入、または予約順序・式の変更が必要。

**成果物影響** 正当な oracle campaign が予約境界で途中拒否され、ratified artifact を生成できない可能性がある。

**scope 内/外** 現在の二ファイル実装範囲外。時間上限という新しい契約を要するため裁定へ返す。ただし未裁定のままの land は不可。

### 既知 — T126 は依然として probe 出力を消費できない

**場所** [t126_driver.py:442](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/qualification/t126_driver.py:442)、[t126_driver.py:454](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/qualification/t126_driver.py:454)

**なぜ危険か** `compare_profiles()` に `CalibrationV2` を、`profile_sha256()` に `ObservedAttestationProfile` を渡しており、成功経路へ進めない。α が新設した破壊ではなく、段 4 B6 が明示的に scope-out した既知事項である。

**成果物影響** T126 qualification は fail-closed のままで、成功 receipt を生成できない。

**scope 内/外** scope 外・裁定済み。本 wave の新規 blocker には数えない。

## 総括

静的条件式上、持続する 1 CPU の帯外値は 5 回の最小値にも残り、既存 comparator に拒否されるため γ 化していない。安定した計算ノードでは singleton affinity、pre/post processor、interval、identity、復元 mask の各検査に日常的な必然発火条件は見当たらない。ただし実機 quiet positive は段 4 の scope-out どおり未実測である。

全 caller/test double は zero-argument 呼出しなので keyword-only 追加による破壊はない。最低時間との比較は、単発 wrapper 0.20/120 秒、silo 0.20/180 秒、T126 最大 1.8/600 秒、certification 全体最低 1.2 秒対約 590 秒の余裕、floor 0.20 秒対約 6300 秒の余裕で、Oracle 以外は既存 timeout を脅かさない。

no-touch 指定ファイルは Git object 上 HEAD と同一で、登録較正 SHA-256 も `753f535a…e5a49` のまま。`effective_clock` は exact に `samples_mhz` / `method` / `governor`、profile hash・比較 field・v1/v2 parser・旧 v1 corpusにも差分はない。5 CPU 化後も governor、cache index、hidepid、NUMA の期待値は緩和されていない。

テスト・変異は未実行であり、緑・赤の実測主張はしない。最重要所見は M08 の偽 kill。判定は **NO-GO**。M08 fixture と M12 の preregistration 不一致を直し、Oracle 時間予算を裁定してから land 判定へ戻すべきである。