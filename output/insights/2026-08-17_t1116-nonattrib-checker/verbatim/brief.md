# 段 1 brief — [T-1116] 受入の非帰属 checker を実測で確定し、残る穴を閉じる

wave: `dev-wave-t1116-nonattrib-checker` / 2026-08-17 / branch
`worktree-dev-wave-t1116-nonattrib-checker` / base `5a19b8ab`

## 確定済みユーザー裁定 (2 件・どちらも有効)

- **R1 = [T-1116] 択 (2)** (`docs/archive/worklog-phase3-0816-574.md:510-514`):
  「対象 wave より前から main に存在する entry」を批准と弱く再定義し、AI による 2 wave
  事前登録が残ることを明示的に受容する。択の全文は同 `-561.md:451-466`。
- **R2 = 2026-08-16 のユーザー裁定** (`git log -1 8a2b735b` の body 冒頭):
  「確率的なフレークで受入全走を何度も無駄にする構造は全てのセッションに対して許さない。」

## 親が実測した前提 (投げ文の 2 点を訂正)

- **8a2b735b は R1 の実装ではない。** R1 相当の分類 (`main 単独再走が赤 → non-attributable`) は
  8a2b735b **より前から**存在した (`git show 8a2b735b` の削除行
  `"attributable" if rerun_rcs[nodeid] == 0 else "non-attributable"`)。
  8a2b735b が足したのは第 3 分類 `flake` で、その根拠は R2 である。
- **効果は未実測。** 受領証は 44 file (投げ文の 48 を訂正)、赤 88 件 (同 100 を訂正)、
  status 全件 `attributable-red`、新 schema field (`main_rerun_rc`/`wave_rerun_rc`) を持つ
  受領証 0 件、tested_main が 8a2b735b を含む受領証 0 件。
- **稼働 wave との重複ゼロ。** dev-wave-t650-lease-release の branch 差分に
  `tools/check_acceptance_reds.py` / `orchestrator/tests/test_check_acceptance_reds.py` は無い。
- **land の構造的制約 (実測)。** `tools/dev_wave_land.py:660-680` は `non-attributable-only`
  経路で `tested_main:tools/check_acceptance_reds.py` と `tested_tip:` の blob 一致を要求する
  ([T-1131])。**checker を編集する本 wave は child-green の受入走行でしか land できない。**
  したがって自分の受入走行から分類の証拠は取れない (緑では checker が起動しない)。
- **受領証 root field は exact pin。** `tools/dev_wave_wait.py:2762-2776` が 9 field の
  `set(receipt) == expected_fields` を要求する。root field を 1 つ足すだけで待ち手が壊れる。

## 変更面の実アンカー

| anchor | 内容 |
|---|---|
| `tools/check_acceptance_reds.py:1349-1401` | `_probe_nodes` の 3 分類 (main probe → 条件付き wave probe) |
| `tools/check_acceptance_reds.py:1556-1582` | rc/status 決定と `nodes` の `classification` 構築 |
| `tools/check_acceptance_reds.py:22` | `_SCHEMA_VERSION = "izanagi-acceptance-red-check/v1"` |
| `tools/dev_wave_wait.py:240,2762-2790` | 受領証 schema pin と root field exact 集合 |
| `tools/dev_wave_land.py:607-680` | `non-attributable-only` 受理と checker blob 一致要求 |
| `orchestrator/tests/test_check_acceptance_reds.py:533,571,614,649` | 3 分類の既存単体被覆 |

## 既存被覆と純増検出力 (性質で検索)

性質「単独再走 2 点 (main / wave tip) の組で赤を分類する」は :533 / :571 / :614 / :649 で
被覆済み。**未被覆の性質は「その赤が wave の差分から到達しうるか」** — 現行の入力は
単独再走 rc 2 個だけで、差分そのものを一切見ない。本 wave の純増検出力はここに限る。

## scope と provisional 裁定 (すべて攻撃対象)

- **(P1)** R1 は registry 形では既に不要になっており、`main 単独赤 → non-attributable` という
  live probe が R1 の弱い批准をより強く (事前登録の余地なしで) 実現している。
  したがって [T-1116] は registry を作らずに終端できる。
  成果物影響 = 終端しないと [T-1116] が P1 のまま残り、次タスク選定を塞ぎ続ける。
- **(P2)** 残る穴は `flake` 分類の**過剰受理**である。8a2b735b の正当化は commit body で
  「本 wave の 20 commit は同 file に 1 行も触れていない」と述べるのに、**実装はその条件を
  一切検査しない**。全走でだけ再現する赤が wave の差分起因 (順序依存・グローバル状態汚染) でも
  単独再走は main / wave tip 双方で緑になり、`flake` へ落ちて land を通る。
  成果物影響 = 差分起因で壊れたテストを抱えた tip が main へ入り、以後の受入全走が
  その赤を「main 単独でも赤」= `non-attributable` として恒久的に赦す連鎖が起きる。
- **(P3)** 閉じ方の第一候補: `flake` へ落とす条件に
  「`tested_main..wave_tip` の差分が当該 node の test file を触っていない」を加える。
  触っているなら `attributable` に留める。**受理集合を縮める向き**であり規律 2 に整合する。
  差分到達可能性の完全な写像 ([T-389] の免除述語) は未実装なので、直接 path 接触に限る。
  成果物影響 = 未実装なら (P2) の穴がそのまま残る。
- **(P4)** 受領証の root field は増やさない。判定根拠は `nodes[]` 要素内の field
  (例: `wave_touched_path`) で表す。増やす設計になるなら `dev_wave_wait.py` /
  `dev_wave_land.py` の同時更新が必須で scope が 3 file へ広がるため、段 4 で再裁定する。

## 不変条件

- 規律 2: 受理集合を広げる変更をしない。(P3) は縮める向きに限る。
- R2 を壊さない: wave が触っていない file のフレークは引き続き `flake` として通す。
- `--wave-tip` 必須・probe worktree の identity/fingerprint 検査・rc が 0/1 以外の
  `InvalidInput` 停止・受理 2 経路 (`child-green` / `non-attributable-only`) を変えない。
- 実装面は Codex `role=author` が書く (D95)。親は docs 本文のみ。

## 成果物の形

`tools/check_acceptance_reds.py` + `orchestrator/tests/test_check_acceptance_reds.py` の 2 file、
変異 matrix (過剰受理の正例を必ず含む)、`output/insights/2026-08-17_t1116-nonattrib-checker/`、
spool fragment (worklog / decisions)。

## 並列分割方針

編集面は 2 file で一枚岩。段 5 は Codex author 1 単位。段 3 と段 6 レビューは 2 レンズ並列。

## brief v2 — 段 2 の実測で (P2) が覆った (2026-08-17 02:05 JST)

段 2 プランが指摘し、親が独立に実測して成立を確認した。

- **`flake` は land を通らない。通るどころか受領証すら発行されない。**
  `tools/dev_wave_wait.py:2803-2812` は checker 受領証の**全 node** に
  `set(node) == {"classification", "nodeid", "rerun_rc"}` かつ
  `classification == "non-attributable"` を要求する。8a2b735b が作る `flake` node は
  5 field で `classification="flake"` なので `_StageFailure` になる。
  実測: probe2 の実受領証を同述語にかけると REJECT。
  文字列 `flake` の出現数は `tools/dev_wave_wait.py` = 0、`tools/dev_wave_land.py` = 0、
  `orchestrator/tests/test_dev_wave_wait.py` = 0、`orchestrator/tests/test_dev_wave_land.py` = 0。
- したがって **8a2b735b は end-to-end で R2 を果たしていない。** checker 層だけが直り、
  消費層が取り残された。commit body は「既存の呼び手は壊れない」を root field と `--wave-tip`
  flag だけで確認しており、node 形の exact 検査を見落としている。
  これは規律 6 が監査発火条件に挙げる **consumer 取り残し**の型である。
- **(P2) の「過剰受理」は現状では成立しない**(全 flake が拒否されるため穴になりようがない)。
  正しい問題は**過少受理**であり、R2 が 1 度も発効していないことである。
  投げ文の「受理集合を広げる方向の変更」という枠付けが正しく、親 brief が誤っていた。

### 訂正後の scope

1. **消費層に `flake` を教える** (`tools/dev_wave_wait.py`)。**受理集合を広げる。**
   成果物影響 = これなしでは R2 が永久に発効せず、フレーク 1 件で受入全走が捨てられ続ける。
2. **(P3) を同時に入れる** (`tools/check_acceptance_reds.py`)。拡大を
   「wave がその test file を触っていない flake」に限定する。**受理集合を縮める向き**。
   成果物影響 = これなしでは差分起因の全走限定赤が land を通る。
   実測: 過去 89 赤のうち wave が当該 file を触っていたのは 4 件 (4.5%) だけで、
   R2 の救済の 95.5% は残る。
3. `tools/dev_wave_land.py` は外側受領証の `red_nodeids` しか読まないので変更不要 —
   **段 3 で独立に裏取りする**。
4. 変異事前登録には**過剰受理を検出する正例** (投げ文の必須制約) と、
   **過剰拒否を検出する正例** (`DW-M01`、縮小側) の**両方**を入れる。

編集面は 4 file (production 2 + test 2)。稼働 11 wave すべてと重複ゼロを実測済み (02:05 JST)。
base は `7c83eeac` (main へ ff 済み、submodule も recursive 同期済み)。

## 実測環境

Pegasus。テストは `python3 tools/run_tests.py` (受入形)、焦点走は同 runner の file 選択走。
段 1 の生死実験は実履歴 log への checker 直接適用 (`run_probe2.sh`)。
