単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/s6-adjudication-2.md

## 必読事項の射影

作業 repository は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix3`
(branch `fix-dev-wave-t1851-c1b-3`、base `ffbba31ba`) である。
**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `<repo>/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md` の **1.1 節** — 「再導出面 (平文) と束縛面 (digest) を分ける」。**三軸 conjunction の境界を測った節である。**
2. `<repo>/orchestrator/campaign/s8b_holdout_freeze.py` の `_expressions()` / `_scan_one()` / `_assert_search_pass()` — 走査の実体

## 所有 path (これ以外は 1 byte も変更しない)

- `orchestrator/tests/test_s8b_terminal_evidence.py`

**他の file を 1 byte も変えるな。** docs の編集と commit はしない。

## 依頼 — holdout の三軸 conjunction 漏洩を閉じる (must-fix・本 wave 帰属)

**親が実測で特定した欠陥である。**

`orchestrator/tests/test_s8b_terminal_evidence.py` の **179〜181 行**が、ある holdout の
**三軸 (read ratio / zipf skew / rmw) を同一 file 内に平文で揃えている。**
`s8b_holdout_freeze._assert_search_pass()` の conjunction 走査に **1 件 hit** し、
`t080` の凍結検証 E2E が **41 件赤**になる。

### 親の実測 (帰属の証拠)

| 走行 | 木 | 結果 |
|---|---|---|
| 焦点走 (`test_s8b_oracle_driver.py` + `test_s8b_floor_campaign.py`) | **健全 main `6172ea26b`** | **617 passed / 0 failed** |
| 同じ焦点走 | **本 wave `ffbba31ba`** | **41 failed / 576 passed** |
| conjunction hit path | — | **`orchestrator/tests/test_s8b_terminal_evidence.py` ただ 1 件** |

**したがって差分に帰属する。走行条件由来ではない。**

### 直し方

契約 1.1 が測った境界は「**三軸のうち 2 軸までは通り、3 軸そろうと落ちる**」である。
したがって **3 軸が同時に揃わないようにすれば閉じる。**

- 当該 fixture の workload 値を、**どの holdout の三軸にも一致しない組**へ変える。
  最小の変更で足りる (1 軸を holdout 以外の値にすれば conjunction は成立しない)。
- **値を別 file へ逃がしたり、文字列を分割・難読化して走査を迂回する形にしてはならない。**
  走査は正しく発火しており、迂回ではなく**値そのものを holdout でないものにする**のが正しい。
- この fixture が何を検査していたのかを保て。**テストの意図を弱めるな。**
  workload 値は「証拠文書に平文で載らないこと」を示すためのものであり、**具体値が holdout である
  必要はない。**

### 検算 (必ず自分で走らせろ)

修正後、**conjunction hit が 0 件になったこと**を次で確かめろ。

```
cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix3
PYTHONPATH=. python3 -c "
from orchestrator.campaign import s8b_holdout_freeze as f
p='orchestrator/tests/test_s8b_terminal_evidence.py'
t=open(p,encoding='utf-8').read()
bad=[]
for name,h in f.HOLDOUTS.items():
    y=h['ycsb']
    e=f._expressions(y[f.RRATIO_KEY],y[f.SKEW_KEY],y[f.RMW_KEY])
    r=f._scan_one({p:t},h['candidate_id'],e)
    if list(r['conjunction_hits']): bad.append(name)
print('conjunction hits:', bad)
"
```

**`conjunction hits: []` にならなければ止めて報告しろ。**

## 禁止

- **既存テストの期待値を変更しない。** 反転・緩和・skip・削除を禁じる。
- **走査を迂回する形の修正をするな** (文字列分割、難読化、別 file への退避、scanner の除外登録)。
- **`IZANAGI_RUN_GROWTH_HELD_TESTS` を設定するな。**
- 所有外 file を触るな。commit しない。docs を編集しない。
- **修正後の値を holdout の三軸へ再び揃えるな。**

## 検査・報告

- 上の conjunction 検算を必ず走らせ、出力を報告に貼れ。
- 自走 harness で所有 file を走らせろ。
  `cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix3 && PYTHONPATH=. python3 orchestrator/tests/test_s8b_terminal_evidence.py`
  **72 件が緑のままであることを確かめろ。減っていたら報告しろ。**
- 同じ fixture 値を参照する他の test があれば自分で引いて走らせろ。
- **緑には実走 nodeid・範囲を併記する。**

## 制約

- 出力へ結合文字 U+0300〜U+036F を使わない。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。

## 総括

最後に `## 総括` 節を置き、次を書く。

- 変更した行と、変更前後の値の性質 (**holdout でない組にしたこと**)
- conjunction 検算の出力 (`conjunction hits: []` であること)
- `test_s8b_terminal_evidence.py` の実走件数 (72 件のままか)
- fixture の意図を保てたか。保てない場合はその理由
- `git diff --stat`
