単独段 dispatch: stage=author; sandbox=read-only; role=author (merge 合成の監査と merge message の起草)

## この依頼で行うこと

**file を 1 つも書かない。** あなたは read-only sandbox で走るので file を書けない。
成果物は**最終メッセージの本文に全文**を出す。親がそれを逐語で file へ写す。

依頼は 2 つである。

1. **merge の合成を監査する。**
2. 監査結果に基づいて **merge commit の message を起草する。**

## 対象

- wave 側 tip: `d7495dc7e` (branch `worktree-dev-wave-t1851-unit-a`)
- main 側 固定 SHA: `f2cca136ae2724899df10ed191030b6f104d57bf`
- merge-base: `086694d8c5ccd8be5a1fe8eb0475a208b896d952`

**両親が共に変更した file は次の 3 件**である。うち 2 件が実装面である。

- `orchestrator/campaign/attempt_registry_core.py`
- `orchestrator/tests/test_attempt_registry_core_s8b_profile.py`
- `docs/dev-wave/operations.md`

自動 merge は競合を出さない見込みだが、**競合が無いことは合成が健全であることを意味しない。**
それを確かめるのがこの依頼である。

## 必読事項の射影

作業 repository は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a` で、
その HEAD が wave 側 tip である。main 側の現物は repo から直接読めないので、次の絶対パスに
射影してある。**読めなければ即停止**し、読めなかった path を報告して終われ。

merge-base から見た**両側の差分**:

- `/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/merge-refs/main-side.attempt_registry_core.py.diff`
- `/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/merge-refs/wave-side.attempt_registry_core.py.diff`
- `/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/merge-refs/main-side.test_attempt_registry_core_s8b_profile.py.diff`
- `/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/merge-refs/wave-side.test_attempt_registry_core_s8b_profile.py.diff`
- `/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/merge-refs/main-side.operations.md.diff`
- `/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/merge-refs/wave-side.operations.md.diff`

**main 側の現物 (全文)**:

- `/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/merge-refs/main-current.attempt_registry_core.py`
- `/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/merge-refs/main-current.test_attempt_registry_core_s8b_profile.py`
- `/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/merge-refs/main-current.operations.md`

wave 側の現物は repo の HEAD をそのまま読めばよい (同 dir にも `wave-current.*` として置いてある)。

本 wave の裁定と背景:
`/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b/s4-adjudication.md`

## 監査の要件

**競合の有無ではなく、意味の合成を見る。** 少なくとも次を検査せよ。

1. **main 側が `attempt_registry_core.py` へ足した検査**が、wave 側が同 file へ入れた変更 (v2 profile の
   terminal 検査経路、slot codec、binding、terminal writer 周辺) と**意味的に干渉しないか**。
   特に、main 側が genesis の解析へ足した schema 分岐が、wave 側が使う schema 世代を
   誤って新しい拒否経路へ落とさないかを、両側の現物を読んで判定せよ。
2. **main 側と wave 側が同じ関数・同じ定数・同じ受理集合を別方向へ変えていないか。**
   片方が広げ片方が狭めている箇所があれば名指しせよ。
3. **`test_attempt_registry_core_s8b_profile.py`** で、main 側が足した test が wave 側の実装で
   落ちる可能性、または wave 側の test が main 側の実装変更で落ちる可能性を判定せよ。
   落ちうるなら、どの test 関数がどの理由で落ちるかを名指しせよ。
4. **`docs/dev-wave/operations.md`** は両側とも節の追記である。**同じ節を両側が編集していないか**、
   編集していれば意味が両立するかを判定せよ。
5. 干渉が無いと判定する場合も、**なぜ無いと言えるか**を file:line で示せ。
   「競合が出なかった」を根拠にしてはならない。

## 出力形式

最終メッセージに次の 2 節をこの順で置け。他の前置きを書かない。

### 1 節: `## 監査結果`

上の 1〜5 それぞれについて、判定 (干渉なし / 干渉あり) と根拠を file:line で書く。
**干渉ありと判定した場合は、その内容を 2 節の message 本文にも必ず書く** (隠して merge させない)。
各主張に [実測] / [推測] を付ける。行番号・件数は必ず [実測] にする。

### 2 節: `## merge message`

merge commit の message を**全文**、code fence の中に置く。次を満たすこと。

- 1 行目は `merge(main): ` で始まる 1 行の要約。
- 本文は日本語。何を取り込んだか、両親が共に触った 3 file の合成をどう監査したか、
  その結論を書く。**専門的な内部用語を避け、第三者にも読める平易な日本語**にする。
- 事実だけを書く。テストを走らせていないので「テスト緑」と書いてはならない
  (あなたは pytest を走らせられない)。
- 末尾は次の 3 行を**この順で、空行を挟まず 1 ブロック**で置く。

```
AI-Agent: product=codex; model=gpt-5.6-sol; reasoning=xhigh; role=author; scope=t1851-c1b-acceptance-merge
AI-Agent: product=claude; model=claude-opus-5; reasoning=default; role=manager
Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

## 制約

- 読取専用。実装しない。file を書かない。pytest を走らせない (走らせられない)。
- 出力へ結合文字 U+0300〜U+036F を使わない。
- 三軸語 (`ycsb_rratio` / `ycsb_zipf_skew` / `ycsb_rmw`) の値を message 本文へ書かない。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力の最後に `## 総括` 節を置き、干渉の有無と merge 可否を 6 行以内で書け。
