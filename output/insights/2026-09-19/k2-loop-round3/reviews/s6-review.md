## 1. 数値・識別子の逐語照合

以下、`I` は `output/insights/2026-09-19/k2-loop-round3`、`J` は repo 外 job root を指す。

**R#1 — refuted：実測表・ハッシュの不一致。**  
根拠：`I/README.md:65`、`:121`、`:127`、`J/ingest-real.log:1`、原本 `runs/wal.jsonl:1`。

job・host・時刻・Elapse 69 秒・driver_rc・variant・genome・build・verdict・commits・aborts・anomalies・反復値・settled は一致。再計算でも median 815983、CV 0.1587557%、trace abort 率 18.9377234% となり、記載の丸めと一致した。WAL、防護 5 file、AO、材料レポート、入力・出力・prompt の SHA-256 は `sha256sum` と一致。AO ref 3 件も再計算で一致し、source_refs は重複なしの 9 件だった。  
成果物影響：本走の認証結果・性能値・証拠識別に不一致はない。

**R#2 — real / should：較正記録の不在という説明が誤り。**  
根拠：[README.md:131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-round3/output/insights/2026-09-19/k2-loop-round3/README.md:131)、`I/layer3_report.json:1`。

`no-matching-env-record` は一致するが、「submit-tree に較正記録が無い」は一致しない。レポートは 8 file を走査し、between-run では 48 threads / 100万 records の候補との条件不一致、within-run では `self-inconsistent-calibration` による除外を記録している。原本 tree にも較正記録が存在する。「本走に適合する採用可能な較正記録が得られない」へ限定すべき。  
成果物影響：floor 欠測の原因を、資料不在と誤って次巡へ継承する。

**R#3 — real / nit：abort 率差の算術誤記。**  
根拠：`I/README.md:110`、`I/materials/run-summary.json:5`、`I/materials/planner-input-4.json:3`。

`9.065 − 7.40 = 1.665 pt` であり、記載の `+1.65 pt` は合わない。表示値同士なら `9.07 − 7.40 = 1.67 pt`。critic 原文にも同じ誤記があるため、逐語を改変せず README 側で注記するのが適切。  
成果物影響：差分の説明値だけが誤る。実測値・認証・帰属不能という結論は変わらない。

## 2. 主張限定の遵守

**R#4 — real / should：success の意味が README 本文に明記されていない。**  
根拠：[README.md:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-round3/output/insights/2026-09-19/k2-loop-round3/README.md:74)、`I/reviews/s4-ruling.md` 末尾「主張限定」、`I/verbatim/critic-3.md:22`。

README は success を載せるが、必須の「success は certified の意味であり、性能改善ではない」という対応を明示していない。逐語資料には存在する。表の該当行に短く補えば足りる。  
成果物影響：README の whiteboard 記録を単独で読む際、success を性能改善と解釈する余地が残る。

**R#5 — refuted：禁止された実証・因果・完了主張。**  
根拠：`I/README.md:12`、`:35`、`:50`、`:94`、`:145`、worklog fragment `:14`、`:25`、`docs/phase3.md:448`。

改善・診断効果・既知値非開示・認可内容の完全達成・候補間 certified 選択・K2 因果・B-4 適格の肯定的主張は確認しなかった。該当語は否定や留保の文脈にある。stock 未達、同時刻対照なし、非同時刻値を対照にしない、delta null、20/25 の開示、CLI emit 非使用も記録されている。  
成果物影響：R#4 の明記不足を除き、部分成果が改善実証や完全達成へ昇格されていない。

## 3. ユーザー決定との対応表の正確さ

**R#6 — refuted：対応表の改変・再投入。**  
根拠：`I/README.md:19`、`J/rulings/user-decision-2026-09-19.md:3`、`J/qsub-0001.stdout:1`。

対応表は生成 1 回、評価 1 本、stock 1 本の要求を保持し、stock を未達としている。20 の再評価禁止、候補 10 の非正解扱い、delta null、anomaly 即 reject も一致する。qsub 出力は `10761.nqsv` 1 件、evidence は `attempt-0001` のみで、確認資料に再投入の形跡はない。  
成果物影響：縮小走行をユーザー要求の完全履行として記録していない。

## 4. 可逆最小正規化の記述

**R#7 — refuted：正規化の SHA・byte 数・変更範囲の不一致。**  
根拠：`I/README.md:171`、原本・複製の `evidence/attempt-0001/job.stdout:29`、`:72`。

再計算結果は記載どおりだった。

| 対象 | bytes | SHA-256 |
|---|---:|---|
| 原文 | 12365 | `2b7c25f7957614d2d38d635a0314a509e3dddbf61657442db2babdb09c48087a` |
| 正規化後 | 12361 | `f223cecc05429fc0613a47af4966962fed31807cb7eadaca3f41546fc50d4677` |

通常 diff は `-- Found Threads: TRUE` の 2 行から末尾空白を各 2 byte 除いた差だけ。`diff -w -B` は rc=0。他の evidence 複製 4 file も原本とハッシュが一致した。  
成果物影響：可視内容・実測結果の改変はない。

## 5. worklog fragment の形式

**R#8 — refuted：fragment・phase チェック行の形式違反。**  
根拠：`docs/spool/worklog/2026-09-19-dev-wave-k2-loop-round3-1.md:7`、`:10`、`:29`、`:33`、`docs/phase3.md:448`。

H2 は指定の 2 つで順序も正しい。新規 2 件は `{{T:...}}` 形式、title に未採番 T はない。完了・更新・見送りの操作がないため base は不要。phase 行も周囲と同じチェック項目・継続行の形式で、stock 未達を明記している。  
成果物影響：指定された形式上の不備や、stock 残件の終端化はない。

## 6. 過剰・欠落

**R#9 — real / should：critic-2 の参照先が本 dir の実在 file を指さない。**  
根拠：[README.md:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-round3/output/insights/2026-09-19/k2-loop-round3/README.md:31)。

`verbatim/critic-2.md` は本 dir に存在しない。実在するのは `output/insights/2026-09-18/t2746-k2-loop-round2/verbatim/critic-2.md` で、再計算 SHA は記載の `d2b2ab77…` と一致した。複製追加ではなく、既存原本への参照訂正で足りる。  
成果物影響：診断抽出元の逐語へ README から直接たどれない。

**R#10 — refuted：必要材料の欠落・campaign 原本の不適切な複製。**  
根拠：`I/README.md:165`、`:177`、`I/materials/critic-prompt-3.md:1`、原本 `runs/agent_outputs.jsonl:3`。

入力・prompt・出力・proposal・実測射影・材料レポートは存在する。critic prompt の保存と AO の prompt SHA も確認でき、段 3 の当該 must-fix は解消されている。本 wave の保存物に WAL・lock・digest・state・receipt・AO の独立した原本複製はない。材料レポート内の射影は依頼された成果物に該当する。  
成果物影響：R#9 の参照不備を除き、評価と診断の追跡に必要な材料は保持されている。

## 総括

- **must-fix：なし。**
- **should：R#2 較正欠測理由、R#4 success の意味、R#9 診断元参照。**
- **nit：R#3 abort 率差の算術誤記。**

**判定：GO。** 縮小走行の記録として受理可能。stock 対照を含む認可内容の完全達成を意味しない。編集・pytest・commit・push は実施していない。