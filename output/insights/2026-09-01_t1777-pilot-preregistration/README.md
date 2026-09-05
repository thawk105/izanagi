# [T-1777] A-1 pilot の事前登録本文を起草し、人間の発効直前で止めた

- `authority: insight` — 可変状態の正本ではない。現在地の正本は worklog の「次の一手」。
- `default_effect: no-state-change`
- wave = `worktree-dev-wave-t1777-pilot-prereg`、基準 commit `c6a94ec99` (着手直前の local main)
- **本 wave は docs-only である。** `orchestrator/` 配下を 1 byte も変えていない。発効は人間の手番
  であり (D1383 / D1391)、既成事実化していない。

---

## 1. 依頼と、実測した関門

依頼は「A-1 対計画 pilot の事前登録本文を、人間の発効直前まで用意する」であった。関門は
着手時点で実際に成立していた。

`load_policy("paper-story-a1-20260901-balanced5-pilot-v1")` は通り、policy bytes の SHA-256 は
`405e26b976fc421203cda0d29f74b762f53e7a982bcd536dc8da4a42a5c079c4` である。`preregistration` は
`{"path": None, "sha256": None}` であり、`_require_policy_ready_for_execution` は
`PaperStoryError("v3 policy preregistration binding is not frozen by the parent")` を投げた。
submit も measure も必ず拒否される。

coordinator の実装は `08a17b3b3` で着地済みであり、本 wave では作り直していない。

## 2. 成果物

| 成果物 | 内容 |
|---|---|
| `output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md` | pilot の事前登録本文。機械可読の正本 `paper_story_a1_paired.v3-pilot.json` の人間可読の対 |
| 本文書 §4 | 人間が発効するときの手順と、編集箇所の全列挙 |

## 3. 段 3 の独立レビューが出した real 所見と、親の裁定

段 2 のプラン 1 本と、段 3 の独立レンズ 2 本 (内容 / 工程) を起こした。逐語は `verbatim/`。
**親はすべての real 所見を一次資料で検算してから採否を決めた。**

### 3.1 発効閉包は 4 箇所ではなく 5 箇所だった (工程レンズ、採用)

親 brief は発効の編集を 4 箇所と数えていた。工程レンズは 5 箇所目を指摘し、親が検算して
real と確定した。

`orchestrator/tests/test_paper_story_a1_paired.py` の
`test_v3_loader_accepts_future_sized_policy_shape` は、sized policy の形を
`copy.deepcopy(_v3_pilot_policy())` で作る (同 file:1018-1020)。fixture はそのあと `study_id`、
`final_estimate_eligible`、sizing の入力、各 workload の `reps` / `df` / `k` / `planned_sigma_tps` を
書き換えるが、**`preregistration` だけは sized 用へ戻していない。**
`_v3_pilot_policy()` は `load_policy(V3_PILOT_STUDY_ID)` で**実ファイルを読む** (同 file:255-256)。
したがって pilot を発効させると、この fixture は pilot の非 null な `preregistration` を
引き継いだまま `load_policy(V3_SIZED_STUDY_ID)` を呼び (同 file:1074)、sized 側の module pin
(まだ `None`) との照合 `_validate_policy_v3_semantics` (`paper_story_a1_paired.py:1377-1389`) で
`PaperStoryError` になる。

**この 1 件を落としたまま発効すると、人間の commit がテスト赤で止まる。**

### 3.2 `rep_notes` の限界は消えていない (内容レンズ、採用)

段 2 のプランは「`rep_notes` は v3 の `invalid_rules` に無いので、旧先例の感度分析は持ち込まない」
と書いていた。内容レンズはこれを実装との食い違いとして指摘し、親が検算して real と確定した。

`paper_story_a1_paired.py:3644-3645` は `bench.get("rep_notes") != []` を `rep-notes-not-empty` として
無効に数える。この検査は v3 で分岐しておらず、pilot にも掛かる。**policy の 16 文字列の外に
ある受理規則である。** 事前登録本文は 6.3 節でこの条件を明示し、8 節に反復数に対する性質
(pilot の n=60、2n=120 で p=0.1% なら約 11.3%) を感度分析として残した。

### 3.3 分類の語彙が 2 系統ある (内容レンズ、採用。親 brief の (P1-3) を訂正)

親 brief は分類名を `resolved-above-floor` / `bounded-below-floor` と書いていたが、これは
`paper_story_a1_paired.py:199-215` の `CLASSIFICATION_RULES` の語彙である。**反復数を決める手順が
実際に使うのは `tools/size_paper_story_a1_balanced.py:54-58` の
`bounded-within-floor` / `resolved-beyond-floor` (improvement / regression) である。**
本文は後者を主表記とし、条件 ID は policy の語彙 (`zero` / `positive-six-percent` /
`negative-six-percent`) を主、sizing 側の別名を併記した。

**2 系統は用途で分かれる。** `CLASSIFICATION_RULES` 定数を参照するのは v2 policy の検証だけだが、
同じ `resolved-above-floor` / `bounded-below-floor` の語彙は `_classify_difference`
(`paper_story_a1_paired.py:3045-3054`) が返し、最終推定の対象になる v3 sized study の統計でも
使われる (同 file:3186)。pilot は `final_estimate_eligible: False` のため同 file:3174-3179 で
`pilot-sizing-input-only` へ分岐し、そもそも分類されない。

### 3.4 記録量が閉じていなかった (内容レンズ、採用)

観測行の形は、生産側 `paper_story_a1_paired.py:1581-1584` の `_BALANCED_RECEIPT_REP_KEYS` と
消費側 `tools/size_paper_story_a1_balanced.py:74-85` の `_ROW_KEYS` が exact に一致する 8 個である
(`tps`, `arm`, `pair_index`, `group`, `block`, `block_position`, `started_at_ns`, `ended_at_ns`)。
本文はこの 8 個を閉じた列挙として書いた。

### 3.5 判定手順の未凍結値 (両レンズ、採用。ただし凍結先は本文とする)

`--search-trials` と `--certification-trials` は必須引数で既定値が無く、policy にも欄が無い。
Clopper–Pearson の試行別 alpha `1/(60 * j * (j + 1))` (`size_paper_story_a1_balanced.py:133-136`) と、
上限まで通る候補が無いときの `no-passing-n` 終了 (同 file:726) も、プラン案では本文に出ていなかった。

**親の裁定:** 3 つとも本文へ書く。試行回数は、同じ A-1 族で先に凍結された headline study の値
(`orchestrator/campaign/paper_story_a1_headline.v1.json` の `search_trials` = 20000、
`certification_trials` = 100000) に揃えた。

内容レンズは「機械可読の正本 (policy JSON) へ凍結せよ」と述べたが、**この部分は採らなかった。**
policy JSON の編集は発効閉包そのものであり、人間の手番である。人間可読の事前登録本文で
凍結するのは v2 の先例 (`2026-08-26_paper-story-a1-sized-preregistration/README.md` が Monte Carlo の
seed と試行数を本文で凍結している) と同型で、「データを読む前に決める」という事前登録の意味を
満たす。この 2 値を人間が変えたい場合の手順は §4 に含めた。

### 3.6 3 つの無効規則は実装の裏取りが閉じていない (内容レンズ、部分採用。scope 外の real 所見)

内容レンズは、16 の無効規則のうち「両 arm の bench 前 build・verify」「ブロックごとの競合テナント
検査」「静定がちょうど 1 回」の 3 つについて、射影した driver だけでは成果物から拒否できると
確認できないと述べた。

**親の裁定: 本文の書き方としては採用、実装は scope 外。** 本文は登録した判定の規則を逐語で書き、
「これらは機械的に拒否される」という実装の完全性の主張は**書かない** (本文 8 節末尾に明示した)。
恒真な保証を書かないための措置である。実装側の裏取りは docs-only の本 wave の scope 外であり、
別項として残す。

### 3.7 refuted と裁定した所見

- 本文を local main へ着地させることは発効の既成事実化にあたらない。線は「候補となる bytes が
  存在するか」ではなく「policy の束縛と module pin を非 null で commit し、実行可能性を開いたか」
  である。親も同じ判断である。
- 新しい成果物を足すだけで赤になる既存検査は無い。`test_frozen_artifacts.py` は
  `FROZEN_MANIFEST` の列挙 path だけを検査し、`test_artifact_admission.py` の実 tree 検査は
  `output/campaigns` と `campaign.lock` に限られ、`tools/check_docs.py:2611-2649` の placeholder 走査は
  `output/insights` の**直下の** `*.md` だけを `glob` で列挙する (再帰しない)。親が実測でも確認した。
- 計測先 `output/insights/2026-09-01_paper-story-a1-balanced5-pilot` と接頭辞を共有する点も無害。
  v2 でも先例が同じ形 (`..._sized-preregistration` と `..._sized`) である。
- **ただし `check_docs.py` が本文を走査していないことは、本文に placeholder が無いことの証明には
  ならない。** 親は本文を目視で確認したうえで、値の欄を作らない方針で書いた。

## 4. 発効手順 (人間の手番)

**追記 (2026-09-05、[T-2272]):** この手順は D1638 の委任により worklog (1275) で AI が実施済みである。
以下は記録として残し、§4.1 の行 locator 4 件だけを 2026-09-05 時点の位置へ更新した (本文の pin hash は動かない)。

**AI はここから先を行わない。** 次の 5 箇所を 1 つの commit にまとめる。
**本文を編集する場合は、その本文自身が 6 箇所目として同じ commit に入る。**

### 4.0 前提

- **path** =
  `output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md`
- **SHA-256** = `8f8d2ad338a7a3193aaee8433c1495cef06b9520425251dd8bef89584ca626fc`
  — これは**本 wave が着地させた bytes に対する値**であり、それ以上の意味を持たない。
- **本文を 1 byte でも編集した場合、この値は無効になる。** 必ず手順 1 から計算し直し、
  計算した値のほうを使う。試行回数 (探索 20,000 / 認証 100,000) を変える場合もここに当たる。
- 手順の順序を入れ替えない。特に手順 3 (policy JSON の編集) より先に手順 4 (policy の hash 計算)
  を行うと、古い bytes の hash を pin することになり、`load_policy` が
  「tracked policy bytes differ」で拒否する。

### 4.1 手順

repo root で、1 コマンドずつ実行する。

1. 本文の hash を計算する。

   ```
   sha256sum -- output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md
   ```

2. `orchestrator/campaign/paper_story_a1_paired.py:198-203` の
   `V3_PILOT_PREREGISTRATION_RELATIVE_PATH` に
   `output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md` を、
   `V3_PILOT_PREREGISTRATION_SHA256` に手順 1 の値を入れる。

3. `orchestrator/campaign/paper_story_a1_paired.v3-pilot.json` の `preregistration` を、
   手順 2 と同じ path と hash にする。

4. policy JSON の hash を計算する。

   ```
   sha256sum -- orchestrator/campaign/paper_story_a1_paired.v3-pilot.json
   ```

5. `orchestrator/campaign/paper_story_a1_paired.py:192-194` の `V3_PILOT_POLICY_SHA256` を
   手順 4 の値にする。

6. `orchestrator/tests/test_paper_story_a1_paired.py:1387-1397` の未凍結を固定している 4 つの
   assertion を、束縛後の正例へ更新する。**非 null であることではなく、exact 一致を固定する。**
   - `policy["preregistration"]` が
     `{"path": paired.V3_PILOT_PREREGISTRATION_RELATIVE_PATH, "sha256": paired.V3_PILOT_PREREGISTRATION_SHA256}`
     と等しいこと。
   - `paired.V3_PILOT_PREREGISTRATION_RELATIVE_PATH` が手順 2 で入れた exact な path と等しいこと。
   - `paired.V3_PILOT_PREREGISTRATION_SHA256` が手順 1 の exact な値と等しいこと。
   - `paired._require_policy_ready_for_execution(policy)` が例外を投げないこと
     (`pytest.raises` を消し、素の呼び出しにする)。

7. `orchestrator/tests/test_paper_story_a1_paired.py:1012-1019` の
   `test_v3_loader_accepts_future_sized_policy_shape` で、pilot から複製した `sized` の
   `preregistration` を sized 側の module pin
   (`V3_SIZED_PREREGISTRATION_RELATIVE_PATH` / `V3_SIZED_PREREGISTRATION_SHA256`) から
   作り直す 1 行を足す。これを欠くと §3.1 のとおり赤になる。

### 4.2 commit の前に走らせる検査

1 コマンドずつ実行する。

```
python3 tools/run_tests.py orchestrator/tests/test_paper_story_a1_paired.py
```

```
python3 tools/run_tests.py orchestrator/tests/test_paper_story_a1_balanced_sizing.py
```

```
python3 tools/run_tests.py orchestrator/tests/test_campaign.py
```

```
python3 tools/run_tests.py orchestrator/tests/test_paper_story_a1_job_contract.py
```

後ろの 2 つは、発効後の pilot policy を直接 `load_policy` して、スケジュール・source closure・
CCBench 契約を検査する
(`orchestrator/tests/test_campaign.py:13168-13217`、
`orchestrator/tests/test_paper_story_a1_job_contract.py:271-282,1825-1835`)。

### 4.3 commit の後に走らせる検査

**`orchestrator/tests/test_paper_story_a1_headline.py` は commit の前に走らせない。**
同 file:1303-1312 は、A-1 の manifest に載る path (driver と
`orchestrator/tests/test_paper_story_a1_paired.py` を含む) について
`git status --porcelain` が空であることを要求する。発効の編集を未 commit のまま走らせると、
**変更が正しくても必ず赤になる。**

commit のあとに、1 コマンドずつ実行する。

```
python3 tools/run_tests.py orchestrator/tests/test_paper_story_a1_headline.py
```

```
python3 tools/check_ai_provenance.py
```

受入全走は wave 単位の機構であり、`docs/dev-wave/operations.md` の `DW-O18` / `DW-O27` の
手順に従って行う。push は人間が行う。

## 5. 本 wave で実測した検査

| 検査 | 結果 |
|---|---|
| `tools/check_docs.py` (段 6 の修正後に再走) | 違反なし |
| `orchestrator/tests/test_s8b_repo_scan_invariant.py` (三軸語の走査、段 6 の修正後に再走) | rc=0 |
| `orchestrator/tests/test_frozen_artifacts.py` + `test_artifact_admission.py` | 138 passed (着手時の基準線) |
| `orchestrator/tests/test_paper_story_a1_paired.py` + `test_paper_story_a1_balanced_sizing.py` | 174 passed (着手時の基準線) |

本 wave は実装面の差分がゼロ (`orchestrator/` 配下を 1 byte も変えていない) のため、
変異 matrix は `DW-S04` により免除である。受入全走は免除せず、段 9 の取り込みで行う。

## 6. 残る項目

- **pilot の発効** — 人間の手番 (§4)。
- **3 つの無効規則の実装の裏取り** (§3.6) — 本 wave の scope 外。
- **反復数を決める道具の受理範囲** — 段 6 のレビューが出した real 所見。試行回数は
  1 以上 1,000,000 以下、候補範囲は `28 <= n_min <= n_max <= 4096` の任意値が受理され
  (`tools/size_paper_story_a1_balanced.py` の `SizingConfig.validate`)、下流の sized certificate の
  照合も選ばれた `n` / `df` / `k` / sigma を見るだけで、certificate 内の試行回数と候補格子を
  照合しない (`orchestrator/campaign/paper_story_a1_paired.py:1028` 付近)。
  **事前登録本文はこの点を主張しない書き方にした** (本文 5.5 節) が、機械側で閉じるかどうかは
  別途の判断が要る。本 wave は docs-only のため実装しない。
- pilot の投入と計測、sized study の policy と事前登録 — 発効の後。

## 7. 還元判断

CCBench 本体への還元候補は含まない。
