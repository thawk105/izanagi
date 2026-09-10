判定は **NO-GO** です。A-01/A-02/B-01 は意味上閉じましたが、B-02 の操作直前 dispatch が未解決です。pytest・checker・実行系検査は行わず、Git blob と本文の静的照合だけを行いました。

| 所見 ID | closed / partial / regressed | 根拠 (file:line) | 残余があればその内容 |
|---|---|---|---|
| A-01 | **closed** | `60314069^:docs/dev-wave/core.md:107-109`、[core.md:109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/core.md:109)、[operations.md:129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/operations.md:129) | 非成功結果の catch-all は復元済み。ただし成功 status の列挙が `DW-O23` と二重管理になった点は別枠の新規退行。 |
| A-02 | **closed** | [core.md:111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/core.md:111)、[operations.md:129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/operations.md:129)、[dev-wave.md:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/.claude/commands/dev-wave.md:112) | main HEAD・既存 branch・fresh-context 再開・条件再評価は、段 9 の必読閉包を合わせれば保存されている。 |
| A-03 | **partial** | [failures.md:3379](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/failures.md:3379)、[workers.md:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/workers.md:65)、[operations.md:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/operations.md:83)、[spool README:91](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/spool/README.md:91) | `DW-S06-C` という現在形の担い手参照が stale のまま。通常 fold では置換できないため、単なる後続タスク化だけでは閉じない。 |
| B-01 | **closed** | [core.md:111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/core.md:111)、[operations.md:129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/operations.md:129) | 元所見の二義務は回復。ただし status 列挙の二重管理は残る。 |
| B-02 | **partial** | [core.md:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/core.md:5)、[dev-wave.md:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/.claude/commands/dev-wave.md:21)、[dev-wave.md:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/.claude/commands/dev-wave.md:60)、[dev-wave.md:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/.claude/commands/dev-wave.md:84) | wave 全体の規律としての意味は通るが、待ち手生成・通知処理・producer 停止の直前に再読させる dispatch がない。設計択一は未解決。 |
| B-03 | **closed** | [check_docs.py:176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/check_docs.py:176)、[check_docs.py:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/check_docs.py:254)、[commit-msg-2.txt:12](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t597-budget/commit-msg-2.txt:12) | 現在値と 3 gate は整合。段 4 文書の旧数値は歴史的誤記として残る。 |

### A-01 / A-02 / B-01 の逐語照合

削除前 `60314069^:docs/dev-wave/core.md:107-109`：

> 成功は `landed` / `already-landed` だけとし、他結果は `DW-STOP` に従う。stale / lock busy は同じ wave 内へ巻き戻さず、main HEAD と既存 branch、条件再評価を含む fresh-context 再開を報告する。

現在：

> `landed` / `already-landed` 以外は `DW-STOP` に従い、main HEAD と既存 branch を報告する。

義務ごとの対応は次のとおりです。

- 成功集合と全非成功結果の停止：現行 [core.md:111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/core.md:111) で回復。
- stale/busy を同一 wave に巻き戻さない：段 9 で必読の [operations.md:129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/operations.md:129) が `fresh context` を要求。
- 条件再評価：同 [operations.md:130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/operations.md:130) が要求。
- fresh-context 再開の報告：入口終端 [dev-wave.md:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/.claude/commands/dev-wave.md:112) が再開コマンドを要求。
- main HEAD・既存 branch の報告：現行 `DW-S09` が要求。

したがって義務の欠落はありません。ただし現在文は branch 報告を stale/busy だけでなく全非成功結果へ広げています。安全上の弱化ではありません。

一方、`landed` / `already-landed` は [core.md:111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/core.md:111) と [operations.md:129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/operations.md:129) の二箇所で管理されています。現在値は一致しますが、Sup-3 が消そうとした drift 面を再作成しています。例えば次なら `DW-O23` を単一正本にできます。

```markdown
`DW-O23` の成功結果以外は `DW-STOP` に従い、main HEAD と既存 branch を報告する。
```

### A-03 の spool 判定

canonical を直接編集しなかった判断自体は、[core.md:89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/core.md:89) と [spool README:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/spool/README.md:3) に整合します。

ただし通常 fold が既存 F にできるのは `## 再発` 挿入だけです。[failures fragment 契約:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/spool/failures/README.md:38) このため、後続 wave でも `DW-S06-C` を `DW-O16` へ直接置換できません。

今回は「fix が別の不整合を作った」という F146 自体の再発なので、現在 wave の段 7で F146 への再発 fragmentを追加し、現担い手が `DW-O16` であることを追記するのが契約内です。旧文の置換が必須なら、通常 fold 外の一回限り migration を別途裁定する必要があります。

### B-02 の判定

親の「`DW-C00` は wave 全体の manager 規律」という説明には一理あります。しかし「親は実装面を直接編集しない」は入口 L0 でも再掲され、実装・fix 節でも補強されています。[dev-wave.md:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/.claude/commands/dev-wave.md:34)、[workers.md:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/workers.md:26) 待ち手規約には同等の操作時点の補強がありません。

より良い第 3 案は、文を `DW-C00` に保ったまま、次の条件 dispatch を追加することです。

> 背景 producer／待ち手の生成・再利用・停止、通知処理、待ち条件作成の直前に `DW-C00` を再読する。

これなら非 Codex の land loop にも届き、wave 開始時だけという弱点も消えます。新しい `DW-O24` へ移す案は operations が現在 99 bytes しか余っておらず、186-byte 規約をそのまま収容できません。また条件表を増やす場合は、ハードコードされた [check_docs.py:478](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/check_docs.py:478) と対応テストも同時変更が必要です。

### B-03 の再計数

| 文書 | 現在 | cap | 余白 |
|---|---:|---:|---:|
| core | 8,588 | 9,600 | 1,012 |
| workers | 4,575 | 5,000 | 425 |
| mutation | 3,674 | 3,750 | 76 |
| operations | 8,301 | 8,400 | 99 |
| 合計 | **25,138** | **25,200** | **62** |

3 gate はすべて緑です。

- 個別 cap：4 文書すべて範囲内。
- aggregate：25,138 ≤ 25,200。
- cap 総和：26,750 ≤ 25,200 × 110% = 27,720。

### 新しい退行

fix commit の変更は `core.md` の 1 行だけです。新しい実挙動上の破壊は見つかりませんが、成功 status 集合の二重管理を復活させた点は新しい保守上の退行です。byte gate は壊していません。

## 総括

- 対象 6 所見：**closed 4 / partial 2 / regressed 0**
- 別枠の新規退行：**1**（成功 status 集合の二重管理）
- land 判定：**NO-GO**

理由は、must-fix の B-02 が未解決で、親自身も置き場所を裁定へ戻しているためです。A-03 は nit で単独では blocker ではありません。