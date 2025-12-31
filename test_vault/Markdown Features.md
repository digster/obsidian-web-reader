---
title: Markdown Features
tags:
  - documentation
  - features
  - markdown
---

# Markdown Features

This note demonstrates all the markdown features supported by Obsidian Web Reader.

## Basic Formatting

**Bold text** and *italic text* and ***bold italic***.

~~Strikethrough~~ and `inline code`.

## Headings

All heading levels are supported (H1 through H6).

## Lists

### Unordered Lists

- Item one
- Item two
  - Nested item
  - Another nested item
- Item three

### Ordered Lists

1. First item
2. Second item
   1. Nested numbered
   2. Another nested
3. Third item

### Task Lists

- [x] Completed task
- [ ] Incomplete task
- [ ] Another task

## Links

### External Links

Visit [Obsidian's website](https://obsidian.md) for more information.

### Wiki Links

Link to [[Welcome]] or [[Welcome|the home page]].

Link to a heading: [[Welcome#Getting Started]].

## Embeds

### Image Embeds

![[attachments/sample-image.png]]

### Note Embeds

![[Welcome#Features Demo]]

## Blockquotes

> This is a simple blockquote.
>
> It can span multiple paragraphs.

### Callouts

> [!note] Note Title
> This is a note callout with custom content.

> [!info]
> An info callout without a custom title.

> [!tip] Helpful Tip
> Tips are great for sharing useful information.

> [!warning] Be Careful
> Warnings alert users to potential issues.

> [!danger] Critical Warning
> Danger callouts are for critical information.

> [!example] Example
> This is an example callout.

> [!quote] Famous Quote
> "The only way to do great work is to love what you do." - Steve Jobs

## Code Blocks

### Python

```python
from typing import List

def fibonacci(n: int) -> List[int]:
    """Generate Fibonacci sequence."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    
    sequence = [0, 1]
    while len(sequence) < n:
        sequence.append(sequence[-1] + sequence[-2])
    return sequence

print(fibonacci(10))
```

### JavaScript

```javascript
const fetchData = async (url) => {
  try {
    const response = await fetch(url);
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
};
```

### Bash

```bash
#!/bin/bash
echo "Hello, World!"
for i in {1..5}; do
    echo "Count: $i"
done
```

## Tables

| Feature | Supported | Notes |
|---------|-----------|-------|
| Wiki Links | ✅ | Full support |
| Embeds | ✅ | Images and notes |
| Callouts | ✅ | All types |
| Math | ✅ | KaTeX rendering |

## Math

### Inline Math

The quadratic formula is $x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$.

### Block Math

$$
\sum_{i=1}^{n} i = \frac{n(n+1)}{2}
$$

$$
\begin{bmatrix}
a & b \\
c & d
\end{bmatrix}
\begin{bmatrix}
x \\
y
\end{bmatrix}
=
\begin{bmatrix}
ax + by \\
cx + dy
\end{bmatrix}
$$

## Horizontal Rules

---

## Footnotes

Here's a sentence with a footnote[^1].

And another one[^note].

[^1]: This is the first footnote.
[^note]: This is a named footnote.

## Tags

This note has several tags: #documentation #features #markdown

You can also use nested tags like #tech/web-development.

---

*That's all the markdown features!*

