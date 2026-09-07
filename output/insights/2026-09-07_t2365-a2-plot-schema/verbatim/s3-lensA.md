## 総括

最重大所見は、CLI で対象 bytes と期待 hash を同じ呼び手に選ばせるため、bytes pin が恒真化することである。  
旧 certification の `status` だけを書き換えて再計算した hash を渡せば、偽の outer status を図と provenance に掲載できる。  
他の旧検査には概ね新版側の対応物があるが、この authority 低下だけで plan は現状のまま採用不可。  
`GATE_NOTE` も確認できるのは「admitted と記録された receipt」であり、D1198 の実行・通過そのものではない。  
静的検査のみで、pytest は実行していない。

## 所見

1. **CLI bytes pin は独立した pin ではなく、呼び手による自己申告になる**

   **主張:** `--certification-sha256` と `--raw-manifest-sha256` に任意値を渡せる設計は、P1-2 を構文上しか守らない。対象ファイルから算出した hash をそのまま渡せば常に一致するため、旧 CLI 経路の受理集合も広がる。新 digest は repo-owned の固定値・固定 pin 台帳など、対象入力と独立した authority に束縛する必要がある。少なくとも legacy profile では CLI override を受け付けてはならない。

   **file:line の根拠:** plan は hash の key set・書式しか制約せず、CLI 値をそのまま `expected_hashes` にする（[s2-plan.md:20](/home/SFC/tanab/.claude/jobs/3ecec6be/tmp/codex/dev-wave-t2365-a2-plot-schema/s2-plan.md:20)、[s2-plan.md:22](/home/SFC/tanab/.claude/jobs/3ecec6be/tmp/codex/dev-wave-t2365-a2-plot-schema/s2-plan.md:22)）。比較処理は渡された期待値との単純な等価比較である（[plot_a2_certification.py:92](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:92)、[plot_a2_certification.py:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:98)）。現行 CLI は固定 digest だけを使用する（[plot_a2_certification.py:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:34)、[plot_a2_certification.py:530](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:530)、[plot_a2_certification.py:538](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:538)）。

   具体例は、凍結 legacy certification の `status` を `reject` から `observed-positive` に変更し、そのファイルの SHA-256 を `--certification-sha256` に渡す入力である。`status` は文字列であることしか検査されず（[plot_a2_certification.py:274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:274)）、effect から outer status を再導出しない。その値は caption と図へ転記される（[plot_a2_certification.py:330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:330)、[plot_a2_certification.py:404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:404)）。したがって plan の「任意の legacy bytes pin でも旧受理集合は広がらない」という説明（[s2-plan.md:31](/home/SFC/tanab/.claude/jobs/3ecec6be/tmp/codex/dev-wave-t2365-a2-plot-schema/s2-plan.md:31)）は refuted。

   P1 判定は、P1-1 と P1-4 は守られているが、P1-2 は意味論上不成立。P1-3 も、独立 pin がない限り「成果物由来」ではなく「呼び手が選んだ bytes 由来」に落ちる。

   **放置したときの成果物への影響 1 行:** 改変 legacy/current 入力に自己計算 hash を添えるだけで、偽の status・条件・provenance を持つ図を publish できる。

   **nit かどうかの自己申告:** nit ではない。plan 採用を止める correctness blocker。

2. **`GATE_NOTE` が証明できるのは receipt の記録内容まで**

   **主張:** plan の loader は「D1198 が実際に実行され、通過した」とは検査できない。言えるのは「manifest-bound の canonical record が `use_class="paper"` / `admitted=true` と記録している」までである。plan の caption 案を厳密に receipt 観測として書くなら成立するが、総括の「D1198 適用済みを導出する」は過剰主張である。

   **file:line の根拠:** live producer は supply/meaning records を実測して gate を呼ぶ（[paper_story_a2_certification.py:616](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:616)、[paper_story_a2_certification.py:682](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:682)）。しかし永続化されるのは admission canonical record と source evidence で、元の supply/meaning records は保存されない（[paper_story_a2_certification.py:978](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:978)、[paper_story_a2_certification.py:987](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:987)）。再読時の検査も canonical form、key set、`paper`、`admitted=true` に限られ（[paper_story_a2_certification.py:962](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:962)）、policy 順に位置対応させるだけである（[paper_story_a2_certification.py:1069](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:1069)）。manifest による bytes 束縛は存在する（[paper_story_a2_certification.py:3984](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:3984)、[paper_story_a2_certification.py:4044](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:4044)）が、これは記録の完全性であって gate の再実行ではない。

   **放置したときの成果物への影響 1 行:** caption が「receipt は admitted と記録する」を「D1198 を実施し通過した」に一般化し、論文図に証拠より強い主張を載せる。

   **nit かどうかの自己申告:** nit ではない。caption の事実性に直結する。

3. **独立 bytes authority 以外に、旧経路から落ちる検査は見つからなかった**

   **主張:** plan を記載どおり実装する前提では、旧検査には次の対応物がある。片側だけなのは「固定された bytes authority」であり、所見 1 の CLI 化によって失われる。

   **file:line の根拠:**

   | 旧経路で効く検査 | 旧実装 | 新版 plan の対応 |
   |---|---|---|
   | 固定 bytes pin | [plotter:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:34)、[plotter:95](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:95) | [plan:20-22](/home/SFC/tanab/.claude/jobs/3ecec6be/tmp/codex/dev-wave-t2365-a2-plot-schema/s2-plan.md:20) は caller-selected。対応物なし |
   | exact schema 組 | [plotter:104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:104) | [plan:15-18](/home/SFC/tanab/.claude/jobs/3ecec6be/tmp/codex/dev-wave-t2365-a2-plot-schema/s2-plan.md:15) |
   | study/attempt/protocol/current-pin identity | [plotter:271](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:271) | [plan:56](/home/SFC/tanab/.claude/jobs/3ecec6be/tmp/codex/dev-wave-t2365-a2-plot-schema/s2-plan.md:56) |
   | exact closure と各外部 bytes hash | [plotter:133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:133)、[plotter:175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:175) | [plan:33-41](/home/SFC/tanab/.claude/jobs/3ecec6be/tmp/codex/dev-wave-t2365-a2-plot-schema/s2-plan.md:33) |
   | cell order、build attempt、variant、genome、samples、条件 | [plotter:146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:146)、[plotter:190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:190) | [plan:29](/home/SFC/tanab/.claude/jobs/3ecec6be/tmp/codex/dev-wave-t2365-a2-plot-schema/s2-plan.md:29)、[plan:58](/home/SFC/tanab/.claude/jobs/3ecec6be/tmp/codex/dev-wave-t2365-a2-plot-schema/s2-plan.md:58) |
   | median/CV/effect 再計算 | [plotter:225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:225)、[plotter:252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:252) | [plan:60](/home/SFC/tanab/.claude/jobs/3ecec6be/tmp/codex/dev-wave-t2365-a2-plot-schema/s2-plan.md:60) |
   | toolchain 同一性 | [plotter:284](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:284) | [plan:58](/home/SFC/tanab/.claude/jobs/3ecec6be/tmp/codex/dev-wave-t2365-a2-plot-schema/s2-plan.md:58) の「legacy 全項目」 |
   | request/claim/campaign/time | [plotter:293](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:293) | [plan:61](/home/SFC/tanab/.claude/jobs/3ecec6be/tmp/codex/dev-wave-t2365-a2-plot-schema/s2-plan.md:61) |
   | correctness 回数・全 cell certified | [plotter:306](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:306) | [plan:62](/home/SFC/tanab/.claude/jobs/3ecec6be/tmp/codex/dev-wave-t2365-a2-plot-schema/s2-plan.md:62) |
   | failure 時の無出力 | [plotter:474](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:474)、[plotter:546](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:546) | [plan:13](/home/SFC/tanab/.claude/jobs/3ecec6be/tmp/codex/dev-wave-t2365-a2-plot-schema/s2-plan.md:13) |

   P1-1 は新 destination/fresh leaf 方針（[s2-plan.md:74](/home/SFC/tanab/.claude/jobs/3ecec6be/tmp/codex/dev-wave-t2365-a2-plot-schema/s2-plan.md:74)）、P1-4 は full schema 限定（[s2-plan.md:15](/home/SFC/tanab/.claude/jobs/3ecec6be/tmp/codex/dev-wave-t2365-a2-plot-schema/s2-plan.md:15)）として守られている。

   **放置したときの成果物への影響 1 行:** この一覧の検査から追加の値変化は見つからないが、bytes authority 欠落だけで一覧全体を自己整合した偽入力に対する保証へ弱体化できる。

   **nit かどうかの自己申告:** nit ではない。負の検算結果を含む correctness 境界の棚卸し。

4. **plan の `cert status="bound"` は実在しない field 名として読める**

   **主張:** `bound` は certification の top-level `status` ではなく、各 cell の `source_binding_status` である。実装指示では exact field path を明記すべきである。

   **file:line の根拠:** plan は「cert status=`bound`」と書く（[s2-plan.md:59](/home/SFC/tanab/.claude/jobs/3ecec6be/tmp/codex/dev-wave-t2365-a2-plot-schema/s2-plan.md:59)）。producer の top-level status は `observed-positive`、`reject`、`indeterminate`、`performance-indeterminate`（[paper_story_a2_certification.py:4242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:4242)）。`bound` が入るのは cell の `source_binding_status`（[paper_story_a2_certification.py:2594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:2594)、[paper_story_a2_certification.py:4249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:4249)）。

   **放置したときの成果物への影響 1 行:** 文言を literal に実装すると全 current certification を拒否し、新 attempt から図を生成できない。

   **nit かどうかの自己申告:** nit ではない。実装不能または誤 field 検査につながる。

## 親 brief の実測の検算

1. **real** — schema 定数、固定 SHA-256、旧 default path/root は [plotter:28-41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:28)。CLI に hash 引数はなく、差し替え口は `expected_hashes` kwargs だけ（[plotter:530](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:530)、[plotter:538](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:538)）。

2. **real** — `GATE_NOTE` と caption の D1198 文は固定値（[plotter:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:43)、[plotter:344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:344)）。

3. **real** — producer の current schema は cert v4、full manifest v4、cell v3（[producer:46-60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:46)）。

4. **real（コード側）／policy 値は射影内だけでは未確定** — materialize の fresh-leaf 拒否は実在する（[producer:4453-4456](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:4453)）。ただし live policy JSON 自体は必読射影に含まれないため、「現行 policy が旧 destination を指す」という後半を独立には検算できない。

5. **real** — `canonical_policy_path` は A-2/A-6 の二つだけを列挙し、それ以外を拒否する（[producer:304-316](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:304)）。

6. **real** — `_protocol_preimage` に `tracked_destination` も `durable_measurement_base` も含まれない（[producer:290-301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:290)）。したがって destination だけの変更では protocol hash は変わらず、raw policy bytes hash は変わる（[producer:551-556](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:551)）。brief が挙げる別 test の exact golden 行は射影外なので未検算。

7. **real** — test は `CANONICAL_SHA256` の dict 等価を要求し（[test_plot_a2_certification.py:400-407](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/tests/test_plot_a2_certification.py:400)）、landed provenance の caption が README に存在することも要求する（[test_plot_a2_certification.py:432-443](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/tests/test_plot_a2_certification.py:432)）。

## scope 外だが返すべきもの

裁定パッケージ候補: **新 attempt の consumer integration を誰が、どの新規 path で所有するか。**

brief は新しい図一式と新しい日付の results 節を成果物に含める（[s1-brief.md:70-73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/output/insights/2026-09-07_t2365-a2-plot-schema/s1-brief.md:70)）一方、plan の所有範囲と手順は plotter、policy、attempt collect までで、図名・results file・figures README 登録・closure 実行の担当がない（[s2-plan.md:175-180](/home/SFC/tanab/.claude/jobs/3ecec6be/tmp/codex/dev-wave-t2365-a2-plot-schema/s2-plan.md:175)）。

repo closure 関数自体は path 非依存で新 provenance にも利用できる（[plotter:508-528](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:508)）が、landed bundle test は旧 `fig5_a2_certification_reject` だけを対象にする（[test_plot_a2_certification.py:432-443](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/tests/test_plot_a2_certification.py:432)）。旧 bytes を変えず、新しい dated results file・新しい figure prefix・README entry・その closure test を一組にする裁定が必要。