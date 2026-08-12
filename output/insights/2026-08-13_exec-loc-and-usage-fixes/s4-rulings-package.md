# 裁定パッケージ — 実行場所分類 wave が scope 外で見つけた real 所見 4 件

本 wave (dev-wave-exec-loc-and-usage-fixes) は 3 点の scope を実装した。
その過程で、**実装せずユーザー裁定へ返すべき real 所見**が 4 件出た。
いずれも独立 2 レンズの敵対検証と親の実測で real と確定している。

---

## R-1. registry の分類を直しても、段 9 の使用量収集は login で永久に blocked のまま

**事実 (親・レンズ A・レンズ B の 3 者一致、親が実コードで確認)**

`tools/collect_wave_usage.py:198` は `site_policy.refuses_heavy_work(site)` だけで `blocked` を決める。
`orchestrator/campaign/site_policy.py:95-97` はこれを site (`PEGASUS_LOGIN` / `PEGASUS_SUSPECT`) の
集合判定として実装しており、**admission registry の class を一切参照しない**。

一方 `docs/decisions.md` の D233 決定 4 の理由文は
「fail-closed を機械化すれば、**分類が済んだ時点で同じ契約のまま収集が始まる**」と書いている。
**この結線は実装されていない。** したがって:

- 分類を `local-ok` にしても、collector は site だけを見て `blocked` を記録し続ける。
- 本 wave が evidence を是正しても、収集が始まるわけではない。

**選択肢**

- **(a) 結線する。** collector が admission registry を読み、対象実行体が `local-ok` なら
  login でも収集する。**受理集合が広がる。** hook・loader・site_policy・collector の
  4 層の契約を 1 つに束ねる設計と、正例・負例の両方が要る。
- **(b) 結線しない。** 収集は計算ノードでのみ行う運用に確定し、D233 の理由文から
  「分類が済んだ時点で収集が始まる」という含意を削除して、実装と説明を一致させる。
- **(c) 据置。** 食い違いを既知として記録だけする (現状。ただし説明は誤ったまま残る)。

**親の推奨: (b)。** 理由: (a) は 4 層の受理集合を同時に広げる新しい admission architecture であり、
本 wave の台帳反映の外である。また収集は D220 により wave 完了 gate ではないので、
計算ノード限定でも運用は回る。説明と実装の食い違いを消すほうが安全側である。
(a) を選ぶなら独立の wave が要る。

---

## R-2. `local-ok` を非 `tools/pegasus/` path へ付けるには、単調性の防壁を変える必要がある

**事実 (親が実コードで確認)**

- `tools/pegasus_admission_registry.py:105-107` — 非 `tools/pegasus/` の `local-ok` で
  registry 全体を `AdmissionRegistryError` にする。
- `hooks/guard_bash.py:270-272` — loader を通っても wrapper が再検証して拒否する。
- `hooks/guard_bash.py:275-288` — sanctioned 投影は `tools/pegasus/` 配下しか作らない。
- 専用 negative test 3 本 (`test_pegasus_registry_loader_rejects_non_pegasus_local_ok`、
  `test_bash_pegasus_entry_lookup_rejects_registry_keys_outside_subtree`、
  `test_bash_non_pegasus_local_ok_corruption_cannot_borrow_sanctioned_allow`)。

この禁止は D175 決定 6 の「適用 path を広げても受理集合は単調に縮むだけ」を成立させている当の機構である。
**entry を registry から削除する案も不採用**: `_NON_PEGASUS_ADMISSION_FALLBACK_PATHS` が
空集合になると `"|".join(...)` が空文字になり `re.compile("")` が全入力に一致するため、
hook 内部例外時に無関係な command まで拒否する (レンズ A が指摘、親が実コードで確認)。

**選択肢**

- **(a) 非 Pegasus exact allowlist を新設する。** 一般の禁止は残したまま、
  名指しした exact path だけを例外にする。negative test 3 本は維持できる。
- **(b) 作らない (現状維持)。** 非 `tools/pegasus/` の実行体は login で走らせない。
- **(c) 対象 tool を `tools/pegasus/` 配下へ移す。** 呼び手の path が全部変わる。

**親の推奨: (b)。** 理由: R-1 のとおり、class を変えても収集は始まらないので、
今 (a) を入れても得られる効果がない。R-1 で (a) を選ぶときに一緒に設計するのが筋である。

---

## R-3. 「分類の測定はユーザー端末の手番」の扱い — 委任はどこまでか

**事実**

- `docs/pegasus-runbook.md` §7.0 と D233 決定 4 は「AI セッション・子エージェント・自動化は
  分類の実測を自分で行わない」と定める。F159 / F160 はその違反の記録である。
- 2026-08-13、ユーザーは「実行場所分類？あなたが適切なところを選んでください」と述べ、
  **分類の選択**を AI へ委任した。その下で別 job が計算ノードで測定を実施した。
- 採られた方法は §7.0 の canonical な専有 scope 手順ではない (計算ノードには per-job cgroup も
  delegation も無く、非 root では専有 scope を作れない。2 ノードで確認)。

**本 wave の扱い**: 委任を「AI が §7.0 の専有測定を自ら実行してよい」へ**拡大解釈しなかった**。
runbook には委任の事実と、測定が非 canonical であることを明記し、手番の規定は変えていない。

**残る問い (ユーザー裁定が要る)**

- (a) この委任は恒久か、この 1 件限りか。
- (b) 計算ノードでの非 canonical 測定を、今後も「分類の補助証拠」として台帳へ入れてよいか。
  入れる場合、`local-ok` の根拠にはならないという線引きを規範へ書くか。
- (c) F159 / F160 の恒久対応 (D233 決定 4) を書き換える必要があるか。

**親の推奨: (b) を明文化する。** 非 canonical 測定は evidence へ残す価値がある
(現に「実行できない」という事実自体が重要な知見である) が、class を軽い側へ倒す根拠には
できない、という線を規範に 1 行入れるのが最小で安全である。

---

## R-4. 分類は argv 単位か path 単位か

**事実**

- §7.0 は「測定が保証するのは記録した argv と入力だけ」と定める ([T-482] 択 (a))。
- 一方 `hooks/guard_bash.py` の admission は **path 粒度**であり、許可された path は任意 argv で通る。
- 今回の測定対象は ledger の既定 argv (`--max-files=25`) だが、
  本番 helper (`tools/collect_wave_usage.py:105`) は既定で `--max-files=1000` を渡す。
  入力母集団は 1,045 file / 1.40 GB なので、**測った argv と本番 argv は別物である**
  (レンズ A の must-fix)。

**選択肢**

- (a) argv 範囲を registry entry に持たせ、範囲外の argv は拒否する。
- (b) 分類対象を「本番 caller が実際に渡す argv」に固定し、それを測る。
- (c) 現状維持 ([T-482] (b)(c) の裁定待ちのまま)。

**親の推奨: (b)。** 測る対象を本番 argv に合わせるのが、path 粒度 admission と
「記録した argv だけ保証」の食い違いを一番安く埋める。(a) は hook 側の parser を
argv 解析まで拡張する話になり大きい。

---

## R-5. 段 1 の前提検査に「機械防壁で禁止されていないか」を明示的に含めるか (段 8 の自己改善候補)

**事実**: 本 wave では、指示された最終状態 (`class = local-ok`) が既存の機械防壁で
**構造的に禁止されている**ことが、段 1 で親の裁量によって拾われた。`DW-S01` は
「承認済み裁定の前提を実測する」と定めるが、この件を拾ったのは実測ではなく**静的な防壁の存在確認**だった。

**選択肢**

- (a) `DW-S01` へ「指示された最終状態が既存の機械防壁・negative test で禁止されていないかを
  先に検索する」を 1 文追加する。
- (b) 追加しない (現状の裁量に任せる)。

**親の推奨: (a)。ただし本 wave では実装できない。** `docs/dev-wave/**` の L1 予算は
`DEV_WAVE_L1_BYTES_MAX = 10_625` に対し現在 10,624 bytes で**余白 1 byte** しかなく、
追記は入らない。既存の安全文を削る置換は自己改善契約が禁じている
(「予算のために安全義務を削除・弱化してはならない」)。したがって契約どおり
**変更を止めてユーザー裁定へ返す**。予算の引き上げは通常の自己改善に含めない独立審査対象である。

## 本 wave で実装したこと (対比のため)

- collector の内側 argv 等号化と rc の fail-closed 化 (受理集合は外側 CLI で狭くなる方向)。
- ledger の replica resolver (同一 `message.id` の複製を 1 回だけ計上。支配関係が付かなければ従来どおり fatal)。
- registry の `reason` / `primary_gate` / `evidence` の是正 (**class は `unknown` 据置**、
  hook の受理 bit は 1 つも変わらない)。
