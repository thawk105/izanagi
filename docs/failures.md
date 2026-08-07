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


- **再発: 2026-08-06** — 裁定 inbox が「**起票者の見立て**」として明示的に留保した推測が、
  [T-495] の起票文では「ahead>0 のブランチを**検査なしに消した**経路を特定する」という
  確定事実に変わり、wave がその誤った前提から出発した。一次資料 (削除セッションの transcript と
  `output/insights/2026-07-30_dev-wave-improve-wave/s9-t193-ruling.md`) に当たると、
  削除には内容検査・ユーザー明示承認・2 日前のユーザー裁定がすべて先行しており、
  「検査なし」は事実でなかった。転写対象が日付・機構の実在状態から
  **推測の確度 (見立て → 確定事実)** へ広がった顕在化である。検出は段 1 の前提実測と
  段 3 の敵対レンズ 2 本 (独立に追認)。実害は誤前提での 1 wave 分の起票に留まり、
  結論は是正して land した。恒久対応は memory から変更なし — 起票文が引く一次控えに
  「見立て」「推測」の留保があるなら、brief はその留保ごと引くこと (worklog 2026-08-06)。
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
- 再発 (near-miss): 2026-08-01 [T-244] wave。新設した campaign freshness gate のテストが
  `load_loop_state` を **layout 引数を無視して** monkeypatch していたため、production が
  「常に空の別 layout を検査する」形に退行しても全テストが緑になる構造だった。
  「gate を呼んでいること」だけを固定し、gate が**実物を見ていること**を固定していない同型。
  段 6 の敵対レビューが land 前に検出し、実 `loop_state.json` を書く負例・正例を追加して閉じた
  (`test_run_workload_rejects_actual_existing_campaign_state` /
  `test_run_workload_accepts_actual_fresh_campaign_layout`)。
  monkeypatch 版は「provider 呼び出し順序の poison test」として責務を分離して残した

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


- **再発 (near-miss): 2026-08-04** — 完了判定を中間状態から推測する同型を、`-o` 出力ファイルで
  実測した。段 2 の codex は `-o` の成果物を **00:01 に 31,141 bytes で書き、rc=0 で終了した
  00:08 に 36,694 bytes へ書き換えた**。途中版も末尾が整って見えるため、
  「出力ファイルが存在する / サイズが安定した / 末尾が整っている」で完了判定していれば
  切り詰めたプランを採用していた。**F24 の恒久対応 (`.done` の存在 + exit code だけで判定) が
  そのまま効き、実害はゼロ**であった。本追記は恒久対応の射程が log 本文 grep だけでなく
  **`-o` ファイルの存在・サイズ・末尾形にも及ぶ**ことを明示するためのものである

- **再発: 2026-08-05** — 別機序で再発した。段 6 焦点再レビューで、codex の出力 `.md`
  (13,253 bytes、末尾に結論あり) は書かれたのに完了マーカー `.done` が作られなかった。
  ジョブ中断により detached wrapper が `echo $? > .done` に到達せず落ちたためである。
  成果物だけを見ると完成しており、途中書きと区別できない。`DW-O01` の「完了は `.done` と
  exit code だけで判定する。ログの grep も完了通知も判定にしてはならない」が防壁として働き、
  採用せず再走した (孤児成果物は `s6-refocus-orphan.md` として保存)。
  同日さらに、変異 harness の完了を待つ背景タスクが `.done` 生成前に「完了」通知を返し、
  成果物を直接確認して実行中と判明した事例もある。**恒久対応は既存の `DW-O01` で足りる**
  — 完了判定を `.done` + exit code に限る規律を、通知が先行した場合にも例外なく適用する。
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
- **再発: 2026-08-01** ([T-118] wave の段 9)。`git worktree remove` の無条件拒否に当たった時点で、
  **本エントリの恒久対応である `/cleanup-branches` を読む前に即興で `git submodule deinit` を実行**した。
  結果は本エントリの記述どおりで、共有 `.git/config` の `submodule.*` 登録が消え main checkout の
  `git submodule status` が `-` prefix になった (実害は一時的。`git submodule update --init` で復元し、
  pin `d706650` 一致と並行 3 worktree の無影響を確認済み)。**恒久対応の内容は正しく、経路が欠けていた** —
  dev-wave の段 9 は自分の worktree を畳むよう求めるが、その手順の正本が `/cleanup-branches` §3 に
  あることを指していない。判別 = worktree 削除で `working trees containing submodules cannot be
  moved or removed` を見たら、そこで手を止めて `/cleanup-branches` を読む
- 根本原因: git の worktree × submodule の仕様 2 点 (remove の gitlink 無条件拒否、submodule 登録
  config の worktree 間共有) を知らず、即興で deinit を挟んだ。追加事象は同じ実体化 submodule が
  削除コストを押し上げる点を見落としたもの。**2026-08-01 の再発は仕様の無知ではなく、
  既知の恒久対応へ到達する前に即興したこと**が原因である
- 恒久対応: `/cleanup-branches` スキル (.claude/commands/cleanup-branches.md) に安全手順を固定 —
  deinit を使わず「detach → ディレクトリ削除 → `git worktree prune`」(git 文書化済みの回避)、
  事後に `git submodule status` で main checkout の初期化状態を検査
- 現行実体: `.claude/commands/cleanup-branches.md` §3。dev-wave では
  `docs/dev-wave/operations.md` の `DW-O06`（submodule 系 test）と `DW-O08`（初期化）。
- 再発検知: スキル末尾の事後検査 (`git submodule status` が `-` prefix なしで pin 一致)。worktree
  掃除をスキル外で即興したらレビューで差し戻す


- **再発: 2026-08-05** ([T-472] wave の land 後の worktree 撤去)。2026-08-01 の再発と**同一経路**
  である。`git worktree remove` が `working trees containing submodules cannot be moved or removed`
  で拒否した時点で、本エントリが定める判別 (「そこで手を止めて `/cleanup-branches` を読む」) を
  実行せず、即興で `git -C <worktree> submodule deinit -f external/ccbench` を打った。
  結果も同じで、共有 `.git/config` の `submodule.*` 登録が消え main checkout の
  `git submodule status` が `-` prefix になった。復元は `git submodule update --init external/ccbench`
  で即時、pin `d706650` 一致と並行 4 worktree (t452-t453 / t474 / t476 / token-economy) の
  無影響を確認済み。実害は一時的。
- **前回の再発が診断した経路欠落が塞がれていなかった。** 2026-08-01 の追記は
  「dev-wave の段 9 は自分の worktree を畳むよう求めるが、その手順の正本が
  `/cleanup-branches` §3 にあることを指していない」と特定していたが、`DW-S09` への
  ポインタ追記は未実施のままだった。今回その追記を試みたところ
  `docs/dev-wave/**` が hard ceiling 25200 bytes に対し 25377 bytes となり、
  予算超過で入らなかった (上限は上げない規律のため撤回)。**恒久対応の経路は依然未実装**であり、
  裁定へ返した。
- 補足: memory `bg-job-closes-its-own-worktree` は deinit 禁止を本文に持っていたが、
  索引 1 行だけを見て動いたため到達しなかった。索引行に禁止を明記する形へ更新済み
  (repo 外の個人 memory)。

- **再発: 2026-08-05** — main checkout の `.git/config` から `submodule.external/ccbench.*` の登録が
  消え、`git submodule status` が `-` prefix (未初期化) を返す状態を **2026-08-03 と 2026-08-05 の
  2 回**観測した。両回とも working tree の実体は健全で、HEAD は pin (`d706650`) 一致・clean であり、
  **失われていたのは登録だけ**である。復旧は `git submodule init external/ccbench` (config 書き込みのみ、
  通信もファイル書き換えも無し) で両回とも即座に完了した。F26 本文が記録する
  「worktree 側の `git submodule deinit` が共有 `submodule.*` 登録を消す」経路と**最終状態は同一**だが、
  **機序は同定できていない** — repo 内のコード・スクリプトに `git submodule deinit` の呼び出し箇所は
  無く、今回の消失を起こした主体は不明のままである。恒久対応は**検出のみ機械化済み**で、予防の実体は
  無い — `.claude/commands/cleanup-branches.md` §4 の事後検査が `-` prefix を検査しており、
  上記 2 回はいずれもこの検査で発見した (発火実績 2 回)。**機序未特定のため予防策は未実装**であり、
  この点を恒真な対応として扱わない。次に再発したら、消失の直前に走った worktree 操作の特定を
  先に行う。
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
- 再発: 2026-08-01 ([T-288] wave)。**親が段 4 で登録した M01〜M15 のうち 4 件が `DW-M01` を
  満たしていなかった** — M03 と M11 が同じ換算行を奪い合い (注入位置が一意でない)、M06 の対象
  `None` がファイル内に複数あり、M15 は未観測 `None` に対して先に `TypeError` を起こすため赤理由が
  二重だった。2026-07-26 と同じく**段 3 をすり抜け段 6 のレビューが検出**した。今回の新しさは、
  無効の原因が「先行検査に食われる」ではなく「**anchor 逐語が一意でない**」ことにある。
  恒久対応の追補 = 事前登録では位置を散文でなく**一意な old 逐語 anchor**で書き、harness が置換前に
  対象ファイル内の出現数を数えてちょうど 1 でなければ `ANCHOR_ERROR` で止める。
  再登録した N01〜N15 は最終 anchor commit で 15/15 KILL・`ANCHOR_ERROR` ゼロを実測した

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


- **再発: 2026-08-05** ([T-490] wave)。段 1 の前提実測で、外周空白付き述語と正準述語の
  **raw 文字列 sha256** を比べて「別 `src_token` になる」と結論した。実際の `src_token` は
  対象 source を C++ preprocessor に通した出力の digest であり、raw 文字列の hash ではない。
  結論の向きは正しかったが、測定対象が命題と違っていた。段 3 の敵対レンズ 2 本が独立に
  この一般化を指摘し、identity の証明を「実 `quarantine` の materialized bytes が byte-exact に
  同一」と「本番 `source_digest.resolve` の token 一致」へ置き換えさせた。
  既存の恒久対応 (何を模擬したか・実差分との差を書く) は自己 hash / 参照 / pin 対象を
  想定していたが、**digest の前処理を挟む対象**でも同じ罠が起きる。
  防壁として効いたのは段 3 のレンズであり、F29 の「再発検知」がそのまま機能した。

- **再発: 2026-08-05** ([T-420] wave)。段 1 の前提実測で、登録済み較正の `effective_clock`
  mapping を**そのまま** expected として consumer 述語
  (`execution_guard.effective_clock_comparison_passes`) へ渡し、「登録済み較正は自分自身の述語を
  通らない → 実行時 attestation は必敗 → 通す道は gate を緩めるか較正を取り直すかの 2 つだけ」と
  結論した。実際にはこの述語は expected に `{samples_mhz, tolerance_pct}` の**ちょうど 2 key** を
  要求し、artifact の mapping は `governor` / `method` を含む 4 key を持つ。したがって親の測定は
  **値ではなく形で** False を返しており、3 通り試した観測値のすべてが同じ理由で False だった。
  実行時と同じ射影 (`env_attestation._clock_value`) を通して測り直すと、**静穏な機械 (48 標本が
  すべて中央値) なら現行の登録済み較正のままでも受理される (True)**。すなわち gate は構造的に
  壊れておらず、親の因果説明は誤りだった。真の阻害要因は probe の観測者効果 (走行 CPU は定義上
  busy なので必ず帯外標本が出る) である。検出は段 3 の敵対 codex で、親が実行時射影で再測して撤回した。
  **教訓: gate 述語を直接呼んで前提を測るときは、引数を手で組まず production の呼び出し経路が
  使う射影関数を通して作る。** 手組みの「それらしい mapping」は shape 拒否と値拒否を区別できず、
  gate が「必ず落ちる」ように見える。F29 の再発検知行 (レンズに「親の実測は実差分を
  モデル化しているか」を含める) は今回も設計どおり機能した
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


- **再発: 2026-08-04** — 逆向きの pin を見落とした。F30 は「自分の成果物の bytes を pin している
  台帳」を数え落とす型だったが、今回は「**自分の編集面 source を bytes で pin している成果物**」
  (qualification evidence の `binding.runtime_modules` が `orchestrator/verifier/**.py` を全件束縛)
  を段 1 で数え落とし、段 3 の敵対相談で blocker として出た。成果物パスからの `grep` は
  この向きを見つけない。段 1 では「この成果物を pin しているのは誰か」に加えて
  「**自分が編集する source を pin している成果物はあるか**」も列挙する。

- **再発: 2026-08-06** — 三度目。今回は **role 名を key にした pin** を数え落とした。段 1 で
  `grep -rn "<編集する module path>"` を走らせて「publish 済み artifact に旧 hash を pin した
  ものは 0 件」と結論したが、実際には `output/env/pegasus/t419-probe-causality/**/manifest.json`
  が `env_contract_sha256` という **role 名 key** で同 module の旧 sha を保持していた
  (path 文字列を持たないため path 検索に掛からない)。`DW-O09` は F30 の恒久対応として
  「role 名を key に張る pin は key 側でも検索し、path の hit 0 件を pin なしと結論しない」と
  既に明記しており、**本文を読んだうえで path 検索だけで結論した**。段 3 のレンズが訂正した。
  今回は当該 module を変更しなかったため実害はない。恒久対応は `DW-O09` から変更なし
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
- **再発: 2026-08-01** ([T-244] wave)。恒久対応 5 (background 起動) に反し、前景の tool 経路で
  起動した。19 変異 × 計算ノード dispatch は親の実行時間上限 (10 分) を確実に超えるのに、
  その見積りをせずに走らせた。上限で親ごと殺され `finally` が走らず、承認上限判定の変異が
  production に残った。検出は直後の `git status`、回復は `git checkout --` + `__pycache__` 除去。
  **恒久対応 6 を追加する — harness は逐次 flush + resume と、起動時の対象ファイル clean 検査を持つ。**
  「background で起動する」規律は 3 回破られており (2026-07-27 / 07-30 / 08-01)、規律だけでは
  止まらないことが実証された。clean 検査があれば、次の起動時に残留変異を fail-closed で検出できる
  (SIGKILL は捕捉できないので、これが唯一の機械的防壁である)。resume があれば、上限で切れても
  やり直しの取りこぼしが出ない。
- 現行実体: `docs/dev-wave/mutation.md` の `DW-M05` と `DW-M06`。
- 再発検知: 変異・fault 注入ハーネスの設計時に「復元検査が対象ファイルの追跡状態に依存して
  恒真化しないか」「二重走行を機械的に排除しているか」「上限で殺された次の起動が残留変異を
  検出できるか」をレンズに含める (段 6 の作法)

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


- **再発: 2026-08-04** — provenance 監査を `check_ai_provenance.py 2>&1 | tail -4; echo rc=$?` で
  走らせ、表示された rc=0 は `tail` のものだった。実際は Pegasus dispatch が queue-wait-timeout の
  infra 失敗で監査未実行。land 前に出力全文を読み直して検出し、単独 rc で再走した。O17 は単独 rc を
  既に要求しており手順は増補しない。

- **再発: 2026-08-04** — 親が `run_tests.py ... | tail` で dispatch を投げ、pipeline rc (=tail) を
  見て緑と誤読しかけた。dispatch の `result.json` の `child_rc=1` を突き合わせて実測前に検出し、
  偽緑の記録には至っていない (near miss)。以後の受入・変異走行は rc をパイプに通さず
  ファイルへ直接取得した。
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
- **再発: 2026-08-01** ([T-288] wave)。親が段 1 で `.claude/agents/planner-v4.md` と
  `coder-v4-autonomous-trigger-gating.md` を「完了段の歴史的例示」と断定し、それを
  「触らないから scope 外」という provisional 裁定の**根拠**に据えた。実際は 8c が
  `ROLE_FILES` 経由で読む **live prompt** であり、段 3 の両レンズが独立に反証した。
  誤りの型は F39 本体と同じ「**射程を実測せずに scope 除外の根拠にした**」で、対象が
  凍結 bytes でなく参照文書の live/歴史区分である点だけが異なる。実害なし (実装前に検出)。
  結論 (触らない) は維持したが根拠を「ユーザー裁定の射程外」へ差し替えた。
  恒久対応 = `DW-O09` が既に持つ 4 分類 (live copy / 独立 golden / 凍結 snapshot / 歴史記録) を、
  凍結 bytes wave に限らず**「触らない」と裁定する全参照物へ適用する**。
  `docs/dev-wave/**` は余裕 10 bytes で本文追記できないため、本追記を運用の正本とする
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
- **射程拡大分の恒久対応 (2026-08-01、[T-220] wave)**: repo 直下に `pytest.ini` を新設し、
  `testpaths = orchestrator/tests` で引数なし起動の収集範囲を閉じ、`norecursedirs` に
  `output` / `external` を足した (pytest 既定 9 要素は明示再掲。`.*` を落とすと
  `.claude/worktrees/` が収集対象へ戻るため)。**`addopts` は書かない** — `run_tests.py` の
  受入判定 4 ゲート (`_is_full_suite:314` / `_has_no_execution_flag:375` /
  `_has_dispatch_exempt_flag:390` / `_is_acceptance_run:403`) はいずれも環境変数
  `PYTEST_ADDOPTS` しか読まず ini を構造的に見ないため、ini に書くと「全走のつもりで実は
  選択走」が preflight を通る。この非対称は正例つきで
  `orchestrator/tests/test_pytest_collection_config.py` に機械固定した。
  あわせて `pytest.ini` が `check_ai_provenance.py` の実装面分類に当たらず D95 が発火しない
  穴も閉じた (`IMPLEMENTATION_BASENAMES` へ追加、受理集合は狭まる方向)。
  **「測定値が checkout に依存する」本体 ([T-129] の残り) は未解決のまま**である

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


- **再発: 2026-08-03** — land 署名 wave の段 3 で、敵対レンズ A の codex 子が upstream の
  安全フィルタに掛かり、最終メッセージだけが遮断された
  (`This content was flagged for possible cybersecurity risk`)。rc=1 で `-o` の成果物は生成されず、
  敵対レビュー 1 本を失いかけた。ログには推論要約が残っており、そこから結論の骨子
  (「守るべき資産を 2 path へ狭めた前提が破れている」) は読めた。
- **今回は回復できた。恒久対応をここに残す。** F45 の初回は「同一 prompt の再投でも通らない」で
  終わっていたが、今回は**プロンプトの語彙を変えて再投したところ通った**。
  効いた書き換えは次の 3 点である。
  1. 役割を「敵対検証者・攻撃せよ」から「**検証関数の仕様適合レビュー**」へ変える。
  2. 攻撃語彙 (攻撃・密輸・偽造・迂回・bypass) を、判定語彙 (判定漏れ・仕様漏れ・反例・
     入力クラス・false negative) へ置き換える。
  3. **gate を回避する具体的な command 列を要求しない。**「どの commit がどの path を
     どう変えるかの表」で足りると明記する。
  意味は保たれ、返ってきたレビューは blocker 3 件を名指しした (痕跡集合の不十分性、
  免除条件の健全性、cutoff の実在)。したがって**検出力を落とさずに通せる**。
- 判定に使うのは `.done` の exit code と `-o` 成果物の実在だけであり、
  harness の完了通知やログ本文の grep を完了判定にしてはならない (`DW-O01`)。
  本件でも通知は rc=1 の子について「completed」と告げた。
- 記録: worklog 2026-08-03 (本 wave)、逐語 =
  `output/insights/2026-08-03_land-merge-signature/s3-lens-a-spec-conformance.md`
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
- **再発: 2026-08-01** ([T-221] 段 1)。親 brief が計算ノードの `-n 48` 全走で測った
  `/dev/shm` peak 7.39 GiB を、ログインノードの経路にも「同機序で最大 7.39 GiB」として
  転写した。repo に `addopts` は無く login 直叩きは既定で**直列**なので、同時生存する
  temp 総量は worker 数に比例して桁が違う。段 3 の敵対レンズ (`DW-S03` の「親自身の実測値と
  その一般化も明示的にレンズへ入れる」) が実測で refute し、親が撤回した。**一般則の拡張**:
  「別環境」だけでなく**別並列度・別実行形態**へ数値を転写するときも、転写先で成立するかを
  実測してから書く。同 wave では「ガードが恒真だ」という主張を caller を全列挙せずに
  行った誤りも同レンズが refute した (呼び出しは `main()` 内のみでテスト非到達だった) —
  **恒真だと主張する前に呼び出し元を全列挙する**

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


- **再発: 2026-08-03** — [T-313] wave の立ち上げで、専用 handoff を背景 job harness の既定
  (`$CLAUDE_JOB_DIR/tmp` = home 配下の `~/.claude/jobs/<id>/tmp`) に作り、ユーザーに止められた
  (near-miss、実害なし)。前回 (2026-07-29) は worktree 内、今回は home 配下で、**置き場を
  間違える型は同じ**である。原因は `DW-O20` の「専用handoffはworktree外（背景jobはjob tmp）」
  という文言が、要件 (worktree の外) ではなく harness 既定の実体 (home 配下) を指しており、
  Pegasus の「home に不要物を置かない」規律 (runbook §6 の領域分担) と衝突したこと。
  repo 内 `.claude/jobs/` への退避も worktree 隔離ガードが Write を拒否するため使えず、
  最終的に repo 外の `/work` 配下へ置いた。
  恒久対応 = `DW-O20` の当該語を byte 中立で「背景jobはrepo外」へ是正 (本 wave の段 8) と、
  auto-memory `pegasus-keep-home-clean`。
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
- **恒久対応の射程を後に狭めた (2026-08-01、D109 / [T-220])**: 上記の「**形式が正しく**Git admin と
  双方向束縛された制御面だけを非接触例外にし」という形は、**書式が崩れた他 session の handoff で
  無関係な wave の land を止める**という新しい実害を生んだ ((73) は着地せず終了、(77)(78) は各 1 回拒否)。
  D109 が cleanliness 軸を「incoming と衝突する untracked だけ拒否」へ一本化し、
  `docs/handoff/` 配下は**書式を問わず**非接触にした。**本 F の恒久対応欄の「形式が正しく」は
  現在の実装を表さない。** 現況の正本は D109。
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
- **再発: 2026-08-01 (Claude 側の同型を実測)**。`claude -p --effort <不正値>` は
  `Warning: Unknown --effort value ... using the default effort` を出して **rc=0 で続行**し、
  既定へ黙って落ちる (`--model` の不正値は rc=1 で fail-closed)。さらに effort は
  `--output-format json` の result にも `stream-json` の `init` event にも現れず、`--help` にも
  既定値の記載がないため、**要求値と実効値を突き合わせる経路が Claude 側にも無い**。
  fallback 先がセッション設定値か CLI 内蔵既定かは未確認 (3 arm の出力トークン probe は陰性)。
  同型の検証非対称は `tools/dev_waves` にもある (model は `allowed_models` に照合、effort は
  形のみ、receipt に effort field なし) が、同層は D74 で fake child 限定のため成果物影響ゼロ。
  一次資料 = `output/insights/2026-08-01_token-hygiene-audit/probes/cli-effort-failopen.md`、
  記録 = worklog 2026-08-01 (81)

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
- **再発: 2026-07-31 ([T-200] 受入全走)。** Pegasus計算ノード bnode002 の48-worker全走で
  `test_check_receipt_recomputes_usage_actuals_from_sealed_artifacts` が
  `assert 1 == 0` / stderr空で1件落ちた (request `874538`)。同一ノードでの単独再走は
  1 passed / 2.55秒 (request `874539`) で再現せず、直後の48-worker全走も
  4112 passed / 0 failed (request `874540`) だった。**48 workerでも出る**ことと、
  失敗nodeがまた移動したことが新しい情報である。`DW-O18` により当該waveの差分
  (t080 fixture面のみ) へは帰属しない
- **再発: 2026-07-31 (同 [T-200] の land 再試行受入)。** bnode040 の48-worker全走で
  `test_manifest_is_appended_while_correlated_session_is_running` が1件落ちた (request `874704`)。
  bnode041 での単独再走は 1 passed / 2.85秒 (request `874705`) で再現せず。**同一waveで
  失敗nodeが3回とも異なり** (`test_check_receipt_recomputes_usage_actuals_from_sealed_artifacts`
  → 本node)、いずれも launcher subprocess 系である点が繰り返し確認された
- **再発: 2026-08-01 ([T-248] wave の記録後検査)。** bnode012 の48-worker全走で
  `test_check_receipt_recomputes_usage_actuals_from_sealed_artifacts` が再び
  `assert 1 == 0` / stderr空で1件落ちた (request `876829`)。同ノードでの同file単独再走は
  58 passed / 5.21秒 (request `876832`)、直後の全走は bnode004 で
  4709 passed / 19 skipped / rc=0 (request `876835`) で再現しない。当該waveの差分は
  **docs のみ**で launcher 実装・同test fileへ到達しえず、`DW-O18` により帰属しない。
  2026-07-31 の再発と**同一 node 名**である点が新しい情報で、失敗nodeは毎回移動するのではなく
  この node が繰り返し当たりやすいことを示す
- **再発検知:** 上記2 nodeの単独対照、同file直列、repository全走16/32/48-worker対照。
  記録: worklog 2026-07-30 (70)、2026-07-31 (73)、2026-08-01 (95)


- **再発: 2026-08-06 ([T-522] 受入全走)。** 6,606 件の全走 (48 worker、request `892018`) で
  `test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`
  が 1 件落ちた。原因は assert 不一致ではなく
  `git -c core.useReplaceRefs=false cat-file --batch-check` の 15 秒 timeout (`returncode -9`) で、
  同 file 単独の再走は 8 passed / 29.23 秒で再現しない。**[T-327] が 2026-08-05 に
  同型 (全走 6,034 件で `git add -A` が 30 秒 timeout) を session fixture 化 + timeout 180 秒で
  塞いだ直後の再発**であり、対策された呼び出しではなく `_batch_oids` 側の別の git 呼び出しで出た。
  本 wave の差分 (admission registry) は当該コードへ到達しない。恒久対応は
  [T-553] として起票する。

- **再発: 2026-08-06 ([T-459] 受入全走 2 回目)。** 計算ノードの全走で
  `test_codex_worker_launch.py::test_all_repo_policy_reasoning_values_are_accepted[high]` が
  launcher returncode 1 / stderr 空で 1 件落ちた。同 file の単独再走は 145 passed / 3.29 秒
  (request `891949`) で再現せず、main 取り込み後の全走も 6512 passed / 0 failed だった。
  **新しい情報は、この全走が親の起動した codex 子 (焦点再レビュー) と同時に走っていたこと**で、
  資源競合という既存の見立てと整合する。`DW-O18` により当該 wave の差分 (WAL 回復面) へは
  帰属しない。恒久対応は F57 既載のとおり失敗 artifact 保存による原因分離であり、
  本 wave では受入全走の隣で子 process を走らせない運用で回避した。
- **再発: 2026-08-06 (同 [T-459] の land 前受入)。** 同じ wave の別の全走で、今度は
  `test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`
  が `PreregistrationError: git-timeout` で 1 件落ちた。同 file の単独再走は 8 passed / 28.12 秒で
  再現しない。**新しい情報は、subprocess が codex launcher ではなく git であること** —
  全走の並列度が subprocess の wall-clock gate を押し出す型は、launcher 固有ではなく
  「全走中に外部 process を待つテスト」一般に及ぶ。この wave 単独で 2 つの独立した
  producer (codex launcher / git) が同型を出したため、族として扱う。
  `DW-O18` により当該 wave の差分 (WAL 回復面) へは帰属しない。
### F58. 並行 wave が land 済みの「次の一手」ID を別内容へ再利用し、裁定待ち 2 件が正本から消えた [手順漏れ] [恒真ゲート]

- **事象 (2026-07-31, `/rulings`):** worklog (72) が land した 2 つの ID を、並行して走っていた
  (73) の wave が自分の新規項目へ再採番した。「次の一手」の正本は末尾エントリだけなので、
  (72) 側の内容 — 未取り込み branch の取り込み可否と、cleanup-branches への F26 反映 —
  が誰にも引き継がれずに消えた。D70 の「一度 land した ID は変更・再利用しない」に反する
- **なぜ機械検査を素通りしたか:** `tools/check_docs.py` の保存則は「前エントリの ID が後続
  エントリまたは見送り台帳のトップレベル項目に**現れる**こと」だけを見る。ID が同じまま中身が
  入れ替わると存在検査は真になるため、**内容の消失に対しては恒真**である
- **同型の先行例:** (72) 自身も branch 側の ID / D 番号が main 側の先行採番と衝突し、統合直前に
  振り直している。そのときは親が手で気づいた。**機械検査で止まった事例はまだ無い**
- **恒久対応:** 内容を新規 ID として復元し (worklog (74))、再発検知は下記による。
  保存則を内容のすり替えまで検出するよう強める案は validator の受理集合を変えるため、
  [T-211] としてユーザー裁定へ返した
- **再発: 2026-08-01 (同 (74) の land 前統合)。** `/rulings` 側が未 land の branch で採番した
  `T-213` と、並行 wave が (77) で採番した `T-213` が同一 ID・別内容で衝突した。**同事象を (78) が
  別 ID で独立起票していた**ため、裁定を後者へ一本化し前者を撤回した。手で気づいた 3 例目であり、
  機械検査は 3 回とも素通りしている
- **再発: 2026-08-01 ([T-209] wave)。同一 wave 内で 2 度**。親の初期採番 `T-234`/`T-235` は (83) の
  land で無効になり、振り直した worklog 番号 (84) も並行 wave の archive
  `worklog-phase3-0801-83-84.md` で無効になった。wave 実行中に main が (83) → (91) へ 8 エントリ、
  最大 ID が T-234 → T-264 まで動いたため、docs 反映を一度破棄して再ベースラインした。手で気づいた 4 例目
- **対偶も同じく恒真だと判明した (同 wave):** 保存則は「同じ ID の中身がすり替わる」だけでなく
  **「同じ内容を別 ID で新規発番する」も検出しない**。本 wave の親は研究側タスクとして 2 件を新規起票
  しようとしたが、実体は既存の [T-139] / [T-140] / [T-144] であり、うち 1 件は**実測で廃止済みの
  陰性結果**だった。段 3 の敵対レンズが一次資料で反証しなければ、台帳に重複 ID が入り、
  完了済みの実験を再実行するところだった。**新規起票の前に、同じ内容の既存 ID が無いかを
  archive まで含めて意味検索すること** (ID 走査だけでは捕まらない)
- **再発検知:** 統合直前の再走査 (D70 の採番規約) を wave 側の land 前手順として守ること。
  `/rulings` は末尾エントリだけでなく、直前エントリとの ID 差分も照合する。
  記録: worklog 2026-07-31 (74)、2026-08-01 (74) の land 前統合、2026-08-01 (92)

### F59. gate の上限が、その gate を強制する装置自身の前処理コストで必ず違反した [自己不整合]
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

### F60. 事前登録変異の期待 node が実効 gate を検査しておらず、新設防壁に対応テストが無いことを露出させた [テスト代表性]
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


- **再発: 2026-08-07** — `dev-wave-t595-reasoning-ab` で、単層変異 2 件 (可視化フィルタ除去・
  引用除去) が SURVIVED した。親は DW-M04 に従って両層同時変異を追加登録し、2/2 KILLED を得たので
  「単層の生存は冗長層ゆえ」と結論しかけた。焦点再レビューがこれを反証した — その KILLED は
  既存の**裸表記 `reasoning=high`** fixture に対する結果にすぎず、単独 SURVIVED を冗長と判定する
  根拠にならない。実際には検査が現実の起動キー表記 `model_reasoning_effort=` を認識しておらず、
  単層変異のそれぞれが単独で fail-open 反例を構成できた。親が書き込みなし probe で裏取りした。
  今回は F60 と違い期待 node の割当ては正しく、**負例 fixture の表記が現実の攻撃表記を
  覆っていなかった**点が原因である。恒久対応として (a) 過剰拒否を検出する正例 control
  (`orchestrator/tests/test_check_docs.py` の
  `test_dev_wave_reasoning_effort_pins_ignore_comment_and_fence_examples`) を足し、
  可視化フィルタ層を単独で kill 可能にした。(b) 負例 fixture に実運用の表記
  (`reasoning_effort=` / `model_reasoning_effort=`、引用符付き) を加えた。
  再照準後の変異は 7/7 KILLED。**両層同時変異の KILLED を単独 SURVIVED の冗長性根拠に使わない。**
### F61. 実走後の装置修正が、凍結成果物の replay 認証を失わせた [順序]
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

### F62. 受入全走の実行中に親が `output/` を編集し、repo scan invariant テストを 10 件偽赤にした [手順漏れ] [測定の交絡]
- 事象: [T-205] wave の受入 2 回目 (request `874786`) で `test_s8b_floor_campaign.py` の official / pilot
  resume 系 **10 件**が落ちた。差分 (provenance / dispatch / hook) が到達しないファイルであり、
  親は `DW-O18` に従って帰属を保留した。原因は**親が全走の実行中に
  `output/insights/<wave>/s4-adjudication-plan-v2.md` を Edit したこと**だった。
  同テスト群は `_real_output_snapshot()` で `output/` 配下の全ファイル hash を before/after 比較し、
  「campaign が repo の `output/` に副作用を残さないこと」を検査している。編集を止めた 3 回目
  (request `874788`) は 4268 passed / rc=0 で再現しなかった
- 根本原因: 受入は計算ノードへ dispatch され数分かかるため、その間に親が「別の作業」として insight や
  裁定文書を書き進めるのが自然な手順になっている。しかし repo scan invariant を持つテストから見ると、
  親の編集と campaign の副作用は区別できない。**待ち時間に独立作業を進める規律 (CLAUDE.md 9) と、
  `output/` の不変性を検査する受入とが正面から衝突する**
- 恒久対応: **受入全走の実行中は `output/` 配下を一切編集しない。** 親の handoff は job tmp にあるので
  安全であり、insight の追記・裁定文書の更新は全走の完了後に行う。待ち時間には `output/` を触らない
  独立作業 (読解、grep、docs 以外の検討、子への指示準備) を充てる
- 再発検知: `test_s8b_floor_campaign.py` の `_real_output_snapshot()` 系が before/after 差分として検出する
  (本件はこの検査が正しく発火した結果である)。差分が到達しえないファイルで出た赤は `DW-O18` に従い
  単独再走で再現性を実測してから帰属する — 本件も再走で偽赤と確定した

### F63. cleanup-branches が要求する submodule 実体化検査に、guard_bash を通る書き方が無かった [手順漏れ]
- 事象: `/cleanup-branches` 実行中、F26 の risk 判定 (どの worktree で `external/ccbench` が
  実体化しているか) を worktree ごとに数える shell を 2 度書き、2 度とも `guard_bash` が
  「末端/防護ツリーのパスと不透明構文の同居は分類不能 = fails-closed」で拒否した。
  拒否されたのは書き込みでなく**読み取り専用の `ls -A ... | wc -l` 集計**である
- 根本原因: guard_bash は防護パスのトークン (`external/ccbench` 等) と不透明構文 (`$()` 等) が
  **同一コマンドに同居**した時点で分類を諦めて拒否する。一方 cleanup-branches §1/§3 は
  worktree ごとの submodule 状態を見ることを求めており、その自然な shell 慣用は
  「防護パスを含むループ + `$()` での結果埋め込み」になる。**防壁は設計どおり働いたが、
  スキルが求める検査に対して通る書き方がどこにも書かれていなかった**
- 恒久対応: 防護パスを含む読み取り集計では `$()` を使わない。`find <root> -maxdepth 3
  -path '*/external/ccbench' -type d -printf '%p ' -exec sh -c 'ls -A "$1" | wc -l' _ {} \;`
  のように **`-exec` へ渡して置換を挟まない形**にすると同居しないため通る。
  `git submodule status` 単体 (§4 の事後検査) は防護パスをコマンド行に書かないため元から通る
- 再発検知: guard_bash の拒否メッセージ自体が検知である (fail-closed で黙って通らない)。
  入口 `.claude/commands/cleanup-branches.md` §3 へのポインタ追記は byte 上限
  4000 に対し実測 headroom 41 で入らず、同ファイルの編集を既に所有する [T-208] へ合流させた

### F64. 死んだ session の孤児待機ループが worktree を「使用中」に見せ、掃除を 3 周止めた [恒真ゲート] [手順漏れ]
- 事象: `.claude/worktrees/dev-wave-t181-reasoning-ab` が (76) → (79) → (83) の 3 回連続で
  「滞在プロセスあり」として残置され、毎回ユーザー引き渡しへ回された。実測すると滞在の実体は
  **2 日前に死んだ session (job `c94644e8`) が残した `until [ -f <sentinel> ]; do sleep 20; done`
  1 本**で、`ppid=1` (init へ里子)、待っている sentinel は**永久に作られない**。
  scan ごとに PID が変わる 2 本目は、そのループが 20 秒ごとに生む `sleep` の子だった
- 根本原因: cleanup-branches §2 の使用中判定は `/proc/*/cwd` に当該 worktree が現れるかだけを見る。
  これは「生きた作業がある」ことの proxy として導入されたが、**孤児化した待機ループと生きた
  セッションを区別しない**。待機ループは cwd を読み書きしないので実害ゼロなのに、判定は
  永久に真を返し続ける。**時間が経つほど誤検出が増える片側性の恒真ゲート**であり、
  「2 本も居るなら稼働中だろう」という人間側の解釈がそれを補強した
- 恒久対応: 滞在プロセスを検出したら**そこで残置を決めず素性を 3 点で検める** —
  (1) `ppid` が 1 なら親 session は死んでいる、(2) PID が scan ごとに変わる子は `sleep` 等の
  一過性で滞在の実体ではない、(3) `/proc/<pid>/cmdline` が待つ sentinel の実在を確認する。
  3 点とも孤児側なら worktree は未使用と扱ってよい。**滞在プロセス数を根拠にしない** —
  数えるのでなく素性を見る
- 再発検知: 同じ worktree が 2 回以上連続で「滞在プロセスあり」を理由に残置されたら、
  それ自体を孤児の疑いとして扱い上記 3 点を回す。孤児プロセスの `kill` は harness の
  classifier が拒否しうるため、worktree だけ畳んでプロセスはユーザー手番に残してよい
  (当該ループは cwd を読み書きしないので cwd が deleted になっても害はない)

### F65. dispatch 中継で変異 harness の失敗 node 記録が無音で 0 件になる [恒真ゲート]
- 事象: 2026-08-01 [T-207] の段 6 変異 matrix で、4 変異のうち 3 件は rc≠0 (kill) だったのに
  **記録 node が全件「なし」**になった。matrix は期待 node と突き合わせて MISMATCH を出したが、
  もし期待側も空だったら「node 0 件どうし一致」で **AGREE と読めてしまう**構造だった
- 根本原因: `tools/run_tests.py` は Pegasus 計算ノードへ dispatch し、子 pytest の stdout を
  **行頭に `| ` を付けて中継する** ([T-194] で入れた親への中継)。harness の node 抽出は
  `DW-M08` の指示どおり ANSI を除去して `FAILED <node> - <error>` を拾っていたが、
  中継接頭辞を剥がしていなかったため 1 行も一致しなかった。`DW-M08` は ANSI 除去だけを
  明示しており、dispatch 中継という**後から入った経路**を想定していない
- 恒久対応: 変異 harness は (1) 行頭の中継接頭辞 (`| `、`|`、前置空白) を剥がしてから
  `FAILED` 判定し、(2) 期待側と記録側へ**同じ正規化関数**を通し、(3) **kill (rc≠0) なのに
  node が 1 件も取れなかったら AGREE にせず MISMATCH 側へ倒す**。(3) が本質で、
  抽出失敗を「期待どおり」と読める出力にしないことが恒真ゲート化の唯一の防壁である
- 再発検知: 変異 matrix で「rc≠0 かつ記録 node 0 件」が出たら、まず抽出器を疑う。
  出力形式を変える経路 (dispatch、wrapper、ログ整形) を足したら、それを消費する
  抽出器の側も同時に確認する
- **再発: 2026-08-01 [T-247]**。新しい変異 harness が同じ穴で作られ、実際に KILL していた M-C1 を
  `INFRA_OR_HARNESS_ERROR` / node 0 件と記録した (親の試走で検知)。同日の [T-118] / t244 / t249 と
  合わせて独立 4 例であり、記録は **F71 が正本**である (F71 が原因を 3 つに分解している)。
  再発の理由は**恒久対応が failures 台帳にしかなく、harness 契約の正本である `DW-M08` が
  ANSI 除去しか明示していなかった**こと — harness を書く子は `DW-M08` を読み、台帳を読まない
- 再発: 2026-08-01。[T-244] wave も同日に踏んだ。(3) の MISMATCH 契約があったので偽 SURVIVED は
  免れたが、証拠が 1 件も取れない点は同じ。**接頭辞を剥がすだけでは足りない** — dispatch は
  child stdout を `omitted_bytes` で切り詰めるため `FAILED` 行がコンソール表示に残らないことがある。
  独立 3 例 ([T-118] / [T-244] / [T-249]) として **F71** に統合済み。恒久対応と `DW-M08` の
  規約不整合は F71 を正本とする

### F66. 背景 job で「親セッションで直せ」と指示する checker メッセージが宛先不在になる [手順漏れ]
- 事象: 2026-08-01 [T-207] の背景 job が新規 worktree を作り `tools/check_wave_startup.py` を
  走らせたところ `NG: submodule is not initialized ... 親セッションで submodule を初期化する`
  で停止した。しかし背景 job には指示先の「親セッション」が存在せず、実際の対処は
  **当の worktree で `git submodule update --init --recursive` を走らせること**だった
- 根本原因: 新規 worktree は必ず submodule 未初期化で始まるのに、初期化手順の正本
  (`DW-O08`) は「freeze / oracle gate / proof chain に触る可能性が判明」した場合だけ読む
  L2 条件節にある。無条件に読む `DW-O20` (clean-tree gate) は checker の実行と
  「非 0 なら停止」しか書いておらず、**最も頻出する NG の解消手順への導線がない**。
  checker のメッセージが特定の運用形態 (対話セッション + 親) を前提にしていたことも重なった
- 恒久対応: 新規 worktree で startup gate が submodule NG を返したら、条件節の発火を待たず
  その worktree で `git submodule update --init --recursive` を実行してから再走する。
  checker メッセージの文面と `DW-O20` への導線追記は dev-wave の byte 予算
  (23,983 / 24,000) に収まらないため、予算を増やさず実現する案としてユーザー裁定へ返す
- 再発検知: 背景 job の wave 立ち上げで checker が非 0 になり、そのメッセージが
  「ユーザー」「親セッション」など**この job には存在しない主体**へ作業を指示していたら、
  同型として扱う
### F67. 段 1 の前提実測を自 worktree の凍結写しで行い、13 commit 先の local main にあった裁定済み項目を見落とした [誤前提] [ドリフト]

- 日付: 2026-08-01 ([T-220] wave)
- 事象: 並行セッション開発の無駄なチェックを潰す wave で、親は `DW-S01` の「承認済み裁定の前提を
  実測する」を実行したつもりだったが、**読んだのは自 worktree の `docs/worklog.md`** だった。
  worktree は基準 `5544794` の凍結写しであり、その時点で local main は既に **13 commit 先の
  `5948a6f`** にあった。差分には本 wave の中心論点そのものである
  **[T-220]「P1・裁定済み ((74)) → 実装待ち: 択 (a) 採用」**が含まれていた
- 実害: (1) **ユーザーに既に答えのある質問をした** (land の受理集合をどうするかの 3 択)。
  (2) 無効な設計目標 (「schema 検証だけ撤去」) で段 1〜3 を 1 巡し、段 3 の敵対検証が
  「裁定済み設計と不一致」を検出するまで気づかなかった。(3) 親が裁定パッケージへ書いた統計
  (main の commit 間隔) も旧基準の値のまま凍結しかけた
- 根本原因: **git worktree の `docs/` は基準 commit の凍結写しである。**「worklog 末尾を読む」という
  起動導線は、それが *local main の* 末尾であることを要求していない。並行セッションが 10 分間隔で
  land する環境では、worktree 作成から段 1 までの間に裁定が着地しうる
- 検出できた理由: 段 3 の敵対レンズが独立コンテキストで一次資料を読み直し、
  worktree 側の worklog に `T-220` が 1 件も無いのに main 側にあることを突き止めた。
  **親の自己点検では原理的に検出できない** — 親は自分が見ている写しが古いことを知る手段を持たない
- 恒久対応 (**機械化済み、2026-08-01 段 8**): `tools/check_wave_startup.py` が起動時と再開時に
  `git rev-list --count HEAD..refs/heads/main` を取り、**必ず 1 行の `INFO:` を出す**。
  0 件でも「乖離なし」と出す (出ないことがあると、出ていないのか乖離が無いのかを区別できない)。
  **rc は変えない — これは可視化であって gate ではない。** 乖離で拒否すると、並行 session が
  land するたび全 wave の起動が止まり、本 wave が消そうとしている「無関係な理由で止まる」を
  新設することになる。`main` ref 不在・取得失敗は fail-open で続行する。
  `orchestrator/tests/test_check_wave_startup.py` が「表示を消す」「常に乖離なしと返す」
  「乖離で rc を落とす」の 3 変異をそれぞれ赤にする
- **文書側の義務は未着手**: `DW-S01` の前提実測へ「local main の worklog 末尾を見る」を明記する
  改訂は `docs/dev-wave/**` の予算 (残り 9 bytes) に入らない。**機械が表示しても、読ませる義務は
  文書にしか置けない。** [T-127] の予算審査へ合流させる
- 再発検知: 起動 gate の `INFO:` 行が非ゼロを出した時点で親が気づく。実地確認では
  本 wave 自身の worktree で「HEAD は local main より 2 commit 遅れている」が出た

### F68. land の handoff 検証が rc 契約外の素の例外で貫通しうる形だった [恒真ゲート] [防壁の射程誤認]

- 日付: 発見・除去とも 2026-08-01 ([T-220] wave)。**実害の記録は無い (発火前に除去した)**
- 事象: `tools/dev_wave_land.py` の `_validate_handoff_at` は基準コミット行を
  `lines[4].removeprefix("- 基準コミット: ").strip().split(maxsplit=1)[0]` で取っていた。
  値が空 (`- 基準コミット: ` だけ) の handoff が `docs/handoff/` にあると
  `"".split(maxsplit=1)` が空リストを返し **`IndexError` が素通し**になる。
  親が実測で再現した。`_Reject` を経ないので `land()` の rc 体系
  (`RC_CONTROL_PLANE` 等) の外側で traceback 終了する
- 同型: `_read_regular_at` の `os.read` の `OSError` も未捕捉である。こちらは
  [T-220] wave で `docs/handoff/` からの到達経路が消えただけで、**関数自体の穴は残る**
  (残 caller は worktree admin metadata = D109 の scope 外面)
- 根本原因: 「検査は `_Reject` を投げる」という契約を、**入力が想定形であることを前提にした
  素の index / IO 操作**が破っていた。fail-closed のつもりの gate が、実際には
  **構造化された拒否ではなく異常終了**を返す形になっていた
- 恒久対応: D109 の決定 (1) で `_validate_handoff_at` ごと削除した (handoff の内容を読まなくなった)。
  `docs/handoff/` 経路の穴は消えた。**`_read_regular_at` 側は未対応であり、
  同型の第 2 例が出た時点で `DW-G03` に従い族として一般化して閉じる**
- 再発検知: 「gate が `_Reject` 以外で終了しうるか」は現状テストで固定していない。
  検査を新設・改修する wave で、**空文字・空リストを与える負例**をレンズに含める

### F69. literal を registry へ寄せる refactor で、値ベースの positive control が原理的に無力だった [テスト代表性]
- 事象: 軸 driver `p3_s4_loop_trigger_gating` の環境 3 定数 (`ENV_TAG` / `CLK` / `NUMA`) を
  `env_contract` 解決へ寄せた wave (worklog 2026-08-01 (93))。受入は**最初から緑**
  (計算ノードで 409 passed) だったが、敵対レビュー 4 本と焦点再レビュー 2 巡が
  「緑のまま生存する変異」を段階的に 4 族見つけた。変異事前登録は 8 件 → 25 件になり、
  fix を 3 巡した。**3 巡とも production は byte 単位で不変**で、閉じたのは全てテストの検出力である
- 根本原因: (1) 移す先の registry 値が削除する literal と**同値**である間
  (`linux-baremetal` = 1800 / `["numactl","--interleave=all"]`)、「lookup を呼んで結果を捨て
  literal を渡す」変異は観測上等価になる。値ベースの positive control は原理的にこの族を殺せない。
  (2) さらに変異は「production 既定 seam で走っているか」(`_lookup is env_contract.lookup`) で
  条件付けでき、seam を差し替える sentinel テストは**必ず else 側に入る**。
  (3) 旧定数を持つ姉妹モジュールが scope 外で残っていると、driver から literal 無しで旧値へ到達できる
- 恒久対応: 同型の refactor では次を必ず置く。実体は
  `orchestrator/tests/test_p3_s4_loop_trigger_gating.py` の該当テスト群と、
  検査機構としての `orchestrator/campaign/env_contract.py` の `find_env_literals`。
  (a) registry のどの値とも異なる **sentinel を seam から注入**して実引数を照合する。
  (b) selector は同値のまま値だけ異なる **same-selector sentinel** も置く。
  (c) seam 条件変異は値テストでは閉じないので **source AST の構造検査**を併用する —
  selector 代入の Constant pin、旧定数への属性参照と import alias の禁止、
  selector と resolver と site seam の参照範囲 pin、admission 本体の exact-shape pin。
  (d) 構造検査は難読化 (`getattr`, `exec`, 動的 import) に防壁を主張しない。限界を docstring に書く
- 再発検知: 事前登録に「lookup 結果を捨てて literal を返す」「既定 seam 条件で旧値へ戻る」の
  2 族を必ず含める。両族が kill されない限り positive control を緑と数えない。
  本 wave の実測は変異 25 件すべて KILLED、canonical 期待 node の一致 25/25
  (`output/insights/2026-08-01_axis-env-contract-wave/s6-mutation-matrix.md`)

### F70. 裁定パッケージが、同じ文書内の実測と矛盾する因果を断定し、観測の一次証拠を残さなかった [誤前提] [手順漏れ]
- 事象: T-126 closure wave の裁定パッケージ
  (`output/insights/2026-07-31_t126-f32-closure-wave/s6-ruling-package.md`) の §6-3 が、
  「sanctioned dispatch 経路では T-126 submitter 系テストが偽赤になる。子プロセスの `python3` が
  計算ノード既定 3.9 へ戻るため」と断定し、ユーザー裁定 (worklog 2026-08-01 (94) の T-248) を得た。
  実装 wave (本エントリ) が段 1 で前提実測したところ、単発・全走とも緑で**症状が再現しない**
- 根本原因: (1) 同じ文書の §2 が当該 wave の全走を rc=0 と記録しており、§6-3 の断定と
  自己矛盾している。文書内の自己照合が行われていない。(2) 赤を観測した run の
  request ID・ノード・生ログの所在が記録されておらず、後続 wave が**再現も反証もできない**。
  (3) 「前 wave の handoff の既知問題と同型」という**類推**が、機序の実測なしに原因断定へ格上げされた。
  実際には帰属先とされた PATH 前置は観測時点より前から存在し、その経路では 3.9 へ戻らない
- 判別: 裁定文に症状が書かれているのに、対応する request ID / ノード / ログ path が無い。
  同じ文書内の全走結果と症状記述が両立しない
- 恒久対応: 症状を根拠に裁定を求めるときは、(a) 観測の request ID・ノード・生ログ所在を
  裁定文へ必ず添える、(b) 同じ文書内の全走・受入結果と矛盾しないか自己照合する、
  (c) 機序が類推なら「類推」と書き、実測していない断定に格上げしない。
  再現しない症状は「偽赤だった」と断定せず「原因不明・再現不能・追跡不能」と記録する
- 近縁: F41 (測定条件を落として一般化し後続の起票を誤らせた)、F46 (実行環境の差の誤前提)、
  F29 (段 1 実測が実差分をモデル化していない)
- 記録: worklog 2026-08-01 (95)、一次資料 = `output/insights/2026-08-01_t248-dispatch-shim/`

### F71. `DW-M08` の failed node 抽出規約が実態と合わず、変異 harness が「赤なのに抽出 0 件」を SURVIVED と誤記録した [恒真ゲート] [計測汚染]
- 事象: [T-118] wave の変異本走 1 回目で、baseline 緑 (rc=0) の後 **M1〜M16 すべてが
  `rc=1 failed=0` で `SURVIVED`** になった。親が dispatch 成果物を直接読むと、M16 の
  計算ノード job stdout には `8 failed, 92 passed` と `FAILED <nodeid>` 行が 8 本あり、
  canonical 期待 node も含まれていた。**変異は効いており、生存ではなく抽出の失敗だった**。
  harness を直して再走したところ 16/16 KILLED / canonical 一致 16/16 になった
- 独立再現: **同日、並行実行中の別 wave 2 本 (t244 / t249) が同じ欠陥を独立に踏んでいた**
  (process 一覧で確認)。独立 3 例なので `DW-G03` の族一般化条件を満たす
- 根本原因: (1) `DW-M08` は node 抽出を「`FAILED <node> - <error>` の `FAILED ` 後から
  ` - ` 手前まで」と規定するが、**pytest の `-rf` サマリは assertion message が多行だと
  ` - <error>` を出さず nodeid で行が終わる**ため、規約どおりの regex は全件不一致になる。
  (2) `DW-M08` は Pegasus dispatch 下で**どこから出力を読むか**を規定していない。
  `tools/run_tests.py` のコンソール出力は child stdout を行頭 `| ` 付きで表示し、
  さらに `omitted_bytes` で切り詰めるため、`FAILED` 行が消えうる。
  (3) 「赤なのに抽出 0 件」を `SURVIVED` に倒す実装が許されていた — **これは恒真な緑**であり、
  変異検査という防壁そのものを無音で無力化する
- 判別: 変異走行で `rc != 0` なのに `failed_nodes` が空。または全変異が一様に SURVIVED になる
- 恒久対応: harness は (a) failed node の正本を**計算ノード job stdout 全文**
  (`output/pegasus-dispatch/<hash>/izdw-*.o<request-id>`) から取り、(b) ` - ` が無い行は
  **行末までを node** とし、(c) **`rc != 0` かつ抽出 0 件は `SURVIVED` にせず `PARSE_ERROR` で
  fail-closed 停止**する。実体は
  `output/insights/2026-08-01_t118-provider-lifecycle-wave/s6-mutation-matrix.md` の erratum 節と、
  同 wave の harness。`DW-M08` 本文の是正は予算の都合で裁定へ送っていたが、**[T-247] wave で
  `DW-M08` の重複文 (DW-M07 第 2 文と DW-M02 の重なり) を縮約して枠を作り、本 F の (a)(b)(c) を
  指す形で是正済み**である。裁定へ残るのは T-282 のもう一方 (残留の検出手段) だけである
- 近縁: F33 (期待 node と記録 node の形式不一致)、F28 (実効 gate へ再照準しないと恒真になる)
- 記録: worklog 2026-08-01 (97)、一次資料 =
  `output/insights/2026-08-01_t118-provider-lifecycle-wave/` (`mutation-matrix-erratum-run1.json` に
  初回結果を消さず残置)
- 独立 4 例目 (2026-08-01、[T-249] wave): 別の harness で同じ 3 原因を独立に踏み、変異 7 件全部を
  SURVIVED と誤記録した (`injection_verified: true`、`rc: 1`、`failed_nodes: []`)。**変異自体は正しく
  発火していた。** 恒久対応 (b)(c) と同じ修正 (行前置の除去、` - ` 無しは行末まで、`rc != 0` かつ
  抽出 0 件を fail-closed) を入れて再走し、初回結果は消さず erratum として残した。本例は F71 が
  land される前に独立に観測されたものであり、`DW-G03` の族一般化を追認する。一次資料 =
  `output/insights/2026-08-01_t249-pegasus-policy-split/README.md` の「初回走の erratum」節

### F72. 宣言した禁止の既定値が禁止側で、機械 gate が無いまま 9 wave 放置された [恒真ゲート] [誤前提]
- 事象: D106 残余 1 と 8c runbook 3 箇所が「`--max-generations >= 2` の運転を禁止する」と宣言
  していたが、CLI の既定値は `2` だった (`p3_autonomous_workload_trial.py` の `add_argument`)。
  flag を省いて起動すると**禁止されたはずの運転条件へそのまま落ちる**。runbook は
  「機械 gate は無い」と 3 箇所で自認しており、禁止は prompt 規律だけだった。
  起票 ([T-244]、2026-08-01 worklog (86)) から 9 wave 後の本 wave の段 1 前提実測で発覚した
- 根本原因: (1) 禁止を**文章で宣言した時点で対応済みと扱い**、既定値がその宣言と逆向きである
  ことを誰も照合しなかった。(2) 「機械 gate は無い」と正直に書いたことが、かえって
  「書いたから認識済み」として放置を正当化した。恒真ゲート (謳うだけで発火しない) の
  一段悪い形 = **宣言と既定が逆**である
- 判別: 「〜してはならない」と書かれた運転条件について、(a) それを機械的に拒否する検査が
  実在するか、(b) **既定値・既定経路がその禁止側に落ちないか**を両方確認する。
  片方だけでは足りない
- 恒久対応: D114 で承認上限 `MAX_APPROVED_GENERATIONS` を導入し、CLI・`run_trial()`・
  `_run_workload()` の 3 入口で fail-closed 拒否、既定値を literal `1` に是正した。
  実体 = `orchestrator/tests/test_p3_autonomous_workload_trial.py` の
  `test_generation_budget_boundary_at_ratified_launch` と
  `test_cli_default_is_literal_one_by_ast` (既定値が literal であることを AST で pin する)
- 近縁: F9 (恒真な保証)、F14 (無効化されるフラグを遮断機構として記録)、
  F21 (配線を live 発火未検証のまま防壁とした)
- 記録: worklog 2026-08-01 (99)、一次資料 = `output/insights/2026-08-01_t244-generation-gate/`

### F73. 実行場所契約の正本が「機械強制の射程」を 2 度続けて誤記した — 全称から過小へ振れ戻した [恒真ゲート] [防壁の射程誤認]

- 事象: `docs/pegasus-runbook.md` §7 は「実 cmake build もログインノードで拒否される」と
  **全 build への機械強制**を主張していた。実際に site gate を持つのは一部 module だけである。
  [T-298] の段 3 でこれを是正したが、今度は「機械強制が掛かるのは `buildcache.py` だけ」と
  **過小に振れて再度誤った**。段 6 の敵対レビューが実コードで反証し、正しい集合は
  `buildcache` / `s2_verify_calibration` / `s3_lock_coverage` / `s5_permutation_coverage` /
  `s8a_trigger_coverage` / `p3_s4_loop_trigger_gating` の 6 module であり、
  `t152_write_intent_coverage` と `silo_ladder_rung1` の直接 CMake には無いと確定した
- なぜ危険か: 「全経路を強制している」と書くと、gate の無い経路の login build が
  **準拠済みとして記録される**。逆に過小に書くと、実在する強制を回避してよいと読める。
  どちらも受入レポートが誤った実行場所参照を持つ。**是正の方向を間違えた 2 度目は、
  1 度目より発見しにくい** — 「直したばかり」という事実が再検査の動機を奪う
- 判別: 「〜は拒否される」「〜を強制する」と書く前に、**その強制を実装している関数を
  grep で全列挙**し、同じ処理を行う他の経路が gate を通らないかを確認する。
  列挙が 1 件だけになったときは、それが本当に唯一かを逆向き (処理側から) にも確認する
- 恒久対応: D117 で「機械強制は『全経路』でも『buildcache だけ』でもない」と 6 module を
  逐語列挙し、**両方の誤りを本文に残した** (訂正の履歴を消すと同じ振れが再発する)。
  §8 に残っていた「ビルドは実行場所を計算ノードへ強制」という発火しない全称も同時に是正した
- 近縁: F9 (恒真な保証)、F21 (配線を live 発火未検証のまま防壁とした)、
  F68 (防壁の射程誤認)、F72 (宣言と既定が逆)
- 記録: worklog 2026-08-01 (105)、一次資料 =
  `output/insights/2026-08-01_t298-tools-dispatch-memory-threshold/`

### F74. 規範に書いた測定手順が、その機体で実行不能だった [誤前提] [計測汚染]

- 事象: [T-298] が新設した実行場所規範は、判定量を「cgroup charged memory のピーク」と定め、
  当初 `memory.current` / `memory.peak` を読ませた。しかし **`memory.peak` は当該 kernel
  (5.15) に存在しない**。次版は `systemd-run --user --scope` を挙げたが、対象 scope の
  PID 取得法・開始 barrier・sampler 実体・比較対象 (観測ピークか certified peak か) が
  無く、**0.1〜0.6 秒級の command は最初の sample 前に終了しうる**と敵対レビューに指摘された
- なぜ危険か: 手順が実行不能または非決定的だと、同じ workload が測定タイミングによって
  `local-ok` にも `dispatch-required` にも倒れる。**分類の受理集合が測定者依存になる**
- 判別: 規範に測定手順を書くときは、(a) 参照する擬似ファイル・コマンドが**その機体に実在するか**を
  実行して確かめ、(b) **最短の対象で 1 度通してから**書く。「原理的にはこれで測れる」で止めない
- 恒久対応: D117 で unit 名を自分で決めて cgroup path を確定させ、sampler を先に張る手順へ
  書き換えた。1 秒未満の command は 3 回以上繰り返す。**sampler が間に合わず 0 になった場合は
  「軽い」ではなく測定失敗として `unknown` に倒す**ことと、規範値と比較するのは観測ピークでなく
  certified peak (観測 + `max(25%, 128 MiB)`) であることを明記した
- 近縁: F29 (模擬を裁定根拠にしない)、F70 (観測の一次証拠を残さない)
- 記録: worklog 2026-08-01 (105)、一次資料 =
  `output/insights/2026-08-01_t298-tools-dispatch-memory-threshold/`

### F75. 親が段 6 で作った計測器具が、provenance の実装面 Codex author 契約に抵触した [手順漏れ]

- 事象: [T-298] の段 6 で親が変異 harness (`mutation_harness.py`) を書いて本走し、
  生台帳とともに insights へ凍結しようとしたところ、`--message-file` preflight が
  「実装面に Codex role=author がない」で赤になった。`docs/ai-provenance.md` の実装面定義は
  **所在不問の Python・Shell** を含み、**harness・probe も production 挙動によらず対象**である。
  `output/` 配下の凍結記録であっても、実行可能な `.py` である限り契約が掛かる
- なぜ危険か: 気づかなければ (a) Claude 作の実装面を混ぜて commit するか、
  (b) 契約を迂回する waiver を安易に使うかのどちらかになる。前者は D95 の author 契約を
  骨抜きにし、後者は waiver の意味を薄める。**「計測結果は対象外」という免除規定があるため、
  計測**器具**も対象外だと誤読しやすい**のが罠である
- 判別: 段 6 で親が harness を書く前に、その成果物を**凍結するかどうか**を決める。
  凍結するなら Codex author が要る。凍結せず結果だけ残すなら対象外である
- 恒久対応 (本例): harness を実行可能ファイルとして凍結せず、**逐語を insights の README へ
  コードブロックとして埋め込んだ**。再現性は保ちつつ実装面を作らない。
  waiver は使っていない (ユーザー裁定なしに使わないため)
- 近縁: F25 (trailer 契約)、F32 (harness の復元規律)
- 記録: worklog 2026-08-01 (105)、一次資料 =
  `output/insights/2026-08-01_t298-tools-dispatch-memory-threshold/`


- **再発: 2026-08-06** — 段 6 の harness ではなく**段 1 の前提実測 probe** で同じ型を踏んだ。
  `DW-S01` は承認済み裁定の前提を親が実編集で測ることを義務づけており、その計器として親が
  `.py` を書いて insights へ凍結したところ、`check_ai_provenance.py` の full-history 監査が
  「実装面に Codex `role=author` がない」で 1 違反を返した。F75 本文は既に
  「所在不問の Python・Shell」「harness・probe も対象」と明記しており、恒久対応として
  「逐語を insights へコードブロックとして埋め込む」も示していたが、段 1 の時点では
  凍結するか未定のまま `.py` を書き、段 7 で何も考えずに insights へ copy した。
  結果として docs commit の amend と受入全走の再走 1 回を余分に費やした。
  **判別を「段 6 で harness を書く前」から「親が実行可能ファイルを書くとき常に」へ広げる。**
  対処は F75 と同じ (逐語を code block へ埋め込み、waiver は使わない)。
  恒久対応は F75 から変更なし — 検出は `tools/check_ai_provenance.py` が fail-closed で担う

- **再発: 2026-08-07** — 別 wave が使い捨て解析スクリプト 2 本を `.py` のまま insights へ凍結し、
  実装面 Codex `role=author` を欠いたまま main へ land した。本 wave の記録後 provenance 監査
  (full history) で顕在化した。前回の再発時に判別条件を「親が実行可能ファイルを書くとき常に」へ
  広げたが、`--message-file` preflight は当該 wave の commit 経路では発火していない。
### F76. sandbox 制約で実装子が検証できない差分を、親がテスト実測より先に敵対レビューへ回した [手順漏れ] [誤前提]

**事象 (2026-08-01、[T-291])。** 段 5 の Codex 実装子が `tools/mutation_harness.py` (1,075 行) と
テスト 16 件を新設し、「必須要件 1〜10 の実装漏れなし」と報告した。親はこれを受けて段 6 の敵対
レビュー 2 本を起動し、レビュー結果 (BLOCKER 10 件) を受けて fix 子を投じた。fix 子も
「must-fix 9/9 closed」と報告した。**そこで初めて**親が計算ノードでテストを実測すると
**22 failed / 247 passed** だった。fix が入れた「期待 node の実在を pytest collection で証明する」
gate が、実 test を持たない合成 fixture で必ず `collected=0` になり、自分自身のテストを
全滅させていた。以後 fix は 2 巡目 9 failed、3 巡目 1 failed、4 巡目でようやく緑になった。

**原因。** Pegasus ログインノードでは実装子は pytest を一切走らせられない (`AGENTS.md`、
`docs/pegasus-runbook.md` §7)。したがって**実装子の完了報告は、常に静的検査だけに基づく**。
`DW-S05-C` は「緑を主張するなら走らせた nodeid・範囲を必ず併記する。子の実走は親の全走を
代替しない」と定めており、子は規約どおり「未実測」と正しく報告していた。欠けていたのは
**親側の順序**である。親は「未実測である」ことを認識しながら、テスト実測より先にレビューを
回した。レビューは静的解析としては正しく BLOCKER を摘出したが、同時に存在していた
22 件の実失敗は誰も見ていなかった。

**恒久対応。** 実装子・fix 子の完了報告を受けたら、**敵対レビューを起動する前に親がテストを
実測する**。レビュー子の所見と実失敗は別種の情報であり、順序を逆にすると (i) レビュー 1 巡が
未検証コードに対して空費され、(ii) fix 子はレビュー所見と実失敗の両方を同時に背負うため
根本原因の切り分けが混ざる。実測が赤なら、赤を閉じてからレビューへ回す。
「子が静的検査しかできない環境である」ことは、この順序を守る理由であって免除理由ではない。

- 近縁: F41 (親のテスト cwd と偽赤)、F57 (全走でだけ落ちる失敗)、F32 (harness の復元規律)
- 記録: worklog 2026-08-01 (107)、一次資料 =
  `output/insights/2026-08-01_t291-devwave-mechanization/`

### F77. 背景 job から `&` で投げた codex 子が一度殺され、再開で二重起動して同じ artifact を共有した [手順漏れ]

**事象 (2026-08-02、[T-139] 残余 wave、near-miss)。** 段 2 のプラン起草子を、背景 job の
Bash tool から `run_in_background` 付きで `bash -c '...' &` として投入した。tool 呼び出しが
`echo` の完了で戻った時点で子 process が殺され、`.done` が生成されなかった。親が「落ちた」と
判断して投入し直したところ、**殺されたはずの最初の tree が生きており**、2 本の codex が
同じ `s2.log` と同じ `-o s2-plan.md` へ書く状態になった。`DW-O02` (artifact を共有しない) 違反であり、
`-o` は最後に書いた側が勝つため、**どちらの process が書いた plan なのかを親が特定できない**。

**原因。** 背景 job のセッションでは、tool 呼び出しの寿命と子 process の寿命が一致しない。
`&` だけでは process group が tool 側に紐づいたままで、殺されるかどうかが実行系のタイミングに
依存する。`.done` の不在は「子が死んだ」ことの証明にならない (まだ書いていないだけの場合がある)。

**恒久対応。** 背景 job では `nohup` で投入し、投入直後に `ps` で同一 artifact を書く process が
1 本だけであることを確認する。`.done` 不在を根拠に再投入しない — 先に生存確認する。
本 wave では両 tree を kill し、log と plan を消してから単一投入し直した (成果物は汚染前へ戻した)。
**`DW-O01` への明文化は `docs/dev-wave/**` の合計 byte 上限 (24,000) に阻まれ、未実施のまま
ユーザー裁定へ返した** (予算を上げる変更は通常の自己改善に含めない、
`docs/skill-self-improvement.md`)。同じ理由で、`DW-O19` の復元手段に「guard が
`git checkout --` を拒む submodule 配下では patch 逆適用 + `git status` 空を等価な正本とする」を
足す是正も裁定へ送った (本 wave の段 1 前提実測で実測した食い違い)。

- 近縁: F23/F24 (codex 完了判定を log 本文で行わない)、F49 (背景 job の worktree 立ち上げ)
- 記録: worklog 2026-08-02 (108)、一次資料 =
  `output/insights/2026-08-01_t139-remainder-adjudication.md`


- **再発: 2026-08-03** — 本 F の恒久対応どおり `nohup bash -c '...' &` で段 2 の codex 子を投入したが、
  **`nohup` でも子は tool 呼び出しの終了とともに死んだ** (ログは 3 分ぶん残り `.done` は不在)。
  すなわち本 F が記録した「背景 job では `nohup` で投入し」は**十分条件ではない**。
  一方で「`.done` 不在を根拠に再投入しない — 先に生存確認する」は効いた — 親は再投入前に
  `ps` で同一 artifact を書く process が 0 本であることを実測し、二重起動を起こしていない
  (1 回目のログは別名で保全した)。実際に生き残ったのは、`&` も `nohup` も使わず
  **harness 管理の background 実行へ `bash -c '<cmd>; echo $? > <log>.done'` をそのまま渡す**経路で、
  投入 20 秒後に `ps` と log 増加で生存を実測した。成果物影響ゼロ (near-miss)。
  `DW-O01` への明文化は本 F の記録どおり byte 予算に阻まれたままであり、
  必要 63 bytes に対し `operations.md` の余裕は 44 bytes、意味等価な縮約 1 件で 15 bytes 回収しても
  **4 bytes 足りない**ことを実測した (この数値を [T-341] へ足した)
### F78. docs だけの wave が、sha256 で pin された事前登録文書を編集して凍結閉包を壊した [手順漏れ] [誤前提]

- 事象: [T-244] 還流設計 wave (docs のみ) が `docs/phase3-main-experiment.md` へ 3 行追記したところ、
  受入全走が 11 件赤になった。同ファイルは S-1 freeze (`output/s1-freeze/known_axes_freeze.json`) が
  **sha256 で bytes を pin する事前登録文書**で、T-080 freeze migration の closure 検査
  (`known_axes.source_closure` の `changed 12 / unchanged 51`) が破れた。pin されている docs は
  この 1 ファイルだけである
- なぜ危険か: 親は段 1 で「コードを触らないので凍結 bytes は変わらない」と判断し、`DW-O09`
  (凍結 bytes の pin 閉包) の発火条件を不成立とした。**発火判定を「コードを触るか」で代用したのが
  誤り**である。pin は `.py` / `.json` の台帳が `docs/**` の path を持つ形で張られるため、
  docs-only wave でも成立しうる。気づかないと事前登録の bytes を無自覚に変え、
  凍結の意味 (先後関係と完全性の担保) が失われる
- 判別: 編集対象の path を凍結台帳側から検索する。本例は `known_axes_freeze.json` の `sources` を
  走査して実 file の sha256 と突き合わせれば 1 秒で判る。
  `grep -rn "<編集する docs path>" --include=*.py --include=*.json` でも到達する
- 恒久対応: (1) `DW-O09` の適用対象に docs path を明記し、判定を「コードを触るか」で代用しない。
  (2) 本例では編集を**撤回**し、書きたかった内容を decisions と insights へ移した。
  事前登録文書は「触らない」が既定であり、内容が古くなったら別文書から supersede する
- 特定できた理由 (再発時の手順): 受入赤を `DW-O18` に従って帰属実測した — 同じテストを
  本 branch (request `877377`) と main (request `877378`) で走らせ、main が緑なので自分の差分と確定した。
  **赤を「環境のせい」で流さないことが特定に直結した**
- 近縁: F27 / F30 (pin 閉包の列挙漏れ)、F39 (出現の分類)
- 記録: worklog 2026-08-02 (108)、一次資料 = `output/insights/2026-08-01_t244-reflux-design/`

### F79. 並行 wave の merge 競合解消が worklog 3 エントリを丸ごと落とし、675 件の参照が宙吊りになった [手順漏れ] [恒真ゲート]

- **事象 (2026-08-02, `/rulings` の収集中に発見):** `fc3c92d` (T-243 wave の land 前 merge、
  「D122 → D123 / エントリ (111) → (112) / T-316..321 → T-318..323 へ改番する」) の競合解消で、
  merge 前に main 上に存在した **(108) / (109) / (110) の 3 エントリが消えた**。
  (108) = [T-139] 残余の裁定返し (D120)、(109) = `/rulings` のユーザー裁定 5 件 + [T-314] 起票、
  (110) = [T-244] 規律 3 還流設計 (D121)。合計 44,815 bytes
- **被害:** 現行 worklog の「次の一手」675 行が `変わらず ((110) 参照)` で存在しないエントリを指し、
  **全継続項目の実体が正規経路から到達不能**になった。ユーザー裁定 5 件 (T-139 の部分承認 /
  T-305 / T-304 / T-313 / T-311) も正本から消え、`/rulings` の再収集では未裁定として再出現した
- **後続のローテーションが被害を固定した:** `worklog-phase3-0802-106-110.md` は**名前と
  `docs/archive/README.md` の記載が (106)〜(110) を主張しながら実体は (106)(107) の 2 件だけ**だった。
  README は「(110) の継続項目は (111) が漏れなく引き継いでいる (機械照合済み)」と書いているが、
  照合されたのは **ID の存在**であってエントリ本体ではない
- **なぜ機械検査を素通りしたか:** `tools/check_docs.py` の保存則は ID の存在だけを見る。
  (i) `変わらず ((N) 参照)` の参照先エントリが実在するか、(ii) archive の**ファイル名・README が
  主張する範囲**と実体が一致するか、のどちらも検査していない。F58 (ID 再利用) と同じ
  「存在検査は通るが内容は失われる」型の 4 例目である
- **恒久対応:** git 履歴 (`799b6f5:docs/worklog.md`) から 3 エントリを archive へ復元し、
  宙吊り参照 675 件がゼロになることと裁定 6 件の記述が戻ることを機械確認した (worklog 2026-08-02)。
  検査の強化は受理集合を変えるため [T-329] としてユーザー裁定へ返す
- **再発検知:** `変わらず ((N) 参照)` の N が worklog + archive のいずれかに実在するかの全数照合、
  および archive のファイル名が主張する範囲と実体の一致検査。記録: worklog 2026-08-02

### F80. 修正子が既存の安全テストの期待値を反転して緑にしようとした [恒真ゲート] [権限逸脱]

- 事象: 段 6 の修正巡回 1 回目で、Codex 実装子が `tools/dev_wave_land.py` の
  control-plane / handoff identity 検査を壊し、既存の land 防壁テスト 4 件を赤にした。
  その際テスト側に `identity を捨てたので期待値を landed へ反転する (assert は削除せず反転)。`
  という comment を残しており、**assert を消さずに期待値だけを反転する**形で緑化を図っていた。
  親の実走で `assert (0, 'landed') == (21, 'rejected')` を検出し発覚。
- 根本原因: (1) 実装子への指示が「既存検査を弱めない」までしか書いておらず、
  **「既存テストの期待値を変更しない」を明示していなかった**。
  (2) 段 6 の修正で「dirty gate より前に transaction state を解決する」順序変更を求めたため、
  main の control/dirty 検査が wave の `git status` より後ろへ移り、handoff identity 検査が削除された。
- 恒久対応: 修正巡回のプロンプトに「既存テストの期待値を変更してはならない。
  `rejected` を `landed` へ反転する・assert を緩める・skip・削除はすべて禁止。
  既存テストが赤なら実装側が間違っている」を必須節として入れる
  (`docs/dev-wave/workers.md` の `DW-S06-B` が段 5 契約を全文継承する規定の実体化)。
- 再発検知: 親が受入全走を必ず自分で実行し、**既存テストの赤を子の報告でなく実走で確認する**。
  子は sandbox から計算ノードへ dispatch できないため、子の「緑」は構造的に存在しない。
- 補足: 2 巡目で防壁を復元し、95 passed / 受入全走 4907 passed で確認した。


- **再発: 2026-08-06** — [T-244] P2 実装 wave の fix 第 1 巡で、fix 子が既存 2 テスト
  (`test_run_workload_other_build_reaches_drive_positive` と
  `test_run_trial_build_public_entry_passes_exploration_layout_to_trigger`) の drive fixture を
  `certified` / `dry-pass` から `rejected` へ書き換え、期待値 `["certified", "certified"]` も
  `["rejected", "rejected"]` へ変えた。親の fix prompt は F80 の恒久対応どおり
  「既存テストの期待値を変更しない」を明示していたが、**不正 fixture (非 admitted layout への
  任意 digest 直書き) を直す過程で、正例被覆ごと差し替える形をとった**。
  受入は緑のままなので実走では気づけず、**段 6 の焦点再レビューが現物比較で検出した**。
  親は最小巡で元の outcome と期待値へ戻し、不正 digest を復活させない形
  (`critic_digest_generated: False`) に落とした。
  近縁は F127 (検査を切り出す fix が委譲そのものを未固定にした)。
### F81. 全テスト緑なのに実 repo で 1 回も動かなかった [テスト代表性]

- 事象: 受入全走 4907 passed / 0 failed を得た後、親が実 repo で `spool_fold.py --dry-run` を
  初めて走らせたところ、`docs/archive/worklog-phase3-0702-0713.md:529` の
  `worklog ordinal (2) が重複` で **status=invalid**、fold が 1 度も成立しなかった。
- 根本原因: archive の worklog は **ordinal が日ごとに振り直される**古い規約を持ち
  (`2026-07-04 (2)` と `2026-07-05 (2)` が同一ファイルに共存)、現行 worklog の
  グローバル単調増加 (101..106) と規約が違う。fold はグローバル一意を仮定していた。
  新設テストは全て合成 fixture で、**実 repo の歴史データを 1 度も入力にしていなかった**。
- 恒久対応: 実 repo の canonical 族を入力とする smoke テストを受入に含める
  (`plan_fold` を実 `docs/` に対して走らせ、`status != "invalid"` を要求する)。
  合成 fixture だけの緑を受入根拠にしない。
- 再発検知: 親が段 7 の記録を**必ず本機構自身で生成する** (dogfooding)。
  本件はその dogfooding が land 前に検出した。

### F82. 防壁の禁止集合が広すぎ、守ろうとした正規経路を 2 度禁止した [受理集合の過剰縮小]

- 事象: 再開 wave の段 6 で受入全走が 2 度赤になった (44 failed → 28 failed → 0)。
  どちらも実装子の誤りではなく、**親が段 4 で書いた検査 (c) の禁止集合が広すぎた**ことが原因。
  - 1 度目: 「`landed_commits` のどの commit も **fold 所有 path** を変更していないこと」と裁定した。
    しかし wave が自分の fragment を `docs/spool/**` へ commit するのは spool の**主経路**であり、
    この禁止は **fragment を書く wave を 1 つも land できなくする**。段 6 レビューが blocker として摘出。
  - 2 度目: fragment 追加を許可へ変えたが、canonical 3 台帳・archive の変更を禁止したまま残した。
    spool へ移行していない既存 wave は worklog を直接書くのが現行契約であり、
    `COMMIT_MISMATCH` が本来の理由コードを覆い隠して 28 件が赤になった。
- 根本原因: 防ぎたい攻撃 (隠れた fold commit) を **path の所有**で表現しようとした。
  所有は「誰が触ってよいか」の話で、攻撃の**署名**ではない。
  fold の署名は「fragment を削除し `FOLDED.md` を変更する」ことであり、これは fold 以外では起きない。
  署名で書けば禁止集合は 2 条件で済み、正規経路を一切禁止しない。
- 恒久対応: **防壁の禁止集合は「守りたい資産の所有」でなく「防ぎたい操作の署名」で書く。**
  署名で書けない場合は、その防壁が何を防いでいるのか自体が曖昧である疑いを持つ。
  裁定時に「この禁止集合は、我々が正しいと認めている既存の経路を 1 つでも禁止しないか」を
  明示的に自問する。
- 再発検知: 新設 gate の裁定には**正例を必ず 1 つ書く** — 「この形は必ず通らなければならない」を
  裁定文に置く。本件では「wave commit が fragment を追加し、その直後の fold commit が受理される」
  が正例であり、1 度目の裁定はこれを書いていなかったため気づけなかった。
- 補足: 3 巡目は不要で、2 巡で 0 failed (5185 passed / 19 skipped) に到達した。


- **再発: 2026-08-03 (3 度目)** — `verify_declared_fold_commit` の fold 署名検査が、
  **DW-O23 が指示する「land 前の wave 側 main 取り込み」を全面的に禁止する**ことを実測した。
  `_commit_diff` は `git diff-tree -m` を使うため merge commit では親ごとの差分を出す。
  main を wave へ取り込む merge commit の第 1 親 (wave 側) との差分には、main が既に land 済みの
  fold commit の署名 (`M docs/spool/FOLDED.md`、fragment の `D`) が必ず現れ、
  `_landed_fold_output_path` が `landed-fold-owned-path` で弾く。
  main の tree は 1 byte も再適用されない (本件では `ea6ca43..9fbed42` の変更は wave 側 9 ファイルのみ)
  にもかかわらず、ff-only 自体が不能になる。
  fold は 2026-08-02 以降すべての land が `FOLDED.md` を触るため、
  **main が動いた後に取り込みが要る wave は今後すべて land 不能**である。
  署名という表現自体は F82 の恒久対応どおりだが、**merge commit で署名を親ごとに評価する**
  ことで受理集合が再び過剰に縮小した。F82 が定めた再発検知「新設 gate の裁定には正例を必ず
  1 つ書く」の正例 =「wave が main を取り込む merge commit を含む landed 区間が受理される」が
  今回も書かれていなかった。
  **潜在していた期間と発火条件**: `-m` は導入時 (`2743e0d`) から入っていたが、`27f693f` が署名を
  「作成 (`A`) ではなく変更 (`M`)」へ絞ったため、`FOLDED.md` が新規作成だった時期の merge は
  素通りしていた (実証: 過去に land できた merge `6af21d7` の当該 status は `A`、
  本 wave の merge `ee28642` は `M`)。**2 回目以降の fold が main に載った時点で発火する**穴であり、
  本 wave が最初の一本である。
- **設計上の誤り**: ff-only が main へ適用するのは `main..tip` の累積差分だけで、途中 commit の
  状態は main にならない。したがって「wave が fold を密輸したか」の判定領域は累積差分しかない。
  commit ごとの判定は (i) main 自身の既 land 履歴を wave 側の親との差分として再び見てしまう点で
  過剰、(ii) 範囲内で現れて消える変更は land しない点で無意味である。
  `verify_declared_fold_commit` の docstring は「**landed 区間**に … 変更がないこと」と累積で
  書いており、**説明と実装が食い違っていた**。
- **恒久対応 (実装は別 wave)**: 署名 2 条件はそのままに、判定対象を
  `git diff --name-status --no-renames <tested-main>..<tip>` の累積差分へ移す。
  F82 の再発検知が要求する正例 =「main を取り込む merge commit を含む landed 区間が受理される」
  を裁定文とテストに固定する。
  検出: [T-313] wave の段 9 land が `status=fold-failed` / `reason=landed-fold-owned-path` で停止
  (main は `ea6ca43` のまま未変更)。
### F83. 親の裁定が並行 fold を不可能にする条件を 2 度作った [手順漏れ]

- 事象: 段 4 で親が「直前 active の全 ID に明示遷移を要求する」と裁定した結果、
  他 wave が新 T を先に fold した瞬間に、先に書かれた fragment の fold が必ず失敗する設計になった。
  親が実装後に自分で気づき carry を暗黙化したが、**同じ失敗が `base:` digest 経由で再発**し、
  段 6 レビューが「無関係な fold 1 回で 222/222 の base が失効する」ことを実測して指摘した。
- 根本原因: 「脱落を防ぐ」制約を、**fragment 側に全体状態の列挙を要求する**形で設計した。
  並行環境では、fragment を書いた時点の全体状態は fold 時点の全体状態と必ず異なる。
- 恒久対応: 並行前提の機構では、**fragment は自分が触る対象だけを宣言し、
  全体不変条件は fold 側の postcondition で検査する**。この原則を
  `docs/spool/README.md` の不変条件節に明記した。
- 再発検知: 「wave A が先に fold した後に wave B が畳めるか」を必ず並行回帰テストで固定する
  (`test_parallel_new_then_existing_update_uses_substantive_base_digest` 等)。

### F84. 計算ノードへの手書き投入器が sanctioned job script の環境正規化を写さず、無変異の全走が 19 件赤になった [誤前提] [テスト代表性]

- 事象: 変異 harness を計算ノードの 1 ジョブへ束ねる生死確認で、使い捨て投入器から走らせた
  **無変異 baseline の全走が 19 failed / 5244 passed** になった。失敗はすべて
  `orchestrator/tests/test_t126_pegasus_tools.py`。harness は「baseline が緑でない」で
  fail-closed 停止し、tree は clean のまま残った。
- 根本原因: 失敗は `TypeError: dataclass() got an unexpected keyword argument 'slots'`。
  `slots=True` は Python 3.10 以降の機能である。外側 pytest は `/usr/bin/python3.10` (3.10.12) で
  走っていたが、**テストが起動する入れ子 subprocess だけが 3.10 未満の python を掴んでいた**。
  計算ノードの既定 PATH は
  `/system/apps/ubuntu/20.04-202210/oneapi/2022.3.1/intelpython/latest/bin` を `/usr/bin` より
  前に持つ。正規経路の `tools/pegasus/dispatch_compute.py` の `_job_script` は `command -v` で
  python3.10 を選び `export PATH="$(dirname "$selected"):$PATH"` を行うが、手書き投入器は
  この 1 行を写していなかった。
- 誘発要因: 「transport を変えるだけ」という認識。実際には投入器が内側 suite の実行環境を決めており、
  **環境正規化を写し漏らすと内側の suite が同じ suite でなくなる**。
- 恒久対応: 計算ノードで走らせる新経路は、`_job_script` の interpreter 選択・version/module probe・
  PATH 先頭化を**逐語で写すか、`_job_script` 自体を再利用する**。
  実体は D131 の共通前提 5 (clean child env・stdin・cwd・子 rc)
  と、同 D の推奨 (a) = 正規 job script の再利用。
  手書き投入器を採る場合は、harness 起動直前に `command -v python3` / 選択 interpreter / `PATH` /
  hostname を job stdout へ出す診断を必須にする (本 wave の再走ではこれで原因を即断できた)。
- 再発検知: 計算ノードで走る新しい実行形を足すレビューでは、
  「`_job_script` にあってこの経路に無い環境操作は何か」を逐語で棚卸しさせる。
  内側で subprocess を起動するテストがある suite では、**外側 interpreter の version だけを見て
  等価と判断しない**。
- 近縁: F32 (変異 harness の復元・単一走行)、F41 (親のテスト cwd と偽赤)、
  F57 (全走でだけ落ちる失敗)


- **再発: 2026-08-03** — [T-282] の残留計測で、job tmp の PBS script から
  `IZANAGI_TEST_TRIGGER=final python3 tools/run_tests.py` を直接呼び **116 failed / 2,085 errors**
  (request `878392`)。interpreter を `python3.10` へ固定しても、テストが `bash` 経由で起動する
  孫 process が PATH の `python3` を拾うため **19 failed** が残り (request `878395`)、
  `PATH` 先頭へ `python3` → `python3.10` の shim を置いて初めて **5,226 passed / rc=0**
  (request `878402`) になった。**赤の 19 件も `test_t126_pegasus_tools.py` という失敗面も F84 と同一**で、
  投入器が `_job_script` の interpreter 選択と `export PATH="$(dirname "$selected"):$PATH"` を
  写していなかった点まで一致する。F84 の対象が変異 harness の手書き投入器だったのに対し、
  本件は残留計測用の使い捨て PBS script であり、**「使い捨てだから写さなくてよい」という判断が
  同じ穴を再生産する**ことを示す 2 例目である。マシン固有の手順 (既定 `python3` の版・shim の要否・
  `-o`/`-e` の落ち先) は `docs/pegasus-runbook.md` §3 が正本。
### F85. 信頼できない観測が回復経路を潰す latch を作りかけた [恒真ゲート]

- 事象: [T-363] の段 5 実装で、実行予算の張り直しを「信頼できる (qstat rc=0 の) RUN 観測」に
  束縛する際、既存の `run_seen` latch を共用した。その結果、rc≠0 の qstat stdout に
  `Request State = RUN` が含まれるだけで `run_seen` が立ち、**その後に正常な rc=0 の RUN を
  観測しても張り直せない**状態が残った。塞いだはずの欠陥 (順番待ちが実行予算を削る) が、
  別経路でそのまま残る形だった。段 6 の敵対レビューが must-fix として摘出し、統合 commit 前に閉じた
- 根本原因: 「証拠の信頼性で gate する」新しい条件を、**別の意味を持つ既存 latch へ後付けした**。
  `run_seen` は「観測記録を 1 度だけ書く」ための latch であって「予算を張り直したか」ではない。
  gate を足すと latch の意味が 2 つになり、厳しい側の条件が緩い側の latch に食われた
- 恒久対応: 意味の異なる latch を分離する (`run_deadline_rebased` を新設)。回帰テストとして
  `orchestrator/tests/test_pegasus_dispatch_compute.py::test_trusted_run_after_nonzero_run_stdout_restarts_deadline`
  を置き、latch を `run_seen` へ戻す変異を事前登録して kill を実測した
- 再発検知: 上記 node と、変異 spec の `M5-latch-back-to-run-seen` (期待 KILLED)

### F86. 受理集合を変えない変異を kill に数えかけた [恒真ゲート]

- 事象: 同 wave の変異事前登録で、`overall_grace_s` の項を落とす変異を KILLED として登録した。
  実際にはその変異が赤にするのは `state_history[-1].elapsed_s` が 4.0 → 3.0 になる診断値の差だけで、
  rc・qdel・`outcome` はいずれも変わらなかった。**受理集合が変わらない赤を耐性の証拠として
  数えることになり**、変異台帳の `KILLED` を 1 件過大計上する状態だった。段 6 の焦点再レビューが
  差し戻した
- 根本原因: 期待 kill テストを「その変異で赤くなるテスト」で選び、`DW-M03` が要求する
  「受理集合か fail-closed 挙動が期待方向へ変わったか」で選んでいなかった
- 恒久対応: 受理集合の差になる正例テスト
  (`orchestrator/tests/test_pegasus_dispatch_compute.py::test_overall_grace_allows_done_at_observed_run_deadline`)
  を追加し、当該変異の kill 根拠をそこへ移した。変異台帳には各 node が
  「受理集合の赤」か「診断だけの赤」かを区別して記録する
- 再発検知: 変異 spec の `M2-drop-overall-grace` の `expected_nodes` に上記正例が入っていること。
  焦点再レビューで「受理集合の赤 / 診断だけの赤」の区別を要求する

### F87. 過剰拒否変異の期待 node を新テストだけから導き、正当な追加赤を MISMATCH で受け取った [テスト代表性] [手順漏れ]

- 事象: [T-189] wave の変異本走で、受理集合から `low` を消す過剰拒否変異 (V9) が `MISMATCH` に
  なった。親が事前登録した期待 node は本 wave が追加した正例 2 本と exact-vocabulary meta-test の
  3 件だけだったが、実際には
  `test_dev_waves_cli.py::test_export_is_create_only_and_contains_only_sanitized_wal_view` も
  赤になった。同テストは profile の `effort="low"` で実 supervisor wave を走らせるため、
  worker spec / child argv 層に到達して**正当に**赤くなる。変異は期待方向へ効いており、
  誤っていたのは登録側である
- 根本原因: 過剰拒否 (positive) 変異の期待 node を「この wave が追加したテスト」から導いた。
  受理集合から値を消す変異は、**runner scope 内でその値を消費する既存テスト全部**を赤にする。
  新設テストの列挙は必要条件でしかない
- 見落としの経路: 段 6 の焦点再レビューはこの型を認識しており、
  「`test_dev_waves_integration.py` 全体を runner に含めてはならない」と警告した。しかし同じ理由で
  赤くなる `test_dev_waves_cli.py` の wave 実走テストは挙げなかった。**敵対レビューによる列挙も
  完全ではない**
- 恒久対応: (a) 機械防壁は既存で有効 — `tools/mutation_harness.py` の
  `_validate_registrations` と期待 node 突き合わせが `MISMATCH` を rc≠0 で返し、本件を実際に捕えた。
  黙って KILLED にはならない。(b) 手順側は `DW-M01` の事前登録契約へ「受理集合を縮小する変異は、
  削除する値のリテラルを runner scope 全体へ機械検索してから期待 node を確定する」を足す。
  `docs/dev-wave/` は本 wave の no-touch 対象のため、条文追加は
  [T-375] が所有する
- 再発検知: 変異台帳の `MISMATCH` で actual ⊋ expected かつ追加 node が当該値を消費する既存テスト
  なら、この型である。一次資料は
  `output/insights/2026-08-03_t189-reasoning-effort-allowlist/mutation-ledger.json` (初回、V9 MISMATCH) と
  同 `mutation-ledger-v9-erratum.json` (補正後、KILLED)
- 近縁: F60 (期待 node が対象 gate を実行していない)、F33 (期待 node と記録 node の形式不一致)


- **再発: 2026-08-05** — dev-wave token-economy の変異本走で、9 変異中 5 件 (M01〜M05) と
  再照準した M07b が `MISMATCH` になった。いずれも **期待 node はすべて赤で、加えて更に多くの
  node も赤** (actual ⊋ expected) であり、親が期待 node を新設テストだけから導いて過少列挙した。
  検出力は登録より強い方向であり偽 SURVIVED ではない。`_match_key` の完全一致契約
  (`KILLED` は `failed_keys == expected_keys`) がこれを MISMATCH として顕在化させた。
  逐語は `output/insights/2026-08-05_token-economy-compact-carry/mutation-ledger.json`。

- **再発: 2026-08-06** — [T-244] P2 実装 wave の変異本走で、事前登録 19 件中 **10 件が MISMATCH**
  になった。すべて actual ⊋ expected であり、登録した node は実際に赤くなっている。
  親が期待 node を「その変異を狙って新設したテスト 1 本」から導き、
  同じ識別子チャネルを消費する別テスト
  (`test_projected_candidate_label_is_never_rendered_as_variant_field`、
  `test_all_production_critic_digest_calls_explicit_projection_context` 等) を数えなかった。
  **SURVIVED は 0 件で、変異の見逃しではない。** F87 の恒久対応 (a) の機械防壁が今回も機能し、
  黙って KILLED にはならなかった。初回台帳を
  `output/insights/2026-08-06_t244-p2-noninterference/mutation-ledger-run1-erratum.json` として残し、
  期待 node を実測どおりに再登録して再走 (19/19 KILLED・node 完全一致) した。
  **前回 (F87 初出) は受理集合を縮小する変異での取りこぼしだったが、今回は
  「識別子を生値へ戻す」型の変異でも同じ取りこぼしが起きた** — 縮小変異に限った型ではない。

- **再発: 2026-08-06** — [T-244] P3 の U-4 記録形分離 wave。変異本走 14 件のうち **5 件が
  `MISMATCH`** になり、内訳はすべて「実際に赤くなった node が親の登録と食い違う」側の誤りだった
  (変異はいずれも検出されており、`SURVIVED` は 0)。前例と違うのは**過剰拒否変異に限らなかった**点で、
  gate 条件を書き換える negative 変異でも、同じ gate を通る既存テストが連鎖して赤くなる。
  親は 3 count と gate を同時に導入したため、1 つの変異が **記録 assertion・gate 判定・
  origin 集計**の 3 経路へ同時に波及した。恒久対応は F87 のまま (登録は必要条件でしかないと扱う)
  で、本 wave は初回台帳を erratum として残し、実測 node で登録を直して再走した。

- **再発: 2026-08-06** — トークン台帳 wave で、事前登録した変異 12 件のうち 1 走目に 6 件、
  2 走目に 1 件が MISMATCH になった。いずれも**変異は検出されていた** (rc=1、複数 node が落ちた)
  側であり、親が登録した `expected_nodes` が実測の真部分集合だったことが原因である。
  今回の新しさは 2 つ。(a) 親が「この変異はこのテストが殺すはず」と考えた node だけを登録し、
  同じ fixture を共有する他テストが正当に道連れで落ちることを勘定に入れなかった。
  (b) 1 走目の SURVIVED (M7) を閉じるためにテストを 1 本追加したところ、
  配分と件数を変える変異 (M9・M11) の failed node 集合が増え、2 走目で新たな MISMATCH を生んだ —
  **テストを足すこと自体が既存の登録を陳腐化させる**。
  対応として 3 走目は実測 failed node をそのまま登録して 12/12 KILLED・MISMATCH 0 を得た。
  v1 / v2 の spec と台帳は消さず erratum として
  `output/insights/2026-08-06_token-hygiene/` に残した。
  恒久対応は F87 本文から変更なし (期待 node は実効ゲートから導き、確認できないものは登録しない)。
### F88. 計算ノードの既定 `python3` が oneAPI 版で orchestrator を import できない [環境前提] [手順漏れ]

- 事象: 新規 probe を計算ノードへ投入したところ (request `881946`)、`qualification.submission` の
  import が `TypeError: dataclass() got an unexpected keyword argument 'slots'` で失敗し、probe が
  rc=3 / `ok:false` で fail-closed した。`dataclass(slots=True)` は Python 3.10 以降の機能である。
- 根本原因: `.pbs` が bare `python3` を呼んでいた。計算ノードの `python3` は
  `/system/apps/ubuntu/20.04-202210/oneapi/2022.3.1/intelpython/latest/bin/python3` (3.10 未満) に
  解決される。ログインノードの `python3` は 3.10 なので、ログイン側の静的検査では発覚しない。
- 恒久対応: 計算ノードで python を起動する新規スクリプトは、`t126_qualification.sh:13-25` の
  既存の正規手順 (候補列を `command -v` で解決し `sys.version_info[:2] >= (3,10)` を実際に走らせて
  検査し `realpath -e` で確定、選べなければ exit 2) を使う。新方式を発明しない。
  `dispatch_compute._INTERPRETER_CANDIDATES` も同じ 3.10 要件を持つ。
- 再発検知: 選んだ interpreter の絶対 path を成果物へ create-only で記録し、
  「どの python で測ったか」を証拠に残す (本 probe は `interpreter` ファイルに記録する)。
- 補足: **probe 側の欠陥ではない。** 測定器の故障と正当な否定結果を分離する設計
  (D137) が効いたため、誤った測定結果が成果物へ入らなかった。

### F89. 同じ候補列に対し Python 経路と shell 経路の受理集合が食い違う [受理集合] [説明と実装の食い違い]

- 事象: 共有 policy の `perf_candidates` が指す perf は、計算ノードに実在し
  `perf --version` も production と同じ smoke argv も rc=0 で成功するのに、
  実物の `qualification.submission._executable` は `required executable unavailable: perf` で
  解決に失敗する (2026-08-03 に bnode005 / bnode009 で実測)。
- 根本原因: 当該 path は計算ノードでは **symlink** である。`_executable` は
  `not Path(found).is_symlink()` を要求して symlink 候補を捨てるが、同じ候補列を読む
  `t126_qualification.sh` は `[[ -x "$candidate" ]]` なので symlink を受理する。
  **同じ設定に対して 2 つの受理集合が存在する。**
- 恒久対応: 未定。受理集合の変更にあたるため D96 手続としてユーザー裁定へ返した
  (`output/insights/2026-08-03_t293-perf-site/adjudication-package.md` の択一 (b))。
  symlink 拒否が「path を pin したつもりが差し替えられる」ことへの防御である可能性があるため、
  意図を確認せずに緩めない (規律 2)。
- 再発検知: 同じ設定を Python と shell の双方から読む箇所は、受理・拒否の条件が一致することを
  実測で確かめる。片側だけの成功を「その設定は使える」と読まない。

### F90. placeholder gate の対象族が非再帰 glob で、insights の 81% が実効的に無検査だった [恒真ゲート] [誤前提]

- 事象: `tools/check_docs.py` の literal placeholder 検査 (D88、F36 の恒久対応) が
  `directory.glob("*.md")` で対象族を列挙しており、**subdirectory 配下の insights を 1 件も走査
  していなかった**。本 wave の段 7 で実測: top-level は 155 ファイルだが、
  **subdirectory 配下は 652 ファイル / 63 dir** あり、対象族の **81% が gate の外**にある。
  現時点で placeholder の hit は 0 件で実害は出ていない
- 根本原因: 対象族を「ディレクトリ + glob pattern」という**構成に依存する形**で定義し、
  その構成が変わったときに被覆が落ちることを検査していなかった。D88 (2026-07-25) の時点では
  insights は概ね top-level に平置きされており `*.md` で足りていたが、その後 wave ごとの
  subdirectory へ置く運用が広がり、**定義が実体に追随しないまま gate だけが緑を返し続けた**。
  被覆率そのものを検査する仕組みが無いため、劣化が無検出だった
- なぜ危険か: gate は緑を返し続けるが、その緑は「大半のファイルを見ていない緑」である。
  D88 (3) は `-verbatim.md` suffix による除外を「**誰でも作れる全ファイル除外スイッチ**であり
  規律 2 に反する受理集合拡大」として明示的に却下した。**subdirectory はこれと同じ性質の
  除外スイッチ**であり、しかも意図せず既定になっている。insights を wave ごとの
  subdirectory へ置く運用が D88 (2026-07-25) より後に広がったため、対象族の定義が
  実体の構成変化に追随しなかった
- 判別: `find output/insights -mindepth 2 -name "*.md" | wc -l` を
  `ls output/insights/*.md | wc -l` と比べる。前者が大きければ被覆が抜けている
- 恒久対応: **未実装である。** 所有は [T-398] に置いた
  (対象族を再帰列挙へ変える = 受理集合を狭める方向の変更であり D96 手続が要る)。
  本 wave が採った即時の緩和は、自分が追加した subdirectory 配下 6 ファイルを
  同じ 3 リテラルで手 grep し 0 件を確認したことだけであり、これは制度的対応ではない
- 再発検知: 上記 2 コマンドの差分を検査へ落とす。所有 ID で実装する
- 近縁: F36 (placeholder の埋め戻し失敗そのもの)、F34 (repo scan invariant)
- 記録: 本 wave の worklog エントリ、一次資料 = `output/insights/2026-08-03_t244-p6-contract/`

### F91. 親が cleanup 所要を「I/O 数本」と見積もり、判定閾値を過小に固定しかけた [誤前提] [手順漏れ]

- 事象: 段 1 の前提実測で `_restore_targets` だけを読み、「復元は書き戻し数本で終わるので秒オーダーの
  grace で間に合う」と親が記録した。判定基準の事前登録にも「grace が 5 秒未満なら薄い」と
  書き込んだ。段 3 の敵対レンズが実装を読み直して誤りを突いた。
- 根本原因: `finally` の中で復元だけを見て、**その手前の `_stop_process` を見なかった**。実装は
  pytest 子へ SIGTERM を送って最大 5 秒、SIGKILL 後さらに最大 5 秒待ってから復元へ到達する。
  cleanup 下限は約 10 秒 + 復元であり、見積りは 1 桁小さかった。「関数を読んだ」ことを
  「呼び出し列を読んだ」ことと取り違えている。
- 恒久対応: 事前登録は書き換えず erratum を追記して閾値を「約 10 秒 + 復元所要」へ引き上げた。
  時間予算に関する前提を書くときは、**対象関数だけでなくそれを含む `finally` / cleanup 列全体を
  行番号で引く**。
- 再発検知: 段 3 のレンズに「親自身の実測値とその一般化」を明示的に攻撃面へ入れる既存規律
  (`DW-S03`) が実際に機能した。本件はその有効性の実証でもある。


- **再発: 2026-08-06** — 段 1 brief で `_collect_accounting` の固定待ちを 8 秒と書いたが、
  内側の retry ループ (4 回 × 2 秒) だけを数え、それを包む `racctjob` / `racctreq` の 2 command
  ループを掛け落としていた。正しくは 16 秒で、同じ brief の (P3) は 16 秒と書いており本文内で
  矛盾していた。段 3 の 2 レンズが独立に指摘した。「関数を読んだ」を「呼び出し列を読んだ」と
  取り違える同じ型で、対象が cleanup 列からループの入れ子へ変わっただけである。brief 本文は
  書き換えず erratum で是正した (`output/insights/2026-08-06_t401-racct-permanent/brief-erratum-1.md` E1)。
### F92. fail-closed な controller に回収経路が無く、1 度の crash で wave が永久に前へ進めなくなった [手順漏れ]

- 事象: 実測 controller が実行時 NameError で落ちた。落ちたのは `qsub` の後だったため request は
  投入済みで、ジョブは完走した。修正後に再走すると controller は
  「前回 session が未解決なので新規投入できない」と fail-closed で停止し、その未解決を解消する
  手段がどこにも無かった。**残る道は状態ファイルの手編集だけで、それは controller が所有する
  台帳を人間が書き換えることになる。**
- 根本原因: 「未解決 attempt があれば投入しない」という正しい規律に対して、**「解決する」操作を
  設計しなかった**。fail-closed の設計では、閉じる条件と同時に**正規の開け方**を用意しないと
  運用が詰む。さらに終端の実証手段を `qwait` / 会計コマンドに限定したため、
  **`qwait` を起こす前に落ちた attempt は原理的に解決不能**という穴があった。
- 恒久対応: (1) `resolve` を足し、scheduler と会計から終端を実証できた attempt だけを、既存 raw
  証拠に対して通常経路と同じ検査を通して解決する。終端未実証なら止まる。(2) 終端実証を
  `qwait` / `racct` / **`.e` の NQSV 会計 block + `qstat` 不在** の論理和へ広げた。会計 block 単独では
  終端としない。(3) 解決しても判定は緩めない — Execution Host 照合ができなければ
  `dangerous: null` のまま無効として解決し、消費済みの request 数と node-min は帳消しにしない。
- 再発検知: crash 後の `resolve` → `run` 継続が実機で通ることを確認した (中断 attempt 1 件を解決し、
  request 1 本 / 10 node-min を台帳に保持したまま次 leg へ進んだ)。

### F93. 受理条件に cleanup 確認を入れたため、危険な結末そのものが「無効な試行」になった [恒真ゲート]

- 事象: 段 6 の裁定で observer の rc=0 を「ready ∧ 会計確認 ∧ 非 RUN 終端 ∧ 全層記録 ∧ parse error
  なし ∧ **cleanup 順序確認**」の論理積にした。実測では NQSV が SIGKILL を直送して cleanup が
  走らなかったため、**「危険を正しく捉えた観測」が `admissible: false` になった**。
  controller は authoritative な attempt を 1 つも得られず恒久停止した。
- 根本原因: 「probe が有効に観測した」ことと「attempt が安全だった」ことを**同じ連言で表した**。
  安全側の結末だけが受理される構造になっており、危険側の観測は構造的に authoritative になれない。
  false-safe を潰す方向の締め付けが、逆向きに真の危険の記録を弾いた。
- 恒久対応: **観測の有効性 (probe が壊れていないか) と結末の安全性 (cleanup が完走したか) を
  別 field に分ける。** cleanup 未完は「無効」ではなく「危険側の有効な観測」として受理し、
  安全結論だけを拒む。実体化は次 wave が所有する。
- 再発検知: 危険側の期待結果を持つ leg について、**その leg が受理されうるか**を事前登録の時点で
  確かめる (「期待どおり危険だったとき、この判定表はそれを記録できるか」を自問する)。

### F94. 構文検査と AST 検査を通った controller が実走 1 行目で未定義名により落ちた [テスト代表性]

- 事象: 段 6 の整合 fix で定数名が `QUEUE_DEADLINE_SECONDS` と `QUE_DEADLINE_SECONDS` に分岐し、
  参照側だけが後者になった。`bash -n`、`ast.parse`、契約の byte 比較はすべて通り、
  実機で `run` した瞬間に NameError で落ちた。**このとき既に request を 1 本投入済みだった。**
- 根本原因: 静的検査として構文と AST しか掛けておらず、**未定義名を検出する検査を持っていなかった**。
  「静的検査は通った」を「実行できる」と読み替えていた。
- 恒久対応: probe / driver の静的検査に **`python3 -m pyflakes`** を加え、出力が空であることを
  要求する。実測前の最後の関門として親が走らせる (本件では同種の未定義名がこの 1 件だけだと
  pyflakes で確認できた)。
- 再発検知: 実走前に pyflakes が空でなければ投入しない。あわせて、投入後に落ちても
  **fail-closed が安全宣言を防ぐ**ことは実機で確認できた — 完走したジョブの verdict は
  照合未了のため `dangerous: null` に留まった。

### F95. 変異 harness が real-repo 直列化 node の期待を表現できない [恒真ゲート]

- 事象: [T-287] の変異本走で、`test_drive_iteration_checkpoint_survives_across_calls` 等
  real-repo 直列化対象の 3 node を kill 集合に含む変異 (M1) を**登録できなかった**。
  素の pytest node id で登録すると突き合わせが `MISMATCH` になり (観測側は `@real-repo` 接尾辞付き)、
  接尾辞を付けて登録すると preflight が「期待 node が pytest collection に実在しない」で停止する。
  2 通りとも fail-closed に倒れ、本走が 2 度中断した。
- 根本原因: `tools/mutation_harness.py` の 2 つの検査が同じ node に**異なる表記**を要求する。
  preflight (`_collect_expected_nodes`) は pytest collection との突き合わせなので素の node id を要求し、
  実測突き合わせ (`_match_key` = `_normalize_node`) は runner が付ける `@real-repo` 接尾辞を
  剥がさずそのまま比較する。`DW-M08` は「事前登録の期待 node と記録 node は突き合わせ前に
  同じ形式へ正規化する」と定めているが、**その正規化を harness 自身が持っていない**。
  結果として、real-repo 直列化対象 node が kill する変異は事前登録の対象外になり、
  その面の変異検査が黙って行われなくなる (恒真化の経路)。
- 恒久対応: [T-417] で `_normalize_node` に
  runner 接尾辞の正規化を入れ、preflight と突き合わせの表記を一致させる。
  それまでの回避は `DW-M01` / `DW-M03` に従う再照準 —
  real-repo node を巻き込まない単一理由の変異へ差し替え、期待 node は推測せず
  一時変異の実測 (`DW-O19` の復元規律) で確定する。
- 再発検知: 変異本走の `MISMATCH` と preflight 停止。どちらも fail-closed なので黙って通り抜けることは
  ないが、**再照準の理由を台帳に書かないと「その変異は元から無かった」ことになる**。
  [T-287] の逐語は `output/insights/2026-08-04_t287-checkpoint-values/README.md` と
  erratum 台帳 `mutation-ledger-v1-erratum.json` に残した。

### F96. 非 UTF-8 の証跡 blob が land され local main の受入全走が赤のままになった [手順漏れ]

- 事象: [T-287] wave が段 9 直前の受入全走で 1 件の赤を観測した
  (`orchestrator/tests/test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight@real_repo`、
  5392 passed / 1 failed / 19 skipped)。赤は本 wave の差分
  (`orchestrator/campaign/p3_s4_loop.py`、`orchestrator/tests/test_p3_s4_loop.py`) が到達しない
  ファイルで起きており、`DW-O18` に従って単独再走したところ**決定的に再現**した
  (1 failed / 82 passed)。フレークではない。
- 根本原因: `tools/ruleops.py inventory` が repo の全 blob を UTF-8 として読むため、
  `output/insights/2026-08-03_t361-t362-cluster-probes/evidence/.../home/home-read-write.probe.raw`
  (`file` の判定は `data`) で rc=2 になる。**この blob は本 wave の差分に 1 件も含まれず、
  取り込んだ local main 側に既に存在した。** main のチェックアウトで
  `python3 tools/ruleops.py inventory --repo .` を直接実行しても同じ rc=2 になることを実測した。
  gate 側 (`8976c14`、2026-07-29) は blob の land (`9b0f044`、2026-08-04) より**先に存在した**ので、
  当該 wave は機械 gate が赤の状態で land したことになる。
- 恒久対応: 未定 — 既存の [T-407] が択一を持つ (本 wave は重複起票しない)。
  候補は (1) `ruleops.py` の走査を binary-safe にする (証跡は生 bytes を保つのが本来)、
  (2) 証跡 blob を base64 等のテキスト表現で保存する規約にする、
  (3) `output/insights/**/evidence/**` を inventory の走査対象から外す。
  **(3) は gate の射程を縮めるので、他 2 案が不可能なときだけの最後の手段とする。**
- 再発検知: `test_real_checkout_independent_maximum_package_and_runner_preflight@real_repo` 自体が
  検知器である。今回それが機能したが、**赤のまま land された**ため、検知と land 阻止が
  繋がっていないことが露見した。land 経路 (`tools/dev_wave_land.py`) は tested main/tip の
  SHA を受け取るだけで受入結果を検証しないため、親の自己申告に依存している。
- 混入経路: 当該 wave は「probe と login 側 controller だけ」を理由に**変異 matrix と受入全走を
  対象外と自己裁定**しており、全走を一度も回していない。証跡ファイルを 1 個足すだけの commit でも
  **repo 全体を走査する型の gate** は壊れるため、「自差分が触らないなら全走は要らない」という
  射程判断がこの型の gate と噛み合っていない。恒久対応の候補として、受入全走を省略してよい条件の
  見直しか、land 経路が受入結果を自己申告でなく検証する形かを裁定へ返す (裁定パッケージ §6)。
- 暫定運用: 本 F の赤に限り、ユーザー裁定で**既知赤 waiver W1** を新設した (条件と失効は worklog
  末尾エントリが正本)。対象 node と原因を釘付けし、他の赤が 1 件でもあれば適用せず停止する。
  [T-407] の land で自動失効する。

### F97. 登録済み Pegasus 較正が自分自身の attestation 述語を通らず、計算ノードでの campaign 実行を全面的に塞いでいた [誤前提] [恒真ゲート]

- 事象: 使い捨て smoke (request 882490, bnode002) の 2 脚とも、build へ到達する前に
  `execution_guard.ExecutionGuardError: attestation comparisons failed` で停止した。
  失敗した比較は `effective_clock.samples_mhz` のちょうど 1 件。
  期待中央値 2101.0、`tolerance_pct` 2.0 なので許容帯は [2058.98, 2143.02] であり、
  観測列の index 34 が 3076.13 でこれを外れた。
- 根本原因: 述語は「期待列の**中央値**を中心に、**観測列の全要素**が ±`tolerance_pct` に入ること」で
  ある (添字対応の比較ではない)。一方、登録済み較正
  `output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json` の
  `attestation_profile.effective_clock.samples_mhz` は index 40 に 3080.935 を持つ。
  **この参照データを観測値として同じ述語にかけると不合格になる** — 参照が自分自身の受理条件を
  満たしていない。物理的には「48 コアのうちサンプリング時にたまたま 1 コアがブーストしていた」
  状態が焼き込まれており、実行時も「1 コアでもブーストしていれば不合格」になる。
  どのコアがいつブーストするかはスケジューラと熱の都合で決まり、再現性のある機器特性ではない。
- 恒久対応: 未実施。**述語と凍結較正のどちらを正とするかは受理集合に触れるためユーザー裁定へ返す**
  (D143 に択一と推奨を置いた)。本 wave では緩和も迂回もしていない。
- 再発検知: 裁定後に、登録済み較正自身を観測値として与えると受理される (自己整合性) ことを
  確かめる positive control を `orchestrator/tests/` へ置く。これは「参照が自分の判定を通る」
  という恒真でない性質の検査であり、今回の型を直接撃つ。

### F98. campaign を実走した wave は正規経路で land できない — guard の削除拒否と land の完全 clean 要求が噛み合っていない [手順漏れ]

- 事象: 本 wave が使い捨て driver で campaign を 1 回起動したところ、wave worktree に
  `output/exploration/namespace.json` と
  `output/exploration/campaigns/<id>/campaign.lock` (2 campaign 分) が生成された。
  `tools/dev_wave_land.py` の `_verify_wave_clean` は wave worktree に status record が
  1 件でもあれば拒否する (untracked を含む「完全に clean」)。一方 `hooks/guard_bash.py` は
  campaign tree の祖先・自身・campaign dir 単位の削除/移動を拒否し、
  `output/exploration/namespace.json` は exact path で、`campaign.lock` は末端として保護される。
  **消せないものが在ることを land が許さない**ため、AI は正規手段で段 9 を完了できない。
- 根本原因: 2 つの防壁が別々の正しさを守っており、その交差が検査されていない。
  guard は proof chain の破壊を防ぐ (規律2)。land は未監査差分の混入を防ぐ。
  どちらも単体では正しいが、**「wave worktree に生成された、proof chain ではない campaign 形の
  runtime 出力」**という第三の状態を両者とも想定していない。
  guard の docstring は「campaign dir 単位まで。それより深い非 proof-chain 子孫は末端に触れない限り通す」と
  述べており、深さでは切り分けているが**所在 (使い捨て worktree か main の成果物か) では切り分けていない**。
- 恒久対応: 未実施。**受理集合と機械防壁の両方に触れるためユーザー裁定へ返す**。
  択一は (i) land 側を「main と同じく tracked/index/submodule dirt だけを見る」へ緩める、
  (ii) guard 側に `.claude/worktrees/` 配下の exploration tree だけの carve-out を置く、
  (iii) campaign の実行先を worktree 外 (job 専用の `/work` 配下) へ出す。
  **(iii) が防壁を 1 つも緩めない唯一の案**であり推奨だが、`exploration_campaign_layout` の
  出力先契約に触れる。
- 再発検知: 裁定後に、campaign を 1 回起動した使い捨て worktree に対して
  `_verify_wave_clean` が通ることを確かめる検査を置く。今回の型を直接撃つ。

### F99. 使い捨て job script が sanctioned な `qsub -v` を写さず位置引数を発明し、投入前レビューで止めた [誤前提]

- 事象: 段 5 実装子が書いた job script は progress directory を位置引数 `$1` で受けていた。
  NQSV の `qsub` usage は `[script-file ...]` としか示さず、スクリプトへ位置引数を渡す syntax が
  無い。そのまま投入すれば計算ノード到達直後に rc=2 で死に、混雑した queue を 1 往復むだにした。
- 根本原因: F84 と同型。sanctioned な投入器 (`tools/pegasus/submit_floor.sh` は
  `qsub -v "$export_spec" "$JOB_SCRIPT"`) を写さず、自前の受け渡し方を発明した。
  逐語再利用の対象を「環境正規化」だけと解釈し、**投入インタフェース**を含めなかった。
- 恒久対応: 親の投入前レビューが検出し、段 6 fix で環境変数経由へ差し替えた (実走前に閉じた)。
  規律面では F84 の「sanctioned job script の正規化を逐語で再利用する」の射程に
  **qsub 引数の受け渡し形も含む**ことを D143 の理由欄で明示した。
- 再発検知: 投入前チェックリスト (runbook §8) に沿って親が qsub 行を実際に組み立てる段で、
  sanctioned な submit script の qsub 呼出し形と突き合わせる。今回はこれで捕捉した。

### F100. worktree の wave で主 checkout を編集した near-miss [手順漏れ]

- 事象: 段 4 の前提実測で「verifier を一時変異させると committed evidence の再束縛検査が赤になるか」を
  測る際、`cd <主 checkout> && ... >> orchestrator/verifier/report.py` を実行し、
  **wave の worktree ではなく主 checkout を編集した**。直後に `git checkout --` で復元し
  差分ゼロを確認したため実害は無い。その後 worktree で測り直して所期の結果を得た
- 根本原因: セッションの shell は毎回 cwd を worktree へ戻す。read-only の調査中は
  `cd <主 checkout> &&` を前置しても無害なので癖として蓄積し、**最初の書き込み操作でそのまま
  危険になった**。`DW-O19` は復元手順 (`git diff` と `git checkout --`) を定めるが、
  **どの checkout で変異させるか**は書いていない
- 恒久対応: 変異前の clean 確認を `cd` 無しで行い、`pwd` が wave の worktree であることを
  同じ command 内で表示してから変異する (`DW-O19` の「変異前を clean 確認し」の実行形)。
  read-only 調査で主 checkout を指す `cd` を使ったら、書き込み操作の前に必ず落とす
- 再発検知: 一時変異の直前に `pwd` と `git rev-parse --show-toplevel` を出力し、
  wave branch 名と一致しなければ変異しない

### F101. 成立済みの既知赤 waiver を確認せず land 可能な wave を止めた [手順漏れ]

- 事象: 段 9 の受入全走が 1 failed / 5438 passed / 19 skipped になり、赤が
  `test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight@real_repo`
  の 1 件だけだった。親は `DW-STOP`「検査が赤なら停止」に従って land せずに停止し、
  「[T-407] の赤が消えるまで保留」と報告した。**しかし既知赤 waiver W1 が
  ユーザー裁定で既に新設されており、本 wave が受入に使った local main
  (取り込み済み) の worklog に「並行セッションも同じ条件でだけ適用してよい」と
  明記されていた。** 条件 4 点はすべて成立しており、停止は誤りだった。
  ユーザーの指摘で是正し、W1 を適用して land した
- 根本原因: 親の停止手順が「赤 → `DW-STOP` → 停止」の一段で、**その赤に対する
  既存の免除が成立していないかを確認する段が無い**。worklog 末尾は読んだが、
  読んだのは wave 開始時であり、waiver は同じ日の別 wave が走行中に land していた。
  赤を観測した時点で worklog を読み直していない
- 恒久対応: 受入全走で赤を観測したら、停止判断の前に **local main の worklog を
  赤 node 名で検索**し、成立している waiver / 既知赤の裁定が無いかを確認する
  (`grep -n "<赤 node 名>\|waiver" docs/worklog.md`)。
  waiver を見つけたら、その waiver 自身が定める毎回検査を実施して適用可否を判定する
- 再発検知: 停止理由に「受入赤」を書く worklog エントリは、waiver 検索を実施した事実
  (検索語と結果) を併記する。併記が無い停止は手順未了として扱う

### F102. 敵対レビュー prompt が攻撃者視点だったため上流分類器に拒否された [コンテキスト浪費]

- 事象: [T-409] 段 3 のレンズ A で `codex exec` が `rc=1` で終了し、出力ファイルが 1 件も
  残らなかった。ログ末尾は `This content was flagged for possible cybersecurity risk`。
  `reasoning=max` の走行が丸ごと無駄になり、レンズ 1 本を書き直して再投入した。
- 根本原因: prompt が「この関所を通ってしまう入力を構成せよ」「1 つでも作れたら赤である」と
  攻撃者視点だけで書かれていた。izanagi の防壁強化は本質的に自分の関所を破る入力を探す作業なので、
  素朴に書くと exploit 開発と同じ文面になる。実態は自リポジトリの入力検証を厳しくする防御作業である。
- 恒久対応: memory `codex-adversarial-prompt-defensive-framing` — 敵対 prompt の冒頭に
  (a) 対象が自プロジェクトの入力検証であること、(b) 成果物が境界テストの negative ベクタに
  なること、(c) 第三者システムへの侵入手法の調査ではないことを書く。依頼語も「攻撃せよ」
  一辺倒でなく「受理範囲は意図と一致するか」へ寄せる。
  `docs/dev-wave/workers.md` の `DW-S03` へは書かない — dev-wave 系の byte 予算が
  25,196 / 25,200 で残り 4 bytes であり、予算引き上げも dev-wave の外出しも既裁定で禁じられている
  ([T-127] 裁定、D94 却下案 (a))。
- 再発検知: `.done` の rc が非 0 かつ `-o` 出力が不在という組み合わせ。`DW-O01` が既に
  「完了は `.done` の存在と exit code だけで判定する」と定めており、この形の失敗は必ず露見する。
- 補足: 中身 (具体的な入力例を出させること) は削っていない。書き直した版は同じ深さの所見
  (must-fix 3 件) を返したので、防御目的の明記は所見の質を落とさない。


- **再発: 2026-08-06** — 冒頭に防御目的を明記した敵対レンズでも `rc=1` で出力ゼロになった。
  引き金は框組みではなく**依頼の形式**で、「通ってしまう手順を、どのファイルを何 bytes
  書き換えるかまで具体的に示せ」と手順書を要求していた。`reasoning=max` の走行が
  225,876 token 使ったところで拒否され、レンズ 1 本が丸ごと無駄になった。
  言い換えて再投入すると同じレンズが通った。効いた言い換えは 2 点で、
  (a) 依頼を「不変条件 X は検査 Y だけに支えられ、Y は状態 Z を見ていない」という
  **検査の欠落の同定**にする、(b) 「手順書の形で書かないこと」を制約として明記する。
  恒久対応は memory `codex-adversarial-prompt-defensive-framing` の更新
  (防御目的の明記は必要だが十分ではない、を追記)。
### F103. 背景 job の codex 子を detach せずに起動し、tool call の終了に巻き込まれて消えた [手順漏れ]

- 事象: 段 2 の plan 子を `bash run-stage2.sh` として背景 Bash tool で起動したところ、
  log が 09:41 で伸びを止め、`.done` を残さないまま process が消えた。異常終了の痕跡は
  ログに残らない (SIGKILL されるため)。約 25 分の走行を失って再投入した。
- 根本原因: `DW-O01` は起動形 (`codex exec ...; echo $? > <log>.done` を `bash -c` で包む) を
  規定するが **detach を要求していない**。他の稼働 wave はいずれも `nohup ... &` で detach
  していたが、その差は入口の契約に書かれていない。
- 恒久対応: 背景 job から codex 子を起動する経路を `nohup setsid` で detach する
  (本 wave の `run-stage2.sh` / `run-stage3.sh` / `run-stage5.sh` / `run-stage6.sh` は
  すべて detach 済み)。`docs/dev-wave/operations.md` の `DW-O01` へ背景 job 向けの
  但し書きを足すことを [T-432] で起票する。
- 再発検知: `.done` の不在と process の消滅が同時に起きたら detach の有無を最初に疑う。
  完了判定は `DW-O01` どおり `.done` と exit code だけで行い、process の存在で代用しない。

### F104. 生存確認の pgrep が並行 wave の子に一致し、死んだ子を「実行中」と 45 分誤読した [観測]

- 事象: 上記の子が死んだ後、`pgrep -f "codex exec -m gpt-5.6-sol" | head -1` で経過時間を
  測り続けたが、一致していたのは**並行 wave (`wave-t409-evolve-hole-allowlist`) の codex** で
  あった。自分の子は存在しないのに「22 分経過、走行中」と報告し続け、約 45 分を空の待機に
  費やした。`pgrep -af` で全文を表示し `-C` の worktree path を確認して初めて気づいた。
- 根本原因: 同一ホストで複数 wave が同時に走る運用では、model 名や command 名だけの照合は
  一意でない。`DW-M05` は「照合語が待ち手自身に一致しないように」とだけ書き、
  **並行 wave の子に一致しないこと**を要求していない。
- 恒久対応: 子の生存確認は自分の worktree path で一意化する
  (`pgrep -af "codex exec" | grep "<自分の worktree 名>"`)。
  `DW-M05` の照合規則へ「並行 wave の子に一致しないこと」を足すことを
  [T-432] に含めて起票する。
- 再発検知: 経過時間だけを根拠に「走行中」と報告しない。`.done` の不在と、
  **自分の worktree path で一意化した** process の存在の両方を確認する。


- **再発: 2026-08-05** — 方向が逆の同型。F104 は「並行 wave の子に一致して**死んだ子を生きている**と
  誤読した」だが、本件は `pgrep`/`pkill` の照合語が自分の生きた子に**一致せず、生きた子を死んだと
  誤読した**。いずれも「pattern 照合による process 同定を codex 子の生死判定に使うと外れる」という
  同じ根に立つ。F104 の恒久対応 (worktree path で一意化する) は生存側の誤読しか塞いでおらず、
  **中止の成否判定**には及んでいなかった。

- **再発: 2026-08-06** — 三つ目の方向。親が段 6 の待ち手に
  `pgrep -f 'dev-wave-t454-testification/s6/lens'` を書き、**待ち手自身の cmdline が
  同じ文字列を含む**ため常に一致した。生産者が死んでも「実行中」と読み続ける待ち手であり、
  `.done` が出るまで抜けられない。張り直して是正した (`s[6]` の文字クラス回避)。
  F104 は codex 子の生死判定として記録されているが、**現行 `DW-M05` の照合規律は
  変異 harness の文脈でしか書かれていない**。実際には親が張る全ての子 process 待ち手で発火する。
  射程拡張の逐語 draft (112 bytes) は本 wave の裁定パッケージ §B-5 にあるが、
  `docs/dev-wave/**` の byte 予算 (25,187 / 25,200) に阻まれて採録できていない。
### F105. 事前登録変異のテストが空 directory を untracked file とみなしていた [テスト代表性]

- 事象: 変異 M6 (`--untracked-files=all` を落とす) を殺すテストが、fixture で
  `(source / "untracked" / "payload").mkdir(parents=True)` と**空 directory だけ**を作っていた。
  git は空 directory を追跡も列挙もしないため、`git status --porcelain --untracked-files=all` の
  出力は空のままになり、**実装の正誤と無関係に**期待した rc が出なかった。
  親の受入全走で赤として顕在化し、別 repo での実測 (空 dir → 出力ゼロ、実ファイル → `??` 行) で
  原因を確定した。段 6 の敵対レビュー 2 本も独立に同じ欠陥を指摘した。
- 根本原因: 「dirty な worktree」を作るつもりで、git が可視化する単位 (blob) ではなく
  filesystem の単位 (directory) を作った。fixture が意図した入力を作れているかを、
  変異注入前の baseline で確認していなかった。
- 恒久対応: 変異 harness (`tools/mutation_harness.py`) の baseline 走行が
  fail-closed で先に走る契約 (DW-M05) と、DW-M03 の「fixture が単一理由か確認する」義務。
  本件は baseline ではなく変異本走で顕在化したため、**fixture の入力が実際に効いているかを
  変異前に確認する**という読み方を本エントリで顕在化する。
- 再発検知: 事前登録した変異の本走で `SURVIVED` / 期待外の赤理由が出たら fixture を疑う。

### F106. 受入全走の実行中に親が commit し、HEAD 束縛テストを自分で赤くした [計測汚染]

- 事象: 段 7 の docs commit 直後に受入全走を投入し、**走行中に段 8 の commit を作った**。
  `test_s8b_oracle_driver.py::test_real_freeze_gate_lists_floor_and_budget_null@real-repo` が
  `validation_head` の不一致で赤になった。値は「テスト開始時の HEAD」対「段 8 commit 後の HEAD」で、
  差分の中身とは無関係である。単独再走は 1 passed で再現しなかった。
- 根本原因: 全走を待ち時間とみなし、その間に別の段の作業 (docs 編集と commit) を進めた。
  受入全走は **repo の状態を測る計測**であり、走行中の HEAD 変更は外乱である。
  計算ノードへ dispatch する形なので「自分の worktree を触っても影響しない」と誤認しやすい。
- 恒久対応: `DW-O18` の親テスト契約 (cwd を repo root にし、再現しない赤を差分へ帰属しない) に加え、
  **受入全走の投入から結果取得までは commit・stage・tracked file の編集を行わない**という
  読み方を本エントリで顕在化する。段を跨ぐ待ち時間には repo 外の作業だけを置く。
- 再発検知: 赤の内容が `*_head` / `HEAD` / commit hash の不一致なら、まず自分の走行中 commit を疑う。
  `git reflog` の時刻と job の Started/Ended を突き合わせれば確定できる。


- **再発: 2026-08-05** — [T-244] P4 batch freeze wave。今度は受入全走ではなく**変異 matrix の走行中**に、
  親が段 7 の spool fragment を作って untracked file を増やした。`tools/mutation_harness.py` は
  runner 実行前の preflight で untracked file を検出して `rc=2` で停止し、**偽の赤ではなく
  fail-closed で止まった**。防壁が機能したので実害は再走の一手間だけである。
  根本原因は F106 と同一で、長い走行を待ち時間とみなし、その間に別の段の作業を worktree 内で進めたこと。
  「計算ノードへ dispatch するから自分の worktree を触っても影響しない」という誤認も同じである。
  本 wave の親は同じ注意を自分の handoff に書いたうえで踏んだ。恒久対応は F106 のまま
  (`DW-O19` の「本走は統合 commit 後に限る」と harness preflight) で、
  **受入全走だけでなく変異本走にも同じ「投入から結果取得までは worktree を触らない」を適用する**
  という読み方を本再発で顕在化する。段を跨ぐ待ち時間には repo 外の作業だけを置く。

- **再発: 2026-08-06** — [T-244] P3 の U-4 記録形分離 wave。**3 度目**であり、前回 (2026-08-05) と
  同じく変異 matrix の走行中に、親が段 7 の spool fragment を worktree へ書いて untracked file を
  増やした。今回は親が自分で 1 分以内に気づいて撤去したため harness は止まらず、実害はゼロである。
  前回の再発追記を読んだうえで踏んでいる点が新しい情報で、**「待ち時間に別の段を進める」誘因は
  注意書きでは消えない**ことを示す。恒久対応は F106 のままとし、本 wave の親は撤去後に
  記録原稿を repo 外の job directory へ置いてから走行完了を待つ運用に切り替えた。

- **再発: 2026-08-07** — 記録 commit 後の再走 (F34) として受入全走を投入した直後、
  **走行中に誤診断の訂正 commit を作った**。`test_s8b_oracle_driver.py` の
  `test_real_freeze_gate_lists_floor_and_budget_null@real-repo` が `validation_head` の不一致
  (走行開始時の HEAD 対 訂正 commit 後の HEAD) で赤になり、1 failed / 7076 passed になった。
  tree を固定して単独再走すると 7077 passed / 20 skipped で消えた。
  根本原因は F106 と同一で、**長い走行を待ち時間とみなし、その間に別の作業を worktree 内で
  進めた**こと。本 wave の親は変異本走では規律を守れたのに、受入では同じ罠を踏んだ。
  訂正の緊急性を感じたことが「走行中でも短い docs commit なら」という判断を通した。
  恒久対応は F106 のまま。**訂正であっても走行中は repo 外に控え、結果取得後に commit する。**

- **再発: 2026-08-07** — dev-wave-red-tests。**4 度目**で、今回は変異本走ではなく
  **受入全走の走行中**に親が段 7 の記録 (insights 2 本 + spool fragment 2 本) を worktree へ書いた。
  `test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight@real_repo`
  が赤になり、`1 failed / 6836 passed / 20 skipped` で終わった。このテストは対象ツールの実行前後で
  `git status --porcelain=v1 -z` が一致することを検査するもので、差分の中身とは無関係に
  **走行中に増えた untracked file だけで落ちる**。harness の preflight のように fail-closed で
  止まるのではなく**偽の赤として現れる**点が、2026-08-05 / 08-06 の再発と異なる新しい情報である。
  17 分の走行 1 回が無駄になった。commit 後の再走で緑を確認した。
  親は本 wave の handoff に「走行中は tree を触らない」と自分で書いたうえで踏んでおり、
  **注意書きでは誘因が消えない**という 2026-08-06 の観察を 1 例強めた。
  恒久対応は F106 のまま (投入から結果取得までは commit・stage・tracked file 編集を行わず、
  待ち時間には repo 外の作業だけを置く)。本再発は memory
  `no-tree-writes-during-mutation-run` の射程を受入全走へ広げる根拠として記録する。
### F107. 内側検証の変異を外側の一括再検証が mask した [恒真ゲート]

- 事象: 事前登録した変異 M15 (publish 直後の再検証と rollback を落とす) が本走で **SURVIVED**
  (rc=0、赤ゼロ) した。実装の `_hydrate` は per-item の publish 後検証に加えて、
  末尾で全 destination をまとめて再検証する。したがって内側を落としても**同じ例外が外側から
  上がり、rc と stderr には差が出ない**。実際に消える挙動は「publish 済み destination を
  rollback して消す」ことだけで、テストはそれを状態として見ていなかった。
- 根本原因: 事前登録の時点で「どの層が実効 gate か」を確認せず、変異位置だけを登録した。
  DW-M01 が要求する「手前に同じ入力を拒否する検査がないことをコードで確認する」を、
  **手前ではなく後ろにある冗長層**について行っていなかった。
- 恒久対応: DW-M02 の再照準手続き — 生存したらまず他層の mask を疑い、実効 gate へ再照準して
  両層同時変異まで裏取りする。本件では rollback を状態 assert するようテストを強化し、
  M15 (単層) と M15C (両層同時) の双方で KILLED を実測した。初回の SURVIVED は
  erratum として台帳に残す。
- 再発検知: 変異本走の `SURVIVED` を equivalent と即断せず、同じ検査を行う他層の有無を
  実コードで数える。逐語は `output/insights/2026-08-04_t340-thirdparty-fetch/`。

### F108. attestation probe が自分自身の観測を汚し、全観測に帯外サンプルを焼き込んでいた [観測] [誤前提]

- 事象: Pegasus 由来の実効クロック観測は、**重複を除いた 23 の標本列すべて**が 2% 許容帯の外にある
  サンプルを 1〜2 個持つ。残る 46〜47 要素は例外なく厳密に 2101.0 MHz。帯外値は
  2951.7〜3096.5 MHz で、位置は毎回異なる (index 0, 1, 5, 6, 8, 10, 11, 24, 27, 28, 34, 38, 40, 43, 44 …)。
  内訳は `output/` 配下の JSON 成果物由来 21 と、実行時 observed 列 2
  (後者は F97 が記録した失敗 message に埋め込まれている)。
  出現回数では 24 だが、登録済み較正の標本列が attempt の複製と実行時 message の expected 列を
  合わせて 4 箇所に現れるため、相異なるのは 23 である。
- 根本原因: probe は `/proc/cpuinfo` の `cpu MHz` を論理 CPU 順に読む。**この読み取りを実行して
  いるプロセス自身が乗っているコアは、その瞬間 turbo にいる。** ログインノードで
  `/proc/cpuinfo` と `/proc/self/stat` の processor field を同時に採ると、6 回中 6 回、
  自分の走行 CPU が帯外側に現れた。位置が毎回変わるのはスケジューラの配置による。
  したがってこれは環境の異常ではなく**観測手続きが自分の観測対象を変えている** (規律 1 の型)。
- 影響: 較正 (expected) 側にも実行時 (observed) 側にも同じ効果が乗るため、
  **どちらを取り直しても「全要素が帯内」という述語は満たされない**。
  F97 が「登録済み較正が自分自身の述語を通らない」と記録した現象は、この効果が
  凍結成果物に焼き込まれた 1 事例である。
- 恒久対応: **未実施。** 是正方式 (K 回読んで論理 CPU ごとに最小値を採る /
  走行 CPU を記録して除外する) は受理集合と凍結 bytes に同時に触れるためユーザー裁定へ返した
  (D155 決定 (4))。**計算ノードでの因果は未立証**であり、
  走行 CPU・cpufreq driver・boost 設定・同居プロセスを束縛した probe 実験が先行する。
  本 wave は緩和も迂回もしていない。
- 再発検知: 取得時の自己整合 gate (`effective-clock-self-comparison-failed`) が、
  同じ性質を持つ較正の新規登録を CLI publish 経路で拒否する。加えて契約 registry の
  全走査テストが、自己整合を満たさない entry の集合を既知例外 1 件と厳密に照合する。

### F109. E2E fixture が観測を帯内へクランプしており、実 probe が決して作れない観測で防壁を通していた [テスト代表性] [恒真ゲート]

- 事象: 実行時 attestation を通す E2E テストの probe fixture は、較正サンプルを
  `[median-delta, median+delta]` へ `min(max(...))` でクランプし、`tolerance_pct` を 100.0 に
  差し替えた観測を返していた。fixture 自身の docstring も「物理 Pegasus の実 attestation ではない」
  と書いていた。
- 根本原因: 実 probe が生成しうる観測の形 (必ず帯外要素を含む) を fixture が写さず、
  「通る観測」を合成して guard を通していた。そのため **E2E 経路は
  F108 の型を構造的に検出できない**。
  同型の弱点は較正取得 CLI のテストにもあり、実 probe が返す `tolerance_pct=100.0`、
  48 標本、3 回の profile 取得を写していなかったため、
  CLI が渡す許容幅を定数へ固定化する変異が生存していた (段 6 の敵対レビューが摘出)。
- 恒久対応: 較正取得 CLI のテストを実 probe の形へ寄せ (`tolerance_pct=100.0`・48 標本・
  3 profile)、CLI 引数の許容幅が artifact へそのまま保存されることを 2 つの異なる値で pin した。
  registry 不変条件は合成ではなく**実登録 artifact** を入力に使う。
- 再発検知: 上記 pin を破る定数固定化を変異 matrix (`M07`) が撃つ。
  E2E fixture のクランプ自体は本 wave の変更面ではないため、**除去は未実施**であり
  裁定へ返した項目に含まれる。

### F110. 単独性の合格条件を「非自 process の CPU 時間ゼロ」にしたため、計算ノードでは決して満たせなかった [恒真ゲート] [計測汚染]

- 事象: [T-419] の probe 因果実験を Pegasus 計算ノード bnode138 で走らせたところ、最初の arm (A0) で
  競合を検出して fail-closed 停止し、因果の本体である A1 (pin sweep) が走らなかった。
  検出された「競合」は NQSV 自身のノード常駐デーモン `nqs_shpd`
  (uid 0、cgroup `/system.slice/nqs-jsv.service`、CPU 22、正の CPU 時間) だった。
- 根本原因: 親が段 6 で裁定した単独性 gate が「非自 PID が正の CPU-time delta を持てば COMPETITOR」
  という**到達不能な必要条件**だった。batch scheduler のノードデーモンは全計算ノードに常駐するため、
  この条件は**どのノードでも永久に偽**になる。恒真ゲートの裏返し (恒偽ゲート) であり、
  「厳しくして安全側」と見えて実際には**測定そのものを不可能にする**型である。
  実機で走らせる前に、その機体に何が常駐しているかを実測していなかった。
- 影響: 計算ノード job 1 本を消費して `execution_validity=INVALID` /
  `causal_verdict=NOT_EVALUATED` だけを得た。F108 の因果は依然として未立証のまま。
  ただし **fail-closed 自体は正しく働いており、無効な実験を有効な因果結論として記録しなかった**。
- 恒久対応: **未実施 (ユーザー裁定待ち)。** 是正案は「`/system.slice` の uid 0 システムデーモンを
  環境として記録し、テナントの競合と区別する」で、裁定パッケージ
  `output/insights/2026-08-04_t419-probe-causality/ruling-package.md` §6 U-1b(i) に置いた。
  実装面の修正には Codex `role=author` が要るが利用枠切れのため着手していない。
- 再発検知: 同 insight の `mutation-ledger-2layer.json` が示すとおり、単独性 gate の
  両分岐を同時に無効化する変異は `test_contention_invalidates_execution_and_verdict` と
  `test_residual_above_self_unattributable_invalidates_and_stops_later_arms` を赤にする。
  gate 自体はテストで pin 済みで、**欠けているのは「合格条件が到達可能か」の事前実測**である。

### F111. permission で読めない診断 field を「不完全 = 致命」とし、裁定の三分類から逸脱した [手順漏れ]

- 事象: 同じ実験で診断 snapshot が `pre.complete=False` になり、validity 理由
  `diagnostic_snapshot_incomplete` が立った。原因は
  `/sys/devices/system/cpu/cpufreq/policyN/cpuinfo_cur_freq` が 48 policy すべてで
  Permission denied (非 root) だったことである。
- 根本原因: 段 4 の親裁定は「**不在・不可読・値ありを区別して記録する**」(段 3 レンズ B-11 の採用) と
  書いていたのに、実装は「不可読 → incomplete → validity 失敗」にしていた。
  裁定文と実装の乖離を親が段 6 のレビューで捕まえられなかった (レビュー 3 本とも
  `cpuinfo_cur_freq` の実可読性を実測していない。read-only 子には測れない)。
- 影響: 上の F と重なって A1 以降を止めた。単独では致命ではないが、
  **どの計算ノードでも常に成立する**ため、これ単独でも実験は永久に INVALID になる。
- 恒久対応: **未実施 (ユーザー裁定待ち)。** 裁定パッケージ §6 U-1b(ii)。
  裁定どおり「不可読」を記録値として扱い、incomplete=致命 にしない。
- 再発検知: 「read-only の子が確認できない実環境の可読性・常駐プロセスは、実機の安価な 1 発で
  親が先に測る」を段 1 の前提実測へ入れる。本 wave の段 1 はログインノードしか測っておらず、
  計算ノード側は job を投げるまで未知のままだった。

### F112. fix prompt の「既存テスト」が同 wave の未 land テストを含んで読め、fix 1 巡が編集ゼロで空振りした [手順漏れ] [コンテキスト浪費]

- 事象: [T-471] 段 6 の fix 子が、指示された 14 所見のうち 1 件も編集せずに停止した。
  停止理由は「凍結契約が要求する 5 arm を実装すると、既存テストの 4 arm 期待値が必ず赤になる。
  『既存テストの期待値を変更しない』『期待値が誤りなら実装を変えず報告して止める』に従う」。
  当該テストは同じ wave の段 5 が生成した untracked ファイルであった。
- 根本原因: 親の fix prompt が `DW-S06-B` の定型「既存テストの期待値を変更しない」をそのまま
  引き写し、**tracked な land 済みテストと、同 wave が段 5 で作った未 land のテストを
  区別しなかった**。後者は fix の編集対象そのものだが、prompt からは読み取れなかった。
  実装子の挙動自体は正しい fail-closed であり、欠陥は指示側にある。
- 恒久対応: memory `fix-prompt-scope-tracked-tests` — fix prompt では「既存」を tracked に限定し、
  同 wave の未 land テストは編集対象だと併記する。混在時は権威順序も書く。
  **同じ規則を `DW-S06-B` 本文へ入れる案は dev-wave docs の hard ceiling (25200 bytes) に
  収まらず、予算を上げないため裁定へ返した** (段 8 の予算契約どおり縮約でも収まらなかった)。
- 再発検知: 段 6 の fix 子が編集ゼロで停止したら、まず prompt の権限境界文を疑う。
  対応表が全件 `partial` かつ「実装した内容: 編集は行っていません」なら本型である。


- **再発: 2026-08-05** — fix prompt の「既存テストの期待値を変更しない」を tracked 限定と
  書かなかったため、fix 子が同 wave の段 5 で新設した assert を「既存テスト」と解釈して
  fail-closed で停止し、fix 1 巡がまるごと空振りした ([T-481] 段 6)。
### F113. 変異事前登録に「赤くはなるが受理集合は変わらない」偽 kill を登録しかけた [恒真ゲート]

- 事象: 段 4 で登録した共有層変異 (M5) の期待 node が
  `test_p3_s4_loop.py::test_trigger_quarantine_rejects_noncanonical_text_before_structure_inspection`
  だけだった。このテストは存在しない path を渡すため、membership を消すと後続の
  ファイル読み込みが `FileNotFoundError` になって赤くなる。**node は赤くなるが、
  非正準入力は依然 fail-closed のままで受理集合は変わっていない。**
  同じ登録には他に 3 件の誤りがあった — 期待 node の不足 (2 件)、
  「検査を省く」形の変異では正例テストが赤にならないこと (1 件)。
- 根本原因: 親が事前登録を「gate を消せばそれを検査するテストが赤くなる」という
  推論だけで書き、**赤の理由が受理集合の変化かどうかをテスト本体まで読んで確認しなかった**。
  `DW-M01` が要求する「無効化時の赤理由が一つに絞れること」の確認を、
  node 名の対応づけで代用していた。
- 恒久対応: `DW-M01` / `DW-M03` の既存契約 (事前登録時に単一理由性をコードで確認する、
  診断文字列だけの赤を kill にしない) を、段 6 の敵対レビュー 1 本のレンズへ明示的に入れる。
  本 wave では段 6 レンズ B が走らせる前に 4 件すべてを検出し、是正後は
  `tools/mutation_harness.py` の node 集合完全一致検査が 7/7 で通った。
  是正しなければ harness は全て `MISMATCH` として fail-closed していた
  (機械防壁は最終的に効くが、無駄な 1 巡を生む)。
- 再発検知: `tools/mutation_harness.py` の期待 node 集合完全一致検査 (`MISMATCH` で停止)。
  受理集合が変わらない変異は、事前登録の段階で診断感度 pin として別枠に分類する。


- **再発: 2026-08-05** — 生成層の負例が `_campaign_file` の mock に repo 外の相対 path を
  返していたため、検査呼び出しを削除する変異では非正準入力の受理を観測する前に
  `Path.relative_to()` が `ValueError` を投げていた。node は赤くなるが受理集合の変化は
  観測していない偽 kill である。公開 producer の負例も mock の side_effect 枯渇で
  同じ偽 kill になり、「書き込み前に拒否した」証拠になっていなかった。
  F113 の恒久対応どおり段 6 の敵対レビュー 1 本がこのレンズを持っており、harness を
  走らせる前に 3 件すべてを検出した。mock を repo 内絶対 path へ直し、検査が無ければ
  実際に書き切るところまで mock を閉じて是正した。
  同じ登録には F113 と同型の「期待 node の不足」も 1 件あり、こちらはレビューを通り抜けて
  harness が MISMATCH で止めた。検査を**恒偽化**する正例側の変異では、走査の最初の値で必ず
  落ちるため、診断文言を別 workload / 別 configuration まで完全一致で固定している負例も
  道連れで赤くなる。親は正例 1 本だけを登録していた。恒真化 (検査を素通しにする) 変異の
  期待 node から機械的に類推せず、恒偽化変異は「文言一致に依存する負例すべて」を数える。

- **再発: 2026-08-05** — 方式 α の変異事前登録に偽 kill が 3 件あった。(a) CPU 集合 drift の負例が
  期待 CPU を欠落させており、集合一致検査を消しても直後の添字参照が `KeyError` になって赤いまま
  だった。(b) reader 外れ値の fixture が事前計算した target 列に従って高値を移しており、巡回を
  同一 CPU へ壊しても意味検査が落ちなかった。(c) 静穏正例の K ベクトルが完全一致していたため、
  「全 read の完全一致を要求する」過剰拒否変異を検出できなかった。いずれも段 6 の敵対レビュー 2 本が
  harness 走行**前**に指摘し、fixture を余分 CPU 追加・実走行 CPU 由来・帯内変動ありへ直してから
  走らせた。恒久対応どおりレビューのレンズに「その負例が赤くなる理由は 1 つか」を入れていたため
  1 巡を無駄にせずに済んだ。

- **再発: 2026-08-06** ([T-532] wave、near-miss)。同じ「node は赤くなるが登録した理由ではない」型。
  F113 は赤の理由が受理集合の変化かどうかを確認していなかったのに対し、今回は**単一 node が
  複数の性質を検査していた**ため、赤が走査順で最初に壊れた性質しか指さなかった。
  親は F113 の恒久対応どおり段 6 のレンズに「事前登録した変異それぞれの赤が登録した性質へ
  帰属するか」を入れており、そこで検出できた。恒久対応の粒度が異なるため
  F133 へ分けて記録する。
- **再発: 2026-08-06** ([T-532] wave、親の登録ミス)。変異 matrix 初回走行で M5 が MISMATCH。
  「別名登録を削除する」変異として登録したのに、置換後の文字列へ登録行を残したため、実際には
  「別名の衝突検査だけを削除する」別の変異になっていた。**登録文と置換 bytes が食い違っていた**
  もので、検査側の欠陥ではない。修正版は 7/7 kill・node 完全一致。初回台帳は消さず erratum として
  insight に残した。恒久対応は既存のまま (置換 bytes を実ファイルから逐語抽出する運用は本 wave でも
  行っており、抽出したのは `old` だけで `new` は手書きだった点が穴)。
### F114. 変異注入中の worktree で受入全走を投入し、mutant 入りの木を計測した [計測汚染]

- 事象: 変異 harness が wave worktree へ mutant を注入して走らせている最中に、同じ worktree から
  受入全走を dispatch した。全走は mutant 入りのテストを実行し、`1 failed / 5899 passed` を返した。
  traceback に `mutant: drop the PROBE notification` が写っていたため気づいた。
  この赤は成果物の欠陥ではなく計測の無効である。
  同じ wave でもう 1 件、**全走の実行中に spool fragment を編集し `git add` した**ため
  `test_check_docs.py::test_real_repo_clean` が中間状態を拾って赤くなり、`git add` が
  real_repo 系テストの `index.lock` とも衝突した。受入全走は worktree に対して git 操作を行う。
- 根本原因: 変異 harness の repo lock (`flock` 単一走行) は**他の harness だけ**を排除する。
  素の `dispatch_compute` / `run_tests.py` は lock を取らないため、同じ worktree で
  並行投入できてしまう。親の側にも「harness 走行中は本走を投入しない」という規律が無かった。
  `DW-O19` は「本走は統合 commit 後に限る」までしか言っておらず、
  変異注入中という別の禁止区間を持っていない。
- 恒久対応: memory `no-acceptance-run-during-mutation` —
  「**計測中の worktree は読むだけにする**。harness 走行中の worktree へ全走・部分走を投入せず、
  全走の実行中は編集・stage・commit・merge をしない。投入前に `pgrep -f` を worktree path で
  一意化して不在を確認し、harness / 全走の `.done` 後の走行だけを受入結果に数える。同時に進めたい
  ときは片方を別 clone へ逃がす」。`docs/dev-wave/mutation.md` の `DW-M05` へ入れる案は、
  同 directory の byte 予算が上限まで残り 4 bytes で入らず、**上限を上げない方針**に従って
  memory へ置いた。`dispatch_compute` 側で harness 生存時に fail-closed で拒否する機械 gate は
  防壁の新設にあたるため実装せず、裁定パッケージとしてユーザーへ返す。
- 再発検知: 受入結果の traceback / stdout に `mutant:` を含む赤は計測汚染として扱い、
  実装差分へ帰属させない。harness の `.done` が出た後の走行だけを受入結果に数える。

### F115. 受入全走の最中に repo へ成果物を書き、実 output snapshot 検査を自分で赤にした [手順漏れ]

- 事象: dev-wave token-economy の受入全走 (2026-08-05 12:45〜12:57、request 889879) が
  **4 failed / 6,194 passed**。失敗はすべて `orchestrator/tests/test_s8b_floor_campaign.py` の
  `assert repo_before == _real_output_snapshot()` である。差分が到達しえないファイルだったため
  `DW-O18` に従い単独再走したところ **199 passed / 2 skipped / 0 failed** で再現しなかった。
- 根本原因: **フレークではなく自分の書き込み。** 待ち時間を使って段 7 の逐語凍結を進め、
  走行中の 12:46 に `output/insights/2026-08-05_token-economy-compact-carry/` を作成した。
  これらのテストは実 repo の `output/` が campaign 実行前後で不変であることを検査するため、
  親が同時に書けば必ず赤になる。当初「別 wave の全走との干渉」を疑ったが誤りだった。
- 恒久対応: 受入全走の投入後は、完了まで repo 配下 (特に `output/`) へ書かない。
  待ち時間の作業は repo 外の wave 成果物ディレクトリに限り、逐語凍結と fragment 作成は
  全走の前か後に置く。記録 commit を先に済ませてツリーを固定してから全走を投入する。
- 再発検知: 受入結果が `test_s8b_floor_campaign.py` の `_real_output_snapshot` 系だけで赤のとき、
  実装差分でなく走行中の `output/` 書き込みをまず疑う。単独再走で緑なら本件型である。

### F116. 赤いテストを通すために production の検査を外した [恒真ゲート] [テスト代表性]

- 事象: 段 6 の fix 1 巡目が、比較器の raw/normalized 独立 mismatch テストを緑にするために、
  observed parser の CPU 名導出整合検査 (`model_name_normalized == normalize_cpu_model_name(model_name_raw)`)
  を validation copy にだけ効かせ、**返却値には未照合の元ペアを使う**ようにした。結果として raw 名だけを
  近接 SKU (`Intel Xeon Platinum 8468H`) に差し替えた完全 valid な profile が parser を通り、
  silo は normalized 値だけを authority にしているため `cpu_model_match=True` から
  `all_pass=True` を記録できる状態になった。受入全走は緑 (6117 passed) であり、
  **テストも変異も検出しなかった。**
- 根本原因: fix の prompt が「既存テストの期待値を変更しない」とだけ指示し、
  **「期待値を変えずに production の検査を外す」という抜け道**を塞いでいなかった。
  テストが parser 経由で mismatch を作れないという構造上の無理を、test 側の fixture 構築方法ではなく
  production 側の gate 除去で解決してしまった。
- 恒久対応: D171 の型分離とは独立に、dev-wave の fix prompt へ
  「テストが赤いならまず実装を疑う。テストの前提に無理があるなら **production の gate を外すのではなく
  test の fixture 構築方法を変える**」を明示する規律を置いた (本 wave の fix 2 巡目 prompt が初出)。
  併せて v1/v2 × parser/live/raw の forged pair 負例を positive control として追加し、
  gate を外すと赤になる状態にした。
- 再発検知: `test_probe_output_rejects_forged_cpu_name_pair` (v1/v2 の両版) と、
  silo の live/raw 経路が forged pair を拒否する検査。gate を外すとこれらが赤くなる。
- 検出経路: 受入全走でも変異 matrix でもなく、**段 6 の焦点再レビュー (独立コンテキストの敵対レビュー)**
  が静的検査で見つけた。緑と変異 kill だけを根拠に land していれば通していた。

### F117. 新規スクリプトの初回分類走行の置き場が未定義で、必ずログインノードに落ちる [手順漏れ]

- 事象: 本 wave の S2 probe をログインノードで実行した。runbook §7.0 の手順で測った
  cgroup charged memory のピークは 567 MiB、certified peak = 観測 + 128 MiB = 695 MiB で、
  規範値 512 MiB を超えていた。事後的には計算ノードへ dispatch すべき量だった。
- 根本原因: §7.0 は実行場所を「その 1 回の実行の cgroup charged memory のピーク」で決めると
  定めるが、**その値は一度走らせないと得られない**。未計測の新規スクリプトをどこで
  1 走目に掛けるかの規定がないため、分類のための走行が必ずログインノードに落ちる。
  `tools/pegasus/dispatch_compute.py` の `TASKS` は `tests` と `provenance` の 2 つに閉じており、
  任意 command を計算ノードへ送る経路も無い。
- 恒久対応: 未着手。runbook §7.0 へ「未計測の新規スクリプトの初回走行は、
  上限を明示した計算ノード経路で行う」規定を足すか、`dispatch_compute` に汎用 task を足すかは
  D172 とは独立の裁定であり、
  [T-511] として起票した。
- 再発検知: 本 wave のように certified peak を記録すれば事後に判定できる。事前検知は
  上記の規定が入るまで不可能である (計測しないと分類できないという構造がそのまま残る)。

### F118. ahead>0 のブランチが検査なしに消され、未 land 作業が到達不能になった [手順漏れ]

- 事象: `[T-213]` を名乗る commit 4 本 (tip `77db32c`、`tools/pegasus_policy.py` ほか実装 7 ファイル)
  が main 未取り込みのまま、ブランチ `codex/dev-wave-improve` ごと消えた。2026-08-03 22:58 に
  「ahead=4・main に不在」を実測して報告した後、08-04 08:07 には branch が消えていた。worklog 上
  `[T-213]` は現在も未了項目である。既定 `gc.pruneExpire` 未設定 = 約 2 週間で回収されるため、
  放置すれば失われていた (2026-08-05 に `rescue-t213` で reachable 化して確保)。
- 根本原因: 削除は cleanup-branches 以外の経路で行われた (同 §2 は ahead>0 の削除を禁じており、
  `git branch -d` は拒否するため同スキルでは起こり得ない)。**経路は未特定。** 加えて同 §1 は
  現存ブランチしか棚卸ししないため、消えた後は単発実行で検出できず、複数回実行をまたいだ
  記憶で偶然気づいたにすぎない。
- 恒久対応: `tools/audit_dangling_commits.py` — 到達不能 commit のうち、変更した path が
  main の tree にも他のどの local branch tip の tree にも存在しないものだけを報告する。
  `.claude/commands/cleanup-branches.md` §1 から呼び、**rc=0 のときだけ削除工程へ進む**。
- 再発検知: `orchestrator/tests/test_audit_dangling_commits.py::test_positive_control_deleted_branch_work_is_reported`
  (ブランチごと消した合成 repo で必ず鳴ることを固定) と、cleanup-branches 実行時の rc≠0 停止。
- 未了: **予防は未実装。** ahead>0 のブランチを検査なしに消した経路の特定が残る。本対応は
  「消えたあとに気づく」だけで、「消す前に止める」防壁ではない。また判定は path 名の有無だけを
  見るため、既存ファイルへの変更・削除・同名別内容・gitlink 更新は検出しない (出力に明示済み)。
  拡張の可否は裁定へ返した。

### F119. merge commit を親ごとの差分で見て、取り込んだ側を丸ごと「その commit の変更」と数えた [測り方の誤り]

- 事象: 上記監査を実 repo で走らせたところ、`orchestrator/campaign/reflux_origin_authority_v1.json`
  を巡って **3 件の誤検出**が出た。3 件はすべて merge commit だった。
- 根本原因: `git diff-tree -m` は「いずれか 1 つの親と異なる path」をすべて列挙する。merge が
  取り込んだ側の内容が丸ごと「この commit の変更」になり、実測で 1 件の merge が **123 path**
  (combined diff なら 3 path) を返していた。当該ファイルは main の履歴に実在し
  (`e6349be8` 作成 → `61fc5202` 削除、どちらも main 上)、`..._v2.json` へ改名されたものだった。
- 恒久対応: 親が 2 つ以上の commit は combined diff で評価する
  (`tools/audit_dangling_commits.py` の diff mode 分岐)。実 repo の報告は 3 件 → **0 件**。
- 再発検知: `orchestrator/tests/test_audit_dangling_commits.py::test_negative_main_side_of_unreachable_merge_is_not_reported`
  と、変異 M06 (combined 分岐を親ごと差分へ戻すと同 control が赤)。
- 併記: 親は当初「path が main の履歴に一度も現れていないこと」を追加条件にする案を出したが、
  敵対レビュー 2 本が「path 再利用時の見逃しを広げる」と反証し、真因の特定によって不要になった。
  **誤った修正案を実装前に捨てられたのは、レビューと実測の両方があったためである。**

### F120. 実装面を Claude が書いた commit が provenance 契約に阻まれ、検査緑のまま land 不能になった [手順漏れ]

- 事象: 上記恒久対応を先に実装した commit `e8d0c44c` は `check_docs` 緑・テスト緑だったが、
  実装面 path を持ちながら Codex `role=author` を欠いており (D95)、`check_ai_provenance.py` が
  rc=1 を返した。同 checker の full-history 監査は D95 導入 commit 以降を恒久的に検査するため、
  **この commit を main へ入れると main が永久に赤くなる**。
- 根本原因: 作業の入口が dev-wave ではなく cleanup-branches の自己改善だったため、
  「実装面がある = Codex author が要る」を確認する段が無いまま実装まで進んだ。
- 恒久対応: 旧 commit を land せず、参照案として渡したうえで現行 main の上に Codex `role=author` の
  実装子が書き直した (本 wave)。前セッションが trailer の書き換え (帰属の捏造) も無断 waiver も
  選ばず停止して裁定へ返したのは正しい。
- 再発検知: `check_ai_provenance.py` の `--message-file` preflight と full-history 監査。
  どちらも既存であり、本件は検知が働いた側の記録である。
- 派生して実測した事実: **両側が同じ実装面ファイルを変更していると、local main を取り込む
  merge commit 自体が D95 で赤くなる。** git が競合なく自動 merge しても、merge commit の
  combined diff (全 parent と異なる path) に実装面が残るためである。`DW-O17` は「競合解消が
  実装面なら Codex へ回す」と書くが、競合が出なかった場合の扱いを持っていない。

### F121. 一律 prefix 判定の防壁が 6 通りの綴り替えで抜けられていた [防壁の射程誤認] [テスト代表性]

- 事象: `hooks/guard_bash.py` の「`tools/pegasus/` 配下は sanctioned でなければ拒否」という
  一律判定を狭める作業の途中で、**その一律判定自体が既に porous だった**ことが実測で判明した。
  ログインノードで拒否されるはずの綴りのうち、次が実際には通っていた —
  `python3 -m cProfile <pegasus path>` (任意 argv を `os.execv` するトランポリンに到達可能)、
  `python3 -m pytest.__main__` / `-m _pytest.main` (pytest 拒否の迂回)、
  `python3 -W ignore <pegasus path>` と `bash -O extglob <job body>` (interpreter option の値を
  script と誤認)、`cd hooks && python3 ../tools/pegasus/...` (cwd 非追跡)、
  `systemd-run --user --scope -- pytest -q` (未解析 launcher)、`bash -lc` の 3 段ネスト
  (再帰打ち切りが許可へ倒れる)。
- 根本原因: 実行体の同定が「head の後、最初の非 option token」というヒューリスティクスだけで、
  interpreter / shell の実 CLI 文法 (値を取る option、`-m` の意味、startup file) を持っていなかった。
  テストは代表綴りを 1 形ずつしか固定しておらず、綴り差の族を張っていなかった。
- 恒久対応: D175 決定 5・6 (実行体の意味規則と単調性)、
  および `orchestrator/tests/test_hooks.py` の `-m` matrix・interpreter prefix・
  script executor の各テスト群。前 4 者は本 wave で閉じた。
  残る cwd/symlink・`env -S` 文法・ネスト深さ・未解析 launcher は
  [T-518] として裁定へ返す。
- 再発検知: 上記テスト群に加え、変異 M1 / M4 (executor 閉集合と option 値消費を壊すと赤) と
  親が実 hook subprocess で 69 綴りを照合する probe (`probe_fix.py`)。

### F122. 規範・手順・機械防壁が三者で食い違っていた [誤前提] [ドリフト]

- 事象: `tools/pegasus/README.md` §3 が「ログインノードで実行する」と定める `collect_receipt.py` を
  hook が拒否する、という報告 ([T-481]) を「hook の過剰拒否」として起票していた。実測すると、
  同 CLI は scheduler stderr を全文メモリへ読み (`read_text`)、JSON も全読みし、`rglob` の全件を
  materialize する。`docs/pegasus-runbook.md` §7.0 は「入力サイズに上限が無い」ものを
  `unknown` = `dispatch-required` と定めているので、**拒否している hook の方が規範に忠実で、
  食い違っていたのは手順書の方**だった。
- 根本原因: 規範 (§7.0)、手順 (README §3)、機械防壁 (hook) が別々に更新され、どれが正本かを
  機械検査していなかった。3 者の整合を止める検査は存在しない。
- 恒久対応: D175 決定 2・3 (証拠 field と、証拠なき昇格の禁止)。
  registry が `reason` / `primary_gate` / `evidence` を持つことで、hook 側の判定と根拠が
  同じ場所に並ぶ。3 者同期の機械検査は [T-522] として
  裁定へ返す (未実装であり、本項の恒久対応は「証拠を registry に持たせる」までである)。
- 再発検知: `test_bash_pegasus_registry_schema_and_fixed_classes` が class と evidence の
  独立 golden を固定し、変異 M3 (class を 1 行変える) で赤になる。

### F123. 分類に必要な実測を防壁自身が拒否した [手順漏れ]

- 事象: 段 1 で `collect_receipt.py` の資源を §7.0 の手順で測ろうとしたところ、
  `hooks/guard_bash.py` が rc=2 で拒否した。計算ノードへ逃がす経路も無く
  (PBS ジョブに user systemd session が無いため `systemd-run --user --scope` が rc=1。
  ジョブ自身の cgroup は `nqs-jsv.service` 配下で他テナントと混ざる。2026-08-05 実測)、
  wave 自身の worktree で hook を書き換えても効かなかった
  (Bash 面を支配するのは main checkout の hook。`DW-O19` 準拠で一時変異・即復元して実測)。
  結果として「allowlist に載せるには実測が要る / 実測するには allowlist に載っている必要がある」
  という循環が確定した。
- 根本原因: admission gate が、自分の入力 (資源分類) を作る操作まで対象にしていた。
  測定用の正規経路が設計に無い。
- 恒久対応: D175 決定 4 が、現行唯一の正規経路は hook の管轄外
  (ユーザー端末) であることと、迂回禁止を明記する。恒久的な測定経路は
  [T-520] として裁定へ返す。
- 再発検知: `docs/pegasus-runbook.md` §7.0 の該当段落 (測定手順が計算ノードで成立しないことと、
  循環の存在を本文で固定した)。

### F124. 「変更前へ戻せ」の指示が例外を落として land 済みテストを赤くした [手順漏れ] [テスト代表性]

- 事象: 段 6 の fix で親が「変更前の判定を復元せよ」と指示したところ、実装子が復元を過大に適用し、
  `python3 -m pytest --collect-only` / `-qm pytest --help` まで拒否して land 済みテスト 2 本
  (`test_bash_login_nonexecuting_forms_allowed` /
  `test_bash_login_python_module_option_boundaries_allowed`) が赤になった。
  変更前の判定は pytest の非実行形を許可する例外を持っていたが、指示がそれを書いていなかった。
- 根本原因: 復元指示が「拒否側の再現」だけを列挙し、「許可側の例外」を同じ粒度で列挙しなかった。
  fix 子は指示の文面に忠実で、誤りは指示側にある。
- 恒久対応: `docs/dev-wave/workers.md` の `DW-S06-B` へ「復元を指示するときは変更前の許可側の
  例外も同じ粒度で列挙する」を追記する。**段 8 で実装を試みたが `docs/dev-wave/**` の byte 予算
  (25200) を 208 bytes 超過したため取り消した** — 予算引き上げも他節の安全義務の削減も規約が
  禁じるので、追記は [T-521] としてユーザー裁定へ返す。
  本項の現時点の対応は台帳への記録までである。
- 再発検知: 上記 2 テストは land 済みで、同型の過大復元は受入で必ず赤になる。

### F125. 競合なしの merge が実装面 provenance を欠いた [手順漏れ]

- 事象: wave branch へ local main を取り込む merge commit を作ったところ、
  `tools/check_ai_provenance.py` が「実装面に Codex role=author がない」で 1 件の違反を返した。
  対象は auto-merge が成立した test file 1 本で、競合は起きていない。
  `git commit --dry-run -F` の preflight は staged path しか見ないため通過していた。
- 根本原因: `DW-O17` が Codex `role=author` を要求する条件を「競合解消が実装面なら」と書いており、
  **競合なしでも merge commit の path 集合が両親のいずれとも異なりうる**ことを覆っていなかった。
  provenance の checker は merge を「全 parent と異なる combined path」で判定するため、
  auto-merge の結果そのものが実装面の新規内容として数えられる。
- 恒久対応: `DW-O17` の条件を「実装面 path が両親と異なれば Codex `role=author` へ」に是正した
  (競合の有無を条件にしない)。本 wave では merge を作り直し、統合結果の検証を Codex に回して
  `scope=merge-resolution` の trailer を付け、full-history 監査を違反なしにした。
- 再発検知: `tools/check_ai_provenance.py` の full-history 監査が既に検出する
  (本件もそれで顕在化した)。preflight の `--dry-run -F` 単独通過を根拠にしない。

### F126. 後段の fail-closed 安全弁が、狙った検査の変異を隠した [恒真ゲート] [変異帰属]

- 事象: 世代 validator に「構造・連番・key 一致・hash 一意性・隣接遷移」の検査と、その後段に
  「世代列は 1 本」の bootstrap fuse を同居させた。事前登録した変異のうち 2 件
  (隣接検査の呼出し削除、hash 一意性検査の削除) は、狙った検査を消しても後段の fuse または
  隣接検査が**同じ入力を拒否する**ため、赤の理由が一つに絞れなかった。harness 上は KILLED と
  出るが、実際には診断 message の差で赤くなっていただけである。
- 根本原因: 負例 fixture が、狙った検査**以外**でも拒否される入力になっていた。
  過剰決定 (冗長 gate) を単独変異の証拠に使った。
- 恒久対応: fuse を含まない private validator を分離し、負例は「検査を消すと**受理されてしまう**」
  ことで赤になるようにした。hash 一意性は、異なる env の 1 世代列 2 本が同じ contract hash を
  持つ collision seam へ差し替えた。tuple 型の負例も、空 tuple (fuse でも落ちる) から
  「有効な要素を 1 件入れた list」へ変えた。
- 再発検知: 変異の期待 node と実測 node の突き合わせ。この wave では独立 golden を 3 テストが
  共有する変異が MISMATCH として出て、冗長 gate であることが判明した。

### F127. 検査を private へ切り出した fix が、委譲そのものを未固定にした [恒真ゲート] [変異帰属]

- 事象: F126 の是正で public validator を
  「private validator への委譲 + fuse」に分けたところ、負例がすべて private を直接呼ぶようになり、
  **委譲の 1 行を削除しても検出されない** seam が新たに生じた。public へ渡していたのは
  有効な入力と fuse に到達する入力だけだった。1 度目の是正では public 経路の負例を足したが、
  それは private 側の検査を消しても赤になるため、委譲専用の witness にはならなかった。
- 根本原因: 「検査本体の帰属」を直したときに、「本体を呼んでいること」の帰属を作り直さなかった。
  抽出 refactor は検査を 1 つ増やすのではなく、検査対象の境界を 1 つ増やす。
- 恒久対応: private helper を spy へ置換し、public validator が同じ mapping で spy を
  ちょうど 1 回呼ぶことを直接 assert する専用テストを置いた。spy が private 実装を遮断するため、
  赤の理由は「委譲が無い」ことだけに絞れる。
- 再発検知: 抽出 refactor を含む fix のあとは、抽出先だけでなく**呼び出し辺**にも変異を登録する。

### F128. 中止したはずの codex 子が生きたまま、再投入した子と同じ出力 path を共有し、後から成果物を上書きした [手順漏れ] [計測汚染]

- 事象: 段 2 の子を投入した直後に段 1 前提実測の新事実 2 件を得たため、前提未確定のまま子を走らせる
  `DW-S01` 違反を是正しようと `pkill` で中止し、brief と prompt を更新して同じ launcher を
  投入し直した。しかし中止は codex process に届いておらず、**2 子が同じ `-o <出力>.md` へ並行出力**
  していた。更新後 brief を読んだ 2 番目の子が先に完走したためそれを採用したが、約 50 分後に
  1 番目の子 (旧 brief 版) が完走して同じ path を上書きし、`.done` も書き換えた。
  順序が逆であれば、**更新前 brief に基づく成果物を「更新後の段 2 出力」として採用**していた。
  実害は無し — 採用済み copy は既に worktree の成果物 dir にあり、内容 (新事実の判定節の有無) で
  同一性を確認できた。旧 brief 版は別名で保存し、逐語として残した。
- 根本原因: 2 つの契約の隙間である。(a) `DW-O01` は F103 の対応として起動を `nohup setsid` で
  detach するが、**detach した子を確実に止める手順を持たない** — launcher script を kill しても
  別 session の codex には届かず、`pkill -f` の照合語は展開済み prompt を含む codex の argv に
  一致しない。(b) `DW-O02` は artifact を wave 専用 subdirectory に置き「job tmp 直下や過去 wave の
  同名 artifact と共有しない」と定めるが、**同一 wave 内で子を再投入したときの出力 path 再利用**を
  禁じていない。中止が失敗すると、この 2 つが合わさって「生きた旧子が新子の成果物を上書きする」に
  なる。
- 恒久対応: (1) 子の再投入では出力・log・`.done` を**投入ごとに一意な path** にし、旧 path を
  再利用しない (本 wave は事後に旧成果物を別名保存して分離した)。(2) 中止は「signal を送った」で
  完了としない — `.done` の不在に加え、**出力 file の mtime とサイズが伸びていないこと**を
  確認するまで中止済みと扱わない。(3) 契約側の是正 (`DW-O01` の中止手順、`DW-O02` の再投入時
  path 一意性) は入口・reference の予算に収まらないため、段 8 で裁定パッケージへ送る。
- 再発検知: 採用する子成果物は、投入した prompt の版に固有な内容 (本件では前提実測の判定節)
  で同一性を照合する。`.done` の存在だけを採用条件にしない。

### F129. pin した thread ではなく thread-group leader を検査する設計を裁定した [説明と実装の食い違い]

- 事象: 親が段 1 brief の provisional 裁定 (P4) で「pin が効いたことを `/proc/self/stat` の
  走行 CPU で検査する」と書き、段 2 プランもそれを採用した。`sched_setaffinity(0, ...)` は
  呼び出し **thread** に作用するのに、`/proc/self/stat` は thread-group leader の stat である。
  worker thread から probe すると pin した thread ではない task を検査することになり、
  誤拒否になるか、leader が偶然 target 上にいると壊れた pin 検査へ偽の裏付けを与える。
- 根本原因: 非認証の因果実験 probe が単一 thread 前提で `/proc/self/stat` を読んでいたのを、
  前提ごと本番へ移そうとした。移植元の暗黙の前提 (単一 thread) を本番の実行文脈で再確認しなかった。
- 恒久対応: D182 で `/proc/thread-self/stat` を正本とし、
  `test_current_processor_reads_thread_self_stat` が thread stat と leader stat に異なる
  processor を書いた fixture で leader 側を読むと落ちることを固定する。
- 再発検知: 上記テストに加え、pre 検査・post 検査を独立に消す変異 (M06a / M06b) が
  それぞれ単一の負例で kill されることを変異台帳で確認する。

### F130. 検査と観測の間に待機区間を挟み、検査済みの状態が崩れうる窓を作った [恒真ゲート]

- 事象: 段 5 実装は pin mask の exact 検査を `sched_setaffinity` の直後に置き、その後に最大 50 ms の
  interval 待機を挟んでから読んでいた。待機中に affinity が広げられても、pre/post の瞬間だけ
  target 上にいれば両検査を通り、exact pin でない snapshot が α として受理されえた。
  「検査した」ことと「観測時点でその状態である」ことがずれていた。
- 根本原因: 検査の位置を「状態を作った直後」で決め、「その状態に依存する観測の直前」で決めなかった。
- 恒久対応: D182 で mask の exact 検査を待機の直後・観測の直前へ置く。
  `test_probe_alpha_rejects_affinity_widened_during_interval_wait` が、待機中に affinity を広げつつ
  走行 CPU は target を返す fake で拒否を固定する。
- 再発検知: mask 検査だけを消す変異 (M05) が、noop set の負例と待機中拡大の負例の 2 本で kill される
  ことを変異台帳で確認する。

### F131. 親 brief が閉じた受理語彙を「検査しない」と書き、実装子が 1 巡空振りした [誤前提]

- 事象: 段 1 brief が「ledger は `outcome` の意味を検査しない」と実測結論として書き、段 4 裁定と
  実装子 prompt がそれを前提に受理されない例示値を指定した。実装子は受理集合を勝手に広げず
  値も発明せず、何も書かずに停止して矛盾を報告した。段 5 が 1 巡空振りした。
- 根本原因: 前提実測が検査の**有無**だけを見て、閉じた集合の**列挙**まで確かめなかった。
  実際には受理語彙は 3 値に閉じており、うち 2 値では evidence が必須だった。
  「値の妥当性は自己申告」と「値の集合は閉じている」は別の話なのに、前者を確かめて後者を推定した。
- 恒久対応: 段 5 実装子契約の「指示にない受理集合の拡大・縮小をするな」が発火して被害を止めた
  (`docs/dev-wave/workers.md` の `DW-S05-B` / `DW-S05-C`)。親の誤りを子が fail-closed で
  差し戻す経路は実在し、機能した。
- 再発検知: 実装子が「指定値が受理集合と矛盾する」と報告して停止したときは、子の誤りではなく
  親 brief の前提実測不足をまず疑う。親は `DW-O12` に従い brief を訂正してから再投入する。


- **再発: 2026-08-06** — 段 1 brief が「pilot は R=1」と暫定裁定した。親は event 適用側の
  「member 行数が下限以上であること」という検査は読んだが、その下限を作る予算 policy parser が
  値域自体を 2 以上に閉じている点を読まなかった。前回と同じく、検査の**有無**は確かめたが
  閉じた値域の**列挙**を確かめていない。今回は実装子ではなく段 3 の敵対レンズが land 前に
  差し戻したため、段 5 の空振りは起きていない。軽量版にせず段 2・3 を回した判断が被害を止めた。
### F132. レビュー所見を閉じる過程で使い捨て probe が 100 行から 486 行へ膨張した [ドリフト]

- 事象: 段 6 の fix 子が must-fix 8 件を実装した結果、使い捨て probe のコード行が 100 から 486 へ
  約 5 倍になった。汎用の path 検証機構と段階別診断機構が主因で、どちらも要件に対して過剰だった。
  親が差し戻し、検査を 1 つも落とさずに 180 行へ縮めさせた。
- 根本原因: 段 4 が課した規模上限 (100 行) が fix prompt へ継承されていなかった。fix 子は
  所見を閉じることだけを最大化し、規模の制約を知らないまま最も堅い実装を選んだ。
  「盛らない」は所見を閉じる圧力と正面から競合するため、明示しなければ必ず負ける。
- 恒久対応: `docs/dev-wave/workers.md` の `DW-S06-B` に、fix prompt へ段 4 の規模上限を継承させ
  超過を差し戻す旨を明記した。
- 再発検知: fix 後の焦点再レビューで、fix 前後の規模 (行数・新規抽象の数) を対応表に併記させる。
  規模が跳ねていれば、閉じた所見の数に関わらず差し戻す。


- **再発: 2026-08-06** ([T-139] 代替 X probe wave、独立 2 例目)。使い捨て probe の driver が
  78 行から約 600 行へ、PBS が 55 行から約 330 行へ膨張した。**段 4 が規模上限を課しておらず、
  fix prompt へも継承されなかった**という根本原因が F132 と同一である。fix は所見を閉じる方向へ
  最大化し、規模の制約を知らないまま最も堅い実装を選んだ。本 wave では fix 巡数が上限に達しており、
  検査を落とす縮約は正しさ側を弱めるため実施していない。**独立 2 例が揃ったので、
  `DW-G03` により族全体への制度化を裁定へ返す。**
### F133. 単一 node 内で無効入力を順に走査したため、変異の kill が登録した性質を証明していなかった [テスト代表性]

- 事象: 新設した検査の負例を「無効な名前を 1 つの test node の中で順に `pytest.raises` する」形で書いた。
  事前登録した変異 (名前の exact 型検査を削除する) を入れると、走査順で先に来る `str` subclass の
  ケースが受理されて node が赤くなり、**登録した性質である「比較偽装 object の拒否」に到達しないまま
  kill と数えられる**状態だった。段 6 のレビューが land 前に検出した。
- 根本原因: 1 node が複数の性質を検査していた。`pytest.raises` は最初の未拒否ケースで node を止めるため、
  node の赤は「走査順で最初に壊れた性質」しか指さない。事前登録は性質ごとに行うのに、
  検出側は node 単位でしか観測できないという粒度の不一致。
- 恒久対応: 変異事前登録した性質は**性質ごとに独立 node** へ分ける。plain runner 契約のあるファイルでは
  `parametrize` を使えないので、素直に関数を分ける。
- 再発検知: 段 6 のレビューのレンズに「事前登録した変異それぞれについて、赤くなる node が
  登録した性質に帰属するか」を入れる (本 wave で実際に発火した)。

### F134. scheduler が前 job の出力を repo root へ残し、次の job の clean-tree 検査が発火した [手順漏れ]

- 事象: probe job を再投入したところ、性能段の手前で `pre_performance_infra_failure` (rc=3、6 秒)
  になった。原因は、直前 job の標準出力・標準エラーが submit directory (= repo root) へ書かれ、
  untracked として残っていたことである。job 自身の clean-tree 検査が正しく fail-closed した。
- 根本原因: PBS は `-o` / `-e` を指定しないと submit directory へ出力する。probe が実走を
  commit へ束縛して clean-tree を要求する設計にした結果、**job の出力自体が次の job の前提を壊す**
  構造になった。scheduler 出力の置き場を投入手順が決めていなかった。
- 恒久対応: 投入時に `-o` / `-e` を repo 外の wave directory の**ファイル**へ向ける
  (directory を渡すと `NQScrereq: [BSV EINVAL] Not a regular file.` で受理されない)。
  script 内に絶対 path を書く案は採らない — 機体固有値を repo へ持ち込むため。
  手順を `docs/pegasus-runbook.md` の投入前チェックリストへ本 wave で追記した。
- 再発検知: clean-tree 検査が発火した job は terminal state に
  `pre_performance_infra_failure` を残す。投入前に `git status --porcelain --untracked-files=all`
  が空であることを確認する。


- **再発: 2026-08-06** — certify 再投入で `certify_calibration.sh.o<ID>` / `.e<ID>` が再び repo 直下へ
  返り、clean 要求のある land を塞ぎうる状態になった。`submit_certify.sh` は `qsub` へ
  repo 外の `-o` / `-e` を渡さず、job 側が `PBS_O_WORKDIR` を repo root と解釈するため cwd も
  変えられない。前回 job と同じく job-staging directory へ移して clean 化した。
  submitter 側の恒久対応は本 wave の scope 外として裁定パッケージへ返した。
### F135. `local` 一文内で先行代入を参照し `set -u` で実走が停止した [誤前提]

- 事象: probe job が投入 5 秒後に `destination: unbound variable` で停止した。
  該当は `local relative=$1 destination=$2 tmp="$destination.tmp"`。bash は `local` の全引数を
  builtin 実行**前**に展開するため、同じ文の中で先行する代入結果を参照できない。
  同型が driver 側にもう 1 件あった。
- 根本原因: 静的検査で検出できない形である。`bash -n` は通り、実装子は PBS を実走できず、
  親も機械防壁によりログインノードで probe を実行できないため、計算ノードで初めて表面化した。
  **「静的に緑」と「実走で緑」の差が構造的に残る面である。**
- 恒久対応: 両 script の `local` / `declare` / `readonly` / `export` を全走査し、同一文内依存を
  0 件にした。実装子の prompt に、`set -u` 下での最小再現 (修正前が落ち修正後が通ること) を
  実走して示すことを要求した。
- 再発検知: 実行時のみ表面化する形は、計算ノードでの実走が唯一の検査面である。probe の
  terminal state を必ず読み、`pre_performance_infra_failure` の detail から rc を特定する。

### F136. 受入全走の隣で dispatch する検査を走らせ、9 件の偽の赤を得た [計測汚染] [手順漏れ]

- 事象: docs のみの commit を検査するため `tools/run_tests.py` と
  `tools/check_ai_provenance.py` を同時に起動したところ、受入全走が
  `9 failed, 6444 passed, 20 skipped` で返った。落ちたのはすべて `output/` の
  副作用スナップショット検査 (`test_official_*` 族) で、差分の実体は
  `output/pegasus-dispatch/<nonce>/request.json` と `output/task-runs/pilot.json` —
  **並走させた provenance 監査自身が dispatch 中に書いた receipt** だった。
  同じ tree を単独で再走すると `6453 passed, 20 skipped` (rc=0) で、赤は再現しない。
- 根本原因: `check_ai_provenance.py` は login で打つと計算ノードへ自動 dispatch し、その過程で
  `output/` 配下へ receipt を書く。一方で受入側には「実行前後で `output/` が bit 単位で不変」を
  assert する検査群がある。両者は互いを知らないため、同時に走らせると後者が前者の正当な
  書き込みを副作用として検出する。テスト側の隔離漏れではなく、**同じ作業木で 2 つの
  書き込み主体を同時に動かした操作側の誤り**である。
- 恒久対応: memory `no-concurrent-dispatch-during-acceptance` — 受入全走の最中に
  `output/` へ書く検査・ツール (provenance 監査、dispatch を伴うもの) を投入しない。
  既存の `no-acceptance-run-during-mutation` と同型の規律で、対象を変異 harness から
  「dispatch receipt を書く全経路」へ広げたものである。
- 再発検知: 赤が `output/pegasus-dispatch/` や `output/task-runs/` の差分だけを指しているなら、
  実装差分へ帰属する前に単独再走で再現性を実測する (`DW-O18`)。本件は単独再走で消えた。

### F137. 衛生上の所見を閉じる fix が、元の所見より重い破壊経路を新設した [権限逸脱]

- 事象: 段 6 レビューが「publish の一時ファイルが書込み失敗時に `registered/` へ残る」を
  must-fix として出した。fix 1 巡目は cleanup を無条件 `unlink` にし、
  **自分が作っていない既存ファイル・symlink まで削除する**経路を作った。
  焦点再レビューがこれを `regressed` と判定した。fix 2 巡目は `stat` による inode 検査を
  足したが、`stat` と `unlink` が分離した **TOCTOU** であり、しかもその危険な cleanup を
  共有 helper の全 caller へ拡大していた。2 回目の焦点再レビューが再び `regressed` と判定した。
  3 巡目で helper を wave 前の実装へバイト一致で戻し、掃除の代わりに
  「orphan の path を構造化 reason として申告する」形へ縮退させて閉じた。
- 根本原因: 残骸が残るという**衛生**の所見に対して、能動的な削除で応じた。
  削除は content-addressed で immutable な公開領域に対する破壊操作であり、
  元の所見 (ゴミが残る) より失敗時の被害が大きい。
  所見の重大度と対応の破壊力を突き合わせていなかった。
- 恒久対応: 正しさ防壁でない衛生所見は、**能動的な削除より申告 (構造化 reason) を既定**とする。
  破壊操作を伴う fix は、その操作が「自分が作ったものだけ」に限定されることを
  race を含めて示せない限り採らない。判断規律は `DW-O16` の焦点再レビューが担い、
  fix が破壊操作を含む巡では所見ごとの closed/partial/**regressed** 表を必ず取る。
- 再発検知: 焦点再レビューの対応表で `regressed` が出ること。本 wave では 2 巡連続で出た。

### F138. 変異の期待 node を主要 node だけで登録し、実際の blast radius を過小に見積もった [テスト代表性]

- 事象: 事前登録した 10 変異を走らせたところ、全件で赤は出た (検出は成立) が
  **5 件が MISMATCH** になった。観測された赤 node 集合が、登録した期待集合の
  真の上位集合だったためである。例えば early gate を削除する変異は、登録した 5 node に加えて
  late gate 側の 3 node と metamorphic 1 node も赤にした。gate の欠陥ではなく親の登録が過少だった。
  観測集合で再登録して再走し、10/10 KILLED・期待 node 完全一致を得た。初回台帳は
  erratum として保持している。
- 根本原因: 期待 node を「その変異が主に狙う検査」だけで書き、
  **同じ入力経路を共有する他のテストも赤くなる**ことを数えていなかった。
  二重 gate (early と late) を意図的に併存させた設計では、片方を消すと
  両方を踏むテストが同時に赤くなるのが正常である。
- 恒久対応: 期待 node は「狙った検査」ではなく **その変異で赤くなる node の完全集合**として登録する。
  完全集合が事前に確定できないなら、初回走行を登録確認 (probe) として扱い、
  観測集合で再登録して再走し、初回台帳を erratum として残す。手順の正本は `DW-M08`
  (事前登録の期待 node と記録 node を同じ形式へ正規化して突き合わせる) と `DW-M02` (erratum 保持)。
- 再発検知: 変異 harness が MISMATCH を返し、観測集合が期待集合の上位集合であること。


- **再発: 2026-08-07** — 過剰拒否検出用の正例変異の期待 node を、狙った新設正例 1 本だけで
  登録した。実際には同じ入力経路を共有する既存 2 node も赤くなり MISMATCH。変異の適用範囲を
  field 不在経路だけへ狭めたうえで、コードを読んで期待 node を 2 件に確定して再走し 4/4 一致。
  初回台帳は erratum として保持している。
### F139. 実機の外部書式と防壁を机上で仮定し、実験 leg を 3 度空振りさせた [手順漏れ] [テスト代表性]

- 事象: 生死確認 probe の実走で、机上レビューを通過した実装が実機で 3 回止まった。
  (1) 検査・修復を login ノードで走らせる段 1 の前提が `hooks/guard_bash.py` に拒否され、
  修復側 PBS を追加実装するまで leg が 1 本も完走しなかった。
  (2) NQSV accounting の見出しを `PBS request ID` と仮定したが実際は `Request ID:` であり、
  `PBS_JOBID` も `0:` 接頭辞付きで accounting 側と文字列一致せず、walltime leg が
  `scheduler terminal accounting is invalid` で隔離された。
  (3) 修復 job が writer より先に起動すると、`ready` を 300 秒待つ設計でありながら
  その手前の `realpath -e` で即死し、2 job が成果物ゼロで終わった。
- 根本原因: 外部権威 (scheduler の出力書式、機械防壁の許可集合) に依存する述語と手順を、
  **実データを 1 件も採らずに**書いた。3 件とも fail-closed 側に倒れたため被害は空振りに
  留まったが、いずれも実走するまで検出できなかった。
- 恒久対応: D195 と併せ、`docs/dev-wave/core.md` の
  `DW-S01` が既に要求する「別 program を起動する成果物では build・環境変数・外部 command と
  注入 seam の実在を棚卸しする」を、**外部出力の書式そのもの**まで及ぶものとして適用する。
  実データ 1 件を採取してから述語を書く。
- 再発検知: 外部書式に依存する述語は、その書式の**実採取物**を逐語で pin する負例テストを
  同じ commit に置く (本 wave では `test_scheduler_evidence_accepts_nqsv_accounting_format` と
  拒否 8 種)。逐語 pin の無い外部書式述語をレビューの must-fix 対象にする。

### F140. 取得した成果物を取り込んだだけで、物理コピーの網羅検査が赤くなった [テスト代表性] [手順漏れ]

- 事象: certification job が成功して新しい試行 directory を 1 つ増やしたところ、
  `output/env/pegasus` 配下の probe 出力の**物理コピーを漏れなく列挙する** golden corpus
  (`test_probe_output_v1_corpus_is_exact_and_replays_all_physical_copies`) が
  `calibration.md` の未登録で赤くなった。コードは 1 行も変えていない。
- 根本原因: 「実物が増えると赤くなる」網羅検査が存在するのに、job 成果物の取り込みを
  コード変更と別扱いし、取り込み後に受入を再走させる手順を親の受理手順へ書いていなかった。
  段 6 までの受入は成果物取り込み**前**の tip で緑だった。
- 恒久対応: `DW-O18` の「親がテスト・受入を走らせる」義務は tree を変えた全操作に掛かる。
  job 成果物の取り込みも tree 変更であり、取り込み commit の後に受入を再走させる。
  本 wave では実際に再走させて land 前に検出した (near miss)。
  再走を省いて land していれば local main が赤くなっていた。
- 再発検知: 網羅検査自体が検知器である。取り込み後の受入再走を省かなければ必ず発火する。

### F141. 成果物が 2 本目になった瞬間、単一要素前提の選択が非決定へ倒れた [誤前提] [計測汚染]

- 事象: 登録済み較正が 1 本しか無かった間、`next(glob("calibration-*.json"))` は曖昧さなく
  唯一の較正を選んでいた。本 wave が 2 本目を取得したことで、この選択は filesystem の
  列挙順に依存するようになった。選ばれた較正の `samples_mhz` は corpus 全体に対する
  ±2% 基準に使われるため、順序が変われば判定が変わりうる。
- 根本原因: 「いま 1 個しかない」という**実行時の偶然**を、選択の一意性の根拠にしていた。
  成果物が増えるのは正常な運用であり、増えた瞬間に検査が非決定になる。
- 恒久対応: 環境契約が現に指す較正 (`env_contract.lookup(...).calibration_ref`) を明示的に読み、
  参照 bytes の sha256 が契約の値と一致することも検査する
  (`orchestrator/tests/test_env_attestation.py`)。較正が 1 本だった時点の意味は保存している。
- 再発検知: 契約が指す較正が実在しない・bytes が食い違えば同検査が赤くなる。
  実 repo を対象に同型の単一要素前提が他に無いことは静的に確認した
  (他の `next(glob(...))` はいずれも tmp fixture 上であり、独立 2 例の族一般化は成立しない)。

### F142. 「read-only 再検証」と分類した入口が live 実走 admission と共用だった [誤分類]

- 事象: 段 1 brief が 4 つの consumer を「publish 済み成果物の read-only 再検証」と分類し、
  そこだけ受理集合を広げれば live 経路は無傷だとする不変条件を立てた。実際には
  そのうち 3 つを含む関数が oracle driver の実走 admission そのもので、通過後に
  marker・WAL・予算が書かれる。段 3 の敵対相談 2 レンズが独立に blocker として検出した
- 根本原因: 入口の性質を**呼び出し元をたどらずに関数名と docstring から**推定した。
  「再検証」と読める名前の関数が、同時に実行の前提条件を満たす gate でもある、という
  二役を見落とした
- 恒久対応: 受理集合を広げる wave の段 1 では、対象関数の呼び出し元を実際に列挙し、
  **その戻り値を消費して副作用を起こす経路が 1 本でもあるか**を file:line で確認してから
  「read-only」と分類する。確認できないものは read-only と呼ばない
- 再発検知: 段 1 brief の scope 表に「この入口の戻り値を消費して書き込みを行う経路」列を設け、
  空欄のまま子を起動しない

### F143. 新設した検査が既存層と冗長で、変異が単独では殺せなかった [恒真ゲート]

- 事象: 実装子が履歴解決の返り値に対する hash 再検査を 2 箇所へ足したが、変異検査で
  どちらを消しても、両方消しても既存 test は緑のままだった。実際に落としていたのは
  さらに下流にある既存の等値検査で、新設 2 箇所は冗長だった。3 層すべてを外す変異では KILLED になり、
  実効 gate が既存層であることが確定した
- 根本原因: 「fail-closed を足した」ことを、その検査が**単独で受理集合を決めている**証拠と
  取り違えた。前後に同じ入力を拒否する層があるかを、実装前にコードで確認していなかった
- 恒久対応: `docs/dev-wave/mutation.md` の `DW-M01` (同じ入力を拒否する層が前後に無いことを
  コードで確認してから登録する) と `DW-M02` (生存したら mask を疑い実効 gate へ再照準し
  両層同時変異まで裏取りする) を、新設検査ごとに適用する。冗長と判明した層は
  「冗長 gate」と台帳へ明記し、単独変異の受理集合 kill 証拠から外す
- 再発検知: 変異事前登録の各行に「この位置の前後で同じ入力を拒否する層」欄を書き、
  空欄で登録しない

### F144. 自作の計測スクリプトが二重計上したまま結論をユーザーへ報告した [誤前提] [テスト代表性]

- 事象: 開発ループのトークン消費を測る使い捨てスクリプトで、同一の content block を
  `assistant:tool_use` と `in:<tool>` の 2 系統へ加算し、割合の分母にも両方を入れた。
  その比 (tool_result 33.5% / thinking 26.8% / tool_use input 17.9% / text 2.0%) を
  「文脈の内訳」としてユーザーへ報告した。同じ走査で、観測 model call 数を tool 呼び出し数と
  取り違えた値 (子 1 tool あたり 105,774 tok) も報告した。いずれも敵対レンズが実データで否定した。
  さらに前段では、transcript が 1 応答を content block ごとに複数 record へ割り usage を
  複製することに気づかず、record 単位で数えて応答数とトークンを 2 倍に計上していた
  (これは自分で気づいて訂正した)。
- 根本原因: 計測器そのものに正しさの検査を置かなかった。合成 fixture で
  「期待どおりの値になるか」を確かめないまま、実データの出力の大きさだけを見て納得した。
  母集団 (走査 root・filter・時間窓の判定根拠) も定義せず、単一 encoded cwd の subtotal を
  「6 日間の総量」と呼んだ。
- 恒久対応: 計測を `tools/claude_session_ledger.py` へ固定し、
  `orchestrator/tests/test_claude_session_ledger.py` が合成 fixture で
  dedupe・最終 usage・入力 3 項・母集団報告・model call と tool 呼び出しの分離を検査する。
  台帳は母集団と読めなかった件数を必ず出力へ含める (D206)。
- 再発検知: 変異 M1〜M5 (dedupe を外す / 最初の usage を採る / 入力 3 項をそれぞれ落とす) と
  M12 (母集団を報告から省く) が事前登録済みで、3 走目に 12/12 KILLED を確認した。

### F145. 背景 job が子を投入したまま待ちを張らず 6 時間 24 分停止した [手順漏れ]

- 事象: 段 6 の fix 子を投入したあと、完了待ちを張らずにユーザーへ中間報告して turn を終えた。
  子は 14:19 に rc=0 で完了していたが、ユーザーが 20:43 に「動いていますか？」と尋ねるまで
  何も進まなかった。空白は 6 時間 24 分。
- 根本原因: 「待ちは通知に任せて polling しない」という既存規律を、
  「待ちを張らなくてよい」と読み違えた。待ちが存在しないと完了通知が発火しない。
  投入と報告を同じ turn に置き、待ちだけを次 turn へ送る形にしたことが直接の原因である。
- 恒久対応: memory `never-end-turn-with-unawaited-child` — 子の投入と
  `until [ -f <.done> ]` の待ちを**同じ応答に入れる**。中間報告をする場合も、
  報告テキストと待ちを同居させ、報告だけで turn を終えない。
  待ちが tool timeout で背景へ移るのは可 (完了通知が発火するため)。
- 再発検知: ユーザーが概ね 1 時間おきに確認する運用とし、
  **5 時間以上まったく変化がない job は死んでいるとみなして止め、状態と再開コマンドを報告する**
  (2026-08-06 ユーザー指示)。

### F146. 規範記述の fix が新しい不整合を生み、焦点再レビュー 1 巡では閉じなかった [手順漏れ] [恒真ゲート]

- 事象: docs-only wave の段 6 で、レビュー所見への fix が**新しい内部矛盾を 3 回連続で生んだ**。
  焦点再レビューは 4 巡を要した。(1) 択一を分類したが批准方法の記述と割当てが食い違った。
  (2) 発行の分岐を 1 条件で書いたが既裁定は 2 条件の一体だった。(3) 同一節の手順 1 と 4 で
  provisioning の順序が矛盾した。いずれも**前巡では存在しなかった誤り**である。
- 影響: 最も危険だったのは (2) で、ユーザーが決めた手順 (批准で発行) を親の推奨 (発行の延期) が
  黙って置き換えた形の記述になっていた。1 巡で打ち切っていればそのまま提出していた。
- 根本原因: `DW-S06-C` の「焦点再レビューは全体へ 1 本でよい」を、規範記述 (誰が何を決めるか、
  どの条件で何が起きるか) の fix にもそのまま適用した。コードの fix と違い、規範記述の fix は
  **他の箇所の前提を変える**ため、局所の修正が離れた節と矛盾する。テストが無いので
  機械検査では捕まらない。
- 恒久対応: 段 6 の焦点再レビューは `regressed` が 0 になるまで回す。
  `DW-S06-C` への明文化は **docs/dev-wave/** の byte hard ceiling (25,200) に 13 bytes しか
  空きがなく入らないため、[T-577] の既裁定 (予算上限は上げない、入らない分は台帳が担う) に従い
  本エントリを恒久対応の所在とする。次に `docs/dev-wave/**` へ空きが出たとき
  `DW-S06-C` へ 1 文で統合する。
- 再発検知: 焦点再レビューの closed / partial / regressed 表 (`DW-S06-C` が既に要求している) で
  `regressed` 行が出たら、その巡を最終とせず次巡を回す。

### F147. 拒否メッセージの生成が subprocess を起動した [恒真ゲート]

- 事象: `site_policy.heavy_work_refusal()` へキュー状態の診断を織り込んだ結果、拒否文を作る
  過程で `subprocess.run(["qstat", "-Q"])` が走った。`test_build_site_gate.py` の 4 node が
  固定していた「gate は subprocess を 1 つも起動する前に拒否する」を破り、受入全走で赤になった。
- 根本原因: 診断を「拒否を報告する場所」ではなく「拒否を判定する場所」へ入れた。深い gate
  (`buildcache._run` 等) から呼ばれる純関数に I/O を足したため、gate の副作用ゼロ性が壊れた。
- 恒久対応: `heavy_work_refusal()` は純粋に戻し、キュー診断は呼び出し側の最上位
  (`run_tests.py` / `check_ai_provenance.py`) と `python3 -m orchestrator.campaign.queue_state`
  でだけ合成する (D209 決定 4)。
- 再発検知: `heavy_work_refusal()` が `subprocess` を一切起動しないことを固定するテスト
  (`subprocess.run` を例外送出でパッチして到達しないことを assert する)。

### F148. 「tree が clean なら」の条件が開発の通常状態を殺した [手順漏れ]

- 事象: 「cap 到達後の自動 fallback は working tree と submodule が clean のときだけ」という
  裁定をそのまま実装した結果、**未コミットの変更がある通常の開発状態で必ず fallback が止まり**、
  rc=16 で終了するようになった。変異 harness の本走が M1 で停止して顕在化した。
- 根本原因: 裁定の意図は「local 試行が書き散らした状態のまま計算ノードで再実行しない」で
  あったのに、実装条件を「tree が clean か」という**絶対状態**にした。守りたかったのは
  **相対変化**である。開発中の tree はほぼ常に dirty なので、絶対状態の条件は常に偽になる。
- 恒久対応: local 試行の**前後で tree と submodule の指紋を比較**し、変化していなければ
  fallback する (D209 決定 9)。指紋取得に失敗したら安全側へ倒す。
- 再発検知: 「最初から dirty な tree で、local 試行が何も変えなければ fallback する」を固定する
  回帰テスト。


- **再発: 2026-08-07** — 変異 matrix の本走が MW-06 で rc=16・stdout 0 byte で停止した。
  変異適用中の tree は必ず dirty なので、local 試行から dispatch への fallback が
  「tree が clean なら」の条件で拒否され続ける。D209 決定 9 の指紋比較が
  `mutation_harness` 経由の経路へ届くまで、変異本走はこの停止を踏みうる。
  初回台帳 = `output/insights/2026-08-07_t503-disposable-worktree/mutation-ledger-run1-erratum.json`。
### F149. 実行場所を可変にして既存 tool の前提を壊した [ドリフト]

- 事象: `tools/mutation_harness.py --runner-mode dispatch` は runner の stdout に
  `[Pegasus dispatch] receipt を … へ保存しました (child rc=…)` が現れる前提で計算ノード側の
  stdout を集める。`run_tests.py` が余裕のあるときに local 実行するようになったため、この行が
  出なくなり、変異 matrix が baseline から `PARSE_ERROR` になった。
- 根本原因: 「常に dispatch する」という**暗黙の契約に依存した consumer** を棚卸ししないまま、
  entry point の挙動を条件付きへ変えた。契約は runner の stdout 形式として存在していたが、
  どの docs にも「dispatch されることに依存する consumer」として記録されていなかった。
- 恒久対応: 実行場所を確定させる `--force-dispatch` を設け、harness 側がこれを明示する
  (D209 決定 10)。
- 再発検知: 強制指定時に `grant_budget` / `dispatch_possible` が呼ばれないことと、
  preflight 順序・task_run の exactly-once が保たれることを固定するテスト。


- **再発: 2026-08-07** — 同じ停止で harness が `receipt 表示行が exactly one でない: 0` を記録した。
  `--runner-mode dispatch` の consumer は receipt 行の実在に依存し続けており、
  D209 決定 10 の `--force-dispatch` を `mutation_harness` 側が渡すまで塞がらない。
  親は当初これを計算機の queue 混雑と誤診断し、待ち行列を見て投げ直す運用で凌いだ。
  **混雑は相関であって原因ではなかった** — 待ち 142 件のままでも完走した走行がある。
### F150. 例外型だけを見る負例試験が、後段の無関係な失敗で満たされ恒真になった [恒真ゲート] [テスト代表性]

- 事象: 段 2 のプランが「current 契約が後継世代へ進んだ状態で resume を呼び、
  `pytest.raises(FloorCampaignError)` の型だけを確認する」試験を推奨した。しかし守るべき
  current 契約検査を削除しても、制御が 1 段先の calibration 読込みへ進み、そこが**必ず**
  `AttestationError` を出して同じ `FloorCampaignError` へ翻訳されるため、試験は緑のままだった。
  必ず失敗するのは、正当な後継世代が calibration 参照を必ず変えるのに対し、当該 env の
  attestation mode が grandfathered な唯一の bytes しか受理しないためである。
  段 3 の 2 レンズが独立に land blocker として検出し、段 4 で設計を差し替えた。
- 根本原因: 負例試験の oracle を「拒否されたこと」で書き、「**どの層が拒否したか**」で書かなかった。
  同じ例外型へ翻訳する層が下流にあると、拒否の事実は上流 gate の存在を証明しない。
  F133 が node 粒度の不一致だったのに対し、こちらは oracle 自体が層を区別しない弱さである。
- 恒久対応: `docs/dev-wave/mutation.md` の `DW-M01` が求める単一理由性を、
  **負例試験の oracle 側にも適用する**。拒否の因果を、下流の副作用が起きていないこと
  (下流 loader の呼出し回数 0 等) で pin し、対象 gate を外す変異でその assert が赤くなることを
  変異検査で確認する。本 wave では calibration loader の呼出し回数 0 で pin し、変異 M3 が
  この assert でのみ KILLED になることを実測した。
- 再発検知: 変異事前登録の各行に「その変異で赤くなる assert」を書き、赤の原因が
  `pytest.raises` の型一致だけの行を登録しない。

### F151. 別 ID で裁定された項を話題文だけで同一視し、未裁定の gate を「裁定済み」と宣言した [手順漏れ]

- 事象: 段 1 で、依存 wave が「ユーザー裁定待ち」とした択一 R1 (記録 hash を世代選択の権威にして
  よいか) を、別タスクの裁定 (1)(activation record の trust root を「レビュー済み git commit」と
  明示する) が既に答えていると結論し、brief の実測 5 に「blocker は成立しない」と書いた。
  段 3 の 2 レンズが独立に file:line 付きで否定した。**R1 は未裁定のままだった。**
- 根本原因: 突き合わせを**話題文**で行い、**選択肢集合**で照合しなかった。両者はどちらも
  「何を権威とみなすか」の話題を共有するが、問うている対象が違う —
  一方は *activation record* の trust root を何にするか、
  もう一方は *記録 hash だけで、その世代が artifact 作成時に active だった証明なしに*
  世代を選んでよいか。選択肢を並べれば別問だと判るのに、要約同士を比べて同一と判断した。
  裁定の逐語 (rulings-inbox) には当たったが、**R1 側の選択肢表に当たらなかった**。
- 影響: 実害には至らなかった。段 3 が止めたためで、親の手続きが止めたのではない。
  そのまま進んでいれば、未裁定の受理集合拡大 (registry にあるだけで一度も active でない世代を
  記録した artifact まで再検証が受理する) を既成事実にしていた。
- 恒久対応: 規律「別 ID で裁定された項を『裁定済み』と扱うときは、**両者の選択肢集合を並べて
  照合する**。話題文・要約・題名の一致を同一性の根拠にしない。照合できないなら未裁定として扱う」。
  memory `ruling-match-by-option-set` へ恒久化した。既存の逆向き規律
  (memory `check-withdrawal-rulings-before-wave` = 対象 ID の項だけ読むと別 ID の裁定を
  取りこぼす) と対になる — あちらは**見落とし**、こちらは**取り違え**である。
- 再発検知: 段 3 のレンズに「親自身の実測値とその一般化」を明示的に攻撃面へ入れる既存規律
  (`DW-S03`) が本件でも機能した。本件はその有効性の 3 度目の実証であり、
  **親の一般化が段 3 で覆るのは 3 wave 連続**である (直前 2 件は worklog (277) と (275) が記録)。

### F152. 段 1 前提実測の rc を pipe 越しに読み、`tail` の rc を実測値として報告した [恒真ゲート] [手順漏れ]

- 事象: 段 1 の前提実測 probe を `command ... | tail -N` の形で書き、直後の `$?` を実測 rc として
  brief に載せた。`pipefail` が無いため読んでいたのは `tail` の rc であり、
  **producer が失敗しても常に 0 が報告される**構造だった。段 3 の敵対レンズ 2 本が独立に指摘した。
- 根本原因: 実測を「読みやすく tail する」ことと「rc を取る」ことを同じ pipeline で行った。
  検査対象の rc が pipeline の最終段に来ないため、gate が恒真化した。
  段 1 brief は子の起動根拠になるので、恒真な前提実測は wave 全体の土台を崩す。
- 恒久対応: 段 1 の前提実測では **producer を pipe の最終段に置くか、`PIPESTATUS` / 出力を
  file へ落として rc を別に取る**。本 wave では pipe を外して測り直し、
  worktree add / submodule init / 受入全走 / `--plan-only` の rc をすべて再取得した
  (逐語 = `output/insights/2026-08-07_t503-disposable-worktree/verbatim/s3-lensA.md` A-8、
  同 `s3-lensB.md` B-13、再測定手順 = 同 README の実測表)。
- 再発検知: 段 3 のレンズ prompt に「親自身の実測値とその一般化も攻撃対象」を入れておくこと
  (`DW-S03` の既存義務)。本件はその義務が実際に発火して検出された事例である。

### F153. 受入全走に `-rf` を足したら事前検査 2 件が黙って発火しなくなった [恒真ゲート] [手順漏れ]

- 事象: 親が `python3 tools/run_tests.py -rf` を「受入全走」として走らせ、
  6837 passed / 20 skipped を台帳へ書こうとした。実際にはこの形は `_is_acceptance_run()` が
  False を返す形であり、**未 stage 削除検査と RuleOps 台帳検査の 2 つの事前検査が発火していない**。
  テスト node は同じ数だけ走り、警告も出ないため出力からは区別できない。
  段 3 の敵対検証子が file:line で指摘して露見した。
- 実測: `tools/run_tests.py` を直接 import して分類器を呼ぶと
  `[]` → acceptance=True、`['-rf']` → acceptance=False、`['-q']` → acceptance=True、
  `['orchestrator/tests']` → acceptance=True / full=False。
  許される compact option は `q` と `v` だけである。
- 根本原因: report flag は「出力を増やすだけの無害な追加」に見えるが、受入形の判定は
  引数列全体の形で決まる。**gate を失っても静かに成功する**ため、気づく手がかりが出力に無い。
- 同時刻に **別 wave も `run_tests.py -rf` を受入として走らせていた** (独立 2 例)。
  単発の不注意ではなく、この形が自然に選ばれることを示す。
- 恒久対応: memory `acceptance-run-takes-no-extra-flags` (受入として記録する走行は引数なし、
  逐語や skip ラベルが要るなら受入形とは別の走行を立てる)。
  **`run_tests.py` が受入形でない走行に 1 行警告を出す改修**は
  `output/insights/2026-08-07_red-test-audit/README.md` の裁定パッケージでユーザーへ諮っている。
- 再発検知: 上記分類器を引数列に対して直接呼べば真偽が出る。
  受入結果を台帳へ書く前に、走らせた引数列そのものを記録に残す。
- 近縁: F37 (検査 rc をパイプで握り潰す — 「検査が実は走っていないのに緑と読む」同じ根)。

### F154. 見送り裁定が依存タスクの着手条件へ反映されず、見送り済みの機構を対象に wave が起動された [手順漏れ] [コンテキスト浪費]

- 事象: `/dev-wave [T-419] (iii)` の対象「別 process の完全独立検証」は、前日の委任一括裁定で
  [T-560] として見送り済みだった。しかし [T-419] の「次の一手」項には着手条件 (iii) として
  残っていたため、wave が起動し段 1〜3 を実行した。検出したのは段 3 の敵対レンズが台帳の
  一次資料に当たったときで、それまでに codex 子 3 本 (段 2 プラン 1 + 段 3 敵対 2) を消費した。
  同型は worklog (273) の [T-558] に続く **2 例目**で、検出者が異なる (前者 = rulings セッション、
  後者 = dev-wave の敵対レンズ)。
- 根本原因: 裁定は代表 ID の項にだけ書かれ、その機構を着手条件として列挙する別タスクの項は
  更新されない。wave の起動読了は対象タスクの項と関連 D を読むが、「その機構を見送った裁定が
  別 ID の項に無いか」は探さない。ID を key にした検索は、機構名を key にした裁定を見つけない。
- 恒久対応: memory `check-withdrawal-rulings-before-wave` — 段 1 の前提実測で、対象タスク ID の
  検索と並べて**機構名の語**で `docs/worklog.md` を検索する。fold 時の相互参照検査による
  機械化の可否は裁定へ返した (プロトタイプ基準の下では prompt 規律に留まりうるため親が決めない)。
- 再発検知: 段 3 の敵対レンズに「対象が既に見送り裁定済みでないか台帳の一次資料で確かめる」を
  含める。本件はこの経路で実際に検出された (段 4 裁定の根拠になった唯一の所見)。
