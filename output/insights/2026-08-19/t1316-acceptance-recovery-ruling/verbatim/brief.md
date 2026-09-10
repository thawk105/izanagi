# [T-1316] 段 1 brief — 受入 lease 取得後・受入 command 投入前に落ちる型の裁定パッケージ

## scope

[T-1316]: lease 取得後・受入 command 投入前に落ちる型 (実測 t1180、F365) からの回復経路が無い
問題について、**設計択一を裁定パッケージとして作成する。本 wave は実装しない。**
成果物は「事実 → 効き → 択一 (親推奨/非推奨を明記) → 親の推奨」形式の裁定パッケージ文書
(先例: `output/insights/2026-08-17_t650-lease-release/ruling-package.md` の R-A/R-B/R-C/R-D 形式)。
提出先は次回 `/rulings` セッション。

## 確定済みユーザー裁定・関連決定 (不変条件)

- D253 (`docs/decisions.md:11614`): 受入 lease の待ち札 FIFO 意味論。**変えない。**
- D486 (`docs/decisions.md:20257`): 受入の同一 process 内再試行は「pytest 判定を 1 つも産まずに
  戻った」場合の 6 条件肯定的証拠が揃ったときだけ発火。raw rc だけでの再試行は規律 2 違反として
  却下済み。**この境界そのものが T-1316 を生んだ張本人** — D486 の wave (T-1275) は自ら
  「本 wave が閉じない残余」として t1180 の 52 分喪失を T-1316 へ切り出した
  (`docs/archive/worklog-phase3-0817-630-631.md:583-587`)。**この 6 条件・発火境界は変えない
  前提を既定とするが、変える択一を出すこと自体は禁止しない (ただしコストとして明記)。**
- 受領証 schema・rc の意味論・受入の受理 2 経路 — 変えない前提を既定とする。

## 事実 (file:line、親が実読了・実測済み。codex は独立に検証すること — 鵜呑みにしない)

- `tools/dev_wave_wait.py:3734-3747` (preclaim): claim **前**に `_behind_count` を測り、
  main が進んでいて `merge_message_file is None` なら `_StageFailure("merge-message-preflight")`
  で claim せず拒否する。F365 の恒久対応その 1。ここは問題なく塞がっている。
- `tools/dev_wave_wait.py:3773-3798` (postclaim): lease 取得 **後**に `_behind_count` を
  再計測する。claim 中の待ち (queue 待ちは F365 実測で 11〜50 分) の間に main が進んだ場合、
  `behind > 0` かつ `merge_message_file is None` (または検証失敗) なら
  `_StageFailure("merge-message")` を投げる。**ここが T-1316 の未解決点。**
- `tools/dev_wave_wait.py:4186-4238`: retry は `retry_evidence_reason ==
  "retryable-no-verdict-infra"` のときだけ発火する (D486 の 6 条件)。`merge-message` 失敗は
  受入 command (pytest) を 1 度も起動していないため、この 6 条件を構造的に満たせず
  `retry_evidence_reason` は設定されない → `retry=False` → `_cleanup_lifecycle`
  (`tools/dev_wave_wait.py:4255-4261`) が lease を解放し、待ち札を失う。F365 が実測した
  「300 秒 heartbeat 切れ → 新しい到着時刻の札に作り直され後着に追い越される」経路そのもの。
- `orchestrator/tests/test_dev_wave_wait.py:6736-6745`
  `test_postclaim_merge_message_requirement_still_catches_main_race` が上記を**現状の意図された
  挙動として pin している** (`outcome == _Outcome(70, "merge-message")`、
  `(claims, submissions, releases) == (1, 0, 1)`)。テスト名が示すとおり、この race が塞がって
  いないことは実装者 (T-1275 wave) も認識済みで、意図的に T-1316 へ切り出している。
- `merge_message_file` は `--merge-message-file` CLI 引数由来の `Path | None` で、
  `run_acceptance` の attempt ループ (`tools/dev_wave_wait.py:4323-4338`) を通じて**同一値が
  全 attempt (最大 2 回) で使い回される**。process 起動後に再取得・再解決する経路は無い。
- `_message_has_ai_agent` (`tools/dev_wave_wait.py:2891-2894`) の要件は「非空 + `AI-Agent:` で
  始まる行が 1 行」だけ。`_validated_message_copy` (`tools/dev_wave_wait.py:2897-2909`) も
  ファイル実在・読取可能性・上記要件しか見ない。**main の現在状態・具体的 commit 列・wave 固有
  情報への依存は無い** (F365 も「この呼び出しは merge message の trailer 書式しか検査しない」
  と明記 — `docs/failures.md:9267`)。`docs/ai-provenance.md:20` の trailer 書式も同様に静的。
- `merge_message_file` の repo 内使用箇所は 8 行 (1613, 3689, 3732, 3739, 3793, 3795, 4301,
  4329, 4437) で全数 grep 済み。receipt / attestation など下流へ「供給されたか否か」が
  漏れる経路は無い (merge を実際に行ったかどうかは `behind > 0` だけで決まり、
  `merge_message_file` の非 None 自体は何も強制しない — 未使用なら単に無視される)。
- `--merge-message-file` を渡す呼び手は dev-wave manager 本人の直接 CLI 呼び出しだけで、
  他の wrapper script は存在しない (repo 全体 grep、false positive のみ確認)。
- 隣接する別の失敗経路として `tools/dev_wave_wait.py:3791` の `owned-path-overlap` がある
  (main の新規 commit が本 wave の所有 path と衝突) — これは正当な terminal 失敗であり、
  本 wave の scope 外 (択一がこれを誤って救おうとしていないか、段 3 で確認すること)。

## (P1) 親の暫定裁定 — 攻撃対象

**merge-message-file を、投入時点で main が現在 behind かどうかに関わらず毎回用意して
`acceptance` 呼び出しの argv へ渡せば、race window (queue 待ちの全長、11〜50 分) そのものが
消える。** 内容が main 状態に非依存 (上記事実) なので、いつ postclaim で必要になっても
既に手元にある。**コード変更は不要**で、`docs/dev-wave/operations.md` へ「manager は
`tools/dev_wave_wait.py acceptance` を投入する前に merge-message-file を無条件に用意し
`--merge-message-file` を常時渡す」という運用規約を追記するだけで足りる。
`test_postclaim_merge_message_requirement_still_catches_main_race`
(既存 pin) はコード側の fail-closed backstop として**そのまま残ってよい**
(merge_message_file を本当に省略した場合の保険であり、P1 はその省略を運用側で無くす提案)。

P1 が本当に race を閉じ切るか、他に見落としがないか (attempt 2 との相互作用、
owned-path-overlap との相互作用、無人 supervisor 経路での実行可能性、メッセージ内容の
テンプレート化が別の不変条件と衝突しないか等) は段 3 の攻撃対象とする。
**P1 以外の設計 (コード側で解決する案) が必要になる理由がないか、独立に検討すること。**

## 並列分割方針

- 段 2: 1 本 (plan 起草)。brief と `tools/dev_wave_wait.py` の該当箇所を渡し、
  P1 を鵜呑みにせず独立に file:line 粒度で検証させ、裁定パッケージ草稿
  (事実→効き→択一→推奨、R-A 形式) を起草させる。択一は P1 だけでなく、
  コード側で解決する案・却下すべき案も含めて複数出すこと。
- 段 3: 2 レンズ並列。
  - レンズ A: 「P1 は本当に race window 全体を閉じるか」を正しさ境界から攻撃する
    (attempt 2 との相互作用、owned-path-overlap、無人 supervisor 経路、
    メッセージテンプレートの妥当性、D253/D486 の不変条件との整合)。
  - レンズ B: 「P1 は運用規約の追記だけで本当に足りるか、他の設計 (コード側の変更) を
    要求する隠れた要件がないか」を実効性・網羅性から攻撃する。段 2 の草稿と親 brief
    自身 (P1 とその根拠となった事実の一般化) の両方を攻撃対象に含める。

## 成果物影響 (DW-G05)

直さない場合、この型を踏むたびに certified 選択・材料レポート・台帳の確定が観測範囲で
40〜70 分遅れ続ける (task 引数の記述、F365 の実測 40〜70 分待ち直しに基づく)。
