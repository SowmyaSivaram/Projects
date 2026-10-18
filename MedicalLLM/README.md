# Medical LLM

## Task 1: Data (cells 2–4)

- reads each compressed file one article at a time.
- Foreach article- pulls out the ID, title, abstract, year and language.
- Abstracts split into labelled sections are joined into one text.
- Only articles with abstract are kept and each one is written into JSONL file.
- load that file as a dataset
- drop abstracts shorter than 20 words, and adds word and character counts. 
- splitting the data into 95% training and 5% validation, using the fixed seed.
- cell 4 EDA- prints counts, length statistics, the top languages and the year range. It also draws two charts one of abstract lengths and one of publications per year.

## Task 2: Tokenization (cells 5–11)

- trained 4 tokenizers on the training abstracts- BPE, WordPiece, Unigram and byte-level BPE, each with a 16,000-token vocabulary. Each has its own text cleaning, word-splitting and decoding settings, and each is timed.
- BPE: 
  - Starts with single characters as its vocab, then repeatedly finds the most frequent adjacent pair in the training text, merges it into 1 token. 
  - Repeats until 16k tokens exist, so common words become single tokens and rare words break into pieces. 
  - A whitespace splitter runs first and discards the spaces, which is why the decoded text comes back with no spaces.
- WordPiece: 
  - Starts from characters and builds the vocab by merging pairs. 
  - Chooses merges by how much they improve the likelihood of the training text, not by frequency. 
  - Pieces that continue a word are marked with ##. 
  - Splitter breaks text at spaces and punctuation, so decoder re-joins pieces with extra spaces around punctuation.
- Unigram: 
  - Starts with a large pool of candidates, each with a probability and repeatedly removes the pieces whose loss affects the likelihood of the training data least, until 16K remain. 
  - It picks the most probable way to split a word. Spaces are kept as a _ symbol.
- Byte level BPE: 
  - uses the same merging criteria as BPE, but the starting vocabulary is the 256 possible raw bytes instead of characters. 
  - Every possible text can be built from bytes, so it never needs an unknown token. 
  - Spaces stay attached to the start of the word after it and decoding simply reverses the bytes, so text is recovered exactly.
- We then compare them on 2,000 validation abstracts:
  - Vocab size
  - Avg tokens/abstract
  - chars/token
  - UNK rate
  - train time
  - encoding speed
- After that we check how each tokenizer splits eight hard medical words
- Conclusion:
  - BPE loses the spaces.
  - WordPiece adds spaces around punctuation.
  - Unigram and byte-level BPE matched the original on the sample.
  - Byte-level BPE was chosen because it is lossless, never needs an unknown token, and keeps medical symbols intact.
- Then we set the chosen tokenizer, save it to a file and record the EOT token's ID and the vocab size.

## Task 3: Masking Scheme for Training (cells 12–13)

This demonstrates what the model is trained to do, using an example
- Sentence is tokenized. The i/p is every token except the last, and the targets are the same sequence shifted by 1, so at each position the answer is the next token.
- A table shows each input next to its target, as text.
- The notebook then builds and prints the triangular causal mask. It shows that each position may only look at itself and earlier positions, never at the future.

## Task 4: (cells 14–17)
- We fix the context window at 256 tokens and the batch size at 32.
- Tokenize every training and validation abstract in chunks and put an end of text marker after each one. 
- Everything is joined into one long stream of token IDs, which is converted to numbers the model can use, and the totals are reported.
- Then we build the data pipeline:
  - A dataset class cuts the stream into consecutive 256 token blocks, each with one extra token so the last position has an answer.
  - Each item supplies inputs, shifted labels and a mask of all ones.
  - A data module then serves shuffled training batches and unshuffled validation batches.
  - The block counts are printed.
- Cell 17 inspects one batch.
  - It checks the shapes and data types.
  - It decodes an example back to text.
  - It verifies that the labels really are the inputs shifted by one.
  - It lists the first 12 input and target pairs and counts the EOT markers.

## Task 5: model (cells 18–20)

- Cell 19 picks the fastest available hardware and defines the model in three layers.
- Attention layer:
  - Each token produces a query, key and value for several parallel heads.
  - Queries are compared with keys to make match scores, and the triangular mask hides the future.
  - The scores become probabilities, which are used to blend the values.
  - The result is mixed back together with some random dropout.
- Transformer block: 
  - normalize
  - apply attention
  - add the original back.
  - Then normalize, apply a feed-forward network and add the original back again.
- Full model:
  - A lookup table turns token IDs into vectors and a second table adds position information.
  - These go through 4 blocks and a final normalization.
  - An o/p layer then produces a score for every vocab token. It shares its Nos. with the token table, which saves params.
  - Starting values are small and random, and smaller still in the layers that feed the shortcut paths.
- Cell 20 builds the model with 4 layers, 4 heads and 256-wide vectors and counts its params ~7.3 million. 
- runs three sanity checks:
  - A real batch passes through to confirm the o/p shapes.
  - The starting loss should be ~ 9.68.
  - A causality test changes one token at pos 100 and confirms that earlier predictions stay identical while later ones change.

## Task 6: Training and val (cells 21–26)

- Wraps the model with its training rules.
  - loss- how wrong the predictions are.
  - Training, validation and test losses and perplexity are logged.
  - The optimizer applies a penalty on large weights only to the weight matrices.
  - The learning rate warms up linearly for 200 steps, then decays smoothly along a cosine curve to 10% of its peak.
- Trains for 3,000 steps.
  - Validation runs every 250 steps on 50 batches.
  - Snapshots are saved in three ways: the best by validation loss, 1 every 500 steps, and the last one.
  - Metrics go to a log file, and gradients are clipped to avoid unstable jumps.
  - Old checkpoints are deleted so the run starts clean.
- Builds a proper test set.
  - It uses the second half of the validation data. The best checkpoint was chosen using only the first 1,600 validation blocks, so the second half never influenced any choice.
  - It adds a test loader to the data module, evaluates the best checkpoint, and reports test loss and perplexity.
- Reads the log file and plots training loss and validation loss. Also plots validation perplexity on a logarithmic scale.
- Takes one training block, gets the best checkpoint's prediction at each position, and prints the first 30 positions as the context, the predicted next tokens and the true next tokens.

## Task 7: Generation (cells 27–30)
- Defines the generator. It encodes the prompt, then repeats these steps:
  - Run the model. 
  - Take the scores at the last position. 
  - Choose a token. 
  - Append it, keeping only the last 256 tokens as context.

It stops at the end-of-text token or after 80 new tokens. Four ways of choosing the next token are supported:
| Strategy | How the next token is chosen |
|---|---|
| Greedy | Always the top score |
| Temperature | Sharpens or flattens the probabilities before sampling |
| Top-k | Samples only among the k best tokens |
| Top-p | Samples among the smallest group of tokens whose probabilities add up to p |

## Task 8: Validation

This task has two sections: ML accuracy and medical usefulness

### Section A: How accurate is the model at next-token prediction?

- What it does
  - Loads the best model- It loads the checkpoint with the lowest validation loss during training. 
  - Builds the validation and test halves
   - The validation data is split in two. The first half is used as validation, and the second half is the test set built in Task 6.
   - The best checkpoint was chosen using only the first 1,600 validation blocks, so the test half never influenced any choice. 
  - Measures prediction quality- One routine runs the model over the data 16 blocks at a time and records:
    - the average loss
    - perplexity
    - top-1, top-5 and top-10 accuracy
    - the average loss at each of the 256 positions in the context window 
  - Reports results next to a reference Validation and test results are shown side by side, with a pure-guess model (loss 9.68, perplexity 16,000) as the reference.
    - Plots training against validation loss. The training loss from the log is smoothed over 10 points and drawn against the validation loss at each check. Training loss is measured with dropout on, so it reads slightly worse than validation loss.
  -Plots loss by position. The early and final models are run on 60 test batches, and the loss at each position is smoothed over 8 positions. The early positions have little context, so loss should start high and fall. 
  - Compares medical terms with common words
   - Three hand-picked lists are used: 16 function words (the, of, and…), 15 general scientific words (patients, study, results…) and 40 medical terms (hypertension, thrombosis, cholesterol…).
   - Each word is found in the test text by its token pattern. It counts only if the following token does not continue the word, so "the" is not counted inside "therapy".
   - The first 16 positions of each block are skipped so the model has some context.
   - For each word, the loss of its tokens is added up, then averaged per group for the early and final models. The tables and the bottom two charts show loss per word and loss per token.

What the results showed in this run

- Overall accuracy:

  | Split | Loss | Perplexity | Top-1 | Top-5 | Top-10 |
  |---|---|---|---|---|---|
  | Validation | 4.483 | 88.5 | 26.0% | 46.0% | 53.9% |
  | Test | 4.485 | 88.7 | 26.0% | 45.9% | 53.9% |

  Perplexity of about 89 is far better than the pure guess (16,000). The validation and test numbers are almost identical, so the estimate is stable.
- Medical terms are the hardest words. Loss per word, early vs final model:

  | Word group | Occurrences | Early | Final |
  |---|---|---|---|
  | Function words | 76,545 | 2.48 | 2.01 |
  | General scientific words | 6,464 | 4.51 | 3.38 |
  | Medical terms | 1,525 | 7.34 | 5.47 |

  - In the final model, medical terms cost about 2.7 times as much as function words.
  - Training reduced the loss by about 19% for function words, 25% for general scientific words and 26% for medical terms.
- Every word in the lists was a single token (tokens per word is 1.0), so loss per word and loss per token are the same here. The lists therefore do not test how the model handles rare words that split into pieces.
- The training curves and the position plot are only saved as figures, so read them from the notebook.

### Section B: How useful is the model for a medical application?
This section checks whether what the model says is true.

What it does

1. Reviews the Task 7 samples.
   - It takes the final model's samples and flags any that contain a number with a unit, a percentage or a p-value, since a model with no grounding can invent these.
   - It saves a blank scoring sheet (fluency, medical plausibility and factual correctness, each 1 to 5) to manual_review_template.csv, and prints the 5 top-p samples to read.
   - The scoring itself is done by a human.
2. Probes medical knowledge.
   - It uses 12 sentence starts, each with one correct ending and four wrong but plausible ones, for example "Metformin is used in the treatment of" with "diabetes" against "asthma", "epilepsy", "tuberculosis" and "glaucoma".
   - The model scores how likely each ending is, both in total and per token (which removes the bias against longer endings).
   - It records where the correct ending ranks among the five. It then reports top-1 accuracy and mean reciprocal rank (the average of 1 divided by the rank, which gives partial credit for second or third place), against chance.
   - A per-item table compares the early and final models.
3. Lists other benchmarks. It prints other medical benchmarks to explore (BioLAMA, PubMedQA, MedMCQA, MedQA, MMLU medical subsets, BLURB, BioASQ and HealthBench) and evaluations that suit a small model better.

What the results showed in this run

- Samples: the final model's samples use medical-sounding vocabulary but are not coherent.
  - They contain invented words such as "caseiophagen" and "intrajeffingomas".
  - Phrases repeat across different prompts, for example "malignant malignancy. Following removal of…" and "multicip gland of pre-light…".
  - None of the five was flagged for a numeric claim. The trial sample does contain numbers ("24 months", "28--7 hours"), but the flag only looks for doses, percentages and p-values.
- Fact probe:
  | Model | Top-1 accuracy | Mean reciprocal rank |
  |---|---|---|
  | Early (step 500) | 41.7% (5 of 12) | 0.62 |
  | Final | 33.3% (4 of 12) | 0.60 |
  | Chance | 20% | 0.46 |

  - Both models beat chance, but the final model is not better than the early one. The difference is one item out of 12, which is within noise.
  - The final model ranks the correct ending first for penicillin, hypertension, statins and cirrhosis.
  - It ranks the correct ending last for glaucoma and jaundice.
  - It prefers "blood pressure" over "blood glucose" for diabetes mellitus, so a frequent phrase beats the correct fact.
  - It picks "asthma" for metformin and insulin.
