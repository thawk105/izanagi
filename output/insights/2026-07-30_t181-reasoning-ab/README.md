# [T-181] focused review の reasoning `max` 対 `high` — 名指し R-1 正例と限定負例における記述的比較 (凍結、2026-07-30)

親の裁定要約は `docs/worklog.md` 2026-07-30 (65)。実装 commit は `d07142b` / `94c7b08` / `419018c`。

**この wave は歴史 focus1 の再走ではない。** 歴史 T-153(e)/T-154 の focus prompt から導出した
**新規凍結 benchmark** 上の限定 A/B である。歴史 run は指定 9 入力以外に `CLAUDE.md`、`AGENTS.md`、
`docs/dev-wave/**`、`worklog`、`phase3`、`adjudication-plan-v2`、skill 定義を実読しており
(親が rollout の tool call 27 件を走査して確認)、byte 一致の再現は不可能である。

## 射程 (これを越える引用を禁じる)

測ったのは **「prompt が名指しした因果仮説 (R-1) を裏取りして must-fix へ昇格させる率」** であり、
盲目的な発見率ではない。POS prompt は R-1 を攻撃候補として明示的に名指ししている。

## 実測 (10 run、すべて exit 0 / receipt rc=0)

| slot | case | arm | 実効 effort | model_calls | CLI reported | wall_ms | 機械 decision | 機械 R-1 候補 | 親 verdict | 第二読者 |
|---|---|---|---|---:|---:|---:|---|---|---|---|
| s01 | POS | high | high | 24 | 195,374 | 479,830 | NO-GO | false | **true** | true |
| s04 | POS | high | high | 25 | 180,161 | 441,065 | NO-GO | true | true | true |
| s05 | POS | high | high | 28 | 215,638 | 587,285 | NO-GO | true | true | true |
| s02 | POS | max | max | 30 | 221,557 | 619,107 | NO-GO | true | true | true |
| s03 | POS | max | max | 26 | 312,077 | 730,583 | NO-GO | true | true | true |
| s06 | POS | max | max | 39 | 231,701 | 915,034 | NO-GO | true | true | true |
| s07 | NEG | max | max | 74 | 448,536 | 1,104,462 | GO | false | false | false |
| s10 | NEG | max | max | 74 | 691,401 | 1,693,113 | GO | false | false | false |
| s08 | NEG | high | high | 68 | 478,798 | 712,631 | **NO-GO** | false | false | false |
| s09 | NEG | high | high | 66 | 399,585 | 748,079 | GO | false | false | false |

要求 arm と実効 `turn_context.effort` は **10/10 一致**。snapshot は run 前後で不変。
block 内の 2 arm の間隔は 5,229〜8,105 ms、pair 同時実行はしていない (逐次 crossover)。

### arm 別の集計 (primary = 親 + 第二読者の label-masked 裁定)

| case | arm | n | `r1_detected` | NO-GO | model_calls | CLI 合計 | CLI 中央値 | wall 中央値 |
|---|---|---:|---|---|---|---:|---:|---:|
| POS | high | 3 | **3/3** | 3/3 | 24 / 25 / 28 | 591,173 | 195,374 | 479,830 |
| POS | max | 3 | **3/3** | 3/3 | 30 / 26 / 39 | 765,335 | 231,701 | 730,583 |
| NEG | high | 2 | 0/2 | 1/2 | 68 / 66 | 878,383 | 439,191 | 730,355 |
| NEG | max | 2 | 0/2 | 0/2 | 74 / 74 | 1,139,937 | 569,968 | 1,398,787 |

**両読者の一致は 10/10** (`r1_detected` と `decision` の両方)。不一致はゼロ。

## 出せる最強の主張 (事前登録した判定表の適用)

> 固定した、R-1 の因果仮説を明示した単一正例に対する各 3 回の記述的確認で、
> 記録された実効 effort が `high` の run も `max` の run も R-1 を **3/3** 回 must-fix 相当と裁定した。
> 限定負例 (各 2 回) では両 arm ともに偽の R-1 主張は 0 件だったが、`high` の 1 run が
> R-1 とは無関係の理由 (snapshot に author patch が無く所有 gate を独立確認できない) で NO-GO を返した。
> 観測資源は上表のとおりで、`max` は同一入力に対し model_calls・token・wall-clock のいずれも一貫して大きい。
> この結果は当該 prompt、当該 snapshot、当該 serving 期間に限定される。

事前登録表の「max 3/3、high 3/3」行に該当するため、許される裁定は
**「この 6 run で劣化を観測しなかった」だけ**である。非劣性・同等・採用の証明にはしない。

## 認証の欠落 (重要。これを隠して引用してはならない)

`aggregate` / `verify` はともに **rc=24 / `experiment_complete=false`** である。
理由は全 10 run の **`snapshot oracle replay mismatch`** で、実体は次のとおり。

- 実走は fix9 **以前**の oracle 下で行われ、各 run の `snapshot-before.json` はその版が記録した。
- fix9 で stale commit-graph の除去と閉包 manifest への記録を追加したため、
  現在の oracle で再検証すると manifest が一致しない。
- receipt 側の replay 不一致は最終版コードで全 10 run を再収集して解消済み (collect/score ともに rc=0)。
- 実走時に記録した oracle を現在の版で作り直すのは provenance の改竄になるため**行わない**。

したがって本 wave の数値は **replay 認証済みではない**。認証済み台帳を得るには
**最終版装置の下で 10 run を再走する**必要がある (次の一手)。
「凍結 artifact を raw rollout から replay 検証した」と書いてはならない。

## limitation (射程の限界。すべて実測または構造上の事実)

- **logical turn は測れていない**。`model_calls` は非 null `token_count` event 件数であり turn 数ではない。
  T-184 で「turn 削減」を根拠にしてはならない。
- **新規 finding の dedup は文字列一致**であり、同義別表現を落とし得る。finding coverage は下限・advisory。
- **masking は same-owner advisory** であり盲検ではない。mapping は custodian
  (`fresh-0700-root/opaque-name/freeze-before-discovery`) に隔離し、両読者 verdict の凍結後にのみ公開したが、
  同一 owner は技術的には secret を読める。receipt にも `mask_strength: "same-owner-advisory"` として記録した。
- **親は verdict 記入前に機械層の arm 別候補数を観測した** (装置運用の副作用)。per-packet 対応は不明のままだが、
  集計値の事前観測は masking を弱める。第二読者は packet 本文と codebook だけを見ており、一致は 10/10。
- **backend が実際に max/high 相当の計算を行った証明はない**。記録された実効 effort に限定される。
- **NEG の `high` 1 件の NO-GO は benchmark 設計の副作用**である。snapshot に author patch / author worktree を
  置かなかったため所有 gate を独立確認できず、それを理由に NO-GO とした。high 固有の品質劣化ではない。
- `zero_component_total_only` は本走 (最終版コードでの再収集) では **0 件**。
  fix8 前の収集時に NEG 4 run で各 1 件観測した記録は `fix8.md` にある。

## 上流データ・装置について本 wave が確定させた事実

- `turn_context.payload.effort` が実効 reasoning の receipt になる (両 arm 10/10 で要求値と一致)。
- `--dry-run` は「起動しない」ではなく **「bwrap 無しで実走する」** 意味である。
  receipt に `dry_run` が残るため取り違えは検出できるが、隔離なし run を実験データにしてはならない。
- 通常の `git clone` は **894 commit 全部**を持ち込み、`git log --all -- focus1.md` から
  答えの commit `08a7e5f2` へ到達できる。bwrap の path 遮断はこの経路に無力。
  閉包を `8c8dc5e` 到達可能集合へ限定して 834 commit にし、答え commit の到達不能を oracle 化した。
- clone は **stale commit-graph** を持ち込み、prune 済み commit を列挙して `git fsck` を rc≠0 にする。
  これを「unreachable objects がある」と誤報告していた (fix9 で分離)。
- `MAX_SCHEDULE_GAP_MS=60_000` を全連続 run に適用すると、**装置自身の snapshot 検証コスト
  (実測 350,980 ms)** で block 間が必ず違反する。intra 60 秒 / inter 900 秒へ分離した。
- 計算ノード (bnode1xx) は **外向き DNS 不通**のため codex 実走はできない。`python3` は 3.9.13 で
  `python3.10` (3.10.12) を明示指定する必要がある。git は 2.34.1 で
  `ls-files --stage --recurse-submodules` は使えない。

## 装置の検査結果

- テスト **194 件 / rc=0** (計算ノード、python 3.10.12 / pytest 9.1.1)。
  ログインノードでは走らせていない (2026-07-30 ユーザー指示)。
- 変異 **kill 12/12** (`mutation-ledger-raw.json`)。再照準前の 7/12 は
  `mutation-ledger-round1-erratum.json` に erratum として保存。
  M6 は冗長 2 層に守られ単層変異で生存したため、DW-M04 に従い両層同時変異 M6p を追加登録し
  **KILLED** を確認 (`mutation-ledger-m6p.json`)。復元検査 OK、変異後も tree clean。
- 隔離の生死確認は親 probe 2 本 (`probe-isolation-1.md` / `-2.md`)。
  bwrap + 新規 CODEX_HOME 下で `focus1.md` が `No such file or directory` になることを実測。

## 凍結ファイル

| ファイル | 役 |
|---|---|
| `brief.md` | 段1 brief (親) |
| `plan.md` | 段2 Codex plan |
| `consult-a.md` / `consult-b.md` | 段3 敵対相談 (実験妥当性 / fail-open) |
| `adjudication-plan-v2.md` | 段4 裁定・訂正 A1〜A7・変異事前登録 (親) |
| `author.md` | 段5 実装報告 |
| `review-a.md` / `review-b.md` | 段6 敵対レビュー 2 本 |
| `fix1.md`〜`fix9.md` | 段6 fix 9 巡 |
| `focus1.md` / `focus2.md` / `focus3.md` | 焦点再レビュー 3 巡 (DW-O16 上限) |
| `codebook.md` | run 前に凍結した 3 命題の判定規則 |
| `reader2.md` | 独立第二読者の逐語 |
| `prompt-pos.txt` / `prompt-neg.txt` | 実走に使った prompt (歴史 prompt + root 置換のみ) |
| `schedule.json` | run 前に凍結した順序表 |
| `verdicts-parent.json` / `verdicts-reader2.json` / `verdict-log.jsonl` / `verdict-freeze.json` / `revealed.json` | label-masked 裁定の系列 |
| `mutation-ledger-*.json` | 変異台帳 (本走 / erratum / 両層) |
| `probe-isolation-*.md` | 隔離の生死確認 |
| `run-ledger.json` | 上表の機械抽出値 |
