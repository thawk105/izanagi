## 方針と編集範囲

行番号は現行 worktree 基準。編集は `orchestrator/tests/test_codex_reasoning_ab.py` のみに限定する。

**一時 repo の合成 blob と合成 rollout を使い、production の二経路を最後まで実行する案を採る。** 正例は既存 m2 node を改修して残し、mismatch 負例を隣に追加する。今回は静的読解のみで、編集・git 状態変更・pytest 実行は行っていない。

## 1. 撤去する範囲

対象は `orchestrator/tests/test_codex_reasoning_ab.py:3569–3587`。

| 現行行 | 扱い |
|---|---|
| `:3569–3571` | 関数名と `monkeypatch` を残し、引数に `tmp_path` を追加 |
| `:3572–3573` | 削除。既定 sessions root と歴史 rollout の availability guard 呼出しを撤去 |
| `:3574–3582` | 比較関数の呼出し観測と実関数への委譲を残す。比較入力の記録も追加 |
| `:3583` | 合成 repo・sessions root・明示的 `task_manifest` を渡す呼出しへ置換 |
| `:3584` | 呼出し到達の assert を残す |
| `:3585–3587` | 歴史 SHA の assert を削除し、合成 golden 全体の bytes 一致へ置換 |

理由：**関数を消さず、歴史 bytes 依存だけを除いて、既存の「production が比較を実行する」性質を常時実行へ戻す。**

同ファイル `:6` の M2 node 名も維持できる。`_require_pinned_rollouts` 本体 `:794–800`、自己検査 `:963–995`、source-bound node `:9152` は変更しない。

## 2. 常時実行 node の骨格

`orchestrator/tests/test_codex_reasoning_ab.py:3569` の直前に、両 node 専用の小さな合成入力 helper を置く。既存の `_synthetic_task_manifest`（`:6581`）と `_write_synthetic_benchmark_rollout`（`:836`）を使う。

**正例：`test_m2_production_golden_requires_both_routes` を維持。**

- `tmp_path` 内の合成 repo・3 rollout・manifest を用意する。
- `_apply_patch_set` と `_apply_patch_set_independent` に、実関数へ委譲する観測 wrapper を置く。結果を作る stub にはしない。
- `_compare_golden_routes` も現行 `:3577–3582` と同様に実関数へ委譲し、入力を記録する。
- `derive_independent_golden(repo, sessions_root, task_manifest=manifest)` を呼ぶ。`verify_source_sha` は指定せず既定の `True` を使う。
- 次を assert する。
  - route A は integrated blob と fix2 patch を受け取り、`reverse=True` で実行された。
  - route B は base blob と author → fix1 の順の patch を受け取り、順適用された。
  - 比較へ渡った両辞書が、独立に記述した期待 bytes 辞書と一致する。
  - 比較呼出しは 1 回、返った golden も期待辞書と一致する。

到達先は `tools/codex_reasoning_ab.py:956–978`。別 parser は `:685` と `:841`、別適用実装は `:784` と `:893`。

**負例：`test_m2_production_golden_rejects_route_mismatch` を現行 `:3588` 付近に追加。**

- 同じ合成構成で、fix1 patch の追加行だけを変更する。
- 改変後 rollout の SHA を manifest に入れ、SHA 検査も patch 適用も正常に通す。
- 比較 wrapper は入力を記録して実関数へ委譲する。wrapper 自身では例外を投げない。
- 呼出しを次の形で囲む。

```python
with pytest.raises(TOOL.ValidationError) as caught:
    TOOL.derive_independent_golden(
        repo, sessions_root, task_manifest=manifest
    )

assert caught.value.rc == TOOL.RC_SNAPSHOT
assert caught.value.reasons == (
    f"independent golden mismatch for {TOOL.PATCH_PATHS[0]}",
)
assert len(comparisons) == 1
assert comparisons[0] == (expected_route_a, expected_route_b)
assert expected_route_a != expected_route_b
```

`_compare_golden_routes`（production `:912–922`）を `return dict(route_a)` にすると例外が出ず、**`pytest.raises` が必ず失敗する構造**になる。これは静的な成立条件であり、変異実測結果ではない。

## 3. 合成入力と採用案

**blob の選択肢を比較する。**

| 案 | 内容 | 判断 |
|---|---|---|
| 現行 commit の blob を使う | production `:957`・`:963` の歴史 commit を維持し、実 blob から合成中間状態への patch を構成する | 復元可能だが、大きな歴史本文に依存し、親 repo reader の登録判断も必要になる |
| module 定数を一時差替え | `tmp_path` に小さな repo を作り、base・integrated の 2 commit を作成。両 commit 定数だけを `monkeypatch` する | **採用。** 小さな入力で各段の寄与を明示でき、実 `_git` と両 parser を通せる |

既存例は `orchestrator/tests/test_codex_reasoning_ab.py:2417–2454` の一時 repo 作成と、`:2461–2462` の commit 定数差替え。新 helper では参照削除など、この検査に不要な操作は持ち込まない。ここでいう repo 作成は**親による実装後のテスト処理の計画**であり、この段では実行しない。

`PATCH_PATHS`・`TRACKED_PATHS`（production `:225–236`）は差し替えない。各対象 path に対して、次の 4 状態をテスト側の literal として定義する。

| 状態 | 各ファイルの bytes |
|---|---|
| base | `b"base\n"` |
| author 後 | `b"authored\n"` |
| golden | `b"golden\n"` |
| integrated | `b"integrated\n"` |

author patch は、各 `PATCH_PATHS` に以下の update block を持たせる。

```text
*** Begin Patch
*** Update File: tools/check_ai_provenance.py
@@
-base
+authored
*** Update File: orchestrator/tests/test_check_ai_provenance.py
@@
-base
+authored
*** End Patch
```

同じ envelope で、fix1 は `-authored` / `+golden`、fix2 は `-golden` / `+integrated` とする。各 session に patch 呼出しを **1 件**入れる。これにより：

- route A：integrated に fix2 を逆適用 → golden。
- route B：base に author、fix1 を順適用 → golden。

負例は fix1 の **最初の path だけ** `+golden-mismatch` にする。除去側の `-authored` は維持するため適用可能で、比較時だけ不一致になる。

rollout は以下の手順で組む。

1. `_synthetic_task_manifest`（test `:6581–6599`）で独立の manifest を作る。
2. `_write_synthetic_benchmark_rollout`（`:836–857`）で、各合成 session ID の session metadata を持つ JSONL を作る。
3. 各 JSONL に次の形の row を追加する。message に patch を埋め込むだけでは抽出されない。

```python
{
    "type": "response_item",
    "payload": {
        "type": "custom_tool_call",
        "name": "apply_patch",
        "input": patch,
    },
}
```

4. **追加後の全 bytes** の SHA-256 を計算し、`shared_provenance.auxiliary_sessions[label]` の `session_id`・`rollout_sha256` を設定する。

抽出条件は production `:664–673`、manifest 経由の pin 解決・SHA 検査は `:932–950`。helper の返す追加前 SHA を流用しない。

期待値を production の適用結果から生成しない。これは歴史 anchor の復元ではなく、明示した合成状態遷移を別実装で導出・照合する検査とする。

## 4. 登録簿の更新

**採用案では、両登録簿とも更新不要。** 根拠は `tmp_path` の使用だけでなく、親 repo・共有 submodule・登録済み共有 fixture を新 node が利用しないことにある。

生成規則は次のとおり。

- `orchestrator/tests/conftest.py:260–441`：`_REAL_REPO_NODE_INVENTORY` は手書き `frozenset`。fixture や `_git` 呼出しから自動生成していない。
- 同 `:612–656`：手書きの分類集合からアクセス辞書を生成。`:642–647` で分類集合の和と inventory の完全一致を要求する。
- 同 `:659–662`：公開分類集合と resource 集合を設定する。
- 同 `:2144–2152`：収集 node を辞書・resource 集合で引き、登録済み node に marker を付ける。
- `orchestrator/tests/test_real_repo_serialization.py:1592–1615`：上記公開集合・辞書と独立 golden を比較する。
- 同 `:1437–1467`：session/module scope の共有 fixture を対象に、登録 node を seed とした consumer 閉包を要求する。

新 node は function scope の `tmp_path`・`monkeypatch` と通常 helper のみを使い、`benchmark_snapshots`（test `:860–863`）を使わない。したがって手書き集合も共有 fixture 閉包も変わらない。

親の P1-c は、**この入力構成に限定すれば成立**する。「`benchmark_snapshots` を使わなければ常に登録不要」とは一般化しない。

## 5. 受理集合を広げないことの固定

新負例では、production `:915–921` が現在拒否する「適用後 bytes の不一致」を、次の 3 点で固定する。

- `pytest.raises(TOOL.ValidationError)`。
- `caught.value.rc == TOOL.RC_SNAPSHOT`。
- `caught.value.reasons` が対象 path の mismatch 理由だけであること。

さらに比較入力の実記録を assert し、manifest・SHA・patch context の失敗を mismatch 検査の成功と取り違えない。

production は変更せず、`verify_source_sha=True`（`:929`）も維持する。既存の guard/SHA 負例（test `:985–995`）、rollout 不在・重複検査（`:7735`）、pin 結線検査（`:8887`）も残す。有限の assert だけで全入力を証明したとはせず、**production 無変更と既存検査維持に、新たな mismatch 拒否の固定を加える**。

## 6. 変異事前登録の候補

以下の node 名はすべて `orchestrator/tests/test_codex_reasoning_ab.py::` 配下。

| 変異箇所・内容 | 赤になる予定の node |
|---|---|
| `tools/codex_reasoning_ab.py:912–922`：比較せず `dict(route_a)` を返す | `test_m2_production_golden_rejects_route_mismatch`：例外が出ない |
| 同 `:978`：比較呼出しを飛ばして route A を返す | 負例、および `test_m2_production_golden_requires_both_routes` の比較到達 assert |
| 同 `:960`：`reverse=True` を `False` にする | 正例：integrated に順適用できない |
| 同 `:969`：author/fix1 の順を反転する、または fix1 を省く | 正例：context 不一致、または golden 不一致 |
| 同 `:965`：`_apply_patch_set_independent` を `_apply_patch_set` に置換 | 正例：独立適用関数の呼出し観測が欠ける |

既存の歴史 mutation ledger は変更しない。上記は候補であり、殺傷結果の実測は親に委ねる。

## 総括

既存 m2 を合成正例へ改修し、隣に production 比較まで到達する mismatch 負例を追加する。
一時 repo の commit 定数だけを差し替え、実 git・独立 parser・SHA 検査を通す。
編集は test 1 ファイルで完結し、採用構成では登録簿更新は不要。
最大の risk は、負例が比較前のエラーで止まり、比較恒真化を殺せないこと。
比較入力・例外理由の assert で構造を固定し、実測は親が行う。