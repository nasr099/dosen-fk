// Simple KaTeX renderer for HTML strings with $...$ (inline) and $$...$$ (block)
// Usage: renderMathHTML('<p>Area is $A=\pi r^2$</p>')
import { renderToString } from 'katex'

// Convert math delimiters to KaTeX-rendered HTML, preserving other HTML and sanitization done upstream
export function renderMathHTML(html) {
  if (!html || typeof html !== 'string') return html || ''
  // Work inside a DOM container to handle existing HTML structure
  const container = document.createElement('div')
  container.innerHTML = html

  // 1) Handle <pre> blocks first: treat their textContent as-is to support multi-line $$ ... $$
  const pres = Array.from(container.querySelectorAll('pre'))
  for (const pre of pres) {
    const txt = pre.textContent || ''
    // look for one or more $$...$$ blocks in this pre
    const parts = []
    let i = 0
    while (i < txt.length) {
      const start = txt.indexOf('$$', i)
      if (start === -1) { parts.push({ type:'text', value: txt.slice(i) }); break }
      if (start > i) parts.push({ type:'text', value: txt.slice(i, start) })
      const end = txt.indexOf('$$', start+2)
      if (end === -1) { parts.push({ type:'text', value: txt.slice(start) }); break }
      const exprRaw = txt.slice(start+2, end)
      let expr = exprRaw.replace(/\\{2,}/g, '\\')
      const div = document.createElement('div')
      try {
        div.innerHTML = renderToString(expr, { throwOnError:false, displayMode:true })
        parts.push({ type:'node', node: div })
      } catch {
        parts.push({ type:'text', value: txt.slice(start, end+2) })
      }
      i = end + 2
    }
    // If we found at least one math block, replace the <pre> with mixed content
    if (parts.some(p => p.type==='node')){
      const wrapper = document.createElement('div')
      for (const p of parts){
        if (p.type==='text') wrapper.appendChild(document.createTextNode(p.value))
        else wrapper.appendChild(p.node)
      }
      pre.replaceWith(wrapper)
    }
  }

  
  // Walk text nodes and replace math segments
  const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, null)
  const toReplace = []
  while (walker.nextNode()) {
    const node = walker.currentNode
    // Skip inside inline code only; allow in <pre> because our editor uses it for block math
    if (node.parentElement && node.parentElement.tagName === 'CODE') continue
    // Skip if already inside a KaTeX-rendered element
    if (node.parentElement && node.parentElement.closest('.katex')) continue
    if ((node.parentElement && node.parentElement.closest('script,style'))) continue
    if (!node.nodeValue.includes('$')) continue
    toReplace.push(node)
  }

  for (const textNode of toReplace) {
    const frag = document.createDocumentFragment()
    const text = textNode.nodeValue
    // Tokenize for $$...$$ (block) and $...$ (inline). Prefer block first.
    const tokens = []
    let i = 0
    while (i < text.length) {
      if (text.startsWith('$$', i)) {
        const end = text.indexOf('$$', i + 2)
        if (end !== -1) {
          const expr = text.slice(i + 2, end)
          tokens.push({ type: 'math-block', expr })
          i = end + 2
          continue
        }
      }
      if (text[i] === '$') {
        const end = text.indexOf('$', i + 1)
        if (end !== -1) {
          const expr = text.slice(i + 1, end)
          tokens.push({ type: 'math-inline', expr })
          i = end + 1
          continue
        }
      }
      // normal text until next $
      const next = text.indexOf('$', i)
      const chunk = next === -1 ? text.slice(i) : text.slice(i, next)
      tokens.push({ type: 'text', value: chunk })
      i = next === -1 ? text.length : next
    }

    for (const t of tokens) {
      if (t.type === 'text') {
        frag.appendChild(document.createTextNode(t.value))
      } else {
        const span = document.createElement(t.type === 'math-block' ? 'div' : 'span')
        span.className = t.type === 'math-block' ? 'math-block' : 'math-inline'
        try {
          // Normalize: collapse double or repeated backslashes to a single backslash so KaTeX understands
          // e.g., `\\frac` -> `\frac`
          let expr = String(t.expr)
          expr = expr.replace(/\\{2,}/g, '\\')
          span.innerHTML = renderToString(expr, { throwOnError: false, displayMode: t.type === 'math-block' })
        } catch {
          // If render fails, fall back to the original delimiters
          span.textContent = (t.type === 'math-block' ? `$$${t.expr}$$` : `$${t.expr}$`)
        }
        frag.appendChild(span)
      }
    }
    textNode.replaceWith(frag)
  }
  return container.innerHTML
}
