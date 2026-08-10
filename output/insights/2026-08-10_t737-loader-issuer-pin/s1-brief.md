# [T-737] 段 1 brief — 量化縮退の loader / issuer integration pin

正本: `output/insights/2026-08-09_t673-transition-quantifier-ruling/RULING-PACKAGE.md` §5 選択肢 G
(2026-08-09 t673 RULING-PACKAGE)。起票文は `docs/worklog.md` (367) の [T-737] 項。
wave tip = `7a84b638` / branch `worktree-dev-wave-t737-loader-issuer-pin`。

## scope

`_validate_activation_transition` の 2 つの量化点を、**private gate 直叩きではなく実際に効く
2 層の入口から** M > N の合成 registry で通す integration pin を追加する。

- 量化点 G = `orchestrator/campaign/env_contract_activation.py:275` `for successor in successor_rows:`
  (exactly +1 判定と `changed` 構築の走査範囲)
- 量化点 P = 同 `:300` `for predecessor, successor in changed:` (successor 述語の適用範囲)
- 層 1 = production loader: `env_contract.py:519 _load_authority_snapshot` →
  `env_contract_activation.py:479 load_activation_state` → `:332 validate_activation_records` → gate
- 層 2 = 発行 tool: `tools/issue_env_contract_activation.py:155 main()` → 同 `:206`

**scope 外:** production コードの編集 (選択肢 D の走査完全性 guard は [T-673] §5 の別項で未裁定)、
A / A′ / B1 / B2 / C1 / C3 の候補採用、hypothesis 依存の導入。

## 確定済みユーザー裁定

- 2026-08-10 rulings §56 (5): 選択肢 G を [T-737] として起票可 (worklog 368 に記録済み)。
- 同 §5 D: 本番編集禁止は [T-673] wave の指示であり、G は「pin は別途必要」とだけ言う。
  本 wave も production 無編集を守る (下記不変条件)。

## 実測 (brief 前に取った。子の申告ではない)

- baseline: `tools/run_tests.py orchestrator/tests/test_env_contract_activation.py --force-dispatch`
  = **77 passed / 4.38 秒 / rc=0** (Pegasus dispatch request `900440.nqsv`、tip `7a84b638`)。
- **既存被覆を性質で検索した結果 (機構名でなく「どの入口から / 何 env で / 何を拒否するか」で数えた):**
  - 遷移違反を拒否する既存テストはすべて `validate_activation_records` へ in-memory record を渡す形
    (`_validate` helper、`orchestrator/tests/test_env_contract_activation.py:157`)。env 数の上限は
    `FOUR_ENV_CATALOG` の **4**。
  - `load_activation_state` を入口にする既存テストは 3 件だけで、内容は「実 repo の正例」
    (`:343`) と「述語引数の型検査」(`:1356` 以下) のみ。**遷移違反を拒否する例は 0 件。**
  - 発行 tool `main()` を入口にする既存テストは 5 件。拒否例は「全 env で述語 False」(`:2071`) と
    「全 env 据置 no-op」(`:2117`) の 2 つで、いずれも実 registry の **2 env**。
    changed が 1 本しかないため、`changed[:1]` は素通りする。
  - `ec.current_activation_state()` を入口にする既存テストは tail 削除・suffix 注入・kwargs 同一性の
    3 件で、遷移違反の深い index を突く例は 0 件。
- **純増検出力:** 層 1・層 2 の入口から、量化点 G と P それぞれについて frontier を
  **(現状 0〜1) → (M-1)** へ上げる。private gate 直叩きの候補群 (frontier 3〜63) とは別軸で、
  「gate が本当にその 2 層で発火する」ことを固定する。
- test file への外部 pin は 0 件 (`grep -rn "test_env_contract_activation" --include=*.py`、
  自ファイル以外 hit なし)。plain-runner meta-test は既存 `_run()` で充足済み。

## 不変条件

1. `orchestrator/campaign/env_contract_activation.py` と `env_contract.py` を **1 byte も編集しない**
   (blob SHA-256 が `test_t671_source_binding.py` 等で pin されている)。`tools/issue_env_contract_activation.py`
   も編集しない (並行 wave `dev-wave-t720-import-unify` が同 file の `main()` 冒頭を所有)。
2. 既存テストの期待値を変更しない。受理集合 (production の受理・拒否挙動) を変えない。
3. 合成 env_tag は実 env (`linux-baremetal` / `pegasus`) と字面で衝突させない (D75、同名識別子の二義化禁止)。
4. 凍結成果物の bytes を変えない。producer 出力なし。

## 成果物の形

`orchestrator/tests/test_env_contract_activation.py` への追記 (新規ファイルを作らない)。

- 層 1 × 量化点 G: M env の合成 registry で **最後の env_tag** だけ generation +2 → `load_activation_state`
  が `ActivationRecordError("... exactly +1 でない ...")` で拒否する。
- 層 1 × 量化点 P: M env 全部が +1 で、**最後の changed env** だけ述語 False → 同 loader が拒否する。
- 層 2 × 量化点 G / P: 同じ 2 形を `issuer.main(argv)` から通し、rc=1 かつ **record が publish されない**
  ことを固定する (`00000002.json` 不在)。
- 正例 1 本: M env 全部 +1・述語 True が両層で受理される (過剰拒否の検出)。

## 判断が割れうる前提 (親の provisional 裁定であり攻撃対象)

- **(P1) M = 65。** 候補群の最良 frontier 63 を跨ぐ最小の切りの良い値。`[:N]` は N ≥ M で
  equivalent mutation になるため frontier は常に M-1 であり、**族は閉じない**。
  コストは record 2 本 × 65 行で数 KB、gate は O(M)。
- **(P2) 層 1 の入口は `activation.load_activation_state`。** `ec.current_activation_state()` まで
  上げると合成 contract に対して `_verify_entry_calibration` が走り、実 calibration ファイルが要る。
  既存 `test_production_loader_passes_source_head_constants_to_leaf` (`:1544`) が
  「production loader が同じ catalog / 述語 / head を identity で渡す」を固定しているので、
  合成すれば層 1 は閉じるとみなす。**この合成が成立するかはレンズで攻撃対象。**
- **(P3) 層 2 は既存の `_load_issue_tool()` + `ec` への monkeypatch seam を踏襲する** (DW-O14: 正規の
  注入 seam を先に探した結果、`GENERATIONS` / `_REGISTERED_CONTRACT_CATALOG` /
  `current_activation_state` / `_repository_root` / `_ACTIVATION_DIRECTORY` / `is_valid_successor` が
  既存テストで使われている seam である)。`_is_valid_activation_successor` (adapter) は patch しない。
- **(P4) 変異事前登録は `[:N]` を両量化点へ 1 本ずつ + 両層同時 mask 1 本。** 詳細は段 4。

## 成果物影響 (DW-G05)

放置した場合: env registry が 3 env 以上へ育った時点で、量化点 G / P の縮退が **loader と発行 tool の
両方で素通り**する。素通りすると (a) 未登録世代へ飛んだ contract を active とする activation record が
`current_activation_state()` から返り、certified 選択が参照する contract 世代が承認外へずれる、
(b) 発行 tool がその record を publish して authority directory に残る。どちらも「certified 選択の
proof chain が承認済み世代を指す」という受理集合の前提を壊す。本 pin はその経路を M-1 まで固定する。

## 並列分割方針

編集面は 1 ファイルだけなので実装子は 1 単位 (所有 = `orchestrator/tests/test_env_contract_activation.py`)。
段 3 のレンズ 2 本と段 6 のレビュー 2 本は並列。

## 受入・実測の環境

Pegasus。単体確認・変異は `tools/run_tests.py <対象> --force-dispatch`、受入全走は
`tools/wave_land_window.py claim` 取得後に背景投入。login node で pytest を直接起動しない
(hook が拒否する)。
