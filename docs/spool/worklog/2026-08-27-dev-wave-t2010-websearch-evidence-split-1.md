---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-t2010-websearch-evidence-split
seq: 1
title: [T-2010] codex 子の Web 検索を許可し、拒否の定義域を成果物側へ限った (コード + docs、branch worktree-dev-wave-t2010-websearch-evidence-split、変異 matrix = baseline PASSED・8/8 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

D1149 (ユーザー裁定) の実装。**拒否を緩めるのではなく拒否の定義域を正した。**
Codex CLI の `web_search` event は同一 object 内に `id` を 2 個持ち、
`parse_jsonl` の重複 key 拒否が `stdout_invalid` を立てて成果物ごと捨てていた (F259 / F263)。

- 依頼時の引数は本件を「未 land、branch `worktree-rulings-all-20260827`」としていたが、
  **wave 開始時点で既に main へ land 済みだった** (`f4df2eeac` が main の祖先)。
  裁定内容は不変。収集時点の事実が wave 開始までに覆っていた型である。

**親が段 1 で実測し、裁定 inbox の前提を 2 つ更新した。**

- 控えは「dev-wave docs は L1.5 の byte 予算が満杯」を制約として引いていたが、
  それは `DW-O02` の話であり本件の制約ではない。**`DW-C01` は L2 節で単節予算 1,000 bytes、
  当時 996 bytes、余白 4 bytes** が真の制約だった (親が予算定数を 0 に落として実測)。
  採用した置換行は改行込み 54 bytes で現行と同じ長さのため、節は 996 bytes のまま変わらない。
- 控えは D517 を引いて「`codex exec --help` に検索の on/off flag は無い」としていたが、
  **`orchestrator/codex_roles/launcher.py` は `-c 'web_search="disabled"'` を既に渡している。**
  移送先の機構は flag ではなく `-c` config として実在する。
  一方 `tools/codex_worker_launch.py` (dev-wave の実行経路) は渡しておらず、
  ambient `~/.codex/config.toml` にも `CODEX_*` 環境変数にも設定が無い。
  F259 の子が実際に検索している挙動と合わせ、**dev-wave 側は CLI 既定 (有効) のまま**と確定した。

**因果は F259 を出した実物の走行で再現した。** stdout 99 行中 22 行が `web_search` item の
`id` 重複、同 attempt の rollout 259 行は重複 0 件。現行コードで再生し、反実仮想
(`stdout_invalid=False`) で `evidence_status=complete` になることまで確認した。
**stdout 経路だけを直せば足りる**ことの根拠である。

**この wave 自身が子の全損を 1 回起こし、それが新しい失敗型だった。** 段 3 のレンズ B が
`codex_exit_code=0` / `validator_rc=0` / 成果物 7,543 bytes 健在のまま捨てられ、
原因は重複 key ではなく非 NFC だった。詳細は {{F:nonnfc-fixture-kills-readers}}。

**段 3・段 6 の敵対検証が blocker 4 件と must-fix 10 件を出し、すべて解消した。**
とくに次の 3 件は親が見落としていたか、親の誤りを正したものである。

- **last-wins 正規化で D68 型の隠蔽が成立していた。** レンズ A が
  `{"type":"thread.started","thread_id":"不正","thread_id":"正当"}` 等の反例を構成した。
  受け取り口の許容条件を T1〜T4 へ締めた ({{D:stdout-duplicate-key-admission}})。
- **`_evidence_status` の優先順位が旧 receipt を壊していた。** 実装は致命的 issue を
  `missing` より先に判定しており、旧 writer が `missing` と記録した receipt を
  `invalid` と再計算して `check-receipt` が拒否する。親が旧実装と新実装へ同一状態を与えて
  実測確定し、元の優先順位へ戻した。両レンズが独立に指摘した。
- **`tools/t189_task_catalog.py` の consumer 取り残し。** `SUPPORTED_RECEIPT_SCHEMAS` が
  `{3, 4}` のままで、v5 receipt が catalog から静かに落ちる。親が閉包検索で発見し、
  レンズ B が「これが唯一の取り残された production consumer」と閉包で確認した。

**親の brief の実測を 4 点訂正した。** (1) 「invalid の唯一の原因は `stdout_invalid`」は
receipt の field 集合からは導けない (`payload_decoy` が反例)。直接再生へ置き換えた。
(2) M7 の根拠を argv 単独から ambient 設定・環境変数・実挙動の 3 経路へ差し替えた。
(3) rollout に重複 key が無いという観測は 1 attempt の性質であり、rollout を緩めない根拠は
D1149 の evidence payload 境界である。(4) `tools/task_runs/ledger.py` は events 側 parser の
consumer ではない (`.schema` からの import で別関数)。同名 `strict_json_loads` は 3 つ存在する。

**変異 matrix**: baseline PASSED、8 変異すべて KILLED、SURVIVED 0、MISMATCH 0。
初回走は 9 変異で登録し、2 件を erratum として再照準した (`DW-M08`)。

- `t2010.m04-t4-cr` は初回 MISMATCH。CR 検査を消すと 3 node 落ちるのに 1 node しか
  登録していなかった。**期待 node は完全集合**という規則どおり実測 3 node へ訂正し、
  再走で KILLED (完全一致) を得た。初回を probe として記録する。
- `t2010.m08-dwc01` (`DW-C01` の docs 行を旧文へ戻す) は初回 SURVIVED。
  原因は検査の穴ではなく、**それを拾う唯一の node
  `test_normative_exact_section_pins_accept_real_repo` が growth hold で恒久 skip**
  されていること (解除条件はユーザーの明示命令のみ、2026-08-12 の裁定)。
  実効 gate は `tools/check_docs.py` 単独走であり、親が直接測った —
  docs を旧文へ戻すと rc=1 で「`DW-C01` の節全体が exact 契約と不一致」1 件を出す。
  逆向き (literal 側を壊す) も測ったが 332 node が落ちる過剰決定で、`DW-M03` により
  単独変異の証拠から外す。一時変異は 2 件とも復元し、作業ツリーの clean を確認した。

**焦点走で赤 103 件と 3 件を見たが、どちらも負荷起因の偽赤だった。** 判定は署名一致では
行っていない — 負荷平均 16.56 のとき `finalization` の 0.1 秒境界検査が落ち、
3.77 へ下がると同じ file が 25 passed で通ることを実測した。実装差分には帰属しない。

**pytest は子が 1 node も実走できなかった** (`qstat -Q` preflight rc=1、runner rc=16、child 未起動)。
段 5 の実装子・段 6 の fix 子とも「実装済み・未実走」と正直に申告し、
**焦点走はすべて親が login node で実測した。**

**scope 外として裁定パッケージへ返すもの 2 件。**
`-c web_search` の既定 off 配線は D1149 が「段ごとに既定無効 (F263 案 2)」を明示的に却下しており、
親の一存で入れない ({{T:websearch-default-off-wiring}})。
非 NFC 地雷の恒久対処は別 gate で D1149 の射程外 ({{T:nonnfc-landmine-permanent-fix}})。

## 次の一手差分

### 完了

- [T-2010] D1149 を実装した。受け取り口を T1〜T4 で分け、成果物側の重複 key 拒否は
  1 bit も緩めていない。負例 3 本と正例 1 本、rollout 負例 1 本で固定し、
  変異 8/8 KILLED で裏を取った。`evidence_status=invalid` の理由は receipt の
  `evidence_issues` へ残る。`DW-C01` は既裁定 [T-981] と整合する文言へ改めた。
  remaining: none
  base: 33064b4cd951bae30b36e479f154ffc3bb5d850a0dd5f5a31d34b4437402a65e

### 更新

- [T-981] **P2・裁定済み・部分実装**: 「`evidence_status=invalid` の理由を receipt へ記録する」は
  本 wave で実装した (schema v5 の `evidence_issues`)。**残るのは「consult / review 段の
  Web 検索を既定 off にし、必要な段だけ明示的に有効化する」の配線だけ**である。
  移送先の機構は実在する (`orchestrator/codex_roles/launcher.py` の `-c 'web_search="disabled"'`)。
  ただし D1149 が「段ごとに既定無効 (F263 案 2)」を却下しているため、
  この残件の実装可否は {{T:websearch-default-off-wiring}} でユーザー裁定へ返す。
  base: f1a48fdc40ad729f9747d44008d6278024d8732c20f247144f6723d9ca92d3b7

### 新規

- {{T:websearch-default-off-wiring}} **P2・新規・ユーザー裁定待ち**:
  `tools/codex_worker_launch.py` へ `-c web_search=<既定 disabled>` を配線するか。
  **D1149 は「段ごとに既定無効にする (F263 案 2)」を明示的に却下している**一方、
  既裁定 [T-981] は「既定 off、必要な段だけ明示的に有効化」を定めており、両者は衝突しうる。
  現況は dev-wave の実行経路が `-c web_search` を渡さず CLI 既定 (有効) のままで、
  ambient 設定にも環境変数にも指定が無い (親が 3 経路で実測)。
  移送先の機構は `orchestrator/codex_roles/launcher.py` に実在する。
  **どちらの裁定が優先するかを決めてほしい。** 実装するなら実装面のため Codex `role=author` が要る。
- {{T:nonnfc-landmine-permanent-fix}} **P2・新規・ユーザー裁定待ち**:
  {{F:nonnfc-fixture-kills-readers}} の恒久対処を決める。
  repo 内の意図的な非 NFC fixture を codex 子が**読むだけ**で成果物が全損する。
  候補は (a) fixture を実行時合成へ変え repo 内 bytes を NFC に保つ、
  (b) rollout の NFC 検査を tool 出力の記録に限って緩める、
  (c) 恒久的に prompt へ行番号回避を書き続ける (現況の運用回避)。
  **(b) は evidence の健全性検査を緩める方向であり規律 2 の面に触れる。**
  親の推奨は (a) — 検査を 1 つも緩めず地雷だけを消せる。実装面のため Codex `role=author` が要る。
- {{T:growth-hold-hides-exact-pin-gate}} **P3・新規**:
  `DW-C01` の docs 行を旧文へ戻す変異が変異 matrix で SURVIVED した。
  原因は `test_normative_exact_section_pins_accept_real_repo` が growth hold で
  恒久 skip されていることで、**docs と exact literal の束縛は pytest ではなく
  `tools/check_docs.py` の単独走だけが担っている**。同型の pin が他にもあるかを棚卸しし、
  変異 matrix が構造的に見えない gate の一覧を作る。
  hold の解除はユーザー明示命令のみなので**解除は提案しない** — 見えない範囲を明示するだけ。
