## 総括

**NO-GO。** 段 5 へ進む前に、次の blocker を裁定・修正すべきです。

1. resolver の実 consumer がなく、#1/#2/#3 は未発火。
2. D282 は「approved blob 6＋target core 1」であり、brief の「6 blob」表現は誤り。
3. S15 旧形式と v2 exact-key 契約の互換条件が未定義。
4. D234 の API 署名と `approval_manifest_ref` 追加が不整合。
5. `a13` 台帳は未実装で、manifest の扱いも境界不明。
6. A/B 2 分割と行数見積りは成立しない。
7. 多段 resolver の変異が前段に mask され、単一理由帰属を証明できない。
8. spool fragment の stale `base` が最終 land を止める。
9. pilot / `b03` は外部依存で blocked。ただし land 2 の基礎実装全体まで止める根拠にはならない。

コード変更・テスト実行はしていません。静的読取と digest 確認のみです。

## 詳細

### 1. consumer 不在と D264 非 export

(a) 現在 `orchestrator/preregistration/` は 4 file のみで、`resolve_effective_preregistration`、`PreregBinding`、`submit_pilot`、`submit_main` の実装・callsite はありません。存在する `verify_receipt` は T-080 用の別概念です。[t080_freeze_migration.py:1957](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/campaign/t080_freeze_migration.py:1957>)  
brief 自身も writer、validator、submit、consumer を scope 外にしています。[s1-brief.md:17](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2/s1-brief.md:17>)  
D264 の機械検査は 4 名を package root に export しない契約です。[test_t139_preregistration_binding.py:865](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/tests/test_t139_preregistration_binding.py:865>)

(b) resolver を実装して直接テストするだけでは #1/#2 を満たしません。実際の producer/admission consumer が投入前に resolver を呼び、失敗時に副作用を止め、成功時の同じ binding を writer・submit・validator へ渡す必要があります。D264 の非 export は維持し、必要なら consumer の内部 import にします。resolver module に public 名を置くなら、package root 検査だけでは direct submodule import を防げません。

(c) 現 session の成果物は `foundation-only` と記録すべきです。certified 選択は未生成、材料レポートは「gate 未発火」、試行台帳は pilot submission なしのままです。

### 2. scope 外の実効層

(a) §S7 #4〜#7、受領証 writer、semantic validator、`a13` consumer、PBS/driver/collector、correctness feedback、certified consumer は明示的に後続です。[s1-brief.md:17](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2/s1-brief.md:17>)  
D234 も producer・受領証・validator・consumer・投入 script を別実装境界としています。[decisions.md:11065](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/decisions.md:11065>)  
また plan 自身が snapshot API は consumer 未結線で #3 完了とは記録しないと認めています。[s2-plan.md:137](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2/s2-plan.md:137>)

(b) 次を裁定パッケージ候補として明示すべきです。

- `T139AdmissionProducer` — submit/PBS/driver/collector
- `T139ReceiptWriterSemanticValidator` — §6.10 と §7.1
- `T139A13AppendOnlyConsumer`
- `T139RawSnapshotConsumer`
- `T139CorrectnessFeedbackConsumer`
- `T139CertifiedSelectionConsumer`
- `T139MutationAttributionHarness`
- `T139B03PublicationConsumer`

(c) これらを scope 内と誤記すると、certified・材料 report・試行台帳の全てを「防壁適用済み」と誤って記録することになります。現時点では全て未確定・未発火です。

### 3. D282 の 6 と 7

(a) D282 の `approved_blobs` は 6 件です。[decisions.md:12898](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/decisions.md:12898>) ただし別枠の `target_core` が 1 件あります。[decisions.md:12893](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/decisions.md:12893>)  
従って正しい表現は **target core 1＋approved blob 6＝7 三つ組**です。plan の訂正は正しく、brief の「6 blob」と 7 列挙は不整合です。[s1-brief.md:30](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2/s1-brief.md:30>)

なお D282 の order と composed digest は `S15 → S7`、`e0b0caea…8e0c` です。[decisions.md:12924](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/decisions.md:12924>) 旧 record root は path＋sha256 のみで、commit を捏造してはいけません。[decisions.md:12927](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/decisions.md:12927>)

(b) manifest は `approved_blobs` を 6 role に限定し、`target_core` を別 key にする必要があります。

(c) 7 三つ組を誤ると manifest は D282 と一致せず、certified binding、材料 report、試行台帳の preregistration 参照は全て不成立になります。

### 4. D234 署名の変更

(a) D234 の署名には `approval_manifest_ref` がありません。[decisions.md:11027](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/decisions.md:11027>) 一方 plan は「署名を保つため」としながらこの引数を追加しています。[s2-plan.md:115](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2/s2-plan.md:115>) これは署名維持ではなく API 契約変更です。

(b) 外部署名を D234 のまま保ち、canonical manifest の解決は内部 fixed path/private helper にするか、API 変更を独立裁定へ送る必要があります。T-139 の receipt verifier は R5 に従って `verify_prereg_receipt` とし、既存 T-080 の `verify_receipt` と混同しないことも必要です。

(c) 解決しない限り consumer の callsite 契約が確定せず、certified 選択・材料 report・試行台帳は binding を記録できません。

### 5. S15 旧形式との互換

(a) 承認済み S15 文書の operations は `index`、`locator`、`old_sha256`、`old_text`、`new_text` の旧形式で、`new_sha256` と `expected_composed_sha256` はありません。[erratum-core-s15.md:59](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-addendum-a/erratum-core-s15.md:59>)  
D282 はこの S15 blob を承認済み role としています。[decisions.md:12907](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/decisions.md:12907>)  
一方 v2 S7 は `new_sha256` と最終合成値を持ちます。[erratum-core-s7-stresscheck-v2.md:127](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-11_t139-manifest-land1/erratum-core-s7-stresscheck-v2.md:127>)

全体に optional field を許すと exact-key 閉集合が壊れ、全体で field を必須化すると S15 が parse 不能になります。[s2-plan.md:38](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2/s2-plan.md:38>)

(b) `erratum_id` 別に次の exact grammar を固定すべきです。

- S15: 旧 top-level/operation key 集合、`new_sha256` なし、文書内 composed digest なし
- S7: `{operations, expected_composed_sha256}`、operation 6 key、`new_sha256` 必須
- 最終 `e0b0…` は S15＋S7 の全 operation 適用後に照合

S15 の承認 blob は再発行しません。

(c) 未定義のままでは承認済み S15 を parse できず、`e0b0…` を再現できません。certified 選択は不可、材料 report と試行台帳は preregistration binding なしです。

### 6. `a13` 台帳

(a) 実物の 1 行は key 集合 `{family_root, kind, ordinal, schema_version}` で、142 bytes（LF 除外）の entry digest は `52ba…cf3`、143 bytes 全体の ledger digest は `38968…65`、末尾は LF です。[t139-alpha-reservations.jsonl:1](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/registry/t139-alpha-reservations.jsonl:1>) D282 も `reservation_commit` は pin せず全履歴から再導出するとしています。[decisions.md:12953](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/decisions.md:12953>)

現行 4 module にこの registry path への write/read はありません。従って現在の resolver/manifest が台帳へ書く経路は確認できません。ただし D282 payload には `alpha_reservation` が含まれるのに、plan の manifest exact key 一覧には対応 key がありません。[decisions.md:12941](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/decisions.md:12941>) [s2-plan.md:96](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2/s2-plan.md:96>)

(b) 今 session は registry を変更せず、`alpha_reservation` を扱うなら「台帳証明ではない literal descriptor」と明記する必要があります。全履歴検査は別の `T139A13AppendOnlyConsumer` に送るべきです。

(c) 現 session の binding は `a13 unchecked` のままです。current row を読むだけで proof 済みとすると、試行台帳が編集・再作成された行を受理し、certified 選択と材料 report が誤った reservation root を指します。

### 7. PATH / TOCTOU

(a) 現行 Git wrapper は ambient `PATH` を環境 allowlist に含め、実行も `"git"` です。[blobref.py:21](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/blobref.py:21>) [blobref.py:162](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/blobref.py:162>)  
従って brief の P2「絶対 path と digest 記録だけで足りる」は成立しません。digest は偽 Git の出力を正当化する実行防壁ではありません。[s2-plan.md:201](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2/s2-plan.md:201>)

また P3 の leaf fd 再利用だけでは親 directory swap、regular 検査、bounded read、read 前後 metadata の契約が不足します。[s2-plan.md:202](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2/s2-plan.md:202>

(b) resolver 内の全 Git call が trusted executable context を共有し、raw pointer は component-wise `O_NOFOLLOW` walk と同一 bytes buffer の hash/parse を行い、実 consumer へ結線される必要があります。

(c) 未達なら偽 Git に祖先検査を通され、未承認 core が certified identity になります。未結線の helper だけなら、材料 report・試行台帳の値は変わらず、#3 は未達のままです。

### 8. 行数・分割・実行可能性

(a) A/B の 2 並列という brief は、plan 自身の再分割と矛盾します。[s1-brief.md:75](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2/s1-brief.md:75>) B1 は概算 655〜795 行、B2 は 603〜753 行で、双方の上限 750 を超えます。[s2-plan.md:145](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2/s2-plan.md:145>)  
B2 は A/B0/B1 完了後でなければ着手できません。[s2-plan.md:148](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2/s2-plan.md:148>)

実質は A/B0/B1 の 3 lane 並列 → B2 の 1 lane 直列です。B3 を独立実行できる場合だけ初期 frontier は 4 lane ですが、5 lane 完全並列ではありません。

(b) P1 と 2-unit 分割は撤回し、A/B0/B1 → B2 の dependency graph を brief に反映する必要があります。B3 は semantic validator と同じ session に残すなら別の裁定・予算に分離すべきです。1 session に収まるという主張は、行数だけでは証明できません。

(c) 現時点の certified/report/trial の値は変わりませんが、実装完了を `closed` と記録できません。状態は `plan invalid / replan required` です。

### 9. 変異の単一理由帰属

(a) resolver の順序が payload → ancestry → blob → composition なので、例えば次が mask されます。

- manifest の composed digest 改変は payload exact mismatch が先に落とす
- erratum の `new_sha256` 改変は blob digest または parse が先に落とす
- caller の commit 改変は caller/payload 比較または blob 解決が ancestry より先に落とす
- fake Git の不正応答は PATH 検査ではなく top-level 検査で落ちうる
- raw snapshot、`a13`、`b03` は consumer 不在で一度も発火しない

(b) 各 mutation について、先行層を固定した独立 fixture が要ります。特に「blob は存在するが ancestry だけ不成立」「ancestry は成立するが tree/blob だけ不成立」「全 blob 検査後に composition digest だけ不成立」を別々に構成し、matrix に `first_rejecting_node` を記録しなければなりません。現 plan の「直接 kill」はこの条件をまだ定義していません。[s2-plan.md:176](</work/1/SFC/tanab/dev-wave-t139-manifest-land2/s2-plan.md:176>)

(c) 帰属未証明の mutation matrix を `KILLED` として扱うと、材料 report の proof chain と試行台帳の mutation result が誤ります。正しい状態は `partial/unproven` で、certified 選択はまだ出せません。

### 10. spool の land blocker

(a) fragment の `base` は stale です。[2026-08-10-dev-wave-t139-manifest-w1-1.md:89](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/spool/worklog/2026-08-10-dev-wave-t139-manifest-w1-1.md:89>) `spool_fold.py` は現本文との不一致を fail-closed で拒否します。[spool_fold.py:1453](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/tools/spool_fold.py:1453>)

(b) 今 session で先に直すと、後続 session の carry・worklog 変更で再び stale になります。現 session はこの finding を記録するだけにし、最終 session が carry 解決後の本文から `base` を再計算し、land 直前に dry-run で確認すべきです。既存 stale fragment の上に新しい transition を積むだけでは悪化します。[docs/spool/README.md:78](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/spool/README.md:78>)

(c) 修正されるまで land 状態は `invalid`、canonical worklog/decisions は未確定です。certified 選択・材料 report・試行台帳の値を変更する問題ではありませんが、最終成果物を land できないため blocker です。

## 外部依存 N1/N2 の判定

N1 は **pilot に関しては正しい**です。`docs/worklog.md` は段階 2 の再提出後まで本走投入不可と記録しています。[worklog.md:629](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/worklog.md:629>) [worklog.md:635](</work/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/worklog.md:635>)  
さらに unlanded `worktree-dev-wave-t139-pubcore-stage2` の package は、3 文書を承認候補/草案とし、pilot は依然不可としています。したがって pilot の試行台帳は空、certified 選択・材料 report は未生成のままです。

ただし N1 を「land 2 の manifest/resolver 基礎実装も全て blocked」と読むのは過大です。今 session は foundation を進められますが、最終 gate/pilot を完了とは記録できません。

N2 も **required な新 source については正しい**です。main にある旧 `addendum-b.md` の `b03` は予約規則を含む旧版です。[addendum-b.md:148](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-09_t139-addendum-b/addendum-b.md:148>) C-2b 後の新 core §8.2 / `p03` は unlanded branch 側にしかなく、main の旧 `b03` を代用してはいけません。

なお brief が根拠に挙げる「handoff w3」は現 worktree の `docs/handoff/` には存在しません。N1 の根拠は既存 worklog と unlanded branch の package/README に差し替えるべきです。