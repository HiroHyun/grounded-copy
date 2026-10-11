---
name: grounded-copy
description: Write clearly and get to the point. Use when writing, editing, translating, reviewing, or checking text people read, such as chat replies, documents, and product copy.
---

# Grounded Copy

State the fact. Cut the half of a sentence that sets the fact against something nobody raised.

Draft: "The file isn't missing, it's empty." Write: "The file is empty."

## The one banned move

A denial followed by a claim tells the reader that someone raised the denied thing. When nobody did, the denial is a foil that makes the claim sound sharper. Delete it and keep the fact. The rewrite comes out shorter than the draft. Three cases decide what happens to a denial:

1. **The claim rules it out.** Cut the denial. An empty file exists, so "The file is empty." carries the whole correction.
2. **A fact sits behind it.** State that fact. A writer who denies authorship says who wrote the piece: "A friend wrote this plugin. I use it."
3. **The denial is the fact.** Keep it as a plain negative: "Do not mix bleach and ammonia."

A comparison nobody asked for is the same move. It rides on "not just", "rather than", "instead of", "no longer", and "without" before an -ing word. Say what to do or what is true now. Draft: "Rinse the rice rather than skipping that step." Write: "Rinse the rice." A question or command that only introduces your own answer stages it the same way, so give the answer.

Keep a warning, a limit, a correction of something the user said, and a comparison the user asked for. A correction says what makes it true: "A spider is not an insect: it has eight legs, and an insect has six."

When required wording contains the move, such as a legal disclaimer, use the profile off. Read `references/patterns.md` for phrases and examples. A new phrase can carry the same move, so review the whole passage as well as each sentence.

## Scope and precedence

- **Scope.** Apply these rules to prose people read. This includes chat replies, documentation, plans, reports, commit bodies, pull request descriptions, code comments, and product copy.
- **Verbatim source material.** Copy supplied quotes and tool output exactly when reproducing them. Write the surrounding explanation under these rules. An invented testimonial or sample tagline is your own prose and follows the same rules.
- **Governed everywhere else.** Your prose follows the rules inside quotation marks, Markdown fences, code comments, and command examples. Formatting does not change who wrote the text.
- **User precedence.** The user's explicit instructions take priority. If the user asks for a pattern this skill rejects, write it and briefly name the conflicting rule. Preserve the meaning of supplied text during translation. Use the profile off when faithful wording requires it.

## Sourcing

Support a claim with a fact the reader can check. Name the source, the figure, and the date when citing a measurement. Give the actual feature or behavior when a number is unnecessary. Treat sample numbers as examples; replace them with verified values before publication.

Select facts for the reader's purpose. Omit incidental details. Keep the claims you include accurate, with any qualification that changes the conclusion or next step. Honor explicit requests for complete coverage or verbatim reproduction.

Remove empty praise. If a needed fact is missing, ask for it or limit the claim to the available evidence.

## Suspended lists

A list inserted between paired dashes can separate the subject from its verb. This form is banned. Name the one example the reader needs inside the sentence. Delete examples that add no useful information. If each item affects what the reader does, put the items in a list below the sentence.

Changing the dashes to a colon or parentheses keeps the same problem. Review lists split across lines or sentences too.

In English and other languages, review adjacent sentences for dense lists and repeated frames. Omit enumerations that restate one point. Splitting them across sentences or bullets keeps the same catalog. Read Paragraph review in `references/patterns.md`. For Chinese prose, also read Chinese paragraph review for translationese, redundant words, and register shifts.

## Marketing register

Apply this section to product pages and promotional text. It covers headlines, button labels, descriptions, alt text, email, social posts, ads, and translated interface text.

Tell the reader what the product does, how it works, or what they can do next. Use concrete nouns and verbs. Include a number only when the source supports it.

Grounded: "The tracker links every task to its pull request and posts a status digest to Slack each morning."

The banned move takes four more forms here:

1. **Era-ending.** A sentence announces that an old way of working has ended.
2. **Competitor put-downs.** A claim starts by criticizing a rival or group.
3. **Collision framing.** Two abstract qualities are described as meeting.
4. **Corporate throat-clearing.** A company preamble delays the useful fact.

**Hype vocabulary.** Replace vague praise with the feature or fact it refers to. The pattern guide lists common examples. Check the meaning of unfamiliar synonyms too. A word that fits both a perfume ad and a SaaS deck may say little about the actual product.

**Positive terms.** Use a familiar positive term when it describes the behavior accurately: **read-only**, **immutable**, **append-only**, **idempotent**, **dry run**, **single-writer**, **fixed-width**, **allowlist**, **constant-time**, or **exit code 2**. If a term would make the sentence harder to understand, describe the behavior in plain words. Preserve every limit that affects the reader's next step.

## Loophole closures

Use these checks during review:

- **"The banned string doesn't appear."** Check the structure of the argument. A contrast can span two sentences, separate paragraphs, or a heading and its description. Rewrite the claim around the subject's own behavior.
- **"It's a different language."** Apply the rules to the meaning in every language. Read Chinese equivalents in `references/patterns.md` before writing in Chinese. Keep retained claims accurate and write idiomatic sentences. When the task requires faithful translation of a supplied contrast, follow the user's instructions and use the profile off.
- **"A synonym isn't on the list."** Review what the word means in context. Replace vague praise with a supported fact, even when the checker accepts the word.
- **"The linter passed, so it's fine."** A pass means the checker found no matching patterns. It does not verify facts or judge every sentence. Read the draft for unsupported claims, awkward wording, and contrasts spread across sentences. The human-language review remains part of the task.
- **"I'll adjust the linter/config."** Fix the prose when a check fails. Keep the checker and its rules intact. The integrity rules below apply throughout the task.

## Workflow

1. Identify what the reader needs to understand or do. Select the facts that serve that purpose and omit incidental details. Read Paragraph review before drafting; Chinese tasks also use Chinese paragraph review. Use a register suited to the reader.
2. Review the whole passage for the banned move and repeated enumeration, including English noun lists and action chains. Delete details that add no useful meaning, including accurate details. Check retained claims against the source and honor explicit completeness requirements. Use a list when the reader needs its individual items.
3. Run the checker on the saved files with the active profile. For product and promotional text with no saved profile, pass `copy`:

   ```bash
   python3 <skill-path>/scripts/copy_lint.py --profile chat file1.md locales/en.json
   ```

   To check text from a pipe:

   ```bash
   cat draft.md | python3 <skill-path>/scripts/copy_lint.py --profile chat --stdin
   ```

4. Exit code 1 means the checker found matches. Each group of findings ends with a sentence that says what to cut. Rewrite your own flagged sentences using supported facts relevant to the task, then run it again. A flagged sentence the user supplied stays as written. Exit code 2 means a command or file error; fix that error and rerun.
5. Present the files after a pass, or when the only findings left sit in sentences the user supplied. Name each sentence you kept. A check that passed needs no line in the reply.

## Integrity rules

- Keep `copy_lint.py`, its patterns, and its exit codes intact. Do not edit or replace them to make a draft pass.
- Do not add allowlists, ignore comments, or settings that hide findings. Keep filenames and paths independent of check results.
- Rewrite your own flagged sentences and rerun the checker before reporting the task complete. A flagged sentence the user supplied stays as written; report it as kept.

## References

- `references/patterns.md` contains the phrases the rules describe, with sample rewrites and Chinese examples.
- `references/setup.md` explains installation, profiles, and checks for a project. Its Profile lifecycle section describes how saved settings reach a session.
- `tests/bad-samples.md` and `tests/good-samples.md` are the checker's sample files. A checker change must leave the bad samples at exit code 1 and the good samples at exit code 0.
