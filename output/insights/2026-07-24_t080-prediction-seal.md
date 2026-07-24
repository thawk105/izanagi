# T-080 selector 予測封印 — 執行 wave 材料レポート (2026-07-24)

科学レーン第 2 手の AI 側工程。protocol 実凍結 (c8cbd17、ユーザー手番) の後、selector の
**盲検予測を封印**した。手順正本 = worklog 2026-07-23 (1) (iii)。機構は wave2 (D79) で
配線済みで、本 wave はそれを **実行** した (新規 production code 変更なし)。

逐語 = [`2026-07-24_t080-prediction-seal-verbatim.md`]、変異台帳 =
[`2026-07-24_t080-prediction-seal-mutation-ledger.json`]。

## 成果 commit

- **commit A = 7766407** 「pin floor_protocol.json into FROZEN_MANIFEST」— seal 前。
  承認定数から凍結済みの floor_protocol.json (774B / sha256 261cec1c…) を exact
  path→sha256 manifest へ pin。件数 8→9。内容は盲検のため未読、sha256 のみ束縛。
- **commit B = 82803d6d** 「seal selector 予測封印」— seal + 証拠 pin。commit A の clean
  HEAD を pre_oracle_head として claude-headless で 4 セル実走し封印。prediction +
  selector-runs 13 を FROZEN_MANIFEST へ bytes pin。件数 9→23。
  (初回 commit 00b9faa を provenance 訂正のため message-only amend、tree 同一。)

## 封印の事実

- **seal**: rc=0 / status:sealed。pre_oracle_head=7766407 (実行時 HEAD 完全一致検査)。
  protocol は承認定数からの canonical 再導出と HEAD blob を照合、holdout freeze は v1
  trust root (315b1e…) 照合、書込後 reload verify、selector-runs 宣言照合まで seal 内で
  通過。body_sha256=69c7ad3e…、selector_predictions.json file sha=5884c83f…、
  selector_basis_sha256=779c6396… (レビューが独立再構成で一致確認)。
- **6 行 prediction** = 4 agent cell (claude-opus-4-8 / effort=high、role selector-8b) +
  2 static cell。**missing ゼロ** (全セル解決)、R3 の null 行なし。agent 選択 = c03/c04、
  static = c06 (upstream_defaults) の 2 行。derangement は rr20↔rr80 の固定点なし全単射。
- **盲検 (P5)**: selector 入力 = descriptor (ycsb/records/threads 射影) + 固定6候補
  (opaque choice_id c01-c06) のみ。payload top-level は 3 キー固定 + forbidden-key scan で
  protocol 値・floor 測定値・holdout 名・arm・binding 対応表・winner・measured_tps の混入を
  構造的に拒否。neutral cwd・tools/MCP なし・env allowlist。レビュー 2 本が実 payload/raw/
  envelope を読み混入なしを確認。
- **証拠鎖**: protocol(261cec1c…) → prediction → journal → 12 cell files が commit B 後に
  全 bytes anchor。B^==A、pre_oracle_head==A、envelope.result==raw (4/4)、
  choice/rationale/session が raw==journal==prediction で一致 (レビュー独立確認)。

## 事前敵対相談の裁定 (P1-P6、逐語 段3)

- **P1 real**: commit B で prediction + selector-runs 全件を FROZEN_MANIFEST に pin
  (正常4セルで 23 件)。ratified_freeze は manifest を書かない consumer。payload 直接 pin が
  ratified の payload 非再照合の穴 (レビュー相談 B2) を塞ぐ。
- **P2 real** (ancestry は refuted): pre_oracle_head は HEAD 完全一致検査。commit A/B 分離。
- **P3 refuted (= ratified 批准 run 不要)**: seal 自身が reload verify + 宣言照合まで担う。
  ratified loader は active v2 pointer 前提で、commit B 直後は no-active が正常。floor 実測後
  launch lane の工程。
- **P4 real**: git add 全 write-path = prediction + selector-runs/{journal, payload_*,
  envelope_*, raw_*}。.lock/tmp/cell-*(fixture 名)/floor_protocol.json は非対象。
- **P5 real** (盲検維持、条件付き): コード上は盲検。残存境界 = claude 実行体
  (~/.local/bin/claude、journal の e1207175… と一致) と HOME/global memory に floor 情報が
  無いこと。コードだけでは無条件保証不可 → 運用境界として honor (floor 内容未読・どこにも
  floor 情報を置いていない)。
- **P6 real** (verify 実効的、限定): step3 verify は prediction 意味検証 (body hash・basis・
  canonical cell・binding 再導出・raw strict reparse) として非恒真。ただし journal/protocol
  blob/seal 実走真正性の証明ではない。

## 敵対レビュー (段6) の所見と処置

- **R1/F2 (両レビュー収束、real/regressed) → FIX 済み**: commit B の headless selector
  provenance を `model=not-exposed; reasoning=not-exposed` で記録していたが、role selector-8b
  は model=opus/effort=high 固定・runner は --effort high 明示・journal modelUsage は
  claude-opus-4-8。正確値 `model=claude-opus-4-8; reasoning=high; scope=selector-predictions`
  へ message-only amend (00b9faa→82803d6d、tree 同一、check_ai_provenance 320 緑)。
- **R2 (real/partial) → 裁定パッケージ PKG へ繰延**: test_manifest_shape_is_exact は exact
  key-set を検査せず同数 path 差し替えを検出しない。本 commit の証拠鎖は 23/23 独立 recompute
  + HEAD blob 照合 + 三集合一致で担保。durable な key-set/lineage assert 化は別 wave
  (条件: 本 commit OID 82803d6d 保持・下流 ratification 前に導入)。両レビューが繰延を妥当と裁定。
- **R3/F1 (real/partial) = 既知残余**: 初回導入の bundle は「実走」と「後付け自己整合生成」を
  commit 内だけでは暗号学的に区別できない (D80 の初回導入捏造 residual と同型)。本 wave の実走は
  genuine (時系列・session ID 4 一意・token/duration/cost 実在・実行体 bytes 一致・raw==envelope)。
- **R4/A4 (real/partial) = 既知残余**: HOME/global memory の盲検境界 (上記 P5 と同一)。
- **親ハンク = refuted/closed**: 両レビューが 23/23 SHA 一致・実ファイル集合==manifest key
  集合==journal 宣言・phantom 0・件数内訳一致を独立確認。転記/件数/pin 過不足なし。
  `2026-07-16_s8b-selector-leak-control-case.md` は「未実走」設計事例で pin 対象外 (穴でない)。
- **consumer 波及 = refuted/closed**: official preflight (固定4+journal 動的導出)・namespace
  exact 検査 (H tree 再検証)・launch cert (preflight から再生成)・generator hash pin (対象
  source 無変更)・V1 trust root いずれも更新不要。

## 変異 (執行ゲート裏取り)

FROZEN_MANIFEST 凍結ゲートは sha256 直接 recompute-compare で多層マスク構造なし。単層変異 2 件:
MUT-1 (prediction sha 1 文字改変 → match test 赤)・MUT-2 (件数 23→22 → shape test 赤) とも
**KILLED**、復元を read_text 内容一致で検証。SURVIVED 0 / injection failed 0。台帳が正本。

## 受入

- 中心テスト (frozen_artifacts / prediction_runner / selector_freeze / selector_input) 96 passed。
- 全走 **2878 passed / 18 skipped / 0 failed** (前 baseline と一致・回帰ゼロ)。
- check_docs / check_codex_agents / check_ai_provenance (320 件) 緑。

## 残余と次の一手

- **PKG (R2)**: manifest exact key-set / lineage の durable assert 化。本 commit OID 82803d6d
  保持、下流 ratification (floor 実測後 launch lane) より前に導入する条件で繰延。
- **既知残余**: 初回導入捏造 (R3/F1、D80 同型)・HOME 盲検境界 (R4/A4)。floor 実測前の統合 E2E
  ([T-011]) で lineage 照合として扱う。
- floor 実測は本封印の後 (Pegasus 単独)。予測は封印済みで、floor 実測が予測を変えられない盲検が成立。
