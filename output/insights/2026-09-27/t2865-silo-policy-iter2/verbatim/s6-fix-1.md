## 変更 file と要点 (file:line)

[patches/instr-silo-function-policy-probe.patch:125](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865i2-unit-seed/patches/instr-silo-function-policy-probe.patch:125) の hunk 位置を更新し、[begin() の hunk](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865i2-unit-seed/patches/instr-silo-function-policy-probe.patch:172) に骨格が追加した seed 呼出しを文脈行として反映しました。計器の加除行は変更していません。変異 patch 11 本はすべて適用できたため、bytes を変更していません。

## 適用確認 (積み方ごとの git apply の結果)

pinned CCBench `681066606` の一時 copy で、各段の `git apply --check` と実適用が成功しました。

- 骨格 → 計器: 成功
- 骨格 → 計器 → `MUTATION_PATCHES` 9 本を各 1 本ずつ: 全件成功
- 骨格 → `NEGATIVES` 3 本を各 1 本ずつ: 全件成功。所有外の early-unlock patch も含みます。

## 意味が不変であることの確認

修正前後の計器 patch の `+` / `-` 行本文は完全一致しました。変更した文脈行は骨格に追加された seed 呼出しだけです。旧骨格＋旧計器と新骨格＋新計器の適用後 source 差分は、seed 関数まわりの 9 行と `begin()` の呼出し 1 行のみで、削除は 0 行でした。

## test の実走 (または未実走)

焦点 3 nodeid を `tools/run_tests.py` から起動しましたが、`qstat -Q` の事前確認が失敗し、子 test は未起動です。**実装済み・未実走**です。`check_codex_agents.py`、`check_docs.py`、`git diff --check` は成功しました。

## 所有外への波及

静的に確認した参照先は、積み方を定義する `silo_policy_coverage.py`、patch と macro の対応を登録する `condition_meaning_gate.py`、`test_ccbench_spawn_sites.py`、`test_p3_s4_loop.py`、および `patches/README.md` です。いずれも編集していません。

## 総括

計器 patch を新しい骨格へ追随させ、指定された全 patch stack の適用と意味の不変性を確認しました。焦点 test の緑判定は未取得です。commit は作成していません。