# [T-781] 案 A (scheduler spool 証拠の独立取得) 実現可能性 — 調査結果と択の再提示

- `authority: none`
- `default_effect: no-state-change`

本書は裁定パッケージの凍結スナップショットであり、可変状態の正本ではない
(正本は worklog 末尾と現行 phase doc)。

2026-08-11、bounded 調査 wave `dev-wave-t781-spool-feasibility`。**実装差分ゼロ。**
ユーザー裁定 (2026-08-11 /rulings、worklog 404) 「択は保留し調査先行」に対する返答である。

- 逐語: `verbatim/` (段 1 brief、段 2 plan、段 3 レンズ A / B、probe 1 / 2 の生ログ)
- 段 4 裁定: `verbatim/s4-adjudication.md`
- 起票の一次資料: `output/insights/2026-08-11_t8b-restart-integration/package.md` の R-5 節

---

## 0. 結論 (3 行)

1. **起票時の前提は誤りだった。** scheduler が spool した script bytes を独立取得する手段は実在する
   — Pegasus のスケジューラは PBS ではなく **NEC NQSV** で、`qcat -i <RequestID>` が返す。
   計算ノードからも使える。
2. **しかし取得できるのは「caller が指定した live request の入力」であって、現プロセスの同定ではない。**
   さらに `qattach command = Enable` を実測した — 同一 uid の攻撃者は真正 request の**外**から
   任意 command を request 内へ注入できる。したがって案 A 単独では A-1 を閉じない。
3. **よって「(A) を実装すれば D86 §4 を満たせる」とは言えない。** 択は元の (A)〜(D) ではなく、
   判断軸ごとの Q1〜Q4 として再提示する (§4)。

---

## 1. 実測 (M1〜M14)

Pegasus login `pegasus02` と計算ノード `bnode042` / `bnode046`、2026-08-11。
値はすべて実物から採った。probe は repo 外に置き、repo へは入れていない
(`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t781-spool-feasibility/probe/`)。

| # | 事実 |
|---|---|
| M1 | scheduler は PBS ではなく **NEC NQSV** (`/opt/nec/nqsv/bin`)。観測した CUI/API は R1.16。`/etc/pbs.conf` は不在 |
| M2 | **`qcat -i <ReqID>` が spool 済み request script を返す** (自分の request、rc=0)。login からも計算ノードからも取れる |
| M3 | 忠実性 = 出力は投入 bytes + 末尾 `\n` **1 個ちょうど** (2077→2078、2031→2032、357→358 の 3 例。先頭部 sha256 は投入ファイルと一致)。非 ASCII 保存 |
| M4 | 既定は末尾表示。全文には `-b -n <大きい数>` が要る。`-n` は**行数**であり、小さすぎると rc=0 のまま静かに切り詰まる (実測 1173 / 全 2078 bytes) |
| M5 | request 消滅後は取得不可 — `NQSopenjfl: [BSV ENOREQ] No such request.` (完了済 900530 で実測) |
| M6 | **HLD 状態では rc=0 のまま空 1 byte (`\n`) を返す**。QUE / PRR / RUN では全 bytes |
| M7 | `qstat -f` に script bytes・hash・`-v` 環境変数は現れない |
| M8 | `qsub -U key=value` は User Attributes として保持され、40 hex を格納できる |
| M9 | **`qalter` に `-U` が無い** (`Invalid argument flag: -U`)。一方 **`qalter -N` は rc=0 で成功** = request 名は所有者が事後変更できる。script bytes を書き換える qalter option も無い |
| M10 | 計算ノードで `qcat` が使える (rc=0) |
| M11 | 実行中スクリプトの実体は `/var/opt/nec/nqsv/jsv/jobfile/0.<req>.10/user_script` に **root:root `-r-xr-xr-x`** で存在し、sha256 は投入ファイルと**完全一致** (`qcat` のような +1 byte なし) |
| M12 | その親 dir は **`drwx------ <user>`** (sticky bit なし)。所有者は dir 内に file を作成・削除できる (`touch` rc=0 → `rm` rc=0 を実測) |
| M13 | 計算ノードからの `qstat -f` は**正規化 ID なら rc=0** (`901512.nqsv`)。`0:` 付きの raw ID では rc=1 |
| M14 | **job 内から `qstat -f` で User Attributes を読める** (`izanagi_source_commit = 0c336b8e…`) |
| M15 | **`qattach command = Enable`** (`qstat -f` の属性として実測)。NQSV の `qattach` は request owner が RUN 中の request 内で任意 command を実行できる機能である。**実際に attach して検証はしていない** |
| M16 | `Exclusive = (none)` — job は形式的には排他ではない |

### 実測でない推論 (区別して記す)

- **I1**: M12 より、root 所有 0555 の `user_script` は所有者が unlink して差し替えられる
  (POSIX: unlink には dir の書き込み権限だけが要る。sticky bit なし)。
  **破壊的検査は権限層に拒否されたため実施していない (迂回もしていない)。**
  immutable flag・NFSv4 ACL・LSM・mount option は反例になりうる。
  推論どおりなら **JSV 直読経路は証拠に使えず、診断 observation にとどまる**。
- **I2**: `qcat` / `qstat` は server へ問い合わせるため、**server の記録**を所有者が書き換える手段は
  観測範囲に無い (M9)。ただしこれは **admission process が正しく観測できること**を意味しない —
  `PBS_JOBID`・PATH・`$0`・`LD_PRELOAD`・同一 Python 内 monkeypatch はすべて攻撃者側にある。

### 主張の射程 (意図的に狭めた点)

- M3 の「+1 byte 規則」は、小さい text shell script 3 例・非 TTY 出力・同一 site・同一 client
  version の範囲でのみ実証した。長大 script、極端に長い 1 行、locale 差、NUL は未測定。
- M5 は「少なくとも 1 request で消滅後取得不能」であり、全終了形態の普遍則ではない。
- M6 の状態列挙は HLD / QUE / PRR / RUN のみ。ARI/HOL/MIG/POR/SUS/TRS/WAT/STG/EXT は未観測。
- M1 は client (CUI/API) の version であり、batch server 実装の version は未実測。

---

## 2. 案 A の可否 — 何が閉じ、何が閉じないか

### 閉じるもの

元プランの `9<"$0"` (job script が自分自身を固定 FD で渡す) は「caller が選んだ file を開くだけ」
という恒真化だった。`qcat` はこれを **request → spool された bytes** の辺に限れば実際に閉じる。
scheduler が保持する bytes は所有者から書き換えられない (M9)。**primitive は本物である。**

### 閉じないもの

| 欠けている辺 | なぜ閉じないか |
|---|---|
| process → request | `PBS_JOBID` は環境変数であり、caller が任意値で exec できる。`qcat` の引数は「self」ではなく「caller が名前を指定した所有 request」である (probe 1 は同一 uid の**別** request の script も読めた) |
| request → wrapper lineage | 真正 floor request の中で wrapper を経ずに core を起動した process も、同じ真正な spool bytes・属性・job ID を得る。さらに **M15 (`qattach=Enable`) により、request の外にいる同一 uid の攻撃者が任意 command を注入できる** |
| submitter → ユーザーの明示指示 | 属性も receipt も submitter 自身が選ぶ。AI が qsub しても同じ値を置ける。D86(8)「artifact の存在を認可の証明として扱ってはならない」がここに効く |
| 実行時 → 下流 proof chain | request 消滅後は `qcat` / `qstat` を再取得できない (M5)。certificate v1・journal・ratified verifier に対応する field は無い (A-5 のまま) |

### 受理集合が実際にどうなるか

`r` = revision、`j` = scheduler request、`p` = core を呼ぶ process とする。

| 状態 | 機械的に束縛されるもの |
|---|---|
| 現状 (guard 生存) | `∅` — official は空集合 |
| 案 A のみ | `qcat(j) == blob(r) + "\n"` を満たす live request。**`p` が `j` の wrapper の子孫であることは束縛されない** |
| 案 A + User Attributes | 属性・receipt・HEAD・spool が同じ `r` に整合する request。ただし `r` は submitter が自己選択できる |
| ユーザー署名 authority + lineage 束縛 | ユーザーが指した `r` と、認証済みの `p` まで束縛する将来形 (未設計) |

つまり案 A を入れても、受理集合は「**ユーザーが指した revision**」ではなく
「**同一 uid が指定できる live request と、そこへ任意に注入できる process**」まで広がる。
A-2 が言った「全 clean revision へ広がる」は**解消しない**。

---

## 3. 費用 (段 2 プランの見積り + レンズ B の指摘)

- 案 A + User Attributes の production 差分: **350〜550 行**。
- A-3 (private core の seam) と A-4 (`VerifiedFreeze` の forge) を同時に閉じ、既存 official test seam を
  移行すると**テスト込み 900〜1400 行**。
- A-5 (certificate v2 / journal / ratified verifier) は**別に 500〜900 行級**で、D86(4)(5) を覆す独立 wave。
- **上記に含まれていない費用**: process lineage の真正な束縛、User Attributes の認可性、
  D86(8) と両立する authority の設計。lineage を閉じる設計は現時点で存在しない。

`docs/phase3-8b-restart-runbook.md` §0 の不変事項 — 「8b の証拠価値は限定されたままである」 — と
突き合わせる必要がある。

---

## 4. 択の再提示 (Q1〜Q4)

元の (A)〜(D) は判断軸が異なり択一ではなかった (R-5 自身が (D) は (A)〜(C) と独立に必要と書いている)。
実測を踏まえ、軸ごとに 4 問へ再構成する。**親の推奨を付ける** — 起票時は実測が無く
「推奨なし」だったが、実測が揃ったため推奨できる。

### Q1 — `qcat` 経路をどう扱うか

- **(a) official は空集合のまま維持し、実測事実だけ記録する**【親推奨】
  実装ゼロ。`qcat` primitive が実在することと、それでも lineage が閉じないことを台帳に残す。
  再訪条件 = queue の `qattach` が無効化される、または lineage を閉じる設計が出た時点。
- **(b) bounded な設計だけ続ける (実装はしない)**
  lineage・authority の設計案を read-only wave で 1 本作る。official は空集合のまま。
- **(c) 案 A + User Attributes で解禁する**
  受理集合が「同一 uid が指定できる live request と、そこへ注入できる process」まで広がることを
  明示的に受諾する。350〜550 行 + 未解決の lineage。

**推奨 (a) の根拠**: `qattach command = Enable` が生きている限り、どんな spool 証拠を積んでも
「真正 request の中で動いている」ことしか言えない。350〜550 行を投じて得られるのは
「official が空集合でなくなる」ことだけで、A-2 が指摘した受理集合の拡大は解消しない。
8b の証拠価値は限定的である (runbook §0) 一方、正しさ防壁を緩める方向の変更は絶対規律 2 の
中心にある。**実装の便益がコストと risk を下回る。**

### Q2 — User Attributes の位置づけ

- **(a) 観測 assertion に限定する**【親推奨】
  revision 整合の診断値として使ってよいが、認可には使わない。
- **(b) scheduler-level の revision authority として採用する**
  submitter が選んだ clean revision を束縛できるが、ユーザーの明示指示は証明しない。
  D86(8) / D87(5) との整合をユーザーが明示裁定する必要がある。
- **(c) 署名付き allowlist 等の外部 authority を新設し、属性はその器として使う**
  D86(3) の「新しい Git launch receipt は作らない」を覆すかどうかの判断が要る。

**推奨 (a) の根拠**: 属性を置くのは submitter であり、AI も同じ値を置ける。
「`qalter -U` が無い」は所有者 CLI による**事後**変更耐性を示すだけで、**投入時の値**に権威を与えない。
段 1 で親が (P3) として「D86(3) に直接は当たらない」と書いたのは**裁定の先取りであり、撤回する**。

### Q3 — proof chain へ通すか (元の (D))

- **(a) 先送りを維持する (D86(5) のまま)**【親推奨】
  certificate v1・journal・ratified verifier は不変。official が空集合である限り、
  通すべき admission 実績が無い。
- **(b) 拡張する**
  spool hash・source commit・request ID を certificate v2 / journal / verifier に残す。
  D86(4)(5) を覆す独立 wave (500〜900 行級)。
- **(c) 非公式の診断台帳にだけ残す**
  certified result の受理根拠にはしない。

**推奨 (a) の根拠**: Q1 が (a) なら通すべき admission が存在しない。Q1 が (c) に振れた場合のみ
(b) が必須になる — その意味で Q3 は Q1 に従属する。

### Q4 — W-2 との優先度

- **(a) T-139 / A 系列の後まで保留する**【親推奨】
  本 wave は結果付き再提示で終端し、追加の qsub も実装もしない。
- **(b) A 系列の後に read-only の設計 wave を 1 本だけ行う**
  不足している数字 (下記) と lineage の選択肢だけを埋める。
- **(c) 直ちに実装する**

**推奨 (a) の根拠**: 並走ガード (iii)「裁定帯域は A 優先」。W-1 は現在 blocker ではない
(official は空集合のままで W-2 = 床値実測は進む)。

### 裁定に必要だが本 wave が持っていない数字

- この証拠を何回・何候補で再利用するか (1 回限りなら機械化の便益は小さい)
- survivor による誤 admission をどの確率・損失まで許すか
- T-139 / A 系列に対する queue・計算時間の機会費用
- proof chain 拡張をしない場合の証拠価値
- lineage と authority を閉じる追加工数 (現時点で設計が無いため見積り不能)

### 実測から生まれた新しい選択肢 (元の (A)〜(D) に無かったもの)

- **site へ queue-level の `qattach` 無効化を要請する**: これはユーザー手番であり AI では実行できない。
  実現すれば「request → 注入経路」の 1 本が塞がるが、`PBS_JOBID` 偽装と job 内兄弟プロセスは残る。

---

## 5. 本 wave 自身の手続きの自己申告

隠さず記す (レンズ A 13 / レンズ B 10・12 の指摘は real)。

- **計算ノードへ 3 request を投入した** (901499 / 901501 / 901512)。「2 本」ではない —
  901501 は hold 解除後、`qdel` の前に実際に実行された。
- **F49 (ii) の 3 点検査**: (a) 計算ノードが書いた marker = 実在、(b) `qstat` 可視性 = 901499 / 901501 は
  投入直後に親側で確認したが **901512 は投入直後の親側 `qstat` を実施していない**、
  (c) 会計痕跡 = `.e` / `.o` 3 組が実在 (ポイント消費差分は `racctjob` が sudo を要求するため未取得)。
  → **(b) の一部が欠けた手続き不備である。**
- **並走ガード (i) は形式的に未充足**。ノード同居は実測上無い (他 wave = bnode034、
  probe = bnode042 / bnode046) が、**計算ノード上での単独性確認と静穏 preflight は行っていない**。
  性能値を一切採っていないため計測汚染は生じないが、ガード文言は無条件であり
  「非性能 probe だから」は充足の論拠にならない。
- **probe 2 は read-only ではない**。JSV jobfile dir へ `touch` → `rm` を行った (自分の job の dir だが
  scheduler 管理領域への書き込み)。「非破壊」と「read-only」は同義ではない。
- **`-U` は sanctioned な submit script に無い qsub surface**である。ただし script へパラメータを
  渡す用途ではなく、属性の保持と `qalter` 耐性を測る**測定対象そのもの**だった。
- **破壊的検査 (`user_script` の unlink / 差し替え) は権限層に拒否されたため実施しておらず、
  迂回もしていない。** I1 は推論であり実測ではない。
