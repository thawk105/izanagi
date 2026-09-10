## 所見

### 1. call-only の無条件 return は T-930 のコスト迂回と偽緑を再開く

- 主張: wrapper と末尾 raise の差は非空。wrapper は関数の call phase しか守らず、末尾 raise は collection／fixture setup／plain runner より前に module 読み込みを止める。段 2 の「wrap 後なら即 return」はこの保証を失う。
- 根拠: [growth_test_holds.py:599-606](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/growth_test_holds.py:599)、[growth_test_holds.py:640-655](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/growth_test_holds.py:640)、[s2-plan.md:6](/work/1/SFC/tanab/dev-wave-jobs/2026-08-17_t1226-hold-guard/s2-plan.md:6)。wrapper-only では fixture が先に走って 38.01 秒を消費した既往が [decisions.md:15679-15687](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/docs/decisions.md:15679) に明記されている。
- 具体的な失敗シナリオ: call-only module を `pytest --noconftest file.py::held_test` で集めると import は成功し、成長比例 fixture が完走した後で初めて wrapper が拒否する。また原型の `test_s8b_floor_campaign.py` は `__main__` guard を持たず EOF が [同:9916](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_s8b_floor_campaign.py:9916) なので、将来 `plain_runner="none", guard_mode="call-only"` を結ぶと `python3 file.py` がテスト 0 件のまま rc=0 になり得る。計画の正例は direct call だけで、call-only の `--noconftest`／plain 実行を検査していない。
- 重大度: blocker

### 2. canonical global の wrap だけでは「held function の呼出は必ず拒否」を満たさない

- 主張: wrapper は namespace の canonical 名だけを差し替える。元関数の事前 alias／callback 登録を機械拒否しない限り、call-only import 後に未包装参照から本体へ入れる。
- 根拠: 差し替え面は [growth_test_holds.py:640-644](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/growth_test_holds.py:640) のみ。プラン自身もこの危険を認識するが、対応は decisions への記載だけである [s2-plan.md:102-103](/work/1/SFC/tanab/dev-wave-jobs/2026-08-17_t1226-hold-guard/s2-plan.md:102)。exact 述語 [同:35-43](/work/1/SFC/tanab/dev-wave-jobs/2026-08-17_t1226-hold-guard/s2-plan.md:35) に元関数参照の保持禁止はない。
- 具体的な失敗シナリオ: guard 前に held test を callback table へ登録した module が自己読込みされ、その helper が table 経由で呼ぶと、global 名の wrapper を通らず exact token なしで held body が実行される。現行末尾 raise はその standalone import 自体を止める。
- 重大度: blocker

### 3. 新規受理集合は manual 1 形ではなく runner 3 形

- 主張: 新たに受理される集合は、既存の import/call/配置条件をすべて満たし、canonical self-load があり、keyword 名列が正確に `("plain_runner", "guard_mode")`、mode が文字列定数 `"call-only"`、かつ runner が AST 導出値と一致する source の集合である。runner は `"none"`、`"manual"`、`"pytest-delegating"` の3族になる。
- 根拠: 現行数値条件は `len(call.args) == 2`、`len(call.keywords) == 1` [test_growth_test_holds_contract.py:541-564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:541)。プランは runner 3 literal を維持する [s2-plan.md:35-43](/work/1/SFC/tanab/dev-wave-jobs/2026-08-17_t1226-hold-guard/s2-plan.md:35) 一方、表は manual だけを示す [同:45-54](/work/1/SFC/tanab/dev-wave-jobs/2026-08-17_t1226-hold-guard/s2-plan.md:45)。
- 具体的な失敗シナリオ: `"none"` は所見1の無検査 rc=0、`"manual"` は main harness の先払い処理、`"pytest-delegating"` は direct import 面の緩和を受理する。keyword 名列の exact 比較を実装する限り未知 keyword、重複、逆順、`**mapping`、第三 positional arg は拒否され、「何でも通る」形ではない。
- 重大度: must-fix

### 4. 親が挙げた第2の実在 consumer を detector が扱わない

- 主張: 親 brief は `test_dev_waves_integration.py` の subprocess package import も発火実例に挙げるが、プランの detector は loader／runpy／exec(open) 系だけで、自己 package import を扱わない。
- 根拠: 実経路は [test_dev_waves_integration.py:2050-2058](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_dev_waves_integration.py:2050)。検出予定形は [s2-plan.md:56-63](/work/1/SFC/tanab/dev-wave-jobs/2026-08-17_t1226-hold-guard/s2-plan.md:56)。
- 具体的な失敗シナリオ: 同 file の成長比例 node を将来登録すると、正規 subprocess import を self-load と認識できず、call-only binding を契約テストが拒否して F351 型の受入赤を再発させる。
- 重大度: must-fix

## 親 brief への反証

- 「後者だけを条件付きにできる」という一般化は反証あり。末尾 raise は単なる import 拒否ではなく、fixture 先払い防止と plain runner の非ゼロ終端も担う。
- 関数本体の解除だけを見れば、wrapper の exact token 比較 [growth_test_holds.py:602-604](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/growth_test_holds.py:602) と collection 側 [conftest.py:321-333](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/conftest.py:321) は同じ定数を使い、標準 pytest の受理集合は不変。ただし call-only は第2の import 許可経路となり、conftest 不在時のコスト防壁を解除するため、hold 全体では第2の迂回になる。
- `count=59` と `key_sha256=30e646a8…d6508c` は保たれる。両値は registry の sorted key だけから導出される [growth_test_holds.py:658-669](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/growth_test_holds.py:658) うえ、inventory はその値をそのまま射影する [hold_inventory.py:80-100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/tools/hold_inventory.py:80)。literal pin も [test_growth_test_holds_contract.py:39-41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:39) にある。
- live source-byte SHA／凍結成果物については反証なし。ただし「docs は failures/archive の叙述のみ」という一般化は誤りで、D347 が `hold_inventory.py` の exact 構造と `effective_status`／`bypass_surface` を規範化している [decisions.md:15303-15317](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/docs/decisions.md:15303)。D360 も二層防壁を規範化している。
- 「held file の自己読込みを静的に見る既存検査は 0 件」は反証なし。既存記録も当該検査を未実装と明記する [failures.md:8857-8858](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/docs/failures.md:8857)。

## 総括

段 2 の無条件 call-only return は、そのままでは T-930 のコスト先払いと偽緑を再開く。  
新規受理集合は syntax 上は閉じているが、`none`／`manual` を含む3族であり、表より広い。  
fixture 前拒否と元関数 alias の機械的封鎖を追加しない限り blocker。  
registry の count／digest と標準 conftest の exact-token 契約は不変と確認した。  
read-only 静的レビューのみで、pytest・編集・commit は実施していない。