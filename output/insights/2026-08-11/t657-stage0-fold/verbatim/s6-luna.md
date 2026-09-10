# 段 6 レビュー B — NO-GO

## 所見

### LB-B-01 / 下位 conformance の中核前提が偽

- **主張:** 上位失効 schema は下位 §S2-1.10 と exact conformance ではない。特に下位の共通規則は UTC を `YYYY-MM-DDTHH:MM:SSZ` と定義するのに、上位と実装 pin は `revoked_at` を exact int にしている。さらに `revoked_by` の trim・長さ制限と `reason` の非空制限も下位からは導出できない。
- **file:line 根拠:** 下位 UTC 定義 [freeze-permanent-design-s2.md:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/freeze-permanent-design-s2.md:26)、下位 7 fields [freeze-permanent-design-s2.md:432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/freeze-permanent-design-s2.md:432)、上位制約 [calibration-freeze-authority-bundle-design.md:460](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:460)、実装 pin [calibration_freeze_authority_contract.py:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:132)、誤った段 4 推論 [s4-ruling.md:28](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-stage0-fold/s4-ruling.md:28)。一次裁定自身も int を明記している [rulings-session-5rulings.md:718](/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-04-rulings-session-5rulings.md:718)。
- **具体的な失敗シナリオ:** 下位正本どおりの `"revoked_at":"2026-08-11T16:00:00Z"` を上位へ写すと、上位 pin は integer でないため拒否する。逆に上位 int を下位へ置けば、下位正本の UTC 規則に違反する。「hash 名 1 件だけの写像」では両立しない。
- **深刻度:** blocker
- **成果物影響:** canonical record bytes・raw hash・失効受理集合が上下層で分裂し、下位 conformance を根拠にした proof chain が成立しない。
- **これはユーザー裁定が要るか:** **yes** — T-795 は int を明示的に選んでいるため、AI が文字列へ変更できない。新事実を添えて R1 を再裁定するか、「意図的な上位差分」として conformance 主張を撤回する必要がある。

### LB-B-02 / 下位実装の非適合を topology 1 件に過少計上している

- **主張:** 現行 `s8b_ratified_freeze.py` と凍結済み下位正本の差は A/X の同一 commit 要求だけではない。approval は下位正本 exact 8 fields 対現行 4 keys、pointer は 7 対5、revocation は7対4、cancellation は6対4で、対象も `bundle_digest` ではなく `generation_sha256` になっている。この差を `FREEZE-AX-TOPOLOGY` だけでは表現できない。
- **file:line 根拠:** 下位 approval [freeze-permanent-design-s2.md:308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/freeze-permanent-design-s2.md:308)、pointer [freeze-permanent-design-s2.md:377](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/freeze-permanent-design-s2.md:377)、revocation/cancellation [freeze-permanent-design-s2.md:432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/freeze-permanent-design-s2.md:432)。現行 key 集合 [s8b_ratified_freeze.py:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/campaign/s8b_ratified_freeze.py:113)、parser [s8b_ratified_freeze.py:1104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/campaign/s8b_ratified_freeze.py:1104)。設計が記録する差は topology のみ [calibration-freeze-authority-bundle-design.md:728](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:728)。
- **具体的な失敗シナリオ:** `_verify_pairing` の同一 commit 要求だけを直して `FREEZE-AX-TOPOLOGY` を resolved にすると、required gate は下位適合済みの体裁になるが、現行 parser は凍結正本どおりの approval・pointer・revocation bytes を依然拒否する。
- **深刻度:** must-fix
- **成果物影響:** 上位 A が参照する「下位 family 検証器が承認済みと判定した束」の受理集合が、凍結正本ではなく旧 parser schema に支配される。
- **これはユーザー裁定が要るか:** **no** — 下位凍結正本が既に exact authority である。required gate の射程を全非適合へ広げるか、schema 非適合を別 gate として登録すべきである。

### LB-B-03 / 「残るユーザー裁定 0 件」と cancellation 未確定は自己矛盾

- **主張:** これは正しい区別ではない。文書は cancellation の置き場・粒度が未確定で、裁定前に親が選ぶなと明記しながら、無限定に「残るユーザー裁定は 0 件」と書いている。さらに段 0 条件は「§12 の全問」に裁定が付くことを要求する。
- **file:line 根拠:** cancellation 未確定 [calibration-freeze-authority-bundle-design.md:492](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:492)、段 0 の全問条件 [calibration-freeze-authority-bundle-design.md:707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:707)、0 件宣言と未確定再掲 [calibration-freeze-authority-bundle-design.md:846](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:846)。下位 cancellation exact 正本 [freeze-permanent-design-s2.md:460](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/freeze-permanent-design-s2.md:460)。
- **具体的な失敗シナリオ:** 上位 pointer fork の回復実装時、実装者は cancellation を独自設計すれば越権し、設計しなければ正当な fork-loser 回復の受理集合を定義できない。一方、裁定帳簿は追加裁定なしと指示する。
- **深刻度:** blocker
- **成果物影響:** 上位 pointer の回復可能状態と cancellation 後の active 束参照が未定義のまま、裁定閉包だけが完了扱いになる。
- **これはユーザー裁定が要るか:** **yes** — 上位 cancellation を不要として明示禁止するか、先送り項目として owner/gate を付けるか、下位同型 schema を採るかは受理集合を変える択一である。

### LB-B-04 / docs の「4 件」と実装の `blocking_gates=4` は同じ 4 件ではない

- **主張:** §12.3 の 4 項目には S/B が含まれる。一方、実装の `blocking_gates=4` は S/B を含まず、policy gate・fixture assignment・他者手番2件である。S/B は別の `applicable_unresolved=2`、fixture 実体はさらに `pending=5` として数える。
- **file:line 根拠:** 三つの完了軸 [calibration-freeze-authority-bundle-design.md:740](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:740)、docs の「4件」 [calibration-freeze-authority-bundle-design.md:854](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:854)、実装の計数 [calibration_freeze_authority_contract.py:1086](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:1086)、exact 4 gate のテスト [test_calibration_freeze_authority_contract.py:266](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_calibration_freeze_authority_contract.py:266)。
- **具体的な失敗シナリオ:** docs の「4件」を解消対象として S/B・policy・他者手番を処理しても fixture assignment が残る。逆に実装診断の4 gateを解消しても S/Bとpending fixtureが残り、段0は閉じない。
- **深刻度:** must-fix
- **成果物影響:** `status=incomplete` 自体は正しいが、未完了理由の台帳・診断対応が一致せず、完了証拠が再現不能になる。
- **これはユーザー裁定が要るか:** **no** — §12.3 を「4区分」と呼び、`pending=5 / applicable_unresolved=2 / blocking_gates=4` を別々に列挙すれば直る帳簿不整合である。

## 総括

- 判定: **NO-GO**
- blocker の所見 ID: **LB-B-01, LB-B-03**
- ユーザー裁定が要ると判定した項目: **LB-B-01（R1 の int と下位 UTC string の衝突）、LB-B-03（上位 cancellation の扱い）**

下位 §S2-1.10 への 7 key 対応:

| 下位 | 上位 | 検算 |
|---|---|---|
| `schema_version` | `schema_version` | key 対応可。schema literal の層別変更は必要 |
| `bundle_digest` | `bundle_digest` | 対応可。上位 authority bundle を指す schema-local な意味 |
| `approval_sha256` | `approval_raw_sha256` | 宣言どおり唯一の key rename |
| `revoked_by` | `revoked_by` | key は一致。ただし trim・1〜128 は下位にない追加制約 |
| `revoked_at` | `revoked_at` | **不適合。下位 UTC string、上位 exact int** |
| `scope` | `scope` | `bundle-only` は一致。schema/namespace が対象 bundle を識別するため D75 の同名二義化には当たらない |
| `reason` | `reason` | key は一致。ただし非空は下位にない追加制約 |

4 意味規則の対応:

| 下位規則 | 上位対応 | 検算 |
|---|---|---|
| 一度 X された束だけ | 一度上位 X が成立した束だけ | 一致 |
| live tip 失効後 active なし・fallback禁止 | active 上位束なし・下位へfallback禁止 | 一致 |
| descendant を自動失効しない | 子孫世代を自動失効しない | 一致 |
| 変更・削除・rename・再追加拒否 | 同じ4操作を拒否 | 一致 |

- 下位 §S2-1.10 への conformance の検算結果: **7-key 名の形と4規則は対応するが、field 制約は不適合。したがって総体として conformance 不成立**
- 攻撃したが破れなかった主張: **docs と `_UPPER_REVOCATION_SCHEMA` の7組、および `_EXPECTED_STAGE6_STRUCTURAL_PREDICATES` の5文は現行 bytes と1文字単位で一致／段6 (iii) の「真に大きい」は §5.1 の「新しい世代番号で前進」「単調増加」から導出でき、`+1` は上位には規定されていない／execution 層は fixture ID だけを消費し `load_manifest()` の全体検証を受けるため変更不要／required_gates の未更新 consumer なし／現行 extractor anchor は全て fence 外で、除去対象 fence 内に正当な既存 anchor なし／追加機構はいずれも schema・predicate・gate・fence authority の受理集合または参照を変えるため、段0への不要な盛りは確認できず**