# 段 1 brief — [T-410] sort 軸の構造化 integrity witness

## scope

verifier に **sort 軸 (P 行 = permutation 保存違反) の構造化 integrity witness** を新設する。
`verdict` / `certified` / `Integrity.clean()` の判定は 1 ビットも変えない (受理集合不変)。
他軸 (X 行 = lock 被覆、I 行 = write intent) の witness 化は scope 外 — D138 決定 (8) が
「witness 契約と axis adapter の意味契約は軸ごとに別に書く」と定めているため。
C++ 側 (trace emit) は無改変。P6 / generalized cut / cap-lift へは結線しない (D138 決定 (7))。

## 確定済みユーザー裁定 (前提)

- [T-244] 裁定 U5 (2026-08-04): sort 軸の構造化 integrity witness を新設する。所有は [T-410]。
  理由 = 現行は整数 counter と自然文 notes だけで「同じ理由で危険」の同値関係が書けない。
- D138 決定 (4): P6 の入力は `CycleWitness ∪ IntegrityWitness` の閉じた和、未知 kind は fail-closed。
- D138 決定 (7): P6 本体は実装しない。本 wave は witness の**表現だけ**を作り、判定へ結線しない。
- D138 決定 (8): 軸ごとに別契約。cycle witness と integrity witness を単一署名で扱わない。
- D138 未確定事項に「sort 軸の同値関係」が明記されている → 本 wave が定義する ((P1))。

## 不変条件 (破ったら停止)

1. **受理集合不変** — 全入力で `verdict` / `certified` / `clean()` の値が現行と一致する (規律 2)。
2. **後方互換** — 既存 12 キーの integrity dict と `permutation_violations` の int 値は不変。
3. **観測者効果なし** — 変更は verifier (Python) 側のみ。C++ / trace-disabled build に影響しない (規律 1)。
4. **凍結 bytes 不変** — FROZEN_MANIFEST 23 件は非対象 (実測済)。producer を再生成しない。
5. **consumer 閉包を残さない** — 下記 3 系統すべてを同じ commit で追随させる。

## 実測した consumer 閉包 (DW-O09/O13、一次資料)

- `orchestrator/codex_roles/policy.py` — evidence schema の `_exact_keys(result, …)` と
  `_exact_keys(result["integrity"], …12 キー)`。**proof chain の schema gate。**
- `orchestrator/campaign/silo_ladder_rung1.py` — result 級と integrity 級の同型 exact-key 検査。
- `orchestrator/campaign/t152_write_intent_coverage.py` の `_integrity_counters_zero` —
  **`clean`/`notes` 以外の全キーに `type(value) is int` を要求する**。非 int の witness キーを
  integrity 直下へ足すと、この driver は**実走時にだけ**赤くなる (単体テストは自前 fixture ゆえ緑のまま)。
  = 潜在的 consumer 取り残し経路。
- `orchestrator/campaign/s5_permutation_coverage.py` — witness が無いため**生 trace を自前で
  再パースして `p_reasons` を作っている**。本件の実害の現物。
- `orchestrator/critic/digest.py` — integrity を素通しするだけ (形状仮定なし)。

## 成果物の形

`orchestrator/verifier/` に構造化 witness 型と生成経路、`report.py` での JSON 露出、上記 consumer の
追随、純増検出力のテスト。docs は spool fragment (worklog / decisions)。

## 親の provisional 裁定 (すべて段 3 の攻撃対象)

- **(P1) 同値関係 = reason 種別のみ** (`size-changed` / `rcdptr-set-changed`)。thid・出現順・件数は
  同値キーに入れない (schedule 由来のノイズであり variant の性質ではない)。D138 が未確定としており割れうる。
- **(P2) 配置 = `integrity` dict 内の新キー**。`result` 直下でなく integrity 内に置き、exact-key を
  更新する。t152 の int 前提を壊すため、その追随を必須にする。
- **(P3) 受入 = s5 driver の E2E 再走はしない**。site=`PEGASUS_LOGIN` / `refuses_heavy_work=True` を
  実測済。代替は (a) trace レベル positive control、(b) 既存 s5 artifact の `p_reasons`
  (erase 249252 / swap 879025) を witness が再現することの照合。
- **(P0) DW-G04 の発火 gate は満たす**。発火する既存 artifact =
  `output/env/linux-baremetal/calibration/s5_permutation_coverage.json` (all_pass=true、
  erase/swap で非ゼロ)。P6 が未実装でも、s5 driver の parse 重複という現在進行形の consumer が実在する。

## 成果物影響 (DW-G05)

実装しない場合、sort 軸の失敗は「整数 1 個 + 自然文 1 本」のままで、reason 内訳は prose からしか
取れない。結果として材料レポートと critic の次手帰属は、**要素欠落 (size-changed) と同一性入替
(rcdptr-set-changed) という別種の危険を 1 個の整数へ潰す**か、生 trace を再パースする consumer を
増やすかの二択になる (s5 driver が現に後者)。certified 選択と受理集合は本 wave では不変。

## 既存被覆と純増検出力 (DW-S01)

既存 = `orchestrator/tests/test_verifier.py` の P 行 positive control 4 本 (indeterminate 化 /
沈黙 control / 2 reason parse + **note 文字列**の assert / txn ブロック間出現)。
純増 = (i) reason 別内訳の**機械可読**性、(ii) 同値キーの安定性、(iii) evidence schema の追随、
(iv) `_integrity_counters_zero` 型の consumer が新キーで壊れないこと、(v) 受理集合不変の pin。

## 追記 (段 2 起動後に親が実測。段 3 のレンズは本節も攻撃対象に含める)

- **witness の実在する読み手は `orchestrator/critic/digest.py` の rejection 描画である。**
  同所は integrity カウンタを dict repr で、`notes` を 1 行ずつ LLM prompt へ描画する
  (= sort 軸の reason 内訳が次手生成へ届く唯一の経路が自然文であるという規律 3 の欠落の現物)。
- さらに同所には `lock_coverage_violations` と `write_intent_violations` にだけ
  **「分類: 機構欠落型」の行**があり、`permutation_violations` には**無い**。
  sort 軸だけが分類なしで次手へ渡っている。
- **(P4) 親の provisional 裁定 = critic digest の sort 軸描画を scope に含める。**
  witness を作っても読む層が 1 つも変わらなければ「実装したふり」になるため
  (DW-S03 の「成果物が実際に効く全層」)。ただし critic の**判定**は変えない (描画のみ)。
- **規律 6 の攻撃面**: P 行の reason は trace 由来文字列であり、そのまま critic prompt へ届く。
  witness が raw string を構造化フィールドとして持つとき、語彙を閉じるか・注入面が広がらないかを
  段 3 レンズ A で検査させる。

## 並列分割方針

正しさ防壁 (verifier) に触るため**軽量版ではない** (DW-C00)。段 2 = codex プラン起草 1 本。
段 3 = 敵対相談 2 レンズ並列 (A = 受理集合不変性と consumer 閉包、B = 同値関係の意味と D138 契約整合)。
段 5 = 実装子 1 本 (編集面が verifier + consumer + test で相互依存が強く分割の利が無い)。
段 6 = 敵対レビュー 2 本並列。
