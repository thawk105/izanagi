# Izanagi 作業ログ (worklog)

セッションごとの進捗を時系列で記録する。git 履歴や各正本に入らない協議・異常・持ち越しを束ねる
「作業の索引」であり、commit 内容の再説明はしない。役割分担:

- 設計判断と却下案 → `docs/decisions.md`
- CCBench の構造的事実 → `docs/ccbench-anatomy.md`
- CCBench のバグ等の知見 → `output/insights/`
- タスク分解 → `docs/phaseN.md`
- **このファイル = それらを束ねる日誌 (各セッションの索引)**

## 新規エントリの書式 (D35)

過去エントリは凍結し、次の規約は新規エントリに適用する。

- 本文化するのは、ユーザー承認・協議の決着、棄却 finding (refuted)、未コミット事象・セッション異常と
  救出、エージェント工数、人間判断待ち・持ち越し、次の一手など **git に入り得ない情報だけ**
- commit は「hash + 件名 (+ 位置づけ 1 行)」まで。連続群は「先頭..末尾 (N 本)」で表し、内容を再掲しない
- 監査の finding 全文と裁定は insight / audit JSON に凍結する。worklog はレンズ数、real/refuted 数、
  最重要 1〜3 件、一次資料ポインタの 10〜15 行に留める
- 論文素材になる段落は行頭に「素材:」を付ける。持ち越しは逐語再掲せず「変わらず (前エントリ参照)」
  とする
- docs(worklog) だけの commit は prose の body を付けず、件名 + 必須 trailer だけにする

## ローテーション

Phase 境界または現行ファイルの肥大時 (`tools/check_docs.py` の閾値超過が
知らせる) に、過去分を `docs/archive/worklog-<範囲>.md` へ**移動**し、現行ファイルを軽く保つ
(ブート時に読むのは末尾エントリのみ、の運用を軽く保つため。2026-07-05 導入、D35)。
アーカイブは凍結 (訂正注記のみ追記可)。既存アーカイブの一覧は `docs/archive/README.md`。

---
## 2026-07-17 (1) — wave 2 前半: floor protocol 凍結案パッケージ + env-neutral floor driver (裁定待ち)

worklog (12) 次の一手 1 の前半。プラン骨子 → codex gpt-5.6-sol reasoning=max 敵対相談 4 本
(C-α 統計 / C-β budget・運用 / C-γ driver 設計 / C-δ 世代・承認束縛。所見 47 件 must-fix 大半、
逐語 = output/insights/2026-07-16_s8b-floor-protocol-consultations.md) → 親裁定 → Claude workflow
8 agents (起草・実装 = opus、テスト・修正 = sonnet、fable 子なし) + 親再投げ 2 (sonnet)。
計測なし。**何も発効していない** (パッケージは全項ユーザー裁定待ち)。

- 裁定案 = output/insights/2026-07-16_s8b-floor-protocol-package.md (F1〜F7): 12 セル per-pair
  floor (pair-contrast 絶対値式 formula v1 = u_noise/delta/wired 下限の max)、seed 均衡置換 +
  2 block、予測封印 → floor → 機械充填 → 承認 → oracle の順序凍結、budget 三層 namespace +
  oracle verify ×96 (~11.6h) の正直計上、世代 transition table (v1→v2 / gN→gN+1)、承認束縛 =
  approval record + `AI-Agent: none` 逐語 + active pointer、v2 検証 = git blob 照合 + 歴史的
  未知性 + launch certificate。数値はすべて案 (n=8 / reps=5 / gap 1800s / wired 3% /
  scale ±10% / retry 通算 2)
- 相談の主要な設計転換 (real 採用): CV×stock 変換は on 側分散を覆わない (B1) / 無関係セルの
  veto (C1) / 固定巡回の周期共鳴 (D1) / α 未保証の逐語限定 (A1) / floor データは oracle 相当
  情報を露出 → 予測封印を前置 (H2/B11') / v1 freeze は design・generator の hash drift で現在
  verify 不合格 — 実測確認、driver は bytes-pin 束縛へ / 「trailer なし = 人間」は provenance
  規約と逆 (D2')。縮小 = env contract 抽象 (裁定 6 工数欄どおり Pegasus 差分に据え置き)・rep
  単位 runner API・共有 probe fail-open 是正 (v2 前提条件へ登録)
- 実装 (env-neutral): s8b_floor_stats.py (formula v1 純関数 + verify_floor_artifact 独立再計算)
  / s8b_floor_campaign.py (pilot のみ。official mode は承認束縛の §8 裁定まで一律拒否。strict
  protocol + bytes-pin freeze + seed schedule + 臨界区間 probe + append journal + create-only +
  forward-only resume + binary 再ハッシュ) / テスト 45 本 (golden pin・改竄検出・mutation 殺し)。
  orchestrator 全体 925 passed (既存 11 failed は ccbench submodule 未 checkout の本マシン環境
  要因 — 増減なし)
- レビュー: レーン内敵対 (opus×2) must-fix 0 / should 2 → 反映 (G6' の台帳脱落、blocks=2 の
  構造検査漏れ)。親の独立検算 = formula 実装と手計算の一致・縮退 fail-closed を確認。親再投げ
  で resume binary 再ハッシュ (文書 claim と実装の F14 齟齬)・golden schedule pin・retry 通算
  意味論の逐語化を閉鎖。C3 (sonnet) が blocks!=2 検査漏れと retry 意味論の曖昧さを実装前に発見
- 工数: codex 4 (reasoning=max) + workflow 8 (opus 5 / sonnet 3、951k tokens) + 単発 sonnet 2

### 次の一手
1. パッケージ F1〜F7 + 数値案 + env_tag のユーザー裁定 (チェックリストは同文書末尾)
2. 裁定後: protocol JSON 凍結 → selector 予測封印 → floor 実測 (実行計画テンプレート) →
   freeze v2 再凍結 + strict v2 verifier 本体
3. v2 前提条件 (oracle 側 binary hash 照合 / 共有 probe fail-open 是正 / manifest per-pair 追随 /
   共有 materialization 抽出) は再凍結 wave で実装 (一覧 = パッケージ実装状況節)

## 2026-07-17 (2) — リポジトリ棚卸し・リファインメント (課題 1〜5、計測なし)

ユーザー依頼 5 課題 (棚卸し掃除 → 明瞭化 + glossary 圧縮 → docs 外の実態検査 → docs 反映 →
docs リファイン)。標準ループ (プラン → codex 敵対相談 → workflow → 親検算 → 再投げ) で実施。
相談 2 本・独立最終レビューの逐語と裁定、棚卸し・監査の要約 =
output/insights/2026-07-17_repo-refinement-consultations.md。

- 課題 1 裁定: 全 835 tracked ファイルの棚卸し (9 レーン) = **削除対象ゼロ**。全ファイルが参照・
  凍結契約・parity 検査・試行台帳のいずれかで保護されており、参照ゼロの残骸なし。codex 相談 2 本
  22 所見 = 全 real (誤削除リスクの事前攻撃、実害未然)
- 課題 3 監査: docs 外 243 ファイル全数 (opus 9 レーン) = 20 所見 (must-fix 3)、独立最終レビュー
  (codex、branch 全 diff) = 8 所見 (must-fix 3)。nit 1 件 (d98d9fe message の src/ 表現) を実害なし
  と裁定した以外は全て修正。F9 恒真 (check_docs 対象不在 skip) は failures.md へ再発追記
- 持ち越し (**s8b 裁定の判断材料に追加**): (a) s8b_floor_campaign の official 拒否が CLI 限定で
  run_campaign() 直呼びは fail-open (裁定待ちパッケージのため未修正・要裁定)、(b) 8b-descriptor
  §7-8 見出しの stale (SHA 凍結閉包のため未修正)。v1 freeze の hash drift 3 件は前エントリ既知の
  状態と一致することを byte 照合で確認 (本セッション由来の凍結違反ゼロ)
- テスト: 11 failed/925 passed/12 skipped → **1 failed/940 passed/22 skipped** (新テスト 15 本。
  環境依存 10 件は「submodule 未初期化のみ」の精密ガードで SKIP 化、残 1 failed = D56 意図的 gate)
- 環境注記: 計測機ではない本機に numpy 2.2.6 を導入 (repo requirements 不変)
- commit: 86d3076..21116bc (7 本)
- 工数: workflow 6 本 (52 agents、~3.7M tokens、opus/sonnet)、codex 3 本 (gpt-5.6-sol
  reasoning=max)、単発 opus 1 (phase3 突合 = 齟齬ゼロ)

### 次の一手
1. 本ブランチ (worktree-repo-refinement) の PR レビューと merge 判断 (ユーザー)
2. s8b: パッケージ F1〜F7 のユーザー裁定 (変わらず — 前エントリ参照。上記持ち越し 2 件を材料に追加)

## 2026-07-17 (3) — docs 衛生リファインメント wave (worklog ローテ + coder-spec バナー + 地図修正)

凍結・保護規約の相談から派生したユーザー依頼 (棚卸しで挙がった 4 候補の実施)。3 件実施 + 1 件を
凍結により見送り。計測なし。敵対検証 workflow 4 レンズ (byte-exact / バナー事実性 / 凍結安全性 /
参照整合) = all pass、must-fix 0。

- 見送り (裁定): 8b-descriptor §1 内の stale 引用「(8b 未着手) workload 次元のループ入力化」の修正
  — `output/s8b-freeze/holdout_freeze.json` の SHA pin 対象のため編集せず、(2) 持ち越し (b) と同枠で
  freeze v2 再凍結時の修正材料に追加
- 検証の副次所見 (nit 2、本 wave 由来ゼロ): 8b-descriptor の現 hash は §9 記録コミットにより pin と
  既に乖離 ((1)/(2) の既知 drift と整合、凍結違反の新規発生なし)。地図の従属文書行は
  main-experiment を拾わない (個別 entry があるため実害なし)
- commit: 2c1e0d2 (worklog ローテ 07-14〜07-16 分、境界 = 07-17 (1) 以降を現行保持) / 9b744d4
  (coder-spec §3/§5/§8 バナー + 地図 glob に phase3-8b-*.md 追加)
- 工数: 調査 Explore 2 + 敵対検証 workflow 1 本 (opus 4、~206k tokens)

### 次の一手
1. 本ブランチ (worktree-docs-refinement-wave) の push → PR → merge 判断 (ユーザー実施 —
   Pegasus は AI ツールから push しない運用)
2. s8b: パッケージ F1〜F7 のユーザー裁定 (変わらず — (1) 参照。8b-descriptor の stale 引用を
   再凍結時の修正材料に追加)

## 2026-07-17 (4) — roadmap 明瞭化リファインメント (協議改訂) + CLAUDE.md 提案台帳 (計測なし)

セッション冒頭のユーザー要望 (「roadmap.md と CLAUDE.md の分かりにくい部分を分かりやすく」、
前夜 wave が裁定 A4 でスコープ外化した宿題) の実施。roadmap は協議改訂 (in-place・版凍結なし)。

- commit: 9997d61 (roadmap layout-only 19 hunk)、5ab330a (レビュー修復 4 件)、ebdafb6 (逐語凍結)
- 協議決着: 意味保存を正しさゲートとする三分類 (byte-frozen / semantic-lock / normative-care) と
  決定的 checker (変異 self-test 12 種で恒真性を排除) を敵対相談 3 本 (codex、must-fix 30) から確立
- 盲検変異回帰: checker 不可視の意味反転 7 種を R1 opus×2 が全捕捉・偽陽性ゼロ — レビュー系の
  弁別力を実証してから本番レビューに入る手順が機能した
- 最重要 finding: R1 (語レベル双方向含意) が preserved と判定した構造スコープ型ドリフト 3 件
  (継続段落の同格化・実績括弧のスコープ狭窄・共有述語の分断) を codex 第二系統が検出 —
  異製品レンズは冗長でなく補完 (一次資料: output/insights/2026-07-17_roadmap-claudemd-clarity-consultations.md)
- CLAUDE.md は 1 byte も変更していない: 起草レーンが「byte/行予算内の編集は不可能」と正直に判断し
  全 hunk を提案化。絶対規律 (憲法) 帯・真の曖昧性を含む 11 案は未裁定提案台帳
  output/insights/2026-07-17_clarity-proposals-unadjudicated.md へ (全件 default: do-not-apply)
- 工数: codex 相談 3 + survey 6 + draft 2 + 回帰 2 + 本番レビュー 4 + codex レビュー 2、
  subagent 計 ~1.5M tokens
- 棄却 finding: survey 66 所見中 11 件を親裁定で却下 (Markdown 段落内改行の無効性等)、
  R1-b の R-73 反論は codex 構造所見を優先して棄却

- 追記 (同日): 「CLAUDE.md 総 byte 純増ゼロ」は相談 B 由来の保守側デフォルトでありユーザー指示では
  なかったと指摘を受け、ユーザー裁定で予算を緩和。提案 C-32/C-139/C-150 (語追加ゼロのマーカー付与
  3 件) を採用・適用。残る未裁定は 8 案

- 追記 2 (同日): 残 8 案もユーザー裁定完了 (「推奨で変更していい」)。採用 4 (P-19/P-118/P-209/P-155)
  + P-100 再起草版 (協議改訂の 1 文を CLAUDE.md 三層可変性へ追記)、見送り 3 (P-89/P-93/P-3 —
  絶対規律帯は不変のまま)。台帳に pending なし

### 次の一手
1. 本ブランチ分の push (ユーザー実施 — Pegasus は AI から push しない運用)
2. 本ブランチのローカル main 取り込み後の push (ユーザー実施 — Pegasus は AI から push しない運用)
3. s8b: パッケージ F1〜F7 のユーザー裁定 (変わらず — (1) 参照)

## 2026-07-17 (5) — s8b v2 前提条件の裁定非依存サブセット実装 (部分基盤、計測なし)

worklog (1)〜(4) の次の一手が全てユーザー待ち (push / F1〜F7 裁定) のため、パッケージ「v2 前提条件」の
裁定非依存部分を標準ループ (プラン → codex gpt-5.6-sol reasoning=max 敵対相談 4 本 36 所見・全
「修正後に進めよ」 → 親裁定 → Claude workflow 20 agents (実装 opus / commit sonnet / fable 子なし、
レーン内敵対レビュー opus×2 + 修正 + 再レビュー) → 親検算) で実装。逐語・裁定表・確定プラン =
`output/insights/2026-07-17_s8b-v2-prereqs-consultations.md`。**「3/6 完了」とは数えない (D-1)** —
L1 は生産基盤のみ (oracle 消費配線なし = 照合は未保証)、L3 は G6' 部分準備。

- commit: 2646e73 から本エントリ分まで 8 本 (逐語凍結 / L1 full-sha256 基盤 + 未配線 gate / L2 probe
  fail-closed / L3 s8b_materialization 部分抽出 / L5 結線テスト + 台帳完了化 / nit 後始末 / allowlist / docs)
- セッション異常と救出 2 件: (a) workflow 産 4 commit で AI-Agent trailer が Co-Authored-By と別段落に
  なり git trailer 非認識 (provenance 監査 4 違反) → filter-branch --msg-filter で未 push 範囲を修復
  (hash 変更)。(b) L3 新規テストが plain-runner メタテスト赤 (レーンの対象テスト集合の外) → 親フル
  スイート検算で検出し pytest 専用 allowlist へ
- 挙動拡大の裁定記録 (スコープ外だが採用): screening_driver が identity-error も再評価するようになった
  (`model.RETRYABLE_ABORT_REASONS` で loop の D25 契約に統一 — D25 繰延の identity-error poison の
  screening 側部分解消。番人テスト + verifier-red の negative control で固定)。S2 pass 先頭の verdict
  消去 (aborted+serializable 矛盾) は既存バグの是正 (B-4)
- **ユーザー裁定材料に追加 (B-2):** 共有 probe の自己子孫除外は「生きた自分の子 ycsb」を競合から外す。
  freeze-v2-design-material の記載 (子孫除外を明記) と衝突するため実装では変えていない — admission を
  自 PID のみ除外へ狭めるかは裁定待ち
- v2 前提条件の正直な残 (D-1/D-2): oracle 消費配線 (F5 裁定後) / strict v2 verifier 本体 / manifest
  per-pair 追随 / bench_max_rounds=1 凍結 / **G5' env contract (パッケージ一覧から脱落していた第 7 項)** /
  floor の共有 probe 切替。G6' 残課題 6 件 (PreparedCell 所有移動・verifier 三重実装統合・trace-disabled
  build 共有・binding 検証 adapter・VerifiedFreeze/NUMACTL 中立化・v2 での closed source bundle pin —
  新モジュールは現 materializer pin の対象外) は insights §4 と同文
- v2 設計材料の追加所見 (実装せず): oracle report の bench-failed 分岐は abort reason 非検査 (偽装面、
  B-5) / probe reason の stage 別写像案 (B-5) / 実行 byte 保証の起動直前再照合・fstat 等メニュー (A-4)。
  D-5 の fan-out 監査 (7 driver) は CompetingBenchProbeError 非捕捉伝播 = fail-closed で正しいと確認
- 棄却/縮小: 36 所見中、部分採用・見送り 8 (B-2 実装見送り、B-5/G-6 の oracle 側は D-4 優先で v2 へ、
  G-1/G-2 は fallback 側採用、G-9/A-4 部分、B-1 の procps capability 検証は過剰)。詳細 = 裁定表
- phase3: checkpoint (c) 完了化 (代替凍結・逐語復元不能の D-11 文言)・更新日同期・残欄に部分基盤の
  注記。裁定待ちパッケージ文書は 1 byte も不変 (D-10)
- テスト: 基線 1 failed (D56 意図 gate)/940 passed/22 skipped → **1 failed (同一)/996 passed/22 skipped**
- 工数: Explore 3 (sonnet) + codex 4 (reasoning=max) + workflow 20 agents (~1.5M tokens) + 親直接修正 3

### 次の一手
1. 本ブランチ (worktree-s8b-v2-prereqs) の push → PR → merge 判断 (ユーザー実施 — Pegasus は AI から
   push しない運用)。D-12 の推奨: L2 (意味論変更) は個別レビュー価値が高い
2. s8b: パッケージ F1〜F7 のユーザー裁定 (変わらず — (1) 参照)。裁定材料に B-2 (自己子孫除外) を追加
3. 裁定後の v2 wave で「正直な残」を消化 (一覧は本エントリと insights §4)

## 2026-07-17 (6) — Claude-Session trailer の廃止 + AI-Agent scope 導入 (計測なし)

ユーザー問題提起 2 件への対応。(a) commit message の `Claude-Session:` URL は第三者に見られると
まずくないか → 調査結論: URL はログイン + 所有者限定のアクセス制御下で ID は bearer でないが、
「AI セッションの存在と ID が履歴に永続する」ため停止 + 履歴除去を裁定。(b) 同一 role の AI-Agent
行が複数あると何をどれが担ったか復元不能 (既存 8 commit) → scope フィールドで解消。

- commit: 6507c87 (sessionUrl 停止 + 除去スクリプト同梱), faafbbf (scope 導入) の 2 本
- 停止は二層: project settings (6507c87) + user settings `~/.claude/settings.json` (repo 外、
  未マージ worktree のセッションにも即時有効)。本セッション以降の commit に Claude-Session なし
- 履歴除去 (50/460 commit) は**未実行・ユーザー承認待ち**: strip_claude_session_trailers.sh は
  preflight → 書き換え → 検証で停止し push しない設計。opus 敵対レビュー (7 主張中 5 成立、real 4:
  rebase 復活 / 未 push 盲点 / branch protection / PR 本文・refs/pull 残存) を反映。合成 repo の
  実地テスト + preflight 負テストで発火確認済み
- scope 規則: 同 role 複数行で必須。checker は導入 commit を -S 内容検出する epoch 方式で遡及なし
  (SHA 非依存 = 履歴書き換え耐性)。message-file 7 ケースと全履歴監査 123 件で固定
- 工数: claude-code-guide (sonnet) 1 + opus 敵対レビュー 1 + 親直接実装
- 履歴除去を実行 (ユーザー承認後、同日追補): サンドボックスから GitHub へ git 接続不可のため、
  リモートの上位集合であるローカル repo を素材に `../izanagi-rewrite` を生成。初回実行は残存判定が
  本対応自身の commit 件名 (プロース言及) に fail-closed 発火 → 判定を実害基準 (URL / 行頭 trailer
  形式) へ修正して再実行。force-push はユーザー引き渡し。旧→新 SHA 対応表は
  `izanagi-rewrite/.git/filter-repo/commit-map` に**残し、repo へはコミットしない** (旧 SHA の索引を
  公開しないため)。push 後は worklog 中の既存 hash 引用が旧履歴参照になる (対応表で解決可能)

### 次の一手
1. **force-push (ユーザー)**: `cd ../izanagi-rewrite && git remote add origin
   git@github.com:thawk105/izanagi.git && git fetch origin` で想定外の新規 commit がないことを確認 →
   `git push --force origin main worktree-s8b-ruling-prep` (ruling-prep は完全マージ済みなので
   `git push origin --delete worktree-s8b-ruling-prep` でも可)。main の branch protection は事前解除
2. push 後の後始末 (依頼あれば AI 実施可): 各ローカル checkout / worktree / 他マシン clone (Pegasus 等)
   の fetch + reset、GitHub PR 本文のセッション URL 確認・編集 (スクリプトヘッダの一覧に従う)
