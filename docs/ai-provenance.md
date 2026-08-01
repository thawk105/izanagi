# AI 作業 provenance — commit trailer 規約

## 目的

product・model・reasoning の選択と、タスク種別・レビュー結果・手戻りの対応を監査・分析する。
正本は Git commit message とし、worklog へ二重記録しない。本規約は導入 commit 自身と以後の commit に
適用し、既存履歴は書き換えない。

## 必須形式

すべての commit は message 末尾に次の trailer を 1 行以上持つ。`AI-Agent` は本文と空行で区切った最終段落
(Git が trailer と認識する位置) に置き、本文は任意。フィールド順と区切りは固定し、値に `;` や改行を
含めない。ここまでが機械検査対象である。

`Co-Authored-By` を併用する場合は空行を挟まず連続させる。
Co-Authored-By 候補行はすべて最終 trailer block に置く。
checker は raw 候補行数と隔離 Git parser の認識数を照合し、一致しなければ拒否する。この規則は内容
検出した導入 commit 以後へ適用する (F25)。

```text
AI-Agent: product=<product>; model=<model>; reasoning=<reasoning>; role=<role>[; scope=<scope>]
```

- `product`: `codex` または `claude`。他製品には安定した小文字の識別子を使う。
- `model`: 実行面が表示する slug。表示名しかなければ小文字化し空白を `-` に置換する。
- `reasoning`: 選択面が表示する値を同じ規則で正規化する。明示的に既定設定を選んだ場合は `default`。
- 共通則: 製品面が値を表示しない場合は `not-exposed`、本来確認できるが記録時に確定できない場合は
  `unknown` とし、世代や内部モデルを推測しない。
- `role`: 実質的な寄与を `author`, `reviewer`, `researcher`, `manager`, `integrator` のいずれかで表し、
  複数の役割は role ごとに行を分ける。
- `scope` (任意、2026-07-17 導入): その行の構成が担った作業範囲の短い識別子。**同じ role が複数行に
  わたる commit では全行に必須**、単独行は省略可。導入 commit 以降にのみ適用して既存履歴へ遡及せず、
  checker も内容検出した導入 commit 以後だけ検査する。

`product`, `model`, `reasoning`, `scope` と waiver の `reason` は `[a-z0-9][a-z0-9._-]*` に収める。

AI が実質的に関与しなかった commit は次の 1 行を使う。

```text
AI-Agent: none
```

`AI-Agent: none` は唯一の `AI-Agent` trailer である場合だけ有効で、構造化した `AI-Agent` 行と併記しては
いけない。導入 commit より後の trailer 欠落は human-only ではなく規約違反として扱う。

## 実装面の Codex author 契約

本節を導入する commit 以後、実装面を変更する AI 関与 commit は Codex author を必須とする。
実装面は `orchestrator/`、`tools/`、`hooks/`、`.github/`、`.codex/`、`external/` 配下の `.md` / `.rst`
以外、`patches/` の patch/diff、所在を問わない Python・Shell・C/C++・CMake 等の実行可能資材。テスト・
checker・hook・probe・harness・生成器・機械設定も production 挙動によらず含む。

- 実装面を変更する非 `none` commit は `product=codex; ...; role=author` を 1 行以上含める。Claude 親は
  `manager` / `integrator` / `reviewer`、docs を書けば docs scope の `author` を記録できる。
- docs-only、ログ・計測結果・凍結記録だけの変更、AI 非関与の `AI-Agent: none` は対象外。
- 小さい、軽量版、test-only、probe-only、production 挙動 0 は免除理由にならない。Codex が実行不能なら
  Claude が代行せず停止し、例外の必要性をユーザー裁定へ返す。
- Codex 不可用時はユーザー裁定のうえ、次の物理 1 行を最終 block へ `role=author` と併記する (D105)。
  checker は免除が実際に発火した件数と理由を stdout へ出し、件数と経緯は worklog に残す。

```text
AI-Agent-Waiver: reason=<ident>; ratified=<YYYY-MM-DD>
```

checker は変更 path と trailer を本節の導入 commit から照合し、`--message-file` では staged path に
同じ検査を適用する。

## 記録単位

- 同一の product・model・reasoning・role の子が複数いても行を重複させない。異なる構成・役割は別行、同一
  構成が別作業を担った場合は `scope` で分ける。
- 変更案・finding・レビュー結果が採否または commit 内容へ実質的に影響した構成だけを記録し、起動しただけ・
  読んだだけ・結果が使われなかった構成は記録しない。
- Git 操作の機械的代行は記録しない。範囲選定・競合解決・採否を伴う最終統合に実質的な判断を加えた場合だけ
  `integrator`、説明と実体の独立レビューを行った構成は `reviewer` とする。
- `Co-Authored-By` は著者表示に併用してよいが、model と reasoning を持たないため `AI-Agent` の代用にしない。
  セッション URL は commit message にも PR 本文にも記録しない (2026-07-17 ユーザー裁定: 履歴に永続し
  公開時に session の存在と ID を露出するため)。機械抑止は `.claude/settings.json` の
  `attribution.sessionUrl=false`。
- トークン数・利用枠・料金は trailer の対象外。工数や棄却 finding は `docs/worklog.md` 冒頭の書式に従い worklog か一次資料へ残す。

## `6b64d21` の一回限り forward correction

共有済み `6b64d21753d2cfc790f80caba29df7a40fef3072` はrewriteせず、strict descendant 1件で補記する。

```text
AI-Agent-Correction: target=6b64d21753d2cfc790f80caba29df7a40fef3072; product=claude; model=claude-opus-5; reasoning=xhigh; role=integrator
```

自身の `AI-Agent` と上記物理1行は同じ最終blockに置く。checkerはraw/canonical/final-block exact、selected
set内の両commit、strict lineage、target実欠落、candidate 1件、自身の通常greenを連言し、targetの欠落
findingだけを相殺する。有効な `AI-Agent-Waiver` を持つ commit は担い手になれない。一般allowlist・設定・
CLI免除へ拡張しない。

監査は両commitを含むrangeか既定full-historyを権威とする。target抜き`OLD_HEAD..HEAD`は補助で、初回伝播も
免除しない。green時は両SHAを`forward-corrected=1`で示す。

## commit 前の確認と監査

関与した構成は自己申告だけでなく、可能なら UI・CLI の表示、設定、実験ロールの frontmatter で確認する。
値の欠落規則は「必須形式」に従い、推測で埋めない。

通常列は「message file → `--message-file` で rc=0 → `commit -F` → 既定 full-history 監査」。

```bash
python3 tools/check_ai_provenance.py --message-file <path>
python3 tools/check_ai_provenance.py
```

別範囲は `--range <range>`。Git の trailer 解釈は `git log -1 --format='%(trailers:key=AI-Agent)'` で
補助確認できるが、規範 gate の代用にしない。導入 commit より前の欠落は legacy とし、遡及違反にしない。

この記録は観察データであって統制実験ではない。タスク難度・役割・入力コンテキストが交絡するため、commit
数や成功率だけから製品・モデル・推論深度の優劣を断定しない。改善判断ではタスク種別を揃え、手戻り・
レビュー finding・テスト結果・所要時間と併せて評価する。
