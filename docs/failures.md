# 失敗台帳 (failures ledger)

起こした問題 (事故・near-miss・誤記・規律違反・監査での重大 finding) の一覧と、恒久対応の
実体・再発検知手段を 1 箇所で追えるようにする台帳。「二度と同じ過ちを犯さない」の正本
(2026-07-13 ユーザー要望で新設)。worklog は時系列の日誌、本台帳は失敗の型ごとの索引 —
詳細な経緯は各エントリの worklog 日付から引く。

## 運用規則

- 問題が起きたら、worklog エントリと同時に本台帳へ 1 エントリ追加する
- **恒久対応は実体へのポインタ必須** — CLAUDE.md 規律番号 / memory / hook / lint
  (check_docs.py) / スクリプトの fails-closed 検査のいずれか。宣言だけの対応 (恒真) は
  対応と認めない
- 機械化できる対応は機械化を優先する (lint・hook・driver 検査 > 行動規律 > 記憶)
- エントリは追記のみ。**同じ型が再発したら既存エントリに「再発: 日付」を追記して顕在化させる**
  (再発ゼロがこの台帳の成功条件)
- 型タグ: [捏造/幻覚] [恒真ゲート] [セッション死・救出] [権限逸脱] [ドリフト]
  [コンテキスト浪費] [計測汚染] [手順漏れ]

## エントリ (時系列)

### F1. 日付誤記 — 前エントリの日付を引き継いだ [手順漏れ]
- 事象: 6/28 のセッションが worklog/insights の日付を前エントリの 6/22 のまま誤記
- 根本原因: 日付をコンテキスト内の先行記述から転写した (実日付を確認しない)
- 恒久対応: memory `use-actual-current-date` — セッションの実 currentDate を使う
- 再発検知: worklog の日付列とコミット日付の不一致 (目視。lint 化は未実装)

### F2. C1 drift — campaign ディレクトリ発見ロジックの分裂 [ドリフト]
- 事象: report/critic 3 本が campaign ディレクトリの発見方法を各自実装し、歴史的ディレクトリ
  構成の変化で挙動が割れた (worklog Phase 2、修理 065593a)。同時期に repro_command の
  reps=3→5 誤記も混入
- 根本原因: 同じ発見ロジックの多重実装
- 恒久対応: `discover_campaign_dir` への一元化 (コード)
- 再発検知: 新スクリプトが独自のディレクトリ探索を書いていないかレビューで見る

### F3. 計測前の単独性未確認 — 孤児ベンチとの並走 near-miss [計測汚染]
- 事象: 前セッションの孤児ベンチプロセスが残ったまま計測に入りかけた (load average は
  指数移動平均で laggy なため気づきにくい)
- 恒久対応: memory `verify-single-tenant-before-measuring` — 計測前に pgrep で競合確認。
  補足 (2026-07-16): 単独性の確認は、どの環境でも計測を走らせるノード上で行う — スケジューラの
  ノード割当ては専有の保証ではなく、共有ログインノード上の pgrep は他ユーザーを拾って意味を
  なさない。共有ノード上で計測するしかない環境も含め、この技法系 — pgrep・load average の監視で
  外乱を避け、外乱を検知したら測り直す — が引き続き第一線であり、捨てない
- 再発検知: 計測系 runbook の事前チェック手順

### F4. 監査セッション突然死と文書一貫性の腐敗 [セッション死・救出] [ドリフト]
- 事象: 2026-07-04 夜の監査セッションが報告済み状態で突然死。加えて docs 横断監査で
  real 39 件 — 可変状態 (完了状況・現在地) の複数文書への再掲が相互に腐っていた
- 根本原因: (a) 生きた状態がセッション内にだけあった、(b) 正本の一元化なし・行番号参照が
  追記でずれる構造
- 恒久対応: CLAUDE.md 作業の進め方 6 (正本 = worklog 末尾 + 現行 phase doc のみ・再掲禁止・
  行番号参照禁止・チェックボックス同一コミット) + `tools/check_docs.py` (lint、機械化) +
  BG タスク出力からの救出手順の実証 (worklog 2026-07-05)
- 再発検知: check_docs.py が毎セッション末に走る

### F5. 幻の Read 出力による誤警報 [セッション死・救出]
- 事象: worklog の Read が幻の出力 (5000 行超の `---`・文字化け) を返し「worklog が壊れた」と
  誤診しかけた (実ファイルは無傷。worklog 2026-07-07 (3))
- 恒久対応: 破壊的な修復に入る前に独立手段 (wc / git show / hash) で実状態を診断する —
  CLAUDE.md 外の行動規律 (memory `verify-before-asking` の延長)
- 再発検知: 「ファイルが壊れた」と判断する前の二重確認

### F6. 別セッションの無記録放置 — 未コミット差分の孤児化 [手順漏れ]
- 事象: 別セッションが worklog も handoff もコミットも残さず段 4 loop harness の未コミット
  差分を放置 (worklog 2026-07-07 (3) が規律 6 発火で敵対監査後に継承)
- 根本原因: handoff がプラン止まりで生きた進捗を刻んでいなかった + セッション死
- 恒久対応: CLAUDE.md 作業の進め方 8/9 (handoff を 10 分おきに育てる・~15 分作業単位・
  心拍) + memory `scope-work-in-15min-units` / `handoff-grow-every-10min`
- 再発検知: handoff の更新時刻と作業の進行の乖離

### F7. 監査エージェントの read-only 逸脱 [権限逸脱]
- 事象: general-purpose サブエージェントが read-only 指示 (prompt 規律) を逸脱しスコープ外の
  編集を行った
- 根本原因: prompt 規律はツール権限の代替にならない (audit-2026-06-30 §4 と同根)
- 恒久対応: memory `audit-agents-read-only` — 監査/レビューは Edit 非付与の Explore/auditor
  型で回す (構造遮断)
- 再発検知: workflow 定義の agentType 指定をレビュー

### F8. LLM 生成文書の定量捏造 — token-management-strategy.md [捏造/幻覚]
- 事象: Haiku に生成させた体系化文書の定量記述がほぼ全て一次記録の裏付けなし — 架空の
  「Phase 5」・論文用 Table 1 の捏造値・実在 workflow id を流用した架空の中断復旧物語。
  論文転写事故の一歩手前 (2026-07-11 監査で発覚、real 21)
- 根本原因: 生成物を採用前監査 (規律 6) なしで docs に置いた
- 恒久対応: 削除/プレースホルダ化 + 冒頭監査注記 + lint 登録。教訓 = LLM 生成の体系化文書は
  概念枠が正確でも定量はほぼ捏造 — 採用前の一次記録突き合わせを必須とする (規律 6 の適用)
- 再発検知: 定量記述を含む生成文書の provenance 確認をレビュー観点に含める

### F9. check_docs の恒真化 — 実在しないファイルを黙って skip [恒真ゲート]
- 事象: check_docs の LIVING_DOCS が実在しない related-work.md を指し、黙って skip して
  いた (lint が発火しない = 恒真な保証。2026-07-11 監査で発覚)
- 根本原因: 検査対象の存在自体を検査していなかった
- 恒久対応: check_docs 修正 (対象不在は fail)。「恒真な保証 (謳うだけで発火しない assert)」は
  監査の標準疑い項目 (CLAUDE.md 規律 6 の監査発火条件に明記済み)
- 再発検知: 新しい検査を足すときは「わざと壊して発火を確認」(positive control) を習慣化

### F10. runbook の固定 campaign 名参照 — pin 前進で腐る構造 [ドリフト]
- 事象: runbook が固定の campaign 名を参照しており、submodule pin の前進で確実に腐る構造
  だった (2026-07-12 (4) 監査)
- 恒久対応: check_docs に runbook glob 自動検査を追加 (機械化)
- 再発検知: check_docs が毎セッション末に走る

### F11. セッション終了定型の漏れ — handoff 削除忘れ [手順漏れ]
- 事象: 正常終了時に handoff の削除 (worklog への吸収) を落とした
- 恒久対応: memory `session-close-checklist` — セッション TODO 末尾に worklog → lint →
  handoff 吸収・削除の定型 3 点を必ず置く
- 再発検知: クラス 2 / 3 セッションの開始時に docs/handoff/ の残ファイルを ls する (CLAUDE.md
  現在地の作業種別ゲート。クラス 1 は handoff を読まない)

### F12. 架空スキーマ例示による coder 誘導 near-miss [捏造/幻覚]
- 事象: 出力スキーマの description に具体戦略・CC 機構名を例示すると coder がそれに誘導される
  (D43 で必須修正として検出・是正)
- 恒久対応: D43/D47 必須条件 5 — スキーマ例示はすべて中立プレースホルダにする (agent 定義に
  反映済み)
- 再発検知: 新 agent 定義のレビュー観点

### F13. provenance 全文 JSON の直接 Read — 一撃 25k tokens [コンテキスト浪費]
- 事象: stock 17 本全文入りの n=1 provenance JSON (33k tokens) を Read し単発 25k を消費。
  workflow の返り値にも裏取り全文を入れ通知 ~25k (2026-07-13、ユーザー指摘)
- 根本原因: 凍結側の全文主義を読む側がそのまま踏んだ + 返り値スキーマの絞り込み不在
- 恒久対応: memory `provenance-json-via-extraction` (python 抽出・要旨返し + must-fix/
  partially-real/レンズ衝突時の全文エスカレーション規則)。書く側は hash + ポインタ + 要旨
  方式へ (実走 driver の frozen/ + hash_ledger.json が実装例)
- 再発検知: /context の Messages 伸び率。単発 10k 超の Read をやる前に抽出可否を自問

### F14. 無効化されるフラグを遮断機構として記録 [恒真ゲート]
- 事象: canary (worklog 07-13 (1)) の実行記録が `--exclude-dynamic-system-prompt-sections` を
  遮断構成の一部として記録したが、このフラグは `--system-prompt` 併用時に無視される仕様
  (2026-07-13 に --help で確認)。遮断の実効は完全置換 + preflight 実測が担保しており実害
  なし — 記録の不正確のみ
- 根本原因: CLI フラグの仕様を確認せず前例転写した
- 恒久対応: canary provenance に訂正注記 (erratum) + s6 driver は無効フラグを外し docstring に
  実態を記載。新しい CLI フラグは --help で仕様確認してから遮断構成に数える
- 再発検知: preflight (保有ツール NONE の実測) を毎実走の必須段にする (s6 driver に実装済み)

### F15. モックテスト母集団が実出力分布を含まず欠陥を素通し [テスト代表性]
- 事象: s6 driver の機械部分テスト 18 件 (07-13 (7) 新設) はモック束で三分法を検査したが、
  モックにコードフェンス付き JSON (LLM 出力として高頻度の形) を含めておらず、
  classify_proposer_output のフェンス非対応が実走 1 巡目まで発覚しなかった。5/7 attempt が
  supplement 誤判定、c5-15 が判定不能化、レート枠 3 倍消費で実走中断 (2026-07-13 09:03)
- 根本原因: テスト母集団を「仕様が定義する形」だけで作り、「実際に来る形」(LLM の整形ゆらぎ)
  を含めなかった。実出力 1 本の観測前にテストを凍結した
- 恒久対応: フェンス剥がし strip_code_fence + 実出力由来の回帰テスト 5 件 (23 passed)。
  復旧はユーザー裁定 A = amendment 2026-07-13-fence (機械再分類、追加呼び出しゼロ、
  全差分 = output/s6-rounds/amendment-2026-07-13-fence.json、原状 = コミット d6895d3)
- 再発検知: LLM 出力を機械判定する新規経路では、実出力サンプル (最低 1 本) をテスト母集団に
  含めてから本走する。実走 1 本目の final を確認してから残りを流す (canary 走行)

### F16. Codex profile の load を実 spawn・権限隔離の証明と誤認 [恒真ゲート] [権限逸脱] [ドリフト]
- 事象: commit 0d8b2f2 で 3 role を active としたが、現行 0.144.2 surface の spawn schema は
  custom agent type を選べず、fresh 実走でも spawn event 無し。初回試行は子を起動せず
  「adapter instructions を受領」と自己申告した。read-only profile も親の MCP/skills を継承する
  ため、外部 write/read 面は構造遮断されない (2026-07-14 再監査 CA-01〜03)。
- 根本原因: TOML parse/load と prompt 文字列の存在を、profile の選択可能性・実拒否・全 tool surface
  の read-only と同一視した。実 runtime の spawn event と権限負例をテスト母集団に入れなかった。
- 恒久対応: D54 の「条件を満たせない client/surface では使用禁止」を現行 surface に適用し、3 role は
  selector + tool allowlist harness と E2E positive/negative control が揃うまで利用しない。一次資料 =
  `output/insights/2026-07-14_codex-agent-adapter-reaudit.json`。監査時点では実装修正をユーザー判断待ちとした。
- 再発検知: agent adapter の有効判定は自然言語 final でなく JSON event の spawn type/receiver、child
  instruction digest、write/read 負例で行う。文字列 presence test だけを証拠に数えない。
- 対応実体 (2026-07-14): D55 で `0 active / 3 dormant / 9 blocked` に再裁定し、project の発見可能な
  profile/agent role、custom role の通常ブート省略を撤去。checker は全 role の metadata/body digest・
  description の JSON quote/value digest、project config の agent role 不在を hard gate にし、runtime
  E2E は再開条件未充足のまま成功扱いしない。
  独立再現と修正証拠 = `output/insights/2026-07-14_codex-agent-adapter-remediation.json`。

### F17. top-level tools 0 件を総合 tool-free と誤認 [恒真ゲート] [権限逸脱] [ドリフト]
- 事象: 全 12 role 用 standalone harness の実装途中、raw Responses の top-level `body.tools` が無い
  known sol/terra を「production tool 0 件」と判定した。しかし同じ request の先頭には developer
  `input.additional_tools` があり、`exec` / `wait` / `request_user_input` / `collaboration` と、その下の
  file 操作・agent fan-out 宣言面が残っていた。JSONL に `view_image` call が出ない負例も再現した。
- 根本原因: tool inventory を top-level field だけに限定し、developer input と custom/code-mode tool
  descriptor を同じ信頼境界として数えなかった。static adapter の capability 空集合、prompt の不使用
  命令、outer filesystem sandbox を runtime 全面の不存在と混同しかけた。
- 恒久対応: D56 で全 12 adapter を非自動発見 static/dormant、runtime activation を blocked に固定。
  runtime probe は raw request の top-level key 集合、message/content boundary と順序、
  `additional_tools` 全 descriptor、forced fixture の tool history を exact に照合し、存在する限り
  auth/external model 使用前に停止する。wire bytes は strict UTF-8/JSON (重複 key・非有限数・過深入力拒否)
  で読み、検証した Codex/bubblewrap bytes を固定してから実行する。adapter 自体から
  wire/tool-free/absent surface の主張を撤去した。
- 再発検知: tool-free 判定は request body 全体と product/runtime developer surface を対象にする。
  JSONL の tool event 不在、自然言語 final、`body.tools=[]`、sandbox mode のどれか単独では証拠にしない。
  新 runtime/model/CLI は raw envelope/descriptor digest drift を赤にし、runtime prerequisite の欠落も
  skip 成功にせず、負例を再監査する。同一 UID の敵対 process に対する loopback provenance や network
  隔離は証明しておらず、probe/outer sandbox 単独を active 化の根拠にしない。
- 同時に閉じた移植ドリフト: 初期案は Claude 本文を hash するだけで Codex instructions へ完全移植せず、
  禁止入力 class も metadata のみだった。全本文 exact 埋込、top-level closed envelope と重要 field schema、
  recursive forbidden-key と cross-field validator、source input/output parity、description JSON quote の mutation
  tests へ置換した。auditor の `pass + violations` は現役 trusted parser まで fail-closed 化した。opaque
  string と意図的に open な object subtree は trusted projection producer の責任である。source/manifest/
  adapter/product override を同時に弱める自己承認を避けるため、生成物と独立した reviewed source/
  description/schema SHA、full role manifest SHA、共通 developer template SHA と I/O 契約台帳を固定し、
  台帳自体の変更は明示レビュー対象にした。

### F18. 正本の再肥大と無指定全読 — D35 が prompt 規律だけで止まらない [コンテキスト浪費]
- 事象: worklog.md が Phase 3 分だけで 224KB (88 エントリ) まで再肥大し、セッションの利用枠が
  半日で約 2 割消費される事態に (2026-07-15 ユーザー報告、別セッションの分析)。decisions.md
  235KB 級の offset 無し Read は 1 回 ≈ 70K token で、D35 (grep index → 部分読み) は prompt
  規律のみ — 事故 1 回を機械的に止められない構造だった
- 根本原因: ローテーションの発火条件が「Phase 境界」だけで肥大を検知する仕組みが無い +
  D35 の読み方規律が機械執行されていない (F13 の読む側対策は memory どまりで、読む主体が
  変わると効かない)
- 恒久対応: (1) `hooks/guard_read.py` — repo 内 docs/output 配下 80KB 超の offset/limit 無し
  Read を拒否し部分読みへ誘導 (settings.json 配線 + test_hooks.py 回帰)、(2) `tools/check_docs.py`
  の worklog 肥大検査 (100KB 超で lint 違反 = ローテーションの合図)、(3) worklog を 07-14
  戦略改訂境界で再ローテーション (224KB → 20KB)
- 再発検知: check_docs.py (セッション締めの必須 lint) が肥大を、guard_read が全読を機械検知

### F19. freeze variant の実体化バグ — 単体検査は通るが実 build で落ちる経路が本走まで潜伏 [手順漏れ]
- 事象: S-1 develop v1 で backoff_fixed_best 3 セルが build-error ×3 → abandoned
  (2026-07-16、worklog 同日)。`prepare_cell` が EVOLVE-BLOCK hole に生の数値文字列 "5" を
  quarantine 書き込みし、骨格の変数宣言を破壊した。正方式は backoff-sweep と同じ
  「骨格パッチ + CMake フラグのみ」で、hole 置換は不要かつ有害だった
- 根本原因: 実体化経路の positive control が「quarantine が pass する」まで しか届いておらず、
  「その生成物が実際に build を通る」という統合検査が無かった。gate 述語 / comparator /
  数値という三種の variant を同じ `implementation` 変数で運ぶ設計が、種別ごとの意味論の
  違い (コード片 vs フラグ値) を隠した
- 恒久対応: (1) d2a46f1 — 数値種別は hole 置換経路から分離し、backoff_us と
  flags.BACKOFF_FIXED の不一致を DriverError で fails-closed 化 + 「骨格が汚れないこと」の
  回帰テスト、(2) trial 版上げ (v1→v2) で実行系の版を campaign identity に反映し、失敗
  campaign を改竄せず保存する前例を確立、(3) 開発相 (develop role) がこの型のバグを本計測前に
  検出する防壁として実証された — 開発相を飛ばして floor/block を直接走らせない
- 再発検知: test_s1_direct_comparison.py の骨格温存検査 + develop 相の実 build (18 構成) が
  毎回の統合 positive control として機能する

## 未回収

- Phase 1〜2 の恒久対応 4 件 (docs/archive/worklog-phase1-2.md 内) は本台帳へ未回収 —
  必要になったとき grep で回収して追記する
