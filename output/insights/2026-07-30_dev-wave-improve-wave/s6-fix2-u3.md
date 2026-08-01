R1 は実装上 closed です。pytest green は主張しません。

変更ファイル:

- [buildcache.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u3/orchestrator/campaign/buildcache.py:28)
  - trusted policy sourceをFDから直接読み、private namespaceで`compile`/`exec`
  - public/private `sys.modules` poisonと`sys.path`から独立
  - `lstat`・`O_NOFOLLOW`・`fstat`でsymlink、非regular、読取途中変更をfail-closed
  - production gateはmetadataではなくロード済みtrusted object identityを正本化
- [test_campaign.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u3/orchestrator/tests/test_campaign.py:590)
  - canonical-looking `__file__`・`spec.origin`・compile filename・`__module__` forgeを実login helper branchへ投入
  - ordinary import、`sys.path` poison、private/public module-cache poison、source raceの回帰test
  - trusted caller positive controlを維持

静的確認:

- Python 3.10 AST: U3 8ファイル成功
- production caller import identity: 6 modules成功
- 変更2ファイルのpyflakes: 成功
- `git diff --check`: 成功
- valid hit→miss gate順、4 helper早期gate、`s8a_trigger_freq`先頭gate、4箇所の`-j16`: AST静的確認成功
- U3全体のpyflakesには、今回以前からHEADにも存在する `s2_verify_calibration.py:249` のplaceholderなしf-string警告が1件残存。R1外のため未変更

pytest・build・qsubは未実走です。commit/push、U1 policy source、docs、insight、freeze、provenance、submoduleは変更していません。既存のU1 untracked filesも触れていません。

## 総括

R1は、ambient moduleの見た目を検査する方式を廃止し、trusted source bytesとprivate object identityを信頼の正本にしたことでclosedです。動的テストは指示どおり未実走です。
