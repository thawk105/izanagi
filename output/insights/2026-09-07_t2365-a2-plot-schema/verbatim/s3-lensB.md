## 総括

plan は現状のまま採用不可。最も重い反証は、計画中の attempt `t2364-20260907a` がすでに実投入され、2 workload とも condition-gate receipt の `RENAME_NOREPLACE` が Lustre 上で `EINVAL` となり、49s / 52s・`driver_rc=2` で終了していること。  
新 ID に替えるだけでは同じ箇所で再失敗するため、producer `.py` の最小修正が必要である。  
さらにこの attempt は旧 policy SHA `42bfee…`・base HEAD `cf4273f…` で投入されており、単位 B 後の policy とは一致しない。  
receipt chain が preregistration の policy byte hash を照合しないため、別木から collect すると新 policy を後付けできてしまう。これは動作はするが provenance が成立しない。  
修正後、単位 B を含む固定 detached tree から新 ID `t2364-20260907b` で取り直すべきである。pytest は実行していない。

## 所見

1. **主張:** condition-gate receipt の公開処理は、実際の durable filesystem では走らない。producer `.py` の編集を避ける計画は成立しない。

   **file:line の根拠:** condition receipt は [`_write_condition_gate_admissions_x`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:978) から [`_atomic_write_bytes_noreplace`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:939) を呼ぶ。同 helper は [`_rename_noreplace` の `EINVAL` を処理しない](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:945)。対照的に directory materialization は [`EINVAL` fallback を明示実装済み](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:4521)。実走 stderr は [rr5:1](/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2364-20260907a/jobs/rr5/scheduler/job.stderr:1) と [rr50:1](/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2364-20260907a/jobs/rr50/scheduler/job.stderr:1) でともに `Errno 22`、同 :14 は Elapse 49s / 52s。compute result も [rr5](/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2364-20260907a/jobs/rr5/compute-result.json:1)・[rr50](/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2364-20260907a/jobs/rr50/compute-result.json:1) とも `driver_rc=2`。

   最小ハンクは `:939-953` の file publish だけに、`EINVAL` 時の同一 directory・create-only hard-link publish と staging unlink を追加するもの。既存 destination を置換しない collision 負例と、注入 `EINVAL` 正例が必要で、materializer の directory fallbackをそのまま流用してはいけない。

   **放置したときの成果物への影響 1 行:** raw cell・manifest・certification・図・results 節が一つも生成されない。

   **nit か:** nit ではない。実走で再現済みの blocker。

2. **主張:** `tracked_destination` は receipt chain に束縛されておらず、現在の `t2364-20260907a` を単位 B 後の木から collect すると「旧 policy で投入、新 policy を certification に埋込み」という後付けが通る。

   **file:line の根拠:** preregistration は [`policy_sha256` を記録する](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:873) が、参照箇所は submitter の [`attempt_root` / `current_pin` 読出し](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/pegasus/submit_paper_story_a2_certification.sh:111) だけで、policy hash は照合しない。submission の exact fields [`:1201-1205`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:1201)、completion [`:1563-1567`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:1563)、acquisition [`:1689-1695`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:1689)、raw manifest [`:3723-3731`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:3723) はいずれも `policy_sha256` / destination を持たない。collect は実行木の policy を再読込し [`:4639-4642`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:4639)、その policy の destination と bytes を使う [`:4452-4468`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:4452)。

   現物の [preregistration](/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2364-20260907a/preregistration.json:1) は旧 SHA `42bfee…`、[submission](/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2364-20260907a/receipts/submission.json:1) は source commit `cf4273f…`。したがってこの attempt を新 policy の正式な取り直しとして再利用してはならない。

   **放置したときの成果物への影響 1 行:** `certification.json.policy_sha256` / `policy_bytes_base64` と公開先が、投入時 policy ではなく collect 時 policy を表す偽の provenance になる。

   **nit か:** nit ではない。今回の実 attempt に該当する。

3. **主張:** detached submit tree と開発中 wave tree の分離自体は成立するが、plan の command は wave worktree から投入しており、親の「そこで実装を継続する」と両立しない。

   **file:line の根拠:** submitter は起動 script から `REPO_ROOT` を固定する [`submitter:6-10`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/pegasus/submit_paper_story_a2_certification.sh:6) と、それを `IZANAGI_A2_REPO_ROOT` として qsub へ渡す [`:238-244`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/pegasus/submit_paper_story_a2_certification.sh:238)。job はその木の HEAD/clean を検査する [`job body:230-239`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/pegasus/paper_story_a2_certification.sh:230) うえ、compute preflight でも再検査する [`producer:4576-4587`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:4576)。finish/collect 時も submission receipt の `submission_cwd` にある job-body bytes を読む [`:1223-1232`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:1223)。

   一方、`collect --repo-root` は materialization 先にしか使わない [`:4452-4458`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:4452)。よって collect の Python は固定 submit tree から起動し、`--repo-root` だけ開発 wave tree に向ければよい。開発 wave tree は投入後も編集可能。固定すべきなのは submit tree である。

   **放置したときの成果物への影響 1 行:** job 開始前の HEAD/clean 検査または finish/collect の job-body hash 照合で落ち、成果物が公開されない。

   **nit か:** nit ではない。

4. **主張:** `t2364-20260907a` は再投入不能で、新 attempt ID が必要。失敗時の再利用条件は plan より厳密に切り分ける必要がある。

   **file:line の根拠:** attempt root は [`mkdir(..., exist_ok=False)`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:821)、submitter は preregister を必ず再実行する [`submitter:231-233`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/pegasus/submit_paper_story_a2_certification.sh:231)。job 側も既存 compute-result を拒否する [`job body:46-49`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/pegasus/paper_story_a2_certification.sh:46)。`t2364-20260907a` には root・submission・両 compute-result がすでに存在する。

   再利用可能なのは、preregister 前の引数/queue/path 検査失敗、または terminal 未到達で finish-group が receipt/manifest を一つも作る前に止まった場合。collect は publish 前なら staging cleanup [`:4530-4532`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:4530) 後に再提示できるが、destination 公開後は再利用できない。

   **放置したときの成果物への影響 1 行:** 古い raw/receipt と新しい測定を混ぜずに取り直す経路がなくなり、submit が直ちに失敗する。

   **nit か:** nit ではない。

5. **主張:** 段 6 で広い plotter 変異を登録すると、単一理由への帰属が成立しない。

   **file:line の根拠:** plan が同時に追加する current positive・schema cross・closure・receipt・token・caption test は [plan:72](/home/SFC/tanab/.claude/jobs/3ecec6be/tmp/codex/dev-wave-t2365-a2-plot-schema/s2-plan.md:72)。したがって、次の変異は複数 node を同時に赤にすると予想される。

   - current schema routing 全体の削除・legacy への統合
   - current 12-file closure 検査全体の削除
   - condition receipt parser/admitted 検査全体の削除
   - receipt/raw/WAL/cert の src_token 共通検査全体の削除
   - CLI explicit pin の構築・再現 argv 反映をまとめて削除

   単独登録するなら、より狭い比較式や一つの schema pair、特定 receipt field、特定 token edge 単位へ分割すべきである。producer の `EINVAL` fallback 削除は、注入 `EINVAL` 正例だけに照準すれば単一 node 化できる。

   **放置したときの成果物への影響 1 行:** 複数の受理条件を同時に失う変異を「一つの検査が殺した」と誤認し、新 schema の誤受理が図の値・caption・参照 closureへ入る可能性が残る。

   **nit か:** nit ではない。変異証拠の帰属条件に関する所見。

## pin 閉包の全列挙

| 検索軸 | 一致・意味 | 宛先変更で赤になるか | planとの差分 |
|---|---|---:|---|
| live destination literal | [policy:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.v2.json:9) | 編集対象 | 列挙済み |
| test fixture destination | [test:984-991](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/tests/test_paper_story_a2_certification.py:984) | ならない。fixture が明示上書きする | 列挙済み。更新は parity 用 |
| policy raw SHA-256 `42bfee…c897e` | [test:1767-1770](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/tests/test_paper_story_a2_certification.py:1767) の2 assertion | 同一 node が赤 | 列挙済み。新値 `67dce5a7…0487` も独立再計算一致 |
| protocol SHA-256 `136b823e…d9f4` | [test:1771-1772](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/tests/test_paper_story_a2_certification.py:1771) | ならない | 列挙済み。不変更で正しい |
| `Policy` dataclass identity | raw bytes hash は [`:551-557`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:551)、protocol preimage は [`:290-301`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:290) | bytes hash のみ変化 | 追加 pin なし |
| campaign/dataclass-derived identity | `campaign_preimage` は protocol hash を使用 [`:728-752`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:728)、CampaignConfig digest は [`:2934-2961`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:2934) | ならない | 追加 golden なし |
| policy file 全体 SHA / git blob | SHA-256 は上記 `42bfee…`、git blob は `90d04a1ee0996bf68aeaa7a3f9495392c4cd4caf` | blob ID の grep hit はゼロ | 取りこぼしなし |
| policy path literal | [one-shot cost probe:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/pegasus/probes/t1683_rr5_cost_probe.py:21) | ならない。destination を読まない | plan の grep 列挙から漏れているが actionable pin ではない |
| frozen producer consumer | [plotter defaults:40-41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:40)、[producer test:4019-4027](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/tests/test_paper_story_a2_certification.py:4019)、[plot test:400-407](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/tests/test_plot_a2_certification.py:400) | ならない。旧 frozen artifact を読む | plan の「旧成果物参照は不変」で正しい |
| frozen figure/results/path refs | `docs/paper-story/figures/*`、`docs/paper-story/results/*`、run README、archive/decisions | ならない | 全て履歴・凍結参照。編集不可 |
| study / role 名 | [`paper-story-a2-certification` → `paper-a2-cert`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:319)、[job body:6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/pegasus/paper_story_a2_certification.sh:6)、job-contract fixtures | ならない | 追加張替え不要 |
| xdist group | 対象 test file 内に handwritten marker なし。conftest に対象 file/function の登録 hit なし | ならない | 追加 pin なし |
| generic `tracked_destination` accesses | producer `Policy` property/loader/materializerと materialization tests | 値を動的に読むので赤にならない | 追加張替え不要 |

plan に対する live pin 閉包の差分は、非 pin の one-shot probe path 1 件だけ。実際に張り直す live golden は、planどおり同一 test node 内の SHA assertion 2 箇所である。

## 投入手順の検算

まず失敗済み `t2364-20260907a` を、submit tree を更新する前に terminal receipt で閉じる。更新後では job-body hash が一致しなくなる。

```bash
cd /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2365-a2-plot-schema/submit-tree

tools/pegasus/submit_paper_story_a2_certification.sh \
  finish-group \
  --attempt-id t2364-20260907a
```

これは失敗 attempt の completion/acquisition を作るだけであり、collect は実行しない。

producer の `EINVAL` 修正と policy destination 変更を含む新しい固定 HEAD を submit tree に配置した後、新 ID で投入する。`t2364-20260907b` は調査時点では未存在だが、実行直前に再確認が必要。修正済み HEAD の値はまだ存在しないため埋められない。

```bash
cd /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2365-a2-plot-schema/submit-tree

tools/pegasus/submit_paper_story_a2_certification.sh \
  --attempt-id t2364-20260907b \
  --ccbench-root /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2365-a2-plot-schema/submit-tree/external/ccbench \
  --dependency-prefix-source /work/1/SFC/tanab/izanagi-a2-deps
```

両 path 引数は必須。[submitter:166-169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/pegasus/submit_paper_story_a2_certification.sh:166) で片方でも空なら preregister 前に exit 2 となる。その場合だけ同 attempt ID を再利用できる。CCBench root は patch checkout の元となり [`producer:599-604`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:599)、patch 済み `variant_root` で src_token を解決する [`:3434-3450`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:3434)。dependency source は job-local scratch へ複製される [job body:281-301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/pegasus/paper_story_a2_certification.sh:281)。

terminal 後:

```bash
cd /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2365-a2-plot-schema/submit-tree

tools/pegasus/submit_paper_story_a2_certification.sh \
  finish-group \
  --attempt-id t2364-20260907b
```

collect も同じ固定 submit tree の Python/policy から起動し、materialization 先だけ wave worktree にする。

```bash
cd /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2365-a2-plot-schema/submit-tree

python3.10 -B -m orchestrator.campaign.paper_story_a2_certification \
  collect \
  --attempt-root /work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2364-20260907b \
  --current-pin 511c953 \
  --acquisition-receipt /work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2364-20260907b/receipts/acquisition.json \
  --repo-root /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema
```

投入元への実装要求は次のとおり。

- submit tree HEAD は投入時に確定し、その tree は collect 完了まで tracked clean・同一 HEAD・同じ job-body bytesを維持する。untracked file は検査対象外。
- `external/ccbench` は実 directory・非 symlink、HEAD `511c9538e4e8efa54b45cda62e72389ed3b706ec`、tracked clean。親 gitlink も現物では同 commitで、`git submodule status` の先頭は空白だった。
- dependency source は実 directory・非 symlink。
- scheduler 出力は attempt 配下の `jobs/<rr5|rr50>/scheduler/` に置かれる。`job.stdout` / `job.stderr` は qsub `-o/-e`、`qsub.stdout` / `qsub.stderr` は投入診断、`allocation-qstat.*` は job 内 reservation evidence。
- 開発 wave worktreeは投入から collect の間も編集してよい。ただし collect の実行コード/policyには使わず、`--repo-root` の materialization 先としてのみ使う。
- submit tree を削除・更新した後に別木から collect することは不可。receipt validation が記録済み `submission_cwd` の job body を再読するためである。
- 技術的には別木の policy でも protocol hashが同じなら通ってしまうが、所見 2 の provenance 不成立を起こすため採用しない。

所要見積り:

- policy 上限: workload ごとに 6時間。2 request は独立。
- 1 workload の実処理: condition-gate prebuild 1回、2 cell × trace-enabled/performance build、各 cellで legacy correctness 1回 + full-scale correctness 5回 + trace-disabled bench 5 sample。
- 2 workload 合計: condition prebuild 2回、cell 4個、correctness 24回、bench 20 sample。build は cellごとに trace/performance の2系統。
- 過去の完走実測は rr5 3671s、rr50 3594s [run README:20-21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/output/insights/2026-08-28_t2022-a2-certification-run/README.md:20)。今回の pre-campaign gate は失敗地点まで約50sだった。
- queue 待ちを除く見積り: workload 当たり約1.0〜1.2時間。並走時の外側経過も約1.0〜1.2時間、直列なら約2.0〜2.4時間。hard cap は各6時間。
- queue 待ち込み: `max(queue_i + service_i)`。今回の観測例は rr50 約13s、rr5 約321sだが、将来値は保証できず上限も実装されていない。

## 親 brief の実測の検算

| brief の主張 | 判定 | 現物 |
|---|---|---|
| plotter は旧 schema と凍結 SHA を固定し、CLI では変更不能 | **real** | schema は [plotter:28-30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:28)、SHA は [`:34-37`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:34)。parserに hash option はなく [`:530-536`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:530)、Python `main(expected_hashes=...)` のみ [`:538-547`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:538)。brief の `33-37` は schema 行としてはずれている |
| 既定 measurement root / certification / manifest が旧 attempt 固定 | **real** | [plotter:38-41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:38) |
| `GATE_NOTE` が D1198 未適用を固定表示 | **real** | [plotter:43-44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:43)。新版に使えば偽 caption になる |
| producer schema は cert v4 / full manifest v4 / raw v3 | **real** | [producer:46-60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:46) |
| materialize は既存 tracked destination を拒否する | **real** | [producer:4448-4456](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:4448) |
| canonical policy は A-2/A-6 の2本だけ | **real** | [producer:304-316](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:304) |
| destination/base は protocol preimage 外で、policy byte hashだけ変化 | **real** | [producer:290-301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:290)。置換後 SHA `67dce5a785dfc52d5df9b773f7a65905a030b7bd61ab7706704e2ed8e85a0487` を read-only pipe で独立再計算し一致 |
| plotter test は frozen hash/path/caption を pin | **real** | [plot test:400-407](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/tests/test_plot_a2_certification.py:400) と [`:432-443`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/tests/test_plot_a2_certification.py:432) |

brief の「段 1 の実測」に結論上の refuted 項目は見つからなかった。行番号の軽微なずれと、policy SHA assertion が1値・2 siteである点だけ補正が必要である。