# 段 6 review 1 本の逐語 (gpt-6-astra、read-only)

原文: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2796-docs4/codex/review-out.md` (12302 bytes、sha256 `8d32b264cbddabfa142c3875cbb800a36921f3147c85d8c0162e9ca19904f7ee`)。
可逆最小正規化: 行末の空白・tab を除去 (35 行)、末尾 newline を保証。可視文字は不変。復元は原文 file を読む。

---

## 所見

以下の相対 path は、指定 worktree `W=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2796-docs4` 基準。

1. **real / must-fix — PIN の取得元が投入対象 checkout に固定されていない。**

   対象: `tools/pegasus/README.md:380–385`。
   一次資料: `tools/pegasus/p3_s4_loop_pegasus.sh:213–234`。job body は `cd "$repo"` 後に PIN を import するが、追記のコマンドは現在 directory の module を読む。手順 (1) は別 checkout からも呼べるため、(2) の実行場所は自明ではない。

   対案: PIN 取得例を `(cd "$REPO_ROOT" && python3 -B -c 'from orchestrator.campaign.p3_s4_loop import PIN; print(PIN)')` に置換する。PIN の読み方自体は、値の転記を避けるため残す。

   **放置の影響:** 操作者が別世代の PIN へ submodule を切り替え、投入対象が要求する PIN と不一致になって job body の rc=2 を踏み得る。

2. **real / must-fix — 4 照合の入力相互の束縛が明文化されていない。**

   対象: `docs/phase3-s4b-runbook.md:143–147`。
   一次資料: `orchestrator/campaign/p3_s4_loop.py:1597–1630,1293–1306`、`knowledge_manifest.py:490–505,575–613`、verbatim の D2172 項 9。

   CLI は**同じ resolved manifest**から cfg の knowledge level／manifest SHA、campaign ID、receipt、projection を作る。現文の各 bytes 一致検査だけでは、照合した identity と、今回 `planner_context_payload` に渡す cfg・projection が同じ組立てに属することを明示していない。`planner_context_payload` は cfg と projection の SHA 一致を検査するが、保存 `campaign.lock` との一致は検査しない。

   対案: 4 照合の前に次を追加する。

   > 同じ検証済み manifest から受領証と射影を生成し、その knowledge level と manifest SHA を束縛した、今回 context へ渡す cfg から campaign identity の preimage と ID を再計算する。ID が選択した campaign に対応することを確認したうえで、以下を照合する。

   **放置の影響:** 保存 campaign の identity だけを別途照合し、異なる cfg で context を組み立てても、列挙された照合を満たしたと判断して送付し得る。

3. **real / nit — CLI emit 経路が呼ぶ関数の説明が一つ多い。**

   対象: `docs/phase3-s4b-runbook.md:140–142`。
   一次資料: `orchestrator/campaign/p3_s4_loop.py:2965–3011`、`output/insights/2026-09-19/k2-loop-round3/README.md:31–34`。

   `k2_next_generation_inputs` は round 3 の入力組立てで使うが、CLI emit 分岐では呼ばない。

   対案:

   > login では `k2_critic_diagnosis_from_bytes` → `planner_context_payload` で context を作り、`k2_next_generation_inputs` で完全入力 2 本へ診断を組み込む（round 3 の形）。

   **放置の影響:** 関数の呼出し順自体は正しいが、CLI の出力が完全入力 2 本まで含むと誤読させる。

4. **real / nit — `[T-548]` を staging 導入の根拠とする説明は一次資料で裏付けられない。**

   対象: `docs/b10-backoff-static-tail-submission.md:27`。
   一次資料: `docs/decisions.md:9655–9694`（D200）、同 file:55556（T-548 = D200）、`tools/pegasus/b10_backoff_grid.sh:499–540`。

   D200 は gflags／glog の source path を home 外へ移す裁定であり、現在の checkout 内 hydrate staging の導入を述べていない。carry の文面とは一致するが、来歴としては弱い。

   対案: 括弧内を「現行 job body の前提」に置換する。

   **放置の影響:** 現行の投入操作は変わらないが、参照先から staging 前提の成立経緯を確認できない。

5. **real / nit — 実測記録の手順化・再掲を削れる。**

   対象: `docs/phase3-s4b-runbook.md:146,148`、`docs/b10-backoff-static-tail-submission.md:32–33`。
   一次資料: round 3 insight:35–40、verbatim の D2172 項 9・entry 1690。

   対案:

   - `knowledge-input.json` は「前巡 insight の `materials/knowledge-input.json`」と明記する。現文も「前巡の記録」と限定しており、campaign root 内と断定する誤りではない。
   - 「照合した各bytesのsha256を当該job rootへ残す」は削除するか、記録例として書く。裁定は照合を要求しており、この保存形式までは指定していない。
   - attempt 1 の日付・job 数・秒数は削り、「投入 script は staging を login で検査しない ([T-2794])」を残す。実測値自体は逐語と一致する。

   **放置の影響:** 操作者に不要な保存作業を課し、必要な投入前条件を過去の経緯の中から拾わせる。

6. **real / nit — 任意指定の説明を例と後半にも揃えるとよい。**

   対象: `docs/pegasus-runbook.md:898–904,1021–1028`。
   一次資料: `tools/dev_wave_wait.py:1676–1682,3101–3110,3841–3849`。

   fence に指定例があること自体は「任意」と矛盾しない。ただし、後半の message file 分離義務は指定する場合の話である。

   対案: fence の直前に「message file を明示する場合の例」と添え、後半を「**待ち手へ message file を渡す場合は、親の merge 用 file と別にする。**」へ置換する。「旧機構の記述であり…」は現行説明と重複するので削除できる。1096 行の「渡す場合は」は妥当。

   **放置の影響:** 省略可能な利用者にも、待ち手用 file の作成が必須と読まれる余地が残る。

7. **real / nit — submodule 初期化の環境前提を、tool の自動処理と区別する。**

   対象: `tools/pegasus/README.md:381–382,385–386`。
   一次資料: `tools/dev_wave_submodule_init.py`、`tools/dev_waves/git_state.py:645–701`、`.gitmodules`。

   helper は `.git/modules` を自動選択せず、設定済み URL が絶対 path／`file://` であることを要求する。今回の共有設定は実際に `/work/1/SFC/tanab/izanagi/.git/modules/external/ccbench` であり、指定された登録 worktree での手順は成立する。

   対案:

   > 主 repo の submodule URL がローカル `.git/modules` を指す既存設定を利用し、file transport を明示許可して再帰初期化する。

   また「superproject 側は tracked clean のまま」は「job body の submodule 除外付き tracked-clean 検査を満たす」に置換する。通常の status では gitlink 差が表示され得る。

   **放置の影響:** 他の設定でも helper が URL を補うと誤認し、`nonlocal-url` で止まる可能性がある。今回の環境では操作上の問題はない。

8. **refuted / nit — (P1) 2 経路を書くことは正しい。**

   対象: `docs/pegasus-runbook.md:1018–1020`。
   一次資料: `tools/dev_wave_wait.py:217–221,613–625,3080–3110,3785–3790,3836–3849`。

   指定 path が regular file でない場合の `merge-message-preflight` は rc=2、behind 判明後の複製失敗 `merge-message` は既定 rc=70。carry の「後者だけ」に戻す必要はない。読取不能（decode 失敗を含む）・`AI-Agent:` 行欠落・temp 書込不能も実装に対応する。

   対案: 2 経路を維持し、「止まるのは次の 2 経路だけ」を「**message の事前確認・複製で止まる経路は次の 2 つ**」と限定する。他の merge／provenance 停止まで否定しないための任意修正。

   **放置の影響:** 2 経路の説明による誤操作はない。指定 file 不在時の claim 前停止を正しく予測できる。

## 検算の記録

必読の射影 file はすべて読めた。巨大 file の全文読取、書込み、commit、push、pytest、build、測定は実施していない。

読取範囲:

- 文書5件: `docs/phase3-s4b-runbook.md:131–157`、`docs/b10-backoff-static-tail-submission.md:1–34`、`docs/pegasus-runbook.md:893–905,1015–1028,1096–1097`、`tools/pegasus/README.md:331–400`、`.claude/commands/next-tasks.md:25–36,170–178`。
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2796-docs4/verbatim/rulings-and-carries.md` と同 directory の `HANDOFF.md`: 全文。
- `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-09-19-k2-loop-round3-same-job-stock-control.md`: 全文。
- `output/insights/2026-09-20/t2796-docs-carry4/README.md:1–100`（§1を含む）、`output/insights/2026-09-19/k2-loop-round3/README.md:29–54`。
- `orchestrator/campaign/p3_s4_loop.py:133–146,1237–1328,1597–1630,2965–3011`。
- `orchestrator/campaign/knowledge_manifest.py:490–550,575–640`、`projection_guard.py:385–400`、`site_policy.py` の指定定数検索。
- `tools/pegasus/b10_backoff_grid.sh:495–560`、`fetch_third_party.py` の指定検索および `50–78,93–106,143–156,621–635`。
- `tools/dev_wave_wait.py:217–221,613–625,1676–1682,3080–3110,3785–3790,3836–3875`。
- `tools/pegasus/p3_s4_loop_pegasus.sh:12–18,214–255` と `cd` の位置検索。
- `tools/dev_wave_submodule_init.py`、`.gitmodules`、`/work/1/SFC/tanab/scripts/next_tasks_wave_impl_diff.sh`: 全文。
- 追加確認: `tools/dev_waves/git_state.py:377–438,645–745`、`orchestrator/campaign/silo_ladder_rung1.py:68–72`、`docs/decisions.md:9655–9694` と T-548 の対応検索。

実行 command と要点:

- `git diff 371674ea6 HEAD -- <対象5文書>`: docs 4 件の追記と next-tasks の差分を確認。
- `git diff -- tools/pegasus/README.md`: 未 commit の登録 worktree 前提の追記を確認し、working tree 文面をレビューした。
- `git rev-parse --short=9 HEAD`: `d6014c943`。
- `git ls-tree HEAD .claude/commands/next-tasks.md` と `git ls-tree ac0e5d4be .claude/commands/next-tasks.md`: ともに blob `ff5fe7afa0c2db02da3539ea0fb73ed1a22b52fd`。
- `rg -n 'thirdparty|gflags|glog|staging' tools/pegasus/submit_b10_backoff_grid.sh`: 該当なし。指定された投入 script の staging 検査追加は確認されない。
- `git config --get submodule.external/ccbench.url`: 主 repo の `.git/modules/external/ccbench` を指すローカル path。
- PIN の検索と `git ls-tree HEAD external/ccbench`: ともに `511c9538e4e8efa54b45cda62e72389ed3b706ec`。
- `sed -n '377,386p' tools/pegasus/README.md | rg -n 'tools/pegasus'`: 該当なし。追記に admission registry 向けの新 path はない。
- 自発的に探した `orchestrator/campaign/identity.py` と `tools/dev_waves/submodule*.py` は不在。検査は継続した。

一致した項目:

- login 定数、許可 site 集合、admission と emit の順序、tripwire の実在。
- round 3 の3関数の順序、4照合の実測記録、T-2796 の対応。round 1 の実測は指定一次資料中の参照を確認した範囲。
- staging の既定 path、gflags／glog の exact HEAD・clean 検査、stage 名、`fail 2`、attempt 1 の3 job・5秒。
- message 省略時の `merge main`／`role=integrator`、停止2経路の順序と rc。
- 登録された detached worktree を helper が受理する構造、job body の expected HEAD・submodule 除外 clean・PIN 検査。追記は「現在も gitlink と PIN が不一致」とは主張していない。
- `<tools>` の定義と用法、script の merge-base 算出と `git -C "$d" diff "$mb"`、取り込み元との blob 一致。
- 項7の文体は既存列挙に整合。横断文書へのマシン固有絶対 path の新規混入、経路改修・投入側検査追加の要求はない。

## 総括

**must-fix 2 件、real の nit 5 件、refuted 1 件（nit 扱い）**。レンズ A では主要な名前・値・停止経路は一致するが、PIN の取得元と、直呼び時の cfg・manifest・campaign の束縛を明確にする必要がある。

レンズ B では「親が行う照合」と明記されており、新しい機械 gate の宣言にはなっていない。実測経緯の再掲、SHA 保存形式の義務化、任意指定の説明は簡素化できる。
