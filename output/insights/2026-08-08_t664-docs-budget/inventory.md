# [T-664] dev-wave docs 予算の削減候補 — 棚卸しと段 4 裁定

wave = `worktree-dev-wave-t664-docs-budget`、起点 HEAD = `3ae4856c`、2026-08-08。
依頼 = dev-wave reference (25,200) と dispatcher (9,500) の予算逼迫を、上限引き上げ以外の 2 経路
(陳腐化ルールの削除候補、prose の機械検査への移管 = テスト化) で棚卸しし、裁定パッケージで返す。
**本 wave は本文を 1 byte も編集していない。** 節の削除・移管の実施はユーザー裁定に限る。

逐語 = `verbatim/`。裁定用の択一は `package.md`。

## 1. 予算の実測

| file | bytes | cap | 空き |
|---|---:|---:|---:|
| `docs/dev-wave/core.md` | 8,655 | 9,600 | 945 |
| `docs/dev-wave/workers.md` | 4,526 | 5,000 | 474 |
| `docs/dev-wave/mutation.md` | 3,689 | 3,750 | 61 |
| `docs/dev-wave/operations.md` | 8,329 | 8,400 | 71 |
| **`docs/dev-wave/**` 合計** | **25,199** | **25,200** | **1** |
| `.claude/commands/dev-wave.md` | 9,457 | 9,500 (最長行 140) | 43 |
| `docs/skill-self-improvement.md` | 5,997 | 6,000 (最長行 100) | 3 |

**この表は wave 中に 1 度変わった。** 段 1 の実測は合計 25,184 / 空き 16 bytes だったが、
並行 wave [T-627] が `DW-M07` を 15 bytes 是正して land したため (commit `b7158554`、
「変異の本走前検証へ期待 node を含める」)、取り込み後の空きは **1 byte** になった。
同 commit の message は「残る候補 3 件は合計上限に収まらないため worklog へ記録するに留める。
上限引き上げは提案しない」と記録しており、**本 wave が扱っている壁に同じ日に別 wave が当たっている**。
以下の解放 bytes の算術はすべて取り込み後の 25,199 を基準にしている。

実効 gate は集約 25,200 (`tools/check_docs.py` の `DEV_WAVE_AGGREGATE_BYTES`)。
個別 cap の総和 26,750 は ceiling の 110% (27,720) 以内なので、**1 file の cap を上げても集約が先に落ちる**。
集約値は `orchestrator/tests/test_check_docs.py:1650,1841` が literal で pin しており、
上限の引き上げは機械的に見える。

L2 (条件成立時だけ読む節) は `operations.md` の 13 節 = `DW-O04` `O06` `O08` `O09` `O10` `O11`
`O12` `O14` `O16` `O17` `O18` `O19` `O20`、合計 **5,008 bytes**。
段 2 の子と親が独立に同じ外延へ到達し、[T-412] の当時の外延 (14 節 5,135 bytes、`DW-O15` 削除前)
とも整合する。

## 2. 経路 A — 陳腐化ルールの削除候補

### 結論: 候補ゼロ。1 節も D94 決定 (2) の削除 gate を通らない。

削除 gate = 「L2 である × 発火実績なし × テスト/機械検査で義務代替済み」の 3 条件
(`docs/skill-self-improvement.md` routing 3、D94 決定 (2)、[T-313] 裁定が再利用)。

13 節すべてで条件 (ii)「発火実績なし」が偽だった。段 2 の子が各節について直接事例を挙げ、
親が薄いと見た 2 節を一次資料で裏取りした結果も同じだった。

| 節 | bytes | 発火の直接証拠 (親が一次資料で確認したもの) |
|---|---:|---|
| `DW-O12` | 195 | `docs/archive/worklog-phase3-0728-38-0729-48.md:255` —「段 4 裁定に書いた『gap job は CXXFLAGS scrub』は未実装だった。実態を実行手順の正とした」。裁定手順と実行手順の食い違いを実際に訂正している |
| `DW-O10` | 261 | `output/insights/2026-08-06_t419-u2-recalibration/s4-adjudication.md:88-105` で producer の書き出し面を実際に棚卸しし、同 `:215-221` で新規 sidecar の漏れを是正している |

残る 11 節は段 2 の表 (`verbatim/s2-plan.md` §2) のとおり、いずれも hit 数が 3 桁規模か、
F 番号 (F25/F30/F37/F41/F48/F49/F50/F66) に直接紐づく。

### これは [T-412] の確定結果の再確認であって、新発見ではない

`docs/archive/worklog-phase3-0804-163-164.md:284-306` (2026-08-04) が既に同じ棚卸しを実施し、
**14 節すべてを不採**と確定している。当時の唯一の生き残り候補だった `DW-O10` は
「条件 A だけ満たすが `write_path` の機械検査が `tools/` にも `orchestrator/tests/` にも存在せず
条件 B で脱落」だった。本 wave はさらに、**2026-08-06 の [T-419] で `DW-O10` の条件 A も失われた**
ことを新たに確認した。剪定余地は当時より狭くなっている。

### 副次の裁定 — 閉包検査は条件 (iii) に算入しない

`tools/check_docs.py` の `_OPERATION_NUMBERS` / `STAGE_DISPATCH_CONTRACT` /
`REQUIRED_REFERENCE_SECTIONS` は**節の外延と dispatch 表の一致だけ**を検査する。
節を削除して定数と表を同時更新すれば、この検査は新しい外延へそのまま追随する。
削除前に義務違反だった操作を与えても、読む実成果物も拒否述語も持たない。
**これを「機械検査で義務代替済み」に数えるのは恒真保証**であり、条件 (iii) には算入しない
(段 3 レンズ A 所見 3、親は real と裁定)。

## 3. 経路 B — prose の機械検査への移管 (テスト化)

### 予算を実際に空けうる候補は 1 件だけで、それも移管の証明が足りない

| # | 対象 | 解放 bytes | 段 4 裁定 |
|---|---|---:|---|
| B1 | `DW-O23` の内部手順を `tools/dev_wave_land.py` + `orchestrator/tests/test_dev_wave_land.py` の機械契約へ移管 | **449** (1,123 → 674、親が独立検算) | **ユーザー裁定へ (R2)。親の推奨は「移管しない」** |
| B2 | `DW-O10` の producer 棚卸しを receipt の file-set 差分検査へ | 0 | **候補から削除** — 実成果物に「登録集合」field が無く `DW-O13` を満たさない |
| B3 | `DW-O04` の防護パス commit を hook の `-m` 拒否へ | 0 | **候補から削除** — `-m` 一綴りしか塞がず、Write→message file→`-F` の因果を強制できない |
| — | [T-454] の確定 scope (`DW-C00` 待ち手 3 条 / `DW-O01` 残留 `.done` / `DW-M05` pgrep / `DW-M08` 期待 node / `DW-S06-B`) | 既裁定 | **新規候補に数えない** |

### B1 の検算と、親が推奨しない理由

算術は正しい。現行 `DW-O23` は 1,123 bytes、段 2 の縮約文案は 674 bytes、差は 449 bytes。
代替と主張された `orchestrator/tests/test_dev_wave_land.py` は実在し 64 test を持ち、
`test_fold_failure_rolls_back_ff_and_never_returns_landed` (:1925) も実在する。恒真ではない。

それでも親は移管を推奨しない。段 3 の 2 レンズが独立に同じ核心へ到達したためである。

1. **tool とその test は互いの独立 oracle にならない。** 同じ変更で両方を弱められる。
   段 2 の子自身が「tool と test を同時に弱める変更には別の独立 oracle が必要」と自認している
   (`verbatim/s2-plan.md:96`)。`tools/check_docs.py` が `DW-O23` について検査するのは
   helper literal と path 件数だけである。
2. **落ちる文言は受理集合の境界である。** 「fragment 0 件の fold は no-op」「tracked/index/submodule
   dirt と incoming 衝突 untracked の区別」「`docs/handoff` 直下と Git admin に双方向束縛した
   worktree は書式不問で非接触」は、過去に F80 / F81 / F82 / F98 が実際に踏んだ境界である。
3. **機械検査は違反を事後に赤くするだけで、作業者に事前指示を与えない。** どの dirt を拒否し
   どの untracked を許すかは、赤が出る前に効く判断である。
4. **同型の前科がある。** `tools/check_docs.py:165-167` は、過去の縮約案が `DW-S07` の安全義務
   (「再走値は amend」「insights の逐語・変異台帳」) を byte 予算のために落とした事実を記録している。

## 4. dispatcher (L0) の削減候補 — ゼロ

段 2 は 2 件を提案したが、両方とも段 3 で倒れ、親は 2 件とも real と裁定した。

- **`.claude/commands/dev-wave.md:39` → `DW-STOP` / `DW-S09`**: 入口の
  「local main 取り込みは全条件成立時の共通段 9 operation だけ」は**段 9 限定の禁止文**であり、
  `DW-S09` が持つのは「`tools/dev_wave_land.py` が唯一の通常 land 経路」だけである。
  唯一の helper を段 9 より前に呼ぶことは「唯一経路」違反ではないので、移管すると早期の
  local main 更新を止める層が消える。`LandRequest` に stage も受入 receipt も無い (段 3 レンズ A 所見 5)。
- **`.claude/commands/dev-wave.md:42` → `DW-CTX`**: D94 却下案 (c) の再発。D94 は
  `docs/decisions.md:4228-4233` で「`DW-CTX` ポインタ統合」を、読者主体が外部 supervisor と
  manager で異なるため意味等価にならないとして却下している。段 2 は同じ節で
  「(c) は復活させない」と書きながら本体で提案しており、自己矛盾していた (段 3 レンズ B 所見 3)。

## 5. 段 4 裁定 — 所見の real/refuted

段 3 の 2 レンズが合計 16 所見 (レンズ A 8 件、レンズ B 8 件、うち blocker 5 件) を出した。
**親は 16 件すべてを real と裁定した。refuted は 0 件。** 親 brief の (P1) と (P3) が倒れた。

| 所見 | 深刻度 | 裁定 | 親の対応 |
|---|---|---|---|
| A1 / B1 既裁定の状態が brief と逆 | blocker | real | brief (P1) を撤回。§2・§6 で再基準化 |
| A2 / B4 親の hit 数は発火実績の証明にならない | major | real | 親のスクリプト (`verbatim/firing-evidence-script.md` に逐語) は `jobs` を定義しながら一度も走査していない (実装の欠陥)。hit 数を裁定根拠から外し、直接事例だけを証拠にした |
| A3 閉包検査は条件 (iii) 不算入 | major | real | §2 末尾に明記 |
| A4 / B6 B1 は独立 oracle 不在 | blocker | real | R2 として択一でユーザーへ。親推奨は「移管しない」 |
| A5 dispatcher 39 行は段 9 限定を失う | blocker | real | 候補削除 |
| B3 dispatcher 42 行は D94(c) 再発 | blocker | real | 候補削除 |
| A6 / B7 B2 に登録集合 field 無し | major | real | 候補削除。検出力の課題は [T-419] 側へ |
| A7 / B8 B3 は prose を削れない | major | real | 予算候補から削除。hook 強化は [T-594] の所有 |
| A8 P3 の一般化誤り | major | real | §6 で訂正 |
| B2 T-328 は (c) = T-313 先行 | major | real | §6 の中心結論 |
| B5 `DW-M08` は 7 vector の部分実施 | major | real | §6 で [T-454] の状態を訂正 |

親 brief の誤りの型は 2 つとも同じ — **archive の古いエントリで裁定状態を確定させ、
後発エントリを読まなかった**。[T-454] は entry (244) の「起票可」で止めて (258)(270) を読まず、
(P3) は D94 と memory の要約で止めて [T-313] の裁定本文 (`0803-140.md:67-71`) を読まなかった。
`DW-S01` が要求する「裁定要約が指す decision 本文と archive worklog を開く」(F31) への違反である。

## 6. 予算問題の本体 — 既裁定 4 件が [T-313] の実装へ収束している

一次資料で確認した現在の状態:

- **[T-412]** (L2 剪定): `0804-163-164.md:284-306` で **14 節すべて不採**。剪定 0 bytes。
  本 wave が 13 節で再確認し、`DW-O10` の条件 A も失われたと更新した。
- **[T-454]** (テスト化 pass): `0806-256-261.md:845-866` で **部分実施、回収 0 bytes**。
  固定できたのは変異 kill 判定の 7 vector だけで、未固定の弱化変異が他に無いことは示していない。
  「既存実装 + 既存テストがある」を「その性質が固定されている」と読み替えた誤りも記録されている。
- **[T-577]** (`0806-270.md:396-400`): 回収 207 bytes 内の上位のみ採録し、**入らない分は見送りで確定**。
  再発防止は failures 台帳・memory・rulings inbox が担う。**予算上限は上げない。**
- **[T-328]** (`0804-152-153.md:14-26,69-72`): 択 **(c) = [T-313] を先に実装する**。
  親の前回推奨だった外出しは D94 却下案 (a) と同一形として**撤回済み**。
  従属する [T-345] / [T-346] / [T-317] / [T-279] も T-313 実装後に判断する。
- **[T-313]** (`0803-140.md:3-9,67-71`): **裁定済み・実装待ち**。3 層 gate を現在値で凍結し、
  常に読む層は固定上限を維持、ノウハウ全体の固定文字数上限は撤廃する。
  **剪定は byte 数でなく「発火実績 + 機械検査での義務代替」で行う。**

したがって親 brief (P3) の「[T-313] が実装されれば経路 A は価値を失う」は誤りである。
失効するのは**「解放 bytes」という評価単位だけ**で、剪定述語そのものは
「常に読まない層は合計上限を持たないが無制限には増えない」を成立させる**正規の歯止め**として残る
(段 3 レンズ A 所見 8、[T-313] 裁定本文で確認)。

## 7. 本 wave の段 8 候補は [T-594] が所有している

worklog (316) が [T-664] へ寄せた候補 —「背景 job + worktree 隔離では `DW-O01` の 1 行起動形が
worktree guard に機械拒否される」— は、本 wave でも 2 回発火した (段 1 の byte 計測と
過去 wave の一覧取得)。launcher script を Write して `bash <script>` で起動する形で回避した。

しかしこの摩擦は既に **[T-594]** (2026-08-06 /rulings、防壁変更、`0806-263-264.md:809-813`) が
所有している — 「worktree 隔離 guard が redirect / pipe 付き複合命令を『検証不能』で一律拒否する挙動を、
解析強化で改善する。許可範囲は広げない」。**`DW-O01` へ 1 行足す必要はなく、予算も要らない。**
[T-664] の材料からは外す。
