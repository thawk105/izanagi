---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-15
wave: dev-wave-t817-epoch
seq: 1
title: verifier epoch を導出ラベルとして入れ、certified を名乗る 16 経路から E0 を外した — 変異 7/7 KILLED、裁定 2 件をユーザーへ返す (コード + docs、branch worktree-dev-wave-t817-epoch)
---

## 本文

- **裁定どおりの scope を実装し切った。** `campaign_verifier_epoch` を v2 lock の**既存 authority
  からの導出ラベル**として入れ、除外の適用点を読み取り側の受理層 1 箇所へ集約した。
  各 consumer は `purpose` の**呼び出し方**で「受理集合として読む」か「歴史生値として読む」かを
  表明する ({{D:epoch-purpose-declaration}})。新 lock field、新 JSON artifact、新しい凍結 pin、
  署名機構はいずれも作っていない。
- **段 1 の実測が裁定文の欠けを 1 つ埋めた。** 裁定パッケージは「v2 lock を持つ campaign は
  bytes が既に pin されている」と書いていたが、**実 corpus の lock 版数は v1 30 / v2 0** だった。
  したがって E0 = 既存 30 campaign 全部であり、除外の母集合は P2-2 の 24 attempt に留まらない。
  裁定の substance (P2-5 の replay/guided/baseline が停止することを承知の上での選択) は覆らないが、
  適用面の広さが確定した。
- **consumer は 8〜10 経路ではなく 16 経路だった。** 段 3 の敵対 2 レンズが独立に
  `s6_sort_sweep` / `s8a_trigger_sweep` / `backoff_sweep_report` /
  `autonomous_trial_completeness` / p3 loop 群 / `plot_backoff.py` / `critic/online_digest` を
  追加発見した。取り込み後の AST 集計で実呼び出し 65 件のうち production 16/16・test 48/49 が
  purpose を明示し、残る 1 件は purpose 必須を確かめる意図的な負例である。
- **変異 7/7 KILLED、SURVIVED 0、baseline 緑。** 負例の発火は合成でなく実在 artifact
  (`p2-2-silo-read-heavy-enumerate-5ffcabad`、v1 lock、現行 admission を通る) で示しており、
  「既存 admission を通る記録が新 gate だけで落ちる」ことが恒真でないことの証拠になっている。
- **初回の変異走は probe だった ({{F:new-gate-preempts-downstream-checks}})。** MUT-4/5/7 が
  MISMATCH で、原因は検出力不足ではなく**事前登録した期待 node 集合の不完全さ**である
  (登録 1 件に対し実際の kill は 31 / 8 / 30 件)。新設 gate が発火すると後段の loop が走らないため、
  一見無関係な既存テストが同じ分岐に依存し始める。`DW-M08` の「初回を probe と明記して完全集合を
  再登録し再走」で閉じた。baseline が完全に緑であることが観測 kill 集合を採用してよい根拠である。
- **前 job が段 6 の変異 matrix で無音死し、本 job が引き継いだ。** 停止の原因は既に解決済みで、
  前任者は期待 node を param 付きへ直し script の期待 sha256 も更新した直後に落ちていた。
  **残っていたのは再走であって原因調査ではなかった。**
- **main を 69 commit 取り込んだところ、衝突 1 件のほかに「行が競合しなかった穴」が 3 件出た。**
  衝突は [T-244] の 8c 多世代開放が同じ分岐を fail-closed へ強化した箇所で、両側を保存する合成に
  した。残る 3 件は conflict marker が出ない面 — main から入った `require_admitted_campaign`
  呼び出しの purpose 省略 2 件と、[T-856] が新設した `test_s8b_verdict.py` の合成 fixture が
  epoch を宣言していない 1 件である。**後者は本 wave の gate が正しく fail-closed で発火した結果**
  なので gate は緩めず、fixture 側へ certified E1 の宣言を足して閉じた。production は 1 行も
  変えていない。**行が競合しないことは意味が壊れていないことの証拠にならない**
  ({{F:non-conflicting-merge-hides-semantic-breakage}})。
- **焦点走の赤 8 件のうち 6 件は非帰属だった。** 5 件は login node に `/tmp/.git`
  (2026-07-28 作成の空ディレクトリ) が実在して `_has_git_ancestor` が発火する [T-698] の環境要因、
  1 件は `codex_roles` の import 経路依存の既知偽赤である。
- **計算資源が本 wave の実質的な律速だった。** 2026-08-15 21:57–23:20 JST の間、`gen_S` は
  実行中ジョブ 0 のまま待機列だけが残り、dispatch 経路は 15 分の `queue-wait-timeout` を 3 回
  返した。bounded local も代替にならず、予算が「前回ピーク × 1.25」でしか伸びないため
  `test_s8b_verdict.py` 単独走で 2 走を空費した。**`IZANAGI_TEST_NPROC=4` で並列度を落とすのが
  実際に効いた唯一の手**で、65 秒で完走した。変異 8 走もこの設定で回している ([T-1127] 関連)。
- **段 8 の自己改善は 1 件が予算で入らず、裁定へ返した。**
  {{F:non-conflicting-merge-hides-semantic-breakage}} の恒久対応 (取り込み時の合成監査) は
  発火点が「統合後の再検証」なので `DW-S06-C` へ統合しようとしたが、**L1.5 の unique footprint
  予算の余白は 7 bytes** しかなく、325 bytes の追記は入らなかった (9884 > 9566)。
  同節を含む層の棚卸しは独立 2 wave が「削除可能な節ゼロ件」を実証済みで、
  意味等価な縮約の余地もない。契約どおり編集を撤回し、新規 L2 節 + dispatch 条件の追加として
  {{T:merge-synthesis-audit-dispatch}} へ起票した。**予算値の引き上げは提案しない。**
- 材料の正本 = `output/insights/2026-08-15_t817-verifier-epoch/`
  (変異台帳 2 本、段 4 裁定、裁定パッケージ、取り込み合成監査、fix 報告の逐語)。

## 次の一手差分

### 完了

- [T-817] 裁定 Q1(a) 限定形 / Q2(a) / Q3(a) / Q4 の scope をすべて実装し、変異 7/7 KILLED で
  検出力を示した。scope 外で出た real 所見 2 件は裁定パッケージへ返した。
  remaining: none
  base: 77d3b2718dc9c3e40571f59b7b5d879eb5aec0f616c75ed31e2a79058eba20b1

### 更新

- [T-834] **P2・ユーザー裁定待ち**: 旧 certified / 旧 fitness を読む生きた consumer の分類は
  本 wave が 16 経路で完了し、全経路に受理目的を機械的に表明させた (段 3 の敵対 2 レンズが
  当初の 8〜10 経路に 7 経路を追加発見)。**これで本項を閉じてよいかがユーザー裁定**である
  (裁定パッケージ Q2、親推奨 = 閉じる)。独立に悉皆性を検査したい場合のみ本項を継続する。
  base: 7bf3998b3409ceff192eb5f8ea01c6f4f3d5d5dac14095f15484696ff6ed0c0d

### 新規

- {{T:epoch-authority-verifier-closure}} **P1・ユーザー裁定待ち**:
  `campaign_verifier_epoch` が束縛する authority は enforcement source closure の exact 8 path で、
  そこに正しさ判定の実体である `orchestrator/verifier/{core,dsg,model,parse}.py` が**入っていない**。
  E1 の lock を作った後に `verifier/model.py` だけを書き換えて `VerifyResult.certified` を常に真に
  しても epoch は変わらず、anomaly を含む run が同じ epoch の certified 集合へ入りうる。
  親推奨 = closure を広げる (実 corpus に v2 lock が 0 件の今なら壊れる既存成果物はゼロで、
  効くのは将来 run だけ)。本 wave は裁定 Q3 が「**既存**の authority へ束縛する」であることを
  理由に、名乗りの限定 (docstring と構造化診断で束縛範囲と除外範囲を明記) だけを行った。
  詳細と選択肢 3 案は `output/insights/2026-08-15_t817-verifier-epoch/verbatim/ruling-package.md`。
- {{T:merge-synthesis-audit-dispatch}} **P2・ユーザー裁定待ち**:
  取り込みの合成監査を dev-wave の dispatch 経路へ載せるか。現行 `DW-O17` が Codex 著者を
  要求するのは「実装面 path が両親と異なる」ときだけで、**片側が呼び出し規約を厳しくし、
  もう片側がそれを知らずに新しい呼び出しを足した**場合は行が重ならず素通りする
  ({{F:non-conflicting-merge-hides-semantic-breakage}})。本 wave はこの型で 3 件の破壊を出した。
  `DW-S06-C` への統合を試みたが L1.5 予算の余白が 7 bytes で入らず撤回した。
  選択肢は (a) 新規 L2 節 + dispatch 条件を足す、(b) L1.5 の既存節を縮約して枠を作る
  (棚卸し済みで余地なしと実証されている)、(c) failures 台帳の記録だけに留める。
  親推奨 = (a)。理由: 発火実績があり、`check_docs` にも provenance checker にも機械代替が無く、
  同じ発火点を持つ既存正本も無い (D271 の鏡像 3 条件をすべて満たす)。
  ただし command 入口の dispatch 表を触るため、段構成に近い変更として裁定に委ねる。
- {{T:mutation-harness-node-diagnostics}} **P3・新規**:
  変異 harness の「期待 node が pytest collection に実在しない」診断が、parametrize を持つ関数へ
  bare 名を登録したときに「同名 prefix の collected node がある」ことを示さない。本 wave の前 job は
  この診断だけを手掛かりに 1 日止まった (原因には到達していたが再走前に死亡)。
  近傍 node の提示を足す価値がある。
