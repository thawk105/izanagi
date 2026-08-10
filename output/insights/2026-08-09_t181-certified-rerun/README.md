# [T-181] reasoning `max` 対 `high` の認証済み再走 (凍結、2026-08-09)

2026-07-30 の同一プロトコル (`output/insights/2026-07-30_t181-reasoning-ab/adjudication-plan-v2.md`
§2.5〜2.8 + 訂正 A2〜A7) を**変えずに**最終版装置の下で 10 run 再走し、
`aggregate` / `verify` がともに `experiment_complete=true` を返す台帳を得た。
装置 `tools/codex_reasoning_ab.py` は本 wave で 1 byte も変更していない。

**これは同一プロトコルの 2 回目の実施であって、2026-07-30 の 6 run との合算ではない。**
合算は事前登録に無い。

## 射程 (これを越える引用を禁じる)

測ったのは **「prompt が名指しした因果仮説 (R-1) を裏取りして must-fix へ昇格させる率」** であり、
盲目的な発見率ではない。POS prompt は R-1 を攻撃候補として明示的に名指ししている。

## 認証状態 (2026-07-30 版との最大の差)

| 検査 | 2026-07-30 | 本走 (2026-08-09) |
|---|---|---|
| `aggregate` | rc=24 / `experiment_complete=false` | **rc=0 / `experiment_complete=true`** |
| `verify` | rc=24 / `experiment_complete=false` | **rc=0 / `experiment_complete=true`** |
| `failure_reasons` | 12 件 | **0 件** |
| snapshot oracle replay | 全 10 run で mismatch | **全 10 run で一致 (run 前後とも不変)** |

`manifest_sha256` = `afd5cf40c94dafd63b60a1fa21de2144b9e1cd03cf48280dbb698d3b65a5c196`。

### 2026-07-30 が未認証だった原因は 3 つあり、うち 2 つは装置外だった

1. **実走後の装置修正 (F61)。** 実走時に記録した `snapshot-before.json` を修正後の版で
   再現できなくなった。**この原因は fix9 の時点で装置側では既に解消していた** —
   本 wave の段 1 で `build-snapshot` → `verify-snapshot` を POS / NEG 各 2 回走らせ、
   replay 出力が byte 完全一致することを実測した。コード修正は不要だった。
2. **保存場所 (本 wave で判明)。** 旧 manifest が指す prompt / receipt / score / packet_state /
   verdict_log / verdict_freeze / revealed_map は `~/.claude/jobs/c94644e8/tmp/t181-wave/` にあり、
   この一時領域は既に削除されている。2026-08-09 時点で旧 manifest を `verify` すると
   失敗理由は `snapshot oracle replay mismatch` **ですらなく** `prompt cannot be read` ×10 になる
   (`verify-repro-2026-07-30-manifest.json`)。**旧成果物はもはや再検証できない。**
3. **manifest の形 (本 wave で判明)。** 旧 manifest は top-level の `schedule_sha256` と
   `judgments` を持たない。旧 `aggregate` の失敗理由にも
   `manifest schedule_sha256 mismatch` と `manifest.judgments is not an array` が含まれる。
   snapshot 問題が無かったとしても認証は通らない形だった。

本走は (2) を run root・prompt・packet・裁定ログすべて
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/` 配下に置くことで、
(3) を規定どおりの manifest を組むことで塞いだ。

## 実走前に凍結したもの (F61 恒久対応 (a))

`apparatus-pin.json`: 装置 sha256 `58f1176e0ff705ade85ac0cec0c15b77a26f8eaa2d75bb3f7d711519ed6657f7`、
repo HEAD `34957a2489641146f6c33ee5bfd6eb4709af60f1`、`codex-cli 0.146.0`。
`schedule.json` (sha256 `7a865c74999f4423c8096c7888585cd5cd2d1d06e02f777f4c8ae6f6d1b54220`) は
事前登録どおりの block/arm 配置 (s01〜s10、b1〜b5、block 内で arm 順序を交互) をそのまま再利用した。
実走中に装置を編集していない。

## 実測 (10 run、すべて exit 0 / 再試行ゼロ / snapshot 前後不変)

| slot | case | arm | model_calls | CLI reported | wall_ms | 機械 decision | R-1 (label-masked) | 機械 failure_class |
|---|---|---|---:|---:|---:|---|---|---|
| s01 | POS | high | 28 | 190,371 | 383,600 | NO-GO | **true** | — |
| s04 | POS | high | 25 | 178,704 | 505,451 | NO-GO | **true** | — |
| s05 | POS | high | 27 | 182,038 | 567,596 | NO-GO | **true** | — |
| s02 | POS | max | 35 | 211,715 | 728,693 | NO-GO | **true** | — |
| s03 | POS | max | 24 | 226,285 | 808,918 | (採点不能) | **true** | **post-treatment** |
| s06 | POS | max | 41 | 262,843 | 869,254 | NO-GO | **true** | — |
| s07 | NEG | max | 82 | 451,739 | 1,206,684 | GO | false | — |
| s10 | NEG | max | 97 | 571,201 | 1,582,776 | GO | false | — |
| s08 | NEG | high | 62 | 706,919 | 1,397,556 | GO | false | — |
| s09 | NEG | high | 59 | 428,414 | 756,271 | GO | false | — |

要求 arm と実効 `turn_context.effort` は 10/10 一致 (receipt が検証)。
block 内 2 run の間隔は 5,121〜8,658 ms (上限 60,000)。block 間も上限 900,000 内。

### arm 別の集計

| case | arm | n | R-1 (両読者一致後) | model_calls | CLI 合計 | CLI 中央値 | wall 中央値 |
|---|---|---:|---|---|---:|---:|---:|
| POS | high | 3 | **3/3** | 28 / 25 / 27 | 551,113 | 182,038 | 505,451 |
| POS | max | 3 | **3/3** | 35 / 24 / 41 | 700,843 | 226,285 | 808,918 |
| NEG | high | 2 | 0/2 | 62 / 59 | 1,135,333 | 567,666 | 1,076,914 |
| NEG | max | 2 | 0/2 | 82 / 97 | 1,022,940 | 511,470 | 1,394,730 |

**両読者の一致は 10/10** (`reader_agreement.rate = 1.0`)。不一致ゼロのため保守側裁定は発火していない。
新規 finding は **0 件** (`new_finding_ledger = []`)。
負例で real と裁定された偽 must-fix は **両 arm とも 0 件**であり、4 run すべてが GO を返した。

## 出せる最強の主張 (事前登録した判定表の適用)

> 固定した、R-1 の因果仮説を明示した単一正例に対する各 3 回の記述的確認で、
> 記録された実効 effort が `high` の run も `max` の run も R-1 を **3/3** 回 must-fix 相当と裁定した
> (label-masked、両読者一致)。限定負例 (各 2 回) では両 arm ともに偽の R-1 主張は 0 件で、
> 4 run すべてが GO を返した。観測資源は上表のとおりで、正例では `max` が同一入力に対し
> model_calls・token・wall-clock のいずれも中央値で大きい。
> この結果は当該 prompt、当該 snapshot、当該 serving 期間に限定される。

事前登録表の「max 3/3、high 3/3」行に該当するため、許される裁定は
**「この 6 run で劣化を観測しなかった」だけ**である。非劣性・同等・採用の証明にはしない。

## 機械 `decision` 行は採点器の欠陥を含んでいる (隠さない)

> **2026-08-09 追記**: 本節の続きとして `erratum-f176.md` を置いた。汚染されている field は
> `decision` 行だけでなく計 8 個ある。[T-184] へ渡す際の可否は同 erratum が正本である。

`aggregate.json` の `decision` は次のとおりである。

```
row = POS_PRIMARY
quality_decision = "benchmarkまたはmax基準が不安定"
reason = "label-masked R-1 judgment max=2/3 high=3/3; NEG real false finding occurrence={'max': 0, 'high': 0}"
```

`max=2/3` は **s03 が `failure_class="post-treatment"` に落ちたため**であり、
両読者は s03 の R-1 を **true** と裁定している。原因は採点器 `score_run` の decision 検査である。

- 第 1 段 `decision_match` = 「総括の最初の一文が単一の GO/NO-GO」。s03 は**通過**している。
- 第 2 段 `len(distinct_decisions) != 1`。抽出正規表現
  `(?<![A-Za-z-])(NO-GO|GO)(?![A-Za-z一-龯ぁ-んァ-ヶ-])` は `GO` の直後がひらがなだと数えない。
  s03 だけが総括を「**NO-GO です。**」で始めたため抽出 0 件となり、「一意でない」と判定された。
- 第 2 段の意図は「GO と NO-GO の併記による曖昧さ」の検出であり、**抽出 0 件は曖昧さではない**。
- 2026-07-30 の 10 run は全て「`NO-GO。`」「`GO。`」だったため発火せず、欠陥は潜在していた。

**実走後に採点器を直していない。** 直せば凍結した装置が変わり、F61 と同じ理由で
本走の replay 認証が失われる。事前登録も「判定表は run 前に凍結、事後変更禁止」である。
したがって上の `decision` 行は欠陥を含んだままの正直な出力であり、
**この行を「max 基準が不安定」という実質的知見として引用してはならない**。
採点器の是正と、その後の扱い (再走の要否) は本 insight の外の裁定に属する。

## limitation (射程の限界。すべて実測または構造上の事実)

- **logical turn は測れていない** (`turn_accounting.logical_turns_reported = false`)。
  `model_calls` は非 null `token_count` event 件数であり turn 数ではない。
  [T-184] で「turn 削減」を根拠にしてはならない。
- **親は本 wave 開始時に 2026-07-30 の結果表を読んでいる。** packet→slot の対応は今回新規かつ
  ランダムなので arm は推測できないが、「両 arm とも R-1 を検出した」という事前知識は
  masking を弱める残差である。緩和として、**verdict を凍結する前に `aggregate` を走らせていない**
  (2026-07-30 の既知弱点「親が verdict 記入前に機械層の arm 別候補数を観測した」は本走では発生していない)。
- **masking は same-owner advisory** であり盲検ではない。mapping は custodian
  (`fresh-0700-root/opaque-name/freeze-before-discovery`) に隔離し、両読者 verdict の凍結後にのみ公開した。
- **backend が実際に max/high 相当の計算を行った証明はない**。記録された実効 effort に限定される。
- **全 10 run で `compaction_observed = true`、`rate_limited = true`。** 本走は前回より
  入力規模が大きく (CLI reported 合計 3,410,229)、compaction と rate limit の下で観測された。
  arm 間で条件が偏っていた証拠は無いが、前回と同条件ではない。
- `zero_component_total_only` は **NEG 4 run に各 1 件** (POS は 0 件)。前回の本走では 0 件だった。
  `last_token_usage` の component 総和が 0 の event であり、資源値の下限側の誤差要因になる。
- **新規 finding の dedup は意味同値判断**であり、両読者とも「bare CR の読取入口正規化」は A-1、
  「M2 ambient fixture の過剰決定」は B-3、性能 backlog は成果物影響未立証として数えなかった。
- 非名指しの held-out 正例 (blind discovery stratum) は本走にも無い。外的妥当性の最大の限界である。

## 凍結ファイル

| ファイル | 役 |
|---|---|
| `s1-brief.md` | 段 1 brief (親) |
| `apparatus-pin.json` | 実走前に固定した装置版・repo HEAD・codex 版 |
| `schedule.json` | 実走前に凍結した順序表 (supervisor が run root へ写したもの) |
| `attempt-ledger.jsonl` | supervisor の逐件台帳 (10 run、再試行なし) |
| `manifest.json` | `schedule_sha256` と `judgments` を含む正規形 manifest |
| `aggregate.json` / `verify.json` | 認証済み集計と replay 検査 (ともに rc=0) |
| `verify-repro-2026-07-30-manifest.json` | 旧 manifest を 2026-08-09 に `verify` した結果 (rc=24) |
| `packet-state.json` / `verdict-log.jsonl` / `verdict-freeze.json` / `revealed-map.json` | label-masked 裁定の系列 |
| `verdicts-parent.json` / `verdicts-reader2.json` | 両読者の入力 |
| `reader2.md` | 独立第二読者の逐語 (codex `gpt-5.6-sol` / effort high、`check_codex_output` rc=0) |
| `run-outputs/` | 10 run の出力本文 (unblind 後に slot 名で保存した一次証拠) |

benchmark snapshot・run root・packet・custodian の実体は
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/` にある。
`verify` の replay にはこの実体が要る (`--sessions-root` は `bench/runs`)。
