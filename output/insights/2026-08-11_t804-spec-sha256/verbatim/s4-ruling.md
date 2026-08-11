# [T-804] 段 4 裁定 — plan v2 と変異事前登録

base main `856f4d4c`。入力 = 親 brief、段 2 plan、段 3 レンズ A (正しさ境界) / B (全層被覆)。
**両レンズとも NO-GO。** 親は下記のとおり裁定し plan v2 を確定する。

## 0. 親自身の誤りの訂正 (両レンズが独立に指摘、親が一次資料で裏取り)

1. **brief の「凍結 bytes の pin 閉包 = 影響ゼロ」は無限定には誤り (refuted)。**
   正しくは「**凍結 output bytes への影響はゼロ、test/review の pin 閉包は非ゼロ**」。
   `orchestrator/tests/test_s8b_oracle_manifest.py` の `PIN_GATE_SPEC_RAW` /
   `PIN_GATE_SPEC_SHA256` は **role 名を key にした pin** で、`artifacts` / `judge` / `report` /
   `materializer` / `outcome_stage_contract` の source SHA-256 を埋め込む。実装子 B が
   report / judge / artifacts を編集すればこの golden が動く。
   親は path のみを検索して 0 件を「pin なし」と結論した = **DW-O09 が名指しで警告する
   踏み外し方 (F30) そのもの**。brief を訂正する。
2. **run contract の「自由なのは 4 項目」は逐語では refuted。**
   定義済み 9 key の中では real だが、`_validate_run_contract` の部分集合判定と
   `copy.deepcopy(dict(...))` の全保存により **任意の余剰 key も自由**。
   なお実走時は driver が `env_tag` / contract hash / clocks を外部 authority へ束縛するため、
   この 3 つは「manifest 検証時点で自由」であって「実走まで自由」ではない。

## 1. 親 provisional 裁定の確定

| # | 裁定 | 理由 |
|---|---|---|
| P1 | **採用 (強化)** | `verify_manifest` の `approved_spec: ReviewedSpec` は required keyword、default なし、`seal_verifier` wrapper も同時更新。**加えてレンズ A 所見 4 を採用し `ReviewedSpec` を再帰 immutable 化する** (`s8b_ratified_freeze` の深い凍結と同型)。`@dataclass(frozen=True)` は属性再代入しか止めず、nested dict/list は可変のままだった |
| P2 | **採用 (条件付き)** | `8b-oracle-manifest/v1` / `8b-oracle-observations/v1` 据え置き。D288 と同 wave 系列の先例が「発行済み oracle manifest 0 件を機械確認したうえで SCHEMA_VERSION 据え置き、durable 発行後に変えるなら再発行」と決めている。**条件 = 発行 0 件の機械確認テストを本 wave で置く** (将来 durable 発行後にこの決定が黙って生き残らないようにする) |
| P3 | **撤回して差し替え** | 下記 §2 |
| P4 | **採用 (強化)** | 下記 §3 |
| P5 | **撤回** | 下記 §4 |

## 2. P3 差し替え — 判定層は「pin 比較」でなく実再検証にする

**両レンズが独立に同じ穴を指摘した (DW-G03 の独立 2 例を満たす)。**
レンズ A 所見 1 = 「pin は公開定数なので、迂回者は正しい値を手書き observations に書くだけで
新検査を満たす」。レンズ B 所見 7 = 「module 定数参照は同じ入力の判定を module 状態で変える」。
どちらも real。親の元案 (judge が `APPROVED_SPEC_SHA256` を参照して比較) は
**恒真かつ非純粋**であり採らない。

**差し替え案 (採用):**

- judge CLI (`s8b_oracle_judge.main`) に `--manifest` / freeze 解決を足し、
  **judge 自身が `load_approved_spec` → `verify_manifest` を実際に呼ぶ**。
- `judge_oracle(observations, *, verified_manifest_sha256, approved_spec_sha256)` を
  **required keyword** にする。core は純関数のまま (I/O は CLI 側)、渡し忘れは即 TypeError。
- observations の `manifest_sha256` / `spec_sha256` を、その `VerifiedManifest` の実値へ束縛する。
  一致しなければ判定不能へ倒す。
- 裁定文「driver / report / judge の**全層で再検証する**」の逐語に忠実。「記録して公開定数と
  比べる」は再検証ではない。
- 副次効果として **legacy 迂回路が閉じる** — legacy manifest は verify できないので
  certified 結論へ到達しない (親が独立に発見した「judge は `manifest_kind` を一切見ない」も同時に解消)。
- 波及は限定的 = `judge_oracle` の production caller は自身の CLI 1 箇所のみ (親が実測)。

## 3. P4 強化 — pin の向きを直す

レンズ A 所見 2 (BLOCKER) = 「AST pin が choke point を逆向きに数えている」。real。
`verify_manifest` の caller を数えても、**verify を通らない loader-only consumer** は捕まらない。
実際 `load_official_manifest` の production 呼び出しは report の 1 箇所で、legacy 分岐は
verify を通らずに observations を作る。

**採用:**

1. pin の対象を `load_official_manifest` / `load_official_observations` /
   `load_official_verdict` の **production consumer 集合**へ反転する (迂回の実際の扉)。
   `verify_manifest` の直接 caller pin は補助として残す。
2. pin test の docstring に **主張の限界を明記**する — 「直接呼び出しと module 階層の
   import alias 解決までを捕捉する。動的 `getattr` / 動的 import は捕捉しない」。
   恒真な全称主張をしない。
3. **層別 negative test は metamorphic 形にする (レンズ B 所見 3、must-fix)。**
   各層で「同じ otherwise-valid fixture の spec 一致版が**通る**」を先に固定し、
   **その 1 箇所だけ**を別 spec に変えた負例を置く。正例が無いと、`no-approved-spec` や
   fixture 不備など別理由の拒否でも negative test が緑になる。
   - manifest 層: 6 projection それぞれ
   - driver 層: gate allowed + 実行到達 ↔ 拒否、`run_block` は prepare/evaluate 0 回・
     campaign/budget/marker 不生成まで固定
   - report 層: rc=0 + spec hash 付き observations ↔ rc=2 + output 不生成。**verifier を mock しない**
   - judge 層: determinate ↔ 判定不能
4. legacy が certified 結論へ到達できないことの**統合テスト**を置く。
   legacy observations の `spec_sha256` は manifest 自己申告値をコピーせず不在にする
   (ロンダリング経路を作らない)。

## 4. P5 撤回 — 既裁定 D288 に抵触する

レンズ A 所見 6 (BLOCKER)。**real、親が D288 本文を逐語で確認した。**
D288 は「成果物の受理集合を狭める gate は共有 verifier へ置く。**生成側 generic builder の
受理集合は変えない**」と決定し、却下選択肢に「**generic builder に置く — 既存 programmatic
caller の受理集合を狭め、互換を壊す**」を明記している。
親の P5 (`_validate_run_contract` を exact-key 化) は generic builder
(`_build_manifest_from_snapshot` 経由) が使う共有 helper を変える案であり、これに抵触する。

**撤回する。** 代わりに **`verify_manifest` 内の approved spec との完全一致比較だけ**で
余剰 key の自由を閉じる (D288 の決定「gate は共有 verifier へ置く」に整合し、方向は縮小のみ)。
余剰 key 付き generic builder 入力が**引き続き受理される**ことを正例として登録する (§6 M9)。

## 5. scope 外 real 所見 → 裁定パッケージ (段 7 で作成)

1. **`s8b_verdict.judge_combined` の oracle verdict が未封印** (両レンズ、BLOCKER)。
   親が一次資料で確認 — 同じ関数の隣り合う 2 行で、予測側は `verify_prediction` →
   `VerifiedPrediction` (封印 token)、oracle 側は `load_official_verdict` (schema 名確認のみ)。
   **real だが本 wave の scope 外**と裁定する:
   - これは **spec 迂回とは別の穴** = verdict artifact 自体の偽造。manifest を一切使わずに
     成立する既存の穴で、本 wave が新設も拡大もしていない。
   - A-9 の定義は「縮小 schedule による certified 選択の直接改変」。verdict を丸ごと偽造できる者は
     manifest を触る必要がない。
   - 閉じるには sealed verdict token = 権威の設計判断。[T-805] が同型の理由で単独変更を退け
     [T-657] 権威束設計へ合流する裁定を既に受けている。
   - ただし `VerifiedPrediction` という**同ファイル内の既存 pattern** があるため実装費用は
     見た目より安い。この事実を裁定パッケージに明記する。
   - **採らない案:** verdict へ `spec_sha256` を掲載するだけの field 追加。決定台帳が
     「証拠 field を足し受理集合を変えずに掲載だけ義務付ける」を恒真化として明示的に却下している。
2. **legacy 受理そのものの廃止 / report official API を VerifiedManifest 専用にする**。
   既存契約 (`test_cli_legacy_skips_freeze_resolution` が rc=0 を要求) を変えるため
   受理集合の変更が裁定範囲を超える。[T-807] が同型の「旧 writer を狭めるか」を現状維持で
   終端した先例がある。本 wave は「legacy は certified へ到達しない」までを閉じる。
3. **official sink 全体の static/runtime 監査、動的 access の allowlist** (レンズ A 所見 2 の
   最大形)。横断的な新機構であり DW-G03 の独立 2 例要件も未充足。

## 6. 主張の限定 (本 wave が謳ってよい範囲)

**「manifest を消費する全層 (verify → driver → report → judge) で approved spec への束縛を
閉じた」までとする。** combined verdict 層は未被覆であることを worklog と insight に明記する。
**全層被覆・全チェーン被覆を主張しない。**
また `generator_versions` の比較は **defense-in-depth であって新規の受理集合縮小ではない**
(レンズ A 所見 5 = real。`_validate_generators` が両側で canonical path + 実 byte hash を
既に強制しており、安定 root では両側で異なる有効 mapping は存在しない)。

## 7. 変異事前登録 (DW-M01 / B-057、実装前)

各変異は「同じ入力を拒否する層が前後に無いこと」を親がコードで確認済み。
期待 node の完全集合は fix 後の統合 tip で再導出する (存在検査では代替しない)。

| ID | 位置 | 変異 | 単一帰属の根拠 (前後の層が同じ入力を拒否しないこと) | 期待 |
|---|---|---|---|---|
| M0 | `verify_manifest` | approved spec 照合 block を丸ごと削除 (= **wave 前の実コードの形**) | wave 前はこの入力を誰も拒否していなかった (A-9 残余そのもの) | KILLED (層別 negative 全件) |
| M1 | 同上 | schedule の deep equality だけ削除 | manifest B は自己整合 (`schedule_sha256` 再計算一致) で cell 積も同一。`n` 差は他のどの層も見ない | KILLED |
| M2 | 同上 | campaign_ids の deep equality だけ削除 | 既存検査は block と 1:1・非空・一意のみ。別 ID 集合は通る | KILLED |
| M3 | 同上 | run_contract の deep equality だけ削除 | 差分軸は `env_tag` (manifest 検証時点では形式検査のみ)。`reps`/`extime` 等の凍結定数は使わない | KILLED |
| M4 | 同上 | `spec_sha256 == approved_spec.sha256` の等値検査だけ削除 | 内容は spec A と一致・hash だけ spec B を名乗る入力。他の projection 比較は通る | KILLED |
| M5 | `verify_manifest` signature | `approved_spec=None` の default を付け、None なら spec 検査を skip (**fail-open 形**) | 既存 caller は spec を渡すので層別 negative は緑のまま。signature pin だけが捕える | KILLED (signature pin node) |
| M6 | `judge_oracle` / judge CLI | verified manifest への束縛検査を削除 | observations は自己整合。上流 report は判定に関与しない | KILLED |
| M7 | report legacy 分岐 | manifest 自己申告の `spec_sha256` を observations へコピー (**ロンダリング形**) | legacy は verify を通らないので他層が拒否しない | KILLED |
| M8 | driver `gate_check` | `verified_manifest` 注入時の再束縛を削除 (レンズ A 所見 3 の形) | 注入経路は verify を呼ばないので他層が拒否しない | KILLED |
| M9 | `verify_manifest` の spec 比較 | 比較を過剰拒否側へ倒す (`==` を同一性比較へ) | **過剰拒否の正例** — spec と完全一致する正当 manifest が拒否されることを検出する | KILLED (各層 positive control) |
| M10 | — | 余剰 key 付き generic builder 入力 (D288 の受理集合) | **正例** — 本 wave が generic builder の受理集合を狭めていないことを固定する | 変異なし・正例テストとして常時緑 |

**登録しない変異と理由:**
- `generator_versions` の deep equality 削除 — `_validate_generators` が**前段で**同じ入力を
  拒否するため単一帰属が成立しない (レンズ A 所見 5、DW-M01 の要件不成立)。
- run_contract の余剰 key 変異 — P5 撤回後は spec 完全一致比較が拒否するため、
  もともと二重拒否になり帰属が成立しない。

## 8. 実装子への分割 (plan v2)

- **A = `s8b_oracle_manifest.py` + `s8b_oracle_spec.py` + `test_s8b_oracle_manifest.py` +
  共有 spec fixture + 機械検査 (loader consumer pin / signature pin / 発行 0 件検査)**
- **B = `s8b_oracle_driver.py` + `s8b_oracle_report.py` + `s8b_oracle_judge.py` +
  `s8b_oracle_artifacts.py` + 対応 test + `test_s8b_binding_driftguards.py`**
- 収束順序: A が API・schema・fixture を確定 → B が 3 consumer と judge を実装 →
  **A が B の最終 bytes に対して `PIN_GATE_SPEC_RAW` / `PIN_GATE_SPEC_SHA256` を更新** →
  統合状態で pin と全 negative/positive を確認。
  レンズ B が「`binding_identity` に generator hash は無く A→B→A の 1 往復で収束する」ことを
  確認済み (親の循環依存懸念は **refuted**)。

## 9. 実装子への禁止事項 (レンズ B 所見 6、逐語で prompt へ入れる)

- `approved_spec` に default を置かない。
- shared fixture は official positive 経路だけに使う。legacy fixture は別管理。
- divergence test は spec A と manifest B を**明示的に分離**する。manifest に合わせて spec を
  自動生成する fixture を使ってはならない (恒真化)。
- **テストを通すために production を緩める方向へ倒してはならない。** テスト側の代役追加は
  許すが、production の fail-open 化は禁止。
- 共有 `_validate_run_contract` の受理集合を変えてはならない (D288)。
