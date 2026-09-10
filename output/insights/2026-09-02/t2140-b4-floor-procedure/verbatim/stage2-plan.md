## 事実確認

- **P1-a — 中核は成立。ただし estimand の表現を精密化すべき。**  
  §5.1.1 は、共通参照点から `gain = throughput / reference_tps - 1` を求め、`|gain_on - gain_off| <= floor` を tie とするため、floor が直接支配する量は 1 槁成の CV ではなく、同一条件を独立に測った 2 側の相対利得差である。[事前登録:383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:383) [事前登録:420](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:420) [事前登録:440](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:440)  
  ただし `|gain_on - gain_off|` は各 null pair の乖離量であり、floor の estimand はその between-run 分布に対する、事前固定した保守的な統計関数と書くのが正確である。現行 driver は session-median の CV を返すだけである。[between_run_floor.py:228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/between_run_floor.py:228) 単純な独立・同分散モデルでも差の標準偏差は単側のおおよそ平方根 2 倍になりうるため、単一構成 CV をそのまま採って保守側になる保証はない。

- **P1-b — sanctioned driver として成立。**  
  `RECORDS`、`THREADS`、`EXTIME` は `p2_2` から import され、測定時にも固定値が直接渡される。[between_run_floor.py:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/between_run_floor.py:50) [between_run_floor.py:202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/between_run_floor.py:202) `SESSION_REPS` も固定され、CLI が選べるのは stock の `silo` / `mocc` と固定 3 workload だけである。[between_run_floor.py:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/between_run_floor.py:58) [between_run_floor.py:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/between_run_floor.py:76) [between_run_floor.py:318](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/between_run_floor.py:318)  
  `measure_point_floor()` 自体は binary、workload、baseline を引数に取るが、B-4 の対象 driver や校正済み `PerfConfig` 全体を受ける入口ではない。したがって現行 CLI をそのまま B-4 floor 測定器として使えない。

- **P1-c — 順序は一部不成立。**  
  `対象 driver と軸 -> 校正済み PerfConfig -> env_tag -> floor` ではなく、推奨順は `対象 driver と軸 + 実行 site -> site resolver 由来 env_tag -> その環境で校正した PerfConfig -> floor protocol freeze -> floor campaign` である。§5.1 自身が driver・site・tag の 3 つ組を要求している。[事前登録:245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:245) 現行 driver も env_tag を測定前に解決し、測定 profile を変えている。[between_run_floor.py:368](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/between_run_floor.py:368) 出力先が `env_scope_dir(env_tag)` 配下である点は P1-c のとおりである。[between_run_floor.py:255](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/between_run_floor.py:255) [layout.py:600](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/layout.py:600)

- **P1-d — 成立。**  
  JSON と Markdown のどちらかが存在すれば `FileExistsError` となる create-only 設計である。[between_run_floor.py:263](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/between_run_floor.py:263) 同一 env_tag、protocol、threads、workload ではファイル名に campaign 識別子が入らないため、同一点の 2 回目を同じ出力 root へ保存できない。

- **P1-e — 成立。**  
  driver は back-to-back セッションを cold-boot・温度ドリフトを含まない下限と明記し、時間窓の異なる genuine cross-campaign データとの最大を人間が確定するとしている。[between_run_floor.py:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/between_run_floor.py:14) [between_run_floor.py:290](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/between_run_floor.py:290) [between_run_floor.py:416](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/between_run_floor.py:416) §5.1 と main experiment も対象別再実測と保守側最大を要求する。[事前登録:215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:215) [main experiment:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-main-experiment.md:57) したがって、連続した 1 invocation だけでは足りない。

## 書き足す内容の骨子

- **発効手続き案 — 誰が**

  - ユーザーが、少なくとも「測定実行者」「証拠確認者」「§5 記入・commit 担当者」を識別子付きで指名する。兼務を許すかもユーザーが決める。
  - AI は手順案、静的チェックリスト、機械計算の補助までとし、測定実行者、証拠の承認者、floor 欄の記入者にはならない。[D1383:3](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2140-b4-floor-procedure/verbatim/D1383.md:3)
  - §11 の追記自体は「未裁定の案」であり、上記の指名や測定開始、値の採用を意味しない。

- **発効手続き案 — 何を根拠に**

  - 測定前に commit された procedure freeze を根拠とする。そこには対象 driver・軸・site・env_tag、校正済み `PerfConfig` の path/hash、測定対象セル、null-pair の作り方、セッション数、時間分離、欠測・retry 規則、統計関数、保守側最大の対象集合、出力命名を固定する。
  - 測定後は、raw session 値、共通参照点、各 `|gain_1-gain_2|`、全失敗、実行順、時刻、環境・source・build・command provenance、および導出結果を含む create-only artifact とその sha256 を根拠とする。
  - 既存値、stock だけの calibration、48 スレッド動作点の calibration は採用根拠にしない。[D1060:7](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2140-b4-floor-procedure/verbatim/D1060.md:7)
  - caller が渡した値や自由記述の出所は証拠にしない。[D1377:3](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2140-b4-floor-procedure/verbatim/D1377.md:3)

- **発効手続き案 — どの順で**

  - まず §11 の案を追加する commit を作る。この commit は §5 の値セルを変えず、発効版ではない。
  - 次にユーザーが担当者、採用証拠、統計関数を裁定し、その exact な測定 protocol を結果閲覧前の別 commit で freeze する。
  - 対象 driver・軸と site を確定し、同じ site resolver から env_tag を得た後、その環境用 `PerfConfig` を校正して artifact 化する。
  - 指名された実行者が、freeze 済み protocol どおりに複数の時間分離 campaign を実施する。既存出力への上書きや、途中値を見た追加測定をしない。
  - 証拠確認者が、全予定標本、失敗、hash、環境一致、計算再現性、保守側選択を確認する。確認結果だけでは §5 を変更しない。
  - ユーザーの採用裁定後、指定された担当者が floor 行だけを専用 commit で artifact path/hash へ変更する。artifact commit と procedure-freeze commit はその祖先でなければならない。
  - この floor 登録 commit 単独では発効しない。残る全 §5 欄と §6 の全条件が満たされた版を実走前に commit して初めて発効し、実走成果物はその commit hash を記録する。[事前登録:32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:32) [事前登録:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:45) [事前登録:540](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:540)

- **床値を得る測定計画 — AI が起草してよい部分**

  - 測定対象を、B-4 結果とは独立に事前固定した protocol・workload・contention 域・代表構成の集合とする。stock だけで対象 variant 域を代表したことにしない。
  - 各 null block で、共通の `reference_tps` と byte-identical な null candidate の独立 2 測定を作り、順序を事前無作為化する。各側の session median から `gain_1`、`gain_2`、`D=|gain_1-gain_2|` を計算する。これにより §5.1.1 の tie 入力と同じ尺度を直接測る。
  - 両側は trace-disabled、同じ校正済み `PerfConfig`、同じ env_tag、同じ admission・単独性条件で測る。可能なら正式 B-4 と同じ build/bench surface を通し、別プロセス・独立セッションとする。
  - 少なくとも時間窓を分けた複数 campaign block を事前固定する。各 block の標本数も結果を見る前に固定し、現行 driver の `SESSIONS=8` を前例だけで自動採用しない。同 driver 自身が相対 SE の粗さを明記している。[between_run_floor.py:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/between_run_floor.py:76)
  - 各セル・campaign の `D` 分布から何を floor candidate とするかを事前固定する。推奨は、将来の null 差を覆う片側 upper tolerance bound または高 quantile の片側上限であり、最後に全セル・全時間窓の最大を採る。単なる session-median CV は使わない。
  - 欠測・非有限値・環境不一致・競合検出・予定外 retry は値を都合よく小さくする除外に使わず、campaign 不採用または再計画へ倒す規則を先に固定する。
  - raw 値から最終 scalar まで再計算できる単一 artifact を作る。§5 に将来書くのは、この artifact の path/hash だけとする。

- **床値を得る測定計画 — ユーザーが決める部分**

  - 担当者の指名、代表構成と対象 contention 域、標本数、campaign 間の時間分離、採用する quantile・信頼水準・tolerance rule、許される retry、最終的に受理する証拠集合。
  - 現行 driver を拡張するか、選定済み対象 driver の既存測定面で null pair を取得するか。実装差分 0 を第一候補とし、既存の sanctioned surface で要件を満たせなければ測定を開始せず、別途ユーザー裁定へ戻す。
  - create-only 衝突の解決方法。既存 artifact の削除・上書きは認めず、時間窓ごとの一意な出力 path が確保できなければ停止する。
  - 証拠受理後に誰が floor 行を変更し、誰がその commit を確認するか。

## 編集位置

- [事前登録:215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:215) の既存 `floor` 項の末尾、現在の 216 行目の直後へ、通常本文の 1 行 pointer を加える。趣旨は「発効手続き案と測定計画は §11。D1383 により未裁定の案であり、floor 欄の記入権限や実走許可を与えない」とする。見出しにはしない。
- [事前登録:822](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:822) の後、文書末尾へ `## 11. floor 欄の発効手続き案と測定計画 (D1383・未裁定)` を追加する。節内は H3 以下を使わず、太字ラベルと箇条書きで上記内容を配置する。
- [事前登録:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:162) の値セルは変更しない。
- pin 対象は H4 `5.1.1` の開始から、次の level 4 以下の見出しである `## 6.` の直前までである。[consumer:301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:301) pointer は H4 より前、§11 は `## 6.` より後なので、抽出された raw bytes は変わらない。絶対 offset が後ろへずれても hash 対象 bytes は同一である。
- consumer は H5 の個数と順序も固定しているため、§5.1.1 内には何も置かない。[consumer:291](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:291) 新しい H4 も作らない。
- 親の provisional 配置が最善である。§5.1.1 より前へ長い節を挿すと見出し階層が不自然になり、§5.1.1 より後への挿入は pin を破る。§11 だけでは発見しにくいため、短い pointer との組合せが最小差分である。

## 危険

- **§11 が承認済み手続きに見える危険:** 見出しと冒頭で「未裁定の案」「ユーザー裁定前は測定・記入を許可しない」と明記する。案の commit を発効版と呼ばない。
- **CV を proxy にして floor を過小評価する危険:** `D=|gain_1-gain_2|` を直接測り、単側 CV からの換算を採らない。統計関数と最大を取る集合は結果閲覧前に固定する。
- **対象域の cherry-pick:** workload、contention 域、代表構成、標本数、時間窓を procedure-freeze commit へ列挙し、観測後の追加・削除・差替えを禁じる。
- **同一時間窓だけで下限を採る危険:** 複数の時間分離 campaign を必須とし、全 campaign の保守側最大を使う。途中結果を見て campaign 数を変えない。
- **create-only 衝突を上書きで回避する危険:** 現行 driver の既存ファイルを削除・改名して同じ path を再利用しない。一意な事前登録済み出力先が得られなければ停止する。
- **env_tag を後付けする危険:** site resolver の tag を校正・floor の前に確定し、異なる tag の値を混ぜない。
- **caller 自己申告へ戻る危険:** 将来の分析経路は凍結 artifact から束縛された値だけを受け取る。CLI `--floor` や自由記述の出所を代替経路にしない。
- **floor 行だけで関門を開く危険:** floor 登録 commit は部分充足にすぎないと明記する。§5 全欄、§6 全条件、§5.1.1 の実在 consumer を一つも免除しない。[事前登録:592](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:592)
- **値伝搬の未実装を文章で代替する危険:** §11 はコード変更や 4 分類の有効化を認可しない。artifact-bound な正規 consumer が別途実在するまで、D1377 の evidence-only / `protocol_violation` 状態を維持する。

## 総括

P1-a、P1-b、P1-d、P1-e は中核的に成立し、P1-c の順序だけは `env_tag` を校正前へ移す必要がある。  
測るべき量は単一構成の CV ではなく、§5.1.1 と同尺度の null-pair `|gain_1-gain_2|` の保守的上限である。  
配置は、現行 floor 項への非規範的 pointer と文書末尾の未裁定 §11 が最小かつ pin-safe である。  
AI は案と静的検証までとし、担当者、証拠、統計関数、採用、記入、commit はユーザー裁定へ残す。  
ファイル編集、commit、測定、pytest は行っていない。