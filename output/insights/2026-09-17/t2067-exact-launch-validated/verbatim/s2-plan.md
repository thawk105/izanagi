## 前提の検算

射影の必読ファイルはすべて読めた。以下は静的検査による計画であり、テスト実行結果ではない。ファイル編集・git 状態変更・pytest 実行は行っていない。

行番号は現在の作業木を基準とする。以下、略記を用いる。

- `D` = `orchestrator/campaign/s8b_oracle_driver.py`
- `R` = `orchestrator/campaign/s8b_ratified_freeze.py`
- `T` = `orchestrator/tests/test_s8b_oracle_driver.py`
- `N` = 新規 `orchestrator/tests/test_s8b_gate_core_exact_launch_validated.py`

**二読 fallback の到達経路は成立する。** `D:615` の初回 `_load_verified_freeze` が失敗すると、`D:619` は `verified` なしで core を呼ぶ。`D:458` の再読が成功して v2 document を返し、adapter が発火しなければ `D:487` に進む。token・`ratified`・`ratified_error` がいずれもなければ、`D:496` が static loader を呼び、sha256 一致だけでこの枝の refusal がなくなる。

ただし、初回失敗→再読成功だけで必ず `allowed=True` になるわけではない。receipt、known-axes、floor、budget、任意の manifest の refusal も空である必要がある。

**brief の callsite 数は訂正が必要。** `gate_check` 内の core 呼び出しは「4 箇所」ではなく **5 箇所**。`ratified=` を渡すのは **2 箇所**である。

| core 呼び出し | 到達条件 | core 側の経路 |
|---|---|---|
| `D:619` | 初回 freeze load 失敗 | `D:458` で再読。再失敗なら既存の読取 refusal 集約。再読 v2 成功なら修正対象 |
| `D:632` | 初回 load 成功、v1 | `verified=loaded` を使用。adapter または v1 verifier |
| `D:646` | v2 static loader が `RatifiedFreezeError` | `verified=loaded` と `ratified_error`。`freeze-ratify:` と後続診断を集約 |
| `D:655` | v2 static loader がその他の例外 | 同上。例外型名を含む error 翻訳 |
| `D:677` | full launch validation 成功 | `launch_validated.ratified` を優先。`verified` の document/hash は使わない |

`ratified=` の実引数は `D:624` と `D:638` だけで、`D:646`・`D:655` は既に `ratified_error=` のみを渡す。

既存 5 node の静的な整合性は次のとおり。

| node | 検算結果 |
|---|---|
| `T:5783::test_v2_standalone_gate_check_requires_full_floor_validation` | 正常系は public loader→launch 1 回→`D:677`。末尾の injected 経路も `D:641`→`D:664` で full validation を受ける。core の fallback 撤去とは独立 |
| `T:4198::test_nonnull_floor_without_active_generation_is_refused` | **public gate のテストではなく `run_block` のテスト**。`D:1330` の active 解決失敗で戻り、core に達しない |
| `T:2842::test_gate_check_core_rejects_reverified_freeze_token` | `D:436` の既存 exact-type 検査で拒否。この検査を保持すれば期待値は変わらない |
| `T:5850::test_private_validated_gate_has_only_run_block_as_production_caller` | public signature と private caller を変更しないため期待値は変わらない。既存テストの維持であり、caller 閉包テストの新設ではない |
| `test_s1_known_axes_freeze.py:1135::test_historical_oracle_nonadapter_reaches_current_semantics` | core を `verified=loaded` で直接呼ぶ。既定 freeze の `floor`・`budget` は `output/s8b-freeze/holdout_freeze.json:622`・`:623` でともに null。v1 経路を維持すれば期待値は変わらない |

したがって「無変更で通る見込み」はあるが、**「無変更で緑」は未確認**。また no-active payer などには既存の growth hold があり、通常実行で skip されたものを検証済みとして数えてはいけない。

`D:687` の `_gate_check_validated` は独自の exact-type 検査後、token を core に渡す。`run_block` は `D:1346` で launch validation、`D:1360` 以降で要求 freeze の実 bytes hash 照合を行い、`D:1402` で private gate を呼ぶ。この経路は変更不要。

`real_repo_ratified_memo.py:37` の説明も維持できる。public `ratified=` は候補注入、public `ratified_error=` は `D:607` からの早期 return であり、loader 例外から core へ入る診断集約の代替ではない。

## production 差分の具体案

**推奨は P1 維持、P2 修正、P3 修正。**

- P1：core の freeze 再読は残す。
- P2：今回要求された直接注入の負例を成立させるため、core の既存 `ratified` 引数は残す。ただし admission には一切使用しない。
- P3：loader を例外 fake にせず、hash が一致する合成 `RatifiedFreeze` を返す fake にする。

**変更箇所：`D:487`〜`:508`。**

既存 `D:436` の非 None token に対する exact-type 検査を保持し、v2 枝を次の形にする。

```python
# adapter 非発火、floor または budget が non-null の既存 v2 枝
if ratified_error is not None:
    refusals.append(f"freeze-ratify: {ratified_error}")
elif launch_validated is None:
    refusals.append(
        "v2-execution: launch-validate: "
        "LaunchValidatedFreeze exact type が必要"
    )
elif (
    freeze_sha is None
    or freeze_sha != launch_validated.ratified.sha256
):
    refusals.append(
        "freeze-not-active-generation: "
        "与えられた freeze bytes sha256 が承認束縛済み active 世代と不一致"
    )

# 既存の known-axes / floor / budget / manifest の診断集約を維持
```

新規 refusal は次の **1 文字列**に確定する。

```text
v2-execution: launch-validate: LaunchValidatedFreeze exact type が必要
```

`orchestrator/`・`tools/` の検索では既存の同一文字列はなかった。既存の「validated freeze object の型が不正」とも区別できる。

`ratified_error` を先に判定するのは I3 のためである。逆順にすると `D:646`・`:655` で既存の `freeze-ratify:` が新しい token 欠落 refusal に置換される。両方 append する案も既存集合を変えるため採らない。

**sha256 比較は今回残す。**

`D:449`〜`:451` は document/hash を `launch_validated.ratified` から取り出す。そのため通常の immutable な `RatifiedFreeze` と文字列 hash では、後段の比較は同じ object の同じ値同士であり、一致は恒真である。これは要求された `freeze_path` と active 世代の独立な照合ではない。

ただし、既存条件の `freeze_sha is None` は、constructor で作った malformed token に対する refusal を持っている。条件全体を削除すると、その入力の受理集合を広げうる。今回は既存条件と refusal を残し、恒真的な比較の整理は差分に混ぜない。`run_block` の実 bytes と token の独立な照合 `D:1360`〜`:1377` はそのまま残る。

**docstring 改訂箇所：**

| 現在位置 | 改訂内容 |
|---|---|
| `D:418`〜`:422` | token の同一 object 使用、`verified` 使用、両方なければ legacy loader を 1 回呼ぶ、という説明を保持 |
| `D:424`〜`:427` | manifest object の共有・再束縛の説明を保持 |
| `D:429`〜`:435` | static ratified を v2 検証結果として扱う説明と core self-load の説明を削除 |
| 同置換部分 | 「floor または budget が non-null の v2 枝は exact `LaunchValidatedFreeze` を要求する。`ratified` 単独では admission を満たさない。`ratified_error` は従来の `freeze-ratify:` に翻訳する。core は static loader を呼ばない」と記載 |

現行の「floor/budget が両方 null でない」は曖昧なので、「いずれかが non-null」に直す。

**P2 を採らない理由。**

依頼の新規 node (ii) は、core に `ratified=<合成>` を渡し、構造化 refusal を観測することを要求している。引数を削除すると観測結果は `TypeError` になり、この要件を満たさない。既存引数の保持は新しい互換層の追加ではない。

保持案では public/core の signature と callsite を変更しない。core の `ratified` は未使用となり、public `ratified` は引き続き `D:641` の候補として使う。core `ratified_error` は v2 枝の翻訳で使う。

削除案を親が選ぶ場合の実差分は、core `D:412`〜`:414` の引数削除、`D:624` の `ratified=ratified` 削除、`D:638` の行削除だけ。`D:646`・`:655`・`:677` に引数整合の変更は不要。ただし node (ii) の要件を同時に変更する必要がある。

**再読を残す案と撤去する案：**

| 観点 | 残す案・推奨 | 撤去する案 |
|---|---|---|
| 受理集合 | token なし v2 の受理だけを閉じる | 初回失敗→v1 再読成功の既存経路も失う |
| refusal 集合 | 二読とも失敗した場合、二読目の例外と既存診断を維持 | 初回例外を渡すと例外本文が変わりうる |
| 変更面 | v2 枝約 22 行の置換と docstring | `D:455`〜`:463`、`D:615`〜`:625`、例外受渡し用 signature/docstring に拡大 |
| 差分量 | production は数十行規模 | 上記に追加で十数〜数十行。意味を維持するなら再読を wrapper へ移す必要もある |

後者で I3 を守ろうとすると、単なる撤去では済まない。D1872 の対象である static self-load だけを取り除く前者を選ぶ。

## 新規 test file の設計

ファイル名は **`orchestrator/tests/test_s8b_gate_core_exact_launch_validated.py`** とする。既存 `T` から helper を import しない。

新規ファイル内で次を直接構築する。

- `driver._freeze_io.VerifiedFreeze(document, sha256)`
- `driver.s8b_ratified_freeze.RatifiedFreeze(...)`
- 同 module の `VerifiedFloorArtifact(...)`
- 同 module の `LaunchValidatedFreeze(...)`
- `driver._t080_migration.ReceiptResolution("never-issued", (), None, "a" * 40)`

`R:751` の docstring は production constructor の使用を制限するもので、テストに対する同じ制限を述べていない。既存 `T:2820` も直接構築している。型同一性を守るため、**driver が保持する module の型**を使用する。

document は次の小さい合成値で足りる。

```python
{
    "floor": {},
    "budget": {},
    "known_axes_freeze": {"path": "known.json"},
}
```

空 dict は non-null であり、truthiness と non-null 判定の混同も検出できる。hash は合成 raw bytes の SHA-256 とし、`VerifiedFreeze` と `RatifiedFreeze` に同じ値を渡す。

**receipt / adapter の扱い。**

`_resolve_t080_receipt` は `verify_receipt`→`_capture_head` を呼ぶ（`D:166`、`t080_freeze_migration.py:2284`・`:637`）。Git repo 外の空 tmp root なら通常は Git エラーが構造化 refusal になり、単に receipt がないから `never-issued` になるわけではない。tmp root が repo 内なら親 repo の探索も起こりうる。

したがって public 経路では `_resolve_t080_receipt` を上記の合成 resolution に置換する。direct core にはそれを直接渡す。`D:246` の条件により `_t080_adapter_refusals` は実関数のまま `None` を返す。adapter 自体を空リストで置換しない。空リストでも `is not None` を満たし、対象の v2 枝を迂回してしまう。

known-axes verifier は `driver.s1_known_axes_freeze.verify` を no-op に置換する。manifest は原則省略する。その他の production verifier を広く無効化する fixture は作らない。

新規 node は以下とする。`R_missing` は上記の確定 refusal を表す。

| node 名 | 入力・観測点 |
|---|---|
| `test_public_reread_v2_requires_launch_validated` | `_load_verified_freeze` に `[OracleDriverError("first read failed"), loaded]`。static loader は hash 一致 ratified を返す。`allowed=False`、refusal exact `{R_missing}`、legacy loader 2 回、static loader 0 回、launch 0 回 |
| `test_core_static_ratified_does_not_authorize_v2` | direct core、`verified=loaded`、`launch_validated=None`、`ratified=synthetic`。`both`・`floor-only`・`budget-only` を parameterize。missing refusal と必要な null refusal の exact 集合、static loader 0 回 |
| `test_core_exact_launch_validated_preserves_predicates` | exact token を direct core に渡す。同じ 3 ケース。`both` は `allowed=True`・空集合、片側のみは既存の null refusal だけ |
| `test_core_rejects_launch_validated_subclass` | `LaunchValidatedFreeze` の subclass instance。既存の型不正 refusal だけ。`isinstance` への緩和を検出 |
| `test_public_ratified_load_errors_preserve_refusals` | 初回 verified 成功後、static loader が `RatifiedFreezeError` / `RuntimeError` を送出。`freeze-ratify:` と既存 null refusal を exact 固定し、missing refusal が混ざらないことを確認 |
| `test_public_explicit_ratified_error_keeps_early_return` | public `ratified_error="sentinel"`。exact `{"freeze-ratify: sentinel"}`、freeze/static/launch loader は 0 回 |
| `test_public_two_failed_reads_preserve_refusals` | legacy loader が 2 回とも失敗。二読目の例外による holdout refusal、known-record 欠落、floor-null、budget-null を exact 固定 |
| `test_core_launch_validated_missing_hash_remains_refused` | exact token だが ratified hash は `None`。既存 `freeze-not-active-generation:` を exact 固定し、sha 条件全削除による受理拡大を検出 |
| `test_cli_gate_check_transports_missing_token_refusal` | 第 1 node と同じ race を in-process `main(["gate-check", ...])` へ通す。rc=2、stdout JSON の refusal と既存 field 集合を確認 |

第 1 node は修正前なら、static loader が 1 回呼ばれ、hash が一致し、他の診断を通過して **`allowed=True` になる fixture**である。これを変異 KILL の中心にする。`AssertionError` fake だけでは、旧実装も例外を捕捉して拒否するため、受理差の観測として弱い。

exact refusal の helper は新規ファイル内に小さく置き、`T:285` と同じく **集合と件数の両方**を比較する。既存ファイルは import も編集もしない。

Git 初期化・履歴走査・実 active 解決・実 submodule・emitter fixture・subprocess は不要。`tmp_path` と合成 object、局所 patch だけなので、conftest の real-repo access map（`:430`〜`:438`、`:528`〜`:530`）への登録は不要。追加 node 全体は **1 秒級を目標**とするが、未計測であり保証値ではない。

## 変異 matrix の事前登録候補

対象行は修正前のアンカー。実装後に同じ式・枝の実行位置へ対応付ける。

| 変異 | 対象 | 期待 KILLED node |
|---|---|---|
| token 欠落枝に static self-load＋hash 一致による受理を復活 | `D:487`〜`:508` | `test_public_reread_v2_requires_launch_validated` |
| `type(x) is not LaunchValidatedFreeze` を `not isinstance(x, LaunchValidatedFreeze)` に変更 | `D:436`〜`:437` | `test_core_rejects_launch_validated_subclass` |
| missing-token refusal の append を削除 | 新 v2 枝 | `test_public_reread_v2_requires_launch_validated`、`test_core_static_ratified_does_not_authorize_v2[both]` |
| core の v2 判定を floor の non-null だけに変更 | `D:476` | `test_core_static_ratified_does_not_authorize_v2[budget-only]` |
| core の v2 判定を budget の non-null だけに変更 | `D:476` | `test_core_static_ratified_does_not_authorize_v2[floor-only]` |
| public の v2 判定を片側だけに変更 | `D:628`〜`:630` | `test_public_ratified_load_errors_preserve_refusals` の片側ケース |
| `launch_validated is None` でも `ratified` があれば受理 | 新 missing-token 枝 | `test_core_static_ratified_does_not_authorize_v2[both]` |
| error 翻訳より missing-token 拒否を優先 | 新 v2 枝 | `test_public_ratified_load_errors_preserve_refusals` |
| sha 条件を全部削除 | 新 token 有り枝 | `test_core_launch_validated_missing_hash_remains_refused` |
| missing-token refusal を重複追加 | 新 v2 枝 | 第 1 node の exact 集合＋件数 |
| public `ratified_error` を通常 core 経路へ流す | `D:607`〜`:610` | `test_public_explicit_ratified_error_keeps_early_return` |

各片側判定の変異では、v1 verifier 側で別 refusal が増えても exact 集合の差として検出される。例外 fake による偶然の拒否だけを成功条件にはしない。

等価または契約内では等価になりうる候補も分けて記録する。

- token 有り枝の `freeze_sha != launch_validated.ratified.sha256` **だけ**を削除し、`freeze_sha is None` を残す：通常の immutable object/string 契約では恒等比較なので等価になりうる。
- core に残した未使用 `ratified` の内部代入を増減する：観測されないなら等価。KILL 数に算入しない。
- `ratified_error` と missing-token の順序変更は等価ではない。static loader 失敗の既存経路で refusal が変わる。
- exact→`isinstance` は `ReverifiedFreeze` の既存負例だけでは殺せない。両型は非継承なので、新規 subclass 負例が必要。

caller inventory や source 全走査を固定する新規メタテストは追加しない。

## 焦点テスト集合と影響範囲

`orchestrator/tests/` と `tools/` を文字列検索し、対象関数・helper・埋込み subprocess script を追った。以下は静的探索結果であり、権威ある caller 閉包ではない。

**直接 consumer：**

| 対象 | consumer |
|---|---|
| `_gate_check_core` | `T:2859`、`test_s1_known_axes_freeze.py:1154`・`:1169` |
| `gate_check` | `T:1601`（helper 内の subprocess script）、`:1793`、`:3053`、`:3123`、`:3462`、`:3542`、`:4667`、`:4799`・`:4810`・`:4815`、`:5809`・`:5826`・`:5843` |
| driftguards の `gate_check` | `test_s8b_binding_driftguards.py:321` |
| public `ratified=` | `T:5844`。その他の同名 keyword は主に token constructor・別 API |
| `ratified_error=` | `T:5150`・`:5234` は private gate を置き換える recording fake の引数。実 core への注入ではない |
| `freeze-not-active-generation` | `T:6485` の run-block 負例、期待値 `T:6505` |
| `freeze-ratify` | `_NO_ACTIVE_REFUSAL` `T:127`、memo 説明・翻訳テスト |
| `tools/` | 関連する driver 呼出しなし。`check_ai_provenance.py` の `ratified=` は waiver trailer の日付で無関係 |

**helper 経由を二段追った結果：**

- `T:3122` のローカル `gate()` → public gate。親 node は `test_gate_check_rebinds_each_injected_verified_manifest_axis`。
- `_run_with_real_manifest_gate` `T:2989` → `run_block` → private gate/core。親 node は `T:3034` の spec 正負例。
- `_run_v2` `T:5754` → `run_block` → private gate/core。consumer は `T:4603`、`:5868`、`:5985`、`:6051`、`:6446`、`:6511`、`:6565`、`:6596`、`:6626`、`:6680` の node。
- `_run` `T:2951`、`_run_required_preflight` `T:3167`、`_run_required_fixture` `T:3291` は private gate を差し替える。これらの通過は実 core の検証証拠に数えない。
- `_t080_stub_free_e2e_repo` `T:964` → `_build_t080_stub_free_e2e_repo` `T:1364` → child script の gate `T:1601`。consumer は `T:1735`、`:1835`、`:1924`、`:2156`、`:2182`、`:4753`。共有 base 構築経路 `T:929` からも同 builder に至る。
- driftguards の `_broken_binding_manifest` `:230` 前後 → `driver_fixtures._synthetic_freeze` / `_write_manifest` → `:249` の run-block node、`:300` の gate node。
- `real_repo_ratified_memo.py:112` の patch → `memo_loader:105` → `real_repo_ratified:92`。consumer は `T:3725`・`:4229`、driftguards `:249`・`:300`。`test_real_repo_serialization.py:2390` が payer とこの opt-in 集合を確認している。

**実装後の第一焦点集合：**

1. 新規 `N` 全 node。
2. brief 指定の既存 5 node。
3. `T` の以下の node。

```text
test_spec_matching_gate_and_run_reach_execution_but_other_spec_refuses_without_outputs
test_gate_check_rebinds_each_injected_verified_manifest_axis
test_real_freeze_gate_lists_floor_and_budget_null
test_t080_gate_hermetic_primary_states_exact
test_tampered_freeze_fails_source_verification
test_never_issued_generator_tamper_reaches_public_driver_gate_g7
test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing
test_active_resolution_and_manifest_structure_refusals_are_aggregated
test_cli_subprocess_returns_rc_2_on_gate_refused
test_run_block_reuses_launch_validated_and_legacy_loader_is_dead
test_run_block_verifies_manifest_once_and_reuses_object
test_v2_gate_happy_path_completes_and_binds_env_store_receipt
test_v2_floor_disk_swap_after_launch_uses_same_validated_object
test_v2_freeze_bytes_not_active_generation_is_refused
```

4. `test_s8b_binding_driftguards.py` の以下の node。

```text
test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal
test_run_block_broken_binding_manifest_refuses_and_writes_nothing
test_ratified_memo_delegates_to_production_loader_exactly_once
test_ratified_memo_reraises_the_production_exception_object
test_ratified_memo_patches_the_module_object_the_driver_uses
test_ratified_memo_refuses_roots_other_than_the_real_repository
```

T080 builder 経由と残る v2 統合 consumer は受入全走の対象に含める。通常焦点走は `tools/run_tests.py` 経由、受入全走は brief 指定の `tools/dev_wave_wait.py acceptance --lease-optional` を用いる計画とし、この段では実行しない。

既存 growth hold は解除しない。skip された node は「期待値を静的に確認、実行未確認」と報告する。追加テストの所要と受入 5 分上限は、後段の実測で判定する。

## リスクと未確定点

**I1 の文言と I3 の診断集約には解釈上の境界がある。** 推奨案は、token のない v2 を必ず `allowed=False` にする一方、既存の known-axes／floor／budget／manifest の診断評価は続ける。I1 の「gate predicates へ進める」を「predicate を一切呼ばない」という意味で読むと、`ratified_error` 経路の既存診断を残す I3 と両立しない。親の計画確定時には「admission を許さない、拒否理由の集約は続ける」と明記すべきである。ここを黙って early return に変更しない。

また、現行 core は adapter 分岐が v2 分岐より先にある。今回の計画は指定された **adapter 非発火の v2 枝**を修正する。任意に構築した document/token まで含めて adapter より前に型必須条件を移す変更は、この最小差分には含めない。

その他の確認点は以下。

- **public injected ratified：** `D:641`〜`:664` を変えないため、`T:5843` の injected 候補は従来どおり launch validation を受ける。core に残す同名引数とは役割が異なる。
- **CLI JSON：** `GateDecision` と `asdict(decision)` は変更しない。field 構造・通常 rc は不変。二読 fallback の場合だけ refusal 内容と allowed/rc が意図どおり変わる。
- **既存 CLI テストの限界：** `T:5054` は名前に gate とあるが、実際のコマンドは `run-block`（`:5070`）。新規 in-process `gate-check` node で今回の transport を直接観測する。
- **no-active 集合：** `T:3746`・`:4224`・`:4255`・`:5084` は run-block 側の翻訳を期待する。`D:1330`〜`:1344` を変更しない。
- **hash 比較の意味：** core に残す比較を、独立した requested-path/active 検証の証拠として説明してはいけない。独立照合は run-block の処理である。
- **P2：** 引数削除と、指定された「core への `ratified=` 注入で構造化 refusal」を同時には採れない。本計画は後者を優先する。
- **性能：**新規 node は履歴量に依存しない構成だが、合計 1 秒級は設計目標。未実測値を受入実績として記録しない。

## 総括

core の legacy 再読を残し、v2 枝の static self-load を撤去する。既存 error 翻訳を優先したうえで、exact `LaunchValidatedFreeze` がなければ確定した refusal を追加する。public API、run-block、既存テストファイルは変更しない。

P2 は直接注入負例との整合から引数保持へ修正し、P3 は hash 一致の合成 ratified を返す fake に修正する。これにより、旧 fallback が許可する入力を新規テストで明確に拒否へ変え、fallback 復活変異を観測できる。既存 5 node の期待値との静的整合は確認したが、緑・KILLED・所要時間はいずれも後段での実行確認事項である。