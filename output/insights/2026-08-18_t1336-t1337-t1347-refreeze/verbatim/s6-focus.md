## 総括

| 所見 | 判定 | 根拠 |
|---|---|---|
| RA-1 | `partial` | 記入禁止は追加されたが、値セルは保護対象外で、任意の非空 canonical JSON は `FILLED` になる。[8b:476](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8b-descriptor-design.md:476)、[8c:157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:157)、[判定器:806](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/campaign/s8c_preregistration.py:806)、[判定器:1727](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/campaign/s8c_preregistration.py:1727) |
| RA-2 | `closed` | 登録 `n` と観測反復数の exact 一致、全 cell の集合一致が両文書に入った。[8b:469](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8b-descriptor-design.md:469)、[8c:224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:224) |
| RA-3 | `closed` | exact 列挙、信頼側分類、性能出力外の証拠、出力読取り前の確定、create-only 受領証がすべて要求された。[8b:529](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8b-descriptor-design.md:529) |
| RA-4 | `closed` | canonical path、初期 hash、freeze identity を key とする exclusive-create、第二 root の全履歴拒否が規範化された。[8b:536](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8b-descriptor-design.md:536) |
| RA-5 | `partial` | nonce 例外は削除されたが、「provider へ送る bytes」と transport metadata を除いた「比較対象 bytes」の境界が一意でない。[8c:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:96) |
| RA-6 | `closed` | §7 項 3 の floor 部分と §9 前提段落の resume 部分だけが明示的に読み替えられ、他の凍結項目は維持された。[8b:426](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8b-descriptor-design.md:426) |
| RA-7 | `closed` | 旧値を変更せず、再開条件と報告義務の正本ではないことを保護本文が明記した。[8c:164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:164)、[8c:191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:191) |
| RB-1 | `partial` | 構造的限界は正確に記録されたが、g6 は依然として改訂を承認した決定へ束縛されず、record 単体から権限を証明できない。[8c:319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:319)、[g6:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/output/s8c-preregistration/condition-freeze/condition-freeze.v1.g6.json:1) |
| RB-2 | `closed` | RA-7 と同じ保護本文により、残存値の権威性が明示的に否定された。[8c:164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:164) |
| RB-3 | `partial` | 欠落は明記されたが、g6 の保護 preimage は依然として 8b bytes を含まない。[8c:329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:329)、[判定器:1272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/campaign/s8c_preregistration.py:1272) |

### Freeze record 照合

現在の 8c 文書と証拠契約から構成 hash を再導出し、保護 preimage を標準 JSON 規則で独立計算した。

- 再計算値: `00d5acf450168be41d83019ddffa3a979f1537668ca79d934492fbff63f0d8d6`
- g6 記録値: 同値
- 4 構成 hash と 12 個の条件別 hash: すべて現文書と一致
- g5 bytes hash と `supersedes_sha256`: `8980803794d858d81e69325e98a8bce6ef9c4da7d65cbab89680dbfd09b7466b` で一致

したがって g6 は fix 後の最新 8c 文書から再生成されている。[計算式:191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/campaign/s8c_preregistration.py:191)、[g6:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/output/s8c-preregistration/condition-freeze/condition-freeze.v1.g6.json:1)

### 段 4 不変条件

- correctness gate と build 分離の旧 bytes は不変で、production code の差分もない。[8b:201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8b-descriptor-design.md:201)
- §5 は欄名 1 行だけが変わり、値セルと既存 prose は不変。[8c:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:183)
- 8b の旧 35,136 bytes は current file の同長 prefix と byte 同一。変更は §10 の末尾追記だけ。
- 追加行の結合文字、禁止された三語はいずれも 0 件。`git diff --check` も無出力。
- pytest は実行していない。

### RF-1

- **主張:** 「consumer が実在するまで値を記入しない」は機械関門ではなく、保護対象外の値セルに対する作業規範だけである。現在は条件 7 が非充足なので即時発効しないが、将来の evaluator 更新が数値 schema を明示検査しなければ迂回できる。
- **証拠:** [8c:157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:157)、[8c:267](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:267)、[判定器:806](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/campaign/s8c_preregistration.py:806)
- **深刻度:** blocker
- **成果物影響:** 将来、不正な型・符号・単位・向きの値が `FILLED` となり、consumer の実装次第で公式判定へ到達しうる。
- **推奨:** 数値欄専用 schema validator を発効判定へ置き、条件 7 の充足証拠にも同 validator の production 到達性を必須化する。

### RF-2

- **主張:** 結果構造の個数が不整合である。8b と条件 7 は三つの表または層を要求する一方、起動形は「二層」と呼びながら三要素を列挙する。
- **証拠:** [8b:486](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8b-descriptor-design.md:486)、[8c:224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:224)、[8c:477](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:477)
- **深刻度:** must-fix
- **成果物影響:** selection 評価を公式性能表へ混在させる consumer が実装され、certified 選択の入力境界が曖昧になる。
- **推奨:** 「性能主張は二層、選択評価は独立した第三表」と統一するか、全箇所を明示的な三表契約へ揃える。

### RF-3

- **主張:** byte 同一性の比較境界が自己矛盾気味である。provider へ実際に送る全 bytes の同一を要求した直後に、transport metadata を比較対象外へ分離できるよう読める。
- **証拠:** [8c:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:96)
- **深刻度:** must-fix
- **成果物影響:** provider-visible metadata が対象別ラベルとして残り、対照 arm の非干渉性を偽って認証する余地がある。
- **推奨:** 比較対象を request body、role input、transport header に分解し、provider-visible な各領域について同一性または固定された除外根拠を個別に規定する。

## NO-GO

RA-1 と RA-5 は部分解消に留まり、RB-1 と RB-3 の機械束縛欠落も残る。  
g6 自体は最新文書と一致するが、数値関門と byte 比較境界を閉じるまで land 不可。