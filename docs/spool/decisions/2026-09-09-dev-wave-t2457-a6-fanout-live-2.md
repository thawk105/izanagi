---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-09
wave: dev-wave-t2457-a6-fanout-live
seq: 2
---

## {{D:certification-body-runs-on-job-number-zero-only}}. 認証 job body は job 番号 0 の rank だけで走らせ、他の rank は何も書かずに正常終了する

**決定:** NQSV の multi-node request では job script が全 rank で走る。認証 job body
(`tools/pegasus/paper_story_a2_certification.sh`) は必須環境検査の直後に job 番号 gate を置く。

1. `PBS_JOBID` が `<canonical な 10 進 job 番号>:<非空 request id>` でなければ `exit 2` で止める。
   先頭ゼロ (`00:` など) は形式不正とする。形を推測して続行しない。
2. job 番号が `0` でなければ、理由を stderr へ 1 行書いて `exit 0` で抜ける。durable path は
   1 つも触らない。非 0 で抜けると request 全体の失敗として読まれるので 0 で抜ける。
3. job 番号が `0` なら従来どおり続行する。既存の `${PBS_JOBID#0:}` と `#PBS -b 1` directive は
   変えない。
4. gate の位置は静的 assertion で固定する。**抜ける側の分岐そのもの**が compute-only 検査・
   durable path 検査・復旧 trap より前にあることを検査する。実走テストからは、この分岐だけを
   後ろへ動かす変異が見えない (変異 M4 が実測で 1 件も落とさなかった)。

D1810 の輸送設計 (単一 multi-node request、head から兄弟への ssh、head 生成の stdin secret に
よる HMAC、建て直し禁止、欠落・不一致は indeterminate) は一切変えない。本決定はその前提に
あった「job body は 1 回だけ走る」という暗黙の仮定を、実機の挙動に合わせて明示的な gate へ
置き換えるだけである。

**理由:**

- `-b 5` の実走で job script が 5 rank すべてで走り、rank 1〜4 が同じ compute 結果 file を
  作ろうとして 5 秒で失敗した。結果 file を実際に書いたのは head ですらなく rank 4 だった。
- rank>0 が即終了しても割当ノードは request に保持され、head から兄弟への ssh が通ることを
  `-b 3` の probe で実測した (45 秒後に `Execution Hosts` は 3 ノードのまま、ssh rc=0)。
  したがって兄弟 rank を生かし続ける機構は要らない。
- 修正後の実走は完走し、1 ノードの 4382 秒が 1057 秒になった。

**却下した選択肢:**

- **兄弟 rank を sentinel file で待たせる** — 割当が保持されることを実測したので、待たせる
  理由が消えた。新しい同期機構を足さずに済む。
- **job 番号の比較を数値で行う** — `00` を head と読むか非 head と読むかの解釈が要る。
  実機で観測された形は `0:` と `4:` だけなので、canonical でない表現は形式不正として
  fail-closed に倒すほうが、誤って複数 rank が走る側にも誰も走らない側にも倒れない。
- **非 0 rank を無出力で終わらせる** — 診断 1 行は gate が実機で発火した唯一の証拠である。
  NQSV 会計検査の正規表現は `^Request ID:` と `^Group Name:` の行に錨を打つので、この 1 行では
  発火しない (4 行入った `job.stderr` に対して `finish-group` が rc=0 で受領証を作ることを実測)。
