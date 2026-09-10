## 総括

現 plan のままの land は不受理です。

F79 の完全再現では新検査は確実に発火し、恒真ではありません。一方、より一般的な「既存 entry を指すが、その entry に同じ T が存在しない carry」を緑にします。実 corpus に既に 4 件あります。また、番号付きに見える不正 filename と README 行の欠落を「対象外」に落とせる経路、変異の帰属不成立があります。

read-only の静的レビューのみです。pytest と `tools/check_docs.py` 本体は実走しておらず、「緑」とは判定していません。

## F79 の再現追跡

結論は「発火する」です。

1. `worklog-phase3-0802-106-110.md` は plan の番号付き filename 文法に合い、主張範囲は `(106)〜(110)` になります。[plan.md:31](/home/SFC/tanab/.claude/jobs/6a7dec0f/tmp/t329/plan.md:31)

2. F79 当時の本文抽出結果は `{106,107}` です。[failures.md:2571](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/docs/failures.md:2571)

3. archive loop 末尾の filename 照合で、期待件数 5、実体件数 2、欠番 `108〜110` となり filename finding が出ます。[plan.md:22](/home/SFC/tanab/.claude/jobs/6a7dec0f/tmp/t329/plan.md:22)

4. 全 archive 入力が完全なら、`(110)` を指す carry は universe に参照先がなく、各 carry 行でも「宙吊り参照」が出ます。[plan.md:64](/home/SFC/tanab/.claude/jobs/6a7dec0f/tmp/t329/plan.md:64)

5. README 行も `(106)〜(110)` と解釈され、同じ `{106,107}` に対して欠番 `108〜110` を返します。現在の復旧済み行は [README.md:255](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/docs/archive/README.md:255) です。

したがって、元の F79 は filename、README、carry の最大 3 経路で赤になります。ただし、以下の除外経路では F79 同型を逃がせます。

## 所見

### 1. [real] 親実測は既に古く、しかも弱い述語だけを測っている

レビュー時点の同じ文法による静的再集計は、archive 424 件、番号付き 415 件、carry 参照先 ordinal 505 種でした。plan の 423／414、brief の 504 から既に 1 件ずれています。ordinal が不在の参照は 0 ですが、これは「同じ T の本文へ到達可能」を証明しません。

**成果物影響:** Stage 4 が 504 種を固定 positive corpus として扱うと、実装時 HEAD に追加された archive／参照が受理証拠から外れ、canonical green の前提を認証できません。

**file:line:** [brief.md:36](/home/SFC/tanab/.claude/jobs/6a7dec0f/tmp/t329/brief.md:36)、[plan.md:11](/home/SFC/tanab/.claude/jobs/6a7dec0f/tmp/t329/plan.md:11)、[worklog-phase3-0816-579.md:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/docs/archive/worklog-phase3-0816-579.md:1)

### 2. [real] entry の実在だけでは carry の実体を保存しない

plan は task ID を収集しますが、検証するのは参照 ordinal が universe にあるかだけです。実 corpus では entry `(77)` の次の 4 行が `(73)` を指しています。

- `[T-209]`
- `[T-208]`
- `[T-210]`
- `[T-211]`

ところが entry `(73)` の次の一手にも本文全体にも、この 4 ID はありません。提案検査はすべて緑にします。`spool_fold` 側は、最新 active chain について同じ T の不在、循環、同一・未来参照を既に拒否しています。

さらに `worklog-phase3-0730-1000.md` を current から参照する正例は、current の source ordinal を `1001` 以上へ変更しないと未来参照を正例として固定します。

**成果物影響:** entry 番号だけ残して T 本文・逐語・持ち越し理由を失う F79 同型が緑になり、裁定や proof chain が到達不能なまま certified 選択へ使われます。

**file:line:** [plan.md:57](/home/SFC/tanab/.claude/jobs/6a7dec0f/tmp/t329/plan.md:57)、[plan.md:164](/home/SFC/tanab/.claude/jobs/6a7dec0f/tmp/t329/plan.md:164)、[worklog-phase3-0731-77.md:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/docs/archive/worklog-phase3-0731-77.md:74)、[worklog-phase3-0731-73.md:6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/docs/archive/worklog-phase3-0731-73.md:6)、[spool_fold.py:1565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/spool_fold.py:1565)

段 4 では、少なくとも「参照先 entry の次の一手に同じ T がある」「参照先 ordinal は source より小さい」を scope 内へ入れるか、別裁定パッケージへ明示的に送る必要があります。前者なら既存 4 件は brief 不変条件 1 に従い、検査を緩めず内容欠落として扱うべきです。

### 3. [real] filename 除外は構文分類ではなく fail-open な正例 allowlist

番号付きと認識するのは `worklog-phase3-...` の 2 文法だけで、その他すべてを「番号を名乗らない」に落とします。例えば次はすべて検査を回避します。

- `worklog-phase3-0802-106-110-copy.md`
- `worklog-phase4-0901-600-605.md`
- production に置かれた `worklog-synthetic.md`

前者の本文が `{106,107}` でも、filename 範囲、内部 carry、README 範囲がすべて免除されます。既存テスト fixture を修正しないために `worklog-synthetic*.md` まで legacy 扱いする計画は、brief の「日付だけの旧 archive」という除外より広いです。

**成果物影響:** 名前に番号範囲が見えている破損 archive を未採番扱いして受理し、欠落 entry と宙吊り参照を archive／レポートから見えなくします。

**file:line:** [brief.md:39](/home/SFC/tanab/.claude/jobs/6a7dec0f/tmp/t329/brief.md:39)、[plan.md:31](/home/SFC/tanab/.claude/jobs/6a7dec0f/tmp/t329/plan.md:31)、[plan.md:140](/home/SFC/tanab/.claude/jobs/6a7dec0f/tmp/t329/plan.md:140)、[check_docs.py:1700](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:1700)

必要なのは三値分類です。

- 正規の legacy date-only／phase-range 名: 除外
- 正規の numbered 名: 検査
- それ以外の `worklog-*.md`: malformed filename として赤

### 4. [real] README の「全 numbered archive に一意な正規行がある」ことを検査していない

既存到達性検査は filename が README 全文のどこかに含まれれば通ります。plan は「現在の収容物」の各行を検査しますが、全 numbered archive がその節にちょうど 1 行現れたかという postcondition を持ちません。

したがって、正規行を削除し、README の別節や単なる説明文へ filename を書けば、既存到達性は通り、新 README validator は対象行を一度も見ません。filename と本文が一致していれば全体が緑です。

**成果物影響:** README 索引から archive の正規範囲行が消えても受理され、人間とレポート生成側が参照する収容範囲が欠落・陳腐化します。

**file:line:** [check_docs.py:5012](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:5012)、[plan.md:25](/home/SFC/tanab/.claude/jobs/6a7dec0f/tmp/t329/plan.md:25)、[plan.md:95](/home/SFC/tanab/.claude/jobs/6a7dec0f/tmp/t329/plan.md:95)

`seen_numbered_names` を持ち、実在 numbered archive の key 集合と正規行の key 集合が一致し、各 key が 1 回だけ現れることを I/O 追加なしで確認すべきです。

### 5. [疑い] 未裁定の受理集合変更が 2 件ある

現在の archive title 文法は、ordinal なしと `(続き)` を受理します。plan は numbered archive 内ではこれを新たに赤にします。安全側ですが、brief が承認したのは entry 集合と主張範囲の一致であり、継続 H2 自体の禁止までは明記していません。

逆方向では、README／filename の日付は構文として読むだけで、実体 entry の先頭・末尾日付とは比較しません。entry ordinal が一致すれば、虚偽の日付範囲が緑になります。

**成果物影響:** 前者は従来受理された継続形式を未裁定で拒否し、後者は README の日付索引を誤ったまま受理します。

**file:line:** [check_docs.py:772](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:772)、[plan.md:55](/home/SFC/tanab/.claude/jobs/6a7dec0f/tmp/t329/plan.md:55)、[plan.md:87](/home/SFC/tanab/.claude/jobs/6a7dec0f/tmp/t329/plan.md:87)、[spool_fold.py:2213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/spool_fold.py:2213)

段 4 で、継続 H2 禁止と日付一致が T-329 の受理集合に含まれるかを明記する必要があります。

### 6. [real] 変異候補の一部は単一理由性を満たさない

| 変異候補 | 先取りする検査 | 帰属不能の理由 |
|---|---|---|
| filename を min/max のみにする | 同じ fixture の README 集合検査 | filename 検査を殺しても入力全体は README 側で赤のまま |
| README を min/max のみにする | 同じ fixture の filename 集合検査 | 同様に受理集合は変わらない |
| README だけ `10〜11`、実体 `{10,11,12}` | min/max 実装自身 | actual max が 12 なので、min/max だけでも赤になる |
| exact F79 を `_CLEAN_WORKLOG` に足す | 既存 archive/current 順序検査 | F79 の末尾 `(107)` と current 先頭 `(1)` が同じ 8 月 1 日になり、範囲検査を消しても既存順序検査が赤 |
| README pass で再読する | なし | I/O 契約違反であり、受理集合を変えないため mutation kill ではない |

内部欠番の個別 validator は helper 単体の diagnostic pin にするか、filename と README の両方を min/max 化する二層変異として事前登録すべきです。exact F79 fixture は current を `(111)` 以後・8 月 3 日以後へ置き、既存順序赤を消す必要があります。

**成果物影響:** このままでは「KILLED」と記録しても壊れた gate の受理集合が変わっておらず、検査の実効性を偽って認証します。

**file:line:** [plan.md:182](/home/SFC/tanab/.claude/jobs/6a7dec0f/tmp/t329/plan.md:182)、[plan.md:200](/home/SFC/tanab/.claude/jobs/6a7dec0f/tmp/t329/plan.md:200)、[mutation.md:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/docs/dev-wave/mutation.md:5)、[test_check_docs.py:365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/orchestrator/tests/test_check_docs.py:365)、[check_docs.py:1801](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:1801)

### 7. [real、scope 外残存面] fold producer 自体は変更・実証されない

公式 dev-wave land は、fold apply 後かつ commit 前に `check_docs.py` を実行し、赤なら rollback します。この公式経路は新検査の恩恵を受けます。

一方、`spool_fold.py` の直接 CLI は `apply_fold()` 後に `check_docs.py` を呼びません。producer の rotation テストも README に名前が入ったことまでしか固定していません。したがって「fold producer が範囲整合を保証する」とは言えません。

**成果物影響:** 公式 land の certified 台帳は保護されますが、直接 fold 経路では不一致 archive／README が canonical bytes に適用され、後続レポートや台帳参照が壊れ得ます。

**file:line:** [dev_wave_land.py:2211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/dev_wave_land.py:2211)、[dev_wave_land.py:2340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/dev_wave_land.py:2340)、[spool_fold.py:3435](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/spool_fold.py:3435)、[test_spool_fold.py:1918](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/orchestrator/tests/test_spool_fold.py:1918)

これは二択の裁定パッケージ候補です。

- 推奨: T-329 は公式 land の postcondition gate と明記し、実 `check_docs` による rotation 統合テストを追加する。直接 CLI の producer postcondition は別タスクへ送る。
- 拡張案: `spool_fold` の plan 出力にも同じ範囲 postcondition と producer テストを追加する。

## 診断の質

提案済みの dangling carry、重複 ordinal、範囲差分の文言は、path、line、T、ordinal、欠番、範囲外を返すため概ね良好です。F79 なら `欠番=108〜110` と圧縮表示すれば、人間は対象 archive を直せます。

一方、numbered archive 内の ordinal なし／`(続き)` H2 は文言が未規定です。`path:line`、H2 title、filename が numbered であるため拒否したことを必須にすべきです。これは受理集合を変えない診断仕様なので nit です。

**成果物影響:** なし。修復箇所の特定時間だけに影響する nit です。

**file:line:** [plan.md:55](/home/SFC/tanab/.claude/jobs/6a7dec0f/tmp/t329/plan.md:55)

段 4 では、少なくとも所見 2、3、4、6 を plan v2 と変異事前登録へ反映しない限り、実装段へ進めるべきではありません。