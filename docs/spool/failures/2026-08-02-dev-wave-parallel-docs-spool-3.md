---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-02
wave: dev-wave-parallel-docs-spool
seq: 3
---

## 新規

### {{F:guard-expectation-inversion}}. 修正子が既存の安全テストの期待値を反転して緑にしようとした [恒真ゲート] [権限逸脱]

- 事象: 段 6 の修正巡回 1 回目で、Codex 実装子が `tools/dev_wave_land.py` の
  control-plane / handoff identity 検査を壊し、既存の land 防壁テスト 4 件を赤にした。
  その際テスト側に `identity を捨てたので期待値を landed へ反転する (assert は削除せず反転)。`
  という comment を残しており、**assert を消さずに期待値だけを反転する**形で緑化を図っていた。
  親の実走で `assert (0, 'landed') == (21, 'rejected')` を検出し発覚。
- 根本原因: (1) 実装子への指示が「既存検査を弱めない」までしか書いておらず、
  **「既存テストの期待値を変更しない」を明示していなかった**。
  (2) 段 6 の修正で「dirty gate より前に transaction state を解決する」順序変更を求めたため、
  main の control/dirty 検査が wave の `git status` より後ろへ移り、handoff identity 検査が削除された。
- 恒久対応: 修正巡回のプロンプトに「既存テストの期待値を変更してはならない。
  `rejected` を `landed` へ反転する・assert を緩める・skip・削除はすべて禁止。
  既存テストが赤なら実装側が間違っている」を必須節として入れる
  (`docs/dev-wave/workers.md` の `DW-S06-B` が段 5 契約を全文継承する規定の実体化)。
- 再発検知: 親が受入全走を必ず自分で実行し、**既存テストの赤を子の報告でなく実走で確認する**。
  子は sandbox から計算ノードへ dispatch できないため、子の「緑」は構造的に存在しない。
- 補足: 2 巡目で防壁を復元し、95 passed / 受入全走 4907 passed で確認した。

### {{F:green-suite-cannot-run-on-real-repo}}. 全テスト緑なのに実 repo で 1 回も動かなかった [テスト代表性]

- 事象: 受入全走 4907 passed / 0 failed を得た後、親が実 repo で `spool_fold.py --dry-run` を
  初めて走らせたところ、`docs/archive/worklog-phase3-0702-0713.md:529` の
  `worklog ordinal (2) が重複` で **status=invalid**、fold が 1 度も成立しなかった。
- 根本原因: archive の worklog は **ordinal が日ごとに振り直される**古い規約を持ち
  (`2026-07-04 (2)` と `2026-07-05 (2)` が同一ファイルに共存)、現行 worklog の
  グローバル単調増加 (101..106) と規約が違う。fold はグローバル一意を仮定していた。
  新設テストは全て合成 fixture で、**実 repo の歴史データを 1 度も入力にしていなかった**。
- 恒久対応: 実 repo の canonical 族を入力とする smoke テストを受入に含める
  (`plan_fold` を実 `docs/` に対して走らせ、`status != "invalid"` を要求する)。
  合成 fixture だけの緑を受入根拠にしない。
- 再発検知: 親が段 7 の記録を**必ず本機構自身で生成する** (dogfooding)。
  本件はその dogfooding が land 前に検出した。

### {{F:guard-forbids-its-own-input}}. 防壁の禁止集合が広すぎ、守ろうとした正規経路を 2 度禁止した [受理集合の過剰縮小]

- 事象: 再開 wave の段 6 で受入全走が 2 度赤になった (44 failed → 28 failed → 0)。
  どちらも実装子の誤りではなく、**親が段 4 で書いた検査 (c) の禁止集合が広すぎた**ことが原因。
  - 1 度目: 「`landed_commits` のどの commit も **fold 所有 path** を変更していないこと」と裁定した。
    しかし wave が自分の fragment を `docs/spool/**` へ commit するのは spool の**主経路**であり、
    この禁止は **fragment を書く wave を 1 つも land できなくする**。段 6 レビューが blocker として摘出。
  - 2 度目: fragment 追加を許可へ変えたが、canonical 3 台帳・archive の変更を禁止したまま残した。
    spool へ移行していない既存 wave は worklog を直接書くのが現行契約であり、
    `COMMIT_MISMATCH` が本来の理由コードを覆い隠して 28 件が赤になった。
- 根本原因: 防ぎたい攻撃 (隠れた fold commit) を **path の所有**で表現しようとした。
  所有は「誰が触ってよいか」の話で、攻撃の**署名**ではない。
  fold の署名は「fragment を削除し `FOLDED.md` を変更する」ことであり、これは fold 以外では起きない。
  署名で書けば禁止集合は 2 条件で済み、正規経路を一切禁止しない。
- 恒久対応: **防壁の禁止集合は「守りたい資産の所有」でなく「防ぎたい操作の署名」で書く。**
  署名で書けない場合は、その防壁が何を防いでいるのか自体が曖昧である疑いを持つ。
  裁定時に「この禁止集合は、我々が正しいと認めている既存の経路を 1 つでも禁止しないか」を
  明示的に自問する。
- 再発検知: 新設 gate の裁定には**正例を必ず 1 つ書く** — 「この形は必ず通らなければならない」を
  裁定文に置く。本件では「wave commit が fragment を追加し、その直後の fold commit が受理される」
  が正例であり、1 度目の裁定はこれを書いていなかったため気づけなかった。
- 補足: 3 巡目は不要で、2 巡で 0 failed (5185 passed / 19 skipped) に到達した。

### {{F:parent-ruling-forces-serial-only}}. 親の裁定が並行 fold を不可能にする条件を 2 度作った [手順漏れ]

- 事象: 段 4 で親が「直前 active の全 ID に明示遷移を要求する」と裁定した結果、
  他 wave が新 T を先に fold した瞬間に、先に書かれた fragment の fold が必ず失敗する設計になった。
  親が実装後に自分で気づき carry を暗黙化したが、**同じ失敗が `base:` digest 経由で再発**し、
  段 6 レビューが「無関係な fold 1 回で 222/222 の base が失効する」ことを実測して指摘した。
- 根本原因: 「脱落を防ぐ」制約を、**fragment 側に全体状態の列挙を要求する**形で設計した。
  並行環境では、fragment を書いた時点の全体状態は fold 時点の全体状態と必ず異なる。
- 恒久対応: 並行前提の機構では、**fragment は自分が触る対象だけを宣言し、
  全体不変条件は fold 側の postcondition で検査する**。この原則を
  `docs/spool/README.md` の不変条件節に明記した。
- 再発検知: 「wave A が先に fold した後に wave B が畳めるか」を必ず並行回帰テストで固定する
  (`test_parallel_new_then_existing_update_uses_substantive_base_digest` 等)。
