## BLOCKER: `conftest` の単なる import が enforcement の証明になり、第 7 経路が成立する

根拠 (実在): plan は `sys.modules["conftest"]` または `sys.modules["orchestrator.tests.conftest"]` の属性が sentinel と同一なら、env や `module_name` の検査より先に return する設計である。[s2-plan.md:28-33](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t930-hold-no-bypass/s2-plan.md:28) [s2-plan.md:45-67](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t930-hold-no-bypass/s2-plan.md:45)

一方、contract module は pytest plugin 登録とは無関係に canonical conftest を通常 import している。[test_growth_test_holds_contract.py:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/test_growth_test_holds_contract.py:17) 実際の保留処理は conftest module の存在ではなく、pytest が hook を登録して `pytest_collection_modifyitems` を呼んだ場合だけ行われる。[conftest.py:346-375](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/conftest.py:346)

静的帰結 (推論): 次の G 経路では、active hook がないのに sentinel だけが存在する。

```bash
python3 -c 'import orchestrator.tests.conftest; import runpy; runpy.run_path("orchestrator/tests/test_campaign_import_invariant.py", run_name="__main__")'
```

canonical conftest の import で sentinel が置かれ、guard は no-op になる。その後、brief で E 経路 `30 passed` と実測済みの manual `_run()` が実行され、held 6 node も走る。[brief.md:40-43](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t930-hold-no-bypass/brief.md:40)

B も次の形で再開できる。

```bash
python3 -m pytest --noconftest \
  -p orchestrator.tests.test_growth_test_holds_contract \
  -q orchestrator/tests/test_campaign_import_invariant.py::test_repository_scan_set_is_nonempty_and_contains_sentinels
```

`-p` で登録されるのは contract module であり、そこから通常 import された `CONF` は plugin 登録されない。しかし sentinel は立つため、held module の guard だけが解除される。

さらに private sentinel は Python 上のアクセス制御ではない。import した sentinel を偽 `conftest` module の属性へ置けば同じ解除ができる。これは plan が避けるとした public `activate()` と実質的に同じ第 2 の解除口である。[s2-plan.md:69-79](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t930-hold-no-bypass/s2-plan.md:69)

fail-open 側も同じ欠陥を持つ。plan は lazy load 成功時にも sentinel を設定するが、現行 `_ensure_growth_test_holds_loaded()` は registry を importするだけで、pytest plugin 登録を検証しない。[s2-plan.md:67](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t930-hold-no-bypass/s2-plan.md:67) [conftest.py:58-74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/conftest.py:58)

失敗シナリオ: env token を設定せず、canonical conftest の事前 import、`-p` plugin、または sentinel 偽造後に held module を実行する。guard は存在して呼ばれるが、held body が走る。

成果物影響: `growth_test_hold_inventory()` の `count=30` と key digest は変わらない一方、実際には held node が実行される。[growth_test_holds.py:215-228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/growth_test_holds.py:215) active hook がないので hold summary も出ず、受理結果と台帳が食い違う。certified selection の値を直接書き換えなくても、その受理証拠は成立しない。

提案: `sys.modules` の永続属性を認可根拠にしない。held function 自身に、既存 exact env token 以外では本体を呼ばない node-level wrapper を置く。早期 collection 拒否も必要なら、実際の pytest lifecycle に限定した短命な補助状態と併用する。任意の `-p` や `sitecustomize` を攻撃者として扱うなら、Python process 内の private object は防壁にならないため、外部 launcher で plugin と環境を固定するか、その攻撃面を明示的に scope 外と裁定する必要がある。

## BLOCKER: `--collect-only` 後の同一 process 再入で import-time guard は再実行されない

根拠 (実在): plan は各 held module の top-level import 時に 1 回だけ guard を呼ぶ。[s2-plan.md:82-106](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t930-hold-no-bypass/s2-plan.md:82) B/E メタテストはどちらも fresh subprocess だけである。[s2-plan.md:201-237](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t930-hold-no-bypass/s2-plan.md:201) plan 自身も、同一 process の `pytest.main()` 再入で履歴が残る危険を認識しているが、選んだ sentinel と module import に同じ危険を適用していない。[s2-plan.md:77-80](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t930-hold-no-bypass/s2-plan.md:77)

この repository には実際に in-process `pytest.main()` runner がある。[test_growth_test_holds_contract.py:309-315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/test_growth_test_holds_contract.py:309) [test_codex_reasoning_ab.py:4269](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/test_codex_reasoning_ab.py:4269)

失敗シナリオ:

```python
import pytest

pytest.main([
    "--collect-only",
    "-q",
    "orchestrator/tests/test_campaign_import_invariant.py",
])
raise SystemExit(pytest.main([
    "--noconftest",
    "-q",
    "orchestrator/tests/test_campaign_import_invariant.py::"
    "test_repository_scan_set_is_nonempty_and_contains_sentinels",
]))
```

第 1 run は正規 conftest 下で held module を importするが body は走らない。第 2 run では test module が `sys.modules` に残れば guard 自体が再実行されない。再 importされた場合でも conftest sentinel が残るため no-op になる。新しい item には第 1 run の item-local skip markerが引き継がれず、held body が走る。skip marker は collection item にだけ追加されている。[conftest.py:346-375](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/conftest.py:346)

成果物影響: 提案済みの fresh subprocess tests と AST binding tests は全て緑のまま、同一 process runner だけが held node を受理する。hold summary と試行台帳は第 2 run の実行を保留済みとして表現できず、runner 依存の受理集合が残る。

提案: module import を最終防壁にしない。held function の呼び出し時にも exact env token を検査する backstop を置く。また、1 subprocess 内で `collect-only -> --noconftest execution` を行う実挙動テストを必須にする。

## BLOCKER: 正規 A の中でも non-held item から held function を実行できる

根拠 (実在): A では held module import 前に conftest sentinel が存在することを no-op 条件にする。[brief.md:27-29](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t930-hold-no-bypass/brief.md:27) [s2-plan.md:28-30](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t930-hold-no-bypass/s2-plan.md:28)

現行 hook は、収集された item の file basename と function name から node id を作り、その item だけへ skip を付ける。[conftest.py:314-319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/conftest.py:314) [conftest.py:346-375](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/conftest.py:346) Python function の別 item からの呼び出しは監視しない。

失敗シナリオ: registry 外の test file が正常な A で次を行う。

```python
from orchestrator.tests import test_campaign_import_invariant as target

def test_wrapper():
    assert target._run() == 0
```

target import 時は正規 conftest があるため guard は no-op になる。collection hook が見るのは `test_wrapper` だけなので skip されず、manual `_run()` が held 6 node を含む 30 tests を実行する。

成果物影響: A のレポートでは元の held item に skip が 1 個付き、同じ held body は wrapper 経由で実行されうる。従って skip count、`collected_hold_functions`、inventory は見かけ上正しいまま、A の実際の実行集合だけが拡大する。これは「A は bit 単位不変」より強い反例であり、certified acceptance の正しさ境界を破る。

提案: file-level import guard ではなく、registry の 30 function 全てへ node-level execution guard を結線する。通常 A では既存 skip により wrapper 本体は呼ばれず、B/E、再入、別 test からの直接呼び出しでは exact token がない限り本体へ入らない構造にする。non-held wrapper からの呼び出しを subprocess で負例化する。

## MAJOR: メタテストは構文結線を証明するが、実効境界を証明しない

根拠 (実在): binding test は canonical import、top-level call、引数形を AST で検査し、負例も in-memory source から call node を除くだけである。[s2-plan.md:164-193](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t930-hold-no-bypass/s2-plan.md:164)

実挙動 E test は campaign と ruleops を対象にする。[s2-plan.md:223-237](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t930-hold-no-bypass/s2-plan.md:223) しかし brief が実測した真の E bypass は campaign と `test_s8b_repo_scan_invariant.py` であり、ruleops は `__main__` がなく、元から held node を 0 件しか実行しない。[brief.md:31-43](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t930-hold-no-bypass/brief.md:31)

A no-op testも、contract module が先に `CONF` を通常 importした状態をそのまま認可するため、最初の BLOCKER の偽 seam をテスト仕様として固定する。[s2-plan.md:195-200](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t930-hold-no-bypass/s2-plan.md:195) [test_growth_test_holds_contract.py:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/test_growth_test_holds_contract.py:17)

失敗シナリオ: guard call が全 file に構文上存在していても、canonical conftest の先読み、same-process 再入、または別 item からの呼び出しでは no-op になる。全 proposed test は緑になりうる。また repo-scan file だけで import 名を call 前に no-op へ再束縛しても、plan に列挙された AST 条件は満たせるが、その file の実挙動 test はない。

成果物影響: test report は「8 file binding 済み、B/E 封鎖済み」と主張できる一方、実際の第 2 E bypass と G/H/I 経路が残る。certification が syntactic presence を実効 enforcement と誤認する。

提案: 次を実挙動 matrix に追加する。

- canonical conftest を通常 importしただけの G 経路
- `--noconftest -p <preload plugin>` 経路
- 1 process 2 回の `pytest.main()` 経路
- non-held wrapper からの held function 呼び出し
- 実測済み第 2 E bypass の `test_s8b_repo_scan_invariant.py`
- 通常 A と xdist worker の skip 1 個、body 0 回

AST 負例だけでなく、held body の副作用が発生していないことを subprocess で観測する必要がある。

## MAJOR: alpha は node 台帳を実質的な module-wide hold に変える

根拠 (実在): brief の訂正では、`test_env_attestation.py` と `test_s8b_binding_driftguards.py` の direct runner は既に pytest conftest を読み、非 held nodes を実行しつつ held node だけを skip する。blanket `__main__` refusal はこの正常経路を壊すと明記されている。[brief.md:44-51](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t930-hold-no-bypass/brief.md:44)

plan の alpha は、それでも全 8 modules の direct invocation を rc 2 にし、partial module の non-held nodes も B/E では拒否する。[s2-plan.md:110-119](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t930-hold-no-bypass/s2-plan.md:110) [s2-plan.md:154-158](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t930-hold-no-bypass/s2-plan.md:154)

さらに plan は `test_plain_runner_coverage.py` の harness signal が残ることを理由に「契約は壊さない」としながら、直後に direct invocation の意味が変わると認めている。[s2-plan.md:276-285](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t930-hold-no-bypass/s2-plan.md:276)

失敗シナリオ: `python3 orchestrator/tests/test_env_attestation.py` は従来の `103 passed, 1 skipped` から、non-held 103 nodes を 1 件も走らせず rc 2 へ変わる。`test_codex_reasoning_ab.py` も `pytest.main()` に到達しない。[test_codex_reasoning_ab.py:4269](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/test_codex_reasoning_ab.py:4269) それでも harness signal の構造検査は緑になる。

成果物影響: registry と inventory は node-level 30 rows のままなのに、B/E の実効 hold 集合は同じ modules の全 non-held nodes に拡大する。A root pytest の集合とは別件だが、plain-runner report と台帳が実効受理集合を表さなくなり、従来 direct runner が供給していた非 held coverage も消える。

提案: alpha を実装都合だけで採らない。beta 相当の node-level enforcement を採るか、module-wide refusal を新しい policy としてユーザーに明示裁定させ、inventory schema、README、plain-runner の実挙動 testを同時に変更する。

## MAJOR: reload で sentinel identity が変わり、正規 A が collection error になる

根拠 (実在): sentinel は `growth_test_holds.py` の module import ごとに生成する `object()` で、conftest はその時点の object を属性へコピーする。guard は identity を要求する。[s2-plan.md:43-65](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t930-hold-no-bypass/s2-plan.md:43) plan 自身が reload を考慮対象としている。[s2-plan.md:77-80](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t930-hold-no-bypass/s2-plan.md:77)

失敗シナリオ:

```python
import importlib
import orchestrator.tests.conftest
import orchestrator.tests.growth_test_holds as holds

importlib.reload(holds)
# この後、まだ import されていない held module を A で collect
```

conftest 属性は旧 object、reloaded guard は新 objectを見る。active conftest hook が正しく登録済みでも guard は enforcement 不在と誤判定し、held module import を collection error にする。

成果物影響: A の `1 skipped` が rc 2 の collection errorへ変わり、完全 collection の missing-key 検査へ到達しない。worker ごとに reload 履歴が異なる場合は xdist の受理集合も process 依存になる。これは brief の A bit 不変条件への直接違反である。

提案: reloadable module の object identity を A の認可条件にしない。少なくとも reload と同一 process 再入を A の実挙動試験へ追加する。根本策は sentinel を廃止し、node-level execution guardを最終防壁にすることである。

## 総括

判定: **STOP**

最も危険なのは、canonical conftest の単なる import を active enforcement と誤認する sentinel seam である。guard を削除も改変もせず、env token も使わずに G 経路と `-p` 経路から held node を実行できる。その状態を proposed A no-op test 自身が正しいものとして固定するため、実装して検査を緑にしても封鎖は成立しない。

静的検査のみであり、テストは実行していない。