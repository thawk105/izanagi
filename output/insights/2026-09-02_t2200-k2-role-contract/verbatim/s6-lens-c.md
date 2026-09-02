## 所見一覧

| ID | 判定 | scope | 所見 |
|---|---|---|---|
| C1 | **real / must-fix** | 本 wave 内の文言修正は可能。実配線は scope 外 | `knowledge_use` の index・重複を「機械検査する」という無限定な記述は、実際の role 出力経路には当てはまらない。検査関数と直接 unit test は存在するが、consumer は未配線である。 |
| C2 | **real / must-fix** | 本 wave 内 | 入力例の `whiteboard` は実 producer と不一致。`direction` / `magnitude` がなく、段 4 で禁止される非 `null` の `delta_pct` を例示している。 |
| C3 | **real / 既知** | 裁定パッケージ | `sources.minItems: 1` は「知識水準は量ではなく範囲」という D1429 と整合しないゼロ取得 K2 を拒否する。段 4 裁定自身も認識済み。 |
| C4 | **refuted** | — | 「source に根拠を持たない性能値」の禁止は段 4 裁定と一致し、未評価候補の測定済み性能まで禁止していない。 |
| C5 | **refuted** | — | K2 の許可・禁止境界は D1429 / roadmap と整合し、正当な K2 知識を一律に落としていない。 |
| C6 | **refuted** | — | `implementation` 契約は兄弟 role と逐語一致し、同じ policy 分岐を通る。正しさゲートを変更する実装経路もない。 |
| C7 | **refuted** | — | `data_boundary_report` の本文契約は、検出時に source index・文字列の性質・従わなかった理由まで要求している。`classification` 等も自己申告だと明示されている。 |
| C8 | **refuted** | — | de novo、LLM 固有寄与、知識因果、K2 条件の certified 最終選択を role 出力だけから主張する契約上の経路はない。 |
| C9 | **refuted** | — | 入力例の `knowledge_input` 部分は実際の `planner_projection()` と一致し、出力例も manifest の required key tree と一致する。 |

## 一次資料・実装との突き合わせ

**C1 — `knowledge_use` の「機械検査」は実出力経路について過大**

段 4 裁定は「index が有効かどうかは機械検査する」と定めています（[stage4-ruling.md](</home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/stage4-ruling.md:103>)）。role 本文も同じ主張です（[coder-v4-autonomous-k2.md](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/.claude/agents/coder-v4-autonomous-k2.md:122>)）。

検査ロジック自体は実在し、範囲外 index と重複 index を拒否します（[policy.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/policy.py:521>)）。直接呼び出す正負例もあります（[test_codex_agents.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/tests/test_codex_agents.py:968>)）。

しかし実出力経路には接続されていません。

- manifest は `consumer: null` です（[manifest.json](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/manifest.json:965>)。
- architecture も「自動 consumer は無く、信頼中核が手で起動する」と明記します（[agent-architecture.md](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/docs/agent-architecture.md:138>)。
- Codex runtime は全件 blocked です（[README.md](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/.codex/agents/README.md:11>)。
- launcher は `validate_input_semantics` だけを import・実行し（[launcher.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/launcher.py:41>)）、出力側は JSON Schema 検証だけです（[events.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/events.py:595>)。

したがって正確な記述は「`validate_output_semantics` を明示的に通した場合は機械検査する」です。実配線を追加しないなら、role 本文と段 4 裁定をこの限定付き表現へ直す必要があります。

成果物への影響: 現状の手動経路では、存在しない／重複した source 参照を伴う提案が拒否されず、材料レポートや試行台帳へ正しい知識参照を結べない。

**C2 — `whiteboard` 入力例が live producer と不一致**

role の例は次の形です（[coder-v4-autonomous-k2.md](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/.claude/agents/coder-v4-autonomous-k2.md:85>)。

- `iteration`
- `result`
- `delta_pct: -1.2`

実 producer は `iteration` / `direction` / `magnitude` / `result` / `delta_pct` の 5 field を出します（[p3_s4_loop.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/campaign/p3_s4_loop.py:701>)）。さらに段 4 では `delta_pct` は常に `None` で、非 `None` は勝ち筋性能チャネルとして fail-closed です（[p3_s4_loop.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/campaign/p3_s4_loop.py:808>)）。

これは既存兄弟 role にもある古い例ですが、新 role の producer 一致という主張には使えません。

成果物への影響: 例どおりの入力は producer で拒否されて試行が成立しないか、producer を迂回すると段 4 が閉じている性能フィードバックを合成入力へ混入させる。

**C3 — ゼロ取得 K2 の拒否**

D1429 は知識水準を量ではなく宣言範囲と定義します（[D1429-verbatim.md](</home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/D1429-verbatim.md:13>)）。一方、producer は source 1 件以上を要求し（[knowledge_manifest.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/campaign/knowledge_manifest.py:186>)）、role schema も `minItems: 1` です（[manifest.json](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/manifest.json:788>)）。

段 4 裁定はこれを正しく裁定パッケージへ送っています（[stage4-ruling.md](</home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/stage4-ruling.md:208>)）。

成果物への影響: K2 範囲を宣言したものの取得結果がゼロだった正当なアームは campaign／試行台帳へ入れない。

**C4・C5 — 知識境界と性能値条項**

role の許可側（[coder-v4-autonomous-k2.md](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/.claude/agents/coder-v4-autonomous-k2.md:31>)）は、D1429 の Web・文献・他 CC・Izanagi 蓄積・失敗／差なしを含む台帳（[D1429-verbatim.md](</home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/D1429-verbatim.md:3>)）と一致します。一般知識、baseline、whiteboard、planner direction の許可も roadmap の最小射影と矛盾しません。

禁止条項 3 は段 4 裁定を意味変更なく反映しています。特に、

- 候補が本 campaign で未評価というだけでは禁止しない
- 公開文献や過去 campaign の測定済み性能は source-bound なら許す
- 禁止対象は根拠のない数値を測定値として扱うこと

まで明記されています（[coder-v4-autonomous-k2.md](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/.claude/agents/coder-v4-autonomous-k2.md:47>)）。

成果物への影響: なし。既知の測定済み候補を K2 合成に使える受理集合を維持し、未根拠の性能値だけを落としている。

**C6 — 絶対規律 2 と兄弟 role の比較**

両 role の `implementation` 条項は逐語一致です。

- ちょうど 1 文
- suffix-free strict C++ numeric literal 1 個
- `value` と数値一致
- comment token、行末 backslash 禁止

既存 role は [coder-v4-autonomous.md](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/.claude/agents/coder-v4-autonomous.md:20>)、K2 role は [coder-v4-autonomous-k2.md](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/.claude/agents/coder-v4-autonomous-k2.md:20>) です。

manifest の proposal schema も同型で、policy は両 role を同じ literal/value 分岐へ通します（[policy.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/policy.py:475>)）。また、K2 role は gate の定義・順序・閾値の変更／迂回を二重に禁止しています。

成果物への影響: なし。K2 化によって executable proposal の受理集合は広がっていない。

**C7 — 絶対規律 6 と自己申告**

本文は指示めいた内容を検出した場合に、次を必須としています（[coder-v4-autonomous-k2.md](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/.claude/agents/coder-v4-autonomous-k2.md:130>)。

- `instruction_like_content_detected: true`
- source index
- 文字列の性質
- 従わなかった理由
- 未検出時も走査範囲

したがって、本文契約上は「常に false」と書くことは適合しません。ただし schema は boolean/string の型しか検査せず、恒常的な `false` や空 `details` も schema-valid です（[manifest.json](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/manifest.json:946>)）。

これは frontmatter がデータ境界を自己申告と明示しており、機械的検出を保証していないため、現契約の偽装ではありません。`classification` と「本当に source を使ったか」も明瞭に自己申告扱いです。なお `use` の非空性も本文規約であり、schema／policy の機械検査対象ではありません。

成果物への影響: 契約どおり自己申告として扱う限り変化なし。機械検証済み証拠として扱えば誤りになるが、その読み方を本文は許していない。

**C8 — 主張境界**

role は強い主張を明示的に禁止し（[coder-v4-autonomous-k2.md](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/.claude/agents/coder-v4-autonomous-k2.md:50>)）、`classification` は親の受領証を上書きしない自己申告としています。同じ境界を設計根拠でも繰り返しています（同:137）。

これは D1429 の「候補単位の gate verdict は有効だが、K2 条件の certified 最終選択は proof chain が閉じるまで不可」（[D1429-verbatim.md](</home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/D1429-verbatim.md:37>)）と一致します。

成果物への影響: なし。`classification: "de_novo"` 単体は自己申告であり、新軸発見・LLM 固有成果・最終選択の証拠にはならない。

**C9 — knowledge projection と出力例**

`knowledge_manifest.planner_projection()` は次の 4 field を返します（[knowledge_manifest.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/campaign/knowledge_manifest.py:344>)。

- `data_boundary`
- `knowledge_level`
- `knowledge_manifest_sha256`
- `sources`

各 source は canonical な `kind` / `identity` / `sha256` に `content_utf8` を加えます。role の `knowledge_input` 例はこの形と一致します。repo source の commit/path 例も live producer が実際に作れる形です。Web は契約上許可されていますが、現 producer の live 解決は未配線で fail-closed です（[knowledge_manifest.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/campaign/knowledge_manifest.py:301>)）。

出力例の 4 top-level field と proposal の 5 field は manifest の required key tree と一致します。`<1-1000>` は既存 role と同じ擬似 placeholder で、source parity checker は形の照合時に `null` へ正規化しています（[check_codex_agents.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/tools/check_codex_agents.py:140>)）。

成果物への影響: `knowledge_input` と出力 key tree については参照ずれなし。C2 の whiteboard 部分だけ修正が必要。

## scope 外として裁定パッケージへ返すもの

- `knowledge_use` の参照整合性を実出力経路へ接続する consumer。新しい配線・gate を追加しない制約により、本 wave では role 文言を限定するところまでとし、実配線は裁定対象に戻す。
- 許可範囲・実投入 source・実利用 source を campaign、材料レポート、試行台帳へ端から端まで束縛する consumer。これがない間は K2 条件の certified 最終選択を主張できない。
- `knowledge_use` の実利用、`classification` の妥当性、`data_boundary_report` の真偽を機械判定する仕組み。現在はいずれも意図的な自己申告であり、D1429 が初手の一般的 leak 判定を却下している。
- source 取得ゼロでも K2 と認めるかという `minItems: 1` の裁定。
- Web source の live 解決。role の許可境界は正しいが、現 producer はまだ Web projection を作れない。

## 総括

判定は **must-fix 2 件**です。

1. `knowledge_use` の「機械検査する」を、未配線である現状に合わせて限定表現へ直す。
2. 入力例の `whiteboard` を live producer の 5 field・`delta_pct: null` に直す。

それ以外の核心契約――K2 の許可範囲、source 非拘束性能値の扱い、兄弟 role と同一の `implementation`、絶対規律 2/6、自己申告性、強い主張の禁止、knowledge projection の形――は一次資料と一致しています。

検査は指定どおり静的に行い、pytest その他のテストは実走していません。