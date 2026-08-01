# 段 4 裁定 — [T-241] 実装しない。前提を覆す新事実つきでユーザー再裁定へ戻す

wave: `t241-compute-llm-transport` / 2026-08-01 / 親裁定

## 裁定の結論

**S1 (env allowlist への proxy 追加) と S2 (計算ノードでの 8c 実走受入) を実装しない。**
`DW-S04` の「実装しない」分岐を採り、段 5・6 を飛ばして `4→7→8→9` とする。
実装差分がないため、変異 matrix と受入全走は本 wave の対象外である。

docs は 2 点だけ触る — runbook §7.1 の**事実**訂正と、記録・起票。防壁 (D108 の分割線、
`_site_admits_measurement` の Pegasus 拒否、現行 allowlist) には手を触れない。

## なぜ止めるか (一次資料で確認済み)

`docs/decisions.md` D108 決定 (1) は次を明記している。

> supervisor と planner / coder / auditor / critic は外部 network を持つログインノードが所有し、
> 計算ノードへ送るのは build / verify / bench の機械部分だけとする。
> **計算ノードで `claude -p` を起動しない。**

そして同 D108 の背景は、その根拠をこう書いている。

> 計算ノードが外部 network 不可 (request 873903/873904) で `claude -p` を呼べないという前提は
> 正しく、分割の必要性そのものは動かない。

**この前提を本 wave の実測が覆した。** 計算ノードは direct DNS/socket では外へ出られないが、
計算ノードの shell profile が `http_proxy` / `https_proxy` を持ち、Claude CLI はそれ経由で
API に到達する (下記「実測」)。同じ prohibition は `docs/pegasus-runbook.md` §8 の投入前
チェックリストにも規範として書かれている。

したがって本件は `DW-STOP` / `DW-S04` の「承認済み裁定の前提を覆す未見の新事実」に該当する。
親は裁定を独断で失効させず、**新事実を付けてユーザー再裁定へ戻す**。

さらに `DW-G04` (条件付き機能の発火 gate) が独立に同じ結論を与える。proxy を allowlist へ
通す機能の発火条件は「role process が計算ノードで走ること」であり、それは現行契約で禁止されて
いる。発火する既存 artifact path も計測 ID も brief に書けない以上、実装せず設計メモに留める。

## 実測 (この wave の一次証拠)

| # | request | node | 内容 | 結果 |
|---|---|---|---|---|
| 1 | `876527` | bnode002 | `getent hosts api.anthropic.com` / `/dev/tcp` | いずれも名前解決不能 |
| 2 | `876527` | bnode002 | 素の `claude -p` (nonce `PONG`) | rc=0 |
| 3 | `876528` | bnode002 | `claude -p` 算術 nonce `8123+4517` | `12640` rc=0、3 秒 |
| 4 | `876529` | bnode002 | proxy 変数の実体 | `http_proxy` / `https_proxy` = `10.120.96.1:8080` |
| 5 | `876529` | bnode002 | TEST A: full env `claude -p` `7311+2088` | `9399` rc=0 |
| 6 | `876529` | bnode002 | TEST B: **driver の allowlist と同一 env** | `API Error: Unable to connect to API (ENOTIMP)` rc=1、**172 秒** |
| 7 | `876529` | bnode002 | TEST C: allowlist + proxy 復元 `4011+2044` | `6055` rc=0 |
| 8 | `876729` | bnode002 | toolchain 棚卸し | `g++-12` のみ (**`g++-13` 不在**)、gflags/glog 不在、cmake 3.25 |
| 9 | `876813` | **bnode145** | 8c driver 実走 (claude-headless / A,B,C / 1 gen / no-build) | driver rc=2、3 cell とも `planner-invalid`、`nonzero rc: 1` |

補足と限界:
- TEST C の大文字 4 変数は**空文字**で足しただけである。非空 uppercase と `no_proxy` の意味論は
  未測定であり、支持されている事実は **lowercase 2 変数**に限る。
- #9 は bnode145、#1〜#8 は bnode002 で、別 allocation である。よって #9 は「同一ノードでの
  before/after 対照」ではない。ノードを跨いだ再現として読む。
- #9 の実行は「計算ノードで `claude -p` を起動しない」という現行チェックリストに**抵触する**。
  前提の実測 (`DW-S01`) として行い、計測値は 1 つも生んでいないが、事実として記録する。

## 所見の裁定 (段 3 敵対レビュー 2 本)

| # | 所見 | 判定 | 裁定 |
|---|---|---|---|
| A1 | proxy 値は無検査の外部制御面であり「transport のみ」は隔離契約の変更の言い換え | **real** | 採用。親 brief の「能力は 1 bit も増やさない」を**撤回**する |
| A2 | 攻撃者制御 proxy から MITM / prompt injection が成立しうる (規律 6) | **real** | 採用。実装を止める主要根拠の 1 つ。裁定パッケージへ |
| A3 | key-only provenance では 8b resume が別 proxy 値を同一 journal へ混載できる | **real** | 採用。実装するなら値同一性の証拠が要る。裁定パッケージへ |
| A4 | 凍結 `agent_provenance` (exact 8 key) から transport が落ち proof chain が分裂 | **real** | 採用。段 2 プランの射影案でも「凍結側からは証明不能」は残る |
| A5 | `getattr(provider, "transport_env_keys", ())` が未計装 provider を「proxy なし」に偽装 | **real** | 採用。実装時の必須修正として台帳化 |
| A6 | 「transport だけ」は timeout・token・課金の面で実測上すでに偽 | **real** (supervisor retry 不変の部分のみ refuted) | 採用 |
| A7 | bnode002・lowercase 2 key から 6 key・全 site への一般化に根拠がない | **real** | 採用。上記「実測」の限界欄に反映済み |
| A8 | S2 は runbook §8 と D108 の実行場所契約に反する | **real** | **採用。本裁定の中核** |
| B1 | consumer 面: `s6_proposal_rounds.py:318` と `tools/dev_waves/daemon.py:1060` も同型経路 | **real** (第 3 の provider は refuted) | 採用。起票のみ (本 wave scope 外) |
| B2 | S2 の `transport_env_keys` 一致検査は実装と同じ env から期待値を作る**恒真** | **real** | 採用。実装時は独立 literal 事前登録 + child env receipt が要る |
| B3 | 新設テスト 7 件のうち複数が F64 同型 (期待値が実装定数を参照) | **real** | 採用。実装時の設計制約として台帳化 |
| B4 | compiler/deps だけ直しても live は動かない (`_site_admits_measurement` が Pegasus を拒否) | **real** | **採用。親 brief の scope 切りが甘かった。下記へ反映** |
| B5 | 訂正すべき文書が §7.1 だけでは足りない。runbook が split 裁定を D106 と誤参照 | **real** | 事実訂正は採用。D 参照の訂正は裁定パッケージへ (裁定文の書換えになるため) |
| B6 | before control の node 誤記 (bnode002 → bnode145)、proxy 値が平文で残っている | **real** | 採用。handoff を訂正済み。proxy は内部 IP であり秘匿対象として扱わない |
| B7 | before/after の因果対照に source/CLI/PBS hash の束縛がない | **real** | 採用。実装が裁定されたら受入設計に含める |

`refuted` / nit: 親 brief の「login で重処理しない」「実装面は author が書く」への攻撃 (A の
brief 行別表 [57][58][80]) は規範の再確認であり成果物値を変えない。

## 親 brief の訂正 (自己修正)

1. 「role へ渡る文脈・能力は 1 bit も増やさない」は**誤り**。正しくは「role の
   prompt / tool / MCP / settings / session の能力は増えない。外部 API 到達性は意図的に回復し、
   接続先を決める外部入力が 1 つ増える」。
2. 「全 role attempt が `role-invalid`」は**誤り**。planner で cell が停止するため planner 3 件だけ
   が発火する (実測 #9 と一致)。8b 側はさらに別で、nonzero rc が invocation 前に例外となり
   `claimed_missing` になる。
3. scope 切りが甘かった。live pilot の残余は「compiler と gflags/glog」だけではない。
   `p3_s4_loop_trigger_gating.py` の `_site_admits_measurement` が**認識済み Pegasus を明示的に
   拒否**しており、加えて D108 決定 (5) の cache key 貧弱性 (別環境の cache が同 key で hit しうる)
   がある。これらは受理集合と build identity の問題で、toolchain 調達より重い。

## 成果物影響 (DW-G05)

- **実装しないことの影響:** 成果物の値・受理集合・参照はいずれも変わらない。8c/8b の role は
  ログインノード限定のまま、live A/B/C pilot は塞がったまま残る。T-241 は完了しない。
- **誤った事実を放置した場合の影響 (だから docs は直す):** 「計算ノードから LLM を呼べない」が
  裁定根拠として生き続け、次の wave が同じ前提で設計判断を積む。値は変わらないが、
  受理集合の設計が誤った制約の上に載る。

## ユーザー裁定パッケージ

### 択一 1: D108 決定 (1) の前提が覆ったことをどう扱うか

- (a) **D108 をそのまま維持する** — 前提は覆っても、分割線 (LLM は login、機械部は compute) には
  proxy 到達性と独立の利点がある (資格情報を計算ノードへ持ち込まない、外部 proxy を信頼境界に
  入れない、規律 6)。事実だけ訂正し、実行場所契約は変えない。**親の推奨**
- (b) **計算ノードでの role 実行を解禁する** — proxy 経由で到達できる以上、8c を単一 allocation で
  完結させられる。ただし A2 (攻撃者制御 proxy)、A3 (値同一性)、B2 (恒真な受入) を先に閉じる必要が
  ある
- (c) 条件付き解禁 — 「no-build の配線検査に限り可、計測を伴う run は不可」

### 択一 2: live A/B/C pilot (T-241 の見出し) をどう進めるか

- (a) **Pegasus 限定 pilot path を新設する** — `_site_admits_measurement` に Pegasus を通す道を
  D96 手続で開き、compiler realpath/version・dependency prefix・site・env contract を build
  identity へ入れ、`/scr` に fresh namespace を切る。certify の recipe を再利用する
- (b) **T-241 を保留にする** — 現行の防壁が拒否している以上、先に他タスクを進める
- (c) linux-baremetal 等、network と gcc-13 の両方がある機体で走らせる (機体の所在はユーザーのみが
  知る)

### 択一 3: 訂正の射程

- (a) runbook §7.1 の事実行だけ直す (**親が本 wave で実施する既定**)
- (b) D106/D108 の参照バグ (runbook が split 裁定を D106 と書いている) も同時に直す
- (c) 過去 worklog / archive / insights の同じ前提も supersede 追記する

### 択一 4: 段 8 自己改善の 2 候補が予算で入らない

本 wave で実測した手順の穴 2 件を `docs/dev-wave/operations.md` の既存節へ統合しようとしたが、
`docs/dev-wave/**` の合計が hard ceiling 24000 bytes に対し 23991 bytes で、**空きが 9 bytes** しか
ない。既存の義務文に無損失で縮められる箇所を見つけられなかったため、`docs/skill-self-improvement.md`
の「予算に収まらなければ … 意味等価にできなければ変更を止めてユーザー裁定へ返す」に従って戻した。

候補 (どちらも本 wave で実際に踏んだ):

1. **`DW-O01` へ**: 背景 job から codex を起動するときは `nohup` で切り離す。呼び出しが返ると子が
   死ぬ。本 wave では段 2 の 1 本目がこれで落ち、`.done` も `-o` 出力も残らなかった
2. **`DW-O20` へ**: worktree から `qsub` すると `<script>.o<ID>` / `.e<ID>` が cwd (= worktree root) へ
   落ちる。clean-tree gate と `git add -A` の前に回収しないと未追跡ごみを巻き込む。本 wave では
   commit 直前に 10 ファイルを回収した (near miss)

択:
- (a) **予算の独立審査**を行い、`dev-wave/**` の ceiling か中身の配分を見直す (規約は予算値の変更を
  通常の自己改善から外し、理由付きの独立審査対象としている)
- (b) 既存節の**意味等価な縮約**を別 wave で行って空きを作り、その後に統合する
- (c) 統合しない (2 件は本 insight にだけ残す)。**親の推奨は (b)** — 2 件とも実測済みで、
  次に踏む wave が同じ時間を失う

## 本 wave が実施すること (実装なし)

1. `docs/pegasus-runbook.md` §7.1 の「計算ノードは外部 network 不可」を実測どおりに訂正し、
   飛躍 (「https が通るなら FetchContent も通る」) を明示的に禁止する
2. worklog へ本エントリを記録し、[T-241] を再スコープ、新規 ID を起票する
3. 本 insight 一式 (brief / plan / lens A / lens B / 本裁定) を凍結する
