---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-20
wave: dev-wave-t2803-provenance-receipt
seq: 2
---

## {{D:receipt-attributes-history-candidates}}. 全史 provenance 監査の受領証の属性 fingerprint は、実在する候補だけを digest にし、候補 directory を「index の祖先」に加えて「監査で属性が効く merge path の祖先 (履歴で単調増加)」から取る (D2045 の改訂)

**決定:** `tools/check_ai_provenance.py` の受領証 (D2045) の属性 fingerprint を次のとおり改める。受領証の schema・key 集合・他の 12 束縛・fail-closed の型は変えない。

- **候補 directory** `C(H)` = repo root ∪ index path の祖先 directory ∪ **S(H) の merge 全件について「merge と第 1 親の name-only diff」に現れる path の祖先 directory**。
  後者は `git rev-list --merges <policy>..<H>` (+ `--no-walk <policy>`) と `git log --diff-merges=first-parent --no-walk=unsorted --stdin --name-only -z --format= --no-renames`
  で列挙する (受領証の lookup と publish 前の再照合で 1 走 2 回。D2169 の path batch `diff-tree --stdin`、D2033 の message batch `log --no-walk=unsorted` と argv 接頭が
  重ならない形)。submodule 内・ignored 出力・tracked file の無い directory の走査はしない。
- **digest** は候補のうち lstat が absent を返した entry を含めない。unreadable (errno)、directory、symlink (link 文字列)、regular (sha256) と regular の読取失敗は残す。
  `info/attributes`、`core.attributesFile` (未設定時の XDG / HOME 既定)、system、index entry の `.gitattributes` (mode / oid) の束縛は不変。
- 監査 tip の tree は読まない (履歴 commit 間の name-only diff は読む)。git 失敗は `RuntimeError` のまま呼び手の except に落ち、受領証は使わず発行もしない (cold)。

**論証 (D2045 の「S(A) の判定は 13 項目が一致すれば同一」の属性項目を置き換える):**
監査で git が属性を読む操作は merge の `diff-tree --cc -p <merge> -- <path>` (候補 path ごとの combined patch の空判定) だけである。non-merge の `diff-tree --name-only`、
trailer parse、`rev-list`、message 取得は属性の影響を受けず、pickaxe (`log -S`) の結果は policy / scope_epoch / implementation_epoch / cab_hits として別に束縛される。
`--cc` の候補 = 全親の name-only diff の交わり ⊆ 第 1 親の name-only diff なので、`AttrDirs(S) := {祖先 dir of p | merge m ∈ S, p ∈ diff(parent1(m), m)} ∪ {root}` は
S の監査で属性が読まれる directory の上位集合であり、S(A) ⊆ S(B) (ff-only、同 policy) から `AttrDirs(S(A)) ⊆ AttrDirs(S(B))`。
digest `New(H)` を C(H) の absent 以外の entry (+ 他の入力) とすると、`New(A) = New(B)` ⇒ ∀d ∈ AttrDirs(S(A)): `state_A(d) = state_B(d)`
(実在なら B 側に同じ entry、absent なら B 側に entry が無く d ∈ C_B なので absent)。よって S(A) の再監査で git が読む属性入力は A 時点と同一である。
index 由来の候補は健全性に不要な過剰近似で、既存テスト (index-only path の祖先が候補) を保つために残す。候補集合の包含検査や受領証への候補集合の保存は不要である。

**理由:**
- D2045 の属性 fingerprint は index の全 path の祖先 directory ごとに absent を含めて束縛していたため、新 insight directory を足す commit (直近 60 main first-parent
  commit の 50 %) を跨ぐと失効し、共有 store の直近 8 受領証は同一 checker なのに attributes digest が 8 種すべて異なっていた (land はほぼ毎回 cold、login 88〜113 秒級)。
- absent 候補を外すだけでは、段 3 相談と段 6 レビューが実 Git で構成した 2 つの反例 (候補 dir が index から脱落した後に untracked `.gitattributes` が現れる / 候補外
  dir の untracked `.gitattributes` が root の `-diff` を上書きして監査に効き、後で dir が候補入りしつつ file が消える) で、旧形と受領証なし oracle が rc 1 とする履歴を
  rc 0 で再利用してしまう。候補集合の包含検査 (受領証に候補集合を保存) は前者しか閉じない。監査で属性が効く path の祖先を履歴から加えると両方が digest で cold になる。
- 実測 (attributes 束縛単独の隣接失効指標、同一 60 遷移、独立 clone、旧 = 改訂前 blob / 新 = 改訂後): 旧 25/60 → 新 0/60。これは cold 率・land wall・時間短縮率ではない。
  実機正例 (独立 clone、新 checker、login 1 回ずつ): cold 全史 wall 58.4 秒 / CPU 108 秒 → 新 directory 導入 commit で warm 21.9 秒 / 9.5 秒 → `.gitattributes` 変更で
  cold 62.6 秒 / 96 秒。
- 費用 (login 実測、4,369 merge): `rev-list --merges` 0.65 秒 + `git log --no-walk` 1.7〜3.5 秒 (path 36,359、祖先 dir 3,704) を bindings 計算ごと (1 走 2 回) に追加。
  当該 login 環境の参考実測で、一般の値ではない。

**この決定が保証しないこと:**
- `attr.tree` / `--attr-source`、bare、`GIT_ATTR_*` の全経路は従来どおり束縛しない。errno の揺れは従来どおり不要な失効を生む。
- 既存テスト `test_attribute_fingerprint_is_independent_of_tip` と `test_many_commit_delta_warm_hit` は緑を保つが absent 候補差への感度を失う。
- 他の束縛 (checker sha、registry manifest、CAB hit、環境 partition) による cold は減らない。改訂直後の land は checker sha が変わるので cold。
- 費用は merge 数に比例して増える。混雑時・計算ノード・実 land の wave 間連鎖は未観測。

**却下した選択肢:**
- absent 候補を外すだけ — 上の反例 1 で旧形が拒んだ再利用を新たに許す。
- absent 除外 + 受領証に候補集合を保存して包含検査 (本 wave の初版実装) — 反例 2 を閉じない。受領証も 32 KB 増える。
- 候補列挙を `rev-list --objects` の tree path で取る — 同一 tree oid の path が初出でしか出ず単調でない。
- 候補列挙を `diff-tree --stdin` の merge 第 1 親 pair で取る — 同じ path 集合だが、既存テストが D2169 の path batch の識別子として pin する argv 接頭と重なる。
- 全親の diff (`-m`) — 出力 36 MB / 5〜7 秒で第 1 親 diff (22 MB / 1.7〜3.5 秒) より重く、上位集合としての性質は同じ。
