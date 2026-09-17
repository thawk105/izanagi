## 総括

- **real 2 件、refuted 5 件。must-fix は 2 件**：D922 追補の期限への一般化、DW-O18 の固定 byte 数 assert の追随漏れ。
- DW-O18 の安全義務、F1000 の防壁、D1875 の保留、rc 契約を緩める変更は確認しなかった。
- DW-O18 と D922 追補の訂正版を以下に提示する。
- 読取り・文字列計数・構文解析だけを実施。pytest・checker は実走していない。

## 1 DW-O18 案文の差分と安全義務

照合対象は `/home/SFC/tanab/.claude/jobs/4aa46448/tmp/wave/dw-o18-current.md:5` と `/home/SFC/tanab/.claude/jobs/4aa46448/tmp/wave/dw-o18-new.md:5`。現行ファイルは production literal と合成 fixture の双方に byte 一致した。

**変更は次の 3 箇所だけ**。見出し、空行、それ以外の文言は一致する。

| 削除された逐語 | 追加された逐語 |
|---|---|
| 再赤/決定的赤はmain既存Fを証拠にCodex`role=author`が`orchestrator/tests/flaky_test_holds.py`へ登録(field正本=同file)。 | 再赤/決定的赤でもhold登録簿へ登録しない(契約testが1件に固定、F1000)。 |
| F不在は登録せず裁定送り、 | 真に決定的な不安定testは1件ごとにpin更新を裁定送り、 |
| 停止条件外は治すかhold登録後だけ投げ直しwaveを止めない。 | 停止条件外は治すか投げ直しwaveを止めない。 |

**refuted F1：他の安全義務も弱めた、という懸念。** 判定主体の境界、根拠の記録、署名一致禁止、5 分超禁止、単独再走→非再現時の受入再走、同一 tip で各 1 回、判定不能・原因未理解の停止、`child-green` 限定は逐語で残る。取り下げ対象は登録経路とその前提条件であり、D2104 項 30 と一致する（`docs/decisions.md:65140`）。

「停止条件外は…投げ直し」は直前の「同一tipで各1回だけ」に制約される。回数を消費した後に再々投入できる授権はない。ただし、後の文だけを切り出すと無制限の継続と誤読しやすいため、「上記の制限内で」を補うと明確になる。

**refuted F2：個別の pin 更新相談が F1000 の防壁を破る、という懸念。** 「1件ごとに…裁定送り」は「その1件について…個別に諮る」と同義であり、wave 自身による更新を許可しない。F1000 が否定するのは、当該 wave を緑にするための自律的な pin 書換えである。後続のユーザー裁定による個別相談まで禁止していない（`/home/SFC/tanab/.claude/jobs/4aa46448/tmp/wave/F1000.md:15`、`docs/decisions.md:65140`）。

**refuted F3：byte・最長行制約違反。**

| 対象 | UTF-8 bytes | 最長行の文字数 | 最長行の bytes |
|---|---:|---:|---:|
| 現行 | 997 | 354 | 796 |
| 親案 | 971 | 308 | 770 |
| 下記訂正版 | 995 | 316 | — |

- 見出しは不変。exact pin は `tools/check_docs.py:656`、比較実体は同 `:1923`。
- L2 上限は同 `:360` の 1,000 bytes。節 slice を UTF-8 で数える検査は同 `:5393`。
- **DW-O18 に最長行上限は設定されていない。** reference は `limit=None` で登録される（同 `:5983`）。最長行検査は `limit` と `max_line_chars` がある場合だけ発火する（同 `:6022`）。command 側の最長行上限を operations へ適用してはならない。

裁定の逐語と再投入制限を明確にする訂正版は以下。**末尾を `。\n\n` として 995 bytes**。予算に収まる。

```markdown
## DW-O18 — テスト cwd と非帰属赤の着地

cwd=repo root。nested subprocess import path偽赤は回帰外。file選択走は`from tests import`確立後に限り未確立赤も偽赤。

受入赤返却時が判定主体の境界。待ち手は赤返却だけ。人・AIが判定し根拠をworklogへ残す。assertion本文・差分実体で判定、署名一致禁止。非帰属赤の着地5分超禁止、悩まない(D690)。自分起因は直す。N走完全一致はflakeでも非帰属の証拠でもない。差分到達不能は単独再走、非再現なら受入再走。同一tipで各1回だけ。再赤/決定的赤でもhold登録簿へ登録しない(契約testが1件に固定、F1000)。真に決定的な不安定testはその1件のpin更新を個別に諮る。判定不能・原因未理解は除外せず共に停止。停止条件外は治すか上記の制限内で投げ直しwaveを止めない。受理は`child-green`だけ、赤の受領証禁止。

```

## 2 実装面の追随

**real R2・must-fix：997 bytes の固定 assert が親 brief の編集箇所から漏れている。**

`orchestrator/tests/test_check_docs.py:9484`：

```python
assert len(_SYNTHETIC_DW_O18_SECTION.encode("utf-8")) == 997
```

親案採用なら **971**、上記訂正版なら **995** へ追随が必要。所属 node は `test_normative_exact_section_contract_is_handwritten_and_complete`（同 `:9457`）。fixture を更新しても、この assert を残せば失敗する。

必要な追随は次のとおり。

| 箇所 | 必要な対応 |
|---|---|
| `tools/check_docs.py:605` | production literal 更新 |
| `orchestrator/tests/test_check_docs.py:166` | 独立した合成 fixture 更新 |
| 同 `:9484` | 固定 byte 数更新 |
| 同 `:9582` | M2 needle 更新 |
| 同 `:9639` | M11 needle 更新 |

**新案に対する実計数**：

| case | needle | count |
|---|---|---:|
| M1 | `非帰属赤の着地5分超禁止、悩まない(D690)。` | 1 |
| M2・旧 | `F不在は登録せず裁定送り、` | 0 |
| M2・新候補 | `真に決定的な不安定testは1件ごとにpin更新を裁定送り、` | 1 |
| M3 | ``受理は`child-green`だけ、`` | 1 |
| M4 | `判定不能・原因未理解は除外せず共に停止。` | 1 |
| M10 | `N走完全一致はflakeでも非帰属の証拠でもない。` | 1 |
| M11・旧 | `停止条件外は治すかhold登録後だけ投げ直しwaveを止めない。` | 0 |
| M11・新候補 | `停止条件外は治すか投げ直しwaveを止めない。` | 1 |
| M12 | `未確立赤も偽赤。` | 1 |

M2 は「個別裁定の要求を落とす」変異へ再照準する。登録禁止自体の保護は §6 の負例でも確認する。訂正版採用時は M2・M11 を訂正版の対応する全文へ置き換える。

M7 の旧見出しも新案に 1 回出現する。M5・M6 は DW-O16 への禁止語追加、M8 は DW-O26 の文削除なので、DW-O18 新案内の出現数を要求する case ではない（同 `:9600`、`:9625`）。

その他の依存関係：

- `_build_min_repo` は独立 fixture を採用する（同 `:1039`）。production literal だけを変えると、合成 repo を使う正例が広く失敗する。
- `test_dw_o18_exact_section_pin_accepts_synthetic_fixture` は fixture と checker が揃えば本文修正不要（同 `:9521`）。
- exact map の assert は同じ fixture を参照するため、別の本文複製の更新は不要（同 `:9490`）。
- `.claude/commands/dev-wave.md:106`、`docs/dev-wave/operations.md:190`、`orchestrator/tests/README.md:98` は節参照。見出し不変なら変更不要。
- `.codex/`、`hooks/`、`AGENTS.md`、他の `orchestrator/tests/` から旧登録文への追加依存は検出しなかった。対象外の歴史記録を除いた本文検索でも、上記 3 ファイル以外に旧登録文の複製は検出しなかった。

## 3 D1875 追補の事実関係

**refuted F4：予算訂正が誤っている、または保留解除を含む、という懸念。**

現物は一致する。

| 確認対象 | 根拠 |
|---|---|
| D1875 の「D114 が定めた承認済み generation 予算 1」 | `docs/decisions.md:56793` |
| D410 の「D114 の承認上限 1 を 2 へ上げる」 | `docs/decisions.md:17153` |
| `MAX_APPROVED_GENERATIONS = 2` | `orchestrator/campaign/p3_autonomous_workload_trial.py:145` |

追補の読み替えは予算の履歴・現在値だけを訂正する。公開呼び手を置かないこと、origin 分岐を先行すること、残る 3 件の保留を明記しており、他の決定を変更しない（`/home/SFC/tanab/.claude/jobs/4aa46448/tmp/wave/decisions-fragment-draft.md:15`、同 `:18`）。

**「Q2〜Q4」は D1875 自身の項目名ではない。** T-2293 側の分類であり、台帳遷移・起点専用 entry point・completion/report を指す（`docs/archive/worklog-phase3-0916-1566.md:417`）。D2104 項 3 が対象を `T-2293 (Q2〜Q4)` と明記し、後続 worklog も同じ対応を持つ（`docs/decisions.md:64857`、`docs/archive/worklog-phase3-0917-1596.md:431`）。

したがって文脈を含めれば一意。ただし追補単独での明瞭さのため、次へ変更するとよい。

> **T-2293 の Q2〜Q4（D2104 項 3）の保留は維持し、一括承認はしない。**

これは参照の明確化であり、新しい保留対象を追加しない。

## 4 D922 追補と timeout の境界

**real R1・must-fix：「候補上限や期限」の期限部分は実装から支持されない。**

問題の逐語は `/home/SFC/tanab/.claude/jobs/4aa46448/tmp/wave/decisions-fragment-draft.md:42`：

> 正証拠で既に確定した `landed` は、その後に候補上限や期限へ達しても `indeterminate` へ倒れない。

候補上限については正しい。

- `candidate_limit + 1` 件まで候補を取得する（`tools/check_branch_landed.py:777`）。
- 候補照合で一致すれば `matched` を返す（同 `:791`）。
- 全候補の照合後に初めて上限超過を報告する（同 `:802`）。
- `_regular_decision` も `matched` を先に `landed` へ変換する（同 `:1348`）。

しかし **deadline は別の経路**。

- Git 起動前の残時間切れ・subprocess timeout は `AssessmentError`（同 `:215`、`:241`）。
- batch の解析途中も残時間切れで raise する（同 `:750`）。batch 全体の解析が終わる前に、一致候補の個別照合へ進めない。
- proof unit が `landed` でも、最後に ref snapshot を再取得する（同 `:1941`）。
- そこで期限切れが外側へ伝播すると、assessment 全体の `decision` は `indeterminate` になる（同 `:1989`、`:2002`）。
- ref 移動自体も集約判定を `indeterminate` にする（同 `:1591`）。

既に得た unit の証拠が残ることと、assessment 全体が `landed` を返すことは別である。候補探索の局所的な優先順を、走行全体の期限免除へ一般化している。

**追補の訂正版：**

> **D922 点 4 のうち、候補探索の上限超過について限定する。** 候補上限超過を報告する前に点 2 の決定的な正証拠との照合が成立した場合、その探索は `matched` とし、当該証明単位は `landed` とする。候補上限超過だけを理由に、その正判定を `indeterminate` へ変更しない。負証拠を閉じられない探索の打ち切りは `not-landed` ではなく `indeterminate` とする。本追補は timeout、parse 不能、shallow、履歴書き換え、ref 移動の扱いを変更しない。assessment 全体の `landed` は既存の集約条件による。現行実装を正とし、実装は変えない。

見出しも「**D922 点 4 の候補上限超過の扱いを限定し、照合済みの正証拠を維持する**」へ揃える。現案の却下理由（同 draft `:57`）も「候補上限超過だけで照合済みの正証拠を捨てる」に限定すべきである。

## 5 rc 表への追記

**refuted F5：landed 判定の `indeterminate` を rc=2 とする追記が誤り、という懸念。**

経路は明確である。

1. `expected_conclusive = verdict != "indeterminate"`（`tools/check_branch_rescue.py:1614`）。
2. `complete` に同じ値を設定（同 `:1631`）。
3. `complete=False` なら `technical_incomplete=True`（同 `:2071`）。
4. 通知の rc=3 より先に rc=2 を返す（同 `:2141`）。

D1231 の「完全な絵を描けたか」という rc 定義と、`indeterminate` があっても rc=0 とする案の却下にも一致する（`docs/decisions.md:40560`）。

**置き場は親案どおり rc=2 行でよい。** 推奨全文：

```markdown
| `2` | timeout、上限超過、root 移動、期限算出不能、台帳 parse 不能などで技術的に不完全。landed 判定に `indeterminate` が 1 件でもある場合を含む (D1231) |
```

直後の段落は `retention.loss_possible_not_before` の分類を説明するものであり、landed verdict の定義ではない（`docs/unreachable-object-ledger.md:91`）。「landed 判定に」と限定すれば、同 `:97` の storage・時刻由来の `indeterminate` と混同しない。段落側への重複追記は不要。

## 6 P1-1〜P1-4 への意見

根拠となる親裁定は `/home/SFC/tanab/.claude/jobs/4aa46448/tmp/wave/parent-brief.md:37`。

| 裁定 | 判断 | 条件・理由 |
|---|---|---|
| P1-1 | 同意 | 一般登録を撤回し、個別相談を残す構造は D2104 と整合。§1 の明確化を推奨する。 |
| P1-2 | 条件付き同意 | literal・fixture・needle に加え、R2 の byte assert を追随対象へ追加する。最小変異でよいが、実行結果で確認する。 |
| P1-3 | 同意 | rc=2 行への限定した追記で十分。 |
| P1-4 | 設計上は同意 | R1・R2 を段 4 の確定事項と author 指示へ反映すれば、独立した再計画で増える内容は小さい。file:line の存在だけを省略理由にはしない。 |

P1-4 について、本 consult は指定された射影だけを読む契約である。**段 2 省略が dispatcher の手続規則上も許されるかまでは、今回の資料から認定しない。**

P1-2 の具体的な最小 matrix は次の構成を推奨する。**変更対象は production literal だけ**であり、fixture・docs は固定する。

| 変異 | 内容 | 指定する検出 node |
|---|---|---|
| M0 | Python 文字列の分割など、評価後の literal が完全に同一 | `test_dw_o18_exact_section_pin_accepts_synthetic_fixture` が通る |
| N1 | 登録禁止を登録許可へ反転 | `test_dw_o18_exact_section_pin_accepts_synthetic_fixture` が失敗する |
| N2 | 新 M2 の個別 pin 相談句を削除 | `test_non_attributable_landing_contract_mutations_have_one_finding[M2]` が失敗する |
| N3 | 新 M11 の継続句を削除 | `test_non_attributable_landing_contract_mutations_have_one_finding[M11]` が失敗する |

正例 node は `orchestrator/tests/test_check_docs.py:9521`、変異 node は同 `:9557`、対応分岐は同 `:9581` と `:9638`。

N2・N3 は、test が docs から同じ句を削った結果と改変 checker の期待値が一致してしまい、期待する exact 不一致が消えることで殺される。N1 は独立 fixture を正常と認めなくなることで殺される。全負例は独立全文比較 node（同 `:9457`）でも検出される。

これは**静的に導いた検出予測**である。親による実走で M0 通過・各負例の失敗を確認すること。また、この matrix は一般登録禁止や再投入上限の実行時 enforcement を証明するものではない。

## 7 scope 逸脱と F1000 の扱い

**scope 逸脱として確認したのは R1 の期限への一般化。** 同じ追補の冒頭で D922 点 4 全体を引用して限定する書き方も、parse 不能・ref 移動まで正判定優先へ変えたように読める。§4 のように候補上限に限定すれば解消する。

その他は所見なし。確認箇所は以下。

- 予算訂正と保留維持：draft `:11`〜`:22`、`docs/decisions.md:64857`。
- rc 文言補完：`docs/unreachable-object-ledger.md:84`、`docs/decisions.md:65058`。
- 一般登録撤回と個別相談：`docs/decisions.md:65140`。
- fragment の frontmatter・遅延採番：draft `:1`〜`:9`、`docs/spool/decisions/README.md:5`。新 D 2 本を 1 fragment に置く形式は適合する。

**F1000 の supersede 追記 1 行は、D2104 項 30 の帰結を記録する限り scope 内と判断する。** 新しい恒久対応を設計するのではなく、「未定」としていた選択が既に裁定されたことを記録するためである。F1000 自身がその選択を裁定送りとしている（`/home/SFC/tanab/.claude/jobs/4aa46448/tmp/wave/F1000.md:19`）。

記録する内容は例えば次に限定する。

> D2104 項 30 により、契約テストの登録簿 pin を維持し、DW-O18 の一般登録手順を取り下げる方針が確定した。真に決定的な不安定 test の pin 更新は当該 1 件ごとに個別裁定へ送る。

「実装完了」とは書かず、方針確定と施工完了を分ける。canonical の既存文を書き換えず、既存の supersede 挿入機構を使うことは `docs/spool/README.md` の不変条件にも沿う。

ただし、**本 consult の必読射影には failures fragment の個別文法がないため、上記は payload の提案であり、投入用 fragment の形式確認済みという意味ではない。** 親が段 4 で採否を確定すればよく、新しい gate・台帳・pin 更新権限を追加する理由にはならない。