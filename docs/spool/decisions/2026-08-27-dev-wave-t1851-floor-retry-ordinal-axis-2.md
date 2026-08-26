---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-27
wave: dev-wave-t1851-floor-retry-ordinal-axis
seq: 2
---

## {{D:floor-registry-namespace-fork}}. 床値 attempt registry の名前空間は、現用 2 世代を収容できないまま配線できない

**決定 (親裁定 = ユーザー裁定待ちとして返す):** 床値 campaign を attempt registry へ配線する
工程を、名前空間の択一が返るまで止める。親は択一を選ばない。

**実測:**

- 台帳の path は freeze SHA だけで決まる
  (`orchestrator/campaign/s8b_attempt_profile.py` の `S8B_REGISTRY_LAYOUT.registry_path`
  = `floor-attempt-registries/{freeze_sha256}/registry.jsonl`)。
- genesis の binding は freeze / protocol / schedule の 3 SHA を持ち、台帳の全行は 1 つの
  binding を共有しなければならない (`attempt rows do not share one binding`)。
- 現用の床値 protocol は 2 つあり、**どちらも freeze `315b1eb8` を共有する**。
  `output/s8b-freeze/floor_protocol.json` (ccbench_pin `d706650c`) と
  `output/s8b-freeze/floor-protocols/e576e9cd...--511c9538....json` (同 `511c9538`)。
  campaign は legacy anchor と版付き namespace の両方を `(contract_sha256, ccbench_pin)` で
  索引し、どちらも選択できる。
- D444 はこの namespace を「組ごとに 1 件・追加のみ」と定めるため、世代は構造的に増え続ける。

**何が起きるか:** 未配線の現状では衝突しない。配線すると、先に走った世代が genesis を作り、
後の世代の campaign は同じ path の genesis と binding が食い違って拒否される。測り直しが
止まるのではなく campaign 全体が止まる。D1007 が「配線まで押し通す — 最初の測り直しで
campaign が止まる実装を land することになる」として却下した形と同型で、射程がより広い。

**なぜ親が決めないか:** 回避策がいずれも正しさ防壁の意味を変えるため。

- **(i) 台帳を protocol 世代ごとに分ける。** `_s8b_budget_key()` は
  `(freeze_holdout_key, configuration_id)` で「repetition と attempt に依らず cell 予算を集約する」
  と定義され、slot は `campaign_run_id` を意図的に持たない。すなわち測り直し予算は freeze 単位で
  campaign run を跨いで共有される。これは「protocol を版上げして同じ cell を測り直し、
  良い床値を採る」経路を塞ぐ防壁である。世代ごとに分けると、この防壁が世代ごとにリセットされる。
  絶対規律 2 の面を緩める変更であり、親の裁量を超える。
- **(ii) freeze 単位のまま据え置き、後続世代を fail-closed で拒否する。** 防壁は保たれるが、
  新しい ccbench pin で床値 campaign を走らせられなくなる。運用上の後退である。
- **(iii) 予算だけ freeze 単位に残し、台帳を世代ごとに分ける複合形。** 両方の性質を保てる
  可能性があるが、予算を台帳の外へ出すことになり、その置き場所自体が新しい設計判断になる。

**親の推奨は (iii)。** 防壁の意味を変えずに世代を収容できる唯一の形だから。

**却下した選択肢:**

- 親が (i) を選んで進める — 予算防壁を世代ごとにリセットする変更を、裁定なしに入れることになる。
- 配線せず軸だけ land する — {{D:no-partial-land-for-dead-gate}} を参照。

## {{D:floor-registry-proof-chain-binding}}. certified 検証は attempt registry を読んでおらず、束縛の可否は裁定が要る

**決定 (親裁定 = ユーザー裁定待ちとして返す):** attempt registry を certified 成果物の proof chain
へ束縛するかどうかを裁定へ返す。親は選ばない。

**実測:**

- `verify_floor_artifact` 自身が attempt registry と schedule の突合を保証外と明記している。
- live wrapper は holdout admission 台帳を検査するだけで台帳を読まない。
- ratified verifier も result / journal / live admission だけを渡す。
- legacy trigger の認可は台帳行が無くても通り、最終 inspector も同じ関数を使う。

**何が起きるか:** 新しい試行番号軸を台帳へ書く経路を作っても、**台帳を削除・不正化した状態で
certified 検証が通る**。測り直しの試行を台帳へ書く production 経路は増えるが、certified 選択が
その台帳を根拠にする保証は増えない。D1032 が解こうとした「結果を見た後の選び直しが追跡不能」は、
書き手だけでは閉じない。

**なぜ親が決めないか:** 束縛には chain head・start event hash・台帳 identity のいずれかを
成果物へ pin する必要があり、凍結成果物と historical reverify の受理面を変える。
既に certified 済みの成果物を遡って再検査対象にするかどうかも含めて受理集合の変更であり、
親の裁量を超える。

**択一:**

- **(a) 台帳の chain head を result へ pin し、historical reverify も対象にする。**
- **(b) 新しい成果物だけに前向きに掛け、既存 certified 成果物の受理面は変えない。**
- **(c) 束縛しない。** この場合 T-1851 の成果物影響は達成されないことを明記して閉じる。

**親の推奨は (b)。** 既存の certified 選択を遡って無効化せずに、以後の測り直しを追跡可能にできるから。

**却下した選択肢:**

- 書き手だけ land して束縛を後続へ送る — proof chain が台帳の欠落を許したまま「測り直しを
  追跡している」と読める状態を作る。謳うだけで発火しない保証にあたる。

## {{D:floor-remeasurement-reason-scope}}. D1032 の「外部 scheduler 証拠に限る」は既存 retryable 集合に掛かり、新軸の理由は sealed 証拠から強制導出する

**決定 (親裁定。ユーザーが覆せるよう裁定パッケージにも併記する):** D1032 の
「受理する理由の集合を広げる場合も外部 scheduler の証拠が付いた場合に限る」は、
既存の `S8B_RETRYABLE_FAILURE_REASONS` (`attempt_ordinal` 軸の retryable 集合) に掛かる制約と読む。
新設する測り直し軸が統計的無効を理由として受理することは、これに当たらない。

ただし次を必須条件とする。**新軸の理由は呼び手が選べてはならない。** 信頼境界の内側で、
既に封じられた trigger session の canonical bytes から機械的に導出する。引数で受け取る形は採らない。

さらに、新軸は凍結 4 語 (`competing_process` / `launch_failure` /
`nonfinite_or_partial_output` / `performance_anomaly`) を再利用せず、**台帳専用の閉じた語彙**を持つ。
各値は封じられた session record から機械的に導出する。

**理由:**

- D1032 が却下したのは「再試行可能な理由の集合を**無条件に**広げる」ことである。D1032 が
  肯定した内容 (事前登録された別軸 + 性能量到達前の理由固定) こそが、その「条件」に当たる。
- 逆に読むと D1032 は元の問題を何も解かない。D1007 は阻害要因を
  「`S8B_RETRYABLE_FAILURE_REASONS` が空で `attempt_ordinal > 0` が terminal 経路から永久に
  開かない。解消するには受理集合を広げるしかなく、親が決めてよい範囲を超える」と書いており、
  D1032 はその人間裁定である。裁定文が自分の目的を否定する読みは採らない。
- 理由が封じられた証拠から強制導出されるなら、そもそも「受理する理由の集合を広げる」に
  当たらない。自由選択が存在しないからである。逆に呼び手が選べる形なら、どちらの読みでも
  D1032 違反になる。
- 凍結 4 語は D444 で「session を除外する理由」として人間承認され、`allowed_excluded_reasons` は
  AI が改訂できない 16 field の 1 つである。同じ語を「次の測り直し番号を開く権限」として
  再利用すると、bytes を変えずに field の権限の意味を増やすことになる。台帳専用語彙にすれば
  この問題を回避できる。

**却下した選択肢:**

- 新軸も外部 scheduler 証拠に限る — recovery authority 集合が空のため production 発火が 0 になり、
  D1032 が解こうとした問題が残る。
- 凍結 4 語をそのまま新軸の権限語彙として再利用する — D444 の人間手番に触れる。

## {{D:no-partial-land-for-dead-gate}}. 発火する path を名指しできない gate は、部分実装でも land しない

**決定:** 新しい gate や条件付き機構を作る wave で、(a) 発火条件を満たす既存 artifact path も
計測 ID も名指しできず、(b) 独立した敵対検査が「先行 land すると production 呼び手 0 件の
死んだ gate になる」と判定した場合、部分実装を land しない。設計を凍結して裁定へ返す。

**理由:**

- DW-G04 は「条件付き機能は発火条件を満たす既存 artifact path か計測 ID を書ける場合だけ
  実装する。書けなければ設計メモに留める」と定める。
- 書き手だけ land すると、検査側が台帳の欠落を許したまま「追跡している」と読める状態になる。
  検査だけ land すると既存 campaign が止まる。どちらも成果物の意味を偽る。
- 機構の形そのもの (理由の語彙、証拠の束縛、台帳の同一性) が未裁定の択一に依存する場合、
  先に形を決めて land すると裁定の答え次第で作り直しになる。

**D1007 との違い:** D1007 は起動器を未配線のまま land した。あれは起動器と収集器が
1 つの完成した単位で、破棄すると同じ設計をやり直すことになるという理由だった。
単体で完成していない部分を先行 land する根拠にはならない。

**却下した選択肢:**

- 軸だけ先に land し配線を後続へ送る — 上記 (b) に該当する。
- 何も記録せず止める — 段 3 の所見と実測が失われ、次 wave が同じ調査をやり直すことになる。
