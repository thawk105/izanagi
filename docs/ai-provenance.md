# AI 作業 provenance — commit trailer 規約

## 目的

product・model・reasoning の選択とタスク種別・レビュー結果・手戻りの対応を監査する。
正本は Git commit message とし worklog へ二重記録しない。本規約は導入 commit 自身と以後の commit に
適用し、既存履歴を書き換えない。

## 必須形式

すべての commit は message 末尾に次の trailer を 1 行以上持つ。`AI-Agent` は本文と空行で区切った最終段落
(Git が trailer と認識する位置) に置き、本文は任意。フィールド順と区切りは固定し、値に `;` や改行を
含めない。ここまでが機械検査対象。

`Co-Authored-By` を併用する場合は空行を挟まず連続させる。
Co-Authored-By 候補行はすべて最終 trailer block に置く。
checker は raw 候補行数と隔離 Git parser の認識数を照合し、一致しなければ拒否する。この規則は内容検出した導入 commit 以後へ適用する (F25)。

```text
AI-Agent: product=<product>; model=<model>; reasoning=<reasoning>; role=<role>[; scope=<scope>]
```

- `product`: `codex` または `claude`。他製品は安定した小文字の識別子。
- `model`: 実行面が表示する slug。表示名だけなら小文字化し空白を `-` に置換する。
- `reasoning`: 選択面が表示する値を同じ規則で正規化する。明示的に既定設定を選んだ場合は `default`。
- 共通則: 値を表示しない場合は `not-exposed`、本来確認できるが記録時に確定できない場合は `unknown`
  とし、世代や内部モデルを推測しない。
- `role`: 実質的な寄与を `author`, `reviewer`, `researcher`, `manager`, `integrator` から選び、複数役割は行を分ける。
- `scope` (任意、2026-07-17 導入): その構成が担った作業範囲の短い識別子。**同じ role が複数行に
  わたる commit では全行に必須**、単独行は省略可。導入 commit 以降にのみ適用して遡及せず、
  checker も内容検出した導入 commit 以後だけ検査する。

`product`, `model`, `reasoning`, `scope` と waiver の `reason` は `[a-z0-9][a-z0-9._-]*` に収める。

AI が実質的に関与しない commit は次の 1 行を使う。

```text
AI-Agent: none
```

`AI-Agent: none` は唯一の `AI-Agent` trailer である場合だけ有効で、構造化した `AI-Agent` 行と併記しては
いけない。導入 commit より後の trailer 欠落は human-only ではなく規約違反として扱う。

## 実装面の Codex author 契約

本節を導入する commit 以後、実装面を変更する AI 関与 commit は Codex author を必須とする。
実装面は `orchestrator/`、`tools/`、`hooks/`、`.github/`、`.codex/`、`external/` 配下の `.md` / `.rst`
以外、`patches/` の patch/diff、所在不問の Python・Shell・C/C++・CMake 等の実行可能資材。テスト・
checker・hook・probe・harness・生成器・機械設定も production 挙動によらず含む。

- 実装面を変更する非 `none` commit は `product=codex; ...; role=author` を 1 行以上含める。Claude 親は
  `manager` / `integrator` / `reviewer`、docs は docs scope の `author` で記録できる。
- docs-only、ログ・計測結果・凍結記録だけの変更、AI 非関与の `none` は対象外。
- 小さい、軽量版、test-only、probe-only、production 挙動 0 は免除理由にならない。Codex が実行不能なら
  Claude が代行せず停止し、例外の必要性をユーザー裁定へ返す。
- Codex 不可用時はユーザー裁定のうえ、次の物理 1 行を最終 block へ `role=author` と併記する (D105)。
  checker は免除が実際に発火した件数と理由を stdout へ出し、件数と経緯は worklog に残す。

```text
AI-Agent-Waiver: reason=<ident>; ratified=<YYYY-MM-DD>
```

checker は変更 path と trailer を本節の導入 commit から照合する (`--message-file` では staged path)。

## 記録単位

- 同一の product・model・reasoning・role の子が複数でも行を重複させない。構成・役割が違えば別行、同一
  構成の別作業は `scope` で分ける。
- 採否または commit 内容へ実質的に影響した構成だけを記録し、起動・読取だけ・結果不使用の構成は記録
  しない。
- Git 操作の機械的代行は記録しない。範囲選定・競合解決・採否を伴う最終統合に実質的な判断を加えた場合だけ
  `integrator`、説明と実体を独立レビューした構成は `reviewer` とする。
- `Co-Authored-By` は著者表示に併用してよいが、model と reasoning がないため `AI-Agent` の代用にしない。
  セッション URL は commit message にも PR 本文にも記録しない (2026-07-17 ユーザー裁定: 履歴に永続し公開時に
  session の存在と ID を露出するため)。機械抑止は `.claude/settings.json` の
  `attribution.sessionUrl=false`。
- トークン数・利用枠・料金は対象外。工数や棄却 finding は `docs/worklog.md` 冒頭の書式で worklog か
  一次資料へ残す。

## commit 前の確認

関与した構成は自己申告でなく、可能なら UI・CLI の表示・設定・実験ロールの frontmatter で確認し、値の
欠落規則は「必須形式」に従って推測で埋めない。通常列は「message file → `--message-file` rc=0 →
`commit -F` → 既定 full-history 監査」で、既定 full-history を権威とする。

## 条件 dispatch

| key | 発火条件 | 読む節 |
|---|---|---|
| correction | 固定 target の forward correction を扱う | `docs/provenance/correction.md`: `PR-C01`, `PR-C02`, `PR-C03` |
| message-file | commit 前に message を検査する | `docs/provenance/audit.md`: `PR-A01` |
| history | commit 後・別 range の履歴を監査する | `docs/provenance/audit.md`: `PR-A02`; `docs/provenance/correction.md`: `PR-C03` |
| analysis | provenance を比較や改善判断に使う | `docs/provenance/audit.md`: `PR-A03` |

reference が不在・非一意・読取不能なら操作を止める。非該当節は読まない。
