# 段 1 brief — [T-553] s8c 事前登録の git wall-clock 予算化

- wave: `dev-wave-t553-git-budget` / branch `worktree-dev-wave-t553-git-budget`
- base: main `58d1878d`
- worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget`

## 0. 確定済みユーザー裁定 (2026-08-09、逐語は handoff)

`output/insights/2026-08-09_t553-s8c-git-timeout/package.md` の R1〜R3 に対し:

- **R1 = (a) 採る** — `GIT_TIMEOUT_SECONDS = 15.0` の固定値を、作業量比例の上限付き予算へ変える。
  レンズ A の 5 条件 (①〜⑤、下記「不変条件」) を**必須要件**とする。
- **R2 = (b)** — `git-timeout` は**環境依存の false reject** として扱い、「受理集合不変」に含めない。
  したがって本変更は正しさの変更ではなく可用性の修復である。
- **R3 = (a)** — 実 repo を読む重い git テストの xdist group 統合は**別タスクとして起票するだけ**。
  本 wave では実装しない。

## 1. scope

- **in**: `orchestrator/campaign/s8c_preregistration.py` の `_git` の wall-clock 予算。
  同モジュールの単体テスト (`orchestrator/tests/test_s8c_preregistration_core.py`)。
  invariant テスト (`orchestrator/tests/test_s8c_preregistration_invariant.py`) は⑤の確認のみ。
- **out**: xdist group 統合 (R3 = 別起票)。`tools/ruleops.py` (20 秒) と
  `orchestrator/campaign/reflux_origin_ledger.py` (30 秒) の別 timeout — 別 producer であり、
  `DW-G03` の「独立 2 例」に達しないため族一般化しない。
- **out**: `MAX_COMMITS` / `MAX_BATCH_REQUESTS` / blob byte 上限などの**量的上限は一切触らない**。

## 2. 実測した前提 (すべて本 worktree、main `58d1878d`)

- **赤 1 (provenance rc=1) は既に解消している。** `python3 tools/check_ai_provenance.py` は
  **rc=0** (`known-violations=30` / `1995 件、新規違反なし`)。worklog 342 が t682・t139 の所有と
  記録した赤で、両 wave の land により閉じた。本 wave の対象は**赤 2 のみ**である。
- 残る赤 = `orchestrator/tests/test_s8c_preregistration_invariant.py::
  test_candidate_freeze_matches_contract_and_generation_chain` の `PreregistrationError: git-timeout`。
  F57 族、同一 nodeid の再発は 6 回。
- **cardinality**: `git rev-list --count HEAD` = **2334**。
  `validate_condition_freeze_at` (`:1310`) の `paths` = `[SOURCE_PATH, EVIDENCE_CONTRACT_PATH, g1]`
  = **3 本** (`git ls-tree` / `git log --name-only` で freeze namespace は g1 のみと実測)。
  → `_batch_oids` の 1 回の要求数 = **7,002**。
- `_git` (`:880`) の `timeout=GIT_TIMEOUT_SECONDS` は**全 git 呼び出しに共通**の固定値である。
  stdin 付きの呼び出しは 2 種のみ: `cat-file --batch-check` (`:1113`)、`cat-file --batch` (`:1160`)。
  stdin なしは `rev-parse` / `for-each-ref` / `rev-list` / `log --name-only` / `ls-tree`。
- **DW-O09 pin 閉包** (`grep -rn "output/s8c-preregistration/condition-freeze" --include=*.py`):
  hit は `s8c_preregistration.py:35` (`FREEZE_DIR` 定義) と
  `test_s8c_preregistration_invariant.py:133` (`legacy_prefix` の否定検査) の 2 件のみ。
  `orchestrator/tests/test_frozen_artifacts.py` の `FROZEN_MANIFEST` (23 key) に s8c 系の key は
  **無い** (`grep -n "s8c"` で 0 件)。docs 側の hit は `docs/phase3-8c-preregistration.md` のみ。
  → **bytes を pin する台帳・trust root は存在しない。** durable manifest の再発行は不要。
- **DW-O10 producer 棚卸し**: `prepare_revision` (`:1650`) が書くファイル種は
  `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g{N}.json` の **1 種だけ**
  (`os.O_EXCL` の exclusive-create、mode 0644、`fsync` 付き)。他のファイル・ログ・receipt を書かない。
  `validate_condition_freeze_at` の成功が `gN.json` 生成の前提条件である (`:1688` → `:1713-1725`)。

## 3. 不変条件 (レンズ A の 5 条件を必須要件として展開)

1. **① 予算に caller 引数を持たせない。** `_git` の予算は呼び出し側が渡すのではなく、
   `_git` 自身が **stdin の要求行数**から一意に算出する。public API (`validate_condition_freeze_at` /
   `prepare_revision` / CLI) に timeout 引数を出さない。`timeout=10**9` の迂回口を作らない。
2. **② 1 回の `_git` 呼び出し = 1 logical invocation = deadline 1 つ。** chunk 分割しない
   (分割は `cat-file-count` などの reason code 境界を動かすため、段 3 レンズ B が real と判定済み)。
3. **③ `MAX_BATCH_REQUESTS` (50,000) 相当点で絶対時間 cap を置く。** 予算は無限に伸びない。
4. **④ rate を warm 0.690 秒の線形外挿で決めない。** contended な計算ノードでの実測値から決める。
5. **⑤ invariant テストは引数を渡さず production と同じ計算式を通す。**
6. `git-timeout` 以外の reason code (`git-input-limit` / `git-output-limit` / `git-failed` /
   `cat-file-count` / `path-not-blob` / `blob-byte-limit` ほか) の**発火条件を一切変えない**。
7. 予算は現行 15.0 秒を**下回らない** (下回れば受理集合を狭める)。

## 4. 親の provisional 裁定 — (P1)〜(P3)。**攻撃対象である**

- **(P1)** stdin を持たない git 呼び出し (`rev-list` / `log --name-only` / `ls-tree` ほか) は
  現行 15 秒に据え置いてよい。根拠は F57 の観測 6 回がすべて `cat-file --batch*` であること。
  → 攻撃点: 2334 commit の `log --format= --name-only --diff-merges=separate` は本当に安全か。
- **(P2)** 予算式は `min(BASE + R × RATE, CAP)` の線形形でよい。`BASE = 15.0`、`R` = stdin 行数。
  → 攻撃点: `cat-file --batch` (blob 実体) の所要は行数でなく**出力 bytes** に支配される。
    行数比例が過小になる入力があるか。
- **(P3)** ④ の実測は「実 repo に対し `cat-file --batch-check` を 48 並列で流す」で代表させる。
  受入全走そのものの再現ではない。
  → 攻撃点: 48 並列の同種 git は全走の混合負荷より厳しい/緩いのどちらか。代表性の主張が過大でないか。

## 5. 成果物影響 (`DW-G05`)

- **実装しない場合**: 受入全走は今後も約 20% の頻度で 1 failed のままになる。依頼が明記するとおり
  **producer / pilot の受入がこの suite に乗る**ため、赤が常態化して受入判定そのものが機能しなくなる
  (「赤 1 件は既知」で通す運用は、新規回帰を隠す)。
- **実装した場合**: `prepare_revision` が、旧実装では `git-timeout` で作られなかった
  `gN.json` を作りうる。R2=(b) によりこれは**環境依存 false reject の修復**として受理する。
  certified 選択・レポート・台帳の**値そのものは変わらない** (予算は判定結果を変えず、
  判定に到達するかどうかだけを変える)。

## 6. 成果物の形

1. `s8c_preregistration.py`: `_git` の予算算出 (module private) + 定数 3 本
   (`GIT_TIMEOUT_SECONDS` 相当の BASE、RATE、CAP)。
2. `test_s8c_preregistration_core.py`: 予算式の単体テスト (境界: R=0 / R=7,002 /
   R=MAX_BATCH_REQUESTS / R>CAP 到達点)、および `git-timeout` reason code が消えていないこと。
3. 計測 probe (repo 外、Codex author が書く) と実測値の記録。
4. worklog / decisions / failures の spool fragment、R3 の別タスク起票。

## 7. 分割方針

- **単位 M (先行)**: 計測 probe。Codex `role=author` が書き、**親が計算ノードで走らせる**
  (codex 子は dispatch できない)。出力 = R ごとの wall-clock 分布。
- **単位 A**: production + 単体テスト。M の実測値が出てから段 4 で定数を確定し投入する。
- 単位間に依存があるため直列。単位 A は単一 codex 子で足りる (編集面が 2 ファイル)。
