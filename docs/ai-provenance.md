# AI 作業 provenance — commit trailer 規約

## 目的

Claude と Codex の製品選定、モデル選択、推論深度を後から監査し、タスク種別・レビュー結果・
手戻りとの対応を分析できるようにする。記録の正本は Git commit message とし、worklog に同じ
情報を二重記録しない。

この規約は、本ファイルを導入する commit 自身と、それ以後の新しい commit に適用する。既存履歴は
書き換えない。

## 必須形式

すべての commit は、message 末尾に次の trailer を 1 行以上持つ。フィールドの順序と区切りは
固定し、値に `;` または改行を含めない。必須なのは、本文と空行で区切った最終段落 (Git が
trailer と認識する位置) に `AI-Agent` があることで、本文の有無は任意 (ここまでが
`check_ai_provenance` の機械検査対象)。`Co-Authored-By` を併用する場合は空行を挟まず連続させ、
Co-Authored-By 候補行はすべて最終 trailer block に置く。checker は候補行数と隔離した Git parser の
認識数を照合し、本規則を導入 commit 以後へ適用する (failures F25)。

```text
AI-Agent: product=<product>; model=<model>; reasoning=<reasoning>; role=<role>[; scope=<scope>]
```

- `product`: `codex` または `claude`。将来ほかの製品を使う場合は、安定した小文字の識別子を使う。
- `model`: 実行面が表示するモデル slug を使う。slug がなく表示名しかない場合は、小文字化し空白を
  `-` に置換した識別子を使う。製品面が値を表示しない場合は `not-exposed`、本来確認できるが
  記録時に確定できない場合は `unknown` とし、世代や内部モデルを推測しない。
- `reasoning`: 選択面が表示する値を小文字の識別子で書く。表示名しかない場合は、小文字化し空白を
  `-` に置換する。明示的に既定設定を選んだ場合は `default`、製品面に設定がない・表示されない場合は
  `not-exposed`、本来確認できるが記録時に確定できない場合は `unknown` とする。
- `role`: 実質的な寄与を `author`, `reviewer`, `researcher`, `manager`, `integrator` のいずれかで表す。
  複数の役割を果たした場合は role ごとに行を分ける。
- `scope` (任意、2026-07-17 導入): その行の構成が担った作業範囲を表す短い識別子
  (例: `floor-protocol`, `tests`, `worklog`)。**同じ role が複数行にわたる commit では全行に必須**
  (どの行が何を担ったかが復元不能になるのを防ぐ)。単独行では省略してよい。この規則は導入
  commit 以降にのみ適用し、既存履歴へ遡及しない (checker も導入 commit を内容検出して以降だけ
  検査する)。

`product`, `model`, `reasoning`, `scope` は `[a-z0-9][a-z0-9._-]*` に収まる識別子とする。

AI が実質的に関与しなかった commit は、構造を埋める代わりに次の 1 行を使う。

```text
AI-Agent: none
```

`AI-Agent: none` は唯一の `AI-Agent` trailer である場合だけ有効で、構造化した `AI-Agent` 行と
併記してはいけない。導入 commit より後の trailer 欠落は human-only ではなく規約違反として扱う。

## 実装面の Codex author 契約

本節を導入する commit 以後、実装面を変更する AI 関与 commit は Codex author を必須とする。
実装面は `orchestrator/`、`tools/`、`hooks/`、`.github/`、`.codex/`、`external/` の非 Markdown、
`patches/` の patch/diff、および所在を問わない Python・Shell・C/C++・CMake 等の実行可能資材である。
テスト、checker、hook、probe、harness、生成器、機械設定も production 挙動の有無によらず含む。

- 実装面を変更し、`AI-Agent: none` でない commit には
  `product=codex; ...; role=author` を 1 行以上含める。Claude 親は `manager` / `integrator` /
  `reviewer`、docs を書いた場合は docs scope の `author` として記録できる。
- docs-only、ログ・計測結果・凍結記録だけの変更、および AI 非関与の `AI-Agent: none` は対象外。
- 小さい、軽量版、test-only、probe-only、production 挙動 0 は免除理由にならない。Codex が
  実行不能なら Claude が代行せず停止し、例外の必要性をユーザー裁定へ返す。

`tools/check_ai_provenance.py` は commit の変更 path と trailer を照合する。過去履歴へ遡及せず、
本節の導入 commit から適用する。`--message-file` では staged path に同じ検査を適用する。

## 記録単位

- 同一の product・model・reasoning・role で動いたサブエージェントが複数いても、同じ行を人数分
  重複させない。異なる構成または役割が寄与した場合は別行にし、同一構成が別々の作業を担った
  場合は `scope` で行を分ける。
- 変更案、finding、レビュー結果が採用判断または commit 内容へ実質的に影響した構成だけを記録する。
  起動しただけ、ファイルを読んだだけ、結果が使われなかっただけの構成は記録しない。
- Git 操作を機械的に代行しただけの AI は記録しない。変更範囲の選定、競合解決、採否を伴う最終統合に
  実質的な判断を加えた場合だけ `integrator` として記録する。説明と実体の独立レビューを行った構成は
  `reviewer` とする。
- `Co-Authored-By` は著者表示のため必要に応じて併用してよいが、model と reasoning を持たないため
  `AI-Agent` の代用にはしない。セッション URL (`Claude-Session:` trailer 等) は commit message にも
  PR 本文にも記録しない (2026-07-17 ユーザー裁定: 履歴に永続する識別子であり、リポジトリ公開時に
  セッションの存在と ID を露出するため)。機械抑止は `.claude/settings.json` の
  `attribution.sessionUrl=false` が担う。
- トークン数、利用枠、料金はこの trailer の対象外とする。必要なエージェント工数や棄却 finding は
  `docs/worklog.md` 冒頭の書式に従い、worklog または一次資料へ残す。

## `6b64d21` の一回限り forward correction

共有済み `6b64d21753d2cfc790f80caba29df7a40fef3072` はrewriteせず、strict descendant 1件で補記する。

```text
AI-Agent-Correction: target=6b64d21753d2cfc790f80caba29df7a40fef3072; product=claude; model=claude-opus-5; reasoning=xhigh; role=integrator
```

自身の `AI-Agent` と上記物理1行は同じ最終blockに置く。checkerはraw/canonical/final-block exact、
selected set内の両commit、strict lineage、target実欠落、candidate 1件、自身の通常greenを連言し、
targetの欠落findingだけを相殺する。一般allowlist・設定・CLI免除へ拡張しない。

監査は両commitを含むrangeか既定full-historyを権威とする。target抜き`OLD_HEAD..HEAD`は補助で、
初回伝播も免除しない。green時は両SHAを`forward-corrected=1`で示す。

## commit 前の確認と監査

commit 前に、関与した構成を会話の自己申告だけでなく、可能なら UI、CLI の選択表示、設定ファイル、
実験ロールの frontmatter で確認する。製品面が値を開示しない場合は `not-exposed`、本来確認できる値を
記録時までに失った場合は `unknown` を使い、推測で埋めない。

Git が trailer として解釈できるかは、commit 後に次で確認できる。

```bash
git log -1 --format='%(trailers:key=AI-Agent)'
```

範囲監査では `<range>` を対象範囲に置き換える。

```bash
git log --format='%H %s%n%(trailers:key=AI-Agent)' <range>
```

導入 commit から `HEAD` までの欠落、排他違反、フィールド順、値と role の形式は次で検査する。

```bash
python3 tools/check_ai_provenance.py
```

別の範囲を監査するときは `--range <range>`、commit 前の message を検査するときは
`--message-file <path>` を使う。導入 commit より前の欠落は legacy とし、遡及的な規約違反にはしない。

この記録は観察データであり、モデル間の統制実験ではない。タスク難度、役割、入力コンテキストが
交絡するため、commit 数や成功率だけから製品・モデル・推論深度の優劣を断定しない。改善判断では
タスク種別を揃え、手戻り、レビュー finding、テスト結果、所要時間などと一緒に評価する。
