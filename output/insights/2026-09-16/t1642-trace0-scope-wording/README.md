# [T-1642] TRACE=0 検査の射程文言を「必要条件の一つ」へ統一した — 効いたのはコメントではなく成果物 JSON の 1 文だった

- 日付: 2026-09-16
- wave: dev-wave-t1642-trace0-scope-wording (branch `worktree-dev-wave-t1642-trace0-scope-wording`)
- 起点の裁定: [T-1642] (2026-08-25 ユーザー裁定、/rulings 全件の択 (c))。成果物側の文言を
  「必要条件の一つ」へ統一する作業を先に行い、別防壁の設計は [T-1644] と同じ閉包でだけ起こす。
  正本 = D780。
- 正本: D780 (射程の文言と別防壁の閉包)、D297 (この検査が与える保証の定義)、
  D774 (隣接する限界の扱い)
- 一次資料: `output/insights/2026-08-25_t1584-trace0-identity-holes.md` (R2 の起票)、
  `output/insights/2026-08-25_t1641-report-binding.md` (束縛の実装)、
  `output/insights/2026-08-25_t1677-trace0-remeasure.md` (統一文言の初出)
- 基準: local main 9d52ef1459fdae5bc97050155b28fce0601d259f
- 実装 commit: 9b4a06d68

## 1. 統一した文言と、統一した場所

D780 決定 1 の逐語は「この検査は D297 の保証を証明するものであり、計測ビルドからの trace
完全除去に対しては必要条件の一つである」であり、「完全除去を証明したと読める記述を残さない」
ことを求める。本 wave が編集したのは次の 3 アンカーだけである。

| # | path | 変更 |
|---|---|---|
| A1 | `tools/check_trace0_preprocess_identity.py:3` | module docstring に射程 (D780 決定 1 の逐語)、解釈の禁止、D297 の compiler 留保を足した |
| A6 | `tools/pegasus/mocc_trace_pilot.sh:1742` | D297 checker の hard gate 説明の直後へ、同じ射程を英語で足した |
| A7 | 同 `:357` と `:426` | artifact classification manifest が書き出す `reason` を `Certifies the TRACE=0 preprocess identity gate.` から、完全除去の証明と読めない 1 文へ置き換えた (2 箇所は同一文字列) |

## 2. 本 wave の実質は A7 である — コメントは成果物に出ない

段 2 のプランは A1 と A6 の 2 箇所で閉じる案だった。段 3 の敵対相談が、
**A1 も A6 もコメントであり、checker report・receipt・job-result のどれにも転記されない**ことと、
`reason` が唯一 artifact classification manifest という成果物 JSON へ出る射程文言であることを
別々のレンズから指摘した。親は A7 を編集対象へ追加した。

D780 が言う「成果物側の文言」に最も直接当たるのはこの 2 行だった。段 1 の親のアンカー表は
`D297` を検索鍵にしていたため、D297 を引用しないこの 2 行を取り逃がしていた
(`Certifies the TRACE=0 preprocess identity gate.` に `D297` の語は無い)。

## 3. 統一の前後で主張の強さが変わった箇所

| アンカー | 変更前 | 変更後 | 強さ |
|---|---|---|---|
| A1 | 同一性検査の処理説明のみ。完全除去との関係は無記載 | D297 の保証を証明し、完全除去には必要条件の一つと明記 | 保証対象は不変。完全除去への外挿を塞ぐ **弱める方向** |
| A6 | 非ゼロなら TRACE=0 実行を止め fallback を許さない (失敗時の強制力) | 同じ強制力を保ち、成功しても完全除去の証明ではないと明記 | 拒否側は不変。成功側の外挿を塞ぐ |
| A7 | `Certifies the TRACE=0 preprocess identity gate.` | 証明対象を D297 の gate に限定し、完全除去に対しては必要条件の一つでしかないと明記 | **実質的に弱まる唯一のアンカー** |

親は段 1 で「A6 だけが弱まる」と見立てたが、段 2・段 3・段 6 の 4 者が独立に
「`hard gate` は失敗時の実行禁止の説明であり、成功時の十分性を述べていない」と判定した。
親の見立ては誤りで、実際に弱まるのは A7 だけである。
**保証対象や受理集合を上げる方向の変更は 1 つも無い。**

## 4. 触らなかったもの (裁定と根拠)

- `GUARANTEE` 定数 (`:38-41`) — D297 が定めた保証名そのもの。値は checker report →
  pilot receipt → job-result へ転写され、`orchestrator/tests/test_check_trace0_preprocess_identity.py:24`
  に literal 複製がある。射程の注記と保証名の変更は別物なので、名前は動かさない。
- `CheckError` docstring (`:62-63`)、`_mocc_trace_include_addition_index` docstring (`:421-425`)、
  `:539-541` のコメント — いずれも失敗の説明と局所例外の説明であり、「通れば規律 1 が満たされる」と
  読ませる文ではない。段 3・段 6 の 4 者が本文を読んで同じ判定に達した。
- checker report の schema (`izanagi-trace0-preprocess-identity/v2`) と field 集合 —
  D780 が求めたのは文言の統一であって新しい束縛ではない。
- 過去の insight・receipt・台帳 — 規律 7 に従い遡及改変しない。

## 5. 実測したこと / していないこと

実測した:

- 受入全走: rc=0、**23961 passed, 68 skipped** (`child-green`、receipt 発行、tested tip
  `50a3a52a24dd09538b14be115df0ba33c021917b`)。
  1 回目の投入は 2 件の非帰属赤で rc=70 だった —
  `orchestrator/tests/test_t1259_qsub_env_delivery_probe.py` の setup で
  `git ls-files --others --exclude-standard -z` が 30 秒 timeout、
  `orchestrator/tests/test_s8c_preregistration_predicates.py` が real-repo flock の deadline 超過。
  どちらも並行する他 wave の受入との競合であり、本 wave の差分 (docstring・コメント・JSON の 1 文) とは
  因果が無い。2 件を単独再走して **269 passed (rc=0)** で非再現を確認し、load の下降局面
  (1 分 22.05 < 5 分 25.55 < 15 分 35.27) で受入を再走して緑にした。

- 焦点走 4 file (`test_check_trace0_preprocess_identity.py`, `test_mocc_trace_job_contract.py`,
  `test_mocc_trace_pair.py`, `test_hooks.py`): rc=0、785 passed, 1 skipped。
  このうち `test_mocc_trace_job_contract.py:76` が pilot の `bash -n` 構文検査を含む
  (実装子の直接実行は `guard_bash` に拒否されたため、親の焦点走が唯一の構文検査である)。
- manifest の validator (`validate_artifact_classification_manifest`) が `reason` に課すのは
  非空・単一行・禁止表現 4 語 (`not derivable` / `cannot derive` / `impossible to derive` /
  `non-derivable`) だけで、literal 照合は無い。新文言はどれにも抵触しない。
- `Certifies the TRACE=0` の repo 全体の出現は編集した 2 行のみ。test に literal pin は 0 件。
- provenance 全史監査 rc=0 (10346 件、新規違反なし)。

していない・主張しない:

- **完全除去の実証はしていない。** 本 wave が閉じたのは文言であって防壁ではない。
  D780 決定 2 の別防壁 (実 compile command・全 TU・link object・trace symbol/data・build receipt の
  結合) は [T-1644] と同じ閉包でだけ設計するという裁定の順序に従い、着手していない。
- **TRACE=0 の再計測はしていない。** checker と pilot の source bytes が変わるため、
  将来の実行が生む receipt の束縛値は変わる。しかし過去の受領証
  (`output/insights/2026-08-26_mocc-trace-pair-receipt.json:90,123` に旧 checker SHA が literal で
  残る) は当時の事実であり、現行コードとの差だけを理由に無効化しない (規律 7)。
- **未知の派生 digest pin の不在は証明していない。** 段 3・段 6 が走査した範囲
  (test fixture、hooks inventory、freeze / preregistration、`.claude`、`.codex`) で
  対象 path または現 SHA の追加一致は見つからなかった、までが言えることである。
- **「残った過大な表現がない」とは報告しない。** 段 6 レビュー A が
  `docs/archive/worklog-phase3-0811-445.md:26` (「規律 1 の機械検証」の直後に 3 本 pass) と
  `output/insights/2026-08-11/t816-fn2-trace-v2/README.md:38` を挙げた。いずれも歴史記録であり、
  後者は同文書 `:120-121` が保証を限定して名乗っている。本文全体では完全除去を主張していないため
  必須訂正とはしないが、見出しと結果だけを引用すれば射程を過大に読める。

## 6. 変異事前登録がゼロである理由

本 wave の実装面差分は文言だけであり、DW-S04 の免除条件 (実装面の差分ゼロ) には当たらない。
それでも登録した変異はゼロである。**文言を守る実効 gate が repo に存在しないためである。**

段 6 レビュー B が独立に走査した結果: placeholder 検査は `tools/check_docs.py` の文書族が対象、
禁止語検査は同 file の operations 本文が対象で、`tools/` 配下の文言の意味には及ばない。
hooks も当該文言を検査しない。したがって `reason` を「十分条件」と書き換える変異を作っても、
殺す gate が無いので SURVIVED にしかならない。DW-M01 は「赤理由が一つに絞れる」変異だけを
登録することを求めるので、登録できる変異が無い。
**その gate を本 wave で新設することは D780 決定 1 と依頼の scope 外である。**
これは免除ではなく「登録可能な変異が存在しない」ことの記録である。

## 7. ユーザー裁定へ返す (scope 外の real 所見)

1. **過去記録の見出しと結果の引用。** `output/insights/2026-08-11/t816-fn2-trace-v2/README.md` は
   §3.1「規律 1 (TRACE=0 側の等価性)」の見出し直下に checker の 3 本 pass を置き、
   `docs/archive/worklog-phase3-0811-445.md:26` も「規律 1 の機械検証」の直後に同じ結果を記録する。
   どちらも本文全体では完全除去を主張していないため親は必須訂正としなかったが、
   段 3・段 6 の 2 者が日付つきの射程注記の追記を推奨した。追記するなら 1 行で閉じられる。
