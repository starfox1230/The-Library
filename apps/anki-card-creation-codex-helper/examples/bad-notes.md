# Bad Anki Note Patterns

Avoid these patterns.

## Too Vague

```json
{"content":"The sky is {{c1::blue}}.","tags":["#AnkiChat::YYYY.MM.DD_Subject"]}
```

This fails because the surrounding text does not lock what attribute is being tested.

## Generic Prompt

```json
{"content":"Key teaching point?<br><br>{{c1::This disease has important imaging features}}","tags":["#AnkiChat::YYYY.MM.DD_Subject"]}
```

This is vague and does not create a useful recall target.

## Raw Textbook Prose

```json
{"content":"Familial adenomatous polyposis is {{c1::an autosomal dominant syndrome featuring innumerable premalignant adenomatous polyps in the colon and to a lesser extent the small bowel, with risk of colon cancer being 100 percent and prophylactic colectomy being the standard of care}}.","tags":["#AnkiChat::YYYY.MM.DD_Subject"]}
```

This is too long. Split it into smaller, locked notes.

## Image Diagnosis Without Image

```json
{"content":"Most likely diagnosis?<br><br>{{c1::Hepatic steatosis}}","tags":["#AnkiChat::YYYY.MM.DD_Subject"]}
```

Diagnosis cards using this stem need image support.

