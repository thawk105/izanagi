# s8b C2-2 launch certificate 結線 wave — codex 敵対相談の逐語・裁定・確定プラン (2026-07-18)

**編集方針 (逐語性の例外):** §6 の相談逐語のうち、単一 holdout の三軸リテラルが同一行に並ぶ箇所は、
本ファイル自身が holdout scan の conjunction hit になるのを防ぐため `ycsb_rratio=` →
`ycsb_rratio⟦=⟧` の形で軸名直後の `=` を可視マーカーで置換した (意味は不変、機械照合のみ破壊)。
それ以外は逐語。原文はセッション一時領域のみに存在し揮発する (F20 の教訓どおり、恒久正本は本ファイル)。

## §1 背景とスコープ

- セッション: 2026-07-18 bg job (worktree s8b-c22-launch-cert、基準 e45db19)。クラス 3。
- レーン A: worklog (8) 次の一手 1 の guard_agent live 発火確認 → **不発を発見**、原因調査と文書化。
- レーン B: worklog (7) residual の C2-2 launch certificate 発行結線 + verifier lineage 照合。
- ループ: 親プラン v1 (.consult 一時ファイル、非 commit) → codex gpt-5.6-sol 敵対相談 4 本並列
  (A=発行側 max / B=検証側 max / C=テスト・スコープ・順序 max / D=guard_agent high) → 親裁定 →
  codex 並列実行 → claude opus 並列レビュー → 残所見再投げ。
- 所見総数: **must-fix 26 / should-fix 7 / nit 0、refuted 0 (全 real 裁定、ただし一部は「今 wave では
  実装せずユーザー裁定パッケージへ」)。**

## §2 親裁定表 (要旨)

| # | 所見 (severity) | 裁定 | 反映先 |
|---|---|---|---|
| A1 | repo が既に clean scan hit-0 でない — test_s8b_ratified_freeze.py が rr80/rr20 に実 hit (must) | real (親が実 scan で追認) | E2 (脱同居 + 実 scan 不変条件テスト) |
| A2 | clean_scan_digest が malformed report に fail-open — F9 型 (must) | real | E1 (_assert_search_pass 必須通過) |
| A3 | scan と digest の列挙分離 TOCTOU (must) | real | E1 (before→search(files)→after 完全一致) |
| A4 | scan hit 時 zero-side-effect とプラン順序の矛盾 (must) | real | E1 (scan を mkdir より前へ) |
| A5 | mode domain 未検証 + path traversal (must、既存バグ) | real | E1 (_validate_mode、seam より前、テストで patch 禁止) |
| A6 | output/s8b-freeze/ prefix 全除外が clean cert の盲点 (must) | real | E1 (preflight 限定 exact allowlist)。恒久設計は §5-(ix)-9 |
| A7 | 実 manifest/result 自身が hit し closure 導出と矛盾 (must、in-memory 実証付き) | real | §5-(ix)-3 (closure 契約の裁定が必要) |
| A8 | cert 発行後 campaign-start 前 crash が回復不能 + cert は一回限り問題 (must) | real | E1 (launch-start journal 耐久化)。回復 semantics と one-shot 裁定は §5-(ix)-4/5 |
| A9 | resume が bytes hash のみで意味再検証なし (should) | real | E1 (共有 validator + run_id==dirname) |
| A10 | builder 自由文字列 field 経由の hit 混入 (should) | real | E1 (canonical bytes の hit-0 自己検査) |
| B1/C3 | 「journal 束縛」が result 内 wall_ledger 自己申告に弱まる (must) | real | §5-(ix)-1 (journal.jsonl G blob 実体検証) |
| B2/C4 | cert・closure 同一 commit では時間順序を証明できない (must) | real | §5-(ix)-2 (厳密祖先 + 導入一意) |
| B3 | 複数導入の量化未定義 (削除再導入/merge/rebase bypass) (must) | real | §5-(ix)-2 |
| B4 | 裁定済み「closure を G に同時収録」を現行 V1d が強制していない (must) | real | §5-(ix)-10 (§5-(ii) 追認と同時に機械化) |
| B5 | dirname 由来 path の偽造 + symlink blob 偽装 (must) | real | §5-(ix)-7 (canonical path parser + mode 100644) |
| B6/C8 | protocol/freeze の equality chain 不完全 (must) | real | 発行側分は E1 テストで束縛、verifier 分は §5-(ix)-1 |
| B7 | 検証済み floor artifact が oracle に引き渡されない (should) | real | §5-(ix)-8 (VerifiedFloorArtifact) |
| B8 | fixture は段階 builder への再設計が必要 (should) | real | 追認後実装 note (§5 末尾) |
| B9/C1 | 検証側 normative 実装は追認待ち領域への越権 (must) | real — **方針転換の決定打** | 検証側は本 wave 実装せず §5 パッケージ化 |
| B10 | reason code 表が失敗面を閉じない (should) | real | 追認後実装 note |
| C2 | スコープ文言と tmp-only 拘束の不備 (should) | real | E1 拘束 + Lane A 別 commit + worklog 文言 |
| C5 | clean scan 恒真 + output/env の恒久拒否リスク (must) | real | E1 + §5 運用 note |
| C6 | orphan cert / 発行順矛盾 (must) | real | = A4/A8 |
| C7 | resume 意味再検証 (must) | real | = A9 |
| C9 | eligible_for_refreeze 三択未裁定のまま happy fixture 化は不可 (must) | real | §5-(ix)-6 |
| C10 | _need_v1 の pytest.skip で攻撃 matrix 全 skip (must) | real | 親直接修正 (skip→fail、E 完了後) |
| C11 | writer/verifier 別 stub では dormant 結線を証明できない (must) | real | E1 統合は production bytes 経由。full E2E は追認後 |
| C12 | 変異 2 件では不足 — 6 群列挙 (must) | real | レビュー後の変異スポット段で now-scope 群を適用 |
| C13 | Lane A の因果断定は観測超過 (should) | real | 文書化済み (F21/README は「原因未分離」記載) |
| D1 | bg 固有と断定不能 — 2.1.211/2.1.212 × bg/headless の二重交絡 (must) | real (親が transcript で version 追認) | F21/README 記載修正済み + §5 再検証条件 |
| D2 | 対照実験が enforcement 陽性対照になっていない (must) | real | 追実験実施 — §4 (3) で閉鎖 |
| D3 | worktree 仮説の refuted を明記せよ (must) | real | README/F21 に反映 |
| D4 | 「機械的防衛は無い」は偽 (must) | real | §5 Lane A 候補 (適用はユーザー判断) |
| D5 | 別 lifecycle hook は検知であって予防でない (should) | real | README 表現に反映 |
| D6 | docs-only 恒久対応は failures 契約を満たさない (must) | real | F21 は「恒久検査未実装」と正直に記載 |

Q-1 (テスト seam): 採用。条件 = _validate_mode / path 検証は seam に含めない・テストで patch しない、
CLI 拒否と unpatched core の zero-write テスト維持、production bypass なし、monkeypatch は局所 scope。
Q-2: A の回答を採用 (golden protocol は hit 0 / 自由文字列で hit 混入可 → E1 で自己検査 /
manifest・result は実 hit → (ix)-3 / cert hit-0 は「v1→g1 初回一回限り」裁定案 → (ix)-4)。
Q-3〜Q-6: B の回答を §5 の推奨案として記載 (裁定はユーザー)。Q-7: D の回答を §5 Lane A に記載。

## §3 確定プラン v2 (本 wave の実装スコープ = 判断非依存部分のみ)

- **E1 (codex, s8b_floor_campaign.py + 同テスト + builder テスト):** _validate_mode (exact
  {pilot,official}、既存 path traversal バグ修正) / _assert_official_permitted seam 抽出 (無条件
  raise 不変) / clean_scan_digest 恒真封鎖 (_assert_search_pass 必須 + 列挙 before/after 一致 +
  output/s8b-freeze exact allowlist) / validate_launch_certificate (exact 6 keys、fresh・resume 共用)
  / _official_launch_preflight (scan は mkdir 前、now 1 回捕捉、cert create-only 発行 + 自己検査 +
  launch-start journal 耐久化) / campaign-start への cert sha 束縛 (official のみ、schema bump なし)
  / _verify_resume_journal 拡張 (意味再検証 + rename 検出 + pilot 混線拒否) / builder canonical
  bytes の hit-0 自己検査 / 統合・負例・zero-side-effect テスト一式 (tmp-only、実 output/ 前後不変)
- **E2 (codex, test_s8b_ratified_freeze.py + 新規不変条件テスト):** 軸リテラルの実行時結合化
  (バイト列不変) + 実 scan hit-0 の repo 不変条件テスト (既知 hit 台帳方式、陽性対照 >0 併記)
- **Lane A (実施済み):** hooks/README hook 4 既知限界 + failures F21。コード変更なし。別 commit
- **親 follow-up:** _need_v1 skip→fail / claude opus 並列レビュー (2 レンズ × レーン) / 変異
  スポット (C12 の now-scope 群) / worklog・memory・handoff 削除
- **本 wave でやらないこと (越権防止):** launch_validate の受理条件変更・§5-(ix) の normative 実装・
  happy fixture の official 化・実 cert / 実 approval / 実凍結の生成。official 拒否 (CLI + core) 不変

## §4 本セッションの実測検証 (親またはツールによる一次事実)

1. **実 scan:** search_repository(ROOT) → rr80 / rr20 とも hit = orchestrator/tests/
   test_s8b_ratified_freeze.py の 1 件のみ。positive_control hit_count = 42 (稼働)
2. **guard_agent 不発:** 本 bg セッション (daemon 2.1.211) で model 無し general-purpose Agent
   呼び出しが素通り。同セッションで guard_bash は発火。hook 単体 stdin は exit 2
3. **enforcement 陽性対照 (headless 2.1.212):** repo と同一 command 形 ($CLAUDE_PROJECT_DIR 展開)
   + model 欠落呼び出し → PreToolUse 配送 (併設 logger が input_keys=[description,prompt,
   subagent_type] を記録) + exit 2 + spawn 阻止 + 拒否メッセージが親モデルへ逐語到達
4. **matcher 実験 (headless 2.1.212):** matcher 無し / matcher "Agent" 完全一致の両方で
   tool_name "Agent" として配送。公式 docs も matcher/tool_name とも "Agent"、hooks は live-reload

## §5 ユーザー裁定パッケージ (次回ユーザー接点で提示)

**裁定結果 (2026-07-18 ユーザー裁定 — 同日 C2-2 検証側実装 wave で発効):**
- (ix)-3 = **択 (a)** (期待 hit を union 導出)。実装解釈: 検証鎖で束縛される run_dir artifact
  (floor_protocol / floor_source=result / journal / manifest) は期待集合へ暗黙に含め、それ以外の
  hit は measurement_closure の列挙のみを想定内とする (journal/manifest も実 hit するため、
  これを含めないと (a) が成立しない — 実装 wave の敵対相談で攻撃対象)
- (ix)-4 = **初回限り** (現 schema の clean hit-0 cert は v1→g1 専用。再実測用の別 schema は将来裁定)
- (ix)-5 = **厳密検証付き pre-start resume** (ユーザーは「推奨案どおり」と裁定。本項は文書上
  推奨が明示されていなかったため、launch-start 耐久化の設計意図に沿うこの択を推奨と解釈して採用
  — 解釈である旨をユーザーに明示済み)
- (ix)-6 = **official 完走 finalize 時のみ True** の provenance フラグ (B 推奨案)
- (ix)-1 / -2 / -7 / -8 / -9 / -10 = **追認** (推奨案どおり。-2 の「履歴書換え耐性は H 内記録順
  のみ」という限界記載も含めて追認)
- 未裁定のまま残るもの: 前 wave §5 の (i)〜(viii) (strict-v2-wave-consultations.md)、
  master_seed / env_tag の受領、guard_agent 防衛候補 (次回 bg セッション再検証待ち)

**C2-2 検証側 (§5-(ix) として追認リストへ追加提案。裁定まで launch_validate は現状維持):**
- (ix)-1 journal 実体検証: floor_source と同 dir の journal.jsonl を G の regular blob として必須化し
  状態機械を検証、result.wall_ledger は raw journal からの決定的射影として照合 (自己申告排除)。
  equality chain: canonical_sha256(floor_protocol blob) == result.protocol_sha256 == journal
  campaign-start.protocol_sha256 == cert.protocol_sha256、v1/freeze hash 側も同型
- (ix)-2 cert anchor の lineage 条件: cert 導入 commit は非 merge・導入一意 (|I_cert|=1)・G の
  **厳密祖先** (同一 commit 不許可 — 同一 commit では「測定後に cert を後付け」と区別不能)。
  closure entry 側は全称条件 ∀i∈I_entry: anchor < i。rebase / 履歴書換え耐性は「検証 commit H 内の
  記録順のみ」という限界を明記 (強保証が要るなら署名 tag / 保護 remote 等の外部 anchor が別途必要)
- (ix)-3 closure 契約: 実 official campaign の manifest.json / result.json は holdout に実 hit する
  (in-memory 実証済み) ため、現行の「期待 hit = measurement_closure bytes のみ」導出では正直な
  official 実走が必ず拒否される。択: (a) 期待 hit を floor_protocol + floor_source + closure の
  union から導出 / (b) 「全 scan-hit artifact (manifest/journal/result 含む) を closure に必ず列挙」
  という契約を明文化。いずれも §5-(i) closure schema 裁定と同時に決める
- (ix)-4 cert の適用範囲: 現 schema の clean hit-0 cert は「v1→g1 の初回 official 一回限り」。
  二回目以降の official (再実測) を許すなら、active closure を baseline とした完全一致 + baseline
  digest 束縛の別 schema が必要
- (ix)-5 crash 回復: cert 発行後・campaign-start 前の crash は本 wave の launch-start journal で
  耐久化したが、その状態からの回復 (pre-start resume を許すか、cert 失効 + 再発行手順か) は未裁定
- (ix)-6 eligible_for_refreeze: 択 = field 廃止 / official 完走 finalize 時のみ true (provenance
  フラグ、B 推奨) / 非権威の診断 field と明記し verifier は別導出。裁定まで happy fixture 化しない
- (ix)-7 path 契約: floor_source.path は canonical root-relative + 正規 run layout (env_tag /
  s8b-floor-official / run-id 形式 / protocol hash prefix) 完全一致 + cert/result/journal は
  ls-tree mode 100644/100755 の regular blob 要求 (symlink blob 偽装の封鎖)
- (ix)-8 型伝搬: LaunchValidatedFreeze に検証済み floor artifact (bytes/hash/deep-immutable doc) を
  保持させ、oracle は再 parse せずそれを消費 (parser 分裂の fail-open 面を閉じる)
- (ix)-9 scan 除外の恒久設計: output/s8b-freeze/ の prefix 全除外は先行測定の隠し場所になる
  (本 wave は cert preflight 限定の exact allowlist で暫定封鎖)。恒久的には「既知宣言 artifact の
  exact path + bytes hash 免除」への移行を提案
- (ix)-10 §5-(ii) の機械強制: closure / floor_source の導入 commit == G (同時収録) を V1d に追加
- 運用 note: 過去 campaign 出力を output/env に commit すると official clean scan を恒久拒否し得る
  ((ix)-3/-4 の裁定と連動して baseline 設計を決める)。fixture は段階 builder base(clean) → C(cert)
  → G(result+closure+generation) → A(approval) へ再設計 (追認後、B8)。reason code 追加 (B10) も同時

**Lane A (guard_agent):**
- 再検証: 次回新規 bg セッションで daemon version 確認の上、model 無し Agent 呼び出しを再試験
  (拒否 = version drift だった / 素通り = bg surface の配送欠落)
- 素通りだった場合の機械的防衛候補 (いずれも副作用あり、適用はユーザー判断): permissions.deny で
  Agent 全面拒否 (orchestration 全停止) / CLAUDE_CODE_SUBAGENT_MODEL で子モデル強制 (named role の
  frontmatter ピンも上書き) / bg を使わない foreground 運用 / 絶対パス logger による
  SubagentStart/PostToolUse telemetry (検知のみ、予防ではない)
- worklog (8) の「hook 設定はセッション起動時 snapshot」という記述は現行 docs (live-reload) と
  不一致 — 本セッションでは snapshot/live-reload の切り分け実験は未実施 (どちらでも上記結論に影響なし)

## §6 相談逐語 (redacted 逐語 — 編集方針は冒頭)

### 相談 A (gpt-5.6-sol reasoning=max, read-only, cwd=worktree)

結論から言うと、現プランのままの実装開始は不可です。`must-fix` 8件、`should-fix` 2件です。特に Q-2 は将来懸念ではなく、現リポジトリですでに発火しています。

## 所見

1. {
   severity: `must-fix`  
   タイトル: 現リポジトリはすでに clean scan hit-0 ではない  
   攻撃シナリオ: 現在の `search_repository(ROOT)` を実行すると、`rr80` と `rr20` の双方が `orchestrator/tests/test_s8b_ratified_freeze.py` を conjunction hit として返す。D-1 を結線すれば、実 official は必ず certificate 発行前に拒否される。一方、計画中の統合テストは scan を stub 化するため、この本番不能を見逃す。  
   根拠: fixture が三軸を同一ファイルに直書きしている [test_s8b_ratified_freeze.py:166-168](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:166)。matcher は同一ファイル内の三軸一致で hit にする [s8b_holdout_freeze.py:270-282](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_holdout_freeze.py:270)。既存 clean-scan テストは検索結果を全て monkeypatch している [test_s8b_floor_campaign.py:1245-1262](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_floor_campaign.py:1245)。  
   提案: テスト fixture は `HOLDOUTS`/`concrete_axis_encodings` から実行時に組み立て、source file 自身には三軸 literal を同居させない。テストディレクトリを scan 除外してはいけない。さらに実 scan を通す repo invariant テストを追加する。
   }

2. {
   severity: `must-fix`  
   タイトル: `clean_scan_digest` の受理判定が malformed/inoperative report に fail-open  
   攻撃シナリオ: `search_repository` が回帰して `{"holdouts": {}, "positive_control": {"hit_count": 0}}` を返しても、ループは0回で終了し digest が返る。`rr20` だけ欠落した report や陽性対照が死んだ report でも certificate を発行できる。  
   根拠: 現実装は「存在する holdout」だけを走査し、holdout 集合・型・陽性対照を検査しない [s8b_floor_campaign.py:896-910](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:896)。必要な exact-name/zero-hit/positive-control 検査は既に `_assert_search_pass` にある [s8b_holdout_freeze.py:384-404](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_holdout_freeze.py:384)。これは F9 型の恒真ゲート。  
   提案: `clean_scan_digest` は `_assert_search_pass(report)` を必須通過させ、`FreezeError` を `FloorCampaignError` に翻訳する。欠落 holdout と陽性対照 0 の mutation test を置く。
   }

3. {
   severity: `must-fix`  
   タイトル: scan 対象と digest 対象が別列挙で、TOCTOU と意味不一致がある  
   攻撃シナリオ: `search_repository` が clean と判定した直後に、別プロセスが `ycsb_rratio⟦=⟧80 ycsb_zipf_skew⟦=⟧0.9 ycsb_rmw⟦=⟧0` を持つ untracked file を追加する。後段の列挙 digest はその filename を含むが、コードは再検索も集合一致検査もしないため certificate を発行する。さらに search は除外後の集合、digest は除外前の全集合を hash している。  
   根拠: search と digest が独立に列挙される [s8b_floor_campaign.py:902-910](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:902)。`search_repository` は `files` 注入を既に持ち、除外後集合を検索する [s8b_holdout_freeze.py:297-304](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_holdout_freeze.py:297)。既存 `launch_validate` は少なくとも列挙前後 digest を比較している [s8b_ratified_freeze.py:1283-1290](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:1283)。  
   提案: `files_before = enumerate...` → `search_repository(root, files=files_before)` → `files_after = enumerate...` → 完全一致要求、の順にする。digest は検索した正規化済み集合と match convention/search result を canonical に束縛する。内容 TOCTOU は single-tenant residual として明記する。
   }

4. {
   severity: `must-fix`  
   タイトル: 「scan hit 時 zero side effects」はプラン自身の順序と矛盾  
   攻撃シナリオ: 空の `out_root` で official gate だけを開け、dirty scan を返す。D-2 は先に `_fresh_run_dir` を呼ぶため、scan が拒否しても `out_root/env/.../s8b-floor-official/...` が残る。既存 zero-side-effect テストの `assert not out_root.exists()` と両立しない。  
   根拠: プランは run_dir 作成後に preflight と書く一方、テスト計画では zero side effects と記載する [.consult-c22-plan-v1.md:22-23](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:22)、[同:76-78](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:76)。実装は `mkdir(parents=True)` で親まで作る [s8b_floor_campaign.py:1864-1873](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1864)。既存テストも出力 root 不在を要求する [test_s8b_floor_campaign.py:500-516](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_floor_campaign.py:500)。  
   提案: `now_fn()` を1回だけ捕捉して候補 run ID/path を純粋計算し、scan 合格後に初めて `mkdir` と cert 発行を行う。あるいは「empty run_dir を残す」と明示して zero-side-effect 主張を削除する。
   }

5. {
   severity: `must-fix`  
   タイトル: D-5 は core の mode domain 未検証と path traversal を温存する  
   攻撃シナリオ: core を直接 `mode="pilot/../../../../../../escaped"` で呼ぶ。exact `"official"` ではないため拒否を通過し、raw mode が path に埋め込まれる。例えば `/safe/out/env/linux-baremetal/...` から `/escaped/<run-id>` へ解決でき、`out_root` 外へ書き出す。CLI の choices は core 直接呼出しを守らない。  
   根拠: core は exact official だけを拒否する [s8b_floor_campaign.py:1705-1715](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1705)。mode は無検証で path segment に入る [s8b_floor_campaign.py:1864-1870](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1864)。`choices` は CLI にしかない [s8b_floor_campaign.py:2001-2009](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:2001)。  
   提案: patchable な permission seam より前に、別の `_validate_mode(mode)` で exact `{"pilot", "official"}` を強制する。テストは permission helper だけを patch し、mode/path 検証は絶対に patch しない。
   }

6. {
   severity: `must-fix`  
   タイトル: `output/s8b-freeze/` の prefix 全除外が clean certificate の盲点になる  
   攻撃シナリオ: `output/s8b-freeze/prior_measurement.txt` を commit し、rr80 三軸を置く。tracked file なので列挙されるが prefix 除外され、clean certificate が発行される。v1/v2 generation を除外する必要性を利用して、任意の先行測定を同 namespace に隠せる。  
   根拠: 除外は directory 全体 [s8b_holdout_freeze.py:27-33](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_holdout_freeze.py:27)、判定は単純 prefix [s8b_holdout_freeze.py:232-233](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_holdout_freeze.py:232)。v2 resolver も未知の committed namespace file を無視する [s8b_ratified_freeze.py:969-973](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:969)。  
   提案: clean preflight 専用に「既知の宣言 artifact の exact path + bytes hash」だけを免除する。directory prefix の全面免除は禁止し、未知ファイルは hit 有無にかかわらず拒否する。
   }

7. {
   severity: `must-fix`  
   タイトル: 実 campaign 出力は closure fixture と異なり、manifest/floor_source 自身が hit する  
   攻撃シナリオ: official campaign を完走し、自然に `result.json` を `floor_source`、raw 計測物だけを `measurement_closure` に宣言する。実 `manifest.json` と `result.json` は rr80/rr20 の双方に hit するが、`launch_validate` の期待集合は `measurement_closure` の bytes だけから作るため、floor_source/manifest が未申告 hit になって拒否される。in-memory で実 `assemble_manifest` 形と result session 形を matcher に通し、双方が rr80/rr20 hit になることを確認済み。  
   根拠: cell workload は freeze の ycsb をそのまま持つ [s8b_floor_campaign.py:585-601](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:585)、manifest は全 cells を収録する [s8b_floor_campaign.py:845-866](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:845)、session/result も workload を保持する [s8b_floor_campaign.py:1250-1268](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1250)、[同:1528](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1528)。期待 hit は measurement closure 限定 [s8b_ratified_freeze.py:1271-1304](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:1271)。既存 fixture は floor_source に ycsb params を含めないよう明示しており、実分布を隠している [test_s8b_ratified_freeze.py:187-204](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:187)。これは F15 型のテスト代表性不足。  
   提案: expected hit を `floor_protocol + floor_source + measurement_closure` の union bytes から導出するか、result/manifest/journal を含む「全 scan-hit artifact を closure に必ず列挙する」契約を明文化する。実 `_result_bytes` と manifest bytes を使う統合テストが必要。
   }

8. {
   severity: `must-fix`  
   タイトル: cert 発行後・campaign-start 前の crash が回復不能状態を作る  
   攻撃シナリオ: clean scan と cert 発行に成功し、build/manifest 作成後、`_Runner.run()` の campaign-start append 前に crash する。manifest は既に holdout hit を持つ。resume は campaign-start 不在で拒否、fresh retry は manifest hit により clean scan で拒否される。削除以外に進路がなく、痕跡削除を誘発する。また完走済み closure が残る限り、二度目の fresh official も同じ hit-0 条件で必ず拒否される。  
   根拠: manifest は runner 起動前に書かれる [s8b_floor_campaign.py:1777-1823](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1777)。campaign-start は後段の `_Runner.run` で初めて書かれる [s8b_floor_campaign.py:1287-1300](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1287)。resume は campaign-start 不在を一律拒否する [s8b_floor_campaign.py:1934-1939](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1934)。production path は `output/env/...` で [layout.py:87-90](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/layout.py:87)、この領域は scan 除外されない。  
   提案: `launch-start` のような二相 journal marker を cert 直後に耐久化するか、`cert + sealed manifest + empty journal` を厳密検証して campaign-start を初回発行できる pre-start resume 状態を定義する。さらに本 certificate schema を「v1→g1 の一回限り」と明記する。再実測を許すなら hit-0 ではなく active closure を baseline とする別 schema が必要。
   }

9. {
   severity: `should-fix`  
   タイトル: D-4 の resume 検査は cert bytes hash だけで、cert の意味を再検証しない  
   攻撃シナリオ: partial official run directory を別名へ rename する。cert と journal は未変更なので bytes hash は一致し、D-4 案では resume が進む。しかし cert の `campaign_run_id` は旧 dirname のままで、後段検証で初めて拒否される。無効な official 測定を先に続行してしまう。  
   根拠: cert は protocol/freeze/run ID を持つ [s8b_floor_campaign.py:913-929](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:913)。プラン D-4 は存在と bytes hash 一致だけを要求する [.consult-c22-plan-v1.md:29-31](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:29)。現 resume API は run_dir/mode を受け取らない [s8b_floor_campaign.py:1925-1949](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1925)。  
   提案: exact-key/strict parse 後、schema、v1 freeze hash、protocol hash、UTC、`campaign_run_id == run_dir.name` を resume 前に照合する。pilot は journal key だけでなく cert file の存在も mode 混線として拒否する。
   }

10. {
    severity: `should-fix`  
    タイトル: Lane J protocol output の hit-0 は builder の型では保証されない  
    攻撃シナリオ: `master_seed="seed-ycsb_rratio⟦=⟧80 ycsb_zipf_skew⟦=⟧0.9 ycsb_rmw⟦=⟧0"`、他は golden 引数で builder を呼ぶ。この値は valid として canonical JSON に入り、matcher は protocol file を rr80 hit と判定する。実行確認では通常 golden は hit 0、この seed は rr80 hit 1だった。  
    根拠: master seed は non-empty string しか要求しない [s8b_floor_campaign.py:278-281](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:278)、builder も同様で、そのまま document に埋め込む [s8b_floor_campaign.py:406-410](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:406)、[同:438-460](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:438)。通常 golden bytes には三軸がない [test_s8b_protocol_builder.py:45-60](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_protocol_builder.py:45)。  
    提案: protocol 凍結時に canonical bytes 自身を `holdout_conjunction_hits` へ通して hit 0 を要求する。代替は master seed/stock ID を slug/hex grammar に制限する。
    }

## Q-1 への直接回答

裁定案は「D-5 の private test seam を採用」です。helper 単体テストだけでは、D-1〜D-4 の実結線が一度も実行されず、F9/F21 型の恒真保証になります。

ただし条件があります。

- patchable な `_assert_official_permitted` は official 拒否だけを担う。
- exact mode 検証と path safety は別関数で先に実行し、統合テストでも patch しない。
- CLI 拒否と、unpatched core の zero-write 拒否テストを残す。
- production flag、環境変数、公開引数による bypass は作らない。
- monkeypatch は1テストの局所 scope に限定する。

Python process 内で任意コードを実行できる主体は既存関数も差し替え可能なので、private helper 抽出自体は新しい実質的信頼境界を開きません。問題は「その seam が mode/path 検証までまとめて無効化する」設計です。

## Q-2 への直接回答

裁定は次のとおりです。

- 通常の Lane J golden protocol は conjunction hit しません。ただし builder の valid output 全体については保証されず、自由文字列で hit を作れます。
- protocol/v1/v2 generation を `output/s8b-freeze/` に置けば、現 scanner は prefix 全除外するため、それら自身は発行を妨げません。その代わり同 namespace が先行測定の隠し場所になります。
- 過去 campaign 出力は `output/env/...` に置かれ、除外されません。manifest、journal、result は実際に holdout hit になります。
- hit-0 と宣言済み closure hit は、時間軸を分ければ両立します。初回 official の直前は hit 0、実走後は `launch_validate` が hit 0 を要求せず、現 hit と closure 由来 hit の完全一致を要求しています [s8b_ratified_freeze.py:1228-1231](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:1228)、[同:1293-1304](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:1293)。

したがって現 schema の `clean hit-0` certificate は「v1→g1 の初回一回限り」と裁定すべきです。二回目以降を許すなら、active closure を baseline として完全一致を要求し、その baseline digest を束縛する別 certificate schema が必要です。また closure は manifest/journal/result/floor_source を含む全 scan-hit path を閉じなければなりません。

## 確認済み事項

- launch certificate scaffold は create-only で、実際に書いた bytes の SHA-256 を返す [s8b_floor_campaign.py:870-880](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:870)、[同:932-935](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:932)。
- D-2 が使う `freeze_sha256` は protocol の freeze hash と事前照合済み [s8b_floor_campaign.py:1746-1753](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1746)。
- preflight を fresh branch の `build_cells` 前へ置く方針自体は正しく、build/measure 前拒否を実現できる [s8b_floor_campaign.py:1777-1785](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1777)。
- campaign-start への追加 field は `wall_ledger` に全フィールドごと伝播する [s8b_floor_campaign.py:1492-1495](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1492)。
- resume の campaign-start 一意性と protocol/freeze/manifest hash 検査は既にあり、cert 検査の挿入点として妥当 [s8b_floor_campaign.py:1934-1949](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1934)。
- CLI と core の official 二重拒否は現状独立している [s8b_floor_campaign.py:1711-1715](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1711)、[同:2029-2036](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:2029)。
- scan は tracked regular files、非 ignore の untracked files、ccbench submodule regular filesを列挙する設計で、file-level conjunction の定義もコードと文言が一致している [s8b_holdout_freeze.py:90-99](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_holdout_freeze.py:90)、[同:179-212](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_holdout_freeze.py:179)。
- official journal がリポジトリ内に存在しない現状では、pilot の key 不在を維持し mode 混線を明示拒否するなら、JOURNAL_SCHEMA 据置は妥当です。
### 相談 B (gpt-5.6-sol reasoning=max, read-only, cwd=worktree)

結論: このままの実装開始は不可です。must-fix 7件、should-fix 3件。D-9 が証明できるのは「捕捉した H の DAG 上の blob 導入順」だけで、実測順序・raw journal 由来・履歴書換え耐性までは証明しません。

## 所見

1. {severity: must-fix, タイトル: D-6 は「journal 束縛」を自己申告 wall_ledger へ弱めている}

- 攻撃シナリオ: `result.json` に `mode="official"` と、`wall_ledger=[{"event":"campaign-start","launch_certificate_sha256":H}]` を直接書く。raw `journal.jsonl` は G に一切入れず、cert C の後に任意の測定 artifact B を追加して closure に載せる。D-6 は campaign-start 1件と H を取得でき、D-9 も `C < B` で通るが、journal が H を記録した事実も、B がその campaign の出力であることも証明されない。
- 根拠: 裁定は「journal が certificate hash を束縛、closure は certificate 起点 lineage から導出」とする一方、プランは result 内の projection だけを読む（[裁定:516](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:516)、[プラン:45-59](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:45)）。`assemble_result` は journal record を単に `dict(r)` で複写するだけ（[s8b_floor_campaign.py:1492-1495](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1492)）。既存 verifier 自身も raw session/journal の真正性を保証しないと明記する（[s8b_floor_stats.py:434-442](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_stats.py:434)）。
- 提案: 同一 run directory の `journal.jsonl` を G の regular blob として必須化し、campaign-start・terminal・attempt/receipt の状態機械を直接検証する。result の wall_ledger は raw journal からの完全な決定的射影として照合し、closure 各 entry は journal receipt または確定した出力 inventory から機械導出する。単なる Git 祖先関係を「lineage」と呼ばない。

2. {severity: must-fix, タイトル: D-9 の「同一 commit 可」は順序証明を消滅させる}

- 攻撃シナリオ: 未申告測定を先に行い、その後 cert、result、closure artifact、generation JSON をすべて G に押し込む。cert hash を result の wall_ledger に合わせれば、cert と closure の導入 commit はともに G。D-9 の `anchor と同一または子孫` を満たし、cert が測定後に作られたことを検出できない。
- 根拠: `_immutable_introductions` の導入とは「present かつ全 parent で absent」であり、同じ G に追加された二 path は同じ導入 commit を返す（[s8b_ratified_freeze.py:322-347](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:322)）。create-only は発行側の filesystem 操作にすぎず、後日の Git blob から実行時刻を証明できない（[s8b_floor_campaign.py:870-880](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:870)、[同:932-935](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:932)）。
- 提案: `anchor` は G の厳密な祖先、すなわち `anchor != G ∧ is_ancestor(anchor,G)` とする。運用上 cert を別 commit にできないなら Git ancestry は証明手段として不適格なので、測定前の署名済み tag、保護 remote、または append-only 外部台帳を anchor にする。

3. {severity: must-fix, タイトル: 複数導入の量化が未定義で、削除再導入・merge・rebase に選択的 bypass が残る}

- 攻撃シナリオ:
  - closure を C0 で追加→削除→cert を C1 で追加→同一 bytes の closure を C2 で再導入する。後側 C2 だけ選べば祖先条件を通る。
  - 二枝で同一 cert bytes を add/add して merge する。どちらを anchor にするかで結果が変わる。
  - closure-before-cert の履歴を rebase/squash して cert-before-closure に作り直す。検証時 H からは旧順序が不可視になる。
- 根拠: 関数は単一 commit でなく tuple を返し、同一 bytes の削除→再導入を明示的に許す（[s8b_ratified_freeze.py:325-347](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:325)）。既存テストも2導入と merge add/add を確認している（[test_s8b_ratified_freeze.py:508-559](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:508)）。履歴集合は `rev-list H` の到達可能 commit だけ（[s8b_ratified_freeze.py:282-292](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:282)）。
- 提案: `|I_cert|=1` を要求し、merge anchor を拒否する。§5-ii を採るなら closure は各 entry について `I_entry == {G}` とする。採らない暫定案でも、全導入に対する全称条件 `∀i∈I_entry: anchor<i` が最低線。rebase 耐性は得られないため、「H 内の記録順のみ」という限界を§5へ明記し、強い保証には外部 immutable anchor を要求する。

4. {severity: must-fix, タイトル: D-9 は裁定済みの「closure を G に同時収録」を実装しない}

- 攻撃シナリオ: cert を C、closure を E、generation を後の G に置く。`C<E<G` なので D-9 は通り、現行 V1d も G tree に同じ blob が存在するため通る。しかし closure の導入は G ではなく、裁定の発効トポロジー違反。
- 根拠: 裁定は G に「世代 file + closure artifact を同時収録」と要求する（[裁定:520](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:520)、[同:561-563](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:561)）。現行コードは G に blob が見えることしか検査せず、導入 commit == G を要求しない（[s8b_ratified_freeze.py:789-807](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:789)）。共有 fixture も closure/source を base に置き、G では generation JSON だけを追加している（[test_s8b_ratified_freeze.py:222-240](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:222)、[同:262-266](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:262)）。
- 提案: §5-ii 追認後、少なくとも `floor_source(result)` と全 `measurement_closure` entry の一意な導入 commit を G に固定する。cert は G の厳密な祖先とする。

5. {severity: must-fix, タイトル: dirname ベース D-8 は canonical path と regular-file 性を証明しない}

- 攻撃シナリオ:
  - `floor_source.path="./output/rogue/run-x/result.json"` とし、同じ任意 directory に自己整合した cert を置く。basename/run-id 比較は攻撃者が選んだ path と攻撃者が選んだ field の循環比較になる。
  - cert path を mode `120000` の Git symlink にし、その link-target blob bytes 自体を certificate JSON にする。Git symlink object は blob なので `_blob_at_or_fail` は parse でき、wall_ledger hash も一致する。実際の create-only regular JSON file は存在しなくても通る。
- 根拠: `floor_source.path` は非空文字列しか要求せず、正規 path や layout を検査しない（[s8b_ratified_freeze.py:697-705](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:697)）。`_blob_oid_at` は object type `blob` のみを見て tree mode を見ない（[同:462-473](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:462)）。正規の run layout は `output/env/<env>/calibration/s8b-floor-official/<UTC>-<protocol-prefix>`（[s8b_floor_campaign.py:1864-1868](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1864)）。symlink inventory は列挙するだけで拒否しない（[s8b_ratified_freeze.py:1207-1225](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:1207)）。
- 提案: issuer/verifier 共通の path parser を作り、POSIX root-relative canonical path、basename=`result.json`、env_tag、`s8b-floor-official`、run-id形式、protocol hash prefixを完全一致させる。cert/result/journal は `ls-tree` mode `100644` または `100755` の regular blob を要求する。UTCはrun-idと同一の一度だけ捕捉した時刻から生成する。

6. {severity: must-fix, タイトル: result→journal→cert→protocol/freeze の結合が不完全}

- 攻撃シナリオ: result に `protocol_sha256=P, freeze_sha256=X`、campaign-start に `protocol_sha256=Q, freeze_sha256=Y`、cert に `protocol_sha256=P, v1_freeze_sha256=V1` を書く。さらに cert の `clean_scan_digest=null, started_utc=[]` とする。D-8 が列挙した検査はすべて通るが、実 journal、実 protocol、実 freeze、clean scan、UTCが相互に一致しない。
- 根拠: certificate builder は6 fieldを出すが入力 validation はない（[s8b_floor_campaign.py:913-929](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:913)）。production campaign-start は protocol/freeze/manifest を持つ（[同:1287-1300](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1287)）。result にも別に protocol/freeze/manifest がある（[同:1497-1510](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1497)）。実 run の protocol hash は parsed protocol の canonical hash（[同:152-153](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:152)、[同:1761](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1761)）だが、現行 generation verifier は floor_protocol を parse するだけ（[s8b_ratified_freeze.py:808-810](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:808)）。
- 提案: cert は exact 6 keys、clean digest=64 lower-hex、started_utc=canonical UTC、run-id非空を要求する。さらに  
  `canonical_sha256(floor_protocol) == result.protocol == journal-start.protocol == cert.protocol`、  
  `V1 == result.freeze == journal-start.freeze == cert.v1`、  
  `result.manifest == journal-start.manifest`  
  を完全一致させる。result の top-level schema・型・wall_ledger shapeも exact に定義する。

7. {severity: should-fix, タイトル: D-6 で検証した floor artifact が oracle に引き渡されない}

- 攻撃シナリオ: launch_validate に strict result parserを追加しても、戻り値にはその document が無い。oracle は戻り値を捨て、同じ blob を permissive `json.loads` で再parseして binaries を消費する。現在は G blob が immutable なので直接TOCTOUではないが、「検証済み objectだけを実走へ渡す」型保証が成立せず、parser差分が将来の fail-open 面になる。
- 根拠: `LaunchValidatedFreeze` は floor artifactを保持しない（[s8b_ratified_freeze.py:604-615](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:604)）。oracle は `launch_validate()` の戻り値を捨て（[s8b_oracle_driver.py:463-476](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:463)）、後で再読込・再parseする（[同:402-446](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:402)）。
- 提案: `VerifiedFloorArtifact` を作り、raw bytes/hash/deep-immutable documentを `LaunchValidatedFreeze` に保持する。`_prepare_v2_execution` は戻り値を受け取り、その objectから binaries と inventory を消費する。

8. {severity: should-fix, タイトル: fixture 更新は「全面手修正」ではないが、commit topology の再設計が必要}

- 攻撃シナリオ: stubを単にofficial resultへ置換すると、closureがcert以前のbase commitにあるため、既存の `closure-hit-mismatch` 負例が先に `closure-predates-certificate` で落ちる。oracle fixtureも productionの `schema` ではなく `schema_version` しか持たず、store系テストがcertificate/schema拒否で早期終了する。
- 根拠: 共有 helper は floor source stubとclosureをbaseに置く（[test_s8b_ratified_freeze.py:169-170](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:169)、[同:222-240](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:222)）。verify側の直接 launch_validate は7箇所（代表: [test_s8b_ratified_verify.py:39-47](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_verify.py:39)、[同:227-320](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_verify.py:227)）。oracleの独自 artifact は `{schema_version,binaries}`（[test_s8b_oracle_driver.py:1268-1307](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_driver.py:1268)）。
- 提案: 中央fixtureを `base(clean) → C(cert) → G(result+closure+generation) → A(approval)` の段階builderにする。valid official result documentへの mutation hookを用意し、raw `floor_source_bytes` 差替えを主APIにしない。静的検索では呼出し19箇所・3ファイルだが、主要変更点は共有helperとoracle helperの2箇所。工数は中程度。ただし各負例の「最初に発火すべき reason」を再確認する必要がある。

9. {severity: must-fix, タイトル: 「schema変更なし」は§5追認待ち領域へ進んでよい根拠にならない}

- 攻撃シナリオ: D-9の同一commit可・複数導入解釈をテストで固定した後、ユーザーが§5-iiを「closureはGで一意、certはGより前」と追認すると、既に実装したacceptance contractが裁定と逆になる。検証追加はschema bytesを変えなくても、受理集合を変更する規範実装である。
- 根拠: §5-(i)/(ii) は明示的に追認待ち（[裁定:593-606](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:593)）。D-9自身も未裁定の(ix)追加案である（[プラン:55-59](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:55)）。現行コードには既に exact header と measurement_closure が実装されている（[s8b_ratified_freeze.py:69-79](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:69)、[同:668-684](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:668)）が、これは追加実装への白紙委任ではない。
- 提案: §5-(i)/(ii)に加え、新しい(ix)「cert anchorとGの厳密祖先関係・導入集合の量化・履歴書換え限界」を先に追認する。pure parser/helperの準備は可能だが、`launch_validate`の受理条件とnormativeテストは追認後に結線する。

10. {severity: should-fix, タイトル: D-10 の reason code 表が実際の失敗面を閉じていない}

- 攻撃シナリオ: floor_sourceを壊れたJSONにする、certにduplicate keyを入れる、certを削除→同一bytes再導入する、pathを非正規にする。既存helperをそのまま使うと `bad-json`、`json-duplicate-key`、`multiple-introduction` 等が漏れ、D-10列挙のどれにもならない。
- 根拠: `_strict_load` は複数の低レベルreasonを送出する（[s8b_ratified_freeze.py:221-248](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:221)）。複数導入にも既存reasonがある（[同:427-435](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:427)）。D-10は5種類のみ（[プラン:60-61](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:60)）。
- 提案: 少なくとも `floor-source-invalid`、`launch-certificate-invalid`、`launch-certificate-path-invalid`、`certificate-lineage-ambiguous` を追加する。低レベルparse reasonをcauseとして保持し、外向きreasonは閉じた表へ翻訳する。

## Q-3〜Q-6 裁定案

**Q-3:** official 解禁後は `eligible_for_refreeze` を「official経路で完走し、artifact自己検査を通ってfinalizeされた」というprovenanceフラグに限定する。pilot=false、official finalized=true。`launch_validate` は `mode=="official"` と `eligible_for_refreeze is True` の両方を整合検査するが、このbool自体を証拠にはしない。floorが非null等の品質意味まで持たせるなら別裁定が必要。

**Q-4:** 同一commitは不許可。certは一意・非mergeのanchor commit C、`C` は `G` の厳密祖先。§5-ii採用後は各closure/floor_sourceの導入集合を `{G}` に固定する。certの複数導入、merge add/add、削除再導入は拒否。rebase耐性まで主張するなら外部immutable anchorが必要。

**Q-5:** 無条件強制。すべての `RatifiedFreeze` の実走昇格で、floor_sourceがexact official resultでなければ拒否する。stubや「parseできる場合だけ」の互換分岐は明確なfail-open。

**Q-6:** 越権になる。D-9、G同梱、同一commit可否、複数導入裁定は受理意味論そのものであり、単なるschema非変更ではない。§5-(i)/(ii)と新(ix)、Q-3/Q-4を追認してからnormative実装へ進むべき。D-6〜D-8のpure helper準備はできるが、official発効・完了扱いは不可。

## 確認済み事項

- `launch_validate` は現在certificate検証を明示的に行わない（[s8b_ratified_freeze.py:1240-1260](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:1240)）。
- v2 headerはexact集合で、未知top-level keyは拒否される（[同:69-79](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:69)、[同:680-684](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:680)）。
- `read_floor_source_blob` はG treeから読み、記録sha256を照合する（[同:1146-1164](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:1146)）。
- cert scaffoldingは6 field・create-onlyだが未結線（[s8b_floor_campaign.py:883-935](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:883)）。
- `assemble_result` はcampaign-startを全fieldごと複写し、`eligible_for_refreeze=False`を定数出力する（[同:1492-1509](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1492)）。
- 現行fixtureのfloor_sourceはstub、closureはG以前、oracle独自artifactもproduction result schemaではない。
- oracleはlaunch検証済みobjectを保持せずfloor_sourceを再読込する。
- HEAD treeの `output/s8b-freeze/` はv1 fileのみで、実v2世代・approval・active pointerは存在しない。
- コード変更・テスト実行はしていない。指定範囲のread-only設計監査のみ。
### 相談 C (gpt-5.6-sol reasoning=max, read-only, cwd=worktree)

結論: 現状のままの実装着手は不可です。無改変の production 経路は official を拒否し続けるため「直ちに実 artifact が発効する」穴はありませんが、certificate–journal–closure の証明鎖と dormant テストに恒真化できる穴が残っています。

1. `{severity: must-fix, タイトル: ユーザー追認より先に B-II を固定すると手戻りが確定する}`

   攻撃シナリオ: ユーザーが §5-(i)/(ii)、同一 commit 可否、無条件適用、`eligible_for_refreeze` のどれかを否認すると、D-6〜D-10、fixture の全面改造、reason code、lineage テストを作り直す。プラン自身が Q-3〜Q-6 を未決のまま残している。

   根拠 file:line: [.consult-c22-plan-v1.md:55-72](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:55)、[consultations §5:593-606](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:593)、[worklog:509-513](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/worklog.md:509)

   提案: 今実装してよいのは、既存 official 拒否の負例、clean-scan の陽性対照、strict cert parser、tmp-only fixture など判断非依存の防壁まで。D-6〜D-10、happy fixture の新意味論、§5-(ix) 追加はユーザー追認後へ送る。

2. `{severity: should-fix, タイトル: 発効境界は保つが「machinery + テストのみ」という文字どおりのスコープではない}`

   攻撃シナリオ: プランは同じ wave で `hooks/README.md`、`docs/failures.md`、memory、worklog を変更するため、変更種別としては machinery + tests を超える。また patched official 統合テストの `out_root` を誤ると、実 repo の `output/env` に real-shaped cert/run artifact を作れる。

   根拠 file:line: [scope declaration:13-15](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:13)、[Lane A writes:93-95](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:93)、[wave scope:8-10](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:8)、[既存 tmp-only 規約:4-6](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_verify.py:4)

   提案: Lane A を別 wave/commit に分離するか、scope を「machinery + tests + limit documentation」に明記する。全 bypass テストは `tmp_path` の repo/root/out_root を必須にし、実 `output/s8b-freeze` と `output/env` の前後 tree 不変を検査する。

3. `{severity: must-fix, タイトル: journal 束縛が journal ではなく result の自己申告を見ている}`

   攻撃シナリオ: 攻撃者が `mode=official` の result に任意の `wall_ledger.campaign-start.launch_certificate_sha256` を書き、同じ hash の cert を添える。実 `journal.jsonl` が存在しなくても D-6〜D-8 は整合する。「通常 assembler が journal からコピーする」は provenance の証明にならない。

   根拠 file:line: [D-6:45-48](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:45)、[wall_ledger copy:1492-1495](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1492)、[`verify_floor_artifact` の保証外:438-442](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_stats.py:438)

   提案: `floor_source` と同じ directory の `journal.jsonl` を G tree から読み、immutable introduction・bytes hash・JSONL 状態機械を検証する。result の `wall_ledger` はその journal から再導出して完全一致させる。少なくとも「cert/result は一致するが journal 不在」「journal と result の campaign-start が不一致」を拒否するテストが必要。

4. `{severity: must-fix, タイトル: cert と closure の同一 commit を許すと時間順序を証明できない}`

   攻撃シナリオ: 計測を済ませた後で cert と closure artifact を作り、両方を G に一括 commit する。D-9 は同一 commit を許すため合格するが、「cert が official 開始時に存在した」ことは履歴から区別できない。さらに `_immutable_introductions` は削除後の同一 bytes 再導入を複数 anchor として返すため、どの anchor を使うかでも判定を操れる。

   根拠 file:line: [D-9:55-59](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:55)、[Q-4:65-66](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:65)、[_immutable_introductions:322-347](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:322)、[複数導入を許す既存テスト:508-521](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:508)

   提案: temporal proof を謳うなら cert の導入 commit を一意にし、全 closure introduction の厳密祖先にする。batch commit を維持するなら、Git lineage は「artifact 集合の同梱」しか証明しないと保証を縮小し、別の append-only/WORM anchor を置く。複数導入、兄弟 branch、pre/post 両方の導入、向きを反転した祖先判定を負例にする。

5. `{severity: must-fix, タイトル: clean scan は空集合で通る恒真ゲートであり snapshot にもなっていない}`

   攻撃シナリオ: `search_repository()` が `{holdouts:{}}`、holdout 欠落、`conjunction_hits=None` を返すとループは拒否せず digest を発行する。rr50 陽性対照も検査しない。また search 後に別途ファイル名だけを列挙するため、走査中の内容差替えや名前集合の往復も検出しない。

   根拠 file:line: [clean_scan_digest:896-910](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:896)、[既存の正しい陽性対照検査:384-404](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_holdout_freeze.py:384)、[B-III は hit だけ:76-78](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:76)、[F9:88-100](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:88)

   提案: exact `HOLDOUTS` 集合、各結果の型、hit 空、rr50 positive control > 0 を共通 validator で強制する。列挙を `before → search(files=before) → after` で挟む。mock だけでなく tmp git repo 上の実 `search_repository` positive control を1本入れる。内容 TOCTOUを受容するなら cert の保証文にも限界を明記する。

   なお `output/env` は scan 対象で、floor artifact はそこへ出るため、過去の holdout pilot artifact は official を意図的に永久拒否し得る。[除外は freeze のみ:28-32](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_holdout_freeze.py:28)、[run_dir:1864-1869](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1864)。これを「正しい prior-measurement 検出」とするのか、別 baseline を設けるのかをテストで固定すべき。

6. `{severity: must-fix, タイトル: scan-hit zero-side-effect と実際の発行順が矛盾し、失敗時には orphan cert が残る}`

   攻撃シナリオ: D-2 は run_dir 作成後に preflight を呼ぶため、scan hit でも directory が残り、「zero side effects」テストは成立しない。さらに cert 発行後、build/store/manifest が失敗すると campaign-start がまだ書かれておらず、journal に束縛されない create-only cert だけが残る。

   根拠 file:line: [D-2:22-25](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:22)、[B-III の主張:76-78](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:76)、[fresh 順序:1777-1794](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1777)、[campaign-start は後段:1817-1831](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1817)

   提案: run id の計算と mkdir を分離し、scan は mkdir より前に行う。cert 発行後の各 failure point について、certified-attempt/refusal journal を残すか、orphan cert を正式な失敗 artifact とするかを決める。scan/build/store/manifest/journal failure の注入テストを置く。

7. `{severity: must-fix, タイトル: resume は cert の bytes hash しか見ず、意味論を再検証しない}`

   攻撃シナリオ: cert の `v1_freeze_sha256`、`protocol_sha256`、run id、schema を改変し、その新 bytes hash を campaign-start に書き直す。D-4 の条件は満たすため、無効な cert のまま計測を再開できる。D-8 が後で拒否しても測定後では遅い。

   根拠 file:line: [D-4:29-31](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:29)、[D-8 の完全検査:52-54](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:52)、[F2 の validator 分裂教訓:28-34](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:28)

   提案: exact parse と field cross-check を行う単一 `validate_launch_certificate(...)` を fresh、resume、ratified verifier で共有する。resume 負例は「cert だけ改変」だけでなく「cert と journal hash を整合して同時改変」を必須にする。

8. `{severity: must-fix, タイトル: protocol–result–journal–cert の束縛鎖が閉じていない}`

   攻撃シナリオ: cert と result の `protocol_sha256` を同じ攻撃者値へ変更し、G の `floor_protocol` blob は別物のままにする。D-8 は cert==result だけなので合格する。同様に result の `freeze_sha256` は cert の固定 v1 hashと照合されない。さらに `floor_source.path` は現状 non-empty string しか要求せず、任意 namespace から cert path を導出できる。

   根拠 file:line: [D-8:51-54](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:51)、[floor_protocol は parse のみ:789-810](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:789)、[result hashes:1505-1509](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1505)、[source path 検査:697-705](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:697)

   提案: 次を一本の equality chain として検査する: `sha256(floor_protocol G blob) == result.protocol_sha256 == actual journal campaign-start.protocol_sha256 == cert.protocol_sha256`。v1 hash も result/journal/cert/定数で一致させる。floor_source は canonical root-relative path、公式 run namespace、ratified env_tag と一致する directory pattern を要求する。

9. `{severity: must-fix, タイトル: official happy path が eligible_for_refreeze=False を正例化する}`

   攻撃シナリオ: dormant official 経路は現行 assembler により `eligible_for_refreeze: false` を出すが、D-7 は `mode=="official"` だけを要求する。happy path がこれを受理すると、field が嘘でも無視する契約を固定するか、将来の official artifact が恒常的に ineligible になる。

   根拠 file:line: [D-7:49-50](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:49)、[Q-3:63-64](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:63)、[定数 False:1497-1504](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1497)

   提案: 実装前に三択を裁定する: field 廃止、official 完走時だけ true、または非権威な診断 field と明記して verifier は別の導出条件を使う。未裁定のまま happy fixture を作らない。

10. `{severity: must-fix, タイトル: critical attack matrix が trust root 不在時に全 skip できる}`

   攻撃シナリオ: 実 v1 freeze が改名・欠落すると `_need_v1()` が `pytest.skip` し、certificate matrix を含む verifier の主要統合テストが緑扱いになる。F9 と同じ「対象が消えると検査も消える」型。

   根拠 file:line: [_need_v1:27-32](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_verify.py:27)、[happy path:39-47](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_verify.py:39)、[F9 再発記録:88-100](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:88)

   提案: trust-root file は「無ければ fail」にするか、bytes を hermetic fixture として固定する。少なくとも新 certificate matrix は skip 条件を継承しない。

11. `{severity: must-fix, タイトル: writer と verifier の別々の stub テストでは dormant 結線を証明できない}`

   攻撃シナリオ: 発行テストは monkeypatch した official core、検証テストは手書き `floor_source_bytes` でそれぞれ緑になるが、production `assemble_result` の出力と verifier parser が相互運用しない。あるいは oracle から `launch_validate` 呼出しを削除しても直接テストは緑のまま。

   根拠 file:line: [B-III:76-82](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:76)、[stub fixture:187-204](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:187)、[直接 happy path:39-45](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_verify.py:39)、[oracle consumer:463-470](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:463)、[F15:141-152](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:141)、[F19:214-229](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:214)

   提案: tmp repo 内で一本の E2E を置く。production dormant coreで cert/journal/result を生成 → exact bytes を G に収録 → approval/active fixture → `load_ratified_freeze` → `launch_validate` → oracle preflight まで通す。mock は official refusal seam、measure、重い build 境界に限定する。oracle の `launch_validate` call 除去 mutation も殺す。

12. `{severity: must-fix, タイトル: 変異スポット2件では信頼境界を覆えていない}`

   攻撃シナリオ: D-9 と binding 比較だけは生きていても、scan 呼出し、陽性対照、journal 実体、resume、official 二重拒否、consumer 呼出しのどれかが消えている。現行2変異は「局所比較がある」ことしか証明しない。

   根拠 file:line: [提案変異2件:82](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:82)、[前 wave の信頼境界別方針:545](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:545)、[F9 positive control 教訓:92-100](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:92)

   提案: 最低限、次の変異を掛ける。

   - 発行: official core guard 除去、preflight を build/measure 後へ移動、clean scan 呼出し除去、scan root 取り違え、create-only を overwrite 化、cert bytes でなく再直列化 hash を使用。
   - scan: holdouts 空/1件欠落、positive control 0、hit 条件反転、HEAD cache 化、search 前後で file 追加・内容差替え。
   - journal/resume: actual journal 不在、result wall_ledger のみ偽造、cert+campaign-start hash の同時改変、campaign-start 0/2件・先頭でない、pilot/official cross-resume。
   - parser/binding: duplicate key、NaN、非UTF-8、extra/missing key、bad 64hex、非UTC時刻、cert+result protocol の同時改変、floor_protocol/freeze との鎖切断、非正規 path/別 namespace。
   - lineage: 祖先判定反転、同一 commit 許否反転、兄弟 branch、cert 複数導入、closure の pre-cert 導入後 delete/re-add、immutable-history 検査除去。
   - consumer/scope: oracle の `launch_validate` 呼出し除去、v1 欠落を skip、実 `output/env` 書込み、cert 発行後の build/store/manifest failure、official なのに eligible false。

13. `{severity: should-fix, タイトル: Lane A は観測事実から内部原因まで断定している}`

   攻撃シナリオ: 「この bg harness では Agent の PreToolUse が発火しなかった」は観測できても、「非同期 Agent が PreToolUse を通さないことが原因」は dispatch trace なしでは推論である。原因断定を failures 台帳へ入れると、別 runtime でも同じ説明を転写する F16 型になる。

   根拠 file:line: [plan:86-95](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:86)、[直前 worklog の live 確認残:533-536](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/worklog.md:533)、[F16:154-165](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:154)

   提案: docs/failures には「当該 bg surface で不発、内部原因未確定」と記録する。fresh runtime の positive/negative control と tool-dispatch evidence が取れた時だけ原因を確定する。

## (1)〜(5) への直接回答

1. スコープ規律: 無改変の実行経路は適合しています。CLI と core の二重拒否は現存し、既存テストも拒否と `out_root` 不生成を固定しています。[core:1711-1715](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:1711)、[CLI:2030-2036](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:2030)、[tests:490-516](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_floor_campaign.py:490)。実 approval/active/v2/protocol を生成する通常経路はプランにない。ただし patched test の tmp-only 条件が未明記で、D-2 の scan-hit は空 run_dir を残す。Lane A docs/memory は文字どおりの「machinery + tests」外なので分離が必要です。

2. 今実装する順序: 正しくありません。worklog の正本は「ユーザー接点で追認 → その後 protocol 凍結・floor」の順です。D-6〜D-10、Q-3〜Q-6、§5-(ix)、fixture 全面更新は追認後にすべきです。今進められるのは判断非依存の fail-closed parser、positive control、拒否負例、tmp-only E2E harness までです。

3. 恒真リスク: 高いです。主因は、`_need_v1()` の全 skip、wall_ledger 自己申告、発行側と検証側の別 fixture、monkeypatch seam だけの成功、oracle consumer E2E 不在、clean scan の陽性対照不在です。seam 抽出自体は許容できますが、private/test-only、runtime flag 無し、既存 CLI/core 拒否負例維持、一本の production-bytes E2E が条件です。helper 単体だけに退く案はさらに悪いです。

4. 変異スポット: 所見12の6群を最低セットとします。特に必須なのは「scan 呼出し除去」「空 holdouts」「cert+wall_ledger の整合同時偽造」「actual journal 不在」「cert+result protocol 同時偽造」「同一/兄弟/multiple-introduction lineage」「oracle call 除去」「v1 欠落 skip」「実出力 path 誤爆」です。D-9除去とbinding除去の2件だけでは不足です。

5. 過去失敗型の再発面:

   - F2 `[ドリフト]`: fresh/resume/verifier で cert validator が分裂。
   - F7 `[権限逸脱]`: patched test の実 filesystem 書込みを prompt 規律だけに依存。
   - F9/F14 `[恒真ゲート]`: v1 欠落 skip、空 scan、monkeypatch 成功を実防壁と誤認。
   - F15 `[テスト代表性]`: handwritten floor_source stub が production result/journal 分布を表さない。
   - F16/F17 `[恒真ゲート][権限逸脱][ドリフト]`: field/call の存在や自己申告 wall_ledgerを runtime lineage の証明と誤認。
   - F19 `[手順漏れ]`: build/manifest failure 後の orphan cert を stubbed happy pathが踏まない。
   - Lane A の原因断定には F8/F16 型の「観測以上の説明を確定する」再発面があります。
### 相談 D (gpt-5.6-sol reasoning=high, read-only, cwd=worktree)

{severity: must-fix, タイトル: 「bg 非同期 Agent が PreToolUse を通らない」という因果断定は成立しない, 攻撃シナリオ: 既知限界を bg ハーネス固有として固定すると、実因が旧 daemon/runtime、hook command の環境変数展開、または bg sessionKind 固有の設定解決だった場合に再発を放置する。実際、不発側は Claude Code 2.1.211・`sessionKind:"bg"`、対照側は 2.1.212・`sdk-cli` であり、バージョンと entrypoint が同時に変わっている。さらに対照側 Agent も async 起動なので、「async だから迂回」は対照自身が反証している, 根拠: [.consult-c22-plan-v1.md:86](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:86), [.consult-c22-plan-v1.md:90](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:90), [不発 transcript:62](/home/SFC/tanab/.claude/projects/-home-SFC-tanab-github-izanagi--claude-worktrees-s8b-c22-launch-cert/d0d2218c-cafc-4e24-886f-77bfffb5254a.jsonl:62), [不発 transcript:63](/home/SFC/tanab/.claude/projects/-home-SFC-tanab-github-izanagi--claude-worktrees-s8b-c22-launch-cert/d0d2218c-cafc-4e24-886f-77bfffb5254a.jsonl:63), [2.1.212 対照 transcript:9](/home/SFC/tanab/.claude/projects/-home-SFC-tanab--claude-jobs-9b2bec65-tmp-hookprobe/50aedebc-0c7c-422a-be7b-6492cda1e40c.jsonl:9), 提案: 2.1.212 で daemon/background session を新規作成し、同じ project settings・同じ model 欠落 payload を再試験する。可能なら 2.1.211/2.1.212 × bg/headless の 2×2 を取る。原因確定までは「2.1.211 の bg session で不発を観測。原因未分離」とだけ記録する}

{severity: must-fix, タイトル: 対照実験は guard の enforcement positive control になっていない, 攻撃シナリオ: 対照は絶対パスの logger hookを使い、Agent input に `model:"haiku"` を含めている。これは matcher がイベントを観測できることしか証明せず、repo の `$CLAUDE_PROJECT_DIR/hooks/guard_agent.py` が起動して exit 2 を返し、child spawn を阻止できることは証明しない。Agent hook workerだけ `$CLAUDE_PROJECT_DIR` を失う仮説も残る, 根拠: [.claude/settings.json:35](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.claude/settings.json:35), [.claude/settings.json:39](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.claude/settings.json:39), [hookprobe settings:5](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/hookprobe/.claude/settings.json:5), [hookprobe settings:7](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/hookprobe/.claude/settings.json:7), [test_hooks.py:733](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_hooks.py:733), [test_hooks.py:757](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_hooks.py:757), [test_hooks.py:782](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_hooks.py:782), 提案: 対照を repo の実 command と model 欠落 input で行い、(a) exit 2 が親へ返る、(b) async child artifact/notification が生成されない、の両方を確認する。catch-all logger は絶対パスで併設し、「イベント無し」と「command 起動失敗」を分離する}

{severity: must-fix, タイトル: worktree 起因仮説は棄却できるが、現プランはその重要事実を落としている, 攻撃シナリオ: worktree の project-dir 解決を原因候補として追い続ける一方、実際の不発プローブは main checkout cwd で行われ、`EnterWorktree` は約4分後だった。誤った環境記述を failures/memory に固定すると、再現手順が別物になる, 根拠: [不発 transcript:62](/home/SFC/tanab/.claude/projects/-home-SFC-tanab-github-izanagi--claude-worktrees-s8b-c22-launch-cert/d0d2218c-cafc-4e24-886f-77bfffb5254a.jsonl:62), [EnterWorktree:126](/home/SFC/tanab/.claude/projects/-home-SFC-tanab-github-izanagi--claude-worktrees-s8b-c22-launch-cert/d0d2218c-cafc-4e24-886f-77bfffb5254a.jsonl:126), [handoff:26](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-18-s8b-c22-launch-cert.md:26), 提案: 観測表に `version / entrypoint / sessionKind / cwd / settings source / model key / hook command / spawn結果` を必須列として残す。今回の worktree 仮説は refuted と明記する}

{severity: must-fix, タイトル: 「repo 側で取れる機械的防衛は無い」は偽, 攻撃シナリオ: PreToolUse が再び欠落すれば、現在は prompt/memory だけで fable 子を止められない。しかし repoまたは bg launcher には、Agent 全面 deny、脆弱 surface の foreground 化、subagent model の安全な fallback設定という別の機械点がある, 根拠: [.claude/settings.json:5](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.claude/settings.json:5), [guard_agent.py:25](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/hooks/guard_agent.py:25), [guard_agent.py:116](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/hooks/guard_agent.py:116), [hooks/README.md:114](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/hooks/README.md:114), 提案: 原因確定までは bg surface を fail-closed にし、`permissions.deny: ["Agent"]` または launcher の `--disallowedTools Agent` を候補にする。可用性を優先するなら bg launcher限定で `CLAUDE_CODE_SUBAGENT_MODEL=sonnet` を検討できるが、これは invocation/frontmatter より優先されるため全子を同モデルに上書きする副作用を明記し、必ず実測する。foreground 運用へ切り替えられる場合は `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` も候補。公式仕様上、Agent deny と model 解決順位は [permissions](https://code.claude.com/docs/en/permissions)・[subagents](https://code.claude.com/docs/en/sub-agents) に存在する}

{severity: should-fix, タイトル: 別 lifecycle hook は予防ではなく検知・封じ込めにしかならない, 攻撃シナリオ: `SubagentStart` や `SubagentStop` を第二の拒否点と数えると、spawn・モデル消費後のイベントを事前防壁として誤記する。既存 guard_bash/read/write も各自の tool eventしか見ず、Agent 呼び出しを側面検査できない, 根拠: [guard_write.py:62](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/hooks/guard_write.py:62), [guard_read.py:44](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/hooks/guard_read.py:44), [guard_agent.py:74](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/hooks/guard_agent.py:74), [hooks/README.md:116](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/hooks/README.md:116), 提案: `SubagentStart` は非 blockingかつ model field無し、`SubagentStop` と `PostToolUse:Agent` は事後なので enforcement と数えない。ただし絶対パス loggerによる `SubagentStart`/`PostToolUse` telemetry は、「spawn は起きたが PreToolUse だけ欠落」を機械検出する補助線として有効。公式 hook 能力表も [Hooks reference](https://code.claude.com/docs/en/hooks) と整合する}

{severity: must-fix, タイトル: docs-only の「恒久対応」は failures ledger 自身の契約を満たさない, 攻撃シナリオ: README・failures・memoryだけを追加して「環境別対照実験を行う」と宣言しても、次の runtime 導入者が実行しなければ再び恒真な防壁になる。特に現行テストは settings の文字列存在と hook script直叩きだけで、runtime dispatchを検査しない, 根拠: [.consult-c22-plan-v1.md:93](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:93), [docs/failures.md:10](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:10), [docs/failures.md:12](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:12), [docs/failures.md:14](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:14), [docs/failures.md:88](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:88), [docs/failures.md:154](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/failures.md:154), 提案: 新エントリの型タグは少なくとも `[恒真ゲート] [テスト代表性]`。原因がversion driftと確定した場合だけ `[ドリフト]` を追加する。恒久対応は checked-in runtime probe、または bg launcher の fail-closed preflightへのポインタにする。今回は docs-onlyを維持するなら「恒久対応未実装・再現条件調査中」と正直に残す}

{severity: should-fix, タイトル: README と memory に blanket な「bg セッションでは効かない」を書くと即座に腐る, 攻撃シナリオ: 2.1.212で修復済み、または2.1.211 daemon固有だった場合、全 bg sessionを恒久的に危険扱いし、不要な Agent denyや過剰なモデル固定を続ける。一方で別 entrypointの本当の穴を見逃す, 根拠: [hooks/README.md:10](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/hooks/README.md:10), [hooks/README.md:95](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/hooks/README.md:95), [.consult-c22-plan-v1.md:94](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.consult-c22-plan-v1.md:94), 提案: READMEには「観測済み事実」「未分離の候補」「再検証条件」を分ける。memoryは規律だけに留め、特定version/surfaceの状態正本にしない。hook 4冒頭の「止める」も「PreToolUse が配送される surface では止める」と限定する}

対抗仮説の裁定は次のとおりです。

- matcher の大小文字: 現設定と transcript の tool名はいずれも `Agent`。主因候補としては弱い。
- worktree project-dir変化: 不発が worktree進入前なので refuted。
- user/local settings上書き: 実機の user settingsに hooks無し、main checkoutの local settingsにも permission allowしかなく、`disableAllHooks`無し。さらに同sessionで guard_bash発火のため、全hook無効化説は弱い。
- settings読み込み優先順位: 静的ファイル上の衝突は見つからないが、失敗sessionの `/hooks`・`/status` または debug logによる active source確認がないため、runtime証明までは未達。
- 残る有力候補: 2.1.211 bg daemon固有、bg `sessionKind`固有、Agent hook command実行時の環境/`CLAUDE_PROJECT_DIR`差、または PreToolUse配送欠落。

Q-7への直接回答: 「無い」と断定してはいけません。別 lifecycle hookに同等の事前拒否点はありませんが、Agent全面deny、脆弱surfaceのforeground化、安全な subagent model fallback、runtime preflightという機械的防衛はあります。`SubagentStart`/`SubagentStop` は検知用であって予防ではありません。

レーンAの裁定: 不発という観測事象は real。ただし「repo配線は正しく、bgハーネスの非同期 Agent が PreToolUseを通さない」「コード変更不要で文書化のみ」という結論は要追加実験です。
## §7 付録 — 親プラン v1 全文 (相談 4 本の攻撃対象。§6 の行番号引用の対象)

    # C2-2 launch certificate 結線 + guard_agent 既知限界 — 実装プラン v1 (敵対相談用ドラフト)
    
    このファイルは相談用の一時ドラフト (untracked、commit しない)。正本ポインタ:
    - worklog (7) residual: 「C2-2 launch certificate は素体のみ — 発行の結線 + verifier の lineage 照合は
      floor 実走 wave の blocking 前提」 (docs/worklog.md)
    - 結線注記: orchestrator/campaign/s8b_floor_campaign.py:884-935 (scaffolding 3 関数) / 1706-1710
      (run_campaign の official 拒否直後の C2-2 前提条件コメント)
    - verifier 側不実装の明記: orchestrator/campaign/s8b_ratified_freeze.py:1254-1260 (launch_validate docstring)
    - 裁定: output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md §3 C2-2 行 (516) / §4 項 4 (565) /
      §5 (i)(ii)(viii)。cert フィールド = {v1 hash, clean-scan digest, protocol sha256, UTC, run id}、
      official 開始時 create-only 発行、journal が cert hash を束縛、closure は cert 起点 lineage から導出。
      closure↔cert を紐付ける具体的検証手順は文書上未確定 (= 本プランの実装解釈)
    - スコープ規律 (同 §冒頭 8-10 行): machinery + テストのみ。実 approval record / active pointer /
      v2 世代 file / protocol JSON の実凍結・発効なし。official 拒否 (CLI main 2030-2036 + core
      run_campaign 1711-1715 の二重) は不変
    
    ## レーン B-I: 発行側結線 (s8b_floor_campaign.py)
    
    - **D-1** `_official_launch_preflight(root, run_dir, *, v1_freeze_sha256, protocol_sha256, now_fn,
      campaign_run_id) -> str` を新設: clean_scan_digest(root) → build_launch_certificate(...) →
      issue_launch_certificate(run_dir / "launch_certificate.json", cert) → cert bytes sha256 を返す
    - **D-2** run_campaign fresh 分岐 (1777-1794) で run_dir 作成直後・build_cells の**前**に
      `cert_sha = _official_launch_preflight(...) if mode == "official" else None`。
      v1_freeze_sha256 = freeze_sha256 (1746-1753 で protocol の freeze.sha256 と照合済みの値)、
      campaign_run_id = run_dir.name、started_utc = now_fn().isoformat()
    - **D-3** _Runner に cert_sha (optional) を渡し、fresh の campaign-start record (1290-1300) に
      official のときのみ `"launch_certificate_sha256": cert_sha` を追加。pilot は従来どおりキー無し。
      JOURNAL_SCHEMA は bump しない (official journal は世界にまだ 1 つも存在しないため互換性問題なし)
    - **D-4** resume: _verify_resume_journal (1925-1995) を拡張 — mode == "official" なら campaign-start に
      launch_certificate_sha256 必須 + run_dir/launch_certificate.json 実在 + bytes sha 一致。
      pilot の campaign-start に同キーがあれば拒否 (mode 混線検出)
    - **D-5** 無条件 official 拒否 (1711-1715) を `_assert_official_permitted(mode)` へ抽出 (無条件 raise の
      まま意味不変)。テストはこの 1 点だけを monkeypatch して dormant official 経路を統合テストする。
      CLI 拒否と将来の F6a 承認 machinery は独立防壁として不変
    
    **Q-1** D-5 のテスト seam (monkeypatch 可能な関数抽出) は防壁の弱体化か? 代替 = seam なしで helper
    単体テストのみ (結線コード自体は一度も実行されない = 恒真保証リスク)。どちらが正しいか。
    **Q-2** clean_scan_digest の root は実リポジトリ。将来の official 実走時、凍結済み protocol JSON
    (Lane J builder 出力) や過去 campaign 出力・v2 世代 file 自体が conjunction hit して cert 発行不能に
    ならないか? s8b_holdout_freeze の match convention / _is_excluded と、closure 宣言済みファイルの
    扱い (clean scan は hit 0 を要求 — 宣言済み hit の存在と矛盾しないか) を検査せよ。
    
    ## レーン B-II: 検証側 (s8b_ratified_freeze.launch_validate 拡張)
    
    - **D-6** 到達経路: 新 header field は §4-2 exact 列挙により追加不可 → ratified.floor_source blob
      (= result artifact、read_floor_source_blob 1146-1164 で G tree から取得) を parse し、wall_ledger
      (assemble_result 1492-1495 が campaign-start record を全フィールドごと収録) の campaign-start
      ちょうど 1 件から launch_certificate_sha256 を得る
    - **D-7** floor_source は s8b-floor-result/v2 として parse でき mode == "official" であることを要求
      (無条件強制。Q-5 参照)
    - **D-8** cert blob の所在 = dirname(floor_source.path) + "/launch_certificate.json" を G tree から
      _blob_at_or_fail で読取。検査: bytes sha256 == wall_ledger の launch_certificate_sha256 /
      strict parse / schema == LAUNCH_CERT_SCHEMA / v1_freeze_sha256 == V1_FREEZE_SHA256 定数 /
      protocol_sha256 == result の protocol_sha256 / campaign_run_id == basename(dirname(floor_source.path))
    - **D-9** lineage 順序条件 (実装解釈、§5 追認リストへ (ix) として追加提案): cert path の導入 commit
      (_immutable_introductions 322-347 で取得) を anchor とし、measurement_closure 各 entry の導入
      commit が「anchor と同一 commit または anchor の子孫」であることを要求。根拠: cert の clean scan
      hit-0 が発行時点で hit を生むファイルの非存在を証明するため、closure entry が cert より古い履歴で
      導入されていれば矛盾 (未申告先行測定の再現)
    - **D-10** 拒否 reason code: "launch-certificate-missing" / "launch-certificate-binding-mismatch" /
      "launch-certificate-field-mismatch" / "closure-predates-certificate" / "floor-source-not-official"
    
    **Q-3** 現 assemble_result は eligible_for_refreeze を定数 False で書く (1501-1504)。将来 official 化の
    際この定数はどうなるべきで、launch_validate は eligible_for_refreeze を検査すべきか?
    **Q-4** D-9 で「同一 commit」を許す設計 (campaign 出力一括 commit を想定) は正しいか。merge 由来の
    複数導入 (_immutable_introductions は集合を返す) はどう裁くべきか。
    **Q-5** cert 検証は無条件強制 (提案) か、floor_source が result artifact として parse できる場合のみか。
    無条件なら既存 fixture (build_valid_semantic_g1 の floor_source = stub、test_s8b_ratified_freeze.py
    187-267) は floor_source_bytes 拡張点で全面更新 + closure ファイルの導入位置を cert 後へ再配置。
    条件付きは stub を差した bypass が成立し fail-open。
    **Q-6** §5-(i) measurement_closure schema / (ii) 世代導入 commit 機械制約はユーザー追認待ち。本実装は
    スキーマを変更せず検証を追加するのみだが、追認待ち領域への先回りとして越権になる部分はないか。
    
    ## レーン B-III: テスト計画
    
    - 発行側: seam monkeypatch + scan/measure stub で official dormant 経路統合テスト — cert create-only
      発行 / campaign-start 束縛 / resume 再検証 / scan hit 時は build 前 refuse (zero side effects) /
      pilot 不変 (キー無し)。既存 official 拒否テスト (486-, zero-side-effect) は seam 抽出後も不変で緑
    - 検証側攻撃 matrix (test_s8b_ratified_verify.py へ): binding mismatch / cert 不在 / schema 不正 /
      v1 hash 不一致 / protocol sha 不一致 / run id 不一致 / closure-predates-certificate / campaign-start
      にキー無し / wall_ledger の campaign-start 0 件・2 件 / happy path
    - 変異スポットチェック: D-9 祖先条件を外す → 攻撃テスト赤 / D-8 binding 照合を外す → 赤 (恒真防止)
    
    ## レーン A: guard_agent 既知限界の文書化 (コード変更なし)
    
    事実 (本セッション実測): (1) model 未指定 Agent 呼び出しが本 bg セッションで素通り、同セッションで
    guard_bash は発火。(2) hook 単体は手動 stdin で正しく exit 2。(3) 対照実験: 使い捨てプロジェクト +
    headless claude 2.1.212 で、matcher なし・matcher "Agent" 完全一致の両方で PreToolUse が
    tool_name "Agent" で発火。(4) 現行公式 docs は matcher/tool_name とも "Agent"、hooks 設定は
    live-reload。結論: repo 配線は正しく、不発は bg ハーネスの非同期 Agent ツールが PreToolUse を
    通さないことによる環境固有の穴。
    
    - 変更: hooks/README.md hook 4 節へ既知限界追記 / docs/failures.md 新エントリ (「発火しない防壁」は
      導入時に環境別対照実験で発火条件を確定する、を恒久対応に) / memory subagent-model-economy 追記
      (bg セッションでは機械防壁が効かず規律のみが防衛) / worklog (8) 次の一手 1 の消化
    **Q-7** repo 側で他に取れる機械的防衛はあるか (無いなら「無い」と断定してよいか)。
    
    ## 進め方 (このセッション)
    
    プラン → codex 並列敵対相談 (本ファイル + repo を read-only で) → 親裁定 → codex 並列実行
    (worktree 内 workspace-write) → claude opus 並列レビュー → 必要なら codex 再投げ → 親検算
    (全 suite + check_docs + 変異スポット) → AI-Agent trailer 付き commit (push はユーザー引き渡し)。
    子エージェント/codex 拘束: 作業ツリー巻き戻し系 git コマンド (stash/restore/reset/checkout -- 等) 禁止。
