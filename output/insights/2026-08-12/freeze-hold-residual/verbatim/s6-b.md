## 総括

BLOCKER 1 件, MAJOR 3 件, MINOR 1 件です。現状の land は不可です。pytest は実行していません。静的検査に加え、書き込みを伴わない clean-env CLI probe のみ実行しました。

## BLOCKER

### 1. 新規 test file が既存の全走を確実に赤にする

根拠:

- 全 `test_*.py` は自走 harness または pytest-only allowlist 登録が必須です: `orchestrator/tests/test_plain_runner_coverage.py:44-74`
- 新規 file は `test_output_does_not_claim_unknown_layer_completeness` の終了が EOF で、`_run()` / `__main__` / `pytest.main()` がありません: `orchestrator/tests/test_hold_inventory.py:150-168`
- allowlist にもありません: `orchestrator/tests/README.md:128-170`

成果物影響: 既存の受入集合で `test_every_test_file_is_self_runnable_or_allowlisted` が `test_hold_inventory.py` を offender として拒否し、全走が赤になります。

推奨対応: scope 内で直すなら `test_hold_inventory.py` に `pytest.main([__file__, "-q"])` を呼ぶ `_run()` と `__main__` を追加してください。README allowlist 追加は段 5 の編集許可外です。

## MAJOR

### 2. CLI は通常の script 起動で import に失敗する

`tools/hold_inventory.py` は shebang を持つ一方、repo root を `sys.path` に入れる前に `orchestrator` を importしています: `tools/hold_inventory.py:1-20`

clean env probe の結果:

```text
env -u PYTHONPATH python3 tools/hold_inventory.py --format json
ModuleNotFoundError: No module named 'orchestrator'
rc=1
```

`python3 -m tools.hold_inventory --format json` は rc=0 でした。

成果物影響: ユーザーが自然な script entrypoint を使うと inventory を取得できず、21 check ID と保留 test 一覧の参照面が欠落します。

推奨対応: repo 内の他の standalone tool と同じ bootstrap を入れるか、module 起動だけを正式契約として usage と test に固定してください。

### 3. bypass surface が不完全で、`effective_status="held"` が偽になる経路がある

inventory は test 層の bypass surface を次の 2 件に固定しています: `tools/hold_inventory.py:95-111`, `orchestrator/tests/test_hold_inventory.py:67-84`

しかし保留の唯一の適用点は conftest hook です: `orchestrator/tests/conftest.py:346-369`。少なくとも次が未記載です。

- pytest の `--noconftest`
- suite conftest より下を指す `--confcutdir`
- test module を import して関数を直接呼ぶ runner
- `PYTEST_ADDOPTS` に上記 option を入れる Pegasus transport

特に `tools/run_tests.py` は未知 option を拒否せず targeted run として扱い、`--confcutdir` は非選択 option に分類しています: `tools/run_tests.py:76-94`, `tools/run_tests.py:390-428`。Pegasus は `PYTEST_ADDOPTS` も transport しますが、inventory は release token 用 env しか記録していません: `tools/pegasus/dispatch_compute.py:56-68`

この状態では release env が未設定でも conftest を無効化すれば test は実行される一方、inventory は `held` と返します: `tools/hold_inventory.py:62-68`

成果物影響: `effective_status` が実際の受理集合と逆になり、保留中と表示された最大 30 function が実行対象へ戻り得ます。

推奨対応: bypass surface に conftest suppression, `PYTEST_ADDOPTS` transport, direct invocation を追加し、status に runner assumption を持たせてください。可能なら runner 側で `--noconftest` と危険な `--confcutdir` を fail-closed に拒否してください。

なお、`-k` は hook が selection 前に skip marker を付けるため実行 bypass ではありません。`--ignore` / `--ignore-glob` / `--pyargs` は collection を狭めますが、保留 test を実行可能にはしません: `orchestrator/tests/conftest.py:322-369`

### 4. 現在の 3 分岐は一致するが、契約テストが conftest との一致を検査していない

現在の対応自体は一致します。

- unset / empty: conftest は opt-in false, inventory は `held`
- exact token: conftest は opt-in true, inventory は `released-by-explicit-user-command`
- その他: conftest は `UsageError`, inventory は `invalid-opt-in-rejected`

根拠: `orchestrator/tests/conftest.py:277-289`, `tools/hold_inventory.py:62-68`

しかし test は inventory 自身だけを呼び、conftest の判定には接続していません: `orchestrator/tests/test_hold_inventory.py:130-147`。今後 conftest だけが変更されても緑のままです。

成果物影響: env 判定の drift 後も inventory の表示値だけが旧状態に残り、解除済み test を held、または拒否される値を released と報告できます。

推奨対応: env 分類を副作用のない共有関数へ抽出して conftest と inventory の両方から使い、test は期待 literal を独立 pin してください。

production 層で `configured_status == effective_status` とすることは現状では妥当です。`HELD=True` が source 上の唯一の解除状態で、各 registered consumer がこの module flag を参照しています: `orchestrator/campaign/freeze_verification_hold.py:14-48`

## MINOR

### 5. `git diff --check: 成功` は現状の変更を検査していない

実装報告は成功としています: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-freeze-hold-residual/s5-author.md:23-30`

しかし両 file は現在 `??` の untracked です。通常の `git diff --check` は untracked file を対象にしないため、この 2 file だけが変更された状態では空の検査です。

成果物影響: whitespace error があっても検査済みと記録され、段 5 の品質証拠が実体を持ちません。

推奨対応: `git add -N` 後に実行するか、各 file を `/dev/null` と `git diff --no-index --check` で検査し、実 command を報告してください。

## 親裁定 1 の再攻撃結果

4 function を保留しない裁定を覆す根拠は見つかりませんでした。

- `_init_repo` は固定 seed から tmp repo を作ります: `orchestrator/tests/test_t793_publication_ledger.py:31-41`
- 対象は固定履歴と固定 payload だけです: 同 `:180-185`, `:259-302`, `:310-350`
- 同型の publication ledger 検査を性質検索しましたが、別の直接検出者は見つかりませんでした。
- D320 は既存 live 検査の無裁定撤去を認めていません: `docs/decisions.md:14532-14538`
- D328 の対象は実装と測定の同一性であり、防壁の自己完全性は対象外です: `docs/decisions.md:14784-14793`
- D335 の対象は repository 成長比例コストです: `docs/decisions.md:14957-14974`

0.14 秒および受入 wall 186 秒は今回再測定していません。ただし、その数値を除いても成長比例性がなく、唯一検出者を失うため、保留へ反転する根拠にはなりません。

## その他の静的確認

- import 時に file 走査、subprocess 起動、socket 接続はありません。
- `dispatch_compute` import は定数と `_TaskSpec` の構築だけです: `tools/pegasus/dispatch_compute.py:45-78`
- 新規 test のコストは明示登録された check ID と hold row 数にだけ比例し、commit 数、repo file 数、docs 量、output 蓄積を走査しません。
- 新規 4 node は `REAL_REPO_SERIAL_NODES` に入らず、`xdist_group("real-repo")` も付きません。実 repo や共有 submodule を読まないため、この判定は正しいです: `orchestrator/tests/conftest.py:354-357`, `orchestrator/tests/test_real_repo_serialization.py:585-615`
- pytest および関連 meta-test は未実走です。緑は主張しません。