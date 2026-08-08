### [BLOCKER] 案 A は実行時 model の precedence を一意にしない

- 根拠: 段 3 は `DW-S03` と `DW-O01` を同時に読む契約です（[dev-wave.md:63](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/.claude/commands/dev-wave.md:63)）。変更後の S03 は luna になりますが、O01 の実行可能な雛形は引き続き `-m gpt-5.6-sol` です（[workers.md:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/dev-wave/workers.md:12)、[operations.md:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/dev-wave/operations.md:8)）。`DW-C00` は worker 本文と operation 本文の優先順位を定めず、scope 不整合なら停止させます（[core.md:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/dev-wave/core.md:7)、[core.md:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/dev-wave/core.md:22)）。案 A は見出しだけで O01 の `-m` を書き換える規則や「無記載時は既定値」の規則を本文にしません（[s2-plan.md:9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t182-luna-stage3/s2-plan.md:9)）。
- 具体的な失敗経路: manager は、(a) O01 を逐語的な executable recipe として sol を起動する、または (b) luna と sol の不整合として `DW-STOP` する、の二通りに読めます。S05-A、S06-A、S06-B は model 無記載であり、S06-B の継承列挙にも model がありません（[workers.md:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/dev-wave/workers.md:22)、[workers.md:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/dev-wave/workers.md:43)、[workers.md:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/dev-wave/workers.md:48)）。従って「無記載なら O01=sol」も、案 A の文面からは導出規則ではなく推測です。
- 第 4 案 D: O01 の現行見出しと本文を残し、command 側に `codex \`-m\` は worker 節の model、無記載なら \`DW-O01\` の値とする。` を exact literal として追加・pin する。この文は 80 bytes、前後改行込みで **+82**。command は **9,035→9,117 / 9,500**（残り383）、reference は S03 slug の **+1**だけで **25,197 / 25,200**です。案 A より82 bytes多い一方、別予算を使い、起動見出しを保持し、S05/S06 の fallback まで明文化できるため契約品質は上です。安全義務の prose は削りません。
- 成果物影響: 段3が sol で走るか停止し、さらに段5/6の model が不定になるため、land 前の欠陥検出力と worklog の model 帰属が契約値からずれます。

### [BLOCKER] model pin は期待 slug の decoy が一つあれば実起動 drift を通す

- 根拠: 提案 regex は `codex` の直後に水平空白と backtick slug がある場合だけを認識します（[s2-plan.md:28](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t182-luna-stage3/s2-plan.md:28)）。値が `[expected]` なら受理するため（[s2-plan.md:49](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t182-luna-stage3/s2-plan.md:49)）、`codex exec -m ...`、`--model=...`、改行後の slug は検査外です。checker 呼び出しも workers 本文だけを渡し（[check_docs.py:3576](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/check_docs.py:3576)）、O01 の実 `-m sol` は見ません。Bash 経由の `codex exec` は hook の管轄外でもあります（[hooks/README.md:140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/hooks/README.md:140)）。
- 具体的な失敗経路: S03 を次の形にできます。

  ```text
  ## DW-S03

  codex `gpt-5.6-luna`、`-m gpt-5.6-sol`、`reasoning=max`、...
  ```

  regex が拾う model は luna 一件だけです。S03 見出しを現行32 bytesから bare ID の9 bytesへ縮め、`-m sol` 部分19 bytesを加えても、案 A 後の合計は **25,197−23+19=25,193**。H2 検査は ID しか見ないため通ります（[check_docs.py:3630](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/check_docs.py:3630)）。さらに案 A の O01 見出しを同じ37-byteの現行見出しへ戻して precedence だけ消しても、どの検査も発火しません。
- 成果物影響: `check_docs` が緑でも実際の CLI は sol を要求でき、機械検査の受理集合に「docs/worklog=luna、実起動=sol」が残ります。

### [BLOCKER] M3〜M5 は公開経路の単一理由変異として成立していない

- 根拠: `DW-M01` は前後層による同一入力拒否の不存在と単一赤理由を要求します（[mutation.md:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/dev-wave/mutation.md:5)）。F28 は private helper 直呼びによる偽 KILL を明示的に禁じています（[failures.md:482](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/failures.md:482)）。しかし段2プランが公開経路として用意するのは S03=sol の一件だけです（[s2-plan.md:74](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t182-luna-stage3/s2-plan.md:74)、[s2-plan.md:89](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t182-luna-stage3/s2-plan.md:89)）。

  | 変異 | 静的判定 |
  |---|---|
  | M1 caller 削除 | 公開経路 S03=sol があるため単一理由にできる。 |
  | M2 S03 tuple 削除 | 同じ公開入力は成立するが、全 S03 negative も同時に無効化する。対象 node を限定しなければ単一赤にならず、プランは node を登録していない。 |
  | M3 `if values and ...` | missing S02、missing S03、comment-only がすべて受理へ変わる。複数赤かつ direct helper のみ。 |
  | M4 `expected not in values` | expected を含む全 duplicate/decoy を受理する。公開経路テストがなく、現行実文書へ単純追加すれば先に byte gate に食われる。 |
  | M5 raw section | comment-only を誤受理する一方、正例の comment/fence example を誤拒否する。受理拡大と縮小の二理由で赤になる。 |

- 具体的な失敗経路: M3〜M5 を helper test だけで KILL と数えると、caller が未接続でも KILL できます。逆に実文書へ duplicate/comment を足した入力は、残り3 bytesを超えて model pin より先に byte gate で落ち、目的の変異へ到達しません。各入力を headroom のある `_build_min_repo()` 経由にし、exact finding 一件を固定する公開経路テストが必要です。
- 成果物影響: 無効または過剰決定な変異を KILL と記録し、実効性のない model gateを検証済みとして land させます。

### [SHOULD] O01 見出し変更は ID 配線を保つが起動義務の意味上の索引を失う

- 根拠: 条件01は「codex subprocess を起動する直前」に O01 を読むと規定します（[dev-wave.md:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/.claude/commands/dev-wave.md:84)）。一方、案 A は見出しから同じ語を完全に消します（[s2-plan.md:9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t182-luna-stage3/s2-plan.md:9)）。H2 orphan 検査は em-dash 前の ID だけを取得し、見出し語を検査しません（[check_docs.py:3634](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/check_docs.py:3634)）。
- 具体的な失敗経路: ID を忠実に追う manager なら読み飛ばしません。しかし条件名と見出し語で leaf を意味検索する reader は、O01 を「model precedence の節」と分類して起動手順を未読のまま直接 `codex exec` できます。その場合 nohup/setsid、`.done`、prompt 非空、`check_codex_output` がまとめて脱落しても checker は緑です。
- 成果物影響: 未完了・空出力のレビューを完了扱いし、must-fix の取りこぼしを含む実装が land し得ます。

### [SHOULD] byte 数値は LF checkout では正しいが、checker は visible ではなく raw bytes を数える

- 根拠: checker は `newline=""` で読み、raw text を UTF-8 encode して数えます（[check_docs.py:3526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/check_docs.py:3526)、[check_docs.py:3542](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/check_docs.py:3542)）。`_visible_markdown_text` はこの会計には使われません（[check_docs.py:1005](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/check_docs.py:1005)）。

  | 案 | core余裕 | workers余裕 | mutation余裕 | operations余裕 | 合計 / 25,200 |
  |---|---:|---:|---:|---:|---:|
  | A | 954 | 424 | 76 | 99 | **25,197**（残3） |
  | B | 954 | 422 | 76 | 99 | **25,199**（残1） |
  | C | 954 | 424 | 76 | 97 | **25,199**（残1） |

  見出し・slug・placeholder の差分は段2プランどおりで、現 checkout の数値自体に誤りはありません。command は **9,035 / 9,500**（残465）です。

- 具体的な失敗経路: 現在は全5文書が LF・末尾改行ありなので raw=visible です。しかし root の EOL 固定がなく、4 reference を CRLF 化すると案 A は改行381本ぶん増えて **25,578**、operations 単体も **8,432 > 8,400**になります。逆に末尾改行削除は1 byteの「余裕」として受理されます。
- 成果物影響: 表示内容が同じ文書でも checkout/EOL により機械検査の受理結果が変わり、CIや別環境で land 可否が不安定になります。

### [SHOULD] 棚卸しは現行 wave の実 launch surface と非文字列 consumer を落としている

- 根拠: プランの棚卸しは tracked tree の文字列一致に限定されています（[s2-plan.md:95](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t182-luna-stage3/s2-plan.md:95)）。しかし Codex Skill は全 worker を O01 の直接 subprocess へ結線しています（[SKILL.md:32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/.agents/skills/dev-wave/SKILL.md:32)）。従って [operations.md:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/dev-wave/operations.md:8) は「model 無記載 worker の既定」だけではなく、段3にも到達する live command です。また現 wave の [launch-s3.sh:19](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t182-luna-stage3/launch-s3.sh:19) と両 lens のログ先頭は実際に sol を示しています（[lensA.log:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t182-luna-stage3/s3-lensA.log:5)、[lensB.log:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t182-luna-stage3/s3-lensB.log:5)）。
- 具体的な失敗経路: luna probe は別 job では成功しており、requested slug と13,017 tokens、rc=0は確認できます（[luna.log:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t182-luna-stage3/s1-probe/luna.log:5)、[luna.log:265](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t182-luna-stage3/s1-probe/luna.log:265)、[luna.done:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t182-luna-stage3/s1-probe/luna.done:1)）。ただしそれを本 wave の段3実行と取り違えると、P2の「全 lens luna」と実測が食い違います。bootstrap として現段3を sol で走らせたなら、その事実を明記する必要があります。
- 成果物影響: 現回の敵対所見を luna の結果として worklog に記録すると provenance が誤り、将来の model 比較・rollback 判断の入力を汚します。

## 総括

BLOCKER は **3件**です。  
最も危険なのは、workers の luna pin が通っても O01や別構文の `-m sol` が実行できる点です。  
このままでは `check_docs` 緑と実際の段3 model、worklog の帰属が乖離します。  
pytest・`check_docs.py` は実行しておらず、指定どおり静的検査のみです。