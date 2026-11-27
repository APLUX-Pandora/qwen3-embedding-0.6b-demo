# Web Demo

Complete [Install](../README.md#1-install) and [Get the model](../README.md#2-get-the-model). From the Demo root in the activated environment, run:

```bash
bash demo/run.sh --port 7860
```

Open `http://127.0.0.1:7860/` once the console reports that the Demo is listening. The status bar shows the device chip and model readiness.

- **Sentence similarity** opens first. Enter two sentences or select an example to fill both fields. Select **Compute similarity** to see cosine similarity on a scale from −1 to 1 and the encoding time. A higher score usually means the sentences are closer in meaning.
- **Document search** starts with a bilingual sample library. Expand a title to read the full text. Paste one document or upload one UTF-8 `.txt` file (up to 128 KiB), then select **Add and index**. Each input must fit the model's 8,192-token limit. The library holds up to 200 documents. Additions are shared by visitors to this instance and reset when the server restarts. Search results show up to ten ranked titles, excerpts, and scores. Try **Chinese query, English result** and **Paraphrased query** to find the same English document using two Chinese questions.

The performance panel shows model load and first query encoding separately. Encoding times cover the SDK call, including tokenization, and exclude request queueing, token counting for display, scoring, network, and browser rendering. Token counts include any query prefix and special tokens. Index timings cover encoding and building the index. They accumulate as you add documents.

Use `--model-dir` to select another downloaded model folder. To connect from another machine on a trusted network, add `--host 0.0.0.0` and open the device's address on the selected port. This Demo has no sign-in. Stop it with `Ctrl+C`.
