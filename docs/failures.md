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
- **再発: 2026-07-25** — T-080 の R receipt 発行日を、一次資料 (commit 日時・receipt の
  `confirmed_at`) に当たらず周辺記述から転写し、3 箇所が `2026-07-24` と誤記した。実際は
  `8bec195` = `2026-07-23 21:49:33 +0900`、`confirmed_at=2026-07-23T12:49:16Z`。誤記箇所 =
  `docs/failures.md` の F35 本文 / `docs/worklog.md` 2026-07-25 (2) / `docs/phase3.md` 現行
  チェックポイント。**同じ wave のプラン起草 codex も置換案へ誤日付を再転写した**ため、
  誤りが下流へ自走することが実証された。検出は closure wave の独立 sweep + 親の一次資料照合、
  敵対相談 2 本が独立に追認。living doc (phase3) は直接訂正し、追記型 (failures / worklog) は
  本追記と worklog 2026-07-25 (3) の erratum で訂正した。恒久対応は memory から変更なし
  (実日付でなく**一次資料の日付**を確認する対象がコミット・成果物へ広がった点を本追記で顕在化)
- **再発: 2026-07-28 (near-miss)** — [T-142] 段 1 brief が D36 決定 4-2 の「AND 判定は
  wal/replay の共通ヘルパ 1 箇所に実装」という**規定 (should) を実装済みの機構 (is) として
  転写**し、裁定条件の充足根拠に使った。現物 `wal.records_by_stage()` は最後勝ちで AND 判定に
  使えないと docstring が自警しており、段 2 の codex プラン起草が検出 (実装前に是正、実害なし)。
  転写対象が日付・属性から**機構の実在状態**へ広がった顕在化。決定文の規範文は実在の一次資料では
  ない — brief の根拠にする機構は現物 file:line で実在を確認する (worklog 2026-07-28 (42)、
  旧番号 (38) から D70 統合時振り直し)

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
- 現行実体の更新 (2026-07-28 [T-147] 追記): trailer 配置規則は正本 `docs/ai-provenance.md`
  「必須形式」へ移設。`DW-O17` は commit 前 `--message-file` 検査・commit 後監査・rc 手順を担う
- **再発 (2026-07-29、[T-187]で回収):** `git merge main --no-edit` が
  `Merge branch 'main' into ...`を自動生成し、`AI-Agent`なしの2-parent commit
  `6b64d217…`を作った。件名ではなく、自動mergeがmessage-file preflightを迂回し、merge後の
  full-history監査もないまま共有されたことが欠陥。共有済みのためrewriteせず、D101の固定
  forward correctionで是正した。O17は`--no-commit`で止め、`commit -F`とpost full監査を必須化
- **再発 (2026-07-30、[T-187] main統合):** local-only T-180記録`cb79147`はprobe用Shellを追加したが、
  trailerがClaude manager 1行だけだった。新checkerのpost-merge全履歴監査が検出しmain更新を停止。
  remote未到達を確認し、ユーザー承認後にCodex authorが最終bytesへ実際に寄与した`677c32a`へ
  履歴を組み直した。単なるauthor行の後付けや第二例外にはしなかった
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
- 追加事象 (2026-07-30、別機序・同じ根): 掃除対象 8 worktree を 1 ループで `rm -rf` したところ、
  7 件目まで削除した時点で **2 分の command timeout に掛かって kill され**、8 件目が中途状態で残った
  (実害なし。単独で再実行して完了)。submodule を実体化した worktree はファイル数が多く 1 件の
  `rm -rf` が分単位に達しうるため、**一括ループにすると kill 位置が不定で「半分消えた worktree」を
  作る**。運用則 = **1 worktree ずつ削除し、必要なら timeout を延ばす**。command 本文への反映は
  `.claude/commands/cleanup-branches.md` が Codex skill との whole-file SHA-256 parity 契約下に
  あり checker 定数の同時更新を要するため未実施 (次の一手へ登録)
- 根本原因: git の worktree × submodule の仕様 2 点 (remove の gitlink 無条件拒否、submodule 登録
  config の worktree 間共有) を知らず、即興で deinit を挟んだ。追加事象は同じ実体化 submodule が
  削除コストを押し上げる点を見落としたもの
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
- 再発: 2026-07-26 ([T-106][T-107] wave)。事前登録 5 件のうち 2 件が同型で無効だった —
  S3 は `valid` 行の `parser_error_code` が手前で `None` に強制されるため status 照合だけを消しても
  等価変異、S5 は置換すると直後の base commit が空 commit で先に落ちるため目的の assert へ到達不能。
  **今回は段 3 の敵対相談をすり抜け、段 6 のレビューが検出した**。実装子が「前段に同じ入力を拒否する
  検査がないか」を自己申告で確認していたが、公開経路でなく private 関数の直呼びを前提にしていたため
  誤った。恒久対応の追補 = 事前登録の妥当性を実装子の自己申告に委ねず、`DW-S03` のレンズ項目
  (「変異の帰属不成立を探させる」) として明示し、段 3 で落とす。あわせて、変異が撃つ経路は
  private 関数の直呼びでなく**公開経路**で成立させる (直呼びは偽の KILL を作る)
- 再発 (near miss): 2026-07-28 ([T-157] wave)。poison テスト (resolve 非呼出) を private 直呼びで
  組んだため、旧 signature ごと戻す忠実な回帰では side_effect でなく引数不一致の TypeError が先に
  赤を作る偽 KILL だった。段 6 レビュー B → 焦点再レビューの二段が commit 前に捕捉。恒久対応の
  追補 = 呼び出しに依存しない構造的束縛 (code object の co_names 検査) を独立テストへ分離し、
  変異 (旧 signature 忠実回帰) で構造テスト単独の semantic kill を実測してから閉じる

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
- **再発: 2026-07-28** ([T-140] wave)。段 1 の生死確認で、CCBench の write set 用 use site を
  簡約した使い捨て probe を書き、「hole 内定義型では非修飾 `sort` が壊れるので `std::sort` への
  修飾が必須」と結論した。実際には `external/ccbench/include/backoff.hh` の大域
  `using namespace std;` が実 TU に入るため通常の名前探索で解決し、**この結論は誤りだった**。
  親は恒久対応どおり「何を模擬したか・実差分と模擬の差は何か」を brief に明記していたが、
  **その差の列挙自体が不完全** (include 閉包を挙げていなかった) だったため誤りを止められなかった。
  検出は段 2 の codex プランで、親が probe に同じ using-directive を足して再走し撤回した。
  **教訓: 「模擬の差を書く」だけでは足りず、その列挙の網羅性を独立レンズに攻撃させる必要がある**
  (今回は再発検知どおりレンズ A へ明示的に入れて機能した)。
  同 wave の隣接事象として、段 1 実測表に「すべて file:line 裏取り済み」とラベルしながら
  toolchain 事実 (shell 実測) を混ぜており、**一次資料の種別を一括りにラベルしない**ことも
  同レンズが指摘した。恒久対応の追加は dev-wave docs の byte 予算 (`T-127` 裁定待ち) が
  満杯のため保留し、裁定パッケージ側に記録した。
  **閉じ方 (2026-07-28、T-127 裁定 = 上限据え置き)**: prose の追加はしない。恒久対応の実体は
  本エントリの再発検知行 (レンズへ含める — 今回の検出もこの経路で機能した) + CLAUDE.md 規律 6 の
  「レンズ設計時は failures の型タグを攻撃面に含める」義務 (いずれも byte 予算の外)。
  機械化できる分はテストへ反映する (失敗例は prose でなくテストに、ユーザー指示 2026-07-28)

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
- **再発: 2026-07-27** ([T-119] wave)。今回殺されたのは子ではなく**親**である。ハーネスを
  実行時間上限のある前景経路で起動したため、上限で親 python が SIGKILL され `finally` の復元が
  走らず `worker.py` が変異したまま残った。直後の `git status` で検出し内容比較で復元を確認。
  恒久対応 5 = **ハーネスは外側の実行時間上限に掛からない経路 (background) で起動する**。
  あわせて恒久対応 4 へ**自己一致**の罠を追加 — `until ! pgrep -f "<script path>"` の待ちループは
  自分のコマンド行がその文字列を含むため常に一致し、終了しない (今回 3 本が滞留)。
  反映時に `docs/dev-wave/**` の hard ceiling (24000 bytes) の余裕が 16 bytes しかなく、
  ユーザー裁定 ([T-124] = reference 再編で圧縮してから入れる) を経て [T-104] で反映した。
- **再発: 2026-07-30** ([T-180] wave)。恒久対応 5 (background 起動) に反し、ハーネスを
  前景の tool 経路で起動した。セッション process が異常終了して `finally` の復元が走らず、
  M6 (`max_attempts` の off-by-one) が作業ツリーに残った。さらに孤児ハーネスが生存したまま
  次のセッションで走り続け、こちらの `git checkout --` 復元と競合した (flock guard は
  同一 job の再入だけを防ぎ、孤児の継続走行そのものは止めない)。検出は再開時の `git status`、
  回復は孤児の停止 → `git checkout --` → commit 済み内容との byte 一致確認。
  恒久対応 5 は既出で追加の規律は起こさない — 守らなかったこと自体が事象である。
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
- **再発: 2026-07-27** ([T-119] wave)。今回は注入ではなく**照合**が原因の偽 SURVIVED である。
  事前登録の期待を bare 名 (`test_foo`) で書き、記録した失敗節点は `DW-M08` が要求する
  `<file>::<name>` 形式だったため、両者の積が常に空になり **10 件全部が SURVIVED と記録された**
  (実際は 8 件が kill)。節点一覧 (一次証拠) は正しかったので再測定せず再計算した。
  恒久対応 3 = **期待節点と記録節点は突き合わせ前に同じ形式へ正規化する**。
  型は F33 と同じ「ハーネスが偽 SURVIVED を報告する」であり、**期待の事前登録がある変異
  (M1・M3 など) は誤記録でも節点一覧との矛盾が即座に見えた**点も F33 と同じ。
  反映経路は F32 の再発行に同じ ([T-124] 裁定 → [T-104] の再編で `DW-M08` へ)。
- 現行実体: `docs/dev-wave/mutation.md` の `DW-M04` と `DW-M08`。
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
- **erratum (2026-07-25、本文は訂正せず追記)**: 上の事象欄にある「ユーザーは 2026-07-24 に R receipt を
  発行済み」は日付が誤り。一次資料では `8bec195` = `2026-07-23 21:49:33 +0900`、receipt の
  `confirmed_at` = `2026-07-23T12:49:16Z`。**F35 は「一次資料に照合せよ」という教訓であるにもかかわらず、
  その本文自身が一次資料に当たらず周辺記述から日付を転写していた。** 型としては F1 の再発なので、
  顕在化は F1 の「再発: 2026-07-25」に記録した。恒久対応 1 (DW-S01 の照合義務) は日付にも及ぶ
- **再発: 2026-07-27**。`/rulings` が **§5-(viii) 残存限界の受諾**を裁定待ちとして提示し、ユーザーが
  裁定してしまった。実際は **2026-07-24 (6) で受諾済み** (「floor 実測前 gate クリア」) で、
  `docs/phase3.md` の同じ節の後段にも「§5-(viii) 受諾も完了」と書かれていた。**前段の gate 行だけを
  読み、後段の日付付き改訂 (消化記録) を読まなかった**のが直接原因。着手順は前段に gate を残したまま
  後段で消化を書く構造なので、gate 行の存在は未裁定を意味しない
- **再発が防げなかった構造的理由 (本件の主眼)**: 上の誘発要因欄は「**承認を記録する側 (`/rulings`) が
  『その手番は既に済んでいないか』を照合していなかった**」と `/rulings` を名指ししているのに、
  恒久対応 1 は `docs/dev-wave/core.md` の `DW-S01` にしか入っていない。**`DW-S01` は dev-wave の
  段 1 にしか効かず `/rulings` の収集手順は射程外**であり、名指しされた当事者に防壁が無いまま
  2 日で同型再発した。恒久対応 2 (「発行待ち」表記と実成果物の機械照合) も未実装のまま
- **`/rulings` 側の恒久対応は未実装 — ユーザー裁定へ回した**。`.claude/commands/rulings.md` は
  byte 予算 4500 に対し 4479 (余裕 21) で、照合義務を書く場所が物理的に無い。予算のために既存の
  安全義務を削るのは自己改善契約が禁じるため、**予算増額か reference 新設かを独立審査**にする
  ([T-127])。それまで `/rulings` の既決照合は本項を読むことでのみ担保される (機械防壁なし)

### F36. 受入・検査の結果欄をプレースホルダのまま記録 commit し、恒久対応の実行が空証明になった [恒真ゲート] [手順漏れ]

- 事象: `<受入結果を反映>` `<反映>` というリテラルのプレースホルダが埋められないまま記録 commit に
  入り、独立 3 wave + insight 1 本で残存した。`docs/worklog.md` 2026-07-24 (4) / 2026-07-24 (5) /
  2026-07-25 (1) と `output/insights/2026-07-24_e2e-real-seal.md`。とくに後 2 者は
  「repo scan invariant (F34) は本 docs commit 後に再走 `<反映>`」であり、**F34 の恒久対応を実行した
  という記録が空証明**になっていた
- 根本原因: 記録テンプレートを先に書き、実測後に埋め戻す運用にしていたため、埋め戻しの失敗が
  無検出だった。プレースホルダは「値が無い」ことを主張せず「値がある」ように読めるため、
  読み手には緑と区別がつかない
- 検出できた理由: closure wave の独立 sweep がリテラル文字列を横断検索した。前 wave の裁定パッケージ
  でも E2E 1 件は既知だったが、族としては未認識だった
- **retroactive に埋めてはならない**: 当時測っていない値を今書くのは捏造である。訂正は erratum に限る。
  なお全走値 (2919 passed / 18 skipped) 自体は `output/insights/2026-07-24_t086-keyset.md` と
  `output/insights/2026-07-25_t067-exact-residual.md` に現存する — 欠けているのは**記録 commit 後**の
  検査結果だけであり、「値が一切残っていない」という一括断定も誤りである
- 恒久対応:
  1. **受入・検査の結果欄にプレースホルダを残したまま記録 commit を作らない。実測前なら欄を作らず、
     実測できなかったなら「未実施」と書く** (`docs/dev-wave/core.md` の `DW-S07` へ統合、2026-07-25)
  2. リテラル placeholder の機械検出は、既存 4 件の allowlist と対象ファイル族・引用/verbatim の
     除外設計が先に要るため、裁定パッケージへ送る (本台帳では宣言に留めない — 未実装であることを明示する)
- 現行実体: `docs/dev-wave/core.md` の `DW-S07`。
- 記録: worklog 2026-07-25 (3)、closure evidence = `output/insights/2026-07-25_t068-t077-t078-closure.md`
- **再発: 2026-07-25 (本エントリ新設の次のセッション)** — /rulings の記録 (worklog 2026-07-25 (4)) で、
  検査欄の `check_ai_provenance` 件数を**実測前に「337 件」と先書き**して commit した。直後の実走で
  337 と一致したため記録は結果的に真だったが、外れていれば偽の実測値を commit していた。
  **プレースホルダより悪い変種である** — 空欄は空だと見えるが、予測した具体値は実測と見分けがつかない。
  恒久対応 1 (`DW-S07` の「実測前なら欄を作らず」) は文言としては本件を既に禁じており、
  不足は文言ではなく遵守。予測値の先書きが同条に含まれることを本追記で顕在化させる
- **恒久対応 2 の現行実体 (2026-07-25、[T-094]、D88)**: `tools/check_docs.py` の
  `_check_literal_placeholder_guard` を `main()` に結線し、`LITERAL_PLACEHOLDERS` の各要素が
  独立に効くことを positive control で固定した (実装 = commit `8ba4aed`、材料レポート =
  `output/insights/2026-07-25_t094-placeholder-gate.md`)
- **射程は限定される**: 保証するのは同定数の 3 要素の exact な出現と、対象 3 族
  (`docs/worklog.md`、`docs/archive/worklog-*.md`、`output/insights/*.md`) の raw text だけである。
  既知の債務 4 行と説明的言及 5 行は台帳で固定しただけで**解消していない** —
  `check_docs` の「違反なし」は「未許可 hit がない」の意味であって「placeholder が存在しない」
  ではない
- **この exact-literal gate だけを「実体化済み」とする。** 意味的に同じ別表記、HTML entity、
  **本台帳の再発である予測値の先書き**、対象 3 族の外 (phase/decisions/failures/handoff/JSON) は
  保証しない。それらの拡張は [T-097]〜[T-100] の裁定パッケージへ送った

### F37. 検査の rc をパイプで握り潰し、予算違反のまま commit した [恒真ゲート] [手順漏れ]

- 事象: 段 8 自己改善で `python3 tools/check_docs.py 2>&1 | tail -3 && git commit ...` と連鎖させた。
  pipeline の終了 status は `tail` のものになるため、`check_docs` が違反 1 件
  (`docs/dev-wave/**` 合計 24379 bytes > hard ceiling 24000) を報告していたにもかかわらず
  `&&` の右辺が実行され、**予算違反の状態が 1 commit 入った** (`419fa70`)
- 誘発要因: 出力を短くするための `| tail` が、そのまま「検査の成否」を判定する guard を恒真化した。
  `&&` は直前のコマンドではなく **pipeline 全体**の rc を見る、という基本挙動の取り違え。
  同じ形は「検査を走らせてから状態変更する」あらゆる箇所に潜む
- 検出できた理由: 直後に `python3 tools/check_docs.py; echo "rc=$?"` を単独で走らせ直したため。
  自動検出ではなく、たまたま値を確認したかっただけだった
- 恒久対応: **検査コマンドの rc はパイプに通さず単独で取り、その rc を見てから状態変更へ進む**
  (出力を絞るなら rc を取ってから表示する)。予算違反は予算値を上げずに、入口と重複する
  reference 記述の削除で収める (安全義務の削除・弱化はしない)
- 現行実体: `docs/dev-wave/operations.md` の `DW-O17`。
- **再発 (2026-07-29、[T-187]で回収):** 元sessionのmerge確認は
  `git merge main --no-edit | tail ...`の後に`MERGE_RC=0`と記録しており、0はGitでなく`tail`のrc。
  merge成立は約5秒後の2-parent objectで別途確認できたが、pipeline値をGit成功証拠には使えない。
  O17の単独rc契約をmerge preflight/post監査にも適用した
- **再発 (2026-07-30、[T-187] main統合):** target抜きの補助range監査が設計どおり赤になった後、
  同一shellの次行に置いた`merge --no-commit`が継続した。commit前で停止し、target-inclusive監査を
  単独再走してgreenを確認した。既存O17は単独rcと赤停止を既に要求するため、手順本文は増補しない
- **再発 (2026-07-30、[T-146] 段9再開):** Pegasusのmerge前preflight scriptが
  `set -uo pipefail`で`-e`を欠き、`git diff --cached --check`の赤後も後続検査へ進んだ。
  最後の`check_docs`がgreenだったためtrapはrc=0を記録した。commit前にlogから検出し、
  request `874111.nqsv`の結果を不採用化。手動解消面だけへdiff-checkを限定したfail-fast scriptを
  `874113.nqsv`で再走してgreenを確認してからcommitした。既存O17の赤停止契約で十分な同型再発のため、
  手順本文は増補しない
- 記録: worklog 2026-07-25 (5)

### F38. 記録後検査の値を埋める amend で、worklog 内の記録 commit hash が dangling になった [ドリフト] [手順漏れ]

- 事象: `DW-S07` の F34 恒久対応 (記録 commit の後に再走) と F36 恒久対応 (実測前に欄を作らない) を
  両方守ると、**再走値は記録 commit を作った後にしか書けない**。値を同 commit へ `--amend` で
  埋めた結果 hash が変わり、欄に書いた「記録 commit (`<旧 hash>`) の後に再走」の hash が
  **その amend 自身によって存在しない object を指す**ようになった。worklog 2026-07-26 (2) の
  記録中に発生し、同 wave 内で自己参照を外して是正した (未 land)
- 根本原因: 二つの恒久対応が要求する順序 (記録 commit → 再走 → 値の記入) が、
  値の記入先である欄に**その commit 自身を指す参照**を置くと循環する。
  前 wave (worklog 2026-07-26 (1)) の欄も同型の自己参照を持つが、そちらは amend 前後の hash が
  たまたま台帳に残らなかったため無検出だった
- 検出できた理由: 親が amend 直後に `git log` で hash の変化を確認し、worklog の記述と突き合わせた。
  `check_docs` は hash の実在を検査しないため機械検出はされない
- **retroactive に直さない**: 既 land のエントリは erratum の対象であり、本件は未 land のため
  その場で是正した。過去エントリの hash は改稿しない
- 恒久対応: **再走値は amend で埋め、その欄に記録 commit hash の自己参照を書かない**
  (`docs/dev-wave/core.md` の `DW-S07` へ統合、2026-07-26)。
  手順の正本を hash でなく記述に置くことで、amend による hash 変化と独立にする
- 現行実体: `docs/dev-wave/core.md` の `DW-S07`。
- 記録: worklog 2026-07-26 (2)、材料レポート = `output/insights/2026-07-26_t098-selector-lp-reject.md`

### F39. 「凍結 bytes を触らない」を安全条件と誤認し、ファイル追加が承認済み手番を割ることを見落とした [誤前提] [防壁の射程誤認]

- 事象: `/dev-wave クロスプロトコル対応` の段 1 で、親は cross-protocol 実装が凍結成果物と衝突すると
  実測し、「`genome.py` を編集せず ccbench gitlink も前進させなければ凍結 bytes は 1 byte も変わらない
  = 安全」という回避路を brief の不変条件に据えた。段 3 のレンズ B がこれを否定した —
  floor launch certificate の `clean_scan_digest` は**実 repository file 一覧を preimage に含む**
  (`orchestrator/campaign/s8b_floor_campaign.py:1597-1639`)。新規 patch / driver / PBS script を
  commit するだけで、承認済み・未実行の [T-088] receipt の `source_commit` と `clean_scan_digest` が
  承認時点から変わる。親は段 2 待機中に (P6) を「解決済み」と handoff へ凍結までしていた
- 根本原因: 凍結の単位を **bytes** だとだけ理解し、**ファイル集合**もまた凍結の preimage に入ることを
  見落とした。`DW-O09` の pin 閉包列挙は `FROZEN_MANIFEST`・generator source hash pin・
  key→canonical path 束縛を既定対象に挙げるが、いずれも「特定ファイルの中身」を pin する台帳であり、
  **「どのファイルが存在するか」を pin する digest** が既定対象に無い。
  grep 対象がファイルパスでなく digest 名になるため、パス名での閉包検索に掛からない
- 検出できた理由: 段 3 の敵対レンズが `s8b_floor_campaign.py` の launch certificate 生成経路まで
  読んだため。親の pin 閉包検索 (`grep -rn "<成果物パス>" --include=*.py`) では原理的に出ない
- 実害: なし。実装前 (段 4 裁定前) に検出され、コードは 0 byte も書いていない。
  ただし親は誤前提を handoff に「解決済み」と記録しており、段 3 が無ければ実装へ進んでいた
- 恒久対応: 未実施。`DW-O09` の既定対象へ「ファイル集合を pin する digest」を加える改訂が要るが、
  `docs/dev-wave/**` は hard ceiling 24000 に対し 23987 (余裕 13 bytes) で収まらない。
  [T-109] の裁定パッケージと併せてユーザー裁定へ送る ([T-101] / [T-104] / [T-108] と同じ形)
- 現行実体: なし (裁定待ち)。
- **再発: 2026-07-29** ([T-149] wave)。段 4 の pin 閉包が output 配下だけを掃引し、
  `.claude/agents/coder.md` の review ledger pin (`review_ledger.SOURCE_FILE_SHA256` +
  role-adapter 埋込) を見逃して「pin なし」と誤裁定。初回受入全走の test_codex_agents 赤で
  land 前に検出 (実害なし)。恒久対応 = `DW-O09` へ「output 外の review ledger を既定対象に
  含める + 出現の 4 分類 (live copy / 独立 golden / 凍結 snapshot / 歴史記録)」を追記
  (T-160 の DW-O07 削除で予算原資が回復していたため、段 8 で自動統合。同 wave の記録参照)
- 記録: worklog 2026-07-26 (3)、材料レポート = `output/insights/2026-07-26_s1-cross-protocol-gate-survey.md` §3.4

### F40. 測定のための一時変異ハーネスが部分一致の anchor で tracked file を壊し、実装の退行に見える赤を出した [恒真ゲート] [防壁の射程誤認]

- 事象: [T-120] の A/B 交互測定 (xdist group あり/なしを交互に走らせて wall を比べる) で、親は
  `orchestrator/tests/test_dev_waves_integration.py` の `pytestmark` 行を script で付け外しした。
  挿入位置の anchor に `_REPO = Path(__file__).resolve().parents[2]` を選び
  `str.replace(anchor, ..., 1)` で置換したが、この文字列は 26 行目の
  `_BOOTSTRAP_REPO = Path(__file__).resolve().parents[2]` の**部分文字列**であり、先にそちらへ命中した。
  結果 `_BOOTSTRAPpytestmark = ...` という壊れた行ができ、A1 走が
  `1 failed / 32 errors` (collection 段の `NameError`) になった
- 根本原因: `DW-M04` は「置換対象が一箇所でなければ harness を停止」を**変異ハーネス**の契約として
  持つが、**測定・比較のために tracked file を機械的に書き換えるハーネス**はその射程外だった。
  変異は「赤くなるべき」操作なので異常に気づきやすいのに対し、測定用の書き換えは「緑のままのはず」
  なので、壊れた結果が**実装の退行に見える**という点で危険度はむしろ高い
- 検出できた理由: 親が A1 の赤を「分割と無関係な collection エラー」として本文まで読んだため。
  rc と件数だけを見ていれば「分割すると赤が出る」と誤って帰属していた
- 実害: 測定 1 走 (約 70 秒) が無駄になった。ファイルは Edit で修復し、`git diff` の内容確認と
  `ast.parse` で健全性を検証済み。実装差分・commit への混入はなし
- 併発した既知型: 停止確認の `pgrep -f "run_tests.py"` が**自分のシェルコマンド文字列に自己一致**し、
  停止済みなのに「まだ走行中」と表示した (F32 の同型、実害なし)
- 恒久対応: **未実施 (予算不足)**。`DW-M04` の射程を「対象ファイルを機械的に書き換えるハーネス一般」へ
  広げ、(i) anchor は行の完全一致で一意性を確認する、(ii) 書き換え直後に構文と期待状態を実測して
  違えば停止する、の 2 点を要求する改訂が要る。`docs/dev-wave/**` は合計 23919/24000 bytes で
  余裕 81 bytes (日本語 27 文字) しかなく、既存の安全義務を削らずには収まらない。
  自己改善契約が「予算値を上げる変更は独立審査」と定めるため、[T-127] の審査へ合流させた
- 暫定の実体: 本 wave の harness (`ab_measure2.sh`) は上記 (i)(ii) を実装済みで、以後の同種作業の
  雛形になる。ただし文書化された義務ではないので、次の実行者が同じ設計を選ぶ保証はない
- 記録: worklog 2026-07-27 (20)、材料 = `output/insights/2026-07-27_t120-quiescence-window-and-group-split.md`

### F41. worktree で測った全走 wall を checkout 非依存の値として記録し、後続 wave の起票を誤らせた [誤前提] [測定の交絡]

- 日付: 2026-07-27 (混入は 2026-07-27 (20)、露出と是正は同 (21))
- 事象: worklog 2026-07-27 (20) は cygnus での全走 wall を 67.8〜106.3 秒、律速を単一 node
  (46〜58 秒) と記録し、それを根拠に [T-128]「唯一残った律速の短縮」を起票した。次 wave が
  main checkout で測ると全走は 300.65 / 321.34 秒、その node は durations 9 位で、記録とは
  wall も律速も一致しなかった
- 根本原因: **git worktree には ignored なファイルが存在しない。** `output/s1-build-cache/` は
  `.gitignore` 対象で main checkout に 36,158 件 (1.8GB) あるが、worktree では 0 件になる。
  T-080 E2E fixture は実 repo の `output/` を丸ごと複製してから `git add -A` するため、
  main checkout では ignored な生成物まで scan 対象に入り、worktree では入らない。
  **wall は checkout に依存するのに、その条件が記録に併記されていなかった**
- 検出できた理由: 次 wave の変異検査で、変更前 fixture を使う走 (102.89 秒) と変更後 (103.62 秒)
  が worktree でほぼ同時間になり、「worktree では修正前でも膨張しない」と分かったため。
  wall の数字だけを追っていれば、環境差 (Pegasus と cygnus) や他ユーザー負荷に誤って帰属していた
- 実害: 誤った前提での [T-128] 起票と、次 wave での baseline 再測 2 走 (約 10 分)。
  加えて、次 wave が最初に出した「修正で 17,119 → 2,507 件」という比較自体が checkout 違いで
  交絡しており、同一 source で測り直すまで効果を確定できなかった (実測し直して 121.72 → 22.13 秒)
- 恒久対応: `DW-O18` に「測定値は測った checkout を併記する」を追加した (2026-07-27)。
  `docs/dev-wave/**` の合計 hard ceiling 24,000 bytes に対し残余が 81 bytes しかないため、
  理由 (worktree に ignored 生成物が無いこと) は本台帳へのポインタに委ね、義務だけを置いた。
  「前 wave の値と比べるときは同じ checkout で測り直す」まで明文化する改訂は予算に入らず、
  [T-127] の独立審査へ合流させた ([T-129] として起票)
- 暫定の実体: worklog 2026-07-27 (21) と
  `output/insights/2026-07-27_t128-t080-fixture-scan-inflation.md` に、checkout 依存の事実と
  「同一 source で測り直す」手順を実測値つきで残した。既存の 69 秒という記録にも
  worktree 測定である旨を追記した
- 記録: worklog 2026-07-27 (20) (混入) と (21) (露出・是正)
- **射程の拡大 (2026-07-27 (25))**: 同じ根本原因が **wall より重い形**で現れた。main checkout で
  repo root から素の `pytest` を走らせると、ignored な `output/s1-build-cache/` 配下の
  googletest 由来 `*test*.py` を収集して **1253 errors** になる (worktree では ignored ファイルが
  存在しないため同じコマンドでも緑)。**この型は「測定値が checkout に依存する」に留まらず
  「赤の有無が checkout に依存する」**。受入全走は並列度と範囲の両方を明示し
  `python3 -m pytest -q -n 32 orchestrator/tests` の形で回す。恒久対応は [T-129] へ集約した
  (同タスクを本エントリで P1 へ昇格)

### F42. 新規テストファイルが自走 harness / allowlist の二択を満たさず、2 wave 連続で受入全走を空振りさせた [手順漏れ]

- 日付: 2026-07-27 (初発は同日 (24)、**再発が同日 (25)**)
- 事象: テストファイルを新設した wave が、受入全走で
  `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted` の赤を出した。
  (24) は `test_dev_waves_isolation_contract.py`、(25) は `test_profiler_directive.py` で、
  **同じ契約を 2 wave 連続で落とした**
- 根本原因: 全 `test_*.py` は「自走 harness (`_run()` + `__main__`) を持つ」か
  「`orchestrator/tests/README.md` の pytest 専用 allowlist に載る」かの二択を満たす必要があるが、
  **この契約はファイルを書く時点で目に入る場所に無く、受入全走まで露出しない**。
  新規ファイルを足す作業では、書き終えた後に思い出す手がかりが無い
- 検出できた理由: メタテストが機械強制しているため必ず赤になる — **防壁は設計どおり機能した**。
  失敗しているのは検出でなく、赤を出す前に満たすための手順
- 実害: 受入全走 1 回分の空振り (本 wave は約 80 秒 + 是正 + 再走)。(24) では是正後に全走 3 回を
  回し直している。**実害は小さいが確実に繰り返す**
- 恒久対応: 未定。手順書へ「新規 test ファイルは二択を満たす」を書く案は
  `docs/dev-wave/**` の合計 hard ceiling が満杯のため入らず ([T-127] と同じ制約)。
  メタテストが必ず捕まえるので受入全走 1 回のコストで収まるという理由で放置する選択もある —
  2 回目の発生をもって台帳に型として登録し、3 回目が起きたら恒久対応を優先する
- 暫定の実体: (25) は allowlist へ追加して解消した (parametrize 依存という allowlist の
  記載基準に正当に該当する。隣接の `test_s6_proposal_rounds.py` も同じ理由で載っている)
- **再発: 2026-07-27 (26)、3 回目。射程は「自走 harness / allowlist の二択」に限らない。**
  既存ファイルへテスト関数を 1 つ足した wave が、直列化契約
  (`test_dev_waves_isolation_contract.py` の
  `test_every_node_that_touches_process_external_resources_stays_serialised`) の marker 欠落で
  受入全走を赤にした。**型は「新設したテストが meta-test の契約を落とし、受入全走まで
  露出しない」**であり、新規ファイル固有ではない (今回は関数追加、かつ実装子ではなく親が直接書いた)
- **恒久対応 (2026-07-27 (26) に実施)**: `docs/dev-wave/workers.md` の `DW-S05-C` の該当行を
  「新しいテストファイルを作る単位」から「**テストを新設・改名する単位 (親が直接書く場合も)**」へ
  広げ、`meta-test も走らせる` の射程を関数追加と親の直接実装まで伸ばした。byte 予算は
  23,991/24,000 で収まった。3 回目をもって「未定」を閉じる
- 記録: worklog 2026-07-27 (24) (初発)、(25) (再発・型として登録)、(26) (3 回目・恒久対応)

### F43. codex 子が exit 0 のまま最終メッセージへ推敲断片だけを残し、レビュー本文が失われた [手順漏れ]
- 事象: [T-147] の敵対レビュー B (2026-07-28) が 168k tokens・exec 31 回の実検証を行いながら、
  `-o` の最終メッセージに出力書式の推敲メモ断片 194 bytes だけを残して exit 0 で終了した。
  ログに `[must-fix]` の推敲が残っており未放出の所見が実在した — 同一 prompt の再投 (B2) は
  must-fix 5 + nit 1 を返した。初回を成果物として採用していれば全所見を失い、破損出力を
  「所見なし」と誤読する経路もあった (near-miss。親検収 = 出力サイズの異常で検出し再投)
- 根本原因: 完了判定 (`.done` + exit code、F24 恒久対応) は「子が正常終了したか」しか保証せず、
  「最終メッセージが成果物であるか」とは独立。F24 は完了検知の偽陽性を塞いだが、完了した
  成果物自体の破損は射程外だった
- 恒久対応: 親の検収 — `-o` 成果物が指示した出力書式 (所見形式・総括の実在) を満たすか確認し、
  破損・断片は採用せず同一 prompt で再投する。reference への反映は段 8 で裁定
- 再発検知: 検収での差し戻し (行動規律) + `tools/check_codex_output.py` (最小サイズ・fence 外
  総括見出し。[T-153] (d) で機械化、2026-07-29)。意味整合の検収は引き続き親の行動規律
- 段 8 裁定 (2026-07-28 追記): `DW-O01` への prose 追記は見送り — dev-wave 総量の残 49 bytes に
  収まらず、T-127 裁定「恒久対応は prose でなくテスト・機械検査を優先」にも整合。恒久対応の実体 =
  本エントリの検収手順 (行動規律) + [T-153] (d) の機械化
- 記録: worklog 2026-07-28 (28)、逐語 = `output/insights/2026-07-28_t147-review-verbatim/README.md`
  (破損原文を凍結)

### F44. pipefail 下の `producer | grep -q` が SIGPIPE で計測ジョブを偽赤停止させた [手順漏れ]
- 事象: [T-140] set-size 実測ジョブ 1 回目 (872881.nqsv、2026-07-28) が、trace シンボル存在検査
  `nm -C bin | grep -qi izanagi_trace` で「シンボル無し」と誤判定し 43 秒で停止した。実際は
  シンボル実在 (2 回目 872886 の同一 build で 8 行確認)。`grep -q` が最初のマッチで即終了 →
  nm が SIGPIPE(141) → `set -o pipefail` がパイプ全体を失敗扱いにした。fail-closed 方向の
  偽赤で成果物影響ゼロ (near-miss)。キュー 1 投分の浪費のみ
- 根本原因: pipefail の意味論 (全段の rc を合成) と `grep -q` の早期終了最適化の相互作用。
  F37 (検査 rc をパイプに通して喪失 = 偽緑方向) の鏡像で、パイプ rc 意味論の同族
- 恒久対応: 大出力 producer の存在検査はパイプでなくファイル経由にする —
  `output/env/pegasus/t140-setsize/job.sh` の是正が実体 (nm 出力を一旦ファイルへ、grep は
  ファイルに対して実行し match をそのまま証拠として staging へ残す)
- 再発検知: この型は fail-closed 方向 (偽赤 = ジョブ停止) にしか壊れないため、成果物は
  構造的に守られる。検知はジョブの非 0 終了そのもの。偽緑方向の同族は F37 が既登録
- 記録: worklog 2026-07-28 (29)、両 attempt の staging =
  `output/env/pegasus/t140-setsize/job-staging/`

### F45. codex 子が upstream の安全フィルタで kill され、同一 prompt の再投でも通らず敵対レビュー 1 本を失った [手順漏れ]

- 事象: [T-148] 段 6 (2026-07-28) の敵対レビュー A (レンズ = 正しさ境界の迂回構築) が、2 回とも
  upstream の安全フィルタで停止した。1 回目は解析の途中、2 回目は**243k tokens の解析を終えた
  応答生成段階**で kill され、いずれも rc=1 かつ `-o` 成果物 0 byte。1 回目の prompt が使った
  攻撃比喩 (「攻撃者として破りに行け」「偽 cache hit を構築せよ」) を QA 語彙 (被覆漏れ・
  誤判定ケースの列挙) へ書き換えても通らなかった。親は claude 子へ切り替えて同レンズを実施し、
  結果的に must-fix 4 件を得た (成果物影響ゼロ)
- 根本原因: identity 迂回の具体的構築という**解析内容そのもの**がフィルタ対象で、prompt の語彙
  だけでは回避できない。izanagi の敵対レビューは「正しさ防壁をどう破れるか」を書かせるのが本質
  なので、この衝突は構造的に再発しうる
- 判別: F24 の完了判定 (`.done` の exit code) がそのまま効く — rc≠0 かつ成果物 0 byte。
  ログ末尾にフィルタのエラー行が残る。F43 (exit 0 + 断片) とは別型で、あちらの恒久対応
  「同一 prompt で再投する」はこの型には効かない
- 恒久対応: 同一 prompt の再投が通らなければ**エンジンを切り替える** (codex ⇄ claude 子)。
  レビューの独立性はエンジン多様性で担保されるので、切り替えは代替であって格下げではない。
  レンズを落として穴埋めしてはならない (規律 2)
- 段 8 裁定 (2026-07-28): `DW-O01` への prose 追記は見送り — dev-wave 総量の残 49 bytes に
  収まらず (追記すると 24195 > 24000 で赤)、T-127 裁定「上限は上げない・恒久対応は prose より
  テスト/機械検査を優先」にも整合する。F43 の段 8 裁定と同じ判断。恒久対応の実体は本エントリ
  (行動規律)。rc≠0 の検出自体は `DW-O01` の完了判定が既に担っている
- 記録: worklog 2026-07-28 (32)、逐語 = `output/insights/2026-07-28_t148-review-verbatim/`

### F46. ログインノードで実測した interpreter 挙動を計算ノードにも成立すると誤前提し、floor 実機初走が guard 到達前に死んだ [誤前提]

- 事象: [T-088] 段階 1 の実機初走 (job `0:873200.nqsv`, 2026-07-28) が `driver_rc=1` で終了。
  期待は official guard の rc=2 だったが、driver は import 段の
  `dataclass() got an unexpected keyword argument 'kw_only'` で guard に到達しなかった
- 根本原因: 計算ノードは module `intelpython/2022.3.1` が既定ロードされ `python3` が 3.9.13 に
  解決される。事前の rc=2 実測 (材料レポート §1-7) はログインノード (3.10.12) で行われており、
  「検証した環境」と「実行される環境」の interpreter が別物だった。job script は
  `python3.version` を**記録**していたが**束縛 (assert)** しておらず、記録するだけで発火しない
  値が死角になった (恒真な保証の family)
- 判別: `job-result.json` の `driver_rc=1` + driver stderr が import 系 TypeError +
  attempt dir の `python3.version` < 3.10。guard の正常拒否 (rc=2 + refused JSON) とは明確に別
- 恒久対応: interpreter を候補列 + 実行前版数 gate で選択し、全滅なら `stage=interpreter` で
  fail-closed (commit `419d59b`)。環境事実は `docs/pegasus-runbook.md` §4 に記載。一般則:
  実行環境でしか成立しない前提は、実行環境側で **assert として**束縛する (記録だけの値を作らない)
- 記録: worklog 2026-07-28 (33)、材料 = `output/insights/2026-07-25_t088-floor-wrapper.md` §9

### F47. AI セッション内 shell からの qsub が、見かけ成功のまま receipt 不永続・所有者不整合の無効 request を作った [誤前提]

- 事象: ユーザーが `!` プレフィクス (AI セッション内 shell) で `submit_floor.sh` を打鍵
  (request `873213.nqsv`, 2026-07-28)。qsub は request ID を返し script も成功出力を印字したが、
  receipt が実ファイルシステムに存在せず、`qstat -f` は「Not permitted to access」、
  attempt dir・spool・課金 (REMAIN/ESTIMATE) のいずれも痕跡ゼロ。request は一度も走らず消えた
- 根本原因: セッション内 shell は sandbox/namespace 下にあり、ファイル書き込みが実 FS に
  永続せず、プロセスの資格情報も通常端末と同一でない。**人間の打鍵であっても実行の実体は
  AI セッション環境**であり、「人間がコマンドを打つ」の運用定義に実行環境の指定が欠けていた
- 判別: 印字された receipt パスが実 FS に不在 + `qstat -f` が Not permitted + 予約見積・残高が
  不変。正常終了後の purge (単なる does not exist) とは応答が異なる
- 恒久対応: 外部システムへの状態変更操作 (qsub 等) はユーザー自身の端末で実行する
  (`docs/pegasus-runbook.md` §8 に追記)。D86(8) の「認可の実体 = ユーザーの明示指示」は不変で、
  そこに「実行はセッション外」という実行環境の定義を足す (裁定項目 1 の材料)
- 記録: worklog 2026-07-28 (33)、材料 = `output/insights/2026-07-25_t088-floor-wrapper.md` §9

### F48. 背景 job の worktree が origin/main から分岐し、local main より古い base で brief と受入を始めた [誤前提]

- 日付: 2026-07-28
- 事象: dev-wave 用に EnterWorktree で作成した worktree が origin/main (この時点で local main より
  2 commit 古い) から分岐し、wave は直前 wave の着地を含まない stale base で brief の前提実測と
  受入全走 1 回を実行した。handoff の「基準コミット = local main HEAD」も未検証の転写で、実態
  (origin/main) と食い違っていた (F1 型)
- 根本原因: EnterWorktree の既定 baseRef は `origin/<default-branch>` であり、AI から push しない
  運用 (local main が origin より常に先行しうる) と食い違う。worktree 作成直後に HEAD を実測して
  基準を確定する手順も無かった
- 検出できた理由: 受入全走の収集 node 数が直前 wave の記録と 1 件違い (3158 vs 3159)、
  collect-only の node 集合 diff で欠落 1 件が直前 wave 新設のテストと特定できたため。
  「計測値は checkout 併記」(F41 恒久対応) が比較の土俵を与えた
- 実害: stale base での受入全走 1 回 (約 70 秒) と handoff 基準の誤記。branch が未コミットだった
  ため `git merge --ff-only main` の追従で是正でき、成果物への影響なし。旧 base で読了した
  reference 節は現行版との diff で同文を確認した
- 恒久対応: 推奨は `.claude/settings.json` へ `worktree.baseRef: head` を設定し local HEAD から
  分岐させること — settings の編集は AI セッションの権限機構が拒否するためユーザー裁定・
  ユーザー実施 ([T-162])。それまでの作法: worktree 作成直後に `git log -1` で基準コミットを実測して
  handoff へ書き、local main と違えば commit 前に `--ff-only` で追従する
- 記録: worklog 2026-07-28 (38)
- **再発: 2026-07-29** ([T-139] wave、独立 2 例目 — 本台帳追記前の並行発生)。検出 = decisions の
  D 番号 grep 矛盾 (worklog (37) が参照する D94 が worktree に不在)。是正 = `--ff-only` 追従
  (同型)。補強 = `DW-O20` へ基準照合を 1 文追記 + auto-memory
  `dev-wave-bg-worktree-startup-checks` (立ち上げ 3 点検査)
- **恒久対応の適用 (2026-07-29)**: ユーザー裁定 = 採用。`worktree.baseRef: head` は commit
  166dd6f (ユーザー/codex) で適用済み ([T-162] 完了)。以後の worktree は local HEAD 基準で
  分岐し、本罠は構造的に閉鎖

### F49. 背景 job セッションからの qsub が runbook §8 の禁止に反して実行され、しかし有効な request を作った [手順漏れ] [誤前提]

- **事象 (2026-07-29, [T-139] wave):** gap probe の qsub (request 873583) を AI セッション内
  shell から実行した。runbook §8「ジョブ投入はユーザー自身の端末から」(F47 恒久対応) に違反 —
  投入前の §8 読了がリスト後半の当該項目に達しておらず、規則を見ないまま操作した。
- **ただし request は有効だった:** job は bnode011 で実走し、成果物は実 FS に永続 (commit 済み)、
  PBS 会計 (.e ファイル・qstat 可視の QUE→RUN→終了) も実在。F47 の判別条件 (receipt 不在・
  Not permitted・課金痕跡ゼロ) はすべて不成立 = **F47 の機序 (sandbox 不永続・資格情報差) は
  このセッション型 (背景 job の Bash tool) では発現しない**という反例。F47 の再発ではない
  (無効 request は作られていない)。
- **証拠の扱い:** 当該 job の値はもとより non-acceptance (insight §3.3) で、受理集合への影響
  なし。correctness leg は qsub 非関与。
- **恒久対応:** (i) 操作系 checklist (runbook §8 等) は操作前に全文読了する (F31 の「裁定要約が
  参照する本文を開く」と同族。auto-memory `dev-wave-bg-worktree-startup-checks` に固定)。
  (ii) **規則の射程精緻化はユーザー裁定へ** — 一律禁止のままにするか、F47 型 (不永続 sandbox)
  に限定するか。精緻化まで現行規則が正であり、以後の投入はユーザー端末へ引き渡す。
- 記録: worklog 2026-07-29 (40)、材料 = output/env/pegasus/t139-probe/0_873583.nqsv/
- **裁定 (2026-07-29)**: (ii) 射程限定を採用 (ユーザー — wave の自走性を優先し、AI 推奨の
  一律維持を上書き)。規則本文は runbook §8 — 書込永続が実証されたセッション型 (背景 job の
  Bash tool 等) からの投入を許可し、投入直後の有効性検査 (receipt 永続・qstat 可視・会計痕跡)
  を義務化。検査不成立は F47 型として以後の投入を止める

### F50. 専用 handoff を worktree 内に作り、DW-O20 の置き場義務に気づいたのは読了トリガ発火後だった [手順漏れ]

- **事象 (2026-07-29, [T-139] wave、near-miss):** 背景 job + worktree 隔離の wave 立ち上げで、
  専用 handoff を worktree 内 docs/handoff/ に作成した。DW-O20 (置き場義務の正本) の読了トリガは
  「clean-tree gate を worktree で走らせる直前」で wave 開始より構造的に遅く、読んだ時点で
  job tmp へ移動した (実害なし)。
- **原因:** handoff 作成は wave 開始時の操作だが、その置き場義務は L2 節にあり発火が遅い。
  F48 と同根 (wave 立ち上げ時に必要な義務が開始時の必読節に無い)。
- **恒久対応:** auto-memory `dev-wave-bg-worktree-startup-checks` (立ち上げ 3 点検査)。
  **dispatch 前倒し (背景 job + worktree 隔離なら wave 開始時に DW-O20 を読む条件を入口の
  条件表へ追加) は入口編集 = ユーザー裁定待ち** ([T-139] wave の裁定パッケージ)。
- 記録: worklog 2026-07-29 (40)、逐語 = output/insights/2026-07-29_t139-ladder-verbatim/
- **裁定 (2026-07-29)**: dispatch 前倒しを採用 (ユーザー)。入口条件表の条件 20 を「背景 job +
  worktree 隔離の wave 開始時 (最遅: clean-tree gate 直前)」へ更新

### F51. cleanup-branches が背景セッション自身の worktree を削除しかけた near-miss [手順漏れ]
- 事象: /cleanup-branches 実行セッションの cwd が削除対象 worktree に固定されており (背景 job)、
  スキル §2 の「先に main checkout 側へ抜ける」が実行不能だった — ExitWorktree は EnterWorktree
  未使用セッションでは no-op、Bash の cd は呼び出しごとに worktree へ reset される。dir 削除を
  実行していれば以後の全 Bash 呼び出しの cwd が壊れ、セッションが続行不能になっていた
- 根本原因: スキルが「抜ける」手段を対話セッション前提 (cd 持続 / ExitWorktree) で書いており、
  cwd 固定の背景セッションを想定していなかった
- 恒久対応: cleanup-branches §3 に縮退手順 (detach → branch -d → unlock まで、dir 削除と prune
  は引き渡し) を明記 (本エントリと同 commit)
- 再発検知: worktree list に detached HEAD の残骸が残っていれば引き渡し漏れを疑う (次回の
  /cleanup-branches 棚卸しが検出する)

### F52. 変異復元後の stale bytecode cache が同一バイト長変異を実効残留させた [手順漏れ]
- 事象: [T-153]/[T-158] wave の変異 matrix (2026-07-29) で、V11 (`10 * 1024 * 1024` →
  `20 * 1024 * 1024` の同一バイト長置換) をソース復元した後も、`tools/__pycache__` の変異版
  bytecode が「mtime 秒 + サイズ一致」で有効扱いされ、import 経路では上限 20MiB が生き続けた。
  直後の受入全走で本 wave が足した契約テスト 2 本が赤化して発覚 (fail-closed 方向の near-miss。
  M05 のソース内容比較は通っていた — 検出できない層に変異が残った)
- 根本原因: CPython の pyc 無効化は既定で mtime 秒 + サイズ。同一長置換を同一秒内に往復すると、
  ソース照合では検出できない bytecode 層に変異が残留する
- 恒久対応: 変異 harness は復元後に対象モジュールの `__pycache__` を無効化する (削除が最小)。
  本 wave の runner に実装し、台帳 `output/insights/2026-07-29_t153-t158-mutation-ledger.json`
  に事象を凍結
- 再発検知: 変異後の受入再走 (契約テストが残留変異を検出した実績)。M05 の内容比較だけを
  復元の証拠にしない
- 記録: worklog 2026-07-29 (47)

### F53. fix 子が親の一時退避ファイルを知らず同名の断片を新規作成した [文脈欠落]
- 事象: [T-139] wave 段 6 の fix 子 (fix6) が、親が commit II 用に job tmp へ退避していた
  evidence test (53KB) の不在を「未作成」と解釈し、自分の追加分だけの 1.4KB 断片を同名で新規作成
  した。後続 fix 子 (fix9) も旧凍結 hash の版から「復元」し、中間 fix の同期を欠落させた。
  いずれも親が hash/サイズ照合で検出し実害なし (near-miss)
- 根本原因: 退避は親のセッション内知識であり、fix prompt に「このファイルは退避中で親が管理する」
  という事実を書かなかった。子は tree の現状だけから判断する
- 恒久対応: 親が管理する退避 artifact がある間に子へ編集を依頼する場合、prompt に退避の事実と
  正本の所在を明記する。可能なら親が正本を tree へ一時復元してから投入する (fix10 以降で実施)。
  期待位置の再同期は literal 再ピンでなく production import で構造化する (fix10 の形)
- 再発検知: 退避中 hash と tree 上ファイルの サイズ/hash 乖離。受入全走の plain-runner meta-test
  が断片化を最初に検出した (自走 harness 欠落として)

### F54. 集約不変量だけの受入が、実装子へ委ねた未裁定の択一による要素単位の誤帰属を通しかけた [テスト代表性]
- 事象: [T-179] wave 段 6 の fix1 が、prompt 先頭が `段6の fix2 implementation author` の session を
  stage `author` へ分類するよう `STAGE_RULES` を変えた。実 10 session の再集計で 188,905 tokens が
  `fix` から `author` へ移動し、凍結済みの stage 別正本 (worklog (61)) と食い違った。
  このとき **総和 2,757,982・session 数 10・model_calls 434・worklog 突合 gate はすべて不変**
  だった (worklog の bucket が `author・fix` を合算するため gate も緑)。親が stage 別内訳を
  逐件で再照合して検出し fix2 で是正 (near-miss、成果物影響ゼロ)
- 根本原因: 二つが重なった。(a) 親の fix 指示が「到達不能な枝は消すか、到達可能にするか、
  どちらかに決めて理由をコメントに書く」と書き、**意味論の択一を実装子へ委ねた**。stage の定義は
  段 4 / 段 6 で親が裁定すべき事項だった。(b) 受入の目視対象が集約値
  (総和・件数・gate rc) に寄っており、要素単位の帰属が保存されているかを見ていなかった。
  集約が保存される誤帰属は集約検査を素通りする
- 恒久対応: (a) 実装子・fix 子へ渡す指示に**未裁定の意味論の択一を残さない**。選択肢を書くなら
  親がどちらかを裁定してから渡す。(b) 分類・帰属を伴う成果物の受入では、集約一致を正しさの根拠に
  しない (誤帰属の対でも集約は一致する = 循環論法)。**要素単位の独立 oracle と逐件照合**する。
  本 wave の実体 = `output/insights/2026-07-29_t179-worker-ledger-verbatim/README.md` の
  session_id→stage 表 (rollout の raw prompt から台帳の規則表と独立に導出) と、
  8 パターンの分類を固定した表駆動テスト
- 再発検知: 要素単位 oracle との逐件照合の赤 + `test_codex_worker_ledger.py` の
  `test_stage_rules_follow_wave_stage_not_role_words` / `test_stage_rules_keep_fix2_author_in_fix_and_focus_specific`
  (段番号が stage を決め役割語は決めない、を機械固定)
- 記録: worklog 2026-07-29 (64)、逐語 = `output/insights/2026-07-29_t179-worker-ledger-verbatim/`

### F55. 並行 dev-wave の正当な制御ファイルと先行 land を blanket dirt / unexpected main movement として扱い、後続 wave が取り込み不能になった [手順漏れ] [誤前提]

- **事象 (2026-07-29, [T-188] wave):** local main には別 session が所有する schema-valid handoff と
  `.codex/worktrees/` があり、対話型 dev-wave の最終 cleanliness はそれらを未知 dirt と区別できなかった。
  作業中には複数の先行 wave が main を正常に前進させたが、従来手順にはその新 upstream を監査し、
  wave へ merge、受入再走、新しい監査閉包を作ってから local main へ land する共通経路もなかった。
- **根本原因:** 「main checkout は完全 clean」と「開始時 main は不変」を session ownership や受入
  基準 SHA に結びつけず、共有 main の check-then-merge を直列化する機械 helper が無かった。
  `.gitignore` 拡張や他 session 成果物の片付けでは、strict consumer の受理集合または所有権境界を壊す。
- **恒久対応:** D102 / `DW-O23` / `tools/dev_wave_land.py`。形式が正しく Git admin と双方向束縛された
  制御面だけを非接触例外にし、common lock 下で tested main / tip / ordered closure と攻撃面を再検査して
  SHA 指定 ff-only を行う。stale / busy は fresh context へ返し、再監査と受入再走なしに再試行しない。
- **再発検知:** helper の境界 test と同一 base 二 wave の実 subprocess E2E。未知 dirt、偽 worktree、
  stale SHA、lock loser、non-FF、未監査 commit、gitlink postcondition 不成立をそれぞれ拒否する。
- 記録: worklog 2026-07-30 (67)、設計判断: D102、材料:
  `output/insights/2026-07-29_dev-wave-parallel-land/`

### F56. worker 起動の model / reasoning は要求値がそのまま receipt になり、不正値と未サポート model が silent に通る [誤前提]
- 事象: [T-182] wave の段 1 生死確認で、`codex exec` の起動構成が機械検査されていないことを 3 通り
  実測した。(a) `-c model_reasoning_effort="ultra"` (存在しない値) は `gpt-5.6-sol` /
  `gpt-5.6-luna` / `gpt-5.6-terra` で **rc=0 のまま成功**し、rollout の `turn_context` には
  `reasoning=ultra` が記録される。(b) ChatGPT account で未サポートの model
  (`gpt-5.4-nano`, `gpt-5.1-codex-mini`) は 400 で rc=1 になるが、rollout には session が生成され、
  receipt の `model` は**要求 slug のまま**で `model_calls=0` / `cli_reported=0` になる。
  (c) model により reasoning の受理集合が異なる (`gpt-5.4-mini` は `max` を拒否し
  `none`/`low`/`medium`/`high`/`xhigh` のみ)。成果物影響ゼロ (pilot 段階で検出)
- 根本原因: `DW-O01` は `model_reasoning_effort="<効いた値>"` と書いて起動者の注意に委ねており、
  「効いたか」を検査する経路がどこにも無い。さらに rollout receipt は**要求値の記録**であって
  served model の attest ではない — 実体名 (`gpt-5.4-mini-codex-1p-codexswic-ev3`) は 400 応答
  だけが露出し、成功した run には残らない。したがって「receipt に model と reasoning がある」ことを
  「その構成で実際に走った」証拠と読むのは誤前提である
- 恒久対応: (a) model×reasoning の比較や policy 採用を行う台帳は、要求値 (`requested_*`) と
  記録値 (`recorded_*`) を別名で持ち、**記録値を served identity の attest として扱わない**旨を
  出力自身に持たせる。(b) `model_calls=0` / `cli_reported=0` の session を「finding 0 件の観測」
  として集計しない (起動失敗と品質劣化を別分類にする)。(c) 未知の reasoning 値と model×reasoning の
  非対応組は起動前に落とす。実体化の所有は [T-183] (失敗分類) と [T-184] (policy 採用) にあり、
  [T-182] は実測と一次資料の凍結までを行った
- 再発検知: `output/insights/2026-07-29_t182-model-routing-shadow-pilot-verbatim/probe-receipts.json`
  の該当 session (`019fadd3-c15a-79e1-8783-f083061d4e3d` = nano、
  `019fadd3-c19c-7a12-bbf0-ded998aed815` = codex-mini、および `reasoning=ultra` の 4 session) が
  一次資料。機械検査は未実装 (上記所有 ID で実装する)
- 記録: worklog 2026-07-30 (68)、逐語 = `output/insights/2026-07-29_t182-model-routing-shadow-pilot-verbatim/`

### F57. Codex worker launcher の normal fake が32-worker全走だけで失敗し、失敗nodeが移動した [テストフレーク] [資源競合]

- **事象 (2026-07-30, [T-145] 段9再受入):** Pegasus計算ノードの32-worker全走2回で、
  `test_codex_worker_launch.py` の異なるnormal-control nodeが各1件、launcher returncode 1 /
  stderr空で失敗した。1回目はfullとprovenanceの同時走行、2回目はfull単独だった
- **分離できた範囲:** 各失敗nodeの直後の単独再走は1/1 green、同file直列は58/58 green。
  repository全走を16 workerへ下げると旧treeは3956 passed / 19 skipped、latest main統合treeは
  3965 passed / 19 skipped。T-145差分はlauncher実装・同test fileへ到達せず、32-worker時の
  失敗nodeも移動したため当該差分の回帰ではない
- **未確定:** fake normal controlの既定wall上限は3秒だが、pytest tmpは終了時に失われ、
  失敗時receipt / stop reasonを保存していない。従って3秒超過そのものを根本原因と断定しない
- **暫定対応:** 本受入は16 workerを採用し、赤い32-worker走をgreenとして数えない。恒久対応は
  [T-190]で失敗artifactを保存して原因を分離し、production wall-clock gateを緩めずtest fixtureを
  hardenする
- **再発検知:** 上記2 nodeの単独対照、同file直列、repository全走16/32-worker対照。
  記録: worklog 2026-07-30 (70)

### F58. gate の上限が、その gate を強制する装置自身の前処理コストで必ず違反した [自己不整合]
- 事象: [T-181] wave の run supervisor が `MAX_SCHEDULE_GAP_MS=60_000` を連続 run すべてへ適用したが、
  `supervise-pair` 起動時の snapshot oracle 検証が実測 **350,980 ms** かかるため、block 間の gap が
  必ず上限を超えた。block b2 の 2 run は **exit 0 で正常完走していた**のに
  `supervisor_failure: schedule gap exceeds bound` で technical-invalid になり、
  この 1 件で 10 run 全体が使用不能になりかけた (親が実走で検出)
- 根本原因: 「隣接性」という科学的要求を単一の数値上限へ畳み、その上限を**同じ装置の前処理コストと
  突き合わせずに**決めた。静的レビュー 5 巡は数値の妥当性を実測できないため通過した
- 恒久対応: gate の上限を導入するときは、**その gate を強制する経路自身がその上限を満たせるかを
  実測で確認**する。満たせないなら文脈で分ける (本件は intra-block 60 秒 / inter-block 900 秒)。
  実 gap は全 receipt に記録し、結論には実測値を併記する

### F59. 事前登録変異の期待 node が実効 gate を検査しておらず、新設防壁に対応テストが無いことを露出させた [テスト代表性]
- 事象: [T-181] wave で事前登録した変異 M6 (読取時 packet digest 束縛の無効化) が SURVIVED し、
  DW-M04 に従って両層同時変異 M6p (読取時 + freeze 時 digest) を追加登録してもなお SURVIVED した。
  原因は M6 の期待 node にしていたテストが実際には **reader 間の不一致処理**を検査しており、
  packet 本文の swap→restore を一切検査していなかったこと。すなわち直前の fix で入れた
  防壁に**対応テストが存在しなかった**。swap→restore を実再現するテストを追加して kill 12/12 になった
- 根本原因: 変異の事前登録で「期待 node」をテスト名の**語感**で割り当て、その node が当該 gate を
  実際に通過するかをコードで確認していなかった。gate を新設した fix が、
  同じ変更でその gate の負例テストを持たなかったことも重なった
- 恒久対応: (a) gate を新設する変更は、**その gate を無効化したら赤くなる負例テストを同じ変更に含める**。
  (b) 変異の期待 node は、対象 gate を実行するテストであることをコードで確認してから pin する。
  SURVIVED は mask を疑う前に「そもそも対応テストが在るか」を先に確認する

### F60. 実走後の装置修正が、凍結成果物の replay 認証を失わせた [順序]
- 事象: [T-181] wave で 10 run の実走後に oracle を 2 度修正した (上流 token 異常の分類、
  stale commit-graph の除去)。その結果 `aggregate` / `verify` が全 10 run で
  `snapshot oracle replay mismatch` を返し `experiment_complete=false` になった。
  各 run が実走時に記録した `snapshot-before.json` は修正前の版の出力であり、
  現在の版では再現できない。receipt 側は最終版コードで全 run を再収集して解消できたが、
  実走時 oracle の再生成は provenance の改竄になるため行わず、数値は **replay 未認証**として記録した
- 根本原因: 実走の前に装置を凍結せず、実走で露出した欠陥を実走後に直した。
  欠陥修正自体は正しいが、修正が受入検査の出力形を変えるため、既存 artifact の replay が成立しなくなる
- 恒久対応: live 実走を伴う wave では、(a) 実走開始前に装置を凍結し版を receipt へ pin する。
  (b) 実走後に装置を直す場合は**再走を伴うと最初から明記**し、再走しない場合は成果物を
  「replay 未認証」と明示して下流の採用根拠にしない。既存の `experiment_complete=false` が
  この不整合を fail-closed で検出することは確認済み (隠れない)
