## RB-01 — real・blocker：checkpoint の選定可否が定まらない

**根拠:** `docs/agent-architecture.md:129` の定義は「何をどう測り、どう判定したか」。測定結果の要約と探索の進行状態の境界がない。

指定 campaign `output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/` の4件を全文開き、適用した。

| 成果物 | 判定 | 現物の根拠 |
|---|---|---|
| `campaign.lock:1` | 除外 | `spec_content` に設計説明と「fixture red を正系列に混ぜない」がある。 |
| `loop_state.json:2` | **判定が割れる** | iteration・開始時刻・逆方向推奨数という進行状態と、whiteboard の `result: "success"` が同居。測定対象・条件・観測値は記録されず、`delta_pct` は全件 null。 |
| `runs/wal.jsonl:1` | 選定可能 | 全15行に build 条件、検証判定、測定値、commit 結果がある。コマンド文字列も実行履歴を述べている。 |
| `s4_loop_digest.txt:35` | 除外 | 「異常かどうかは読み手が stock 対照比で判断」という運用説明がある。 |

`loop_state.json` は「どう判定したか」の要約として含める読みと、測定記録ではない checkpoint として除外する読みが成立する。設計説明の除外条件だけでは決着しない。

**成果物への影響:** 同じ資料から作る manifest の `sources` とその SHA、投入知識源の記録が送り手によって変わる。既存の certified 判定値が変わる証拠はない。

**最小修正:** 定義直後に次を加える。

> 探索の進行状態と抽象的な成否だけを保存した checkpoint は、ここでいう測定記録には含めない。

## RB-02 — real：参照先の節名が逐語一致していない

**根拠:** `docs/phase3.md:372` → runbook §1 → `docs/agent-architecture.md` という配置は辿れる。参照も planner 起動前の `docs/phase3-s4b-runbook.md:41` にある。

ただし42行の「同 role 節『知識源の選定』」に一致する見出しはない。実際には105行の role 見出しと、128行の **「知識源の選定 (送り手側の義務、D1936 項 2)」という箇条書き**である。

**成果物への影響:** 指定された逐語一致の節参照としては切れている。部分文字列検索では到達でき、certified 選択等への影響は示せない (nit)。

**最小修正:** runbook の参照文を次に置換する。

> 知識源は `docs/agent-architecture.md` の「coder-v4-autonomous-k2 (K2 宣言アーム、D1429 = `.claude/agents/coder-v4-autonomous-k2.md`)」節にある「知識源の選定 (送り手側の義務、D1936 項 2)」項に従って選ぶ。

## RB-03 — refuted：別 campaign では除外規律が転移しない

**根拠:** `output/campaigns/p3-s4-red-s4-red-consumer-9a1897c4/` の全3ファイルも開いた。

| 成果物 | 判定 | 現物の根拠 |
|---|---|---|
| `campaign.lock:1` | 除外 | 設計説明に加え「正系列に混ぜない」がある。 |
| `runs/wal.jsonl:1` | 文種による選定は可能 | 全7行が build・timeout・検証失敗の記録。成功性能値がなくても「どう判定したか」に該当する。 |
| `s4_rejections_digest.txt:17` | 除外 | 別名の digest にも「異常かどうかは読み手が stock 対照比で判断」がある。 |

ファイル名の許可リストにせず、本文の種類で同じ結論を得られる。ただし WAL を選べることは、fixture の結果を実測性能として使えることを意味しない。

**成果物への影響:** 転移不成立による影響は示せない (nit)。

**最小修正:** 不要。現行の「判定は **誰が書いたか**ではなく**何を述べた文か**で行う」を維持する。

## RB-04 — refuted：重複・scope 拡張・可変状態の追加

**根拠:** runbook の追記3行は適用条件と参照だけで、測定記録の定義・除外例・加工禁止を複製していない。`docs/skill-self-improvement.md` routing 5 に抵触しない。

規律は K2 role 節に置かれ、runbook も「K2 宣言アーム」を明示する。新しい gate・台帳・consumer 変更は差分にない。「実績のある例」は歴史的事実であり、増減する件数・現在状態・日付の追加ではない。

**成果物への影響:** K2 外の受理集合や台帳値が変わる根拠は示せない (nit)。

**最小修正:** 不要。適用条件「**K2 宣言アーム (`coder-v4-autonomous-k2`) を回すとき**」を維持する。

## RB-05 — refuted：追記による機械検査違反・架空参照

**根拠:** `python3 -B tools/check_docs.py` は終了コード0、`check_docs: 違反なし`。`git diff --check` も終了コード0。

両文書は living doc の検査対象で、今回の変更先は byte 予算・whole-file pin の対象外。追記に docs 行番号参照、現在 pin の literal はない。D1936 項2は `docs/decisions.md:58110` に実在し、参照する文書・WAL・lock・digest も実際に開いて確認した。RB-02 の意味上の参照不一致は、この検査成功では解消しない。

**成果物への影響:** 機械検査違反による影響は示せない (nit)。

**最小修正:** 不要。裁定参照「D1936 項 2」を維持する。

## 総括

blocker は RB-01。指定された checkpoint の選定可否が本文だけでは一意に定まらない。
現状の差分は land 不可。定義を明確にし、RB-02 の参照表記も訂正してから再確認する。
機械検査は成功した。ファイル変更・commit は行っていない。