---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-14
wave: dev-wave-t1994-readonly-snapshot
seq: 2
---

## {{D:userns-dual-guard}}. user namespace を使う保護は capability 落としと userns 作成禁止を両方要求する

**決定:** sealed snapshot の build 子は、seal を終えて compiler を exec する前に、
**bounding set を含む全 capability を落として `PR_SET_NO_NEW_PRIVS` を立て、
さらに `CLONE_NEWUSER` を含む `unshare` / `clone` と `clone3` を seccomp で禁じる。**
どちらか一方だけの構成は採らない。

**理由:**

- identity map した user namespace の中では、process がその namespace で `CAP_DAC_OVERRIDE` を
  持つため、**mode bits による保護が効かない。** 所有者が `chmod 0444` した file へ書けてしまう。
  namespace の外では同じ操作が `EACCES` で落ちることを対照で確かめた。
- D1755 が実装した「判定後の材料再生成の禁止」は `chmod` に依存している。
  したがって user namespace を素朴に導入すると、**守るべき相手である build 子に対してだけ
  その保護が無効になる。** 受理集合を広げる後退であり、絶対規律 2 に触れる。
- **capability を落とすだけでは足りない。** 落とした process でも新しい user namespace を
  作ればその中で capability を取り戻せることを、4 状態を分離した probe で実測した
  ((a) 落とす前は書ける、(b) 落とすと `EACCES`、(c) 新 userns を作るとまた書ける、
  (d) seccomp で禁じると `EACCES` のまま)。
- (d) の状態で通常の `fork` / `execve` / 孫 process の生成はすべて成功する。
  `clone3` を `ENOSYS` で落としても glibc 2.35 は `clone` へ fallback することを ptrace で実測した。
  **この fallback は glibc 2.35 で測った事実であり、他の libc へ一般化しない。**

**却下した選択肢:**

- **capability 落としだけ** — 新しい user namespace を作って取り戻せる ((c) で実測)。
- **seccomp だけ** — 最初の namespace で既に持っている capability を落とせない。
- **mode bits に頼り続ける** — namespace の中では効かない。

## {{D:sealed-private-spine}}. sealed の root view は `/` 直下に private tmpfs を置き、兄弟を列挙しない

**決定:** sealed snapshot の子の view は、**`/` 直下の component に private tmpfs を被せ、
source までの spine だけを再作成し、共有すべき枝だけを overmount 前に確保した fd から
bind で戻す**形で作る。**兄弟 entry を列挙しない。**

**理由:**

- **祖先を元の inode へ bind すると、外側 namespace からの rename を防げない。**
  mount は dentry に付くので、親が祖先を rename して同じ名前で B を置くと、
  子の絶対 path 解決が B を辿る。攻撃テストが「保護なしなら B が見える」対照つきで実走して捕まえた。
- **兄弟 entry を列挙する構成は成立しない。** この計算機の `/tmp` には 145,596 entry あり、
  列挙から `os.open` までの間に他 job が消した entry に当たって必ず `ENOENT` になる。
  仮に race しなくても、その回数の bind mount は所要にも mount 数の上限にも収まらない。
- **`/` 直下でなければならない。** その directory を rename するには `/` への書込みが要り、
  非特権の所有者は持たない。実際に攻撃テストが `Permission denied: '/tmp' -> '/tmp-moved'` を観測した。
- mount 呼出しは spine の深さ + 共有枝の数だけで、兄弟 entry 数に依存しない。

**却下した選択肢:**

- **全兄弟を bind で戻す** — churn する directory を列挙する設計であり、上記のとおり成立しない。
- **祖先を元の inode へ self-bind して read-only にする** — 子の側からの rename は止まるが、
  外側からの rename を防げない。
- **source だけを seal する** — 親 directory を退避して symlink を置かれると同じ絶対 path で
  別の tree を読ませられる。

**この決定の代償:** 子から見えるのは spine と共有枝だけになる。
source と同じ最上段の下にあって子が必要とするもの (cwd、dependency source、
toolchain の realpath、depfile の出力先) は、**呼び手が共有枝として渡さなければ見えない。**
渡し漏れは「正当な build が壊れる」形で出る。

## {{D:sealed-protection-kind-split}}. 保護種別は「この process が実際に行ったこと」だけを述べる 2 種にする

**決定:** 保護種別を `SEALED_BUILD` と `SEALED_CACHE_HIT` の 2 つに分ける。

- `SEALED_BUILD` = この process が snapshot を seal し、**trusted producer が build として
  指定した command が成功し、指定の出力を新しく作り、その bytes が発行値と一致した。**
- `SEALED_CACHE_HIT` = この process が snapshot を seal し、
  **cache identity が同じ保護契約を束縛する entry を返した。**

**`SEALED_CACHE_HIT` は「過去に保護された build が実行された」とは主張しない。**

**理由:**

- cache hit のとき、保存された JSON の整合性だけを根拠に「保護された build が走った」と
  記録できる設計になっていた。**過去 session の完了を、その JSON から独立に確認する参照が無い。**
- 過去の実行を認証する機構を作ることは、D953 が別審査に属すると裁定済みであり本 wave の scope 外である。
- **2 種に分ければ、どちらも真の陳述になり恒真にならない。**
  下流の policy が、どの種別を正式受入に数えるかを決められる。

**却下した選択肢:**

- **1 種にまとめる** — cache hit が実行していない compile を主張する。
- **過去の実行を認証する機構を作る** — D953 が別審査と裁定済みで scope 外。

## {{D:mutation-redundant-gate}}. 巻き添えの広い変異は冗長 gate と明記し、単独では単一理由の証拠に数えない

**決定:** 観測 node が広範囲に及ぶ変異は、期待 node を完全集合で登録したうえで
**「冗長 gate であり単独では単一理由の証拠にならない」と台帳へ明記する。**
期待 node を削って見かけ上の単一理由にしない。

**理由:**

- `DW-M08` は期待 node を完全集合とし、完全一致だけを KILLED とする。
  部分集合にすると、実際には落ちている他の node を見落とす。
- `DW-M03` は過剰決定の fixture を単独変異の証拠から外すことを求める。
  **両立する唯一の形が「完全集合で登録し、証拠としての弱さを明記する」である。**
- 置換を固定したまま巻き添えを除く再照準はできない。再照準するなら変異そのものを変えることになり、
  それは別の変異である。

**却下した選択肢:**

- **期待 node を絞る** — 完全一致にならず fold も本走も止まる。
- **登録しない** — 実在する gate の再発検知を失う。

## {{D:probe-evidence-over-mutation-pairing}}. 実機 probe が独立必要性を示しているなら両層同時変異を追加しない

**決定:** 2 つの機構が同じ 1 つの test node で捕まる場合でも、
**実機の probe が各機構の独立した必要性を示しているなら、両層同時変異を追加しない。**

**理由:**

- `DW-M02` が両層同時変異まで裏取りを求めるのは**変異が生存したとき**である。
  本件はどちらの単独変異も生存していない。
- 4 状態を分離した probe が、capability を落とした状態と、そこから新しい user namespace を
  作った状態とで結果が変わることを**実機で**示している。
  これは「2 機構が独立に必要」の直接証拠であり、変異による間接証拠より強い。

**却下した選択肢:**

- **常に両層同時変異を足す** — 生存が無いのに変異を増やすと、
  受入所要だけが増えて検出力が上がらない。
