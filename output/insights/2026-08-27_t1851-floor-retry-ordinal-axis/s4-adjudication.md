# 段 4 裁定 — T-1851 (dev-wave-t1851-floor-retry-ordinal-axis)

日時: 2026-08-27 01:07 JST / base: 0d3d80e1 (裁定時点。main はその後 9ebd340b まで進行)

## 結論

**本 wave では実装しない (4→7→8→9)。** 裁定 D1032 は有効であり、方向 (耐久台帳の中の別 ordinal 軸 +
性能量到達前の理由固定) を疑わない。しかし D1032 の裁定時には見えていなかった事実が段 2・3 で
2 件出た。どちらも**この機構を production で発火させる工程を塞いでおり、親が決めてよい範囲を
超える設計択一を含む**。DW-STOP の「承認済み裁定の前提を覆す未見の新事実」に当たるため、
実装せず裁定パッケージとして返す。

軸だけを配線せずに land する案も検討したが採らない。理由は下記「なぜ部分実装もしないか」。

---

## 覆した新事実 1 — 台帳の名前空間が、現用の 2 つの protocol 世代を収容できない

### 実測 (親が一次資料で裏取り済み)

- 台帳の path は **freeze SHA だけ**で決まる。
  `s8b_attempt_profile.py:378-385` の `registry_path = "floor-attempt-registries/{freeze_sha256}/registry.jsonl"`。
- 一方 genesis の binding は **protocol SHA を含む** (`S8BAttemptBinding` = freeze/protocol/schedule、
  `s8b_attempt_profile.py:41-47`)。台帳の全行は 1 つの binding を共有しなければならない
  (`binding_conflict_message = "attempt rows do not share one binding"`)。
- **現用の床値 protocol は 2 つあり、同じ freeze SHA を共有している。**
  - `output/s8b-freeze/floor_protocol.json` — freeze `315b1eb8...`、ccbench_pin `d706650c...`
  - `output/s8b-freeze/floor-protocols/e576e9cd...--511c9538....json` — freeze `315b1eb8...`、
    ccbench_pin `511c9538...`
  - campaign は legacy anchor と版付き namespace の**両方**を `(contract_sha256, ccbench_pin)` で
    索引し、どちらも選択できる (`s8b_floor_campaign.py:895-945`)。
- D444 はこの namespace を「組ごとに 1 件・追加のみ」と定めている。よって世代は**構造的に
  増え続ける**。今回の衝突は偶発ではない。

### 何が起きるか

現状 (未配線) では衝突しない。台帳を production へ配線した瞬間に、先に走った世代が genesis を
作り、**後の世代の campaign は同じ path の genesis と binding が食い違って拒否される**。
測り直しが止まるのではなく campaign 全体が止まる。これは D1007 が
「配線まで押し通す — 最初の測り直しで campaign が止まる実装を land することになる」として
却下した形と同型で、しかもより広い。

### なぜ親が決められないか

回避策は 2 つあり、どちらも正しさ防壁の意味を変える。

- **(i) 台帳を protocol 世代ごとに分ける** (path に protocol SHA を含める)。
  予算 key は `_s8b_budget_key()` = `(freeze_holdout_key, configuration_id)` で、docstring は
  「repetition と attempt に依らず cell 予算を集約する」、slot の docstring は
  「freeze-wide な slot、`campaign_run_id` は意図的に持たない」と明記している
  (`s8b_attempt_profile.py:34-40, 404-408`)。すなわち**測り直し予算は freeze 単位で
  campaign run を跨いで共有される**。これは「protocol を版上げして同じ cell を測り直し、
  良い床値を採る」経路を塞ぐ防壁である。世代ごとに台帳を分けると、この防壁が世代ごとに
  リセットされる。**絶対規律 2 の面を緩める変更**であり、親の裁量ではない。
- **(ii) 台帳を freeze 単位のまま据え置き、後の世代を fail-closed で拒否する。**
  防壁は保たれるが、新しい ccbench pin で床値 campaign を走らせられなくなる。
  運用上の後退であり、これも親が黙って決めてよい範囲を超える。

**返す択一:** (i) 世代ごとの台帳 (予算防壁が世代ごとにリセットされることを受け入れる) /
(ii) freeze 単位据え置き + 後続世代の拒否 / (iii) 予算だけ freeze 単位に残し台帳を世代ごとに
分ける複合形 (実装量は増えるが両方の性質を保てる可能性がある)。
**親の推奨は (iii)。** 防壁の意味を変えずに世代を収容できる唯一の形だから。ただし予算を
台帳の外へ出すことになるため、その置き場所自体が新しい設計判断になる。

---

## 覆した新事実 2 — certified 検証は台帳を一切読んでいない

### 実測 (段 3 の両レンズが独立に指摘、親が anchor を確認)

- `verify_floor_artifact` 自身が attempt registry と schedule の突合を保証外と明記
  (`s8b_floor_stats.py:412-416, 682-695`)。
- live wrapper は holdout admission 台帳を検査するだけで台帳を読まない
  (`s8b_floor_stats.py:1036-1082`)。
- ratified verifier も result / journal / live admission だけを渡す
  (`s8b_ratified_freeze.py:3209-3242`)。
- legacy trigger の認可は台帳行が無くても通る
  (`s8b_holdout_admission.py:4217-4223, 4586-4621`)。最終 inspector も同じ関数を使う (`:5306-5317`)。

### 何が起きるか

新しい軸を台帳へ書く経路を作っても、**台帳を削除・不正化しても certified 検証は通る**。
brief が掲げた成果物影響 (「certified 選択が根拠にする試行台帳から測り直しが欠落する」) は
解消しない。書き手だけを作ると、proof chain は台帳の欠落を許したままになる。

### なぜ親が決められないか

台帳を proof chain へ束縛するには、chain head・start event hash・台帳 identity のいずれかを
成果物へ pin する必要がある。これは**凍結成果物と historical reverify の受理面を変える**。
既に certified 済みの成果物を遡って再検査対象にするか、新しい成果物だけに掛けるかも含めて、
受理集合の変更であり親の裁量ではない。

**返す択一:** (a) 台帳 chain head を result へ pin し historical reverify も対象にする /
(b) 新しい成果物だけに前向きに掛け、既存 certified 成果物の受理面は変えない /
(c) 束縛しない (この場合 T-1851 の成果物影響は達成されないことを明記して閉じる)。
**親の推奨は (b)。** 既存の certified 選択を遡って無効化せずに、以後の測り直しを追跡可能にできるから。

---

## 所見の裁定 (real / refuted、採用 / 不採用、scope 内 / 外)

実装しない裁定のため、下記の「採用」は**次 wave の plan v2 への拘束**として記録する。

| # | 所見 (出所) | 判定 | 扱い |
|---|---|---|---|
| 1 | terminal 理由の一致検査の例外が広すぎる (A-1 / B-記録3) | **real** | 採用・scope 内。閉集合 membership では不可。throughput 由来の 2 理由 (`nonfinite_or_partial_output` / `performance_anomaly`) に限定し、canonical session bytes から `assess_session()` を再実行して一致を証明する形だけを許す |
| 2 | 理由が呼び手から偽造できる (A-2 / B-consumer2) | **real** | 採用・scope 内。理由は信頼境界の内側で sealed な session bytes から**導出**する。引数で受け取らない。`FloorRetryAuthorization` は公開 dataclass + `isinstance` だけで authority 境界になっていない |
| 3 | journal と台帳の二台帳間に crash 整合がない (A-3) | **real** | 採用・scope 内。prepare/commit 順序、孤児状態表、exact retry を plan v2 の必須項目にする |
| 4 | certified 検証が台帳を要求しない (A-4 / B-記録2) | **real** | **scope 外** — 上記「新事実 2」として裁定へ返す |
| 5 | 台帳 namespace が 2 世代を収容できない (A-scope外2、親が裏取り) | **real** | **scope 外** — 上記「新事実 1」として裁定へ返す |
| 6 | D880 の XOR が authority 点で fail-closed でない + 台帳 parse 失敗時の legacy fallback (A-5) | **real** | 採用・scope 内。ただし fallback は**既存の穴**であり本 wave が作ったものではない。plan v2 で塞ぐ |
| 7 | 恒真化 — 信頼できる producer から来る候補に対して legacy 理由 membership と ordinal membership は常に真 (A-7) | **real** | 採用・scope 内。変異事前登録で「信頼 producer の受理集合を実際に落とす負例」と「改変検出だけの負例」を分けて登録する |
| 8 | schema `/v2` の readable 集合と repo 外 live v1 台帳 (B-記録4) | **real** | 採用・scope 内。repo に成果物 0 件という実測は共有 admission root に無いことの証拠にならない |
| 9 | `FloorAttemptTerminal` に failure reason の data path が無い (A-整合) | **real** | 採用・scope 内。plan v2 で誰が canonical bytes を検証し誰が理由を渡すかを決める |
| 10 | test 閉包の穴 — 新軸が無くても緑のままのテスト、`test_s8b_freeze_io.py` の漏れ、AST 在庫の stale 化 (B-テスト) | **real** | 採用・scope 内 |
| 11 | D444 の理由語彙の再利用 (A-scope外1) | **real** | 採用・scope 内へ引き戻す。**親裁定: 凍結 4 語を再利用せず、台帳専用の閉じた語彙を持つ。** 各値は sealed な session record から機械的に導出する。これで protocol の field に新しい権限の意味を足さずに済み、D444 の人間手番に触れない。(P4) を撤回する |
| 12 | 実装子 1 本では閉じない (B-整合) | **real** | 採用。plan v2 では縦切り 1 本を複数の実装単位へ分けるか、所有を素集合に切る |
| 13 | 規模見積もり 1,360-2,075 行は下限 (A-整合) | **real** | 採用。上記の必須項目を足すと確実に増える |

### (P1) の裁定

**親の狭い読みを維持する。** レンズ A は「文脈上は親の読みがやや強い」と判定し、レンズ B は
「逐語は広くも読めるので裁定へ戻すべき」とした。親の裁定は次のとおり。

D1032 の「受理する理由の集合を広げる場合も外部 scheduler の証拠が付いた場合に限る」は、
`S8B_RETRYABLE_FAILURE_REASONS` (既存 `attempt_ordinal` 軸の retryable 集合) に掛かる。
根拠は D1032 の却下理由が「再試行可能な理由の集合を**無条件に**広げる」であり、
D1032 が肯定した内容 (事前登録された別軸 + 性能量到達前の理由固定) こそがその「条件」だから。
逆読みを採ると D1032 は T-1851 を何も解かず、D1007 が「解消するには受理集合を広げるしかない」と
書いた不整合が残る。裁定文が自分の目的を否定する読みは採らない。

ただし所見 2・11 の対応を必須とする。**理由が呼び手から選べる形なら、どちらの読みでも
D1032 違反になる。** 理由が sealed 証拠から強制導出されるなら、そもそも「受理する理由の集合を
広げる」に当たらない — 自由選択が存在しないから。この点は次 wave の plan v2 で機械的に示すこと。

この読みは裁定パッケージにも併記し、ユーザーが覆せるようにする。

---

## なぜ部分実装もしないか

D1007 は起動器を未配線のまま land した前例がある。しかし本 wave では採らない。

- **DW-G04**: 条件付き機能は、発火条件を満たす既存 artifact path か計測 ID を brief に書ける
  場合だけ実装する。床値 campaign の run 成果物は repo に 1 件も無く、配線も塞がっているため、
  新軸が発火する path を名指しできない。
- **段 3 の両レンズが独立に「core/profile だけの先行 land は production 呼び手 0 件の
  死んだ gate になり不可」と判定した。** 書き手だけを land すると proof chain は台帳の欠落を
  許したままになり、検査だけを land すると既存 campaign が止まる。
- 新軸の**形そのもの** (理由の語彙、証拠の束縛、台帳 identity) が、上記 2 つの裁定の答えに
  依存する。先に形を決めて land すると、裁定の答え次第で作り直しになる。
- D1007 が未配線 land を許したのは、起動器と収集器が 1 つの完成した単位で、破棄すると
  同じ設計をやり直すことになるからだった。本 wave の軸は単体では完成した単位ではない。

---

## 次 wave への引き継ぎ (裁定が返った後の plan v2 の骨格)

段 3 の両レンズが独立に同じ分割を推した。裁定が返ったらこれを起点にする。

1. **前半 = legacy 統計的測り直しの縦切り 1 本。** schema v2 + readable 方針、sealed な理由 authority、
   terminal 理由の再導出、二台帳の crash 整合、launcher / campaign 配線、final inspector /
   verifier までを同時に land する。planned attempt には既に production 呼び手があるため、
   死んだ gate にならない。
2. **後半 = `verified-registry-recovery` 側を別 wave。** 現状 authority 集合が空
   (`s8b_holdout_admission.py:101-105`) で、収集器も理由を発行できない
   (`s8b_scheduler_accounting.py:59-62`)。前半から外しても到達可能な機能は失われない。

書き手と検査を別々に land する分割は不可 (両レンズ一致)。

## 変異事前登録 (DW-M01)

実装面の差分が 0 のため変異 matrix は免除 (DW-S04)。受入全走は免除しない。
次 wave で登録すべき変異軸だけ記録する。

- 理由を sealed 導出でなく引数受け取りに戻す変異 → 偽造負例が生き残ることを検出できるか。
- terminal 理由の例外を throughput 由来 2 理由から閉集合全体へ広げる変異。
- `retry_slots_per_cell` を profile が無視する変異 → serialized genesis の検査が赤になるか。
- S8B の equality 例外を 8c formal profile へ適用する変異 → `test_trial_registry.py:7111-7158` が赤になるか。
- 台帳 file を削除する変異 → final inspector / ratified verify が赤になるか (新事実 2 の対応後)。
