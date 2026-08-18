# [T-1162] — D130 条件 2 は「同種の排他の運用前提」では閉じない (2026-08-18)

wave = `dev-wave-t1162-flock-premise`。実装差分ゼロ (docs のみ)。
本 wave が自ら走らせた runtime 測定は無い。証拠はコード読解・台帳読解と、
過去 wave の runtime 実測の引用である。この区別は本書で明示する。

## 1. 依頼と結論

依頼は 2026-08-16 の /rulings 裁定の実行だった。裁定は「D130 条件 2 は測定を増やす方向 (a) では
閉じない。同種の排他 [T-565] が確定に使った運用前提をここへ適用できるかをまず確かめ、
適用できるなら設計変更なしで閉じる。**できない場合に限り (c) supersede を検討し、
その判断材料を裁定パッケージとして返す (実装を先に走らせない)**」である。

**結論: 閉じない。(c) の判断材料を返して止まる。** 理由は 2 つある。

1. [T-565] の前提は述語が違い、そのままでは適用できない (§3)。ただし「適用できない」と
   断ずるところまでは行かない — 別の述語の置き方なら適用しうるが、その可否は
   **ユーザーの運用意思にしか無い** (§4)。
2. 前提の転用に代えて「設計で閉じる」道 (排他を lock から作業木の一意性へ移す) を親は
   段 1 で描いたが、**台帳の既決定 D216 と正面から矛盾するため撤回した** (§5)。

## 2. 条件 2 に残っているのは flock の可否ではない

D130 条件 2 の逐語は「cross-node で効くか、silent fail-open しないかは未実測」である。
しかしこれは **2 回の実測でいずれも肯定側に出ている**。

| wave | host pair | /work | /home | localflock | Execution Host 照合 | 確定 |
|---|---|---|---|---|---|---|
| [T-361] (worklog 149、2026-08-04) | bnode001 / bnode005 | 6/6 BLOCKED | 6/6 BLOCKED | 無し | 未完 | `dangerous: null` |
| [T-402] (worklog 571、2026-08-16) | bnode003 / bnode004 | 6/6 BLOCKED | 6/6 BLOCKED | 無し | 成立 | `dangerous: false` / `BLOCKED_EXPECTED` |

正本 = `output/insights/2026-08-16_t402-flock-execution-host/RESULT.md`。同 §5 が自ら
「1 host pair の 1 回の観測は十分条件ではない」と限定している。
**残っているのは 1 host pair から全 pair への一般化**であり、これが (a) の費用問題である。

(a) は資源上も機械的にも塞がっている。sanctioned probe driver
`output/insights/2026-08-03_t361-t362-cluster-probes/driver/run_probes.py:66` は
`FLOCK_LEG_ONLY_SUBMISSION_LIMIT = 1` を持ち、同 :4309-4314 が persistent wave state を
この上限で fail-closed 検査する。[T-402] RESULT.md §7 はこの枠を **1/1 消費済み**と記録する。

## 3. [T-565] の確定文と条件 2 の述語 (逐語照合)

| | [T-565] 確定文 (worklog 267) | D130 条件 2 (decisions.md) |
|---|---|---|
| 排他の単位 | 「同一 campaign」— campaign 固有 lock file | 「同一 repo で同時 1 本」— 実装は `sha256(str(repo))`、すなわち**解決済み checkout path** 単位 (`tools/mutation_harness.py:2784-2786`) |
| 成立根拠 | 「dev-wave を**ユーザーが番号を付けて投入する**ため、同一 campaign のノード跨ぎ二重投入は運用上発生しない (ユーザー明言)」 | 変異 harness は wave の中で**親が自動起動**する。ユーザーの番号付けは wave の起動を一意にするが、wave 内の harness 起動回数を一意にしない |
| 再検討条件 | 「自動投入へ運用を変えるときは lease 等の再検討を裁定へ戻す」 | 束ねは投入形の変更そのものであり、[T-565] 自身の再検討条件に該当する |

## 4. それでも [T-565] が適用できる最強の読み — ユーザーへ問い返す 1 点

段 3 レンズ A が親の判定を弱めた。述語を「**一つの logical run に node を跨ぐ active owner は
一つだけ**」と置けば、束ねは harness 全体を 1 job に収めるため、
「ユーザーが番号を付けて一度だけ投入し、**retry / resume を重ねない**」運用なら [T-565] と
同型に読める。この読みを排除できるのは lifecycle の事実だけであり、それはユーザーの運用意思にある。

**問い: 束ねた変異 job について、同一 spec / 同一 `--out` に対する retry と `--resume` を、
ノードを跨いで同時に走らせない運用を約束できるか。**
約束できるなら [T-565] と同型に閉じられる。約束できないなら §5 のとおり設計側の手当てが要る。

## 5. 「設計で閉じる」道が塞がっている理由 — D216 の既決定

親は段 1 で「注入先の一意性は `_claim_fresh_container` の `mkdir(exist_ok=False)` という
atomic gate が与えるので flock に依存しない」と考えた。**これは撤回した。**

**D216 (2026-08-07) 逐語:** 「**lock は `--out` へ束縛する** (`<out>.lock`)。harness の `flock` は
repo 絶対 path 由来なので、**scratch を変えると分裂し、同じ台帳を後勝ちで上書きできる。**」

本プロジェクトは既に「path 由来の lock では足りない」と裁定し、producer 一意性の authority を
`<out>.lock` = **flock** に置いている。さらに実コード上、

- `--resume` 枝 (`tools/mutation_worktree.py:1141-1142` → `_validate_resume_container` :456-469) は
  `lstat` と admin 再束縛だけで **atomic claim を行わない**。効く排他は外側の `_out_lock` だけ。
- `mkdir` の cross-node 排他は測っていない。scratch root が共有 FS か node-local かも
  wrapper は検査しない (`:280-299`)。flock は exact host pair から一般化しないと自己限定
  しておきながら `mkdir` を無測定で一般化するのは非対称である。

### 「束ねでは wrapper 経由必須」も既に却下されている

D216 の却下選択肢: 「**`DW-M05` で wrapper を必須化する** — 機械的 admission が無い状態の
「必須」は prose-only であり、旧 direct 経路も台帳 consumer も拘束しない。活性化は独立 wave の
裁定に委ねる。」`docs/mutation-restore-durability-design.md:437-445` も同旨。
runbook §7.4 の本走 recipe は現に wrapper 非経由の直接起動である
(`docs/pegasus-runbook.md:1122-1129`)。

## 6. 束ね経路の共有面と排他機構の対応

| 共有面 | 排他機構 | cross-node での性質 |
|---|---|---|
| fresh invocation の container (注入先) | `_claim_fresh_container` の `mkdir(exist_ok=False)` (`tools/mutation_worktree.py:441`) | atomic create 系。ただし cross-node 成立は未測定 |
| `--resume` の container 再利用 | 実質 `_out_lock` のみ (:456-469, :1141-1142) | **flock 依存** |
| 同一絶対 `--out` の producer | `_out_lock` の `flock` (:186-200)。D216 が authority と定めた | **flock 依存** |
| 元 repo の git admin dir | git 自身の lock file (`git worktree add --detach`、:537) | O_EXCL 系 |
| 同一 checkout path の harness | `_lock_path_for` の node-local `/tmp` flock (`tools/mutation_harness.py:2784-2786`) | **cross-node 保証は元から無い** |

`tools/mutation_harness.py` / `tools/mutation_worktree.py` はいずれも **hostname を記録しない**。
wrapper receipt は `container_path` / `scratch_root` / `lock_path` を記録するが host は無いので、
束ね後に「どのノードで走ったか」を事後照合する手段が現状は無い。

## 7. 二重注入が起きた場合に壊れるもの

変異 matrix の値と復元後 bytes に留まらない。一方の復元中に他方が test を走らせれば**偽 SURVIVED**、
一方の変異上で他方が走れば**偽 KILLED** になる。偽 KILLED は無効な正しさ gate を land させ、
将来の certified 選択の受理集合を誤って広げる。偽 SURVIVED は正しい変更を拒否する。
proof chain の参照先も別 invocation 由来に分裂しうる。

## 8. 択一 (ユーザー裁定を求める)

- **(c-1) 条件 2 を supersede し、「cross-node flock の実測」を「注入先・producer・ledger の
  一意所有を atomic create 系機構で与え、記録と exact 照合する」へ置換する。**
  併せて resume 経路の atomic claim 化と `_out_lock` の置換が要る。D216 の「lock は `--out` へ
  束縛する」を明示的に改める裁定になる。設計先例は fan-out にある
  (`tools/mutation_fanout.py:590-635` の shard_id 由来の一意 path、
  `tools/mutation_fanout_contract.py:1266` の merge 側 exact 照合) が、
  fan-out 本走は D433 でこの機体では実行不能なので**稼働実績としては引用できない**。
- **(c-2) 条件 2 の射程を「`_out_lock` と resume 経路の cross-node flock」へ縮小して維持する。**
  既に得ている 2 host pair の実測が、縮小後の射程に対しては相対的に強くなる。
  ただし 1 pair から全 pair への一般化問題は残る。
- **(b') §4 の問いに「retry / resume をノード跨ぎで同時に走らせない」と答え、
  [T-565] と同型の運用前提で閉じる。** 設計変更は不要だが、[T-565] と同じく
  「運用を変えるときは裁定へ戻す」再検討条件が付く。
- **(a') `FLOCK_LEG_ONLY_SUBMISSION_LIMIT` を引き上げて測定を続ける。**
  費用が host pair 組合せに比例し、裁定が既に却下した方向である。
- **(d) 束ね自体を当面見送る。** D131 (transport 手続きの択一) が未裁定であり、
  D130 条件 1・3・4 も開いたままなので、条件 2 だけを閉じても transport は進まない。

**親の推奨: まず §4 の問いに答えてもらう。** 「約束できる」なら (b') が最も安く、
[T-565] と同じ形なので台帳上も一貫する。「約束できない」なら (d) で保留し、
将来 transport を進める時点で (c-1) を採る。(a')(c-2) は費用と残る一般化問題に見合わない。

## 9. どの択でも明記が要る事項

1. 置換後の安全不変条件 (何が保証されれば二重注入が起きないと言えるか)。
2. 束ね後の transport topology (harness がどこに居て、共有 FS 上の何を触るか)。
3. 全 caller の wrapper 強制の可否 — D131 共通前提 3 と同じ穴である。
4. `--scratch-root` と `--out` の共有範囲 (node-local か共有 FS か) の明示。
5. 衝突・`--resume`・walltime kill 時の fail-closed 挙動 (自動 GC は無い)。
6. **条件 1・3・4 は閉じないことの明記** (D130 は 4 条件の連言)。
7. 再裁定トリガ。
8. host の記録 (§6 のとおり現状は無い)。

## 10. 段 3 の収量と、親が撤回した主張

段 3 は 2 レンズとも独立に否定側で返した — レンズ A (sol) が **NO-GO・must-fix 8**、
レンズ B (luna) が **hold・must-fix 7**。**refuted はゼロ**で、親は 15 件すべてを real と裁定した。
両レンズが独立に指摘した重複は 3 点 — 親の第三の道が裁定の許す分岐の外にあること、
wrapper 必須化が発火しない保証であること、F203 の一般化が誤っていることである。

親が撤回した主張は 3 件。

- **(P3)「排他は lock でなく path の一意性で与えられている」** — D216 と矛盾。§5。
- **M4「F203 は同一 checkout への二重注入の実発生例」** — F203 が共有したのは wave worktree と
  job dir であり、変異 checkout ではない。直接的な資料は **F32** (旧親の死後に harness が
  生存し次走・復元と競合した) である。
- **(P2)「[T-565] の前提は適用できない」** — 「適用可否未確定、ユーザーにしか答えられない」へ
  格下げした。§4。

## 11. セッション事象

レンズ A の初回走行は codex 自体は自然終了 (rc=0、41 model call、673 秒、出力 9983 bytes) したが、
出力に **Web 検索由来の外部 URL** が含まれ evidence chain が invalid となり不受理になった。
Web 禁止を明記した prompt で再走し受理された。両走の結論は同じ NO-GO である。
`tools/dev_wave_wait.py producer` は本 wave で 2 度、producer 生存中に rc=0 で先に終了した
(出力なし)。親は自前の bounded polling (成果物出現・producer 死・deadline の 3 条件) へ切り替えた。
