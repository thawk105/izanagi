差分境界に注意が必要です. `ccb55574` は `f4681b60` と `a1f81a00` の merge commit です. 従って T-930 の fix 差分は実質 `ccb55574..8a027168`, wave 全体は `ccb55574^2..8a027168` です. `f4681b60..8a027168` には他 wave の変更も混入しています.

## 既存所見の閉鎖判定

| 所見 | 重要度 | 判定 | 根拠 |
|---|---|---|---|
| revA 1 | BLOCKER | partial | fresh B/E は import 時拒否へ移り, 親実測で 38.01 秒から 2.33 秒へ短縮し fixture 未到達. ただし別 session の印と module cache で同じ先払いが再現する. `growth_test_holds.py:218-228,292-301`, `test_campaign_import_invariant.py:1073-1075,1654-1664` |
| revA 2 | MAJOR | partial | campaign fixture node と manual runner へ対象を変更し焦点走も緑. しかし検査は fresh subprocess だけで, nested pytest と stale mark を覆わない. `test_growth_test_holds_contract.py:626-670` |
| revA 3 | MINOR | closed | noncallable 負例と非 ASCII raw JSON pin が追加され, 焦点走で確認済み. `test_growth_test_holds_contract.py:529-555` |
| revA 4 | MINOR | partial | 件数 literal は除去されたが, `test_env_attestation.py` 全 file 実行は残り, file 成長比例コストは未解消. `test_growth_test_holds_contract.py:709-720`, `test_env_attestation.py:1359-1364` |
| revB 1 | BLOCKER | closed | exact token 下の fixture/parametrize は親実測 33 passed, 実 parametrize node は 3 params collection. wrapper は `wraps` を維持. `growth_test_holds.py:245-252`, `test_growth_test_holds_contract.py:593-623` |
| revB 2 | MAJOR | closed | `103 passed, 1 skipped` は rc, refusal 不在, skip, passed >= 1 の意味契約へ置換済み. `test_growth_test_holds_contract.py:709-720` |

`regressed` と判定する既存所見はありません. ただし revA 1/2 は別 session 経路が残るため closed にはできません.

## 新規所見

BLOCKER - process-global な active session 印が別 pytest session と import cache に権限を流し, 成長比例 workload を再び先払いさせる.

根拠: config の実体を保持せず `id(config)` だけを global set に格納し, import 側は現在の config との一致ではなく set が非空かだけを見る. `growth_test_holds.py:218-228,292-293`. mark は公開関数で, canonical conftest 由来かも検証しない. `growth_test_holds.py:221-228`, `conftest.py:520-524`. repository には既に in-process nested `pytest.main()` が存在する. `test_pytest_failure_digest.py:953-967`.

失敗シナリオ: canonical outer pytest が active な間に `pytest.main(["--noconftest", campaign-held-node])` を呼ぶ. held module が未 import なら outer session の印で受理され, import 済みなら import guard 自体が再実行されない. inner session には hold marker がないため session fixture `repository_scan` が走り, その後 call-time wrapper が失敗する. 旧 BLOCKER と同じ 38 秒級の先払いになる. また任意の `-p` plugin が公開 mark API を呼ぶだけでも同じ状態を作れる. これは段 4 が拒否した preload 型の再導入である.

`pytest_unconfigure` の `finally` は通常例外を清掃するが, hook 未到達, 手動 mark, または config が GC された経路では整数が残る. process 終了なら state も消えるが, 長寿命 interpreter 内では stale な非空 set が bearer capability になる. id 再利用は主因ではなく, 現 config と照合しないことが主因である. xdist は process 分離されるため通常走では直接共有しないが, 各 worker 内の nested session には同じ穴がある.

成果物影響: hold inventory は workload が停止済みと報告する一方, 正規 pytest 内の nested runner や plugin preload では real repository scan が実行される. T-930 の中心成果物を破る.

提案: process-global import 許可を廃止する. pytest 経路は current `request.config` に canonical enforcement が結線されていることを検証する fail-fast autouse fixture を, 同 scope の高コスト fixture より先に実行する. manual runner は `_run()` 冒頭で拒否する. nested `pytest.main(--noconftest)`, module cache 済み, forged plugin, stale mark の負例を追加する. `WeakSet` への置換だけでは cross-session 許可を直せない.

MAJOR - `plain_runner` AST 検査は `pytest.main` の存在だけを見ており, delegation の実行を証明しない.

根拠: `__main__` guard 配下の任意の descendant に `pytest.main` call が 1 個あれば delegating と分類する. 到達可能性, call 順序, return/exit との結線は見ない. `test_growth_test_holds_contract.py:337-351`. runtime は AST を見ず, caller が渡した literal と `__name__` だけで受理する. `growth_test_holds.py:296-300`.

失敗シナリオ: `if False: pytest.main(...)` を `__main__` block に置き, 実際には `_run()` を呼ぶ. AST は `pytest-delegating` と判定し, plain execution が import gate を通過して helper scan を実行する. 同様に nested function 内の未呼出 callでも通る. 文字列中の `pytest.main` は AST Call ではないため現実装を騙さない. `getattr(pytest, "main")()` や alias call は逆に manual 扱いとなり fail-closed だが, 正当な delegator refactorを過剰拒否する. `__main__` 外の top-level call は guard より前に実行でき, AST 照合対象にもならない.

成果物影響: 将来の軽微な runner refactorで, 検査が緑のまま manual workload を再開できる. runner 宣言を enforcement 根拠として扱えない.

提案: `__main__` body を strict shape に限定し, terminal statement が直接 `raise SystemExit(pytest.main(...))` または `sys.exit(pytest.main(...))` であることを検査する. dead branch, nested definition, top-level side effect, alias/dynamic callを拒否する. 可能なら runtime 共通 delegator 関数へ一本化する.

MINOR - 件数 pin は解消したが, 新設検査の一部は repo 成長に対して O(1) ではない.

根拠: positive control は `test_env_attestation.py` 全 node を plain Python で実行する. `test_growth_test_holds_contract.py:709-720`, `test_env_attestation.py:1363-1364`. AST binding は全 held file を全文 parseし, wrapper 検査は全 registered module/node を importする. `test_growth_test_holds_contract.py:468-482,510-526`.

失敗シナリオ: `test_env_attestation.py` に無関係な non-held test が増えるたびに実行数と時間が増える. held file の肥大化や registry 追加でも parse/import量が増える.

成果物影響: correctness artifact は直接壊さないが, acceptance cost と保守時間が対象 file及び held surface の成長に比例する.

提案: fixed-size synthetic delegating moduleで non-held sentinel と held sentinel を 1 件ずつ検査する. fresh B/E の対象 node検査は維持してよいが, full file positive controlは局所化する.

## 退行確認

- conftest copy契約: 退行なし. コピー後 bytes一致契約は維持され, `test_pytest_failure_digest.py` を含む親の焦点走も緑. `test_pytest_failure_digest.py:542-550,597-643`.
- `python3 orchestrator/tests/test_env_attestation.py`: 親の焦点走内で rc=0が確認済み. `test_growth_test_holds_contract.py:709-720`.
- canonical golden: 静的な退行は見つからない. collection subprocess は canonical conftestを伴い, `pytest_configure` mark後に held modulesを収集する. goldenと順序検査は不変. `test_real_repo_serialization.py:418-431,522-615`. ただし親実測にはこの fileの実走は含まれない.
- conftestを読まない `--noconftest` は意図した拒否経路. canonical root conftestより前に held moduleを importする正規受入経路は現構成では見つからない.
- xdist通常走は workerごとに canonical conftestが configをmarkするため, 静的には新しい赤経路を認めない. 問題は同一 worker内の nested sessionである.

## 恒真化または検出不能な検査

- `test_noconftest_bypass_is_refused_before_held_body` と `test_plain_runner_bypass_is_refused_before_held_body`: fresh process専用なので, 現在の cross-session bugがあっても緑.
- `test_guard_binding_negative_control_detects_removed_call`: AST checker自身の構文検査であり, unreachable `pytest.main` や runtimeの `plain_runner` 無視を壊しても緑.
- `test_refusal_diagnostic_is_canonical_ascii_json`: call-time wrapperだけを検査する. import-time refusalを非 canonical JSONへ壊しても B/E検査は prefixしか見ないため全て緑になり得る.
- `test_plain_pytest_delegating_runner_is_not_over_rejected`: 対象 moduleの guard bindingを削除しても canonical conftestの skipで単独には緑. 別の binding検査が赤にするため, この test単独の保証範囲を過大評価してはいけない.

## 総括

NO-GO.

最も危険な 1 件は, `_ENFORCING_PYTEST_CONFIG_IDS` が非空というだけで別 sessionの held module importを受理し, nested `pytest.main(--noconftest)` で高コスト fixtureを wrapperより先に実行できることである.