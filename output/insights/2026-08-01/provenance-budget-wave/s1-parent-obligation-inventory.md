# 親側の独立義務目録 (段 1、縮約前 8,942 bytes 版)

段 2 planner の目録と突き合わせるための、親が独立に作った baseline。番号 `O**` は本 wave 内の作業用 ID で、
外部からは参照されない。**機械束縛** = checker / test / hook が逐語または構造として読む箇所。

## 目的 (446 bytes)

- O1 記録の正本は Git commit message。worklog へ同じ情報を二重記録しない
- O2 規約は導入 commit 自身と以後の新 commit に適用。既存履歴は書き換えない

## 必須形式 (2,867 bytes)

- O3 すべての commit は message 末尾に trailer を 1 行以上持つ
- O4 フィールドの順序と区切りは固定、値に `;` と改行を含めない
- O5 必須なのは「本文と空行で区切った最終段落 (Git が trailer と認識する位置) に `AI-Agent` がある」こと。
  本文の有無は任意。ここまでが機械検査対象 — **機械束縛 (構造)**
- O6 `Co-Authored-By` 併用時は空行を挟まず連続。CAB 候補行はすべて最終 trailer block に置く —
  **機械束縛 (逐語 exactly-once)**
- O7 checker は候補行数と隔離 Git parser の認識数を照合し、導入 commit 以後へ適用 (F25)
- O8 trailer の形式 literal (`product=`/`model=`/`reasoning=`/`role=`/任意 `scope=`) — **機械束縛 (regex 対応)**
- O9 `product` は `codex` / `claude`、将来は安定した小文字識別子
- O10 `model` は実行面の slug。表示名のみなら小文字化 + 空白→`-`。非表示は `not-exposed`、
  確定できない場合は `unknown`。世代・内部モデルを推測しない
- O11 `reasoning` は選択面の表示値を小文字識別子。表示名のみなら同じ変換。明示的既定選択は `default`、
  設定なし/非表示は `not-exposed`、確定できない場合は `unknown`
- O12 `role` は author / reviewer / researcher / manager / integrator の 1 つ。複数役割は行を分ける —
  **機械束縛 (`ROLES`)**
- O13 `scope` は任意 (2026-07-17 導入)、短い識別子。**同じ role が複数行なら全行に必須**、単独行は省略可。
  導入 commit 以降のみ適用し遡及しない。checker も導入 commit を内容検出して以降だけ検査する —
  **機械束縛 (`_scope_policy_commit` の `-S "scope="`)**
- O14 `product` / `model` / `reasoning` / `scope` は `[a-z0-9][a-z0-9._-]*` — **機械束縛 (`IDENT`)**
- O15 AI 非関与 commit は `AI-Agent: none` の 1 行
- O16 `AI-Agent: none` は唯一の `AI-Agent` trailer のときだけ有効。構造化行との併記は禁止
- O17 導入 commit より後の trailer 欠落は human-only でなく規約違反

## 実装面の Codex author 契約 (1,519 bytes)

- O18 本節導入 commit 以後、実装面を変更する AI 関与 commit は Codex author を必須 —
  **機械束縛 (逐語 exactly-once + epoch 検出)**
- O19 実装面 = `orchestrator/` `tools/` `hooks/` `.github/` `.codex/` `external/` の非 Markdown、
  `patches/` の patch/diff、所在を問わない Python・Shell・C/C++・CMake 等の実行可能資材 —
  **機械束縛 (prefix / suffix / basename 表)**
- O20 テスト・checker・hook・probe・harness・生成器・機械設定も production 挙動の有無によらず含む
- O21 該当 commit は `product=codex; ...; role=author` を 1 行以上含める。Claude 親は
  manager / integrator / reviewer、docs を書いたなら docs scope の author として記録できる
- O22 docs-only、ログ・計測結果・凍結記録だけの変更、AI 非関与の `none` は対象外
- O23 小さい・軽量版・test-only・probe-only・production 挙動 0 は免除理由にならない。
  Codex が実行不能なら Claude が代行せず停止し、例外の必要性をユーザー裁定へ返す
- O24 Codex 不可用時はユーザー裁定のうえ waiver 形式リテラルを最終 block へ `role=author` と併記。
  規則と抑止は D105 — **機械束縛 (逐語 exactly-once)**
- O25 checker は変更 path と trailer を照合。遡及せず導入 commit から適用。
  `--message-file` では staged path に同じ検査

## 記録単位 (1,629 bytes)

- O26 同一 product・model・reasoning・role の子が複数でも行を人数分重複させない。
  異なる構成・役割は別行、同一構成が別作業なら `scope` で行を分ける
- O27 採用判断または commit 内容へ実質的に影響した構成だけ記録。起動しただけ・読んだだけ・
  結果が使われなかった構成は記録しない
- O28 Git 操作の機械代行は記録しない。範囲選定・競合解決・採否の判断を加えた場合だけ `integrator`。
  説明と実体の独立レビューは `reviewer`
- O29 `Co-Authored-By` は著者表示として併用可だが `AI-Agent` の代用にしない。session URL は
  commit message にも PR 本文にも記録しない (2026-07-17 ユーザー裁定、理由 = 履歴に永続し公開時に
  session の存在と ID を露出するため)。機械抑止は `.claude/settings.json` の `attribution.sessionUrl=false`
- O30 トークン数・利用枠・料金は trailer の対象外。エージェント工数や棄却 finding は worklog 冒頭の
  書式に従い worklog または一次資料へ残す

## `6b64d21` の一回限り forward correction (819 bytes)

- O31 共有済み `6b64d21...` は rewrite せず、strict descendant 1 件で補記する
- O32 `AI-Agent-Correction: target=<40hex>; product=...; role=integrator` の形式 —
  **機械束縛 (`RAW_AI_AGENT_CORRECTION` / target 定数)**
- O33 自身の `AI-Agent` と correction の物理 1 行は同じ最終 block に置く
- O34 checker の成立条件は連言: raw/canonical/final-block exact、selected set 内の両 commit、
  strict lineage、target 実欠落、candidate 1 件、**自身の通常 green**。相殺するのは target の欠落 finding だけ
  (D105 決定 1-a がこの「自身の通常 green」に依存)
- O35 一般 allowlist・設定・CLI 免除へ拡張しない
- O36 監査は両 commit を含む range か既定 full-history が権威。target 抜き `OLD_HEAD..HEAD` は補助で、
  初回伝播も免除しない
- O37 green 時は両 SHA を `forward-corrected=1` で示す

## commit 前の確認と監査 (1,466 bytes)

- O38 commit 前に、関与した構成を会話の自己申告だけでなく可能なら UI・CLI の選択表示・設定ファイル・
  実験ロールの frontmatter で確認する
- O39 非開示は `not-exposed`、記録時までに失った値は `unknown`。推測で埋めない (O10/O11 と同内容)
- O40 trailer として解釈されたかの確認コマンド
- O41 範囲監査コマンド
- O42 導入 commit から `HEAD` の欠落・排他・順序・形式の検査コマンド (`check_ai_provenance.py`)
- O43 `--range` / `--message-file` の使い分け。導入 commit より前の欠落は legacy で遡及違反にしない
- O44 この記録は観察データであり統制実験ではない。交絡があるので commit 数・成功率だけから
  製品・モデル・推論深度の優劣を断定しない (**D105 却下案 (f) が削除を明示的に却下した歯止め**)
- O45 改善判断ではタスク種別を揃え、手戻り・レビュー finding・テスト結果・所要時間と一緒に評価する

## 親が見た冗長 (削減の当て所)

- O10 / O11 / O39 が `not-exposed` / `unknown` / 推測禁止を 3 度書いている
- §commit 前の確認と監査 は fenced block が 3 つあり、`git log` の例示が 2 度出る
- §必須形式 の前置き 6 行が「必須なのは何か」を 2 通りに言い直している
- §目的 と §必須形式 冒頭で「導入 commit 以後に適用・既存履歴は不変」が重複 (O2 と O13/O25 の一部)
