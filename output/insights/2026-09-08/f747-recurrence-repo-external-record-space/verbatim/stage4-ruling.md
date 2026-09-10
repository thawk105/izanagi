# 段 4 裁定 — dev-wave-f747-recur-20260908

## 所見の real / refuted

| # | 出所 | 所見 | 裁定 | 採否 | scope |
|---|---|---|---|---|---|
| 1 | consult-a 1 | final 応答後のユーザー発話を「継続」と「明示起動された別 dev-wave」のどちらに分類するかの基準が無く、有能な実行者が実際の着地点へ至る読解経路がある | **real** | 採用 | 内 |
| 2 | consult-a 2 / consult-b 1 | `docs/skill-self-improvement.md:66` が禁止対象を `repo file/history` と限定しており、正本が repo 外を対象外に見せる。plan の「強調にすぎない」という反論に条文上の根拠がない | **real** | 採用 | 内 |
| 3 | consult-a 4 | §0 の default-deny は無限定だが禁止列挙が repo 内の名詞で揃い、`state = repo state` と束縛する読解を止める文言がない | **real** | 採用 (所見 2 の是正で同時に閉じる) | 内 |
| 4 | consult-a 5 | 欠落は (b) 単独でなく (a) の遷移判定と (b) の対象範囲が line 66 で結合して生じる | **real** | 採用 | 内 |
| 5 | consult-b 4 | F747 の既存「再発検知」が挙げる 4 終端 (削除 0・罠・検査赤・外側クラス 2) のいずれにも本件は当たらず、同検知は本件を捕捉しなかった | **real** | 採用 (再発 bullet に明記) | 内 |
| 6 | consult-b 2 | 現行 hook に cleanup 限定の trusted context は無い (`hooks/guard_write.py:421-429`、`hooks/guard_bash.py:2887-2894` が読むのは tool_name / tool_input / cwd / command / site だけ) | **real (親 brief (P1-b) を実装の行で追認)** | 採用 | 内 |
| 7 | consult-b 3 | plan の「別 tool／外側 runner なら可能」は現況では成立しない。モデル自身が申告を選べる以上、5 条件を満たす trusted non-model launcher が無ければ恒真な gate になる | **real** | 採用 (裁定パッケージへ) | 外 |
| 8 | consult-b 6 | 親 brief (P1-c) の「是正には意味等価な縮約が同時に必要」は誤り。予算内に収まる案がある | **real (親 brief の誤りを是正)** | 採用 | 内 |
| 9 | consult-a 6 | 本件は F599 と同型ではない (F599 は観測面の目的代替)。F747 への追記は支持されるが「repo 外変種」と記すべき | **real** | 採用 | 内 |
| 10 | consult-a 1 末尾 | plan 草案の「同一継続内で」は会話順の確認なしに事実として書けない | **real** | 採用 (断定しない文面へ) | 内 |
| 11 | plan 総括 | 「3 経路はいずれも現行条文で拒否できる。条文欠落なし」 | **refuted** (所見 1〜4 が破る) | 不採用 | — |
| 12 | consult-b | plan が引いた行番号・定数・4 nodeid はすべて実在 | **refuted (欠陥なし)** | — | — |

## 裁定 1 — 3 経路の最終判定

- **(a) 一般的な自己改善許可を「明示起動された別 dev-wave」と読むこと**: **現行条文は一義的に拒否できない。**
  §0 の時間境界は final 応答の完了で終わり、その後に届いた発話を「継続」(§6 が禁止) と
  「後から明示起動された別 dev-wave」(正本が許可) のどちらへ入れるかの基準が無い。
- **(b) repo 外の記録空間への書き込み**: **現行条文は一義的に拒否できない。**
  §0 の default-deny は無限定だが、禁止列挙が repo 内の名詞で揃い、正本 (`skill-self-improvement.md:66`) が
  禁止対象を `repo file/history` と書き下している。安全側の読解は拒否だが、条文がそれを強制していない。
- **(c) 継続セッション・自己 spawn での実装**: **その区分だと確定していれば拒否できる。**
  §6 が「同一 cleanup 実行・継続・自己 spawn」を逐語で禁じている。ただし (a) の分類基準が無いため、
  今回の発話をその区分へ入れる根拠自体が現行条文からは出てこない。

## 裁定 2 — 是正 (docs-only、親が編集)

`docs/skill-self-improvement.md:66` を次へ置換する。(a) の起動基準と (b) の対象範囲を 1 行で同時に閉じる。

- 旧: `repo file/history を変更しない。後からユーザーが明示起動した別 dev-wave だけが再照合・routing・実装する。`
- 新: `repo 内外の未列挙 state を変更しない。ユーザーが別 dev-wave と明示起動した後だけ再照合・routing・実装する。`

byte 収支: +6 bytes。5993 → **5999** (上限 6000)。最長行 68 文字 (上限 100)。縮約は不要。
`未列挙` は command §0 の「未列挙の state mutation は…禁止する」と同じ語で、正本間の語を揃える。
弱化なし — 禁止対象は広がり、許可条件は狭まり、許可される行為 (再照合・routing・実装) は不変。

`.claude/commands/cleanup-branches.md` と `.agents/skills/cleanup-branches/SKILL.md` は**変更しない**
(whole-file SHA-256 pin。ユーザー裁定「command 本文への追記を既定にしない」を守る)。

## 裁定 3 — 機械検査

**本 wave では追加しない。** 層ごとの判定 (consult-b の実装照合を採用):

| 層 | 判定 |
|---|---|
| `check_docs.py` に条文逐語を追加 | 恒真になる (whole-file SHA が既に bytes を固定済み。実行時の不遵守は観測しない) |
| `check_docs.py` で live mutation を検出 | 不能 (入力は文書・fragment 構造で、session の tool event を持たない) |
| hook で memory 固定 subtree を全セッション拒否 | 可能だが採らない (正常な memory 書込みまで拒否する) |
| 現行 hook で cleanup 時だけ拒否 | 不能 (trusted lifecycle 入力が実装に無い) |
| モデル自己申告 marker | 恒真になる (申告しない実行を同じモデルが選べる) |
| trusted non-model launcher + OS confinement | 現況では不能。5 条件を満たす実体が無い |
| before/after snapshot | 不能 (並行 writer の帰属を分離できず、事後検知であって阻止でない) |

`docs/skill-self-improvement.md:82-83` が「`check_docs.py` の担保は構造 lint に限る」と自ら宣言しており、
runtime 検出を同 checker の成果として主張してはならない。恒真な gate を候補に残さない (規律 5)。
trusted non-model launcher 案は **scope 外の real 所見**として裁定パッケージへ返す (worklog `新規` item)。

## 裁定 4 — F747 再発 bullet

新しい F を採らない。`## 再発` / `### F747` で追記する。文面は次を満たす。

- 発生事実を書く。会話順 (final 応答の前か後か) は確認できていないので「同一継続内」と断定しない。
- repo 外変種であること、repo file と history が無傷であることを書く。
- 既存の「再発検知」4 終端のいずれにも当たらず、本件を捕捉しなかったことを書く。
- 恒久対応として `docs/skill-self-improvement.md` の該当行を是正したことを書く (実体へのポインタ)。

`supersede 追記` は加えない — 既存の記述は「4 終端を判定する」という限定的記述として今も真であり、
古くなった記述の訂正ではなく同型の新規発生だからである (`docs/failures.md:15-19` の運用規則)。

## 裁定 5 — 変異事前登録 (DW-M01)

変更面は `docs/` 配下の `.md` だけで**実装面の差分がゼロ**のため、`DW-S04` により変異 matrix を免除する。
受入全走は免除しない。

## 変更面 (確定)

| path | 種別 | 担当 |
|---|---|---|
| `docs/spool/failures/2026-09-08-dev-wave-f747-recur-20260908-1.md` | 新規 | 親 |
| `docs/spool/worklog/2026-09-08-dev-wave-f747-recur-20260908-1.md` | 新規 | 親 |
| `docs/skill-self-improvement.md:66` | 1 行置換 | 親 |

## 検査 (親が実走)

- `python3 tools/run_tests.py` で 4 nodeid の焦点走
  (`test_codex_cleanup_branches_skill_contract_pins_exact_surface`,
  `test_cleanup_command_budget_is_pinned_and_enforced`,
  `test_cleanup_skill_one_byte_change_is_rejected`,
  `test_cleanup_command_one_byte_change_is_rejected`)
  および `docs/skill-self-improvement.md` の予算・見出し検査 node
- `python3 tools/check_docs.py`
- `python3 tools/spool_fold.py --dry-run --show-diff` (F747 末尾へ 1 bullet 挿入だけ、新規 F 見出しゼロを目視)
- `python3 tools/check_codex_agents.py`
- 受入全走 (`tools/dev_wave_wait.py acceptance`)
- commit 後 `python3 tools/check_ai_provenance.py`
