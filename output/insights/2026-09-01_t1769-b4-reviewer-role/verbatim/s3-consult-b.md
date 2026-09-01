### 所見

1. **対象:** §5.1.1 の raw / semantic sha256 と、brief の「§5.1 本体の編集は pin を破らない」という一般化  
   **内容:** plan の正確な挿入位置なら安全。ただし一般化は広すぎる。  
   **根拠:** [analysis consumer](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1769-b4-reviewer-role/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:301) は fingerprint に一致する H4 を一意に選び、次の `level <= 4` 見出しの開始直前までを終端とし、逐語で `section = document_bytes[h4.start:end]` と切り出す。H4 行自体は含み、次の同格以上の見出しは含まない。現文書では `#### 5.1.1` から `## 6.` の直前までである。実際に現行 252〜536 行の sha256 を算出すると、実装 pin と同じ `0ceab4cd...f30` だった。plan は H4 より前だけを置換するため raw bytes は不変であり、raw が同じなので semantic hash も不変。  
   一般化が成り立たない形は、H4 行以降から次の `level <= 4` 見出し直前までへの挿入、H4 後への新しい level 1〜4 見出し、section 内への新しい H5、同じ H4 fingerprint の複製、H4 を隠す未閉鎖の fence または HTML comment である。  
   **放置した場合:** plan の差分では値も受理集合も変わらない。一方、一般化を無条件に再利用すると raw / semantic sha256 または H4/H5 構造検査が変わり、consumer の受理集合が狭まる。

2. **対象:** `p3_b4_admission_record.py` の §5 表解析  
   **内容:** plan の差分は表解析へ影響しない。  
   **根拠:** [admission verifier](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1769-b4-reviewer-role/orchestrator/campaign/p3_b4_admission_record.py:625) は、fence・HTML comment と判定された行を除き、逐語で `re.fullmatch(r"## 5\.(?:\s.*)?", line)` と `re.fullmatch(r"### 5\.1(?:\s.*)?", line)` を探し、`len(starts) != 1 or len(ends) != 1` なら拒否する。表は `lines[starts[0] + 1 : ends[0]]` だけである。  
   fence は opener から対応する closer までを不可視化する。HTML comment は行指向で、先頭側が空白だけの opener 行と継続行を comment 扱いにする。開始から終端までに fence/comment 行が一つでもあれば拒否する。plan の追加文は `### 5.1` より後で、新見出し、fence、`<!--` を含まない。  
   **放置した場合:** 表の行数、ラベル、値セル、見出し個数、受理集合はいずれも変わらない。

3. **対象:** `tools/check_docs.py` の当該 living doc 検査  
   **内容:** plan の追加文に抵触はない。当該文書には byte 数・最長行の予算は掛からない。  
   **根拠:** [check_docs.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1769-b4-reviewer-role/tools/check_docs.py:128) は当該文書を `LIVING_DOCS` に列挙する。実際に掛かるのは次である。

   - 列挙対象の存在、および symlink を含まない regular file・UTF-8・読取可能性
   - `LINE_REF_STRICT` による自 repo docs の行番号参照禁止
   - `現在は Phase` という現況主張の禁止
   - `pin.CURRENT_PIN` の現在値 literal の再掲禁止
   - `\bD(\d{1,3})\b` に一致する D 参照の実在性
   - `PATH_REF` に一致する repo 内ファイル参照の実在性

   `TextLimit` の対象集合には当該文書がなく、byte 予算も最長行予算もない。`次 =` 検査は `CLAUDE.md` と `roadmap.md` だけなので掛からない。提案文は上記禁止形を追加しない。  
   **放置した場合:** `check_docs.py` の当該文書に関する受理結果は変わらない。

4. **対象:** brief の「文書 bytes を束縛する admission record は repo に存在しない」という主張  
   **内容:** この射影内では裏取り不能。実装上、record が存在すれば文書全体が明確に束縛される。  
   **根拠:** [admission verifier](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1769-b4-reviewer-role/orchestrator/campaign/p3_b4_admission_record.py:746) は宣言 commit の文書について `_sha256(document_blob) != declared.preregistration_content_sha256` を拒否し、さらに `head_document_blob != document_blob` も拒否する。required path は `...-base.json`、`...-sort.json`、`...-trigger.json` の 3 本である。したがって「whole-file binding の機構が無い」は誤りであり、「現時点で record 実体が無い場合に限り active な whole-file binding が無い」が正確である。  
   不在確認には、少なくとも HEAD の tree と working tree の両方でこの 3 exact path を確認し、repo 全域で文書 basename、`p3-b4-prerun-admission/v1`、`verify_b4_admission_record`、`preregistration_content_sha256` を検索する必要がある。射影外の path・repo inventory は読めないため、実行していない。  
   **放置した場合:** record が実在していた場合、この docs 編集により `preregistration_content_sha256` または HEAD 文書一致が破れ、`VerifiedB4AdmissionRecord` を生成できる受理集合が空になる。

5. **対象:** plan が挙げていない consumer・検査の見落とし  
   **内容:** 指定 6 ファイル内では、新たな独立 consumer は見つからなかった。ただし repo 全域不存在は確認不能。  
   **根拠:** 許可された 6 ファイルに対し、exact に次を検索した。  
   `phase3-b4-reflux-ablation-preregistration\.md`、`PREREGISTRATION_SECTION_5_1_1`、`verify_b4_admission_record`、`preregistration_content_sha256`、`p3-b4-prerun-admission/v1`、`p3_b4_analysis_prereg_consumer`、`p3_b4_admission_record`、`check_docs\.py`。  
   文書 basename の機械側 hit は analysis consumer、admission verifier、`LIVING_DOCS` の 3 か所だった。ただし analysis consumer は [receipt 生成](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1769-b4-reviewer-role/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:1027) で全文 bytes を `analysis_path._generate_analysis_source_closure_receipt` へ渡している。その実装は射影外なので、section hash 以外の派生値を持たないことまでは確認できない。  
   **放置した場合:** 射影外 consumer が全文 bytes を束縛していれば、その receipt・hash・受理集合が変わりうる。現時点では「見つからない」ではなく「確認範囲外」である。

### 安全な挿入位置の条件

- 提案文を、既存の「対象 driver と軸」bullet 内、`### 5.1` より後かつ認識される `#### 5.1.1` の開始 byte より前だけに置く。
- `#### 5.1.1` から次の `level <= 4` 見出し直前までの bytes を変えない。
- H4 fingerprint「5.1.1・分析契約・一括凍結」を複製せず、H4 を隠す未閉鎖 fence・HTML comment を置かない。
- `## 5.` と `### 5.1` を、それぞれ fence/comment 外の exact 1 件に保つ。両者の間へ新しい見出し、fence、HTML comment、非空行を加えない。
- §5 の表行・値セルへ書かない。
- 行番号参照、`現在は Phase`、current pin literal、新しい D 参照、新しい repo path 参照を追加しない。
- 3 種の admission record が実在しないことが別途確認済みであること。実在する場合、docs-only 差分だけでは whole-file binding を保てない。

## 総括

plan の正確な置換文は、§5.1.1 の raw / semantic pin、§5 表解析、`check_docs.py` の当該検査を壊さない。  
提案文を変える必要はない。  
ただし「§5.1 本体なら常に安全」という一般化は誤りで、位置・見出し・fence/comment の条件が付く。  
また admission record 不在と repo 全域の consumer 不在は、指定された射影内では確認できない。  
したがって結論は条件付き通過であり、whole-file binding 不在を無条件の確認済み事実として扱ってはならない。