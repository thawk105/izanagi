静的レビューのみ実施した。pytest、受入全走、provenance 検査、land は実行していない。

## 1. E は赤を閉じない

**判定: real**  
**重大度: High（「すべて直した」と終端するなら Blocker）**

親の推定値は一走失敗率約 20%（6回／約30走）である。[s1-brief-v2.md:66](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s1-brief-v2.md:66)

独立なら、再試行1回後の残存率を `0.2² = 4%` と見積もれる。しかし実際には、同一 node・同一 producer の4走連続再発があり、共有 checkout／ファイルシステム上の並行 wave でも同時発生している。[docs/failures.md:1518](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/docs/failures.md:1518) [docs/failures.md:1432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/docs/failures.md:1432)

したがって残存率は `P(F1∩F2)=P(F1)P(F2|F1)` と扱うべきで、`P(F2|F1)=P(F2)` の根拠がない。再走成功例も単独・低負荷であり、同じ全走条件の再試行ではない。[docs/failures.md:1469](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/docs/failures.md:1469) [docs/failures.md:1521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/docs/failures.md:1521)

結論は「ほぼ閉じる」ではなく、受入保証の観点では**ほとんど変わらない**。E は一時的な観測上の緩和であり、`git-timeout` は作業量劣化と資源競合を区別しない。[s8c_preregistration.py:892](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:892) [s8c_preregistration.py:900](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:900)

**成果物影響:** 無視すると、受入全走は再び `1 failed` になり得て、再試行後だけ緑になる実行が初回の `git-timeout` を隠す。

## 2. Q5 だけでは正直な終端にならない

**判定: real**  
**重大度: High**

Q5 の「緩和であって恒久対応ではない」は必要だが、限定的な注意書きに過ぎない。[s1-brief-v2.md:54](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s1-brief-v2.md:54)

worklog と `docs/failures.md` には最低限、次を明記すべきである。

- E はテスト側だけの有限再試行で、production と発効判定は不変。
- 初回の `git-timeout` と、各再試行の結果・回数・実行経路を記録する。
- 再試行後に通っても、初回 timeout の発生自体を F57 の再発として消去しない。
- T-553／F57 は open のまま、C はユーザー裁定待ち。
- provenance の23件も残っており、「全走緑」「すべて直した」「land 完了」とは報告しない。

例えば、終端文は次の意味を満たす必要がある。

> E により invariant test の `git-timeout` を有限回再試行する緩和を追加した。production、15秒 gate、発効判定、generation 生成条件は変更していない。これは資源競合に対する確率的緩和であり、F57／T-553 の恒久対応ではない。C は裁定待ちで、受入全走および provenance 全履歴の緑は未確定である。

**成果物影響:** 無視すると、F57 の台帳が「再発なし」に改ざんされた状態になり、受入結果・T-553 の状態・終端報告が実態とずれる。

## 3. C の裁定送りは過剰慎重ではない

**判定: refuted（「C の保留は過剰慎重」という攻撃を退ける）**  
**重大度: Critical（無裁定で C を実装した場合）**

C は `B(R)>15` の領域で従来 reject された実行を通し、wall-clock 受理集合を変える。[s1-brief-v2.md:28](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s1-brief-v2.md:28)

さらに `prepare_revision` は既存 generation の検証後に generation ファイルを排他的に生成するため、変更は単なる高速化ではなく凍結成果物の生成条件に到達する。[s8c_preregistration.py:1688](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:1688) [s8c_preregistration.py:1718](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/campaign/s8c_preregistration.py:1718)

よって親が単独で決められる、意味を変えない C の部分集合は、現行15秒境界を維持した計測・証跡・テスト整理までである。比例予算を実際の判定に使う部分は、ユーザー裁定なしに進めてはならない。

**成果物影響:** 無視すると、従来 reject される candidate が valid/effective となり、新しい generation JSON と凍結台帳が生成され得る。

## 4. E は将来の C と競合し得る

**判定: real**  
**重大度: High**

E は `PreregistrationError("git-timeout")` を再試行対象にする。[s1-brief-v2.md:47](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s1-brief-v2.md:47) C 案も予算切れに既存の `git-timeout` を使う設計である。[s2-plan.md:122](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s2-plan.md:122)

このまま共存すると、C が意図的に拒否した予算超過を、テストが validator 全体の再実行で通す可能性がある。再試行ごとに C の deadline が作り直されれば、テスト上の総許容時間も実質的に増える。

共存条件は次のいずれかである。

- C 実装時に E を撤去する。
- C の恒常的な予算超過を別 reason code にし、E はテスト注入の一過性故障だけに限定する。
- 少なくとも、初回 timeout を記録し、再試行が C の判定境界を越えないことをテストで証明する。

**成果物影響:** 無視すると、C の受理集合・timeout 境界をテストが検証できず、誤った緑と誤った凍結判定を報告する。

## 5. 「main の赤はちょうど2つ」は全経路の全数調査ではない

**判定: real（絶対的な全数主張としては refuted）**  
**重大度: High**

親の「2つ」は、親が実行した測定結果については成立する。しかし pytest の収集範囲は `orchestrator/tests` に限定される。[pytest.ini:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/pytest.ini:13) その外側の検査・保護入口は別に監査が必要である。

### 5-a. dev-wave の CI 相当 supervisor

`tools/dev_waves/cli.py` は codex-agents、docs、orchestrator、provenance の4検査を既定で束ねる。[cli.py:188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/tools/dev_waves/cli.py:188) これは親の表にある個別検査とは別の orchestration 経路である。

**成果物影響:** 無視すると、個別検査が通っても supervisor の終了コード・timeout・集約結果を未確認のまま「全チェック緑」と報告する。

### 5-b. `--force-dispatch` 経路

`run_tests.py` と `check_ai_provenance.py` は `--force-dispatch` で通常の admission と異なる経路に入る。[run_tests.py:1713](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/tools/run_tests.py:1713) [check_ai_provenance.py:1918](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/tools/check_ai_provenance.py:1918)

F57 でも通常の単独再走は rc=16 で結果を得られず、`--force-dispatch` で初めて8 passedを得ている。[docs/failures.md:1521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/docs/failures.md:1521) baseline の scheduler receiptだけでは、どの分岐を通ったか証明できない。

**成果物影響:** 無視すると、実行されていない／rc=16 の結果を緑と誤認し、受入値と land 判定が無効になる。

### 5-c. hook の live wiring

`.claude/settings.json` は Claude の PreToolUse にだけ配線されている。[settings.json:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/.claude/settings.json:9) Codex には未配線であり、hook 単体テストも `decide()` を直接呼ぶ machine-independent test である。[hooks/README.md:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/hooks/README.md:15) [test_hooks.py:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/orchestrator/tests/test_hooks.py:4)

**成果物影響:** 無視すると、pytest が緑でも実際の Codex／script／cron 経路で防壁が発火することを証明できず、保護対象の正しさが未監査になる。

### 5-d. site gate のない直接 build 経路

` t152_write_intent_coverage.py` と `silo_ladder_rung1.py` の直接 CMake 呼び出しには site gate がない。[pegasus-runbook.md:587](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/docs/pegasus-runbook.md:587)

**成果物影響:** 無視すると、重い検査の実行場所・資源条件が未制御のまま、測定成果物と land 前提を汚染し得る。

### 5-e. `check_workflow_models.py`

これは現 checkout では対象 directory 不在で非該当という親の判断が妥当であり、現時点の第三の赤とは数えない。[s1-brief.md:16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s1-brief.md:16)

**成果物影響:** 現在の acceptance 値は変わらないが、対象 script が追加された時点で再調査が必要になる。

## 6. provenance 23件は「触らない」は妥当だが、「影響しない」は誤り

### 6-a. 所有権判断

**判定: real（no-touch は妥当）**  
**重大度: Low**

23件は t682／t139 の所有と明記されている。[s1-brief.md:12](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-suite-20260809/s1-brief.md:12) 本 wave が重複修正しない判断は正しい。

**成果物影響:** 無視すると、parallel wave と修正が重複し、provenance 台帳と commit identity の修正が競合する。

### 6-b. land／終端への影響

**判定: real（条件付き）**  
**重大度: High**

`dev_wave_land.py` 自体は、provenance の内容を全履歴監査せず、tested main/tip と audited commit 列の SHA 閉包だけを検証する。[dev_wave_land.py:963](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/tools/dev_wave_land.py:963) また、fold preflight は `--message-file` だけである。[dev_wave_land.py:1392](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/tools/dev_wave_land.py:1392)

したがって、**helper 内部だけなら既存23件が直接 `RC_AUDIT=23` を発生させる経路は見つからない**。[dev_wave_land.py:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/tools/dev_wave_land.py:46)

しかし運用規約は land 前後に full-history provenance audit を要求し、赤なら停止する。[operations.md:93](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/docs/dev-wave/operations.md:93) `check_ai_provenance.py` の通常経路は full history を監査する。[check_ai_provenance.py:2073](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-suite-20260809/tools/check_ai_provenance.py:2073)

**成果物影響:** 無視すると、`dev_wave_land.py` が `landed` を返しても、必須の post-land full audit は rc=1 のままになり、land 状態と終端台帳が食い違う。

## 総括

(i) **NO-GO**。E-only を「すべて直した」「全走緑」として終端するのは不可。E を暫定緩和として扱うこと自体は可能だが、T-553 は未解決である。

(ii) must-fix:

- E 後も初回 timeout を記録し、F57／T-553 を open のままにする。
- 報告を「テスト側の確率的緩和」に限定する。
- C はユーザー裁定なしに実装しない。
- C 実装時は、E を撤去するか、恒常的な予算超過を再試行できない設計にする。
- supervisor、`--force-dispatch`、live hook wiring を「未監査経路」として台帳化する。
- provenance 23件を所有 waveへ委譲しつつ、full-history audit が緑になるまで終端完了とは扱わない。

(iii) 必須留保は、production の発効判定は E で改善していないこと、単独再走の緑は全走条件の証拠ではないこと、provenance 23件が残っていること、そして本レビューでは pytest 等を実行していないことである。