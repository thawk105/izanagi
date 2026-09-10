# [T-2075] 受入が層 3 の鎖を迂回したときの hard failure 化 (D1289)

- 実装 commit: `a4957893b8858a7fe88059be5a954ddd26746d64`
- 編集面: `orchestrator/campaign/trial_registry.py`、`orchestrator/tests/test_trial_registry.py`
- 変異台帳: `mutation-out.json` (spec は `mutation-spec.json`)

## 何を直したか

正式受入 `assert_trial_registry_acceptance` は、build report に対して層 3 の鎖を必須経路で
通したかどうかを真偽値 `layer3_chain_absent_seen` に記録し、最後に受領証の
non-certifying reason code `"layer3-chain-absent"` へ積むだけで受入を通していた。
D1289 はこの「記録に残すだけ」の形を明示的に却下している。

## 迂回の実体

外側の `continue` は鎖の呼出しを飛ばさない。飛ばしているのは鎖の**本体**である。
`assert_campaign_layer3_chain` は campaign を持たない失敗 cell に対して `continue` し、
その cell の persisted report 読取・fresh rebuild・比較を一切行わずに正常 return する。
全 cell がこの形なら、鎖は何も検証しないまま成功し、受入は理由コードを積んで受領証を出す。

「関数名を一度呼んだ」ことと「build report を層 3 の鎖へ通した」ことは同義ではない。

## 実装

- 記録用の真偽値と `"layer3-chain-absent"` の発行を削除した。
- 迂回した cell の index を局所 list へ記録する形に変えた。
- 鎖の呼出しと例外変換は維持し、**その直後**・cross-binding と受理追加の**前**に
  `[campaign-chain]` の hard failure を 2 つ置いた。

呼出しの**前**で拒否しない理由: 証拠契約が「すべての build report に層 3 検証を実行する」と
量化しているため、前で止めるとその report が鎖を一度も実行しないまま終わり、契約を満たさなくなる。
段 3 の敵対レンズが段 2 プランのこの点を突き、親が段 4 で書き換えた。

## 線引き

`do_build=False` の no-build は hard failure にしない。D536 は「no-build report の受理そのものを
拒否する」を却下しており、D1289 が覆したのは build 経路の迂回を記録だけで通す部分である。
この境界は変異 `reject-no-build` で固定した。

## 2 つ目の hard failure の到達性 — 恒真な保証を主張しない

層 3 レポート不在側の hard failure は、現行 tree の安定 artifact では独立に到達しない。
段 3 の 2 レンズが**別々の下流経路**を根拠に同じ結論へ達した (一方は手前の腕 digest 検査、
もう一方は後段の cross-binding 検査)。

この位置は「迂回を記録するだけ」の場所であり、D1289 が消せと言っている形そのものなので
fail-closed にはする。**ただし効いている機構としては数えない。** 変異を登録せず、
他の gate を stub して到達させるテストも書かない。

## 実体を名指しした正例

「鎖が呼ばれた」を性質だけで判定すると、producer 層と consumer 層の両方を差し替えたテストが
機構を一度も通らずに緑になる。そこで実体を 2 つ名指しした。

1. `autonomous_trial_completeness.assert_campaign_layer3_chain` (鎖の入口)
2. `autonomous_trial_completeness._fresh_layer3_for_comparison` (鎖の本体。実 `build_report` を呼ぶ)

どちらも stub にせず本物へ委譲する記録用の包みで観測し、入口 6 回・本体 6 campaign 分の到達を固定した。
変異 `skip-layer3-chain-call` がこの正例を殺すことで、名指しが効いていることを確かめた。

## 変異 matrix の実測

runner argv: `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_trial_registry.py -rf -q`
baseline は PASSED。5/5 KILLED、MISMATCH と SURVIVED は 0、rc=0。

| id | 種別 | 殺したテスト数 | 意味 |
|---|---|---|---|
| `drop-bypass-hard-failure` | 負例 | 1 | 迂回の hard failure を消すと新しい負例だけが落ちる |
| `drop-bypass-record` | 負例 | 1 | 迂回の記録を消しても同じ 1 件だけが落ちる |
| `bypass-gate-always-fires` | 正例 | 2 | gate を恒真化すると正常な build が止まる |
| `skip-layer3-chain-call` | 負例 | 2 | 鎖の実体呼出しを消すと実体名指しの正例が落ちる |
| `reject-no-build` | 正例 | 23 | no-build を拒否すると 23 件が落ちる (D536 の境界) |

期待 node は probe 走の観測を完全集合として焼いた。probe は全件 `SURVIVED` 期待で登録し、
実測された失敗 node を収集する目的で走らせた (DW-M07)。

### 走行環境についての実測

probe 走は共有木の事後検査で rc=125 になった。並行 wave が共有 checkout の未追跡ファイルを
書き換えるため、`source/main 共有木の観測 bytes が変化した` と判定される。変異の結果自体は
5 件とも収集できていた。本走は独立 clone を `--source-repo` に渡して構造的に断ち、rc=0 を得た。

## scope 外として裁定パッケージへ返す 3 件

1. **条件 9 判定器に生死判定が無い。** `_called_names` は `ast.walk` で走査するため、
   `if False:` の下に置いた呼出しも「呼んでいる」と数える。実効化するか契約側の文言を直すか。
2. **証拠契約の量化と書き込み先が実装と食い違う。** 契約は「every build report」「registry append」と
   書くが、受入の永続書込は受領証だけである。「受領証発行へ到達する全 build report」へ直すかどうか。
3. **producer と standalone verifier に同型の空走が残る。** campaign を持たない失敗、
   materialized admission failure、致命的 zero-cell を、層 3 実体ゼロのまま診断 report として
   発行できる。D1289 の逐語は「受入の確認処理」なので本 wave では触らない。全 verifier へ
   広げるなら producer・診断契約・発行順序の一体改訂になる。

## 残した nit

改名したテストの nodeid が所要時間台帳 (`orchestrator/tests/acceptance_duration_ledger.json`) に
旧名のまま残り、新テストが所要不明として scheduling される。台帳の値は実測で入るものなので
手で書き入れない (書き入れれば計測の捏造になる)。旧名は挙動を反転させた今の内容と食い違うため
改名は戻さない。被覆のメタテスト
`test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`
は単独実走で緑を確認した。

## 受入を塞いだ非帰属赤 (本 wave の所有ではない)

受入全走 1 回目は `rc=70` / child rc=1 で戻り、赤 26 件がすべて
`orchestrator/tests/test_codex_reasoning_ab.py` に集中した。内訳は setup error 21 件と failed 5 件。

非帰属である。赤の本文は repo 外 `~/.codex/sessions/2026/07/29/rollout-*.jsonl` の
`FileNotFoundError` および `ValidationError: ... rollout count is 0, expected 1` で、
本 wave の差分 (`trial_registry.py` と `test_trial_registry.py`) は repo 外を作ることも
消すこともできない。tested main `24014bdb2` を独立 clone へ checkout して同 file を単独走し、
`failures=26 / failed=5 / errors=21` が受入の内訳と完全一致することを確かめた。

原因は `test_codex_reasoning_ab.py:128` の `_HISTORICAL_SESSIONS = Path("/home/SFC/tanab/.codex/sessions")`
という機体絶対 path と、ユーザーがストレージ上限のため会話ログを定期削除する運用の組合せである。
`~/.codex/sessions/2026/` は `08` と `09` だけになり `07` が丸ごと消えていた。
深さ 8 の全探索と `git ls-files` のいずれでも当該 rollout は 0 件で、過去の実 session なので再生成もできない。

**修正は編集面の衝突を避けるため並行セッションの取りまとめで別 wave へ一本化された。**
本 wave は該当 file に触れていない。失敗の記録と再導入タスクは修正を所有する wave が立てるため、
本 wave では F を起票しない (同じ型に F 番号が 2 つ付くのを避ける)。

本 wave が調べて所有 wave へ渡した材料は次のとおり。

- **除外台帳での回避は構造的に不可能。** `flaky_test_holds.py` は証拠 ID に採番済みの `F[0-9]+` と
  `docs/failures.md` 内の該当節を要求し、さらに `green_run_count >= 1` と非空の緑観測を要求する。
  この 26 件は当該 file が消えて以降この機体で一度も緑になっていないため、緑観測を書けば証拠の捏造になる。
  F の採番は land 時の fold でしか起きず land には緑の受入が要るという循環は F766 に同型が記録済みで、
  今回が 2 例目である。
- **26 node の内訳。** 21 件は module fixture `benchmark_snapshots` (`:787`) が
  `_HISTORICAL_SESSIONS.is_dir()` しか見ず、`08` / `09` が残るため skip せずに失われた 5 session の
  検索まで進んで setup error になる。同 fixture の consumer は静的には 23 node だが、2 件は
  `growth_test_holds.py:157` の既存 hold で先に skip されるため 21 件になる。残り 5 件は body から
  直接読む系で、欠損対象が `author`/`fix1`/`fix2` の 1 件と POS の 4 件に分かれる。
- **pin の張り替えは採らない。** D1164 の却下選択肢が凍結された T-181 provenance 値の書き換えを
  禁じており、pin は `TASK_MANIFEST` の canonical bytes と `task_manifest_sha256` の連鎖に入る。
- **source-bound golden が束縛しているもの (恒久設計の一次入力)。** (1) POS の SHA-256 pin と
  当該 rollout file 全体の bytes、(2) `_REAL_TOKEN_SLICE` とその rollout の 16 行目の逐語、
  (3) その実行由来の `total_token_usage` を production collector と共通の validator
  (`LEDGER._validated_usage`) に通した `input_tokens == 17295`。失われるのは
  「validator が synthetic fixture だけでなく pin された実 rollout の当時の schema と値を処理できた」
  という根拠であり、collector の end-to-end 正しさを単独で証明する test ではなく real-data anchor である。
- **恒久対応の形。** exact 5 rollout を content-addressed な束として repo へ置き、repo には
  session ID・相対 path・SHA-256 の manifest だけを持たせ、fixture は個人 home ではなく束を読む。
  束の不在や digest 不一致は skip ではなく hard failure にする。pin を 1 bit も変えないので
  D1164 と衝突せず、欠落時も静かに通さないので規律 3 にも触れない。
  ただし元 bytes が現存しないため、器の作成と anchor の作り直しの 2 段になり、後者は
  期待値の再導出を伴う実質的な新 benchmark で設計裁定を要する。
- **緊急解除として採られた対象限定 skip の性質。** データが在る環境では検査が減らないが、
  corpus が無い機体では受理集合が広がる (golden 導出・prompt 束縛・snapshot 検証・token 検証を
  壊した実装でも受理される)。削除が定期運用である以上この機体では corpus 不在が定常状態なので、
  これは「規律 2 に触れない」ではなく「承知のうえで引き受けた取引」として記録する必要がある。
