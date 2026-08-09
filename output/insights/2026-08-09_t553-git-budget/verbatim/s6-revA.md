静的判定は **NO-GO**。Critical 0、Major 5、Minor 0 です。pytest・変異 harness は実行しておらず、緑は主張しません。

## 所見

### 1. Major — `real-invariant-r` が実測の 7,044 ではなく 7,005 を固定している

同じ HEAD `2169a06c` に対し、実測正本は hardened 履歴の要求数を 7,044 と記録しています（[MEASUREMENT.md:28](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/MEASUREMENT.md:28)、[MEASUREMENT.md:98](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/MEASUREMENT.md:98)）。実際にも HEAD は 2,347 commits、invariant は候補 commit を 1 件加えるため（[test_s8c_preregistration_invariant.py:92](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_invariant.py:92)）、`2,348 × 3 = 7,044` です。

ところが unit test は 7,005 と `75.243` を `real-invariant-r` としています（[test_s8c_preregistration_core.py:1002](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:1002)）。正しい現値は `75.5784` 秒です。production helper 自体は実 stdin を数えるので正しく動きますが、テストと実装報告の golden が実対象を検査していません。

修正案: `real-invariant-r` を 7,044 / 75.5784 に直す。7,005 を残すなら一般的な合法例へ改名する。

成果物影響: 7,044 要求だけを誤処理する回帰を受入が見逃し、有効な freeze が `git-timeout` となって activation report・certified 選択・trial ledger 行が欠落し得る。

### 2. Major — 変異 9 は、MAX 境界で分割する実装なら生存する

call-count 検査は有効ですが、fixture がちょうど `MAX_BATCH_REQUESTS` 行です（[test_s8c_preregistration_core.py:1046](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:1046)）。したがって「1 chunk = `MAX_BATCH_REQUESTS`」として、それを超えたときだけ分割する変異はこの nodeid で1回しか呼ばれず通ります。

**変異 9 はこの具体化では生存する。**

修正案: `MAX_BATCH_REQUESTS + 1` または2倍の stdin を `_git` に渡し、なお `subprocess.run` が1回であることを検査する。小さい `MAX_BATCH_REQUESTS` を monkeypatch して2行を渡す方法でもよい。

成果物影響: chunk ごとに独立 timeout が付く変異を見逃すと、単一300秒 capを超える総実行時間が許容され、validation・report・ledgerへ到達する時間上の受理集合が広がる。

### 3. Major — 変異 10 の caller-override 検査が裁定対象を網羅しない

裁定は `_git`、`_git_text`、`validate_condition_freeze_at`、`prepare_revision`、CLI の signature 不変を要求します（[s4-ruling.md:62](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/s4-ruling.md:62)）。しかしテスト対象は `_git`、`validate_condition_freeze_at`、`prepare_revision` の3つだけで（[test_s8c_preregistration_core.py:1085](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:1085)）、`_git_text` と CLI parser を見ていません。また検査は完全一致ではなく、引数名が正確に `timeout` / `budget` / `deadline` かだけです。`timeout_seconds` も生存します。

例えば CLI に `--timeout` を追加し、`main` 内で capを上書きする変異は指定 nodeidを通ります。

**変異 10 は生存する。**

修正案: 裁定された全関数について baseline signature を完全一致で固定し、CLI option集合に timeout/budget/deadline 系がないことも検査する。

成果物影響: caller が15秒未満または300秒超を指定できると、freeze validation の拒否・受理集合が変わり、report の `freeze_reason_code` と trial ledger の生成可否が変わる。

### 4. Major — A-04 の durable binding が未完成

裁定は生 JSON を `output/insights/2026-08-09_t553-git-budget/` に凍結し、worklog と module コメントから導出を参照するよう要求しています（[s4-ruling.md:30](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/s4-ruling.md:30)）。

現時点ではその directory が存在せず、生 JSON は job directory にだけあります。また production 定数（[s8c_preregistration.py:95](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:95)）にも導出先コメントがありません。テストは同じ literal を複製しているだけです（[test_s8c_preregistration_core.py:987](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:987)）。

これは段7で親が担う記録面を含みますが、GO前には必ず閉じる必要があります。

成果物影響: 根拠と定数の対応が失われると、誤転記された RATE/CAPでもテストが通り、freeze・report・trial ledgerへ到達する時間上の受理集合が無根拠に変わる。

### 5. Major — CRは要求数をずらさないが、末尾CRの path identity を別 pathへ aliasする

`b"x\ry"` はLFを含まない1 fragmentなので、R=1は正しいです（[test_s8c_preregistration_core.py:1015](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:1015)）。read-only の実 Git 照合でも、embedded CR、CR-only、空行を含め、Gitが消費する要求数は「LF数＋末尾fragment」と一致しました。CRによる要求数の過小計上は構成できません。

ただし `read_blob_at` は path の後ろへLFを付加します（[s8c_preregistration.py:957](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:957)）。path が末尾CRなら入力はCRLFとなり、GitはCRを行終端として除去します。実照合では `HEAD:CLAUDE.md\r\n` が `HEAD:CLAUDE.md` と同じ blob SHAを返しました。一方、evidence contract の `_safe_path` はCR/LFを許容します（[s8c_preregistration_evidence.py:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration_evidence.py:183)）。

これはtimeout予算の不一致ではなく、既存の path identity 欠陥です。制御文字拒否は受理集合を狭めるため、このwaveで黙って直さず再裁定が必要です。

成果物影響: contract が `foo\r` を参照しても `foo` のblobを証拠として採用でき、EvidenceRefのpath/hash対応、predicate status、activation report、certified 選択・trial ledger参照が誤る。

## 裁定 §2 との実装照合

| 不変条件 | 静的判定 | 根拠 |
|---|---|---|
| `R=min(LF行数, MAX_BATCH_REQUESTS)` | closed | [s8c_preregistration.py:882](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:882) |
| `B(R)=min(BASE+R×RATE,CAP)` | closed | [s8c_preregistration.py:887](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:887) |
| signature 不変 | closed（実装） | 差分にsignature変更なし。テスト検出力は所見3 |
| `subprocess.run` 1回 | closed（実装） | [s8c_preregistration.py:899](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:899) |
| input-limitが予算より前 | closed | [s8c_preregistration.py:893](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:893) |
| reason-code分岐不変 | closed | timeout/output/failed分岐は従来位置・条件を維持 |
| 量的上限不変 | closed | [s8c_preregistration.py:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:88) |
| invariant/xdist不接触 | closed | 差分対象外。[test_s8c_preregistration_invariant.py:124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_invariant.py:124) |

したがって、裁定 §2 に対するproduction実装の Critical 違反は見つかっていません。

## 変異12件の静的適用

| # | 判定 | 適用時の結果 |
|---:|---|---|
| 1 | killed | RATE literal assertが赤 |
| 2 | killed | BASE literal assertが赤 |
| 3 | killed | CAP=445となり、`==300` と `!=従属式` の両方が赤 |
| 4 | killed | clampを外すと amplified入力が445となりcap assertが赤 |
| 5 | killed（構造pin） | CAPを1000へ上げたテストでは mutant が875、期待445となり赤 |
| 6 | killed | `len(stdin)=14,010` となり135.486秒、期待75.243に不一致。ただしfixtureの「実R」は所見1のとおり誤り |
| 7 | killed | fragmentを落とすと15.0、期待15.0086に不一致 |
| 8 | killed | helper call記録または123.25秒のtimeout伝播が不一致 |
| 9 | **survived** | MAX単位で、MAX超だけ分割する具体化は現fixtureで1 call |
| 10 | **survived** | CLI override、`_git_text`、`timeout_seconds` を検出しない |
| 11 | killed | `TimeoutExpired` が `PreregistrationError("git-timeout")` にならない |
| 12 | killed | budget monkeypatchが先に発火して赤 |

変異5については、productionではCAPが約33,140要求で先に効くため、50,000超で `R` のminを外しても戻り値は常に300秒です。CAP=1000へのmonkeypatchは裁定された構造を隔離して検査する正しい方法ですが、現在のproduction受理集合に対する semantic kill ではなく、構造 sensitivity pin と記録するのが正確です。

## 既存テストの強化と浮動小数点

`test_git_input_limit_stops_before_subprocess` は弱体化されていません。従来の subprocess 0回検査を残し、予算helperも0回であることを追加しています（[test_s8c_preregistration_core.py:1102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:1102)）。

integration testがhelperをmonkeypatchするのは、予算値の伝播とcall-countを単一理由で検査するため妥当です。production式は別のparametrize、絶対CAP、request clampテストで検査されています。ただし実R=7,044のpinだけ欠けています。

現CPythonで以下は同じbinary64 bit patternになり、`==` は真でした。

- `15.0 + 7005 * 0.0086 == 75.243`
- `15.0 + 7044 * 0.0086 == 75.5784`
- `15.0 + 0.0086 == 15.0086`

現在の式と対応環境について、浮動小数点等値が実赤になる根拠はありません。literal契約をpinする目的では `approx` へ緩める必要もありません。

## 段3採用所見の閉包表

| 所見 | 状態 | 判定 |
|---|---|---|
| A-01 | closed | request RATEと独立CAPへ分離 |
| A-02 | closed（採用部分） | request clamp＋絶対CAP。LF拒否残余は裁定どおり対象外 |
| A-03 | closed | rev-list/log/ls-treeを負荷下測定し15秒余裕を確認 |
| A-04 | **partial** | 実測済みだがdurable出力・module参照・worklog束縛が未完 |
| A-06 | **regressed** | 7,005へ直した後、実測が7,044を示したのにテストへ反映されていない |
| B-01 / B-04 | closed（採用部分） | 2ノード、mixed負荷、安全係数4、降順、再較正条件あり |
| B-02 / B-11 | **regressed** | A-06と同じ実要求数不一致 |
| B-03 | closed | completedは失敗・timeout・missing worker 0を要求 |
| B-06 | closed | 独立CAP 300.0 |
| B-12 | closed | 実装scopeをs8cに限定し、ruleops同型は既存T-510へ分離可能 |

記録のみの A-05/B-05/B-07/B-08/B-10 と、不採用のB-09は表から除外しました。

## 総括

**NO-GO。Critical 0、Major 5、Minor 0。**  
productionの予算式・発火順・reason code・量的上限にはCritical違反なし。  
実要求数goldenは7,005でなく7,044。  
変異9はMAX超chunk、変異10はCLI等のoverrideで生存する。  
変異5は赤になるが、現productionでは等価な構造pinである。  
CRは要求数をずらさないが、末尾CR pathを別pathへaliasする。  
A-04の実測根拠のdurable bindingも未完。  
pytest・変異実走はしておらず、緑は主張しない。