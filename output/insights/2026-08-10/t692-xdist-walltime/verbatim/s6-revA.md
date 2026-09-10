### 1. kwargs 負例は二重決定で MT4 を検出できない

- **重大度**: Major
- **主張**: kwargs 検査だけを削除しても負例は拒否され続ける。MT4 の単一理由性を満たさない。
- **根拠**: helper は `len(args) == 1` と `not kwargs` を同じ assert に畳んでいる（[test_real_repo_serialization.py:431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_real_repo_serialization.py:431)）。負例は kwargs-only なので `args` も空である（[同:541](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_real_repo_serialization.py:541)）。`and not kwargs` だけを削除しても `len(args) == 1` で拒否され、テストはそれを意図した拒否と数える（[同:562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_real_repo_serialization.py:562)）。これは事前登録 MT4（[s4-ruling.md:87](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t692-r3-xdist-walltime/s4-ruling.md:87)）を殺せない。
- **成果物影響**: 変異 matrix が kwargs 経路の検出力を証明していないのに、受入 proof chain が同経路を監査済みとして参照する。
- **直し方**: 負例を `xdist_group("real-repo", name="real_repo")` にし、expected names を `{"real-repo"}` とする。これなら失敗理由は kwargs 非空だけになる。

### 2. group 集合負例は missing と extra を同時に起こし、片側緩和を検出できない

- **重大度**: Major
- **主張**: MT5 の「完全一致から部分一致への緩和」が生存する。
- **根拠**: helper の契約は集合の `==`（[test_real_repo_serialization.py:440](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_real_repo_serialization.py:440)）。underscore 負例の actual は `{"real_repo"}`、expected は `{"real-repo"}`（[同:545](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_real_repo_serialization.py:545)、[同:568](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_real_repo_serialization.py:568)）。missing と extra が同時にあるため、`actual <= expected` に変えても extra 側で、`expected <= actual` に変えても missing 側で拒否され続ける。事前登録 MT5（[s4-ruling.md:88](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t692-r3-xdist-walltime/s4-ruling.md:88)）の部分一致変異を区別できない。
- **成果物影響**: group 名閉包の片側が弱体化しても変異証拠に現れず、試行台帳が exact-set 監査の検出力を過大申告する。
- **直し方**: missing-only（actual 空、expected 1 件）と extra-only（正当名＋余分名、expected は正当名のみ）を別々の合成 report として追加する。

### 3. 順序 gate は最終 hook 順と xdist 実行順を束縛していない

- **重大度**: Major
- **主張**: 新設テストが固定するのは conftest 内の list 変換と通常 collection 結果までであり、実効実行順ではない。
- **根拠**:
  - sort hook は非 wrapper の `tryfirst=True`（[conftest.py:249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/conftest.py:249)）。現行 pytest 9.1.1 の `--ff` と `--nf` は wrapper の post-yield で items を再配置する（[cacheprovider.py:363](/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/cacheprovider.py:363)、[同:435](/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/cacheprovider.py:435)）。
  - 合成 meta-test は hook 関数を直接呼ぶため、後続 hook を通らない（[test_real_repo_serialization.py:627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_real_repo_serialization.py:627)）。実 collection subprocess にも外側 argv の `--ff` / `--nf` は渡らない（[同:401](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_real_repo_serialization.py:401)）。
  - live loadgroup test は二 node の worker ID 一致しか検査しない（[同:779](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_real_repo_serialization.py:779)、[同:825](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_real_repo_serialization.py:825)）。
  - 現在の xdist 3.8.0 は insertion 順で index を送る（[loadscope.py:276](/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/scheduler/loadscope.py:276)）が、runner は任意の `>=2.5` を受理し、未導入時は版を pin せず導入する（[run_tests.py:63](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/tools/run_tests.py:63)、[同:253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/tools/run_tests.py:253)）。将来版で FIFO が変わるケースは推測だが、それを検出する歯がないことは現行コード上確定している。
- **成果物影響**: writer が barrier より先に実行されると receipt reader が submodule patch 窓を観測し得て、受入参照が実行順依存になるか、wall 上限で受入結果自体を取得できなくなる。
- **直し方**: marker 付与を wrapper の pre-yield、sort を post-yield に分けて最終順を固定する。さらに live loadgroup probe に A が sentinel を書き、B がその存在を必須とする FIFO 検査を追加する。

### 4. priority node の複数 parameter instance を監査側が誤拒否する

- **重大度**: Minor
- **主張**: 推測（将来の parameter 化時）。hook は複数 instance を正しく同順位で並べるが、監査は先頭二 item を異なる二 node と決め打ちして失敗する。
- **根拠**: instance は `originalname` により同じ canonical node へ畳まれ（[conftest.py:243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/conftest.py:243)）、同じ priority key で安定 sort される（[同:269](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/conftest.py:269)）。一方、監査は raw な `real_repo_order[:2]` を `(CLI, barrier)` と比較する（[test_real_repo_serialization.py:462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_real_repo_serialization.py:462)）。CLI が二 instance なら先頭は `(CLI, CLI)` になる。
- **成果物影響**: priority node の正当な parameter 化だけで全走の収集監査が停止し、受入結果を取得できなくなる。
- **直し方**: consecutive な canonical node を重複除去して先頭二種類を比較するか、全 CLI instance の最大 index が全 barrier instance の最小 index より小さいことを検査する。

## 総括

- **NO-GO**
- **Critical 0 / Major 3 / Minor 1**
- must-fix:
  - kwargs 負例を positional＋kwargs の単一理由 fixture にする。
  - group 集合に missing-only / extra-only の二負例を追加する。
  - sort を hook chain の post-yield で行い、live loadgroup probe で FIFO 実行順を検査する。