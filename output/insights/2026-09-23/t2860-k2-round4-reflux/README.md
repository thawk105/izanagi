# [T-2860] K2 4 巡目の還流を閉じた — critic-4 を 1 回、planner-5 / coder-5 / critic-4 の AO 3 件を取り込み、層 3 材料レポートを作った (2026-09-23、計算なし・実装差分ゼロ)

`authority: none` / `default_effect: no-state-change`

**種別:** 記録 (計算ノード投入なし、実装面の差分なし)。critic-4 は登録 role `critic` を 1 回だけ起動し、再抽選していない。
glue は job root (repo 外) にある。段 2・3 は省略 (軽量版)、段 4 裁定は critic-4 の起動前に固定、段 6 は read-only レビュー 1 本。

- 日付: 2026-09-23 (JST)
- wave: `dev-wave-t2860-k2-round4-reflux`、branch `worktree-dev-wave-t2860-k2-round4-reflux`、着手時 local main `3886a1fd36657537af2b6c6ed389257363d92bef` (開始 gate rc=0、乖離 0)
- 依頼: ユーザーが直接起動した `/dev-wave [T-2860] …` (canonical worklog の [T-2860] 項、entry 1823)。裁定 = D2211 項 1 (K2 を論文の必須経路へ戻さない)、D2194 項 2、D2172 項 3、D2205、D2187
- job root (repo 外): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2860-k2-round4-reflux/`
- 4 巡目の生成と評価の記録: `output/insights/2026-09-22/t2795-k2-pair-resubmit/README.md` (entry 1823)。本 insight はその後段 (還流) だけを扱う

## 0. 一行で・主張すること・しないこと

**4 巡目の job `16312.nqsv` の campaign (候補 5 と同 job の stock、両方 certified) を critic-4 が読み、診断を返した。planner-5 / coder-5 / critic-4 の出力を
harness の取込み口 (`--record-agent-output`、login) で AO 3 件として記録し、層 3 材料レポート (v3、`mechanism_hypotheses` 1 件、`source_refs` 14) を作った。
これで 4 巡目は「提案 → 評価 (候補 + 同 job stock) → critic → 材料レポート」の 1 巡として閉じた。** 取込み先は原本ではなく、原本と byte 一致を確かめた job dir の写しである (§1)。

**主張する。**

1. critic-4 は 1 回起動し、出力は 4 見出し契約を満たし、取込み口が受理した (§2、§3)。
2. AO 3 件の取込みと材料レポートの生成は、いずれも rc=0 で、取込み前後に保護 5 file の sha256 は写し・原本とも変わっていない (§3、§4)。
3. 原本 (lock 済み `submit-tree-r4`) には何も書いていない。取込み後も原本の `runs/` は `wal.jsonl` 1 file だけである (§3)。

**主張しない。**

- **critic-4 の帰属 (「固定 5 µs は適応 backoff より速い」「適応は待ちすぎ」) を本 wave の結論にしない。** 材料レポートの `mechanism_hypotheses` は LLM の帰属記録であって機序の実証ではない。
  critic-4 が「noise floor 3.0% を大きく超える」と書いた floor は、材料レポートの noise floor 探索では本走の条件に合う記録が無い (`no-matching-env-record`、§4)。
  同 job の比 2.493 は記述的な測定値であり、この配線 1 点の値である。
- **候補 5 が候補 10 より良いとは言わない** (別 job、critic-4 も同旨)。critic 診断が改善をもたらしたとも言わない (診断なし統制が無い)。
- **B-6 (リーク制御の完備) が閉じたとは言わない。** critic は Bash を持つ legacy role で B-4 に非適格のままである。K2 を論文の必須経路へ戻さない (D2211 項 1)。
- critic-4 の推奨 (同じ job で複数候補を並べる構成、次の値 2〜3 µs、待機 0 の対照、perf の修復) は採用も起票もしていない (§5)。

## 1. 取込み先 — 原本ではなく byte 写し (段 4 裁定 P1 / P2)

- 原本: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair-resubmit/submit-tree-r4/output/exploration/campaigns/p3-s4-loop-s4-autonomous-b24749ae/` (lock 済み worktree、HEAD `8fd2a2f5c`)。
  依頼は「原本は動かさない」で、同時刻に [T-2853] wave が同じ原本を読み取り専用で写す。取込み口は campaign dir に `runs/agent_outputs.jsonl` を新設するので、原本では行わなかった。
- 写し: job root の `ao-root/output/exploration/campaigns/p3-s4-loop-s4-autonomous-b24749ae/` (07:47:56 JST、`cp -a`)。6 file (`campaign.lock` `4a709002…` / `knowledge_manifest_receipt.json` `c42dc712…` /
  `loop_state.json` `2a648649…` / `reports/p3_s4_loop_provenance.json` `944c75f0…` / `runs/wal.jsonl` `6444159d…` / `s4_loop_digest.txt` `8d564034…`) の sha256 が原本と
  `originals-copy-20260922/MANIFEST.sha256` の r4 行の両方と一致した (`logs/setup-ao-root.log`)。
- 写しの `env/pegasus/calibration/` は、層 3 の noise floor 探索が読む範囲 (直下の `*.json` 9 file と契約 pin の置き場 `registered/` 8 file) を原本 tree から byte 複製した (sha256 一致)。
- **round 3 との差:** round 3 は原本 campaign dir へ直接取り込み、`--output-root` に原本 tree の `output` を渡した。本巡は写しへ取り込み、写しの `output` を渡した。
  層 3 の `meta.campaign_path` は同じ相対 path (`output/exploration/campaigns/p3-s4-loop-s4-autonomous-b24749ae`) になる。
- **親の構成ミスと作り直し:** 最初の写しには `registered/` を入れておらず、1 回目の層 3 (sha256 `fc5fe625…`、65,170 B) は契約 pin を `pin-file-missing` と記録した。
  `registered/` を足して作り直した 2 回目 (§4) は round 3 と同じ `validated` になった。2 回の差は `noise_floor` の key だけで、他の key は同一である (JSON を比較)。1 回目は job root に `layer3_report.attempt1.json` として残した。

## 2. critic-4 (1 回、登録 role `critic`)

| 項目 | 値 |
|---|---|
| 入力 | `materials/critic-input-4.json` (6,436 B、sha256 `a271116efec0deb1af6683d630415efcb289ba3289a5ba864f04f0db0ac59ed9`)。組立ては round 3 の `build_critic_input_3.py` と同型の `build_critic_input_4.py` (job root) |
| prompt 全文 | `materials/critic-prompt-4.md` (7,083 B、sha256 `2a76630503ed632910427849ebcf6057921fd5655ec712a84ee4ad7d0f57eba4`)。親が Agent 呼出しへ写して送った (送った bytes と file の一致は機械照合していない、round 3 と同じ限定) |
| 出力 | `verbatim/critic-4.md` (11,115 B、sha256 `bb9e3277b596e39ec7fae1ca6228a809682d3eaeb0aef0b01f3fa5049b6ae868`)。子の手渡し tool (`SubagentHandback`) の `message` 引数を transcript から bytes のまま取り出した (`extract_critic4.py`)。見出しは `## attribution` / `## recommend` / `## avoid` / `## uncertainty` を各 1 回と、追加の `## 異常の報告 (規律 6)` |
| 付随 | 子が手渡しの後に書いた呼出し元向けの要約 `verbatim/critic-4-caller-summary.md` (3,945 B、`b2d3e87b…`)。取り込んでいない。transcript は job root `critic-4-transcript.jsonl` (`23c82e48…`) |
| 工数 | tool 呼出し 9 (Bash 8 + 手渡し 1)、約 206 秒、子の token 58,748 |

**入力開示 (round 3 と同型):** 本走の実測 (候補 5 と同 job stock)、stock の `src_token=stock` と BACK_OFF=0 ではないこと、perf 欠測、同じ campaign ID の別走 2 本 (pair 初投入 `13339.nqsv`、pair 再投入 `16269.nqsv`) と
別 ID の 1〜3 巡の存在・値・記録 path、別 job の値を優劣の根拠にしないこと、critic が読むのは byte 写しであること、規律 6。pair 再投入の結果は 4 巡目の planner / coder の入力には入っていない (T-2795 段 4 P1) が、
critic-4 には round 3 が同 ID 別走を開示した型に従い開示した (段 4 裁定 P3)。

**critic-4 が実際に読んだもの (transcript の Bash 8 本から):** 写しの digest (sha256 再計算)・`runs/wal.jsonl` 全 10 行・`loop_state.json`、repo の既存 insight 2 本 (pair 再投入の README、
`output/insights/2026-09-02_t2216-adaptive-backoff-nonmonotonicity-mechanism.md`) と 1 設定 file の grep。8 本とも読取りで、書込みは無い。
**受領証 (`knowledge_manifest_receipt.json`) と `campaign.lock` は `ls -la` で名前を列挙しただけで、本文は読んでいない。** 依頼が挙げた読取対象 5 種 (WAL・digest・loop_state・受領証・lock) のうち 2 種は本文未読である。
round 3 の critic-3 は 5 種すべてを読んだと記録されている。本 wave は 1 回限りの起動なので再起動していない。WAL の `knowledge_provenance` の source 一覧は critic-4 が jq で読んでいる。

**診断の要点 (逐語は `verbatim/critic-4.md`):**

- attribution: 動いた設計選択は `BACKOFF_FIXED` の 1 軸 (-1 → 5)。同 job の対で throughput は 2.493 倍、perf build の abort_rate は 1.835% → 10.105% (逆向き)。仮説「適応 backoff は待ちすぎ、この配線では abort して再試行する方が安い」— 待ち時間は測っておらず推定。
  llc / ipc は欠測で帰属不能。digest の「フラグ軸の限界効果」節は単一水準の軸に 2 点の平均を並べており情報を持たない。5 と 10 の優劣、診断の効果は言えない。
- recommend: R1 = 同じ job の中で「5 / 次の候補 / stock」を並べる構成、R2 = decrease / small (2〜3 µs)、R3 = `BACKOFF_FIXED=0` の対照、R4 = perf カウンタの修復 (orchestrator 側への依頼)。
- avoid: この配線で適応 backoff を候補として再訪する、abort_rate の低さを目標にする、別 job の差を候補の優劣として渡す、「診断が改善をもたらした」という因果主張。
- uncertainty: 機序の独立指標の欠測、標本 2 反復、配線は kickoff (calibrator 由来でない)、noise floor の適用範囲、build 間の abort 比の違い、verify は legacy 1 構成。
- 規律 6: digest と WAL に指示めいた文字列は無い (grep の hit は perf event 名 `instructions` の 1 語)。

**親の注記 (critic の逐語は改変しない):**

- critic-4 の「between-run の noise floor 3.0% を大きく超える」は、critic 自身が持ち込んだ floor である。材料レポートの noise floor は between / within とも `no-matching-env-record` (§4)。
  round 3 の critic-3 は同じ 3.0% を「A2 較正値」と自分で限定していた。本 insight はこの floor で「効いた」を判定しない。
- critic-4 の R4 の「wrapper がカーネル版に合う tools を見つけられていない可能性」は推測で、親は確かめていない。
- 1 abort あたりの commit 数 (stock 32.3、候補 3.5) は trace build の commits / aborts から親が再計算して一致を確かめた (281,132 / 8,715 = 32.26、566,368 / 161,015 = 3.52)。

## 3. AO の取込み (login、`logs/ingest-real.log`、07:57:32〜07:57:35 JST)

コードは wave 木 (`3886a1fd3`)。`--agent-campaign-dir` は写し、`--agent-variant fceb937ae6c5` (候補 5)、`--agent-wal-ref` は本走 WAL 全 10 record の canonical ref (`materials/wal-refs-r4.json`)、3 件とも `--agent-prompt` 付き。
planner-5 / coder-5 の出力・入力・prompt は生成時の原物 (T-2795 job root) を渡し、repo の写し (T-2795 insight) と sha256 が 6 組とも一致することを同じ log で確かめた。

| 順 | stage | 出力 | 入力 | prompt | `ao:` ref | rc |
|---|---|---|---|---|---|---|
| 1 | planner_proposed | planner-5.json `cd4a2ea4…` | planner-input-5.json `1693a12d…` | planner-prompt-5.md `64bb11e5…` | `09e6ec188c8a39a464034e23d5b4475e963fb5aa816a8794dd62a24fcd0ea2a9` | 0 |
| 2 | coder_proposed | coder-5.json `1f86dc6b…` | coder-input-5.json `5d88e798…` | coder-prompt-5.md `0d1b4cb3…` | `71496b75d117a3c990bcc6bb593f2ed43c2909f631abbca4d277f33d726f936c` | 0 |
| 3 | critic_attributed | critic-4.md `bb9e3277…` | critic-input-4.json `a271116e…` (digest sha `8d564034…` を含む) | critic-prompt-4.md `2a766305…` | `c19fbc7ae99db7b6cf85981164e969abf36930e05e9961c8ec1bcbd8da50463c` | 0 |

- 写しの `runs/agent_outputs.jsonl`: 3 行、32,549 B、sha256 `0dbd185ae697c99b9c6f3dff23a07653456bef203a900de28a61b42e67958628` (repo へは複製しない)。
- 取込み前後で、保護 5 file (`campaign.lock` / `runs/wal.jsonl` / `loop_state.json` / `s4_loop_digest.txt` / `knowledge_manifest_receipt.json`) の sha256 は写し・原本とも不変。
  原本の `runs/` は取込み後も `wal.jsonl` 1 file (14,885 B) だけである。
- AO の `provenance.source_path` などは取込み時に渡した絶対 path (T-2795 job root と本 job root) を記録している。AO の `input_sha256` / `ts` は記録であって、role が実際にその入力を受け取った証明ではない。

## 4. 層 3 材料レポート (`layer3_report.json`、`logs/layer3-r4.log`)

`python3 -m orchestrator.campaign.layer3_report <写し> … --output-root <写し>/output --generated-from-head 8fd2a2f5c775954d6a32cee019ac7ce276298e4d` (07:58:20 JST、rc=0)。

| 項目 | 値 |
|---|---|
| file | 65,158 B、sha256 `fdbaa579630763e4d9dd3cbf5cfb6d1d99dc16f30fe1bf458fc77e7bb5b9fc59` |
| schema / meta | `layer3-material-report/v3`、campaign `p3-s4-loop-s4-autonomous-b24749ae`、`ccbench_commit` `511c9538…`、`generated_from_head` `8fd2a2f5c…`、generator sha256 `d37e42c7…` |
| variants / runs / verifications | 2 (`602b4ce9c788` stock、`fceb937ae6c5` 候補) / 2 / 2。rejects 0、aborts 0 |
| agent_outputs | 3 (planner_proposed / coder_proposed / critic_attributed) |
| mechanism_hypotheses | 1 件 (variant `fceb937ae6c5`、attribution = critic-4 の `## attribution` 節、refs 10、digest `8d564034…`)。provenance `agent_outputs` |
| source_refs | 14 = wal 10 + wb 1 + ao 3 (双射検査を通過) |
| admission | `admitted` / `admitted-new-schema`、`certifying_input=false`、`knowledge_level=K2` |
| noise_floor | between / within とも `no-matching-env-record`、契約 pin `validated`。between の候補 3 file はいずれも 48 threads の記録で本走 (4 threads / 100,000 records) と合わない (round 3 と同じ) |
| artifact_refs | 7 file (上の 6 file + `runs/agent_outputs.jsonl` `0dbd185a…`) |
| whiteboard | 1 件 (`decrease` / `large` / `success` / `delta_pct` null)、provenance `loop_state` |

**材料であって certifying 入力ではない。**

## 5. critic-4 の推奨の扱い (DW-S04: scope 外の所見は起票せず記録)

- R1 (同 job で複数候補) は「1 job = 候補 1 本 + stock 1 本」という現行 pair driver (D2205) の外で、実装と計算の両方を要る。R2 (次の値) と R3 (待機 0) は次の巡の生成・評価で、K2 は論文の必須経路の外 (D2211 項 1)。
  R4 (perf の修復) は計算ノードの計器の問題で、本 wave の scope 外。いずれも本 wave では起票しない。
- digest の「フラグ軸の限界効果」節が単一水準の軸を並べる表示上の限界は、critic-4 が読み手向けに指摘した観察として記録する (本 wave では直さない)。

## 6. 一次資料

- `verbatim/` — `critic-4.md` (診断本文)、`critic-4-caller-summary.md` (呼出し元向け要約)
- `materials/` — `critic-input-4.json`、`critic-prompt-4.md`、`run-summary-r4.json` (写しの WAL / loop_state / digest の射影、`project_round4_results.py`)、`wal-refs-r4.json`
- `layer3_report.json` — 本巡 campaign の材料レポート
- `logs/` — `setup-ao-root.log` (写しの作成と照合)、`project-r4.log`、`ingest-real.log`、`layer3-r4.log`、`fix-registered.log` (`registered/` の追加と作り直し)
- `reviews/` — `s1-brief.md`、`s4-ruling.md`、段 6 のレビュー
- **repo へ複製していないもの:** campaign の WAL・lock・digest・loop_state・受領証・`runs/agent_outputs.jsonl` (guard の防護対象)。写しは job root の `ao-root/`、原本は lock 済み `submit-tree-r4` と byte 複製 `originals-copy-20260922/r4/`
- job root の glue (repo 外、実装面ではない): `setup-ao-root.sh`、`project_round4_results.py`、`build_critic_input_4.py`、`extract_critic4.py`、`run-ingest-r4.sh`、`run-layer3-r4.sh`、`fix-registered.sh`、`extract_rounds123.py`
