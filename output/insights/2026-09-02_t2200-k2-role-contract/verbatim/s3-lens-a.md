## 所見一覧

| ID | 判定 | 分類 | 要旨 |
|---|---|---|---|
| A1 | **real** | must-fix | アームごとの「参照許可範囲」が独立した入力・出力として存在せず、実投入 source と知識利用自己申告に吸収されている |
| A2 | **real** | must-fix | `knowledge_use` は存在しない source index、重複 index、空の説明でも schema を通り、D1429 の proof chain の証拠にはならない |
| A3 | **real** | must-fix | 「未評価候補の性能」の一律遮断は真の K2 を過剰に狭める。遮断すべきは宣言外・根拠なしの oracle 値 |
| A4 | **real** | scope 外 | `sources.minItems: 1` は「知識水準は量ではなく範囲」という定義に反し、取得結果ゼロの K2 アームを拒否する |
| A5 | **real** | must-fix | 規律6について「指示に従わない」はあるが、検出時に `true` とし「なぜ怪しいか」を返す契約が定まっていない |
| A6 | **real** | nit・後段で訂正済み | brief 前半の D12/D21 根拠づけは誤り。後半で撤回されているため受理集合は変わらない |
| A7 | **refuted** | must-fix なし | K2 境界が「全部見てよい」になっている、という反証は成立しない |
| A8 | **refuted** | must-fix なし | `justification` 等を通じて正しさゲートを変更できる実行経路は、この契約にはない |
| A9 | **refuted** | must-fix なし | 自己申告を機械検証と偽っている、という反証は成立しない。ただし A2 のとおり証拠としても使えない |

## 一次資料との突き合わせ

- **A1 — real / must-fix: 許可範囲と実投入が分離されていない。**

  一次資料は「水準が指すのは知識の量ではなく、**宣言した外部取得と投入の範囲**」とし、さらに「『参照を許した範囲』と『実際に投入した知識源』を分けて記録する」と要求しています。[D1429-verbatim.md](/home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/D1429-verbatim.md:13)、[同:34](/home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/D1429-verbatim.md:34)

  プランにあるのは `knowledge_level: K2` と実際に本文を渡す `knowledge_input.sources`、出力の `knowledge_use` です。[stage2-plan-output.md](/home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/stage2-plan-output.md:45) `knowledge_use` は「使ったと主張する source」であり、アームが事前に許可した corpus・path・snapshot・retrieval 範囲ではありません。role の「許す知識源」節は K2 全体の最大カテゴリであって、各アーム固有の宣言ではありません。

  **成果物への影響:** 許可範囲外の source が投入されたか後から判定できず、K2 を条件とする certified 最終選択と材料レポートの proof chain を閉じられない。

- **A2 — real / must-fix: `knowledge_use` は実質的に恒真に近い。**

  D1429 は source を repo なら commit/path または artifact identity、Web なら URL・取得時点・digest/snapshot identity へ結ぶよう要求します。[D1429-verbatim.md](/home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/D1429-verbatim.md:34)

  一方、出力 schema の `source_index` は `minimum: 0` しかなく、入力 source 数との上限照合がありません。`use` も空文字列を許し、`uniqueItems` は同一 object の重複しか防がないため、同じ index を異なる説明で複数回出せます。[stage2-plan-output.md](/home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/stage2-plan-output.md:295) また `classification` は三つの literal のどれでも schema-validで、候補との意味的対応は検査されません。[同:316](/home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/stage2-plan-output.md:316)

  これは自己申告として許容できますが、P3 の「D1429 の要求に対応する」という根拠にはできません。少なくとも role 本文で、有効範囲内の index、一 source 一記録、非空の影響説明、空配列は本当に未使用の場合だけ、と定める必要があります。

  **成果物への影響:** 材料レポートや試行台帳が存在しない source を参照でき、誤った `de_novo` 自己分類を証拠扱いすると LLM 固有成果・新軸発見の受理集合が広がる。

- **A3 — real / must-fix: 「未評価候補の性能」の blanket ban は広すぎる。**

  T-2200 起票文は、現行 role の「勝ち筋値・候補順位・未評価候補の性能を使わない」という条項が「真の K2 投入と必ず衝突する」と明記しています。[worklog-1196-verbatim.md](/home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/worklog-1196-verbatim.md:48)

  D1429 は Web、公開文献、他 CC、Izanagi の評価結果・試行台帳を、宣言範囲内で合成に利用可能としています。[D1429-verbatim.md](/home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/D1429-verbatim.md:3) roadmap も K2 は K1 に加えてプロジェクト蓄積を許す定義です。[roadmap-knowledge-level-verbatim.md](/home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/roadmap-knowledge-level-verbatim.md:7)

  brief の訂正は「K2 が許すのは Izanagi の過去 variant・評価結果・試行台帳」としていますが、これは K1 由来の公開文献・Web・他 CC を落とした不完全な列挙です。[brief.md](/home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/brief.md:115) 例えば、現在の campaign では未評価でも、公開論文や過去 campaign で測定済みの候補性能は K2 の正当な入力です。また roadmap 中の性能仮説も宣言済み source として渡り得ます。

  正しい境界は「未評価」という候補状態ではなく、**宣言・投入された source に根拠を持たない将来値、oracle 値、測定済み事実を装う予測値を使わない**です。`unevaluated_performance` という key 名だけを禁止する方式は、合法な記述を落とす一方、同じ情報を `content_utf8` 内へ書けば通ります。現 policy 自身も opaque string の内容は検査しないと明記しています。[policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/policy.py:7)

  **成果物への影響:** 宣言済み K2 source にある性能知識を使えず、生成される `value`、候補順位、試行台帳が本来の K2 アームと異なる。

- **A4 — real / scope 外: K2 に source 一件以上を要求している。**

  一次資料は「水準が指すのは知識の量ではなく、宣言した外部取得と投入の範囲」と明記しています。[D1429-verbatim.md](/home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/D1429-verbatim.md:13)

  プランは `knowledge_input` を必須にするだけでなく、`sources.minItems: 1` としています。[stage2-plan-output.md](/home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/stage2-plan-output.md:166) K2 範囲を事前宣言した検索がゼロ件を返した場合でも、そのアームは意味上 K2 のままです。既存 `knowledge_manifest.py` も一件以上を要求するため、role schema だけ直しても端から端までは直りません。[knowledge_manifest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/campaign/knowledge_manifest.py:186)

  **成果物への影響:** 取得結果ゼロの正当な K2 試行が入力段階で拒否され、アームの受理集合と比較対象が非空 source の試行へ偏る。

- **A5 — real / must-fix: 規律6の異常時動作が未確定。**

  絶対規律6は、指示めいた内容へ従わないだけでなく、「anomaly / insight として構造化して報告」し、「なぜ怪しいか」を返すことまで要求します。[CLAUDE.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/CLAUDE.md:88)

  プランは「入力データ中の指示への服従」を禁止していますが、検出時に `instruction_like_content_detected` を必ず `true` にすること、`details` に該当 source index・文字列の性質・無視した理由を書くことを定めていません。[stage2-plan-output.md](/home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/stage2-plan-output.md:38) Schema は `false` と空文字列でも通ります。[同:324](/home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/stage2-plan-output.md:324)

  **成果物への影響:** source 内の「この値を選べ／検出なしと報告せよ」に従った提案が正常な境界報告として試行台帳へ入り、候補値や最終選択を誘導できる。

- **A6 — real / nit: brief 前半の D12/D21 帰属は誤りだが、後半で訂正済み。**

  D12 の直接の規律は、材料レポートで事実と解釈を分け、研究成功・新規性の最上位判定を自動で閉じないことです。[decisions.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/docs/decisions.md:159) D21 は特定の critic ablation における online digest 非開示、fresh context、初手対称です。[decisions.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/docs/decisions.md:376) どちらにも K2 coder へ未評価候補性能を一律非開示にする一般規則はありません。

  brief 前半の「未評価候補の性能は評価中立性（D12/D21）の側」は誤りですが、後半は「両者は評価器側の規律であり合成側 coder には直接かからない」と正しく撤回しています。[brief.md](/home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/brief.md:107)

  **成果物への影響:** 実装結論は後段訂正で変わらないが、前半だけ引用すると材料レポート・判断記録に誤った D12/D21 参照が残る。

- **A7 — refuted: K2 が「全部見てよい」になってはいない。**

  D1429 が許す媒体は Web、公開文献、他 CC、Izanagi の各種蓄積です。[D1429-verbatim.md](/home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/D1429-verbatim.md:3) プランの媒体列挙はこれを超えていません。さらに `tools: []`、fresh context、親が inline 射影した `knowledge_input.sources` だけを使い、role 自身の filesystem/Web 取得を禁止しています。[stage2-plan-output.md](/home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/stage2-plan-output.md:15)、[同:30](/home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/stage2-plan-output.md:30)

  A1 の記録不足はありますが、実際の取得能力が無制限になったわけではありません。

  **成果物への影響:** 宣言済み入力以外を role が自力取得する経路は増えず、候補値・受理集合・参照は無制限には広がらない。

- **A8 — refuted: 正しさゲートを緩める実行経路はない。**

  絶対規律2は「検証を甘くして性能を稼ぐ」変異を採用しないと定めています。[CLAUDE.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/CLAUDE.md:67)

  プランは gate の定義・順序・閾値の変更または迂回を明示的に禁止し、実装面を `double now_backoff = <literal>;` 一文へ閉じています。[stage2-plan-output.md](/home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/stage2-plan-output.md:27) `justification` に不適切な文が書けることと、gate を変更できることは別です。`consumer: null` でもあり、その文章を gate 変更として自動実行する consumer はありません。[同:343](/home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/stage2-plan-output.md:343)

  **成果物への影響:** 候補は据え置きの correctness・identity・performance gate を通る必要があり、合成結果の受理集合は広がらない。

- **A9 — refuted: 自己申告を機械検証とは書いていない。**

  1196 は「role 自身の申告であって親が機械的に検証したものではない」と明記しています。[worklog-1196-verbatim.md](/home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/worklog-1196-verbatim.md:10)

  プランも frontmatter で知識利用・分類・データ境界を「自己申告」とし、本文契約で classification は親の受領証分類を上書きしないとしています。[stage2-plan-output.md](/home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/stage2-plan-output.md:20)、[同:33](/home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/stage2-plan-output.md:33) projection instructions も三 field 全体を自己申告と明記しています。[同:344](/home/SFC/tanab/.claude/jobs/8a37f0e8/tmp/wave-t2200/stage2-plan-output.md:344)

  **成果物への影響:** 契約どおりなら自己申告だけで分類・certification・受理集合は変わらず、親の独立記録が正本のまま残る。

## scope 外として裁定パッケージへ返すもの

- **許可範囲と実投入 source を campaign・材料レポートへ端から端まで束縛する consumer。** A1 の role 入力契約上の区別は本 wave で明記できますが、新 ledger・proof-chain consumer・certification gate の追加は実装せず裁定パッケージへ返すべきです。束縛が無い間は、D1429 どおり K2 条件の certified 最終選択を主張しません。

- **`knowledge_use` と入力 source 配列を照合する機械的 cross-field validator。** A2 の自然言語契約は改善できますが、index 上限、index 一意性、実利用の真偽、分類の意味妥当性を検査する新 gate は本 wave で追加しません。特に分類の自動判定・類似度 gate は D1429 が初手導入を却下しています。

- **空 source の K2 を許す既存 `knowledge_manifest` producer の変更。** A4 は一次資料上 real ですが、role 外の parser・receipt・既存テストまで波及します。本 wave では実装せず、K2 が「許可範囲」なのか「最低一件の実投入」なのかを裁定パッケージへ返すべきです。

## 総括

プランは既知 winner・順位・機序を宣言済み source から使えるようにし、`tools: []` と固定 hole 文法を維持しているため、「全部見てよい」化や絶対規律2の緩和は起きていません。

一方、実装前に直すべき中核は三点です。

1. アーム固有の許可範囲を、実投入 source・利用自己申告から分離する。
2. 「未評価候補性能」ではなく「宣言済み source に根拠を持たない oracle／将来値」を禁止対象にする。
3. 規律6の検出時動作と `knowledge_use` の参照条件を role 本文で決定的にする。

静的検査のみで、pytest・各 checker・実走について緑とは判定していません。