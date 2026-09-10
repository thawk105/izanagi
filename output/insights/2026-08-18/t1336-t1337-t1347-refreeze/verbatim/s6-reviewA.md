## 総括

必読資料はすべて読めた。静的レビューの結果は **NO-GO**。採用所見 8 件のうち、A-2・A-5・A-6・A-8 は規範文が追加されたものの、拒否条件または権威への束縛が不足している。

| 採用所見 | 照合結果 |
|---|---|
| A-2 | 未完。数値制約と発効判定が矛盾し、`n` も判定入力へ束縛されない。RA-1・RA-2 |
| A-3 | 反映済み。主量は対差の有限な平均と標本 SD に限定され、診断量は成立可否へ伝播しない |
| A-4 | 反映済み。二表の consumer 境界と消える保証 4 件が明記されている |
| A-5 | 未完。閉集合の要素と分類権威が未定義。RA-3 |
| A-6 | 未完。唯一性を主張する root が事前登録へ固定されない。RA-4 |
| A-7 | 反映済み。時刻・環境・実装 identity と 3 分類がある |
| A-8 | 未完。byte 同一性に例外を設け、裁定より弱くなった。RA-5 |
| A-12 | 反映済み。機械配線が未完成であることも明記されている |

### RA-1

- **主張:** 不正な数値契約を未発効にする規範は、同じ文書の発効定義と現判定器により発火しない。
- **証拠:** 新規範は不正値を未発効とする一方、発効定義は型・単位・範囲を検証対象外と明記する（[8c:255](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:255)、[8c:261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:261)）。実装も非空の canonical JSON を内容に関係なく `FILLED` とし、発効判定は全欄が `FILLED` かだけを見る（[s8c_preregistration.py:806](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/campaign/s8c_preregistration.py:806)、[s8c_preregistration.py:1727](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/campaign/s8c_preregistration.py:1727)）。
- **深刻度:** blocker
- **成果物影響:** 後続 evaluator が揃った際、負の下限や不正な標本数でも事前登録が発効し、公式判定と certified 選択を作れる。
- **推奨:** §6 の「対象外」を撤回し、数値欄の exact schema、型、有限性、単位、方向、範囲を発効判定器が検証することを条件 7 の証拠契約へ追加する。

### RA-2

- **主張:** 登録した `n` と実際の反復数を一致させる規範がなく、`n` は書くだけの欄になっている。
- **証拠:** 判定表が要求するのは反復 2 以上だけで、観測数と登録 `n` の一致を要求しない（[8b:440](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8b-descriptor-design.md:440)）。`n` の制約は整数かつ 2 以上だけで（[8b:463](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8b-descriptor-design.md:463)）、8c 条件 7 も完全 block の復元だけを要求する（[8c:217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:217)）。例えば `n=8` を登録し、2 反復だけの完全 block を作る実装を本文は拒否しない。
- **深刻度:** blocker
- **成果物影響:** 事前登録より小さい標本で公式判定が成立し、ばらつきと certified 選択が変わる。
- **推奨:** manifest の各 cell に exact `n` 行を要求し、全 cell の観測反復集合が登録 `n` と完全一致しなければ事前登録未発効にする。

### RA-3

- **主張:** 「再走を許す失敗理由は閉じた集合」という記述は要素も分類権威も固定しておらず、低い結果を失敗へ分類する経路を閉じない。
- **証拠:** §10.5 は閉集合とだけ記し、列挙、schema、分類主体、分類時点を固定していない（[8b:520](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8b-descriptor-design.md:520)）。8c 条件 4 も同じ文言を再掲するだけである（[8c:204](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:204)）。出力を見られる非信頼側が、信頼側の読取り前に `parser_error` や終端欠落を付ける実装を構成できる。
- **深刻度:** blocker
- **成果物影響:** 良い attempt だけが primary value となり、公式平均、対差、最終選択が上方へ偏る。
- **推奨:** 許可理由を世代 record に exact enum として凍結し、raw output の生成前に trusted launcher が外部証拠から分類した create-only receipt が無ければ再走を拒否する。

### RA-4

- **主張:** master registry root の唯一性は事前登録された権威へ束縛されず、複数 registry がそれぞれ自分を唯一と名乗れる。
- **証拠:** §10.5 と条件 4 は root を測定前に固定するとだけ定める（[8b:523](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8b-descriptor-design.md:523)、[8c:209](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:209)）。第 6 世代 record には root path/hash や canonical pointer がなく（[g6:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/output/s8c-preregistration/condition-freeze/condition-freeze.v1.g6.json:1)）、成果物へ事後的に root hash を記録する要求しかない（[8b:536](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8b-descriptor-design.md:536)）。
- **深刻度:** blocker
- **成果物影響:** 複数 registry を実走して良い結果の root だけを公開でき、全 attempt 報告と公式対差が改変される。
- **推奨:** root の canonical path と初期 hash を内容 commitまたは発効束縛 recordへ固定し、freeze identity を key にした exclusive-create authority と第二 root の全履歴拒否を要求する。

### RA-5

- **主張:** 非干渉性は「実際に送る bytes が同一」としながら role-visible な nonce 等の差分を許し、A-8 の byte 同一裁定より弱い。
- **証拠:** actual payload と provider bytes の同一性を要求した直後に、事前列挙した nonce 等を例外にしている（[8c:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:96)、[8c:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:101)）。これは段 4 が採用した「真の holdout を跨いで byte 同一」に無かった例外である。
- **深刻度:** blocker
- **成果物影響:** 例外 field が対象別の安定ラベルになれば、off 側が対象を識別でき、6 cell の差を descriptor 効果として認証できない。
- **推奨:** role が受け取る最終 stdin は例外なしの byte 同一とする。transport 固有 metadata が必要なら role から不可視な trusted envelope 外へ分離し、比較対象 bytes を exact に定義する。

### RA-6

- **主張:** §10 が上書きを宣言していない旧本文に、床値利用と resume 拒否を要求する生きた規範が残る。
- **証拠:** §10 は上書き範囲を限定し、それ以外を不変としている（[8b:426](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8b-descriptor-design.md:426)）。しかし §7 は再利用軸へ floor の全規定を組み込むよう要求し（[8b:248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8b-descriptor-design.md:248)）、§9 の前提段落は resume 拒否の強化を要求したままである（[8b:284](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8b-descriptor-design.md:284)）。
- **深刻度:** must-fix
- **成果物影響:** consumer が旧参照を採れば床値関門または全面 resume 拒否が復活し、新しい公式判定・registry の受理集合と食い違う。
- **推奨:** §10 の上書き対象へこの 2 箇所を明示的に追加し、それぞれ新しい測定衛生規則と事前割当 registry へ読み替える。

### RA-7

- **主張:** §5 の未変更 JSON に古い floor 再測定要求が残り、新しい解除条件と文面上矛盾する。
- **証拠:** §4 は floor 再測定を解除条件から外す（[8c:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:153)）一方、§5 の `reopen_requires` は旧要求を保持する（[8c:184](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:184)）。
- **深刻度:** nit
- **成果物影響:** 現判定器は JSON の意味を消費しないため受理集合への現在影響はないが、人間向け再開条件は二義的になる。
- **推奨:** 段 4 の「§5 値を変えない」を守り、本 wave では変更せず、規範側でこの旧値が非権威であると明記するか、値を正式記入する次世代で是正する。

## 不変条件と検索結果

- correctness gate と build 分離は旧本文 [8b:201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8b-descriptor-design.md:201) の bytes が不変で、production code の変更もない。性能側の受理変更以外に correctness 側の拡大は見つからなかった。
- §5 は欄名 1 行だけが変更され、値セルと既存 prose は不変だった。
- file-first の全件検索では、8c の旧 floor 記述は RA-7、旧証拠契約は [8c:297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:297) で意図的 divergence と明記済み、workload 名漏れは [8c:195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:195) で未充足と明記済みだった。D496 の旧測り直し単位も [8c:311](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:311) が限界として明記している。
- 第 6 世代だけでは formal 発効も測定認可もできない。判定器が全条件を充足へ倒せないこと、起動・受入への結線が未完成であることは [8c:286](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:286) と [8c:376](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:376) に正直に書かれている。任意 process の起動を止める機構ではなく、formal 受理を不能にする境界である。
- 変更面と未追跡 record の結合文字は 0 件、禁止された三語も 0 件。`git diff --check` は無出力だった。
- 指示どおり pytest は実行していない。

## NO-GO

数値契約、失敗分類、registry 唯一性、非干渉性に具体的な file-drawer または識別漏れ経路が残る。  
少なくとも RA-1〜RA-5 を閉じ、RA-6 の上書き範囲を整合させるまで land 不可。