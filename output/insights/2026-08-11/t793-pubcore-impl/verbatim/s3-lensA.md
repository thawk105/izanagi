## 総括

**判定: NO-GO。**

段 2 の NO-GO 自体は維持するが、主理由は差し替えるべきである。(iii) と pubcore §10.2 は、科学的 `main_admission` を変えず、公表文書を要求せず、台帳だけを見る別の送信前 deny とするなら両立できる。新 D はこの区別を記録できるが、同じ呼出しを「運用 precondition」と改名するだけでは抵触を消せない。

現プランにはそれ以前に、台帳の worktree 差替え、未 commit 予約、孤児 gate、fold resume の迂回、canonical D291 を parse できない文法、`F_p` 差替え可能 API、`exact_closure` の部分解決がある。(i)・(ii)・(iv) だけの先行 land も不可である。

ファイル変更・commit・テスト実走は行っていない。worktree は clean のままである。

## 独立再測

| 項目 | 結果 |
|---|---|
| `F_p` | **一致。** `b13b7ea840ad51199f40b3a534c9d1cdb422af2e`。親には D291 がなく、この commit が追加した D 見出しは D291 のみ。brief base `974207ae…` の祖先でもある。 |
| `F_p:docs/decisions.md` SHA-256 | **一致。** `3d2cd5dc6cf63c5928a3ec64a91ae3b3c530dafc83d83d52a038a2eb5cf0c2b8`。 |
| D292 の所在 | **`F_p` には存在しない。** `F_p:docs/decisions.md` は D291 の末尾で EOF。D292 は後続 commit で追加されている。 |
| 根 | **親と一致。** 公表 `88d68f91…`、primary 実台帳 `dce4ae4f…`。公表 core の「同じ commit」は偽。[publication-core-v2.md:548](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/output/insights/2026-08-11_t139-pubcore-stage2/publication-core-v2.md:548) [t139-alpha-reservations.jsonl:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/output/registry/t139-alpha-reservations.jsonl:1) |
| `(root, kind)` | **親と一致。** `(88d68f91…, individual_publication)` 対 `(dce4ae4f…, alpha_reservation)` で両軸とも異なる。 |
| D291 top-level key | **14 個。**プランの数え上げは正しい。 |
| D291 role 数 | `approved_blobs` は **2 role**、`document_relations` は **3 role**。プランの区別は正しい。[docs/decisions.md:13347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/docs/decisions.md:13347) [docs/decisions.md:13369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/docs/decisions.md:13369) |
| P Markdown 構造 | `## fields` は一意、外側の H3 は exact `p01,p02,p03`。既存 fence-aware parser の前提に適合する。[addendum-p-draft.md:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/output/insights/2026-08-11_t139-pubcore-stage2/addendum-p-draft.md:71) |
| P5 の直接経路 | **実在する。** fresh な `validate_spool_tree()` と `plan_fold()` はともに `_discover()` を通る。[tools/spool_fold.py:1041](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:1041) [tools/spool_fold.py:1932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:1932) ただし resume/apply の迂回が残る。 |
| 0-byte tracked file | 「不在」と「存在する空」を区別できる点だけは正しい。しかし worktree 選択・未 commit 行・共有 lock を閉じないため、全体として fail-closed とはいえない。 |

## 所見

### A1 — severity: blocker — caller が worktree を選ぶことで「唯一の台帳」を複製できる

- **根拠:** `p03` は checkout 選択による台帳差替えを禁止し、根から唯一の実体への束縛を要求する。[addendum-p-draft.md:165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/output/insights/2026-08-11_t139-pubcore-stage2/addendum-p-draft.md:165) D291 の保証境界も canonical local main と Git common directory を単位にする。[docs/decisions.md:13503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/docs/decisions.md:13503) 一方、計画 API は `repository_root` を caller 引数にし、lock は台帳 file/inode にしか置かない。[s2-plan.md:90](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t793-pubcore-impl/s2-plan.md:90)
- **落ちる具体入力:** 同じ Git common directory を共有する `/work/1/SFC/tanab/izanagi` と `.claude/worktrees/dev-wave-t793-pubcore-impl` をそれぞれ `repository_root` にし、両方の 0-byte 台帳へ予約する。物理 path、inode、lock が別なので、双方が `(88d68f91…, individual_publication, 1)` を取得できる。
- **成果物影響:** 試行台帳に ordinal 1 の競合予約が生じ、公表表の「一意に予約済み」という proof chain が偽になる。

### A2 — severity: blocker — 予約行を canonical history に固定する transaction がない

- **根拠:** 計画の writer は worktree file へ append して `PublicationReservation` を返すだけで、予約が初出した commit を返さない。[s2-plan.md:102](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t793-pubcore-impl/s2-plan.md:102) witness にも `reservation_commit` がない。[s2-plan.md:233](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t793-pubcore-impl/s2-plan.md:233) 既存 primary 契約は同一 land lock への取込みと初出 commit の再導出を要求する。[docs/decisions.md:12953](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/docs/decisions.md:12953) [record-items-v2.md:656](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:656)
- **落ちる具体入力:** 0-byte 台帳に ordinal 1 を append するが commit しない。その worktree bytes を `inspect_publication_ledger()` が読むと reservation precondition が成立し得る。その後、worktree 行を破棄すれば Git 履歴には消費記録が一度も残らない。
- **成果物影響:** 失敗後の ordinal 非解放が破れ、同一 dataset に対する再予約で試行台帳の受理集合が増える。

### A3 — severity: blocker — (iii) は新 D を作っても active gate にならず、D292 誤読経路も残る

- **根拠:** §10.2 が禁じるのは `main_admission` の変更と、公表文書の存在を `submit_main` に要求することである。[publication-core-v2.md:644](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/output/insights/2026-08-11_t139-pubcore-stage2/publication-core-v2.md:644) 旧 B は既に「科学的 admission は狭めず、別の送信前 deny」と分離していた。[addendum-b.md:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/output/insights/2026-08-09_t139-addendum-b/addendum-b.md:55) したがって ledger-only deny なら両立可能だが、計画は `submit_main` を scope 外に残し、公開 `require_*` 関数だけを置く。これは「部品だけを gate に見せない」という D264 と、「必ず通る共有 verifier に置く」という D288 に反する。[docs/decisions.md:12185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/docs/decisions.md:12185) [docs/decisions.md:13175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/docs/decisions.md:13175)
- **落ちる具体入力:** 一意な reservation を持つ ledger で `require_source_main_publication_reservation_precondition()` を呼ぶ。正常 return 後、caller が witness の `submission_authority="not_granted"` を読まず次の送信処理へ進めば、通常の exception-only `require_*` API として投入許可に誤読できる。report CLI の rc=0 も同型である。
- **成果物影響:** canonical decision による解除なしに source 本走が始まり、certified primary と試行台帳が生成され得る。

### A4 — severity: blocker — `_discover()` 結線は durable resume と直接 `apply_fold()` を覆わない

- **根拠:** fresh `plan_fold()` は `_discover()` を通るが、active transaction がある CLI は stored plan を直接復元する。[tools/spool_fold.py:2504](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:2504) `apply_fold()` も既存 state を読むだけで再 discovery しない。[tools/spool_fold.py:2277](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:2277) state version は固定 `1` で、gate version を束縛しない。[tools/spool_fold.py:2168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:2168)
- **落ちる具体入力:** marker gate 導入前に作られた version 1 state が、未解決 P blob を承認する `docs/decisions.md` の after bytes を保持している。新コードで CLI を resume すると `_discover()` を通らず、その after bytes が適用される。外部 caller が組み立てた `FoldPlan` を直接 `apply_fold()` に渡す経路も同じ。
- **成果物影響:** 未解決 `core_ref` を持つ追補 P が canonical decision に fold され、材料レポートの参照が永続的に解決不能になる。

### A5 — severity: must-fix — `approved_blobs:` は承認 decision の閉じた schema ではない

- **根拠:** 計画 guard は `approved_blobs:` の triple だけを抽出する。[s2-plan.md:218](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t793-pubcore-impl/s2-plan.md:218) 現行 `_decision_symbols()` が検査するのは H2 形状だけで、decision 本文の authority schema は制約しない。[tools/spool_fold.py:701](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:701)
- **落ちる具体入力:** canonical decision fragment が `approved_blobs:` を使わず、本文で「この path/commit/sha256 の追補 P を承認する」と記す。その triple が marker 入り blob を指していても guard の target は空集合となり、fragment は fold できる。
- **成果物影響:** 未解決 P blobが承認済み参照として材料レポートへ入る。

### A6 — severity: blocker — 計画どおりの D291 parser は canonical `F_p` bytes を読めない

- **根拠:** 計画は D291 を「D292 直前まで」切り出す。[s2-plan.md:182](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t793-pubcore-impl/s2-plan.md:182) しかし `F_p` のファイルには D292 がなく、D291 が EOF まで続く。さらに計画は historical role ごとに `note` を持つとするが、実 bytes では `note` は二 role の sibling である。[docs/decisions.md:13426](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/docs/decisions.md:13426) `required_core_ref.commit` にも `symbolic:F_p` 後の説明文が存在する。[docs/decisions.md:13364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/docs/decisions.md:13364)
- **落ちる具体入力:** 正規入力である `b13b7ea8…:docs/decisions.md` を `load_d291_payload()` に与える。D292 delimiter が見つからず拒否される。回避のため current checkout の D292 を delimiter に使うと、今度は `F_p` 以外の文書を trust root に混ぜる。
- **成果物影響:** 正規の二 role が未承認扱いになり、材料レポートの承認欄と参照集合が空または error になる。

### A7 — severity: blocker — `F_p` を caller が差し替えられる公開 parser がある

- **根拠:** D291 は manifest より先に固定 `F_p` の payload を読むことを要求する。[docs/decisions.md:13312](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/docs/decisions.md:13312) しかし計画の `parse_d291_payload()` は任意 bytes と overrideable `fold_commit` を受け取る。[s2-plan.md:159](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t793-pubcore-impl/s2-plan.md:159) その戻り値は trusted loader の戻り値と同じ型で、`require_d291_projection_exact()` も payload を caller から受け取る。
- **落ちる具体入力:** canonical D291 bytes と `fold_commit=88d68f9127b31df5aafc3d59607896626a1652e8` を渡し、`symbolic:F_p` を D234 の commit に置換した payload を作る。その payload から作った自己整合 projection は `require_d291_projection_exact()` を通り得る。
- **成果物影響:** 材料レポートの `required_core_ref.commit` と proof chain が、本来の `F_p` 以外へ差し替わる。

### A8 — severity: blocker — individual role resolver が D291 の集合ちょうど制約を迂回する

- **根拠:** D291 は approved role 集合をちょうど 2、同一 path の別 digest を拒否し、relations 節全体も一致させる。[docs/decisions.md:13441](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/docs/decisions.md:13441) ところが `resolve_d291_role()` は単一 `role` と `candidate` しか受け取らず、full projection 検査は別の任意 API である。[s2-plan.md:169](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t793-pubcore-impl/s2-plan.md:169) land 2 には両 API の「どちらか」を使わせる計画になっている。[s2-plan.md:582](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t793-pubcore-impl/s2-plan.md:582)
- **落ちる具体入力:** manifest が canonical `source_addendum_b` triple だけを持ち、`publication_core` を欠落させ、`document_relations.note` も変更している状態で、B の triple だけを `resolve_d291_role()` に渡す。単一 triple は正しいので approved resolution が返る。
- **成果物影響:** 不完全な manifest が source binding／材料レポートに受理され、D291 が定めた受理集合が広がる。

### A9 — severity: blocker — P exact-key の parser は適合するが、実行経路に一度も呼ばれない

- **根拠:** 既存 parser は fence 外の一意な `## fields` と、その範囲の H3 token を読む。[addendum_envelope.py:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/preregistration/addendum_envelope.py:83) P draft は exact に p01・p02・p03 の形なので、固定 expected set への差替え自体は成立する。[addendum-p-draft.md:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/output/insights/2026-08-11_t139-pubcore-stage2/addendum-p-draft.md:71) しかし計画上、fold に結線する `approval_guard` は marker しか検査せず、P wrapper の production caller がない。
- **落ちる具体入力:** marker を解決済みにした P blobへ `### p04 — post-hoc override` を追加し、正規の `approved_blobs:` triple から承認する。marker gate は通り、`require_approved_addendum_p_fields()` は呼ばれないため fold できる。
- **成果物影響:** p04 を持つ追補が受理され、公表解析の受理集合と材料レポートの承認値が増える。

### A10 — severity: blocker — 親の「root 不一致は blocker でない」は一般化できない

- **根拠:** 公表 core は root を `88d68f91…` と固定する一方、「primary 系列と同じ commit」とも断言する。[publication-core-v2.md:548](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/output/insights/2026-08-11_t139-pubcore-stage2/publication-core-v2.md:548) [publication-core-v2.md:565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/output/insights/2026-08-11_t139-pubcore-stage2/publication-core-v2.md:565) 実 primary 台帳は `dce4ae4f…` である。[t139-alpha-reservations.jsonl:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/output/registry/t139-alpha-reservations.jsonl:1)
- **落ちる具体入力:** 計画どおり publication を `88d…`、primary を `dce…` と固定して conformance report を作る。tuple disjoint 検査は通るが、承認済み core の「同じ commit」という命題は偽のまま「適合」と報告される。逆に同一 root を強制すると実 primary 台帳と不一致になる。
- **成果物影響:** 材料レポートの root provenance が偽となり、二台帳の分離根拠を proof chain として利用できない。

### A11 — severity: must-fix — resolver が D291 の後続 supersession scope を無視する

- **根拠:** D291 の閉包は明示的な後続 canonical supersession までに限定される。[docs/decisions.md:13442](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/docs/decisions.md:13442) 片側だけの更新時は後続 decision が preserve／失効を明記するとしている。[docs/decisions.md:13496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/docs/decisions.md:13496) 計画の report は固定 `F_p` だけを読み、現在 HEAD の supersession を解決しない。
- **落ちる具体入力:** 後続 D が `source_addendum_b` を新 digest へ更新し旧 digest を失効させた後も、旧 triple を `resolve_d291_role()` に渡す。固定 D291 だけを見るため `approved_by_canonical_decision` を返し続ける。
- **成果物影響:** 材料レポートが失効済み blob を現行承認 role として参照する。

## 裁定パッケージ候補

1. **source gate の層と所有**

   推奨は「Q1(a) は ledger-only の送信前 deny を授権するが、`main_admission` は変更せず、pubcore/P blob の存在を要求しない」と canonical に明記すること。ただし `submit_main` 所有層へ結線されるまで公開 gate APIを land せず、T-793 を「active gate 完了」と閉じない。公表文書自体を要求するなら §10.2 の明示的 supersession をユーザーが裁定する必要がある。

2. **公表 core の false root 文**

   推奨は「literal `88d…` と実 primary `dce…` を正とし、§8.1 の同一 commit 文は conformance 根拠に使わない」という canonical erratum／decision を追加すること。承認済み bytes の直接編集や、primary root を `88d…` へ変更する案は採らない。

3. **予約 operation の所有**

   0-byte ledger の導入だけを本 wave に残し、writer は canonical main・Git common-directory lock・land transaction・初出 commit 再導出を一体化する owner へ送るか、その operation まで scope を明示的に拡張する。現在の worktree-local writer は land しない。

4. **承認 decision の機械 schema**

   marker gate を「全承認に効く」と主張するなら、blob authority を付与する decision は閉じた machine-readable target schema を必須とする裁定が要る。裁定しない場合、guard の保証は `approved_blobs:` 形式だけに限定して記録する。