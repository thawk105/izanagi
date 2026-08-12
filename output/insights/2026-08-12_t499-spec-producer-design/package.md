# 裁定パッケージ — [T-499 後継] 8b oracle spec producer の設計と D302 schema 判断

```text
状態: 設計完了。実装差分ゼロ。durable artifact 0 件。`APPROVED_SPEC_SHA256` は `None` のまま。
authority: 親 (dev-wave-t499-spec-producer-design) の実測 + 段 2 プラン子 + 段 3 敵対 2 本。
起点: 2026-08-12 第 6 束ユーザー裁定 [T-499] Q1 = (b)
  「承認手番は 8b oracle 本走の事前登録が固まるまで待ち、先に producer と schema 再発行の
   設計を作る別タスクとして起票する」
検証: 段 2 プラン (codex sol/max) + 段 3 敵対 2 本 (sol / luna、いずれも max) + 親の独立実測。
  A/B 択一の否認は 3 者独立に一致。
branch: worktree-dev-wave-t499-spec-producer-design (docs + insights のみ)
```

## 結論の要旨

1. **D302 の「据え置き解除か再発行か」は、そのままでは択一になっていない。**
   contract test は schema version で分岐しないため、どちらを選んでも同じ検査が落ちる。
   **親裁定 = 実 semantic delta が無い限り v1 据え置き** (`d302-schema-choice.md` §6)。
2. **より重大な欠陥が 4 件見つかった。** schema version をどちらにしても残る
   (`producer-design.md` §2)。うち最重要は
   **人間承認が機械強制されておらず、AI が bytes・hash・receipt・pin をすべて作れる**こと。
3. **裁定控えの前提 1 件が取り違えだった。** oracle spec の承認経路に
   `_assert_user_commit` の要求は存在しない (`producer-design.md` §1.1)。
4. **親の M7 (T-810 を先例とする) は撤回した。** T-810 の artifact 自身が
   trust root 不在を宣言し、launch には正例が構造的に存在しない。
5. **事前登録 9 項目のうち、ユーザーが実質的に承認できるのは 4 項目だけ**
   (`n` / master seed / block ID / campaign ID)。残りは validator が固定するか、
   active freeze が強制するか、導出できない
   (`preregistration-approval-package-draft.md` §1)。
6. **現在の先行 blocker は `no-approved-spec` ではなく `no-active-ratified-freeze`。**
   spec 承認はこの列の最後尾に近い。

## 裁定を求める項

### Q1. lifecycle gate の受理集合を広げる判断

durable artifact を将来発行するには、`test_s8b_oracle_manifest_contract.py:128-144` の
「両 directory に file 0 件」という条件を置き換える必要がある。置換後の受理集合は
**真に広がる** (0 件 ⊊ {承認された 1 件})。これは規律 2 に関わるため、実装者の裁量ではなく
ユーザーの明示裁定として記録されるべきである。

- **(a)** 3 状態 lifecycle gate (`UNAPPROVED` / `APPROVED` / `CANDIDATE`) への置換を承認し、
  別タスクとして起票する。未承認状態では現行の zero-file 条件をそのまま保つ。
- **(b)** 置換自体を保留し、8b oracle 本走の再開が決まるまで現行の zero-file 条件を維持する。
- **親推奨 = (b)。** 理由: §「先行 blocker」のとおり律速は active ratified freeze v2 であり、
  gate を先に置換しても本走には近づかない。**受理集合を広げる変更は、それが必要になる
  直前に行うのが安全である。** (a) を選ぶ場合も、下の Q2 が先に解けていなければ
  gate だけ広げて trust root が無い状態になる。

### Q2. 人間承認の trust root

現行の code pin も receipt も、同じ実装担当 (AI を含む) がすべて作成できる。
AI が bytes・hash・receipt・pin を作った場合でも値の一致検査はすべて通る。

- **(a)** repo 外の allowlist key による detached signature を導入する。
- **(b)** allowlist 済みの署名 commit が exact spec hash・receipt scope・freeze SHA・
  approval ID を署名し、production loader が検証する。
- **(c)** trust root を導入せず、「承認は staged diff の人間 review という手続きで担保する」と
  明記したうえで、**その限界を成果物へ明示する**。
- **親推奨 = (c) を当面の運用とし、(a)/(b) は 8b 本走の再開が決まった時点で再裁定。**
  理由: 現在 durable artifact は 0 件で pin は `None`、active v2 も不在であり、
  **この欠陥はまだ certified 選択に到達していない。** ただし (c) を選ぶ場合、
  「人間承認を機械確認した」と書いてはならない。書けるのは
  「人間が staged diff を review した」までである。

### Q3. 事前登録の設計選択値 (4 項目)

ユーザーが実質的に決められるのはこの 4 項目だけである。**今この場で決める必要はない** —
最終承認は前提が揃った後の 1 回に限定すべきである (下記 Q4)。

| 項目 | AI 草案 | 備考 |
|---|---|---|
| `n` | `8` | 総試行 `8 × 2 × 6 = 96` 行。純測定時間の下限は `96 × 5 × 5` 秒 = 40 分 |
| `master_seed` | `"s8b-oracle-v2-t499-20260812"` | 結果を見る前に確定すること |
| block ID | `"b0"` | 単一 block 契約により 1 件のみ |
| `campaign_ids` | `{"b0": "s8b-oracle-v2-b0-20260812"}` | repo 全体での衝突検査は未実施 |

### Q4. 承認手番の分割

- **(a)** 「設計選択値の暫定承認」と「最終 exact spec 承認」を分け、前者を今、
  後者を前提 (active v2 freeze / floor / budget / 12 binding / 環境契約 / 5 source hash /
  canonical bytes) が揃った後に行う。
- **(b)** 分割せず、前提が全部揃うまで承認手番を引き続き保留する。
- **親推奨 = (b)。** 理由: 暫定承認しても、`generator_versions` が pin する 5 source が
  変わるたびに再承認が要る。**最終承認はこの 5 source の改修が実質的に止まってからでなければ
  意味を持たない。** 暫定承認は「承認済み」という記録だけを増やし、失効管理の負荷を上げる。

## 記録のみ (択一ではない)

- **`ccbench_pin` に正しい値が 2 つある。** 現 floor protocol は `d706650...`、
  現 submodule は `511c953...`。現在の凍結済み floor と比較する本走は前者、
  floor を後者で再測定して v2 を作る場合は後者と新 binary hash を束縛する。
  **混ぜると binary hash mismatch で本走が止まる。** 選択規則の明文化が要る
  (`preregistration-approval-package-draft.md` §3.4)。
- **誤 binding が one-shot 実走を消費する。** campaign marker 作成
  (`s8b_oracle_driver.py:1333-1345`) が binding 照合 (同 `:1440-1448`) より先に起きる。
  cross-validator を marker 作成前に置く設計が要る (`producer-design.md` §2.4)。
- **oracle の除外理由表は floor の 4 理由からの流用が未承認。** oracle validator は
  形式検査しかしていない。

## 本 wave が行っていないこと

`output/s8b-oracle-spec/` と `output/s8b-oracle-manifest-candidates/` への書込 (0 byte)、
`APPROVED_SPEC_SHA256` の設定、contract test の変更、`SCHEMA_VERSION` の変更、
D302 の変更、実装差分。すべてゼロである。
