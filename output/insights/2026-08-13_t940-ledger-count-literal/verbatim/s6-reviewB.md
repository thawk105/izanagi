## 総括

**GO ではない。裁定の erratum と再登録が必要。**

主要所見は次の 3 件。

1. **real — M8 は期待 node 2 件自体は正しいが、DW-M01 の単一理由性を満たさない。**  
   literal oracle が先に同じ入力を拒否するため、M8 は D4 の実効性を証明しない。裁定独自の「複数層でも理由が一つならよい」という解釈は、正本の「同じ入力を拒否する層が前後に無いこと」と矛盾する。
2. **real — M1・M4・M8 は exact entry/SHA と置換 anchor が未登録で、期待 node 完全集合を確定できない。**  
   SHA や entry 内容によって stale、schema error、重複、stdout pin が追加発火する。
3. **real — M4 は entry の実在性・実在違反を検証しない。**  
   存在しない SHA や、実在するが違反のない commit でも、現在の固定 test 選択集合外なら SURVIVED になりうる。「承認済み entry の正例」という意味論までは証明できない。

pytest・変異本走は行っていない。以下は指定ファイルの静的検査と、副作用のない Python in-memory probe による判定であり、「緑」とは報告しない。

略号:

- `LIT` = `orchestrator/tests/test_check_ai_provenance.py::test_known_violation_ledger_matches_literal_entries`
- `REG` = `orchestrator/tests/test_check_ai_provenance.py::test_production_registry_notes_satisfy_descriptive_contract`

| 変異 | 期待 status（親案 → 判定） | 期待 node（親案 → 判定） | real / refuted・根拠 file:line |
|---|---|---|---|
| M1 | KILLED → **条件付き KILLED**。現登録のままでは未確定 | `LIT` → **`LIT`**。ただし exact SHA/entry を固定し、schema-valid・一意・全固定選択集合外なら | **real（登録不足）**。通常の valid 39 件目は generator により観測され、38 行の expected と不一致になる [test:1386](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1386)、[test:1448](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1448)。SHA 未固定のままでは stale 等を排除できない [production:1639](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:1639)。 |
| M2 | KILLED → **KILLED** | `LIT` → **`LIT`** | **refuted（親案が正しい）**。`187fed...` は expected の1箇所だけ [test:1443](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1443)。`missing-codex-author` の note は記述性必須集合外 [production:665](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:665) なので schema-valid 1文字は `REG` を落とさない。 |
| M3 | KILLED → **KILLED** | `LIT` → **`LIT`** | **refuted（親案が正しい）**。削除後も registry と source はともに37件なので self-consistency は通る [test:1913](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1913)。固定35・30・stdout pin に対象 SHA はない。 |
| M4 | SURVIVED → **条件付き SURVIVED**。ただし「実在する承認済み違反」の証明にはならない | — → **—** | **real（意味論と登録不足）**。両層の全5 field・順序を一致させ、registry schema を満たす一意 row なら通る。しかし entry の存在を全件確認する処理はなく、stale は selected commit だけが対象 [production:1470](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:1470)、[production:1639](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:1639)。 |
| M5 | SURVIVED → **SURVIVED** | — → **—** | **refuted（親案が正しい）**。現 production は38件のままなので再導入 assert は真。source-contract consumer も見つからない。実装変更箇所は author 報告 [s5-author:10](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t940-ledger-count/s5-author.md:10)。 |
| M6 | SURVIVED → **SURVIVED** | — → **—** | **refuted（正直な SURVIVED）**。対象 assert は対象ファイル内 exactly 1 箇所 [test:1448](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1448)。その test の source を監査する別 gate はない。 |
| M7 | SURVIVED → **SURVIVED** | — → **—** | **refuted（正直な SURVIVED）**。現38件は一意なので guard 削除単独は振る舞いを変えない。guard は [production:613](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:613)、後段の dict 登録は [production:693](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:693)。 |
| M8 | KILLED → **KILLED。ただし D4 の証拠としては不適格** | `LIT`, `REG` → **`LIT`, `REG`**。simple `__len__` override・valid unique 39件目・選択集合外という条件付き | **real（単一理由性違反）**。iteration は39件を見るため `LIT` が赤。registry は39件だが source の `len()` は38なので `REG` も赤 [test:1913](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1913)。裁定の複数層容認 [s4:64](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t940-ledger-count/s4-adjudication.md:64) は DW-M01 [mutation.md:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/docs/dev-wave/mutation.md:7) と衝突する。 |

### M1 の SHA 選択による先取り条件

**real — SHA を固定しない限り期待 node は完全集合にならない。**

- 現台帳 SHAを選ぶと「一意 SHA」に反し、`_known_violation_registry()` の duplicate guard が先取りする [production:613](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:613)。固定35・固定30・stdout pin の SHA はいずれも現台帳 entry なので、この条件に該当する。
- full lower-case 40 hex、entry型、kind、ruling、note/value契約のどれかを破ると registry validation が先取りする [production:591](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:591)–[production:693](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:693)。
- 新 SHA がある test の `commits` に選択され、その commit に期待違反がなければ stale になる。stale 対象は `registry ∩ selected` だけ [production:1639](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:1639)。
- 選択された commit に別 kind/value の違反があれば、通常 finding と stale の双方の原因になりうる [production:1480](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:1480)。
- **実在するが違反のない commitでも、選択集合外なら stale は発火しない。** `_known_violation_audit()` は未選択 registry entry の count を作らない [production:1470](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:1470)。したがってこの場合、valid・uniqueなら `LIT` だけが赤になる。

修正は、M1 の exact SHA・kind・ruling・note・valueを段4 erratumで固定し、固定35 [test:1458](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1458)、固定30 [test:2529](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:2529)、stdout pin [test:2629](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:2629) の外であることを再確認すること。

### M2 / M3 の `187fed...` 固定

**refuted — 親の選択は正しい。**

静的実測結果:

- `git cat-file -t 187fed...` は `commit`。
- tracked Python上の完全SHA出現は production entry [production:541](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:541) と literal expected [test:1443](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1443) の2箇所だけ。
- 固定35、固定30、`test_ledgered_3f2c...` のいずれにも含まれない。
- M2 の1文字 note は `missing-codex-author` なので、malformed専用の note記述性検査に触れない。

したがって、正確な production block を置換すれば M2/M3 の失敗 node は `LIT` だけ。

### M4 が SURVIVED になるための完全条件

追加 row は次をすべて満たす必要がある。

- production側は `KnownViolationSpec` として反復可能である。
- commit は built-in `str` として扱われ、小文字hex 40桁 [production:603](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:603)。
- SHA は既存 entry と非重複 [production:613](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:613)。
- kind は `missing-ai-agent`、`missing-codex-author`、`malformed-ai-agent` のいずれか [production:623](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:623)。
- ruling は非空の `str` [production:628](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:628)。
- note は `str` かつ単一行。malformed kind では非空・禁止文字なし・記述的文字あり [production:633](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:633)–[production:686](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:686)。
- finding value は `str`。malformedでは非空必須、それ以外では空必須。禁止文字も不可 [production:643](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:643)–[production:691](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:691)。
- production と expected の5 fieldおよび挿入順序が完全一致 [test:1386](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1386)–[test:1448](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1448)。
- expected側でも SHA が一意 [test:1449](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1449)。

**実在性は条件として検査されない。** 未選択 SHA の存在確認も実違反確認もない。したがって、現在の M4 は「件数39のschema-valid同期rowを過剰拒否しない」ことだけの正例へ改称するか、実在違反を `_audit_history([sha])` へ通す coverage を追加すべき。

### M8 の2 nodeと第三経路

副作用なしの simple tuple subclass probeでは次を実測した。

```text
reported_len=38
iterated_len=39
registry_len=39
literal_equal_38=False
registry_tuple_equal_source=True
d4_len_equal=False
```

したがって、記述どおり `__len__` だけを偽るなら `LIT` と `REG` の2件は正しい。

第三件以降が出る条件:

- 39件目がschema-invalidまたは重複なら、registryを利用する複数 node が validation error。
- 39件目の SHA が固定 commit 集合やstdout対象に選択されれば、staleまたは出力差。
- tuple以外の容器なら container検査が発火する。ただし tuple派生型は `isinstance(..., tuple)` を通る [production:591](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:591)。

1件だけになる条件:

- `__iter__` も偽装して literal testから39件目を隠す。
- literal oracleを同時変異で無効化する。
- harnessのpytest選択から片方を外す。

これらは現在の「`__len__` だけ」の記述には含まれない。

### 単一理由性と修正案

**real — M8 をそのまま走らせてはならない。**

DW-M01は、同じ入力を前後の別層が拒否しないことを要求する [mutation.md:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/docs/dev-wave/mutation.md:7)。親裁定の独自解釈 [s4:64](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t940-ledger-count/s4-adjudication.md:64) はこれを緩和している。

修正案:

- M8を `both-layers` に再登録する。
- productionへ simple `Len38Tuple`＋valid 39件目を注入する。
- 同じ変異内で literal側の反復だけ39件目を除外し、`LIT` を通す。
- 期待を `KILLED`、期待 nodeを **`REG` 1件だけ**にする。

harnessは1変異内の複数 replacementを累積適用できる [mutation_harness.py:803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/mutation_harness.py:803)。したがって「1変異に収まらない」という裁定理由は **refuted**。

### DW-M04 の置換一意性

現段4表には exact `old` / `new` がないため、正式な注入実在性は未確定。静的に確認できた候補は以下。

- M2/M3: productionの `187fed...` は1箇所。
- M5/M6: `assert observed == expected` は対象test file内1箇所。
- M7: `if spec.commit in registry:` はproduction内1箇所。
- M1/M8: production assignment `KNOWN_PROVENANCE_VIOLATIONS = (` と末尾production SHAはいずれも1箇所。
- M4: expected側で末尾SHA `8ceeb...` だけを anchorにすると **3箇所一致**し、harnessが停止する。行全体と直後の `expected` tuple閉じを含む文脈 anchorにする必要がある。

harness自身は各 replacement の累積後 count が exactly 1でなければ停止する [mutation_harness.py:808](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/mutation_harness.py:808)。本走前に生成するspecの exact anchorとSHAを段4 erratumへ固定すべき。

### 親裁定に不足する変異

- **real — D4を単独で発火させる再照準済みM8**が不足している。現M8は `LIT` にmaskされ、D4の証拠にならない。
- **real — entry実在性・実在違反のpositive coverage**が不足している。裁定自身もF13として認識している [s4:59](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t940-ledger-count/s4-adjudication.md:59)。scope外を維持するなら、M4の主張をschema/count acceptanceに限定する必要がある。
- **refuted — M5/M6/M7をSURVIVEDとすること自体は偽装ではない。** いずれも現在の入力に対して観測不能であることを正直に記録している。
- **refuted — M2/M3に追加node漏れはない。** `187fed...` 固定は適切。

結論として、親は本走前に少なくとも M1/M4/M8 の exact payloadとanchorを固定し、M8をD4だけが殺す両層変異へ再照準し、M4の主張を実在性まで広げない形へ裁定を訂正する必要がある。