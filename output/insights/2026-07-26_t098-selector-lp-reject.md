# [T-098] selector の選択理由欄で literal placeholder を拒否する — 材料レポート (2026-07-26)

- 対象: worklog 2026-07-25 (7) でユーザーが承認した「生成側で拒否」の実装 ([T-098])
- branch: `worktree-dev-wave-t091-093-hardening`、基準 = `c129e73`、統合 commit = `ef9ef76`
- 成果物: `orchestrator/campaign/s8b_selector_output.py` (+13 行)、テスト 3 ファイル (+386 行)
- 逐語 = 同 `-verbatim.md` (codex 子 9 本)、変異台帳 = 同 `-mutation-ledger.json` (23 変異の新旧全走)
- **表記規約 (D88 (6) を継承)**: 検出対象の 3 バイト列は本文へ再掲しない。
  `tools/check_docs.py` の `LITERAL_PLACEHOLDERS` を正本とし、宣言順に **LP-1 / LP-2 / LP-3** と呼ぶ。

## 1. 何を作ったか

段 8b selector の raw 出力 parser (`parse_selector_output`) に、decode 済み `rationale` が
LP-1〜LP-3 を **substring として含む**入力を拒否する fail-closed gate を追加した。
新 error code は `rationale_placeholder` の 1 個。検査位置は `rationale_blank` /
`rationale_too_long` の後で、既存 code と既存拒否挙動は不変である。

受理集合は **「長さ 1〜2000 の既存受理文字列のうち LP を含むもの」だけ**縮小する。
拒否は他の parse 違反と同型に流れ、`record_agent_attempt` は `status="invalid"` /
`choice_id=None` / `parser_error_code="rationale_placeholder"` を記録する。既定選択への fallback はない。

## 2. 実装前の実測 (裁定前提の検証、模擬なし)

親が段 1 で実コードへ 6 パターン (LP-n 単独 3 + 長文埋め込み 3) を投入し、**6/6 が受理 (status=valid)**
であることを確認した。承認済み裁定の前提は成立していた。

既に封印済みの `output/s8b-freeze/selector_predictions.json` の 6 rows に LP を含む rationale は
**0 件**である。したがって受理集合を狭めても既存 freeze の再 parse 結果は変わらない。

## 3. 裁定時に未見だった新事実 (親 brief の訂正を含む)

### 3-1 parser の bytes は封印済み journal に pin される (DW-O09)

`output/s8b-freeze/selector-runs/journal.jsonl` の run_header は `parser_module_sha256` を持ち、
実測で **worktree の値 == `pre_oracle_head` blob の値 == journal header の値**の 3 者が一致していた。
当該 run は 15 record・6 cell 完走・封印済みである。

本変更で worktree 側だけが変わるため、**prediction 未生成の crash-resume で旧 journal だけが残る経路**では
`ensure_run_header` が header 不一致で fail-closed 拒否する。既存 prediction がある状態の `seal` 再実行は、
parser を読む前の「既存 prediction 拒否」で先に止まる。当該 run は完走・封印済みのため実害はない。

### 3-2 **親 brief の誤りを訂正** — floor は現行 parser に不感ではない

親 brief は「floor / ratified の両検証は `pre_oracle_head` blob から再計算するので worktree 編集に不感」
と書いた。これは **parser の hash pin にだけ当てはまり、parse 挙動には当てはまらない**。

- `s8b_floor_campaign.py:1365-1367` は launch preflight で `verify_prediction_freeze` を呼び、
  その中の `_reparse_agent_raw` が **現行 parser で raw を再 parse** する (段 3 レンズ A の A-1)。
- したがって floor 経路は新 gate を**実行する**。既存 6 rows が無事なのは
  **データ依存**であって構造保証ではない。

### 3-3 no-touch 境界 (実測で確定)

`verify_prediction_freeze` → `_verify_file_record` が `sources` の 5 ファイル
(holdout_freeze / builder / role / input schema / **output schema**) を worktree から再読して
sha 照合する。したがって `s8b_selector_output_schema.json` と `.claude/agents/selector-8b.md` の
bytes 変更は既存 freeze の検証を割る。両者を no-touch とした。parser module は `sources` に
含まれないため編集できる。

## 4. 敵対相談・レビューが否定した親の裁定

段 3 の両レンズ・段 6 のレビュー B・焦点再レビューの **4 本が NO-GO** を返した。

| 裁定 | 親の当初案 | 否定の理由 | 確定 |
|---|---|---|---|
| P1 (機構) | ast 抽出でトップレベル `Assign` を 1 個取り、docs 側と parser 側を等号照合 | helper がトップレベル `Assign` しか見ないため `LITERAL_PLACEHOLDERS += (...)` を**静かに取りこぼす** (B-4) | **テスト内に独立記述した 3 語**を置き、docs 側・parser 側の**双方**と照合する三者照合へ変更 |
| P1 (機構、第 2 巡) | ast 検査だけで足りる | `globals()["…"] += (…)` は target が `Subscript` なので ast では捕まらない (RB-2) | ast 検査に加え、テストから `check_docs` を**実行時 import** して実効値も照合 |
| P2〜P4 (主張) | 「raw より強い」「code で診断できる」 | 強いのは **JSON lexical escape に限る**。長さ超過の LP は `rationale_too_long` に吸収されるため新 code の件数は LP 出現件数ではない (B-6) | 実装は維持し、**記録の主張範囲を限定**した (下記 §6) |
| テスト設計 | parser 単体の負例で足りる | collector が新 code だけ別 code へ再分類する誤実装は parser 単体テストを素通りする (B-1) | `record_agent_attempt` と prediction runner の**統合負例**を追加 |
| テスト設計 | 負例を並べれば検出力になる | 承認済み 3 語**以外**を拒否しない境界が固定されておらず、ASCII 山括弧語を広く拒否する誤実装が全テストを通る (RB-1) | 非承認語・片側 delimiter 欠落・全角・HTML entity・token 内空白の**受理を正例で固定** |
| テスト設計 | LP-1 の代表例で足りる | 「LP-1 のときだけ choice 優先」「LP-1 だけ特別扱い」の誤実装が生存する (RB-3、refocus §3-A) | collector・順序テストを**独立 3 語 + escape** で parametrize |
| テスト設計 | 埋め込み例は 1000 文字目で足りる | `rationale[:1500]` の**先頭走査**誤実装が全テストを通る (refocus §3-B) | 全長 2000 の**末尾に接する** LP の負例を追加 |

**素材: 正例が検出力になった。** 当初の設計は負例だけだった。レビューが「承認外の**過剰拒否**も
受理集合の改変である」と指摘し、全角・HTML entity・token 内空白・非承認語の**受理**を固定する正例を
追加した。これらは変異 S2 / S7 / S8 で実際に KILL しており、正例なしでは検出できなかった。

## 5. 変異 matrix (親実測、統合 commit 後)

事前登録 **23 件が 23/23 実測と一致**した。帰属成立 **22 件** (新テストのみ KILL・変更前 HEAD 版テストは
SURVIVE)、非帰属 control **1 件** (N1 = 最大長を 3000 へ。新旧とも KILL のため新規検出力に計上しない)。

`DW-M08` に従い各変異を**新テストと変更前 HEAD (`c129e73`) 版テストの双方へ全走**した。
harness は `flock` の単一走行 guard、置換アンカーの出現数 1 の assert、注入後 diffstat による注入実在確認、
内容比較 (`read_text() == 元ソース`) による復元検査を持つ。全走後の tree は clean である。

とくに次の 3 件は、レビューが指摘しなければ検出できなかった誤実装を実測で捕まえている。

- **S1** (`AugAssign` で docs 語彙へ 4 語目) / **S11** (`globals()` 経由で同じことをする) —
  当初の ast 束縛案では両方 SURVIVE していた。
- **S15** (先頭 1500 文字だけ走査) — 焦点再レビューの指摘で追加した末尾負例が KILL した。

## 6. 射程と限界 (正直な記述)

### 6-1 この gate が防ぐもの

`parse_selector_output` を通る **decode 済み `rationale`** における LP-1〜LP-3 の exact な出現。
JSON lexical escape (`<` 等、大文字 hex を含む) を経て同一文字列になる場合も含む。
生成経路 (`record_agent_attempt` → journal → materialized row) はこの gate の下流にあるため、
**LP を含む rationale が新たに封印されることはない**。

### 6-2 この gate が防がないもの (受容した偽陰性)

- **意味的に同じ別表記**: 全角山括弧、HTML entity、token 内の空白や U+200B、片側 delimiter 欠落、
  非承認の類似語は**受理する**。これは D88 が却下済みの一般化であり、拡張は [T-100] の裁定対象。
  本 wave はこれらの**受理を正例で固定**しただけである。
- **新 code の件数は LP 出現件数ではない**。長さ 2000 超の LP は従来どおり `rationale_too_long` に
  吸収される。`rationale_placeholder` は「長さ検査まで到達した exact LP の**主拒否理由**」であり、
  LP-n の別や出現数は機械可読にならない (invalid row では rationale が null 固定のため、
  識別には raw artifact の再読が要る)。
- **ratified proof chain はこの gate を実行しない**。`s8b_ratified_freeze.py` には
  `verify_prediction_freeze` / `parse_selector_output` の呼び出しが**ない** (親が grep で 0 件を実測)。
  ratified 側は `pre_oracle_head` blob 射影による再現性を優先した構造検査である。
  結果として、**floor は新 gate で拒否する evidence を ratified は構造検査だけで通す**。
  生成経路は本 wave で閉じたので残余は「手で偽造した evidence」という別の脅威モデルだが、
  「certified 選択の rationale が LP でないこと」を ratified 単独では独立再検証できない ([A-2] → §7)。
- **schema と role は新しい受理集合を表現していない**。両者は封印済み prediction の `sources` に
  sha pin されるため bytes 変更が既存 freeze の検証を割る。現状は parser-authoritative である ([A-3] → §7)。

## 7. 裁定パッケージ (scope 外の real 所見)

1. **[A-2] ratified proof chain が selector raw を再 parse しない。**
   選択肢 = (a) 現状維持 + 射程の明記、(b) ratified にも再 parse を入れる (歴史射影の設計変更)、
   (c) 封印時点の parser 判定を artifact に刻む。**(a) を推奨**。
2. **[A-3] schema と role が新受理集合を表現しない。**
   選択肢 = (a) parser-authoritative 契約の明文化、(b) versioned schema/role への移行。
3. **[A-5 残余] floor と ratified の受理差を固定する境界テスト。** 1 の裁定に従属する。
4. **[T-105 新規] `tools/dev_waves/daemon.py:626-638` の `_run_artifact_bytes` に競合がある。**
   `os.walk` の列挙後に `path.lstat()` するため、atomic-write の一時ファイル (`*.tmp.<pid>.<tid>`) が
   列挙と lstat の間に rename / 削除されると `FileNotFoundError` が**素通し**され、
   `DevWavesError` の fail-closed にならない。本 wave の受入全走で 1 度発現し、
   単独再走 3/3 passed のフレークであることを実測した。本 wave の差分とは無関係
   (差分 4 ファイルに `tools/dev_waves/` を含まない)。

## 8. 検査

| 検査 | 結果 |
|---|---|
| 受入全走 (統合 commit 直前) | **3058 passed / 18 skipped / 0 failed** (288.31s) |
| 基線 (`c129e73`) | 2994→**2995 passed / 18 skipped / 0 failed** (294.91s)、node 消失 0 |
| `tools/check_docs.py` | 違反なし (rc=0) |
| `tools/check_ai_provenance.py` | 358 件・違反なし (rc=0) |
| 変異 matrix | 事前登録 23/23 一致、帰属 22 / 非帰属 control 1、復元後 tree clean |

## 9. エージェント工数

codex 子 **9 本** — プラン 1 (max)、敵対相談 2 (max)、実装 1 (high)、敵対レビュー 2 (max)、
fix 2 (high)、焦点再レビュー 1 (max)。
段 3 は両レンズ NO-GO・所見 11、段 6 は A=GO 所見なし / B=NO-GO 所見 4、
焦点再レビューは closed 4 / partial 1 + 残存誤実装 2 で NO-GO、fix 巡 2 で全 closed。
