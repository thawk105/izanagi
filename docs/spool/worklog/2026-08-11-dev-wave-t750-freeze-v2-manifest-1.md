---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t750-freeze-v2-manifest
seq: 1
title: T-750 統合実装 — freeze v2 producer と reviewed spec を pinned literal 承認で実装し、choke point の cell-product 検査で縮小 schedule を塞いだ (コード + docs、変異 6 KILLED + 2 MISMATCH = 実質 8/8、branch worktree-dev-wave-t750-freeze-v2-manifest)
---

## 本文

- **起票根拠 = worklog 405 の [T-750] 裁定 2 点 (ともに (a)) と 404 の [T-782] (b)。**
  並走ガード 3 条件は起票文へ記載済み。**キュー投入の直前に毎回 `qstat` で再確認**し、
  走行中は他 wave の汎用テスト dispatch (`izdw-*`) だけで [T-139] の pilot / 本走は
  wave を通じて一度も走っていなかった。ノード同居なし。
- **[T-782] の spec 凍結は未所有と確定してから着手した。** 稼働中の 8b 残余 wave
  (`dev-wave-t8b-restart-residue`) の brief §scope 外 が「W-3 / W-4 / W-5 — [T-750] 未裁定。
  着手しない」と明記しており (同 wave の base main は裁定を含まない)、file 所有も重ならない。
- **段 3 の敵対 2 レンズ (max) がいずれも NO-GO** (BLOCKER は A が 4 件、B が 3 件)。
  段 2 プランは人間承認を「非 merge commit + 逐語 `AI-Agent: none`」で表そうとしたが、
  これは D86(8) が禁じた「artifact の存在を認可の証明として扱う」形であり**恒真化**である。
  親は承認 authority を **module 内 pinned literal** (`V1_FREEZE_SHA256` や env contract の
  reviewed golden と同型) へ差し替えた。未承認のあいだ定数は `None` で、機構全体が fail-closed する。
- **段 4 で親が 4 点を追加実測し、[T-782] (b) の文言を超える追加を裁定した。**
  (i) direct `verify()` は本 wave と無関係に既に RED (`design_source` の drift)、
  (ii) judge の product 検査は holdout 間の不一致しか捕えず一様 subset は通る、
  (iii) `run-block` は任意の `--manifest` を `verify_manifest` へ通すだけで
  **choke point は CLI ではない**、(iv) `verify_manifest` は既に freeze document を持つ。
  → CLI だけでは A-9 (縮小 schedule による certified 選択の直接改変) が閉じないため、
  **`verify_manifest` に cell-product 検査を足した**。方向は受理集合の縮小のみ。
  事後承認を裁定パッケージ P-2 で求める。
- **段 6 の敵対レビュー 2 本 (high) がいずれも NO-GO を返し、独立に同じ BLOCKER を指摘した。**
  親が段 4 で追加を裁定した cell-product 検査は、初版が期待積の holdout 集合を **schedule 自身**
  から導いており、**holdout を丸ごと落とした manifest を受理していた**。configuration の
  間引きは塞いだが holdout の欠落は素通りしていた。fix で
  `schedule の holdout 集合 == set(freeze["holdouts"])` を先に要求する形へ直した。
  他の must-fix 6 件 (closure の HEAD 束縛、v2 専用 module の eager import、canonical bytes の
  自己参照 assert、`-0.0` の受理、変異 4 件の単一理由性、candidate 出力先 parent の不在) も閉じた。
- **親の実測 2 件を自分で訂正した。** (i) 段 1 の M-1「T-080 受領証が generator sha を
  metadata-only で受理済みだから受理集合は変わらない」は**機序が誤り**で、実際は direct 経路が
  `design_source` の drift で既に RED である (結論だけ正しい)。(ii) M-5(ii)「configuration 網羅の
  検査は repo に不在」は言い過ぎで、judge に部分検査がある。
- **変異 matrix は 8 件中 6 KILLED / 2 MISMATCH / SURVIVED 0。** MISMATCH はいずれも
  **親の期待 node の誤り**であり、コード側の欠陥ではない。MU-3B は期待 2 node に対し 3 node が
  落ちた過剰 kill (超過分は happy path)、MU-6 は期待 3 node に対し 2 node で、落ちた側に
  「pin 無しでは出力前に失敗する」行動テストが含まれるため `DW-M03` の kill は成立している。
  `DW-M02` に従い初回結果を消さず erratum として残した。**実質は 8/8 である。**
- **エージェント工数**: codex 子 7 本 (プラン 1 = max / 敵対相談 2 = max / 実装 2 = high /
  レビュー 2 = high) + fix 2 本 = 9 本。親は brief・裁定・統合・実走・記録。
- **空振り 3 件 (いずれも codex 未起動 or 誤判定、成果物への影響なし)**: (i) `--artifact-root` の
  親 dir 不在で argparse error、(ii) `--stage review` へ `--reasoning` を渡して argparse error、
  (iii) 変異の再投入で `.done` 名を変えず、待ち手が**前回走行の stale marker**を掴んで
  「完了」と誤報告した (実際は走行中で、pid 照合で判明)。3 件とも段 8 の候補へ回した。
- **ユーザー手番**: 裁定 4 件 ({{T:oracle-spec-trust-root}}・P-2〜P-4、逐語は
  `output/insights/2026-08-11_t750-freeze-v2-manifest/package.md`)。push は行わない。

## 次の一手差分

### 更新

- [T-750] **P2・実装完了 (2026-08-11) → 残りは裁定パッケージ 4 件と将来の実凍結手番 (B 系)**:
  裁定 2 点をともに実装した。producer は旧 module 内 (`s8b_holdout_freeze.py`) の
  `generate-v2-candidate` として実装し、記録上の generator と実 producer を一致させた。
  budget authority は pinned literal `BUDGET_APPROVAL_SHA256` (現在 `None`) で、承認済みのときだけ
  approval record の bytes hash と exact 一致し、`approval["budget"]` と入力 budget の
  canonical bytes 完全一致を要求する。must-fix (A-8/B-9 の出力 path containment、B-8 の
  namespace 検査) も同 wave で閉じた。実走データは synthetic fixture のみ ([T-781] 待ち)。
  残余 = {{T:oracle-spec-trust-root}} と裁定パッケージ P-2〜P-4
  base: 4a60665aa0a83077dd2b969340c470de7bb1d786f4d187a11ae7d6deae0c5dbf
- [T-782] **P1・実装完了 (2026-08-11) → 承認手番待ち (B 系)**: reviewed spec の schema・
  validator・pinned literal 承認 (`APPROVED_SPEC_SHA256`、現在 `None`) を新 module
  `s8b_oracle_spec.py` に置き、`build-approved` CLI (値入力は `--output` だけ) を足した。
  **spec の承認者 = ユーザー、時点 = 将来の実凍結手番**とし、その手番で行うのは
  (i) candidate spec の内容確認、(ii) canonical path への設置、(iii) 定数への hash 記入 の 3 つ。
  承認形そのものの恒久裁定は {{T:oracle-spec-trust-root}} へ分離した
  base: dd1106a48507017890242ab054362ac53b001440bae152350a5a484fabca67fe

### 新規

- {{T:oracle-spec-trust-root}} **P1・新規 (ユーザー裁定待ち、B 系)**: 「人間が承認した」を
  機械で表す形の恒久裁定。本 wave は pinned literal (人間がコード diff をレビューして定数を置く)
  を暫定形として実装したが、これは既存 reviewed golden と同型というだけで暗号学的な人間性証明では
  ない。段 3 レンズ A は恒久案として「人間だけが保持する鍵による署名」を挙げたが、repo に鍵管理の
  trust root が無く新設は D86 の再裁定を要するため親は不採用にした。
  択 = (a) pinned literal を恒久形として承認 (親推奨) / (b) 署名方式を新設 / (c) 運用規律に委ねる
- {{T:manifest-spec-propagation}} **P1・新規 (ユーザー裁定待ち、B 系)**: A-9 の残余。
  本 wave は choke point (`verify_manifest`) で cell 集合を freeze の全 product へ束縛したが、
  **cell 集合以外 (`n` / `master_seed` / campaign ID / run contract) は approved spec を迂回**して
  変更でき、試行数・WAL 所有・report 数値が変わる。閉じるには manifest schema へ `spec_sha256` を
  持たせ driver / report / judge の全層で再検証する必要があり、これは [T-782] で不採択となった
  (a) 側の scope 拡大である。択 = (A) 現状で止める / (B) schema 伝播 wave を起票 (親推奨) /
  (C) oracle 結線 wave へ送る
- {{T:budget-authorization-proof-chain}} **P1・新規 (ユーザー裁定待ち、B 系)**:
  budget 承認が ratified proof chain に残らない。producer は生成時に一致を検査するが、
  v2 schema に budget authorization の field が無く、transition table は `/budget` を自由変更可能と
  しており、equality chain にも edge が無い。**producer を経ない自己整合 g1 なら任意の budget が
  世代承認を通りうる。** 構造化 field の追加は凍結契約 (transition table) の変更を伴うため
  親は実装しなかった。択 = (a) v2 schema へ `budget_authorization` を追加 /
  (b) 運用規律に委ね受理集合の広さを明示受諾 / (c) [T-657] の世代交代と合流
- {{T:dev-wave-launch-procedure-gaps}} **P3・新規 (段 8 発、予算超過で撤回)**: 本 wave で実測した
  dev-wave 手順の欠落 3 件を `DW-O01` / `DW-O02` へ 1 行ずつ統合しようとしたが、
  `DW-O01` が 1077 bytes となり単節予算を超え、さらに dispatcher route 行の exact 1 件検査にも
  抵触したため撤回した (L1.5 の unique footprint も 9926 > 9566 で超過)。
  内容 = (i) `--stage review` / `focus` へ `--reasoning` を渡すと codex を起動せず rc=2、
  (ii) `--artifact-root` の親 directory が無いと同じく起動せず rc=2、
  (iii) 再投入で `.done` 名を使い回すと待ち手が前走の marker を掴んで偽完了を報告する
  (待ち手は producer の pid で生死を見る)。**予算のために安全義務を削除・弱化する案は採らない。**
  docs 予算棚卸し wave の package で入庫可否を判定するのが妥当
- {{T:legacy-writer-path-containment}} **P2・新規 (ユーザー裁定待ち、B 系)**:
  `s8b_holdout_freeze.generate(output_path=...)` と `s8b_oracle_manifest.write_manifest(path, ...)` は
  任意 path を受理し続けるため、programmatic には canonical namespace へ到達でき、到達すると
  `namespace-dirty` で certified 選択・レポート・台帳がすべて欠落する。本 wave は新設経路のみを
  閉じた。旧 API を狭めると v1 の受理集合が変わるため親は決めない。
  択 = (a) v1 不変条件を「document 判定」に限定し直して旧 writer を狭める /
  (b) OS 権限で canonical namespace を隔離 / (c) 現状維持で終端
