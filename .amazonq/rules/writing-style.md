---
title: Writing style (ASD-STE100)
summary: The Simplified Technical English rules and the glossary for all English text in the integration.
---

# Writing style (ASD-STE100)

All English text in this project follows **ASD-STE100 Simplified Technical English**
(STE): user docs (`README.md`, `CHANGELOG.md`, `docs/`, `website/docs/intro.md`),
user-facing strings (`strings.json`, `services.yaml`, `locales/en.json`, logs and
exceptions), code comments, PR text and review replies, and chat replies.

Other locales are translations. They do not follow STE. Keep their placeholders and
keys the same as the English source (see [testing.md](testing.md#translations)).

## The rules

### Words

- Use one approved word for one thing, and one meaning for one word. Do not use synonyms
  for variety. The project names are in the glossary below.
- Use the shortest common word. Write "start", not "initiate". Write "use", not
  "utilize". Write "show", not "surface" or "expose".
- Do not use slang, idiom, or metaphor. No "side door", "on the floor", "reach for",
  "under the hood".
- Do not use contractions. Write numbers as numerals ("3 items"), except at the start
  of a sentence.
- Use "must" for a requirement. Use "can" for a possibility. Do not use "may",
  "might", "should", or "could".
- Use "if" for a condition and "when" for a point in time. Write "make sure that", not
  "ensure".
- Do not put more than 3 nouns in a row. Write "the list of items that changed", not
  "the changed item list summary view".
- **Name the noun.** Do not write "nothing", "anything", or "something" where a real
  noun fits. Write "a record that matches no stored record", not "a record that
  matches nothing".
- **Say what a thing does, not what it does not do.** Write "Preview only reports what
  would change", not "Preview reports what would change and writes nothing". Use a
  negative only when the absence *is* the point, such as a limitation.

### Sentences

- Keep a sentence to 20 words or fewer in instructions, and to 25 words or fewer in
  descriptive text.
- Give one instruction or one idea per sentence.
- Use the simple present tense for descriptions. Use the imperative for instructions.
- Do not use a verb form that ends in "-ing" as the main verb. Write "before you
  start the container", not "before starting the container". As a noun it is
  acceptable: "the setting of a value".
- Do not omit articles. Write "open the panel", not "open panel".
- **A product or platform name takes no article.** Write "on iPhone", not "on an
  iPhone". The same goes for Android, Home Assistant and HACS. The article still
  belongs to a common noun that the name modifies: "An Android channel keeps its
  settings" is correct.
- Do not omit "that" after "make sure", "confirm", and "check".
- Put a condition before its instruction. Write "If the item has a value, the card
  shows it", not "The card shows it if the item has a value".
- Do not use parentheses for a second thought. Write it as a separate sentence, or
  remove it.
- Do not use em dashes, semicolons in prose, or rhetorical questions.

### Paragraphs and structure

- Keep a paragraph to 6 sentences or fewer and 1 topic. Start with the topic sentence.
- Use a numbered list for steps in sequence. Use a bulleted list for items with no
  sequence. Do not put more than 2 items in a series inside one sentence. Use a
  list instead.
- Put a warning before the step it applies to. Write it as a command.
- Use a table for data with 2 or more attributes per row. Do not put full
  sentences in a table cell if a short phrase is enough.
- Write a heading as a noun phrase or a command: "Admin operations", "Install the panel".

### Voice

- State the fact first. Start a feature section with what the software supports or
  does: "The integration supports a sensor for each item." Then say what it is useful
  for. Do not open with a problem statement or a scene from daily life.
- Write about the software and the configuration, not about people.
- Do not personify the software. It does not carry, know, want, learn, remember,
  or refuse. It supports, stores, reads, writes, adds, removes, and marks.
- Do not describe the UI. The user can see it. Do not describe a rail, a dot, a
  color, a layout, or how a page looks on a phone. Write what the user does and
  what the software does in response: "Select an item in the list."
- Do not invent a reason for a behavior. Write why only if the maintainer stated the
  reason. "The card shows no edit button" is a fact. "Because users do not edit on a
  dashboard" is an invented reason.
- Do not invent context that the software does not have.
- Use the active voice when the reader is the actor: "select an item". The passive
  voice is acceptable when the actor is obvious or is the software: "the item is
  removed from the list".

### Tone

- Do not write for effect. Do not use "simply", "just", "note that", or
  "it is important to note".
- **Cut the empty subject and verb.** Write "No items", not "There are no items".
  Write "Value: 4", not "It has a value of 4". This applies to UI text, help text,
  and a short line that states a value. A full sentence is still correct in
  documentation, where the subject names a real thing.
- Do not tell a story. Do not repeat a point in different words.
- **Do not write mannered prose.** This rule is strict for `CHANGELOG.md` and all user
  documentation. Write each fact as a plain statement. Do not use these forms:
  - A contrast formula such as "not X, but Y" or "X, not Y". Write Y.
  - A colon that sets up a reveal, such as "The fix is simple: one field."
  - An aphorism, or a line written to sound neat, such as "The URL is the state."
  - A dramatic fragment, such as "No setup. No automation."
  - Quotation marks around a name that you made up.
  - A stock phrase such as "worth noting", "in short", or "out of the box".
  - Alliteration, wordplay, or a pun.

### Vale

- The `STE` style in `styles/STE/` enforces these rules next to `ai-tells`. Add a token
  there when review finds a new banned word. If STE and `ai-tells` disagree, STE wins.
  Disable the vale rule for that line with an inline comment.
- Vale reads a whole list as one block, and its regexes cross sentence ends. Keep
  commas out of list items. Do not start 2 sentences in a row with the same word, or
  `StackedAnaphora` fires.
- Do not start a list item with a bold noun phrase and a colon, such as
  "**The dashboard card**: ...". `LabelAndExplain` fires on "The X:" and "A X:".
  A bold UI name with no article, such as "**Two-way sync**: turn this off", is
  acceptable.
- How the `vale` CI job runs is in [ci-and-ha-versions.md](ci-and-ha-versions.md#vale).

## Glossary of approved names

Use these names and no others for these things. When you build on the template,
replace the rows for the example feature with the nouns of your own domain.

| Use this | Not this | Note |
| --- | --- | --- |
| item | entry, record, thing | The example feature. Replace it with your own noun. |
| value | amount, number, count | The integer on an item. |
| panel | sidebar panel, admin UI, management UI | The panel is in the Home Assistant sidebar. Say that as a sentence, not as a name. |
| card | dashboard card, Lovelace card | |
| admin | administrator, owner | |
| user | member, person | "non-admin user" is permitted. |
| Home Assistant | HA | `HA` is permitted in code comments and PR text. |
| service | action | Home Assistant renamed services to actions. This project keeps "service". |
| event | signal, notification | A Home Assistant bus event. |
| websocket command | ws command, socket call | |
| config entry | integration entry, entry | |
| device | | A Home Assistant device. |
| AI agent | assistant, AI assistant, chatbot, LLM, model | Any tool a user asks to write or read data for them. |

Service and code names keep their identifiers. `add_item` stays `add_item` in code and
in a code span. Add a row when a new name appears. A name in this table is a technical
name, so it can be a noun or a verb as listed, and it can appear in a heading.

## Length budgets

- **CHANGELOG bullets** follow the budget and the bold-lead rules in
  [changelog-and-release.md](changelog-and-release.md).
- **`services.yaml` descriptions** stay at 1 or 2 sentences. The first sentence says
  what the service does. The second says a constraint, if there is one.
- **UI labels** in `locales/en.json` and `strings.json` are 1 to 4 words. A tooltip
  or help text is 1 sentence.

## Checklist before you commit prose

1. Count the words in each sentence. Split any sentence over the limit.
2. Replace every "-ing" verb, "may", "should", "ensure", contraction, and glossary synonym.
3. Remove or split every parenthesis, em dash, and semicolon.
4. Rewrite every contrast formula, colon reveal, aphorism, and dramatic fragment.
5. Cut the subject and verb from each sentence that opens with "it", "this", or "there".
6. Check that every instruction is a command in the active voice.
7. Run `vale <file>` on a documentation file.
