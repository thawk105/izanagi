# 恒久 bundle 機構の設計プラン

## 1. 調査結果と設計判断

指定された必須資料はすべて読めた。sandbox は read-only のまま使用し、ファイル変更・pytest 実行はしていない。

M1〜M4 は静的検査の範囲では反証できなかった。

- M1 は [`s8b_ratified_freeze.py:1189`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:1189) の `_verify_pairing` が、A の追加 path を approval record と active pointer の2件だけに限定していることで確認できる。G≠A、非 merge、逐語的 `AI-Agent: none` は同ファイルの [`_assert_user_commit`:537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:537)、[`_assert_candidate_commit`:552](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:552) にある。
- M2 は [`env_contract.py:373`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract.py:373) の二つの literal と、それを authority loader に渡す [`env_contract.py:519`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract.py:519) で確認できる。発行ツールも source 編集を要求している（[`issue_env_contract_activation.py:143`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/tools/issue_env_contract_activation.py:143)）。
- M3 は pointer/resolver 実装が [`s8b_ratified_freeze.py:1079`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:1079) と [`s8b_ratified_freeze.py:1214`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:1214) に存在する一方、現 worktree の generation/approval/active record が0件であることをファイル一覧で確認した。
- M4 は `active_bundle` / `bundle_resolver` 相当を `git grep` して production 実装がないことを確認した。これは負の検索結果なので file:line はない。

結論として、同一 commit に全出力を詰め込む方式ではなく、候補を事前に蓄積し、**人間 approval A と人間 activation X を分離した多段 topology**を採るべきである。これは既承認の R5/R13 にも合う（[`freeze-permanent-design.md:402`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/freeze-permanent-design.md:402)、[`freeze-permanent-design.md:424`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/freeze-permanent-design.md:424)）。

## 2. 新設設計文書の中心命題

新設文書では、既存の freeze 内部 bundle と区別して、上位概念を仮に `CalibrationFreezeAuthorityBundle` と呼ぶ。

```text
environment activation candidate ─┐
                                  ├─ joint bundle B ─ approval A ─ active pointer X
ratified freeze authority ────────┤
deferred-ruling profile ──────────┘
```

重要なのは、既存 freeze bundle を破棄することではない。freeze family 内の generation/approval/pointer は下位コンポーネントとして残し、最終的な production authority だけを上位 bundle に移す。

現行の freeze resolver は `HEAD` を自分で取得する（[`s8b_ratified_freeze.py:1214`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:1214)）。実装段階ではこれを次の二層へ分ける計画を書く。

- 内部専用 `_resolve_freeze_generation_at(H, exact_ref)`：与えられた H と bundle が指定した正確な freeze ref だけを検査する。
- 公開 `resolve_active_authority_bundle(root)`：H を一度だけ取得し、環境と freeze の両方を解決する。

既存 `resolve_active_generation()` は g0・履歴検査用の compatibility API に限定し、新 consumer からの利用を禁止する。

## 3. Commit topology の再設計

### 採用案

新文書では次の topology を規範にする。

```text
H_base
  └─ E  環境 activation candidate record
      └─ F  freeze candidate/generation と下位承認
          └─ B  joint bundle record
              └─ Q  自動検査 receipt
                  └─ A  人間による joint approval（1追加だけ）
                      └─ X  人間による active pointer（1追加だけ）
```

E/F/B/Q のどの commit でも現行 X は動かないため、production resolver の結果は変わらない。A も承認済み・未活性の状態であり、X だけが両権限を同時に切り替える。このため中間 commit は「新旧の片側だけが有効」という赤状態にならない。

### 現行検査をどう変えるか

既存 freeze family の `_verify_pairing` は g0互換・下位 freeze 検査として維持する。そこへ環境 record を追加して許容 diff を広げてはならない。

代わりに上位モジュールを新設し、次を独立して検査する。

1. `verify_joint_approval(A, B, Q, H)`

   - A は非 merge。
   - A は逐語的 `AI-Agent: none`。
   - A の親は指定された Q。
   - A の diff は joint approval record 1件の追加だけ。
   - approval が指す `bundle_sha256` は B の canonical digest と一致する。
   - B の環境・freeze の両 ref は、同じ H の祖先に存在する。

2. `verify_joint_activation(X, A, H)`

   - X は非 merge。
   - X は逐語的 `AI-Agent: none`。
   - X の親は選択した A。
   - X の diff は joint active pointer 1件の追加だけ。
   - pointer は A が承認した同一 `bundle_sha256` を指す。
   - pointer chain の gap・fork・rollback・二重 genesis を拒否する。

既存の差分列挙手段は [`_added_paths`:586](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:586) を共通化して再利用できる。ただし joint approval と joint activation は別の allowlist にする。

同一 commit 案を採るなら、環境 candidate record はあらかじめ E に置き、最終 commit の正確な追加集合を `{joint approval, joint pointer}` にする必要がある。しかしこれは既承認 topology の A/X 分離（[`freeze-permanent-design-s2.md:583`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/freeze-permanent-design-s2.md:583)）を崩すため、不採用と明記する。

## 4. M2 literal の record 化と、失う保証

### record 化

[`env_contract_activation.py:332`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract_activation.py:332) は現在、directory 全体を連鎖として検査したあと、末尾を source literal と一致させる。この責務を次の二つへ分離する。

- `validate_activation_catalog(root, H)`  
  すべての activation record の schema、連番、previous hash、遷移を検査する。正しい未活性 suffix の存在は許す。
- `resolve_activation_at(root, H, activation_serial, activation_state_sha256)`  
  上位 bundle が指定した record までの prefix を検査し、正確な state を返す。catalog の末尾を自動選択しない。

上位 bundle は、実在する次の二 field を入力にする。

- `activation_serial`
- `activation_state_sha256`

また、選択した環境と freeze の結合検査には、実在する以下を使う。

- activation state の `active_contracts[].{contract_sha256, env_tag, generation}`
- floor protocol の `contract_sha256`
- freeze generation の `floor_protocol.{path, sha256}`

floor protocol の `contract_sha256` が、同じ `env_tag` に対する選択 activation row と一致しなければ resolver を失敗させる。

### literal を外すことで失うもの

新文書には、次を「回復済み」と装わず、明示的な損失として書く。

- activation ごとに `env_contract.py` の source blob が変わるという review signal を失う。
- 現在は campaign loader closure が `env_contract.py` を含むため、loader binding が間接的に active activation を pin している（[`contract_loader_binding.py:47`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/contract_loader_binding.py:47)）。literal 除去後はこの性質を失う。
- 正しい activation suffix を未承認のまま置くことまで拒否していた現行挙動を失う。新機構では、その suffix は「妥当だが inactive」として許される。
- activation record と source 編集が同じ commit に存在するという結合を失う。
- 長寿命 process の cache が自動で更新される保証は得られない。現行 cache は [`env_contract.py:576`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract.py:576) にあり、再 resolve / restart のどちらを要求するかは副作用境界の裁定待ちである。

代替として得るのは、人間 X、commit ancestry、content digest、bundle ID を campaign lock へ記録することによる data-side pin である。これは source-side pin と同一の保証ではない。

## 5. Bundle 識別子と resolver 契約

### Field の出自

設計文書には field provenance 表を置く。

| Field | 分類 |
|---|---|
| `activation_serial` | 実在入力 |
| `activation_state_sha256` | 実在入力 |
| `active_contracts[].contract_sha256/env_tag/generation` | 実在入力 |
| floor protocol `contract_sha256` | 実在入力 |
| freeze `floor_protocol.path/sha256` | 実在入力 |
| predictions `pre_oracle_head`, `selector_basis_sha256`, `body_sha256` | 実在入力 |
| `bundle_sha256` | **新規出力** |
| joint bundle/approval/pointer の schema・parent・path/hash refs | **新規出力** |
| `ruling_profile_sha256` | **新規出力** |
| consumer observation の `bundle_sha256` | **新規出力** |

次は入力として使わない。

- calibration JSON の raw/artifact SHA
- T126 series ID
- claim ID
- prediction document 内に存在しない whole-file hash

必要なら bytes から新たに hash を計算して **新規出力**として記録できるが、既存 field と主張してはならない。

### Digest

`bundle_sha256` は domain-separated canonical JSON の SHA-256 とし、少なくとも次を覆う。

- parent bundle identity
- `{activation_serial, activation_state_sha256}`
- exact freeze authority `{kind, path, sha256}`
- `ruling_profile_sha256`

`kind/path/sha256` や parent field 自体は新規出力である。g0 では固定 path の現物 hash を、g1 以降では下位 freeze pointer または generation record の exact hash を参照する。

### Resolver 入出力

公開契約は概念的に次とする。

```python
resolve_active_authority_bundle(repo_root) -> ResolvedAuthorityBundle
```

入力:

- repository root のみ。
- resolver 内で HEAD `H` を一度だけ取得する。

出力:

- captured `H`
- `bundle_sha256`
- immutable な environment authority
- immutable な freeze authority
- `ruling_profile_sha256`
- bundle/approval/pointer の exact path と raw hash
- consumer が記録すべき observation tuple

失敗条件:

- pointer/approval/bundle の schema・digest・ancestry 不一致
- environment record prefix の破損
- freeze generation closure の破損
- floor `contract_sha256` と選択 environment row の不一致
- unknown ruling profile
- H 取得後に family resolver が再度 HEAD を取得する実装
- g1 consumer が fixed path や family active pointer を独自に読む実装

family 別 resolve を禁止する理由は二つある。

1. 同じ H でも、独立した environment tip と freeze tip の直積から、承認されていない組合せを生成できる。
2. 二回 HEAD を取得すると、その間に checkout が動き、異なる commit の権限を結合できる。

既承認設計も一回の H と family 個別 resolve 禁止を要求している（[`freeze-permanent-design.md:297`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/freeze-permanent-design.md:297)、[`freeze-permanent-design-s2.md:416`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/freeze-permanent-design-s2.md:416)）。

## 6. Consumer 移行面

### 親 brief の6ファイルの検証

| ファイル | 固定 path / 停止点 |
|---|---|
| [`s8b_floor_campaign.py:138`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_floor_campaign.py:138) | protocol/predictions/freeze の固定 path。preflight・run directory 作成・claim 前に bundle resolve する。 |
| [`s8b_prediction_runner.py:98`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_prediction_runner.py:98) | 固定 protocol/freeze/destination。journal header や provider claim を書く前に停止する。 |
| [`certified_writer_admission.py:207`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/certified_writer_admission.py:207) | live fixed protocol を読む。compute/calibration 開始前に bundle ID と receipt を照合する。 |
| [`s8b_verdict.py:791`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_verdict.py:791) | literal はないが protocol/prediction を独立 CLI 引数で受けられる。`judge_combined` 前に同一 bundle 所属を要求する。 |
| [`s8b_holdout_freeze.py:28`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_holdout_freeze.py:28) | legacy fixed destination。g0 compatibility 専用に隔離し、g1 producer は明示的 versioned destination のみ許す。 |
| [`s8b_selector_freeze.py:52`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_selector_freeze.py:52) | 固定 predictions/freeze path。generation 作成前に bundle-owned refs を検証する。 |

`s8b_verdict.py` は固定文字列 grep では出ないが、独立入力を組み合わせられるため consumer 一覧から外してはならない。

### 親一覧から不足していた直接 consumer

- [`s8b_oracle_driver.py:62`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_oracle_driver.py:62)：固定 protocol default があり、さらに freeze resolve と environment authorization が独立している。marker・artifact 書き込み前に一度だけ joint resolve する。
- [`s8b_ratified_freeze.py:61`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:61)：固定 legacy paths と独立 HEAD resolver を持つ。内部 exact-at-H helper へ分解する。
- [`tools/pegasus/floor_campaign.sh:947`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/tools/pegasus/floor_campaign.sh:947)：固定 protocol から driver を起動する。launch marker より前に source commit と bundle receipt を照合する。
- [`t080_freeze_migration.py:37`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/t080_freeze_migration.py:37)：legacy migration 専用として allowlist 化し、g1 authority resolver からは到達不能にする。

さらに `submit_floor.sh` は固定 path grep には出ないが、qsub 前の receipt に bundle identity がない。[`submit_floor.sh:353`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/tools/pegasus/submit_floor.sh:353) の receipt schema と [`submit_floor.sh:412`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/tools/pegasus/submit_floor.sh:412) の投入境界も移行面に含める。

### 閉包として扱うべき registry

親の6ファイルだけでは不足する。既承認 S2 文書は19 production consumer を列挙している（[`freeze-permanent-design-s2.md:2594`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/freeze-permanent-design-s2.md:2594)）。この19件を基底 registry とし、環境側の以下を追加して閉包を取る。

- `env_contract.py`
- `env_contract_activation.py`
- `ident.py`
- `campaign_lock.py`
- `contract_loader_binding.py`
- certified writer / Pegasus shell の authority receipt 面

とくに campaign lock は現在 environment authority だけを記録する（[`campaign_lock.py:19`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/campaign_lock.py:19)、[`ident.py:465`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/ident.py:465)）。新 schema では `bundle_sha256` と exact freeze ref を新規出力として持たせる。

producer だけ versioned 出力へ変え、上記 consumer が fixed path・current family resolver・独立 CLI 引数を使い続ける案は、先行設計が述べるとおり「実装したふり」であり却下する。

## 7. 先送り3件の構造的隔離

新規出力として content-addressed `RulingProfile` を設ける。ただし本 wave では値を選ばない。

```text
RulingProfile
  seal_policy          = unresolved(S1/S2)
  guarantee_boundary   = unresolved(G-a/G-b/G-c)
  side_effect_boundary = unresolved
```

core bundle は profile の raw hash を束ね、内容が既知の schema/tag であることだけを検査する。各裁定の意味は別 adapter に閉じ込める。

- `SealPolicyAdapter`：predictions/freeze が何を封印するかだけを担当。
- `GuaranteeBoundaryAdapter`：bundle が主張可能な保証範囲だけを担当。
- `SideEffectBoundaryAdapter`：長寿命 process の再 resolve、restart、既発行 job の扱いだけを担当。

core resolver、digest、A/X topology、環境と freeze の同時選択は、いずれの裁定でも不変とする。unknown/unresolved profile の X は拒否するため、暗黙に一方へ倒れない。

## 8. 段階分割と完了判定

| 段 | 内容 | 実装を落とせる完了判定 |
|---|---|---|
| 0 | schema、field provenance、topology の固定 | schema fixture の全 field が「実在入力」または「新規出力」に分類される。台帳外 field を入力にすると静的 schema check が失敗する。 |
| 1 | g0 joint resolver | pointer hash swap、環境 ref swap、freeze ref swap、fork、gap、二重 genesis、extra namespace file の各 mutation が失敗する。正常 g0 は現行 environment/freeze identity と一致する。 |
| 2 | activation catalog 化と literal 除去 | 正しい未参照 suffix を加えても active bundle は不変。参照済み record の削除・改変は失敗。AST 検査で `_ACTIVATION_HEAD_*` が production authority に残っていれば失敗する。 |
| 3 | consumer 全面移行 | 19-file registry と環境/shell registry に対する AST/grep check で、legacy allowlist 外の fixed path、family active resolver、独立 HEAD 取得が1件でもあれば失敗。launch・oracle・verdict・writer・shell の各境界で bundle ID を消す mutation が side effect 前に失敗する。 |
| 4 | E/F/B/Q/A | E/F/B/Q/A の追加だけでは g0 resolver が変化しない。A の extra file、merge、AI trailer、wrong digest、環境/freeze cross-pair がすべて失敗する。 |
| 5 | X activation | X 後は環境と freeze が同時に切り替わる。`new env + old freeze`、`old env + new freeze`、別 HEAD からの resolve、未承認 bundle への pointer がすべて失敗する。 |
| 6 | seal / 保証 / 副作用の policy 実装 | **未定義**。S1/S2、G-a/G-b/G-c、副作用境界の各裁定がないため、期待すべき acceptance/refusal corpus を一意に書けない。共通して「unknown profile の X を拒否」「全 observation に profile/bundle ID を残す」までは判定可能。 |
| 7 | 次世代継承 | synthetic g2 で parent、gap、fork、rollback、両 component の同時遷移を mutation test する。policy の世代間変更可否は当該裁定がなければ **未定義**。 |

「設計文書に条件を書いた」「人間が妥当と判断した」「測定手段は後で決める」は完了判定に含めない。

## 9. 設計文書の置き場

主正本を新設ファイル、例えば `docs/calibration-freeze-authority-bundle-design.md` にする P1 の方向には賛成する。freeze family 内部設計と、上位の環境＋freeze authority を混ぜないためである。

ただし「`docs/freeze-permanent-design.md` を一切改訂しない」はそのままでは危険である。同文書は freeze `ActiveOfficialBundle` を最終 authority とし、単一 resolver を要求している（[`freeze-permanent-design.md:297`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/freeze-permanent-design.md:297)）。上位 bundle 導入後はそれが「下位 freeze component」であることを知らない読者が、古い family resolver を production authority と誤認できる。

したがって次のいずれかが必要である。

- 推奨：既存文書の R1..R16 本文は変えず、上位正本への短い cross-reference と authority precedence だけを追記する。
- 厳密に改訂禁止なら、新設文書で旧文書の適用範囲を明記し、docs checker が両方を必ず結び付ける。ただし旧文書単独では誤読可能という残余リスクを記録する。

## 10. 旧 branch から再導出するもの

`worktree-dev-wave-t657-t660-g2-activation` は merge/cherry-pick せず、次の考え方だけを現設計から再実装する。

- activation record builder と successor transition の test vector  
  新しい candidate catalog の連鎖検査に必要。
- suffix・rollback・record mutation の negative cases  
  「未参照の正しい suffix は非活性」「参照済み prefix の破損は拒否」という新 semantics に合わせて再導出する。
- g0 historical lane と current joint-authority lane を分けた E2E 構成  
  compatibility と新拒否集合を混同しないため。
- calibration verification CLI の「新 candidate のみを検証し、過去 evidence を遡及して認証しない」という scope  
  保証境界を勝手に広げないため。

floor 固定 path の上書き、source literal 更新、pin 追従、旧 topology を前提にした E2E は再導出しない。

## 11. 親 brief への反証・修正要求

- P1：新設ファイル自体は正しいが、「既存 freeze 文書を改訂しない」という絶対条件は不十分。既存文書が最終 authority と呼ぶ resolver の適用範囲が変わるため、最低限の precedence 注記が必要。
- P2：方向は正しいが、A の許容 diff を広げるだけでは不足し、既承認の A/X 分離とも衝突する。候補を事前配置し、A=承認1件、X=pointer 1件とする方が既存 R5/R13 に整合する。
- P3：stage 4 以降を一括して「裁定待ち・未定義」とするのは広すぎる。joint A/X の topology、digest、cross-pair refusal、consumer cutover は現在の実在 field だけで完了判定できる。未定義なのは seal、保証範囲、副作用挙動の policy-specific 部分である。

## 総括

**採るべき骨格：** 環境 candidate と freeze authority を content-addressed 上位 bundle に束ね、人間 A と人間 X を分離する。X だけが一度取得した HEAD 上で両権限を同時に切り替え、全 consumer は同じ typed result を使う。  
**親 brief への反証：** P1 の完全無改訂、P2 の A-diff 拡張、P3 の後段一括未定義はいずれも修正が必要。  
**未確認事項：** 外部 floor の復元・scheduler/process 状態、三つの先送り裁定、将来 policy profile の具体値は未確認・未決定である。