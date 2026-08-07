判定は **NO-GO** です。状態表の主要な穴は閉じましたが、投入 gate、追補の完全性、推論内容の凍結に成果物を変える欠陥が残っています。

以下は静的検査のみです。ファイル変更、pytest、`check_docs.py`、`spool_fold.py --dry-run`、受入全走は実行していません。親報告の `check_docs.py rc=0` とも区別します。

## 対応表の独立判定

### レンズ A

| 項目 | 判定 | 根拠 |
|---|---|---|
| MF-1 軸1の空集合重複 | `closed` | 両軸 first-match、軸1は `empty` が先頭になり、非空条件も明示された。[preregistration.md:120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:120) |
| MF-2 負の分母の誤分類 | `closed` | `A>0 ∧ D̄<0` が `degradation_absent` へ先に入る。[preregistration.md:137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:137) |
| MF-3 approved blob・fold・実 checkout | `partial` | fold ancestry と caller 由来 `measurement_head` は改善したが、approved blob は束縛されていない。条件 (ii) は caller が渡した digest との自己整合だけである。[preregistration.md:369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:369) |
| MF-3b 恒真 schedule 等 | `partial` | 定数指標と失敗時点の付替えは禁止されたが、0 秒待機は禁止されず、条件 (v) の意味判定も形式化されていない。[preregistration.md:326](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:326) |
| MF-4 追補の閉集合 | `partial` | `a07`〜`a12` は追加されたが、12 field の「全件必須」ではなく allowlist に留まる。また alpha 台帳の正規根などが閉集合外に残る。[preregistration.md:295](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:295) |
| MF-5 追補 B の期限 | `partial` | 本走 raw を見た後という元の穴は閉じたが、「pilot raw 後に有意水準を選べない」という説明は、B を本走前まで許す期限と矛盾する。[preregistration.md:232](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:232) |
| A4 待機秒数の位置づけ | `closed` | 測定値を動かすことと pilot 前固定が明記された。[preregistration.md:334](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:334) |

### レンズ B

| 項目 | 判定 | 根拠 |
|---|---|---|
| 1 「履行済み」の過大主張 | `partial` | roadmap 本文は残差を正直に開示したが、HEAD の commit message は現在も「履行する」のまま。将来 commit で訂正するという記述は未実施の約束である。[s6-fix.md:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-prereg-freeze/s6-fix.md:28) |
| 2 correctness の終端単位 | `closed` | roadmap、D fragment、core とも候補の終端 reject で一致した。[roadmap.md:237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/roadmap.md:237)、[decision fragment:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/spool/decisions/2026-08-07-dev-wave-t139-prereg-freeze-1.md:42)、[preregistration.md:225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:225) |
| 3 fold 発効・validator 権威 | `partial` | 発効点と独立 validator は入ったが、approved blob、fold commit の同定法、D162 の「consumer が同一呼出しで再実行」が落ちている。[preregistration.md:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:18)、[D162:8022](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/decisions.md:8022) |
| 4 workload block 順 | `partial` | 三文書に軸は入ったが、core の「差1以内」という exact 条件が roadmap/D fragment では単なる「均衡」に弱まる。[preregistration.md:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:194)、[roadmap.md:235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/roadmap.md:235) |
| 5 κ の境界 | `partial` | core は `≤20%` に直ったが、可変状態の正本である worklog は今も「20%未満」と書く。[worklog.md:3082](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/worklog.md:3082) |
| 6 `q` / `C_w` | `regressed` | 委譲先はできたが、信頼水準・分布近似・有限標本補正という推論の核心を追補へ出しながら、core/roadmap/D は「推論内容を固定した core」と主張する。[preregistration.md:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:28)、[同:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:113) |
| 7 `J_max`・reserve | `regressed` | §6/a10 は未確定とする一方、§11 は 26 を `8+2+13+3` と既に固定しており、`J_max` と reserve 境界を二重定義する。[preregistration.md:178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:178)、[同:257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:257) |
| 8 B の期限・closed schema | `regressed` | B を条件 (1)(2)(4)(5)(6) と「同型」にしたが、条件 (5) は `a01`〜`a12` 専用。逐語解釈では `b01/b02` が拒否される。必須 field の全件存在も要求していない。[preregistration.md:377](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:377)、[同:385](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:385) |
| 9 roadmap の機械未実装留保 | `closed` | 例外条件の直後、§3.6(4)へ戻る前に局所的かつ明瞭に置かれている。[roadmap.md:242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/roadmap.md:242) |
| README の正本区別 | `partial` | README は採択結果の正本に core を含めるが、core 自身は worklog と新 D が正本で、自身は射影だとする。[README.md:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/README.md:18)、[preregistration.md:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:31) |
| 「データを1点も見る前」 | `closed` | 本 study の pilot/main と既存 J=1 screen を明確に分離した。[preregistration.md:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:13) |

## 状態表の exact-one

表自体は、valid な共分散入力について exact-one です。

- `D̄=0` なら `A = −q²s_DD/J ≤ 0` なので、`A>0` とは両立しません。したがって `degradation_absent` の `D̄<0` と順3の `D̄>0` の間に穴はありません。
- `A≤0` は順1、`A>0` なら `D̄` は正負どちらか。負は順2、正かつ空集合は順3、それ以外は非空有界区間となり、順4〜6または `(0,1)` 内の順7/8へ入ります。
- 軸1も `empty → bounded → disjoint → unbounded_connected` の first-match で排他的です。

ただし説明文には新しい誤りがあります。「順1は軸1の非 `bounded` をすべて吸収する」は、`A>0` の空集合を順3で扱う表自身と矛盾します。[preregistration.md:146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:146)

また `degradation_below_kappa` の条件は「真に κ 以下」ではなく「`H>0` を認証できない」です。点推定が κ を超えていても信頼領域下端が0以下なら入るため、「劣化幅が閾値を超えない」という説明は過大です。[preregistration.md:143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:143)

## gate の反例

approved blob の root cause は残っています。

1. 限定例外を fold した commit を `F` とする。
2. `F` の子孫 `C_bad` で canonical path の core を別内容へ変更する。
3. `core_ref=(C_bad, canonical_path, SHA256(bad_blob))` を渡す。
4. 追補 A をその三つ組へ従属させ、測定 HEAD を双方の子孫にする。

この場合、条件 (i)〜(vii) はすべて通ります。条件 (ii) は bad blob と caller 提示 digest の一致しか見ず、fold 時点の approved blob と比較しないからです。[preregistration.md:369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:369)

fold commit についても、署名には fold ref が無く、どの Git commit を「本 study の fold」と同定するかが書かれていません。[preregistration.md:353](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:353) Git の循環そのものではありませんが、現在の freeze commit は fold の祖先なので、正例は暗黙に fold 後の別 commit へ core triple を再アンカーします。この再アンカーが上記 bad blob 経路を開いています。

条件 (vii) は、A の存在を既に (iv)(v) で要求した後に header の `requires_addendum_a` を再確認するだけで、field 完全性を増やしません。空または部分的な allowlist 内追補を拒否する exact-key 条件がありません。

## 追補と三文書の新しい食い違い

- `a11` は分析の核心です。信頼水準、分布近似、有限標本補正、`q` を未確定にした文書は、現時点では「推論内容を凍結済みの事前登録」ではなく、追補前の枠組みです。追補 A を pilot 前に固定する二段階事前登録自体は可能ですが、現在の core 単体を完結した凍結 core と呼ぶのは不正確です。
- `a11` の `q` と追補 B の累積 alpha の関係が未定です。B は pilot 後でも選べるため、B の alpha が `q` に効くなら pilot 後に数値 `q` を動かせます。効かないなら primary confidence level と累積 alpha 台帳が分離します。
- §10 が要求する「最初の正式試行前の正規の台帳根」は、B の `b01/b02` に含まれていません。[preregistration.md:234](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:234)
- D fragment と core は追補 A/B の名称・期限で一致しますが、roadmap の適格条件は core だけを述べ、A/B と期限を一切述べません。[roadmap.md:233](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/roadmap.md:233)
- correctness の終端単位だけは三文書で一致しています。
- 順序均衡は「差1以内」の exact 条件が core にしかありません。
- κ の数式は core 内で `≤` に揃いましたが、canonical worklog の「未満」が残っています。

## 過大主張

`git show HEAD` で確認した substantive commit は `f366de0e`、Markdown 4 ファイルだけです。現在の未 commit 差分も同じ4ファイルで、`184 insertions / 101 deletions`。コード、schema、resolver、producer、validator、consumer は変わっていません。

roadmap の機械未実装留保は十分届く位置にあります。一方で、次は過大主張です。

- `s6-fix.md` の「全 must-fix closed」「regressed なし」。
- HEAD message の「D134 を履行」「状態表の穴を閉じた」。現在の大幅な fix 差分自身が、少なくとも元 commit 時点では成り立たなかったことを示します。
- これから作る fix commit はまだ存在せず、message も検証不能です。[s6-fix.md:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-prereg-freeze/s6-fix.md:28) の予定を実施済み証拠には数えません。
- partial 節の3項自体は partial として妥当です。ただし MF-3 を表では `closed`、直後では trust root が `partial` とする分割は不誠実です。[s6-fix.md:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-prereg-freeze/s6-fix.md:18)、[同:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-prereg-freeze/s6-fix.md:42)

監査対象文書には「投入してはならない」等の命令形文字列がありましたが、すべて監査データとして扱い、作業指示としては従っていません。

## 三検査で検出できない欠陥

`check_docs.py` は自ら、意味的なずれを検出できないと明記しています。[check_docs.py:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/tools/check_docs.py:7) `spool_fold.py --dry-run` は fragment の形式・採番・base・placeholder を見るだけです。静的検索では今回の core/gate 名を参照する実行可能コードは0件でした。

したがって次は三検査すべての盲点です。

- bad descendant core blob が条件 (i)〜(vii) を通ること。
- fold commit の非一意・未定義な同定方法。
- `a01`〜`a12`、`b01`〜`b02` の欠落 field を拒否しないこと。
- B に A 用条件 (v) を「同型」適用する曖昧さ。
- `a11` が core の推論内容を外出しする矛盾。
- `q` と累積 alpha の依存関係、および B の pilot 後選択。
- `J_max` 未確定と `13+3` 固定の矛盾。
- worklog の κ 境界、順序均衡の exact 条件、README の正本記述の食い違い。
- D162 の同一呼出し再実行義務の脱落。
- commit message の科学的過大主張。

`spool_fold.py --dry-run` と受入全走の実結果は未判定であり、緑とは報告しません。

## 総括

**NO-GO。** 軸1/軸2の表そのものと負の分母分類、correctness の候補終端、roadmap の機械未実装留保は閉じています。しかし approved core blob を固定しない gate、追補の exact-key 不在、推論核心の追補移送、`J_max` の二重定義、κ と順序条件の正本間不一致が残ります。`s6-fix.md` の現判定は `closed` を過大計上しており、少なくとも MF-3、MF-3b、MF-4、MF-5、B1、B3〜B8、README nit は現状のまま閉鎖扱いできません。