結論は **NO-GO**。指定対象はすべて読了しました。pytest・runner・checker は実行しておらず、緑は主張しません。実行したのは静的読解、byte 数確認、書込みを伴わない `git interpret-trailers` probe だけです。

### B-1 — Git 設定により CAB 件数が相殺される

- severity: **High**
- real/refuted: **real**
- file:line: [plan.md:18](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/plan.md:18)、[check_ai_provenance.py:44](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:44)
- 影響: `raw CAB 件数 == parsed CAB 件数` は、parsed CAB がすべて raw 候補由来という前提を固定していない。read-only probe では `trailer.cab.key=Co-Authored-By` を設定すると、本文側の分断 CAB 1 件と、最終 block の `cab:` alias 1 件が raw=1/parsed=1 に相殺された。`trailer.separators=:=` でも `Co-Authored-By=` が parsed CAB になる。計画どおりでは、新 gate が拒否すべき分断 message を受理し、受理集合が Git 設定依存になる。
- 最小修正: CAB placement 用 `interpret-trailers` を system/global/local の trailer alias・separator から隔離するか、非既定設定を fail-closed にする。alias と追加 separator による相殺を境界テストへ追加し、D98 に parser 環境契約を記録する。

### B-2 — `SELF_LIMITS` 直接追加は dispatch allowlist を広げる

- severity: **High**
- real/refuted: **real（brief の欠陥。planner は修正案を提示済み）**
- file:line: [brief.md:17](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/brief.md:17)、[check_docs.py:228](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_docs.py:228)、[check_docs.py:1627](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_docs.py:1627)
- 影響: `SELF_LIMITS` の key は予算だけでなく `NORMATIVE_DISPATCH_ALLOWLIST` に入る。段契約は section pair を比較する一方、section を伴わない bare path は allowlist が最後の防壁なので、直接追加すると `docs/ai-provenance.md` を dispatch 表へ混入させる変更まで機械受理し得る。
- 最小修正: 段4で brief の P2 を明示的に覆し、plan の独立 `PROVENANCE_LIMITS` を採用する。`all_limits` と budget-governed test 集合には加え、dispatch allowlist には加えない。

### B-3 — 既定履歴と `--range` の両方が境界テストで固定されていない

- severity: **Medium**
- real/refuted: **real**
- file:line: [plan.md:66](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/plan.md:66)、[check_ai_provenance.py:247](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:247)
- 影響: plan は「既定履歴監査**または** post-epoch range」としている。どちらか一方しか拒否 positive-control を持たないため、他方で epoch 適用が蒸発する変異をテストが受理できる。
- 最小修正: 同じ synthetic history に対して、pre-epoch `--range` は rc=0、post-epoch `--range` は rc=1、引数なし既定履歴も rc=1、`--message-file` は正負双方、を別々に固定する。

### B-4 — D96 用の外延 matrix が宣言した境界を固定し切っていない

- severity: **Medium**
- real/refuted: **real**
- file:line: [plan.md:20](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/plan.md:20)、[plan.md:50](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/plan.md:50)、[decisions.md:4275](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/docs/decisions.md:4275)
- 影響: bullet/quote を本文扱いで受理する選択、CAB 値・email 構文を検査しない選択、同一値の重複を件数で扱う選択がテスト表に明示されていない。worker が装飾形を過剰拒否したり、値検査や set 比較を入れても境界テストを通し得て、D96 が要求する機械受理集合が固定されない。
- 最小修正: bullet/quote の受理・拒否を段4で裁定し正例または負例を追加する。さらに Git が認識する `Co-Authored-By: not-an-email` の受理、同一値 CAB の contiguous 重複受理、同一値の本文側＋最終 block 分断拒否を固定する。

### B-5 — 「一度だけ parse」の全 consumer 配線が未記載

- severity: **Low — nit/backlog**
- real/refuted: **real**
- file:line: [plan.md:24](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/plan.md:24)、[check_ai_provenance.py:175](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_ai_provenance.py:175)
- 影響: `validate_message()` 後に `validate_implementation_author()` が再度 parse する現 consumer を変更しなければ、計画の「一度だけ」は成立しない。安定した Git 設定下では受理集合への直接影響はなく、主に余分な subprocess と設定変更 race。
- 最小修正: parsed map/value を implementation-author 検査にも渡すか、「一度だけ」の主張を撤回する。

### B-6 — 予算 registry、living-doc、9,000境界、headroom の疑い

- severity: **None**
- real/refuted: **refuted**
- file:line: [check_docs.py:38](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/check_docs.py:38)、[plan.md:77](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/plan.md:77)、[test_check_docs.py:2085](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/orchestrator/tests/test_check_docs.py:2085)
- 影響: なし。`docs/ai-provenance.md` は既に `LIVING_DOCS` と `_ENUMERATED_DOCS` に含まれる。plan は独立 registry を `all_limits` と budget-governed 集合へ加え、allowlist 外を literal pin し、9,000 exactly と9,001拒否を実体で検査する。実測サイズも8,817 bytes、headroom 183 bytesで一致した。置換対象の現行14〜19行だけで677 bytesあり、追記でなく置換・縮約する方針は実行可能。
- 最小修正: なし。plan の consumer 一式を省略せず実装する。

### B-7 — 全層呼出しと D97 scope 外 closure の疑い

- severity: **None**
- real/refuted: **refuted（B-3 のテスト不足を除く）**
- file:line: [operations.md:91](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/docs/dev-wave/operations.md:91)、[task_run_check.py:15](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/tools/task_run_check.py:15)、[decisions.md:4298](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/docs/decisions.md:4298)、[plan.md:101](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423/output/insights/2026-07-29_t153e-t15423-review-verbatim/plan.md:101)
- 影響: なし。`DW-O17` は既に message-file と commit 後監査を要求し、task-run は既定履歴 checker を消費する。D97 は T-153(e) を明示的に scope 外としており、plan は D97 を改変せず新 D98 と同一変更の境界テストで別途閉じる。worklog でも T-153(e) と T-154(2)(3) が未完として残り、phase3 に架空 checkbox はない。
- 最小修正: D98・実装・境界テストが同一 commit になるまで `[T-153]` / `[T-154]` を完了扱いにしないこと。

## 総括

**NO-GO。** must-fix は4点です。第一に、raw/parsed 件数一致を ambient Git trailer 設定から隔離し、alias・追加 separator による相殺 bypass を閉じること。第二に、brief の `SELF_LIMITS` 直接追加を段4で明示的に覆し、独立 registry を採用すること。第三に、`--message-file`、引数なし既定履歴、明示 `--range` の三経路すべてへ正負の境界テストを置くこと。第四に、bullet/quote、値構文非検査、同一値重複をD98と境界テストで明示し、D96の同時更新義務を実質化すること。これらを直せば、living-doc集合、budget consumer、9,000/9,001境界、8,817+183 bytes、D97 scope外だったT-153(e)の別変更closureについてはGOにできる。