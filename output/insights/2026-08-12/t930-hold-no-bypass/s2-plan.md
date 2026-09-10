# [T-930] 段 2 実装プラン

結論は案 `alpha` を推奨する。conftest の enforcement 印がない状態では module 全体を refuse し、B は collection error、E は stderr に診断を出して exit code 2 とする。通常の A では guard を完全な no-op にする。

案 `beta` は B の node 単位制御に加えて plain harness の個別改修が必要であり、現行 brief のいう「5 本の `_run()`」とも実装実態が一致しない。

## 1. enforcement API

### 公開面

`orchestrator/tests/growth_test_holds.py:4-10,13-16,207-210` に次を追加する。

```python
class GrowthTestHoldBypassRefused(RuntimeError):
    """A held test module was imported without conftest enforcement."""


def enforce_growth_test_hold_module(
    module_file: str | os.PathLike[str],
    *,
    module_name: str,
) -> None:
    ...
```

挙動順序は次で固定する。

1. `module_file` の basename から `GROWTH_TEST_HOLDS` の該当 node を列挙する。0 件なら guard の誤設置として `ValueError`。
2. 正規 conftest の sentinel 印があれば即 return。env の検査もしない。これにより A の invalid-token 診断順も既存 conftest に残す。
3. `IZANAGI_RUN_GROWTH_HELD_TESTS` が既存 token `explicit-user-command` と完全一致すれば return。
4. unset、空、または typo なら refuse。
5. `module_name == "__main__"` なら診断を stderr に 1 回出し、`raise SystemExit(2)`。
6. それ以外は `GrowthTestHoldBypassRefused` を送出する。B では pytest の collection error と exit code 2 になる。

診断 prefix は literal で固定する。

```text
IZANAGI_GROWTH_HOLD_BYPASS_REFUSED_V1
```

JSON payload には少なくとも `module`、`held_node_ids`、`release_env`、`release_token` を入れ、`ensure_ascii=True` とする。新しい解除口は作らない。

### enforcement 印

`growth_test_holds.py:13-16` に private sentinel を置く。

```python
_GROWTH_TEST_HOLD_ENFORCEMENT_SENTINEL = object()
```

`conftest.py:41-55` はこの private sentinel を import し、自 module 属性へ置く。

```python
_IZANAGI_GROWTH_TEST_HOLD_ENFORCEMENT = (
    _GROWTH_TEST_HOLD_ENFORCEMENT_SENTINEL
)
```

guard は `sys.modules` の次の module だけを確認し、その属性が同一 sentinel である場合だけ有効と認める。

```python
("conftest", "orchestrator.tests.conftest")
```

親実測の A は `conftest`、契約テストの import は `orchestrator.tests.conftest` なので、両方が必要である。

`conftest.py:47-55` の fallback では属性を `None` にする。`conftest.py:58-74` の lazy load が成功した場合にも同じ sentinel 属性を設定する。

public な `activate()` は作らない。呼べば有効になる API は、既存 env 以外の事実上の解除口になるためである。

### sentinel を選ぶ理由

採用するのは「conftest module 属性に置いた sentinel object の identity」である。

落選案は次のとおり。

- module の存在だけを見る案: B/E の guard 自身が `growth_test_holds` を import した時点で seam が消える。
- boolean module 属性: `True` や別 object の誤代入でも有効になり、正規 conftest 由来かを区別できない。
- activate 呼び出し記録や counter: reload、同一 process 内の pytest 再入、failure-digest の別名 import で履歴が残る。また public setter が新しい解除口になる。
- pytest fixture による node 単位 guard: A に autouse fixture を追加しうるため、「A では完全 no-op」という不変条件を守りにくい。

## 2. held module への結線

各 file に public guard の import と呼び出しを 1 組ずつ置く。呼び出しは test function 実行前であれば、module 末尾でも import-time enforcement である。

| file | 挿入位置 |
|---|---|
| `test_campaign_import_invariant.py` | `:23-28` の root 設定と既存 import の後 |
| `test_codex_reasoning_ab.py` | `:4268-4269`、実 `__main__` の直前 |
| `test_env_attestation.py` | `:18-23` の `sys.path` 設定後 |
| `test_s8b_binding_driftguards.py` | `:535-536`、実 `__main__` の直前 |
| `test_s8b_repo_scan_invariant.py` | `:14-18` の root 設定と production import 後 |
| `test_ruleops.py` | `:22-24` の root 設定後 |
| `test_s8b_holdout_freeze.py` | `:17-25` の root 設定と既存 import 後 |
| `test_s8b_oracle_driver.py` | `:27-30` の root 設定後 |

各 file の実装は原則 2 logical lines である。

```python
from orchestrator.tests.growth_test_holds import enforce_growth_test_hold_module
enforce_growth_test_hold_module(__file__, module_name=__name__)
```

5 本の plain harness だけでなく、pytest-only の 3 file も direct execution 時に exit 2 とする。これにより「held module を直接起動したのに静かに 0」は残らない。

既存 `_run()`、`pytest.main()`、台帳の 30 row は編集しない。

## 3. P2 の決着

### 案 alpha

B/E では held node を含む module 全体を refuse する。

- B: 8 file 全てが collection error。
- E: 5 harness file も pytest-only 3 file も exit 2。
- A: conftest sentinel により全 guard が no-op。非保留 node は従来どおり実行され、保留 node だけ既存 hook が skip する。
- 実装費: 8 file x 2 lines、conftest の sentinel 結線、registry API。plain harness の改修なし。

非保留 node を B/E で実行したければ、正規 A を使うか、既存の明示 token を使う。この wave では B/E を第二の受入経路として維持しない。

### 案 beta

node 単位を維持するには、import-time の module exception は使えない。少なくとも次が必要になる。

- B 用に 30 held function への decorator、または 8 module 全てへの conditional autouse fixture / namespace rewrite。
- E 用に manual harness が held function を呼ばず、かつ nonheld function を続行し、最後に非 0 を返す結線。
- `test_campaign_import_invariant.py:1654-1704`: 最低 5 logical lines。held function の partition、`scan_repository()` の eager 実行抑止、refusal 出力、exit code 上書きが必要。
- `test_codex_reasoning_ab.py:4269`: 最低 2 logical lines。ただし許可された範囲には `__main__` の header しかなく、body を静的に確定できないため、実装可能な正確な行数を保証できない。
- `test_env_attestation.py:1359-1360`: 現在の inline `pytest.main()` を rc 保存と refusal rc 上書きの 2 logical lines に変更。
- `test_s8b_binding_driftguards.py:536-540`: 同じく 2 logical lines。
- `test_s8b_repo_scan_invariant.py:38-51`: held body を呼ぶ前の診断と return 2 に最低 3 logical lines。

合計は判明分だけで最低 14 logical lines の harness 改修に加え、B の node-level 結線が要る。

さらに、`pytest.skip(allow_module_level=True)` と collection error はどちらも module 全体を止めるため、案 beta とは両立しない。beta なら B は function-level `pytest.mark.skip` 等の第三案が必要になる。

以上から、親が示した「harness 侵襲を強いるなら alpha」の条件は成立している。案 alpha を推す。

## 4. P3 の決着

### B

`pytest.skip(allow_module_level=True)` ではなく collection error とする。

理由は次のとおり。

- `--noconftest` は正規 hold plugin が判断した skip ではなく、enforcement 自体を外した実行である。
- module-level skip は rc 0 になり、正規 A の hold と bypass refusal を automation が区別できない。
- collection error なら held body は collection 前に止まり、解除方法も診断に残る。
- A の skip 受理集合は sentinel no-op により変えない。

期待 exit code は 2。

### E

全 8 held module の direct Python invocation は診断後 exit code 2 とする。traceback だけに依存せず、API 自身が prefix 付き診断を stderr へ出す。

これにより、plain harness の 5 fileだけでなく、これまで 0 件で終わっていた pytest-only 3 file も静かな rc 0 にはならない。

## 5. メタテスト

全て `orchestrator/tests/test_growth_test_holds_contract.py` に追加する。既存 `_run()` の `pytest.main()` 経路 `:309-315` はそのまま使える。

### binding 検査

`test_growth_test_holds_contract.py:4-9` に `ast`、`os`、`subprocess` を追加する。

`GROWTH_TEST_HOLDS` から file 名集合を導出し、各 source を AST で検査する helper を `:105-116` 付近に置く。

各 file について次を要求する。

- `enforce_growth_test_hold_module` の正規 import が 1 個。
- top-level 呼び出しが厳密に 1 個。
- positional argument は `__file__`。
- keyword `module_name` は `__name__`。
- plain harness file では呼び出しが top-level `if __name__ == "__main__"` より前。
- registry 由来 file が実在する。

テスト名の例:

```python
def test_every_held_module_has_exact_import_guard_binding():
    ...
```

恒真性を避けるため、同じ helper に in-memory で guard call を 1 個除去した AST/source を渡す負例を置く。

```python
def test_guard_binding_negative_control_detects_removed_call():
    ...
```

期待 file 集合を guard 実装側から importしてはならない。producer は registry、consumer は source AST とし、guard を外せば必ず binding test が赤になる。

### A の no-op 検査

現在の contract process では `CONF` が `:17` で import 済みである。この状態で env token を消し、held module 名を public guard に渡して例外が出ないことを確認する。

既存 `:173-203` が skip marker は 1 個だけと検査しているため、これと組み合わせて「guard no-op + conftest skip 1 個」を固定できる。

### B の実挙動

fresh subprocess で親と同じ形を起動する。

```text
python3 -m pytest --noconftest -p no:cacheprovider -q \
  orchestrator/tests/test_campaign_import_invariant.py::test_repository_scan_set_is_nonempty_and_contains_sentinels
```

検査項目:

- cwd は repo root。
- env から既存 opt-in と `PYTEST_ADDOPTS` を除去。
- return code は 2。
- stdout + stderr に literal prefix と対象 node id がある。
- `1 passed` がない。
- timeout や signal 終了を refusal 成功として扱わない。

guard call を外すと binding test が直ちに赤になり、実挙動 test も held body の pass または timeout になるため赤になる。

案 alpha を固定するため、同じ partial module の nonheld node を `--noconftest` で指定しても rc 2 になる test を 1 件追加する。

### E の実挙動

次を fresh subprocess で起動する。

```text
python3 orchestrator/tests/test_campaign_import_invariant.py
```

期待値:

- return code 2。
- refusal prefix がある。
- `PASS ` と末尾の `passed` summary がない。

加えて pytest-only 代表として `python3 orchestrator/tests/test_ruleops.py` も rc 2 と prefix を要求する。guard を外せばこちらは従来の静かな rc 0 となるため、安価で強い負例になる。

### 唯一の解除口

同じ B subprocess で、既存 token を明示し、campaign module 内の軽い nonheld node を指定する positive control を置く。

- exact token: rc 0、`1 passed`。
- typo token: rc 2、refusal prefix。
- 新 env や別 token は使わない。
- held body を positive control で走らせないため、契約テスト自身が保留コストを復活させない。

診断 prefix と exit code は test 側の独立 literal にする。producer 定数をそのまま期待値として importすると、producer と consumer の同時退行で恒真化する。

## 6. 既存契約への影響

### (a) A 経路の受理集合

壊さない。

- conftest は held module より先に registry を importする `conftest.py:41-46`。
- sentinel はこの import 成功時に設定する。
- module guard は sentinel を見て副作用なしで return。
- skip と metadata の付与は従来の `conftest.py:346-375` だけ。
- opt-in typo の `pytest.UsageError` は `conftest.py:277-289` に残る。

したがって skip marker は 1 個、非保留 node の実行、xdist metadata、summary は変更しない。

### (b) failure-digest の conftest copy と plain-import fail-open

壊さない。

- plain import consumer は `test_pytest_failure_digest.py:32-42`。
- copy と走行後の bytes 同一検査は `:542-550`。
- `ModuleNotFoundError("orchestrator")` fallback は `conftest.py:47-55` に残し、sentinel 属性を `None` にするだけ。
- copy は変更後の real conftest を複製して同じ real file と比較するため、conftest bytes の変更自体は golden 破壊ではない。
- fallback 時には public guardも registry も実行しない。

`test_pytest_failure_digest.py` 自体は編集しない。

### (c) `test_plain_runner_coverage.py`

機械契約は壊さない。

- checker は `__main__` 後の harness signal の存在だけを見る `:25-41`。
- 5 file の既存 `_run()` / `pytest.main()` signal は削除しない。
- pytest-only 3 file は README allowlist `README.md:128-170` に残る。
- test の期待値緩和や skip 化はない。

ただし README の説明 `:107-126` にある「direct invocation は実走または意図的 no-op」は、held module だけ refusal へ変わる。段 7 の親記録で「held module は exact opt-in 無しでは import-time refusal」と追記すべきである。これを不変の実挙動契約と解釈するなら alpha は開始不可で、beta の再設計が必要になる。

### (d) `test_real_repo_serialization.py` の canonical golden

壊さない。

- golden は `test_real_repo_serialization.py:35-84` の `REAL_REPO_SERIAL_NODES` 独立集合。
- equality と実 collection は `:567-615`。
- 本案は `REAL_REPO_SERIAL_NODES`、priority、`xdist_group` marker を変更しない。
- A では guard no-opなので collection count と marker count は同じ。
- held module に手書き `xdist_group` decorator も追加しない。

したがって canonical golden は編集しない。

## 7. 親 brief への反論と条件

### P1

趣旨には賛成する。A は既に塞がっているため、B と executable E を閉じるのが裁定の実質である。

さらに alpha を採るなら、pytest-only 3 file の direct rc 0 も同じ guard で rc 2 にする。これは held body の実行穴ではないが、「held module direct invocation の静かな成功」を残さないためである。

### P2

provisional beta には反対し、alpha を推す。

また「5 本の `_run()`」という前提は source と一致しない。

- `_run()` が確認できるのは campaign `:1654-1704` と repo scan `:38-51`。
- env attestation `:1359-1360` と binding driftguards `:536-540` は inline `pytest.main()`。
- codex reasoning は許可された末尾範囲で `__main__` header しか確認できず、body の改修量を確定できない。

この不一致自体が、beta を段 5 に渡せる精度で起草できない理由である。

### P3

B の module-level skip provisional には反対する。missing enforcement は legitimate hold ではなく runner misuse なので collection error が正しい。E は exit code 2 とする。

### 実装開始条件

段 4 で次を明記してから実装へ進む。

1. B/E は module 単位 refusal とし、partial module の nonheld node を B/E で維持しない。
2. A の node 単位受理集合だけを bit 単位不変対象とする。
3. pytest-only 3 file の direct rc 0 も rc 2 へ変更する。
4. README の plain-runner 説明差分は段 7 の親所有で記録する。
5. 並行 wave を先に land し、`growth_test_holds.py` を main 再取り込み後に再読してから実装する。

この 5 条件のどれかを採れない場合は alpha を実装せず、beta 用に `test_codex_reasoning_ab.py` の実 harness body を読める scope を取り直して段 2 から再起草する。

静的検査のみであり、pytest は実行していない。

## 総括

推奨案は `alpha + B collection error + E exit code 2` である。private sentinel を conftest module 属性へ置き、8 held module の public guard が identity を検査する。解除口は既存 env token 1 本だけとする。

最大のリスクは、partial module の nonheld node と pytest-only file の direct no-opまで B/E で拒否し、README の plain-runner 説明を狭める点である。一方、A の受理集合、failure-digest copy、plain-runner の構造メタテスト、real-repo canonical golden は変更しない。

実装開始の条件は、段 4 でこの module 単位 refusal を明示採択し、並行 wave の land 後に `growth_test_holds.py` を再同期することである。