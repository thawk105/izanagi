# 段 1 brief — [T-639] admission 縮小版の制度化

## 裁定 (確定済み・一次控え §43, 2026-08-08「推奨通りで」)

**[T-639] = 縮小版制度化 — 「未分類はログインで走らせない (計算ノードへ)」の既定だけ機械化。**
admission registry の適用 path を広げる ([T-522] 族の延長)。**全 tool の分類完備は目指さない。**
根拠 = F159 (AI が §7.0 の測定手番を実行) / F160 (未分類 tool をログインで実行) の独立 2 例。

## 段 1 実測 (worktree 6cc3e59a、実編集 → `git checkout --` 復元、復元後 clean)

1. `GB.decide("python3 tools/claude_session_ledger.py --scan", site="PEGASUS_LOGIN")` = `(True, '')`。
   `PEGASUS_SUSPECT` も同じ。**F160 の穴は現在も開いている。**
2. `tools/pegasus/collect_receipt.py` (unknown) と未登録 `tools/pegasus/*` は現に deny。
   `tools/pegasus/fetch_third_party.py` (local-ok) は allow。
3. registry へ `tools/claude_session_ledger.py` を実追加 → loader が `AdmissionRegistryError`、
   hook registry は 0 件へ縮退し **`fetch_third_party.py` まで deny**、`check_docs.py` rc=1。
   非 pegasus path 自体は依然 allow。**loader と hook の両方を直さない限り登録は不可能。**
4. `tools/collect_wave_usage.py` は `site_policy.current_site(require_evidence=True)` で自己 gate し
   login / 証拠不足では `blocked` を記録して collector を呼ばない (F159 恒久対応)。
5. pin 閉包 (`DW-O09`): registry bytes を pin するのは `tools/check_docs.py` の投影検査
   (runbook §7.0 投影表と (path, class, evidence) 集合完全一致) のみ。`FROZEN_MANIFEST` は
   `output/` 配下のみで registry を含まない。producer 出力 bytes は変わらない (`DW-O10` 不成立)。
   runbook unknown 表・実測表・`tools/pegasus/README.md` 宣言表はいずれも
   `tools/pegasus/` 前置の path だけを対象にしており、非 pegasus entry の追加を要求しない。

## 既存被覆の性質検索 (検査を増やす wave の義務)

「repo 内の非 `tools/pegasus/` 実行体を、実行場所の分類が無いことを理由にログインノードで拒否する」
機構は現在ゼロ (実測 1)。`_NON_PEGASUS_SANCTIONED_PATHS` は逆向き (許可) の 2 本のみ。
**純増検出力 = registry に登録した非 pegasus path の login/suspect 実行を hook が拒否する。**

## scope (成果物影響 = `DW-G05`)

- **S1 loader**: `_validated_document` の path 検証を「canonical な repo 相対 path」へ一般化する
  (`tools/pegasus/` 前置強制を撤廃、`..`・絶対 path・制御文字・後置 `/` は従来どおり拒否)。
  *不実装なら*: 非 pegasus tool を分類できず、未分類実行がログインの共有 cgroup を圧迫して
  並走計測に外乱を与える (F3 型)。計測値の環境タグが同一でも実効条件が揃わず、campaign の
  比較値が汚染されうる。
- **S2 hook**: `_pegasus_admission_entry` を「登録があれば path を問わず entry。未登録は
  `tools/pegasus/` 配下だけ `_PEGASUS_UNREGISTERED`、他は `None`」へ。deny は admission 判定が
  sanctioned 早期許可より前 (現状の順序) のまま。*不実装なら*: S1 だけでは hook が読まず、
  registry が飾りになる。
- **S3 registry**: `tools/claude_session_ledger.py` = `unknown` を 1 件登録する
  (`reason`/`primary_gate`/`evidence` は既存 unknown 群と同型)。*不実装なら*: F160 の実例が
  塞がらず、[T-638] の測定手番が済むまで規律だけが防壁のまま。
- **S4 docs**: runbook §7.0 投影表へ 1 行、同節 admission 段落と `hooks/README.md` の
  「`tools/pegasus/` 配下の admission」という射程文を「registry が登録した path」へ改訂。
  *不実装なら*: `check_docs` が赤 (投影表の集合一致)、かつ正本記述が実装と食い違う。
- **S5 tests**: 非 pegasus 登録 path の deny (login / suspect)、未登録非 pegasus path の allow
  (過剰拒否の正例)、loader の非 pegasus path 受理と非 canonical 拒否、縮退時挙動 (P2)。

## 不変条件 (緩めない)

- `unknown` は `dispatch-required` と同じに扱う。`local-ok` へ倒す変更は本 wave では作らない。
- `legacy-admitted` を他 entry の許可根拠に流用しない。grandfather は当該 4 本限り。
- **分類の実測は行わない** — §7.0 の測定手番はユーザー手番 ([T-638])。AI は測らない (F159)。
- `tools/pegasus/` 配下の「未登録 = deny」閉包は撤廃しない (現状の deny を狭めない)。
- registry 正本は JSON 1 本。hook と `check_docs` は投影であって正本ではない。

## provisional 裁定 (親の暫定・攻撃対象)

- **(P1) 適用 path の広げ方は「登録された path のみ」**とし、`tools/**` のような prefix 閉包
  (未登録 = deny) は作らない。prefix 閉包は `check_docs.py` 等の日常 tool を全 deny するため、
  分類完備 (ユーザー手番・未了) を前提にしてしまい裁定「完備は目指さない」に反する。
- **(P2) registry load 失敗時の縮退**: 現状 pegasus は全 deny (fail-closed) だが、非 pegasus
  登録 path は allow へ戻る (fail-open 方向)。hook 側に非 pegasus governed path の静的 fallback
  集合を置き、縮退時も deny する。drift は「fallback 集合 == registry の非 pegasus entry 集合」の
  meta-test で固定する。
- **(P3) 登録するのは `tools/claude_session_ledger.py` 1 件のみ。**
  `tools/collect_wave_usage.py` は自己 gate 済み (実測 4) かつ `DW-S09` が段 9 で実行を要求するため
  登録しない。
- **(P4) sanctioned との衝突**: 同一 path が `_NON_PEGASUS_SANCTIONED_PATHS` と非 local-ok entry の
  両方に現れたら deny を優先する。load 時に sanctioned 集合から差し引き、meta-test で固定する。

## 成果物の形

コード 3 file (`tools/pegasus_admission_registry.py`, `hooks/guard_bash.py`,
`tools/pegasus/admission_registry.json`) + docs 2 file + テスト。
実装面は Codex `role=author` が書き、親は brief・裁定・統合・全走・記録・commit のみ。

## 並列分割

- 段 3 レンズ A = 受理集合と fail-closed の退行 (縮退・sanctioned 衝突・prefix 閉包の穴)。
- 段 3 レンズ B = 裁定射程の逸脱 (完備分類への滑り、AI による測定、legacy-admitted 流用) と
  docs 投影の同期。
