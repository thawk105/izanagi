# 環境戦略監査 (2026-07-22) — 逐語 (codex)

実行: codex exec, model=gpt-5.6-sol, reasoning=high, sandbox=read-only。親 = claude-fable-5 (background job)。
発端 = ユーザーの指摘「環境を跨ぐと全てを焼き直すのは無駄では」。roadmap §5「環境間の知見可搬性」節 (2026-07-22 協議改訂) の根拠資料。

## プロンプト (逐語)

```text
あなたは izanagi プロジェクトの計測環境戦略を監査する外部レビュアーである。リポジトリは読み取り
専用で自由に調べてよい。出力はすべて日本語。忖度不要。

# 背景
オーナーの懸念: 「cygnus と pegasus は環境が違うから、何かを立証するのに全てを焼き直さないと
いけないのは非常に無駄では?」。事実確認と戦略評価をしたい。

前提知識: cygnus = 研究室共有の Dell R760、env-tag `linux-baremetal` の実体。凍結済み実験 (S-1 等)
はこの env-tag に束縛。pegasus = 共有スケジューラ型スパコン。2026-07-19 に env_contract 登録
(attestation、certification job は attempt 10 で accepted)。8b の floor 実測は pegasus で計画中。

# 読むべきもの (必要に応じて広げる)
- docs/decisions.md の D59 全文 (grep -n "D59" で位置特定) と、env 関連の他の D
- docs/roadmap.md §5 (計算リソース)
- docs/pegasus-runbook.md
- docs/failures.md F22 (pegasus 登録の attempt 1〜9)
- docs/phase3-8b-descriptor-design.md の env/floor 関連節 (cygnus 固有値・非拘束 prior の記述)
- docs/archive/worklog-phase3-0714-0716.md、-0717-0718.md、-0719.md の env 選択関連エントリ
- output/env/ 配下のディレクトリ構造 (env-tag ごとに何が束縛されているか)

# 問い

1. **経緯の再構成**: pegasus 導入はいつ・何を理由に決まったか。cygnus に留まる選択肢はなぜ
   棄却されたか。明示的なユーザー裁定はあるか。導入の実コスト (commit 数、attempt 1〜10 の
   試行、attestation/env_contract 機構の実装量、較正) を見積もれ。

2. **焼き直しの実態**: env を跨いだために再取得が必要になった/なる資産を全て列挙せよ
   (calibration、within/between-run floor、holdout freeze の floor/budget が null なのはこれが
   原因か、S2 verify 構成、noise floor 等)。それぞれの再取得コスト (bench 時間・裁定) も。
   逆に、env を跨いでも再取得不要なもの (correctness 検証、identity、コード資産) も列挙せよ。

3. **科学的必然性の判定**: roadmap の主張階層 (評価器の主張 / システムの主張 / LLM 固有の主張 /
   無人自律の主張) のうち、環境 2 つを維持しないと立証できないものはあるか。「workload 特化
   variant の合成・選択」というシステム主張は 1 環境で立証可能か。2 環境維持は科学的必然か、
   それとも可用性保険 (cygnus の寿命・共有性) か。保険なら、その保険料 (焼き直しコスト) は
   いま払うべきか、E2E 1 cycle 成立後に払うべきだったか。

4. **オーナーの直観の評価**: 「全てを焼き直さないといけないのは非常に無駄」は正しいか。
   (a) env-tag 分離の規律自体を緩める (異なる環境の数値を混ぜる) のは科学的に許されるか、
   (b) 規律は維持しつつ焼き直しを最小化する設計はあり得たか (例: 最初から 1 環境に pin して
   E2E を通す、環境可搬な資産と env 束縛資産の分離を徹底する等)。

5. **提案**: ここからの最小 env 戦略を具体的に描け。8b E2E 1 cycle をどの環境でやるべきか
   (cygnus 続行 vs pegasus 続行 vs 両方)。既に払った pegasus 投資 (登録・certification) を
   無駄にしない形で。将来の環境追加・移行の gate 条件も提案せよ。

出力: 構造化 markdown。各主張に根拠 (ファイル・行・commit・日付) を付け、推測と実測を区別せよ。
```

## 出力 (逐語)

# 計測環境戦略監査

## 総合判定

1. **Pegasus 導入は二段階だった。**  
   2026-07-16 の D59 は「開発主戦場を Pegasus に移すが、正式計測の正本は cygnus=`linux-baremetal` のまま」という決定であり、Pegasus の正式計測採用ではない。8b の `env_tag=pegasus` は7月18日に別途ユーザーが明示決定し、7月19日に登録された。根拠: [D59](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2278)、[7月18日の env 選択](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/archive/worklog-phase3-0717-0718.md:589)。

2. **cygnus は棄却されていない。**  
   凍結済み成果の正本兼 Pegasus 不可時の退避先として明示的に残されている。8b だけ Pegasus が選ばれた理由は、ユーザーが当面 Pegasus を使うと決め、cygnus 側の実行者・時刻が未定だったためである。[D59 lines 2286–2297](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2286)、[worklog 7月16日 lines 1000–1020](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/archive/worklog-phase3-0714-0716.md:1000)。

3. **現行 roadmap の四層の主張に、二環境維持を必須とするものはない。**  
   二環境はハードウェア可搬性・外的妥当性を追加で主張する場合にだけ科学的価値を持つ。現行の「workload 特化 variant の合成・選択」は、同じ環境内で workload だけを変える方が交絡が少なく、一環境で立証可能である。[主張階層](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/roadmap.md:32)、[システム合成の要件](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/roadmap.md:118)。

4. **オーナーの直観は半分正しい。**  
   「全てを焼き直す」は誤りだが、「二環境を同時に正式維持すると性能証拠の大半が二重化し、非常に無駄」は正しい。環境タグ分離は緩めるべきでない。緩める対象は規律ではなく、同時に正式運用する環境数である。

5. **ここからは Pegasus 一環境で 8b E2E 1 cycle を完走すべきである。**  
   cygnus は凍結成果の保管・障害時 fallback とし、同じ 8b campaign を今すぐ複製しない。Pegasus 登録費は既に sunk cost であり、今 cygnus に戻るとその投資を生かせず、しかも rr80/rr20 の floor は cygnus にも存在しない。

---

## 1. 導入経緯

### 時系列

| 日付 | 事実 | 判断 |
|---|---|---|
| 2026-07-16 | Pegasus runbook を新設。初期位置づけはデバッグ環境。正式採用時だけ専用 env-tag と再較正を行う。[worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/archive/worklog-phase3-0714-0716.md:831) | まだ正式計測環境ではない |
| 2026-07-16 | 実機 smoke、キュー、`Exclusive submit=OFF` 等を確認。[worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/archive/worklog-phase3-0714-0716.md:845) | ノード割当てを専有保証と見なさない |
| 2026-07-16 | D59、commit `00624d4`。正式正本は `linux-baremetal` に据え置き、別環境採用の4条件を定義。[D59](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2278) | cygnus 維持、Pegasus は未登録 |
| 2026-07-16 | ユーザー回答「pegasus も cygnus も使う」。その後「しばらく Pegasus」で、env-neutral 実装先行を承認。[worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/archive/worklog-phase3-0714-0716.md:943) | 二環境の数値混合ではなく、env-tag 別運用 |
| 2026-07-18 | ユーザーが env contract 抽象化を明示承認。「しばらく Pegasus を多用」。[descriptor design](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/phase3-8b-descriptor-design.md:362) | Pegasus 対応が一般化実装へ拡大 |
| 2026-07-18 | `env_tag=pegasus` を明示確定。[worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/archive/worklog-phase3-0717-0718.md:589) | 8b floor の環境選択が確定 |
| 2026-07-19 | certification attempt 10 が accepted、commit `26a9ad6` で registry 登録。[worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/archive/worklog-phase3-0719.md:26) | bootstrap 登録完了。ただし between-run floor 未取得 |

### cygnus に留まる案が採られなかった理由

**実測・記録された理由**

- ユーザーが当面 Pegasus で作業すると明示した。
- cygnus で測る実行者・時刻が未定だった。
- cygnus の既存 floor は rr5/rr50/rr95 で、8b holdout の rr80/rr20 には転用できない。
- cygnus の古い calibration は toolchain、pin、日時等の完全な契約を欠き、再利用には鮮度照合が必要だった。[再利用資格の監査](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/insights/2026-07-16_s8b-ruling-prep-consultations.md:195)。

したがって、**cygnus が科学的に不適格だったのではない。運用上 Pegasus が選ばれた**というのが正確である。

### 導入コスト

直接帰属できる commit は、監査上次の **20 commits**。

- D59/runbook 段: 4 commits
- env contract 基盤・要件記録: 3 commits
- 7月19日の登録 wave～記録完結: 13 commits（`950757e`～`0b4f67c`）

コード量は Git 差分による実測で、

- env contract 基盤 `28ccb07`: **+658行**（本体227、テスト430、README 1）
- 登録 wave `950757e^..26a9ad6`:  
  **+12,272 / −352行**
  - production + tools: +6,696 / −284
  - tests: +5,576 / −68
- 合計純増: およそ **12,930行**

証拠ログ・smoke 出力はこの行数から除外している。登録 wave は実装19単位、レビュー17本、最終テスト1927件と記録されている。[worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/archive/worklog-phase3-0719.md:32)。

### attempt 1〜10

[一次記録](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/insights/2026-07-18_env-contract-pegasus-consultations.md:1191)による。

| attempt | 秒 | 発見 |
|---:|---:|---|
| 1 | 6 | NQSV の qstat 開始時刻 field |
| 2 | 7 | worktree の submodule 未実体化 |
| 3 | 9 | gflags 不在 |
| 4 | 11 | `/scr/0:ID` の `:` を CMake が分割 |
| 5 | 10 | glog 不在 |
| 6 | 136 | raw 表記と正規化表記の照合空間不一致 |
| 7 | 105 | probe が自身の argv に一致 |
| 8 | 106 | perf dispatcher とカーネルの不一致 |
| 9 | 207 | NFS 上の `renameat2` が `EINVAL` |
| 10 | 210 | accepted |

合計 **807秒＝13分27秒**。記録上は投入等を含め約15分、約0.1 point。commit 時刻では初期実装 `950757e` から accepted `26a9ad6` まで約3時間23分である。F22 自身も、依存を事前全量列挙すれば一部 attempt は削減できたと認定している。[F22](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/failures.md:259)。

---

## 2. 焼き直しの実態

### Pegasus で取得済み

- CPU/clock/cache/NUMA/core topology と attestation
- `clocks_per_us=2100`
- 48 threads、1 NUMA、numactl なし
- rr50/skew0.9/rmw0 の calibration
- records=1M の working-set 下限
- within-run 10 reps、CV=1.17%

根拠: [登録 calibration](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json)、[registry](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/env_contract.py:163)。

これは **bootstrap registration** であって、正式な性能差を判定できる between-run floor ではない。[worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/archive/worklog-phase3-0719.md:40)。

### 8b でまだ必要なもの

| 資産 | 再取得 | コスト |
|---|---|---|
| rr80/rr20 × 6構成の対象別 between-run floor | 必須 | 12セル × 8 sessions × 5 reps × 3秒 = **名目bench 1,440秒＝24分**。起動・build・retry 込みの実 wall は Pegasus pilot 後に確定。[floor protocol](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/insights/2026-07-16_s8b-floor-protocol-package.md:211) |
| floor の retry | 異常時のみ | 最大2 slots/cell。最大全セルなら追加名目bench 360秒 |
| full-pipeline pilot | 必須 | Pegasus の build/verify/bench 比を測る。現時点では未実測 |
| oracle 性能分布 | 必須 | 12セル × `N_oracle=8` = 96 evaluations |
| legacy + S2 correctness | 各 Pegasus build に必須 | cygnus prior では S2 verify 433秒 ×96 ≈ **11.6時間**。Pegasus では未実測の非拘束 prior。[descriptor design](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/phase3-8b-descriptor-design.md:348) |
| performance budget | floor/pilot 後に凍結 | 独立したベンチではなく、pilot と floor の実 wall を用いた算出＋ユーザー承認 |

### `holdout_freeze` の floor/budget が null の理由

`floor=null`、`budget=null` は7月16日の生成時点から意図的であり、「対象別 floor 再実測後に再凍結する」と明記されている。[holdout freeze](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/s8b-freeze/holdout_freeze.json:622)。

したがって、

- **直接原因:** rr80/rr20 対象別 floor を結果閲覧前に取得していないこと
- **副次的遅延要因:** その後 Pegasus を選び、登録・attestation・pilot が前置されたこと
- **誤り:** 「env を跨いだから null になった」

cygnus を選んでも rr5/50/95 の既存 floor は rr20/80 に転用できず、null の解消には新規 floor が必要だった。

### S2 verify の扱い

S2 のロジックと workload 定義は可搬だが、D36 の「contention 再現・trace 規模・broken positive control」の実証値は cygnus 固有である。[D36](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:859)。

- verifier コードや positive-control の設計を作り直す必要はない。
- ただし Pegasus で生成した exact binary の certification は再実行が必要。
- Pegasus 上でも「S2 の検出力を実証済み」と強く主張するなら、D36 の3点資格試験を一度再実行すべき。
- 過去の cygnus S2 成果物を上書きしてはならない。

### 過去の env 資産

`linux-baremetal` には calibration、RR5/50/95 between-run noise、S1/S2 qualification、S3 lock coverage、S5 permutation coverage、S8a trigger coverage、backoff profile がある。[ディレクトリ](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/env/linux-baremetal)。

これらは、

- **過去主張の証拠としては再取得不要**
- **同じ主張を Pegasus の主張として再発行する場合だけ再取得**
- **8b E2E の成立には大半不要**

である。S1 やS8aを Pegasus で丸ごと再実行する必要はない。

### env を跨いでも可搬なもの

- CCBench source、patch、variant の論理的実装
- workload descriptor/schema、holdout 定義
- selector の封印済み予測
- verifier、positive-control、trace schema
- source/genome/implementation identity
- WAL、report renderer、判定純関数
- env contract/attestation/certification の機構

ただし、**コンパイラ生成 binary hash、build cache、性能数値、実行時 correctness certificate は可搬ではない**。現行 build cache は contract SHA で意図的に環境分離される。

---

## 3. 二環境の科学的必然性

| roadmap の主張 | 二環境が必要か | 判定 |
|---|---|---|
| 評価器の主張 | 不要 | 一つの宣言済み環境で positive control、identity、trace 範囲を示せばよい |
| システムの主張 | 不要 | 同一環境内で rr80/rr20 等の workload を変え、異なる certified 選択を出せばよい |
| LLM 固有の主張 | 不要 | 同一環境で LLM 有無をアブレーションすべき |
| 無人自律の主張 | 不要 | セッション外駆動・予算・checkpoint の問題で、ハードウェア数とは無関係 |

二環境が必要になるのは、次の新しい主張を追加するときだけである。

- 「variant の勝敗がマイクロアーキテクチャを跨いで再現する」
- 「Izanagi が未知の計測環境へ自動移植できる」
- 「選択結果が hardware-robust である」

現行 roadmap はこれらを要求していない。

したがって、二環境維持は主として、

- cygnus の寿命
- 利用者間のアクセス差
- Pegasus 障害・混雑時の退避
- 将来の外的妥当性

に対する**可用性保険**である。

この保険は、登録可能性の確認までなら合理的だった。しかし full floor/oracle を二重実行する保険料は、E2E 1 cycle 成立後に払うべきだった。現行 worklog 自身も、7月19日以降100 commits、本線0、6日間新規計測なしとして速度配分を「重大に誤っている」と評価している。[2026-07-22方向性監査](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:973)。

---

## 4. オーナーの直観の評価

### 「全てを焼き直す」

**文字どおりには誤り。**

- 凍結済み cygnus 実験はそのまま有効
- correctness/identity/schema/code は再利用可能
- 新環境で取り直すのは、その環境上の性能主張に必要な数値と exact build 証明だけ

### 「非常に無駄」

**二環境で同じ正式 campaign を維持する意味なら正しい。**

8b を両方で行えば、少なくとも、

- 対象別 floor 12セル
- oracle 96 evaluations
- exact binary の legacy/S2 verify
- build/cache
- budget/pilot
- report の env 別判定

が二重になる。

### env-tag 分離を緩められるか

**不可。**

cygnus と Pegasus は、CPU、clock、SMT、NUMA、cache、binding、scheduler/isolation、toolchain が異なる。異なる env-tag の throughput を同じ分布へ投入すると、workload/variant 効果と hardware 効果を識別できない。[roadmap §5](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/roadmap.md:321)、[D59不変条件](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2294)。

緩めるべきは env-tag 規律ではなく、以下である。

- 第一主張環境を一つに pin
- 過去 campaign を新環境へ無条件移植しない
- env 可搬資産と env 束縛数値を明示分離
- 二環境目は独立 replication として後置
- 同一環境内の再較正は、全面再走前に hardware/toolchain/pin/binding の reuse qualification を行う

---

## 5. 推奨する最小 env 戦略

### 今回の8b

**Pegasus 単独で続行する。**

理由:

1. ユーザーが `env_tag=pegasus` を明示確定済み。
2. env contract、attestation、certification、calibration は既に完了。
3. cygnus に戻っても rr80/rr20 floor は新規取得が必要。
4. 両方で行う科学的必要性がない。
5. 現在の最大リスクは環境不足ではなく、E2E が一度も完走していないことである。

実行順は現行 phase の最短列をそのまま使う。

1. 残存限界のユーザー受諾
2. protocol JSON 凍結
3. selector 予測封印
4. Pegasus pilot
5. Pegasus floor 12セル
6. freeze v2 候補生成・承認
7. Pegasus oracle
8. 層3実レポート

根拠: [現行 phase](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/phase3.md:61)。

### cygnus の扱い

- `linux-baremetal` の凍結成果はそのまま保管
- Pegasus 利用不能時の fallback
- 8b E2E 完了までは新規 full campaign を投入しない
- 完了後、外的妥当性が必要なら「探索全体」ではなく、封印済み selected variant 対 stock の最小 replication を別 env-tag の独立結果として行う
- 両環境の数値は統合せず、結論の一致・不一致をカテゴリとして報告する

### 将来の環境追加・移行 gate

新環境追加は、次の少なくとも一つが成立した場合だけにする。

- 現主環境が利用不能・廃止予定
- topology/toolchain 変更で現 contract が失効
- 論文上、cross-hardware replication が明示的に必要
- 現主張が hardware-specific ではないと主張する必要が生じた
- 主環境の待ち時間が E2E throughput の支配要因になった

追加時の受入条件:

1. 専用 env-tag
2. source/toolchain/job-script pin
3. topology・clock・NUMA・PID visibility の attestation
4. workload/thread ごとの qualifying calibration
5. within-run 品質測定
6. 対象 workload/pair の between-run floor
7. isolation・walltime・永続ストレージ検査
8. exact binary の correctness certification
9. 旧 env 成果を上書きしない
10. 実走前に「移行」か「独立 replication」かを一つに決める

最終的な戦略は、**一つの active measurement environment、複数の frozen/standby environments** が最小である。今は active=`pegasus`、standby/frozen=`linux-baremetal` が妥当である。