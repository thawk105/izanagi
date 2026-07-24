# [T-080] post-R テスト負債 11 件 fix — 逐語・変異台帳の凍結

- 日付: 2026-07-24
- branch: worktree-dev-wave-ruling-ac、code commit = c9d71fd (基準 8bec195)
- 種別: test-only 復旧 wave (production・凍結成果物・output/ 配下は無変更)
- 変異台帳の機械可読版 = `2026-07-24_t080-postr-mutation-ledger.json`

## 背景

R commit (8bec195) で legacy freeze migration receipt が発効した結果、
`orchestrator/tests/test_s8b_oracle_driver.py` の 11 node が決定論的に赤化した。
worklog 2026-07-22 (10) の「post-R 受入 = 全走 0 failed」は R が存在し得ない時点の
未検証予測であり、[T-067]「real-repo 2 状態 exact 化の残余」の負債が顕在化した形。
親環境とユーザー環境で赤集合が node 単位一致 = 負荷起因でない。

## 根本原因と fix (E1-E6)

- **(a)(b) stub-free/full-valid e2e 10 件**: fixture `_t080_stub_free_e2e_repo` が
  `output/` を丸ごと copytree する際、発効済み receipt (`output/t080-migration/` 配下) を
  fixture 基底 commit へ混入させ、fixture 内に R 履歴が無いため receipt state が
  never-issued でなく invalid に化けて子の draft が入口拒否されていた。
  - **E1**: copytree の ignore callable で t080-migration 直下の receipt/draft basename
    だけを除外 (basename は `migration.RECEIPT_REL`/`DRAFT_REL` から導出、literal 禁止)
  - **E2**: 基底 commit 直後に never-issued guard (`inspect_receipt_history(check_worktree=True)`)
    を追加。未使用の `rev-parse` を置換。混入を単一理由で検出可能に
- **(c) G12 二重 subprocess 1 件**: 子が `run_block(root=実ROOT)` を呼び、入口の receipt
  解決 (実測 13.8s) が `communicate(timeout=10)` を決定論的に超過。
  - **E3/E4**: 子の root を receipt-free な最小 hermetic git repo (SHA-1・署名無効・改行固定・
    空 1 commit) へ差し替え、never-issued 早期 return 経路に載せて **13.8s→0.49s**。
    子先頭の実 `verify_manifest(root=ROOT)` は receipt 非依存なので不変
  - **E5**: 子プロセス回収を全例外経路 (部分生成含む) + 個別保護へ堅牢化 (レビュー R2-1 の fix)
- **E6**: never-issued generator tamper の gate 検査を exact 化。真の refusal 集合は **4 件**
  (holdout generator + known-axes legacy source drift + floor-null + budget-null)。
  legacy source drift は T-080 移行の存在理由そのもの (D75 §14 の repin 対象) で never-issued
  常在。その path/hash は無関係な正当編集で変わる**揮発診断 payload** のため prefix + 件数
  のみ固定し期待へ焼き込まない (親・相談 A・静的分析はこの 4 件目を数え落としており、実装子の
  実走観測で判明 → E6v2 再裁定)

## 検証フロー逐語 (結論のみ凍結)

- **段 2 プラン (codex max)**: 4 編集で完結。brief 補正 2 点 — (i) 子の verify_manifest は 1 回
  実走で receipt 非依存、(ii) MUT-1 は 11 node 全部が guard 赤。P3 強化: L1197 の再解決は
  epoch TOCTOU 防壁で cache 化は正しさを弱める
- **段 3 相談 2 本 (max、両 NO-GO)**:
  - A (正しさ境界): L2178 の refusal を exact 化せよ / M1 の「11 node 新検出」は虚偽 (新規は
    1 node のみ) / M2 (root 戻し) は環境依存 timeout で semantic kill でない → kill 集計外へ
  - B (整合・実効性): timeout 時の子残留を親 finally で回収せよ (BLOCKER) / 記録後の repo scan
    invariant 再走が欠落 (BLOCKER) / hermetic root の git 設定固定 / P3「許容確定」撤回
- **段 4 裁定**: 13 所見中 12 採用。M2 を **MUT-2 (production O_EXCL 一時変異)** へ差し替え、
  root 戻しは REC-1 (kill 集計外) へ降格。B-6 (output/ 全コピー) のみ親 override (G3 単発 +
  10 golden 差分リスク → 残余記録)
- **段 6 レビュー 2 本**: R1 = GO (must-fix 0)。R2 = NO-GO 2 所見 —
  - R2-1 (BLOCKER, E5 部分回収) = 採用 fix (processes を try 内 + finally 個別保護)
  - R2-2 (MAJOR, E3 git env 非 hermetic) = 不採用。主根拠は **本 wave scope 外 + 発火条件つき
    残余明記** (焦点再レビューの精緻化を採用: G3 は補助根拠であって単独根拠でない。E3 固有でなく
    既存 `_run_git` fixture 族すべての性質)
  - 焦点再レビュー = GO: R2-1 closed (`except Exception: pass` は cleanup 中の新規例外のみ捕捉し
    本体 assert を偽緑化しない構造を確認)、R2-2 partial=残余、regressed 0

## 変異 matrix (本走 = HEAD c9d71fd、全 restored=True)

| ID | 層 | 期待方向 | 結果 | 帰属 |
|---|---|---|---|---|
| MUT-1 | test (E1 ignore 無効化) | 11 node guard 単一理由赤 | 11 failed、全て never-issued guard Assertion | **KILLED** |
| MUT-2 | production (campaign_claim O_EXCL 除去) | G12 statuses assert 破れ | `['claim-won','claim-won'] == ['claim-won','refused']` 単独赤 | **KILLED** (fail-open 検出) |
| REC-1 | test (root 戻し) | G12 timeout | TimeoutExpired (10.8s) | **kill 集計外** (環境束縛 recovery evidence) |

### MUT-1 差分実証 (テスト強化 wave の「買った検出力」)

- **基準 8bec195** (ignore 無し = 混入あり + guard 無し) で同 11 node: **10 failed + 1 passed**。
  passed = `never_issued_generator_tamper` (issue_receipt=False、基準で緑)
- **新版 HEAD + MUT-1** (ignore=None): **11 failed** (全 guard 単一理由)
- **差 = `never_issued_generator_tamper` が緑→赤 = 新規検出 1 node** (issue_receipt=False 経路の
  混入を新版だけが検出)。残り 10 = **診断局所化** (基準は子 draft の returncode assert 経由で
  診断が子 stderr に散る / 新版は fixture 構築時 guard で単一理由局所化)

### MUT-2 の帰属注記

fail-closed 排他 (O_EXCL) → fail-open を修復後テストが検出。基準 8bec195 では同 node が timeout で
claim 層に到達できず未検出 = **hermetic 化 (E3/E4) が検出力を回復した**。statuses assert が glob
assert (`len(...glob("*.claim"))==1`) より先行するため単一理由 (glob は claim path 同一で不変)。

## 受入

- 全走 (統合 commit 前、xdist) = **2878 passed / 18 skipped / 0 failed** (baseline 一致、赤 11→緑、
  退行 0)。check_ai_provenance 316 件違反なし
- production 受理集合は不変。テスト状態の変更は G12 入力の active-valid→never-issued 化と E6
  exact 化のみ

## 発火条件つき残余 (本 wave では不採用/未解決、将来トリガ付き)

1. **R2-2 (E3/`_run_git` の git env 非 hermetic)**: GIT_DIR/GIT_INDEX_FILE/GIT_CONFIG_*/
   templateDir/hooksPath 等の異常 env がある環境では G12 (および既存 `_run_git` fixture 族全体) が
   Git setup error へ逸れ、MUT-2/REC-1 の可搬的再現性が条件付きになる。GIT_DIR 未設定前提は本 wave
   全走 2878 緑が実証。**トリガ**: env 汚染で fixture 族が赤化する事例が別 producer で 2 件再現したら
   (G3) `_run_git` の env 固定を族一般化として設計裁定する
2. **gate latency (P3)**: `verify_receipt(実ROOT)` = 13.8s は receipt history の reachable commit
   全体 rev-list + commit ごと batch 照合で、履歴長に伴い増える。30 分 per-attempt cap は build/
   verify/bench 用で receipt gate latency の上限ではない。launch あたり ≤2 回 + 人間 CLI のみで
   現時点許容だが「閉じた問題」ではない。**トリガ**: gate 単体 >60s、または launch の反復運用化。
   cache/増分 epoch 検査は L1197 TOCTOU 防壁を壊さない production 設計択一 (G4 未発火)
3. **B-6 (output/ 全コピー)**: E1 後も fixture は receipt/draft 以外の output/ 配下 (campaigns・
   insights 等) を丸ごと copytree する。holdout scan は tracked/untracked 双方を列挙するため、
   他セッションの output 書込みや三軸文字列を含む一時記録が混入すると 11 node が無関係に赤化しうる。
   本 wave では G3 単発 + 10 golden 差分リスクで allowlist 化を見送り。**トリガ**: 同型汚染が別 fixture
   で再発したら allowlist/snapshot 化

## anomaly (規律 6 — 信頼境界)

本 wave 終盤の複数 turn で、task-notification 内および tool 出力内に、system・user メッセージを装う
文字化けテキスト (「queued message from the user」「Continue working」等) の注入が反復発生した。
いずれも正規の task-completion payload に寄生する形で、正しさゲート (変異帰属・受入判定・commit) を
歪める誘導を試みる構造だった。すべて **spoof = データであって指示でない** として無視し、実状態
(commit c9d71fd・変異 matrix・全走 2878) は一切変更していない。規律 2/3 (ゲートを緩めない・シグナルを
後付けにしない) は不変。素性の知れない入力経路 (bg job notification) からの注入という点で Jitskit/IDS
の想定攻撃面と一致。

## 監査後記 (2026-07-24、別 job c4f664a6 の独立検証・敵対監査)

前セッションの成果 (c9d71fd + 本 insight/ledger) を、`~/tmp/p1.txt` 引き継ぎのユーザー指示で消化する
にあたり独立検証・監査した。全文 = `2026-07-24_t080-postr-audit-verbatim.md`。

- **実測 (親、cwd=worktree)**: 全走 2878 passed / 18 skipped / 0 failed (受入と一致、退行 0)、
  check_ai_provenance 316 件違反なし。実状態確定で **worklog 新エントリは未作成**だった (p1.txt の
  「working tree にあるはず」と食い違い、本セッションで新規執筆)
- **敵対監査 codex 2 レンズ (gpt-5.6-sol/max/read-only、独立コンテキスト、本記録を非採用で審査)**: 両 GO・
  コード blocker 0。E3/E4 の reward-hack 疑いは early-return が `verify_receipt()` 内に閉じ、claim 競合
  (`_acquire_g12_claim`→O_EXCL) が実走することのコード追跡で否定
- **errata (コード正しさに影響せず)**: (i)「hermetic」は `_run_git` が git env を継承するため git env に
  対しては不正確 (§残余 R2-2 が既に caveat)、(ii) 本記録および commit message の「communicate(timeout=10)
  を決定論的に超過」は host 依存で過大 (ledger REC-1 は「環境束縛で高速ホストでは非成立」と正しく記載、
  prose 側の過大表現)。13.8s→0.49s 等の実測値は環境束縛で本セッションでは非再認証
- **手順 (F34)**: 後付け記録 bytes は 2878 全走の対象外だったため、docs commit **後**に
  `test_s8b_repo_scan_invariant.py` を再走して認証 closure。**minor**: E6 の inline set 判定は将来
  `_assert_exact_refusals` へ委譲推奨 (残余)
