静的監査結果は **NO-GO**。対象は `HEAD=e0b9073ade90`。pytest、`check_docs.py`、provenance 監査は実行していない。

以下、`PLAN` は `/home/SFC/tanab/.claude/jobs/61a0e66d/tmp/wave-t328/s2-plan.md`、`BRIEF` は `output/insights/2026-08-03_t328-devwave-docs-externalize/s1-brief.md` を指す。

### B-1 — 総量上限を据え置いたふりをして 2,000 bytes 引き上げている

判定: **real / blocker**

根拠:

- 確定済み裁定は「予算上限は上げない」(`BRIEF:17-19`)。
- 旧 dev-wave 契約の総量上限は 25,200 bytes (`tools/check_docs.py:253-257`)。
- plan は primary 25,200 を名前だけ残し、横断上限 27,200 を新設する (`PLAN:80-99`)。受理可能総量は 25,200 → 27,200、明確に 2,000 bytes 拡大する。
- 先例 D110 は総量を 9,000 のまま維持し、分割 overhead を非義務重複の削減で吸収した (`docs/decisions.md:5125-5128,5154-5162`)。
- さらに dev-wave 固有の D94 は、新 reference が読了 payload を減らさず checker と予算面だけ増やすとして明示的に却下している (`docs/decisions.md:4203-4209,4228-4233`)。後発のユーザー裁定で覆すなら、新 D で D94 を明示 supersede しなければならない。

失敗シナリオ: primary を 25,200、risk を 2,000 まで肥大させても横断 27,200 を通る。旧 gate なら拒否された 2,000 bytes が、sibling root へ移しただけで受理される。

影響: **受理集合**が 2,000 bytes 拡大し、「上限不増」という台帳記録と実際の reference 受理集合が食い違う。

### B-2 — 発火条件を弱めても proposed checker は通す

判定: **real / blocker**

根拠:

- plan は「ID・発火条件・最遅期限は変更しない」と宣言するだけ (`PLAN:293-305`)。
- proposed 三面一致が比較するのは path と `(path, ID)` だけ (`PLAN:195-203`)。
- 現行 checker の dev-wave 条件契約も key→参照節しか持たない (`tools/check_docs.py:476-484`)。検査は参照集合と row count だけである (`tools/check_docs.py:3035-3046`)。
- D110 の先例は「発火条件の逐語不一致」を独立 finding にしている (`docs/decisions.md:5130-5135`)。plan はこの歯を移植していない。

失敗シナリオ: condition 09 を

> 凍結成果物の bytes を変えうる可能性が判明

から

> 凍結成果物の bytes を変更すると決定

へ狭める。path、ID、期限、row count、三面一致は全部通るが、brief 前の pin 閉包調査は発火しなくなる。O04/O06/O08/O09/O10/O11/O14 の全 7 条件で同型が成立する。

影響: **受理集合**は checker 上緑のまま安全義務の発火範囲だけ広がり、F27/F30/F39/F78 の再発を受理する。

### B-3 — 「byte-for-byte 移設」は節本文しか対象にせず、継承していた前置き義務を落としている

判定: **real / blocker**

移設前の exact slice は再計測できたが、移設後の逐語は plan に存在しない。plan が示すのは前置きの説明と予定 byte 数だけである (`PLAN:53-69`)。

| 節 | 移設前逐語 | 移設後逐語 | 落ちる／未証明の義務 |
|---|---|---|---|
| O04 | `operations.md:26-30`、200 bytes | 未提示。「byte-for-byte」とだけ記載 | 下記 operations 共通義務 |
| O06 | `operations.md:36-40`、210 bytes | 未提示 | 同上 |
| O08 | `operations.md:41-45`、183 bytes | 未提示 | 同上 |
| O09 | `operations.md:46-58`、935 bytes | 未提示 | 同上 |
| O10 | `operations.md:59-63`、261 bytes | 未提示 | 同上 |
| O11 | `operations.md:64-68`、223 bytes | 未提示 | 同上 |
| O14 | `operations.md:78-82`、200 bytes | 未提示 | 同上 |
| M06 | `mutation.md:38-42`、258 bytes | 未提示 | mutation 文書が担っていた規範範囲との exact 対応 |

7 個の O 節は現在、次の共通逐語を継承している。

> 発火条件は入口の条件 dispatch が正本で、本書は各条件が成立したときの実行手順だけを持つ。操作の直前に該当節を読み、停止条件を迂回しない。  
> (`docs/dev-wave/operations.md:3-4`)

この 231-byte の義務は H2 slice の hash 対象外である。新 `guards.md` の前置きは H1 込み 152 bytes とだけ指定され、操作直前読了・停止条件非迂回の逐語がない (`PLAN:53-57`)。

M06 も `mutation.md:1-3` が定める「変異事前登録、kill 意味論、harness、fix 後再検証の正本」という親契約を slice に含めない。新前置きは exact text 不在のため対応を証明できない (`PLAN:59-61`)。

失敗シナリオ: skill や failure 台帳から新 `guards.md` の節を直接開いた consumer が、入口を再読せず局所手順だけ実行する。旧配置では同じファイルの前置きが課していた直前読了・停止非迂回が、新配置では誰にも課されない。

影響: **reference** の義務対応表が H2 本文だけの偽完全性になり、D110 の「移設であって削除ではない」を証明できない。

### B-4 — 節間参照そのものより、逆向きの F 台帳 pointer が壊れる

判定: **real**

内部参照を全列挙すると次のとおり。

- `O10 → O09` (`operations.md:61`): 両方移設。
- `O15 → M07` (`operations.md:83-85`): 両方残留。
- `M01 → M08` (`mutation.md:7-10`): 両方残留。
- `M07 → M02` (`mutation.md:43-46`): 両方残留。
- `S02 → O05` (`workers.md:5-8`): 両方残留。
- `S06-B → S05-A/B/C` (`workers.md:51-59`): 残留。
- `S06-C → G05` (`workers.md:64-68`): 残留。
- `S01 → O19` (`core.md:32-36`)、`G05 → G02` (`core.md:62-67`)、`S04 → M01` (`core.md:69-74`)、`S09 → O23/STOP` (`core.md:104-109`): すべて残留。

したがって inline の片側移設はない。しかし逆向き pointer が plan の scope 外で壊れる。

- F26 は O06/O08 の現行実体を `docs/dev-wave/operations.md` と記録 (`docs/failures.md:380-383`)。
- F27 と F30 は O09 の現行実体を旧 path に固定 (`docs/failures.md:400-401,477-488`)。
- F32 は M05/M06 を同じ `mutation.md` にあると記録 (`docs/failures.md:501-547`)。

移設節から外へ出る参照の意味自体は変わらない。

- O09 の F27/F30/D84/F39/F78 は pin 閉包の意味を維持。
- O14 の D78 は正規 seam / monkeypatch の意味を維持。
- M06 の F32 は hang の部分集合・timeout 隔離を維持。

壊れるのは failure→現行実体の逆方向である。旧ファイル自体は残るため、単なる path 実在検査 (`tools/check_docs.py:3259-3264`) では検出できない。

失敗シナリオ: F32 から「現行実体」を辿った実行者が `mutation.md` を開き、M06 がないため failure の恒久対応を未実装または削除済みと誤認する。

影響: **参照**が非到達になり、failure 台帳と現行契約の対応が壊れる。追記型台帳なので直接改稿ではなく failure fragment/erratum が要る (`core.md:84-90`)。

### B-5 — checker 外の consumer が plan の所有範囲から脱落している

判定: **real / blocker**

指定 consumer の実走査結果は次のとおり。

| consumer | path / ID 参照 |
|---|---|
| `.agents/skills/dev-wave/SKILL.md` | command (`:14,27`)、workers/operations (`:30`)、O01 (`:32`) |
| `.agents/skills/dev-wave/agents/openai.yaml:1-4` | なし |
| `AGENTS.md:1-41` | なし |
| `tools/dev_waves.py:1-16` | なし。package への薄い import のみ |
| `tools/dev_wave_land.py:1-1994` | なし |
| `tools/check_codex_agents.py:1-372` | なし |
| `hooks/README.md:1-210`、`hooks/guard_*.py` 全文 | なし |
| `docs/README.md` | 4 reference を閉じた列挙として記載 (`:28-29`) |
| `docs/agent-architecture.md:1-161` | なし |

破断は 2 件。

1. Skill は実装 worker の契約を `workers.md` と `operations.md` と明記する (`SKILL.md:30`)。O06 等が `guards.md` へ出た後もこの文は旧 2 ファイルだけを指す。
2. 文書地図は「core/workers/mutation/operations」が runbook 族だと列挙し、新 root を示さない (`docs/README.md:28-29`)。

さらに checker 自身が skill に旧 `operations.md` literal を要求する一方、新 `guards.md` を要求しない (`tools/check_docs.py:263-267,2495-2499`)。したがって skill が取り残されても検査は緑になり得る。

plan の docs 所有範囲は command、既存 4 reference、新 2 referenceだけであり、skill・README・failure fragment を含めない (`PLAN:505-509`)。

失敗シナリオ: Codex skill manager が `SKILL.md:30` を正本として worker 契約を組み、移設済み O06/O09/O14 を渡さない。command を完全に再解釈した場合だけ偶然回避される。

影響: **参照**の consumer 閉包が壊れ、Claude dispatcher と Codex skill で課される義務集合が分岐する。

### B-6 — 外部 supervisor は `DW-CTX` を spawn 前に読む導線を持たない

判定: **real / 現在は runtime blocked**

根拠:

- 入口は外部 supervisor 自身へ「最初の `claude -p` spawn 前に DW-CTX を読む」と課す (`.claude/commands/dev-wave.md:16-17`)。
- `tools/dev_waves.py` は CLI import だけ (`:1-16`)。
- daemon は manifest を作り、`/dev-wave --supervised-manifest ...` を prompt にするだけ (`tools/dev_waves/daemon.py:1177-1207`)。
- worker の argv も同 prompt のみ (`tools/dev_waves/worker.py:231-251`)。`DW-CTX` や reference path の読取処理はない。
- 現在は fake-only (`tools/dev_waves/worker.py:1`) で、Codex skill も supervised manifest を拒否する (`SKILL.md:38-39`)。

失敗シナリオ: real supervisor が将来解禁された際、最初の process を起動した後で、その子が wave 開始時に DW-CTX を読む。これは「spawn 前」という期限を満たさず、新族への到達も子 command に全面依存する。

影響: **参照**義務が supervisor 層で未結線。現時点の台帳には fake-only と明記すべきで、無人継続まで閉じたと記録してはならない。

### B-7 — A1/A2 の衝突解消文は正本へ入らず、A2 の実測を殺している

判定: **real / blocker**

根拠:

- A2 の一次資料は「背景 job では `nohup` で切り離さないと、呼び出しが返った時点で子が死んだ」と明記する (`output/insights/2026-08-01_t241-compute-llm-transport/s4-adjudication.md:139-145`)。
- 現行 O01 はすでに `codex exec` を `.done` wrapper の foreground で実行する形である (`operations.md:8-12`)。
- plan の A2 は同じ foreground 規則を再掲し、source の `nohup` 要求を削る (`PLAN:324-328`)。
- A1/A2 を繋ぐ「親が background に置く単位は専用 job」という橋渡しは plan の解説にしかない (`PLAN:384-388`)。実際の挿入先一覧・A追加 bytes には含まれない。

失敗シナリオ:

1. outer background harness が呼出し終了時に job process group を殺す。
2. A2 の proposed 文どおり `codex exec` を foreground に置く。
3. outer call の return で子が死に、`.done` も `-o` も残らない。
4. source どおり `nohup &` を重ねると、今度は wrapper の `.done` が子より先に出て A1 の二重 `-o` 事故へ戻る。

必要なのは散文の読み合わせではなく、outer job の寿命所有、attempt ごとの原子的 artifact namespace、`.done` を書く process と `-o` writer の同一性を launcher で固定すること。

橋渡し文を正本へ追加すると 248 bytes 増える。plan の全 reference は 26,946 → 27,194 bytesとなり、主張する余裕 254 は 6 bytesへ消える。

影響: **台帳と参照**の両方。完了済みと記録された child と実際の `-o` writer が分離し、別 child の出力を review 証拠として採用できる。

### B-8 — A5 は「投入前」を「受入前」へ遅らせている

判定: **real**

根拠:

- 出所は「計算資源を消費する投入の前に、親が識別子の実在を実測」と要求する (`docs/worklog.md:434-440`)。
- proposed 文は「親が受入前に実 checkout で実在確認」とする (`PLAN:342-346`)。

失敗シナリオ: worker が存在しない macro/member を参照した patch を返す。親は規則どおり受入前に検査して拒否するが、その時点まで child job、build job、review が全て消費済みである。出所事故を防いでいない。

影響: **台帳**に回避可能な failed task-run と再投入が残り、「投入前責務」を実装したという reference 記録が虚偽になる。

### B-9 — A9 は F29 の実編集義務を stdin 模擬で再び迂回できる

判定: **real / blocker**

根拠:

- 現行 S01 はコード変更を伴う前提を monkeypatch で済ませず、実編集・即時復元で測る (`core.md:32-36`)。
- F29 は file bytes/self-hash/include 閉包を模擬から落とした事故そのものである (`failures.md:443-475`)。
- proposed A9 は「file を書かない実行で測れるなら一時編集より優先」と一般化するが、実差分との同値性を要求しない (`PLAN:366-370`)。
- T-317 の出所は「既存 module を stdin から呼べば足りた一例」であり、コード変更一般への優先規則ではない (`worklog.md:804-807`)。

失敗シナリオ: heredoc から関数を monkeypatch して planned behavior を再現し、green を得る。実ファイルを 1 byte 編集すると自己 hash や include closure が先に落ちるが、A9 により実編集は省略される。

影響: **受理集合**の前提を誤って green と裁定し、誤った brief・plan が台帳へ固定される。

### B-10 — A10 と plan 自身の実装順が正面衝突する

判定: **real / blocker**

根拠:

- 出所は「親 docs 確定後に契約逐語を渡し、変えたら即同期」とする (`docs/archive/worklog-phase3-0801-89.md:48-53`)。
- proposed A10 も同じ逐語を置く (`PLAN:372-376`)。
- しかし plan は checker U1 と docs U2 を U0 後に並行可能とする (`PLAN:499-509`)。つまり親 docs 確定前に実装 worker を投入する。

失敗シナリオ: U1 が `guards.md` の未確定 path/ID/condition を plan から実装する。同時に U2 が前置きや所属 ID を変更する。「即同期」は進行中 worker の既読 context を巻き戻さず、旧契約由来のコードを判別する digest もない。

必要なのは契約 files の SHA-256 を worker input と結果へ束縛し、受入時に同じ hash を照合すること。散文だけでは TOCTOU を止めない。

影響: **受理集合と参照**が分岐し、checker が docs と異なる条件を機械的に正本化する。

### B-11 — A3/A4/A6/A7/A8/A11 も事故を閉じ切らない

判定: **real（強度は行ごとに異なる）**

| 候補 | stale 判定 | proposed 文を通る反例 | 必要な封じ | 変わるもの |
|---|---|---|---|---|
| A3 | 非 stale。O20 は handoff だけ (`operations.md:118-123`) | 新 qsub は `-o/-e` を指定しても、前 attempt が既定 `.o/.e` を残していれば `git add -A` 汚染は残る。proposed 文に pre/post root scan がない (`PLAN:330-334`) | qsub argv の固定と worktree root の new `.o/.e` postcondition | clean-tree **受理集合** |
| A4 | **部分 stale**。M05 と tool が競合 abort を既に機械化 (`mutation.md:29-36`) | lock key は `sha256(str(repo))` (`tools/mutation_harness.py:1814-1835`)。別 worktree の同一 repository は別 lock。テストも同一 path 競合だけ (`test_mutation_harness.py:698-704`) | git common-dir 等へ scope を束縛するか、「同一 checkout lock」と正直に狭める | mutation **台帳**の走行帰属 |
| A6 | 非 stale。現行 G01 は brief 前期限を持たない (`core.md:42-45`) | constructor/import だけの「最安生死確認」を green にし、実 caller path が死んでいても proposed 文を満たす (`PLAN:348-352`) | witness path・driver・合否条件を brief に exact 化 | brief/計画 **参照** |
| A7 | 非 stale | `「全拒否分岐を外れる」` 自体を upstream classifier が evasion と判定し得る。出所が要求した branch file:line 対応も proposed 文から落ちている (`worklog.md:791-795`, `PLAN:354-358`) | prompt template と実際の preflight 投入結果 | review **台帳** |
| A8 | 非 stale | worklog が誤って「完了」と書く。一次資料との照合が不一致でも proposed 文は brief を作らず「照合結果を返す」だけ (`PLAN:360-364`) | 「一次資料でも完了を確認できた場合だけ」に条件を狭める | requested task の **台帳** |
| A11 | **部分 stale**。M01 は二重理由変異を既に登録禁止 (`mutation.md:5-10`) | 同じ文字数・異なる UTF-8 bytes の replacement を人が byte 中立と誤認する。harness は old/new の byte 長を検査しない (`mutation_harness.py:284-290`) | harness に `len(old.encode()) == len(new.encode())` 型の機械 gate。ただし余裕内の非中立変異まで一律拒否する根拠は別途必要 | mutation **受理集合** |

規律だけで扱えるのは、条件を修正した A5/A6/A8 と、実差分同値性を人間が証明する限定版 A9。A1/A2/A3/A4/A7/A10/A11 は launcher、postcondition、実投入、hash、byte 検査のいずれかが必要である。

### B-12 — 「9 件」の外延が存在しない

判定: **real**

根拠:

- brief は「stale を除く 9 件」と記録する (`BRIEF:113-115`)。
- candidate 表は A1〜A11 の 11 行 (`BRIEF:73-85`)。
- stale とされたのは `[T-328](a)` と `[T-264](a)/[T-279](100)` で、いずれも A1〜A11 の表へ採番されていない (`BRIEF:58-60`)。
- plan は実際に A1〜A11 全 11 文を加算し、合計 1,463 bytesとしている (`PLAN:314-398`)。

失敗シナリオ: 段 4 が「9 件を統合した」と記録しながら、実際の reference には 11 件が入る。逆に 2 件を後から除くと byte 表・cap・変異対象が変わる。

影響: **台帳と reference 外延**が不一致になる。A2 は現行 foreground wrapper と重複しつつ一次資料を満たさず、A4/A11 も部分 stale なので、単純に「末尾 2 件を除く」とは決められない。

### B-13 — 現行 byte 表は再現するが、移設後見積りは再現不能

判定: 現行値への攻撃は **refuted**、移設後見積りは **real finding**

独立計数結果:

- core 8,537
- workers 4,623
- mutation 3,682
- operations 8,356
- 合計 25,198
- command 8,907

`tools/check_docs.py` は `newline=""` で UTF-8 decode し、`len(text.encode("utf-8"))` で測る (`:2669-2686`)。現行 LF 文書では `wc -c` と一致する。移設 slice 8 件と A1〜A11 の各 bytes、合計 1,463 も再現した。

再現できないのは次。

- `guards.md` 152 bytes / `hang.md` 133 bytes の exact prose がない (`PLAN:53-61`)。
- command の新しい段 dispatch 行が exact text でない (`PLAN:269-312`)。
- A1/A2 の衝突解消文は 248 bytesだが追加表に含まれない (`PLAN:384-398`)。
- したがって 26,946、入口 9,265、余裕 254 は、実際に land する逐語の計数ではない。

失敗シナリオ: author が説明から前置きを起草し、旧共通義務や A1/A2 bridge を入れる。実装後に ceiling 超過または数 bytes の余裕しかないと判明し、そこで安全文を削る圧力が発生する。

影響: **reference 受理集合**と予算台帳が未確定 prose に依存する。exact prose を段 4 で凍結してから再計測しなければならない。

### B-14 — 「非軽量」の結論だけでは、未消化の重い gate を代替できない

判定: **real**

`BRIEF:4-5` は受理集合変更だけを理由に非軽量とする。しかし `DW-C00` は設計択一の分岐、正しさ防壁、受理集合変更を独立 trigger とする (`core.md:11-15`)。

未消化なのは次。

- P1/P2/P3 は明示的な設計択一である。
- 新 reference family への制度一般化について `DW-G03` の独立 2 例を brief が立証していない (`core.md:52-55`)。
- P3 の恒久 residue tool を採る場合、`DW-G01` の brief 前生死確認がない。plan が P3 不採用を推奨しても、段 4 が採用へ反転するなら段 1 まで戻る必要がある。
- D94 の dev-wave 固有却下判断を開かず、D110 だけを先例としている。

失敗シナリオ: 段 4 が P3 または 27,200 ceiling を選び、「既に非軽量レビュー済み」を理由に G01/G03/D94 supersede を省略する。

影響: **台帳と受理集合**に、根拠のない family 一般化または恒久 tool が入り込む。

## 総括

最も重い 3 件は次。

1. **B-1**: sibling root で総量上限を 25,200 → 27,200へ隠れて引き上げ、D94とD110の双方を外している。
2. **B-2**: 発火条件の逐語を固定しないため、path/IDを維持したまま安全義務を条件付き・遅延発火へ弱められる。
3. **B-7**: A1/A2 の解消規則が正本に入らず、foreground を既に要求する O01へ重複文を足す一方、`nohup` が必要だった実測を捨てている。

採否は **NO-GO**。

段 4 で少なくとも次の択一を明示裁定する必要がある。

- 総量を **25,200 のまま維持して縮約・候補選別する**か、27,200 への引上げをユーザー再裁定へ返し D94 を明示 supersede するか。
- A1/A2 は **outer 専用 job が child の完了まで寿命を所有する foreground 方式**か、当該 surface では `nohup` が不可欠と認め別 launcher にするか。両方を散文で併存させない。
- consumer scope に skill、`docs/README.md`、failure erratum、skill literal gate、外部 supervisor を含めるか、それらを scope 外として「無損失・consumer 閉包」を主張しないか。