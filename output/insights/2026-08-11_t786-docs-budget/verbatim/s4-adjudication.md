# 段 4 裁定 — [T-786] docs 予算棚卸し wave

親 = claude-opus-5-1m / reasoning=high / role=manager。base = merge `516cc504` (main `f4db7036`)。

## 0. scope の再確定 (未見の新事実による)

wave 開始時の基準 (worklog 404) では滞留 **8 件**だった。main 取り込みで worklog **407/408** が
入り、同じ [T-786] の裁定が次のとおり更新されていた。**親はこれを承認済み裁定の最新版として採る**
(memory `ruling-status-follow-to-latest-entry`、既裁定の状態は最新エントリまで辿る)。

- **滞留 9 件**へ拡大 — 9 件目 = [T-788] の `DW-O02` へ「制御文字を話題にする artifact は作成
  直後に生の制御 byte を機械走査して除去する」1 行 (実測 L1.5 を **228 bytes 超過**)。
- **[T-789] と同一 wave へ合流** — S9 (a) 起票の L1.5 独立審査 + 第 2 波実測の手順改善 3 件。
  (1) 段 5 の子が読む正本を親が稼働中に編集し子の出力が旧版基準になった → `DW-O02` /
  (2) prompt の必読 path が子の worktree に無くレビューが fail-closed して 1 巡空費 → `DW-O02` /
  (3) file 選択走が `from tests import` の import path を確立せず偽赤 → `DW-O18`。

したがって**本 wave の入庫候補は 12 件** (9 + 3) である。ユーザーの command 引数は 8 件時点の
snapshot を指しているが、台帳の最新裁定が 9 件 + 合流を明示しているため、狭めずに 12 件で扱う。
これは裁定を覆す変更ではなく同一裁定の拡張なので、wave は停止せず続行する。

**[T-760]** (「再訪条件 = docs 予算棚卸し wave で余白が出たとき」) は上記 12 件に含まれない。
余白が残った場合の**第 13 候補**として package に載せるが、実装はしない。

## 1. 段 3 所見の裁定

### 採用 (real、実装へ反映)

| # | 所見 | 裁定 | 反映 |
|---|---|---|---|
| A-1 | 段 6 から runbook 住所を消すと F153 の迂回が開く | **real / blocker** | 段 6 の runbook 住所と「裸の `run_tests.py`」を**削らない**。waiter literal は追加のみ |
| A-2 / B-1 | 新 checker が literal の所在しか見ず恒真 | **real / blocker** | 検査を**全文一致の normative line pin** へ変更。否定・参考例化・blockquote 化・fence 隠蔽の negative test を必須にする |
| A-3 | script は `--pid` を受理し pid-file の自己発行を検証しない。`/proc` 不読時は starttime なしへ降格 | **real** | [T-757] を「0 bytes で解消」としない。`DW-O01` に producer 自身の pid-file 発行を**明文で残す** |
| A-4 | 「生産者を止めるときは待ち手も落とす」は manager の能動義務で script 未実装 | **real** | `DW-C00` の能動形を**保持**。plan の「生産者の停止・死で待ち手も終える」は採らない |
| A-5 | `DW-O01` の「**先に**検査」順序義務 (F23) の消失 | **real** | 「投入前に」を保持 |
| A-6 | [T-765] は変異免除の明確な拡大 | **real / blocker** | **本 wave から除外し、ユーザー裁定へ返す** |
| A-7 | `DW-M08` の「予測を実測へ揃える走行」が無条件で expectation laundering を許す | **real** | F138 の条件 (静的に完全集合を確定できない場合に限り初回を probe と明記し erratum を残して再登録・再走) を**残す** |
| A-8 | 親 brief の「現状余白では 1 件も入らない」は過度な一般化 | **real** | 親の誤りとして認める。**[T-784] は `DW-O09` の既存 slack 内 (935+63=998) に入る** — 同節の縮約を前提にしない |
| B-7 | [T-773] だけを先に land すると L1.5 が 9,597 で 31 bytes 超過 | **real (sequencing)** | 縮約と追加を**同一 commit** に閉じる。中間状態を緑と報告しない |
| B-8 | brief の snapshot が 8 件で、台帳は 9 件 + [T-789] 合流 | **real** | §0 で scope を再確定した |
| B-9 | 変異が「literal を消す・移す」型ばかりで恒真性を証明しない | **real** | **decoy 変異を事前登録**する (literal を残したまま実体を非 canonical へ差し替える形) |
| B-5 | 「既存検査との重複なし」は過大主張 | **real (限定)** | 純増分の主張を「docs consumer literal と target path の binding」だけに限定して記録する |
| B-6 | pin 閉包の差集合 (synthetic fixture、needle/count、runbook §7.3、SKILL.md) | **real** | fixture 登録漏れを段 5 の必須事項に入れる。runbook §7.3 / SKILL.md / runtime argv は**明示的に scope 外**と裁定し package へ書く |

### 不採用・scope 外 (real だが本 wave では実装しない)

- **B-2 / B-3 (runtime argv と receipt の検査、`/proc` 不読時の fail-closed 化)。** real だが、
  実行時 receipt 層の新設は待ち手 script 本体の設計変更であり、docs 予算棚卸しの scope を超える。
  `DW-G04` (条件付き機能の発火 gate) に照らしても、発火する artifact path を本 brief に書けない。
  **裁定パッケージへ返す** — 「[T-773] の結線は docs 層までで、runtime 層は未閉包」と明記する。
  これに伴い **(P1) の「[T-757]/[T-738](c) が 0 bytes で解消」は撤回**する。
- **B-3 後段 (`DW-C00` の「1 条件 1 本」「再生成禁止」の機械検査)。** 同上。prose で保持する。

### refuted

- rulings の ID 差分義務の弱化 (親の疑い) — 新案の差集合検査が新規 ID も捕捉する。
  ただし**「差集合」の向きを明示**する (実体 ID − 索引 ID)。
- `.done` 実在照合の消失 (親の疑い) — script が regular file 実在を照合する。
  ただし **script は `.done` の内容を読まない**ため、「exit code を読んで成否判定する」prose は削除不可。
- B-9 の個別変異の帰属汚染 — 静的依存上、他理由で赤にならない。

## 2. 不変条件 (段 5 が破ってはならない)

1. 予算定数 (`DEV_WAVE_L1_BYTES_MAX` / `DEV_WAVE_L1_5_BYTES_MAX` /
   `DEV_WAVE_L2_SECTION_BYTES_MAX` / `COMMAND_LIMITS`) を**変更しない**。
2. 安全義務を削除・弱化しない。上表で「保持」と裁定した逐語は縮約対象から外す。
3. L2 節の削除をしない。
4. `REQUIRED_REFERENCE_SECTIONS` / `STAGE_UNCONDITIONAL_DISPATCH_CONTRACT` /
   `CONDITION_DISPATCH_CONTRACT` の集合・分類・edge を変更しない。
5. `DW-O01` の model authority 行、`DW-S06-A` の pinned first sentence、
   rulings の frontmatter と `$ARGUMENTS` を一字も変えない。
6. 縮約と追加は同一 commit に閉じる (B-7)。

## 3. 入庫の優先順と停止規則

L1 / L1.5 は 12 件の請求が同一の枠を奪い合う。**上から順に入れ、入らなくなった時点で止め、
残りは審査結果として package へ返す** ([T-127]: 上限を上げず空けるが第一)。

| 順 | 件 | 面 | 備考 |
|---:|---|---|---|
| 1 | rulings 2 義務 (総ざらい規則 + 推奨の独立評価) | rulings command | ユーザー明示の優先同梱。親の独立起草で単独成立を実証済み |
| 2 | [T-773] 待ち手正本の結線 (docs 層) | command 段 6/9・`DW-C00`・`DW-O01` | A-1/A-2 の修正込み。runtime 層は scope 外 |
| 3 | [T-757] producer 自身の pid-file 発行 | `DW-O01` | A-3 により 0 bytes 解消は撤回。明文で入れる |
| 4 | [T-769] + [T-775](ii) 期待 node は完全集合 | `DW-M08` | A-7 の F138 条件を残した形で |
| 5 | [T-775](i) meta-test の自己洗い出し | `DW-S05-C` | |
| 6 | [T-784] 同一性 hash の dataclass・schema | `DW-O09` | **L2 単節の既存 slack 内 (998/1000)。他層を消費しない** |
| 7 | [T-789](3) `from tests import` の import path | `DW-O18` | **L2 単節 615→ に余裕あり。他層を消費しない** |
| 8 | t657 候補 A 段 3 所見を段 6 へ渡す | `DW-S06-A` | |
| 9 | t657 候補 B 短絡連結は条件全体を潰す | `DW-M01` | |
| 10 | [T-789](1)(2) 子への入力の実在と不変性 | `DW-O02` | 2 義務を 1 文へ畳む |
| 11 | [T-788] 制御 byte の走査 | `DW-O02` | 単独で L1.5 を 228 bytes 超過した実績 |
| 12 | [T-738](c) pid 死判定禁止 | `DW-C00` | 順 2/3 で構造的に大半が閉じるなら明文は不要と判定してよい |
| — | [T-765] 変異免除の一般化 | `DW-S04` | **A-6 により除外。ユーザー裁定へ返す** |
| — | [T-760] `--sandbox` caller 必須の規範化 | `DW-O01` | 余白が残った場合のみ。第 13 候補 |

**6 と 7 は L2 単節予算で完結し L1/L1.5 を消費しない**ため、順位に関わらず必ず実施する。

## 4. 変異の事前登録 (`DW-M01`)

新設検査 `_check_dev_wave_waiter_consumer_pins` に単一理由で帰属する変異のみ登録する。
期待 node は完全集合とし、runner 範囲は `orchestrator/tests/test_check_docs.py` に限定する。

| # | 変異 | 期待 |
|---|---|---|
| M1 | command 段 6 の normative line を段 5 へ移す | KILLED |
| M2 | command 段 9 の normative line を削除 | KILLED |
| M3 | `DW-C00` の normative line を fence 内へ移す | KILLED |
| M4 | `DW-O01` の `--pid-file` を `--pid` へ置換 | KILLED |
| M5 | `tools/dev_wave_wait.py` を symlink 化 | KILLED |
| M6 | **decoy**: literal を保持したまま「参考例であり手動投入してよい」を同節へ追記 | KILLED |
| M7 | **decoy**: 段 6 の normative line を否定形 (「使わない」) へ書き換え | KILLED |
| M8 | **decoy**: 段 6 の normative line を blockquote (`> `) 化 | KILLED |
| M9 | **wave 前の実コードの形**: 段 6 を wave 前の逐語 (waiter literal なし・lease `claim`/`acquired` の明示 gate のみ) へ戻す | KILLED |

M6〜M8 は B-9 の「literal count checker が vacuous でも全て殺せる」への対策であり、
**恒真性の反証がこの 3 件の生存/死で決まる**。M9 は memory
`mutation-must-include-pre-wave-form` に従う (禁止したい形を wave 前の実コードが使っていた)。
1 件でも SURVIVED したら検査側を直す。

## 5. 段 5 への指示 (要点)

- 実装面 (`tools/check_docs.py` の新検査、`orchestrator/tests/test_check_docs.py` の
  positive/negative、synthetic fixture の同期) は Codex `role=author` が書く。
- docs 本文 (`docs/dev-wave/**`、`.claude/commands/*.md`) は親が書く。
- **順 1〜9 を先に確定して byte を実測し、残枠で順 10〜12 を試す。**入らない件は編集せず、
  超過 bytes を実測値として記録する (package の審査結果に使う)。
- fixture 登録漏れ (`_COMMAND_GUARD_NEEDLES`・expected count・meta-test) を必ず同期する (B-6)。
