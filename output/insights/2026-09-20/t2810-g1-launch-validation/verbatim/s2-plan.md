## 変更面 (file:line と変更内容の表)

行番号は提示された worktree の現行コード基準。P1〜P3 に従い、実装子の変更は `orchestrator/` の code / test に限定する。

| file:line | 変更内容 |
|---|---|
| `orchestrator/campaign/s8b_ratified_freeze.py:240` | `_JOURNAL_KEYS` に binding 無しの `reservation-preflight` を追加。既存の `dict[str, frozenset]` を維持する |
| 同 `:2049` | 対象 2 event だけ、binding 無し / 2 key 付きの exact 集合を選択する |
| 同 `:2075`、`:2167` | binding の型、reservation field の型、両 event の claim 一致を検査する |
| 同 `:3161` | 保証境界を `I_entry ⊆ [C, G]` と世代文書導入 `{G}` に更新する |
| 同 `:3536` | result / closure の一意導入・非 merge・祖先区間を検査。世代文書導入集合 `{G}` を追加する |
| `orchestrator/tests/test_s8b_ratified_verify.py:483`、`:628` | 独立 fixture に result / closure を C と同時導入する option を追加する |
| 同 `:2838` 周辺 | 新 topology 正例、lineage / journal 負例を追加。wrong_g=A の既存負例を維持する |
| `orchestrator/tests/test_s8b_oracle_driver.py:131` | comment と `_ACTIVATED_G1_REFUSALS` の第 2 要素を N1 に更新する |
| `orchestrator/tests/test_s8b_binding_driftguards.py:287`、`:326` | 共用定数への参照を維持し、焦点走で更新値の伝播を確認する |
| `docs/phase3-8b-restart-runbook.md:163`、`:332` | 親が P3 / W-3 を現在形へ更新。live policy 拒否と historical reverify の候補 hit を区別する |

変更禁止は `expected_admission_policy` (`:3304`)、`_active_chain_exempt_exact` (`:3029`)、`_selector_evidence_exempt_exact` (`:2781`)、cert C の条件 (`:3526`)、`_JOURNAL_KEYS["session"]` (`:262`)。既存 `output/` 成果物、候補文書、その bytes / pin を変更しない。

## journal allowlist の実装案 (P2)

**allowlist の値型は変えず、`_exact_keys` に渡す期待集合を対象 event に限って切り替える。**

`_JOURNAL_KEYS["reservation-preflight"]` の base 集合は次の 10 key とする。

```python
{
    "event", "required_s", "safety_margin_s", "formula",
    "build_cap_per_cell_s", "shared_dependency_prebuild",
    "dependency_configure_cap_s", "dependency_target_cap_s",
    "verify_cap_per_attempt_s", "finalize_reserve_s",
}
```

`campaign-start` の既存 15 key は維持する。共用の binding key 集合を `frozenset({"pbs_jobid", "submission_nonce"})` とし、`:2057` の直前で次の形を使う。

```python
if key in {"reservation-preflight", "campaign-start"}:
    claims_binding = bool(binding_keys.intersection(record))
    if claims_binding:
        expected = expected | binding_keys
_exact_keys(record, expected, ...)
```

片方の key だけが存在する record は、2 key を要求する `_exact_keys` で拒否される。他 event の未知 key、未知 event の拒否も維持する。全 event から binding key を取り除いて比較する実装は採らない。

型検査は同じ per-record loop 内で exact 検査の直後に置く。

- claim 時の両 binding 値は `type(value) is str and bool(value)`。空文字、int、bool、null を拒否する。
- `reservation-preflight.formula` は非空 str。
- `shared_dependency_prebuild` は `type(value) is bool`。
- 残る 7 数値 field は `type(value) is int and value > 0`。bool を int として受け入れない。
- reservation の型検査は binding 有無の両形に適用する。

これは `floor_liveness.py:260` の field 分類・型述語と同形である。同モジュールの外部 job 照合や nonce 文法まで取り込まない。campaign の既存 host/process、receipt 検査 (`:2075`) はそのまま残す。

両 event の整合検査は campaign-start 一意性が確定する `:2167` 付近に置く。

1. reservation record の集合を得る。
2. campaign または reservation が binding を claim する場合、reservation をちょうど 1 件要求する。
3. 両 event がともに claim していることを要求する。
4. 両 record の `(pbs_jobid, submission_nonce)` が一致することを要求する。

binding 無しの journal に reservation の存在を新たに要求しない。既存 fixture は campaign-start が binding 無しで reservation 自体を持たないため、不変で通る。binding 無し reservation の重複・順序について新しい規律は加えない。

新規拒否は `journal-state-invalid` とし、cause は例えば `journal-binding-type`、`journal-binding-claim`、`journal-binding-mismatch`、`reservation-preflight-type` に分ける。未知 event は既存の `journal-event`、exact key 不一致は既存 `_exact_keys` の挙動を維持する。

後段の確認結果は次のとおり。

| file:line | 確認結果 |
|---|---|
| `s8b_ratified_freeze.py:2026` | `_journal_schema_key` は event / terminal status のみを見る。binding key は影響しない |
| 同 `:2168` | campaign の mirror 検査は 4 個の hash field のみ |
| 同 `:2394` | `journal["campaign"]` は追加 key を含む record を保持する |
| 同 `:2536`、`:2552` | **campaign record 全体を `_plain_json` で wall_ledger に入れ、result と比較する**。binding を落としてはいけない |
| 同 `:3418` | `equality_nodes` は campaign の個別 hash / receipt field を取り出す。campaign 全体の node はない |
| 同 `:3487`、`:3497`、`:3506` | freeze / cert / receipt の個別照合であり、追加 key は影響しない |
| `s8b_floor_campaign.py:6843` | producer も campaign record 全体を `dict(r)` で result.wall_ledger に転記する |

したがって実物の binding 付き record は後段と整合する。fixture で binding を追加するときは journal と result.wall_ledger を同時に更新し、result hash と世代文書も通常の fixture 構築で再計算する。

## 段階 6 lineage の実装案 (P1)

cert C の既存検査 (`:3526`) は変更しない。一意導入、非 merge、`C != G`、`C` が `G` の祖先という厳密条件を維持する。

result と各 measurement_closure path は次の順に検査する。

```python
_mode, oid = _tree_mode_oid(head, path, root)
introductions = _immutable_introductions(graph, path, oid, root)
introduced = _unique_introduction(introductions, path)

if len(graph.parents.get(introduced, ())) > 1:
    raise RatifiedFreezeError(
        "binding-chain-mismatch", ...,
        cause="artifact-introduction-merge",
    )

if not _git_ok(
    ["merge-base", "--is-ancestor", cert_commit, introduced], root
):
    raise RatifiedFreezeError(
        "binding-chain-mismatch", ...,
        cause="artifact-introduction-before-cert",
    )

if not _git_ok(
    ["merge-base", "--is-ancestor", introduced, gen_commit], root
):
    raise RatifiedFreezeError(
        "binding-chain-mismatch", ...,
        cause="artifact-introduction-outside-generation",
    )
```

`--is-ancestor` は同一 commit も成功するため、これで `C ≤ i ≤ G` になる。下限拒否の detail は「C が i の祖先でない」と記し、時刻順や全順序を意味すると誤読させない。

`_immutable_introductions` の `history-mutated` / `no-introduction` と `_unique_introduction` の `multiple-introduction` は既存 reason を保持する。新しい merge / 区間違反だけ `binding-chain-mismatch` の cause を細分する。

世代文書については同じ段階 6 に次を追加する。

```python
generation_path = _gen_path(ratified.generation_number)
_mode, oid = _tree_mode_oid(head, generation_path, root)
introductions = _immutable_introductions(
    graph, generation_path, oid, root
)
if set(introductions) != {gen_commit}:
    raise RatifiedFreezeError(
        "binding-chain-mismatch", ...,
        cause="generation-introduction",
    )
```

これを artifact 区間検査の後、段階 7 の前に置く。wrong_g=A では artifact の導入 G が区間 `[C, A]` 内に入っても、世代文書の実導入 G と申告 A が異なるため既存 cause で拒否する。

A 導入負例を段階 6 単体で検査できるよう、artifact の上記処理は小さい private helper に抽出する。helper は捕捉済み `head`、`graph`、C、G、path、root を受け取り、HEAD を再解決しない。公開 API や gate を追加するものではない。

H-pure の条件は以下を守る。

- `head` は `:3177` の捕捉値、graph は `_commit_graph(head, root)` に固定する。
- oid と導入集合は H の tree / DAG から取得する。
- lineage 内で worktree を読まない。`git log HEAD` や新たな `_capture_head` を使わない。
- 既存の段階 3 の G/H/worktree endpoint 検査は維持する。

docstring `:3161` は次の趣旨へ置換する。

> cert C の一意導入・非 merge・C<G、result / measurement_closure の各 path の一意導入・非 merge・I_entry ⊆ [C, G]、世代文書 path の導入集合 {G} は、捕捉済み H 内の DAG 上の記録順を保証する。実時間順や通常の履歴再構成への耐性は保証しない。floor_protocol / journal / manifest には導入順を課さず、既存の raw hash・semantic・endpoint 検査を維持する。

旧 `C<i` が `{G}` から従うという記述は削除する。

## test 変更案 (fixture / 正例 / 負例 / 手前落ちの確認)

**C 同時導入 option は `_build_independent_launch_repo` に追加し、production emitter helper の変更は不要とする。**

`test_s8b_ratified_verify.py:50` の B は `test_s8b_ratified_freeze`。`B.build_production_emitter_g1` の定義は同ファイル `:1074` にあり、cert 発行 callback `:1139` で C を先に commit し、result / closure は `:1265` 以降で確定して `:1339` の G に入る。ここで C 同時導入を実現するには emitter の checkpoint topology まで触る必要があり、本 wave の所有 file と最小差分を超える。

独立 fixture (`:483`) に `artifacts_at_certificate=False` を追加する。

- default は現行 C→G→A→X→H のまま。
- 有効時は `:537` の cert bytes 作成を維持し、C の commit だけ遅延する。
- result / closure が確定する `:639` の後、世代文書を書き込む `:657` の前で、cert と完成済み run artifacts / closure を C に commit する。
- 続く G は世代文書を導入する。`cert_at_generation=True` との併用は fixture 引数エラーにする。
- topology に各導入 commit を返し、テスト側でも実 Git の tree / parent を確認する。

正例は最低限、次を置く。

1. 既存 default fixture の `i=G` が成功する。
2. 新 option の `i=C=G^` が `LaunchValidatedFreeze` を返す。
3. 同 topology に binding 付き reservation / campaign を入れたものも成功する。
4. binding 無し reservation を追加した形も成功する。

journal mutation は既存 `mutate(state)` (`:595`) で行う。binding 付き正例では result.wall_ledger の campaign も一致させる。

| 負例 | 作り方・期待 |
|---|---|
| 導入が C より前 | closure80 を `:497` の base 構築時に同じ bytes で導入する。G/H endpoint は一致し、段階 6 の下限拒否になる |
| 導入が G の祖先でない | 実 Git の小 DAG で path を A に初導入し、抽出した artifact lineage helper を直接呼ぶ。上限拒否を exact に確認する |
| merge 導入 | C 後に両 parent が対象 closure を持たない分岐を作り、merge commit M で初追加、続く G に世代文書を置く。区間は成立し、merge cause だけで拒否する |
| 複数導入 | C 後に同 bytes を導入・削除・再導入し、G/H は同 bytes。`multiple-introduction` を確認する |
| 世代文書導入 ≠ G | `:2838` の wrong_g=A を維持。reason / cause は既存どおり |
| C=G | `:2828` を維持。`cert-lineage` が変わらないことを確認する |
| 未知 event | `reservation-preflight` に似た未知名などを追加。`journal-event` |
| 片側だけ binding | campaign のみ / reservation のみ、両方向を parameterize。`journal-binding-claim` |
| binding key の片欠け | 両 key のうち一方を削除。exact key 拒否 |
| binding 型不正 | 各 event × 各 key × `""` / int を parameterize。`journal-binding-type` |
| binding 値不一致 | 両方が非空 str のまま job または nonce を変える。`journal-binding-mismatch` |
| reservation field 型不正 | 各数値に 0 / 負数 / bool / str、formula に空文字 / int、bool field に int。`reservation-preflight-type` |

手前落ちの確認は「例外が出た」だけで済ませない。

- 全負例で reason と cause、必要なら対象 path / field の detail を固定する。
- 対応する無変異 fixture が public `launch_validate` で成功することを対照にする。
- journal は commit 前に変異し、result と世代文書の hash を通常手順で組み直す。commit 後の journal 書換えによる endpoint 拒否を混ぜない。
- base / merge / 複数導入は G/H/worktree の bytes を一致させ、cert C と G の関係は有効に保つ。
- wrong_g=A は新しい世代文書検査で `generation-introduction` が出ることまで確認する。

**A で初導入した path は G に存在しないため、public 経路では段階 3 (`:3235`、`:1765`) を通れない。** これは構造上の制約である。public 経路の早期拒否と、実 Git DAG を使う段階 6 helper の上限拒否を別テストにする。endpoint 検査を monkeypatch して「full launch が段階 6 まで到達した」とは扱わない。

## 実効性の実測手順と _ACTIVATED_G1_REFUSALS

親が修正後の同一 checkout で H、gitlink、実行 API、reason / cause / detail を記録する。長い reverify・焦点走・変異走は brief の計算ノード dispatch に従う。

1. `load_ratified_freeze(root)` (`:1465`) で g1 を読み込む。generation 1、sha `7e111406…`、G `32ba8cae…` を記録する。
2. `reverify_published_freeze(ratified, root)` (`:3736`) をそのまま実行する。暫定変異や policy 書換えは使わない。
3. N3 の再現期待は段階 8 の `closure-hit-mismatch`、未申告 path `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`。これは段階 4〜7 通過の証拠であり、reverify 成功とは報告しない。
4. 独立に `assert_g1_floor_selection_identity(ratified, root)` (`:3636`) を実行し、成功なら戻り値 `None` を記録する。失敗ならその reason / cause を残す。
5. public `launch_validate(ratified, root)` を実行する。N1 の期待は `manifest-invalid` / `binary-admission`、旧 receipt と現行 policy の不一致。
6. runbook の live P3 gate-check も実行し、`allowed: false` と refusals の 2 件 exact を確認する。

identity 単独検査は activation HEAD / policy / closure / live scan を検証しない (`:3643`)。P3 の 3 観測を合わせても、live launch 成功の証明とはしない。

`_ACTIVATED_G1_REFUSALS` は第 1 要素の layer-2 hit を一字も変えず、第 2 要素を次に置き換える。

```python
"v2-execution: launch-validate: [manifest-invalid] [manifest-invalid] "
"binaries[rr20::backoff_fixed_best] admission receipt が不正: "
"receipt admission policy が現行 policy と不一致"
```

comment は次の趣旨にする。

> T-2304 / D2184 の ccbench pin 前進で admission policy epoch が変わった後の live P3 真値。T-2810 の journal / lineage 修復後も、live 経路は段階 4 の現行 policy 照合で拒否される。historical reverify は段階 8 の未発効候補 hit まで到達する。

runbook P3 / W-3 も同じ区別で更新する。T-2724 時点の journal 拒否は過去の観測として保持し、現在の live 拒否原因として記さない。新しい不整合を見つけても policy 緩和、候補削除、除外追加へ進まず、親が別件として記録する。

## 焦点走と変異候補

親の焦点走対象は次の 6 file。`tools/run_tests.py` 経由で計算ノードに dispatch し、held 6 node は既存の診断 token 手順で検証する。hold 登録は変更しない。

- `orchestrator/tests/test_s8b_ratified_verify.py`
- `orchestrator/tests/test_s8b_oracle_driver.py`
- `orchestrator/tests/test_s8b_binding_driftguards.py`
- `orchestrator/tests/test_s8b_terminal_evidence.py`
- `orchestrator/tests/test_s8c_preregistration_invariant.py`
- `orchestrator/tests/test_s8c_preregistration_predicates.py`

変異 matrix は独立 clone で実施し、入力負例と実装変異を区別して記録する。

| ケース | 観測 / 殺す実装変異 |
|---|---|
| 正例: i=C、両 event binding 付き | public launch 成功。旧 allowlist または旧 `{G}` 条件への戻しで失敗する |
| 未知 event | event の無条件受理を殺す |
| binding key 片欠け | optional key を自由に許す実装を殺す |
| 片側だけ claim | 両 event の claim 整合検査の削除を殺す |
| 空文字 / int binding | 型・非空検査の削除を殺す |
| binding 値不一致 | 両 event の値比較の削除を殺す |
| reservation 数値に bool / 0 | `isinstance(x, int)` への緩和、正値検査の削除を殺す |
| base 導入 | `C ≤ i` 検査の削除を殺す |
| A 導入、helper 単体 | `i ≤ G` 検査の削除を殺す。public 経路の証拠とは分ける |
| merge 初導入 | 非 merge 検査の削除を殺す |
| 同 bytes の複数導入 | `_unique_introduction` の削除を殺す |
| wrong_g=A | 世代文書導入集合 `{G}` 検査の削除を殺す |
| C=G | cert 厳密祖先条件の緩和を殺す |
| wall_ledger の binding 欠落 | campaign 全体の mirror 比較を弱める実装を殺す |

`test_s8b_terminal_evidence.py:424` の session key pin は変更せず通す。親の完了検査には規定の code / docs checker と、commit 後の provenance checker を含める。本段では pytest、変異、live probe を実行していない。

## 攻撃点 (P1〜P3・scope への疑義、段 3 へ)

1. **A 初導入負例の到達性。** G に path が無いため、public launch で段階 6 に到達するという要求は既存 endpoint 保証と両立しない。plan は helper 単体で上限条件を検証する。段 3 では、この証拠の分離を受け入れるか確認する。
2. **binding の「一致」の意味。** 本 plan は claim 状態に加えて値の一致も要求する。producer が同じ external binding から両 record を作ることに整合するが、P2 を claim 状態だけの一致と読む場合より強い。
3. **binding 無し reservation の多重性。** P2 に明記のない新しい順序・件数規律は加えない。binding claim 時だけ対となる reservation の一意性を要求する。
4. **P1 は現物だけより広い。** `i=C` と `i=G` に加え、中間の一意な非 merge 導入も受理する。また両 parent のどちらかに既に存在する通常 merge は「merge 初導入」ではない。これは `_immutable_introductions` の定義に従う。
5. **P3 の到達証拠の限界。** historical reverify と identity 単独成功は live launch の成功を代替しない。N1 と N3 が残る以上、本 wave の完了は validator の 2 修復であり、W-4 / W-5 の開始許可ではない。
6. **scope と表題。** 「full launch validation を通す」という表題に対し、現行 main の live は policy で止まる。完了記録では brief の限定された受入条件を明記し、N3 の候補 hit を隠さない。

## 総括

P2 は対象 2 event の exact な 2 形受理と binding 整合検査、P1 は artifact の一意・非 merge・`C ≤ i ≤ G` と世代文書導入 `{G}` で実装する。cert、policy、scan 除外、凍結成果物は変更しない。

親の受入は fixture 成功、負例・変異の拒否、実 repo の段階 8 到達、identity 単独検査、live policy 拒否の再確認で行う。本段は読み取りと静的確認のみで、ファイル変更・テスト実測は未実施。