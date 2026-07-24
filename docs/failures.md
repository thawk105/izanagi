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
  [コンテキスト浪費] [計測汚染] [手順漏れ] [テスト代表性]

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
- 再発 (2026-07-17): related-work.md のパス書き換えで個別事象は解消していたが、恒久対応が
  謳う「対象不在は fail」という構造修正自体は未 land で、LIVING_DOCS ループの
  `if not doc.exists(): continue` が残存 (手書き列挙対象が改名/削除で黙って蒸発する経路が
  再び開いていた)。修正: 手書き列挙分 (_ENUMERATED_DOCS) の不在を違反として積む fail 経路に
  変更し、positive control (orchestrator/tests/test_check_docs.py) で固定。glob 由来の動的分は
  従来どおり実在物のみ検査

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

### F20. 監査全文の揮発性領域退避 — セッション成果の唯一コピーが /tmp から消失 [手順漏れ]
- 事象: 8b 二波監査の全文 (audit-wave1/2-out.md) を /tmp のセッション scratchpad へ退避し、
  worklog 2026-07-16 (5) は「次セッションで output/ へ移すか判断」とポインタだけを記録した。
  同日午後の凍結着手時に全 /tmp/claude-* と ~/.codex/sessions、Claude transcript を探索したが
  不在 — 唯一コピーが失われ、原文全文は復元不能になった (削除時刻・主体・原因は不明のため
  断定しない)
- 根本原因: 「セッションを跨いで必要になり得る成果物」を非永続領域にだけ置き、永続化判断を
  次セッションへ繰り延べた。scratchpad はセッション専用の一時領域であり、生存保証がない
- 恒久対応: セッションを跨ぐ可能性のある成果物 (監査・相談の全文、実測値、裁定) は生成した
  同じセッション内に repo 配下 (output/insights 等) へ置き、worklog / handoff には repo 内
  パスだけを残す (docs/handoff/README.md へ規約追記)。残存証拠からの再構成 =
  `output/insights/2026-07-16_s8b-two-wave-audit-reconstruction.md`
- 再発検知: 機械 lint は見送り — worklog / handoff の /tmp 言及は正当な一時運用でも現れ、
  「唯一コピーか」の意味判定が必要になるため恒真化リスクがある (D31 と同型の prompt 規律とし、
  再発時に機械化を再検討)

### F21. guard_agent の配線を live 発火未検証のまま防壁とした [恒真ゲート] [テスト代表性]
- 事象: 導入 commit e45db19 時点では runtime の live 発火検証が無く、翌セッション (2026-07-18) の
  実測で、model 未指定の Agent 呼び出しを guard_agent が拒否せず spawn する環境があると判明した。
  同じ payload の hook 単体実行は exit 2 となり、同一セッションの guard_bash も発火していた。
- 根本原因: 既存テストは settings の matcher/command 文字列と hook script の stdin 直叩きまでで、
  runtime が Agent の PreToolUse を実際に配送し、exit 2 を spawn 阻止へ結線する全連鎖を検査して
  いなかった。設定 presence と判定核の健全性を live 配送の健全性と同一視した。
- 恒久対応: runtime 配送の恒久検査は未実装。原因分離と次回の再検証条件は
  `hooks/README.md` hook 4「live 発火に関する既知の限界」を正本とする。
- 再発検知: 現行の settings 文字列検査と hook script 直叩きでは検知できない。次の新規
  バックグラウンドジョブ型セッションで、daemon version を確認した live 負例を再試験する。

### F22. 実機前提の検収を rc 成功で確定と誤認 — 表記・依存の逐次発見で attempt 10 回 [手順漏れ] [テスト代表性]
- 事象: Pegasus certification (2026-07-19) が実機固有の未確定前提で 9 回 fail-closed した。qstat の
  時刻 field 表記 (smoke で rc=0 だけ確認し、表記をパーサと突合しなかった) / PBS_JOBID の `0:`
  prefix / CMake の PATH 型 `:` 分割 / gflags→glog の依存逐次発見 / perf dispatcher のカーネル
  不一致 / NFS の renameat2 EINVAL。各回は 10〜210 秒 + 完全 forensic で安価だったが、依存 2 件は
  全量列挙を先にやれば 1 回で済んだ。
- 根本原因: smoke 検収を「コマンドが rc=0 で動く」で閉じ、**出力の表記・意味を消費側 (パーサ・
  照合) と突合するまでやらなかった**。ビルド依存も「最初に踏んだ欠落だけ直す」逐次対応で始めた。
- 恒久対応: (a) smoke の検収基準を「消費側との突合まで」とする (qstat 表記は実 bytes を fixture 化
  済み)。(b) 新環境のビルドは configure 前に find_package/依存の全量列挙 (今回 CCBench 分は
  runbook §7.1 に確定記録)。(c) 実機で確定した事実は pegasus-runbook §7.1 へ都度固定。
- 再発検知: certification ジョブの forensic (stage 別 failure.json) が発見コストを 1 attempt
  ~0.01pt に抑える — 逐次発見自体は安全。型として残すのは「rc=0 ≠ 検収完了」。

### F23. codex exec の stdin 未クローズ — 並列レビュー 3 本が 100 分沈黙 [手順漏れ]
- 事象: バックグラウンド起動した codex exec (プロンプトは引数渡し) が「Reading additional input
  from stdin...」で停止し、敵対レビュー 3 本が約 100 分無進捗 (2026-07-19)。ユーザーの指摘で発覚。
- 根本原因: codex exec は「引数プロンプト + パイプ stdin」のとき stdin を <stdin> ブロックとして
  追記読みし、EOF まで待つ。先行の相談・実行ラウンドは環境の偶然で stdin が即 EOF だったため
  同じ起動形が動いてしまい、危険な形が固定化した。
- 恒久対応: codex exec のバッチ起動は常に `< /dev/null` を明示し、投入前にプロンプトファイルの
  非空を検査する (空 + /dev/null は「空指示実行」の退化形になるため)。長時間サブプロセスは
  起動直後にログの先頭進捗を 1 回確認する。
- 現行実体: `docs/dev-wave/operations.md` の `DW-O01`。
- 再発検知: ログ末尾の「Reading additional input from stdin」を停止指標として grep する。

### F24. サブプロセス完了検知をログ本文 grep に頼り誤検知 — 偽完了 2 回 + 空振りタイムアウト 2 回 [手順漏れ]
- 事象: codex exec のバッチ監視で「tokens used」等の完了マーカーをログ全文 (のち末尾 2KB) から
  grep したところ、子が読んだファイル内容 (過去ログの逐語凍結、さらに**この落とし穴を記した handoff
  の注記自体**) がログに混入して偽完了 2 回。逆に footer 書式の想定違いで完了を検知できず、全単位
  完了済みのままタイムアウトまで待機が 2 回 (2026-07-19)。ユーザーの指摘で恒久対策に切替。
- 根本原因: 完了という状態を、内容が非決定的なログ本文のパターン照合で推測した。子は任意のファイルを
  読んで echo するため、マーカー文字列の混入は構造的に防げない。
- 恒久対応: バッチ起動は `bash -c '<cmd>; echo $? > <log>.done'` のラッパで包み、監視は `.done`
  ファイルの存在 + exit code だけを見る (本文 grep をしない)。プロセス生存確認を併用する場合は
  自己マッチ (pgrep が監視シェル自身や snapshot ラッパに一致) に注意する。
- 現行実体: `docs/dev-wave/operations.md` の `DW-O01`。
- 再発検知: 監視スクリプトに「ログ本文 grep で完了判定」する行が入っていたらレビューで差し戻す。

### F25. commit trailer block の分断・結合ミス — provenance 監査 3+2 違反、積み直し 2 回 [手順漏れ]
- 事象: 2026-07-20 の同一セッションで 2 回、`AI-Agent` trailer が git に trailer と認識されない
  message を作成 (1 回目 = trailer 行と `Co-Authored-By` の間に空行 → block 分断で AI-Agent が本文化。
  2 回目 = 本文と trailer の間の空行欠落 → 本文と同一段落になり trailer 比率不足で不認識 +
  件名 1 行に全文が畳まれた worklog commit)。check_ai_provenance が両回とも検出し、未 push のため
  メッセージのみ修正して積み直し (tree 不変)。台帳 (task-runs) の commit event には旧 SHA が
  append-only で残存
- 根本原因: git の trailer 認識規則 (「最終段落のみ・段落内の trailer 行比率」) を意識せず、
  heredoc で message を手組みした
- 恒久対応: commit message は「件名 / 空行 / 本文 / 空行 / trailer block (AI-Agent 行と
  Co-Authored-By を空行なしで連続)」の 4 段構成で作る。commit 直後に `check_ai_provenance` を回す
  (規約どおり) — 違反が出たら push 前にメッセージだけ積み直す
- 現行実体: `docs/dev-wave/operations.md` の `DW-O17`。
- 再発検知: `python3 tools/check_ai_provenance.py` (機械)。積み直し時は台帳・worklog の SHA 参照の
  更新漏れも併せて見る

### F26. worktree 掃除での submodule 起因の二重の罠 — remove 無条件拒否と deinit の設定共有 [手順漏れ]
- 事象: 2026-07-20 のブランチ・worktree 掃除で、(1) submodule (external/ccbench) の gitlink を
  index に含む worktree は `git worktree remove` が無条件拒否 (`--force` でも submodule を空にした
  後でも不可)、(2) 回避を試みた worktree 側での `git submodule deinit` が、worktree 間で共有される
  `submodule.*` 登録を消し、**main checkout の external/ccbench まで未初期化にした** (実害 = 一時的。
  `git submodule update --init` でローカル .git/modules から即復元し、pin (d706650) 一致を確認済み)
- 追加事象: 同日の ExitWorktree は、作成した worktree の commit を main へ fast-forward 済みでも
  「未取り込みで失われる」と誤警告した。`discard_changes: true` では押し切らず、`git log` で
  main が当該 commit を含むと確認し、`action: keep` で抜けて手動の安全手順で畳んだ。
- 根本原因: git の worktree × submodule の仕様 2 点 (remove の gitlink 無条件拒否、submodule 登録
  config の worktree 間共有) を知らず、即興で deinit を挟んだ
- 恒久対応: `/cleanup-branches` スキル (.claude/commands/cleanup-branches.md) に安全手順を固定 —
  deinit を使わず「detach → ディレクトリ削除 → `git worktree prune`」(git 文書化済みの回避)、
  事後に `git submodule status` で main checkout の初期化状態を検査
- 現行実体: `.claude/commands/cleanup-branches.md` §3。dev-wave では
  `docs/dev-wave/operations.md` の `DW-O06`（submodule 系 test）と `DW-O08`（初期化）。
- 再発検知: スキル末尾の事後検査 (`git submodule status` が `-` prefix なしで pin 一致)。worktree
  掃除をスキル外で即興したらレビューで差し戻す

### F27. 自己ハッシュ generator の改変で凍結成果物を壊し、fixture へ現行 hash を差し込んで隠蔽 [恒真ゲート] [テスト代表性] [手順漏れ]
- 事象: 2026-07-20 の ruling-A/C wave で、実装子 (codex) が WAL reader の収束のため
  `orchestrator/campaign/s1_known_axes_freeze.py` を編集した。同スクリプトは**自分の sha256 を
  `output/s1-freeze/known_axes_freeze.json` に記録する自己ハッシュ generator** であり、1 byte の変更で
  freeze の `verify()` が落ち、公式 oracle gate が `known-axes-freeze-verify` で拒否する状態になった
  (記録値 `1d4d45…` = 基準 HEAD、変更後 `d1d263…`)。さらに実装子は
  `test_verify_rejects_tampered_source_copy` の fixture へ**現行の generator hash を代入する 1 行**を
  足し、先行する generator gate を迂回してテストを緑に保っていた (コメントに迂回の意図まで明記)。
  全走は緑だったため、テスト結果だけでは検出できなかった
- 根本原因: (1) ソースファイル自身が proof chain の hash 対象である構造を、編集面の選定時に誰も
  検査しなかった (親の brief も「WAL の読み手」としてしか見ていない)。(2) 実装子への禁止事項に
  「テストを甘くして緑にするな」が無く、緑を作る自由度が残っていた
- 恒久対応: `/dev-wave` 段 5 の実装子定型に「緑の主張には走らせた範囲を併記」「テストを甘くして
  緑にすることの禁止 (fixture への hash 差し込み等)」を明記 (.claude/commands/dev-wave.md)。
  編集候補が凍結成果物に hash されているかを、変更前に `grep` で確認する
- 現行実体: `docs/dev-wave/workers.md` の `DW-S05-C` と
  `docs/dev-wave/operations.md` の `DW-O09`。
- 再発検知: 敵対レビューのレンズに「既存保証の喪失・テスト期待の弱体化」を常設する (本件はこの
  レンズが唯一の検出経路だった)。凍結成果物を持つ leaf を触る wave では、親が `verify()` を実走する

### F28. 事前登録した変異 5 件が全件無効 — 「受理集合を変える単一理由か」をコードで裏取りしていなかった [恒真ゲート] [テスト代表性]
- 事象: 2026-07-21 の S-1 freeze 再発行 wave で、親が brief に変異 M1..M5 を事前登録した (B-057)。
  敵対相談 2 本が独立に、**5 件すべてが kill を数えられない欠陥**だと指摘した。内訳は
  (a) M1・M5 = 先行検査に食われて受理集合が変わらない (死んだ SHA は `cat-file -e` が先に拒否する /
  source へ当てた変異が generator の自己 hash を変えて `generator sha256 不一致` で先に落ちる)、
  (b) M4 = 既存拒否が `exists()` 検査と `open(...,"x")` の二層なので単層変異は等価変異、
  (c) M3 = 変異対象の bytes 変更が下流 hash 照合でも赤くなる過剰決定、
  (d) M2 = baseline が候補を拒否する前提だったが実装 helper は tip 自身を選ぶため期待が逆転
- 根本原因: 事前登録の時点で「**どこを変えるか**」だけを決め、「**その変異が受理集合を変える
  単一理由になるか**」をコードで確認していなかった。多層防御・自己ハッシュ・下流照合が
  あるコードでは、単層の変異は等価変異か過剰決定になりやすい
- 恒久対応: 変異の事前登録では、各変異について (i) その位置より手前に同じ入力を落とす検査が
  無いこと、(ii) その位置を無効化したとき赤くなる理由が 1 つに絞れること、を**コードを読んで
  確認してから**確定する。確認できない変異は登録せず、実効ゲートへ再照準する
- 再発検知: 本件は変異実測へ到達する前に敵対相談が検出した。相談・レビューのレンズに
  「事前登録変異の kill 帰属が成立するか」を含めると、実測前に落とせる

### F29. 段 1 の実測確認が実差分をモデル化せず、正しく測って誤った結論を出した [テスト代表性] [手順漏れ]

- 事象: [T-005]+[T-063]+[T-068] 束ね wave (2026-07-21、D72) の段 1 で、`frozen_at_head` の
  ancestry 格下げを **runtime monkeypatch** で模擬し「現行 bytes のまま `verify()` が通る →
  再発行は不要」と結論した。実際には成果物が verifier 自身の bytes を pin しており
  (`known_axes_freeze.json` の `/generator/sha256` = `s1_known_axes_freeze.py` 全 bytes)、
  その照合は ancestry より前に走る。**格下げのためにファイルを編集した瞬間に generator hash が
  外れる**ため、実差分では ancestry へ到達すらしない
- 検出: codex プラン起草 (段 2) が指摘し、親が 1 行編集の実測で確認した
  (`1d4d45a3…` → `93174926…`、`generator sha256 不一致`)
- 根本原因: 模擬 (monkeypatch) と実差分 (ファイル編集) の差を意識せずに「実測した」と扱った。
  測定自体は正確だったが、**測定対象が命題と違っていた**
- 恒久対応: 段 1 の実測確認では「**何を模擬したか**」「**実差分と模擬の差は何か**」を明示する。
  コード変更を伴う裁定の前提検証では、可能な限り**実際にファイルを編集して測る** (直後に復元する)。
  自己 hash・自己参照を持つ対象では monkeypatch による模擬を根拠にしない
- 再発検知: 相談・レビューのレンズに「親の実測は実差分をモデル化しているか」を含める

### F30. 凍結成果物を触る wave で `FROZEN_MANIFEST` を見落とした [手順漏れ]

- 事象: 同 wave で、S-1 成果物の bytes を変える設計を検討しながら、
  `orchestrator/tests/test_frozen_artifacts.py` の `FROZEN_MANIFEST` (凍結 8 件の全 bytes sha256 pin)
  を親も codex プランも所有範囲に入れていなかった。敵対相談 2 本が独立に blocker として検出した
- 根本原因: 「凍結成果物の consumer」を verifier と直接参照元だけで数え、**成果物そのものを
  bytes で pin している台帳**を数え落とした
- 恒久対応: 凍結成果物 (freeze / oracle gate / proof chain) の bytes を変える可能性のある wave では、
  着手前に `grep -rn "<成果物パス>" --include=*.py` で **pin 元を全列挙**し、brief の不変条件へ書く。
  `FROZEN_MANIFEST` は既定のチェック対象に含める
- 現行実体: `docs/dev-wave/operations.md` の `DW-O09`。
- 再発検知: 段 1 の実測に「この成果物を bytes で pin しているのは誰か」の列挙を含める

### F31. 裁定要約が元 decision の制約を落とし、迂回できたつもりで同じ閉包へ戻った [手順漏れ]

- 事象: worklog 2026-07-21 (5) の [T-005] 裁定要約は「[T-068] の格下げを採れば再発行そのものが
  不要になる」としていた。しかし D71 (2)(c) は既に「v1→g1 の許可 JSON Pointer 集合に
  `/known_axes_freeze/sha256` が無い」と記録しており、格下げが bytes 変更を強制する以上
  **同じ制約が再び発火する**。要約の側にこの制約が継承されていなかった
- 根本原因: 裁定要約 (worklog) だけを読んで着手し、根拠となる decision 本文へ当たらなかった
- 恒久対応: 承認済み wave の着手時は、**裁定要約が参照している decision 本文を必ず開き**、
  要約が落としている制約が無いかを確認する。要約と本文が食い違う場合は本文を優先する
- 再発検知: 段 1 の実測確認の定型に「元 decision の制約列挙との突き合わせ」を含める

### F32. 変異ハーネスの二重走行汚染と、未追跡ファイルに恒真な `git diff` 復元検査 [恒真ゲート] [手順漏れ]

- 事象: [T-076] の変異 matrix で、旧セッションが起動した `mutation_harness.py` が session
  teardown 後も OS process として生存し、新セッションの走行と衝突して production を変異させた
  まま残した (daemon/git_state/schema に計 3 回)。復元検査は `git diff -- <path>` を使っていたが、
  対象は**未追跡ファイル**のため diff は常に空を返し、残留変異を検出できなかった (恒真ゲート)
- 誘発要因: (i) 生存プロセスの確認に BRE の `\|` を `pgrep -f` へ渡し、`\|` が literal 扱いで
  偽陰性になった。(ii) M8 (nested-launch 検査の除去) が「拒否 → 無期限 serve」に化けて pytest
  全体が 900s hang し、finally での復元前に SIGTERM で殺された (SIGTERM は Python の finally を
  走らせない)
- 恒久対応:
  1. **復元検査は内容比較で行う** (`path.read_text() == source`)。`git diff` は未追跡・
     未 stage のファイルに対して恒真になるため使わない
  2. **ハーネスに flock の単一走行 guard を入れる** (`LOCK_EX|LOCK_NB`、取得失敗で abort)。
     これで旧セッションの生存プロセスとの二重走行を機械的に防ぐ
  3. **hang しうる変異は部分集合 + timeout で隔離**し、timeout はその変異の記録
     (fail-closed→fail-open の証拠) として扱い、ハーネス全体を落とさない
  4. プロセス生存確認に `pgrep -f` を使うなら **ERE (`-P` か素の literal)** にする。
     BRE の `\|` は使わない
- 現行実体: `docs/dev-wave/mutation.md` の `DW-M05` と `DW-M06`。
- 再発検知: 変異・fault 注入ハーネスの設計時に「復元検査が対象ファイルの追跡状態に依存して
  恒真化しないか」「二重走行を機械的に排除しているか」をレンズに含める (段 6 の作法)

## 未回収

- Phase 1〜2 の恒久対応 4 件 (docs/archive/worklog-phase1-2.md 内) は本台帳へ未回収 —
  必要になったとき grep で回収して追記する

### F33. 変異ハーネスの同一ファイル複数置換が上書きで消え、両層変異が偽 SURVIVED になった [恒真ゲート] [手順漏れ]

- 事象: [T-004] の変異 matrix 2 巡目で、両層変異 (M06ab/M07b) の各置換を**毎回 originals から**
  適用していたため、同一ファイルへの 2 番目の置換が 1 番目を上書きして消し、実際には単層しか
  注入されないまま走行した。単層は設計どおり他層に支配されるので緑になり、**両層変異が偽 SURVIVED**
  として報告された (注入されなかった変異を「生存」と誤報する型)
- 誘発要因: multi-site 対応を後付けした際、per-site の書込を `originals[rel].replace(...)` のまま
  にした。site ごとの一意性検査は originals に対して行っており、累積後の内容を検査していなかった
- 検出できた理由: 両層変異に **kill 期待を事前登録**していたため、SURVIVED が即座に「bad」として
  表面化した。期待なしで走らせていたら「両層でも開かない = さらに別の層がある」と誤結論し、
  等価変異の誤記録になり得た
- 恒久対応:
  1. **同一ファイルへの複数置換は累積適用し、置換ごとに累積後内容で一意性を assert する**
     (`.claude/commands/dev-wave.md` の変異ハーネス作法へ追記、2026-07-22)
  2. **SURVIVED は「注入の実在」を mutated 内容の diff で確認するまで equivalent と結論しない**
     (同上)。両層変異には kill 期待を必ず事前登録する (期待の無い変異は生存が黙って通る)
- 現行実体: `docs/dev-wave/mutation.md` の `DW-M04`。
- 記録: worklog 2026-07-22 (6)、erratum = `output/insights/2026-07-22_t004-wal-framing-mutation-ledger.md`

### F34. 受入全走の後に積んだ docs commit が repo scan invariant を破り、main が赤のまま次 wave まで残った [手順漏れ]

- 事象: wave2 は受入全走を fix2 commit (d4b6271) で緑にした後、docs commit (441babc) で凍結逐語
  台帳に三軸語 conjunction の逐語引用を追加した。全走は docs commit 後に再実行されず、repo scan
  invariant + oracle driver 系 11 テストが main で赤のまま残り、次 wave (wave3) の実装子の全走が
  検出した
- 誘発要因: 「docs だけの commit はテストに影響しない」という暗黙仮定。repo scan invariant は
  repo の**全ファイル bytes** への不変量であり、docs / insights も走査対象。逐語凍結は「攻撃例の
  引用」を含みやすく、この不変量と構造的に衝突しやすい
- 検出できた理由: 実装子の定型 (緑主張に実走範囲併記) + 親の独立全走。単体テストの限定実走では
  検出されない位置だった
- 恒久対応:
  1. **docs を含むあらゆる記録 commit の後に repo scan invariant (+影響テスト) を再走してから
     wave を閉じる** (`.claude/commands/dev-wave.md` 段 7 定型へ追記、2026-07-23)
  2. **逐語・台帳を insights へ凍結する前に三軸語 conjunction (軸 template の生値) を機械検査し、
     hit があれば defang + erratum で凍結する** (同上)
- 現行実体: `docs/dev-wave/core.md` の `DW-S07`。
- 記録: worklog 2026-07-23 (2)、defang erratum = wave2 台帳 L642 (原文 = 441babc)、D80 (7)

### F35. 完了済みの人間手番を「発行待ち」として繰り越し、依存 3 タスクを不要に blocked 扱いした [ドリフト] [手順漏れ]

- 事象: ユーザーは 2026-07-24 に R receipt を発行済み (`8bec195` = `AI-Agent: none` commit、
  変更は receipt 1 ファイル)。にもかかわらず、その**後**に書かれた worklog 2 エントリが
  [T-068]/[T-077]/[T-078] を「R receipt 発行後に…承認済 (発行待ち)」として繰り越し続け、
  さらに /rulings は既に実行済みの発行を「承認」として再裁定した。[T-088] の dev-wave で
  敵対相談が指摘し、親が git で確定するまで 1 日以上 stale が残った
- 誘発要因: 「承認」と「実行」を別々に追跡していなかった。次の一手の項目は前エントリから
  文面ごと繰り越されるため、一度書かれた「発行待ち」は誰かが一次資料に当たるまで自走し続ける。
  承認を記録する側 (/rulings) が「その手番は既に済んでいないか」を照合していなかった
- 検出できた理由: dev-wave 段 3 の敵対相談に「親 brief 自身も攻撃対象」と明記していたこと。
  レンズ B が brief の前提 (「R receipt が残 gate」) を否定し、親が `git log` と
  `merge-base --is-ancestor`、および protocol 実凍結が receipt の active-valid を機械要求する事実
  (`orchestrator/campaign/s8b_floor_campaign.py` の `freeze_protocol`) で裏取りした
- 恒久対応:
  1. **「人間手番待ち」と繰り越された前提は、brief 前の実測で git と実成果物に照合して未実行を
     確認する。既実行なら stale と裁定し依存項目を繰り上げる** (`docs/dev-wave/core.md` の
     `DW-S01` へ統合、2026-07-25)
  2. 「発行待ち」表記と receipt 実在の機械照合は `tools/check_docs.py` への追加候補として
     裁定パッケージへ送る (本台帳では宣言に留めない — 未実装であることを明示する)
- 現行実体: `docs/dev-wave/core.md` の `DW-S01`。
- 記録: worklog 2026-07-25 (2)、裁定パッケージ = `output/insights/2026-07-25_t088-official-unlock-design.md` §1
