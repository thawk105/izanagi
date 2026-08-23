## 所見

1. **F1: real / blocker**
   場所: [_manifest.py:243](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_manifest.py:243)、[_manifest.py:267](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_manifest.py:267)、[_manifest.py:315](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_manifest.py:315)
   具体的失敗: private explicit-ref seamへ、固定D282/D574値を保ちながら任意の同一index refを指すmanifest/payloadを渡すと、`_require_vector_index()`は「両refが同じでblobが解決可能」だけで通します。その結果、固定した`T139_*_REF`ではないartifactからsealed `ApprovedManifest`を発行できます。`_assert_approved_manifest_intact()`も保持された可変refを再読するだけで、外部pin定数との同一性を再検査しません。private callerは任意のvector authorityをsealed bindingへ運べます。
   推奨fix: seal生成を固定wrapperだけに限定する。explicit-ref seamはparse/比較結果までに留め、`ApprovedManifest`を返さない。併せてintact検査でmanifest/projection refが固定定数と完全一致することを要求し、両artifactが同じ別indexを指す協調変異を拒否するtestを追加する。
   DW-G05影響: 「固定D574 projection由来だけを受理」は成立しないため、成果物受理をblockします。

2. **F2: real / must-fix**
   場所: [test_t139_submission_path.py:200](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t139_submission_path.py:200)、[test_t338_submission_gate_unit5.py:623](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t338_submission_gate_unit5.py:623)
   具体的失敗: `test_head_same_name_replacement_is_not_authority`はworktreeを書き換えるだけでHEADをcommitしません。fixed blob読取を`HEAD:path`へ退化させるM3でも、HEAD blobは元のままなのでtestが通ります。historical index vectorも、新しいcommitを作って合成`bad_ref`をhelperへ直接渡しており、固定resolverやwriterを通りません。vector記述の「fixed historical commitを変異」と一致していません。
   推奨fix: 固定I/A commitを残したまま、同名payload、manifest、indexを変更した新HEADをcommitし、通常resolverを呼ぶtestへ変更する。historical digest負例も最低限projection loader全体を通し、helper直呼びをやめる。
   DW-G05影響: M3の前後maskを緑として記録できません。

3. **F3: real / must-fix**
   場所: [test_t338_submission_gate_unit3.py:649](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t338_submission_gate_unit3.py:649)、[test_t338_submission_gate_unit5.py:585](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t338_submission_gate_unit5.py:585)
   具体的失敗: positiveが渡す`raw_bytes`自体を`json.dumps(..., separators=(",", ":"))`で生成しています。writerを同じ方法で再serializeするM6は同一bytesを生成できるため、published bytes一致testをすり抜けます。
   推奨fix: 意味は同じだがcompact再serializeとは異なるpretty JSON、末尾LF、または許可された空白を含むraw receiptをpositiveへ渡す。既存の「published bytesは入力と完全一致」という期待値は変更しない。
   DW-G05影響: exact raw-byte publishの変異検出証拠が不足しています。

4. **F4: real / must-fix**
   場所: [test_t338_submission_gate_unit5.py:82](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t338_submission_gate_unit5.py:82)、[test_t338_submission_gate_unit5.py:325](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t338_submission_gate_unit5.py:325)、[test_t139_submission_path.py:98](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t139_submission_path.py:98)
   具体的失敗: index-v2と新vectorはHEAD上のindexから期待値とdigestを導出しています。旧v1は独立literalで正しくpinされていますが、v2には独立literal tripleも、HEAD bytesとsource-pinned historical v2 bytesの一致検査もありません。新vectorとHEAD indexを整合的に変えれば、production authorityが旧historical bytesを指したままtestだけ通せます。loader testもhistorical indexの件数46しか固定していません。
   推奨fix: 独立literalの`_V2_INDEX_REF`をtestへ置き、HEAD bytes、historical bytes、production projection refの三者一致を検査する。parametrize元もそのpinとの一致を前提にする。
   DW-G05影響: 新4vectorの実行証拠がauthority artifactから独立しておらず、検出力閉包が未完成です。

5. **F5: real / must-fix**
   場所: [test_t338_submission_gate_unit1.py:147](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t338_submission_gate_unit1.py:147)、[test_t338_submission_gate_unit3.py:89](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t338_submission_gate_unit3.py:89)、[_manifest.py:319](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_manifest.py:319)
   具体的失敗: unit1/unit3の共通fixtureは`object.__new__`とprivate tokenで不完全な`ApprovedManifest`を作り、production側も欠落fieldをlegacyとして無条件returnします。したがって多数のconsumer testはD574 authority保持や再検査を実際には通りません。また段5のconstructor列挙は、この2つの構築経路を数えていません。writer正例は通常resolverを通るためpublish自体は別途覆われていますが、callsite/consumer閉包の主張は過大です。
   推奨fix: legacy forgeはM1専用負例に局所化し、通常consumer fixtureは完全なauthorityを通常resolverから得る。可能ならproductionの欠落field returnを除去する。constructor inventoryへ`object.__new__`経路も含める。
   DW-G05影響: callsite列挙と既存consumer回帰の完了記録を修正する必要があります。

6. **F6: real / must-fix**
   場所: [approval_payload.py:178](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/preregistration/approval_payload.py:178)、[approval_payload.py:187](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/preregistration/approval_payload.py:187)、[test_t338_submission_gate_unit1.py:198](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t338_submission_gate_unit1.py:198)
   具体的失敗: `VectorApprovalProjection`と`ApprovalManifestProjection`は非underscoreの新public dataclassです。stage4の「新public dataclassを作らない」に直接反します。nonexport testは`submission_gate` packageの名前しか検査していません。
   推奨fix: 両型をmodule-private名へ変更し、approval moduleとpackageの非export検査を追加する。
   DW-G05影響: API非拡張の主張を現状のまま記録できません。

7. **F7: real / nit**
   場所: [test_t139_submission_path.py:110](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t139_submission_path.py:110)、[approval_payload.py:243](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/preregistration/approval_payload.py:243)
   具体的失敗: 実装の`object_pairs_hook`はnested duplicateも拒否しますが、testはroot duplicateだけです。top-levelだけ重複検査する退化を殺せません。
   推奨fix: `forward_supersedes.approval`とmanifest namespace内のnested duplicateを追加し、bool、指数overflow数値も拒否されることを補助的にpinする。
   DW-G05影響: parser実装の現状は通りますが、parser変異検出力の記録に限定的な穴が残ります。

8. **F8: real / nit**
   場所: [_manifest.py:36](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_manifest.py:36)、[_manifest.py:243](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_manifest.py:243)、[_manifest.py:319](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_manifest.py:319)
   具体的失敗: 数値上は6,186行で正しい一方、169文字の定数、170文字のsignature、143文字のtupleなど、目標6,187へ収めるための圧縮が読みやすさを落としています。
   推奨fix: 絶対上限6,200の範囲でsignature、定数、比較tupleを整形する。収まらなければ目標値より可読性を優先する裁定を求める。
   DW-G05影響: runtime阻害はありませんが、保守性注記が必要です。

## 検出力表

| 変異 | 判定 | 静的検出力 |
|---|---|---|
| M1 writer guard恒真化 | 検出 | legacy publish負例が例外を要求するため赤になります。 |
| M2 manifest/payload比較削除 | 検出 | 片側変異loader testがsealed authorityを返して赤になります。ただしwriter統合ではなくseam水準です。 |
| M3 fixed payloadをHEAD読取へ退化 | **未検出** | worktreeだけの変更なのでHEAD reader mutantが生存します。F2。 |
| M4 token検査弱化 | 検出 | wrong-token直接constructorが赤になります。ただし既存`object.__new__`経路は残ります。 |
| M5 binding保持/再検査削除 | 部分検出 | 通常resolver bindingの`vector_index`単独変異は検出します。協調したmanifest/payload/index差替えはF1経路で通ります。 |
| M6 raw bytesを再serialize | **未検出** | positive raw自体が同一compact serializer由来です。F3。 |
| M7 raw CMakeを申告値へ置換 | 検出 | raw siblingだけ1、申告と他脚0の既存testが赤になります。 |
| M8 新必須vector削除、payload pin未更新 | 検出 | 46件、末尾4 ID literal、固定件数で赤になります。ただしv2全体の独立pinはF4。 |

旧index tripleと42 projectionは独立literal、historical bytes、worktree bytes、先頭42 entriesで閉じています。新4件も46件parametrizeには全て入っており、positiveは通常の`_resolve_effective_preregistration()`経路を通っています。弱点は収集漏れではなく、authority pinと期待値の独立性です。

## stage4裁定への直接攻撃

- 「caller指定refを持たない」はF1により成立していません。public wrapperのsignatureだけを固定しても、sealを発行するexplicit-ref seamが残っています。
- 「新public dataclassを作らない」はF6により直接違反です。
- M3とM6の事前登録は、現在のtest入力では実効点へ照準できていません。
- manifest/payload片側変異は内側のindex ref一fieldだけを変え、期待codeも別分岐を検査しています。この点自体はrefutedです。ただし両側を同じ別authorityへ協調変更する攻撃はF1で受理されます。
- parser実装はnested duplicate、型違い、NaN、不正BlobRef pathを拒否しています。schemaの意味的深さは固定され、`RecursionError`も変換されます。source-pinned SHAがexact bytesを認証するため、JSON key順や空白までparserでcanonical強制する追加要件は承認外の過剰拒否です。
- `submission_gate/*.py`は実測6,186行で、未tracked fileはありません。旧index-v1、旧42vector、docs、spool、package export、semantic predicateの変更もimplementation patchにはありません。
- direct publish callのAST allowlistと`submission_gate.__all__ == ()`は閉じています。AST alias hardeningはstage4で明示的にscope外です。

## scope外

- B2 sealed series/receipt-set、producer、driver、collector、report、ledger consumer、D292解除、PBS/qsub、live receiptは今回の記録対象外です。記録先はinsight/handoffです。
- 並行branch所有の実運用履歴は射影資料だけでは確定不能です。patch面はartifact/test/productionだけで、docs/spoolを侵していません。
- [stage5-output.md:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage6/inputs/stage5-output.md:1)の「artifact変更なし」「9件」「production純増342」はUnit C単独の記述なら整合しますが、implementation patch全体は16 fileで、production authority JSONも52行追加されています。DW-G05へaggregateとして転記する場合は「Python production +342、authority JSON +52」と分けて補正してください。
- changed file単独、consumer集合、unit1からunit5個別の実行件数は射影にありません。親の関連9 file 339 passedは実測事実ですが、個別matrixはDW-G05 test recordへ残す事項です。

## 総括

親実測の339 passed、6,186行、provenance新規違反0は事実として採用します。review自身はpytestを実行していません。

結論は **blocker 1、must-fix 5、nit 2** です。最大の問題は、explicit-ref seamが任意の一致済みindexをsealed authorityへ昇格できる点です。これを閉じ、M3、M6、v2独立pin、legacy fixture、public dataclassを是正するまでDW-G05受理は不可です。