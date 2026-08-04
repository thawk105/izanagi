# [T-428] 段 4 裁定 — 所見の real/refuted、プラン v2、変異事前登録

日付: 2026-08-04。裁定者 = 親。入力 = s1-brief.md、s2 plan (357 行)、s3 敵対 2 レンズ
(A=正しさ境界 40 行、B=整合・実効性 36 行、いずれも NO-GO)。
lens 逐語 = 本 dir の stage2-plan.md / stage3-lensA.md / stage3-lensB.md。

## 1. 所見裁定 (全件 real。refuted 0 件)

| # | 所見 | 裁定 | 採否・行き先 |
|---|---|---|---|
| A1/B6 | binding は replay/admission で mask↔source の意味結合を再証明できない (恒真ゲート化) | real | **採用 (主張縮小)**。binding の主張を「producer-time 意味整合 (hole の byte-exact 照合) + replay/admission の構造・commitment 検証」に固定し、WAL 全面改竄への暗号学的防御とは名乗らない (D149 決定 (2) と同じ「順序・範囲の正直な主張」)。mask と predicate_sha256 の**連動改変**は検出射程外と新 D に明記。32 点凍結 witness 表 (mask→source_bytes_sha256) は freeze 族の新設なので実装せず**裁定パッケージ W6** |
| A2 | crash 後 resume が WAL topology を自己破壊 (二重 build_start) | real | **scope 外 (既存欠陥)**。本 wave の差分と独立に現存する。**新規タスク起票 (W1)**。本 wave では crash-after-start の実 WAL 境界テストを追加しない (既存欠陥を本 wave の赤にしない、DW-O18) |
| A3/B2 | 唯一経路が sink で強制されず caller 慣習に依存 | real | **採用**。(i) E-loop driver は IR 型のみ保持し、typed materializer が内部で emit する。(ii) 汎用 `quarantine()` は trigger marker に限り **32 正準文字列への byte-exact membership** を強制する (署名は §3)。機械 caller 3 箇所 (recon sweep / S1 direct / extime 較正) は正準述語を渡しており通過する — 段 5 で 3 caller の実述語を検証し、非正準が見つかれば停止して報告 |
| A4/B9 | positive marker だけでは downgrade / 偽造 / pre-T428 未追跡物を分類できず、P3 (非遡及) と原則拒否が矛盾 | real | **採用 (P3 v2)**。分類式を閉じる: exact overlay → exact snapshot → post-policy。post-policy のうち **proposal 駆動 trigger campaign (E-loop / 8c trial)** だけに marker + binding を要求し、機械 sweep (D 段偵察) は proposal 経路を持たないため要求対象外と明記。**遡及被害ゼロを列挙で実証済み**: 既存 trigger 系 campaign = E-loop 1 件 (`p3-s8a-trigger-loop-…-3f72ecd5`、exact overlay-denied 維持) + 機械 sweep 6 件 (要求対象外)。将来発見時は exact hash の個別 grandfather 登録のみ (包括 legacy 化禁止)。cutoff 権限の一般則は**裁定パッケージ W2 に含めず新 D に手続として記録** |
| A5/B10 | raw mask の WAL/provenance/report 永続化は I3・D121 P2 と衝突 (32 点辞書で predicate_sha も可逆) | real | **採用 (commitment 分離)**。raw binding (mask, predicate_sha256, source, nonce) は**専用 WAL record** に置き、report へ複写される build_start payload と provenance entry には `binding_commitment = sha256(canonical(binding) ∥ nonce)` **のみ**を置く。nonce により 32 点辞書攻撃を封じる。formal report schema の top-level receipt 化と recipient 閉集合の最終設計は D121 P2 の裁定事項 — **裁定パッケージ W4** |
| A6 | 「32 点」「11111=stock」「00000=全素通し」の意味が不正確 | real | **採用 (用語固定)**。「32 encodings」「00000 = kUnset のみ true の退化点」「11111 = ident_all (真 stock ではない — kInsertNode/kScanNode 非含・flag=1 overhead)」を新 D・fixture・docstring に固定。fixture は `true;` をやめ正準文字列へ |
| A7 | axis 帰属を loader/constructor が検証しない | real | **採用**。dataclass `__post_init__` + loader + sink で axis 一致を再検査。combined loader / direct construction の負テスト追加 |
| A8 | source-null attempt の reason / 後続 payload が閉じておらず偽 verifier red を注入可能 | real | **採用**。source-null で許す reason と後続 stage を閉集合化し、receiptless attempt への verify/bench payload を拒否 |
| A9 | 32 点の src_token / variant_id 一意性が未検証 | real | **採用 (nit)**。fixture source で 32 predicate・32 source bytes・32 variant_id の相互一意性を列挙検査 |
| A10/B3 | agent 契約変更の承認と pin 独立レビューの構造 | real | **採用 (手続分離)**。権限根拠 = ユーザーが `/dev-wave T-428` で起動した task 本文 (「consumer 閉包 … proposal schema」を明示) と D149 決定 (6)。遮断設計 (tools なし・構造化出力) は不変。**pin 更新は 子 A に持たせない**: 子 A が agent 本文を変更 → 親が独立レビュー (証跡を insights へ) → 別所有の小単位が manifest/adapter/review_ledger を更新。最終確認は**報告でユーザーへ明示 (W7)** |
| A-P1 | SourceEvidence の ABA / mixed snapshot | real | **scope 外 (既存)**。P2 主張から除外済み (上記 A1 の主張縮小に含む)。**裁定パッケージ W2** |
| A-P2 | 非 E-loop の trigger materializer は raw C++ を受理し続ける | real | **採用 (境界明記) + 部分緩和**。sink membership (A3) により非正準 raw C++ は機械経路でも落ちる。P1 の主張は「**E 段候補表現** (proposal 経路) が 5-bit IR に閉じる」と明記し、機械所有経路 (recon/S1) は候補表現の外と新 D に記録。emitter への完全移行は別 D96 単位 — 起票のみ (W3) |
| B1 | consumer 列挙漏れ (テスト 3 + 文書 2) | real | **採用**。`test_p3_exploration_namespace.py` / `test_p3_build_authority_cli.py` / `test_claude_transport.py` の fixture 追随、`docs/phase3-s8c-autonomous-trial-runbook.md` / `docs/axis-onboarding.md` の記述更新を編集対象へ追加。無編集回帰 = `test_s8b_floor_campaign.py`、`tools/check_codex_agents.py`、`test_reflux_ir.py`、`test_diff_quarantine.py` |
| B4 | 子 A/B の依存が並列投入可能な形でない | real | **採用**。先行単位 P (binding module 骨格 + loop/pipeline signature) を最初に完了させ、所有パス限定 patch を両子へ展開してから A ∥ B 並列 (DW-S05-A)。テスト所有を実装所有へ揃える |
| B5 | schema mode の負側・軸間汚染の変異が未登録 | real | **採用**。mode を閉じた enum にし unknown 拒否。§4 の変異 M-C1〜C4 と mode×auditor×value 負例を追加 |
| B7 | provenance/report は実効 gate でなく生成時コピーのみ | real | **採用 (部分)**。admission が provenance entry の commitment を WAL と照合する検証を追加。report は commitment 残存テスト + 「nested payload は観測コピー」の明記。formal schema 変更は W4 |
| B8 | campaign ID epoch 変更が 8c 全 campaign の freshness/budget を新品化 | real | **採用 (緩和) + 一部裁定へ**。直接 trigger と 8c 全 workload の旧/新 ID を固定するテスト、旧 path へ書かない assert、marker 省略変異を追加。cap-lift FAIL と `MAX_APPROVED_GENERATIONS=1` は epoch に依らず不変 (D114 は campaign 単位 cap で、新 campaign の 1-generation 運転は従来から許可)。**epoch による予算リセットの一般則は裁定パッケージ W5** |
| B11 | D96 充足の立証形式が不足、直接追記は spool 違反 | real | **採用**。新 D は **spool fragment** で書き land の fold で採番 (プラン §6 の直接追記を却下)。境界表は 5 受理面 (proposal / projection mode / role schema / artifact epoch / report 契約) を正負例つきで列挙 |
| B12 | failures 型タグ 5 種の再発経路 | real | **採用**。§5 の対応表を受入・レビュー表として使う |

## 2. プラン v2 (s2 plan からの差分)

1. **binding の置き場を分離**: raw binding + nonce = 専用 WAL record (`trigger_binding`)。
   build_start payload / provenance entry = `binding_commitment` のみ。layer3 report へは
   payload 複写経由で commitment だけが渡る (raw mask は report・provenance に**出ない**)
2. **汎用 quarantine に trigger membership**: marker_id が trigger のとき implementation が
   32 正準文字列 (emit_predicate の全出力) のいずれかと byte-exact 一致しなければ拒否。
   sort/backoff marker は無変更 (I5)
3. **E-loop は typed materializer**: driver は `TriggerGateIR` を保持し、materializer 内部で
   emit。coder 由来文字列は parse_wire 以後存在しない
4. **admission 分類式**: proposal 駆動 trigger campaign だけに marker+binding 要求。
   機械 sweep は対象外。unknown/mixed → 拒否。exact 歴史 2 分類は不変
5. **子分割**: 子 P (先行: trigger_gate_binding.py + signatures) → 子 A (受理経路 + schema +
   driver + agent 本文 + それらのテスト) ∥ 子 B (binding 実装 + wal/admission/replay/pipeline +
   それらのテスト)。pin 更新 (manifest/adapter/review_ledger) は親レビュー後の独立小単位 子 C。
   docs (runbook/axis-onboarding/新 D fragment) = 親
6. **主張の固定**: 本 wave 後に名乗るのは「D121 P1 のうち E 段候補表現の閉包 + D149 emitter 監査
   = **P1 充足 (E 段 proposal 経路について)**」。機械所有経路・P2 以降は含めない
7. その他は s2 plan §1〜§7 のとおり (wire-only cutover、epoch marker、境界テスト群、
   32 点 golden 照合)

## 3. gate 禁止の署名と正例 (DW-S04)

- **署名 1**: `load_proposal_file(path)` は `coder` キー集合が `{axis, wire}` ∪
  `{justification, confidence}` に一致しない、または `parse_wire(coder["wire"])` が
  `RefluxIRError` のとき拒否する。**正例**: `{"axis": "silo-backoff-trigger-gating",
  "wire": "10100", "justification": "...", "confidence": "medium"}` は受理される
- **署名 2**: `quarantine(sub, impl, marker_id=MARKER_ID(trigger), ...)` は
  `impl.strip()` が `{emit_predicate(TriggerGateIR(m)).strip() for m in range(32)}` に
  byte-exact で含まれないとき拒否する。**正例**: `emit_predicate(TriggerGateIR(mask=20))`
  の出力は受理される (recon sweep の正準述語も同値で通過)
- **署名 3**: replay/admission は proposal 駆動 trigger campaign の各 build_start に対し、
  対応する `trigger_binding` record の存在・mask 範囲・predicate_sha256 再計算一致・
  source 欄と admission receipt の一致・commitment 一致のいずれかが欠けるとき campaign を
  拒否する。**正例**: 子 B が作る fixture campaign (canonical binding 完備) は受理される

## 4. 変異事前登録 (DW-M01、B-057)

受理集合縮小 wave のため**過剰拒否を検出する正例 3 件**を含む。各変異は実装後・matrix 前に
「手前に同一入力を拒否する検査がないこと」「赤理由が単一であること」をコードで確認してから
走らせる (確認不能なら登録を外し実効 gate へ再照準、F28)。

| ID | 変異 (位置) | 期待 kill |
|---|---|---|
| M-A1 | loader に `implementation` fallback を復活 | old-key 拒否テスト |
| M-A2 | wire 検査の長さ/文字/型を緩和 | invalid corpus テスト |
| M-A3 | bit 順を MSB-first へ反転 | bit-order テスト + 32 golden |
| M-A4 | preview だけ raw 入力を通す | preview/run 同一性テスト |
| M-A5 | driver が emitter を迂回し raw C++ を渡す | sink membership テスト |
| M-A6 | unattended parser だけ旧 schema | autonomous trial テスト |
| M-B1 | build_start の binding 省略 | replay/admission 欠落テスト |
| M-B2 | mask 単独または sha 単独の改変 | 再計算 validator テスト |
| M-B3 | binding source と receipt の比較を削除 | source 不一致テスト |
| M-B4 | replay の binding 検証を削除 | replay tamper テスト |
| M-B5 | records_by_stage だけ検証迂回 | duplicate/records テスト |
| M-B6 | admission の binding 検証を削除 | admission tamper テスト |
| M-B7 | marker 欠落を一律 legacy 扱い | unproven-history テスト |
| M-B8 | mask を variant_id preimage へ追加 | variant-ID 契約テスト |
| M-B9 | provenance/report が binding を独立再導出 | WAL との exact 一致テスト |
| M-C1 | schema mode の typo で旧 schema へ fail-open | unknown-mode 拒否テスト |
| M-C2 | sort marker の campaign に binding を要求/付与 | 軸分離テスト |
| M-C3 | axis 不一致 proposal の受理 | axis 再検証テスト |
| M-C4 | mask に bool を許す | strict 型テスト |
| P+1 (正例) | 正準 wire "10100" の end-to-end 受理 | 受理されること (過剰拒否検出) |
| P+2 (正例) | recon 正準述語の汎用 sink 通過 | 受理されること |
| P+3 (正例) | sort 軸 proposal の従来どおりの受理 | 受理されること |

**登録しない変異**: mask と predicate_sha256 の**連動**改変 (整合を保った両替え) —
witness なしでは構造検証を通る。検出射程外として新 D に明記 (W6 裁定まで)。

## 5. failures 型タグ → positive control 対応表 (B12)

| 型タグ | 再発経路 | control (所有) |
|---|---|---|
| 捏造/幻覚 | 「全 consumer 閉包済み」の過大主張 | B1 の 4 分類列挙を新 D 境界表に写す (親) |
| 恒真ゲート | mode typo fail-open / 連動改変を試さない緑 | M-C1 登録 + 連動改変の非主張明記 (親) |
| セッション死・救出 | 子 P/A/B の途中孤児差分 | 先行単位 patch 展開 + 所有パス限定統合 (親) |
| 権限逸脱 | pin の自己承認 | 子 A から pin 所有を剥奪、親レビュー証跡必須 (親) |
| ドリフト | s8c runbook / axis-onboarding の旧記述残存 | B1 の文書 2 件を編集対象化 (親) |

## 6. 裁定パッケージ (ユーザーへ返す)

- **W1** = crash-resume の WAL topology 自己破壊 (A2、既存欠陥)。新規タスク起票
- **W2** = SourceEvidence の ABA / mixed snapshot (A-P1、既存)。immutable checkout /
  content-addressed snapshot の要否
- **W3** = 機械所有 trigger materializer (recon/S1) の emitter 完全移行 (別 D96 単位)
- **W4** = formal report schema への binding receipt 追加と recipient 閉集合 (D121 P2 の一部)
- **W5** = campaign ID epoch 変更による予算リセットの一般則
- **W6** = 32 点凍結 witness 表 (mask→source_bytes_sha256) による連動改変検出 (freeze 族新設)
- **W7** = coder agent 契約の wire 化 (本 wave で実施済みの確認。遮断設計不変・親レビュー証跡あり)

## 7. 段 5・6 への指示骨子

- 子 P → (子 A ∥ 子 B) → 親レビュー → 子 C (pin) の順。全子 Codex `role=author`、
  `reasoning=high`、`sandbox=workspace-write`、DW-S05-A/B/C 契約全文を prompt に含める
- 段 6 は敵対レビュー 2 本 (レンズ: 正しさ境界 / 閉包・回帰) + fix + 変異 matrix + 受入全走
- 受入 = `tools/run_tests.py` 全走 + `check_docs` + `check_codex_agents` + provenance 監査
