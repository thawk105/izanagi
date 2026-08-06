結論は **NO-GO** です。brief v1 のまま段 4 で採用・実装へ進めてはいけません。中心となる 7,787 M / 4,027 M は同じ母集団・同じ時間窓の値ではなく、105,774 tok/tool、Bash 47%、context 内訳、effort の因果解釈にも実在する誤りがあります。

Pegasus ログインノードなので、入力上限のない約 1.1 GB の全量再集計と pytest は走らせていません。bounded な生ログ標本・全ファイル metadata・既存正本を照合し、`check_docs.py` だけ実走して現行 baseline の `rc=0` を確認しました。

## 1. 計測の妥当性

### 母集団と「6日間」— real / must-fix

Claude 側は [analyze_v2.py](/work/1/SFC/tanab/dev-wave-jobs/token-hygiene/analyze_v2.py:14) が `/work/1/.../izanagi` に対応する単一 project dir をハードコードし、mtime 上位 N 本を選ぶだけです。request timestamp による 2026-08-01〜08-06 の filter はありません。

現時点の同じ mtime 窓では次の差があります。

- script が見る dir: 102 root transcript / 245,161,013 bytes
- Izanagi の main・旧 checkout・worktree 全体: 165 root transcript / 389,127,025 bytes
- 旧 `/home/SFC/tanab/github/izanagi` だけで 38 本 / 94,456,972 bytes

したがって 7,787 M は「Izanagi の Claude 6日総量」ではなく、単一 encoded cwd の subtotal です。mtime で選んだ後にファイル全履歴を足すため、古い session の再開では窓前 usage まで入り、窓内 turn だけの切り出しにもなりません。さらに 20 応答未満を全除外する [filter](/work/1/SFC/tanab/dev-wave-jobs/token-hygiene/analyze_v2.py:98) が短い session を落とし、平均 context を上方に歪めます。

Codex 側も [filename の開始日だけ](/work/1/SFC/tanab/dev-wave-jobs/token-hygiene/analyze_codex.py:13)で選び、event timestamp の下限・上限を見ません。`~/.codex/sessions` 全体に cwd/originator filter もありません。対象 949 rollout の metadata には `codex_exec` 944 本だけでなく TUI 5 本が含まれ、5 本とも usage を持ち、入力は計 1,312,282 tokens でした。「937 子」は少なくとも 5 本過大です。

放置時の壊れ方: 異なる checkout・親 TUI・窓外 usage を同じ「子の6日消費」として最適化し、誤った effort policy を worker 契約へ入れます。

### requestId dedupe — 一部 real、一部 refuted

「sidechain を親と二重計上」は、確認できた現行形式では **refuted** です。逆に root glob が `subagents/*.jsonl` を拾わず、未計上です。8月4日の nested subagent 4本だけで、global requestId dedupe 後に以下が欠落しています。

- 87 requests
- 入力 5,548,966 tokens
- 出力 63,208 tokens

また「同 requestId の usage は完全複製」という前提も普遍ではありません。生ログでは同じ requestId の先行 block が `output_tokens=1`、後続最終 block が `247` という例がありました。[最初の record を採る実装](/work/1/SFC/tanab/dev-wave-jobs/token-hygiene/analyze_v2.py:65)は再帰的に sidechain を読む新 report では出力を過小計上します。最終 record、または整合性検査付き最大累積値が必要です。

加えて bounded 標本の一つには、`model="<synthetic>"`・usage 全ゼロの rate-limit error requestId が9件あり、現コードは応答数へ数えます。

### Codex `total_token_usage` — refuted、ただし窓集計には不十分

この疑いは狭い意味では **refuted** です。生 rollout で `total_token_usage` は `last_token_usage` を加えながら単調増加する累積値でした。したがって一つの rollout 全期間なら「最後の有効値」を採るのは正しいです。既存の [codex_worker_ledger.py](/work/1/SFC/tanab/izanagi/tools/codex_worker_ledger.py:475) も累積・増分を別々に検査し、non-monotonic、compaction、abort を記録しています。

ただし暦窓の集計には最後の累積値を使えません。窓内 `last_token_usage` の和、または境界累積差が必要です。開始前 session の再開、終了後まで続く session、欠損した最終 event を区別する必要があります。

### context 曲線・内訳 — real / must-fix

旧 `analyze_base.py`、`analyze_context.py`、`analyze_cmds.py` は requestId dedupe をしておらず、block 分割数を turn として数えています。compaction を扱わないため、総入力 traffic は足せても「固定 base + 単調な会話蓄積」という感度モデルは成立しません。46,641 は「初回 request の入力中央値」であり、user brief・attachment を含むので固定 base ではありません。

さらに [analyze_v2.py](/work/1/SFC/tanab/dev-wave-jobs/token-hygiene/analyze_v2.py:80) は `assistant:tool_use` に加算した同じ block を `in:<tool>` に再加算し、その両方を [分母](/work/1/SFC/tanab/dev-wave-jobs/token-hygiene/analyze_v2.py:135)へ入れています。33.5% / 26.8% / 17.9% / 2.0% は二重計上された文字数比で、token 比でも traffic 寄与でもありません。早期 block は後続 request で何度も再読されるため、単純な transcript 文字数比から input-token 寄与は出せません。

なお指定リスト外に `analyze_blocks.py` も実在し、同じ tool_use 二重計上を持っています。「全スクリプト」の再現性にも欠落があります。

### Codex の「tool 1回 105,774」— real / must-fix

[analyze_codex.py](/work/1/SFC/tanab/dev-wave-jobs/token-hygiene/analyze_codex.py:44) が数えるのは `token_count` event、すなわち観測 model call です。tool call ではありません。1 model call が複数 tool を出す場合も、最終 text だけの場合もあります。

そのうえ 105,774 は「子入力の中央値 ÷ model-call件数の中央値」という ratio-of-medians で、同じ session の比ですらありません。既存 ledger の docstring が明示するとおり model call から logical turn/tool call を推測してはいけません。

### effort 比較 — real / must-fix

供給された `analyze_codex.py` は effort 別件数しか出さず、入力 share 63.2%、中央値比 2.02 / 2.05 / 1.44 を計算するコードがありません。したがって数値は supplied scripts から再現不能です。

仮に数値自体が正しくても、現契約は plan/consult=max、author=high なので stage・難易度・turn 数と effort が交絡しています。1.44倍の model-call 数を含む集団の総入力が2.02倍でも、effort の因果効果とは言えません。

放置時の壊れ方: 誤った「max は因果的に2倍」という前提をテストへ凍結し、品質差を測らず production routing を変更します。

## 2. 一般化の飛躍

297,806 は [総和÷応答数](/work/1/SFC/tanab/dev-wave-jobs/token-hygiene/analyze_v2.py:118)の算術平均で、20応答以上の限定標本です。中央値・分位・stage別分布ではありません。

独立 tool A/B を束ねると中間 request は消えますが、残る request の context、tool result の到着時点、後続分布も変わります。したがって「1本消すたび常に30万」は介入後不変の換算率ではありません。baseline の記述統計としてのみ表示し、節約量は before/after で再計測すべきです。

`cache_read + cache_creation + input` は Anthropic が定義する request の総 input tokens としては妥当です。この狭い疑いは **refuted** です。しかし費用ではありません。cache read は通常 input の0.1倍、5分 write は1.25倍、1時間 write は2倍で、長文 tier もあります。[Anthropic pricing](https://docs.anthropic.com/en/docs/about-claude/pricing)

同様に OpenAI の `input_tokens` は cached tokens を含み、cached はその内数です。公式も費用照合には token usage ではなく Costs endpoint を勧めています。[OpenAI Usage API](https://platform.openai.com/docs/api-reference/usage/completions)

したがって 500:1 は raw token traffic 比としては限定的に使えますが、課金比・subscription 枠比ではありません。「生成量ではない」と断言するには pricing/limit semantics が不足しています。

## 3. P1 / P2 と fix 増幅

### P1「一律 downshift しない」— refuted as a defect

これは臆病な現状維持ではなく、規律2に沿う fail-closed 判断です。現時点で段3・段6を一律 high に落とす根拠はありません。P1 は維持すべきです。ただし、維持するだけでは節約施策にならないので controlled experiment へ送る必要があります。

既に focused review の限定 A/B が存在します。名指しした単一仮説では high/max とも3/3検出し、max の資源量が大きかった一方、replay 未認証で production 根拠にしてはならないと明記されています。[T-181](/work/1/SFC/tanab/izanagi/output/insights/2026-07-30_t181-reasoning-ab/README.md:19)

### P2「段2だけ high」— real / must-fix

これは scope の「引き下げはしない」と直接矛盾します。現行 [DW-S02](/work/1/SFC/tanab/izanagi/docs/dev-wave/workers.md:5) は max なので、high 化は明白な downshift です。

具体的な逆効果経路は次です。

1. high plan が caller・consumer・負例・所有境界を一つ落とす。
2. 段3が発見すれば親の再起草と再相談が増える。
3. 見逃せば段5が狭い実装を作る。
4. 段6で発見され、fix worker、統合、focused review、変異、受入再走が増える。
5. それでも見逃せば correctness defect が land する。

節約できるのは plan 1本の差だけですが、追加巡回は少なくとも review + fix + focused review と親 Claude の往復を生みます。T-181 装置自身も9本の fix artifact と3本の focused review を要しており、下流増幅が実在することは確認できます。ただしこれは P2 の因果証拠ではありません。

歴史 rollout から effort と fix 巡回の因果相関は取れません。stage と effort が交絡し、must-fix は自然言語、重複所見の real/refuted 裁定は後段、wave難易度・review本数・retryも異なるためです。必要なのは同一 brief の block-randomized paired run、blind な段3/6裁定、事前非劣性 margin、全 wave token と escaped mutant の同時計測です。

また stage matrix の production 採用は既に [T-184](/work/1/SFC/tanab/izanagi/docs/phase3.md:722) の所有です。この wave が先回りして P2 を入れるのは ownership 競合です。

放置時の壊れ方: 弱い plan が fix 巡回を増やすか consumer 欠落を通過させ、総消費と certified artifact の正しさを同時に悪化させます。

## 4. 施策(3)の実効性と hooks

「独立 call の並列化」は、この Codex 実行契約には既に存在します。少なくとも Codex には重複です。Claude の内部 system prompt は transcript や公式文書からは監査できず、既存と断言できません。

いずれにせよ 82.8% single-tool は「並列可能だったのに逐次化した率」ではありません。依存する call、tool が一つしかない call、最終 text も混ざります。しかも平均1.12は4+を4へ丸め、toolを持つ応答だけを分母にしています。施策根拠として無効です。

Bash の一般的な出力上限は現行 repo 規律にはありません。[guard_read](/work/1/SFC/tanab/izanagi/hooks/README.md:87) は大きい `Read` を止めますが、Bash 経由は明示的に管轄外です。したがって Bash 規律自体は新規性があります。

ただし47%の classifier は無効です。

- `| sort`、`| uniq`、`| grep` を「reducer」とするが、出力件数を制限しない。
- 先頭の `head -n`、`sed -n`、`rg -m`、`find -maxdepth`、intrinsically small な `git status` を無上限扱いする。
- 比率は call 比でなく tool-result 文字数比。
- command 自身の上限、リダイレクト、tool runtime truncationを見ない。

機械強制については、PreToolUse hook は batching を強制できません。将来の tool call が独立か見えないためです。Bash も任意 program・script・変数展開の出力量を静的には決定できません。

実装するなら次の順です。

- まず PostToolUse 相当で実出力 bytes と「明示上限の種類」を記録する。ただし当該 call の token は既に消費済み。
- PreToolUse は `cat` など既知の大容量 file reader にだけ狭く適用し、一般 Bash を「pipe がない」で拒否しない。
- hook は command/output を規律6上のデータとして扱い、`eval`・実行・出力内指示の解釈をしない。
- correctness 証拠を truncation して偽緑にしないよう、上限超過は「digest + tail/head を再取得せよ」と明示する。
- Codex には hooks が未配線なので、Claude だけの強制を共通防壁と主張しない。

## 5. 正しさ防壁と effort 記録

effort の役割別明示自体は、現行値を固定するだけなら直ちに規律2違反ではありません。しかし「安い既定へ変えるための dashboard」と結びつけば、正しさを token 数で最適化する圧力になります。

worklog へ人手で「実際は high」と書くだけでは恒真です。既に次があります。

- [codex_worker_ledger.py](/work/1/SFC/tanab/izanagi/tools/codex_worker_ledger.py:384): model、実効 effort、token、stage、retry、compaction、不整合
- `codex_worker_launch.py`: requested/served effort と terminal usage の receipt
- `CodexWorkerSessionManifest`: exact session selector

worklog は手書き値ではなく session/receipt digest を参照し、少なくとも stage、artifact hash、served effort、real/refuted finding、fix巡回、escaped mutation を機械的に結び付けるべきです。must-fix 件数だけでは「検出力が高い」と「起草が悪い」「重複報告が多い」を区別できません。

放置時の壊れ方: 実 rollout と違う手書き effort が品質根拠として残り、その偽記録を使って将来の downshift が承認されます。

## 6. scope・成果物影響・docs予算

### 既存実装との重複 — real / must-fix

`tools/token_report.py` の Codex parser は既存の [T-179正本](/work/1/SFC/tanab/izanagi/docs/phase3.md:674) と重複します。新規 tool は ledger/receipt の正規化結果を再利用し、独自の `total_token_usage` parser を持たない設計にすべきです。

Claude 側には次を必須にする必要があります。

- `--since` / `--until` の event timestamp filter
- project dirs の明示列挙または provenance 付き discovery
- root/subagent の包含方針
- global requestId dedupeとusage競合検出
- synthetic/error/incomplete件数
- raw input・cache read/write・outputを別表示
- price versionなしでは「cost」と表示しない

また全 session scan は入力上限なしです。既存 ledgerも [Pegasus上では unknown](/work/1/SFC/tanab/izanagi/docs/pegasus-runbook.md:485) と分類され、login 実行の暫定例外にも token report は含まれません。「read-onlyだからloginでよい」は規律違反です。

放置時の壊れ方: 二つの parser が同じ rollout に異なる値を出し、さらに login node の共有 cgroup を圧迫して受入・監査 process を巻き込みます。

### docs予算 — real / must-fix

現行値は以下です。

- workers: 4,668 / 5,000 bytes
- dev-wave 4 reference 合計: 25,187 / 25,200 bytes
- aggregate の余裕: **13 bytes**

個別 workers には332 bytes余って見えますが、実効 aggregate cap は [25,200 bytes](/work/1/SFC/tanab/izanagi/tools/check_docs.py:254) です。net addition は不可能です。`CLAUDE.md` にはこの byte cap はありませんが、毎応答の base に入るため固定換算率を常設するのは本 wave の目的にも逆行します。

現行 checkoutで `python3 tools/check_docs.py` は `rc=0 / 違反なし`。これは変更前 baseline のみで、実装後の緑ではありません。

### wave 契約の衝突 — real / must-fix

- brief は83行で、[DW-S01の10〜30行](/work/1/SFC/tanab/izanagi/docs/dev-wave/core.md:24)に違反しています。これは nit/backlog 扱いでよいですが、token-hygiene brief 自体が肥大しています。
- P3/成果物形は段6 reviewer 1本としていますが、[DW-S06-A](/work/1/SFC/tanab/izanagi/docs/dev-wave/workers.md:46) は実装 wave に異なるレンズ2本を必須とします。これは must-fix です。
- 「軽量版にしない」と言いつつ段2を省くのも自己矛盾です。
- 受入・実測環境が brief に確定されておらず、DW-S01要件を満たしません。
- `orchestrator/tests/test_token_report.py` は pytest 全走へ自動編入されます。新規 parser test だけでなく、既存 `test_codex_worker_ledger.py` との同値性、progressive usage、window境界、sidechain、synthetic error、compaction/non-monotonic、originator selector の回帰が必要です。

### 「成果物影響なし」— 狭義のみ true

token report 自体に certified artifact への直接 write path はありません。この狭義では正しいです。

しかし workers/CLAUDE の変更は将来の plan・レビュー検出力を変えるため、「一切変わらない」は強すぎます。正しくは「既存 certified artifact に直接の producer/consumer 変更はない。将来の開発成果物には effort routing と出力制限を介した間接的 correctness 影響がある」です。

## 総括

**(a) 判定: NO-GO。** brief v1 を段4で採用せず、測定定義と scope を作り直してから再レビューが必要です。

**(b) must-fix**

1. 母集団を project/worktree/originator と event timestamp で定義し直して再集計する。  
   放置時: 窓外・別 checkout・親 TUI の値で worker policy を決めます。

2. requestId の final usage、sidechain、synthetic error、compactionを扱い、model call と tool call、文字数構成と token traffic、raw tokens と費用を分離する。  
   放置時: 誤った metric が `token_report` のテストで正本化されます。

3. Codex 部は既存 ledger/receiptを再利用し、Pegasusの実行場所・入力上限を scope に入れる。  
   放置時: parserが二重管理になり、login scan が共有 process を巻き込みます。

4. P2の段2 high化を本 waveから外し、T-184所有の paired・blind・非劣性評価へ送る。手書き effort ではなく receipt-linked outcome を記録する。  
   放置時: fix巡回増加または plan defect のescapeで、消費と正しさが同時に悪化します。

5. 固定の30万/10.6万換算率と47%根拠をCLAUDEへ入れず、qualitative invariantと実測可能なtelemetryへ改める。  
   放置時: staleな数値規律が依存callの無理なbundlingや診断証拠の切断を誘発します。

6. 段6 reviewerを契約どおり2本へ戻し、dev-wave aggregateから追加bytes以上の具体的削除を先に指定する。  
   放置時: 必須レビューが1本欠けるか、`check_docs.py` が実装後に赤になります。

**(c) 信用してよい値 / 訂正が必要な値**

- 信用可: Claude 3 input field の和は request の raw total input、Codex `total_token_usage` は rollout累積で最後の有効値は全期間合計、現行 workers の max/high 指定、現行 docs baseline の `check_docs rc=0`。
- 限定付き: 7,787 M と4,027 Mは各scriptの限定 corpus subtotalとしてのみ扱える。projectの6日総量ではない。Claudeには確認済みsidechainだけで最低 +5.549 M input、Codexの「子」にはTUI 5本・1.312 M inputが混入。
- 訂正必須: 297,806を普遍的な1往復費用とする主張、105,774/tool、500:1を費用比とする主張、33.5/26.8/17.9/2.0のcontext内訳、Bash 47%、effort 2.02/2.05/1.44の因果解釈と63.2%の再現性。