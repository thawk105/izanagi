## 方針と確認結果

`65e94a3a7` と同型の変更を採る。production は既存 3 ファイル、test は指定された 5 ファイルに収める。以下の行番号は変更前の worktree 基準。ファイル変更・pytest・commit・branch 操作は行っていない。

静的に確認した結果：

- 現行 tuple は 85、追加は 11、合成後は重複なしの 96。
- **現行 tuple ＋ `new_members_sorted` が `closure-head.json.proposed` と全要素・全順序で一致**した。
- 追加 11 本は path の sorted 順。
- 親 oracle の 96-path epoch／順序 hash、および旧 85-path の固定値を独立の標準ライブラリ計算で照合し、一致した。

P2 は、本依頼の「exact-85 を同時収載する」と D2194 項 4 を本件の明示指示として採用する。ただし、**親の走査で exact-85 corpus は 0 本、D1653 の corpus 条件は未充足**である。「production が生成可能」と「記録済み corpus が存在」は区別する。親の受入前再走査と decisions fragment にこの解釈を残す。今回の段では指定外の checkout／外部 corpus を探索しない。

## campaign_lock.py の変更

対象：[campaign_lock.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2344-source-bound-emitters/orchestrator/campaign/campaign_lock.py:49)。

現行末尾 `orchestrator/critic/digest.py` の直後、閉じ括弧の前に以下を追加する。

```python
    "orchestrator/campaign/autonomous_trial_completeness.py",
    "orchestrator/campaign/b10_backoff_shape_sweep.py",
    "orchestrator/campaign/backoff_extended_sweep.py",
    "orchestrator/campaign/backoff_extended_sweep_report.py",
    "orchestrator/campaign/backoff_overthrottle.py",
    "orchestrator/campaign/s8b_abort_reason_contract.py",
    "orchestrator/campaign/s8b_oracle_report.py",
    "orchestrator/campaign/s8b_outcome_stage_contract.py",
    "orchestrator/reports/__init__.py",
    "orchestrator/reports/calibration_report.py",
    "orchestrator/reports/plot.py",
```

既存 85 行は移動しない。`:47` のコメントを exact 96 にする。

| 変更箇所 | 差分 |
|---|---|
| `campaign_lock.py:234` の exact-63 literal の後、`:300` の正規表現定義より前 | `T2344_EXACT85_CONTRACT_LOADER_RELATIVE_PATHS` を独立した 85 行の ordered literal として追加。出典は `5efd69367` の現行宣言。slice・結合・production 定数参照で定義しない |
| `:366` `HistoricalCampaignLockAuthority.__post_init__` | grammar 白名単に exact-85 を追加。現行 96／85／63／62／24 の **tuple 等値**と blob map の宣言順一致を要求 |
| `:629` の exact-63 validator の後 | `_validate_t2344_exact85_historical_authority` を兄弟として追加 |
| `:815` `decode_historical_campaign_lock` | 現行分岐の後、exact-63 分岐の前に exact-85 を追加 |
| `:818` docstring | 現行・exact-85・exact-63・exact-62・exact-24 を列挙 |

兄弟 validator は `:629` の実装をそのまま踏襲し、grammar 定数だけを exact-85 にする。具体的な骨格は以下。

```python
def _validate_t2344_exact85_historical_authority(
        value: Any,
) -> HistoricalCampaignLockAuthority:
    # exact dict、AUTHORITY_KEYS 完全一致
    # activation_serial は正の exact int
    blob_sha256s = value["contract_loader_blob_sha256s"]
    expected_wire_order = tuple(
        sorted(T2344_EXACT85_CONTRACT_LOADER_RELATIVE_PATHS)
    )
    if (type(blob_sha256s) is not dict
            or tuple(blob_sha256s) != expected_wire_order):
        raise CampaignLockCodecError(
            "authority.contract_loader_blob_sha256s の歴史 grammar が不正"
        )
    checked_blobs = {
        path: _require_hex(
            blob_sha256s[path], width=64,
            label=f"authority.contract_loader_blob_sha256s[{path!r}]",
        )
        for path in T2344_EXACT85_CONTRACT_LOADER_RELATIVE_PATHS
    }
    # 他の authority field に既存と同一の _require_hex を適用
    return HistoricalCampaignLockAuthority(
        # 検証済み authority fields
        contract_loader_blob_sha256s=checked_blobs,
        recorded_contract_loader_relative_paths=(
            T2344_EXACT85_CONTRACT_LOADER_RELATIVE_PATHS
        ),
    )
```

上記コメント部分も先例と同じ検証を実装し、省略しない。wire は canonical JSON の **sorted 順**、返却 map と epoch は **宣言順**である。

歴史 decoder の v2 分岐は次の形にする。

```python
# 既存の現行分岐：exact-96
if type(blob_sha256s) is dict and tuple(blob_sha256s) == current_wire_order:
    return _historical_decoded_from_current(decode_campaign_lock(text))

# 既存の identity 検証を維持
if (type(blob_sha256s) is dict
        and tuple(blob_sha256s)
        == tuple(sorted(T2344_EXACT85_CONTRACT_LOADER_RELATIVE_PATHS))):
    authority = _validate_t2344_exact85_historical_authority(authority_value)
elif ...:  # 既存 exact-63 分岐をそのまま維持
    ...
elif ...:  # 既存 exact-62 分岐をそのまま維持
    ...
else:
    authority = _validate_pre_t733_historical_authority(authority_value)
```

最後の `else` は任意 grammar の受理ではなく、既存 exact-24 validator による拒否を含む。v1 経路も現状維持する。

通常 `_validate_authority`（`:484`）・通常 decoder・encode は変更せず、参照する現行 tuple が 96 に進むことで **v2 authority は exact-96 のみ**になる。

## artifact_admission.py の scope と歴史分岐

対象：[artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2344-source-bound-emitters/orchestrator/campaign/artifact_admission.py:76)。

現行 2 定数は以下の確定文字列にする。

```python
CAMPAIGN_VERIFIER_EPOCH_SCOPE = (
    "enforcement source closure (curated exact 96 path; source-import 推移閉包ではない; "
    "発見集合は収載 tuple を起点に静的 import と package 初期化を辿った集合であり、"
    "2026-09-21 (5efd69367 の source 木、本版の 96 path を起点) の実測では 173 module、うち収載 96)"
)
CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE = (
    "同実測の発見集合の未収載 77 module、同発見集合に入らない module、"
    "orchestrator/verifier/__main__.py、orchestrator/verifier/cli.py、"
    "package 外の orchestrator/verify.py、および data/schema、生成物、subprocess、"
    "外部 command/Git、toolchain、binary、動的 import を含む非 import 委譲は本 map の外であり "
    "(収載 path の source bytes は委譲先であっても本 map の内)、完全性を主張しない"
)
```

D2081 の集合定義・日付付き測定値・集合外の除外・非 import 委譲の例外句を保持し、発行器名や収載内訳を加えない。

`:123` の exact-63 scope 定数の後に、以下を**独立 literal**として追加する。文字列連結後の UTF-8 bytes は変更前の現行 2 定数と同一である。

```python
T2344_EXACT85_CAMPAIGN_VERIFIER_EPOCH_SCOPE = (
    "enforcement source closure (curated exact 85 path; source-import 推移閉包ではない; "
    "発見集合は収載 tuple を起点に静的 import と package 初期化を辿った集合であり、"
    "2026-09-20 (f94b61fc8 の source 木、本版の 85 path を起点) の実測では 163 module、うち収載 85)"
)
T2344_EXACT85_CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE = (
    "同実測の発見集合の未収載 78 module、同発見集合に入らない module、"
    "orchestrator/verifier/__main__.py、orchestrator/verifier/cli.py、"
    "package 外の orchestrator/verify.py、および data/schema、生成物、subprocess、"
    "外部 command/Git、toolchain、binary、動的 import を含む非 import 委譲は本 map の外であり "
    "(収載 path の source bytes は委譲先であっても本 map の内)、完全性を主張しない"
)
```

production の `T2429_EXACT63` 参照を全探索したところ、追加が必要な分岐は次の 4 箇所である。

| 箇所 | diff 骨格 |
|---|---|
| `:257` `HistoricalCampaignVerifierEpoch.__post_init__`、既存参照 `:268` | 有効な scope **対**へ `(T2344_EXACT85_…SCOPE, T2344_EXACT85_…EXCLUDED_SCOPE)` を追加 |
| `:300` `_RecordedCampaignVerifierEpoch.__post_init__`、既存参照 `:324` | exact-85 の scope 対なら `expected_paths = campaign_lock.T2344_EXACT85_CONTRACT_LOADER_RELATIVE_PATHS` |
| `:1064` `_verify_committed_loader_binding`、既存参照 `:1078` | 歴史型かつ旧 grammar の列挙に exact-85 を追加。記録した 85 path 全体を `verify_committed_contract_loader_blobs` に渡す |
| `:1096` `_recorded_campaign_verifier_epoch`、既存参照 `:1148` | exact-85 tuple の `elif` を追加し、凍結した scope 対の `HistoricalCampaignVerifierEpoch` を作る |

加えて `:1105`、`:1215` の説明へ exact-85 を追記する。歴史型のデフォルト scope（`:250`、pre-T733）は変更しない。

`_decode_campaign_lock_for_purpose`（`:1037`）と `_require_verifier_epoch_for_purpose`（`:1186`）の分離は維持する。**scope は grammar ごとに選択するが、scope 文字列を epoch hash preimage に追加してはいけない。** 現行の hash 式（`:1128`）は domain と順序付き path／digest のみであり、不変とする。

## contract_loader_binding.py

[contract_loader_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2344-source-bound-emitters/orchestrator/campaign/contract_loader_binding.py:2) は **docstring の 85 → 96 だけ**でよい。対象は `:2`、`:58`、`:61` の 3 箇所。

`:14` が codec の現行 tuple を直接 import しているため、capture、live 検証、committed 検証、timeout 計算への機能変更は不要。歴史 blob 検証は既存の明示 ordered-path API（`:578`）を使う。

## 既存 test の追随と固定値

以下の `test_*.py` はすべて `orchestrator/tests/` 配下。

| file:line | 変更内容・値の出典 |
|---|---|
| `test_t671_source_binding.py:128` | 独立した `_T2344_EMITTER_ENFORCEMENT_SOURCE_PATH_SUFFIX` に上記 11 行を書き、既存の独立 85 行の後へ展開。production 定数を期待列の生成に使わない |
| 同 `:295` | `85 → 96` |
| 同 `:1638,1717,1723,1801,1807` | timeout literal `850 → 960`。10 秒 × 96 の独立期待値 |
| `test_artifact_admission.py:284` | `_EXPECTED_E1_CLOSURE_PATHS` の既存 85 行の後へ独立に 11 行を追加 |
| 同 `:370,373` | 現行 epoch／順序 hash を下記 96 固定値に変更 |
| 同 `:851` | fixture docstring の exact 85 → 96 |
| 同 `:1540` | E0 diagnostic の scope 期待文字列を、上記現行 96 文面の独立 literal に更新 |
| 同 `:1667,1674` | 件数 assert `85 → 96` |
| 同 `:3632` | 現行 map のローカル名 `blobs85` を `blobs96` に追随。exact-63 と現行 map の不一致テストは維持 |
| `test_s1_9pair_figure_provenance.py:75` | `CURRENT_E0_EPOCH` の scope 対を 96 文面の独立 literal に更新。凍結 report の hash は変えない |
| `test_layer3_report.py:584` | helper に `grammar == 85` と exact-85 rewrite を追加 |
| 同 `:1917,1946,2023` | 歴史 param を `[85, 63, 62, 24]` にする |
| 同 `:1934` | 固定 epoch 表に `85: E1:bc8a…423dc7` を追加。旧 3 値はそのまま |
| 同 `:1997,2005,2050` | 「現行」を表す param／条件の `85 → 96` |
| `test_campaign_lock_codec.py:167` | `_authority()` は現行 tuple を列挙するため自動追随。これを独立期待値の根拠にはしない |
| 同 `:746` 以降の helper 群 | `_EXPECTED_T2344_EXACT85_CLOSURE_PATHS` と `_t2344_exact85_v2_value()` を追加。helper は独立 85 literal のキーで合成 map を取り出す |
| `test_artifact_admission.py:3453` 以降の helper 群 | 同様に独立 85 literal と `_rewrite_as_t2344_exact85_lock()` を追加 |

固定値は以下をそのまま literal として保持する。

```python
# 現行 exact-96
_FIXED_SYNTHETIC_E1_EPOCH = (
    "E1:244d998f35b0f7deae215a4053d9dde5acf60fc0775e4ea4c7a315579e7da07a"
)
_FIXED_ORDERED_CLOSURE_PATHS_SHA256 = (
    "5c2c4a6a45ec44f46d655f1d9c43f1d877d5547fc46ff308fbdaa61df6683af4"
)

# 歴史 exact-85
_FIXED_T2344_EXACT85_EPOCH = (
    "E1:bc8a6c8c6fd792ab6f21f22107f5313fb64ef0be1d6f8c97a15065998c423dc7"
)
_FIXED_T2344_EXACT85_PATH_SHA256 = (
    "bea3624661166dbe20df206ebd1e4f855f8c13e39721ab67e8b19d981bd6b5a1"
)
```

D1652 に対応する独立手順は、親の `closure-head.json.proposed`／`oracle-fixed-values.json` を入力とし、production module を import せずに次を一度計算して固定する方法とする。

- 1-based 宣言位置 `i` の fixture bytes：ASCII `epoch closure fixture {i}\n`。
- path hash：`SHA256(concat(path UTF-8 + NUL))`。
- epoch：`"E1:" + SHA256(b"campaign-verifier-epoch/v1" + concat(path UTF-8 + NUL + SHA256(fixture bytes).digest()))`。
- 85 の対照値は変更前の固定値と照合する。

test 実行時に production 定数や期待 tuple から**期待固定値を再生成しない**。計算した実測値を固定 literal と比較する。

## exact-85 の新設 test node

codec は `test_campaign_lock_codec.py:754–877` の exact-63 群と同型で追加する。

| 新 node | 検査 |
|---|---|
| `test_t2344_exact85_uses_dedicated_historical_decoder_type` | str／bytes 入口、専用返却型、authority 型、宣言順、identity／原文保持、通常 activation 検証への型隔離 |
| `test_t2344_exact85_remains_rejected_by_normal_decoder` | 通常 str／bytes decoder の exact-key 拒否 |
| `test_t2344_exact85_rejects_unknown_grammars` | subset／superset／同数置換／wire 順序違い／current-minus-one。兄弟 validator と歴史 decoder の両方で拒否 |
| `test_t2344_exact85_authority_requires_exact_declared_order` | authority の grammar 白名単、map 順序、exact keys、serial、hash shape |

admission は `test_artifact_admission.py:3465–3638` の exact-63 群と同型で追加する。

| 新 node | 検査 |
|---|---|
| `test_t2344_exact85_is_readable_only_as_recorded_historical_epoch` | 両歴史 API、固定 epoch／path hash、凍結 scope の独立 literal、現行適合 unknown、clean／dirty live の両方で同じ歴史結果、lock／WAL bytes 不変 |
| `test_t2344_exact85_is_rejected_for_certified_use` | 両 certified API と `classify_campaign` が codec 段で拒否 |
| `test_unknown_t2344_exact85_grammar_is_rejected_for_both_read_purposes` | 両 purpose × 両 API、未知 grammar を codec 段で拒否 |
| `test_t2344_exact85_rejects_each_recorded_commit_blob_mismatch` | 独立 85 literal 全 path を parametrize。digest の先頭 hex だけを反転し、歴史両 API が当該 path の blob mismatch を報告 |
| `test_t2344_exact85_epoch_requires_matching_scope_and_paths` | scope 対の混在・未知文字列、85／96／63／62／24 map の取り違え、map 順序違いを拒否 |
| `test_t2344_certified_acceptance_rejects_each_emitter_stage_source_drift` | **今回の 11 本だけ**を独立 literal で parametrize。dirty 時は `E1-stale/current-closure-unavailable`、同変更を commit 後は記録 epoch のまま certified 受理 |

最後の node は既存 `:3667` の新 22 本用 node を残し、その兄弟として追加する。11 本を既存 22 本の param に混ぜて前段の試験を失わない。

新しい歴史正例の dirty 対象には `s8b_oracle_report.py` を使うと、旧 85 map の外にある現行収載 path が dirty でも歴史閲覧に影響しないことも確認できる。

## 未知 grammar の否定側棚卸し

以下が source grammar の未知性を直接検査する既存 node 群。いずれも 96／85／63／62／24 への前進後に未知のままである。

| file:line・node | 入力と判定 |
|---|---|
| `test_campaign_lock_codec.py:315` `test_historical_decoder_rejects_unknown_blob_map_grammars` | 24−1、24＋worker、24 の置換。23／25／別集合 24 で未知 |
| 同 `:335` `test_historical_decoder_rejects_reordered_blob_map_wire_keys` | exact-24 の非 canonical wire 順序。引き続き拒否 |
| 同 `:676` `test_t733_exact62_rejects_unknown_grammars` | 61、unknown path を含む 63／62、順序違い。既知 exact-63 と衝突しない |
| 同 `:702` `test_t733_exact62_authority_requires_exact_declared_order` | `paths[:-1]` は 61。追加・置換は unknown path、swap は順序違い |
| 同 `:790` `test_t2429_exact63_rejects_unknown_grammars` | subset は **env_contract.py 除去**なので既知 62 にならない。superset は 64、置換は別集合 63、current-minus-one は前進後 95 |
| 同 `:830` `test_t2429_exact63_authority_requires_exact_declared_order` | `paths[1:]` は env_contract.py 欠落の別集合 62。末尾 worker を落とす `paths[:-1]` に変更してはいけない |
| `test_artifact_admission.py:2195` `test_unknown_pre_t733_grammar_is_rejected_for_both_read_purposes` | 上記 24 系と同じ。未知のまま |
| 同 `:3362` `test_unknown_t733_exact62_grammar_is_rejected_for_both_read_purposes` | 上記 62 系と同じ。未知のまま |
| 同 `:3529` `test_unknown_t2429_exact63_grammar_is_rejected_for_both_read_purposes` | env_contract.py 除去、unknown path 追加・置換、順序違い。未知のまま |

通常 decoder の周辺否定側も維持する。

- `test_campaign_lock_codec.py:396` の extra keys：現行＋extra は 97。
- `:409` `test_v2_rejects_each_missing_enforcement_source_blob_key`：各 95-path map。
- `:422` の exact-two、`:443` の pre-wave exact-twelve：引き続き通常 decoder で拒否。
- exact-24／62／63 の「通常 decoder で拒否」node は、未知性ではなく **certified 隔離**のテストとしてそのまま残す。

差し替えが必須な既存入力は見つからなかった。ただし `:814` と admission `:3554` の「既知 grammar のどれでもない」対照列に、独立 exact-85 literal を追加する。

新 exact-85 負例は、subset に env_contract.py 除去（84）、superset に unknown path 追加（86）、同数置換（別集合 85）、wire swap、current-minus-one（95）を使う。各候補を既知 5 grammar と比較する。**件数だけで未知性を主張しない。**

## 歴史 decoder・authority・scope の consumer

実行コードの直接参照は次のとおり。repo 内 Python 検索で、この一覧以外の直接参照は見つからなかった。

| consumer | exact-85 前進時の挙動 |
|---|---|
| `campaign_lock.py:525,541,586,631,795,815,1009` | authority の構築、現行→歴史型変換、歴史 decoder／bytes wrapper。85 が現行ラップ経路から専用歴史 validator 経路へ移る |
| `artifact_admission.py:1026,1045` | HISTORICAL_RAW だけ歴史 decoder を使用 |
| 同 `:1074,1121` | 記録 85 tuple を明示して全 blob を照合し、記録順 epoch を作る |
| 同 `:250,264,314,1145,1153` | 歴史 scope 対のデフォルト・白名単・map 対応・diagnostic 作成。85 の対を追加し旧対は維持 |
| `b10_backoff_shape_sweep.py:3135,3141` | decode 後も **pre-T733 exact-24 限定**。exact-85 を歴史 decoder が読めても、`:3141` の条件で拒否する。変更しない |
| `b10_backoff_static_tail_formal.py:351,353` | 歴史 admission 後に歴史 decoder で探索 mode を読む。85 の歴史読取が維持され、他の run_kind／record 検査は同じ |
| `layer3_report.py:120,134,278,412,972` | purpose 別 decode、authority commit fallback、epoch 投影。85 が historical scope／unknown を持つ結果として流れる。certified は通常 decoder で拒否 |
| `s8b_oracle_report.py:556,560,595` | **歴史 decoder の consumer ではない**。通常 decoder と certified gate を使う。旧 85 は codec 拒否から unavailable 投影へ進み、その scope は現行 96 文面 |

test の直接 consumer は `test_campaign_lock_codec.py` の上記 codec 群、`test_artifact_admission.py` の歴史 epoch 群、および `test_b10_backoff_shape_sweep.py:2537`。歴史 scope 定数の test 参照は admission の `:3423–3441`、`:3598–3625`。layer3 の test は helper 経由で利用する。

探索時に指定外の任意候補 `paper/` は存在しなかった。必読ファイルではないため停止せず、repo 全体の Python 検索を継続した。

## clean committed の拡張先と既存 fixture／運用

今回の 11 本すべてが次の処理の対象になる。

| 実コード | 要求する条件 |
|---|---|
| `contract_loader_binding.py:518–532` | 現行 HEAD に各 path の blob が存在し、安全に読んだ disk bytes と一致すること |
| `artifact_admission.py:1186–1206` | certified 受理時に上記 capture が成功すること。記録 map と現行 map の同一性は要求しない |
| `ident.py:280,584,587` | 新規 campaign の lock 発行前に capture＋live 検証。96 digest と commit を記録 |
| `ident.py:392` | resume は記録 binding に対する live 検証。旧 85 を通常 decoder へ通す変更はしない |
| `verify_fanout_worker.py:196–205` | worker capture と task の expected HEAD／map が一致すること |
| `p3_b4_wiring_probe.py:1297` | probe の runtime capture にも 11 本が入る |

ここでいう clean は実装上の「対象 path の disk bytes が HEAD blob と一致」であり、repo 全体の `git status` が空であることを新たに要求するものではない。

静的に確認した fixture と dirty 操作：

- `test_t671_source_binding.py:200` は独立期待列全体を tmp repo に作成して commit。`:599` の campaign 起動前 drift 拒否、`:647` の live 拒否、`:675` の記録 blob mismatch は、期待列の前進で新 11 本にも展開される。
- 同 `:776` は dirty のまま **test-only lock helper** が記録 HEAD の blob を使うことを確認する。certified 受理の正例ではない。この性質は維持する。
- `test_artifact_admission.py:850` は全期待 path を作成・commit。既存 `:2096`、`:2510` は dirty live を許す歴史読取であり、certified へ変更しない。
- `campaign_lock_test_support.py:10`、`test_layer3_report.py:74` は disk 非依存で記録 HEAD の全 blob を取得する。tuple の前進に自動追随するが、後続の certified gate は別途 live capture を行う。
- `test_s8a_trigger_sweep.py:969`、`test_s6_sort_sweep.py:691`、`test_bench_first_real_wal.py:171`、`test_t1998_stock_inline_pair.py:507` は tuple 全体を tmp repo に作成／コピーして commit するため、新 11 本も含まれる。
- `test_env_contract_activation.py:307`、`test_t762_ident_wrapper.py:100`、`test_paper_story_a2_certification.py:1157` の合成 map は現行 tuple を列挙する。
- `test_s8b_oracle_report.py:342` と `test_s8b_oracle_driver.py:6092` は tmp root に report／outcome contract 等の偽 source を書く。ただし、その root を `contract_loader_binding._REPO_ROOT` に設定して dirty certified capture を成功させる構造ではない。report test は `:122` 等で epoch API を差し替える。
- `test_s8c_preregistration_predicates.py:3033,3223,3432` 等は tmp Git repo の `autonomous_trial_completeness.py` を変異させるが、commit blob に対する predicate 検査である。
- `monkeypatch.setattr` による関数差し替え自体は source file bytes の dirty 化ではない。

確認したコードでは、**新 11 本を binding の実 root で dirty にしたまま certified 読取／起動を成功させる既存正例は見つからなかった**。実行確認はしていない。運用上は、発行器編集中の実 checkout を用いた certified 読取・campaign 起動が新たに失敗するため、親の焦点走は commit 済みの木で行う。

## 発行器 6 本の束縛の意味

campaign 開始時、6 本の source bytes が HEAD blob と一致した状態で digest／commit を lock に記録する（`contract_loader_binding.py:518`、`ident.py:584`）。
certified 受理時、記録 blob の真正性と、現行 96 path が clean committed で capture 可能なことを確認する（`artifact_admission.py:1064,1201`）。
D1163 により記録時と発行時の bytes 一致は要求せず、収載外 77 module・実行中の関数差し替え・推移閉包全体の同一性も保証しない（同 `:1128,1199`）。

## 変異事前登録候補

以下は事前登録案であり、変異実行結果ではない。

**正例側：収載追加が実際に効くこと**

| 変異 | 落とす test node | 検出段 |
|---|---|---|
| 現行 production tuple から新発行器 `s8b_oracle_report.py` のみ除去 | `test_enforcement_source_closure_is_the_independent_exact_twenty_four_paths` | 独立 literal 不一致。fixture 起動より前に検出 |
| 現行 tuple の末尾 2 path の宣言順を交換 | 上記 node、および `test_certified_acceptance_admits_exact_e1_fixture` | literal 不一致／返却 epoch の固定値不一致 |
| capture で新 11 本の disk-vs-HEAD 比較だけを素通りさせ、map 自体は全 96 を維持 | `test_t2344_certified_acceptance_rejects_each_emitter_stage_source_drift`、t671 `test_loader_drift_rejected_before_campaign_lock_or_wal_bytes` | live 拒否が消え、`raises` が失敗 |
| exact-85 decoder 分岐を削除 | `test_t2344_exact85_uses_dedicated_historical_decoder_type`、`test_t2344_exact85_is_readable_only_as_recorded_historical_epoch` | 正常な歴史入力が codec 拒否される |

**負例側：未知 grammar・certified 隔離・歴史凍結が効くこと**

| 変異 | 落とす test node | 検出段 |
|---|---|---|
| exact-85 兄弟 validator の wire 比較を superset 許容へ変更し、余分なキーを投影で捨てる | `test_t2344_exact85_rejects_unknown_grammars[superset]` の validator 直接呼出し | codec 拒否が消える。decoder の exact 分岐に隠されない |
| 歴史 authority の白名単を緩め、85＋unknown の grammar/map を受理 | `test_t2344_exact85_authority_requires_exact_declared_order` | 型構築時の拒否が消える |
| 通常 authority validator を旧 85 map も正常構築して返すように一貫して緩和 | `test_t2344_exact85_remains_rejected_by_normal_decoder` | codec 隔離の拒否が消える |
| exact-85 の committed blob 検証を省略 | `test_t2344_exact85_rejects_each_recorded_commit_blob_mismatch` | blob 拒否が消える |
| exact-85 歴史 scope の日付または数値を変更 | `test_t2344_exact85_is_readable_only_as_recorded_historical_epoch` | 独立 scope literal 不一致 |
| exact-85 scope 対を現行 96 文面へ差し替え | 同 node | 凍結 scope 不一致。scope は epoch hash 外なので epoch 固定値だけでは検出できない |
| exact-85 の epoch 計算順を sorted にする | 同 node | 固定 epoch 不一致 |
| 現行 scope 対と 85 map の組を `_RecordedCampaignVerifierEpoch` が許す | `test_t2344_exact85_epoch_requires_matching_scope_and_paths` | scope／path 対応の拒否が消える |

通常 validator の比較条件だけを union にして、後続の 96-path lookup が `KeyError` になる変異は登録しない。tuple 除去によって古い helper が `KeyError` になるだけの node も成功判定に使わない。正常な fixture 構築と、狙った拒否段・固定値比較まで到達したことを変異判定条件にする。

## 総括

先例 `65e94a3a7` と同型で、既存順を保った exact-96 と独立 exact-85 歴史 grammar を同時に実装する。
通常 v2／encode／resume／certified は exact-96 のみ、旧 63／62／24 の経路と固定値は維持する。
最大の risk は、exact-85 corpus 0 本という実測と D1653 の収載条件の関係を曖昧にすること。本件明示指示による採用として記録する。
本回答は静的検査に基づく実装プランであり、変更・pytest・変異試験は未実施。