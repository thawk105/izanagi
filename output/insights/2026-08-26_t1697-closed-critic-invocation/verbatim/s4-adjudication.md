# 段 4 裁定 — [T-1697] 閉じた critic invocation

段 3 は 2 レンズ並列。sol (機構の閉じ具合) 13 件、luna (事前登録契約と scope) 14 件、計 27 件。
**26 件を real、1 件を refuted と裁定する。** うち 13 件を本 wave で採用、5 群を scope 外として
裁定パッケージへ返す。

裁定直前に main を再確認した: `d8f777a4` → `33cb6321` (docs 2 land と `trial_registry.py`)。
本 wave の編集面・待ち手・launcher の bytes に触れないため、取り込みは受入投入時に行う。
裁定 inbox に T-1697 の新しい更新は無い (entry 958 でも持ち越し)。

---

## 1. refuted (1 件)

**luna-F2 「role file を増やさなくても role I/O contract pin を迂回している」— blocker としては
refuted。**

`review_ledger.ROLE_IO_CONTRACTS["critic"]` は入力 `("digest",)`・出力 4 field を pin する。
しかし 8c (`p3_autonomous_workload_trial.py:311-318`) は**同じ `critic` role に対して既に別 schema**
(出力 5 field、`reverse_recommended` 追加。入力も `digest` 単独ではない) を projected 起動で使っており、
それが ledger pin と共存したまま main で緑である。したがって同 pin は Codex adapter 側の契約であって、
projected route の route-local schema を禁じていない。**先例が main に実在するため、pin 迂回では
ない。**

ただし所見の是正案「route-local に閉じ、global contract を変えない」は正しいので採用する (A8 に含む)。

---

## 2. 採用する是正 (13 群)

### A1 — trust root を呼び手に選ばせない (sol-1, sol-4)

`repository_root` を caller が渡せると、偽 root を渡すだけで非開示検査を通せる。
`runner` / `executable` を caller が渡せると、CLI を一度も起動せずに 3 性質すべてが自己整合した
receipt を捏造できる。

- `repository_root` は module 位置から導出する。引数を残すなら導出値との exact equality を要求し、
  相違は invocation 前に拒否する。
- certified mode は `runner is subprocess.run` を要求する。executable は解決後の絶対 path と
  sha256 を receipt へ載せる。
- 注入可能 mode の receipt は `evidence_class="test-only"` を持ち、pair 検査は
  `evidence_class="certified"` 同士でだけ通す。

**成果物影響:** 未是正なら偽 receipt の block が受理集合へ入り、certified 選択の候補列が偽の
閉鎖証拠を参照する。

### A2 — 第 2 の arm 切替点を作らない (sol-7, luna-F4)

`invoke(arm=)` を**削除する**。arm は controller 生成時に `cfg.search_config["reflux"]` から
一度だけ導出し、以後 private immutable とする。呼び手は digest も reflux も直接渡せない。

**成果物影響:** 未是正なら `arm` field と実 digest の中身が食い違う receipt が成立し、
赤入り off digest が off 標本として受理される。

### A3 — pair は単一 factory で封をする (sol-8)

on/off controller は単一の sealed pair factory でのみ同時生成する。`CrossRoleSessionTracker` を
**必須共有**とし、receipt へ provider instance id と neutral root identity を載せて、pair 検査で
相違を要求する。controller ID の相違だけを provider 分離の証拠に数えない。

**成果物影響:** 未是正なら provider 状態を共有した block が「fresh」と表示されたまま正規標本へ入る。

### A4 — digest と coarse result を同一 snapshot へ束縛する (sol-9, luna-F3, luna-F5)

receipt に `admitted_view_sha256` (WAL prefix hash)・`loop_state_sha256`・`iteration` を載せ、
digest と `whiteboard[-1].result` が同じ snapshot 由来であることを invocation 時に検査する。

**controller の義務は「束縛と露出」まで。**「両アームの precursor が同一か」の実験的判定は
実走側 (B-4 の block 設計) の義務であり、本 wave では pair 検査が hash の相違を**報告できる形**に
するに留める。同一性そのものを controller が強制すると、B-4 の block 設計を先取りすることになる。

**成果物影響:** 未是正なら別試行の coarse result と最新 digest を組み合わせた invocation が
有効 receipt になり、停止理由と次 synthesis の対応がずれる。

### A5 — receipt は自己申告と証拠を分離する (sol-10)

provider が定数で書く値 (`fresh_context`, `observed_tool_events`, `capability_lowering`) は
`claimed_*` 側へ置く。raw envelope の sha256、payload bytes の sha256、argv の canonical hash を
`evidence_*` として必ず載せ、consumer が事後に再検証できる形にする。

**成果物影響:** 未是正なら実値を変えずに receipt の受理集合だけを恒真化でき、台帳の参照が
検証不能になる。

### A6 — `projection_sha256` は closure を hash する (sol-11)

新 module bytes だけでは、provider の argv 構成・canonicalizer・`make_critic_digest`・
identity renderer が変わっても同じ hash になる。closure manifest
(新 module + `claude_projected_provider.py` + `p3_s4_loop.py` + `orchestrator/critic/digest.py` +
`.claude/agents/critic.md` + mediated contract 文字列) の canonical hash を projection hash とする。

**成果物影響:** 未是正なら意味の違う block が同一 projection 群へ併合され、効果量と比較可能性が壊れる。

### A7 — 非開示の保証範囲を名前で正直にし、安価な範囲だけ広げる (sol-5, sol-6, luna-F8)

- receipt の field 名を `exact_identity_literals_absent_from_canonical_payload` とし、
  保証を「exact byte 非出現」に明示縮小する。
- 安価な拡張として、**JSON escape decode 後の view** と **path の lexical normalization 後の view**
  の 2 view も検査に足す。各 view に対応する負例を対で置く。
- variant / src token / genome label / WAL 由来自由文といった**間接識別子は閉じない**ことを
  receipt の非保証 field と docs の両方へ明記する。

**成果物影響:** 未是正なら semantic な path 開示を「非開示」として受理し、判定不能であるべき block が
成立へ誤分類される。

### A8 — critic 応答は検証して返すだけ (luna-F7)

controller は critic 応答を exact schema で検証し、**データとして返すだけ**とする。
`reverse_recommended` の bool 導出・proposal への書込み・`LoopState` の fold を一切しない。
事前登録の前提条件 5 (`prior_critic_reverse` の供給規則) は**未充足のまま**明記する。

**成果物影響:** 未是正なら `reverse-exhausted` の発火が変わり、試行台帳の停止理由と標本数が変わる。

### A9 — 失敗した invocation も台帳に残す (luna-F9)

invocation_id は閉じた字種で検査し、receipt は exclusive create する。開始 receipt と
terminal receipt (success / failure / timeout) を必須化し、失敗した role query も予算と台帳に残す。

**成果物影響:** 未是正なら失敗 query が台帳から消え、片アームだけの再試行や receipt 差替えが可能になる。

### A10 — sanctioned な起動口を置く。ただし driver への必須配線はしない (sol-13, luna-F1)

新 module に薄い CLI entrypoint を置き、機構が実際に到達可能であることを保証する
(道具は親が実データで一度通すまで完成でない)。runbook には
**「legacy `Agent(subagent_type='critic')` 経路は B-4 非適格」**を明記する。

**driver が receipt 無しを protocol violation として拒否する配線は採らない** — 段 4 driver の
受理集合を変える変更であり、前提条件 3 の範囲を超える (B3 として裁定パッケージへ)。

**成果物影響:** 未是正なら閉じた module が一度も使われないまま旧 critic が候補を生成でき、
材料レポートの B-4 行が非閉鎖 block を受理する。

### A11 — 既存負の対照の docstring を更新する (luna-F12)

`test_p3_s4_loop.py` の 1833 行と 1951 行の docstring は「閉じた critic invocation が要るが
本 wave の scope 外」と書いており、本 wave 後は歴史的に偽になる。この 2 本を更新する。
**1811 行の docstring は該当文を含まない**ことを実測済み (luna の指摘どおり、親 prompt の
「3 本」は誤り) なので触らない。

D824 決定 2 の義務文は残す。残す文は「本 test が固定するのは harness 生成 digest の性質だけであり、
critic role 自体の能力遮断も専用 controller の実効 lowering も証明しない」。

**成果物影響:** 未是正なら焦点走の参照から「閉じた経路は未実装」と誤読され、証拠リンクが食い違う。

### A12 — docs は過大表示しない (sol-12, luna-F10, luna-F11, luna-F14)

- §6 前提条件 3 は「機構は用意された。ただし正式経路への必須配線と §5 の事前 commit は未了」と書く。
  **発効宣言はしない。**
- §7.2 の 3 項 (file-drawer、off の閂、既知の生存変異) は**そのまま残し**、専用 route の
  exact capability lowering だけを追記する。
- §8 の「証明しないこと」3 項をそのまま残し、「新 test と receipt が示すのは専用 invocation の
  declared tools と観測事実だけ」と限定を足す。§10 からは項目を削除しない。
- 親 brief の成果物影響も縮小する。**前提条件 3 だけでは B-4 は走らない** (§5 の全欄、
  floor 再実測、前提条件 4〜8 が未了)。正しい書き方は「閉じた invocation と route-local receipt が
  利用可能になる。certified 選択・材料レポート・試行台帳の値は本 wave では変わらない」。

**成果物影響:** 未是正なら wave 完了だけで B-4 証拠が前進したかのように記録されるが、
実値・受理集合・台帳行はいずれも増えない。

### A13 — 「道具ゼロ」の主張を縮小し、実 CLI の負の対照を 1 本走らせる (sol-2, sol-3)

sol の指摘は正しい。`observed_tool_events=[]` は観測ではなく**定数**であり、
`permission_denials==[]` は「拒否記録が無い」、`server_tool_use==0` は「その集計面の未使用」でしかない。
親の liveness 実測 1 回も「当該 payload では自己実行を観測しなかった」以上を意味しない。

- brief の該当文を上記の縮小形へ書き換える。
- 親は段 6 で**実 CLI に対する負の対照を 1 本**走らせる: payload 内に
  `digest.py --campaign-dir` の実行を促す文字列を置き、(i) critic がそれを実行できないこと、
  (ii) 応答が exact schema を保つこと、(iii) envelope の `permission_denials` と
  `server_tool_use` が空/0 のままであることを観測して worklog に記録する。
  この文字列は**親が管理する対照であり、外部由来の指示ではない** (規律 6 の適用対象外)。
- fake runner 側の test では、`permission_denials` 非空・`num_turns=2`・`server_tool_use>0` の
  envelope を**拒否する**ことを固定する。

**成果物影響:** 未是正なら receipt の「能力遮断」欄が過大表示になり、off 汚染 block を成立扱いにする。

---

## 3. scope 外 — 裁定パッケージへ返す (5 群)

- **B1 (sol-2 の残り):** OS sandbox の追加、または pinned CLI の raw tool descriptor と
  全 tool event 面の保存・検証。CLI が完全な tool event 面を出さないため、閉じるには別機構が要る。
  本 wave では 性質 1 を「declared + 観測された負の事実」までとして正直に記録する。
- **B2 (sol-6 の残り):** B-4 専用の型付き digest renderer で green/red 双方の identity-bearing field を
  中立 label へ射影する案。**採らない** — `make_critic_digest` の下流に第 2 の描画経路ができ、
  両アームの digest 内容が変わる。測るべき差以外が動くため、事前登録 §3.1 の切替点固定と衝突する。
- **B3 (sol-13 / luna-F1 の残り):** 段 4 driver が「有効 pair receipt が無い critic 応答」を
  protocol violation として拒否する配線。受理集合を変えるため本 wave の scope を超える。
- **B4 (sol-12 の残り):** §5 欄の実走前 commit と、model snapshot の期待値を controller の必須入力に
  する admission record。B-4 実走準備そのものであり scope 外。
- **B5 (luna-F13 の残り):** runbook の legacy 手順を B-4 非適格と明記する以上の改訂
  (専用 CLI を参照する新節の追加など) は、実走設計が決まってから。

---

## 4. 変異事前登録 (DW-M01)

**B-057 の既存 candidate は適用なし。** B-057 の candidate 49 件は freeze 族
(`docs/freeze-permanent-design-s2.md`、D76) 向けで、本 wave の編集面 (新規 2 file) には
対応する登録が存在しない。本 wave は新規に登録する。

各変異は「同じ入力を拒否する層が前後に無いこと」「無効化時の赤理由が一つに絞れること」を
実装後に確認してから本走する。確認できない変異は登録せず実効 gate へ再照準する。

|#|変異|期待|
|---|---|---|
|M1|非開示検査から campaign_id 禁止語を落とす|KILLED (campaign_id 負例のみ)|
|M2|非開示検査から repository root 禁止語を落とす|KILLED (repo root 負例のみ)|
|M3|非開示検査から campaign path 禁止語を落とす|KILLED (path 負例のみ)|
|M4|`repository_root` の導出値 equality 検査を外す|KILLED (偽 root 負例のみ)|
|M5|certified mode の `runner is subprocess.run` 要求を外す|KILLED (注入 runner 負例のみ)|
|M6|arm と `cfg.search_config["reflux"]` の一致検査を外す|KILLED (arm 不一致負例のみ)|
|M7|pair 検査の session 相違要求を外す|KILLED (session 再利用負例のみ)|
|M8|pair 検査の provider/neutral root 相違要求を外す|KILLED (provider 再利用負例のみ)|
|M9|payload の key 集合を exact でなく superset 許容にする|KILLED (余剰 key 負例のみ)|
|M10|critic 応答 parser の exact key 検査を superset 許容にする|KILLED (余剰 key 応答負例のみ)|
|M11|非開示検査の escape-decode view を落とす|KILLED (escaped 混入負例のみ)|
|M12|非開示検査の path 正規化 view を落とす|KILLED (`..` 混入負例のみ)|
|M13|receipt から raw envelope hash を落とす|KILLED (receipt field 検査のみ)|
|M14|failure terminal receipt を no-op にする|KILLED (失敗 invocation 負例のみ)|
|M15|closure manifest から provider を落とす|KILLED (closure hash 検査のみ)|

**過剰拒否の正例 (受理集合を縮小する wave の義務):**

- P1: 実 admitted fixture の on digest と off digest が非開示検査を通る。
- P2: `default_cfg(reflux=True)` から作った on controller が invoke に成功する。
- P3: 正常な 5 field 応答 (8c と同形) が parser を通る。
- P4: 正常な pair が `assert_b4_arm_pair` を通る。

---

## 5. plan v2 (段 5 へ渡す確定形)

段 2 プランの骨格 (新規 production 1 本 + 新規 test 1 本、既存 provider・切替点・role file 無変更) を
維持し、A1〜A13 を反映する。追加の編集面は次の 3 つだけ。

- `orchestrator/tests/test_p3_s4_loop.py` の docstring 2 本 (A11)。
- `docs/phase3-s4b-runbook.md` に legacy 経路の B-4 非適格を明記 (A10)。**親が編集する。**
- `docs/phase3-b4-reflux-ablation-preregistration.md` の §6.3 / §7.2 / §8 (A12)。**親が編集する。**

実装子が触るのは新規 2 file と `test_p3_s4_loop.py` の docstring だけとする。
