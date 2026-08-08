| 所見 | 内容 | 2 巡目判定 |
|---|---|---|
| F6 (C-02 residual) | 独立行 pin が Unicode line separator を物理改行と誤認する | **partial** |
| F7 | M3 の S06 固有 receipt | **closed** |
| F8 | M10 と M6 の区別 | **closed** |
| F1 (C-01) | raw HTML 節ごと迂回 | **closed**（regression なし） |
| F3 (C-03) | URL / path の過剰拒否 | **closed**（regression なし） |
| F4 (S3-01) | `DW-O16` の矛盾 effort | **closed**（regression なし） |
| F5 (C-07) | テストの穴 | **closed**（regression なし） |
| CF-07 | operations.md の「発火条件の正本」 | **closed**（regression なし） |

## F6 — Unicode line separator で独立行 pin を迂回できる

- ID: `F6 / C-02 residual`
- 主張: 通常の prefix・blockquote 迂回は閉じたが、`splitlines()` が LF/CRLF 以外も行境界として扱うため、規範文を物理的な独立行にしないまま通せる。
- 根拠: S06 だけ [`visible_section.splitlines().count(required_text)`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:3447) を使う。可視化側は各入力単位から `\r\n` だけを除くため、U+2028/U+2029 は文字列内に残る（[check_docs.py:867](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:867)、[check_docs.py:868](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:868)）。その後の `splitlines()` はそれらを行境界と解釈する。
- 現行行 probe:
  - `workers.md:48 == S06-A 定数` → `True`
  - `workers.md:67 == S06-C 定数` → `True`
  - bytes: `CRLF=0, CR=0, LF=69, ends_lf=True`
  - LF / 全文 CRLF / 最終 LF なし → すべて `findings=[]`
  - ASCII・全角の行頭/行末空白 → 対応する S06 finding
- 通常の F6 負例:
  - 入力: `> <S06-A 規範文>`、`参考（旧規範）: <規範文>`、`<規範文> 参考`
  - 出力: `values=['high']`, `line_count=0`, `findings=[F6-A]`
  - M13 の substring 版ではいずれも `findings=[]`
  - よって通常負例は値列ではなく独立行 count だけで赤くなり、単一理由性は成立。
- 残存迂回の production guard probe:
  - 入力: `参考（旧規範）:\u2028<S06-A 規範文>` → `_check_command_docs_guard findings=[]`
  - 入力: `参考（旧規範）:\u2029<S06-A 規範文>` → `_check_command_docs_guard findings=[]`
  - このとき `values=['high']`, `splitlines_count=1` だが、`\n` 単位では規範文行が `0` 件。
  - VT、FF、NEL でも同じく `findings=[]`。
- 判定: **real / must-fix / partial**。前巡から F6 が partial だったため、closed 項目の `regressed` ではなく F6 の未閉鎖 residual。
- 成果物影響: 実行命令を参考文の後半へ埋め込んだ docs が land でき、「独立した規範を pin する」という保証が再び過大になる。

LF/CRLF/CR だけを明示的に正規化して `"\n"` で数え、その他の Unicode separator は行境界にしない負例が必要である。

## 節境界と現行文書の適合

- ID: `F6-boundary`
- 主張: S06-A 規範文を S06-C へ移動・コピーする節境界迂回は通らない。
- 根拠: 節は次の H2 までで切られる（[check_docs.py:1710](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:1710)）。
- probe:
  - A 文を C へ追記 → C は `values=['high','high']`、C finding のみ。
  - C 文を A 文へ置換 → `values=['high']`, `C_line_count=0`、C finding。
  - A 文を A から除いて C へ移動 → A finding + C finding。
- 判定: **refuted / nit**。境界またぎの指定ケースに受理穴はない。
- 成果物影響: A/C の契約を片方へ集約して checker を通すことはできない。

## wording pin の設計上の代償

- ID: `T2-04`
- 主張: 意味を変えない語順・助詞・空白修正も docs-only ではできず、実質的に二つの全文を凍結する。
- 根拠: 全文定数は [check_docs.py:268-273](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:268)、さらにテストが全文を再度固定する（[test_check_docs.py:5540](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/orchestrator/tests/test_check_docs.py:5540)）。任意の助詞変更 probe は S06 finding になった。
- 判定: **real / nit・裁定パッケージ対象**。意図された強度なので今回の実装修正対象とはしないが、正当な文面改善にも docs + checker + test + 採用裁定を要求する設計上の代償である。
- 成果物影響: 安全 drift は強く止める一方、意味不変の明確化まで実装面変更へ昇格させる。

## F7 — M3 の S06 固有 receipt

- ID: `F7`
- 主張: 規範文を保持した extra-effort fixture により、M3 は S06 の値列層だけで殺せる。
- 根拠: A/C 用 production node は [test_check_docs.py:5345-5378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/orchestrator/tests/test_check_docs.py:5345)。
- probe:
  - 入力: 正規の規範文 + 節末へ `` `reasoning=max` ``
  - 現行: `required_text_count=1`, `values=['high','max']`, 対応 finding
  - M3 membership 化: `findings=[]`
- 判定: **real / must-fix は closed**。
- 成果物影響: exact-list を membership に弱めて別 effort の混入を許す回帰を S06 固有 node で検出できる。

## F8 — M10 と M6 の区別

- ID: `F8`
- 主張: 新 production node は中間 regex assertion を持たず、M9 と M6 の両方を変えた場合だけ受理へ反転する。
- 根拠: 新 node は [test_check_docs.py:5381-5401](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/orchestrator/tests/test_check_docs.py:5381)。
- probe:
  - 入力: S06-A 規範文を `` `reasoning=high/max` `` へ置換
  - 現行 → A finding
  - M9 のみ → A finding
  - M6 のみ → A finding
  - M9 + M6（M10）→ `findings=[]`
- 判定: **real / must-fix は closed**。
- 成果物影響: 曖昧値を production が受理した場合だけ M10 の kill として帰属できる。

## closed 5 件の回帰確認

### F1 / C-01

- 主張: raw HTML 内へ S06-A 節を隠す迂回は再発していない。
- 根拠: pin と H2 inventory は同じ raw-HTML-aware 可視化を使用する（[check_docs.py:3411](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:3411)、[check_docs.py:3693](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:3693)）。production 負例は [test_check_docs.py:5429](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/orchestrator/tests/test_check_docs.py:5429)。
- probe: `<x>\n## DW-S06-A...` → A pin finding + `H2 DW-S06-A が 0 件`。
- 判定: **refuted / closed**。
- 成果物影響: rendered Markdown から消えた段 6 契約は受理されない。

### F3 / C-03

- 主張: URL/path 過剰拒否は再発していない。
- 根拠: 前方境界は [check_docs.py:296-303](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:296)、production 正例は [test_check_docs.py:5404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/orchestrator/tests/test_check_docs.py:5404)。
- probe:
  - `reasoning=high`、`。reasoning=high`、`-c model_reasoning_effort=high` → `['high']`
  - URL、`/path/reasoning=/tmp`、`note.reasoning=boom` → `[]`
  - URL/path を A 節へ追記した guard → `findings=[]`
- 判定: **refuted / closed**。
- 成果物影響: 無関係な参照文字列で docs が偽赤にならない。

### F4 / S3-01

- 主張: O16 の effort 空 pin は維持され、O01 を巻き込まない。
- 根拠: O16 節だけを抽出する [check_docs.py:3455-3463](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:3455)、負例は [test_check_docs.py:5459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/orchestrator/tests/test_check_docs.py:5459)。
- probe: 現行 O16 → `[]`; O16 に `reasoning=max` → O16 finding のみ。
- 判定: **refuted / closed**。
- 成果物影響: S06-C=high と矛盾する O16 override は land できない。

### F5 / C-07

- 主張: 1 巡目で要求された production test は削除・改名されていない。
- 根拠: S06-C exact [5251](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/orchestrator/tests/test_check_docs.py:5251)、decoy [5274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/orchestrator/tests/test_check_docs.py:5274)、URL/path [5404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/orchestrator/tests/test_check_docs.py:5404)、raw HTML [5429](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/orchestrator/tests/test_check_docs.py:5429)、O16 [5459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/orchestrator/tests/test_check_docs.py:5459)。AST で全 node の実在を確認した。
- 判定: **refuted / closed**。ただし U+2028/U+2029 の新負例は未実装。
- 成果物影響: 既知の F1/F3/F4 回帰は test source で拘束される。

### CF-07

- 主張: 「発火条件の正本」は維持されている。
- 根拠: [operations.md:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/dev-wave/operations.md:3) は「発火条件の正本は入口の条件 dispatch」。`a1d04b1b` は同文書を変更していない。
- probe: `repr(line 3)` も同一文。
- 判定: **refuted / closed**。
- 成果物影響: 入口と leaf が競合した際の正本は一意。

## S02 / S03 の非回帰

- 根拠: 分岐は S06-A/C だけで、S02/S03 は従来の substring count のまま（[check_docs.py:3447-3450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:3447)）。既存 finding は [check_docs.py:274-283](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:274)。
- probe:
  - 現行 S02/S03 → `[]`
  - max→high →各節の従来 finding だけ
  - prose のみ変更し `reasoning=max` を保持 → `[]`
- finding 逐語は `test_dev_wave_reasoning_effort_pin_findings_are_time_invariant` が固定する（[test_check_docs.py:5519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/orchestrator/tests/test_check_docs.py:5519)）。
- 判定: **refuted / closed**。
- 成果物影響: 段 2/3 の既存受理集合と診断文字列は変わらない。

## 変異の最終帰属

以下は pytest 実走ではなく、`a1d04b1b` の関数 source を一意置換したメモリ上 production-guard probe による kill 予測である。

| 変異 | 実在する kill nodeid | 判定と単一理由 |
|---|---|---|
| M1 | `orchestrator/tests/test_check_docs.py::test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s06_a_max_exact` | **KILLED**。A tuple 削除で A=max が finding→受理 |
| M2 | `orchestrator/tests/test_check_docs.py::test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s06_c_max_exact` | **KILLED**。C tuple 削除で C=max が finding→受理 |
| M3 | `orchestrator/tests/test_check_docs.py::test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s06_a_extra_visible_effort_exact` | **KILLED**。規範文 count=1 のまま `['high','max']` だけが membership 化で受理 |
| M3 | `orchestrator/tests/test_check_docs.py::test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s06_c_extra_visible_effort_exact` | **KILLED**。C でも同じ単一理由 |
| M7 | `orchestrator/tests/test_check_docs.py::test_dev_wave_reasoning_effort_pin_production_path_rejects_hidden_s06_a_exact` | **KILLED**。pin + inventory を raw text へ同時復元すると fence case が 2 findings→受理 |
| M8 | `orchestrator/tests/test_check_docs.py::test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s06_a_max_exact` | **KILLED**。production call 削除で A=max を拒否する層が消える |
| M9 | `orchestrator/tests/test_check_docs.py::test_dev_wave_reasoning_effort_pin_production_path_rejects_s06_decoys_exact` | **KILLED**。link decoy は values=`['high']` なので規範文 pin 除去だけで受理 |
| M10 | `orchestrator/tests/test_check_docs.py::test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s06_a_ambiguous_value_exact` | **KILLED**。M9 単独・M6 単独は finding、両方だけ `findings=[]` |
| M11 | `orchestrator/tests/test_check_docs.py::test_dev_wave_reasoning_effort_pin_production_path_rejects_hidden_s06_a_exact` | **KILLED**。両層を raw-HTML 非対応可視化へ戻すと `<x>` case だけ受理 |
| M12 | `orchestrator/tests/test_check_docs.py::test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_o16_value_exact` | **KILLED**。O16 pin 除去で `reasoning=max` が finding→受理 |
| **M13** | `orchestrator/tests/test_check_docs.py::test_dev_wave_reasoning_effort_pin_production_path_requires_independent_s06_lines_exact` | **KILLED**。blockquote は values=`['high']` のまま、substring 化だけで finding→受理 |

### mask / 誤帰属

- M3 の旧 `test_dev_wave_reasoning_effort_pin_rejects_dw_s06_a_decoys_and_duplicates` と `test_dev_wave_reasoning_effort_pin_production_path_rejects_s06_decoys_exact` は、fixture が規範文自体を壊すため、M3 下でも規範文 pin に mask され **SURVIVED しうる**。M3 receipt には必ず新 extra-visible-effort node を使う。
- M10 の旧 `test_dev_wave_reasoning_effort_pin_rejects_dw_s06_a_ambiguous_values` は M6 単独でも中間 regex assertion で赤くなるため、M10 の receipt に使えない。
- M4/M5/M6 は事前登録どおり参考単独走行であり、SURVIVED を kill 数へ算入してはならない（[mutation-prereg-v2.md:38](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-stage6-high/mutation-prereg-v2.md:38)）。
- 正しい node を使う限り、M1/M2/M3/M7/M8/M9/M10/M11/M12/M13 に静的 SURVIVED 予測はない。ただし M13 が殺せても、上記 U+2028/U+2029 residual は残る。

## 段 7 記録の残件

| 残件 | 判定 | 根拠 |
|---|---|---|
| D207 限定例外 | **未了** | `b97ad3b5 message:L6-8` は S02/S03 を変更しないと書くだけで、「段6限定・人間裁定による例外／一般 precedent ではない」を書かない。後続 4 commit にも追加なし |
| β 再裁定一次資料 | **未了** | [s4-ruling-package.md:27-35](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-stage6-high/s4-ruling-package.md:27) は選択肢であって回答ではない。`b97ad3b5 message:L3` は β 採用を断定するが、AI 作成 commit message は evidence 開示後のユーザー発話そのものを代替しない |
| local-main SHA gate 工程差異 | **未了** | 段 4 は追加を要求する（[s4-ruling-package.md:57-59](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-stage6-high/s4-ruling-package.md:57)）が、[launch-s5.sh:6-10](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-stage6-high/launch-s5.sh:6) は prompt/done/worktree しか検査しない。commit message に工程差異の記録なし |
| 三記録への必須文面 | **未了** | commit message 群には証拠限界・裁定根拠・supersede・docs-only 射程があるが、decision fragment / worklog / insight の三者へ書く義務（[s4-ruling-package.md:61-78](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-stage6-high/s4-ruling-package.md:61)）を代替しない。`a1d04b1b` までに三記録 commit はない |

未変更 repo に対する `python3 tools/check_docs.py` は実行し、`rc=0 / check_docs: 違反なし` だった。pytest は実行しておらず、緑は主張しない。

## 総括

**NO-GO**。
closed 済み 5 件の `regressed` は 0。F7 と F8 も closed。
ただし F6 は U+2028/U+2029 等を `splitlines()` が行境界と誤認し、production guard が `[]` を返すため partial / must-fix。
M1/M2/M3/M7/M8/M9/M10/M11/M12/M13 は正しい実在 node なら静的 KILLED 予測。
M3 の旧 decoy node と M10 の旧 direct node は receipt に使えない。
全文 pin による文面凍結は real な設計上の代償として裁定パッケージへ返す。
段 7 の D207 限定例外、β 一次資料、SHA gate 工程差異、三記録必須文面はすべて未了。
pytest は未実走。