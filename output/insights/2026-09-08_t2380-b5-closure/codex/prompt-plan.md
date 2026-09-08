単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/9218ced6/tmp/t2380/brief.md (親の段 1 brief。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md (凍結済み部分登録。§3.1〜§3.5、§4.1、§4.2、§4.5、§5.3 が生成器の入力。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis1_search/catalog.py (軸 1 の先例。構造と直列化の参考。import してはならない。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis1_search_catalog.py が在れば test の書式の参考 (無ければ `ls orchestrator/tests | grep axis1` で近い test を 1 本読む)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-01-axis3-registration-preflight.md (seal の先例。読めなければ即停止)

## 役割

あなたは dev-wave 段 2 のプラン起草者である。read-only sandbox なので書込み可能な tmp は無く、pytest は走らせなくてよい (静的検査でよい)。
brief の scope・不変条件・(P1)〜(P5)・変更面の実アンカー表・「catalog 生成器の契約」に従い、**file:line 粒度の実装プラン**を書く。
プランは commit 2 (生成器 + test + 生成 JSON) を主対象とし、commit 1 / commit 3 の docs については「凍結文のどの節のどの規則を、生成器のどの関数が担うか」の対応表だけを書く (docs 本文は親が書く)。

## 書くこと

1. `orchestrator/axis_b5_search/catalog.py` の構成: 定数 (6 block 85 語を §3.1 の列挙順・表記どおり、10 枝の block 順、control 14 本、venue 8 × 年 1993〜2026)、
   関数ごとの入出力、§3.3 規則 1〜7 の各規則を担う関数名、percent encoding の実装方針 (`urllib.parse.quote` の `safe` をどう与えるか、`,` を符号化しない扱い)、
   JSON 直列化 (sort_keys / indent=2 / ensure_ascii=False / 末尾 newline)、CLI (`--output` / `--verify`)。
2. 凍結文の規則 → 生成器の関数 → test の対応表 (§3.1 互いに素・85 語、§3.3 規則 3〜7、§3.3 照合例 `B5-Q10@dblp/T01-O01`、§3.5 直積 7 枝 = 1602、§4.1 control 14 本と `B5-CTL-AND2023@dblp` の同一 bytes、§4.5 venue 272 stream の template と ID)。
3. `orchestrator/tests/test_axis_b5_search_catalog.py` の test 関数一覧 (名前・検査内容・期待値の出所となる凍結文の節)。
4. 凍結文の規則に**曖昧・不足・矛盾**があり、生成器が決定的に bytes を作れない箇所を全部列挙する (例: 単一 block の control (`X` 単独) を規則 3・4 でどう括るか、
   OpenAlex で複数語 term を引用符なしで置く規則 4 の帰結、`B5-OP-3` の arXiv 側の日付節、DBLP `q=` の `%20` と `quote` の関係)。各項目に「凍結文から一意に読める / 読めないので親の erratum 裁定が要る」を付け、読めない項目には推奨の読みを 1 つ添える。
5. 変異 matrix の候補 (実装後に親が事前登録する): 変異位置 (関数・行の目安)、期待する赤 test、単一理由性の懸念。8〜12 件。
6. リスク: 既存 test (`orchestrator/tests/test_check_docs.py` の byte 予算・dispatch 表、claim-survey README の一覧行、`tools/check_docs.py` の関連 lint) に本 wave の docs / JSON 追加が引っかかる可能性を `grep` で確かめて書く。
   特に `docs/related-work/claim-survey/*.json` を tracked に足すことが `check_docs.py` や provenance checker (実装面判定は path と拡張子: `docs/` 配下の `.json` は実装面か) にどう扱われるかを、`tools/check_ai_provenance.py` の判定コードを読んで書く。

## 禁止

- ファイルを 1 つも書かない・変更しない。git 操作をしない。外部 network を使わない。
- 凍結済み 2026-09-07 / 2026-09-05 文書の変更を提案しない (erratum は後継文書で行う)。
- 新しい gate・検査・台帳・一般化を提案しない (本題の生成器と test だけ)。
- 出力に結合文字 U+0300〜U+036F を使わない。

## 出力形式

見出しは全部 H2 (`## `) で書く。最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
予算が尽きそうなら途中結論をこの形式で書いて終われ (無出力が最悪)。

## 構成
## 規則対応表
## test 一覧
## 曖昧・不足・矛盾
## 変異候補
## リスク
## 総括
