## 監査判定

計画はそのままでは採用不可です。最大の問題は、`verify_done` の欠測を正式走全体で 7 件と数えていることです。7 件は「実際に `build_start` した 49 attempt に条件づけた不足」であり、正式 campaign の予定 grid 全体では 73 件の完了記録がありません。

静的検査のみ実施し、ファイル変更・commit・pytest 実走は行っていません。

## 過大射程 1 — 「予定 294・欠測 7」は正式走全体の分母ではない

- **所見:** `49 build_start × 6 = 294` は事前の予定数ではなく、実際に開始した attempt 数に条件づけた事後的分母である。4 campaign は各 15 variant を予定しているため、全 4 attempt の予定枠は `4 × 15 × 6 = 360`、`verify_done=287` との差は 73。最終の workload 別 3 attempt だけを数えても `270 - (90+85+22) = 73` となる。7 は、そのうち開始済み 2 attempt 内の不足だけで、read-heavy の未開始 11 variant、66 枠を除外している。
- **根拠:** `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/docs/b10-backoff-shape-preregistration.md:339-429` は 3 workload、各 15 point、`legacy+performance` を登録する。`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/orchestrator/campaign/b10_backoff_shape_sweep.py:2899-2929` は各 workload で全 `genomes()`、15 variant を `run_campaign` へ渡す。read-heavy WAL は `build_start=4 / commit=3 / verify_done=22`。これに対し brief `:3`、measurements.md `:17-20`、s2-plan.md `:37,103` は 294 を「予定」としている。
- **成果物への影響:** completeness disclosure が正式 grid の欠測を 73 から 7 へ過小表示し、3 workload 系列の完成度を過大に見せる。
- **推奨対応:** 3 分母を分離する。正式 3 workload の最終 attempt は `197/270`、4 campaign 全体の履歴は `287/360`、開始済み 49 attempt 内だけなら `287/294` で「追加の完了記録なし 7」と書く。成果物の表題も「欠測 7」ではなく「開始済み attempt 内の 7 完了枠」に限定する。

## 過大射程 2 — `verify_done` 不在から「実行されなかった」は導けない

- **所見:** WAL に反復開始イベントがないため、7 枠を「未実行」と断定できない。証明できるのは「`verify_done` 完了記録がない」「認証に到達していない」までである。
- **根拠:** `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/orchestrator/campaign/pipeline.py:1365-1381` は反復を起動するが start record を書かず、`:1484-1502` で verifier 完了後に初めて `verify_done` を emit する。balanced WAL 最終行 129 は 11:00:56 の legacy 完了だが scheduler は `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions/f4aa966444a33e90af5131f79c4a67ca/scheduler.stderr:12-16` で 11:02:16 終了。read-heavy WAL 最終行 33 は 06:52:31 の performance 完了だが、scheduler は `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions/9b304374f905603052929a9d629f956b/scheduler.stderr:12-16` で 06:56:55 終了している。次反復の途中だった可能性を排除できない。
- **成果物への影響:** 「実行されなかった反復」と「検査を通った反復」の分離が、開始状態を捏造する形で崩れる。未完了反復へ serializable 等を付けてはいない点は正しい。
- **推奨対応:** brief、insight、worklog fragment の「未実行」をすべて「`verify_done` 完了記録なし」「未完了または未開始、判別不能」へ置換する。未完了枠について verdict、anomaly、integrity の主張をしない。

## 過大射程 3 — P1-1 の「一切限定しない」は文字どおりには成立しない

- **所見:** 45 record 自体の保存済み真偽は欠測で降格しない。一方、3 workload、正式 grid、公式 confirmatory certification まで含む「射程を一切限定しない」は refuted である。s2-plan の「狭義支持、広義限定」が正しい。
- **根拠:** provenance の `.records` は write-heavy、request `965564.nqsv`、45/45 が `correctness_certified=true / missing=false`。同じファイルの top-level `.official_certification=false`、`:5433-5518` では balanced/read-heavy が `pairs=0, status=indeterminate` である。brief `:24-26` は「一切限定しない」とする一方、s2-plan `:83-88,94` は row truth と cross-workload 推論を分離している。
- **成果物への影響:** 45 record の局所的事実が、公式 3-family 結論へ誤移送される。
- **推奨対応:** 「欠測は保存済み 45 record の各 field を変更しない。しかし 45 record は元から 1 workload・1 request の記述的成果であり、正式系列の完全性や他 workload の認証を担わない」と書く。

## 過大射程 4 — M13 は spec 単独ではなく、束縛済み実装との合成で成立する

- **所見:** 「他が揃っていても、この 7 完了枠だけで balanced/read-heavy の 2 族が indeterminate」は結論としては成立するが、spec の字義だけからは導けない。欠けた verify repetition を、3 block の performance cell の `correctness-not-certified`／missing へ写像する実装契約が別途必要である。
- **根拠:** preregistration `:460-486` は「任意の unusable pair で family indeterminate」を定める。しかし attempt と cell の写像は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/orchestrator/campaign/b10_backoff_shape_sweep.py:2430-2460` の「COMMIT 済み attempt だけを certification とする」、`:2950-3015` の「認証なしなら `correctness-not-certified`、cell は missing」、`:1733-1781` の family 判定で初めて閉じる。さらに測定時の analysis binding は campaign.lock の `analysis_commit=0a07481...`、`analysis_code_sha256=34072f...` で、現行ファイル全体の SHA-256 `94d2cb...` とは異なる。
- **成果物への影響:** 反実仮想が事前登録された規則だけの帰結であるかのように見え、規律 7 の測定時実装と現行実装の分離を失う。
- **推奨対応:** 「発効 spec と、そこへ束縛された analysis implementation の合成では」と条件を明記する。実際の provenance の 2 族 indeterminate は 18 pair 全欠落による事実、7 枠だけの話は反実仮想として別段落に置く。

## 過小射程 1 — `certified` の要求条件を 4 項に縮めている

- **所見:** worklog 1189 の `certified` 定義は過小である。また generic verifier の `certified` 自体は witness が両方未指定でも通り得るため、`observed==expected` は B-10 pipeline を含めて説明する必要がある。
- **根拠:** `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/orchestrator/verifier/model.py:158-174` の `Integrity.clean()` は orphan、version duplicate、duplicate txid、genesis commit、missing txid、write-version mismatch、malformed key、framing、lock coverage、write intent、permutation、commit witness をすべて連言にする。`:209-227` はさらに `n_txns>0` と `serializable` を要求する。witness は `expected/observed` が両方 `None` でも clean だが、B-10 pipeline は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/orchestrator/campaign/pipeline.py:1434-1475` で witness 存在と batch count 0 を先に要求して expected count を verifier に渡す。verbatim-worklog-1189.md `:7-10` は observed equality、txid、framing、orphan の 4 条件だけを exhaustive に見える形で列挙する。
- **成果物への影響:** 保存済み認証を降格はしないが、正しさゲートの実際の強度を文書上弱く説明し、規律 2 の理解を損なう。
- **推奨対応:** 既存 entry は変更せず、新 insight の追記訂正へ「4 項は代表例であり全条件ではない」を加える。測定 campaign.lock の verifier blob SHA は現行 `model.py/core.py/parse.py` と exact 一致しているため、この点は測定時実装にもそのまま適用できる。

## 過小射程 2 — P1-2 は variant と attempt の帰属先を過少に数える

- **所見:** 「欠測 2 変種が入る集計は 238 回帰だけ」は refuted。unit を分けると、観測済み workload-specific attempt は 287 aggregate に入り、同じ genome-derived variant ID は 45 write-heavy records に各 3 件入る。未完了の 7 枠そのものはどの集計にも入らない。
- **根拠:** balanced WAL `:127-129` には `c7c331ebe662` の legacy 1 件、read-heavy WAL `:28-33` には `292d58f1dad8` の legacy 1＋performance 3 件がある。provenance `:992,2072,2720,3800,4232,5312` には同じ 2 ID が write-heavy record として各 3 件ある。238 performance-tag aggregate に入るのは read-heavy の 3 件だけで、balanced は 0。s2-plan `:62-77,95` の matrix はこの点を正しく修正している。
- **成果物への影響:** variant ID、workload-specific attempt、未完了 repetition を混同し、下流帰属を欠落させる。
- **推奨対応:** s2-plan の matrix を採用する。ただし「未実行」は前記どおり「完了記録なし」へ直す。

## 証拠誤記 — M7/M14 の `git grep` 0 件は再現しない

- **所見:** Fig2b/Fig2c が別 campaign 系列という中核結論は正しいが、「正式走識別子は docs のどこにもない」「検索 0 件」は false。
- **根拠:** `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/docs/archive/worklog-phase3-0902-1186.md:8-10` に `e3de15eb`、`965564.nqsv`、45 cell が存在する。対して Fig2b provenance は `backoff-sweep-*`、Fig2c provenance は `b10-backoff-grid-*-sweep-*` を入力にしており、formal 4 campaign は参照しない。
- **成果物への影響:** 図の非帰属判定自体は変わらないが、その補助証拠が再現不能になる。
- **推奨対応:** `docs` 全体の grep 0 件という文を削除し、Fig2b/Fig2c の provenance field 不一致だけを根拠にする。

## P1-3 — real、ただし結論の語を狭める

- **所見:** balanced 5 枠は壁時計、read-heavy 2 枠は壁時計ではない、という原因分離は real。read-heavy の技術的理由を追加推測しない方針も正しい。
- **根拠:** balanced scheduler `:2,12-16` は `Exceeded per-req elapse time limit`、SIGKILL、remaining 0。read-heavy scheduler `:1-2,12-16` は SIGTERM の痕跡、elapsed 20950 秒、remaining 22250 秒。formal-run insight `:68-72,147-152` はユーザー裁定による撤去を記録する。
- **成果物への影響:** entry 1189 の「7 件すべて壁時計」は訂正が必要だが、保存済み verifier verdict は変化しない。
- **推奨対応:** 「検査による reject ではない」を「WAL に検査 reject は記録されておらず、完了しなかった直接の外因は scheduler termination」と限定する。「未実行」とは書かない。

## 規律 2・3・7 の監査

- **所見:** 既存 bytes を変更する提案や正しさゲートを緩める提案は見つからなかった。規律 2 と規律 3 は計画上維持されている。規律 7 の append-only 方針も正しいが、追記内容が上記の分母・開始状態・`certified` 定義まで覆っていない。
- **根拠:** brief `:11-16`、s2-plan `:108,119-132,150,160-162` は未完了枠を certified としないこと、既存 insight/worklog bytes を変更しないことを明記する。WAL の `payload.certified`、commit witness、verdict は実行時 signal であり、後付け signal ではない。
- **成果物への影響:** 現在の追記案だけでは entry 1189 のより重い誤りが残り、規律 7 による訂正が不完全になる。
- **推奨対応:** entry 1189 自体は変更せず、新 insight と新 worklog fragment の追記に、294 の条件付き分母、未開始／途中の判別不能、`certified` の完全な意味を含める。

## M1〜M14 の独立検算

- **所見:** 数値の大部分は一致したが、M1/M3 の全体化、M7/M14 の grep、M9 の「唯一」、M13 の spec 単独帰結は成立しない。
- **根拠:**
  - M1: stage 数 `15/15/15/90`, `15/15/14/85`, `15/15/15/90`, `4/4/3/22` は一致。294 を全予定とする解釈は不一致。
  - M2〜M6: variant、genome、タグ内訳 `legacy=49 / performance=238`、read-heavy commit 数、45 record／15 distinct attempt、空 directory は一致。
  - M7: Fig2b/Fig2c の別系列は一致。`docs` grep 0 件は不一致。
  - M8/M10: scheduler 時刻、21609/0 秒、20950/22250 秒、壁時計原因の分離は一致。反復が一度も開始されなかったことは確認不能。
  - M9: `75+75+70+18=238`、read-heavy constant-mu2 の 3 件だけが入る点は一致。「唯一の下流集計」は不一致。
  - M11: 4 build attempt ID と workload 間の差は一致。
  - M12: `official_certification=false`、2 族 `pairs=0/indeterminate`、write-heavy `18/testable/not-detected` は一致。
  - M13: spec と束縛済み実装を合わせれば反実仮想は成立。spec 単独では不足。
  - M14: 2 図の provenance は一致。識別子検索 0 件は不一致。
- **成果物への影響:** 確認済み数値を維持できる一方、分母と一般化を直さないと completeness と provenance の主張が誤る。
- **推奨対応:** 新 insight に「検算済み」とだけ一括記載せず、上記の条件付き分母と不一致項目を明示する。

## 信頼境界

- **所見:** 参照した WAL、campaign.lock、provenance、scheduler／qstat 出力から、読み手へ指示を出したり既存指示を無視させたりする文字列は検出しなかった。WAL の `perf_configure_cmd`／`perf_build_cmd` は実行可能な command 文字列だが、provenance data としてのみ扱い、実行していない。
- **根拠:** 公式出力 root と submissions root 全体を、`ignore previous`、`system prompt`、`follow instructions`、日本語の指示・無視・実行要求相当で静的検索し該当 0。scheduler.stdout は build log、stderr は scheduler 会計と shell error だった。
- **成果物への影響:** 信頼境界由来の成果物汚染は確認されない。
- **推奨対応:** command field は insight へ転載する場合も引用データとして扱い、手順として再掲しない。

## 総括

- 最も重い所見 3 件:
  - 「予定294・欠測7」は開始済み attempt に条件づけた数で、正式 grid 全体では完了記録なしは 73。
  - `verify_done` 不在から「一度も実行されなかった」は導けず、未開始か途中終了か判別不能。
  - `certified` は記載された 4 条件より強く、B-10 pipeline 固有の witness gate と全 `Integrity.clean()` 条件を含めて追記訂正する必要がある。

- P1 判定:
  - P1-1: **refuted**。45 record の row truth に限れば real だが、「一切限定しない」は広すぎる。
  - P1-2: **refuted**。287 aggregate と 45 write-heavy records への帰属を落としている。
  - P1-3: **real**。balanced は壁時計、read-heavy は壁時計ではない。ただし「未実行」ではなく「完了記録なし」とする。

- 親が段 4 で必ず裁定すべき点:
  - 7 を正式走全体の欠測数として扱うのを止め、197/270、287/360、287/294 のどの母集団を本文に置くか。
  - 「未実行」を全面的に「未完了または未開始、判別不能」へ直すか。
  - entry 1189 の append-only 訂正へ、壁時計と variant wording に加え、分母と `certified` 定義の訂正も含めるか。
  - M13 を spec 単独帰結ではなく、発効 spec と measurement-time analysis implementation の合成として書くか。
  - M7/M14 の false な `git grep` 0 件を根拠から外すか。