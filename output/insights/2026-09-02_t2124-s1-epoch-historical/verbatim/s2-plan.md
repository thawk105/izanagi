## 変更 1: s1_report.py

対象は [s1_report.py:302](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/s1_report.py:302) の `_campaign_verifier_epoch_from_lock_bytes` だけ。

現状:

```python
recorded = artifact_admission._recorded_campaign_verifier_epoch(
    artifact_admission._decode_campaign_lock(lock_bytes)
)
return artifact_admission._require_verifier_epoch_for_purpose(
    recorded, CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
)
```

変更後:

```python
recorded = artifact_admission._recorded_campaign_verifier_epoch(
    artifact_admission._decode_campaign_lock(lock_bytes)
)
if recorded.diagnostic.state == "E0":
    raise CampaignVerifierEpochRejected(recorded.diagnostic)
return artifact_admission._require_verifier_epoch_for_purpose(
    recorded, CampaignReadPurpose.HISTORICAL_RAW,
)
```

根拠:

- authority 不在の v1 lock は `_recorded_campaign_verifier_epoch` が `E0 / v1-authority-absent` を生成する。[artifact_admission.py:898](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/artifact_admission.py:898)
- `HISTORICAL_RAW` は中央 gate で記録診断を無条件返却するため、その前に S-1 局所で E0 を拒否する必要がある。[artifact_admission.py:957](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/artifact_admission.py:957)
- `CampaignVerifierEpochRejected` は既に import 済みであり、例外へ投影される5 fieldも既存 constructor のまま使う。[s1_report.py:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/s1_report.py:34)、[artifact_admission.py:206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/artifact_admission.py:206)
- E1 は保存済み commit/blob map の検証を通った後、`HISTORICAL_RAW` として現行閉包を取得せず返る。[artifact_admission.py:919](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/artifact_admission.py:919)
- `HISTORICAL_RAW` 宣言の既存先例は [layer3_report.py:551](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/layer3_report.py:551) と [p2_2_report.py:133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/p2_2_report.py:133)。

保存済み COMMIT 証拠検査は無関係である。呼び出し経路は `_assess_campaign` の epoch gate [s1_report.py:425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/s1_report.py:425) → WAL 読取 [s1_report.py:463](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/s1_report.py:463) → `_sample_from_segment` [s1_report.py:526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/s1_report.py:526) → `require_persisted_certified_commit` [s1_report.py:352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/s1_report.py:352) である。purpose の変更は最後の検査の引数、実装、拒否処理に触れず、E1 が新たに epoch gate を通った場合も各成功標本は必ずこの検査を受ける。

## 変更 2: test_s1_report.py — 負例

対象 node は既存の `test_non_e1_campaign_is_structured_and_wal_is_not_read`。[test_s1_report.py:498](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_report.py:498)

計画:

- `E1_EPOCH` 定義直後、autouse fixture より前の現行 [test_s1_report.py:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_report.py:29) に、production callee を保存する。

```python
_REAL_CAMPAIGN_VERIFIER_EPOCH_FROM_LOCK_BYTES = (
    report._campaign_verifier_epoch_from_lock_bytes
)
```

- autouse fixture は現行 [test_s1_report.py:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_report.py:31) で対象関数を固定 E1 lambda に差し替える。既存テスト内の monkeypatch [test_s1_report.py:524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_report.py:524) を dispatcher へ上書きし、拒否対象 bytes だけ保存済み実 calleeへ渡す。

```python
def epoch_gate(lock_bytes):
    if lock_bytes == rejected_lock:
        return _REAL_CAMPAIGN_VERIFIER_EPOCH_FROM_LOCK_BYTES(lock_bytes)
    return E1_EPOCH
```

この `return _REAL_...(lock_bytes)` が、合成例外ではなく実 `_decode_campaign_lock`、実 `_recorded_campaign_verifier_epoch`、変更後の局所 E0 判定を通る保証になる。他3 roleだけ固定 E1を返すため、既存テストの「block1だけ拒否し、他 campaign の WAL は読む」という焦点も維持する。

v1 bytes は新規 stub を作らない。既存 `_fixture` が role ごとの schema-less JSON lock を書く [test_s1_report.py:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_report.py:162) ため、現行 [test_s1_report.py:512](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_report.py:512) の `read_bytes()` をそのまま入力にする。schema_version のない object が v1になる実 codec は [campaign_lock.py:334](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/campaign_lock.py:334)。専用 helper `encode_campaign_lock_v1` も [campaign_lock.py:487](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/campaign_lock.py:487) に存在するが、この node では既存 fixture bytes を使うため不要。

拒否投影について:

- 現在、`campaign_verifier_epochs["block1"]` の完全一致 [test_s1_report.py:538](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_report.py:538) が `_rejected_epoch_projection` の field 集合を固定している。
- `campaign_verifier_epoch_rejected` reason は現行 [test_s1_report.py:529](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_report.py:529) で一部 fieldしか検査せず、完全な field 集合を担保する既存テストは無い。
- この node を強化し、reason 全体を次の exact dict と比較する。scope値も production 定数から再取得せず、現行文字列をリテラルで固定する。

```python
{
    "code": "campaign_verifier_epoch_rejected",
    "message": "campaign verifier epoch が certified S1 標本を受理しない",
    "campaign": "block1",
    "campaign_verifier_epoch": "E0",
    "state": "E0",
    "reason_code": "v1-authority-absent",
    "identity_scope": <現行の exact scope 文字列>,
    "excluded_scope": <現行の exact excluded scope 文字列>,
}
```

同じ5 fieldの dictを `campaign_verifier_epochs["block1"]` とも exact 比較する。これにより `_rejected_epoch_projection` と reason envelope の field追加、欠落、値変更を同じ負例で殺す。WAL非読取は既存の `observed_read` と `len(read_roots) == len(report.ROLES) - 1` [test_s1_report.py:519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_report.py:519) で引き続き固定する。

## 変更 3: test_s1_report.py — 正例

新規 node 名は `test_v2_epoch_gate_is_historical_when_current_closure_is_unavailable` とし、現行負例の直後、[test_s1_report.py:548](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_report.py:548) の前へ置く。

追加 import は [test_s1_report.py:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_report.py:15) 周辺の `contract_loader_binding` と、共有 helper `build_v2_campaign_lock`。

v2 bytes は次の実経路で作る。

```python
lock_bytes = build_v2_campaign_lock(
    driver.ident.canonical_preimage(
        driver.config_for(_freeze(), "develop")
    )
).encode("utf-8")
```

根拠:

- 共有 v2 fixture helper は [campaign_lock_test_support.py:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/campaign_lock_test_support.py:23) に存在し、記録 HEAD の24 path blob digestを使う。
- helper は production `CampaignLockAuthority` と `encode_campaign_lock_v2` を呼ぶ [campaign_lock_test_support.py:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/campaign_lock_test_support.py:37)。encode本体は [campaign_lock.py:459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/campaign_lock.py:459)。
- S-1系での既存使用例も [test_s1_direct_comparison.py:1451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_direct_comparison.py:1451) にある。したがって「既存 v2 fixture が見つからなかった」ケースではない。

本文では次を行う。

- autouse fixtureを、保存した実 S-1 calleeへ monkeypatch し直す。
- `capture_contract_loader_binding` は呼ばれたら `ContractLoaderBindingError("fixture unavailable")` を投げる関数へ差し替える。
- 差し替え後の関数をテスト本文から一度直接呼び、確かに失敗状態であることを `pytest.raises` で前提確認する。
- `_require_verifier_epoch_for_purpose` は返値を合成せず、呼ばれた purpose を記録して保存済み production 関数へ委譲する透明 spy にする。
- 実 `_campaign_verifier_epoch_from_lock_bytes(lock_bytes)` を呼び、次を検査する。

```python
assert observed_purposes == [report.CampaignReadPurpose.HISTORICAL_RAW]
assert capture_call_count == 1  # 前提確認の1回だけ。gateからは呼ばれない
assert epoch.state == "E1"
assert epoch.reason_code == "recorded-closure"
assert epoch.campaign_verifier_epoch.startswith("E1:")
```

両層 stub ではない。S-1 callee、lock decode、記録 epoch 導出、記録 commit/blob検証、中央 purpose gateはすべて production 実装を通る。中央 gate の spy も保存済み実関数へ委譲し、返値を作らない。唯一の失敗 stub は現行閉包取得 seamである。記録 commit/blob検証は `verify_committed_contract_loader_binding` [contract_loader_binding.py:386](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/contract_loader_binding.py:386) を通り、patch対象の現行閉包取得 [contract_loader_binding.py:348](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/contract_loader_binding.py:348) とは別経路である。

## 既存テストへの影響

既存 node の期待される report 結果が変わるものは無い。

- `test_non_e1_campaign_is_structured_and_wal_is_not_read` は実行経路だけを合成拒否から実 E0 calleeへ強化する。期待する拒否理由、projection、WAL非読取は不変。
- それ以外の既存 `test_s1_report.py` node は autouse fixture [test_s1_report.py:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_report.py:31) により固定 E1を受け取るため、production purpose変更へ到達しない。
- `test_persisted_certification_invalidates_sample` [test_s1_report.py:298](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_report.py:298) と lock交換テスト [test_s1_report.py:325](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_report.py:325) は保存済み COMMIT gateを直接固定しており不変。
- production module の import検査 [test_s1_report.py:683](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_report.py:683) に影響する新規 production importは無い。

変更しない file は `orchestrator/campaign/artifact_admission.py`、`orchestrator/campaign/replay.py`、`orchestrator/campaign/s8b_oracle_report.py`、`orchestrator/campaign/s1_direct_comparison.py`。`output/` 配下と `docs/` 配下も一切変更せず、新規 fileも作らない。

## 変異候補

| 最小変異と箇所 | 殺す test node |
|---|---|
| 追加する E0 `raise` を削除する。[s1_report.py:305](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/s1_report.py:305) 直後 | `test_non_e1_campaign_is_structured_and_wal_is_not_read` |
| purpose を `CERTIFIED_ACCEPTANCE` へ戻す。[s1_report.py:308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/s1_report.py:308) | `test_v2_epoch_gate_is_historical_when_current_closure_is_unavailable`。失敗 stub が呼ばれて拒否される |
| 中央 gate 呼出しを削り、`return recorded.diagnostic` にする。[s1_report.py:308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/s1_report.py:308) | 正例の `observed_purposes == [HISTORICAL_RAW]` |
| E0で `CampaignVerifierEpochRejected` 以外を投げる。[s1_report.py:305](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/s1_report.py:305) 直後 | 負例。`campaign_verifier_epoch_rejected` ではなく validation failureへ落ちる |
| `_rejected_epoch_projection` の fieldを1個削除・差替えする。[s1_report.py:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/s1_report.py:127) | 強化後の負例の exact projection/reason比較 |

## 攻撃対象 (親の provisional 裁定 P1/P2 への異論、および親の実測への異論)

- P1への異論はない。D1387が要求する例外は E0 の局所維持だけであり、中央 gateへ第3 purpose、wrapper、flagを作る方が射程を越える。局所条件が将来の新 epoch stateを一般化して拒否しない点も、D1387の対象が exact E0であるため適切。
- P2への異論はない。ただし「取得失敗関数を置いた」だけでは恒真化の疑いが残るため、失敗 seam の前提呼出し、purpose の透明 spy、capture呼出し回数の3点を同時に固定する。
- 親の autouse fixture、既存 E0テスト、`s1_direct_comparison.py` に対象 gateがないという実測は静的コードと一致した。
- 30 campaign の authority不在という成果物 censusは今回再実測していない。親 briefの実測値を前提としており、これへのコード上の反証はない。局所 E0拒否が残るため、その前提下では既存30件の出力は不変。

## 未確認事項

- sandbox制約と依頼どおり、pytest、build、その他のテスト実走はしていない。緑とは報告しない。
- v2共有 helperとGit検証経路は静的に確認したが、この worktree環境での実行結果は親の担当。
- 記載行番号は現在の read-only tree基準。実装で行追加後、後続行の番号はずれる。
- fileは1 byteも編集していない。

## 総括

変更は S-1 の局所 E0拒否追加と purpose の `HISTORICAL_RAW` 化だけである。  
既存負例を実 callee経由へ直し、E0拒否、拒否投影、WAL非読取を同時に固定する。  
正例は実 v2 encode・記録 blob検証・中央 gateを通し、現行閉包失敗だけを seam化する。  
最も壊れやすい箇所は、autouse fixtureを解除し損ねて実 calleeを一度も通さない恒真テスト化である。