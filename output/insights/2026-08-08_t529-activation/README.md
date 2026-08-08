# [T-529] 契約世代の活性化権限 — wave 逐語一式 (2026-08-08)

wave = `dev-wave-t529-activation` / branch = `worktree-dev-wave-t529-activation` /
起点 = `6cc3e59a`

worklog の該当エントリが要約の正本。ここは逐語と機械成果物の凍結先である。

## 何をしたか

契約世代の**活性化権限**を実装した。bootstrap fuse を撤去し、pegasus 第 2 世代
(`calibration-94a4b79fa31bba3c.json`) を registry へ登録し、activation record の chain を
正本として active 世代を決める形にした。**第 2 世代は登録しただけで活性化していない** —
初期 record (serial 1) は両 env とも第 1 世代を選び、`lookup("pegasus")` の返り値は
land 前後で不変である。

## 実測

| 項目 | 値 |
|---|---|
| 受入全走 | **7345 passed / 20 skipped / 0 failed** (commit `be9de28d` の 1 つ前 `12028e26` で 2 回、`be9de28d` で 1 回) |
| 変異 run 1 (8 件) | baseline PASSED / KILLED 4 (M3 M5 M6 M8) / SURVIVED 1 (M2 = 登録どおり) / MISMATCH 3 (M1 M4 M9) |
| 変異 run 2 (4 件) | baseline PASSED / KILLED 3 (M1b M4b M9b) / MISMATCH 1 (M10 両層同時) |
| 未登録の SURVIVED | **両走とも 0** |
| 変異の HEAD 束縛 | 両走とも `12028e26` |
| provenance | 1782 件、新規違反なし |

### 変異の読み方 (erratum を含む)

- **M2 (head serial 検査の除去) は SURVIVED が正しい。** 段 6 レンズ C が
  「serial は state hash の入力に含まれるので独立した防壁ではない」と指摘したため、
  kill 期待ではなく診断用の冗長検査として事前登録した。生存はその指摘の実測確認である。
- **run 1 の MISMATCH 3 件は gate の失敗ではなく親の node 帰属の誤り。** run 2 で
  node を訂正したところ 3 件とも KILLED になった。run 1 の台帳は消さず erratum として残す。
- **M1 と M2 は互いを mask していた。** serial が変わる攻撃 (末尾削除・後続注入) は serial 検査が、
  同一 serial の改竄は state hash 検査が拾う。単独変異ではどちらも独立には証明できないため、
  `DW-M02` に従って両層同時変異 (M10) を追加登録した。
- **M10 は 5 件中 4 件が期待どおり落ち、1 件だけ落ちなかった。**
  落ちなかったのは production 層の末尾削除 node で、現行 chain が 1 record しかないため
  「末尾削除 = 空 directory」となり head pin ではなく非空検査が先に拒否する**過剰決定**である。
  `DW-M03` に従い、この node を単独変異の証拠から外す。production 配線自体は同じ M10 が
  後続注入の production node を落としたことで示されている。

## この成果が主張できない範囲

- **「レビュー済み commit に束縛した」とは言えない。** head 定数を Python 側に置いたので
  record の改竄・末尾削除・後続注入は落ちるが、その定数を含む source を reviewed commit と
  照合する検査は汎用の certified 経路には無い (段 6 レンズ C 所見 1)。
  これは本 wave が開けた穴ではなく [T-530] が持つ既存の穴と同じものである。
  **親が段 4 で書いた「既存の source binding が効くので閉じる」という理由づけは誤りだった。**
- **第 2 世代の活性化を実証していない。** 実在素材から作った serial 2 でも、一時 record である
  以上「レビュー済み経路に残る永久 fuse」とは区別できない (段 3 レンズ A)。
  正例は通常の回帰テストとして置き、`DW-G04` の発火証拠に数えていない。
- **全入口が activation receipt 済みとは言えない。** 閉じたのは certified sink
  (`pipeline.evaluate` → `execution_guard`) の最初の書込み前だけである。floor / oracle driver /
  selector / T126 の fork child / PBS wrapper への配線は scope 外。
- **production 層の末尾巻き戻し防御は今日は観測できない** (上記 M10 の過剰決定)。
- **発行から配備までに分裂窓がある。** 発行 tool は record を live directory へ公開するが
  head 定数は更新しないため、head 更新と再起動までは fresh process が fail-closed になる。
  失敗方向は安全側だが quiesce/drain と atomic deployment は無い (段 6 レンズ D 所見 3、partial)。
- **世代遷移の述語 (no-op / skip / downgrade 拒否) は入っていない。** [T-627] の裁定 (c) に従う。

## ファイル

| ファイル | 内容 |
|---|---|
| `s1-brief.md` | 段 1 brief。前提実測 4 件と provisional 裁定 (P1)〜(P4)。**pin 件数 4 は誤りで正しくは 5** |
| `s2-plan.md` | 段 2 プラン起草 (条件付き GO。親の P3 に反対) |
| `s3-lensA.md` | 段 3 レンズ A — 正しさ境界と裁定整合 (NO-GO、must-fix 4) |
| `s3-lensB.md` | 段 3 レンズ B — scope 被覆と実効性 (NO-GO、must-fix 6) |
| `s4-adjudication.md` | **段 4 裁定 (正本)**。裏取り 4 点、plan v2、変異事前登録、裁定パッケージ 4 件 |
| `s5-a.md` / `s5-b.md` | 段 5 実装子 2 単位の報告 |
| `s6-lensC.md` / `s6-lensD.md` | 段 6 敵対レビュー 2 レンズ (NO-GO、must-fix 2 / 7) |
| `s6-fix1.md` | fix 第 1 巡 — **親の scope 記述の矛盾により 1 行も書かずに fail-closed 停止した回** |
| `s6-fix1b.md` | 親が境界を再裁定して再投入した回 (認可済み型の導入と caller 閉包) |
| `s6-fix2.md` 〜 `s6-fix6.md` | fix 第 2〜6 巡 |
| `s6-refocus.md` | 段 6 焦点再レビュー (closed 12 / partial 3 / regressed 0 + 新規 regression 1) |
| `mutation-spec.json` / `mutation-ledger.json` | 変異 run 1 (8 件)。erratum を含む |
| `mutation-spec-v2.json` / `mutation-ledger-v2.json` | 変異 run 2 (両層同時 + node 訂正 3 件) |

## 運用知見

- **pin 閉包の検索は `git grep` を authority にする。** 同じ hash を repo root から
  `grep -rl` すると tracked file を 1 件落とすが、`git grep -l` と部分木指定の `grep -rl` は拾う
  (本 worktree で再現)。`DW-O09` は「hit 0 件を pin なしと結論しない」までしか定めておらず、
  検索コマンド自体の取りこぼしは射程外だった。
- **`/tmp/.git` という空 directory が 7/28 から残っており、ローカル実行のテスト 5 件を
  必ず落とす。** 一時 directory の祖先に `.git` があるかで「repository 外か」を判定するため。
  計算ノードでは一時 directory が別なので出ない。本 wave では削除していない。
- **並行 job がキューを占有すると受入全走が git timeout で偽赤になる。** 実際に 3 件
  (`git log` / `git cat-file` の 15 秒 timeout) を経験し、キューを空けた単独実行で消えた。
