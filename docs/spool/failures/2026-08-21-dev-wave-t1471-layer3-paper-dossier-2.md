---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-21
wave: dev-wave-t1471-layer3-paper-dossier
seq: 2
---

## 新規

### {{F:codex-citation-header-drift}}. codexが挙げるfile:line引用が実データ行でなく見出し/表ヘッダ行を指すことがある [手順漏れ]

- 事象: [T-1471] layer3 paper evidence dossier wave の段2 (codex plan, reasoning=max,
  read-only) が起草した file:line 索引について、段3 敵対相談レンズBが最低12件を無作為抽出して
  実ファイルと突合したところ、半数以上が「引用行は節見出しや表ヘッダであり、実際の数値・判定は
  数行〜十数行下にある」というズレだった (例: `s_prime_final_report.md:18` は Holm表の見出しで
  実際の値は20-23行、`p2-2-summary.md:7` は表ヘッダでread-heavyの値は9行)。段3レンズAも独立に
  同型の指摘 (`s_prime_final_report.md:66` が確定手続きの見出しでS' verdict本体は57-62行) を
  行った。親が全件を一次資料で裏取りし、正しい行番号に差し替えて report へ反映した。
- 根本原因: codex は「この情報はこの節にある」という意味で最も近い見出し行を機械的に指す傾向が
  あり、プロンプトが「file:line 粒度」を要求しても、見出し行と内容行の区別を明示しなければ
  自然にヘッダ行へ寄る。
- 恒久対応: 段3 敵対相談 (または最終的に親) が、codex の file:line 索引から無作為抽出した
  サンプルを実際に開いて突合する検査を必須の chunk とする。本 wave では段3レンズBのプロンプトへ
  「最低12件の抜取り検査」を明示的に指示し、これによって発見した。今後の codex plan/consult
  プロンプトに「見出し行でなくデータそのものの行を指せ」を明示追加する候補を段8へ送る
  (dev-wave docs 予算逼迫のため本 wave では追記せず候補記録のみ)。
- 再発検知: codex plan/consult 出力の file:line 索引のうち無作為抽出した N 件 (目安 12件以上)
  を実ファイルと突合し、不一致が1件でもあれば索引全体を無条件には信頼せず、最終成果物へ転記する
  前に該当箇所を親が個別に裏取りする。

### {{F:dryrun-tnumber-mistaken-as-reserved}}. spool_fold.py --dry-runが表示する予測T/D番号を、別の依頼が「既存の予約ID」と誤読した

- 事象: 「[T-1471]」という識別子を伴う作業依頼が来たが、`docs/worklog.md`・`docs/decisions.md`・
  `docs/handoff/` のいずれにも landed な予約 ID としては存在しなかった (grep 0件)。実際には、
  並行稼働中の別 wave (`dev-wave-t1473-d58-ablation-preflight`) の worklog spool fragment
  placeholder に対して当時実行された `spool_fold.py --dry-run` が、その時点の状態で
  「実採番は `[T-1471]`」と予測表示していただけであり、当該 wave 自身の handoff が
  「並行 land でずれうるため確定値として扱わない」と明記する非確定値だった。依頼文はこの
  dry-run 予測値を、まるで既存の予約済み ID であるかのように扱っていた。
- 根本原因: `spool_fold.py --dry-run` は具体的な番号 (`[T-1471]` 等) を画面に表示するため、
  それを見た人間や別セッションが「この番号は既にこの項目に確定的に割り当てられた」と誤読しやすい。
  実際には T/D/F の実採番は land 時の fold が lock 内で行うまで確定しない
  ([[fold-allocation-numbers-are-provisional]])。
- 恒久対応: dry-run が表示する予測番号を、以降の依頼文・branch名・識別子として引用する前に、
  当該番号が対象 wave 自身の handoff/worklog で「未確定」と明記された dry-run 由来のものでないかを
  確認する。`docs/spool/worklog/README.md` の bracket ID 規則 (既存 active item のときだけ
  角括弧 ID を書ける) に従えば、この種の誤認は「角括弧なしで記録する」ことで自然に回避できる
  (本 wave で採用した対応)。
- 再発検知: 依頼文や branch 名に現れる `T-NNNN`/`D-NNNN` が `docs/worklog.md` の次の一手・carry
  または `docs/decisions.md` に実在する landed ID か、それとも別 wave の dry-run 予測値かを、
  着手前に `grep -rn "T-NNNN" docs/worklog.md docs/decisions.md docs/handoff/` と対象候補 wave の
  handoff 本文の両方で確認する。
