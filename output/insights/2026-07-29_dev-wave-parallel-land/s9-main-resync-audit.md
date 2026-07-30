固定 SHA `7be05ef` のまま取り込むのは停止すべきです。静的検査と read-only Git 操作のみを行い、テスト・checker・変更・network access は実施していません。

## Topology と差分

固定入力はすべて実体と一致しました。

| 側 | `0912975..tip` の順序 |
|---|---|
| wave | `43c4ec4` → `16e418b` → `08adb89` (`16e418b`,`0912975`) → `c63a005` |
| main | `72f8858` → `98670a7` → `c75982c` → `6b64d21` (`c75982c`,`0912975`) → `7be05ef` |

`HEAD=c63a005`、local `main=7be05ef`、merge base=`0912975` です。main 側の net diff は T-179 の ledger・fixtures・専用テスト・記録で、T-186 の helper、dev-wave contracts、`test_check_docs.py` を merge base 比で変更していません。`tools/codex_worker_ledger.py` とそのテストの blob は `72f8858` から `7be05ef` まで同一です。

## Real findings

### 1. Blocker — main の merge commit に必須 provenance trailer がない

- 深刻度: 致命的
- 状態: real、merge 前停止
- 箇所: commit `6b64d21753d2cfc790f80caba29df7a40fef3072`
- 証拠:
  - message は `Merge branch 'main' into worktree-dev-wave-t179-worker-ledger` だけで、`AI-Agent:` がありません。
  - 全 commit に trailer が必須です。[ai-provenance.md](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/ai-provenance.md:12)
  - checker は trailer 無しを違反にし、導入 commit から `HEAD` まで全 commit を列挙します。[check_ai_provenance.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/check_ai_provenance.py:174)、[check_ai_provenance.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/check_ai_provenance.py:332)
  - にもかかわらず `7be05ef:docs/worklog.md:1913–1916` は、`0912975` 取込後も `check_ai_provenance.py 違反なし` と記録しています。
- 影響:
  - 規定どおりの全履歴 provenance 検査は `6b64d21` を必ず検出します。記録済み検査結果と実履歴が一致しません。
  - descendant commit では既存 commit message を修復できません。rebase/force や checker 弱体化も [DW-STOP](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/dev-wave/core.md:17)・[DW-O23](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/dev-wave/operations.md:119) が禁止しています。
  - main 所有側の是正または明示的な人間裁定が必要です。どの是正でも main tip SHA が変わるため、新 SHA に対する fresh-context audit をやり直す必要があります。

### 2. High — T-179 の token 不変条件が strict をすり抜ける

- 深刻度: 高
- 状態: real、受入前修正必須
- 箇所:
  - `7be05ef:tools/codex_worker_ledger.py:159–192`
  - `7be05ef:orchestrator/tests/test_codex_worker_ledger.py:323–405`
  - `7be05ef:output/.../focus.md:149–150`
  - `7be05ef:output/.../fix3.md:7–10`
- 証拠:
  - 必須4 field は個別の負値だけ拒否しますが、`cached_input_tokens <= input_tokens` を検査しません。
  - 任意の `reasoning_output_tokens` は型だけ検査し、負値を受理します。
  - 例えば `input=0, cached=1, output=0, total=0, reasoning=-1` は検証を通り、`_billable()` は `-1` を返します。issue がないので `--strict` も rc=0 です。
  - 焦点レビューは「token 各値の非負性と cached/input 条件」を must-fix としましたが、fix3 は必須4 field の負値だけで `closed` としています。
  - negative fixture とテストは4必須 field の単独負値のみです。M9 も既存 `malformed_usage` 登録を丸ごと無効化する変異で、この関係条件には到達しません。
- 影響:
  - 負の session/stage/総 token が T-180〜T-184 の resource envelope、model/reasoning 比較、policy 採否へ流入します。
  - 「10/10 KILLED」は既存10 operator には整合しますが、焦点レビューの token 不変条件全体を閉じた証拠にはなっていません。

### 3. High — 非 null の壊れた usage envelope を黙って捨てる

- 深刻度: 高
- 状態: real、受入前修正必須
- 箇所: `7be05ef:tools/codex_worker_ledger.py:304–320,811–816`
- 証拠:
  - `token_count.payload.info` が `dict` でなければ無条件に `continue` します。
  - `info: null` の互換正例は意図されていますが、`info: []`、文字列、bool も同じく正常無視されます。
  - otherwise healthy session に `info: []` を置くと、model call と token が0へ過少集計されても issue はなく、strict は rc=0です。
  - テストは `info:null` の正例と、`info` が object の場合の各 usage field 型異常しか扱っていません。M9 もこの早期 `continue` より後だけを変異します。
  - commit `72f8858` の「usage の欠損・型異常は fail-closed」という説明とも不一致です。
- 影響:
  - session 数・stage/worklog gateを保ったまま model_calls/token だけを静かに落とせます。凍結10 session の値が一致しても一般 gate の健全性は証明されません。

### 4. Medium — model/reasoning identity の欠落を strict が受理する

- 深刻度: 中
- 状態: real、下流 consumer gate
- 箇所: `7be05ef:tools/codex_worker_ledger.py:195–214,269–280,656–693`
- 証拠:
  - `turn_context` が0件なら model/reasoning は空文字のままです。
  - model/effort が null や非文字列でも `str(...)` により `"None"` 等へ変換され、issue になりません。
  - テストは正常値・object-level schema・複数 context の不一致を扱いますが、欠落・空・型異常を扱いません。
- 影響:
  - T-181/T-182 の model/reasoning 別比較が空 identity または偽 identity に帰属し得ます。
  - 現在 live caller はなく将来 consumer だけですが、T-179 を完了根拠として下流へ進む前に、正当な legacy 形か malformed かを裁定して gate/test を追加すべきです。

### 5. Medium — `F54`、worklog `(64)`、worklog 容量は merge resolution が必要

- 深刻度: 中
- 状態: real、保存型競合。単独では merge 前停止理由ではない
- 証拠:
  - wave の [F54](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/failures.md:987) は T-186。
  - main の `7be05ef:docs/failures.md:987` は T-179。`git merge-tree` の唯一の textual conflict です。
  - wave の [worklog (64)](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/worklog.md:1581) は T-186、main の `7be05ef:docs/worklog.md:1852` は T-179。
  - plan v2 は main resync 時の再採番を明記済みです。[s4-adjudication-plan-v2.md](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s4-adjudication-plan-v2.md:60)
  - worklog は base 84,289、wave 90,212、main 95,712 bytes。両追加をそのまま保存すると約101,635 bytesで、100,000-byte gateを超えます。[check_docs.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/check_docs.py:84)、[check_docs.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/check_docs.py:2090)
- 解消:
  - landed main の T-179 を `F54` / `(64)` として維持。
  - wave の T-186 を `F55` / `(65)` に振り直し、D100、phase、handoff、worklog の参照を一括追随。
  - T-186 entry を main `(64)` 後へ再構成し、T-179 完了と T-180〜T-184 の着手可能状態を保存。
  - 最終サイズに応じて worklog rotation、またはまだ未 land の T-186 entry を worklog の10〜15行索引契約へ縮約し、詳細は既存 insight に残す。
- 影響:
  - 片方を捨てる解決は F台帳・D100・task保存則を破壊します。両記録を独立に保存する解決は可能です。

### 6. Medium — 現在の wave は helper が拒否する dirty 状態

- 深刻度: 中
- 状態: real、land 前の運用 blocker
- 現在の未追跡:
  - `output/insights/2026-07-29_dev-wave-parallel-land/s9-main-resync-audit.log`
  - `output/insights/2026-07-29_dev-wave-parallel-land/s9-main-resync-audit.prompt.md`
- 証拠: helper は wave status に1件でもあれば拒否します。[dev_wave_land.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py:792)
- 影響: 親が所有権を確認して監査成果物として記録するか、適切な外部 handoff へ移すまで、段9 helperは成功できません。

### 7. Medium — `98670a7` の provenance は Codex 寄与を記録していない

- 深刻度: 中
- 状態: real、checker が検出しない provenance completeness 問題
- 箇所: commit `98670a70c43ea15ece05dcb4c349a4afc390f61d`
- 証拠:
  - commit は Codex の author/fix/review 逐語を1,477行追加しています。
  - 同 commit の README は Codex review 3本、implementation/fix 4本を明記します。
  - trailer は Claude author/managerだけです。
  - 採用された finding・review・変更案へ実質的に影響した構成は記録対象です。[ai-provenance.md](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/ai-provenance.md:68)
- 影響:
  - commit 単位の model/reasoning/role 分析が docs統合を Claude-only と誤認します。
  - missing-trailer と異なり現 checkerは検出しませんが、main側の provenance 是正裁定に含めるべきです。

## Refuted / backlog

- refuted — T-186/D100 の番号衝突: main の新規最大は T-185/D99なので、T-186/D100は有効です。parent brief の `T-173` は初期の一時番号で、最終正本はT-186です。ただし [parent-brief.md](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/parent-brief.md:1) の題名には、凍結原文を黙って書き換えず erratum を添えるのが望ましいです。
- refuted — phase state conflict: main のT-179完了とwaveのT-186完了は自動併合可能です。T-180〜T-184 の状態だけ最新 entryから再構成が必要です。
- refuted — dev-wave docs budget超過: mainは `docs/dev-wave/**` を変更せず、wave tipはちょうど24,000 bytesです。merge後も24,000で、超過はしません。ただし余白は0です。
- refuted — T-186 gate/shared-test の弱体化: main net diffはT-186 helper、checker、共有テストを変更していません。RuleOps変更は両tipが既に含むmerge base `0912975` 由来です。
- refuted — topology/hash drift: 指定5 commit、両merge parent、merge baseは一致しました。T-179 README掲載の凍結hashも全件一致しました。
- backlog — `test_tool_import_does_not_create_bytecode_cache` は完全な恒真 assertionではありません。validator importによるpycacheは検出できますが、名前に反してledgerをlibrary importせずscript subprocessを実行するため、ledger自身のimport-time pycacheは被覆しません。T-179 READMEも既知backlogとして記録済みです。
- refuted — `.gitignore` が成果物という現行主張: parent briefの初期案であり、plan v2とD100は明示的に棄却し、実treeも変更していません。

## merge 後に必要な受入集合

以下は未実行です。まず provenance blocker を解消して新しい tested-main SHAを再監査し、その後に固定SHA merge・修正commitを作る必要があります。

1. T-179 targeted acceptance

```text
python3 -m pytest -q orchestrator/tests/test_codex_worker_ledger.py orchestrator/tests/test_check_codex_output.py
```

追加必須負例は cached>input、negative reasoning、非null non-object `info`、turn_context欠落/空/型異常です。各修正には最終commit上の新 mutation operatorと期待failure nodeを固定します。凍結10 sessionについて、完全session ID→stage 10/10、434 model calls、2,757,982 tokens、stage 6値、およびworklog mismatchの期待rc=2を再照合します。

2. T-186 と共有面

```text
python3 -m pytest -q orchestrator/tests/test_dev_wave_land.py orchestrator/tests/test_check_docs.py
python3 orchestrator/tests/test_dev_wave_land.py
python3 tools/run_tests.py -q orchestrator/tests/test_dev_wave_land.py orchestrator/tests/test_check_docs.py orchestrator/tests/test_codex_worker_ledger.py orchestrator/tests/test_check_codex_output.py orchestrator/tests/test_plain_runner_coverage.py
```

T-186の4実装/checker面をmerge resolutionで変更した場合はM1〜M13を最終commit上で再走し、変更しない場合もanchor/source bytesを再確認します。

3. 全受入・文書・provenance

```text
python3 tools/run_tests.py
python3 tools/check_docs.py
python3 tools/check_codex_agents.py
python3 -m py_compile tools/codex_worker_ledger.py tools/dev_wave_land.py tools/check_docs.py
python3 tools/check_ai_provenance.py
```

`check_ai_provenance.py` は導入時点からHEADまで実行します。`6b64d21` を含む現履歴では合格を主張できません。

4. 段9 evidence

- `git status` clean。
- `git diff --check <new-tested-main>..<tested-tip>`。
- merge commitの片親が監査済みwave tip、他方が固定した新main SHA。
- `git rev-list --reverse <new-tested-main>..<tested-tip>` と `--audited-commit` 列が完全一致。
- `F54/F55`、worklog `(64)/(65)`、D100/T-186、phase状態、worklog容量を再確認。
- 全受入を固定した後にだけ `DW-O23` helperを実行。

## 総括

NO-GO