---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2670-merge-provenance-position
seq: 2
---

## {{D:merge-history-provenance-after-commit}}. 受入前 merge 段の全史 provenance 監査は merge commit の作成後に走らせ、赤でも merge commit を保持する

**決定:** `tools/dev_wave_wait.py acceptance` の受入前 merge 段で、全史 provenance 監査
(`check_ai_provenance.py` の既定 authoritative 監査、stage `merge-history-provenance`) を
`git merge --no-ff --no-commit main` の直後から **`git commit` の後 (HEAD の pin 取得直後・
commit message の事後検査の前)** へ移す。監査の argv・stage 名・診断理由は変えない。
HEAD が merge commit になるので、選択集合 `{policy} ∪ rev-list(policy..HEAD)` に取り込んだ
main の commit と merge commit 自身が入る。D2044 項 5 の実装であり、D908 が前提にした
「取り込み後の監査が取り込みの作った違反を捕まえる」をこの位置で初めて成立させる。

中止・後始末の契約は同じ変更単位で次のとおり定める。

- `merge_pending` (未完了 merge の abort 権限) の窓は従来どおり `git merge` 開始から `git commit`
  成功までとし、監査成功後まで延ばさない。commit 後の監査赤では `git merge --abort` を呼ばない
  (MERGE_HEAD は無く abort 対象が無い)。
- 監査赤では **merge commit を保持**し、所有する lease (ACQUIRED / UNKNOWN) を解放し、受入 command を
  投入せず、receipt を書かず、理由本文を呼び手へ返す (rc=70、source_rc、stage)。HELD_SELF の
  lease は従来どおり解放しない。
- claim 前の全史監査 (`preclaim-history-provenance`) と、MERGE_HEAD を前提にする
  `--message-file` 検査 (`merge-message-provenance`、commit 前) は不変。
- 監査赤後の manager の次手: (1) 理由本文・違反 SHA・保持した merge commit SHA を記録し、lease の
  解放結果を確認して同じ投入を止める。(2) main 由来 / merge 自身 / 実行不能 (infra) を切り分け、
  既存契約に従って是正を wave の履歴へ反映する (main の前進訂正 commit は親が `git merge` で
  取り込む。既知違反登録が要るならユーザー裁定へ返す)。(3) wave HEAD の authoritative 監査が緑に
  なってから受入を再投入し、新しい受領証で land する。
- 一時 merge message の削除は従来どおり試行であり (OSError は握り潰す)、削除完了を保証しない。

**受理集合の変化 (段 6 レビューが指摘、親が実 checker の probe で実測):**

1. 縮小: main にだけ存在する provenance 違反 commit を持つ取り込みは、受入投入前に赤になる
   (旧位置は rc=0 で wave tip の commit しか見ず、新位置は rc=1 で当該 commit を名指す)。
2. 解消: main 側が `tools/known_violations/` の entry を追加していた取り込みは、旧位置では registry
   loader の index-vs-HEAD 照合が `index-only member does not match HEAD` の data error (rc=2、
   F206 の再発 2026-09-01 の型) で必ず止まり、親が `--ff-only` で main を揃えてから再投入するしか
   なかった。新位置では merge commit に entry が入るので HEAD / index / worktree が一致し、台帳の
   内容規則と append-only 履歴検査がそのまま適用される (probe では main の full 監査と同じ
   「新規違反なし」rc=0)。checker と台帳の規則は変えていない。旧位置の偶発的拒否を保存するために
   監査を 2 重に置く案は、被覆の増分が無く費用だけ増えるので採らない。

**理由:**
- `--no-commit` 中の HEAD は wave tip のままで、旧位置の監査の選択集合は claim 前の監査と同一
  だった。F365 の説明文「その merge 自身が新しく作る違反を捕まえる」は実装では成立せず、
  main にだけ存在する違反 commit は受入全走の後、land の監査で初めて赤になっていた。
- checker には HEAD 以外を pin する CLI が無く、`--range` は authoritative でない
  (scope 規則の epoch 適用差、既知違反台帳の append-only 検査なし、commit 前は merge commit
  自身を含まない)。同じ監査を保ったまま被覆を広げる位置は commit 後しかない。
- 赤でも merge commit を保持するのは、巻き戻し (`git reset --merge <premerge>`) が捨てた
  merge commit を branch と worktree HEAD の reflog に残し、`tools/dev_wave_cleanup.py` の
  reflog 到達性検査 (D1233 の喪失閉包) が自己撤去を拒むためである。reflog を消して回避するのは
  掃除側の防壁の迂回になる。保持される終端状態 (merge commit が残り land できない) は変更前でも
  受入全走の後に land で止まったときと同じであり、本決定は検出を受入投入前へ早めるだけで新しい
  状態を作らない。
- preclaim の受領証は bindings (checker bytes・環境・registry・属性等の 13 項目、D2045) が
  一致するときだけ prefix として再利用され、`tip..HEAD` (main の新 commit と merge commit) が
  差分として監査される。不一致なら全走になるが、どちらでも取り込み分の被覆は変わらない。
- 残る merge commit が land 適格かは、D689 / D731 / D732 の前進 merge 契約 (first-parent 列・
  tested-main の祖先性・main の単調前進・隔離 merge の再演) が別途判定する。2 親であること自体を
  適格の根拠にしない。

**却下した選択肢:**
- 説明文を実装へ合わせる (旧位置を正当化する) — D2044 項 5 が明示的に却下。
- `git reset --merge <premerge sha>` で巻き戻す — reflog 経由で cleanup の喪失閉包に当たる (上記)。
  reflog の entry を消す派生案は掃除側の防壁の迂回。
- checker に `--head <sha>` を足して commit 前に dangling merge commit を監査する — 別設計
  (受領証・registry の HEAD 束縛の見直し) が要り、本件の位置移動とは変更単位が違う。
- `--range HEAD..MERGE_HEAD` で commit 前に監査する — authoritative でなく受理集合が広がりうる。
- `merge_pending` を監査成功後まで延ばす — commit 後は MERGE_HEAD が無く `git merge --abort` が
  失敗して cleanup failure になる (変異 M4 として登録し、負例が殺すことを確認)。
