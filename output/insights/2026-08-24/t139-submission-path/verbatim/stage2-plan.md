## 現況と欠落

結論は GO である。entry 874 の [T-139] は投入経路 wave を明示的に起票可としており、旧 NO-GO より新しく、親 brief もこれを最終裁定としている。D626 の恒常 fail-closed は撤回するのではなく、「vector-bearing payload が無い間」の安全策から、実在 artifact を使う resolver へ移行する。

現状は次のとおり。

- 単位1〜4の manifest/binding、safe I/O、schema、semantic validator、attempt authority は再利用できる。
- `_semantic_validator.py:998-1114` はすでに、`compile_commands` の sibling `CMakeCache.txt` を `_safe_io.read_relative_regular_bytes()` 経由で no-follow 再読している。申告 `cmake_cache` / `trace_enabled` / `analysis_enabled` は raw 三者検査後の不一致拒否にしか使っていない。production ロジックの追加は不要で、説明と回帰テストの固定だけでよい。
- `_writer.py:29-36` の `_assert_vector_authority()` は `ApprovedManifest.__annotations__` を見るだけで常時拒否する。ここが実 publication を止めている直接の欠落。
- `_manifest.py:208-226` は D282 payload を直接ロードして view を作るため、実 manifest artifact、二段 fold、vector index を持たない。
- `_binding.py:93-162` は解決済み approval capability を保持しないため、writer へ authority を運べない。
- 現行 index は SHA-256 `c66953bef617ff34e51ed988cf063c8e86e2a42e4132cdbab7f02732f2dc0643`、42 vector、内訳は正例1・拒否/API 41。vector JSON 42本は byte 不変で再利用できる。
- 射影された7 production file の小計は4,023行だが、これは `_git.py`、safe I/O、schema、attempt authorityなどを含まないため、D509の全体実測値ではない。
- pytest は実行しておらず、緑とは判定しない。

本当に欠けている結線は、次の5点だけである。

1. canonical history上の vector-bearing successor payload。
2. payloadに外部pinされた tracked manifest。
3. D282から現在値までの effective approval resolver。
4. sealed authorityを運ぶ `_PreregBinding` と、それを検査するwriter。
5. writer正例と三つの差替え負例を含む追加vector。

## provisional裁定への攻撃

旧 NO-GO の根拠は当時は正しかった。vector-bearing payloadが無い状態で resolver を先に作ると、偽造可能なpublic dataclass、writerへの未接続、D282 loader二重実行が生じるからである。しかし entry 874 は、その発火artifactも同じwaveで作ることを明示して起票可にした。したがって「artifact不在なので作らない」という時期判断は失効し、D626の安全要件だけが残る。

provisional P1〜P3への攻撃結果は次のとおり。

- P1の二段foldとprivate sealは採用する。ただし `ApprovalPayload.forward_supersedes` の自由文字列をそのまま使う案は不可。successor用v2 payloadで `decision_id + fold_commit + path + sha256` の構造化参照にする。
- P2の「payload側外部pin」は、manifestとindexを先にcommitし、その後のcanonical payloadが両方を三つ組でpinする形でなければ閉じない。manifest自身のindex宣言、callerから渡された期待digest、production source中のindex hash literalはいずれも受理根拠にしない。
- P3のwriter方針は採用するが、authority引数をwriterへ追加してはならない。caller注入になるためである。authorityはsealed binding内に運び、writerの公開形は現在の3 keyword-only引数のまま保つ。
- 現行 `_assert_vector_authority()` の「型にfieldがあるか」という検査はauthority検査ではない。sealed resolver出力、payloadのindex ref、manifest宣言の三者一致を検査する関数へ置換する。
- manifestはpayloadより先にcommitする。その時点の `approval_fold_commit` はbaseと同じでよい。後続payloadをresolverが発見し、sealed view上のeffective値を更新するのがD574決定(5)の意味である。

D626の拒否条件はすべて残す。

- `forward_supersedes` の参照先が無い。
- 同一nodeに複数successorがある。
- chainにcycleがある。
- baseに到達しないdisconnected payloadがある。
- successorが無く、base D282にvector authorityが無い。
- manifest、payload、indexのどれかが三つ組と一致しない。
- capability tokenが不正。

## file:line実装plan

1. `orchestrator/preregistration/approval_payload.py`

- `:16-74` に successor payload v2 の `decision_kind`、exact-key集合、構造化 `forward_supersedes` grammarを追加する。
- `:76-96` に duplicate decision、bad predecessor、payload/manifest/index ref不正のreasonを追加する。
- 既存 `ApprovalPayload` と `load_approval_payload()` (`:145-188`) はD282 regression用として挙動を変えない。
- `:397-509` のexact-key、field、BlobRef parserを再利用し、末尾に `_SuccessorApprovalPayload` とbytes-only parserを追加する。
- successor payloadは少なくとも `decision_id`、構造化predecessor、`base_approval_fold_commit`、D282由来の承認projection、`approval_manifest`三つ組、`conformance_vector_index`三つ組を持つ。
- parsed dataclass自体をauthorityとして扱わない。authority化はresolverのprivate token経由だけにする。
- `preregistration/__init__.py:17-28` から新しい型やresolverをexportしない。

2. `orchestrator/submission_gate/_approval_resolver.py` 新規 `:1-約220`

- `_EffectiveApproval` を `frozen=True, slots=True, init=False`、module-private token、keyword-only constructorで実装する。
- D282の固定refをbaseとして一度だけロードする。
- `base_approval_fold_commit..measurement_head` の canonical `docs/decisions.md` path historyからsuccessor payloadの導入commitを求める。payload自身に自分のcommitを書かせない。
- decision headingとpayload `decision_id` を一致させ、初出commitをそのpayloadのfold commitとする。
- missing predecessor、payload mutation/removal、cycle、disconnected node、複数successorを拒否し、唯一のtipをeffectiveとする。
- successorが無ければsealed base authorityを返すが、`vector_index=None` のためwriterは従来どおり拒否する。
- resolver結果にbase/effective payload ref、manifest ref、vector index ref、measurement root identityを保持する。
- `_assert_effective_approval_intact()` は再resolveせず、保存済みrefのGit blobとsealだけを再検査する。

3. `orchestrator/submission_gate/_git.py`

- 既存 `read_commit_blob` / `require_ancestor` と同じ実行境界の隣に、特定pathの祖先順historyを返すprivate helperを1個だけ追加する。
- resolver内で独自のsubprocess wrapperを二重実装しない。
- first-parentまたはcanonical fold規約に合う既存履歴契約を使い、base外、非祖先、重複導入をfail-closedにする。
- このファイルは射影外なので、author開始時に既存helperの現行行番号を確定してから差分位置を固定する。新しいGit操作面が不要なら編集しない。

4. `orchestrator/submission_gate/_manifest.py`

- `:140-199` の `ApprovedManifest` を拡張し、`manifest_ref`、declared base/current fold、effective fold、`vector_index`、sealed `_EffectiveApproval` を保持させる。
- D282 legacy viewでは `manifest_ref=approval_ref`、`vector_index=None` とし、既存semantic regressionを維持する。
- `:208-226` の `_load_approved_manifest()` は `measurement_head` を受け、resolverをexact 1回呼び、payloadがpinしたmanifest blobを読み、canonical JSONとexact-keyを検査する。
- manifestのindex宣言はeffective payloadの三つ組と一致しなければ拒否する。一致だけでは受理せず、payload側pinが存在することを必須にする。
- `:297-341` は `record.approval_manifest == approved.manifest_ref`、`record.fold_commit == effective approval fold`、errataのapproval foldもeffective値、という比較へ変える。
- `prereg_commit` は既存の事前登録ancestor rootのまま保持し、effective approval foldへ置換しない。

5. `orchestrator/submission_gate/_binding.py`

- `:54-89` のrecord生成は、manifest refとeffective foldを `ApprovedManifest` から取る。
- `:93-162` の `_PreregBinding` に必須keyword-only `authority: ApprovedManifest` を追加する。seal済みexact type以外を拒否する。
- `:164-217` の `assert_intact()` は既存root/Git検査に加え、manifest/effective approvalのseal、payload・manifest・index blobs、commit順序を再検査する。loaderは呼ばない。
- `:220-261` は先に `measurement_head` を解決し、`_load_approved_manifest(..., measurement_head=...)` を一度だけ呼び、同じauthorityをrecordとbindingへ渡す。
- unit3等のfixtureが `_PreregBinding._issue()` を直接呼ぶ箇所には、sealed legacy authorityを明示的に渡す。`None` defaultは設けない。

6. `orchestrator/submission_gate/_writer.py`

- `:29-36` を `_assert_vector_authority(*, binding: _PreregBinding) -> None` に置換する。
- seal済みbinding、seal済みmanifest/effective approval、payload index ref、manifest index refの一致を要求する。global class annotationやsource literalをauthorityにしない。
- `_publish_receipt()` のsignature `(*, repository_root, raw_bytes, binding)` は変更しない。authority用の第4引数、relative path、expected digestは追加しない。
- `:61-76` の順序は、raw parse → binding検査 → schema/semantic検査 → vector authority検査 → binding再検査 → publish、とする。
- publishするのは入力 `raw_bytes` そのものとし、parse後の再serializationを禁止する。
- `_destination()` と固定 `output/receipts/t139/<study>--<series>--<stage>.json`、`create_receipt_bytes()` のcreate-only性は不変。

7. `orchestrator/submission_gate/_semantic_validator.py`

- production predicateは変更しない。
- `:1038-1042` の説明だけを、正の三者はconfigure argv・compile commands・raw sibling cacheであり、三つの申告値はreject-onlyだと明確化する。
- `:1062-1098` のsibling path導出とno-follow read、`:1100-1114` の申告不一致拒否の順序を維持する。
- `:594-646` のreceipt preregistrationとbinding recordの全field比較により、新manifest refとeffective foldは追加schema fieldなしで結線される。
- `:2527-2605` のwriterからの呼出し形も変更しない。

8. tracked artifact

- `orchestrator/preregistration/t139-approval-manifest-v1.json` 新規。固定schema、base/current approval fold、承認projection、vector index宣言を持つ。
- `docs/decisions.md` に新しいcanonical decisionとexact fenced successor payloadを追加する。fold時にdecision IDを確定し、凍結済みD574本文は編集しない。
- `receipt-schema-v1.json` と `record-items-v2.md` は変更しない。

9. vectors/tests

- `orchestrator/tests/fixtures/t338_submission_gate/conformance/index-v1.json:1-47` は既存42 entryをbyte-for-byte維持したまま、末尾に4 entryを追加する。
- 新規vectorはwriter publish正例、manifest差替え、payload差替え、index差替えの4本。
- `test_t338_submission_gate_unit5.py:315-338` の件数を46、正例2、拒否/API 44へ更新し、旧42のID/path/digestが不変であることを別assertで固定する。
- `:341-345` のwriter signature検査は3引数のまま維持する。
- `:360-443` はlegacy authority不在拒否を残し、新しいsealed authorityの通過検査を追加する。
- `:474-561` に4つの新entrypointを実行する分岐を足す。
- `orchestrator/tests/test_t139_effective_approval.py` を新設し、chain、seal、二重loader不在を集中的に検査する。
- `orchestrator/tests/test_t139_submission_path_consumer.py` を新設し、private resolverからwriterまでのconsumer経路を通す。

`submission_gate/__init__.py:7` と `preregistration/__init__.py:17-28` はno-touchとする。

## commit順序とpin閉包

順序は必ず次にする。

```text
B0  現行base
 |
 I   旧42 vectorを不変のまま新4 vectorとindexをcommit
 |       V = (index path, I, index sha256)
 |
 M   manifestをcommit
 |       base_approval_fold_commit = D282 fold
 |       approval_fold_commit      = D282 fold
 |       manifest vector declaration = V
 |
 P   canonical successor payloadをfold
 |       forward_supersedes -> D282
 |       approval_manifest -> (manifest path, M, manifest sha256)
 |       conformance_vector_index -> V
 |
 C   resolver/writer/testの最終結線
```

重要点は以下である。

- payload `P` は自分自身のcommitを持たない。resolverがcanonical history上の初出commitをfold commitとして与えるため、自己参照が無い。
- manifest `M` はpayloadより前なので、初期 `approval_fold_commit` はbaseと同じでよい。resolverがD282から`P`へ進み、sealed viewとreceiptの `fold_commit` にはeffectiveな`P`を入れる。
- 外部trust edgeは `P -> V` である。manifestの `V` は照合対象にすぎず、authorityではない。
- `P -> M` も固定するため、callerが別manifestを選ぶ余地は無い。
- sourceにはindex digestを置かない。sourceはD282 base、canonical path grammar、parserだけを持つ。
- index内の各vector `path/sha256` はindex commit `I` のtreeに対して解決する。HEADの同名fileを読まない。
- `record.approval_manifest=M`、`record.fold_commit=P`、`record.prereg_commit=既存ancestor root` と役割を分離する。
- 将来のsupersessionは `I2 -> M2(current=P) -> P2(forward_supersedes=P)` の同じ順序を繰り返す。

## test・変異plan

焦点正例:

- D282から唯一の`P`を解決し、manifestとindexを検査してsealed bindingを発行する。
- unit3の完全receiptをsemantic validatorへ通し、writerが固定namespaceへ発行する。
- 発行先bytesが入力 `raw_bytes` とexact一致する。
- 同じpathへの2回目publishは `EEXIST` で失敗し、既存bytesを保持する。
- configure argv、compile commands、raw sibling cacheが正しい場合に通る。申告値は一致しているが受理根拠にはならない。

焦点負例:

- successor無しのD282 bindingは従来どおり `vector_authority_unavailable`。
- manifestだけがindexをpinする。
- callerが期待index、payload、manifestを渡そうとする。
- manifest ref差替え、payload fold差替え、index ref差替え。
- missing predecessor、cycle、同一predecessorへの複数successor、disconnected payload。
- unsealed `_EffectiveApproval`、`ApprovedManifest`、`_PreregBinding`。
- payload/manifest/indexのpath、commit、sha256の各1 field差替え。
- raw `CMakeCache.txt` が欠落、symlink、duplicate macro、非UTF-8、値不一致。
- 申告値が正しくてもraw cache、configure argv、compile commandのいずれかが誤れば拒否。
- 実三者が正しくても申告 `trace_enabled` / `analysis_enabled` / `cmake_cache` が違えばreject-onlyで拒否。
- semantic検査後にbinding/root identityを変えた場合、publish直前の再検査で拒否。
- parsed documentを再serializationした別bytesをpublishする変異。

主要な変異候補:

- `_assert_vector_authority()` を恒真return。
- payloadではなくmanifestのindexだけを採用。
- manifest/payload比較の `!=` を反転または削除。
- 複数successorから先頭を選ぶ。
- missing predecessor時にbaseへfallback。
- cycle集合への追加を削除。
- private token検査を `isinstance` だけへ弱化。
- writerから2回目の `binding.assert_intact()` を削除。
- writer内でresolverを再実行して二重loaderにする。
- `raw_bytes` の代わりにJSON dump結果をpublish。
- raw CMake読取を申告 `cmake_cache` へ置換。
- sibling readからno-follow層を外す。
- 申告値一致時にcompile検査をearly return。

親が `tools/run_tests.py` 経由で実測する集合:

1. 新しいapproval parser/resolver焦点テスト。
2. `test_t338_submission_gate_unit5.py`。
3. CMake raw/reject-onlyのunit3 nodeid。
4. private consumer test。
5. `test_t139_preregistration_binding.py`。
6. `test_t338_submission_gate_unit1.py` から `unit5.py` までの全regression。
7. mutation matrix。
8. repository受入全走。
9. 関連check、commit後のprovenance監査。

本planでは一件も実走していない。

## scope外・停止条件

- D292の `pilot_submission = forbidden` / `main_submission = forbidden`、計算資源投入、pilot/main実走、解除decisionは変更しない。
- driver、collector、PBS、Pegasus registry、`submit_pilot` は作らない。
- D264の4名前は今回exportしない。`submission_gate/__init__.py` は空のまま、`preregistration/__init__.py` も非admission面のままにする。
- `submit_pilot` の恒常deny stubは置かない。今回はprivate gateの受理正例を作るが、投入APIそのものを作らないため、D264とD292の双方に整合する。
- `orchestrator/tests/test_spool_fold.py` はno-touch。
- worklog entry 874の[T-139]本文とdigestはno-touch。記録が必要なら別entryをappendし、874を再生成・修正しない。
- 既存known-violation waveのbranch、test、ownershipへ触れない。
- 既存42 vector JSONはbyte不変。変更対象はindexと新規4本だけ。
- frozen schema、record-items、D574本文は変更しない。

D509実測は、編集前のbase commitと最終treeで同じallowlistを使う。保守的には次の集合を合計する。

```text
git ls-files 'orchestrator/submission_gate/*.py' \
  'orchestrator/preregistration/approval_payload.py'
```

これをlocale固定でsortして `wc -l` へ渡し、個別値とtotalを記録する。D509の既存checkerが別のexact allowlistを持つ場合はその値を正本とし、上の保守的合計も併記する。baseline、各artifact commit後、最終差分後に測り、6,200行以下を要求する。

超過時に削ってはならないものは、raw CMake再読、no-follow、payload側index pin、manifest/payload照合、cycle/欠落/複数候補拒否、private seal、二重loader防止、publish前の再検査、exact raw-byte publish、create-only namespace、既存unit1〜5 predicateである。これらを削らないと収まらない時点で実装を止め、予算拡張または意味不変の独立縮約を裁定へ返す。

author分割は推奨しない。vector/indexのcommit `I`、manifest `M`、payload fold `P`、そのcommit値を使うfixtureとresolverが直列に依存する。authority側とwriter/test側をfile単位で分けること自体は可能だが、両者が `I -> M -> P` を跨いで往復するため実装依存が循環する。単一authorで順次commitし、consult/reviewだけを並列化するのが安全である。

## 総括

entry 874に従い、T-139投入経路は実装可能である。最小の安全な形は、既存42 vectorを保持した `index I`、base foldを持つ `manifest M`、両方を外部pinするcanonical `payload P` の順にcommitし、D282から`P`を一意解決したsealed authorityを `_PreregBinding` 経由でwriterへ運ぶ構成である。

writerのsignature、固定namespace、create-only、semantic validatorのraw CMake検査は維持する。D292、D264の非export、pilot/main禁止は一切動かさない。