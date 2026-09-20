## DW-O28 — land 後の自己撤去

land 成功後、段 9 に main worktree から job 終端後 `python3 tools/dev_wave_cleanup.py` で撤去(絶対 path、`--main-worktree <MAIN>` は両方に付ける)。
先に manifest(`DW-S05-A`)の子木を `remove-child --manifest <M> --child-worktree <P> --evidence-dir <D>` で(回収 wave は旧分も)、次に wave を `--wave-worktree <WAVE> --wave-branch <BRANCH> --tested-wave-tip-sha <TIP>` で撤去し、他へ引き渡さない。
tool は非占有・main 祖先性(子木は所有 path の tree 一致でも可)・dirty 退避可否・manifest 束縛を検査。撤去前の不成立・不明は拒否し木と branch を残す(以後は rc=30)。統合証明済みの manifest 現行 branch は履歴を `<D>` へ bundle 後(HEAD が main 祖先なら省く)に `-D`。
F26: `git worktree remove`/`git submodule deinit` 不可。wave branch は `-d` のみ、手打ち `-D` 禁止。残る子木は unlock し理由を worklog へ。
