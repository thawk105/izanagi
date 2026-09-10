静的判定は **NO-GO（must-fix 1件）** です。実装本体に fail-open は見つかりませんでしたが、段4で禁止された既存テスト防壁の削除が1件あります。

pytest、素の Python runner、production module の import は一切実走していません。`git diff`、`rg`、ファイル読解、`git diff --check` のみです。

## 所見

### 1. multi-record の terminal serial assert が失われている

- 深刻度: **must-fix**
- 根拠: 基準版 `HEAD:orchestrator/tests/test_env_contract_activation.py:490` の `assert state.activation_serial == 4` に対応する assertion が、置換後の [test_env_contract_activation.py:543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:543) にありません。現行の `activation_serial` assertion は serial 1 の2箇所だけです。
- 成果物影響: multi-record load が stale な `ActivationState.activation_serial` を返す退行を見逃し、その値が `AuthorizedContract.activation_serial` と issuer の次 serial 算出へ伝播して activation 参照を誤らせます。
- 修正案: `test_transition_accepts_three_record_forward_chain` に `assert state.activation_serial == 3` を復元してください。

これは受理集合変更に必要な削除ではなく、段4の「assert 削除禁止」に抵触します。

### 2. `first_failure` の「先頭失敗→後続成功」がテストで固定されていない

- 深刻度: **should-fix**
- 根拠: 実装の [env_contract_activation.py:297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:297) は一度設定した `first_failure` を消さないため現在は正しいです。しかしテストは「True→False」[test_env_contract_activation.py:649](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:649)、全件True、単独非bool、単独例外だけです。
- 成果物影響: 後続Trueで失敗状態を消す退行が入ると、先行envの不正 successorを含む activation edgeが受理され、台帳のactivation contract参照が変わります。
- 修正案: 2 env 同時変更で、先頭を `False`／非bool／例外、後続を exact `True` とする負例を追加し、全callback到達と最終 `ActivationRecordError` を固定してください。

### 3. transition 内の env 集合検査は sole production call path で到達不能

- 深刻度: **nit**
- 根拠: 各recordは [env_contract_activation.py:375](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:375) で同じcatalog集合との一致を済ませ、その後にだけ transition が呼ばれます。したがって [env_contract_activation.py:266](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:266) の不一致分岐は発火不能です。N11も [test_env_contract_activation.py:911](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:911) で外側のcatalog診断により落ちています。
- 成果物影響: 現行受理集合への影響はありません。env集合拒否の実効防壁は外側にあり、内側検査の検出力だけがゼロです。
- 修正案: 内側検査を削除して外側を所有者として明記するか、少なくとも「productionではprecondition済みの防御的検査」であることとN11の実際の発火層を明記してください。

## 実装追跡

- 例外・非bool・Falseがどの順に混在しても、`first_failure` は保持され最終的に拒否されます。通常の `Exception` は `ActivationRecordError` に包まれます。
- `predecessor_by_env[successor.env_tag]` は、直前のkey集合一致とexact str・重複なし行により `KeyError` になりません。
- generationは正のexact intに限定され、Python整数演算にoverflowはありません。adapterの `gen - 1` は非負で、超過は `IndexError` として `None` に閉じます。
- `_resolve_activation_entry` は未知env、登録数超過、世代・env・hash不一致を `None` にし、[_is_valid_activation_successor](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract.py:417) は `is_valid_successor` の結果をそのまま返しています。
- callable検査はrecord処理前の [env_contract_activation.py:343](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:343) にあり、serial 1だけのchainでも発火します。
- no-op、skip、downgrade、相殺、不正successor、非bool、callback例外以外の未承認な受理集合変更は見つかりませんでした。

## 不変条件・波及

- 変更は指定4ファイルだけで、所有外3ファイルに差分はありません。
- headは serial 1／`f7807285...d3ed` のままです。`00000001.json` はHEADと同一で、ファイルSHA-256も双方 `6a44b5b1...ec34d` でした。
- docs、activation record directory、凍結成果物に差分はありません。
- activation leafのimportはstdlibだけで、env固有literalもありません。`TYPE_CHECKING` 下の相対importは実行時importを生じません。
- `conftest.py` は `GENERATIONS` とcatalogを同時差替えし、serial 1なのでcallback未発火でも必須callableを満たします。
- `execution_guard.py` が消費する `ActivationState` の型・fieldは不変です。
- `test_campaign.py` のpytest任意importと素Python `_run()` 契約に、新しい非stdlib依存や未更新callerはありません。
- `git diff --check` は成功しました。

既存assertのうち、terminal generationは `(3, 1)` assertionへ、downgradeのcurrent/historical assertionsはforwardのg2/g1 assertionsへ適切に再構成されています。旧 `assert head is not None` はhelper再構成で消滅、terminal serial assertionだけが実質的に未置換です。追加・変更されたskip／xfailはありません。

## 総括

**判定: NO-GO**  
**must-fix: 1件**

multi-record正例へ `assert state.activation_serial == 3` を復元すれば、実装ロジック上のfail-openは静的には認められず、再レビューでGO候補になります。