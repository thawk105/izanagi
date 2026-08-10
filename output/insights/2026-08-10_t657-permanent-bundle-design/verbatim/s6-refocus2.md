## タスク 1 — 1巡目残件の対応表

| ID | 判定 | 判定根拠・残る破れ方 | 成果物影響 |
|---|---|---|---|
| R-1 | `closed` | Q対象集合とA成分一覧の一致、Q hash束縛、X→A参照で元の偽Q構成は閉じた。 | — |
| R-2 | `regressed`（型2） | topology図は各commitを`H_base`の枝として示す一方、§5.1は各commitを直前commitの子に要求する。図を概念図とする注記はない。 | A/Q/Xのparent受理集合とprovenanceが実装解釈ごとに分岐する。 |
| R-3 | `closed` | 閉じたmanifest、fixtureとの全単射、検査node実行、`未定義`段の完了禁止を追加済み。 | — |
| R-4 | `closed` | 下位family自身の検証器、候補型の出口保持、降格accessor禁止を明記済み。 | — |
| R-6 | `partial`（型1） | §9.1は導入commitを単数扱いするが、現行履歴検査は同一bytesの削除・再作成で複数導入を許す。導入commitなしのruntime成果物も対象外。 | X後に生成したbundle-less receipt/reportをlegacy扱いできるか、旧成果物を受理できるかが変わる。 |
| R-7 | `regressed`（型3） | 「両方を毎世代必須にしてはならない」と書き、未裁定Q3のlockstep選択を先に排除している。 | environment-only/freeze-only successor、rollback、pointer・report・台帳の受理世代が裁定前に固定される。 |
| REAL-5 | `closed` | 下位family自身のsemantic verifierを要求し、承認record形状の偽装だけでは通らない。 | — |
| REAL-6 | `partial`（型1） | R-6と同じcutoff未総体化。 | 新規bundle-less成果物の受理集合と台帳参照が不定になる。 |
| REAL-10 | `regressed`（型2） | 本体は「resolverが一意に解決した場合」とするが、追記は「上位pointerが存在する場合」とする。 | 同じHEADを上位authority／下位authorityとして読むconsumerが分岐する。 |
| M-1 | `closed` | Xがdigestだけでなく承認record自身を参照する規則を追加。 | — |
| M-2 | `closed` | Q対象とA成分の集合一致を追加。集合と配列の厳密な符号化は段0のexact化範囲であり、現時点では欠陥扱いしない。 | — |
| M-3 | `closed` | approved-inactive判定を下位family verifierへ委譲。 | — |
| M-4 | `closed` | candidate/currentの型分離と素の権限objectへのaccessor禁止を明記。 | — |
| M-5 | `closed` | fixtureを置くだけでなくmanifest・全単射・実行nodeを受入条件にした。 | — |
| M-6 | `partial`（型1） | R-6と同じ。cutoffは複数導入・未追跡成果物を分類できない。 | bundle-less runがlegacyへ混入し、certified選択と試行台帳のauthority参照が失われる。 |
| M-7 | `regressed`（型2） | 本体のvalidity判定とfreeze文書の単純な存在判定が衝突する。 | 上位／下位のproduction authority、report、certified選択がHEADごとに一致しない。 |
| M-8 | `regressed`（型3） | §5が非lockstepを先取りし、Q3のlockstep/rollback裁定を残したままにしている。 | 上位束の受理世代とpointer chainが裁定結果と食い違う。 |
| M-9 | `partial`（型2） | 下位正本の未了はU-A1だけでなくconformance期待出力literalも含むが、本体§10.1はU-A1のみを段0 gateとしている。 | 下位approved-inactiveの受理集合が確定しないまま、上位A・report・台帳へ進められる。 |

## タスク 2 — 2巡目修正の検査

| # | 判定 | 所見 |
|---|---|---|
| 1 | `regressed`（型2） | 本体§1の「valid resolverが一意」対、`freeze-permanent-design.md`の「pointerが存在」で直接矛盾する。path/schema未確定自体は欠陥ではない。 |
| 2 | `regressed`（型2） | exact parent規則は追加されたが、topology図の枝構造と両立しない。 |
| 3 | `closed` | Qが検査した対象とA成分を束縛するため、旧Q(T1)→A(T2)構成は閉じた。 |
| 4 | `closed` | 同一digestを持つ別承認recordへの差替えを識別できる。 |
| 5 | `closed` | raw approval-looking recordだけではapproved-inactiveにならない。 |
| 6 | `closed` | candidateから通常の権限objectへ降格する経路を禁止した。 |
| 7 | `partial`（型1） | 導入commitが複数、またはruntime成果物に導入commitがない場合の受理規則がない。 |
| 8 | `closed` | reject-allや未実行fixtureを完了扱いする余地を文書上は塞いだ。 |
| 9 | `regressed`（型3・型1） | 非lockstepをQ3前に固定したうえ、非交代成分が親束の値と一致することを検証する規則がない。 |

## 残るmust-fix

### 1. precedenceの文書間矛盾（型2）

本体は、pointerが無い・複数・検証失敗なら下位契約へ戻すと規定しています。[本体§1](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:36>)

一方、追記は「上位active pointerがHEAD上に存在する場合」とだけ書いています。[適用範囲](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/freeze-permanent-design.md:15>)

壊れたpointerを1つ置いたHEADでは、前者は下位、後者は上位を選びます。

### 2. legacy cutoffが総体的でない（型1）

現行の`_immutable_introductions`は、同一bytesなら削除後の再作成を許し、複数の導入commitを返し得ます。[s8b_ratified_freeze.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:469)

```text
C_before_X で R を追加
X
C_after_X で R を削除・同じbytesで再追加
```

このRの導入commit集合は前後にまたがります。どれか一つを見るのか、全てがXの祖先であることを要求するのか、拒否するのかが書かれていません。さらにreceipt、marker、budget、WAL等にはGit上の導入commitが存在しない場合があります。

したがって「機械的にcutoff判定できる」という主張は現状では成立しません。

### 3. 非交代成分の親束継承が未検証（型1）

§5は非交代成分を親束から引き継ぐとしますが、Q/Aの集合一致とdigest再計算だけでは、Aの成分値が親束の値と同じかを検査しません。[該当箇所](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:140>)

親束のfreeze成分F1に対し、G/A_fなしでAがF2を成分に置き、QがF2を検査する構成は、書かれたQ/A条件だけなら通ります。結果として、対応する世代導入・承認なしの成分がcertified authority、report、台帳へ入ります。

### 4. Q3の暗黙裁定（型3）

「両方を毎世代必須にしてはならない」は、Q3が未裁定なのにlockstepを禁止しています。[§5](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:140>)

親推奨はlockstepのままなので、本文内部で受理集合が衝突します。

### 5. 下位conformance gateの脱落（型2）

下位正本冒頭は、U-A1に加えてconformance期待出力literalを未了としています。[freeze-permanent-design-s2.md](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/freeze-permanent-design-s2.md:3)

しかし本体の段0既存gateはU-A1だけです。[§10.1](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:365)

現行実装でも下位resolverはapprovalとpointerを同一commitに要求しており、下位exact topologyとの差は未解消です。[`_verify_pairing`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:1189>)。これは将来実装との差そのものではなく、上位wave開始前の明示的なgateが欠けていることが問題です。

## 実装照合

- 環境activation schemaは未知keyを拒否し、全env据置のno-opも拒否します。[env_contract_activation.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract_activation.py:189>)・[no-op拒否](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract_activation.py:293>)
- 現行freeze側はpointerに承認record hashを持ち、同一commit pairingを検査します。[s8b_ratified_freeze.py](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:114>)
- 現行の上位namespace/resolverは未実装であり、その挙動を実装済みとは断定していません。

## 総括

重複IDを統合した残件数は次のとおりです。

- 型1: **2件**
- 型2: **3件**
- 型3: **1件**

**NO-GO。** cutoffの非総体性、親束継承の未束縛、precedence文書矛盾、Q3の暗黙裁定、下位gate脱落が残っており、certified選択・report・試行台帳の受理集合またはauthority参照を一意に固定できません。静的検査のみで、ファイル変更・pytest実行はしていません。