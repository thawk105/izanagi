## 前提の確認

読めた資料:

- 親 brief、段 2 plan、対象文書 snapshot 全文
- §5 固定表の逐語契約
- D1082、実行責任者裁定控え
- 指定された 5 consumer
  - `orchestrator/campaign/p3_b4_admission_record.py`
  - `orchestrator/tests/test_p3_b4_admission_record.py`
  - `orchestrator/tests/test_p3_b4_closed_critic.py`
  - `tools/check_docs.py`
  - `docs/phase3-s4b-runbook.md`

snapshot と checkout の対象文書は SHA-256 `51307f9f...10356` で一致した。読めなかった必読資料はない。

Web、書き込み、pytest は実施していない。以下は静的検査結果であり、テストの緑は主張しない。

## 正しさ境界の所見

### 1. 現提案の admission は確実に fail-closed になる

- 所見: R1 と R3 は成立する。ただし実際の最初の拒否は複合セルではなく、先に残る `対象 driver と軸|未記入` である。
- 根拠: `p3_b4_admission_record.py:assert_section5_fixed_table_has_nonempty_source_cells_and_no_reserved_sentinel`
  - `## 5.` は `r"## 5\.(?:\s.*)?"`、`### 5.1` は `r"### 5\.1(?:\s.*)?"` の full match。
  - `#### 5.1.1 ...` は hash 数が違うため、どちらにも一致しない。
  - `## 5.` と `### 5.1` の間は引き続きヘッダ 2 行、データ 10 行の計 12 非空行。
  - ヘッダ `|欄|値|`、`|---|---|` は不変。
  - ラベル 10 件も不変で exact 集合に一致する。
  - セル分割は `line[1:-1].split("|")` のみ。提案値の `;` と `=` は区切りではない。
  - strip 後に NFKC 正規化されるが、`実行責任者=thawk105; 開始時刻=未記入` の ASCII 記号と日本語は問題を起こさない。
  - 提案値には `Cf` や default-ignorable range の文字がない。
  - `_RESERVED_SENTINEL_RE` の `未記入` は境界条件なしの部分一致なので、複合セル中でも検出される。
  - whole-value sentinel は `x`, `-`, `--`, `---`, `—`, `…`, `...`。今回の複合セルはこれには該当しないが、正規表現側で拒否される。
- 成立条件: plan 記載どおり、表の行追加・ラベル変更・値中の `|`・隠し Unicode 文字を入れないこと。
- 提案: R1/R3 を安全と裁定してよい。ただし「複合セルで拒否された」と実測報告してはならない。現 bytes では先頭側の `未記入` で先に停止する。

### 2. primary outcome の参照文字列は意味を検査されない

- 所見: R2 の非対称は機械的には正当化できない。checker は母集合、n、primary の意味を区別しない。
- 根拠: 同関数の docstring は「types or rendered meaning」を検査しないと明記する。`§5.1.1「primary outcome の純関数」` は非空・非 sentinel なので、参照先が存在しなくても受理される。見出し解決や本文 hash の個別検査はない。
- 成立条件: 現 wave 直後は他の sentinel が残るため通らない。しかし将来、他セルと model 行が形式上埋まれば、参照先の削除、空洞化、改名があっても admission が通る。
- 提案: D1082 の 4 項目が同じ変更単位で実在するまで primary セルも `未記入` に保つか、checker に参照先見出しと必要小節の実在・内容契約を追加する。

### 3. plan は D1082 の「一括凍結」を実施していない

- 所見: 母集合と n を `未記入` に残し、primary だけ参照へ変える案は D1082 の履行ではない。
- 根拠: D1082 は「赤 precursor 母集合・最小重要効果・n・primary outcome の純関数は一括で凍結する」と逐語で要求する。plan の到達表でも n は `未記入` のままである。一方、新見出しと §9 は「分析契約凍結時点」と表現する。
- 成立条件: 数値 n または D1082 が n として認めた exact な凍結対象が §5 で成立していない限り、凍結宣言は虚偽になる。
- 提案: 段 4 で母集合と n の exact 内容を裁定し、4 項目を同じ commit に入れる。部分着地するなら見出しと §9 に「凍結」を書かず、4 セルすべてを sentinel のままにする。

### 4. primary 純関数案は §7 の判定規則を表現できない

- 所見: 提案された入力型には treatment 未発火、off 汚染、protocol violation を判定する情報がない。そのため §7.1 が「判定不能」または「protocol violation」とする実験を、`A` と p 値だけで成立扱いにできる。
- 根拠:
  - 対象文書 §7.1 は n 不足、treatment 未発火、off 汚染を判定不能とし、protocol violation を独立分類する。
  - 草案の `ArmObservation` は `certified/rejected/aborted/missing` だけ。
  - 草案の成立条件は `p <= 0.05` と `A >= A_min` だけで、§7.1 の override がない。
- 成立条件: treatment 未発火 block や汚染 block が `missing` 等へ写され、expected_n を満たす場合。
- 提案: `treatment_fired`、arm contamination、protocol status を入力契約に追加し、実験全体の判定関数が §7.1 の四分類を優先するよう固定する。

### 5. n 草案は現行 §5.1 と説明不足の衝突がある

- 所見: 現行 §5.1 は n を「B-4 データを含まない」入力から決めると書くが、草案は B-4 型の pilot 20 block の `X_i` を使う。D1082 は pilot 利用を許すものの、正式標本との区別を本文で明示しないと矛盾して読める。
- 根拠: 対象文書 §5.1「n と検定単位」と、plan「n の導出と検定単位」。
- 成立条件: 「B-4 データ」が正式標本だけを意味するという暗黙解釈に依存する場合。
- 提案: 既存 §5.1 の n bullet も更新し、pilot の権限、正式標本との非重複、pilot outcome は n と分散上限以外へ使わないことを明示する。

### 6. docs-only は draft としては安全だが、実走契約としては未閉鎖

- 所見: P1 の「発火する consumer がない」は不正確。primary を計算する consumer はないが、文書を admission に使う consumer は実在する。
- 根拠:
  - `p3_b4_closed_critic.py:create_b4_closed_critic_pair` は provider 起動前に `verify_b4_admission_record` を呼ぶ。
  - §6 は全セル記入と他前提を要求するが、primary 純関数の実装・conformance consumer を要求しない。
- 成立条件: 将来、参照文字列を含む全セルが非 sentinel になった場合。
- 提案: primary セルを解除する前に純関数の実装と conformance test を入れるか、少なくとも §6 に実装済みを要求し、§10 に未実装を明記する。

## 整合・実効性の所見

### 1. 実行責任者の複合セルは §0 と衝突する

- 所見: 機械的には安全だが、§0 の「未記入の欄には placeholder 語だけを置く」と整合しない。
- 根拠: `実行責任者=thawk105; 開始時刻=未記入` は、一つの値セルに確定値と placeholder を併記する。
- 成立条件: §0 の「欄」を固定表の一行単位と読む場合。
- 提案: §0 にこの複合欄だけの狭い例外を追加し、「説明文ではなく二つの構造化値」であると定義する。固定表の行追加やラベル変更はしない。

### 2. R4/R5: `check_docs.py` は提案の主要な問題を検出しない

- 所見: 提案本文は現在の `check_docs.py` には機械的に通る見込みだが、それは意味的整合を証明しない。
- 根拠: 対象文書へ実際に適用される検査は `tools/check_docs.py:_main` の LIVING_DOCS loop に限られ、次である。
  - 列挙対象の存在
  - symlink component の禁止、regular file、UTF-8
  - docs 行番号参照の禁止
  - `現在は Phase` の再掲
  - `pin.CURRENT_PIN` literal
  - D1 から D999 の参照実在性
  -既知トップディレクトリから始まるファイルパスの実在性
- 成立条件:
  - `§5.1.1` は行番号参照ではない。
  - D1082 は 4 桁なので `D_REF = r"\bD(\d{1,3})\b"` の対象外。
  - 新規のファイルパス参照はない。
- 提案:
  - 最長行予算は対象文書へ適用されない。
  - inline code 内 HTML comment 検査は provenance 文書専用で、対象文書には適用されない。
  - literal placeholder guard は worklog、archive worklog、insights の 3 族だけで、対象文書の `未記入` は対象外。
  - 三軸語の専用 lint は `check_docs.py` に存在しない。
  - 節番号参照の実在性検査もない。
  よって R5 の数式・識別子は lint 上の blocker ではないが、人間レビューは必要である。

### 3. tracked 参照は 21 file、現行 consumer は 5 file

- 所見: basename または題名による tracked 走査で、対象文書を参照する file は 21 件だった。
- 根拠:
  - 現行面:
    - `docs/phase3-s4b-runbook.md`
    - `orchestrator/campaign/p3_b4_admission_record.py`
    - `orchestrator/tests/test_p3_b4_admission_record.py`
    - `orchestrator/tests/test_p3_b4_closed_critic.py`
    - `tools/check_docs.py`
  - 凍結・履歴面:
    - `docs/archive/worklog-phase3-0825-936.md`
    - `docs/archive/worklog-phase3-0826-967.md`
    - `docs/failures.md`
    - `output/insights/2026-08-26_b2-descriptor-causal-evidence/{consult-a.md,plan.md}`
    - `output/insights/2026-08-26_t1697-closed-critic-invocation/verbatim/` の 6 file
    - `output/insights/2026-08-26_t1784-prereg-admission-record/` の 5 file
- 成立条件: tracked working tree の文字列参照に限定した列挙。
- 提案:
  - 現提案だけなら既存 unit test は赤にならない。両 test は実 target ではなく synthetic §5 fixture を生成する。
  - runbook の参照は §6 前提条件 3 だけなので更新不要。
  - 履歴面は更新しない。
  - checker を意味検査へ強化する場合は production checker と上記 2 test を更新する。
  - 古い admission record が存在すれば、文書変更後は `HEAD document differs from declared blob` で拒否される。新文書 commit 後に新 record commit が必要。

### 4. 「pin 閉包 6 file」は名称が過大

- 所見: 対象文書自身と現行 literal 参照 5 fileを合わせた 6 file は再現できる。しかし byte-pin 閉包ではない。
- 根拠:
  - `orchestrator/campaign/p3_b4_closed_critic.py` は対象パスを直接書かず、verifier を import して間接消費する。
  - CLI の `--admission-record` は任意パスを受け取り、その record が content commit/hash を pin する。
  - sidecar も preregistration commit/hash を保存する。
- 成立条件: literal path の tracked working-tree 走査だけを「閉包」と呼んだ場合。
- 提案: 結論を「対象 + active な direct literal references は 6 file」に限定する。実行閉包には間接 import、未追跡・ignored・repo 外 admission record、sidecar、Git history を含める。

### 5. 「静的に bytes を pin する台帳はない」も限定付きでのみ正しい

- 所見: 現 SHA-256 literal は tracked working tree から見つからなかった。しかし全体不存在は証明できない。
- 根拠: 実行時 verifier は record の `content_commit` と `content_sha256` を使い、HEAD の文書 blob との byte equality まで検査する。
- 成立条件: tracked HEAD の平文 literal だけを探索した場合。
- 提案: 「tracked HEAD に現 SHA literal を持つ実 admission record は見つからなかった」と書き換える。repo 外、ignored、untracked、過去 commit、実走 artifact は走査外と明記する。

### 6. 並行 wave の宣言範囲へ exact な byte 編集はないが、§9 は §10 に近すぎる

- 所見:
  - `#### 5.1.1` の挿入は §5.1 (ii) の既存行を変更せず、§7.2、§8、§10 にも byte 変更を加えない。
  - 一方、§9 の追記位置を「既存結論段落の後、§10 の直前」にすると、§10 冒頭を編集する並行 wave と unified-diff context が重なる可能性が高い。
- 根拠: snapshot では §9 の結論直後に `## 10.` とその最初の probe bullet が続く。
- 成立条件: 並行 wave が §10 冒頭を編集する場合。
- 提案: §9 の追記は既知結果表の直後、既存の「したがって」段落より前へ移す。これなら §10 の hunk から距離を取れる。

### 7. `2^n` 全列挙は実効性がない可能性が高い

- 所見: 草案の n 式は最大で約 155 block を返し得るが、`2^155` label swap の逐一列挙は実行不能である。
- 根拠: `v_upper <= 1/4` と plan の定数を式へ入れると n0 の上限は約 155。
- 成立条件: 分散上限が 1/4 近傍の場合。
- 提案: exact 性を保つ動的計画法などで検定統計量の分布を数え上げる契約へ変更し、「全 permutation を逐一列挙」とは書かない。

## 親 brief P1-P6 への反証

|項目|判定|
|---|---|
|P1 docs のみ|条件付き反証。draft のまま閉じるなら可能だが、primary セルを解除するなら実装・conformance gate 不在が残る。「consumer がない」は admission consumer の存在を落としている。|
|P2 §5.2|反証。見出し検出は壊さないが、§0 が規範の置き場を §5.1 と §7 に限定する。§0 を変えないなら `5.1.1` が整合的。|
|P3 3 セルを参照で埋める|反証。checker は参照先を解決せず、任意の非 sentinel 文字列で通る。特に n を参照だけで埋めるのは危険。|
|P4 複合セル|機械面は反証できない。`未記入` の部分一致で確実に拒否される。ただし §0 との文書内矛盾が残る。|
|P5 確率優越 A|機械面からは反証できない。checker は尺度も `A_min=0.60` も検査しない。値の妥当性は別の統計裁定が必要。|
|P6 導出関数を n の凍結とする|D1082 履行として反証。§5 の n セルが sentinel のままなので admission 上は未凍結であり、一括凍結にもならない。導出関数の draft としては成立する。|

## 反証できなかった点

- `#### 5.1.1` は checker の `## 5.` / `### 5.1` 検出を二義化しない。
- 複合セルの `未記入` 検出は確実である。
- 現提案後に admission が通る経路はない。先頭側を含む複数セルに sentinel が残る。
- 現 SHA-256 literal を持つ tracked admission 台帳は見つからなかった。
- `A_min=0.60` 自体の科学的妥当性は、提示された機械契約だけでは否定できない。
- 与えられた資料から exact な母集合を新たに構成することはできなかった。
- 並行 wave の宣言された編集範囲との byte 非接触は確認できたが、その worktree の未 commit 差分本文は射影対象外なので独立比較していない。

## 総括

plan はそのまま着地させるべきではない。R1 と R3 は安全だが、R2 は semantic bypass を残し、母集合・n を未記入にしたまま「D1082 一括凍結」と §9 に記録する点が承認済み裁定と衝突する。

段 4 では少なくとも次を要求すべきである。

1. D1082 の 4 項目を同じ変更単位で実在させる。
2. primary の treatment 未発火・汚染・protocol violation 規則を §7 と一致させる。
3. primary 参照を解除する前に実装または conformance gate を置く。
4. 実行責任者の複合セルについて §0 に狭い例外を設ける。
5. §9 追記を表直後へ移し、並行 wave の §10 hunk から離す。
6. 親の「6 file」「pin 台帳なし」は tracked direct literal 走査に限定した表現へ修正する。