## 結論

現行装置を 1 byte も変えずに qsub しない判断は維持できます。ただし結論は「D905 を理由に裁定を不採用」ではなく、**「承認済み裁定と現行成果物の certification 意味論が衝突する新事実を添え、ユーザー再裁定待ちへ戻す」**でなければなりません。

親 brief の成果物影響には明確な誤りがあります。`formal=false` の本走は成功しても論文 §8 A-1 を正式には動かさないため、「投入停止によって A-1 が 0 件のまま」という差分は成立しません。

## 所見

### 1. 親は裁定を実質的不採用にしていないか

- **real:** 「投入しない」を最終決定として wave を閉じるなら、DW-S04 違反です。DW-S04 は、承認済み裁定を親判断で不採用にせず、新事実付きで再裁定へ戻すよう要求しています。[core.md:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/docs/dev-wave/core.md:98)
- **real:** gate 到達自体は前回 worklog に既に記録済みであり、これだけを「裁定時の未見事実」として再利用できません。[worklog-phase3-0826-971.md:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/docs/archive/worklog-phase3-0826-971.md:5)
- **real:** 再裁定へ返せる新事実は二つあります。

  1. 批准履歴 walker が merge-neutral な同一 blob で壊れ、現行 HEAD の受理集合が空であること。
  2. A-1 は論文上 `formal=false` でも、WAL 上は `certified=True` と contract-bound COMMIT を作り、汎用 consumer から certified artifact として読めること。

したがって親の正しい終端は「投入拒否」ではなく、「現行装置のままの投入は保留し、非 certification 経路を新設するか D905 解消を待つかを再裁定へ返す」です。

### 2. `formal=false` なら批准 gate は適用外か

- **refuted — 反証試行:** `formal=false` と `declared_use_class="exploration"` から gate 適用外を導こうとしましたが、現行成果物の意味論では成立しませんでした。
- A-1 は確かに `formal=False` と昇格禁止を identity に固定しています。[paper_story_a1_paired.py:692](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/paper_story_a1_paired.py:692)
- しかし各 arm の受理には verifier の `certified=True` を要求します。[paper_story_a1_paired.py:1772](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/paper_story_a1_paired.py:1772)
- pipeline は certification 成功時だけ COMMIT し、environment-contract hash を必ず記録します。[pipeline.py:1466](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/pipeline.py:1466) [pipeline.py:1534](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/pipeline.py:1534)
- D259 は certification 判定を lane 名ではなく、「成果物が certified 実行を主張するか」で決めています。[decisions.md:11922](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/docs/decisions.md:11922)
- `declared_use_class` は権威ではなく layout selector にすぎません。[decisions.md:21833](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/docs/decisions.md:21833) [loop.py:216](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/loop.py:216)

したがって、現在は「論文上の formal」と「campaign/verifier certification」が別軸です。親の「formal=false でも現行 gate に到達する」という実装読解は正しい一方、「D905 があらゆる探索測定を禁じる」という一般化は誤りです。

### 3. gate の適用範囲を直す判定基準

- **real — 段 2 plan の欠落:** `require_environment_contract=False` だけでなく、environment contract と live source binding を保ったまま、ratification authority だけを持たない**明示的な非 certification artifact 型**を作る経路が列挙されていません。
- ただし単に批准呼出しだけを飛ばして既存 v2 lock を作る案は安全ではありません。汎用 admission は v2 authority map を E1 と導出し、批准台帳を再照合せず `CertifiedCampaignView` を発行できます。[artifact_admission.py:784](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/artifact_admission.py:784) [artifact_admission.py:1141](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/artifact_admission.py:1141)

恣意的でない判定基準は次です。

1. caller の `exploration` ラベルではなく、lock・WAL・consumer が主張する authority を見る。
2. certified consumer の既存受理集合が 1 件も広がらないことを示す。
3. 非 certification が成果物の exact schema に刻まれ、汎用 certified consumer が必ず拒否すること。
4. 後から field の除去・付替えで昇格できず、D510 決定 7 の昇格禁止を機械的に保つこと。[decisions.md:21257](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/docs/decisions.md:21257)
5. environment contract、live HEAD binding、通常 verifier 実走など、批准と独立な防壁を維持すること。

この条件を満たすなら「gate を緩める」のではなく「非 certification 型を certified gate の定義域外へ分離する」変更です。ただし装置変更になるため、**実装せず裁定パッケージ候補**です。

### 4. 批准検査が実際に守っているもの

- **real:** 現行 HEAD の受理集合は空です。履歴 walker は各 path-history commit を別 ledger version と数え、同一 blob にも真の長さ増加を要求します。[enforcement_source_ratification.py:265](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/enforcement_source_ratification.py:265)

静的実測:

```text
git log ... | git cat-file --batch-check=...
=> 17 件すべて blob 42885e36...、112 bytes

capture + require_ratified_closure
=> digest 6d497998...
=> EnforcementSourceRatificationError:
   ratification history is not a strict prefix extension
```

- **real:** よって「受理された closure は台帳にある」という肯定的保証は現行 HEAD では恒真です。merge-neutral 履歴の正例がテストに無いことも確認しました。
- **refuted:** ただし「恒真だから何も守っていない」は成立しません。実際には lock 作成前に発火し、未批准の certified artifact を一件も発行しないという fail-closed 性質を守っています。[ident.py:443](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/campaign/ident.py:443)
- **real:** availability を意図せず全損させている walker は独立した実装欠陥です。merge-neutral commit を version と数えず、異なる blob 間だけ append-only 性を検査する修正は、**実装せず裁定パッケージ候補**です。修正しても現行 digest と台帳行は不一致なので、A-1 は単独では開きません。

受理・拒否の含意は次の二文です。

- **受理:** exact closure map の digest が、検証済みの committed append-only ledger 集合に含まれることまでを意味し、人間が追記したこと自体の証明ではありません。[decisions.md:21740](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/docs/decisions.md:21740)
- **拒否:** 新しい certified v2 lock を発行できないことを意味するだけで、verifier の誤り、測定値の不正、非 certification 実験の禁止までは意味しません。

通る正例は、linear な一回の ledger commit に exact closure digest を記録し、同じ map で新 lock を作る fixture です。[test_t671_source_binding.py:472](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/orchestrator/tests/test_t671_source_binding.py:472) 今回は pytest を実走していないため、これは静的に確認した正例であり緑とは記録しません。

### 5. D905 の射程

- **refuted:** D905 は A-1 投入一般を禁止していません。禁止しているのは批准の執行と、成りすませない主体が無い状態で批准を進めることです。[decisions.md:32931](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/docs/decisions.md:32931)
- **real:** 現行 A-1 は certified v2 artifact を作るため、成功させるには批准済み digest、偽造 v2、または gate 迂回のいずれかが必要です。前者は D905 により現在実行不能、後二者は D905 の理由である自己批准禁止を壊します。
- **real:** 明示的な非 certification artifact 型で、certified consumer が受理不能なら、批准を進めずに探索投入する設計は D905 の文言・理由の双方と両立し得ます。ただし現行 v2 をそのまま使う方式は両立しません。

### 6. 成果物影響の非対称性

- **real:** 親 brief の「投入しないと論文 §8 A-1 が 0 件のまま」という損失表現は誇張です。凍結文書と前回 worklog は、`formal=false` の本走が成功しても §8 A-1 を正式には動かさないと明記しています。[README.md:131](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/output/insights/2026-08-26_paper-story-a1-sized-preregistration/README.md:131) [worklog-phase3-0826-971.md:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit/docs/archive/worklog-phase3-0826-971.md:46)
- **real:** 止めた場合に実際に失うのは、610 rep の探索データ、3 workload の記述的分類、実分散、`rep_notes`、内部再測定発生率、正式系列の設計を更新する経験的材料です。
- **refuted:** 失うものに「論文で +38.5% を現在の契約として主張できる資格」や「正式 A-1 一件」を含めてはいけません。
- **real:** 逆に単純迂回で得るものは探索値だけですが、unratified v2 が汎用 certified consumer へ流れる経路を開きます。この危険は探索値の便益より質的に大きく、現行装置での迂回を止める根拠になります。

## 段 2 plan の経路別監査

| 経路 | 判定 | 所見 |
|---|---|---|
| 正規 qsub / fresh layout | **refuted** | 「実は通る」という反証は失敗。批准へ必ず到達し、現 HEAD では失敗する |
| 既存 sized-v1 v2 lock | **refuted** | 実在しないため resume 経路は使えない |
| forged v2 lock | **refuted** | 技術的成立の分類は正しいが、不批准 map を E1 として流せるため却下も正しい |
| `require_environment_contract=False` + v1 対応 | **refuted** | environment authority 全体を落とし、contract-bound COMMIT の post-policy downgrade になるため却下は正しい |
| 批准だけを既存 v2 から外す | **refuted** | 汎用 admission が批准の有無を識別できず CertifiedCampaignView を発行し得る |
| 明示的な非 certification artifact 型 | **real** | plan の全数列挙から欠落。安全条件を満たせば成立候補だが、装置変更なので実装せず裁定パッケージ候補 |
| `pipeline.evaluate` / calibrator / ccbench 直呼び | **refuted** | 数値は作れても凍結 A-1 の canonical evidence bundle にならない |
| `materialize` のみ | **refuted** | producer ではなく、正当な raw bundle が無ければ成立しない |
| 旧 commit / hybrid rollback | **refuted** | sized-v1 事前登録が無い、または後続 correctness 改善を巻き戻す |
| ledger 追記、人間転記、平文承認 | **refuted** | D758・D905 が明示却下 |
| walker 修正 | **real** | infrastructure defect の修正として必要だが、digest 不一致を解消せず単独では投入不能。実装せず裁定パッケージ候補 |

Web 検索は使用していません。read-only の静的検査と Git/Python probe のみで、pytest は実行せず緑も主張しません。

## 総括

親の「現行装置のまま今すぐ投入しない」は正しいですが、「D905 により裁定を最終却下」は誤りです。正しい裁定パッケージは、現行 A-1 が論文上は exploratory でも campaign 上は certified artifact を作るという新事実を示し、`(a)` D905 解消を待つ、または `(b)` certified consumer へ絶対に昇格できない非 certification artifact 型を別 wave で設計する、の再裁定を求めるものです。