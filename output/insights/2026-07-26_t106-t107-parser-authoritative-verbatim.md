# [T-106][T-107] wave — codex 子の逐語凍結

- `authority: none` / `default_effect: no-state-change`
- 段 3 敵対相談 2 本、段 6 敵対レビュー 2 本、焦点再レビュー 1 本、実装・fix 報告の逐語。
- 材料の解釈と親裁定は `2026-07-26_t106-t107-parser-authoritative.md` が正本。

> **erratum (D88 / DW-S07): リテラル placeholder を可逆 defang した。**
> defang 前の原文 sha256 = `a732f8ce63b3e4c2e9b0e9d21d7ef78617d18b8d8a57b6c5f24af20739e076b2`。
> 逐語中に現れた検出語は `LP-n【defanged】` の形へ置換してある。
> 置換は 1 対 1 なので、`LP-n【defanged】` を D88 の対応する検出語へ戻せば原文を復元できる。

## plan

```markdown
## 1. 境界テスト

### 追加先と関数名

新規ファイルは作らず、[`orchestrator/tests/test_s8b_ratified_verify.py:1318`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_ratified_verify.py:1318) の selector exemption 群へ、[`test_selector_exact_exemption_accepts_declared_three_axis_evidence`:1331](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_ratified_verify.py:1331) の直後に追加する。

- `test_ratified_accepts_parser_rejected_raw_while_prediction_verify_rejects`
- `_verify_prediction_freeze_consumer_routes`
- `test_verify_prediction_freeze_consumer_routes_are_exact`

import は [`test_s8b_ratified_verify.py:10`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_ratified_verify.py:10) に `ast`、[`test_s8b_ratified_verify.py:33`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_ratified_verify.py:33) の近傍に `s8b_selector_output as SO` を追加する。

### 既存テストとの重複

- parser が LP raw を `rationale_placeholder` で拒否すること自体は [`test_s8b_selector_output.py:121`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_output.py:121) で既に固定済み。新規 parser 単体テストは不要。
- `verify_prediction_freeze` が偽装 valid row を再 parse して拒否することは [`test_s8b_selector_freeze.py:598`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_freeze.py:598) で固定済み。ただし非 JSON raw の別 fixture であり、ratified が受理した「同じ入力」との境界ではない。
- 構造検査が parser を呼ばないことは [`test_s8b_selector_freeze.py:527`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_selector_freeze.py:527)、ratified の通常 happy path は [`test_s8b_ratified_verify.py:1331`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_ratified_verify.py:1331) にあるが、現行 parser が実際に拒否する raw は与えていない。
- floor 経路の動的 spy は [`test_s8b_floor_campaign.py:3282`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_floor_campaign.py:3282)、[`test_s8b_floor_campaign.py:3385`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_floor_campaign.py:3385) で既にある。4 経路の閉集合と ratified 非包含は未固定。

したがって既存テストの期待値は変更せず、上記2テストを追加する。

### fixture と exact な変異

`tmp_path` と [`_build_launch_repo`:571](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_ratified_verify.py:571) を使うが、`mutate=` は使わない。

```python
root, _freeze, _topology = _build_launch_repo(
    tmp_path, selector_valid_cell=True,
)
```

`selector_valid_cell=True` により、実 parser を通った agent raw・prediction・journal・envelope が作られる経路は [`test_s8b_ratified_freeze.py:547`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_ratified_freeze.py:547) から [`test_s8b_ratified_freeze.py:617`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_ratified_freeze.py:617)。

構築後、既存の `rr20/on` セルを次のように一貫して変異する。対象 raw path の既存前例は [`test_s8b_ratified_verify.py:1336`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_ratified_verify.py:1336)。

1. `raw_rr20_on.txt` を、元 row の `choice_id` と `rationale="LP-1【defanged】"` を持つ exact JSON raw に置換する。
2. `selector_predictions.json` の同じ row は `status="valid"`、`parser_error_code=None` のまま、`rationale` と `raw_sha256` を新 raw に合わせる。
3. [`_rehash_selector_prediction`:1323](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_ratified_verify.py:1323) で `body_sha256` を再計算する。
4. selector `journal.jsonl` の対応する `invocation` も `rationale` と `raw_sha256` を合わせる。
5. `envelope_rr20_on.json` の `result` も同じ raw 文字列にし、対応する `envelope` record の `envelope_sha256` を更新する。これにより parser 分類以外の不整合を残さない。
6. [`B._fixed_commit_all`:224](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_ratified_freeze.py:224) で selector 4 artifact を新 H に commit する。
7. `M.load_ratified_freeze(root)` で新 H に束縛し直し、[`M.launch_validate`:2752](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_ratified_freeze.py:2752) を呼ぶ。

`mutate=` を使わない理由は、callback に渡る `state` が floor の protocol/cert/manifest/journal/result だけだからである（[`test_s8b_ratified_freeze.py:782`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_ratified_freeze.py:782)）。selector evidence はそれ以前に base commit へ導入される（[`test_s8b_ratified_freeze.py:467`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_ratified_freeze.py:467)）。引用された前例も実際には `mutate=` でなく、build 後の worktree 変異である（[`test_s8b_ratified_verify.py:725`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_ratified_verify.py:725)）。

### assert 単位で固定する不変条件

- `assert parser_error.value.code == "rationale_placeholder"` — 変異 raw が現行 [`parse_selector_output`:88](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_selector_output.py:88) の受理集合外である。
- `assert ratified.activation_head == mutated_head` — stale な変異前 A でなく、新 H を検証対象にしている。
- `assert isinstance(M.launch_validate(ratified, root), M.LaunchValidatedFreeze)` — ratified がその raw を含む evidence を受理する。
- `with pytest.raises(SF.SelectorFreezeError, match=r"invalid:rationale_placeholder"):` — 同じ prediction と同じ raw を [`verify_prediction_freeze`:879](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_selector_freeze.py:879) が再 parse して拒否する。
- `assert routes == {("s8b_floor_campaign", "_floor_preflight_freeze_allowlist"), ("s8b_prediction_runner", "seal"), ("s8b_verdict", "verify_prediction"), ("s8b_selector_freeze", "main")}` — parser 感応経路を4経路 exact で固定する。
- `assert "s8b_ratified_freeze" in scanned_modules` — ratified を検査対象から漏らしていない。
- `assert all(module != "s8b_ratified_freeze" for module, _ in routes)` — ratified が `verify_prediction_freeze` consumer でない。

### 4経路の検査方式

現在の実 call site は floor [`s8b_floor_campaign.py:1365`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_floor_campaign.py:1365)、prediction runner [`s8b_prediction_runner.py:1480`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_prediction_runner.py:1480)、verdict [`s8b_verdict.py:211`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_verdict.py:211)、CLI [`s8b_selector_freeze.py:1033`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_selector_freeze.py:1033) の4件である。

推奨は `Path(SF.__file__).parent.glob("*.py")` を `ast.parse` し、`Import` / `ImportFrom` の alias を `s8b_selector_freeze.verify_prediction_freeze` へ解決したうえで、`ast.Call` を enclosing function に帰属させる方式。

| 方式 | 脆さ | 保守コスト |
|---|---|---|
| grep 件数 | import の二重分岐・docstring・コメントを数え、行移動にも弱い | 低いが偽陽性が多い |
| alias-aware AST | 空白・コメント・行番号に不感。新規/削除 consumer を閉集合差分として検出 | 中。正当な consumer 追加時に expected set と D90 を更新 |
| runtime monkeypatch | 実行到達は証明できるが、直接 import 済み binding を4モジュール別々に patch する必要があり、未知の第5 consumer の不在は証明できない | 高い。floor/seal fixture も重い |

AST を主検査とし、既存 floor spy と新しい ratified 境界テストを動的な補完にするのが最も頑健。

## 2. docs 記録

### D89 に既にあること

[`docs/decisions.md:3885`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/decisions.md:3885) から [`docs/decisions.md:3936`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/decisions.md:3936) には既に以下がある。

- LP 拒否の実装位置・error code・既存 error 優先順位（:3893）。
- parser-local 語彙と parser bytes pin の理由（:3899）。
- docs/parser/独立期待値の三者照合と AST 形状検査（:3904）。
- 承認外類似語を受理し続ける過剰拒否防止（:3912）。
- schema/role no-touch の事実と `parser-authoritative` という結論（:3917）。
- floor は現行 parser に感応し、ratified は再 parse しないという事実、および ratified 単独保証の限界（:3922）。
- 当時の状態は「現状維持を推奨し、裁定へ送る」で止まっている（:3928）。

これらの再説明、LP 語彙、過去の検証プロセス、件数は D90 に再掲しない。

### D90 で新たに書くこと

追加位置は [`docs/decisions.md:3936`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/decisions.md:3936) の直後。

見出し案:

```markdown
## D90. [T-106][T-107] selector parser-authoritative 契約 — ratified 非再 parse と parser 感応 4 経路を確定 (2026-07-26)
```

節構成案:

1. **決定（状態遷移）**  
   D89 (5)(6) の推奨を、2026-07-26 のユーザー裁定 (a)/(a) として確定したことだけを書く。

2. **規範的 authority**  
   raw 受理集合の正本、受理集合変更時に必要な parser・テスト・D の同時更新規則を書く。

3. **no-touch と別裁定境界**  
   schema/role/既存 freeze bytes を追随変更しないこと、versioned migration を本裁定から導出しないことを書く。

4. **parser 感応経路の閉集合と ratified 例外**  
   floor、prediction runner、verdict、selector-freeze verify CLI の4経路を関数名で完全列挙し、ratified は非包含とする。D90 本文には腐る行番号を入れない（[`CLAUDE.md:153`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/CLAUDE.md:153)）。

5. **機械固定と非変更確認**  
   追加した2テスト名を挙げ、本 wave は production 0 byte・受理集合不変であると記録する。

### parser-authoritative の規範文案

以下を規範文としてそのまま使える。

> selector raw の受理集合の唯一の規範的正本は、`orchestrator/campaign/s8b_selector_output.py::parse_selector_output` とする。schema、role、および prediction 文書に記録された `status`・`choice_id`・`rationale`・`parser_error_code` を、raw 受理可否の独立な正本として扱ってはならない。

> 受理集合を拡大または縮小する変更者は、`parse_selector_output` とその正例・負例・境界テストを同一 commit で変更し、変更前後の受理差、error code の優先順位、および全 parser 感応経路への影響を新たな D で裁定しなければならない。

> parser の受理集合変更だけを理由に、`.claude/agents/selector-8b.md`、`s8b_selector_catalog.json`、`s8b_selector_output_schema.json`、既存 prediction、または既存 freeze の bytes を追随変更してはならない。これらの変更または versioned migration は本契約から導出されず、別件のユーザー裁定を要する。

> parser 感応経路は、floor launch preflight、prediction runner の seal reload、verdict の prediction 検証、および selector-freeze verify CLI の4経路とし、いずれも `verify_prediction_freeze` を経由して現行 parser に感応しなければならない。

> 新しい production consumer を追加する場合は `verify_prediction_freeze` を経由させ、consumer 閉集合テストと本決定の後継 D を同じ変更で更新しなければならない。

> `s8b_ratified_freeze` の ratified 経路には、`verify_prediction_freeze`、`parse_selector_output`、または同等の raw 再 parse を追加してはならない。ratified は `pre_oracle_head` の blob、封印文書の構造・hash、および journal との一致を検証範囲とする。

> ratified と parser 感応経路の受理差は意図した契約である。境界テストは、現行 parser が拒否する raw を ratified が受理し、同じ raw を `verify_prediction_freeze` が拒否する非対称を維持しなければならない。

### 他 docs の追記要否

- `docs/glossary.md`: **要らない。** glossary は理解補助で、規範の正典ではない（[`glossary.md:3`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/glossary.md:3)）。現状 `parser-authoritative` は D89 だけにあり、D90 内で定義できるため、規範を複製すると drift を作る。
- `docs/phase3.md`: **要らない。** 現行 checkpoint と完了状態の戦術正本であり（[`phase3.md:19`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/phase3.md:19)）、T-106/T-107 に対応する checklist 項目もない。状態記録は brief 指定の worklog に置く。
- `docs/README.md`: **要らない。** 文書の地図であり（[`README.md:1`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/README.md:1)）、`decisions.md` は既に登録済み（[`README.md:16`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/README.md:16)）。新しい文書種別を増やさない。
- `docs/freeze-permanent-design.md`: **要らない。** T-080 の裁定確定済み設計正本（[`freeze-permanent-design.md:3`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/freeze-permanent-design.md:3)）であり、本 wave は freeze schema・transition・consumer pointer を変えない。

## (P1)〜(P6)

- **(P1) 支持。** D90 の delta だけで足り、phase3/glossary/README/freeze 恒久設計への重複追記は各文書の役割に反する。
- **(P2) 否定。** harness 自体は使えるが `mutate=` の state は floor artifact 限定（[`test_s8b_ratified_freeze.py:782`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_ratified_freeze.py:782)）で、引用前例も post-build 変異（[`test_s8b_ratified_verify.py:725`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_ratified_verify.py:725)）である。
- **(P3) 支持。** 必要な挙動は既に [`verify_prediction_freeze`:879](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_selector_freeze.py:879) と ratified 構造検査 [`s8b_ratified_freeze.py:2537`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_ratified_freeze.py:2537) に存在し、テスト/docs の追加だけで固定できる。
- **(P4) 支持。** ratified 非再 parse と4経路の現行 parser 感応を両方書かなければ、D89 が漏らした runner/verdict/CLI の射程が残る。
- **(P5) 支持。** DW-G03 は独立2例なしの「族全体への制度一般化」を禁じる規則（[`core.md:47`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/dev-wave/core.md:47)）であり、本案は既存1境界の固定で制度や version を新設しない。
- **(P6) 支持。** parser bytes は journal の `parser_module_sha256` に pin され（[`test_s8b_ratified_freeze.py:535`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_ratified_freeze.py:535)）、production docstring も byte 変更になる。

## 実装子への指示書

- 実装子所有: `orchestrator/tests/test_s8b_ratified_verify.py`
  - `ast` と `s8b_selector_output as SO` を import。
  - `test_ratified_accepts_parser_rejected_raw_while_prediction_verify_rejects` を追加。
  - `_verify_prediction_freeze_consumer_routes` を追加。
  - `test_verify_prediction_freeze_consumer_routes_are_exact` を追加。
  - 既存 helper・既存テストの期待値は変更しない。
- 親所有: `docs/decisions.md`
  - EOF の D89 後へ D90 を1本追加。
  - D89 の事実・LP 語彙・過去の検証件数は再掲しない。
- 編集しない: production 全ファイル、schema、role、`output/s8b-freeze/**`、`docs/glossary.md`、`docs/phase3.md`、`docs/README.md`、`docs/freeze-permanent-design.md`。

pytest は実走していない。静的 AST 調査では、現在の `verify_prediction_freeze` 呼出経路は上記4件 exact で、ratified は含まれなかった。```

## lens-a

```markdown
[A-1]  
(a) 主張: 「parser 感応経路は4経路 exact」は現時点で偽である。4件は `verify_prediction_freeze` の消費者だけで、生成時の `drive_journal → record_agent_attempt → parse_selector_output` を落としている。  
(b) 根拠: [plan.md:52](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t106-t107/plan.md:52)、[plan.md:123](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t106-t107/plan.md:123)、[s8b_selector_freeze.py:380](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_selector_freeze.py:380)、[s8b_prediction_runner.py:884](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_prediction_runner.py:884)。  
(c) 放置時: parser 変更が生成 journal/prediction の `status`・`choice_id`・`rationale`・`parser_error_code` を変え、最終選択・verdict を変えても、4経路 assert と D90 の影響台帳は変化を検出しない。

[A-2]  
(a) 主張: 境界 fixture は「raw の受理集合差」ではなく、parser 拒否 raw を `status="valid"` と偽装した分類不整合を検査している。`verify_prediction_freeze` は同じ parser 拒否 rawでも、`status="invalid"` と error code が一致すれば受理する。  
(b) 根拠: [plan.md:36](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t106-t107/plan.md:36)、[plan.md:37](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t106-t107/plan.md:37)、[s8b_selector_freeze.py:194](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_selector_freeze.py:194)、[s8b_selector_freeze.py:196](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_selector_freeze.py:196)、[s8b_selector_freeze.py:202](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_selector_freeze.py:202)。  
(c) 放置時: 将来、正当に `invalid` と記録された prediction の受理を拡大・縮小しても本テストは通り、choice 欠落・indeterminate・certified verdict の値が変わる。

[A-3]  
(a) 主張: `routes == {...}` は恒真化できる presence test であり、実行到達・同一 document/root の検証・例外伝播・第5 consumer の不在を証明しない。第5 consumer が verifier を呼ばなければ、そもそも AST の検出対象に現れない。  
(b) 根拠: scanner は `campaign/*.py` 内の対象 `ast.Call` だけを数える設計である [plan.md:60](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t106-t107/plan.md:60)。現行 floor の意味的保証は call の存在でなく例外を拒否へ変換する処理にある [s8b_floor_campaign.py:1365](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_floor_campaign.py:1365)、[s8b_floor_campaign.py:1368](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_floor_campaign.py:1368)。  
(c) 放置時: 実 call を `if False` に移す、例外を握り潰す、dummy document を渡す、または別 directory に無検証 consumer を追加しても assert は通り、parser 拒否 evidence から floor certificate・seal・verdict を生成できる。

[A-4]  
(a) 主張: ratified 非再 parse の一般契約を、`rr20/on`・`rationale_placeholder` 1例だけで制度化しており、(P5) はプラン自身の「全将来 consumer・全受理集合変更を拘束する規範」と矛盾する。  
(b) 根拠: fixture は1セルに固定 [plan.md:34](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t106-t107/plan.md:34)、契約は全 ratified 経路を禁止 [plan.md:127](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t106-t107/plan.md:127)、一方 DW-G03 は制度一般化に異なる producer/consumer の独立2例を要求する [core.md:47](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/dev-wave/core.md:47)。  
(c) 放置時: ratified が別 arm・別 error code の raw だけを拒否しても当該境界は通り続け、ratified の prediction/evidence 受理集合だけが縮小する。

[A-5]  
(a) 主張: 「唯一の正本=`parse_selector_output`」という文言には、関数本体を変えず helper・定数だけで受理集合を変える抜け道がある。変更規則も「`parse_selector_output` を変更」と書いており、悪意ある実装者は同時更新義務を回避できる。  
(b) 根拠: 規範案 [plan.md:117](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t106-t107/plan.md:117)、変更義務 [plan.md:119](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t106-t107/plan.md:119) に対し、実受理集合は choice・長さ・LP 定数 [s8b_selector_output.py:11](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_selector_output.py:11) と JSON helper [s8b_selector_output.py:57](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_selector_output.py:57) に依存する。  
(c) 放置時: `ALLOWED_CHOICE_IDS`、最大長、placeholder 集合、decode helper のみを変えて raw の受理集合と生成 row を変更しながら、必須の境界テスト・影響評価・後継 D を省略できる。

[A-6]  
(a) 主張: role/output-schema の赤理由は `_verify_file_record` から再現できるが、親実測 (P-C) の「ratified は parser blob sha を照合するだけ」は誤りである。ratified は `s8b_selector_freeze` を importし、その import が現在 checkout の parser module を実行する。  
(b) 根拠: 過大な結論は [measurements.md:17](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t106-t107/measurements.md:17)。間接 import は [s8b_ratified_freeze.py:2461](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_ratified_freeze.py:2461) → [s8b_selector_freeze.py:34](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_selector_freeze.py:34) であり、blob hash 照合 [s8b_ratified_freeze.py:2599](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_ratified_freeze.py:2599) だけではない。  
(c) 放置時: parser の syntax error・top-level raise・import failureで raw 再 parse を一度もせず全 ratified launch が拒否または異常終了し、文書化した ratified 受理集合が実装と食い違う。

[A-7]  
(a) 主張: (P3) の「production 0 byte」を成果物非変更の根拠にはできない。必須の新規 insight file は repository 列挙に入り、内容も holdout scan 対象だが、プランに scan-neutrality 検査がない。  
(b) 根拠: 新規 insight は brief の必須成果物 [brief.md:43](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t106-t107/brief.md:43)。列挙は tracked/untracked 通常ファイルを含む [s8b_holdout_freeze.py:197](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_holdout_freeze.py:197)、その path 集合は digest preimage に入る [s8b_floor_campaign.py:1623](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_floor_campaign.py:1623)、digest は certificate field になる [s8b_floor_campaign.py:1651](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_floor_campaign.py:1651)。  
(c) 放置時: 次の official run の `source_commit`・`clean_scan_digest`・certificate hash と下流 journal 参照は必ず変わり、insight に三軸 conjunction が混入すれば clean scan が拒否して certificate・floor report・台帳が生成されない。

[A-8]  
(a) 主張: 「selector 4 artifact を exact に変異」は assert されない。使用予定の `_fixed_commit_all` は `git add -A` で全差分を取り込み、対象4 path以外の混入を検出しない。  
(b) 根拠: 選定は [plan.md:41](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t106-t107/plan.md:41)、helper は全 add [test_s8b_ratified_freeze.py:224](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_ratified_freeze.py:224)。同ファイルには path 集合を前後で exact 検査する `_commit_exact` が既にある [test_s8b_ratified_freeze.py:231](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_ratified_freeze.py:231)。  
(c) 放置時: temp H に parser・role・schema その他の意図しない bytes まで混入しても `activation_head` assert は通り、ratified の受理結果と H 参照を「4 artifact のみの差」に帰属できなくなる。

NO-GO```

## lens-b

```markdown
[B-1]  
(a) 「delta は4点だけ」は水増しである。D90 案のうち、parser-authoritative、schema/role no-touch、parser bytes pin、floor の現行 parser 感応、ratified 非再 parse、両者の受理差と ratified 単独保証の限界は、すべて D89 に既記載である。許可済みの実質 delta は「D89 の推奨を裁定済みにする」「D89 未記載の consumer を補う」「同一入力の境界テスト」に絞るべきである。  
(b) `docs/decisions.md:3899-3902,3917-3928`、`/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t106-t107/plan.md:98-129`。なお状態遷移自体も `docs/worklog.md:778-820` に既記録である。  
(c) 重複した D89/D90 の一方だけが将来更新されると、raw の受理正本・ratified 例外・既存 freeze の参照先が二義化し、同じ evidence の受理判断が参照する D により変わる。

[B-2]  
(a) production の `verify_prediction_freeze` 直接 call site は4件 exact だが、それは parser 感応経路の完全集合ではない。`parse_selector_output` の直接 caller は `_reparse_agent_raw` と `record_agent_attempt` の2件で、後者は4経路とは別の生成層である。  
(b) verify callers = `orchestrator/campaign/s8b_floor_campaign.py:1365`、`s8b_prediction_runner.py:1480`、`s8b_verdict.py:211`、`s8b_selector_freeze.py:1033`。parse callers = `s8b_selector_freeze.py:194,380`、生成側接続 = `s8b_prediction_runner.py:884-898`。  
(c) 生成側を落とすと、parser 変更が試行台帳と prediction の `status/choice_id/rationale/parser_error_code/raw_sha256` をどう変えるかが契約外になり、最終選択・判定不能・proof-chain 参照が変わっても「4経路固定」テストは検出しない。

[B-3]  
(a) floor 経路は現時点の supported production では発火しない。public wrapper は official を無条件拒否し、pilot は selector preflight を通らないため、call site は internal core/test 用の dormant 経路である。他の runner/verdict/verify CLI は各 `main` から到達する。  
(b) `orchestrator/campaign/s8b_floor_campaign.py:193-203,2639-2679,2688-2696,2856-2867`、`docs/phase3.md:101-103`。到達する3経路は `s8b_prediction_runner.py:1507-1519`、`s8b_verdict.py:836-856`、`s8b_selector_freeze.py:1025-1042`。  
(c) dormant floor を「現行4 consumer」の一員として確定すると、AST テストは通る一方、実際には floor の certified run・結果・全 attempt 台帳を1件も保護しない。D90 には少なくとも「fresh official の dormant preflight」と書く必要がある。

[B-4] (nit)  
(a) 親 measurements の「ratified は parser blob sha だけ照合」は過度な省略である。ratified は raw semantic parse をしないだけで、prediction の strict parse・body/schema/row 構造・source blob・journal 対応・raw/envelope hash を検査する。  
(b) `/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t106-t107/measurements.md:17-18`、`orchestrator/campaign/s8b_ratified_freeze.py:2523-2625,2631-2700`、`s8b_selector_freeze.py:706-827`。  
(c) nit — plan の規範案 `plan.md:127` は構造・hash・journal を列挙しており、この文言を維持する限り成果物の受理集合への残存影響はない。brief/measurements の表現だけ訂正すべきである。

[B-5]  
(a) exact AST 閉集合テストは脆い上に実効性が低い。無害な helper 抽出・関数改名・正当 consumer 追加で偽赤になり、逆に `if False`、早期 return 後、代入 alias、`getattr`、新しい直接 parser caller は見逃せる。固定するのは到達意味論ではなく構文形状である。  
(b) `/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t106-t107/plan.md:52-68`。既に floor の動的到達確認は `orchestrator/tests/test_s8b_floor_campaign.py:3327-3388` にある一方、public official は `s8b_floor_campaign.py:193-203` で停止する。  
(c) 無関係な refactor を受入集合から排除しながら、実際に verifier が発火しない退行を受理できる。global exact set は非 gating inventory に落とし、`record_agent_attempt`、verdict/CLI、ratified 境界を public behavior で固定する方が頑健である。

[B-6]  
(a) 提案境界テストが守るのは ratified/verify の受理差であり、certified 選択・材料レポート・試行台帳の値ではない。`LaunchValidatedFreeze` は prediction を返さず、combined verdict は rationale を値に使わず choice と `prediction_body_sha256` を使う。plan はこの実効射程を成果物へ写像していない。  
(b) `/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t106-t107/plan.md:46-54`、`orchestrator/campaign/s8b_ratified_freeze.py:3131-3139`、`s8b_verdict.py:253-285,602-608,621-748`。  
(c) テストが通っても、combined verdict の `status/holdouts`、材料 renderer、試行台帳 consumer が verifier を迂回する退行は残る。現テストは「受理集合テスト」と限定し、成果物保証が必要なら verdict CLI が出力を作らない E2E、または ratified→oracle の意味保証を別裁定パッケージ候補にすべきである。

[B-7]  
(a) D90 案は裁定射程を超過する。「全受理集合変更で新 D 必須」「新 consumer は必ず `verify_prediction_freeze` 経由」「consumer 閉集合を恒久更新」「catalog・prediction・freeze bytes の追随変更禁止」は、T-106/T-107 の2裁定にはない新しい統治機構であり、既存 `record_agent_attempt` の直接 parser 経路とも不整合である。P3/P5 は成立しない。  
(b) `/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t106-t107/plan.md:119-127,140-145`、裁定原文 `docs/worklog.md:778-780`、族一般化 gate `docs/dev-wave/core.md:47-50`。  
(c) 将来の正当な consumer・parser 修正・version migration が未裁定の手続義務で拒否され、コード変更の受理集合と proof-chain 更新方式が変わる。これらは削除するか、独立2例を備えた別裁定パッケージへ送るべきである。

[B-8]  
(a) P1 の「新 D 1本で足りる」は routing 上の誤りである。長期判断を decisions に置くこと自体は正しいが、plan の親向け指示は worklog 更新を落としており、現行 worklog は T-106/T-107 を依然「実施待ち」としている。phase3/glossary/failures はこの不足の代替にならない。  
(b) `docs/skill-self-improvement.md:22-33`、`docs/README.md:16-23,36`、`docs/worklog.md:818-820`、brief `brief.md:39-44`、plan `plan.md:147-159`、`docs/dev-wave/core.md:78-86`。  
(c) D90 とテストを入れても可変状態の正本では両タスクが未完のまま残り、次 wave の選択対象・handoff・受入済み変更集合が食い違う。

[B-9]  
(a) insight 成果物は未設計かつ既存記録と重複する。T098 の材料・逐語・変異台帳は既に T-106/T-107 の択、全 production 波及、ratified 限界を保持しているのに、brief は新しい単一 Markdown に「材料＋逐語＋台帳」を要求し、plan はそれ自体を実装指示から落としている。  
(b) `docs/decisions.md:3889-3890`、`output/insights/2026-07-26_t098-selector-lp-reject.md:110-126`、同 `-verbatim.md:182-230`、`output/README.md:49-70`、`docs/skill-self-improvement.md:32-33`。  
(c) そのままでは逐語・変異台帳が欠落するか、既存 insight と新 insight が同じ事実の競合参照になる。新 insight を作るなら `authority: none` の delta-only snapshot とし、既存材料へのポインタ、逐語、JSON 台帳を明確に分離すべきである。

[B-10]  
(a) 親 P2 と plan が衝突している。brief は `_build_launch_repo(..., mutate=...)` を前提にするが、callback の `state` は floor protocol/cert/manifest/journal/result だけで、selector evidence は build 前に導入済みである。plan の post-build 変異が正しく、brief は誤りである。  
(b) brief `brief.md:49-50`、plan `plan.md:24-44`、`orchestrator/tests/test_s8b_ratified_verify.py:571-588`、`orchestrator/tests/test_s8b_ratified_freeze.py:462-471,782-794`。  
(c) brief を追った実装子は対象 raw/prediction/selector journal/envelope を変異できず、意図した受理差を撃たないテスト、または gate 到達前に落ちる偽テストを作る。

[B-11] (nit)  
(a) P6 は parser bytes pin の効果を過大化している。現行 verifier の `sources` は parser を含まず、floor/ratified は封印時の `pre_oracle_head` blob hash を使うため、docstring 変更が既存 freeze を直ちに壊すわけではない。ただし新規 seal/resume の parser binding は変わる。  
(b) `orchestrator/campaign/s8b_selector_freeze.py:63-65,879-902`、`s8b_floor_campaign.py:1387-1402`、`s8b_ratified_freeze.py:2580-2620`、`s8b_prediction_runner.py:1427-1455`。  
(c) nit — 本 wave の production 0-byte 方針を維持する限り成果物値は変わらない。ただし「pin と衝突するから不可能」ではなく「不要な新規 seal identity 変更を避ける」と理由を訂正すべきである。

NO-GO```

## impl

```markdown
## 変更したファイルと追加した関数

- [orchestrator/tests/test_s8b_ratified_verify.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_ratified_verify.py:1353)
  - `test_selector_parser_classification_boundary_at_ratified_launch`
  - plan-v2 §3-1 の assert 1〜5を実装。
  - `_commit_exact` で prediction／journal／raw／envelope の4 pathだけを導入。
  - production・docs・既存 helper／期待値は変更なし。commit／git add も未実行。

A 後の既存 selector evidence を変更すると ratified の名前空間履歴検査が先に `history-mutated` で拒否するため、evidence 構築直後・初回導入前に変異して exact commit する topology としました。最終 H は変異 commit の子孫です。

## 走らせた nodeid と結果

- 追加テスト:
  - `python3 -m pytest -q orchestrator/tests/test_s8b_ratified_verify.py::test_selector_parser_classification_boundary_at_ratified_launch`
  - **1 passed in 1.48s**
- 対象ファイル全体:
  - `python3 -m pytest -q orchestrator/tests/test_s8b_ratified_verify.py`
  - **160 passed in 66.78s**
- 補助検査:
  - `python3 tools/check_codex_agents.py` — OK
  - `python3 tools/check_docs.py` — 違反なし
  - `python3 -m py_compile ...` — 成功
  - `git diff --check` — 成功
- 最終差分は指定テストファイル1件のみ。

途中、単独の `pytest` コマンドは Python 3.9 側を使用して `dataclass(kw_only=True)` の収集エラーになりました。以降は所定の Python 3.10 を使う `python3 -m pytest` で実走しています。

## 波及可能性

所有外で静的に確認した関連面:

- 共有 fixture:
  - `test_s8b_ratified_freeze.py` の `_install_emitter_selector_prediction`
  - `_commit_exact`
  - `_fixed_git`
  - JSON/JSONL helper
  - monkeypatch は追加テスト内だけで、終了時に復元されます。
- `verify_prediction_freeze` の production consumer:
  - floor official preflight
  - prediction runner の seal reload
  - verdict prediction 検証
  - selector-freeze verify CLI
- 関連 consumer test:
  - `test_s8b_selector_freeze.py`
  - `test_s8b_prediction_runner.py`
  - floor／verdict 系テスト
  - これらの個別 suite は今回の全走範囲外です。
- ratified は raw 分類の非 consumer のままです。parser module の import可能性と、prediction／journal／evidenceの構造・hash整合には引き続き感応します。

## S1〜S5 の確認結果

変異は未実走、コードによる静的確認です。

- **S1:** ratified の selector 検証より前に同じ raw を parser 意味論で拒否する検査はありません。呼出し追加時は `launch_validate` の受理 assertだけが赤になります。
- **S2:** `_reparse_agent_raw` 前の構造・commit pin・source hash・正規化は同じ入力を受理済みです。呼出し削除時は負例の `pytest.raises` だけが赤になります。既存 `test_verify_reparses_raw_and_rejects_forged_valid_agent_rows` も KILL するため非帰属 control です。
- **S3:** 主負例だけでは error-code 不一致も残るため、同じ raw/hashで error codeを一致させた局所行を直接検査しました。status比較より前の検査は全通過し、status比較削除時はこの `pytest.raises` だけが赤になります。
- **S4:** 正直な `invalid` 文書は構造・hash・source検査を全通過します。parse失敗を無条件拒否へ変えると正例の `is None` assertだけが赤になります。
- **S5:** `_commit_exact` 実行時には対象外の未追跡 selector artifact が存在します。`_fixed_commit_all` へ戻すとそれらが混入し、明示した4 pathの `diff-tree` exact集合assertだけが赤になります。```

## rev-a

```markdown
[RA-1]  
(a) S3 は production 経路では等価変異であり、private helper 直呼びで偽の KILL を作っている。逆に実効的な `parser_error_code` 照合を削除する変異は全 assert を SURVIVE する。  
(b) `valid` 行は前段で `parser_error_code=None` を強制されるため、status 照合を削除しても error-code 不一致で拒否され続ける (`orchestrator/campaign/s8b_selector_freeze.py:637`, `:641`, `:885`, `:902`)。追加テストは公開経路で成立しない `valid`＋正しい error code を作り、直接 `_reparse_agent_raw` を呼んでいる (`orchestrator/tests/test_s8b_ratified_verify.py:1484`, `:1488`, `:1489`)。  
(c) `orchestrator/campaign/s8b_selector_freeze.py:196` の error-code 比較だけを削除すると、raw の実際の拒否理由と異なる任意の非空 `parser_error_code` を持つ `invalid` prediction が floor・runner・verdict・CLI の受理集合へ入る。変異台帳の「S3 KILL」は水増しになる。

[RA-2]  
(a) S5 は exact-path assert では KILL されない。`_fixed_commit_all` への置換は後続の空 commit で先に落ち、目的の assert は未到達になる。  
(b) 境界 commit の直後に base commit が連続する (`orchestrator/tests/test_s8b_ratified_freeze.py:467`, `:471`)。`_fixed_commit_all` は `git add -A` 後、空 commit を許さず commit する (`:224`, `:227`)。全 artifact を先に取り込むと base commit が失敗し、追加された path assert (`orchestrator/tests/test_s8b_ratified_verify.py:1454`) まで到達しない。  
(c) 変異台帳には「exact path assert が KILL」と誤記される一方、実際には boundary commit が全 selector artifact を混入させた後、G/A を生成できず停止する。proof-chain の導入 commit・path 参照を守った実証になっていない。

[RA-3]  
(a) 唯一指示書の post-build 変異を実装せず、selector evidence の初回導入前に変異する別 topology へ差し替えている。  
(b) 指示は `_build_launch_repo` 完了後の変異を要求する (`plan-v2.md:49`)。実装は monkeypatch を先に設定し (`orchestrator/tests/test_s8b_ratified_verify.py:1421`)、installer 内で変異 commit を作ってから (`:1414`)、`_build_launch_repo` を呼ぶ (`:1447`)。実際の post-build 書換えは namespace 履歴検査で `history-mutated` になる (`orchestrator/campaign/s8b_ratified_freeze.py:1072`, `:1074`, `:481`)。  
(c) 実際の post-build evidence は `load_ratified_freeze` の受理集合外となり、certified 選択・レポート・試行台帳は生成されない。現テストが固定するのは「最初から偽装された evidence」の別受理集合であり、assert 5 の参照 H は指示された状態ではない。

[RA-4]  
(a) `assert kwargs.get(...) is None` と `merge-base ... == ""` は、この fixture では常に真になる非 load-bearing assert。成果物影響はないため nit。  
(b) 前者は `selector_payload_hit=False` から必ず `None` が渡る (`orchestrator/tests/test_s8b_ratified_verify.py:1440`; `orchestrator/tests/test_s8b_ratified_freeze.py:774`)。後者は `_fixed_git` が非 ancestor を `check=True` で先に例外化し、成功時の stdout は常に空 (`orchestrator/tests/test_s8b_ratified_verify.py:1463`; `orchestrator/tests/test_s8b_ratified_freeze.py:207`)。  
(c) certified 選択・レポート・台帳の値または受理集合は変わらない。nit。

NO-GO```

## rev-b

```markdown
[RB-1]
(a) must-fix — 親裁定の post-build 変異を、build 中の初回導入へ無断ですり替え、floor の selector verify まで迂回している。  
(b) 根拠: `plan-v2.md:47-52` に対し、`orchestrator/tests/test_s8b_ratified_verify.py:1364-1449` は installer と `_run_campaign_core` を monkeypatch。実際の順序は `test_s8b_ratified_freeze.py:466-471,897-900` の `seed→boundary→base→…→A(=H)`。`impl.md:5,9` も逸脱を認めつつ assert 1〜5 準拠と主張する。  
(c) 放置時、`…→A→boundary(=H)` という裁定対象の受理集合は未検査となり、post-build H だけを誤拒否する実装や通常 floor preflight での回帰が生存する。

[RB-2]
(a) must-fix — 追加テストは `tmp_path` 外へ実ファイルを書き、清掃しない。  
(b) 根拠: `test_s8b_ratified_verify.py:1447-1449` が provider 経路を起動し、`s8b_prediction_runner.py:1070-1086,1138` が OS temp 配下へ `s8b-selector-*`、`empty-mcp-config.json`、`cwd-*` を生成する。`test_s8b_prediction_runner.py:567-574` はそれが明示的に `tmp_path` 外であることを確認している。  
(c) 放置時、反復・並列実行ごとに共有 temp namespace へ未回収 bytes が増え、`TMPDIR` の設定次第では別 worktree 等のテスト所有外 path を汚染する。

[RB-3]
(a) must-fix — fixture の prediction、journal、commit topology が実時刻と実行 Python に依存し、決定的でない。  
(b) 根拠: `s8b_prediction_runner.py:205-206,860,1145-1156,1221-1229` が現在時刻を記録し、同 `:1045-1050` が `sys.executable` の実 path/bytes hash を採取する。これらを `test_s8b_ratified_verify.py:1410-1419` が commit する。  
(c) 放置時、prediction の `agent_provenance`／`body_sha256`、journal bytes、boundary commit、後続 A／`activation_head` の参照値が実行時刻・環境ごとに変わる。

[RB-4]
(a) must-fix — selector evidence 導入 commit の `AI-Agent` trailer が規約外である。  
(b) 根拠: `test_s8b_ratified_verify.py:1414-1419` は `agent="fixture"` を渡し、`test_s8b_ratified_freeze.py:251-254` により `AI-Agent: fixture` となる。一方 `docs/ai-provenance.md:14-45` の許可形は構造化形式または単独の `AI-Agent: none` のみ。  
(c) 放置時、`launch_validate` の受理 assert が非準拠 provenance を持つ H の受理まで固定し、将来の正当な provenance 検査強化を parser 境界とは無関係に赤へする。

NO-GO```

## fix1

```markdown
## F1/F2/F3 の対応

- F1: **closed**
  - private `_reparse_agent_raw` 呼び出しを削除。
  - `invalid`＋誤った非空 error code `invalid_json` を公開 `verify_prediction_freeze` が拒否する負例を追加しました。[対象箇所](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_ratified_verify.py:1484)
  - `valid` 偽装の公開経路での拒否と、正しい `rationale_placeholder` を記録した `invalid` 正例も維持。
- F2: **closed**
  - A 直後に raw evidence を書き換えて commit し、`load_ratified_freeze` が実際の reason `history-mutated` で拒否する assert を追加しました。[対象箇所](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_ratified_verify.py:1538)
  - 変異 commit の親が A であることも固定しています。
- F3: **closed**
  - 恒真だった `_floor_preflight_fn is None` を削除。
  - `merge-base --is-ancestor` は戻り値比較をやめ、`check=True` の無例外完了が検査であることを明示しました。[対象箇所](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_ratified_verify.py:1462)

編集は指定された 1 ファイルのみです。docs・production・schema・fixture helper は変更せず、commit も行っていません。`git diff --check` も成功しています。

## 走らせた nodeid と結果

- `python3 -m pytest -q orchestrator/tests/test_s8b_ratified_verify.py::test_selector_parser_classification_boundary_at_ratified_launch`
  - **1 passed**
- `python3 -m pytest -q orchestrator/tests/test_s8b_ratified_verify.py`
  - **160 passed**
- `python3 tools/check_codex_agents.py`
  - **OK**
- `python3 tools/check_docs.py`
  - **違反なし**

赤の内訳:

- 最初の裸の `pytest -q ...::test_selector_parser_classification_boundary_at_ratified_launch` は収集時エラー。
- `pytest` の shebang が Python 3.9 環境を参照し、`dataclass(kw_only=True)` を解釈できませんでした。テスト本体には未到達です。
- リポジトリで利用可能な Python 3.10 の `python3 -m pytest` に切り替え、上記の単独・全体結果を確認しました。

## 波及可能性

- production の公開 consumer は selector CLI、floor campaign、prediction runner の seal reload、verdict。production コード未変更のため実行時の受理集合は変わりません。
- 直接 consumer test は主に `test_s8b_selector_freeze.py` と `test_s8b_prediction_runner.py`。新テストは error-code 比較契約を追加固定するだけで、既存期待値には触れていません。
- 共有 fixture の `_install_emitter_selector_prediction` と `_run_campaign_core` は当該テスト中だけ monkeypatch され、pytest 終了時に復元されます。`_commit_exact` を含む共有 helper 自体は未変更です。
- post-A 変異は `tmp_path` 内の使い捨て repo に限定されています。

## F1 検出力の根拠

公開経路では `invalid` 行の `parser_error_code` は非空なら構造検証を通過し、その後 `verify_prediction_freeze` から `_reparse_agent_raw` に到達します。

追加負例は以下の組み合わせです。

- 記録: `status="invalid"`、`parser_error_code="invalid_json"`
- raw の実際の拒否理由: `rationale_placeholder`

現行の比較は `status != "invalid" or parser_error_code != exc.code` なので拒否します。error-code 比較だけを削除すると条件は `status != "invalid"` だけとなり偽、正常 return します。後続の期待値と body hash は再計算済みなので別検査では落ちず、`pytest.raises` が失敗します。したがって指定変異は **KILL** されます。

## RA-2 の確認結果

RA-2 は**妥当**です。

fixture の順序は `seed commit → selector installer → base commit`。境界の `_commit_exact` を `_fixed_commit_all` に置換すると、`git add -A` により残る selector artifact も境界 commit に取り込まれます。その直後の base commit は空となり、`check=True` の `git commit` が例外化します。

したがって後段の exact-path assert には到達せず、S5 を「exact-path assert が KILL」と帰属するのは不正確です。実際の赤は手前の空 commit です。```

## refocus

```markdown
| fix 前所見 | 判定 | 根拠 |
|---|---|---|
| RA-1 | closed | 誤 code の `invalid` 行を公開 `verify_prediction_freeze` へ渡している (`orchestrator/tests/test_s8b_ratified_verify.py:1484`, `:1506`)。構造検査は非空 code を許容し (`orchestrator/campaign/s8b_selector_freeze.py:643`)、目的の比較 (`:196`) まで到達する。 |
| RA-2 | partial | 誤帰属自体は報告で認めたが、親プランの「exact-path assert が KILL」は未訂正 (`plan-v2.md:92`)。`_fixed_commit_all` は全 staging (`orchestrator/tests/test_s8b_ratified_freeze.py:224`) 後、base commit (`:471`) を空 commit で落とすため、後段 assert (`orchestrator/tests/test_s8b_ratified_verify.py:1453`) は未到達。 |
| RA-3 | closed | A を親とする post-A commit を固定し (`orchestrator/tests/test_s8b_ratified_verify.py:1539`, `:1546`)、`history-mutated` 拒否を検査した (`:1547`)。 |
| RA-4 | closed | `_floor_preflight_fn is None` は削除済み (`orchestrator/tests/test_s8b_ratified_verify.py:1439`)。ancestor 検査は戻り値 assert を除き、`check=True` の呼出しとして維持 (`:1462`, `orchestrator/tests/test_s8b_ratified_freeze.py:204`)。検出力の退行なし。 |
| RB-1 | closed | 初回導入 topology は親が是認し、未検査だった post-A 受理集合を拒否例で補完した (`orchestrator/tests/test_s8b_ratified_verify.py:1538`)。 |
| RB-2 | 対象外（親が refuted 裁定） | 親の「直すな」裁定は `prompt-fix.txt:58-60`。既存 builder 経路は変更されていない (`orchestrator/tests/test_s8b_ratified_verify.py:1446`)。 |
| RB-3 | 対象外（親が nit 裁定） | `prompt-fix.txt:63`。揮発値への新規 assert・固定化は加えられていない。 |
| RB-4 | 対象外（親が refuted 裁定） | `prompt-fix.txt:61-62`。`agent="fixture"` はそのままで、勝手な修正なし (`orchestrator/tests/test_s8b_ratified_verify.py:1418`, `:1544`)。 |

新規所見なし。RA-2 の未閉鎖を重複して RF 採番しない。

F1 の変異検出力は成立する。`invalid_json` は parser の実在 code (`orchestrator/campaign/s8b_selector_output.py:60`, `:79`) で、実際の raw は先行 assert により `rationale_placeholder` (`orchestrator/tests/test_s8b_ratified_verify.py:1450`)。invalid 行の構造・正規化検査は通過し、`_reparse_agent_raw` の exact code 比較へ到達する (`orchestrator/campaign/s8b_selector_freeze.py:885`, `:894`, `:902`)。`:196` の code 比較だけを削除すると例外が消え、`pytest.raises` (`orchestrator/tests/test_s8b_ratified_verify.py:1506`) が失敗する。他検査による先落ちはない。

F2 も実際に `history-mutated` へ到達する。commit 済みなので namespace-dirty は発火せず、loader は namespace 全 path の履歴を走査する (`orchestrator/campaign/s8b_ratified_freeze.py:1205`, `:1210`, `:1072`)。raw の旧 OID と post-A OID の差で `history-mutated` が送出される (`:479`, `:483`)。

追加 assert に新たな恒真 assert・偽 KILLは見つからない。残る偽帰属は既知の RA-2。`git status` と staged/unstaged 両差分では変更は `orchestrator/tests/test_s8b_ratified_verify.py` のみで、所有違反なし。本再レビューでは pytest を実走しておらず、fix 報告の緑は再主張しない。

NO-GO```

