---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-15
wave: dev-wave-prov-incremental-audit
seq: 1
---

## {{D:provenance-incremental-audit}}. authoritative な provenance 監査は、検証済み prefix を受領証で再利用し per-commit 監査を取り込み差分へ限る

**決定:** `tools/check_ai_provenance.py` の引数なし (authoritative) 監査で、`_normal_commit_audit` を
実行する母集合を差分へ限定する。D908 が条件とした「取り込み差分だけを対象とする独立監査を先に設計し、
被覆が現行と等価であることを示してから置き換える」の経路である。

`--range` は使わない。D254 と D1996 が却下したとおり、`--range` は `authoritative` 述語 (既知違反台帳の
append-only 履歴検査、policy epoch の適用範囲、pinned HEAD 再確認) を同時に落とす。本決定が狭めるのは
**per-commit 監査の母集合だけ**であり、全史の論理的被覆・判定内容・CLI・`authoritative` 述語は変えない。

**等価性の対象を限定して定める。** 等価と主張するのは provenance 判定 — 各 commit の finding 集合、
既知違反台帳との照合と stale 判定、`AI-Agent-Correction` の適用結果、それらから決まる rc と公開 record —
だけである。資源障害・実行不能に由来する終了は等価と主張しない。

**論証:** main は ff-only でしか進まない。受領証の tip `A` が固定 HEAD `H` の祖先なら、policy 導入
commit を `p` として選択集合は `S(H) = S(A) ⊎ (ancestors(H) − ancestors(A))` に分解できる。
`S(A)` の判定は、下記 13 項目がすべて一致するとき前回と同一である。

**受領証が束縛する 13 項目:** checker file の sha256 と受領証 schema version / 監査した tip の完全 OID と
repository identity と object format / policy 導入 commit の OID / scope epoch と implementation epoch の
OID / CAB pickaxe hit の OID 集合 / 既知違反 registry の manifest digest (追加も失効させる) /
prefix 選択集合の digest と件数 / `prefix ∩ registry` の entry key 集合と照合成功記録 / prefix の
correction candidate 数と前方訂正結果 / prefix の waiver 適用と公開 record / 環境 fingerprint
(解決済み `git config --list` 全文と継承した `GIT_*` / `LC_*` / `LANG`) / 属性 fingerprint /
前回の returncode。

**属性 fingerprint は git が読む入力だけから作る。** index 由来の候補 directory と repo root の
作業ツリー `.gitattributes`、作業ツリー側が読めないときの index entry、`$GIT_DIR/info/attributes`、
`core.attributesFile` (未設定時は XDG / HOME の既定)、system 属性 file である。file 種別も束縛し、
中身が同じ symlink と通常 file を区別する。**監査 tip の tree は読まない** — git も読まないためで、
tip に依存させると属性が変わらなくても tip が違うだけで再利用が落ちる (本 wave で実測した)。
tracked file を 1 つも含まない未 tracked directory の `.gitattributes` は列挙しない。

**毎回実行し受領証で省略しないもの:** repository guards (shallow / grafts / replace)、
既知違反台帳の append-only 履歴検査 (D807)、registry loader の完全性検査、policy 導入の一意性、
HEAD 固定と再確認、`[HEAD]` を根とする祖先閉包の構築、隔離 trailer parser の canary、site / admission。

**fallback は fail-open にしない。** 受領証が無い・読めない・非 regular・symlink・壊れている・
schema 不一致・rc≠0、tip が存在しない・commit でない・HEAD の祖先でない、束縛 13 項目のいずれかが違う、
差分に correction candidate が 1 件でもある、差分列挙が失敗した — いずれも全史 oracle を 1 回だけ実行する。
CLI flag・環境変数・警告化の逃がし道は作らない。**受領証の保存失敗は fallback の引き金にしない** —
受領証は次回のためのキャッシュであって今回の判定の根拠ではなく、保存失敗で全史を追加実行すると
480 秒枠に「差分 + 全史」が乗り、正常な履歴を従来より拒否する経路を新設してしまう。

**受領証は共通 git-dir 配下の共有 store に置き、環境 fingerprint で区画する。** land lock と同じ場所の
流儀で、作業ツリーの外・全 worktree で共有・非 tracked を満たす。区画が分かれるため受入
(`dev_wave_wait.py`) と land (`dev_wave_land.py`) は受領証を共有しないが、同じ区画の中では wave を
跨いで積み上がる。land は ff-only の着地 tip をそのまま監査するので、次の wave の着地 tip は前の
着地 tip の子孫になり再利用が連鎖する。

**この決定が保証しないこと。** 受領証を書く主体と検査する主体は同じ OS user である。**受領証は改竄への
防壁にならない。D387 と同型の限界であり、意図的な偽造を防げるとは主張しない。** 総費用の履歴長非依存も
達成しない — 全選択集合の列挙、祖先 bitset の構築、append-only 検査は履歴長に比例したまま残る。
初回・checker 更新後・registry 追加後・correction 追加時・環境や属性の変更後の高速化は保証しない。
受領証の淘汰には残余があり、別枝の publish 時に着地済み tip の受領証が非祖先として捨てられうる
(誤った受理は作らず、warm 連鎖が切れて全史へ戻るだけである)。
新しい wave HEAD を監査する受入の claim 前監査は、区画内に祖先の受領証を持たないため cold のままである。
改修後に land が 480 秒へ収まることは未実測である。

**理由:**
- 監査対象 commit は 10,104 件で、F365 記録時点の 3,727 件から 2.7 倍に増えた。2026-09-15 の login node
  (load 187、worker 32) の 1 走で `_audit_history` 本体が 559.572 秒を要し、D254 が定める land の
  480 秒予算を超えた。超過は rc=29 になり main が 1 bit も進まないため、成果物が着地しない。
- D908 は削減ではなく等価な独立監査への置換を条件付きで認めている。本決定は被覆を削らない。
- D1996 が却下した「監査の履歴範囲を限定する」は `--range` を前提とした案であり、`authoritative`
  述語が落ちることを理由にしていた。本決定は述語を落とさない形を採るため同じ却下理由に当たらない。
  同 D の却下理由「縮める対象が律速ではない (計算ノードで 61 秒)」は、同 D 自身が記録する
  「所要は実行場所で 7 倍振れる」の範囲内で、混雑した login node の実測に反証されている。
- 受入経路の claim 前監査と merge 後監査は同じ HEAD を監査している (merge commit 作成前に走るため)。
  差分監査では 2 本目が差分 0 件になる。D908 が「削るな」と述べた冗長は、削らずに費用だけ消える。

**却下した選択肢:**
- **受領証を worktree ごとに分離する** — 並行 wave の初回監査を 1 件も救えず、受入で作った受領証が
  land で使えない。目的の rc=29 が解消しない。
- **object storage manifest・pack 再編・alternate・外部 diff driver・実行系の version まで束縛する** —
  同一 user による意図的改変にしか効かない。D387 が「達成不能で、達成したふりになる」として却下した形。
- **opt-in の CLI flag にする** — D254 が禁じる逃がし道と見分けがつかない。
- **受領証の保存失敗で全史へ戻す** — 正常な履歴を従来より拒否する経路を新設する。
