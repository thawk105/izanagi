# 段 4 裁定 — [T-2288] A-3 / A-4 / C 群 + [T-2465] (親、2026-09-17 01:10 機体時計)

段 2 plan、段 3 レンズ A (授権・正しさ境界)、レンズ B (実物照合・閉包) の所見を real / refuted / scope 外に裁定し、
plan v2 を確定する。裁定 inbox の再走査: local main は `20a92f6a6` → `1042a1bc9` (T-2630 の 1 wave) へ進み、
本件の D・T (T-2288 / T-2465 は carry のまま) に変更なし。T-2697 (binary 配置規則) は entry 1555 で完了済み。

## 所見の裁定

| # | 出所 | 所見 | 裁定 | 扱い |
|---|---|---|---|---|
| 1 | A | `reps=5` は「calibrator の出力を採り承認する」(D1641 決定 3) の射程外。出力に無い値の新規決定 | **real** | 採用 (記録の形を変える)。値は承認するが「calibrator 出力から導いたものではない AI の選択」と D と insight に明記し、裁定パッケージにも載せる。根拠: 本 wave の依頼文が `reps` を名指しで承認対象にしており、値は事前登録 §11.2 が 2026-09-02 から名目として置く 5 で、spec 凍結前は D 追記で改められる (可逆)。規律 2・3 の射程外 (床値結果は 1 件も無い) |
| 2 | A | 3 cell は既裁定の転記ではなく対象集合を決める新しい選択 | **real** | 採用 (記録の形を変える)。D に「§5 に具体列は無く、本決定が D1641 決定 3 の委任と本 wave の依頼 (具体列を起こす) の下で具体化した」と書く。「利用可能な較正で構成できる集合」と「研究対象として十分か」を分け、後者は主張しない |
| 3 | A/B | C 群の「結果を見る前に」— 較正値は既知 | **real** (時系列の事実) | 採用。D に次を書く: (i) 床値結果は 1 件も存在せず、規則は床値結果より前に固定される、(ii) 較正記録の測定値は 2026-07 以降 repo で公開済みで、本 wave も閲覧した、(iii) 規則の判別条件のうち実際に候補を落とすのは D1537 (2026-09-03 裁定) の既裁定 identity だけで、本 wave が新しく作った条件は 1 件も候補を落としていない。D2044 項 11 の「結果」は床値結果と読み、較正値の既知性は隠さず記録する |
| 4 | A | c5 の method 一致は規律 7 (現行との差だけを拒否理由にしない) に抵触 | **real** | 採用。c5 を「自分の attestation 述語 (effective-clock) を通らないと記録・裁定された記録を除く」(挙動基準、現物は D1537 の g1 1 件) に改め、method 文字列の一致を拒否条件にしない。全適格記録が現行 method であることは事実として記すだけ |
| 5 | A/B | 同 epoch の SHA 昇順は測定値を含む内容に依存する | **real** | 採用。同 epoch は `acquisition_receipt.qsub` の `(project, queue, request_id)` 辞書順。同一取得 identity に異なる内容があれば読み飛ばさず停止 |
| 6 | B | genome 不在の silo 判定は 2 件の完全 SHA に閉じる (D1538)。将来の `--binary` fallback を一般化しない | **real** | 採用。判定式 (`acquisition_receipt.allocation.pbs_jobid` → job-staging の `calibrate-argv.json` の `--binary` と `--binary-sha256`) を D に書き、適用は 2 SHA に限定 |
| 7 | B | c1 の registered 限定は新しい人手規則 (binder の要求ではない) | **real** | 採用。そう明記する |
| 8 | B | 「現行 policy の method」の正本は無い (verifier は tolerance のみ、method は env_attestation 定数) | **real** | 採用 (#4 で条件から外す) |
| 9 | B | accepted は registered 外にも存在 (mocc 2 件・複製)。silo の追加取得は無し | **real** | 採用。閉包表に書く。「accepted 全体が 8 件」とは書かない |
| 10 | B | D1538 の consumer 側限定は未実装 | **real、scope 外** | insight に記録するだけ。実装は本 wave の scope 外 (gate 追加禁止) |
| 11 | B | `"0"` を `"false"` へ置換すると束縛が壊れる | **real** | 採用。D の cell 表に逐語で書く |
| 12 | B | binder 全体 (binary / build receipt) の成功は未証明 | **real** | 採用。「較正側の照合が通る」までしか主張しない |
| 13 | A/B | `reps` は「分散だけ」でなく実行量・時間的標本化・中央値の分布にも効く。sweep 3 は各点の反復数 | **real** | 採用。「bench 1 回の flags を変えない量」と限定し、「calibrator は床値測定に採る reps を一意に指定しない」と書く |
| 14 | B | 「runner は max_ope を渡さない」は一般論として誤り (workload key なら渡せる) | **real** | 採用。「今回の較正 argv には無い」に限定 |
| 15 | A/B | §11.3 のアンカーは第 2 bullet (:1297) | **real** | 採用 |
| 16 | A | 「残前提は A-5 のみ」は成立しない | **一部 real** | 「本 wave が扱った較正非依存の前提 A-3 / A-4 / C は閉じた」に限定し、spec 凍結までに残る作業 (A-5 の裁定、binary の `place` 実行、spec の作成・validate・commit、床値実測、集約、採用裁定、§5 記入) を列挙する |
| 17 | A | 「較正と独立な A-3・A-4・C」は誤記 | **real** | 「較正の再取得なしに閉じられる」に改める |
| 18 | A | §11.1 は候補起草を禁じていない (無裁定の凍結投入を禁じる) | **refuted (親の過大解釈)** | A-5 は「本 wave の依頼が値を書かないと指示した」と説明する |
| 19 | A | T-2465 の 4 点に新規授権が要る | **refuted** | plan の追記案どおり進める。「確定したのは担当と採用手続きであり個別成果物の受理ではない」を 1 文足す |
| 20 | A | plan が機械保証を偽装している | **refuted** | ただし D に「admission 成功は protocol・測定設定・対象集合の意味的一致や選択規則の事前性を保証しない」を残す |
| 21 | B | 焦点走 4 node は fixture 読みで実文書の無影響を直接証明しない | **real** | file 単位 5 本 (実文書を読む test を含む、baseline 255 緑) を走らせ、§5 表の bytes 不変を diff で示す |

## plan v2 (確定)

1. decisions fragment (seq 1、D 3 件): `b4-floor-perf-config-approval` / `b4-floor-cell-set` / `calibration-record-selection-rule`。
   上の #1〜#14 を反映した本文。§11.2 へ値を再掲しない。
2. 事前登録: §11.1 の D1812 (c) 段落末 (「ユーザー裁定へ返してある。」直後) へ追記 1 文、§11.3 第 2 bullet の
   「追記 (2026-09-07)」段落末 (「ユーザー手番である。」直後) へ追記 1 段落。既存文は書き換えない。
3. worklog fragment (seq 2): T-2288 `更新` (残作業の列挙、#16)、T-2465 `完了`。base digest は land 直前に main で再取得。
4. insight README + verbatim (brief・plan・consult 2 本・本裁定・probe・review)。
5. 受入: `check_docs.py`、`spool_fold.py --dry-run --show-diff`、焦点走 5 file、`git diff` で §5 表の bytes 不変、受入全走。
   変異 matrix は実装面差分 0 で免除 (DW-S04)。
6. 裁定パッケージ (insight に置く): A-5 の必要事項 (値なし)、`reps=5` の AI 選択、3 cell の具体化、C 群規則の事前性の記録形、
   D1538 consumer 限定の未実装。

## やらない理由の最も強い形 (記録)

- `reps=5` を承認しない側: D1641 決定 3 の逐語は「出力を採る」であり、出力に無い値の決定は委任の外 (レンズ A)。
  → それでも承認する理由: 依頼文が名指しで承認を求め、値は事前登録自身の名目で、凍結前なら D 追記で戻せる。
- 3 cell を決めない側: 対象集合の網羅性を AI が決めることになる。→ 依頼文が具体列を起こすことを求め、較正が無い cell は
  束縛できず、追加較正は認可外。集合の十分性は主張しない。
- C 群を「事前規則」と記録しない側: 較正値を見た後に書いた規則である。→ 判別条件は既裁定 (D1537) だけで、
  本 wave 由来の条件は候補を 1 件も落としていない。床値結果は存在しない。時系列を隠さず書く。
