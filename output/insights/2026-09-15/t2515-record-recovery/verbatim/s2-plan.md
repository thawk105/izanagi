## 現状の実測

本段は静的確認のみ。ファイル書込み、git 状態変更、テスト実行は行っていない。指定資料はすべて読取り可能だった。

以下、path を短縮する。

- `B` = `/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2515-record-recovery/branch-material`
- `I` = 作業 worktree の `output/insights/2026-09-10/t2515-rr95-rr5-calibration`
- `N` = 同 `output/insights/2026-09-15/t2515-record-recovery`

確認結果：

- `I/README.md` は86行。既存成果物は job-evidence 7本、recovery-verbatim 11本、mutation JSON 6本。
- `B/verbatim/` は指定どおり13本。
- `988706`／`988708` の関門記録はいずれも `admitted=false`。accepted 取得の証拠ではない。
- **P1 の新規 F 2件は訂正が必要。** F500 に認証 script の interpreter 不整合、F766 にファイル名検索による既存 F の選び違いが既載。
- P2 の再登録見送りは妥当。現行 shell は exact 5値を受理し、Python 3.10 選定を保持する。旧専用関門の維持要求は後続裁定と区別する。

## plan (file:line 粒度)

**1. `I/original-verbatim/`：全ファイル新規、各1行目から追加**

次の basename を `B/verbatim/` から同名でコピーする。

```text
s1-brief.md
s2-plan.md
s3-consult-a.md
s3-consult-b.md
s4-ruling.md
s4-ruling-addendum.md
s5-author.md
s6-review-a.md
s6-review-b.md
s6-fix1.md
s6-fix2.md
s6-fix3.md
s6-refocus.md
```

改行、絶対パス、古い判断、見出しを含めて bytes を保存する。リンク修正や訂正文の挿入もしない。13本以外の索引ファイルは同ディレクトリへ追加せず、親 README から列挙する。

**2. `I/README.md:87`：末尾へ H2 を1節だけ追加**

題案：`## 2026-09-15追記：元waveの研究記録と後続裁定`

節内は太字ラベル・表・箇条書きで構成する。

- 出所：元 branch、tip `559bcbc29`、観測期間2026-09-09〜10、今回の回収日。`original-verbatim/` と既存 `recovery-verbatim/` の世代を区別する。
- 年表：元 README:49 の表を基に、8月6日の最後の成功記録、8月20日の潜在不整合投入、9月1日の関門義務化、9月10日の発見を記す。
- **「3週間ずっと実走不能だった」とは確定しない。** 8月20日から発見まで約3週間、関門経由の発火開始は9月1日という区別を示す。最後の成功日だけでは、それ以降の全期間の故障を証明しない。
- 検知穴：選定処理が呼出しより後ろにあったこと、静的 shell 検査と実行環境の差、長期間その経路を通していないこと。
- 旧 README:100以降の知見：literal 照合を正規化変異が通過する問題、参照関係で引いた焦点走が interpreter 抽出 harness の破損を捕まえた経緯。旧変異の M8「1 node」と、既存 README:78 の回収後「8 node」を混同しない。
- 旧 README:25、161の補足：A-6 停止理由の誤前提、exact 集合の射程が sanctioned shell 2経路に限られること。
- 下表の後続裁定を明示し、旧判断を現行の実装指示として扱わない。
- 13本へのリンクと本 wave `N/README.md` へのリンク。

既存1〜86行は完全に保持する。文書本文の参照は節名・ファイル名とし、本 plan の行番号を転載しない。

**3. `docs/spool/failures/2026-09-15-dev-wave-t2515-record-recovery-1.md:1`**

frontmatter は `schema: izanagi-spool-v1`、`ledger: failures`、`authored: 2026-09-15`、`wave: dev-wave-t2515-record-recovery`、`seq: 1`。`title` は付けない。

**新規 F は0件。** `## 新規` は置かず、次の順にする。

| action | 対象・現行アンカー | 書く内容 |
|---|---|---|
| 再発 | F355、`docs/failures.md:11739` | 2026-09-10、producer 生存中の早い成功通知3回、`.done` 非空確認で進行を止めた事実。原因未特定。縮退メッセージとの因果は断定しない |
| 再発 | F500、同:15479 | 同じ認証 script の別呼出しで再発。従来修理した calibrator 起動より前の関門が裸 Python を使用していた。年表と検知穴、当時の前倒し修理、D1936項6による後続の対象撤去を区別する |
| 再発 | F766、同:21125 | **根本原因(1)「証拠 F の選び違い」の再発**。`t1259`／`TimeoutExpired` 検索で F57・F862 を見落とした。F766の根本原因(2)である hold 登録循環の再現は主張しない |
| supersede追記 | F934、同:24625 | 「認定経路で一度も実走していない」を、9月10日の `988706`／`988708` で構造化拒否を記録した事実により限定訂正する |

再発は `### Fnnn` と `- **再発: 2026-09-10** — …`。F934 は **1物理行**の `- F934 **supersede: 2026-09-10** — …` とする。

F934全体を解消済みとは書かない。後段には別 driver の再発がある。旧 fragment の未定義 `{{D:certify-gate-python310}}` 等は転載しない。

**4. `docs/spool/worklog/2026-09-15-dev-wave-t2515-record-recovery-2.md:1`**

`ledger: worklog`、`seq: 2`、その他の共通値は上記と同じ。

title 案：

> T-2515旧waveの未着地研究記録を回収（docsのみ、branch dev-wave-t2515-record-recovery）

先頭を角括弧付きタスクIDにしない。本文は `docs/worklog.md:22` の規約に従い10〜15行程度。

- 今回の回収理由と一次資料ポインタ。
- P1の訂正、P2の採用、後続裁定との整理。
- 元 wave の未着地・救出に関する経緯。
- `素材:` で始める検知穴の短い要約。
- 過去の観測と今回の検査を区別した結果索引。
- 実際に完了した相談の件数・裁定だけを記す。

H2 は `## 本文` と `## 次の一手差分` の2つ。後者は操作なしで自動 carry とする。旧 fragment の T-2515更新、新規T 2件、旧 `base` は転載しない。較正取得を完了扱いにしない。

**5. `N/`：本 wave の記録**

```text
README.md
verbatim/
  brief.md
  rulings-verbatim.md
  s2-plan.md
  …今回実際に得られた相談・裁定の逐語
```

`README.md:1` から、出所、回収対象、P1/P2裁定、既着地 bytes の確認結果、親が実施した検査への索引を置く。旧13本を重複コピーしない。新しい gate・台帳・検査コードは追加しない。

## 親 brief への訂正 (real / refuted を明記)

| 判断 | 結論と根拠 |
|---|---|
| **real：P1「残る2件は新規F」** | F500は同一 script の Python版不整合を記録済み。F766:21133以降はファイル名検索で正しい族を見落とす誤りを明記。双方とも既存Fへの再発が適切 |
| **refuted：P1「待ち手はF355」が誤りという疑い** | F817:22305が「以後この型はF355へ追記」と明記 |
| **refuted：P1「F934の未実走記述を訂正する」が誤りという疑い** | F934:24625の記述と、既存job-evidenceの構造化拒否記録が対応する。ただし「認定経路の保存記録で確認できる初回」に限定 |
| **refuted：P2の旧decisions再登録見送りが誤りという疑い** | exact 5値は現行shellに存在。旧専用関門の維持はD1936項6の後続判断を無視できない |
| **real：「3週間故障」の期間断定** | 元README:53の成功日、:54の潜在化、:55の発火開始は異なる時点。「8月6日以降ずっと故障」「3週間の実走失敗」を同じ証拠で断定しない |

後続裁定との衝突箇所：

- **D1936項6**：旧 spool seq=4:9以降の patch 実体化採用・宣言撤去案の却下は後続裁定と逆方向。seq=3の「解き方は確定」「rr50から取り直す」も再掲しない。`s4-ruling-addendum.md:36`以降、`s6-refocus.md:30`・`:54`以降の専用関門維持は当時の判断として保存する。
- **D1936項43**：旧 seq=4:65の fixture 案は裁定待ちへ戻さない。現行 test の module fixture と独立コピーも確認できた。
- **D1936項46／47**：旧 seq=3末尾の定期smoke案と待ち手修正案を新規Tとして復活させない。
- **D1986項1**：`s6-fix2.md:23` の accepted 生成要求は未達の依頼であり成果ではない。9月10日の関門拒否と、後続裁定が保持を求めたrr5の品質却下を別の記録として扱い、どちらも緑へ読み替えない。

## 走らせる検査の列挙

**親の編集後に必要な既存検査：**

1. `git diff --check`。
2. コピー元13本との byte 比較、basename集合一致、既存 README が変更前 bytes を完全な prefix として持つことの確認。既存 job-evidence・recovery-verbatim・mutation も変更前と比較する。検査コードとしてrepoへ追加しない。
3. `python3 tools/check_docs.py`。
4. `python3 tools/spool_fold.py --dry-run --show-diff`。新規Fが増えず、意図した再発・supersedeだけが挿入され、T操作が無いことを確認する。
5. `python3 tools/check_codex_agents.py`。
6. 親の後続段で既定の受入。commit後は規定の provenance監査。

**consumer test の根拠：**

- `orchestrator/tests/test_check_docs.py:12540` の `test_real_repo_clean`  
  → 実repoの `tools/check_docs.py`  
  → 同:1259の `_check_spool_guard`  
  → `tools/spool_fold.py:1215`以降で新しいfragmentを列挙・検査する。

実走するなら次を既定runnerへ渡す。

```text
python3 tools/run_tests.py orchestrator/tests/test_check_docs.py::test_real_repo_clean
```

`test_spool_fold.py` の新規・再発・supersede混在テスト等は合成fixtureによる機構検査で、今回のfragmentを直接読むテストではない。旧READMEに列挙された calibration／Pegasus のテスト群も、今回変更する記録のconsumerとしては確認できないため、そのまま焦点対象へ流用しない。

**凍結・exact集合への静的照合：**

- `test_frozen_artifacts.py:175`は固定manifestのpathだけを読む。今回の対象pathはその集合にない。
- `hooks/guard_write.py:314`の凍結rootは `output/s8b-freeze/`。今回の追加先とは異なる。
- `tools/spool_fold.py:1195`のroot exact集合は変更しない。既存ledger配下の正規名fragment追加は同:1224以降の通常経路。
- `check_docs.py:2618`のplaceholder走査は insights直下と日付直下のMarkdownまで。topic配下は対象外で、`test_check_docs.py:5143`にも浅い走査の契約がある。**checker通過を逐語本文の正しさの証明とはしない。**

## 残るリスクと限界

- branch blob一致の既存実測は親の報告に依拠する。コピー後の13本と既着地成果物の不変性は、親が最終差分で確認する。
- 旧逐語の絶対リンクは当時のworktreeを指す。bytes保存を優先し、現在の案内は追記節へ置く。
- F766への追記は「証拠Fの選び違い」だけに限定する。既存エントリの全機序が再現したとの説明は不適切。
- insights移動ツールの過去inventoryは恒常的な新規追加禁止ではない。今回その移動計画を再適用しない。

補助的なPython読取り1件は、認証scriptのパスを実行対象と判定したPreToolUse hookに拒否された。必要な箇所は先行の静的読取りで確認済みである。

## 総括

**13本の逐語追加、既存READMEへの1節追記、failures／worklog各1fragmentで回収する。P1は新規F 2件を撤回し、F500・F766への再発へ訂正する。** F355への再発、F934への限定訂正、P2の再登録見送りは維持する。既着地成果物の変更、旧裁定の復活、accepted取得の主張は計画に含めない。