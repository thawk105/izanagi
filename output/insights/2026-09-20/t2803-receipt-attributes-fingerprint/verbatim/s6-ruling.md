# 段 6 裁定 — [T-2803] レビュー A / B の所見と plan v3 (fix1) (親、2026-09-20 21:5x JST)

## 所見の裁定

| # | 所見 | 判定 | 反映 |
|---|---|---|---|
| A-M1 | 候補外 dir の untracked `.gitattributes` (nested が root の `-diff` を上書き) が A の監査に効き、B で dir が候補入りしつつ nested が消える遷移で、旧形 (候補集合差で cold) と oracle は rc 1、新形は受領証を再利用して rc 0。段 4 の「既存限界の内側」という分類は判定差を解消しない | **real** | **plan v3 で閉じる。** 候補集合を「root ∪ index path の祖先 dir ∪ **監査で属性が効く path の祖先 dir**」にする。後者は S(head) の merge 全件について「merge と第 1 親の name-only diff」の path の祖先 dir (checker の `--cc` 候補 = 全親 diff の交わり ⊆ 第 1 親 diff なので上位集合、履歴とともに単調増加)。これで包含検査・受領証への候補保存・schema 変更は不要になり撤去する |
| B-B1 | E-1 probe が包含判定を再導出している | real | plan v3 で包含検査そのものが無くなる。probe は実装の `_attribute_fingerprint` (digest) と `_attribute_candidates` (候補) をそのまま呼び、digest 比較だけを判定にする (再導出なし) |
| B-B2 | 変異は exact な `old`/`new` で事前登録し一意性を確認せよ。M-6 は差分の範囲で kill 理由が変わる | real | 親が `mutation-spec-probe.json` に exact 文字列で登録済み (fix1 後に plan v3 の実装へ合わせて再登録、一意性を再確認)。M-6 / M-7 (候補 field) は plan v3 で消える |
| B-B3 | T-neg-4 の破損形は個別 guard の変異検出力と読まない | nit | 記録のみ (T-neg-4 は plan v3 で消える) |
| B-B4 | E-1 は旧 blob の抽出元と一致確認を親の記録に残し、未測定範囲を列挙 | nit | 採用 (insight に記載: 旧 = `f94b61fc8:tools/check_ai_provenance.py` sha256 7c02fb2d…、`e1-*.log` の sha256 行) |
| A その他 | caller 2 箇所追従、除外条件は厳密比較、schema/保存/淘汰は fail-closed | 確認 | plan v3 でも保つ |

## 等価性の論証 (plan v3)

監査で git が属性を読む操作は、merge の `diff-tree --cc -p <merge> -- <path>` (候補 path ごと、combined patch の空判定 = 実装 path の選別) だけである。
non-merge の `diff-tree --name-only`、trailer parse、`rev-list`、message 取得は属性の影響を受けない。pickaxe (`log -S`、policy / epoch / CAB hit) の
結果は受領証の他の束縛 (policy、scope_epoch、implementation_epoch、cab_hits) として bound 済みで、属性で変われば失効する。

`--cc` の候補 = 全親の name-only diff の交わり ⊆ 第 1 親の name-only diff。よって
`AttrDirs(S) := { 祖先 dir of p | merge m ∈ S, p ∈ diff(parent1(m), m) } ∪ {root}` は、S の監査で git が属性を読む directory の上位集合である。
S(A) ⊆ S(B) (ff-only、同じ policy commit) なので `AttrDirs(S(A)) ⊆ AttrDirs(S(B))`。

候補 `C(H) = root ∪ dirs(index_H) ∪ AttrDirs(S(H))`、digest `New(H)` は C(H) のうち absent 以外の entry (+ info / configured / system / index entry)。
**主張:** `New(A) = New(B)` なら、∀d ∈ AttrDirs(S(A)): `state_A(d) = state_B(d)`。
証明: d ∈ C_A かつ d ∈ C_B。state_A(d) が実在なら entry (d, s) ∈ New(A) = New(B) → state_B(d) = s。state_A(d) が absent なら New(A) に (d, ·) が無く
New(B) にも無い → d ∈ C_B なので state_B(d) = absent。他の入力は digest で一致。∎
よって S(A) の再監査で git が読む属性入力は A 時点と同一。dirs(index) は健全性に不要な過剰近似で、既存テスト (index-only 候補) を保つために残す。
候補集合の包含検査は不要 (index dir の脱落は AttrDirs に無い限り監査に無関係、AttrDirs にあれば C_B にも残る)。

A-M1 の反例: `tools/retired/shared_lines.py` は merge M の第 1 親 diff にある → `tools/retired` ∈ AttrDirs(S(A)) → A で nested `.gitattributes` が実在 entry として
bound → B で消えると digest 不一致 → cold → oracle と一致。段 3 相談 A の M1 (absent → 実在) も同じ dir で cold。

**費用 (実測、login pegasus02、load 11〜16):** `rev-list --parents --merges policy..HEAD` 0.65 秒 (4,369 merge)、`diff-tree --stdin -r --name-only -z --no-renames --always`
(merge 第 1 親 pair) 2.2〜2.4 秒、出力 22.9 MB、unique path 36,359、祖先 dir 3,704。1 走に 1 回計算し publish の再照合へ渡す (bindings の再計算で 2 回にしない)。

## plan v3 (fix1、Codex fix 子、unit worktree で branch `dev-wave-t2803-unit-fix1`)

1. `_attribute_candidates(head, *, policy=None) -> tuple[bytes, ...]` を新設: `policy` が None なら `_policy_commit(head)`。
   `git rev-list --parents --merges <policy>..<head>` と `git rev-list --parents --merges --no-walk <policy>` の行 (`<merge> <p1> <p2> ...`) から
   `"<merge> <p1>\n"` を作り、`git diff-tree --stdin -r --name-only -z --no-renames --always` へ stdin で渡す (bytes、1 process)。NUL 分割し、空 token と
   40/64 hex だけの token (見出し) を除いた path の祖先 dir ごとに `<dir>/.gitattributes` を候補へ加える。root `.gitattributes` と現行の index 由来候補
   (`ls-files --stage` の祖先 dir、index entry の `.gitattributes`) を合わせ、sorted tuple で返す。git 失敗は `RuntimeError` のまま伝播 (呼び手の既存
   except で cold + no publish = fail-closed)。
2. `_attribute_fingerprint(head, *, policy=None) -> str` (返値は文字列に戻す): 候補は `_attribute_candidates` から取り、`working` は absent 以外だけ
   (現行 fix のまま)。`indexed` の束縛は不変。docstring を「候補 = root ∪ index の祖先 dir ∪ 監査で属性が効く merge path の祖先 dir (履歴で単調増加)、absent は
   digest に入れない」に改める。
3. `_receipt_bindings` は `_attribute_fingerprint(head, policy=policy)` を呼び (policy は同関数内の `_policy_commit(head)` を 1 回に共有)、返値は
   `(path, bindings)` に戻す。`_receipt_prefix` の引数・key 集合検査・`attribute_candidates` 復号・包含検査、`_publish_audit_receipt` の候補保存と
   候補再照合、`_audit_history` の `attribute_candidates` 受け渡し、`_RECEIPT_SCHEMA = 2`、`base64` / `zlib` import を**撤去**し、`_RECEIPT_SCHEMA = 1`
   に戻す (受領証 key 集合は元どおり)。publish の bindings 再照合は現行どおり `_receipt_bindings` を再計算する (候補列挙 +3 秒が 2 回になるのを避けるなら
   `state` に digest を渡して比較してもよいが、`current != receipt["bindings"]` の意味を変えない)。
4. テスト: 既存 assertion の `[0]` を元に戻す。T-pos-1 (新 dir 導入 = warm、`_attribute_fingerprint` 同一・`_attribute_candidates` は真に増える)、
   T-pos-2 (候補入り dir の実在 `.gitattributes` = cold)、T-neg-1 (相談 A の M1: 候補脱落 + untracked 出現 = cold、rc 1、merge finding)、
   T-neg-2 (実在 file 削除 = cold)、T-neg-3 (lstat 不能 = cold) を plan v3 の候補で成立させ、**T-neg-6 (レビュー A の反例)** を新設:
   `_attribute_merge_repo(path="tools/retired/shared_lines.py")` → 削除 commit A (Codex author) → untracked root `.gitattributes` =
   `tools/retired/shared_lines.py -diff` と untracked `tools/retired/.gitattributes` = `shared_lines.py diff` → cold で rc 0 (受領証発行、
   `_commit_paths(merge) == []` を assert) → commit B で `tools/retired/README.md` を追加し nested を削除 (root は保持) → 監査は cold で rc 1、
   M の Codex author 欠落 finding、受領証を消した oracle と rc/stdout/stderr 一致。さらに `_attribute_candidates(head)` が `tools/retired/.gitattributes`
   を含むことを直接 assert (履歴由来候補の実在)。T-neg-4 / T-neg-5 (候補 field) は削除。
5. probe `build/probe/t2803_receipt_attr_cold_rate.py`: 新形は `new._attribute_fingerprint(c)` (str) の隣接比較だけを判定にし、候補は
   `new._attribute_candidates(c)` で数える (追加・削除 dir 数)。包含の再導出を削除。

## 変異の事前登録 v2 (fix1 後に exact 文字列で `mutation-spec-probe.json` を更新、一意性を確認)

| ID | 変異 | kill する test | 赤理由 |
|---|---|---|---|
| M-1 | `working` から実在 entry も外す (`if False:`) | `test_additional_attribute_sources_fall_back[untracked]` | untracked root 属性の追加で失効すべきが warm |
| M-2 | absent を再包含 (`if True:`) | T-pos-1 | 新 dir 導入で warm 期待が cold |
| M-3 | unreadable を除外 | T-neg-3 | lstat 不能で cold 期待が warm |
| M-4 | 履歴由来候補を落とす (AttrDirs = ∅、index 由来だけ) | T-neg-1 / T-neg-6 | 候補脱落 dir の属性を見ず warm → 違反を取り落とす |
| EQ-1 | 候補の `sorted(set(...))` (同集合・同順) | なし | 等価、SURVIVED 期待 |

M-4 は T-neg-1 と T-neg-6 の両方で赤になるが理由は同一 (履歴由来候補の欠落)。

## 実測の更新
- E-1: fix1 後の checker で再走 (旧 = `f94b61fc8` blob、新 = fix1 commit の file)。現 patch 版の結果 (旧 25/60、新 0/60) は erratum として残す。
- E-2: fix1 commit を含む wave tip で実施。
