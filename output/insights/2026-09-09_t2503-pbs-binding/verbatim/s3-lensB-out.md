## 1. consumer 閉包

1. Consumer は plan 記載より広い。[ドリフト]

- 所見: 変更対象は自己束縛、test module loader、driver ID、performance surface、Pegasus admission registry、runbook 投影から参照される。二段目まで辿ると次の閉包になる。

  - probe 自身の path tuple → dirty 検査・receipt hash: `t316_sandbox_backend_probe.py:2290-2296` → `:2330-2343`
  - test の `_MODULE_PATH` → `spec_from_file_location` → module 実行: `test_t316_sandbox_probe.py:19-25`
  - driver ID literal → condition gate の独立 oracle: probe `:378,1952` → test `:147,205,241,1012`
  - reviewed perf path →全 production source の AST scan → exact inventory test: `test_official_perf_closure.py:88` → `:518-545` → `:890-897`
  - admission path/class・entry pin → direct command 生成 → registry exact test: `test_hooks.py:3070-3071,3330-3340` → `:3548-3551` → `:3947-3958`
  - runbook path/class/evidence 投影 → `check_docs` の集合照合: `pegasus-runbook.md:495-498,541-542`
- real か refuted か: **real**
- 根拠 file:line: `s2-plan-out.md:100-119` は主に同 test と receipt key しか列挙せず、上記の間接 consumer を閉包へ入れていない。
- 提案: 変更対象を増やさず、影響確認一覧に上記 consumer を明記する。意図した定数変更は各 semantic pin の値を変えない。

2. 「凍結 bytes pin」の反証は射影内では得られない。

- 所見: 射影内に whole-file SHA golden、blob golden、行番号・正規表現による source bytes pin はない。見つかったのは path/class、driver ID、perf surface の semantic pin で、bytes freeze ではない。
- real か refuted か: **refuted**
- 根拠 file:line: `test_official_perf_closure.py:44-94`、`test_hooks.py:3032-3106,3330-3340`、`pegasus-runbook.md:495-498`。提示された SHA は `brief.md:42` にしか現れない。
- 提案: bytes pin 不在の結論自体は維持可能。ただし `FROZEN_MANIFEST` と repo 全体の zero-hit は射影外なので、「この consult でも再検証済み」とは書かない。

## 2. 受入で赤になる経路

1. acceptance ledger と収集規約の主張を一次資料で検証できていない。[手順漏れ]

- 所見: brief/plan は未知 node が default cost 扱いで収集拒否されないと断定するが、射影に ledger と `conftest.py` がなく、一次資料による確認が成立していない。
- real か refuted か: **real**
- 根拠 file:line: `brief.md:43-44`、`s2-plan-out.md:108`。後者が根拠として挙げる `conftest.py:1631-1664` は射影外。
- 提案: ledger を予防的に変更せず、親が実装前に ledger、collection hook、既定 duration、xdist group 割当を直接確認する。

2. helper の Git subprocess に実行時間上限がない。[計測汚染]

- 所見: plan の `subprocess.run` には `timeout=` が指定されておらず、`git commit` hook 等で test が停止できる。対して `_execution_binding` 内の Git は 10秒・15秒で制限される。
- real か refuted か: **real**
- 根拠 file:line: `s2-plan-out.md:46`、`t316_sandbox_backend_probe.py:602-660,2323-2333`。runbook も赤の再走に timeout がない既知限界を記す: `pegasus-runbook.md:997-1000`。
- 提案: helper の各 Git 呼び出しに小さい明示 timeout を付ける。

3. hooks と docs は意図した変更だけでは赤にならない。

- 所見: t316 probe の direct 実行は `dispatch-required` のままだが、pytest 内からの import・subprocess は Bash hook の対象外。path/class/evidence も変わらないため docs 投影更新も不要。
- real か refuted か: **refuted**
- 根拠 file:line: `test_hooks.py:3070-3071,3330-3340`、`pegasus-runbook.md:479-483,495-498,541-542`。
- 提案: probe を login node から直接起動せず、規定 runner で test file/node を指定する。registry・runbookは編集しない。

4. brief の「login node で受入」は authoritative acceptance なら不正確。

- 所見: 単なる診断 test は local 実行可能でも、runbook は非 dispatch の authoritative acceptance では receipt を作れないとする。
- real か refuted か: **real**
- 根拠 file:line: `brief.md:66-67` 対 `pegasus-runbook.md:968-977`。
- 提案: 「計算ノード不要」を削り、実行場所は正規 runner の判定に任せる。authoritative receipt が必要なら dispatch 経路を使う。

## 3. plan の実効性

1. 負例の比較ロジック自体は成立する。[テスト代表性]

- 所見: 正しい実装では `.py` bytes の spool と `.pbs` が異なるため目的の例外へ到達する。比較先を `.py` に戻す変異では hash が一致し、`pytest.raises` が失敗する。完全一致の例外 regex も前段エラーの偽陽性を防ぐ。
- real か refuted か: **refuted**
- 根拠 file:line: `s2-plan-out.md:64-78`、`t316_sandbox_backend_probe.py:2336-2339`。
- 提案: この負例の構造は維持する。

2. Git 環境の隔離順序が逆である。[手順漏れ]

- 所見: numbered plan は step 3 で `git init/add/commit/rev-parse` を実行し、step 4 で `GIT_DIR` 等を消す。ambient Git authority は setup Git に既に作用してしまう。
- real か refuted か: **real**
- 根拠 file:line: `s2-plan-out.md:46-47`。
- 提案: Git 関連環境の除去・固定を repo 作成と最初の Git invocation より前へ移す。

3. `monkeypatch.delenv` と Git identity/template の指定が不足している。

- 所見: `delenv` を通常環境で使うなら `raising=False` が必要。さらに `GIT_AUTHOR_*`、`GIT_COMMITTER_*`、`GIT_TEMPLATE_DIR` が残ると、`-c user.name/email` や signing 無効化だけでは identity override・template hook を封じられない。
- real か refuted か: **real**
- 根拠 file:line: `s2-plan-out.md:46-47,129-130`。
- 提案: `delenv(name, raising=False)`、明示的な author/committer identity、空 template、明示 `cwd=repo_root` または `git -C repo_root` を使う。nested path の親 directory 作成も helper 内で明示する。

4. `.gitignore` と porcelain 判定には本質的な穴はない。

- 所見: 5 path を `git add --all` 後に commit し、spool を repo 外へ置けば、pathspec 付き `git status --porcelain` は空になる。`.gitignore` は不要。
- real か refuted か: **refuted**
- 根拠 file:line: `s2-plan-out.md:37-48,66-69`、`t316_sandbox_backend_probe.py:2330-2335`。
- 提案: status の stdout が空であることを helper 側でも assert すると、fixture setup failure の局所化に役立つ。

## 4. scope 逸脱

- 所見: plan は新しい gate、台帳、framework、互換層、docs 変更を追加していない。正例は「常に目的の例外を投げるだけ」の実装が負例を通るのを防ぎ、負例の非 tautology を支えるため本題内である。
- real か refuted か: **refuted**
- 根拠 file:line: `brief.md:28-33`、`s2-plan-out.md:1-24,60-98,110-119`。
- 提案: 変更は probe の名前付き定数と同 test file の helper・正負2例に限定する。必要な補完は Git setup の順序・timeout・環境固定だけとする。

## 5. 親の実測値と一般化

1. commit と現行 object identity は一致した。

- 所見: `5e12db6ce` では tuple の index 0 が `.py`、index 1 が `.pbs`。`0218acc61` で condition gate path が先頭へ追加され、比較行は index 1 のままである。現行 file SHA-256 は `d7607e0aaf0a13ecdd319776a2b84414d79413cf8269a61df051070de7bce802`、Git blob は `32644847ac6e93ce8ed7a09374a759af3cc82ef0` と再計算できた。
- real か refuted か: **refuted**
- 根拠 file:line: `5e12db6ce:tools/pegasus/probes/t316_sandbox_backend_probe.py:2018-2068`、`0218acc61:tools/pegasus/probes/t316_sandbox_backend_probe.py:2210-2263`、`brief.md:15-19,42`。
- 提案: commit 起因と現行 hash の記述は維持する。

2. monkeypatch の行番号も正しい。

- 所見: 既存 test は `_execution_binding` 全体を1引数 lambda に置換しており、直接被覆にならない。
- real か refuted か: **refuted**
- 根拠 file:line: `test_t316_sandbox_probe.py:1276-1296`、特に `:1282`。
- 提案: 新規 test は `_run_injected` やこの monkeypatch を使わず、関数を直接呼ぶ。

3. receipt SHA と job body の主張は再検証不能で、「必ず落ちる」は過剰一般化である。[テスト代表性]

- 所見: receipt、PBS job body、凍結 manifest が射影されておらず、`44a35985…31b32` も省略表記しかない。二つの過去 receipt から次回すべての spool bytes へ一般化するには、PBS 側の binding を直接確認する必要がある。
- real か refuted か: **real**
- 根拠 file:line: `brief.md:8-24,42-44`。probe 自身も単一 sample の一般化を禁止する: `t316_sandbox_backend_probe.py:2619-2623`。
- 提案: 「必ず」は「job body が committed `.pbs` を spool し、その bytes が `.py` と異なる限り決定的に」に条件化する。親が receipt と PBS body を一次資料で再確認する。

## 6. 変異の帰属

- 所見: `.py` を比較先に戻す変異は、負例だけでなく plan の正例でも殺される。file 全体または正負2 node を同時に走らせると、負例固有の検出力を帰属できない。[テスト代表性]
- real か refuted か: **real**
- 根拠 file:line: `s2-plan-out.md:82-98,133-137`。予測される別 killer は `test_execution_binding_binds_runtime_spool_to_pbs` で、変異時には `t316_sandbox_backend_probe.py:2338-2339` の例外で落ちる。
- 提案: 変異評価は負例 node だけを `expected_nodes` として走らせる。正例と file 全体は通常回帰確認として別走行にする。

既存 test については、目的変異を先に殺す箇所は射影内に見つからない。既存唯一の直接参照は関数全体を monkeypatch する `test_t316_sandbox_probe.py:1282` であり、perf closure と hook tests は比較対象を実行しない。

## 7. 所有範囲

- 所見: author が触るべき file は次の2件だけ。

  - `tools/pegasus/probes/t316_sandbox_backend_probe.py`
  - `orchestrator/tests/test_t316_sandbox_probe.py`

  触ってはいけない file は `test_hooks.py`、`test_official_perf_closure.py`、`docs/pegasus-runbook.md`、acceptance ledger、PBS job body、既存 receipt、凍結 manifest。
- real か refuted か: **refuted**。plan の所有範囲は妥当。
- 根拠 file:line: `s2-plan-out.md:110-119`。runbook の同期対象は path/class/evidence であり、この変更では不変: `pegasus-runbook.md:495-498,541-542`。perf path set も不変: `test_official_perf_closure.py:44-94,890-897`。
- 提案: docs 更新は不要。将来 receipt の source SHA が変わるのは期待動作で、既存 receipt は書き換えない。

## 総括

plan の比較修正と正負 test の核は静的には有効だが、そのまま author へ渡すには次の3点が real blocker である。

- Git 環境隔離を最初の Git invocation より前へ移し、`delenv(..., raising=False)`、identity/template、cwd を明示する。
- helper の全 Git subprocess に timeout を付ける。
- 変異検出力は負例 node 単独で測り、正例による先行 kill と混同しない。

加えて、acceptance ledger・`conftest.py`・receipt・PBS body・凍結 manifest は射影外だったため、親 brief のそれらに関する「実測済み」は本 consult では再証明されていない。pytest は実走しておらず、緑・赤の実測報告はしていない。