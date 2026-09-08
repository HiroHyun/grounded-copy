---
name: grounded-copy
description: Write clear prose using concrete facts. Use when writing, editing, translating, or reviewing text that people read, including chat replies, documentation, product copy, reports, commit messages, and code comments. Also use when asked to check copy or remove AI clichés. Preserve supplied facts and follow the user's requested style.
---

# Grounded Copy

Copy describes things by what they ARE. Tell the reader what the product does, how it works, or what they can do next. Use concrete nouns and verbs. Include a number only when the source supports it.

Grounded: "The tracker links every task to its pull request and posts a status digest to Slack each morning."

## The one banned move

Avoid explaining a subject through a contrast with an alternative. State its features or behavior directly. The pattern guide groups this habit into seven forms:

1. **Comparison with an alternative.** A claim depends on what another option lacks.
2. **Reversal reveals.** A denial sets up the claim that follows it.
3. **Era-ending.** A sentence announces that an old way of working has ended.
4. **Competitor put-downs.** A claim starts by criticizing a rival or group.
5. **Rhetorical bait.** A question or command introduces the writer's own answer.
6. **Collision framing.** Two abstract qualities are described as meeting.
7. **Corporate throat-clearing.** A company preamble delays the useful fact.

Every shape blocks with no exception while the profile is active. When required wording contains one, such as a legal disclaimer, use the profile off. Follow an explicit user request that overrides this rule.

To rewrite, identify the useful claim and state it directly. Keep the facts from the source. Read `references/patterns.md` for phrases and examples. A new phrase can use the same pattern, so review the whole passage as well as individual sentences.

## Positive forms

Use a familiar positive term when it describes the behavior accurately: **read-only**, **immutable**, **append-only**, **idempotent**, **dry run**, **single-writer**, **fixed-width**, **allowlist**, **constant-time**, or **exit code 2**.

Explain a technical term when the reader needs help with it. If a term would make the sentence harder to understand, describe the actual behavior in plain words. Preserve every limit that affects the reader's next step.

## Scope and precedence

- **Scope.** Apply these rules to prose people read. This includes chat replies, documentation, plans, reports, commit bodies, pull request descriptions, code comments, and product copy.
- **Verbatim source material.** Copy supplied quotes and tool output exactly when reproducing them. Write the surrounding explanation under these rules. An invented testimonial or sample tagline is your own prose and follows the same rules.
- **Governed everywhere else.** Your prose follows the rules inside quotation marks, Markdown fences, code comments, and command examples. Formatting does not change who wrote the text.
- **User precedence.** The user's explicit instructions take priority. If the user asks for a pattern this skill rejects, write it and briefly name the conflicting rule. Preserve the meaning of supplied text during translation. Use the profile off when faithful wording requires it.

## Sourcing

Support a claim with a fact the reader can check. Name the source, the figure, and the date when citing a measurement. Give the actual feature or behavior when a number is unnecessary. Treat sample numbers as examples; replace them with verified values before publication.

Remove praise that adds no information to a sentence. Keep the fact it was meant to describe. If the source lacks a needed detail, ask for it or write a claim supported by the available information.

## Suspended lists

A list inserted between paired dashes can separate the subject from its verb. This form is banned. Name the one example the reader needs inside the sentence. Delete examples that add no useful information. If each item affects what the reader does, put the items in a list below the sentence.

Changing the dashes to a colon or parentheses keeps the same problem. Rebuild the sentence so the main point is easy to follow. Review lists split across lines or sentences too.

## Marketing register

Apply this section to product pages and promotional text. It covers headlines, button labels, descriptions, alt text, email, social posts, ads, and translated interface text.

**Hype vocabulary.** Replace vague praise with the feature or fact it refers to. The pattern guide lists common examples. Check the meaning of unfamiliar synonyms too. A word that fits both a perfume ad and a SaaS deck may say little about the actual product. Ask what the reader learns from it, then write that detail.

**Plain negation.** Keep a negative statement when it explains a limit the reader needs to act on. For example, "does not support batching" tells a developer how to use an API. State other claims positively. Apply the same care to short labels and headings as to paragraphs.

## Loophole closures

Use these checks during review:

- **"The banned string doesn't appear."** Check the structure of the argument. A contrast can span two sentences, separate paragraphs, or a heading and its description. Rewrite the claim around the subject's own behavior.
- **"It's a different language."** Apply the rules to the meaning in every language. Read the multilingual section of `references/patterns.md` before writing in Chinese, Russian, Spanish, Arabic, French, German, Japanese, or Korean. Keep the source facts and write idiomatic sentences. When the task requires faithful translation of a supplied contrast, follow the user's instructions and use the profile off.
- **"A synonym isn't on the list."** Review what the word means in context. Replace vague praise with a supported fact, even when the checker accepts the word.
- **"The linter passed, so it's fine."** A pass means the checker found no matching patterns. It does not verify facts or judge every sentence. Read the draft for unsupported claims, awkward wording, and contrasts spread across sentences. The human-language review remains part of the task.
- **"I'll adjust the linter/config."** Fix the prose when a check fails. Keep the checker and its rules intact. The integrity rules below apply throughout the task.

## Workflow

1. Identify the reader, the task, and the facts supplied. Draft sentences that explain what the subject does.
2. Read the draft for the seven patterns above. Check meaning and natural phrasing in each language.
3. Run the checker on the saved files:

   ```bash
   python3 <skill-path>/scripts/copy_lint.py file1.md locales/en.json
   ```

   To check text from a pipe:

   ```bash
   cat draft.md | python3 <skill-path>/scripts/copy_lint.py --stdin
   ```

4. Exit code 1 means the checker found matches. Rewrite the flagged sentences using the same facts, then run it again. Exit code 2 means a command or file error; fix that error and rerun.
5. Present the files after a pass. Report the check result for files you checked. A normal chat reply needs no check-result line.

## Integrity rules

- Keep `copy_lint.py`, its patterns, and its exit codes intact. Do not edit or replace them to make a draft pass.
- Do not add allowlists, ignore comments, or settings that hide findings. Keep filenames and paths independent of check results.
- Complete the rewrite and rerun the checker before reporting the task complete.

## References

- `references/patterns.md` contains the phrases the rules describe, with sample rewrites and multilingual examples.
- `references/setup.md` explains installation, profiles, and checks for a project. Its Profile lifecycle section describes how saved settings reach a session.
- `tests/bad-samples.md` and `tests/good-samples.md` are the checker's sample files. A checker change must leave the bad samples at exit code 1 and the good samples at exit code 0.
