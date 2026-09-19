## 所見 1: 入力由来checkの拒否対照が不足し、M8とtools検査の退行を検出できない

**real/refuted の判定材料：real。重要度：must-fix。** 現行述語が恒真という指摘ではなく、R2・R18と事前登録M8を守るテストの不足である。

[新test:262](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2773-mocc-template-wave2/orchestrator/tests/test_mocc_template_proof.py:262)は、空入力の全false、ON-B identity、12走の一部条件を検査する。しかし、親が列挙したDQ・deny-only・consumer束縛・計装保存・旧proof参照・TRACE=0等には、正常入力を一箇所壊して対応checkを落とす対照がない。

具体的に、[driver:357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2773-mocc-template-wave2/orchestrator/campaign/s3_mocc_template_proof.py:357)の以下を削除するM8を考える。

```python
and records[n]["subtype"] == subtype
```

- `test_mocc_template_quarantine_controls`（新test:153–165）は生成関数の実結果を検査し、`compute_checks`を呼ばない。
- 空入力対照は、削除後も`cases`欠落でfalseになる。
- 完成JSONの正常なsubtypeでは、削除前後の再導出結果が同じになる。

したがって、**M8を検出できないという親所見は静的に支持される**。SURVIVEDの実測は本レビューでは行っていない。

さらに、新test:273–275のBash混入対照には`projections`がない。driver:347のtools比較を削除しても、同:351の欠落キーでfalseになり、対照が通る。こちらは「toolsだけを壊した拒否対照」にもなっていない。

**成果物影響：** subtype検査を削除したdriverがテストを通過し、誤った拒否subtypeを記録した新JSONでも`quarantine_*`をtrue、他条件成立時には`all_pass`をtrueにできる。

**是正案（逐語、file:line）：**

`orchestrator/tests/test_mocc_template_proof.py:262`を、旧testのper-key方式に揃える。

> 全30 checkがTrueになる正常な合成proofを先に検証する。各keyについて、対象入力一箇所の変更または欠落で当該checkがFalseになる対照を置く。DQはpassedを保持してsubtypeだけを変更する。auditorは有効なprojectionsを保持してtoolsにBashだけを追加する。期待key集合・subtypeはテスト側の固定値とする。

M8の最小対照は、正常proofの`cases["stock-frame"]["subtype"]`だけを`"outside-region"`へ変え、`quarantine_rejects_frozen_frame_and_outside_edits is False`を要求する形で足りる。

## 所見 2: OFFの`.text`差は実在するが、R4違反・計装の規律1違反という判定は棄却する

**real/refuted の判定材料：差はreal、must-fix候補はrefuted。重要度：nit（保証範囲の記録）。**

`liveness-run-2.log:12–16`は`0x4a9=1193`から`0x4cc=1228`への変更を示す。preimage:1193には`ERR;`があり、templateの純増35行と整合する。OFFでも原文の物理行番号は保存されない。

一方、R4の保証名はdriver:40、325–327に指定どおり実装されている。`source_digest.py:1686–1687`はincludeを除去して前処理するため、このresolver identityは、include先で定義される`ERR`の展開後即値までの一致を意味しない。隔離checkoutでの実resolver呼出しもdriver:427–445にある。

比較対象を分ける必要がある。

- 無template ↔ OFF：resolverの正規化source identity一致。**実TU・binary完全一致ではない。**
- 同じtemplate状態の計装なし ↔ あり：D1687の論理行列一致。driver:439、452、457–458は基準列を実sourceから独立取得する。
- ON-Bの計装なし ↔ あり：親ログ:26では`.text`一致も確認されている。

したがって、この差を理由に`template_off_stock_identity`をfalseへ変更したり、templateへD1687の`#line`例外を流用したりする必要はない。設計正本:249–250も、その流用を認めていない。

**是正案（逐語、file:line）：**

`s5-author-1.md:41`に対応する親の統合報告へ、次を明記する。

> OFFのstock一致は実resolverの正規化source identityに限定する。無templateとのTRACE=0 `.text`はERRの行番号即値で相違した。実TU・binaryの完全同一性、当該差による性能影響ゼロは主張しない。同一template状態における計装追加の規律1検査とは比較対象が異なる。

性能への影響は未測定であり、不確実である。

## 所見 3: R1の保存述語は入力由来だが、X恒偽化対照の式が恒偽になっていない

**real/refuted の判定材料：保存述語の定数化疑惑はrefuted、対照式の不備はreal。重要度：nit。**

driver:132–159は実patch bytesから追加本文・hunk前後context・復元番号を抽出し、実stock/template sourceの対応からoffsetを導出している。offset定数表の焼き込みはない。`+#line `除外も、現物のX/P検査本文を除外していない。

復元列は旧列に`19,35,35,35,35,35,35`を加えた、

`36 / 1025 / 1026 / 1193 / 1204 / 1222 / 1230`

で、R1・plan:128–136・author報告と整合する。

ただし、新test:206の置換後は次の形になる。

```cpp
if (false && !izanagi_cll_has_writer ||
    counter != W_LOCKED)
```

これは`(false && A) || B`であり、入口検査全体の恒偽化ではない。また同:211–212は「三条件のどれかがfalse」しか要求せず、予定した理由で拒否されたかを固定していない。

現行の追加本文比較はこの変更も完全な恒偽化も拒否するため、現在のJSON受理集合が広がる反例ではない。

**是正案（逐語、file:line）：**

`orchestrator/tests/test_mocc_template_proof.py:206`で条件全体を`false && (...)`に包む。各対照では、X/P変更は`added_body_identical`、publish後への移動は`operation_contexts_identical`、行番号変更は`line_restorations_match`がfalseになることを個別に要求する。

## 所見 4: 残る主要境界に、現行実装の受理集合を広げる反例は認めない

**real/refuted の判定材料：下記の破綻候補はrefuted。重要度：nit（確認記録）。**

| 境界 | 判定根拠 |
|---|---|
| template逐語・4 site | template patch:23–96。helper、外側guard、296のbrace、970のfallback両枝、Options二hunkはR13と整合。親ログ:8–10もmarker/frozen bytesを確認。 |
| 12走・途中保存 | driver:257–280、319–322、413–415。内容検査と終了状態検査を別checkで要求し、欠落走・異常終了は`all_pass=False`。最終auditor記録前もfalse。 |
| DQ・deny-only | driver:167–219。一意一致、実sourceからのdiff、X/P用marker再parse、`source_rel`明示あり。`auditor_gate.py:205–220`はmachine rejectを先に返し、pass側でdigestを照合する。 |
| auditor契約 | 軸module:80–90、102–162、driver:370–384。項目境界で固定literalを検査し、toolsは既存loader由来。性能・未知fieldはallowlist外として拒否する。 |
| DQ passの意味 | 軸module:3–5、auditor.md:64。純粋性・停止性等の証明と扱わず、レンズAの素通り形は型16の文章契約で禁止される。 |
| 束縛・gate | 軸module:55–77、165–186、新test:53–134。束縛関数は`all_pass`を見ず、別path・別OIDを拒否。import失敗を握り潰さず、JSON欠落は指定二nodeで赤になる。 |
| 規律2・旧成果物 | 統合diffの17ファイルに、指定された旧driver/test/patch/JSON、DQ、auditor_gate、source_digest、model、pinの変更はない。既存Silo gateの変更もない。 |

auditorの行番号はpreimage:477、905–913、1010–1013、1024–1036と一致する。hot readのabsent非検査とI absentの限定も維持され、D2134項2・7を弱めていない。

**是正案（逐語、file:line）：** 上記箇所の変更は不要。所見1の対照追加後も、D2134項3・4・9の「経路共通証拠の参照」「全動的被覆を主張しない」「探索非解禁」を維持する。

## 所見 5: author報告と統合版には時点差があり、初回生死ログは成功証拠に使えない

**real/refuted の判定材料：時点差はreal、虚偽報告との断定はrefuted。重要度：nit。**

- author報告:15、51–53、103はadapter未更新とするが、統合diff:44以降にはadapter更新が含まれる。現在のadapterのsource SHAはauditor本文の`dc63a311…65f34`と一致する。
- author報告:105の「11 modified＋新規5」はauthor終了時の記録であり、統合diffは既存12＋新規5である。
- `liveness-run-1.log:6–7`は旧計装が適用できたとしてrc=2で終了する。後続`liveness-run-2.log:6–7`は明示的な`git apply --check`不適用を記録し、同:27はrc=0。初回相違の原因は提示ログだけでは不確実。
- `focus-1.log:30`は658 passed／2 skipped。これはauthorの自走結果とは別の親実測であり、JSON依存二nodeを含む完成proofの受入成功ではない。

新規5ファイルは統合diffと現在の内容が一致し、提示patch SHA・auditor SHAにも不一致はなかった。

**是正案（逐語、file:line）：**

`s5-author-1.md:103`に対応する統合報告では、

> author終了時の未完事項と親統合後の状態を分ける。生死確認の採用証拠はliveness-run-2.log、焦点走はfocus-1.logとし、初回rc=2を成功扱いしない。

と記録する。

## 総括

**NO-GO。must-fixは1件：全30 checkの入力由来拒否対照を補い、M8とBash混入対照の検出漏れを閉じること。**

OFFの`.text`差は実在するが、R4の限定されたidentity保証とは矛盾せず、これ自体を修正必須とはしない。R1のX恒偽化対照は式と拒否理由を修正すべきnitとする。

報告と実体にはadapter・変更件数の時点差、および初回／再走ログの相違がある。現時点で虚偽報告と断定する根拠はない。静的レビューのみ実施し、pytest・build・変異実行は行っていない。