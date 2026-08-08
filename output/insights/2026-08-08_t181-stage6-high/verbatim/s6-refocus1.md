| 所見 | 判定 | 結論 |
|---|---|---|
| C-01 / F1 | **closed** | raw HTML 内へ節ごと隠す迂回は pin・H2 inventory の両層で拒否 |
| C-02 / F2 | **partial** |短い decoy は拒否するが、規範文全文を「参考」や blockquote に置く迂回が残存 |
| C-03 / F3 | **closed** | URL/path を除外しつつ、行頭・句読点後・`-c model_reasoning_effort=` は検出 |
| S3-01 / F4 | **closed** | O16 節だけ effort 無しを検査。O01 の正当な雛形は非対象 |
| C-07 / F5 | **closed** | 指定された raw HTML、S06-C production、decoy、URL/path、O16 のテストは実在 |
| CF-07 | **closed** | `8313b18d` で「発火条件の正本」を意味・逐語とも復元 |

## C-01 / F1

- ID: `C-01 / F1`
- 主張: raw HTML block 内へ必須 H2 全体を隠す迂回は閉じた。
- 根拠: raw HTML、fence、comment を除く可視化は [check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:857)。pin は同 helper を使用し、H2 inventory も同じ可視 text を使う（[check_docs.py:3411](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:3411)、[check_docs.py:3684](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:3684)）。
- probe 入力: `DW-S06-A` 見出し直前へ `<x>\n`。
- probe 出力: `{S06-A adoption pin finding, H2 DW-S06-A が 0 件 finding}`。
- 判定: 元所見は **real**。残存主張は **refuted**、must-fix は closed。
- 成果物影響: rendered Markdown から消えた段 6 契約を land 可能にする受理穴は閉じた。

## C-02 / F2

- ID: `C-02 / F2`
- 主張: 規範文 exact-one pin は、規範文の存在は拘束するが、規範として独立して置かれていることを拘束しない。
- 根拠: S06-A/C の全文定数は [check_docs.py:268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:268)。検査は依然 `visible_section.count(required_text) == 1` という substring 判定である（[check_docs.py:3438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:3438)）。
- probe 入出力:
  - `参考リンク: [例: \`reasoning=high\`](...)` → S06-A finding 1 件。
  - `参考値: outer=\`reasoning=high\`` → S06-A finding 1 件。
  - `参考（旧規範）: 実装 wave は異なるレンズの敵対レビューを ...` → `findings=[]`。
  - `> 実装 wave は異なるレンズの敵対レビューを ...` → `findings=[]`。
- 判定: **real / must-fix、partial**。
- 成果物影響: 実行命令を削除して、同じ文を参考引用としてだけ残した docs が checker を通るため、「docs 契約 + drift pin」の主張がなお過大になる。

必要な修正は、規範文を可視な独立行として exact-one にすること。blockquote、list prefix、「参考:」等を許さない production 負例が必要である。

## C-03 / F3

- ID: `C-03 / F3`
- 主張: 前方境界の過剰拒否は解消され、旧来必要な表記は失われていない。
- 根拠: 前方否定文字へ `. / ?` が追加されている（[check_docs.py:296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:296)）。
- probe 入出力:
  - `reasoning=high`、`。reasoning=high`、`(reasoning=high`、`` `reasoning=high` `` → `high`。
  - `-c model_reasoning_effort=high` → `high`。
  - `https://e.invalid/?reasoning=日本語`、`/path/reasoning=/tmp`、`note.reasoning=boom` → `[]`。
  - canonical high/max → `["high", "max"]`。
- 判定: 元所見は **real**。残存回帰は **refuted / nit、closed**。
- 成果物影響: URL/path の無関係な文字列による偽赤を除きつつ、正当な段契約 drift は検出される。

## S3-01 / F4

- ID: `S3-01 / F4`
- 主張: conflicting effort の拒否は O16 節だけに限定されている。
- 根拠: operations 全体ではなく `_reference_id_sections(..., "DW-O16")` の結果だけを検索する（[check_docs.py:3450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:3450)）。
- probe 入出力:
  - O16 に `` `reasoning=max` `` を追加 → O16 effort finding 1 件。
  - 現行 O16 → `[]`。
  - operations 全体では O01 の `model_reasoning_effort="<効いた値>"` を抽出するが、O16 節内の抽出値は `[]`、production guard も `[]`。
- 判定: 元所見は **real**。残存主張は **refuted、closed**。
- 成果物影響: O16 と S06-C の矛盾は拒否し、正当な O01 起動雛形は維持する。

`operations_text=None` の直接 helper 呼出しでは O16 検査が飛び、probe は `[]` だった。ただし現在の production caller は [check_docs.py:3626](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:3626) の一経路だけで、`main()` は必ず guard を呼ぶ（[check_docs.py:4083](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:4083)）。operations の不在は [check_docs.py:3505](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:3505)、不読は [check_docs.py:3576](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:3576) で独立に finding になる。メモリ上の不読 probe も `docs/dev-wave/operations.md: PROBE_UNREADABLE` を返した。

## C-07 / F5

- ID: `C-07 / F5`
- 主張: 指定されたテスト穴は埋まった。
- 根拠:
  - raw HTML direct wrapper: [test_check_docs.py:5157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/orchestrator/tests/test_check_docs.py:5157)
  - S06-C production exact: [test_check_docs.py:5233](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/orchestrator/tests/test_check_docs.py:5233)
  - link / outer-key decoy: [test_check_docs.py:5256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/orchestrator/tests/test_check_docs.py:5256)
  - URL/path 正例: [test_check_docs.py:5282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/orchestrator/tests/test_check_docs.py:5282)
  - raw HTML production exact: [test_check_docs.py:5307](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/orchestrator/tests/test_check_docs.py:5307)
  - O16=max: [test_check_docs.py:5337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/orchestrator/tests/test_check_docs.py:5337)
- 判定: 元所見は **real**。指定範囲は **closed**。
- 成果物影響: F1、S06-C 配線、F3、F4 の既知回帰を test suite が検出できる。

ただし F2 の残存迂回である「全文を参考文・blockquote として残す」負例はない。これは C-07 の元の列挙ではなく、今回新たに実測した F2 residual である。

## CF-07

- ID: `CF-07`
- 主張: operations 導入文の canonicality 欠落は前方修正済み。
- 根拠: [operations.md:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/dev-wave/operations.md:3) は現在「発火条件の正本は入口の条件 dispatch」。`8313b18d` の message は `b97ad3b5` の「4 主張を保存した」を明示 erratum にしている。
- probe 出力: 現行 `python3 tools/check_docs.py` は rc=0、`check_docs: 違反なし`。
- 判定: 元所見は **real**。残存主張は **refuted、closed**。
- 成果物影響: 条件 dispatch と leaf が競合した際の正本が再び一意になった。

## fix が持ち込んだ退行

- 全 command 3 文書・reference 4 文書について、旧 `_visible_markdown_text()` と新 `_visible_dispatch_inventory_text()` の出力を比較した。全 7 文書で `old_new_equal=True`、H2 集合も完全一致し、production guard は `BASE_GUARD=[]`。既存文書を新たに赤くする回帰はない。
- S06 の語順だけを変えた probe は S06 finding になった。これは [fix 指示:33-41](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-stage6-high/prompt-s6fix.txt:33) が要求した逐語 pin の意図した強さであり、非意図的回帰とは判定しない。ただし maintenance cost は高い。
- S02/S03 へ規範文 pin は追加されていない。各節の prose だけを変え、既存 literal を残した probe はいずれも `findings=[]`。既存の受理集合を変えていない。
- O16 pin、境界、operations 不在・不読についても上記 probe で現行 production 経路の fail-open は見つからなかった。

## 変異の帰属

以下は pytest 実走結果ではなく、fix 後 source をメモリ上で変異し production guard を評価した静的 kill 予測である。

| 変異 | 実在する nodeid | 判定 |
|---|---|---|
| M1 | `orchestrator/tests/test_check_docs.py::test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s06_a_max_exact` | 有効。tuple 削除後の A=max は `findings=[]` |
| M2 | `...::test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s06_c_max_exact` | 有効。C=max は `findings=[]` |
| M3 | `...::test_dev_wave_reasoning_effort_pin_rejects_dw_s06_a_decoys_and_duplicates` | **S06 receipt は無効**。membership 化後も規範文 pin が mask し、S06 finding が残る |
| M3 | `...::test_dev_wave_reasoning_effort_pin_rejects_dw_s02_decoys_and_duplicates` | こちらは有効。S02 の high+max は `findings=[]` になり node が赤になる |
| M7 | `...::test_dev_wave_reasoning_effort_pin_production_path_rejects_hidden_s06_a_exact` | 有効。pin/inventory 両方を raw text へ戻すと fenced section が `findings=[]` |
| M8 | `...::test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s06_a_max_exact` | 有効。production call 削除後は `findings=[]` |
| M9 | `...::test_dev_wave_reasoning_effort_pin_production_path_rejects_s06_decoys_exact` | 有効。規範文 pin を外すと link decoy が `findings=[]` |
| M10 | `...::test_dev_wave_reasoning_effort_pin_rejects_dw_s06_a_ambiguous_values` | **単一理由 receipt 不成立**。M10 では受理へ反転するが、M6 単独でも同 node が先行 regex assertion で赤になる |
| M11 | `...::test_dev_wave_reasoning_effort_pin_production_path_rejects_hidden_s06_a_exact` | 有効。両層を fence/comment-only 可視化へ戻すと `<x>` case が `findings=[]` |
| M12 | `...::test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_o16_value_exact` | 有効。O16 pin 削除後は `findings=[]` |

mask / 誤帰属は次の二点である。

- **M3:** suite 全体では S02/S03 に殺されるが、登録が要求する S06 固有 node は SURVIVED する。S06 規範文を保ったまま別の可視 effort を追記する fixture が必要。
- **M10:** 現 node は checker の受理反転へ到達する前に regex 値 assertion で落ちる。M6 と M10 を区別できる production-path receipt が必要。

登録漏れとして、F2 residual を対象に次を提案する。

- 規範文を「参考:」prefix または blockquote 内へ移した production 負例。
- 独立行 pin を substring pin へ弱める変異。fix 後に新規番号を採り、実在 nodeid はテスト追加後に収集する。
- M10 用に、中間 regex assertion を持たず production の受理集合だけを見る曖昧値負例。

## 記録の射程

commit message 群には、[s4-ruling-package.md:61](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-stage6-high/s4-ruling-package.md:61) の4点が意味上すべて存在する。

- `experiment_complete=false` / `decision=null` / 全10 run mismatch
- 非劣性・同等性・採用の証明ではない
- 採用根拠はユーザー裁定のみ
- T-227 の max と T-184 の再走前提を明示 supersede

射程も `b97ad3b5` が「docs の記述のみ・実起動保証には launcher 結線が別途必要」と明記し、`07aed1ac` も drift pin と O01 非対象を記している。したがって commit message 群そのものの必須文面欠落はない。

ただし commit message は、decision fragment・worklog・insight の三者へ同じ内容を書く義務を代替しない。現 repo に本 wave の三記録はまだなく、次が段 7 の must-fix である。

- 三者すべてへ4点と「docs 契約 + drift pin のみ」「実起動 high の機械保証ではない」「S05-A/S06-B は pin 対象外」を記録する。
- D207 の一般原則に対する「段6限定・人間裁定による明示的例外」であり、一般 precedent ではないと記録する。現 commit は「S02/S03 は変更しない」までで、この限定例外関係を明記していない。
- 指定 artifact 集合内では evidence 開示後の β 再裁定一次資料を確認できない。別のユーザー発話が一次資料なら、その所在を記録へ束縛する必要がある。
- `launch-s5.sh:6-10` には段4で要求した local-main SHA gate が依然ない。今回 stale だった証拠ではないが、工程差異は記録・裁定が必要。

pytest は実行していない。実走済みなのは read-only の `python3 tools/check_docs.py`（rc=0）とメモリ上 probe だけである。

## 総括

**NO-GO**。
C-01、C-03、S3-01、C-07、CF-07 は closed。
C-02 は全文参考引用・blockquote 迂回が残り partial / must-fix。
M3 の S06 固有 receipt は mask され、M10 は単一理由 kill を証明しない。
F2 residual の production 負例と対応変異を追加する必要がある。
段7の三記録には証拠限界・裁定根拠・supersede・docs-only 射程をすべて残す。
D207 限定例外と β 再裁定一次資料の束縛も未了。
pytest の緑は主張しない。