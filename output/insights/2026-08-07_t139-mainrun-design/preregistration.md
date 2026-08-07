# [T-139] 本走 — 事前登録 core (2026-08-07 凍結、実走前に commit する)

```text
authority: none
default_effect: no-state-change
study_label: rf_partial_recovery / paired_cluster / main_study / core
pilot_admission: requires_schedule_addendum
main_admission: requires_schedule_and_alpha_addenda
```

## 0. 本書の位置づけと凍結の意味

本書は **[T-139] 本走の推論内容を、データを 1 点も見る前に固定する事前登録の core** である。
可変状態の正本は `docs/worklog.md` 末尾と現行 phase doc であり、本書はそれらの正本ではない
(`authority: none` はその意味であって、拘束力がないという意味ではない)。

**凍結の実装は commit / blob 参照束縛である。** 本書の凍結単位は作業木の現在の bytes ではなく、
結果の記録が参照する `<commit>` / `<path>` / blob の SHA-256 の三つ組である。検証側は指定 commit の
tree から本書の path の blob を読み、その digest を記録と照合し、さらにその commit が測定 checkout の
祖先であることを確認する。現在の HEAD や作業木の bytes は、過去の結果の設計を上書きしない。
作業木の bytes を固定する検査 (`FROZEN_MANIFEST` 型) は**置かない** — main の前進を妨げる検査を作らない
というユーザー裁定に従う。本書は自分自身の digest を本文へ書かない (自己参照の禁止)。

**結果を見てから本書を書き換えてはならない** (D126 決定 (4))。書き換えたら別 study である。
未確定として残る量は §14 の**追補 (addendum)** に閉集合で委ねてあり、追補は本書の推論内容を変更できない。

**確定値の根拠。** 裁定**前**の問い・選択肢・推奨理由は同ディレクトリの `package.md`
(`authority: none`、凍結) と `preregistration-draft.md` を参照する。それらは裁定前に書かれた記録であり、
**採択後に書き換えない**ので、本文には今も「未裁定」と書かれている。
**採択結果の正本は `docs/worklog.md` のエントリ (299) / (300) と、本 wave が land する決定**であり、
本書はその結果を指定 commit / path / blob へ射影したものである。

## 1. 問い

代替 X (modeX) は、意図的に取り除いた最適化による劣化を、部分的に回復するか。
**部分回復とは、劣化版より速く、かつ元の版に達していないことをいう。**
元の版を超えた場合は「回復」と呼ばず「stock 超過」とだけ述べ、機序の帰属には別証拠を要求する。

## 2. arm と workload

| arm | 内容 |
|---|---|
| `stock` (S) | 元の版 |
| `mode1` (Dg) | 意図的に最適化を 1 つ外した劣化版 |
| `modeX` (X) | 合成システムが作った回復候補 (4 stripe、`alignas(64)` 分離、固定回数 mixer) |

workload は W1 (高競合 write) と W2 (中競合 mixed) の 2 本。
候補の exact bytes は request `892042` の `run_commit = 425ed190` に束縛する。

## 3. 量の定義 (cluster = 1 割当て、`j` を cluster 添字とする)

`m_{A,wj}` を workload `w`・arm `A`・cluster `j` の代表値とする。
**代表値は cluster 内反復の算術平均とする** (裁定 U7)。

```text
N_wj = m_X,wj  − m_Dg,wj      回復量
D_wj = m_S,wj  − m_Dg,wj      劣化幅
G_wj = m_S,wj  − m_X,wj       元の版までの残り
```

恒等式 `D = N + G` が成り立つ。primary endpoint は trace-disabled の `throughput_tps` 1 本
(裁定済み)。`throughput_tps` は大きいほど速いので、劣化版が遅ければ `D > 0` である。
abort 率等は説明用の副次指標であり、受理条件の family へ入れない。

回復率は `RF_w = E[N_w] / E[D_w]` (総回復率、裁定済み)。

**分母条件は総量型を採る** (裁定 U1 (a))。

```text
H_wj = D_wj − κ_w · S_wj        ただし S_wj = m_S,wj
```

とし、`E[H_w] > 0` を検定する。`E[S_w] > 0` のもとで、これは
`E[D_w] / E[S_w] > κ_w` すなわち「劣化幅が元の版の `κ_w` 倍を超える」と同値である。
`D`・`S`・`H` はいずれも `throughput_tps` の次元を持ち、`κ` は無次元である。

**閾値は `κ_W1 = κ_W2 = 0.20` に固定する** (裁定 U2、2026-08-07)。
これは元の版の throughput に対する**相対的な劣化幅**であり、パーセントポイントではない。
候補の測定結果と無関係にユーザーが定めた値である。
劣化幅が元の版の 20% 未満である workload では「回復」を主張しない。

## 4. 受理条件 (primary)

workload ごとに、cluster level の標本平均・標本共分散から構成した**同時信頼領域** `C_w` について

```text
P_w  :=  inf_{C_w} N_w > 0
     AND inf_{C_w} H_w > 0
     AND inf_{C_w} G_w > 0
```

とし、primary は両 workload の連言 `P_W1 AND P_W2` **1 本**とする
(intersection-union なので多重補正は不要)。**受理条件は 3 つである** — 3 つ目 (`G > 0`) を落とすと、
元の版を追い越した候補まで「回復した」と認証できてしまう。

**区間推定は同じ同時領域の ratio projection として導出する。** 別構成の Fieller を二重に課さない —
同じ標本共分散と同じ臨界値 `q` から作れば、Fieller 集合の `r=0` 検査は `N` の検査、`r=1` 検査は
`−G` の検査であり、「有界な集合が `(0,1)` に含まれる」ことと `N>0 ∧ G>0` は**同値**である。
別構成にすると、正当な手続き差を「データ破損」として拒否する偽陰性経路になる。

**ただし分母条件 `H` はこの同値の外にある。** `RF` の区間が `(0,1)` に収まっても `H ≤ 0` はありうる
(例: `S=100, Dg=90, X=95` なら `N=5, D=10, G=5, RF=0.5` だが `H = 10 − 20 = −10`)。
§5 の状態表はこの領域を独立の状態として持つ。

Fieller 係数は
`A = D̄² − q²s_DD/J`、`B = N̄D̄ − q²s_ND/J`、`C = N̄² − q²s_NN/J` に対し `Ar² − 2Br + C ≤ 0`。

## 5. 状態の閉表 (2 軸)

**軸 1 — 区間の形 `interval_shape` (exact-one):**

| 値 | 条件 |
|---|---|
| `bounded` | `A > 0` |
| `unbounded_connected` | `A ≤ 0` かつ解が連結 |
| `disjoint` | `A < 0` かつ解が非連結 |
| `empty` | 解なし (例: `D_j ≡ 0`, `N_j ≡ 1` のとき `A=B=0, C=1`) |

**軸 2 — 適格性の状態 `qualification_status`。上から順に最初に一致した 1 つを採る
(first-match。これにより網羅性と排他性が同時に成り立つ):**

| 順 | 値 | 条件 | 正例 |
|---|---|---|---|
| 1 | `weak_denominator_not_certifiable` | 分母 `D_w` の信頼集合が 0 を除外できない | false |
| 2 | `not_certifiable` | `interval_shape` が `bounded` でない | false |
| 3 | `boundary_ambiguous` | `bounded` かつ集合が 0 または 1 を含む / 接する | false |
| 4 | `below_degraded` | `bounded` かつ集合全体が 0 未満 | false |
| 5 | `stock_exceeding_unattributed` | `bounded` かつ集合全体が 1 超 | false |
| 6 | `degradation_below_kappa` | `bounded` かつ集合全体が `(0,1)` の内側だが `inf_{C_w} H_w ≤ 0` | false |
| 7 | `partial_recovery` | `bounded` かつ集合全体が `(0,1)` の内側かつ `inf_{C_w} H_w > 0` (= `P_w` 成立) | **true 候補** |

順 2 の否定と順 3〜5 の否定のもとで、有界な集合は必ず `(0,1)` の内側にある。したがって
順 1〜7 は到達可能な全状態を尽くす。**`degradation_below_kappa` は「回復は見えたが劣化が浅すぎて
回復を主張する意味がない」状態であり、認証しない。**

`empty` は有効な raw からも生じるので、表現不整合 (`invalid_representation`) と分離する。
`RF > 1` は「回復」とも「新規改善」とも帰属させず、stock 超過とだけ述べる (D162 決定 6)。

## 6. 標本数の決め方 (二段階)

**pilot (外部・非 pool)。** `J_p = 8` + 予備 2 (裁定 U5)。
pilot の raw は本走の推定・p 値・区間へ**一切合算しない**。合算すると「途中で見て足りなければ足す」
形になり、帰無仮説のもとでの誤り率が名目を超える。
pilot が推定するもの: 割当て間共分散、cluster 内残差と位置・直前 arm の効果、
待機後の環境復帰、割当ての実時間と infra failure 率、**計算ポイントの単価**。

**planning alternative は `d = 1.0` に固定する** (裁定 U4)。pilot の下側効果が 1 を下回っても
`d` を引き下げない (引き下げは結果依存の費用裁定変更にあたる)。下回る場合は
`design_not_feasible` を終端状態として本走を投入しない。

**本走の `J`。** 目標は **「6 成分の同時受理確率 80% 以上」** (裁定 U4、成分ごと 80% ではない)。
`J` は pilot 母数の**共同信頼集合上の最悪検出力**で評価し、候補 `J` 全体に同時保証を掛けた上で
最小の適格値を選ぶ。**単一の scalar `d` から一意に決めない** — 6 成分の相関と区間形状で
受理確率が変わるため。正規近似の目安は成分ごと 80% で `J≈11`、全体 80% で `J≈13`。
**これは sanity 値であって本走値ではない。**

`J_max`、pilot 本数、再設計の禁止は **pilot 前に固定する**。
`design_not_feasible` は当該候補・親系列の**終端状態**とし、
再開は全試行を保持した新 study・新しい有意水準割当てに限る。

**本走開始後の追加は一切行わない** (D126 決定 4)。

## 7. paired cluster の適格条件

1 割当てを 1 cluster とする。**cluster 内は 6 反復、3 arm の全 6 順列を各 1 回**とする
(裁定 U6 (a))。これにより arm 位置と直前 arm がともにちょうど 2 回ずつ現れ、厳密に均衡する。

- 推定量・検定統計量・区間は cluster 間の標本平均と標本共分散だけから構成する。
  cluster 内の反復・block・個々の測定値を独立標本や追加の自由度として数えない。
- block の実行順は事前 seed で許容集合から選び、runtime 乱数を使わない。
  W1 / W2 の block 順は cluster 間で差 1 以内に均衡させる。
- 結果を見た後の cluster 選別・順序変更をしない。全 attempt を保存する。
- 性能を測る 3 arm はすべて **trace-disabled ビルド**で揃える。correctness 検証は trace-enabled の
  別ビルド・別 run で行い、同一割当ての中で性能測定と混ぜない (絶対規律 1)。
- pairing・順序均衡・cluster の受領証のいずれかが成立しなければ「判定不能」とし、
  unpaired 推定へも通常の campaign compare へも自動 fallback しない。

**帰無仮説は weak mean null を primary とし** (estimand が平均 contrast のため)、
sharp null は副次感度分析とする。weak null の型 I 誤りは、同じ許容 schedule 集合を使う
事前 simulation で較正する。

## 8. 実行順序・待機・時間予算 (裁定 U11 — 数値は追補で確定する)

**主経路は割当ての時間予算を組み直すこと** (裁定 U11 (a))。具体的には build を割当ての外で済ませ、
使用するバイナリの identity を hash で束縛する。**この経路が成立しない場合にだけ**、
より長い walltime を要求する予備経路 (U11 (b)) を採る。

現時点で、build・run・待機・検証・後片付け・安全余裕を含む**承認済みの数値表は存在しない**。
待機の原案は arm 間 30 秒・block 間および workload 切替時 60 秒だが、**現データはこの十分性を
実証していない。**待機後に環境が戻ったことを確認する指標と、戻らなかった場合の失敗分類も未確定である。

したがって本 core は数値を書かない。数値は §14 の **schedule 追補**で確定する。
**schedule 追補が存在しない間、pilot を投入してはならない** (§15 の gate)。
これは値なし前方参照でも placeholder でもなく、閉じた禁止規則である。

## 9. 欠測と失敗

- **correctness anomaly は候補の終端 reject。** 削除も置換もしない (絶対規律 2 の直接適用)。
- 性能測定の**開始前**の infra failure だけ、結果を見る前に外部証拠で確定した上で
  事前順序固定の予備から置換可。
- 性能測定の**開始後**の失敗は reject または判定不能。予備で置き換えない。
- 救済する場合は worst-case bound と感度分析を併記する。
- 失敗分類は本節の集合を正本とし、追補が新しい分類を作ってはならない。

## 10. 有意水準の台帳 (裁定 U8 — 数値は追補で確定する)

primary 系列と個別公表系列に**別々の累積台帳**を置く。台帳は最初の正式試行より前の正規の根へ
束縛し、新しい親系列 ID の自己申告でリセットできないようにする。
**候補数上限と累積 spending の数値は未確定**であり、§14 の **alpha 追補**で確定する。
alpha 追補が存在しない間、本走の formal verdict を出してはならない。

個別公表は primary の成否にかかわらず **6 セル全件を固定表で公表**する
(成功セルだけを抜き出さない)。

## 11. 着手順序と費用 (裁定 U9 / U10)

```text
段 A  producer を実装する (記録項目を確定。適格性の申告は受け付けない)
段 B  pilot を走らせる → この時点で D162 の発火条件 (i)(ii) が成立する
段 C  それを根拠に validator と最初の消費側を実装する → (iii) が成立する
段 D  pilot から標本数を導き、本走を投入する
```

D162 は書き換えない。pilot 自身を「発火条件を満たす計測」にすることで、
「条件が揃ってから機械化する」規律をそのまま守る。
段 A の記録項目確定は**単独の裁定 gate** とする。

**総ポイント上限は 26 割当て相当** (pilot 8 + 予備 2 + 本走 13 + 予備 3) とする (裁定 U10)。
**単価は未知である。** pilot の 1 本目で scheduler の会計痕跡を取得して検証し、1 本ずつ保守的に
上限を更新する。費用未知のまま全割当てを一括承認しない。
pilot から求めた `J` が残余上限内に無ければ `design_not_feasible` とする。

## 12. 記録項目 (raw receipt。producer が書き、validator が読み直す)

適格性状態・pairing の成否・受理状態・validator の identity / 結果は
**closed schema で拒否する** (D162 決定 2)。producer が宣言できるのは
利用意図を示す閉集合の種別 (field 名は実装 wave の新 D で確定する) と
raw な実行事実・証拠 pointer だけである。

必須項目:

- 事前登録の束縛 — core の `<commit>` / `<path>` / blob SHA-256、schedule 追補の同三つ組、
  および本走では alpha 追補の同三つ組。
- 環境タグ (`pegasus`) と**環境証明** (`attestation_mode` を要求扱いにする)。
- 測定 checkout (repo / CCBench の head)、依存の pin、build identity、compile argv、
  割当て外 build を採る場合は使用バイナリの hash。
- 割当て ID・node・時刻・会計痕跡・単独性検査の結果。
- 3 arm の source / binary / compile identity。
- 計画した実行順序と**実際の**実行順序、各 run の位置・直前 arm・timestamp・raw TPS。
- correctness の**証拠** (boolean の申告ではなく、verifier が再実行できる形)。
- liveness、admission telemetry。
- **全 attempt**、理由コード、置換関係、親系列 ID。

## 13. 必須の否定検査 (実装時に必ず kill する変異)

1. 失敗した投入を台帳と raw の**双方**から落として双射を成立させる。
2. 新しい親系列 ID を自己申告して累積有意水準をリセットする。
3. correctness anomaly を clean と申告する。
4. 適格性 field を raw へ足す (closed schema が拒否するか)。
5. 事前登録した `J` に対し cluster が 1 本足りない状態で受理する。
6. 実際の実行順序が計画と異なる / 待機が不足している状態で受理する。
7. core と異なる blob を core として申告する、または schedule 追補が core の推論内容を変更する。

## 14. 追補 (addendum) の閉集合

追補は **core の推論内容を一切変更しない。**追補が設定してよいのは次の field だけであり、
それ以外の変更は core の変更に当たる。core を変更する必要が生じたら、それは**別 study** であり、
新しい core を起こしてユーザー裁定へ戻す (本 core を書き換えない)。

**schedule 追補 (pilot より前に commit する):**

| # | field |
|---|---|
| s1 | 1 割当ての時間予算表 (build・run・待機・検証・後片付け・安全余裕の秒数と合計) |
| s2 | arm 間・block 間・workload 切替時の待機秒数 |
| s3 | 待機後の環境復帰を判定する指標と、その事前登録した許容範囲 |
| s4 | 復帰しなかった場合の失敗の写像先 (§9 の既存分類のどれに写すか。新分類を作らない) |
| s5 | 割当て外 build を採る場合の binary identity 束縛方法 (hash の対象と記録先) |
| s6 | 予備経路 (U11 (b)) を採る場合の要求 walltime |

**alpha 追補 (本走の formal verdict より前に commit する):**

| # | field |
|---|---|
| a1 | 候補数上限 |
| a2 | 系列ごとの累積 spending 関数の数値割当て |

追補は core と同じく実走前に commit し、結果の記録がその `<commit>` / `<path>` / blob digest を
参照する。追補は自分が従属する core の canonical path を明記する。

## 15. 投入 gate (順序検査。機械配線は producer 実装 wave の責務)

本 gate は「事前登録が存在しない状態で投入しない」という**順序**の検査であり、作業木の前進を
縛るものではない。**本 wave は文書上の契約だけを定める。**producer・validator・consumer・
投入 script・受領証への機械配線は producer 実装 wave が行い、本 wave では追加しない。

署名 (3 段。receipt の照合は投入の**前提にしない** — 投入後にしか存在しないため):

```text
resolve_effective_preregistration(
    repository_root, *,
    core_ref     = (commit, path, sha256),
    schedule_ref = (commit, path, sha256),
    alpha_ref    = (commit, path, sha256) | None,
) -> PreregBinding

submit_pilot(*, binding: PreregBinding, measurement_head) -> submission_id

verify_receipt(*, binding: PreregBinding, receipt) -> None
```

**禁止:** `submit_pilot` は、次をすべて満たす `binding` が `resolve_effective_preregistration` から
返っていない限り実行してはならない。

1. `core_ref.path` が、本 study の決定が定める canonical core path と byte 一致する
   (producer は core を自由選択できない)。
2. `core_ref.commit` の tree に `core_ref.path` の blob が実在し、その SHA-256 が
   `core_ref.sha256` と一致する。
3. `schedule_ref` も (1)(2) と同型に解決でき、その追補が従属先として記す core の canonical path が
   `core_ref.path` と一致する。
4. `core_ref.commit` と `schedule_ref.commit` が、投入時の実 checkout から導出した
   `measurement_head` の祖先である (`orchestrator/campaign/trial_registry.py` の
   `assert_prereg_ancestor` と同型の検査)。`measurement_head` は caller の申告値ではなく
   実 checkout から導出する。
5. core の `pilot_admission` が要求する追補が (3) ですべて解決済みである。

本走の formal verdict は、さらに `alpha_ref` が (1)〜(4) と同型に解決でき、core の
`main_admission` が要求する追補がすべて揃っていることを要する。

`verify_receipt` は投入**後**に、receipt が記録した 3 つ組と `measurement_head` が `binding` と
一致することを確認する。これを admission の前提に置くと、投入前に存在しない値を前提にする
時間逆転になる。

**通る正例 (1 つ):** core が commit `C`・path `P` に blob `B` として存在し、`h = SHA-256(B)`、
schedule 追補が commit `C2`・path `P2` に blob `B2` として存在し、`h2 = SHA-256(B2)`、
`B2` が従属先 core として `P` を記し、`C` と `C2` がともに測定 checkout `M` の祖先であるとき、
`resolve_effective_preregistration(repo, core_ref=(C,P,h), schedule_ref=(C2,P2,h2))` は成功し、
他の admission 条件を満たせば `submit_pilot` へ進める。
**この正例は現時点では成立しない** — schedule 追補がまだ存在しないためである (要件 3・5 が不成立)。
gate は恒真な deny ではなく、追補の land によって到達可能になる。

**この gate が保証しないこと:** 台帳の外で走らせた投入は見えない。producer が実際とは異なる
bytes や schedule で走らせながら整合した受領証を作る偽造も、外部の時刻根拠なしには検出できない。
現在の作業木や main の同 path の bytes が過去の blob と異なることは**検出対象ではない**
(過去の結果は commit の blob に束縛されるため)。

## 16. 本走の後

`RF` の点推定と区間、6 セルすべての調整済み p 値と同時区間を、**primary の成否にかかわらず
固定表で公表する** (成功セルだけを抜き出さない)。
機序の帰属は本 study では行わない (3 変更を同時に入れたため。ablation は別の事前登録 study)。

## 17. 本書が主張しないこと

- 代替 X が適格である、とは主張しない。現時点で成立しているのは J=1 の engineering screen だけである。
- 回復の機序が stripe 数・cache line 分離・固定回数計算のどれによるか、は主張しない。
- 推奨した標本数が正しい、とは主張しない。割当て間のばらつきは 1 点も推定されておらず、
  pilot の前に確定できない。
- **本 wave が投入 gate を機械的に実装した、とは主張しない。**本書が定めるのは文書上の契約である。
